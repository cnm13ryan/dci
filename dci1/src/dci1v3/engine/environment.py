"""Environment and dependency provenance (§28, item 12). Fail closed.

The canonical dependency representation is ``uv.lock`` plus the committed
deterministic ``uv export --frozen`` output. Missing or empty representations
are a qualification failure. Backend-stack fields (vLLM, PyTorch, ROCm,
driver, GPU) are stamped from the backend's own provenance sidecar at
generation time; a container digest is recorded only when the producing
process actually runs in a container.
"""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Any

from dci1v3.engine.context import StudyContext
from dci1v3.errors import IntegrityError
from dci1v3.protocol.hashing import sha_file, sha_obj

#: Execution-relevant environment variables recorded when set (§28).
REGISTERED_ENV_VARS = (
    "HIP_VISIBLE_DEVICES", "ROCR_VISIBLE_DEVICES", "CUDA_VISIBLE_DEVICES",
    "VLLM_WORKER_MULTIPROC_METHOD", "NCCL_P2P_DISABLE", "HF_HOME",
    "PYTORCH_ROCM_ARCH",
)


def dependency_digest(context: StudyContext) -> dict[str, str]:
    for name, path in (("uv.lock", context.deps_lock_path),
                       ("uv export --frozen output",
                        context.deps_export_path)):
        if not Path(path).exists():
            raise IntegrityError(f"dependency representation missing: "
                                 f"{name} at {path}")
        if not Path(path).read_bytes().strip():
            raise IntegrityError(f"dependency representation empty: {name}")
    lock_hash = sha_file(context.deps_lock_path)
    export_hash = sha_file(context.deps_export_path)
    return {"lockfile_hash": lock_hash, "export_hash": export_hash,
            "dependency_digest": sha_obj(
                {"lock": lock_hash, "export": export_hash})}


def interpreter_identity() -> dict[str, str]:
    executable = Path(sys.executable)
    if not executable.exists():
        raise IntegrityError("scientific interpreter binary missing")
    return {"python_executable": str(executable),
            "python_version": platform.python_version()}


def environment_record(context: StudyContext, *,
                       command: list[str] | None = None,
                       backend: dict[str, Any] | None = None,
                       model: dict[str, Any] | None = None) -> dict[str, Any]:
    uname = platform.uname()
    record: dict[str, Any] = {
        **dependency_digest(context),
        **interpreter_identity(),
        "command": list(command if command is not None else sys.argv),
        "operating_system": f"{uname.system} {uname.version}",
        "kernel": uname.release,
        "environment_variables": {
            name: os.environ[name] for name in REGISTERED_ENV_VARS
            if name in os.environ},
    }
    if Path("/.dockerenv").exists():           # only when actually true
        record["container"] = "docker"
    if backend:
        record["backend"] = dict(backend)      # vLLM/torch/ROCm/GPU fields
    if model:
        record["model"] = dict(model)          # repo, revision, template hash
    return record


def environment_digest(record: dict[str, Any]) -> str:
    return sha_obj(record)
