"""Experiment 2: the six-order map, and whether a simple positional rule explains it.

Six permutations is a small number. Nothing here is fitted; each candidate rule
is a partition of the six orders into groups, and what is reported is the group
means and the gap between them. A rule that separates the orders will show a gap
that is large next to the spread within its own groups; one that does not, will
not. That is as far as six points can carry an explanation.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram as A

pd.set_option("display.width", 250)
SCORED = Path(sys.argv[1])
frame = pd.read_json(SCORED, lines=True)
ORDERS = list(A.__dict__.get("PERMUTATIONS", ("QAC", "QCA", "AQC", "ACQ", "CQA", "CAQ")))
ORDERS = [o for o in ORDERS if o in set(frame["order"])]
LOW, HIGH = sorted(frame["reasoning_budget"].unique())
clusters = A.Clusters(sorted(frame["task_id"].unique()), key=f"exp2|{SCORED.name}")

print("## Arm-level A-failure rates\n")
print(frame.groupby(["order", "background_name", "reasoning_budget", "arm"])[
    "A_failure"].mean().unstack("arm").to_string(float_format=lambda v: f"{v:.3f}"))

print("\n\n## Six-order summary\n")
rows = []
for order in ORDERS:
    d0 = clusters.interval(A.delta(frame, order=order, reasoning_budget=LOW))
    d1 = clusters.interval(A.delta(frame, order=order, reasoning_budget=HIGH))
    g = clusters.interval(A.gamma(frame, order=order, low=LOW, high=HIGH))
    rows.append({
        "order": order,
        "A_pos": order.index("A") + 1, "Q_pos": order.index("Q") + 1,
        "C_pos": order.index("C") + 1,
        f"Delta_b{LOW}": d0[0], f"b{LOW}_lo": d0[1], f"b{LOW}_hi": d0[2],
        f"Delta_b{HIGH}": d1[0], f"b{HIGH}_lo": d1[1], f"b{HIGH}_hi": d1[2],
        "Gamma": g[0], "G_lo": g[1], "G_hi": g[2]})
summary = pd.DataFrame(rows)
print(summary.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
summary.to_csv(SCORED.parent / "summary.csv", index=False)

print("\n\n## tau by order and background (what Delta is a difference of)\n")
taus = []
for order in ORDERS:
    for budget in (LOW, HIGH):
        for background in (A.CONTROL, A.AMPLIFIER):
            taus.append((f"{order} b={budget:<5} {A.BACKGROUND_LABEL[background]}",
                         A.tau(frame, background=background, order=order,
                               reasoning_budget=budget)))
print(A.show(A.table(clusters, taus)))

print("\n\n## Do simple positional rules separate the six orders?\n")
RULES = {
    "A first": lambda o: o[0] == "A",
    "A middle": lambda o: o[1] == "A",
    "A last": lambda o: o[2] == "A",
    "Q first": lambda o: o[0] == "Q",
    "Q middle": lambda o: o[1] == "Q",
    "Q last": lambda o: o[2] == "Q",
    "C first": lambda o: o[0] == "C",
    "C middle": lambda o: o[1] == "C",
    "C last": lambda o: o[2] == "C",
    "Q before A": lambda o: o.index("Q") < o.index("A"),
    "C before A": lambda o: o.index("C") < o.index("A"),
    "C adjacent to A": lambda o: abs(o.index("C") - o.index("A")) == 1,
    "C adjacent to Q": lambda o: abs(o.index("C") - o.index("Q")) == 1,
    "A adjacent to Q": lambda o: abs(o.index("A") - o.index("Q")) == 1,
}
out = []
for name, rule in RULES.items():
    hit = [o for o in ORDERS if rule(o)]
    miss = [o for o in ORDERS if not rule(o)]
    if not hit or not miss:
        continue
    for column in (f"Delta_b{LOW}", f"Delta_b{HIGH}", "Gamma"):
        values = summary.set_index("order")[column]
        out.append({"rule": name, "quantity": column,
                    "true_orders": " ".join(hit), "mean_true": values[hit].mean(),
                    "mean_false": values[miss].mean(),
                    "gap": values[hit].mean() - values[miss].mean(),
                    "within_spread": max(values[hit].max() - values[hit].min(),
                                         values[miss].max() - values[miss].min())})
rules = pd.DataFrame(out)
rules["separates"] = (rules["gap"].abs() > rules["within_spread"]).map(
    {True: "yes", False: "no"})
print(rules.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

print("\n\n## Diagnostic order, by the pre-registered rule\n")
print("  1. discard technically invalid orders  2. largest |Gamma|  "
      "3. tie-break largest |Delta_b{}|  4. tie-break alphabetical".format(HIGH))
ranked = summary.assign(absG=summary["Gamma"].abs(),
                        absD=summary[f"Delta_b{HIGH}"].abs()).sort_values(
    ["absG", "absD", "order"], ascending=[False, False, True])
print(ranked[["order", "absG", "absD"]].to_string(
    index=False, float_format=lambda v: f"{v:.3f}"))
print(f"\nDIAGNOSTIC ORDER = {ranked.iloc[0]['order']}")

print("\n\n## Arbitration across all six orders\n")
focal = A.behavioural(frame)
focal = focal[focal["arm"] == A.FOCAL_ARM]
print(pd.crosstab([focal["order"], focal["background_name"],
                   focal["reasoning_budget"]], focal["arbitration_state"],
                  normalize="index").to_string(float_format=lambda v: f"{v:.3f}"))
