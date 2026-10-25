"""The execution environment: attested on the host that will generate, bound
by Freeze 1, and re-checked live before every real backend run.

The environment that produces pilot responses (the backend interpreter, its
vLLM / torch / transformers versions, every installed distribution, and the
accelerator) cannot be observed from the machine the protocol is written
on. So nothing here invents it:

* ``probe(python)`` runs a fixed script in the backend interpreter and
  reports what it finds, or ``UNAVAILABLE`` with the reason;
* ``lock_from_probe`` turns an AVAILABLE probe into a lock: the comparable
  identity (versions, the hash of the full distribution list, the GPU class
  -- model, count, compute capability and memory -- and the backend source
  tree) plus host details recorded without being bound (hostname, kernel,
  GPU UUIDs, driver build). It refuses a host that does not meet D12's
  execution requirements (``requirement_problems``);
* Freeze 1 carries the lock, or records ``UNATTESTED`` and blocks
  authorisation (``freeze.py``);
* ``execute`` probes again and ``freeze.assert_authorized`` refuses when the
  live identity is not the locked one.

The lock is produced by ``python -m dci.batch1 attest-environment`` on the
execution host, and reviewed like any other frozen input.

**Two interpreters (D12).** The *orchestrator* runs this package; it must be
Python ``config.ORCHESTRATOR_PYTHON`` (``require_orchestrator``), and every
protocol command refuses under any other minor version with the reason.
The *backend* runs the vLLM seam in its own process; its version is part of
the attested identity, and a lock is refused unless its minor version is
``config.BACKEND_PYTHON``.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from dci.batch1 import config as CFG
from dci.batch1.store import RunError, record_hash, tree_hash

__all__ = ["PROBE_SCRIPT", "probe", "lock_from_probe", "backend_source",
           "BACKEND_DIR", "identity_of", "PythonMismatch", "orchestrator",
           "python_minor", "require_orchestrator", "requirement_problems",
           "HOST_FIELDS"]


class PythonMismatch(RunError):
    """An interpreter whose Python version is not the one D12 names."""


def python_minor(version: str | None) -> str:
    return ".".join(str(version or "").split(".")[:2])


def _interpreter() -> tuple[str, str, str]:
    return (platform.python_version(), sys.implementation.name,
            sys.executable)


def orchestrator() -> dict[str, Any]:
    """The interpreter running this package, as Freeze 1 records it."""
    version, implementation, executable = _interpreter()
    return {"python": version, "minor": python_minor(version),
            "implementation": implementation, "executable": executable}


def require_orchestrator() -> dict[str, Any]:
    """Refuse, saying why, unless this is CPython ``ORCHESTRATOR_PYTHON``."""
    found = orchestrator()
    if found["minor"] != CFG.ORCHESTRATOR_PYTHON or \
            found["implementation"] != "cpython":
        raise PythonMismatch(
            f"Batch 1 protocol commands run under CPython "
            f"{CFG.ORCHESTRATOR_PYTHON} (D12); this interpreter is "
            f"{found['implementation']} {found['python']} "
            f"({found['executable']}). Use the repository's environment, "
            f"for example `.venv/bin/python -m dci.batch1 ...` after "
            f"`uv sync` at the repository root, which reads .python-version")
    return found

_REPO = Path(__file__).resolve().parents[3]
BACKEND_DIR = _REPO / "exploratory" / "vllm_backend"

PROBE_SCRIPT = r"""
import hashlib, json, platform, subprocess, sys
import importlib.metadata as md
out = {"python": sys.version.split()[0], "implementation": sys.implementation.name,
       "executable": sys.executable, "platform": platform.platform(),
       "hostname": platform.node(), "kernel": platform.release()}
packages = {}
for name in ("vllm", "torch", "transformers", "tokenizers", "triton",
             "xformers", "flashinfer-python", "numpy"):
    try:
        packages[name] = md.version(name)
    except md.PackageNotFoundError:
        packages[name] = None
out["packages"] = packages
dists = sorted({f"{d.metadata['Name'].lower()}=={d.version}"
                for d in md.distributions() if d.metadata["Name"]})
out["distributions"] = len(dists)
out["distributions_hash"] = hashlib.sha256("\n".join(dists).encode()).hexdigest()
try:
    import torch
    out["torch_cuda"] = torch.version.cuda
    out["torch_hip"] = getattr(torch.version, "hip", None)
    n = torch.cuda.device_count()
    out["accelerators"] = sorted({torch.cuda.get_device_name(i)
                                  for i in range(n)})
    out["gpu_count"] = n
    out["gpus"] = []
    for i in range(n):
        p = torch.cuda.get_device_properties(i)
        out["gpus"].append({"name": p.name,
                            "capability": "%d.%d" % (p.major, p.minor),
                            "memory_gib": round(p.total_memory / 2 ** 30),
                            "uuid": str(getattr(p, "uuid", "") or "")})
except Exception as error:
    out["accelerator_error"] = f"{type(error).__name__}: {error}"[:300]
try:
    smi = subprocess.run(["nvidia-smi", "--query-gpu=uuid,driver_version",
                          "--format=csv,noheader"], capture_output=True,
                         text=True, timeout=60).stdout
    rows = [[c.strip() for c in l.split(",")] for l in smi.splitlines() if l.strip()]
    out["gpu_uuids"] = sorted(r[0] for r in rows)
    out["driver"] = sorted({r[1] for r in rows})
except Exception as error:
    out["driver_error"] = f"{type(error).__name__}: {error}"[:300]
print("DCI_BATCH1_ENV " + json.dumps(out, sort_keys=True))
"""


def backend_source() -> dict[str, Any]:
    """Code hashes of the seam the backend interpreter executes."""
    return tree_hash(BACKEND_DIR)


def probe(python: str, *, timeout: float = 600) -> dict[str, Any]:
    if not Path(python).exists():
        return {"status": "UNAVAILABLE",
                "reason": f"backend interpreter not found: {python}"}
    try:
        proc = subprocess.run([python, "-I", "-c", PROBE_SCRIPT],
                              capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "UNAVAILABLE",
                "reason": f"{type(error).__name__}: {error}"[:300]}
    lines = [l for l in proc.stdout.splitlines()
             if l.startswith("DCI_BATCH1_ENV ")]
    if proc.returncode or not lines:
        return {"status": "UNAVAILABLE",
                "reason": f"probe exited {proc.returncode}: "
                          f"{proc.stderr.strip()[-300:]}"}
    found = json.loads(lines[-1].split(" ", 1)[1])
    return {"status": "AVAILABLE", "interpreter": python, **found}


def identity_of(found: Mapping[str, Any]) -> dict[str, Any]:
    """The fields two environments must share to count as the same: the
    software, and the GPU class (model, count, compute capability, memory;
    D12, 2026-10-25). Which physical host or GPUs, and the driver build,
    are recorded in the lock's ``host`` but not compared."""
    gpus = found.get("gpus") or []
    return {"python": found.get("python"),
            "implementation": found.get("implementation"),
            "packages": found.get("packages"),
            "distributions_hash": found.get("distributions_hash"),
            "torch_cuda": found.get("torch_cuda"),
            "torch_hip": found.get("torch_hip"),
            "accelerators": found.get("accelerators"),
            "gpu_count": found.get("gpu_count"),
            "gpu_capabilities": sorted({g.get("capability") for g in gpus}),
            "gpu_memory_gib": sorted(g.get("memory_gib") for g in gpus),
            "backend_source_hash": backend_source()["hash"]}


#: Recorded in a lock, never compared (D12, 2026-10-25).
HOST_FIELDS = ("interpreter", "executable", "platform", "hostname", "kernel",
               "gpu_uuids", "driver", "distributions", "accelerator_error",
               "driver_error")


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(x) for x in str(text).split(".") if x.isdigit())


def requirement_problems(identity: Mapping[str, Any],
                         host: Mapping[str, Any],
                         req: Mapping[str, Any] | None = None) -> list[str]:
    """Where an attested environment falls short of D12's execution
    requirements (``config.EXECUTION_REQUIREMENTS``): checked when the lock
    is made and again when Freeze 1 is built."""
    req = CFG.EXECUTION_REQUIREMENTS if req is None else req
    problems = []
    if python_minor(identity.get("python")) != req["backend_python"]:
        problems.append(f"backend Python {identity.get('python')}, not "
                        f"{req['backend_python']}")
    for name, want in req["packages"].items():
        have = (identity.get("packages") or {}).get(name)
        if have != want:
            problems.append(f"{name} {have}, not {want}")
    if identity.get("torch_cuda") != req["torch_cuda"]:
        problems.append(f"torch built for CUDA {identity.get('torch_cuda')}, "
                        f"not {req['torch_cuda']}")
    if identity.get("accelerators") != [req["gpu_name"]]:
        problems.append(f"GPUs {identity.get('accelerators')}, not only "
                        f"{req['gpu_name']}")
    if identity.get("gpu_count") != req["gpu_count"]:
        problems.append(f"{identity.get('gpu_count')} visible GPUs, not "
                        f"{req['gpu_count']}")
    if identity.get("gpu_capabilities") != [req["gpu_compute_capability"]]:
        problems.append(f"compute capability {identity.get('gpu_capabilities')}"
                        f", not {req['gpu_compute_capability']}")
    drivers = host.get("driver") or []
    if not drivers or any(_version(d) < _version(req["min_driver"])
                          for d in drivers):
        problems.append(f"driver {drivers or 'unknown'}, not >= "
                        f"{req['min_driver']}")
    return problems


def lock_from_probe(found: Mapping[str, Any]) -> dict[str, Any]:
    if found.get("status") != "AVAILABLE":
        raise ValueError(f"no environment to lock: {found.get('reason')}")
    if found.get("packages", {}).get("vllm") is None:
        raise ValueError("the probed interpreter has no vLLM; it cannot be "
                         "the backend environment")
    if python_minor(found.get("python")) != CFG.BACKEND_PYTHON:
        raise ValueError(
            f"the backend interpreter is Python {found.get('python')}; D12 "
            f"records {CFG.BACKEND_PYTHON} for the vLLM backend (the pinned "
            f"vllm wheel is cp312). Attest the pinned backend environment")
    identity = identity_of(found)
    host = {k: found.get(k) for k in HOST_FIELDS}
    problems = requirement_problems(identity, host)
    if problems:
        raise ValueError("this host does not meet D12's execution "
                         "requirements: " + "; ".join(problems))
    return {"schema": "dci.batch1/environment-lock/v2", "status": "ATTESTED",
            "identity": identity, "identity_hash": record_hash(identity),
            "requirements": dict(CFG.EXECUTION_REQUIREMENTS), "host": host}
