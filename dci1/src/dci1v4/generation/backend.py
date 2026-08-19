"""The v4-owned adapter over the shared vLLM execution primitive.

The scientific environment writes ``plan.json`` + ``design.jsonl``; the pinned
backend interpreter (``dci1/environments/backend/.venv``) executes
``python -m vllm_backend`` from the repository's ``exploratory`` tree and
writes ``rows.jsonl`` plus a provenance sidecar.

**Why reusing this seam is legitimate (brief §2).** ``exploratory/vllm_backend``
is stdlib-only at its contract boundary, imports no DCI implementation, and
embeds no scientific assumption: it receives prompt text and a seed and returns
generated text with token counts and a finish reason. Nothing scientific
crosses the seam. This module is the v4-owned adapter around it, and it is the
only place in ``dci1v4`` that knows the seam exists; a v3 module is never
imported to reach it.

GPU hygiene on this host: inherited visibility variables are cleared,
``HIP_VISIBLE_DEVICES`` selects one card, and a per-device flock serialises
engine runs. The autorater path additionally pins concurrency at one (§10.4,
T-15), which the plan carries as ``max_concurrency``.
"""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from dci1v4.engine import fs
from dci1v4.engine.context import DCI1_ROOT, REPO_ROOT
from dci1v4.errors import IntegrityError

BACKEND_PYTHON = (DCI1_ROOT / "environments" / "backend" / ".venv" / "bin"
                  / "python")
BACKEND_CWD = REPO_ROOT / "exploratory"
GPU_LOCK_DIR = DCI1_ROOT / "evidence" / ".gpu-locks"

_VISIBILITY_VARS = ("ROCR_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES",
                    "CUDA_VISIBLE_DEVICES")

#: A generate function maps (run_dir, plan, design_rows) -> outcome dict
#: {"rows": [...], "provenance": {...}}. The synthetic adapter substitutes real
#: inference in CPU tests; everything around it stays production code.
GenerateFn = Callable[[Path, dict[str, Any], list[dict[str, Any]]],
                      dict[str, Any]]


def backend_env(device: int) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _VISIBILITY_VARS}
    env["HIP_VISIBLE_DEVICES"] = str(device)
    env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    env["NCCL_P2P_DISABLE"] = "1"
    # Every model revision is a pinned local snapshot; offline hub mode
    # guarantees the engine reads exactly that snapshot and makes a run immune
    # to transient network failure.
    env["HF_HUB_OFFLINE"] = "1"
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


#: Engine seed for the shared execution primitive. Distinct from every
#: scientific seed: per-request seeds travel on the request and are derived
#: from experimental identity (protocol/seeds.py), and this value only fixes
#: engine-level state the backend needs.
ENGINE_SEED = 20260819


def build_plan(spec, *, stage: str, max_new_tokens: int,
               temperature: float = 0.7, top_p: float = 0.9,
               top_k: int = 50, chunk_size: int = 32,
               skip_special_tokens: bool = True,
               serialised: bool = False) -> dict[str, Any]:
    """The registered decoding policy for one stage, in the seam's own schema.

    Every backend-consumed field is explicit and the backend registry supplies
    nothing: a default that changed on the far side of the seam would be an
    unlogged change of experimental condition. ``reasoning_mode`` is
    NO_THINKING for every registered v4 model — the hybrid Qwen has thinking
    disabled through its chat template's own switch, and the other three have
    no thinking channel at all (§6.1).
    """
    plan: dict[str, Any] = {
        "model_id": spec.model_id,
        "model_revision": spec.revision,
        "model_family": spec.family,
        "dtype": spec.dtype,
        "quantization": "none",
        "tensor_parallel_size": spec.tensor_parallel_size,
        "gpu_memory_utilization": spec.gpu_memory_utilization,
        "disable_custom_all_reduce": True,
        "enforce_eager": True,
        "cpu_offload_gb": 0.0,
        "max_model_len": spec.max_model_len,
        "engine_seed": ENGINE_SEED,
        "trust_remote_code": False,
        "limit_mm_per_prompt": None,
        "temperature": temperature,
        "top_p": top_p,
        # The seam spells "top-k off" as 0 on input; a registered positive
        # value passes through unchanged.
        "top_k": top_k if temperature > 0 else 0,
        "generation_ceiling": max_new_tokens,
        "answer_tokens": max_new_tokens,
        "chunk_size": chunk_size,
        "deadline_seconds": None,
        "strategy": "single_phase",
        "reasoning_mode": "NO_THINKING",
        "chat_template_kwargs": dict(spec.chat_template_kwargs),
        "reasoning_parser": None,
        "think_open": "",
        "think_close": "",
        "decoding_policy": "greedy" if temperature == 0 else "stochastic",
        "skip_special_tokens": skip_special_tokens,
        "thinking_policy": spec.thinking_policy,
        "stage": stage,
    }
    if serialised:
        # §10.4 / T-15: concurrent serving produced repeated-run label
        # instability, so any autorater path serves one request at a time.
        plan["max_concurrency"] = 1
        plan["chunk_size"] = 1
    return plan


def run_backend(run_dir: Path, plan: dict[str, Any],
                design_rows: list[dict[str, Any]], *, device: int = 0,
                timeout_seconds: float = 24 * 3600) -> dict[str, Any]:
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
    design_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n"
                                   for r in design_rows))

    log_path = run_dir / "backend.log"
    command = [str(BACKEND_PYTHON), "-u", "-m", "vllm_backend",
               "--plan", str(plan_path), "--design", str(design_path),
               "--out", str(rows_path)]
    if plan.get("chunk_size"):
        command += ["--chunk-size", str(plan["chunk_size"])]
    with GpuLock(device), log_path.open("w") as log:
        completed = subprocess.run(command, cwd=str(BACKEND_CWD),
                                   env=backend_env(device), stdout=log,
                                   stderr=subprocess.STDOUT,
                                   timeout=timeout_seconds)
    if completed.returncode == 3:
        raise IntegrityError(f"backend crashed (see {log_path}); no rows are "
                             f"trusted")
    if not rows_path.exists():
        raise IntegrityError(f"backend produced no rows (see {log_path})")
    rows = fs.read_jsonl(rows_path)
    provenance_path = rows_path.with_name(rows_path.stem + "_engine.json")
    provenance = (fs.read_json(provenance_path) if provenance_path.exists()
                  else {})
    if provenance.get("blocked"):
        raise IntegrityError(
            f"backend blocked the run: {provenance.get('outcome') or ''} "
            f"(see {log_path})")
    return {"rows": rows, "provenance": provenance}


def real_generate_fn(device: int = 0) -> GenerateFn:
    def generate(run_dir: Path, plan: dict[str, Any],
                 design_rows: list[dict[str, Any]]) -> dict[str, Any]:
        return run_backend(run_dir, plan, design_rows, device=device)
    return generate
