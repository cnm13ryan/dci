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
    parser.add_argument("--resume", action="store_true",
                        help="permit writing into a directory that already "
                             "holds output")
    args = parser.parse_args()

    tag = args.model.split("/")[-1].replace(".", "")
    kind = "calib" if args.calibration else "main"
    out_dir = Path(args.out or
                   f"runs/xmv_{kind}_{tag}_k{args.load}_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    from crossmodel import runlock

    # Exclusive ownership for the whole run — plan, generate and ingest. The
    # engine is a CHILD of this process, so the lock's cleanup reaches it on
    # SIGINT, SIGTERM and on any exception, which is what stops a killed run
    # from leaving workers holding VRAM.
    with runlock.RunLock(out_dir, args.model,
                         run_kind=f"vllm_tp2_k{args.load}",
                         gpus="tensor_parallel_size=2 (cuda:0+cuda:1)",
                         allow_resume=args.resume) as lock:
        return _drive(args, out_dir, lock)


def _drive(args, out_dir: Path, lock) -> int:
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
    lock.revision = plan["model_revision"]
    lock._write_manifest(state="running")
    print(f"  {plan['model_id']} @ {plan['model_revision'][:12]} "
          f"k={plan['load']} rows={plan['expected_rows']} "
          f"{plan['reasoning_mode']} "
          f"budget={plan['generation_ceiling']}/request", flush=True)

    # The lock already reaped orphans and recorded free VRAM at acquisition.
    # Re-read it here so the number sits beside the engine that used it, and so
    # a capacity result can prove what the cards held when it was measured.
    from crossmodel import runlock

    free = runlock.free_vram_gib()
    print(f"  free VRAM before engine: {free} GiB", flush=True)
    (out_dir / "free_vram_before_engine.json").write_text(json.dumps({
        "free_gib_per_card": free,
        "free_gib_at_lock_acquisition": lock.free_vram_at_start,
        "orphans_reaped_at_start": lock.orphans_reaped,
        "host_memory_gib": runlock.host_memory_gib()}, indent=1))
    if free and min(free) < 20.0:
        # Not fatal — the run proceeds and records it — but a memory result
        # obtained on a dirty card is not a fact about the checkpoint.
        print(f"  WARNING: a card has only {min(free):.2f} GiB free before the "
              "engine starts; any capacity result here is NOT attributable to "
              "the model", flush=True)

    print(f"STEP 2/3 — generate (vLLM TP={plan['tensor_parallel_size']})",
          flush=True)
    # A previous attempt in this directory may have left a raw file behind —
    # possibly an EMPTY one, since the backend truncates it before the first
    # chunk. Testing only for existence would let that stale file stand in for
    # this run's output and send a failed generation on to the ingest, which
    # then reports a confusing provenance error instead of the real failure.
    raw_path = out_dir / "raw_generations.jsonl"
    raw_path.unlink(missing_ok=True)

    generate_command = [BACKEND_PYTHON, BACKEND_SCRIPT,
                        "--plan", out_dir / "plan.json",
                        "--design", out_dir / "design.jsonl",
                        "--out", raw_path]
    code = run(generate_command, log)
    rows_written = (sum(1 for _ in raw_path.open())
                    if raw_path.exists() else 0)
    if not rows_written:
        print(f"  GENERATION FAILED (exit {code}, {rows_written} rows); "
              f"see {log}")
        return 3
    if rows_written < plan["expected_rows"]:
        print(f"  PARTIAL GENERATION: {rows_written}/{plan['expected_rows']} "
              "rows — ingesting what exists")
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
