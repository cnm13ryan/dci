"""Forensics on an existing run: no generation, no model, no new sampling.

Three jobs, in the order they must be done:

1. `circularity_audit` — establish how much of the collapse/failure association
   is DEFINITIONAL. A is "exactly N sentences" and collapse is "<= 2 sentences",
   so collapse is a strict SUBSET of A-failure and a high correlation between
   the two is partly guaranteed. Any mechanistic reading has to survive this.

2. `failure_taxonomy` — partition failures by what the answer actually looked
   like, so "arms differ in total failure" can be separated from "arms differ in
   which failure mode they take".

3. `matched_forensics` — task-level comparison across arms and orders: overlap of
   failure sets, per-task susceptibility, replicate repeatability, and the
   transitions caused by reversing instruction order alone.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

# Where the semicolon sits relative to sentence boundaries is the whole question
# for S_SEMICOLON, so structural features are computed from the raw text rather
# than inferred from the verifier's summary.
def structural_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Per-row structure: observed segments, punctuation, chaining."""
    out = frame.copy()
    out["observed_sentences"] = out["verifier_detail"].apply(
        lambda d: d.get("observed") if isinstance(d, dict) else None)
    text = out["response"].fillna("")
    out["n_semicolons"] = text.str.count(";")
    out["n_colons"] = text.str.count(":")
    out["n_commas"] = text.str.count(",")
    out["n_periods"] = text.str.count(r"\.")
    out["n_newlines"] = text.str.count("\n")
    out["n_bullets"] = text.str.count(r"(?m)^\s*(?:[-*•]|\d{1,2}[.)])\s+")
    out["ends_with_terminator"] = text.str.rstrip().str.endswith((".", "!", "?"))
    return out


def circularity_audit(frame: pd.DataFrame, n_target: int) -> dict[str, Any]:
    """How much of the collapse<->failure association is definitional?

    Reports the containment explicitly rather than leaving a reader to infer it
    from a correlation coefficient.
    """
    contrast = structural_features(
        frame[frame["condition"].isin(["focal", "reference"])])
    scorable = contrast[contrast["scorable"]].copy()
    scorable["collapse"] = scorable["observed_sentences"] <= 2
    scorable["failure"] = scorable["a_failure"] == 1

    # The structural facts, stated as facts.
    collapse_and_pass = int((scorable["collapse"] & ~scorable["failure"]).sum())
    report: dict[str, Any] = {
        "n_target_sentences": n_target,
        "collapse_definition": "observed_sentences <= 2",
        "failure_definition": f"observed_sentences != {n_target}",
        "collapse_is_subset_of_failure": collapse_and_pass == 0,
        "n_collapse_without_failure": collapse_and_pass,
        "note": ("collapse is a STRICT SUBSET of A-failure by construction, so a "
                 "high cell-level correlation between the two is partly "
                 "guaranteed. The non-definitional content is whether the "
                 "NON-collapse part of failure is arm-independent."),
    }

    rows = []
    for (order, arm), group in scorable.groupby(["order", "arm"]):
        failures = group[group["failure"]]
        n = len(group)
        rows.append({
            "order": order, "arm": arm, "n": n,
            "P_failure": float(group["failure"].mean()),
            # P(collapse | failure) — of the failures, how many are collapses
            "P_collapse_given_failure": (float(failures["collapse"].mean())
                                         if len(failures) else np.nan),
            "n_failures": int(len(failures)),
            "n_collapse_failures": int(failures["collapse"].sum()),
            # The quantity that is NOT definitional: failure that is not collapse
            "P_failure_and_not_collapse": float(
                (group["failure"] & ~group["collapse"]).mean()),
            "n_failure_not_collapse": int((group["failure"] & ~group["collapse"]).sum()),
        })
    report["by_arm_order"] = rows

    non_collapse = pd.DataFrame(rows)["P_failure_and_not_collapse"]
    report["non_collapse_failure_spread"] = {
        "min": float(non_collapse.min()), "max": float(non_collapse.max()),
        "range": float(non_collapse.max() - non_collapse.min()),
        "mean": float(non_collapse.mean()),
        "interpretation": (
            "If this range is small relative to the spread in P_failure, the "
            "between-arm differences live in the collapse mode specifically, "
            "which is a real decomposition. It is still NOT evidence that "
            "collapse is causally upstream of failure."),
    }
    spread_failure = pd.DataFrame(rows)["P_failure"]
    report["failure_spread"] = {
        "min": float(spread_failure.min()), "max": float(spread_failure.max()),
        "range": float(spread_failure.max() - spread_failure.min()),
    }
    return report


# --------------------------------------------------------------- taxonomy
def classify_failure(row: pd.Series, n_target: int) -> str:
    """What the answer actually looked like when it failed A."""
    observed = row["observed_sentences"]
    if observed is None or (isinstance(observed, float) and np.isnan(observed)):
        return "unscorable"
    observed = int(observed)
    if observed == n_target:
        return "pass"
    if observed == 1:
        return ("one_sentence_semicolon_chain" if row["n_semicolons"] >= 1
                else "one_sentence_no_semicolon")
    if observed == 2:
        return "two_sentences"
    if observed == 3:
        return "three_sentences"
    if observed > n_target:
        return f"more_than_{n_target}_sentences"
    return "other_under_target"


def failure_taxonomy(frame: pd.DataFrame, n_target: int) -> pd.DataFrame:
    contrast = structural_features(
        frame[frame["condition"].isin(["focal", "reference"])])
    scorable = contrast[contrast["scorable"]].copy()
    scorable["mode"] = scorable.apply(classify_failure, axis=1, n_target=n_target)
    table = (scorable.groupby(["order", "arm", "mode"]).size()
             .unstack("mode", fill_value=0))
    return table


def sentence_count_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    contrast = structural_features(
        frame[frame["condition"].isin(["focal", "reference"])])
    scorable = contrast[contrast["scorable"]]
    return pd.crosstab([scorable["order"], scorable["arm"]],
                       scorable["observed_sentences"])


# -------------------------------------------------------- matched forensics
def per_unit_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per (task, order, replicate), one column per arm."""
    contrast = structural_features(
        frame[frame["condition"].isin(["focal", "reference"])])
    return contrast.pivot_table(
        index=["task_id", "order", "replicate"], columns="arm",
        values="a_failure", aggfunc="first")


def failure_set_overlap(frame: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    """Jaccard overlap of failure sets between arms, on shared units.

    Compared against the overlap expected if the two arms failed independently
    at their observed rates — otherwise a high Jaccard between two high-failure
    arms reads as agreement when it is just arithmetic.
    """
    units = per_unit_outcomes(frame)
    rows = []
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            both = units[[a, b]].dropna()
            fa, fb = both[a] == 1, both[b] == 1
            intersection = int((fa & fb).sum())
            union = int((fa | fb).sum())
            jaccard = intersection / union if union else np.nan
            pa, pb = float(fa.mean()), float(fb.mean())
            # Expected Jaccard under independence at the same marginal rates
            exp_i, exp_u = pa * pb, pa + pb - pa * pb
            rows.append({
                "arm_a": a, "arm_b": b, "n_units": len(both),
                "rate_a": pa, "rate_b": pb,
                "n_both_fail": intersection, "n_either_fails": union,
                "jaccard": jaccard,
                "jaccard_if_independent": exp_i / exp_u if exp_u else np.nan,
                "excess_over_independence": (jaccard - exp_i / exp_u) if exp_u else np.nan,
                # Containment: of a's failures, how many are also b's failures
                "P_b_fails_given_a_fails": float(fb[fa].mean()) if fa.sum() else np.nan,
                "P_a_fails_given_b_fails": float(fa[fb].mean()) if fb.sum() else np.nan,
            })
    return pd.DataFrame(rows)


def task_susceptibility(frame: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    """Per-task failure rate in each arm, plus how concentrated failures are."""
    units = per_unit_outcomes(frame).reset_index()
    table = units.groupby("task_id")[arms].mean()
    table["mean_across_arms"] = table[arms].mean(axis=1)
    return table.sort_values("mean_across_arms", ascending=False)


def concentration(frame: pd.DataFrame, arms: list[str]) -> dict[str, Any]:
    """Are failures concentrated in a few tasks, or spread evenly?"""
    units = per_unit_outcomes(frame).reset_index()
    out = {}
    for arm in arms:
        per_task = units.groupby("task_id")[arm].sum().sort_values(ascending=False)
        total = float(per_task.sum())
        if total == 0:
            out[arm] = {"total_failures": 0}
            continue
        n_tasks = len(per_task)
        top_quarter = max(1, n_tasks // 4)
        out[arm] = {
            "total_failures": total,
            "n_tasks_with_any_failure": int((per_task > 0).sum()),
            "n_tasks": n_tasks,
            "share_from_top_quarter_of_tasks": float(
                per_task.head(top_quarter).sum() / total),
            "share_if_uniform": top_quarter / n_tasks,
        }
    return out


def replicate_repeatability(frame: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    """Within (task, order, arm), do the replicates agree?

    All-or-nothing agreement means the outcome is a property of the task; mixed
    replicates mean it is a coin flip the instruction biases.
    """
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    scorable = contrast[contrast["scorable"]]
    rows = []
    for (arm, order), group in scorable.groupby(["arm", "order"]):
        per_cell = group.groupby("task_id")["a_failure"].agg(["mean", "count"])
        per_cell = per_cell[per_cell["count"] > 1]
        rows.append({
            "arm": arm, "order": order, "n_cells": len(per_cell),
            "share_unanimous_pass": float((per_cell["mean"] == 0).mean()),
            "share_unanimous_fail": float((per_cell["mean"] == 1).mean()),
            "share_mixed": float(((per_cell["mean"] > 0)
                                  & (per_cell["mean"] < 1)).mean()),
        })
    return pd.DataFrame(rows)


def order_transitions(frame: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    """Per (task, replicate, arm): outcome under o_A vs o_Q.

    Instruction order is the ONLY thing that differs between the two prompts, so
    a flip here is caused by position and nothing else.
    """
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    scorable = contrast[contrast["scorable"]]
    wide = scorable.pivot_table(index=["arm", "task_id", "replicate"],
                                columns="order", values="a_failure",
                                aggfunc="first").dropna()
    rows = []
    for arm, group in wide.groupby(level="arm"):
        rows.append({
            "arm": arm, "n_units": len(group),
            "pass_pass": int(((group["o_A"] == 0) & (group["o_Q"] == 0)).sum()),
            "pass_to_fail": int(((group["o_A"] == 0) & (group["o_Q"] == 1)).sum()),
            "fail_to_pass": int(((group["o_A"] == 1) & (group["o_Q"] == 0)).sum()),
            "fail_fail": int(((group["o_A"] == 1) & (group["o_Q"] == 1)).sum()),
            "net_o_Q_minus_o_A": float(group["o_Q"].mean() - group["o_A"].mean()),
        })
    return pd.DataFrame(rows)


def run(run_dir: Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    frame = pd.read_json(run_dir / "generations.jsonl", lines=True)
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    n_target = int(config["harvest_provenance"]["exact_sentence_count"])
    arms = [config["selection"]["focal"], *config["selection"]["references"]]

    out = run_dir / "forensics"
    out.mkdir(parents=True, exist_ok=True)

    audit = circularity_audit(frame, n_target)
    (out / "circularity_audit.json").write_text(json.dumps(audit, indent=2),
                                                encoding="utf-8")
    taxonomy = failure_taxonomy(frame, n_target)
    taxonomy.to_csv(out / "failure_taxonomy.csv")
    counts = sentence_count_distribution(frame)
    counts.to_csv(out / "sentence_count_distribution.csv")
    overlap = failure_set_overlap(frame, arms)
    overlap.to_csv(out / "failure_set_overlap.csv", index=False)
    susceptibility = task_susceptibility(frame, arms)
    susceptibility.to_csv(out / "task_susceptibility.csv")
    repeat = replicate_repeatability(frame, arms)
    repeat.to_csv(out / "replicate_repeatability.csv", index=False)
    transitions = order_transitions(frame, arms)
    transitions.to_csv(out / "order_transitions.csv", index=False)
    conc = concentration(frame, arms)
    (out / "concentration.json").write_text(json.dumps(conc, indent=2),
                                            encoding="utf-8")

    return {"dir": str(out), "audit": audit, "taxonomy": taxonomy,
            "counts": counts, "overlap": overlap,
            "susceptibility": susceptibility, "repeatability": repeat,
            "transitions": transitions, "concentration": conc, "arms": arms}


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Forensics on an existing run.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    result = run(args.run_dir)
    pd.set_option("display.width", 220)

    audit = result["audit"]
    print("\n=== 1. COLLAPSE CIRCULARITY AUDIT ===")
    print(f"A-failure  := observed != {audit['n_target_sentences']}")
    print(f"collapse   := {audit['collapse_definition']}")
    print(f"collapse is a strict SUBSET of A-failure: {audit['collapse_is_subset_of_failure']} "
          f"(collapse-but-passing rows: {audit['n_collapse_without_failure']})")
    print(pd.DataFrame(audit["by_arm_order"]).round(4).to_string(index=False))
    print(f"\nP(failure) spread across cells      : "
          f"{audit['failure_spread']['range']:.4f}")
    print(f"P(failure & NOT collapse) spread    : "
          f"{audit['non_collapse_failure_spread']['range']:.4f} "
          f"(mean {audit['non_collapse_failure_spread']['mean']:.4f})")

    print("\n=== 2. FAILURE TAXONOMY (counts of 60 per cell) ===")
    print(result["taxonomy"].to_string())
    print("\n=== observed sentence-count distribution ===")
    print(result["counts"].to_string())

    print("\n=== 3. FAILURE-SET OVERLAP BETWEEN ARMS ===")
    print(result["overlap"].round(4).to_string(index=False))
    print("\n=== concentration of failures across tasks ===")
    print(json.dumps(result["concentration"], indent=2))
    print("\n=== replicate repeatability ===")
    print(result["repeatability"].round(3).to_string(index=False))
    print("\n=== 5. ORDER TRANSITIONS (o_A -> o_Q, same task/replicate) ===")
    print(result["transitions"].round(4).to_string(index=False))
    print(f"\nartifacts: {result['dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
