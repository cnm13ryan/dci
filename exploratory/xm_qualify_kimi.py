"""Drive the Kimi-VL qualification ladder in the checkpoint's own environment.

Design in, report out, across a venv boundary — the same pattern the vLLM path
uses. The scientific environment builds the design and reads the result; the
generation happens in `.venv-kimi`, which carries transformers 4.50.3, the
version `config.json` declares. That is what makes the run shim-free: all three
patches the 5.15.0 environment needed are unnecessary on the published version,
and the backend checks and records that rather than assuming it.

    uv run python xm_qualify_kimi.py --max-memory-per-gpu 17GiB --batch-size 2
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
BACKEND_SCRIPT = HERE / "crossmodel" / "kimi_qualify_backend.py"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--max-memory-per-gpu", default="17GiB")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--generation-ceiling", type=int, default=8192)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    if not BACKEND_PYTHON.exists():
        print(f"{BACKEND_PYTHON} does not exist. Create it with the ROCm torch "
              "wheel and transformers==4.50.3 before running this.")
        return 2

    out_dir = Path(args.out or f"runs/xmq_kimi_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    with runlock.RunLock(out_dir, MODEL_ID, run_kind="qualification_kimi_hf",
                         gpus=args.device_map) as lock:
        from dci_exploratory import extensions, harvest

        extensions.register()
        state = harvest.load()
        design = runner.build_design(state, stage="XM_cross_model",
                                     load=contract.LOAD)[:args.rows]

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

        design_path = out_dir / "design.jsonl"
        with design_path.open("w") as handle:
            for row in design:
                handle.write(json.dumps({
                    "row_id": row.row_id, "task_id": row.task_id,
                    "replicate": row.replicate, "arm": row.arm,
                    "variant": row.variant, "order": row.order,
                    "user_prompt": row.user_prompt,
                    "system_message": state.SYSTEM_MESSAGE,
                    "scientific_seed": seeds.seed_for_row(
                        row, contract.MASTER_SEED, seeds.REASONING_PHASE),
                }) + "\n")

        plan = {
            "stamp": "EXPLORATORY_NO_EVIDENCE",
            "model_id": MODEL_ID, "model_revision": revision,
            "checkpoint_transformers_version": declared,
            "device_map": args.device_map,
            "max_memory_per_gpu": args.max_memory_per_gpu,
            "batch_size": args.batch_size,
            "qualify_rows": args.rows,
            "dtype": "bfloat16", "quantization": "none",
            "generation_ceiling": args.generation_ceiling,
            "answer_tokens": contract.ANSWER_TOKENS,
            "temperature": contract.TEMPERATURE, "top_p": contract.TOP_P,
            "top_k": contract.TOP_K,
            "reasoning_mode":
                contract.ReasoningMode.THINKING_ENABLED_BOUNDED,
            "free_vram_at_lock": lock.free_vram_at_start,
        }
        (out_dir / "plan.json").write_text(json.dumps(plan, indent=1))
        print(f"{MODEL_ID} @ {revision}")
        print(f"  checkpoint declares transformers {declared}")
        print(f"  {len(design)} design rows, batch {args.batch_size}, "
              f"ceiling {args.generation_ceiling}")

        completed = subprocess.run(
            [str(BACKEND_PYTHON), "-u", str(BACKEND_SCRIPT),
             "--plan", str(out_dir / "plan.json"),
             "--design", str(design_path),
             "--out", str(out_dir / "qualification.json")],
            cwd=HERE)
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
