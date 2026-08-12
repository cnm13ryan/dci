"""Drive one vLLM TP=2 slice end to end: plan, generate, ingest.

Three steps in two interpreters. The plan and the ingest run here, in the
scientific environment; the generation runs in `.venv-vllm`, which has the torch
the vLLM wheel needs. Nothing scientific crosses that boundary except the design
and the rows.

    uv run python xm_vllm_run.py --model Qwen/Qwen3.5-4B --load 3
    uv run python xm_vllm_run.py --model google/gemma-4-12B-it --load 5

`--calibration N` runs the Stage B pilot instead: the same DCI-shaped prompts on
N tasks drawn from a split the evaluation slice never touches.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

BACKEND_PYTHON = HERE / ".venv-vllm" / "bin" / "python"
BACKEND_SCRIPT = HERE / "crossmodel" / "vllm_tp2.py"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


#: Every process pattern that can hold VRAM after its driver has gone.
#: `VLLM::` alone is NOT enough: vLLM renames its engine and worker processes,
#: but the BACKEND SCRIPT ITSELF keeps the name `python` and holds a GPU
#: registration for as long as it lives. One such orphan from an abandoned
#: calibration run survived fourteen hours and every reap in between, because
#: every reap looked only for the renamed children.
ORPHAN_PATTERNS = ("VLLM::", "crossmodel/vllm_tp2.py", "vllm_capacity_probe",
                   "vllm_qwen_probe")


def reap() -> None:
    """Kill orphaned vLLM processes and their shared-memory segments.

    Deliberately blunt, and safe because this driver owns the GPUs for the
    duration of a run: anything matching these patterns that is still alive when
    a new engine starts is by definition not wanted. The alternative — reading a
    memory figure that some dead run is still holding — is how a technical
    failure gets recorded as a capacity result.
    """
    import time

    # This script's own command line is `xm_vllm_run.py`, which matches none of
    # the patterns, so there is no self-kill risk. The child it launches has not
    # started yet — reap always runs before the engine.
    for pattern in ORPHAN_PATTERNS:
        subprocess.run(["pkill", "-9", "-f", pattern], check=False)
    for path in Path("/dev/shm").glob("psm_*"):
        try:
            path.unlink()
        except OSError:
            pass
    time.sleep(5)


def free_vram_gib() -> list[float]:
    """Per-card free VRAM, so a capacity claim can prove it started clean."""
    try:
        out = subprocess.run(["rocm-smi", "--showmeminfo", "vram", "--json"],
                             capture_output=True, text=True, timeout=60).stdout
        data = json.loads(out)
        free = []
        for card in sorted(data):
            total = float(data[card]["VRAM Total Memory (B)"])
            used = float(data[card]["VRAM Total Used Memory (B)"])
            # This host also exposes a small integrated GPU. It is not a
            # tensor-parallel target and its 2 GiB would otherwise become the
            # minimum in every cleanliness check.
            if total / 2 ** 30 < 20.0:
                continue
            free.append(round((total - used) / 2 ** 30, 2))
        return free
    except Exception:                                   # noqa: BLE001
        return []


def run(command: list[str], log: Path) -> int:
    """Run a step, streaming to a log so a long generation is observable."""
    print("  $ " + " ".join(str(c) for c in command), flush=True)
    with log.open("a") as handle:
        completed = subprocess.run([str(c) for c in command], stdout=handle,
                                   stderr=subprocess.STDOUT)
    return completed.returncode


def main() -> int:
    from crossmodel import vllm_models

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True,
                        choices=list(vllm_models.CHECKPOINTS))
    parser.add_argument("--load", type=int, default=3, choices=[3, 5])
    parser.add_argument("--calibration", type=int, default=None,
                        help="Stage B pilot on N disjoint tasks")
    parser.add_argument("--max-model-len", type=int, default=None)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--generation-ceiling", type=int, default=8192)
    parser.add_argument("--chunk-size", type=int, default=32)
    parser.add_argument("--deadline-seconds", type=float, default=None)
    parser.add_argument("--cpu-offload-gb", type=float, default=0.0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    tag = args.model.split("/")[-1].replace(".", "")
    kind = "calib" if args.calibration else "main"
    out_dir = Path(args.out or
                   f"runs/xmv_{kind}_{tag}_k{args.load}_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "run.log"

    plan_command = [sys.executable, HERE / "xm_vllm_plan.py",
                    "--model", args.model, "--load", str(args.load),
                    "--out", str(out_dir),
                    "--gpu-memory-utilization",
                    str(args.gpu_memory_utilization),
                    "--generation-ceiling", str(args.generation_ceiling),
                    "--chunk-size", str(args.chunk_size),
                    "--cpu-offload-gb", str(args.cpu_offload_gb)]
    if args.deadline_seconds:
        plan_command += ["--deadline-seconds", str(args.deadline_seconds)]
    if args.max_model_len:
        plan_command += ["--max-model-len", str(args.max_model_len)]
    if args.calibration:
        plan_command += ["--tasks-override", str(args.calibration)]
    print("STEP 1/3 — plan", flush=True)
    if run(plan_command, log):
        print("  plan failed; see " + str(log))
        return 2
    plan = json.loads((out_dir / "plan.json").read_text())
    print(f"  {plan['model_id']} @ {plan['model_revision'][:12]} "
          f"k={plan['load']} rows={plan['expected_rows']} "
          f"{plan['reasoning_mode']} "
          f"budget={plan['generation_ceiling']}/request", flush=True)

    # An engine killed mid-run leaves worker processes holding VRAM and shared
    # memory segments behind. The next launch then fails to allocate and looks
    # like a capacity limit of the model, which it is not. Reap before every
    # launch so a memory result is a result about the model.
    reap()
    free = free_vram_gib()
    print(f"  free VRAM after reap: {free} GiB", flush=True)
    (out_dir / "free_vram_before_engine.json").write_text(json.dumps({
        "free_gib_per_card": free,
        "reaped_patterns": list(ORPHAN_PATTERNS)}, indent=1))
    if free and min(free) < 20.0:
        # Not fatal — the run proceeds and records it — but a memory result
        # obtained on a dirty card is not a fact about the checkpoint.
        print(f"  WARNING: a card has only {min(free):.2f} GiB free before the "
              "engine starts; any capacity result here is NOT attributable to "
              "the model", flush=True)

    print(f"STEP 2/3 — generate (vLLM TP={plan['tensor_parallel_size']})",
          flush=True)
    generate_command = [BACKEND_PYTHON, BACKEND_SCRIPT,
                        "--plan", out_dir / "plan.json",
                        "--design", out_dir / "design.jsonl",
                        "--out", out_dir / "raw_generations.jsonl"]
    code = run(generate_command, log)
    if not (out_dir / "raw_generations.jsonl").exists():
        print(f"  GENERATION FAILED (exit {code}); see {log}")
        return 3
    if code:
        print(f"  generation returned {code} (ceiling hits) — continuing")

    print("STEP 3/3 — ingest", flush=True)
    if run([sys.executable, HERE / "xm_vllm_ingest.py", str(out_dir)], log):
        print("  ingest failed; see " + str(log))
        return 4

    tail = log.read_text().splitlines()[-12:]
    print("\n".join("  " + line for line in tail))
    print(f"\n  {out_dir}/generations.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
