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
from crossmodel.schema import assert_provenance, build_row, final_answer_status
from vllm_backend.contract import NON_BEHAVIOURAL, Outcome, canonicalise_row



def scored_failure_flags(outcome: Outcome) -> tuple[bool, bool]:
    """`(not_generated, technical_failure)` for the scored row.

    A NAMED function because it is the whole boundary between the backend's
    outcome taxonomy and the two booleans the scored-row schema carries, and it
    was previously three inline expressions that disagreed with the taxonomy.

    `contract.NON_BEHAVIOURAL` is the declaration; this projects it, it does not
    restate it. NOT_GENERATED has its own downstream state (an unattempted row
    is not a failed one), so it is separated out; every other non-behavioural
    outcome is an apparatus failure and must reach `final_answer_status` as
    TECHNICAL_FAILURE. Reaching it as NO_FINAL_WITHIN_BUDGET instead -- which is
    what happened to BACKEND_UNSUPPORTED, CAPACITY_EXCEEDED and CHANNEL_INVALID
    -- scores an engine that never served the checkpoint as the model failing
    the constraint.
    """
    if outcome not in NON_BEHAVIOURAL:
        return False, False
    if outcome is Outcome.NOT_GENERATED:
        return True, False
    return False, True


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
    # ONE migration boundary, at the point of reading immutable archived
    # rows. Everything below this line reads canonical names only.
    raw = [canonicalise_row(json.loads(l))
           for l in (run_dir / args.raw).open()]
    engine_path = run_dir / (Path(args.raw).stem + "_engine.json")
    engine = json.loads(engine_path.read_text()) if engine_path.exists() else {}

    config = GenerationConfig(
        reasoning_mode=plan["reasoning_mode"],
        max_answer_tokens=plan["answer_tokens"],
        temperature=plan["temperature"], top_p=plan["top_p"],
        top_k=plan["top_k"],
        max_reasoning_tokens=plan["engineering_ceiling"])

    # Backend-agnostic: the plan says which backend produced these rows. It
    # defaults to vLLM because that is what this script was written for, but
    # Kimi-VL generates through Transformers 4.50.3 in its own environment and
    # its rows must land in the SAME canonical schema, or the analysis would
    # have to special-case one checkpoint.
    backend = plan.get("backend", "vllm")
    device_configuration = plan.get("device_configuration") or (
        f"tensor_parallel_size={plan.get('tensor_parallel_size')}"
        f" (cuda:0+cuda:1)")
    metadata = {
        "model_id": plan["model_id"],
        "model_revision": plan["model_revision"],
        "model_family": plan["model_family"],
        "backend": backend,
        "backend_version": (plan.get("backend_version")
                            or engine.get("backend_version")
                            or engine.get("vllm_version", "unknown")),
        "dtype": plan["dtype"],
        "quantization": plan["quantization"],
        # The device layout IS the point of this retry, so it is spelled out
        # in every row rather than left to a run-level file.
        "device_configuration": device_configuration,
        "chat_template_identifier":
            f"{backend}.apply_chat_template({plan['chat_template_kwargs']})",
        "chat_template_sha256": "",
    }
    control = (f"chat_template({plan['chat_template_kwargs']}) · parser="
               f"{engine.get('reasoning_parser', plan.get('reasoning_parser'))}")

    records = []
    for item in raw:
        row = design[item["row_id"]]
        outcome = Outcome(item["outcome"])
        not_generated, apparatus_failure = scored_failure_flags(outcome)
        generation = Generation(
            prompt=item["rendered_prompt"],
            raw_generation=item["raw_generation"],
            reasoning_text=item["reasoning_text"],
            final_answer=item["final_answer"],
            reasoning_tokens=item["reasoning_tokens"],
            final_answer_tokens=item["final_answer_tokens"],
            finish_reason=item["finish_reason"],
            reasoning_emitted=item["reasoning_emitted"],
            natural_reasoning_closed=item["reasoning_closed"],
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
            # Every NON-BEHAVIOURAL outcome, not just TECHNICAL_FAILURE.
            # `contract.NON_BEHAVIOURAL` is the taxonomy's own declaration of
            # which outcomes must never be scored as behaviour; this used to
            # re-derive that classification by hand and got three of five
            # wrong. BACKEND_UNSUPPORTED, CAPACITY_EXCEEDED and CHANNEL_INVALID
            # set neither boolean, so `final_answer_status` fell through to
            # NO_FINAL_WITHIN_BUDGET -- a BEHAVIOURAL state -- and an engine
            # that could not serve the checkpoint at all was scored as the
            # model failing the constraint. CHANNEL_INVALID exists verbatim
            # "so the cell is not read as 'the model answered badly'".
            technical_failure=apparatus_failure,
            technical_failure_reason=(
                f'{item["outcome"]}: {item["outcome_detail"]}'
                if apparatus_failure else ""))
        record = build_row(
            run_id=run_dir.name, design_row=row, generation=generation,
            adapter_metadata=metadata, config=config,
            reasoning_control=control,
            scientific_seed=item["seed_reasoning"])
        # The scored-row schema keeps these as booleans because the Transformers
        # adapters also feed it. Derived HERE, once, from the outcome -- not
        # read back out of the row under their old names.
        # The canonical outcome, retained verbatim: the booleans below are a
        # lossy projection of it, and an audit needs the original.
        record["backend_outcome"] = item["outcome"]
        record["backend_outcome_detail"] = item["outcome_detail"]
        not_generated = outcome is Outcome.NOT_GENERATED
        record["not_generated"] = not_generated
        record["not_generated_reason"] = item["outcome_detail"] if not_generated else ""
        record["generation_ceiling"] = plan.get("generation_ceiling")
        record["final_answer_status"] = final_answer_status(record)
        records.append(record)

    assert_provenance(records, expected_model=plan["model_id"],
                      expected_revision=plan["model_revision"])
    # Duplicate row ids are the fingerprint of two writers on one file. The
    # count alone can look right while the contents do not.
    from crossmodel.runlock import assert_unique_rows

    integrity = assert_unique_rows(records, expected=plan["expected_rows"])
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
    states = {}
    for record in records:
        states[record["final_answer_status"]] = \
            states.get(record["final_answer_status"], 0) + 1
    print("  final answer status " + ", ".join(
        f"{k} {v}" for k, v in sorted(states.items())))
    print(f"  integrity {integrity}")
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
