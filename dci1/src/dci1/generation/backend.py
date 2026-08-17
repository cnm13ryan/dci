"""The process boundary to the shared vLLM backend.

The scientific environment (this package, repo-root ``.venv``, no GPU stack)
writes ``plan.json`` + ``design.jsonl``; the pinned backend interpreter
(``dci1/environments/backend/.venv`` — vLLM 0.15.1+rocm720, decision D23/A2)
executes ``python -m vllm_backend`` with this repository's backend code and
writes ``rows.jsonl`` plus a provenance sidecar. This is the backend's own
documented seam; nothing scientific crosses it except prompt text and seeds.

GPU hygiene on this host (2× RX 7900 XTX + an unusable integrated gfx1036):
inherited visibility variables are cleared and ``HIP_VISIBLE_DEVICES`` is set
explicitly to the one selected card. A per-device ``flock`` serialises engine
runs so two invocations can never share a card.
"""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from dci1.evidence.store import read_json, read_jsonl, write_json
from dci1.protocol.constants import ProtocolError

REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND_PYTHON = REPO_ROOT / "dci1" / "environments" / "backend" / ".venv" / "bin" / "python"
BACKEND_CWD = REPO_ROOT / "exploratory"
LOCK_DIR = REPO_ROOT / "dci1" / "evidence" / ".locks"

#: Cleared before every backend invocation; a stale value silently moves the
#: engine to the wrong card (documented failure on this host).
_VISIBILITY_VARS = ("ROCR_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES",
                    "CUDA_VISIBLE_DEVICES")


def backend_env(device: int) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _VISIBILITY_VARS}
    env["HIP_VISIBLE_DEVICES"] = str(device)
    env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    env["NCCL_P2P_DISABLE"] = "1"
    return env


class GpuLock:
    """Exclusive per-device lock. Refuses immediately when the card is busy."""

    def __init__(self, device: int):
        self.path = LOCK_DIR / f".gpu{device}.lock"
        self._handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w")
        try:
            fcntl.flock(self._handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self._handle.close()
            raise ProtocolError(
                f"GPU lock {self.path} is held by another run; two engines "
                f"must never share a card") from error
        self._handle.write(str(os.getpid()))
        self._handle.flush()
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._handle, fcntl.LOCK_UN)
        self._handle.close()


def run_backend(run_dir: Path, plan: dict[str, Any],
                design_rows: list[dict[str, Any]], *, device: int = 0,
                timeout_seconds: float = 4 * 3600) -> dict[str, Any]:
    """Execute one backend run; return {"rows": [...], "provenance": {...}}.

    ``design_rows`` each carry ``row_id``, ``user_prompt``,
    ``scientific_seed`` and arbitrary identity fields, which the backend
    returns unchanged on every row.
    """
    if not BACKEND_PYTHON.exists():
        raise ProtocolError(
            f"backend interpreter missing: {BACKEND_PYTHON} — build it with "
            f"`cd dci1/environments/backend && uv sync`")
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    plan = dict(plan)
    plan["expected_rows"] = len(design_rows)
    plan_path = run_dir / "plan.json"
    design_path = run_dir / "design.jsonl"
    rows_path = run_dir / "rows.jsonl"
    write_json(plan_path, plan)
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
        raise ProtocolError(
            f"backend crashed (see {log_path}); no rows are trusted")
    if not rows_path.exists():
        raise ProtocolError(f"backend produced no rows file (see {log_path})")
    rows = read_jsonl(rows_path)
    provenance_path = rows_path.with_name(rows_path.stem + "_engine.json")
    provenance = read_json(provenance_path) if provenance_path.exists() else {}
    if provenance.get("blocked"):
        raise ProtocolError(
            f"backend blocked the run: {provenance.get('outcome') or ''} "
            f"{provenance.get('detail') or provenance.get('engine_error') or ''}"
            f" (see {log_path})")
    return {"rows": rows, "provenance": provenance,
            "returncode": completed.returncode}
