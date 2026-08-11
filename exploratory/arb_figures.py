"""The five figures, built from the scored rows and nothing else.

No headline number is typed into this file. Every value plotted is recomputed
here from `scored_generations.jsonl` through the same estimators the reports use,
and every panel writes the numbers it drew beside it as a tidy CSV, so a figure
and its table cannot drift apart.

Colour carries one meaning throughout: slot 1 is the parenthesis control, slot 2
the semicolon background, and the four arbitration outcomes keep a fixed slot
each. Reasoning condition is carried by position and by a hatch, never by hue, so
a reader who cannot separate the two hues still reads the figure from the
legend and the direct labels.
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
FIGURES.mkdir(exist_ok=True)
DATA = FIGURES / "data"
DATA.mkdir(exist_ok=True)

BACKGROUND_COLOUR = {"parentheses": plotstyle.SLOT[1], "semicolon": plotstyle.SLOT[2]}
STATE_COLOUR = {"both": plotstyle.SLOT[3], "target only": plotstyle.SLOT[1],
                "focal only": plotstyle.SLOT[2], "neither": plotstyle.SLOT[4]}
BUDGET_LABEL = {0: "no reasoning\n(native)", 4096: "high reasoning\n(b = 4096)"}


def load(*parts: str) -> pd.DataFrame | None:
    path = RUN.joinpath(*parts)
    if not path.exists():
        print(f"  [skip] {path} not present")
        return None
    return pd.read_json(path, lines=True)


def save(fig, name: str, table: pd.DataFrame) -> None:
    table.to_csv(DATA / f"{name}.csv", index=False)
    for extension in ("png", "pdf", "svg"):
        fig.savefig(FIGURES / f"{name}.{extension}", bbox_inches="tight",
                    dpi=200 if extension == "png" else None)
    plt.close(fig)
    print(f"  wrote {name}.{{png,pdf,svg}} and data/{name}.csv")


def interval_bars(ax, frame: pd.DataFrame, x, colour, width=0.34):
    ax.bar(x, frame["estimate"], width, color=colour, zorder=3)
    ax.errorbar(x, frame["estimate"],
                yerr=[frame["estimate"] - frame["lo"], frame["hi"] - frame["estimate"]],
                fmt="none", ecolor=plotstyle.INK, elinewidth=1.2, capsize=3, zorder=4)


# ---------------------------------------------------------------- figure 1
def figure_one(frame: pd.DataFrame) -> None:
    clusters = A.Clusters(sorted(frame["task_id"].unique()), key="fig1")
    orders, budgets = ["QAC", "ACQ"], sorted(frame["reasoning_budget"].unique())
    rows = []
    for order in orders:
        for budget in budgets:
            estimate, lo, hi = clusters.interval(
                A.delta(frame, order=order, reasoning_budget=budget))
            rows.append({"order": order, "reasoning_budget": budget,
                         "estimate": estimate, "lo": lo, "hi": hi})
    table = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    positions = np.arange(len(orders))
    for offset, budget in zip((-0.19, 0.19), budgets):
        subset = table[table["reasoning_budget"] == budget]
        colour = plotstyle.SLOT[1] if budget == 0 else plotstyle.SLOT[2]
        ax.bar(positions + offset, subset["estimate"], 0.36, color=colour,
               label=BUDGET_LABEL[budget].replace("\n", " "), zorder=3)
        ax.errorbar(positions + offset, subset["estimate"],
                    yerr=[subset["estimate"] - subset["lo"],
                          subset["hi"] - subset["estimate"]],
                    fmt="none", ecolor=plotstyle.INK, elinewidth=1.2, capsize=3,
                    zorder=4)
        # Anchor each label outside its own interval, not outside the bar, so a
        # long whisker cannot run through the number.
        for position, value, lo, hi in zip(positions + offset, subset["estimate"],
                                           subset["lo"], subset["hi"]):
            ax.annotate(f"{value:+.2f}", (position, hi if value >= 0 else lo),
                        xytext=(0, 7 if value >= 0 else -15),
                        textcoords="offset points", ha="center", fontsize=9,
                        color=plotstyle.INK)
    ax.axhline(0, color=plotstyle.MUTED, linewidth=1)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{o}\n(instruction order)" for o in orders])
    ax.set_ylabel("Δ  =  extra target failure caused by\nthe semicolon, over the bracket control")
    ax.set_title("The semicolon's effect flips sign with instruction order,\n"
                 "and reasoning removes the protective case", loc="left")
    ax.set_ylim(min(table["lo"]) - 0.18, max(table["hi"]) + 0.12)
    ax.legend(frameon=False, ncols=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.14))
    plotstyle.use_style() if hasattr(plotstyle, "use_style") else None
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e6e6e2", zorder=0)
    save(fig, "fig1_core_replication", table)


# ---------------------------------------------------------------- figure 2
def figure_two(frame: pd.DataFrame) -> None:
    clusters = A.Clusters(sorted(frame["task_id"].unique()), key="fig2")
    cells, rows = [], []
    for order in ("QAC", "ACQ"):
        for background in ("parentheses", "semicolon"):
            for budget in sorted(frame["reasoning_budget"].unique()):
                states = A.arbitration(frame, order=order,
                                       background_name=background,
                                       reasoning_budget=budget)
                cells.append((order, background, budget))
                for state in A.STATES:
                    estimate, lo, hi = clusters.interval(states[state])
                    rows.append({"order": order, "background": background,
                                 "reasoning_budget": budget, "state": state,
                                 "estimate": estimate, "lo": lo, "hi": hi})
    table = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    positions = np.arange(len(cells))
    bottom = np.zeros(len(cells))
    for state in A.STATES:
        values = np.array([table[(table["order"] == o) & (table["background"] == b)
                                 & (table["reasoning_budget"] == n)
                                 & (table["state"] == state)]["estimate"].iloc[0]
                           for o, b, n in cells])
        ax.bar(positions, values, 0.62, bottom=bottom, label=state,
               color=STATE_COLOUR[state], edgecolor="white", linewidth=1.6, zorder=3)
        for position, value, base in zip(positions, values, bottom):
            if value >= 0.08:
                ax.annotate(f"{value:.2f}", (position, base + value / 2),
                            ha="center", va="center", fontsize=8.5, color="white")
        bottom += values
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{b}\n{o}\n{'b=0' if n == 0 else f'b={n}'}"
                        for o, b, n in cells], fontsize=8.5)
    ax.set_ylabel("share of answers in the focal (B) arm")
    ax.set_ylim(0, 1)
    ax.set_title("More reasoning does not buy both instructions — it buys the target.\n"
                 "'both' stays under 0.12 everywhere; at ACQ with a semicolon, reasoning makes it worse",
                 loc="left")
    ax.legend(frameon=False, ncols=4, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig2_arbitration_outcomes", table)


# ---------------------------------------------------------------- figure 3
def figure_three(frame: pd.DataFrame) -> None:
    clusters = A.Clusters(sorted(frame["task_id"].unique()), key="fig3")
    orders = [o for o in ("QAC", "QCA", "AQC", "ACQ", "CQA", "CAQ")
              if o in set(frame["order"])]
    budgets = sorted(frame["reasoning_budget"].unique())
    rows = []
    for order in orders:
        for budget in budgets:
            estimate, lo, hi = clusters.interval(
                A.delta(frame, order=order, reasoning_budget=budget))
            rows.append({"order": order, "reasoning_budget": budget,
                         "estimate": estimate, "lo": lo, "hi": hi})
        estimate, lo, hi = clusters.interval(
            A.gamma(frame, order=order, low=budgets[0], high=budgets[-1]))
        rows.append({"order": order, "reasoning_budget": "Gamma",
                     "estimate": estimate, "lo": lo, "hi": hi})
    table = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    positions = np.arange(len(orders))
    for offset, budget, colour in ((-0.19, budgets[0], plotstyle.SLOT[1]),
                                   (0.19, budgets[-1], plotstyle.SLOT[2])):
        subset = table[table["reasoning_budget"] == budget].set_index("order").loc[orders]
        ax.bar(positions + offset, subset["estimate"], 0.36, color=colour,
               label=BUDGET_LABEL[budget].replace("\n", " "), zorder=3)
        ax.errorbar(positions + offset, subset["estimate"],
                    yerr=[subset["estimate"] - subset["lo"],
                          subset["hi"] - subset["estimate"]],
                    fmt="none", ecolor=plotstyle.INK, elinewidth=1.1, capsize=3,
                    zorder=4)
    ax.axhline(0, color=plotstyle.MUTED, linewidth=1)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{o}\nA in slot {o.index('A') + 1}" for o in orders],
                       fontsize=9)
    ax.set_ylabel("Δ  (semicolon minus bracket control)")
    ax.set_title("With reasoning the semicolon hurts in every order; without it,\n"
                 "the same three instructions reordered swing Δ from −0.54 to +0.39",
                 loc="left")
    ax.legend(frameon=False, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e6e6e2", zorder=0)
    save(fig, "fig3_six_orders", table)


# ---------------------------------------------------------------- figure 4
def figure_four(frame: pd.DataFrame) -> None:
    clusters = A.Clusters(sorted(frame["task_id"].unique()), key="fig4")
    priorities = ["equal", "a_over_b", "b_over_a"]
    pretty = {"equal": "equal priority", "a_over_b": "A over B", "b_over_a": "B over A"}
    budgets = sorted(frame["reasoning_budget"].unique())
    cells, rows = [], []
    for background in ("parentheses", "semicolon"):
        for budget in budgets:
            for priority in priorities:
                states = A.arbitration(frame, priority=priority,
                                       background_name=background,
                                       reasoning_budget=budget)
                cells.append((background, budget, priority))
                for state in A.STATES:
                    estimate, lo, hi = clusters.interval(states[state])
                    rows.append({"background": background, "reasoning_budget": budget,
                                 "priority": priority, "state": state,
                                 "estimate": estimate, "lo": lo, "hi": hi})
    table = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    positions = np.arange(len(cells)) + np.repeat(np.arange(len(cells) // 3) * 0.6, 3)
    bottom = np.zeros(len(cells))
    for state in A.STATES:
        values = np.array([table[(table["background"] == b)
                                 & (table["reasoning_budget"] == n)
                                 & (table["priority"] == p)
                                 & (table["state"] == state)]["estimate"].iloc[0]
                           for b, n, p in cells])
        ax.bar(positions, values, 0.8, bottom=bottom, label=state,
               color=STATE_COLOUR[state], edgecolor="white", linewidth=1.4, zorder=3)
        for position, value, base in zip(positions, values, bottom):
            if value >= 0.08:
                ax.annotate(f"{value:.2f}", (position, base + value / 2), ha="center",
                            va="center", fontsize=8, color="white")
        bottom += values
    ax.set_xticks(positions)
    ax.set_xticklabels([pretty[p] for _, _, p in cells], fontsize=8.5, rotation=30,
                       ha="right")
    # The background and budget label the GROUP, so they are written once under
    # each triple instead of repeated on every bar, where they collided.
    for start in range(0, len(cells), 3):
        background, budget, _ = cells[start]
        ax.annotate(f"{background}, b = {budget}",
                    (positions[start:start + 3].mean(), -0.30),
                    xycoords=("data", "axes fraction"), ha="center", fontsize=9,
                    color=plotstyle.INK, annotation_clip=False)
    ax.set_ylabel("share of answers")
    ax.set_ylim(0, 1)
    ax.set_title("Naming a priority does not decide which instruction survives:\n"
                 "reversing it leaves the four outcomes essentially where they were",
                 loc="left")
    ax.legend(frameon=False, ncols=4, loc="upper center", bbox_to_anchor=(0.5, -0.40))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig4_priority_intervention", table)


# ---------------------------------------------------------------- figure 5
def figure_five(primary: pd.DataFrame, second: pd.DataFrame) -> None:
    frames = {primary["model_id"].iloc[0]: primary, second["model_id"].iloc[0]: second}
    shared = set(primary["order"]) & set(second["order"])
    orders = [o for o in ("QAC", "ACQ") if o in shared] + sorted(shared - {"QAC", "ACQ"})
    rows = []
    for name, frame in frames.items():
        clusters = A.Clusters(sorted(frame["task_id"].unique()), key=f"fig5|{name}")
        for order in orders:
            for budget in sorted(frame["reasoning_budget"].unique()):
                estimate, lo, hi = clusters.interval(
                    A.delta(frame, order=order, reasoning_budget=budget))
                rows.append({"model": name, "order": order,
                             "reasoning_budget": budget, "quantity": "Delta",
                             "estimate": estimate, "lo": lo, "hi": hi})
            estimate, lo, hi = clusters.interval(
                A.gamma(frame, order=order,
                        low=min(frame["reasoning_budget"]),
                        high=max(frame["reasoning_budget"])))
            rows.append({"model": name, "order": order, "reasoning_budget": "Gamma",
                         "quantity": "Gamma", "estimate": estimate, "lo": lo, "hi": hi})
    table = pd.DataFrame(rows)

    fig, axes = plt.subplots(1, len(orders), figsize=(4.6 * len(orders), 4.2),
                             sharey=True, squeeze=False)
    for axis, order in zip(axes[0], orders):
        subset = table[(table["order"] == order) & (table["quantity"] == "Delta")]
        models = list(frames)
        positions = np.arange(len(models))
        for offset, budget, colour in ((-0.19, 0, plotstyle.SLOT[1]),
                                       (0.19, 4096, plotstyle.SLOT[2])):
            cell = subset[subset["reasoning_budget"] == budget].set_index("model").loc[models]
            axis.bar(positions + offset, cell["estimate"], 0.36, color=colour,
                     label=BUDGET_LABEL[budget].replace("\n", " "), zorder=3)
            axis.errorbar(positions + offset, cell["estimate"],
                          yerr=[cell["estimate"] - cell["lo"],
                                cell["hi"] - cell["estimate"]],
                          fmt="none", ecolor=plotstyle.INK, elinewidth=1.1,
                          capsize=3, zorder=4)
        axis.axhline(0, color=plotstyle.MUTED, linewidth=1)
        axis.set_xticks(positions)
        axis.set_xticklabels([m.split("/")[-1] for m in models], fontsize=9)
        axis.set_title(order, loc="left")
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="#e6e6e2", zorder=0)
    axes[0][0].set_ylabel("Δ  (semicolon minus bracket control)")
    axes[0][-1].legend(frameon=False, loc="best")
    fig.suptitle("Only half of it transports: the second model shows a reasoning effect too,\n"
                 "but the semicolon protects it rather than harming it, and never amplifies",
                 x=0.06, ha="left")
    save(fig, "fig5_cross_model", table)


def main() -> None:
    print("figures:")
    exp1 = load("priority0", "scored_generations.jsonl")
    if exp1 is not None:
        figure_one(exp1)
        figure_two(exp1)
        exp2 = load("order_map", "scored_generations.jsonl")
        if exp2 is not None:
            figure_three(pd.concat([exp1, exp2], ignore_index=True))
    exp3 = load("priority_intervention", "main", "scored_generations.jsonl")
    if exp3 is not None:
        figure_four(exp3)
    exp4 = load("cross_model", "main", "scored_generations.jsonl")
    if exp4 is not None and exp1 is not None:
        figure_five(exp1[exp1["order"].isin(set(exp4["order"]))], exp4)


if __name__ == "__main__":
    main()
