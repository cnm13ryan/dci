"""The full sanity-check list, run over every dataset in the programme.

Each check is printed with the number it produced, not just a verdict, so a
reader can disagree with the threshold and still see the evidence.
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram as A

pd.set_option("display.width", 240)
RUN = Path(sys.argv[1])
DATASETS = [
    ("Experiment 1 (QAC, ACQ)", RUN / "priority0" / "scored_generations.jsonl"),
    ("Experiment 2 (all six orders)", RUN / "order_map" / "all_orders_scored.jsonl"),
    ("Experiment 3 (priority)", RUN / "priority_intervention" / "main" / "scored_generations.jsonl"),
    ("Experiment 4 (SmolLM3-3B)", RUN / "cross_model" / "main" / "scored_generations.jsonl"),
]


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


for name, path in DATASETS:
    if not path.exists():
        print(f"\n[skip] {name}: {path} missing")
        continue
    frame = pd.read_json(path, lines=True)
    rule(f"{name} — {len(frame)} rows — {path.name}")

    print("\n-- request seeds --")
    per_unit = frame.groupby(["task_id", "replicate_id"])["actual_request_seed"].nunique()
    per_task = frame.groupby("task_id")["actual_request_seed"].nunique()
    print(f"  distinct answer seeds per (task, replicate): "
          f"{set(per_unit.unique())}  (must be {{1}})")
    print(f"  distinct answer seeds per task: {sorted(set(per_task.unique()))}  "
          f"(must equal the replicate count)")
    if "reasoning_request_seed" in frame:
        thinking = frame[frame["reasoning_budget"] > 0]
        overlap = (thinking["reasoning_request_seed"]
                   == thinking["actual_request_seed"]).sum()
        print(f"  rows reusing the thinking seed for the answer: {overlap} (must be 0)")

    print("\n-- fixed final-answer budget --")
    print(f"  answer_token_budget values: {sorted(frame['answer_token_budget'].unique())}")
    print(f"  max observed final_tokens: {frame['final_tokens'].max()}")

    print("\n-- reasoning condition --")
    print(frame.groupby("reasoning_budget").agg(
        native_nonthinking=("native_nonthinking", "mean"),
        cap_hit=("reasoning_cap_hit", "mean"),
        realised_M=("reasoning_tokens", "mean"),
        M_max=("reasoning_tokens", "max")).to_string(float_format=lambda v: f"{v:.3f}"))

    print("\n-- truncation, technical failure, leakage --")
    print(f"  truncated {frame['truncated'].mean():.4f}  "
          f"technical_failure {frame['technical_failure'].mean():.4f}  "
          f"scratchpad_leakage {frame['scratchpad_leakage'].mean():.4f}")

    print("\n-- floor and ceiling on each constraint --")
    group = ["reasoning_budget", "order", "background_name", "arm"]
    if "priority" in frame:
        group = ["reasoning_budget", "background_name", "priority"]
    compliance = frame.groupby(group)[["A_pass", "Q_pass", "background_pass"]].mean()
    for column in ("A_pass", "Q_pass", "background_pass"):
        values = compliance[column]
        flags = []
        if values.max() >= 0.98:
            flags.append(f"CEILING in {(values >= 0.98).sum()} cells")
        if values.min() <= 0.02:
            flags.append(f"FLOOR in {(values <= 0.02).sum()} cells")
        print(f"  {column:16s} min {values.min():.3f}  max {values.max():.3f}"
              + ("   " + ", ".join(flags) if flags else ""))

    print("\n-- baseline movement: A-failure in the REFERENCE arm --")
    if "priority" in frame:
        print("  n/a: the priority experiment has no reference arm by design")
    else:
        reference = frame[frame["arm"] == A.REFERENCE_ARM].groupby(
            ["order", "background_name", "reasoning_budget"])["A_failure"].mean()
        print(f"  min {reference.min():.3f}  max {reference.max():.3f}")
        if reference.max() > 0.15:
            print("  NOTE: the reference arm moves; tau is not carried by the focal "
                  "arm alone in every cell")

    print("\n-- response length --")
    print(frame.groupby(["reasoning_budget", "background_name"])[
        ["sentence_count", "word_count", "final_tokens"]].mean().to_string(
        float_format=lambda v: f"{v:.1f}"))

    if "priority" in frame:
        continue

    print("\n-- task concentration: is Delta carried by a few tasks? --")
    for order in sorted(frame["order"].unique()):
        for budget in sorted(frame["reasoning_budget"].unique()):
            delta = A.delta(frame, order=order, reasoning_budget=budget)
            if delta.empty:
                continue
            total = delta.sum()
            ranked = delta.reindex(delta.abs().sort_values(ascending=False).index)
            share = abs(ranked.iloc[:3].sum() / total) if total else np.nan
            nonzero = int((delta != 0).sum())
            print(f"  {order} b={budget:<5} mean {delta.mean():+.3f}  "
                  f"tasks contributing non-zero {nonzero}/{len(delta)}  "
                  f"top-3 share of the total {share:.2f}")

    print("\n-- seed concentration: does one replicate drive it? --")
    for order in sorted(frame["order"].unique()):
        for budget in sorted(frame["reasoning_budget"].unique()):
            by_replicate = []
            for replicate in sorted(frame["replicate_id"].unique()):
                subset = frame[frame["replicate_id"] == replicate]
                delta = A.delta(subset, order=order, reasoning_budget=budget)
                by_replicate.append(delta.mean() if not delta.empty else np.nan)
            values = np.array(by_replicate, float)
            print(f"  {order} b={budget:<5} per-replicate Delta "
                  + " ".join(f"{v:+.3f}" for v in values)
                  + f"   spread {np.nanmax(values) - np.nanmin(values):.3f}")

rule("cross-dataset: are the four datasets built from the same prompts?")
exp1 = pd.read_json(DATASETS[0][1], lines=True)
xmodel = pd.read_json(DATASETS[3][1], lines=True) if DATASETS[3][1].exists() else None
if xmodel is not None:
    key = ["task_id", "arm", "background", "order", "replicate_id"]
    left = exp1.drop_duplicates(key).set_index(key)["user_prompt"]
    right = xmodel.drop_duplicates(key).set_index(key)["user_prompt"]
    shared = left.index.intersection(right.index)
    mismatch = (left.loc[shared] != right.loc[shared]).sum()
    print(f"  Experiment 1 and Experiment 4 share {len(shared)} design cells; "
          f"{mismatch} prompt mismatches (must be 0)")
print("\ndone")
