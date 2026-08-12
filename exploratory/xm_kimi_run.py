"""Drive one Kimi-VL DCI slice end to end: plan, generate, ingest.

Three steps in two interpreters, exactly like `xm_vllm_run.py`. The plan and the
ingest run here, in the scientific environment; the generation runs in
`.venv-kimi`, which carries transformers 4.50.3 — the version the checkpoint's
own `config.json` declares — so no compatibility shim is needed. See
`KIMI_ENVIRONMENT.md`.

The scientific contract is the repository's, not a Kimi-specific one: the design
comes from `crossmodel.runner.build_design`, the seeds from `crossmodel.seeds`,
and the stored rows from `crossmodel.schema` via the shared ingest. Kimi's rows
therefore have the same shape and the same provenance fields as every other
checkpoint's, and the analysis reads them without special-casing.

    uv run python xm_kimi_run.py --load 3 --rows 24 --out runs/PILOT   # pilot
    uv run python xm_kimi_run.py --load 3 --out runs/MAIN              # all 160
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

from crossmodel import contract, runlock, runner, seeds

MODEL_ID = "moonshotai/Kimi-VL-A3B-Thinking-2506"
BACKEND_PYTHON = HERE / ".venv-kimi" / "bin" / "python"
BACKEND_SCRIPT = HERE / "crossmodel" / "kimi_hf_backend.py"

#: The validated stack from KIMI_ENVIRONMENT.md. Changing any of these means the
#: run is no longer the one that passed qualification.
VALIDATED = {"transformers": "4.50.3", "max_memory_per_gpu": "19GiB",
             "device_map": "auto", "dtype": "bfloat16", "quantization": "none"}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run(command: list[str], log: Path) -> int:
    print("  $ " + " ".join(str(c) for c in command), flush=True)
    with log.open("a") as handle:
        completed = subprocess.run([str(c) for c in command], stdout=handle,
                                   stderr=subprocess.STDOUT)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", type=int, default=contract.LOAD,
                        choices=[3, 5])
    parser.add_argument("--rows", type=int, default=None,
                        help="pilot on the first N rows of the frozen design; "
                             "omit for the full slice")
    parser.add_argument("--device-map", default=VALIDATED["device_map"])
    parser.add_argument("--max-memory-per-gpu",
                        default=VALIDATED["max_memory_per_gpu"])
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--chunk-size", type=int, default=16)
    parser.add_argument("--generation-ceiling", type=int, default=8192)
    parser.add_argument("--deadline-seconds", type=float, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if not BACKEND_PYTHON.exists():
        print(f"{BACKEND_PYTHON} is missing. Rebuild it from "
              "kimi-env.lock.txt; see KIMI_ENVIRONMENT.md.")
        return 2

    kind = "pilot" if args.rows else "main"
    out_dir = Path(args.out or
                   f"runs/xmk_{kind}_k{args.load}_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "run.log"

    with runlock.RunLock(out_dir, MODEL_ID,
                         run_kind=f"kimi_transformers_k{args.load}_{kind}",
                         gpus=args.device_map,
                         allow_resume=args.resume) as lock:
        from dci_exploratory import extensions, harvest

        extensions.register()
        state = harvest.load()

        stage = ("XM_cross_model" if args.load == contract.LOAD
                 else f"XM_cross_model_k{args.load}")
        design = runner.build_design(state, stage=stage, load=args.load)
        if args.rows:
            # A pilot takes a PREFIX of the canonical row_id ordering, which is
            # a hash of design identity. It is therefore a fixed, reproducible
            # subset rather than a convenience sample, and the rows it covers
            # are the same rows the full run will produce.
            design = design[:args.rows]

        from huggingface_hub.constants import HF_HUB_CACHE

        folder = (Path(HF_HUB_CACHE)
                  / ("models--" + MODEL_ID.replace("/", "--")) / "snapshots")
        snapshots = [p.name for p in folder.iterdir()
                     if p.is_dir() and len(p.name) == 40]
        if len(snapshots) != 1:
            raise RuntimeError(
                f"{MODEL_ID}: cannot pin an exact revision ({len(snapshots)} "
                "cached snapshots); a mutable alias is not a revision")
        revision = snapshots[0]
        lock.revision = revision
        lock._write_manifest(state="running")
        declared = json.loads(
            (folder / revision / "config.json").read_text()
        ).get("transformers_version")

        print("STEP 1/3 — plan", flush=True)
        design_path = out_dir / "design.jsonl"
        with design_path.open("w") as handle:
            for row in design:
                handle.write(json.dumps({
                    "row_id": row.row_id, "task_id": row.task_id,
                    "replicate": row.replicate, "arm": row.arm,
                    "variant": row.variant, "order": row.order,
                    "measured": row.measured, "load": row.load,
                    "paraphrase_id": row.paraphrase_id,
                    "pair_key": row.pair_key, "condition": row.condition,
                    "topic": row.topic,
                    "ordered_ids": list(row.ordered_ids),
                    "user_prompt": row.user_prompt,
                    "system_message": state.SYSTEM_MESSAGE,
                    "scientific_seed": seeds.seed_for_row(
                        row, contract.MASTER_SEED, seeds.REASONING_PHASE),
                    "answer_seed": seeds.seed_for_row(
                        row, contract.MASTER_SEED, seeds.ANSWER_PHASE),
                }) + "\n")

        audit = seeds.assert_seed_regime(design, contract.MASTER_SEED)
        plan = {
            "stamp": "EXPLORATORY_NO_EVIDENCE",
            "created_utc": utc_stamp(),
            "experiment": "ACTUAL_CROSS_MODEL_DCI",
            "stage": stage,
            "model_id": MODEL_ID, "model_revision": revision,
            "model_family": "kimi-vl",
            "checkpoint_transformers_version": declared,
            "backend": "transformers",
            "backend_version": VALIDATED["transformers"],
            "device_map": args.device_map,
            "max_memory_per_gpu": args.max_memory_per_gpu,
            "device_configuration":
                f"device_map={args.device_map} "
                f"max_memory={args.max_memory_per_gpu}/gpu (cuda:0+cuda:1)",
            "dtype": VALIDATED["dtype"],
            "quantization": VALIDATED["quantization"],
            "batch_size": args.batch_size, "chunk_size": args.chunk_size,
            "deadline_seconds": args.deadline_seconds,
            "generation_ceiling": args.generation_ceiling,
            "engineering_ceiling": args.generation_ceiling
            - contract.ANSWER_TOKENS,
            "answer_tokens": contract.ANSWER_TOKENS,
            "temperature": contract.TEMPERATURE, "top_p": contract.TOP_P,
            "top_k": contract.TOP_K,
            "reasoning_mode":
                contract.ReasoningMode.THINKING_ENABLED_BOUNDED,
            # The template takes no reasoning argument: this checkpoint always
            # thinks, and its non-thinking sibling is a different checkpoint.
            "chat_template_kwargs": {},
            "reasoning_parser": "delimiters(◁think▷ … ◁/think▷)",
            "think_open": "◁think▷", "think_close": "◁/think▷",
            "load": args.load, "expected_rows": len(design),
            "pilot_rows": args.rows,
            "seed_audit": audit,
            "contract": contract.as_dict(state),
            "free_vram_at_lock": lock.free_vram_at_start,
        }
        (out_dir / "plan.json").write_text(json.dumps(plan, indent=1))
        print(f"  {MODEL_ID} @ {revision[:12]} k={args.load} "
              f"rows={len(design)} {plan['reasoning_mode']} "
              f"budget={args.generation_ceiling}/request", flush=True)
        print(f"  checkpoint declares transformers {declared}; backend runs "
              f"{VALIDATED['transformers']} — no shims", flush=True)

        print("STEP 2/3 — generate (transformers 4.50.3, .venv-kimi)",
              flush=True)
        raw_path = out_dir / "raw_generations.jsonl"
        raw_path.unlink(missing_ok=True)
        code = run([BACKEND_PYTHON, "-u", BACKEND_SCRIPT,
                    "--plan", out_dir / "plan.json",
                    "--design", design_path, "--out", raw_path], log)
        written = sum(1 for _ in raw_path.open()) if raw_path.exists() else 0
        if not written:
            print(f"  GENERATION FAILED (exit {code}, 0 rows); see {log}")
            return 3
        if code:
            print(f"  generation returned {code} — continuing to ingest")

        print("STEP 3/3 — ingest", flush=True)
        if run([sys.executable, HERE / "xm_vllm_ingest.py", str(out_dir)], log):
            print("  ingest failed; see " + str(log))
            return 4

        print("\n".join("  " + line
                        for line in log.read_text().splitlines()[-14:]))
        print(f"\n  {out_dir}/generations.jsonl")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
