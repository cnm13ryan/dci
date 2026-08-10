"""Human-readable behavioural audit export.

The metric can only say a verdict changed. Whether the change *looks like* B
interfering with A — rather than a verifier artefact, an ambiguous task, a
truncation, or a prompt-construction bug — is a question only reading the raw
outputs can answer. This module makes that reading possible without a notebook.

It writes:
  * audit_cases.jsonl  — every field for every inspected case, machine-readable
  * audit_cases.md     — the same cases laid out for a person to read
  * audit_sample.json  — how the sample was drawn, so it is not cherry-picked
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from dci_exploratory.analysis import load_run, paired_units

# The strata the task requires. Each answers a different question, and drawing
# only from the dramatic ones would make the audit an illustration rather than
# evidence.
STRATA = (
    "random_focal",
    "random_reference",
    "focal_failed_A",
    "reference_passed_A_where_focal_failed",
    "focal_passed_A_where_reference_failed",
    "unusual_verifier_outcome",
    "truncated",
)


def _rows_for(frame: pd.DataFrame, config: dict[str, Any], rng) -> dict[str, list[str]]:
    focal_id = config["selection"]["focal"]
    references = config["selection"]["references"]
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    focal = contrast[contrast["arm"] == focal_id]
    reference = contrast[contrast["condition"] == "reference"]

    def sample(pool: pd.DataFrame, k: int) -> list[str]:
        ids = sorted(pool["row_id"].tolist())
        if not ids:
            return []
        k = min(k, len(ids))
        return sorted(rng.choice(ids, size=k, replace=False).tolist())

    picks: dict[str, list[str]] = {
        "random_focal": sample(focal, 6),
        "random_reference": sample(reference, 6),
        "focal_failed_A": sample(focal[focal["a_failure"] == 1], 6),
        # Rows the verifier could not score, or that failed technically — the
        # places a verifier artefact hides. Drawn from the WHOLE frame, not just
        # the contrast: a primitive row that came back unscorable says something
        # about the verifier whichever condition it sat in.
        "unusual_verifier_outcome": sample(
            frame[(~frame["scorable"])
                  | (frame["verifier_status"] == "unscorable")
                  | (frame["technical_failure"])], 6),
        "truncated": sample(frame[frame["output_truncated"].fillna(False)], 4),
    }

    # Discordant matched pairs: the units that actually move tau.
    focal_wins, reference_wins = [], []
    for ref in references:
        paired = paired_units(frame, focal_id, ref)
        if paired.empty:
            continue
        worse = paired[(paired["a_failure_focal"] == 1) & (paired["a_failure_reference"] == 0)]
        better = paired[(paired["a_failure_focal"] == 0) & (paired["a_failure_reference"] == 1)]
        focal_wins += worse["row_id_focal"].tolist() + worse["row_id_reference"].tolist()
        reference_wins += better["row_id_focal"].tolist() + better["row_id_reference"].tolist()
    picks["reference_passed_A_where_focal_failed"] = sample(
        contrast[contrast["row_id"].isin(set(focal_wins))], 10)
    picks["focal_passed_A_where_reference_failed"] = sample(
        contrast[contrast["row_id"].isin(set(reference_wins))], 8)
    return picks


def export(run_dir: Path, seed: int = 20260810) -> dict[str, Any]:
    run_dir = Path(run_dir)
    frame, config = load_run(run_dir)
    rng = np.random.default_rng(seed)
    out = run_dir / "audit"
    out.mkdir(parents=True, exist_ok=True)

    picks = _rows_for(frame, config, rng)
    strata_of: dict[str, list[str]] = {}
    for stratum, ids in picks.items():
        for row_id in ids:
            strata_of.setdefault(row_id, []).append(stratum)

    indexed = frame.set_index("row_id")
    cases = []
    for row_id, strata in sorted(strata_of.items()):
        row = indexed.loc[row_id]
        cases.append({
            "row_id": row_id,
            "strata": strata,
            "task_id": row["task_id"],
            "topic": row["topic"],
            "condition": row["condition"],
            "arm": row["arm"],
            "reference_identity": row["arm"] if row["condition"] == "reference" else None,
            "order": row["order"],
            "load": int(row["load"]),
            "replicate": int(row["replicate"]),
            "pair_key": row["pair_key"],
            "measured_constraint": row["measured"],
            "target_instruction": row["instructions"][
                list(row["ordered_ids"]).index(row["measured"])]
            if row["measured"] in list(row["ordered_ids"]) else None,
            "arm_instruction": row["instructions"][list(row["ordered_ids"]).index(row["arm"])],
            "background_instructions": [
                instruction for cid, instruction
                in zip(row["ordered_ids"], row["instructions"])
                if cid in set(config["selection"]["background"])],
            "ordered_constraint_ids": list(row["ordered_ids"]),
            "all_instructions": list(row["instructions"]),
            "system_message": row["system_message"],
            "user_prompt": row["user_prompt"],
            "rendered_prompt": row["rendered_prompt"],
            "response": row["response"],
            "verifier_status": row["verifier_status"],
            "verifier_binary_pass": (None if pd.isna(row["verifier_binary_pass"])
                                     else int(row["verifier_binary_pass"])),
            "verifier_continuous_score": (None if pd.isna(row["verifier_continuous_score"])
                                          else float(row["verifier_continuous_score"])),
            "verifier_detail": row["verifier_detail"],
            "a_failure": None if pd.isna(row["a_failure"]) else int(row["a_failure"]),
            "scorable": bool(row["scorable"]),
            "technical_failure": bool(row["technical_failure"]),
            "error": row["error"],
            "generated_token_count": (None if pd.isna(row["generated_token_count"])
                                      else int(row["generated_token_count"])),
            "output_truncated": bool(row["output_truncated"]) if not pd.isna(
                row["output_truncated"]) else None,
            "stop_reason": row["stop_reason"],
            "batch_seed": int(row["batch_seed"]),
            # Left blank on purpose: filled in by a person, so verifier/human
            # disagreement is recorded rather than assumed away.
            "human_verdict": "",
            "human_note": "",
        })

    (out / "audit_cases.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    (out / "audit_sample.json").write_text(json.dumps({
        "seed": seed,
        "strata_definition": {
            "random_focal": "uniform sample of A+B rows",
            "random_reference": "uniform sample of A+C_j rows",
            "focal_failed_A": "A+B rows the verifier scored as failing A",
            "reference_passed_A_where_focal_failed": "both rows of matched pairs where "
                                                     "B failed A and the reference passed",
            "focal_passed_A_where_reference_failed": "both rows of matched pairs where "
                                                     "B passed A and the reference failed",
            "unusual_verifier_outcome": "unscorable, technical failure, or no verdict",
            "truncated": "generation hit the output cap without EOS",
        },
        "counts": {k: len(v) for k, v in picks.items()},
        "n_unique_cases": len(cases),
        "row_ids": {k: v for k, v in picks.items()},
    }, indent=2), encoding="utf-8")

    (out / "audit_cases.md").write_text(_markdown(cases, config), encoding="utf-8")
    return {"n_cases": len(cases), "dir": str(out),
            "counts": {k: len(v) for k, v in picks.items()}}


def _markdown(cases: list[dict[str, Any]], config: dict[str, Any]) -> str:
    sel = config["selection"]
    lines = [
        "# Behavioural audit — exploratory DCI probe",
        "",
        f"- model: `{config['model']['model_id']}` @ `{config['model']['revision']}`",
        f"- target A = `{sel['target']}`, focal B = `{sel['focal']}`",
        f"- references = {', '.join(f'`{r}`' for r in sel['references'])}",
        f"- background S = {', '.join(f'`{b}`' for b in sel['background'])}",
        f"- load k = {config['load']}, {config['n_tasks']} tasks, "
        f"{config['replicates']} replicates, orders {config['orders']}",
        "",
        "`human_verdict` and `human_note` are blank in the export and are filled in "
        "by a reader. Disagreement between the verifier and the reader is the point "
        "of this artifact, so it is recorded rather than resolved silently.",
        "",
    ]
    for case in cases:
        lines += [
            "---",
            "",
            f"## `{case['row_id']}` — {case['condition']} / arm `{case['arm']}` "
            f"/ order `{case['order']}`",
            "",
            f"- strata: {', '.join(case['strata'])}",
            f"- task `{case['task_id']}`: {case['topic']}",
            f"- pair key: `{case['pair_key']}`",
            f"- measured: `{case['measured_constraint']}` — {case['target_instruction']}",
            f"- arm instruction: {case['arm_instruction']}",
            f"- verifier: **{case['verifier_status']}** "
            f"(binary_pass={case['verifier_binary_pass']}, "
            f"score={case['verifier_continuous_score']}) → a_failure={case['a_failure']}",
            f"- verifier detail: `{json.dumps(case['verifier_detail'])}`",
            f"- generated tokens: {case['generated_token_count']} "
            f"(stop `{case['stop_reason']}`, truncated={case['output_truncated']})",
            "",
            "### Prompt",
            "",
            "```",
            case["user_prompt"] or "",
            "```",
            "",
            "### Response",
            "",
            "```",
            case["response"] or "<no output>",
            "```",
            "",
            f"- human_verdict: {case['human_verdict'] or '_(to fill)_'}",
            f"- human_note: {case['human_note'] or '_(to fill)_'}",
            "",
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Export the manual audit artifact.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--seed", type=int, default=20260810)
    args = parser.parse_args(argv)
    print(json.dumps(export(args.run_dir, seed=args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
