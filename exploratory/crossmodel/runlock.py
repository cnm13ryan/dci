"""Exclusive ownership of the GPUs and of an output directory.

Written after a session in which two identical Gemma 12B runs executed at the
same time, each holding ~12 GiB per card, each OOMing the other, both appending
to one `partial_generations.jsonl` — which ended with 6 rows carrying 4 distinct
row ids. Nothing detected any of it. The runs simply got slower and produced
corrupt output, and the slowness was misread as a property of the model.

Three separate failures made that possible, and each gets a guard here:

1. **No exclusion.** Two drivers reached the same step and both launched. Now a
   run takes an exclusive `flock` on the GPU lock and on its output directory,
   and a second run refuses to start rather than sharing.

2. **Orphans invisible to cleanup.** A `vllm_tp2.py` process survived fourteen
   hours holding a GPU registration, because cleanup matched only `VLLM::*` —
   the names vLLM gives its *children* — while the backend script keeps the name
   `python`. Now the stale scan matches the scripts themselves, and a process
   holding no lock is reported as an orphan by name and pid.

3. **Silent overwrite.** A rerun appended to a directory that already held
   output. Now that is refused unless resume is asked for explicitly.

The lock is advisory and process-local by design: it protects against this
repository's own runners colliding, which is what actually happened. It cannot
stop an unrelated program from taking VRAM, so `free_vram_gib` is recorded at
acquisition and a dirty card is reported rather than assumed away.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

#: Every command line that can hold VRAM belonging to this study. `VLLM::` alone
#: is not enough — see the module docstring.
RUNNER_PATTERNS = (
    "crossmodel/vllm_tp2.py",
    # The canonical backend entrypoint. `crossmodel/vllm_tp2.py` now delegates
    # to it, but a run started as `python -m vllm_backend` shows only this on
    # its command line, and an orphan invisible to cleanup still holds VRAM.
    "vllm_backend",
    "vllm_capacity_probe",
    "vllm_qwen_probe",
    "xm_vllm_run.py",
    "xm_run.py",
    "VLLM::",
)

#: One lock for the machine's GPUs. Runs are serialised, not interleaved: both
#: cards are a single indivisible resource for tensor parallelism, and the
#: Transformers path shards across both as well.
GPU_LOCK = Path("runs/.gpu.lock")


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def free_vram_gib(minimum_capacity_gib: float = 20.0) -> list[float]:
    """Free VRAM per compute card. Ignores the host's small integrated GPU."""
    try:
        out = subprocess.run(["rocm-smi", "--showmeminfo", "vram", "--json"],
                             capture_output=True, text=True, timeout=60).stdout
        data = json.loads(out)
    except Exception:                                   # noqa: BLE001
        return []
    free = []
    for card in sorted(data):
        try:
            total = float(data[card]["VRAM Total Memory (B)"])
            used = float(data[card]["VRAM Total Used Memory (B)"])
        except (KeyError, TypeError, ValueError):
            continue
        if total / 2 ** 30 < minimum_capacity_gib:
            continue
        free.append(round((total - used) / 2 ** 30, 2))
    return free


#: This checkout. A matched process is only ours if it is working inside it.
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Set into the environment when a lock is taken, so children — including vLLM's
#: spawned workers, which inherit it — can be claimed even if they later chdir.
RUN_ID_VAR = "DCI_RUN_ID"


def _process_cwd(pid: int) -> Optional[Path]:
    """Where a process is working, or None if that cannot be established."""
    try:
        return Path(os.readlink(f"/proc/{pid}/cwd")).resolve()
    except (OSError, PermissionError):      # gone, or another user's process
        return None


def _process_run_id(pid: int) -> Optional[str]:
    try:
        raw = Path(f"/proc/{pid}/environ").read_bytes()
    except (OSError, PermissionError):
        return None
    for entry in raw.split(b"\0"):
        name, sep, value = entry.partition(b"=")
        if sep and name.decode(errors="replace") == RUN_ID_VAR:
            return value.decode(errors="replace")
    return None


def owned_by_this_checkout(pid: int) -> bool:
    """Whether a matched process belongs to THIS repository.

    The patterns are fed to `pgrep -af`, which searches every process on the
    machine. `VLLM::` matches any project's vLLM workers, and `vllm_backend`
    matches any checkout of this one — so a match alone licenses reporting a
    process, never signalling it. Two independent claims are accepted:

    * the process is working inside this checkout, which covers vLLM's spawned
      workers because they inherit the parent's cwd; or
    * it carries this checkout's run id in its environment, which survives a
      later chdir.

    Ownership that cannot be ESTABLISHED is refused. A process belonging to
    another user, or one that exited between the scan and the check, reads as
    not ours — the failure mode of leaving a foreign job alone is a run that
    waits, and the failure mode of the opposite is killing someone else's work.
    """
    cwd = _process_cwd(pid)
    if cwd is not None and (cwd == REPO_ROOT or REPO_ROOT in cwd.parents):
        return True
    run_id = _process_run_id(pid)
    return bool(run_id) and run_id == os.environ.get(RUN_ID_VAR)


def running_runners(exclude_pid: Optional[int] = None,
                    foreign: bool = False) -> list[dict]:
    """Live runner processes belonging to this checkout.

    `pgrep -af` matches the whole command line, which is why the caller's own
    invocation has to be excluded explicitly: a shell running a command that
    merely NAMES one of these scripts would otherwise look like a runner.

    Matches outside this checkout are dropped, not returned, because everything
    downstream of this function may signal what it is given. Pass `foreign=True`
    to see them instead — useful for reporting "a card is busy and it is not us",
    which is a different diagnosis from "a run of ours is already up".
    """
    exclude_pid = exclude_pid if exclude_pid is not None else os.getpid()
    found: dict[int, str] = {}
    for pattern in RUNNER_PATTERNS:
        try:
            out = subprocess.run(["pgrep", "-af", pattern],
                                 capture_output=True, text=True,
                                 timeout=30).stdout
        except Exception:                               # noqa: BLE001
            continue
        for line in out.splitlines():
            pid_text, _, command = line.partition(" ")
            if not pid_text.isdigit():
                continue
            pid = int(pid_text)
            if pid in (exclude_pid, os.getpid(), os.getppid()):
                continue
            # A shell wrapper that happens to quote the pattern is not a runner.
            if command.startswith("/bin/bash -c") or " -c source " in command:
                continue
            # Machine-wide match, repository-scoped result.
            if owned_by_this_checkout(pid) is foreign:
                continue
            found[pid] = command
    return [{"pid": pid, "command": command[:300], "foreign": foreign}
            for pid, command in sorted(found.items())]


def shm_segments() -> list[str]:
    return sorted(p.name for p in Path("/dev/shm").glob("psm_*"))


def clean_shm() -> list[str]:
    """Remove stale vLLM shared-memory segments. Safe only with no runners up."""
    removed = []
    for path in Path("/dev/shm").glob("psm_*"):
        try:
            path.unlink()
            removed.append(path.name)
        except OSError:
            pass
    return removed


def kill_runners(pids: Iterable[int], grace: float = 5.0) -> list[int]:
    """SIGTERM then SIGKILL a set of pids. Returns those that were signalled.

    Ownership is re-checked HERE rather than trusted from the caller. This is
    the only function in the module that signals another process, so it is the
    one place the guarantee has to hold; a pid list assembled elsewhere, or by a
    future caller, must not be able to route a foreign process into a SIGKILL.
    """
    pids = [int(p) for p in pids if int(p) not in (os.getpid(), os.getppid())]
    pids = [p for p in pids if owned_by_this_checkout(p)]
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(grace)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return pids


class RunLockError(RuntimeError):
    """Refusal to start. Always names what is in the way."""


class RunLock:
    """Exclusive GPU + output-directory ownership for one run.

        with RunLock(out_dir, model_id, revision) as lock:
            ...

    Refuses to start when another runner is live, when either lock is held, or
    when the output directory already contains results and resume was not asked
    for. Releases both locks and reaps its own children on normal exit, on an
    exception, and on SIGINT/SIGTERM.
    """

    def __init__(self, out_dir: Path, model_id: str, revision: str = "",
                 *, run_kind: str = "", gpus: str = "cuda:0+cuda:1",
                 allow_resume: bool = False, reap_orphans: bool = True,
                 gpu_lock_path: Path = GPU_LOCK):
        self.out_dir = Path(out_dir)
        self.model_id = model_id
        self.revision = revision
        self.run_kind = run_kind
        self.gpus = gpus
        self.allow_resume = allow_resume
        self.reap_orphans = reap_orphans
        self.gpu_lock_path = Path(gpu_lock_path)
        self._handles: list = []
        self._previous_handlers: dict = {}
        self.manifest_path = self.out_dir / "run_lock_manifest.json"
        self.free_vram_at_start: list[float] = []
        self.orphans_reaped: list[dict] = []

    # ------------------------------------------------------------- acquiring
    def _flock(self, path: Path, what: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = path.open("a+")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.seek(0)
            holder = handle.read()[:400].strip() or "(no holder record)"
            handle.close()
            raise RunLockError(
                f"{what} is held by another run: {holder}. Refusing to start; "
                "two runs sharing the GPUs corrupt each other's output and "
                "each other's memory measurements.")
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps({
            "pid": os.getpid(), "run_dir": str(self.out_dir),
            "model_id": self.model_id, "started_utc": utc()}))
        handle.flush()
        self._handles.append(handle)
        return handle

    def _check_no_runners(self) -> None:
        live = running_runners()
        if not live:
            return
        detail = "; ".join(f"pid {r['pid']}: {r['command'][:120]}"
                           for r in live[:5])
        if not self.reap_orphans:
            raise RunLockError(
                f"{len(live)} runner process(es) are already live and would "
                f"contend for the GPUs: {detail}")
        # Nothing holds the GPU lock — we just took it — so anything matching a
        # runner pattern is by definition an orphan of a dead run.
        killed = kill_runners(r["pid"] for r in live)
        self.orphans_reaped = live
        print(f"  reaped {len(killed)} orphaned runner process(es): {detail}",
              flush=True)
        still = running_runners()
        if still:
            raise RunLockError(
                f"{len(still)} runner process(es) survived cleanup: "
                + "; ".join(f"pid {r['pid']}" for r in still))

    def _check_output_dir(self) -> None:
        existing = [name for name in ("generations.jsonl",
                                      "partial_generations.jsonl",
                                      "raw_generations.jsonl")
                    if (self.out_dir / name).exists()]
        if existing and not self.allow_resume:
            raise RunLockError(
                f"{self.out_dir} already contains {existing}. Refusing to write "
                "into it: appending to another run's output is how a 6-row file "
                "with 4 distinct row ids gets made. Pass allow_resume=True for "
                "a validated resume, or choose a new directory.")

    def __enter__(self) -> "RunLock":
        self.out_dir.mkdir(parents=True, exist_ok=True)
        # Stamp the run id BEFORE anything is spawned, so every child inherits
        # it. vLLM forces `spawn` on ROCm and its workers chdir in some
        # configurations, which is why cwd alone is not relied on to recognise
        # our own processes later.
        self._stamped_run_id = RUN_ID_VAR not in os.environ
        if self._stamped_run_id:
            os.environ[RUN_ID_VAR] = f"{self.out_dir.name}:{os.getpid()}"
        # GPU lock first: taking it is what makes "any live runner is an orphan"
        # a sound inference rather than a race.
        self._flock(self.gpu_lock_path, "the GPU lock")
        self._flock(self.out_dir / ".run.lock", f"{self.out_dir}")
        self._check_no_runners()
        self._check_output_dir()

        stale = shm_segments()
        removed = clean_shm() if stale else []
        self.free_vram_at_start = free_vram_gib()
        if self.free_vram_at_start and min(self.free_vram_at_start) < 20.0:
            print(f"  WARNING: only {self.free_vram_at_start} GiB free per card "
                  "before this run starts. A memory result measured here is "
                  "NOT attributable to the checkpoint.", flush=True)

        self._write_manifest(state="running", stale_shm=stale,
                             removed_shm=removed)
        self._install_handlers()
        print(f"  run lock held: pid {os.getpid()}, {self.out_dir}, "
              f"free VRAM {self.free_vram_at_start} GiB", flush=True)
        return self

    # -------------------------------------------------------------- manifest
    def _write_manifest(self, *, state: str, **extra: Any) -> None:
        """Atomic: written to a temp file and renamed, never partially seen."""
        payload = {
            "stamp": "EXPLORATORY_NO_EVIDENCE",
            "state": state,
            "pid": os.getpid(),
            "run_id": self.out_dir.name,
            "run_kind": self.run_kind,
            "model_id": self.model_id,
            "model_revision": self.revision,
            "gpu_allocation": self.gpus,
            "gpu_lock": str(self.gpu_lock_path),
            "free_vram_gib_at_start": self.free_vram_at_start,
            "orphans_reaped_at_start": self.orphans_reaped,
            "host": os.uname().nodename,
            "argv": sys.argv,
            "updated_utc": utc(),
            **extra,
        }
        temp = self.manifest_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(payload, indent=1, default=str))
        os.replace(temp, self.manifest_path)

    # -------------------------------------------------------------- releasing
    def _install_handlers(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            self._previous_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._on_signal)

    def _on_signal(self, signum, frame):               # noqa: ANN001
        print(f"\n  signal {signum} — releasing the run lock and reaping "
              "children before exit", flush=True)
        self.release(state=f"terminated_by_signal_{signum}")
        previous = self._previous_handlers.get(signum, signal.SIG_DFL)
        if callable(previous):
            previous(signum, frame)
        raise SystemExit(128 + int(signum))

    def reap_children(self) -> list[dict]:
        """Kill runner processes this run started, so none outlive it."""
        mine = []
        for record in running_runners():
            try:
                parent = int(subprocess.run(
                    ["ps", "-o", "ppid=", "-p", str(record["pid"])],
                    capture_output=True, text=True, timeout=20).stdout.strip()
                    or -1)
            except Exception:                           # noqa: BLE001
                continue
            if parent == os.getpid():
                mine.append(record)
        if mine:
            kill_runners(r["pid"] for r in mine)
        return mine

    def release(self, state: str = "finished") -> None:
        if not self._handles:
            return
        children = self.reap_children()
        try:
            self._write_manifest(state=state, children_reaped=children,
                                 finished_utc=utc())
        except Exception:                               # noqa: BLE001
            pass
        for handle in reversed(self._handles):
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()
            except Exception:                           # noqa: BLE001
                pass
        self._handles.clear()
        for sig, previous in self._previous_handlers.items():
            try:
                signal.signal(sig, previous)
            except Exception:                           # noqa: BLE001
                pass
        self._previous_handlers.clear()

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.release(state="failed" if exc_type else "finished")
        # Unstamp what this lock stamped. Leaving it set would mark every
        # process this interpreter spawns afterwards -- including ones with
        # nothing to do with the run -- as belonging to it.
        if getattr(self, "_stamped_run_id", False):
            os.environ.pop(RUN_ID_VAR, None)
            self._stamped_run_id = False
        return False


# ------------------------------------------------------------ dataset checks
def assert_unique_rows(rows: list[dict], expected: Optional[int] = None,
                       key: str = "row_id") -> dict:
    """Every row distinct, and exactly as many as the design called for.

    Duplicate ids are the fingerprint of two writers appending to one file. That
    happened, went undetected, and produced a file whose row count looked
    plausible. This turns it into a loud failure at the point of writing.
    """
    ids = [r.get(key) for r in rows]
    counts: dict[Any, int] = {}
    for value in ids:
        counts[value] = counts.get(value, 0) + 1
    duplicates = sorted(k for k, n in counts.items() if n > 1)
    problems = []
    if duplicates:
        problems.append(
            f"{len(duplicates)} duplicated {key}(s), e.g. {duplicates[:3]} — "
            "this is the signature of two processes writing one file")
    if None in counts:
        problems.append(f"{counts[None]} row(s) carry no {key}")
    if expected is not None and len(rows) != expected:
        problems.append(f"{len(rows)} rows, expected {expected}")
    if expected is not None and len(counts) != expected:
        problems.append(f"{len(counts)} unique {key}s, expected {expected}")
    if problems:
        raise AssertionError("dataset integrity check failed: "
                             + "; ".join(problems))
    return {"rows": len(rows), f"unique_{key}s": len(counts),
            "duplicates": 0, "expected": expected}


def audit_machine() -> dict:
    """A snapshot a run can record, or a human can read before starting one."""
    return {
        "checked_utc": utc(),
        "free_vram_gib": free_vram_gib(),
        "runner_processes": running_runners(),
        "shm_segments": shm_segments(),
        "gpu_lock_exists": GPU_LOCK.exists(),
    }


def _parse_meminfo_gib() -> dict:
    text = Path("/proc/meminfo").read_text()
    fields = {}
    for name in ("MemTotal", "MemAvailable", "Shmem"):
        match = re.search(rf"^{name}:\s+(\d+) kB", text, re.M)
        if match:
            fields[name] = round(int(match.group(1)) / 2 ** 20, 1)
    return fields


def host_memory_gib() -> dict:
    """Host RAM, because CPU offload draws on it and leaked shm eats it."""
    try:
        return _parse_meminfo_gib()
    except Exception:                                   # noqa: BLE001
        return {}


if __name__ == "__main__":
    print(json.dumps({**audit_machine(), "host_memory_gib": host_memory_gib()},
                     indent=1))
