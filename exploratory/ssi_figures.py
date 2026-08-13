"""The manipulation figure.

The directive's primary figure has two panels: the interference contrast and the
manipulation. Only the manipulation panel has data, because the manipulation gate
failed and the main experiment was not run. Rather than draw an empty outcome
panel, the figure shows what was actually measured and says plainly where the
missing panel would have gone.

Every value is recomputed from the scored rows; the numbers drawn are written
beside the figure as a CSV.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import plotstyle

RUN = Path(sys.argv[1])
FIGURES = RUN / "figures"
DATA = FIGURES / "data"
DATA.mkdir(parents=True, exist_ok=True)

ROUTE_COLOUR = {"off_route": plotstyle.SLOT[1], "anti_splice": plotstyle.SLOT[2]}
ROUTE_LABEL = {"off_route": "off-route control\n(\"no exclamation marks\")",
               "anti_splice": "anti-splice\n(\"no semicolon joining two sentences\")"}

frame = pd.read_json(RUN / "manipulation_preflight" / "scored_generations.jsonl",
                     lines=True)
budgets = sorted(frame["reasoning_budget"].unique())
routes = ["off_route", "anti_splice"]

rows = []
for route in routes:
    for budget in budgets:
        cell = frame[(frame["route"] == route) & (frame["reasoning_budget"] == budget)]
        compliant = cell[cell["semicolon_compliant"] == 1]
        rows.append({
            "route": route, "reasoning_budget": budget, "n": len(cell),
            "semicolon_compliance": cell["semicolon_compliant"].mean(),
            "P_spliced": cell["spliced"].mean(),
            "P_spliced_given_compliant": (compliant["spliced"].mean()
                                          if len(compliant) else np.nan),
            "route_instruction_compliance": cell["route_pass"].mean(),
            "n_compliant": len(compliant)})
table = pd.DataFrame(rows)

fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.3))
panels = [
    ("semicolon_compliance", "Did the required semicolon survive?",
     "share of answers with exactly one semicolon"),
    ("P_spliced_given_compliant", "Did the splicing stop?",
     "share of semicolon-compliant answers\nwith splice_count > 0"),
    ("route_instruction_compliance", "Was the fourth instruction obeyed?",
     "share of answers passing the D instruction"),
]
positions = np.arange(len(budgets))
for ax, (column, title, ylabel) in zip(axes, panels):
    for offset, route in ((-0.19, "off_route"), (0.19, "anti_splice")):
        cell = table[table["route"] == route].set_index("reasoning_budget").loc[budgets]
        ax.bar(positions + offset, cell[column], 0.36, color=ROUTE_COLOUR[route],
               label=ROUTE_LABEL[route].replace("\n", " "), zorder=3)
        for x, v in zip(positions + offset, cell[column]):
            ax.annotate(f"{v:.2f}", (x, v), xytext=(0, 5),
                        textcoords="offset points", ha="center", fontsize=9,
                        color=plotstyle.INK)
    ax.set_xticks(positions)
    ax.set_xticklabels(["no reasoning\n(native)", "high reasoning\n(b = 4096)"],
                       fontsize=9)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, loc="left", fontsize=10.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e6e6e2", zorder=0)
axes[1].axhline(0.25, color=plotstyle.MUTED, linestyle="--", linewidth=1, zorder=2)
axes[1].annotate("gate: ≤ 0.25", (1.36, 0.27), fontsize=8.5, color=plotstyle.MUTED,
                 ha="right")
axes[0].legend(frameon=False, ncols=2, loc="upper center",
               bbox_to_anchor=(1.75, -0.20), fontsize=9.5)

fig.suptitle("The instruction was read and not followed: the semicolon survives, the splicing does not stop.\n"
             "No interference panel is shown because the manipulation failed and the main experiment was not run.",
             x=0.02, y=1.10, ha="left", fontsize=11.5)
fig.subplots_adjust(top=0.84, wspace=0.42)

table.to_csv(DATA / "fig1_manipulation.csv", index=False)
for extension in ("png", "pdf", "svg"):
    fig.savefig(FIGURES / f"fig1_manipulation.{extension}", bbox_inches="tight",
                dpi=200 if extension == "png" else None)
plt.close(fig)
print("wrote fig1_manipulation.{png,pdf,svg} and data/fig1_manipulation.csv")
print(table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
