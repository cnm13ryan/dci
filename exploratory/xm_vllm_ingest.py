"""Turn raw vLLM output into canonical cross-model rows.

Runs in the SCIENTIFIC environment. The backend environment cannot import
`crossmodel.schema` (different torch, no `dci`), so it writes a minimal raw
record per row; this script joins that against the design and the plan and
rebuilds the canonical row through `crossmodel.schema.build_row`.

That keeps `schema.py` the single authority on what a stored row is, so the
vLLM rows and the earlier Transformers rows are the same shape and the same
analysis reads both without special-casing.

    uv run python xm_vllm_ingest.py runs/XMV_DIR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, seeds
from crossmodel.adapters.base import Generation, GenerationConfig
from crossmodel.schema import assert_provenance, build_row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir")
    parser.add_argument("--raw", default="raw_generations.jsonl")
    parser.add_argument("--out", default="generations.jsonl")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    plan = json.loads((run_dir / "plan.json").read_text())
    design = {json.loads(l)["row_id"]: json.loads(l)
              for l in (run_dir / "design.jsonl").open()}
    raw = [json.loads(l) for l in (run_dir / args.raw).open()]
    engine_path = run_dir / (Path(args.raw).stem + "_engine.json")
    engine = json.loads(engine_path.read_text()) if engine_path.exists() else {}

    config = GenerationConfig(
        reasoning_mode=plan["reasoning_mode"],
        max_answer_tokens=plan["answer_tokens"],
        temperature=plan["temperature"], top_p=plan["top_p"],
        top_k=plan["top_k"],
        max_reasoning_tokens=plan["engineering_ceiling"])

    metadata = {
        "model_id": plan["model_id"],
        "model_revision": plan["model_revision"],
        "model_family": plan["model_family"],
        "backend": "vllm",
        "backend_version": engine.get("vllm_version", "unknown"),
        "dtype": plan["dtype"],
        "quantization": plan["quantization"],
        # The device layout IS the point of this retry, so it is spelled out
        # in every row rather than left to a run-level file.
        "device_configuration":
            f"tensor_parallel_size={plan['tensor_parallel_size']}"
            f" (cuda:0+cuda:1)",
        "chat_template_identifier":
            f"vllm.apply_chat_template({plan['chat_template_kwargs']})",
        "chat_template_sha256": "",
    }
    control = (f"chat_template({plan['chat_template_kwargs']}) · parser="
               f"{engine.get('reasoning_parser', plan.get('reasoning_parser'))}")

    records = []
    for item in raw:
        row = design[item["row_id"]]
        generation = Generation(
            prompt=item["rendered_prompt"],
            raw_generation=item["raw_generation"],
            reasoning_text=item["reasoning_text"],
            final_answer=item["final_answer"],
            reasoning_tokens=item["reasoning_tokens"],
            final_answer_tokens=item["final_answer_tokens"],
            finish_reason=item["finish_reason"],
            reasoning_emitted=item["reasoning_emitted"],
            natural_reasoning_closed=item["natural_reasoning_closed"],
            reasoning_cap_hit=item["reasoning_cap_hit"],
            answer_truncated=item["answer_truncated"],
            # No splice ran, so the forced-close artefact is structurally
            # impossible in this backend. Recorded as False, not omitted.
            forced_close_artefact=False,
            seed_reasoning=item["seed_reasoning"],
            seed_answer=row.get("answer_seed"),
            batch_seed=None,
            latency_seconds=engine.get("generation_seconds", 0.0)
            / max(len(raw), 1),
            technical_failure=item["technical_failure"],
            technical_failure_reason=item["technical_failure_reason"])
        records.append(build_row(
            run_id=run_dir.name, design_row=row, generation=generation,
            adapter_metadata=metadata, config=config,
            reasoning_control=control,
            scientific_seed=item["seed_reasoning"]))

    assert_provenance(records, expected_model=plan["model_id"],
                      expected_revision=plan["model_revision"])
    if len(records) != plan["expected_rows"]:
        raise SystemExit(
            f"ingested {len(records)} rows, plan expected "
            f"{plan['expected_rows']} — refusing to write an incomplete file")

    out = run_dir / args.out
    with out.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")

    audit = seeds.replicate_duplication(records)
    print(f"{plan['model_id']} k={plan['load']} · {len(records)} rows -> {out}")
    print(f"  backend {metadata['backend']} {metadata['backend_version']} · "
          f"{metadata['device_configuration']}")
    print(f"  cap hits {sum(1 for r in records if r['reasoning_cap_hit'])} · "
          f"empty {sum(1 for r in records if r['answer_empty'])} · "
          f"truncated {sum(1 for r in records if r['answer_truncated'])} · "
          f"failures {sum(1 for r in records if r['technical_failure'])}")
    print(f"  traces opened "
          f"{sum(1 for r in records if r['reasoning_emitted'])}/{len(records)} "
          f"· median reasoning "
          f"{sorted(r['reasoning_tokens'] for r in records)[len(records) // 2]}"
          f" · max {max(r['reasoning_tokens'] for r in records)}")
    print(f"  replicate duplication {audit['identical_pairs']}/"
          f"{audit['replicate_pairs']} = {audit['identical_rate']:.1%}"
          f"{'  <-- IMPLAUSIBLE' if audit['implausible'] else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
