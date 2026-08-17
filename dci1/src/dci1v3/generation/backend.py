"""The process boundary to the shared vLLM backend (generic infrastructure).

The scientific environment writes ``plan.json`` + ``design.jsonl``; the
pinned backend interpreter (``dci1/environments/backend/.venv``) executes
``python -m vllm_backend`` from the repository's ``exploratory`` tree and
writes ``rows.jsonl`` plus a provenance sidecar. Nothing scientific crosses
this seam except prompt text and seeds, and nothing here imports any DCI
implementation.

GPU hygiene on this host: inherited visibility variables are cleared,
``HIP_VISIBLE_DEVICES`` selects the one card, and a per-device flock
serialises engine runs.
"""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from dci1v3.engine import fs
from dci1v3.engine.context import DCI1_ROOT, REPO_ROOT
from dci1v3.errors import IntegrityError

BACKEND_PYTHON = DCI1_ROOT / "environments" / "backend" / ".venv" / "bin" / "python"
BACKEND_CWD = REPO_ROOT / "exploratory"
GPU_LOCK_DIR = DCI1_ROOT / "evidence" / ".gpu-locks"

_VISIBILITY_VARS = ("ROCR_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES",
                    "CUDA_VISIBLE_DEVICES")

#: A generate function maps (run_dir, plan, design_rows) -> outcome dict
#: {"rows": [...], "provenance": {...}}. The synthetic adapter substitutes
#: real inference in tests; everything around it stays production code.
GenerateFn = Callable[[Path, dict[str, Any], list[dict[str, Any]]],
                      dict[str, Any]]


def backend_env(device: int) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _VISIBILITY_VARS}
    env["HIP_VISIBLE_DEVICES"] = str(device)
    env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    env["NCCL_P2P_DISABLE"] = "1"
    return env


class GpuLock:
    """Exclusive per-device lock; refuses immediately when the card is busy."""

    def __init__(self, device: int):
        self.path = GPU_LOCK_DIR / f"gpu{device}.lock"
        self._handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w")
        try:
            fcntl.flock(self._handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self._handle.close()
            raise IntegrityError(
                f"GPU lock {self.path} is held by another run") from error
        self._handle.write(str(os.getpid()))
        self._handle.flush()
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._handle, fcntl.LOCK_UN)
        self._handle.close()


def run_backend(run_dir: Path, plan: dict[str, Any],
                design_rows: list[dict[str, Any]], *, device: int = 0,
                timeout_seconds: float = 4 * 3600) -> dict[str, Any]:
    """Execute one real backend run; return {"rows": [...],
    "provenance": {...}}."""
    if not BACKEND_PYTHON.exists():
        raise IntegrityError(
            f"backend interpreter missing: {BACKEND_PYTHON} — build it with "
            f"`cd dci1/environments/backend && uv sync`")
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    plan = dict(plan)
    plan["expected_rows"] = len(design_rows)
    plan_path = run_dir / "plan.json"
    design_path = run_dir / "design.jsonl"
    rows_path = run_dir / "rows.jsonl"
    fs.write_json(plan_path, plan)
    design_path.write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in design_rows))

    log_path = run_dir / "backend.log"
    command = [str(BACKEND_PYTHON), "-u", "-m", "vllm_backend",
               "--plan", str(plan_path), "--design", str(design_path),
               "--out", str(rows_path)]
    with GpuLock(device), log_path.open("w") as log:
        completed = subprocess.run(
            command, cwd=str(BACKEND_CWD), env=backend_env(device),
            stdout=log, stderr=subprocess.STDOUT, timeout=timeout_seconds)
    if completed.returncode == 3:
        raise IntegrityError(f"backend crashed (see {log_path}); no rows "
                             f"are trusted")
    if not rows_path.exists():
        raise IntegrityError(f"backend produced no rows (see {log_path})")
    rows = fs.read_jsonl(rows_path)
    provenance_path = rows_path.with_name(rows_path.stem + "_engine.json")
    provenance = (fs.read_json(provenance_path)
                  if provenance_path.exists() else {})
    if provenance.get("blocked"):
        raise IntegrityError(
            f"backend blocked the run: {provenance.get('outcome') or ''} "
            f"(see {log_path})")
    return {"rows": rows, "provenance": provenance}
