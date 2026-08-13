"""Supporting figures for the natural-reasoning branch.

Three, each with one job:

  fig16  robustness — is the headline broad across tasks, or a few tasks?
  fig17  what the model did when the instructions competed
  fig18  the technical companion, in this project's own notation

Figure 1 and the reasoning-length distribution are built by `make_headline.py`.
Everything here reads the canonical tables written by `natural_analysis.py`, so
no figure can drift from the analysis.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dci_exploratory import plotstyle

OUT = Path("figures/reasoning_compute")
DATA = OUT / "data"
plotstyle.use_style()

BRACKET_LABEL, SEMICOLON_LABEL = "+ one bracket pair", "+ one semicolon"
COLOR = {BRACKET_LABEL: "#2a78d6", SEMICOLON_LABEL: "#eb6834"}
STYLE = {BRACKET_LABEL: "-", SEMICOLON_LABEL: "--"}
MARKER = {BRACKET_LABEL: "o", SEMICOLON_LABEL: "s"}


def fig16_robustness():
    het = pd.read_csv(DATA / "natural_task_heterogeneity.csv", index_col=0)
    loo = pd.read_csv(DATA / "natural_leave_one_task_out.csv")
    tail = pd.read_csv(DATA / "natural_long_trace_sensitivity.csv")

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8),
                             gridspec_kw={"width_ratios": [1.5, 1, 1]})

    ax = axes[0]
    order = het.sort_values(SEMICOLON_LABEL)
    y = np.arange(len(order))
    ax.barh(y, order[SEMICOLON_LABEL], color=COLOR[SEMICOLON_LABEL], height=.62,
            label=SEMICOLON_LABEL)
    ax.scatter(order[BRACKET_LABEL], y, color=COLOR[BRACKET_LABEL], s=30, zorder=3,
               label=BRACKET_LABEL)
    ax.axvline(0, color=plotstyle.INK, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(order.index, fontsize=7)
    ax.set_xlabel("Extra main-instruction failures for this task")
    ax.set_title("Every task, one bar each\n"
                 "14 of 20 tasks positive, 5 zero, 1 negative", fontsize=10)
    ax.legend(fontsize=8, loc="lower right")

    ax = axes[1]
    for label, group in loo.groupby("background"):
        values = np.sort(group["estimate"].to_numpy(float))
        ax.plot(values, np.arange(len(values)), marker=MARKER[label],
                ls=STYLE[label], color=COLOR[label], markersize=4, label=label)
    ax.axvline(0, color=plotstyle.INK, lw=1)
    ax.set_xlabel("Estimate with that task left out")
    ax.set_ylabel("tasks, sorted")
    ax.set_title("Leave one task out, 20 times\n"
                 "the semicolon result never changes sign", fontsize=10)
    ax.legend(fontsize=8, loc="center right")

    ax = axes[2]
    labels = list(dict.fromkeys(tail["exclusion"]))
    x = np.arange(len(labels))
    for label in (BRACKET_LABEL, SEMICOLON_LABEL):
        sub = tail[tail["background"] == label].set_index("exclusion").loc[labels]
        ax.plot(x, sub["estimate"], marker=MARKER[label], ls=STYLE[label],
                color=COLOR[label], label=label)
    ax.axhline(0, color=plotstyle.INK, lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([l.replace("drop longest", "drop\nlongest") for l in labels],
                       fontsize=8)
    ax.set_ylim(-0.1, 0.7)
    ax.set_ylabel("Extra main-instruction failures")
    ax.set_title("Removing the longest reasoning traces\n"
                 "changes almost nothing", fontsize=10)
    ax.legend(fontsize=8)

    fig.suptitle("Is the result broad, or carried by a few tasks or a few very "
                 "long answers?  Neither.", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    plotstyle.save(fig, OUT, "fig16_robustness")
    plt.close(fig)


def fig17_outcomes():
    table = pd.read_csv(DATA / "natural_question3_outcomes.csv", index_col=0)
    order = ["both satisfied", "main instruction only",
             "competing instruction only", "neither"]
    # No red-green pair: "neither" takes the violet categorical slot so the
    # figure never depends on telling red from green.
    shades = ["#1baf7a", "#2a78d6", "#eda100", "#4a3aa7"]
    fig, ax = plt.subplots(figsize=(9.2, 3.5))
    left = np.zeros(len(table))
    y = np.arange(len(table))
    for column, shade in zip(order, shades):
        values = table[column].to_numpy(float)
        ax.barh(y, values, left=left, color=shade, height=.55,
                edgecolor=plotstyle.SURFACE, linewidth=2)
        for yi, (value, start) in enumerate(zip(values, left)):
            if value >= 0.06:
                ax.text(start + value / 2, yi, f"{value:.0%}", ha="center",
                        va="center", fontsize=9.5, color="white", fontweight="bold")
        left += values
    ax.set_yticks(y)
    ax.set_yticklabels(table.index, fontsize=10.5)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, .25, .5, .75, 1])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Share of answers, when both instructions were present")
    ax.grid(False)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=s) for s in shades]
    ax.legend(handles, order, fontsize=9, ncol=4, loc="upper center",
              bbox_to_anchor=(0.5, -0.32))
    ax.set_title("Allowed to finish thinking on its own, the model mostly "
                 "protects the main instruction\nrather than satisfying both — "
                 "and with the semicolon it often satisfies neither",
                 fontsize=12, fontweight="bold", loc="left", pad=12)
    fig.tight_layout()
    plotstyle.save(fig, OUT, "fig17_what_the_model_did")
    plt.close(fig)


def fig18_technical():
    curve = pd.read_csv(DATA / "canonical_capped_and_natural_curve.csv")
    usage = pd.read_csv(DATA / "natural_question2_reasoning_use.csv")
    settings = ["0", "256", "512", "1024", "4096", "natural"]
    x = [0, 1, 2, 3, 4, 5.5]

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.9),
                             gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    for label in (BRACKET_LABEL, SEMICOLON_LABEL):
        sub = curve[curve["background"] == label].set_index("setting").loc[settings]
        estimate = sub["estimate"].to_numpy(float)
        ax.errorbar(x, estimate,
                    yerr=[estimate - sub["lo"], sub["hi"] - estimate],
                    marker=MARKER[label], ls=STYLE[label], color=COLOR[label],
                    capsize=3, label=label, markeredgecolor="white",
                    markeredgewidth=0.7)
        for xi, value, cap in zip(x, estimate, sub["cap_hit"]):
            if cap >= 0.5:
                ax.scatter([xi], [value], s=115, facecolors="none",
                           edgecolors=plotstyle.INK, linewidths=0.9, ls=":", zorder=6)
    ax.axhline(0, color=plotstyle.INK, lw=1)
    ax.axvline((x[4] + x[5]) / 2, color="#c8c8c2", lw=1, ls=":")
    ax.set_xticks(x)
    ax.set_xticklabels(["0\n(native\nno-think)", "256", "512", "1024", "4096",
                        "natural\n(ceiling\n39,550)"], fontsize=8)
    ax.set_xlabel("assigned reasoning budget b — the treatment "
                  "(natural is not a budget)", fontsize=9)
    ax.set_ylabel(r"$\tau_{B \rightarrow A}$ = paired excess A-failure", fontsize=10)
    ax.set_title("Directional constraint interference, corrected seeds only\n"
                 "dotted ring: budget exhausted on ≥50% of rows", fontsize=10)
    ax.legend(fontsize=9)

    ax = axes[1]
    labels, positions_, colours = [], [], []
    for i, (_, row) in enumerate(usage.iterrows()):
        labels.append(f"{row['background']}\n{row['arm']}")
        positions_.append(i)
        colours.append(COLOR[row["background"]])
    for i, (_, row) in enumerate(usage.iterrows()):
        ax.plot([row["p25"], row["p75"]], [i, i], color=colours[i], lw=6, alpha=.35,
                solid_capstyle="butt")
        ax.plot([row["p25"], row["max"]], [i, i], color=colours[i], lw=1, alpha=.5)
        ax.scatter([row["median"]], [i], color=colours[i], s=55, zorder=3,
                   edgecolors="white", linewidths=0.8)
        ax.annotate(f"median {row['median']:,.0f}   max {row['max']:,.0f}",
                    (row["max"], i), xytext=(8, 0), textcoords="offset points",
                    fontsize=7.5, va="center", color=plotstyle.MUTED)
    ax.set_yticks(positions_)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("realised reasoning tokens M under natural reasoning "
                  "(post-treatment)", fontsize=9)
    ax.set_xlim(0, 7600)
    ax.set_title("Realised reasoning by cell\nbar = interquartile range, "
                 "line to maximum, 0/160 reached the ceiling", fontsize=10)

    fig.suptitle("Technical companion — same data as Figure 1, in the project's "
                 "own notation", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    plotstyle.save(fig, OUT, "fig18_technical_companion")
    plt.close(fig)


def main() -> int:
    fig16_robustness()
    fig17_outcomes()
    fig18_technical()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
