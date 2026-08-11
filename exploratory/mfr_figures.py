"""Figures for the mechanism test and the focal repair.

Two figures, one per experiment, both rebuilt from the scored rows. No headline
number is typed in; each panel writes what it drew to `data/<name>.csv`.
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
from dci_exploratory import arbprogram as A
from dci_exploratory import plotstyle

RUN = Path(sys.argv[1])
FIGURES = RUN / "figures"
DATA = FIGURES / "data"
DATA.mkdir(parents=True, exist_ok=True)

BOUNDARY, NON_BOUNDARY = "X_SEMICOLON_FREE", "X_DEGREE_FREE"
STATE_COLOUR = {"both": plotstyle.SLOT[3], "target only": plotstyle.SLOT[1],
                "focal only": plotstyle.SLOT[2], "neither": plotstyle.SLOT[4]}


def save(fig, name: str, table: pd.DataFrame) -> None:
    table.to_csv(DATA / f"{name}.csv", index=False)
    for extension in ("png", "pdf", "svg"):
        fig.savefig(FIGURES / f"{name}.{extension}", bbox_inches="tight",
                    dpi=200 if extension == "png" else None)
    plt.close(fig)
    print(f"  wrote {name}.{{png,pdf,svg}} and data/{name}.csv")


# ------------------------------------------------------------- figure 1
def boundary_figure() -> None:
    frame = pd.read_json(RUN / "boundary_main" / "scored_generations.jsonl",
                         lines=True)
    budgets = sorted(frame["reasoning_budget"].unique())
    clusters = A.Clusters(sorted(frame["task_id"].unique()), key="mfr-boundary")
    rows = []
    for background in (NON_BOUNDARY, BOUNDARY):
        for budget in budgets:
            estimate, lo, hi = clusters.interval(
                A.tau(frame, background=background, order="QAC",
                      reasoning_budget=budget))
            rows.append({"quantity": "tau", "background": A.BACKGROUND_LABEL[background],
                         "reasoning_budget": budget, "estimate": estimate,
                         "lo": lo, "hi": hi})
    for budget in budgets:
        estimate, lo, hi = clusters.interval(
            A.delta(frame, order="QAC", reasoning_budget=budget,
                    amplifier=BOUNDARY, control=NON_BOUNDARY))
        rows.append({"quantity": "Delta_boundary", "background": "semicolon - degree",
                     "reasoning_budget": budget, "estimate": estimate,
                     "lo": lo, "hi": hi})
    table = pd.DataFrame(rows)

    fig, (left, right) = plt.subplots(1, 2, figsize=(11.2, 4.4),
                                      gridspec_kw={"width_ratios": [1.25, 1]})

    positions = np.arange(len(budgets))
    for offset, background, colour in ((-0.19, "degree", plotstyle.SLOT[1]),
                                       (0.19, "semicolon", plotstyle.SLOT[2])):
        cell = table[(table["quantity"] == "tau")
                     & (table["background"] == background)]
        label = ("degree symbol — cannot be a clause boundary" if background == "degree"
                 else "semicolon — can be a clause boundary")
        left.bar(positions + offset, cell["estimate"], 0.36, color=colour,
                 label=label, zorder=3)
        left.errorbar(positions + offset, cell["estimate"],
                      yerr=[cell["estimate"] - cell["lo"], cell["hi"] - cell["estimate"]],
                      fmt="none", ecolor=plotstyle.INK, elinewidth=1.2, capsize=3,
                      zorder=4)
        for x, v, hi, lo in zip(positions + offset, cell["estimate"], cell["hi"],
                                cell["lo"]):
            left.annotate(f"{v:+.2f}", (x, hi if v >= 0 else lo),
                          xytext=(0, 7 if v >= 0 else -15), textcoords="offset points",
                          ha="center", fontsize=9, color=plotstyle.INK)
    left.axhline(0, color=plotstyle.MUTED, linewidth=1)
    left.set_xticks(positions)
    left.set_xticklabels(["no reasoning\n(native)", "high reasoning\n(b = 4096)"])
    left.set_ylabel("τ — extra target failure caused by the\nfocal instruction, over its matched reference")
    left.set_title("Only the boundary-capable mark interferes", loc="left",
                   fontsize=10.5, pad=26)
    lo_min = float(table[table["quantity"] == "tau"]["lo"].min())
    hi_max = float(table[table["quantity"] == "tau"]["hi"].max())
    left.set_ylim(lo_min - 0.14, hi_max + 0.12)
    left.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    left.spines[["top", "right"]].set_visible(False)
    left.grid(axis="y", color="#e6e6e2", zorder=0)

    cell = table[table["quantity"] == "Delta_boundary"]
    right.bar(positions, cell["estimate"], 0.42, color=plotstyle.SLOT[4], zorder=3)
    right.errorbar(positions, cell["estimate"],
                   yerr=[cell["estimate"] - cell["lo"], cell["hi"] - cell["estimate"]],
                   fmt="none", ecolor=plotstyle.INK, elinewidth=1.2, capsize=3, zorder=4)
    for x, v, hi in zip(positions, cell["estimate"], cell["hi"]):
        right.annotate(f"{v:+.2f}", (x, hi), xytext=(0, 7),
                       textcoords="offset points", ha="center", fontsize=9,
                       color=plotstyle.INK)
    right.axhline(0, color=plotstyle.MUTED, linewidth=1)
    right.set_xticks(positions)
    right.set_xticklabels(["no reasoning\n(native)", "high reasoning\n(b = 4096)"])
    right.set_ylabel("Δ_boundary = τ(semicolon) − τ(degree)")
    right.set_title("The gap does not close with reasoning", loc="left",
                    fontsize=10.5, pad=26)
    right.spines[["top", "right"]].set_visible(False)
    right.grid(axis="y", color="#e6e6e2", zorder=0)

    fig.suptitle("A mark that can stand where a sentence boundary could stand interferes with\n"
                 "sentence-defined instructions; an otherwise identical mark that cannot, does not",
                 x=0.02, y=1.10, ha="left", fontsize=12)
    fig.subplots_adjust(top=0.86, wspace=0.32)
    save(fig, "fig1_boundary_mechanism", table)


# ------------------------------------------------------------- figure 2
def ladder_figure() -> None:
    frame = pd.read_json(RUN / "focal_calibration" / "scored_generations.jsonl",
                         lines=True)
    primary = frame[frame["background"] == "X_PAREN_FREE"]
    rungs = ["B", "X_B_INC2", "X_B_INC1"]
    pretty = {"B": "B3\nthree increases\n(the existing focal)",
              "X_B_INC2": "B2\ntwo increases", "X_B_INC1": "B1\none increase"}
    rows = []
    for rung in rungs:
        subset = primary[primary["arm"] == rung]
        states = subset["arbitration_state"].value_counts(normalize=True)
        for state in A.STATES:
            rows.append({"rung": rung, "state": state,
                         "share": float(states.get(state, 0.0))})
        rows.append({"rung": rung, "state": "focal pass rate",
                     "share": float(subset["Q_pass"].mean())})
    table = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    positions = np.arange(len(rungs))
    bottom = np.zeros(len(rungs))
    for state in A.STATES:
        values = np.array([table[(table["rung"] == r) & (table["state"] == state)]
                           ["share"].iloc[0] for r in rungs])
        ax.bar(positions, values, 0.55, bottom=bottom, label=state,
               color=STATE_COLOUR[state], edgecolor="white", linewidth=1.6, zorder=3)
        for x, v, base in zip(positions, values, bottom):
            if v >= 0.06:
                ax.annotate(f"{v:.2f}", (x, base + v / 2), ha="center", va="center",
                            fontsize=9, color="white")
        bottom += values
    # "focal only" is the state the repair needed and never got; label it where it is.
    for x, r in zip(positions, rungs):
        value = table[(table["rung"] == r)
                      & (table["state"] == "focal only")]["share"].iloc[0]
        ax.annotate(f"focal only = {value:.3f}", (x, 1.02), ha="center",
                    fontsize=9, color=plotstyle.SLOT[2])
    ax.set_xticks(positions)
    ax.set_xticklabels([pretty[r] for r in rungs], fontsize=9)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("share of answers")
    ax.set_title("Making the competing instruction easier does not create competition:\n"
                 "the probability moves into 'both', never into 'focal only'",
                 loc="left")
    ax.legend(frameon=False, ncols=4, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig2_focal_ladder", table)


print("figures:")
boundary_figure()
ladder_figure()
