"""Experiment 1 analysis: does a clause-boundary-capable mark interfere more?

Delta_boundary = tau(semicolon) - tau(non-boundary control), so a POSITIVE value
means the boundary-capable mark caused more focal-versus-reference interference
than the matched mark that cannot occupy a boundary. The headline is the value at
b = 4096.

The primary estimate is never conditioned on whether the background instruction
was actually complied with; that is a post-treatment property of the answer. A
compliant-only column is printed at the end, labelled, for diagnosis only.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram as A

pd.set_option("display.width", 250)
SCORED = Path(sys.argv[1])
BOUNDARY = "X_SEMICOLON_FREE"
NON_BOUNDARY = sys.argv[2] if len(sys.argv) > 2 else "X_DEGREE_FREE"

frame = pd.read_json(SCORED, lines=True)
BUDGETS = sorted(frame["reasoning_budget"].unique())
ORDER = frame["order"].iloc[0]
clusters = A.Clusters(sorted(frame["task_id"].unique()), key=f"boundary|{SCORED.name}")
PAIR = dict(amplifier=BOUNDARY, control=NON_BOUNDARY)
LABEL = {BOUNDARY: "semicolon (boundary-capable)",
         NON_BOUNDARY: f"{A.BACKGROUND_LABEL[NON_BOUNDARY]} (non-boundary)"}

print(f"## Per-cell diagnostics — {len(frame)} generations, order {ORDER}\n")
cells = frame.groupby(["background_name", "reasoning_budget", "arm"]).agg(
    n=("A_pass", "size"),
    A_failure=("A_failure", "mean"), A_pass=("A_pass", "mean"),
    arm_constraint_pass=("Q_pass", "mean"),
    background_compliance=("background_pass", "mean"),
    joint=("A_pass", "mean"), sentences=("sentence_count", "mean"),
    words=("word_count", "mean"), answer_tokens=("final_tokens", "mean"),
    reasoning_M=("reasoning_tokens", "mean"), truncated=("truncated", "mean"),
    leaked=("scratchpad_leakage", "mean"),
    technical_failure=("technical_failure", "mean"))
frame["all_three"] = (frame["A_pass"] * frame["Q_pass"]
                      * frame["background_pass"])
cells["joint_all_three"] = frame.groupby(
    ["background_name", "reasoning_budget", "arm"])["all_three"].mean()
print(cells.to_string(float_format=lambda v: f"{v:.3f}"))

print("\n\n## tau(B->A), paired within task\n")
rows = []
for background in (NON_BOUNDARY, BOUNDARY):
    for budget in BUDGETS:
        rows.append((f"tau  {LABEL[background]:<30} b={budget}",
                     A.tau(frame, background=background, order=ORDER,
                           reasoning_budget=budget)))
print(A.show(A.table(clusters, rows)))

print("\n\n## Delta_boundary = tau(semicolon) - tau(non-boundary)\n")
rows = [(f"Delta_boundary  b={budget}",
         A.delta(frame, order=ORDER, reasoning_budget=budget, **PAIR))
        for budget in BUDGETS]
rows.append((f"Gamma (b={BUDGETS[-1]} minus b={BUDGETS[0]})",
             A.gamma(frame, order=ORDER, low=BUDGETS[0], high=BUDGETS[-1], **PAIR)))
print(A.show(A.table(clusters, rows)))
print(f"\n  HEADLINE: Delta_boundary at b = {BUDGETS[-1]}")

print("\n\n## Four-state decomposition, focal arm\n")
rows = []
for background in (NON_BOUNDARY, BOUNDARY):
    for budget in BUDGETS:
        states = A.arbitration(frame, background=background,
                               reasoning_budget=budget)
        for state in A.STATES:
            rows.append((f"{A.BACKGROUND_LABEL[background]:<10} b={budget:<5} "
                         f"{state}", states[state]))
print(A.show(A.table(clusters, rows), float_format=lambda v: f"{v:.3f}"))

print("\n\n## Task-level heterogeneity\n")
for budget in BUDGETS:
    d = A.delta(frame, order=ORDER, reasoning_budget=budget, **PAIR)
    total = d.sum()
    ranked = d.reindex(d.abs().sort_values(ascending=False).index)
    share = abs(ranked.iloc[:3].sum() / total) if total else float("nan")
    print(f"  b={budget:<5} mean {d.mean():+.3f}  "
          f"tasks non-zero {(d != 0).sum()}/{len(d)}  "
          f"positive {(d > 0).sum()}  negative {(d < 0).sum()}  "
          f"top-3 share of total {share:.2f}")

print("\n## Replicate-specific signs\n")
for budget in BUDGETS:
    per = []
    for replicate in sorted(frame["replicate_id"].unique()):
        d = A.delta(frame[frame["replicate_id"] == replicate], order=ORDER,
                    reasoning_budget=budget, **PAIR)
        per.append(d.mean() if not d.empty else float("nan"))
    print(f"  b={budget:<5} " + "  ".join(f"r{i}={v:+.3f}" for i, v in enumerate(per))
          + f"   spread {max(per) - min(per):.3f}")

print("\n\n## Symbol placement, descriptive only\n")
# `splice_count` is the repository's own audited proxy for "this mark is standing
# where a sentence boundary could stand" -- a shape test on the following
# segment, revised after a human audit in Round 7. It is the mechanism variable,
# measured on both marks with the same code, and it is DESCRIPTIVE: it is a
# property of the produced text, so nothing above is conditioned on it.
from dci_exploratory.extensions import (MARK_IS_BOUNDARY_CAPABLE,  # noqa: E402
                                        splice_count)

CHAR = {BOUNDARY: ";", "X_DEGREE_FREE": "\u00b0", "X_ASTERISK_FREE": "*"}
MARK_NAME = {BOUNDARY: "semicolon", "X_DEGREE_FREE": "degree",
             "X_ASTERISK_FREE": "asterisk"}
placement = frame[frame["background_pass"] == 1].copy()
placement["mark_name"] = placement["background"].map(MARK_NAME)
placement["boundary_capable"] = placement["mark_name"].map(MARK_IS_BOUNDARY_CAPABLE)
placement["splices"] = [splice_count(t or "", m) for t, m
                        in zip(placement["raw_final_answer"], placement["mark_name"])]
placement["stands_at_a_boundary"] = (placement["splices"] > 0).astype(float)
placement["relative_position"] = [
    (t.find(CHAR[b]) / len(t)) if t and CHAR[b] in t else float("nan")
    for t, b in zip(placement["raw_final_answer"].fillna(""), placement["background"])]
print("rows where the background was actually produced:")
print(placement.groupby(["background_name", "reasoning_budget", "arm"]).agg(
    n=("splices", "size"),
    boundary_capable=("boundary_capable", "first"),
    stands_at_a_boundary=("stands_at_a_boundary", "mean"),
    mean_relative_position=("relative_position", "mean"),
    sentences=("sentence_count", "mean")).to_string(float_format=lambda v: f"{v:.3f}"))
print("\n  `stands_at_a_boundary` is splice_count > 0: the mark is followed by a")
print("  clause-initial word or by a segment long enough to be a clause. It is a")
print("  proxy, and it is reported, never conditioned on.")

print("\n\n## DESCRIPTIVE ONLY — compliant-background rows\n")
print("background_pass is post-treatment; this cannot replace the estimate above.")
kept = frame[frame["background_pass"] == 1]
print(f"retains {len(kept)} of {len(frame)} rows = {len(kept) / len(frame):.3f}")
sub = A.Clusters(sorted(kept["task_id"].unique()), key="boundary-compliant")
rows = [(f"Delta_boundary (compliant only)  b={budget}",
         A.delta(kept, order=ORDER, reasoning_budget=budget, **PAIR))
        for budget in BUDGETS]
print(A.show(A.table(sub, rows)))
