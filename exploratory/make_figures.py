"""Build the whole compute-scaling and DCI figure set from preserved artifacts.

    uv run python make_figures.py

Writes tidy plotting tables to figures/reasoning_compute/data/ and every figure
in PNG, PDF and SVG. No headline number is typed in: each is recomputed from the
stored generations, and a QA pass at the end compares the reconstruction against
the numbers already published in the matrices.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dci_exploratory import plotdata, plotstyle
from dci_exploratory.plotstyle import AMP, COND_COLOR, COND_LABEL, COND_SHORT, CTRL

OUT = Path("figures/reasoning_compute")
DATA = OUT / "data"
plotstyle.use_style()

MODEL_REASONING = "Qwen/Qwen3-4B @ 1cfa9a72"
MODEL_AMPLIFIER = "Qwen/Qwen3-4B-Instruct-2507 @ cdbee75f"
EXECUTION = (
    "Reasoning panels: Qwen3-4B @ 1cfa9a72, vLLM 0.15.1+rocm720, tensor-parallel 2 "
    "(disable_custom_all_reduce, NCCL_P2P_DISABLE=1), bf16, T=0.7, top-p 0.9, "
    "fixed 512-token answer budget · b=0 is the model's native non-thinking mode\n"
    "Pair 3: A = exactly 4 sentences (target) · B = strictly increasing sentence "
    "lengths (focal) · C_L3 = matched reference · π = QAC, k = 3 · 20 pilot tasks × "
    "2 replicates · intervals: percentile bootstrap over 20 task clusters, 4000 draws "
    "— exploratory, uncorrected")

CAP_HEAVY = 0.90     # a budget this censored is annotated wherever it is plotted


# ------------------------------------------------------------------ helpers
def budget_axis(ax, budgets, minor: bool = False, footnote: bool = True) -> None:
    """Literal numeric budget axis. Linear — the uneven spacing is real.

    Rotated because it has to be: on a linear scale 0, 256 and 512 fall inside
    the first eighth of the axis, and horizontal labels there collide.
    """
    ax.set_xticks(budgets)
    ax.set_xticklabels([plotstyle.budget_label(b) for b in budgets],
                       fontsize=7 if not minor else 6.5, rotation=45, ha="right")
    # In a multi-panel figure the b=0 note belongs once to the figure, not six
    # times to its panels, where the copies collide with each other.
    ax.set_xlabel(plotstyle.BUDGET_AXIS_LABEL if footnote
                  else plotstyle.BUDGET_AXIS_LABEL.split("\n")[0],
                  fontsize=7.5 if minor else 8.5)
    ax.axvline(0, color="#d8d8d2", lw=0.8, zorder=0)


def errorbars(ax, x, table, prefix, color, label, marker="o", zero_at=None):
    estimate = table[f"{prefix}"].to_numpy(float)
    low = table[f"{prefix}_lo"].to_numpy(float)
    high = table[f"{prefix}_hi"].to_numpy(float)
    ax.errorbar(x, estimate, yerr=[estimate - low, high - estimate], marker=marker,
                capsize=2.5, color=color, label=label, elinewidth=1.1,
                markeredgecolor=plotstyle.SURFACE, markeredgewidth=0.6)
    if zero_at is not None:
        ax.scatter([x[zero_at]], [estimate[zero_at]], s=70, facecolors="none",
                   edgecolors=color, linewidths=1.4, zorder=5)
    return estimate


def mark_capped(ax, x, values, cap_hits):
    """Ring the budgets whose reasoning was almost always cut short."""
    for xi, yi, cap in zip(x, values, cap_hits):
        if cap >= CAP_HEAVY:
            ax.scatter([xi], [yi], s=110, facecolors="none", edgecolors=plotstyle.INK,
                       linewidths=0.9, linestyle=":", zorder=6)


def cond_rows(cells, variant, arm=None):
    sub = cells[cells["variant"] == variant]
    if arm is not None:
        sub = sub[sub["arm"] == arm]
    return sub.sort_values("reasoning_budget")


# =========================================================== build the data
def build() -> dict:
    print("rebuilding plot data from run artifacts …")
    run = plotdata.latest("runs/stageS18_reasoning_design_*/")
    raw = run / "s18_reasoning.jsonl"
    reasoning = plotdata.load_reasoning(raw)

    log = Path("/tmp/claude-1000/-home-cnm13ryan-git-dci/"
               "1f6c8f08-cc59-4f5d-9e64-e3f36d0c6265/scratchpad/s18.log")
    preserved_log = run / "generation_log.txt"
    if log.exists() and not preserved_log.exists():
        shutil.copy(log, preserved_log)
    rows_per_budget = int(len(reasoning) / reasoning["reasoning_budget"].nunique())
    timing = (plotdata.reasoning_timing(preserved_log, rows_per_budget)
              if preserved_log.exists() else pd.DataFrame())

    cells = plotdata.reasoning_cells(reasoning)
    tau = plotdata.reasoning_tau(reasoning)

    runs = {
        "S14 bare wordings, QAC k=3": plotdata.latest("runs/stageS14_markproperty_*/"),
        "S15 semicolon placement, QAC k=3": plotdata.latest("runs/stageS15_placement_semi_*/"),
        "S15 colon placement, QAC k=3": plotdata.latest("runs/stageS15_placement_colon_*/"),
        "S16 semicolon placement 2, QAC k=3": plotdata.latest("runs/stageS16_placement_semi2_*/"),
        "S17 atomicity, QAC k=3": plotdata.latest("runs/stageS17_atomicity_*/"),
        "S19 atomicity, ACQ k=3": plotdata.latest("runs/stageS19_atomicity_ACQ_*/"),
        "S21 atomicity, QAC k=5": plotdata.latest("runs/stageS21_atomicity_k5_*/"),
    }
    amplifier = plotdata.amplifier_conditions(runs)

    DATA.mkdir(parents=True, exist_ok=True)
    reasoning.to_csv(DATA / "reasoning_rows.csv", index=False)
    cells.to_csv(DATA / "reasoning_cells.csv", index=False)
    tau.to_csv(DATA / "reasoning_tau_and_delta.csv", index=False)
    amplifier.to_csv(DATA / "amplifier_conditions.csv", index=False)
    if not timing.empty:
        timing.to_csv(DATA / "reasoning_timing.csv", index=False)
    print(f"  {len(reasoning)} reasoning rows · {len(cells)} cells · "
          f"{len(amplifier)} amplifier conditions")
    return {"reasoning": reasoning, "cells": cells, "tau": tau,
            "timing": timing, "amplifier": amplifier, "run": run}


# ================================================================== figures
def fig01(cells, budgets):
    """b -> realised reasoning, the compute-use diagnostic."""
    for suffix, scale in (("", "linear"), ("_symlog", "symlog")):
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
        ax = axes[0]
        for variant in (CTRL, AMP):
            table = cond_rows(cells, variant).groupby("reasoning_budget").mean(
                numeric_only=True).reset_index()
            x = table["reasoning_budget"].to_numpy(float)
            ax.plot(x, table["realised_reasoning_mean"], marker="o",
                    color=COND_COLOR[variant], label=COND_SHORT[variant] + " · mean")
            ax.fill_between(x, table["realised_reasoning_p25"],
                            table["realised_reasoning_p75"], alpha=.15,
                            color=COND_COLOR[variant], lw=0)
        ax.plot(budgets, budgets, ls="--", lw=1, color=plotstyle.MUTED,
                label="M = b (budget fully spent)")
        if scale == "symlog":
            ax.set_xscale("symlog", linthresh=256)
        budget_axis(ax, budgets)
        ax.set_ylabel("realised reasoning tokens M")
        ax.set_title("Assigned budget → realised reasoning\n"
                     "band = interquartile range across rows")
        ax.legend(loc="upper left")

        ax = axes[1]
        table = cells.groupby("reasoning_budget").mean(numeric_only=True).reset_index()
        x = table["reasoning_budget"].to_numpy(float)
        ax.plot(x, table["cap_hit"], marker="s", color=plotstyle.SLOT[4],
                label="cap-hit rate (budget exhausted)")
        ax.plot(x, table["closed_naturally"], marker="o", color=plotstyle.SLOT[3],
                label="natural </think> closure")
        for xi, yi, cap in zip(x, table["cap_hit"], table["cap_hit"]):
            if cap >= CAP_HEAVY and xi != 0:
                ax.annotate(f"{cap:.0%} capped", (xi, yi), fontsize=7,
                            xytext=(6, -12), textcoords="offset points",
                            color=plotstyle.INK)
        if scale == "symlog":
            ax.set_xscale("symlog", linthresh=256)
        budget_axis(ax, budgets)
        ax.set_ylim(-0.05, 1.05)
        ax.set_ylabel("proportion of rows")
        ax.set_title("Censoring diagnostic\nb = 0 is native non-thinking, never censored")
        ax.legend(loc="center right")
        note = ("linear budget axis (primary)" if scale == "linear"
                else "SUPPLEMENTARY symlog axis (linthresh 256) — read the linear "
                     "version as primary")
        fig.suptitle(f"Figure 1{'b' if suffix else ''}. Reasoning treatment versus "
                     f"reasoning actually used — {note}", fontsize=11)
        fig.tight_layout(rect=[0, 0, 1, 0.9])
        plotstyle.save(fig, OUT, f"fig01_assigned_vs_realised{suffix}")
        plt.close(fig)


def fig02(cells, budgets):
    """Compliance of each constraint against assigned budget."""
    panels = [("A", "P(A compliant) — target, exactly 4 sentences"),
              ("QC", "P(focal/reference compliant) — the Q slot"),
              ("C", "P(C compliant) — background instruction"),
              ("joint", "P(A ∧ Q ∧ C) — joint compliance")]
    fig, axes = plt.subplots(2, 4, figsize=(17, 7.6), sharey=True)
    for column, (key, title) in enumerate(panels):
        for row, arm in enumerate(("B", "C_L3")):
            ax = axes[row][column]
            for variant in (CTRL, AMP):
                table = cond_rows(cells, variant, arm)
                x = table["reasoning_budget"].to_numpy(float)
                values = errorbars(ax, x, table, key, COND_COLOR[variant],
                                   COND_SHORT[variant])
                mark_capped(ax, x, values, table["cap_hit"].to_numpy(float))
            budget_axis(ax, budgets, minor=True)
            ax.set_ylim(-0.05, 1.05)
            if column == 0:
                ax.set_ylabel(f"{'FOCAL arm (B)' if arm == 'B' else 'REFERENCE arm (C_L3)'}"
                              "\ncompliance rate")
            if row == 0:
                ax.set_title(title, fontsize=9)
    axes[0][0].legend(loc="lower right")
    fig.suptitle("Figure 2. Constraint-by-constraint compliance versus assigned "
                 "reasoning budget\ndotted ring = budget exhausted on ≥90% of rows; "
                 "backgrounds are never pooled", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    plotstyle.save(fig, OUT, "fig02_compliance_vs_budget")
    plt.close(fig)


def fig03(cells, budgets):
    """The two rates τ is built from, before any difference is taken."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
    for ax, variant in zip(axes, (CTRL, AMP)):
        for arm, marker, shade in (("B", "o", 1.0), ("C_L3", "^", 0.45)):
            table = cond_rows(cells, variant, arm)
            x = table["reasoning_budget"].to_numpy(float)
            colour = COND_COLOR[variant]
            estimate = table["A_failure"].to_numpy(float)
            ax.errorbar(x, estimate,
                        yerr=[estimate - table["A_failure_lo"],
                              table["A_failure_hi"] - estimate],
                        marker=marker, capsize=2.5, color=colour, alpha=shade,
                        ls="-" if arm == "B" else "--",
                        label=("focal  P(F_A | B, b)" if arm == "B"
                               else "reference  P(F_A | R, b)"))
            mark_capped(ax, x, estimate, table["cap_hit"].to_numpy(float))
        ax.fill_between(
            cond_rows(cells, variant, "C_L3")["reasoning_budget"],
            cond_rows(cells, variant, "C_L3")["A_failure"],
            cond_rows(cells, variant, "B")["A_failure"],
            color=COND_COLOR[variant], alpha=.10, lw=0)
        budget_axis(ax, budgets)
        ax.set_ylim(-0.05, 1.05)
        ax.set_title(COND_LABEL[variant].replace("\n", " "), fontsize=9.5)
        ax.legend(loc="upper right")
    axes[0].set_ylabel("P(target A fails)")
    fig.suptitle("Figure 3. The raw components of DCI — shaded gap is τ(B→A)\n"
                 "under the control the gap closes because FOCAL failure falls, not "
                 "because reference failure rises", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    plotstyle.save(fig, OUT, "fig03_dci_components")
    plt.close(fig)


def _tau_panel(ax, tau, cells, budgets, legend=True, footnote=True):
    for variant in (CTRL, AMP):
        table = tau[(tau["variant"] == variant)].sort_values("reasoning_budget")
        x = table["reasoning_budget"].to_numpy(float)
        estimate = table["estimate"].to_numpy(float)
        ax.errorbar(x, estimate,
                    yerr=[estimate - table["lo"], table["hi"] - estimate],
                    marker="o", capsize=2.5, color=COND_COLOR[variant],
                    label=COND_LABEL[variant].replace("\n", " "),
                    markeredgecolor=plotstyle.SURFACE, markeredgewidth=0.6)
        caps = (cells[(cells["variant"] == variant) & (cells["arm"] == "B")]
                .sort_values("reasoning_budget")["cap_hit"].to_numpy(float))
        mark_capped(ax, x, estimate, caps)
    ax.axhline(0, color=plotstyle.INK, lw=0.9)
    budget_axis(ax, budgets, footnote=footnote)
    ax.set_ylabel("τ(B→A) = paired excess A-failure")
    if legend:
        ax.legend(loc="upper right")


def fig04(tau, cells, budgets):
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    _tau_panel(ax, tau, cells, budgets)
    ax.annotate("control interference\nresolved from here on", xy=(512, 0),
                xytext=(900, 0.22), fontsize=8, color=plotstyle.SLOT[1],
                arrowprops=dict(arrowstyle="->", color=plotstyle.SLOT[1], lw=1))
    ax.set_title("Figure 4. Directional interference versus reasoning budget\n"
                 "points joined as a visual guide only — no law is fitted",
                 fontsize=10.5)
    fig.tight_layout()
    plotstyle.save(fig, OUT, "fig04_tau_vs_budget")
    plt.close(fig)


def _delta_panel(ax, tau, budgets, legend=True, footnote=True):
    table = tau[tau["variant"] == "DELTA_amp"].sort_values("reasoning_budget")
    x = table["reasoning_budget"].to_numpy(float)
    estimate = table["estimate"].to_numpy(float)
    ax.errorbar(x, estimate, yerr=[estimate - table["lo"], table["hi"] - estimate],
                marker="s", capsize=2.5, color=plotstyle.SLOT[4],
                label="Δ = τ(amplifier) − τ(control), paired by task",
                markeredgecolor=plotstyle.SURFACE, markeredgewidth=0.6)
    ax.axhline(0, color=plotstyle.INK, lw=0.9)
    budget_axis(ax, budgets, footnote=footnote)
    ax.set_ylabel("Δ contextual amplification")
    if legend:
        ax.legend(loc="upper left")


def fig05(tau, budgets):
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    _delta_panel(ax, tau, budgets)
    ax.set_title("Figure 5. The contextual amplification gap versus reasoning\n"
                 "a widening gap need NOT mean the amplifier grows more harmful —\n"
                 "here it widens because the control's interference is resolved",
                 fontsize=10)
    fig.tight_layout()
    plotstyle.save(fig, OUT, "fig05_amplification_gap")
    plt.close(fig)


def _arbitration_panel(ax, cells, variant, budgets, legend=False, footnote=True):
    table = cond_rows(cells, variant, "B")
    x = table["reasoning_budget"].to_numpy(float)
    # Several states sit at exactly 0, so their end-labels would print on top of
    # one another. Direct-label only the ones that are actually separated there;
    # the legend carries the rest, so identity is never colour-alone either way.
    for state in plotstyle.ARBITRATION_ORDER:
        y = table[f"arb_{state.replace(' ', '_')}"].to_numpy(float)
        ax.plot(x, y, marker=plotstyle.ARBITRATION_MARKER[state],
                color=plotstyle.ARBITRATION_COLOR[state], label=state)
        if y[-1] >= 0.06:
            ax.annotate(state, (x[-1], y[-1]), fontsize=7, xytext=(6, 0),
                        textcoords="offset points",
                        color=plotstyle.ARBITRATION_COLOR[state], va="center")
    budget_axis(ax, budgets, footnote=footnote)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(-250, budgets[-1] * 1.30)
    ax.set_title(COND_LABEL[variant].replace("\n", " "), fontsize=9.5)
    ax.legend(loc="upper center", ncol=2, fontsize=7)


def fig06(cells, budgets):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, variant in zip(axes, (CTRL, AMP)):
        _arbitration_panel(ax, cells, variant, budgets)
    axes[0].set_ylabel("P(arbitration state | b),  focal arm B")
    fig.suptitle("Figure 6. What the model does when constraints compete\n"
                 "under the control, reasoning moves probability out of "
                 "\"neither\" into \"target only\" — target-priority arbitration, "
                 "not joint satisfaction", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.87])
    plotstyle.save(fig, OUT, "fig06_arbitration")
    plt.close(fig)


def fig07(cells, tau, budgets):
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 7.2), sharex=True)
    table = cond_rows(cells, CTRL, "B")
    x = table["reasoning_budget"].to_numpy(float)
    values = errorbars(axes[0], x, table, "A",
                       COND_COLOR[CTRL], "P(A compliant), focal arm, control background")
    mark_capped(axes[0], x, values, table["cap_hit"].to_numpy(float))
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].set_ylabel("absolute performance\nP(A compliant)")
    axes[0].legend(loc="lower right")
    axes[0].set_title("A conventional accuracy curve: reasoning fixes the task",
                      fontsize=10)
    _delta_panel(axes[1], tau, budgets)
    axes[1].set_title("The same budgets, the residual context dependence",
                      fontsize=10)
    fig.suptitle("Figure 7. Absolute performance can improve while contextual\n"
                 "interference remains — one curve hides what the other shows",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    plotstyle.save(fig, OUT, "fig07_performance_vs_residual_gap")
    plt.close(fig)


def fig08(cells, tau):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    for variant in (CTRL, AMP):
        table = cond_rows(cells, variant, "B")
        ax.plot(table["realised_reasoning_mean"], table["A"], marker="o",
                color=COND_COLOR[variant], label=COND_SHORT[variant])
        for _, row in table.iterrows():
            ax.annotate(f"b={int(row['reasoning_budget'])}",
                        (row["realised_reasoning_mean"], row["A"]), fontsize=6.5,
                        xytext=(4, 4), textcoords="offset points", color=plotstyle.MUTED)
    ax.set_xlabel("mean realised reasoning tokens M (post-treatment)")
    ax.set_ylabel("P(A compliant), focal arm")
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    ax.set_title("Target compliance versus realised reasoning", fontsize=9.5)

    ax = axes[1]
    for variant in (CTRL, AMP):
        table = cond_rows(cells, variant, "B").set_index("reasoning_budget")
        series = tau[tau["variant"] == variant].set_index("reasoning_budget")
        joined = table.join(series[["estimate"]]).sort_values("realised_reasoning_mean")
        ax.plot(joined["realised_reasoning_mean"], joined["estimate"], marker="o",
                color=COND_COLOR[variant], label=COND_SHORT[variant])
        for budget, row in joined.iterrows():
            ax.annotate(f"b={int(budget)}",
                        (row["realised_reasoning_mean"], row["estimate"]), fontsize=6.5,
                        xytext=(4, 4), textcoords="offset points", color=plotstyle.MUTED)
    ax.axhline(0, color=plotstyle.INK, lw=0.9)
    ax.set_xlabel("mean realised reasoning tokens M (post-treatment)")
    ax.set_ylabel("τ(B→A)")
    ax.legend()
    ax.set_title("Interference versus realised reasoning", fontsize=9.5)
    fig.suptitle("Figure 8. DESCRIPTIVE ONLY — realised reasoning is chosen partly by "
                 "the model and is post-treatment.\nThese are not dose-response curves; "
                 "points are condition means labelled by their assigned budget.",
                 fontsize=10.5)
    fig.tight_layout(rect=[0, 0, 1, 0.87])
    plotstyle.save(fig, OUT, "fig08_descriptive_realised_reasoning")
    plt.close(fig)


def fig09(cells, tau, timing):
    if timing.empty:
        print("  fig09 skipped: no preserved timing artifact")
        return
    seconds = timing.set_index("reasoning_budget")["seconds_per_row_batched"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    for variant in (CTRL, AMP):
        table = cond_rows(cells, variant, "B")
        x = [seconds[b] for b in table["reasoning_budget"]]
        ax.plot(x, table["A"], marker="o", color=COND_COLOR[variant],
                label=COND_SHORT[variant])
        for xi, (_, row) in zip(x, table.iterrows()):
            ax.annotate(f"b={int(row['reasoning_budget'])}", (xi, row["A"]),
                        fontsize=6.5, xytext=(4, 4), textcoords="offset points",
                        color=plotstyle.MUTED)
    ax.set_ylabel("P(A compliant), focal arm")
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    ax.set_title("Target compliance versus generation time", fontsize=9.5)

    ax = axes[1]
    for variant in (CTRL, AMP):
        table = tau[tau["variant"] == variant].sort_values("reasoning_budget")
        x = [seconds[b] for b in table["reasoning_budget"]]
        ax.plot(x, table["estimate"], marker="o", color=COND_COLOR[variant],
                label=COND_SHORT[variant])
    ax.axhline(0, color=plotstyle.INK, lw=0.9)
    ax.set_ylabel("τ(B→A)")
    ax.legend()
    ax.set_title("Interference versus generation time", fontsize=9.5)
    for ax in axes:
        ax.set_xlabel("mean seconds per response\n"
                      "(both phases, batch wall clock ÷ rows)")
    fig.suptitle("Figure 9. A tokenizer-free resource axis.  TIME HERE IS "
                 "THROUGHPUT, NOT LATENCY:\nvLLM generated all 160 rows of a budget "
                 "as one continuously-batched job, covering the reasoning phase and "
                 "the fixed-budget answer phase.", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.86])
    plotstyle.save(fig, OUT, "fig09_time_axis")
    plt.close(fig)


def main_figure(cells, tau, budgets):
    fig = plt.figure(figsize=(16.5, 9.8))
    grid = fig.add_gridspec(2, 3, hspace=0.46, wspace=0.28)

    ax = fig.add_subplot(grid[0, 0])
    for variant in (CTRL, AMP):
        table = cond_rows(cells, variant, "B")
        x = table["reasoning_budget"].to_numpy(float)
        for key, ls, marker in (("A", "-", "o"), ("joint", ":", "D")):
            ax.plot(x, table[key], ls=ls, marker=marker, color=COND_COLOR[variant],
                    label=f"{COND_SHORT[variant]} · {'A (target)' if key == 'A' else 'joint'}")
    budget_axis(ax, budgets, minor=True, footnote=False)
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("compliance rate, focal arm")
    ax.set_title("A · Compliance versus reasoning budget", fontsize=10)
    ax.legend(fontsize=6.5, loc="center right")

    ax = fig.add_subplot(grid[0, 1])
    for variant in (CTRL, AMP):
        for arm, ls, marker in (("B", "-", "o"), ("C_L3", "--", "^")):
            table = cond_rows(cells, variant, arm)
            ax.plot(table["reasoning_budget"], table["A_failure"], ls=ls,
                    marker=marker, color=COND_COLOR[variant],
                    alpha=1.0 if arm == "B" else 0.5,
                    label=f"{COND_SHORT[variant]} · {'focal B' if arm == 'B' else 'reference R'}")
    budget_axis(ax, budgets, minor=True, footnote=False)
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("P(target A fails)")
    ax.set_title("B · The raw components of DCI", fontsize=10)
    ax.legend(fontsize=6.5)

    ax = fig.add_subplot(grid[0, 2])
    _arbitration_panel(ax, cells, CTRL, budgets, footnote=False)
    ax.set_ylabel("P(state | b)")
    ax.set_title("E · Arbitration, control background", fontsize=10)

    ax = fig.add_subplot(grid[1, 0])
    _tau_panel(ax, tau, cells, budgets, legend=False, footnote=False)
    ax.legend(fontsize=7, loc="center right")
    ax.set_title("C · τ(B→A): interference versus reasoning", fontsize=11,
                 fontweight="bold")
    for spine in ax.spines.values():
        spine.set_edgecolor(plotstyle.INK)
        spine.set_linewidth(1.2)

    ax = fig.add_subplot(grid[1, 1])
    _delta_panel(ax, tau, budgets, legend=False, footnote=False)
    ax.legend(fontsize=7, loc="upper left")
    ax.set_title("D · Δ contextual amplification", fontsize=11, fontweight="bold")
    for spine in ax.spines.values():
        spine.set_edgecolor(plotstyle.INK)
        spine.set_linewidth(1.2)

    ax = fig.add_subplot(grid[1, 2])
    table = cells.groupby("reasoning_budget").mean(numeric_only=True).reset_index()
    x = table["reasoning_budget"].to_numpy(float)
    ax.plot(x, table["realised_reasoning_mean"], marker="o", color=plotstyle.SLOT[3],
            label="realised reasoning M (mean)")
    ax.set_ylabel("realised reasoning tokens M")
    twin_free = ax.twiny()
    twin_free.set_xticks([])
    # b = 0 is not "0% capped" — it has no reasoning phase to cap, so annotating
    # it as if it were on the same censoring scale would misdescribe it.
    for xi, cap in zip(x, table["cap_hit"]):
        if xi == 0:
            continue
        last = xi == x[-1]
        ax.annotate(f"{cap:.0%}\ncapped", (xi, table.set_index("reasoning_budget")
                                           .loc[xi, "realised_reasoning_mean"]),
                    fontsize=6.5, xytext=(-6 if last else 6, -14 if last else -4),
                    textcoords="offset points", ha="right" if last else "left",
                    color=plotstyle.INK if cap >= CAP_HEAVY else plotstyle.MUTED)
    budget_axis(ax, budgets, minor=True, footnote=False)
    ax.legend(fontsize=7, loc="lower right")
    ax.set_title("F · Realised reasoning and censoring", fontsize=10)

    fig.suptitle(
        "Additional test-time reasoning resolves ORDINARY directional interference "
        "but not AMPLIFIED interference\n"
        "Panels C and D are the result; A, B, E and F show what it is made of",
        fontsize=13, y=0.985)
    fig.text(0.5, 0.005, plotstyle.BUDGET_AXIS_LABEL.split("\n")[1] + "\n" + EXECUTION,
             ha="center", va="bottom", fontsize=7,
             color=plotstyle.MUTED)
    fig.subplots_adjust(top=0.88, bottom=0.16)
    plotstyle.save(fig, OUT, "main_compute_figure")
    plt.close(fig)


# ------------------------------------------------------- amplifier figures
def fig_variants(amplifier):
    qac3 = amplifier[(amplifier["order"] == "QAC") & (amplifier["load"] == 3)].copy()
    qac3["key"] = qac3["variant"] + " · " + qac3["stage"].str.slice(0, 3)
    qac3 = qac3.sort_values(["manipulation_ok", "tau_estimate"])
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 0.30 * len(qac3) + 3.0),
                             sharey=True, gridspec_kw={"width_ratios": [2.1, 1]})
    y = np.arange(len(qac3))
    ax = axes[0]
    for yi, (_, row) in zip(y, qac3.iterrows()):
        colour = (plotstyle.CLASS_COLOR[row["structural_class"]]
                  if row["manipulation_ok"] else plotstyle.INVALID)
        ax.plot([row["tau_lo"], row["tau_hi"]], [yi, yi], color=colour, lw=1.8,
                solid_capstyle="round")
        ax.scatter([row["tau_estimate"]], [yi], color=colour, s=34, zorder=3,
                   edgecolors=plotstyle.SURFACE, linewidths=0.6)
    ax.axvline(0, color=plotstyle.INK, lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(qac3["key"], fontsize=7)
    ax.set_xlabel("τ(B→A), paired excess A-failure")
    ax.set_title("τ by background variant, π = QAC, k = 3", fontsize=10)
    handles = [plt.Line2D([], [], color=c, lw=2.4, label=n)
               for n, c in plotstyle.CLASS_COLOR.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=7.5)

    ax = axes[1]
    colours = [plotstyle.CLASS_COLOR[r["structural_class"]] if r["manipulation_ok"]
               else plotstyle.INVALID for _, r in qac3.iterrows()]
    ax.barh(y, qac3["own_compliance"], color=colours, height=0.62)
    ax.axvline(plotdata.COMPLIANCE_GATE, color=plotstyle.INK, ls="--", lw=1)
    ax.annotate("usability gate 0.50", (plotdata.COMPLIANCE_GATE, len(qac3) - 0.4),
                fontsize=7, xytext=(4, 0), textcoords="offset points")
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("compliance with the background instruction itself")
    ax.set_title("Manipulation check", fontsize=10)
    fig.suptitle("Figure 11. Which background instructions amplify B→A, and which "
                 "were actually followed\n"
                 "Grey = manipulation failed: those τ values are NOT evidence about "
                 "the property the variant was built to vary.\n"
                 "Free placement is therefore UNTESTED, not established.", fontsize=10.5)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    plotstyle.save(fig, OUT, "fig11_amplifier_variants")
    plt.close(fig)


def fig_order_and_load(amplifier):
    valid = amplifier[amplifier["manipulation_ok"]]
    keep = ["X_SEMICOLON_FREE", "X_ELLIPSIS_FREE", "X_PAREN_FREE"]
    conditions = [("S17 atomicity, QAC k=3", "π = QAC\nk = 3"),
                  ("S19 atomicity, ACQ k=3", "π = ACQ\nk = 3"),
                  ("S21 atomicity, QAC k=5", "π = QAC\nk = 5")]

    for name, subset, title, note in (
            ("fig12_order_dependence", conditions[:2],
             "Figure 12. The same instructions, reordered",
             "Amplification lives at QAC and is absent at ACQ. The design varies the "
             "whole permutation at once,\nso this does NOT identify a rule as simple "
             "as \"the amplifier must follow the target\"."),
            ("fig13_load_transport", [conditions[0], conditions[2]],
             "Figure 13. Transport from k = 3 to k = 5",
             "The semicolon transports; the ellipsis attenuates and stops being "
             "separable from the control,\nwhose own interference rises under load. "
             "Same apparent class at low load ≠ same robustness.")):
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
        for ax, (stage, label) in zip(axes, subset):
            table = valid[(valid["stage"] == stage) & valid["variant"].isin(keep)]
            table = table.set_index("variant").reindex(
                [v for v in keep if v in set(table["variant"])])
            x = np.arange(len(table))
            for xi, (variant, row) in zip(x, table.iterrows()):
                colour = plotstyle.VARIANT_COLOR[variant]
                ax.bar([xi], [row["tau_estimate"]], color=colour, width=0.6)
                ax.plot([xi, xi], [row["tau_lo"], row["tau_hi"]],
                        color=plotstyle.INK, lw=1.2)
                ax.annotate(f"compliance\n{row['own_compliance']:.3f}", (xi, 0.02),
                            ha="center", fontsize=6.5, color=plotstyle.INK)
            ax.set_xticks(x)
            ax.set_xticklabels([v.replace("X_", "").replace("_FREE", "").lower()
                                for v in table.index], fontsize=8)
            ax.axhline(0, color=plotstyle.INK, lw=0.9)
            ax.set_ylim(-0.25, 1.05)
            ax.set_title(label, fontsize=10)
        axes[0].set_ylabel("τ(B→A)")
        fig.suptitle(f"{title}\n{note}", fontsize=10)
        fig.tight_layout(rect=[0, 0, 1, 0.85])
        plotstyle.save(fig, OUT, name)
        plt.close(fig)


def fig_strategy(amplifier):
    valid = amplifier[amplifier["manipulation_ok"]
                      & (amplifier["order"] == "QAC") & (amplifier["load"] == 3)]
    # `X_SEMICOLON_FREE` was run three times at this cell. Plotting all three
    # stacks three labels on one point without adding information, so each
    # variant appears once, from a declared preferred run. The replications
    # themselves are in fig11 and in amplifier_conditions.csv.
    preference = ["S17 atomicity, QAC k=3", "S14 bare wordings, QAC k=3",
                  "S15 colon placement, QAC k=3", "S15 semicolon placement, QAC k=3",
                  "S16 semicolon placement 2, QAC k=3"]
    valid = (valid.assign(rank=valid["stage"].map({s: i for i, s in enumerate(preference)}))
             .sort_values("rank").drop_duplicates("variant", keep="first"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, (xcol, xlabel) in zip(axes, (
            ("chain_share_focal", "chain_share in the focal arm\n"
                                  "(share of clause boundaries carried by ; : —)"),
            ("n_sentences_focal", "mean sentences produced in the focal arm\n"
                                  "(target is 4)"))):
        low_seen = 0
        for _, row in valid.sort_values("tau_estimate", ascending=False).iterrows():
            colour = plotstyle.CLASS_COLOR[row["structural_class"]]
            ax.scatter([row[xcol]], [row["tau_estimate"]], s=60, color=colour,
                       edgecolors=plotstyle.SURFACE, linewidths=0.7, zorder=3)
            ax.plot([row[xcol]] * 2, [row["tau_lo"], row["tau_hi"]],
                    color=colour, lw=1.1, alpha=.7)
            # The enclosing-pair variants all sit near (0, 0); stagger their
            # labels deterministically so three true nulls stay three readable
            # points rather than one smear.
            if row["tau_estimate"] >= 0.2:
                offset, align = ((6, 4) if row["tau_estimate"] >= 0.5 else (6, -9)), "left"
            else:
                offset, align = [((7, 3), "left"), ((7, -11), "left"),
                                 ((-7, -12), "right")][low_seen % 3]
                low_seen += 1
            ax.annotate(row["variant"].replace("X_", "").replace("U_FMT_", ""),
                        (row[xcol], row["tau_estimate"]), fontsize=6.5,
                        xytext=offset, textcoords="offset points", ha=align)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("τ(B→A)")
        ax.axhline(0, color=plotstyle.INK, lw=0.9)
    axes[1].axvline(4, color=plotstyle.MUTED, ls="--", lw=1)
    fig.suptitle("Figure 14. Similar interference, different downstream strategy\n"
                 "The semicolon amplifies by collapsing clauses onto one sentence; the "
                 "ellipsis amplifies with almost no chaining at all.\n"
                 "chain_share therefore does not order these variants and is not a "
                 "sufficient mediator of amplification.", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.84])
    plotstyle.save(fig, OUT, "fig14_strategy_dissociation")
    plt.close(fig)


# ====================================================================== QA
def qa(bundle):
    reasoning, cells, tau = bundle["reasoning"], bundle["cells"], bundle["tau"]
    amplifier = bundle["amplifier"]
    problems = []

    def check(label, ok, detail=""):
        print(f"  [{'ok ' if ok else 'FAIL'}] {label} {detail}")
        if not ok:
            problems.append(label)

    check("800 reasoning rows", len(reasoning) == 800, f"({len(reasoning)})")
    check("5 budgets × 160 rows",
          set(reasoning.groupby("reasoning_budget").size()) == {160})
    check("20 task clusters everywhere",
          set(cells["n_tasks"]) == {20}, f"({sorted(set(cells['n_tasks']))})")
    check("no empty answers", reasoning["answer_empty"].sum() == 0)
    check("no truncated answers", reasoning["answer_truncated"].sum() == 0)
    check("no scratch language in any answer",
          reasoning["scratch_marker"].sum() == 0)
    check("b=0 is native non-thinking",
          bool(reasoning[reasoning["reasoning_budget"] == 0]["native_nonthinking"].all())
          and reasoning[reasoning["reasoning_budget"] == 0]["reasoning_tokens"].eq(0).all())
    cap256 = reasoning[reasoning["reasoning_budget"] == 256]["reasoning_cap_hit"].mean()
    check("b=256 is heavily censored", cap256 >= CAP_HEAVY, f"(cap-hit {cap256:.3f})")

    published = {(0, CTRL): 0.400, (256, CTRL): 0.150, (512, CTRL): 0.000,
                 (1024, CTRL): 0.000, (4096, CTRL): 0.000,
                 (0, AMP): 0.600, (256, AMP): 0.075, (512, AMP): 0.375,
                 (1024, AMP): 0.450, (4096, AMP): 0.500}
    for (budget, variant), expected in published.items():
        got = tau[(tau["reasoning_budget"] == budget)
                  & (tau["variant"] == variant)]["estimate"].iloc[0]
        check(f"τ(b={budget}, {COND_SHORT[variant]}) matches the matrix",
              abs(got - expected) < 1e-6, f"(rebuilt {got:+.3f} vs {expected:+.3f})")

    k5 = amplifier[amplifier["stage"] == "S21 atomicity, QAC k=5"]
    check("k=5 rows really carry load 5", set(k5["load"]) == {5})
    check("S20 (the mislabelled run) is excluded",
          not any("S20" in s for s in amplifier["stage"]))
    amp_published = {("S17 atomicity, QAC k=3", "X_SEMICOLON_FREE"): 0.950,
                     ("S17 atomicity, QAC k=3", "X_ELLIPSIS_FREE"): 0.400,
                     ("S17 atomicity, QAC k=3", "X_PAREN_FREE"): 0.075,
                     ("S21 atomicity, QAC k=5", "X_SEMICOLON_FREE"): 0.875,
                     ("S19 atomicity, ACQ k=3", "X_SEMICOLON_FREE"): 0.100}
    for (stage, variant), expected in amp_published.items():
        got = amplifier[(amplifier["stage"] == stage)
                        & (amplifier["variant"] == variant)]["tau_estimate"].iloc[0]
        check(f"τ({variant}, {stage.split(',')[1].strip()}) matches the matrix",
              abs(got - expected) < 1e-6, f"(rebuilt {got:+.3f} vs {expected:+.3f})")
    return problems


def main() -> int:
    bundle = build()
    budgets = sorted(bundle["cells"]["reasoning_budget"].unique())
    print("figures:")
    fig01(bundle["cells"], budgets)
    fig02(bundle["cells"], budgets)
    fig03(bundle["cells"], budgets)
    fig04(bundle["tau"], bundle["cells"], budgets)
    fig05(bundle["tau"], budgets)
    fig06(bundle["cells"], budgets)
    fig07(bundle["cells"], bundle["tau"], budgets)
    fig08(bundle["cells"], bundle["tau"])
    fig09(bundle["cells"], bundle["tau"], bundle["timing"])
    main_figure(bundle["cells"], bundle["tau"], budgets)
    fig_variants(bundle["amplifier"])
    fig_order_and_load(bundle["amplifier"])
    fig_strategy(bundle["amplifier"])
    print("QA:")
    problems = qa(bundle)
    if problems:
        print(f"\n{len(problems)} QA check(s) FAILED — investigate before publishing")
        return 1
    print("\nall QA checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
