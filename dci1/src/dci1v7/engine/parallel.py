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

__all__ = ["cpu_workers", "pool_map", "shared"]

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
    context = mp.get_context("spawn")
    with context.Pool(workers, initializer=_install_shared,
                      initargs=(state,)) as pool:
        return list(pool.imap(fn, items, chunksize=chunksize))


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
