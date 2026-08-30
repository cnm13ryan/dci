"""Process pools for a stage's CPU-bound loops (2026-08-29).

Two loops in the run layer are embarrassingly parallel and were serial:
scoring the rows a backend run returned (``run/execute.generate_and_score``,
~2 ms a row, ~113 verdicts each) and building §13.11's calibration table
(``run/gates_run._calibration_rows``, one entry per split and candidate).
Measured on the registered ``qwen3-4b`` run and again on the 2026-08-28
development rehearsal, the two cost about 200 s and 590 s of Gate 2's two
hours, and the scoring recurs at every generating stage.

**What a pool may not change: anything a record carries.** Every unit of
work is a pure function of its own pickled input and of a small shared
state sent to each worker once; the parent receives the results in input
order and assembles records exactly as the serial loop did. ``workers=1``
runs the same units in-process, in the same order, and that path is the
reference the pooled path is tested against byte for byte
(``tests_v7/test_parallel.py``). No seed is drawn in a worker, no file is
written by one, and no result depends on which worker produced it or when.

**Why not fork.** The first version forked the calling process and let the
workers inherit its state. A forked child of a process that has other
threads --- the spawned scenario workers of the execution-path audit have a
result-queue feeder thread; a stage process may have whatever a library
started --- can inherit a lock another thread held at the fork and wait on
it forever, and the audit did exactly that on 2026-08-29: one worker per
scenario process asleep for eight hours, its siblings zombies. A second
version used ``forkserver``; inside a real stage process
(``python -m dci1v7.run.cli run --stage REGIME_SCREEN``) its forked worker
slept on a futex before importing anything, and the stage hung. Workers are
now **spawned**: a fresh interpreter each, nothing inherited, inputs by
pickle. Spawning re-imports the calling process's main module (as
``__mp_main__``), so the main module must be importable --- every entry
point in this repository is --- and when it is not (a script fed on stdin)
the units run serially rather than fail.

``DCI1_V7_CPU_WORKERS`` sets the pool size for a process (``1`` selects the
serial path); the default leaves four cores to the backend and the other
lane.
"""
from __future__ import annotations

import multiprocessing as mp
import os
from collections.abc import Callable, Sequence
from typing import Any

__all__ = ["PoolStalled", "cpu_workers", "pool_map", "shared"]

#: Below this many units the pool's start-up costs more than it saves.
MIN_ITEMS_FOR_A_POOL = 64
#: The default cap; more workers than this contend with the other lane.
MAX_DEFAULT_WORKERS = 16
#: Cores left to the backend process and the other lane by default.
RESERVED_CORES = 4

#: The shared state of the current pool, in every worker and --- on the
#: serial path --- in the calling process. Read through `shared()`.
_SHARED: dict[str, Any] = {}


def cpu_workers() -> int:
    """The pool size this process uses: the environment's, or the default."""
    env = os.environ.get("DCI1_V7_CPU_WORKERS")
    if env:
        return max(1, int(env))
    return max(1, min(MAX_DEFAULT_WORKERS, (os.cpu_count() or 1)
                      - RESERVED_CORES))


def shared() -> dict[str, Any]:
    """The state `pool_map` was given as ``shared``, wherever a unit runs."""
    return _SHARED


def _install_shared(state: dict[str, Any]) -> None:
    _SHARED.clear()
    _SHARED.update(state)


def pool_map(fn: Callable[[Any], Any], items: Sequence[Any], *,
             shared: dict[str, Any] | None = None,
             workers: int | None = None,
             chunksize: int | None = None) -> list[Any]:
    """``[fn(item) for item in items]``, computed in a forkserver pool.

    ``fn`` must be a module-level callable (it is sent to the workers by
    reference); ``items`` and the results travel by pickle; ``shared`` is
    installed once in every worker before its first unit and is read
    through `shared()`. The result list is in item order whatever the
    completion order. With ``workers`` at 1 --- or fewer than
    ``MIN_ITEMS_FOR_A_POOL`` items --- the units run in this process, in
    order, with the same shared state installed, and no pool is created;
    that is the reference path.

    An exception in a unit propagates to the caller as the exception the
    unit raised, and the pool is torn down.
    """
    workers = cpu_workers() if workers is None else max(1, int(workers))
    state = dict(shared or {})
    if workers <= 1 or len(items) < MIN_ITEMS_FOR_A_POOL:
        _install_shared(state)
        try:
            return [fn(item) for item in items]
        finally:
            _SHARED.clear()
    if not _main_is_importable():
        _install_shared(state)
        try:
            return [fn(item) for item in items]
        finally:
            _SHARED.clear()
    if chunksize is None:
        chunksize = max(1, len(items) // (workers * 8))
    try:
        return _pooled(fn, items, state, workers, chunksize)
    except PoolStalled as stalled:
        # The reference path, on the same units: identical results, later.
        _log(f"pool stalled ({stalled}); running the {len(items)} units "
             "serially instead")
        _install_shared(state)
        try:
            return [fn(item) for item in items]
        finally:
            _SHARED.clear()


class PoolStalled(RuntimeError):
    """A pool that stopped delivering results, or whose workers would not
    exit; the caller falls back to the serial path."""


#: Seconds a pool may go without delivering the next chunk of results
#: before it is declared stalled. A unit is milliseconds of work; a chunk
#: is at most a few thousand of them.
RESULT_TIMEOUT_SECONDS = 600.0
#: Seconds workers get to exit after `terminate()` before they are killed.
TEARDOWN_TIMEOUT_SECONDS = 30.0


def _log(message: str) -> None:
    import sys

    print(f"[engine.parallel] {message}", file=sys.stderr, flush=True)


def _pooled(fn: Callable[[Any], Any], items: Sequence[Any],
            state: dict[str, Any], workers: int, chunksize: int
            ) -> list[Any]:
    """Run the units in spawned workers, one pipe each, with bounded waits.

    **Why not ``multiprocessing.Pool``.** Its workers share one task queue
    behind one lock, and a worker that dies holding that lock --- or is
    killed while holding it --- leaves every other worker, and
    ``Pool.terminate()`` itself, waiting on it forever. That is what a
    stage's pool did on 2026-08-29: every unit done, then 75 minutes in
    ``Pool.__exit__`` behind two workers asleep on that lock. Here each
    worker owns a duplex pipe to the parent and nothing is shared between
    workers: chunks are dealt round-robin by index, results come back
    tagged with the index and are reassembled in order, a worker's death is
    seen on its sentinel, silence beyond ``RESULT_TIMEOUT_SECONDS`` is a
    stall, and teardown joins with a bound and kills what is left. Any of
    those raises `PoolStalled`, and the caller reruns the units serially.
    """
    import pickle
    from multiprocessing import connection as mpc

    context = mp.get_context("spawn")
    chunks = [list(items[i:i + chunksize])
              for i in range(0, len(items), chunksize)]
    n_workers = max(1, min(workers, len(chunks)))
    procs: list[Any] = []
    conns: list[Any] = []
    try:
        for index in range(n_workers):
            parent_end, child_end = context.Pipe(duplex=True)
            process = context.Process(
                target=_worker_main, args=(child_end, fn, state),
                daemon=True, name=f"dci1v7-pool-{index}")
            process.start()
            child_end.close()
            procs.append(process)
            conns.append(parent_end)
        # One chunk in flight per worker, dispatch interleaved with
        # collection. A first version sent every chunk up front and only
        # then read results: with a pipe's buffer smaller than a chunk of
        # scored rows, a worker blocked sending its result to a parent
        # blocked sending it the next chunk, and both waited forever
        # (rehearsal r5 of gemma-3n-e2b-it, Gate 2, 2026-08-29). Which
        # worker computes which chunk is immaterial to the result: a chunk's
        # values are a pure function of its items and the shared state, and
        # they are reassembled by chunk index.
        results: dict[int, list[Any]] = {}
        next_chunk = 0
        in_flight: dict[Any, int] = {}          # conn -> chunk index
        idle = list(conns)
        sentinel_of = {p.sentinel: p for p in procs}
        worker_of = dict(zip(conns, procs))

        def dispatch() -> None:
            nonlocal next_chunk
            while idle and next_chunk < len(chunks):
                conn = idle.pop()
                conn.send(("chunk", next_chunk, chunks[next_chunk]))
                in_flight[conn] = next_chunk
                next_chunk += 1

        dispatch()
        while len(results) < len(chunks):
            ready = mpc.wait(list(in_flight) + list(sentinel_of),
                             timeout=RESULT_TIMEOUT_SECONDS)
            if not ready:
                raise PoolStalled(
                    f"no result within {RESULT_TIMEOUT_SECONDS:.0f} s with "
                    f"{len(chunks) - len(results)} of {len(chunks)} chunks "
                    "outstanding")
            for item in ready:
                if item in sentinel_of:
                    process = sentinel_of.pop(item)
                    if any(worker_of[c] is process for c in in_flight):
                        raise PoolStalled(
                            f"worker {process.name} exited (code "
                            f"{process.exitcode}) with a chunk in flight")
                    continue
                if item not in in_flight:
                    continue
                try:
                    message = item.recv()
                except EOFError as gone:
                    raise PoolStalled(
                        f"worker {worker_of[item].name} closed its pipe "
                        "with a chunk in flight") from gone
                kind = message[0]
                if kind == "result":
                    _, c, values = message
                    results[c] = values
                    del in_flight[item]
                    idle.append(item)
                elif kind == "error":
                    _, _c, payload = message
                    raise pickle.loads(payload)
            dispatch()
        for conn in conns:
            try:
                conn.send(("stop",))
            except (OSError, ValueError):
                pass
        return [value for c in range(len(chunks)) for value in results[c]]
    finally:
        for conn in conns:
            try:
                conn.close()
            except OSError:
                pass
        _join_or_kill(procs, TEARDOWN_TIMEOUT_SECONDS)


def _worker_main(conn: Any, fn: Callable[[Any], Any],
                 state: dict[str, Any]) -> None:
    """A worker: install the shared state, then serve chunks until "stop".

    An exception in a unit is sent back pickled with its chunk index and the
    worker stops; the parent re-raises it as itself.
    """
    import pickle

    _install_shared(state)
    try:
        while True:
            message = conn.recv()
            if message[0] == "stop":
                conn.send(("done",))
                return
            _, index, chunk = message
            try:
                conn.send(("result", index, [fn(item) for item in chunk]))
            except BaseException as error:               # noqa: BLE001
                try:
                    payload = pickle.dumps(error)
                except Exception:                        # noqa: BLE001
                    payload = pickle.dumps(RuntimeError(
                        f"{type(error).__name__}: {error}"))
                conn.send(("error", index, payload))
                return
    finally:
        conn.close()


def _join_or_kill(processes: Sequence[Any], timeout: float) -> int:
    """Terminate the workers, join them within ``timeout`` seconds, kill the
    rest. Returns how many had to be killed."""
    import time

    for process in processes:
        if process.is_alive():
            process.terminate()
    deadline = time.monotonic() + timeout
    for process in processes:
        process.join(max(0.0, deadline - time.monotonic()))
    killed = 0
    for process in processes:
        if process.is_alive():
            process.kill()
            process.join(5.0)
            killed += 1
    return killed


def _main_is_importable() -> bool:
    """Whether a spawned worker can re-import this process's main module.

    A module run with ``-m`` or a script file can be; an interpreter fed on
    stdin or ``-c`` cannot, and a pool started from one dies with an
    ``EOFError`` in the worker rather than a clear message.
    """
    import sys

    main = sys.modules.get("__main__")
    if main is None:
        return False
    spec = getattr(main, "__spec__", None)
    if spec is not None and getattr(spec, "name", None):
        return True
    path = getattr(main, "__file__", None)
    return bool(path) and os.path.exists(path) and \
        not os.path.basename(path).startswith("<")
