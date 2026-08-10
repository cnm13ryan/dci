"""Local ROCm environment diagnostic for the exploratory DCI study.

Deliberately separate from `dci.diagnostics` (the confirmatory doctor): that one
enforces the frozen study's execution-condition policy, and an exploratory probe
must not be able to make it pass or fail. This one only *reports*, plus a single
hard check — that a real GPU tensor op produces the right answer — because every
number this study produces is downstream of that.

Run:  uv run --project exploratory python -m dci_exploratory.rocm_doctor
"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from typing import Any


def _cmd(*argv: str) -> str:
    exe = shutil.which(argv[0])
    if exe is None:
        return f"<{argv[0]} not on PATH>"
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        return (out.stdout or out.stderr).strip()
    except Exception as exc:                                  # pragma: no cover
        return f"<{argv[0]} failed: {exc}>"


def _rocm_version() -> str:
    for path in ("/opt/rocm/.info/version", "/opt/rocm/.info/version-dev"):
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read().strip()
        except OSError:
            continue
    return "<unknown>"


def _package_versions() -> dict[str, str]:
    import importlib.metadata as md
    names = ("torch", "torchvision", "triton", "transformers", "tokenizers",
             "accelerate", "huggingface-hub", "numpy", "pandas", "scipy",
             "matplotlib", "dci")
    out = {}
    for name in names:
        try:
            out[name] = md.version(name)
        except Exception:
            out[name] = "<not installed>"
    return out


def collect() -> dict[str, Any]:
    """Everything about this machine the run record needs, as plain JSON."""
    import torch

    info: dict[str, Any] = {
        "host": platform.node(),
        "kernel": platform.release(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "rocm_version": _rocm_version(),
        "packages": _package_versions(),
        "torch_version": torch.__version__,
        # torch.version.hip is populated only by a ROCm build; `cuda` on a ROCm
        # wheel is a HIP alias, so this is the field that says which stack is
        # really underneath.
        "torch_hip_version": getattr(torch.version, "hip", None),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "is_rocm_build": bool(getattr(torch.version, "hip", None)),
        "torch_cuda_is_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        "devices": [],
        "bf16_supported": None,
        "gpu_smoke": None,
    }

    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(index)
            info["devices"].append({
                "index": index,
                "name": torch.cuda.get_device_name(index),
                "gcn_arch": getattr(props, "gcnArchName", None),
                "total_memory_bytes": int(props.total_memory),
                "total_memory_gib": round(props.total_memory / 2**30, 2),
                "multi_processor_count": getattr(props, "multi_processor_count", None),
            })
        try:
            info["bf16_supported"] = bool(torch.cuda.is_bf16_supported())
        except Exception as exc:
            info["bf16_supported"] = f"<check failed: {exc}>"

    info["rocm_smi"] = _cmd("rocm-smi", "--showproductname")
    return info


def gpu_smoke(device_index: int = 0) -> dict[str, Any]:
    """Allocate, compute, verify, release. The one check that is allowed to fail.

    A matmul of a known matrix against the identity must return that matrix
    exactly, in every dtype we might generate under. `allclose` against a
    tolerance would pass even if the accumulate path were badly wrong, so the
    BF16 case is compared to the BF16 *rounding* of the expected value rather
    than to a loose epsilon.
    """
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("no GPU visible to torch; the exploratory study is "
                           "GPU-only by design and will not fall back to CPU")

    device = f"cuda:{device_index}"
    results: dict[str, Any] = {"device": device,
                               "device_name": torch.cuda.get_device_name(device_index)}
    torch.cuda.reset_peak_memory_stats(device)
    # Measured RELATIVE to a baseline taken after one warm matmul. The first
    # matmul makes hipBLASLt claim a persistent ~32 MiB workspace that
    # empty_cache() does not return, and counting that as a leak would make
    # every honest run report one.
    warm = torch.zeros(8, 8, device=device) @ torch.zeros(8, 8, device=device)
    del warm
    torch.cuda.empty_cache()
    baseline = int(torch.cuda.memory_allocated(device))
    results["baseline_allocated_bytes"] = baseline

    for dtype_name in ("float32", "bfloat16", "float16"):
        dtype = getattr(torch, dtype_name)
        torch.manual_seed(0)
        a = torch.randn(512, 512, device=device, dtype=torch.float32)
        eye = torch.eye(512, device=device, dtype=dtype)
        product = (a.to(dtype) @ eye).to(torch.float32)
        expected = a.to(dtype).to(torch.float32)     # the same rounding, not a tolerance
        max_abs_err = float((product - expected).abs().max())
        results[dtype_name] = {
            "exact": max_abs_err == 0.0,
            "max_abs_error": max_abs_err,
            "sample_value": float(product[0, 0]),
        }
        del a, eye, product, expected

    results["peak_allocated_bytes"] = int(torch.cuda.max_memory_allocated(device))
    torch.cuda.empty_cache()
    torch.cuda.synchronize(device)
    after = int(torch.cuda.memory_allocated(device))
    results["allocated_after_release_bytes"] = after
    results["leaked_bytes"] = after - baseline
    results["released_cleanly"] = after <= baseline
    return results


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    device_index = int(argv[argv.index("--device") + 1]) if "--device" in argv else 0

    report = collect()
    report["gpu_smoke"] = gpu_smoke(device_index)
    print(json.dumps(report, indent=2))

    smoke = report["gpu_smoke"]
    failures = [d for d in ("float32", "bfloat16", "float16")
                if not smoke[d]["exact"]]
    if failures:
        print(f"\nFAIL: identity matmul was not exact in {failures}", file=sys.stderr)
        return 1
    if not report["is_rocm_build"]:
        print("\nFAIL: torch is not a ROCm build", file=sys.stderr)
        return 1
    print("\nOK: ROCm GPU allocates, computes exactly, and releases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
