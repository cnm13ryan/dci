"""Local environment doctor: workstation (ROCm) and generic CPU tiers.

Reports and validates the environment; returns 0 (supported) or 30
(unsupported for the requested tier). `gpu=True` adds the accelerator tier
including a minimal deterministic generation on the dev_fast model. Facts are
read from the live system; nothing is assumed from documentation.

This lives in the PACKAGE, not in scripts/, because `dci doctor` advertises it:
a CLI command whose implementation sits outside the installed distribution
fails on any checkout that has the package and not the repository working tree,
and it cannot be imported by a test. scripts/local_doctor.py remains as the
standalone entry point and delegates here.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys


#: Distributions whose import name differs from their package name.
_IMPORT_NAMES = {"z3-solver": "z3"}


def _requirements_from_pyproject() -> list[str]:
    """`[project].dependencies` from the source tree, for an uninstalled checkout.

    Still the authoritative declaration — the same table the metadata is built
    from — rather than a second list that can disagree with it. Returns nothing
    if the file is absent, which is the ordinary case for a wheel install.
    """
    import tomllib
    from pathlib import Path

    # src/dci/diagnostics.py -> src/dci -> src -> the repository root.
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        table = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    return list(table.get("project", {}).get("dependencies", []))


def declared_dependencies() -> list[tuple[str, str]]:
    """`(distribution, import name)` for every declared runtime dependency.

    Read from the installed distribution's own metadata rather than restated
    here. A hand-maintained list drifts: this one listed six of the seven
    declared dependencies, and the omitted one was `z3-solver` — so an
    environment missing the solver that gates every v19 satisfiability check
    reported itself healthy, and nine tests failed at collection instead.

    The uninstalled case reads `pyproject.toml` for the same reason. It used to
    fall back to a literal six-name tuple in `run()` — which had drifted in
    exactly the same way, omitting `z3-solver` again — so a source checkout run
    without `pip install -e .` reported a healthy environment while the solver
    that gates Stage 2 was absent. There is now no second list to drift.
    """
    from importlib.metadata import PackageNotFoundError, requires

    try:
        requirements = requires("dci") or []
    except PackageNotFoundError:                # not installed as a distribution
        requirements = _requirements_from_pyproject()
    names = []
    for requirement in requirements:
        # "numpy>=1.26", "pytest>=8 ; extra == 'dev'" -- drop extras and markers.
        if ";" in requirement:
            continue
        name = re.split(r"[<>=!~\[ ]", requirement, maxsplit=1)[0].strip()
        if name:
            names.append((name, _IMPORT_NAMES.get(name, name.replace("-", "_"))))
    return names


def _module_version(distribution: str, module) -> str:
    """A version string, preferring the distribution's own metadata.

    `z3` exposes no `__version__`, so the naive attribute lookup reported "?"
    for the one dependency whose absence started this.
    """
    version = getattr(module, "__version__", None)
    if version:
        return str(version)
    from importlib.metadata import PackageNotFoundError, version as metadata_version

    try:
        return metadata_version(distribution)
    except PackageNotFoundError:
        return "?"


def section(title):
    print(f"\n== {title}")


def report(key, value, ok=None):
    mark = "" if ok is None else ("  [ok]" if ok else "  [FAIL]")
    print(f"  {key:34s} {value}{mark}")
    return bool(ok) if ok is not None else True


def run(gpu: bool = False, expect_devices: int | None = None) -> int:
    """Report the environment and return 0 (supported) or 30 (unsupported)."""
    args = argparse.Namespace(gpu=gpu, expect_devices=expect_devices)
    failures = []

    section("host")
    report("os", f"{platform.system()} {platform.release()}")
    report("machine", platform.machine())
    report("python", sys.version.split()[0],
           ok=sys.version_info >= (3, 11)) or failures.append("python>=3.11")

    section("scientific core")
    declared = declared_dependencies()
    if not declared:
        # Neither metadata nor pyproject. Say so and FAIL: reporting a healthy
        # scientific core after checking nothing is the failure mode this whole
        # function exists to prevent.
        failures.append("dependency declaration")
        report("declared dependencies", "NOT FOUND -- neither installed "
               "metadata nor pyproject.toml; nothing was checked", ok=False)
    for distribution, module in declared:
        try:
            m = importlib.import_module(module)
            report(distribution, _module_version(distribution, m), ok=True)
        except Exception as exc:
            failures.append(distribution)
            report(distribution, f"MISSING ({exc}) -- run `uv sync`", ok=False)
    try:
        import dci
        from dci.compat import TORCH_AVAILABLE, TRANSFORMERS_AVAILABLE
        report("dci", dci.__version__, ok=True)
        report("torch importable", TORCH_AVAILABLE)
        report("transformers importable", TRANSFORMERS_AVAILABLE)
    except Exception as exc:
        failures.append("dci")
        report("dci", f"MISSING ({exc})", ok=False)

    section("accelerator")
    hip_ver = cuda_ver = None
    try:
        import torch
        report("torch", torch.__version__, ok=True)
        hip_ver = getattr(torch.version, "hip", None)
        cuda_ver = getattr(torch.version, "cuda", None)
        report("torch.version.hip", hip_ver or "-")
        report("torch.version.cuda", cuda_ver or "-")
        avail = torch.cuda.is_available()
        # On ROCm builds torch.cuda IS the HIP device layer; this is the
        # documented behavior the notebook relied on and the backends keep.
        report("torch.cuda.is_available()", avail, ok=(avail or not args.gpu))
        if args.gpu and not avail:
            failures.append("accelerator")
        if avail:
            n = torch.cuda.device_count()
            report("visible devices", n,
                   ok=(args.expect_devices is None or n == args.expect_devices))
            if args.expect_devices is not None and n != args.expect_devices:
                failures.append(f"expected {args.expect_devices} devices")
            for i in range(n):
                props = torch.cuda.get_device_properties(i)
                arch = getattr(props, "gcnArchName", "") or f"{props.major}.{props.minor}"
                report(f"device {i}", f"{props.name} | {arch} | "
                       f"{props.total_memory / 2**30:.1f} GiB", ok=True)
            bf16 = torch.tensor([1.0], dtype=torch.bfloat16,
                                device="cuda:0").dtype == torch.bfloat16
            report("bf16 tensor on device", bf16, ok=True)
            fp16 = torch.tensor([1.0], dtype=torch.float16,
                                device="cuda:0").dtype == torch.float16
            report("fp16 tensor on device", fp16, ok=fp16)
    except Exception as exc:
        report("torch stack", f"unavailable ({type(exc).__name__}: {exc})",
               ok=not args.gpu)
        if args.gpu:
            failures.append("torch")

    if hip_ver:
        section("ROCm")
        smi = shutil.which("rocm-smi") or shutil.which("amd-smi")
        report("rocm-smi/amd-smi", smi or "not on PATH", ok=bool(smi))
        try:
            import amdsmi  # noqa: F401
            report("amdsmi python", "importable", ok=True)
        except Exception as exc:
            report("amdsmi python", f"unavailable ({type(exc).__name__})")
        if smi:
            try:
                out = subprocess.run([smi], capture_output=True, text=True,
                                     timeout=20).stdout
                print("  telemetry sample:")
                for line in out.splitlines()[:8]:
                    print("   ", line)
            except Exception as exc:
                report("telemetry", f"failed ({exc})", ok=False)

    if args.gpu:
        section("model smoke (dev_fast, deterministic short generation)")
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            model_id = "Qwen/Qwen2.5-0.5B-Instruct"
            rev = "7ae557604adf67be50417f59c2c2f167def9a775"
            tok = AutoTokenizer.from_pretrained(model_id, revision=rev)
            model = AutoModelForCausalLM.from_pretrained(
                model_id, revision=rev, dtype=torch.float16,
                device_map={"": int(os.environ.get("DCI_DOCTOR_DEVICE", 0))})
            prompt = tok.apply_chat_template(
                [{"role": "user", "content": "Say the word ready."}],
                tokenize=False, add_generation_prompt=True)
            ids = tok(prompt, return_tensors="pt").to(model.device)
            torch.manual_seed(0)
            out = model.generate(**ids, max_new_tokens=8, do_sample=False)
            text = tok.decode(out[0][ids["input_ids"].shape[1]:],
                              skip_special_tokens=True)
            again = model.generate(**ids, max_new_tokens=8, do_sample=False)
            same = torch.equal(out, again)
            report("generation", text.strip()[:40] or "<empty>", ok=True)
            report("greedy repeat identical", same, ok=same)
            report("peak VRAM GiB",
                   f"{torch.cuda.max_memory_allocated() / 2**30:.2f}", ok=True)
            if not same:
                failures.append("nondeterministic greedy decode")
        except Exception as exc:
            failures.append("model smoke")
            report("model smoke", f"FAILED ({type(exc).__name__}: {exc})", ok=False)

    section("verdict")
    if failures:
        print(f"  UNSUPPORTED for the requested tier: {failures}")
        print("  See environments/rocm or environments/cuda for the supported "
              "stacks; the CPU tier needs only `pip install -e .`.")
        return 30
    print("  environment supported for the requested tier")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dci doctor")
    ap.add_argument("--gpu", action="store_true", help="require an accelerator")
    ap.add_argument("--expect-devices", type=int, default=None,
                    help="fail unless exactly this many GPUs are visible")
    args = ap.parse_args(argv)
    return run(gpu=args.gpu, expect_devices=args.expect_devices)


if __name__ == "__main__":
    sys.exit(main())
