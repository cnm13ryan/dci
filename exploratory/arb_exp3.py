"""Experiment 3: does an explicit priority cue change which instruction survives?

A and B are jointly satisfiable, so the ideal answer is still "both" under every
priority condition. The question is what happens on the failures. Four patterns
are distinguishable from the same table, and the script reports which one the
data show rather than testing only for the interesting one:

  arbitration       reversing the priority moves probability between "target
                    only" and "focal only" -- Psi is clearly positive;
  general assistance  every priority wording mainly raises "both", in the same
                    direction regardless of which instruction it names;
  null              the wording moves nothing;
  cue-induced damage  adding a priority rule lowers compliance overall.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram as A

pd.set_option("display.width", 250)
SCORED = Path(sys.argv[1])
frame = pd.read_json(SCORED, lines=True)
BUDGETS = sorted(frame["reasoning_budget"].unique())
PRIORITIES = ["equal", "a_over_b", "b_over_a"]
clusters = A.Clusters(sorted(frame["task_id"].unique()), key=f"exp3|{SCORED.name}")

print("## Compliance, and whether the cue itself was followed\n")
print(frame.groupby(["priority", "background_name", "reasoning_budget"]).agg(
    n=("A_pass", "size"), A=("A_pass", "mean"), B=("Q_pass", "mean"),
    C=("background_pass", "mean"), sentences=("sentence_count", "mean"),
    words=("word_count", "mean"), leaked=("scratchpad_leakage", "mean"),
    truncated=("truncated", "mean")).to_string(float_format=lambda v: f"{v:.3f}"))

print("\n\n## The four outcomes\n")
rows = []
for priority in PRIORITIES:
    for background in (A.CONTROL, A.AMPLIFIER):
        for budget in BUDGETS:
            states = A.arbitration(frame, priority=priority, background=background,
                                   reasoning_budget=budget)
            for state in A.STATES:
                rows.append((f"{priority:<9} {A.BACKGROUND_LABEL[background]:<11} "
                             f"b={budget:<5} {state}", states[state]))
print(A.show(A.table(clusters, rows), float_format=lambda v: f"{v:.3f}"))

print("\n\n## S = P(target only) - P(focal only): which instruction survives\n")
rows = []
for priority in PRIORITIES:
    for background in (A.CONTROL, A.AMPLIFIER):
        for budget in BUDGETS:
            rows.append((f"S  {priority:<9} {A.BACKGROUND_LABEL[background]:<11} "
                         f"b={budget}",
                         A.survival(frame, priority=priority, background=background,
                                    reasoning_budget=budget)))
print(A.show(A.table(clusters, rows)))

print("\n\n## Psi = S(A over B) - S(B over A): the direct arbitration test\n")
rows = []
for background in (A.CONTROL, A.AMPLIFIER):
    for budget in BUDGETS:
        common = dict(background=background, reasoning_budget=budget)
        s_ab = A.survival(frame, priority="a_over_b", **common)
        s_ba = A.survival(frame, priority="b_over_a", **common)
        s_eq = A.survival(frame, priority="equal", **common)
        label = f"{A.BACKGROUND_LABEL[background]:<11} b={budget}"
        rows.append((f"Psi          {label}", (s_ab - s_ba).dropna()))
        rows.append((f"A>B - equal  {label}", (s_ab - s_eq).dropna()))
        rows.append((f"B>A - equal  {label}", (s_ba - s_eq).dropna()))
print(A.show(A.table(clusters, rows)))

print("\n\n## Does the cue mainly raise 'both' instead? (general-assistance test)\n")
rows = []
for background in (A.CONTROL, A.AMPLIFIER):
    for budget in BUDGETS:
        common = dict(background=background, reasoning_budget=budget)
        both = {p: A.arbitration(frame, priority=p, **common)["both"]
                for p in PRIORITIES}
        label = f"{A.BACKGROUND_LABEL[background]:<11} b={budget}"
        rows.append((f"both A>B - equal  {label}",
                     (both["a_over_b"] - both["equal"]).dropna()))
        rows.append((f"both B>A - equal  {label}",
                     (both["b_over_a"] - both["equal"]).dropna()))
print(A.show(A.table(clusters, rows)))

print("\n\n## Crosstab\n")
states = A.behavioural(frame)
print(pd.crosstab([states["background_name"], states["reasoning_budget"],
                   states["priority"]], states["arbitration_state"],
                  normalize="index").to_string(float_format=lambda v: f"{v:.3f}"))
