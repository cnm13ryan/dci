"""Experiment 1: does the phenomenon survive correct decoder seeds?

Reports, for each order and budget, the arm-level A-failure rates that everything
else is built from, then tau, then Delta, then the four arbitration outcomes --
in that order, so no contrast is read without the rates that produced it.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram as A

pd.set_option("display.width", 250)
SCORED = Path(sys.argv[1])
frame = pd.read_json(SCORED, lines=True)
ORDERS = list(sys.argv[2].split(",")) if len(sys.argv) > 2 else ["QAC", "ACQ"]
BUDGETS = sorted(frame["reasoning_budget"].unique())
clusters = A.Clusters(sorted(frame["task_id"].unique()), key=f"exp1|{SCORED.name}")

print("## Arm-level A-failure rates (the quantities tau is a difference of)\n")
rates = frame.groupby(["order", "background_name", "reasoning_budget", "arm"])[
    "A_failure"].mean().unstack("arm")
rates["tau (unpaired check)"] = rates[A.FOCAL_ARM] - rates[A.REFERENCE_ARM]
print(rates.to_string(float_format=lambda v: f"{v:.3f}"))

print("\n\n## tau(B->A), paired within task\n")
rows = []
for order in ORDERS:
    for budget in BUDGETS:
        for background in (A.CONTROL, A.AMPLIFIER):
            rows.append((f"tau  {order}  {A.BACKGROUND_LABEL[background]:<11} b={budget}",
                         A.tau(frame, background=background, order=order,
                               reasoning_budget=budget)))
print(A.show(A.table(clusters, rows)))

print("\n\n## Delta = tau(semicolon) - tau(parentheses), paired within task\n")
rows = [(f"Delta  {order}  b={budget}",
         A.delta(frame, order=order, reasoning_budget=budget))
        for order in ORDERS for budget in BUDGETS]
rows += [(f"Gamma  {order} (b={BUDGETS[-1]} minus b={BUDGETS[0]})",
          A.gamma(frame, order=order, low=BUDGETS[0], high=BUDGETS[-1]))
         for order in ORDERS]
print(A.show(A.table(clusters, rows)))

print("\n\n## Arbitration in the focal arm: joint improvement or a change of priority?\n")
rows = []
for order in ORDERS:
    for background in (A.CONTROL, A.AMPLIFIER):
        for budget in BUDGETS:
            states = A.arbitration(frame, order=order, background=background,
                                   reasoning_budget=budget)
            for state in A.STATES:
                rows.append((f"{order} {A.BACKGROUND_LABEL[background]:<11} "
                             f"b={budget:<5} {state}", states[state]))
print(A.show(A.table(clusters, rows), float_format=lambda v: f"{v:.3f}"))

print("\n\n## The same table as a crosstab, for reading the shift at a glance\n")
focal = A.behavioural(frame)
focal = focal[focal["arm"] == A.FOCAL_ARM]
print(pd.crosstab([focal["order"], focal["background_name"],
                   focal["reasoning_budget"]], focal["arbitration_state"],
                  normalize="index").to_string(float_format=lambda v: f"{v:.3f}"))
