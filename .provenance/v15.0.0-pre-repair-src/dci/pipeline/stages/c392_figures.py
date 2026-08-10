"""Stage 392 — migrated from notebook cell 392.py (figures).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/392.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell


plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 9,
                     "axes.grid": True, "grid.alpha": 0.25})
INK, ACCENT, MUTED, WARN = "#1f2933", "#0b6e99", "#9aa5b1", "#b44d12"

with S.phase("plotting"):
    fig, axes = plt.subplots(1, len(S.CFG.orders), figsize=(11, 4.2), sharex=True)
    for ax, o in zip(np.atleast_1d(axes), S.CFG.orders):
        sub = S.PRIMARY.query("order == @o").set_index("reference").reindex(S.SELECTED_REFERENCES)
        y = np.arange(len(sub))
        ax.hlines(y, sub["sim_lower"], sub["sim_upper"], color=MUTED, lw=5, alpha=0.55,
                  label="simultaneous")
        ax.hlines(y, sub["ci_lower"], sub["ci_upper"], color=ACCENT, lw=1.6,
                  label="per contrast")
        ax.plot(sub["estimate"], y, "o", color=INK, ms=5, zorder=3)
        ax.axvline(0, color=INK, lw=0.8)
        ax.axvspan(-S.CFG.sesoi_risk_difference, S.CFG.sesoi_risk_difference,
                   color=ACCENT, alpha=0.06, lw=0)
        ax.set_yticks(y); ax.set_yticklabels(sub.index); ax.invert_yaxis()
        ax.set_title(o, loc="left")
        ax.set_xlabel(r"$\tau_{j,o}$  (failure-scale risk difference)")
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle(f"Primary: adding {S.CFG.focal_id} versus each admitted reference, by order",
                 x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(S.FIGURE_DIR / "primary_tau_matrix.png", bbox_inches="tight")
    plt.show()

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))

    # Gate 3: g1 must beat the random comparator on its own.
    ax = axes[0]
    if len(S.RANDOM_MAE_DISTRIBUTION):
        ax.hist(S.RANDOM_MAE_DISTRIBUTION, bins=20, color=MUTED, alpha=0.7,
                label="random eligible sets")
    for value, colour, label in ((S.G1.get("mae"), ACCENT, "g1 (primary)"),
                                 (S.G0.get("mae"), INK, "g0 (benchmark)"),
                                 (S.G2.get("mae"), WARN, "g2 (secondary)")):
        if value is not None and np.isfinite(value):
            ax.axvline(value, color=colour, lw=1.8, label=label)
    ax.axvline(S.CFG.ref_val_mae_max, color=INK, ls="--", lw=1.0)
    ax.set_xlabel("MAE predicting held-out burden on U_val")
    ax.set_title("Gate 3, one-shot", loc="left")
    ax.legend(frameon=False, fontsize=7)

    # Per-reference validation: what a panel mean would have hidden.
    ax = axes[1]
    if len(S.IND_BOUNDS):
        worst = S.IND_BOUNDS.groupby("reference")["abs_upper"].max().sort_values()
        ax.barh(range(len(worst)), worst.to_numpy(),
                color=[ACCENT if v <= S.CFG.ref_val_individual_max else WARN
                       for v in worst])
        ax.axvline(S.CFG.ref_val_individual_max, color=INK, ls="--", lw=1.0)
        if len(S.PANEL_BOUNDS):
            ax.axvline(float(S.PANEL_BOUNDS["abs_upper"].max()), color=MUTED, lw=2.0)
        ax.set_yticks(range(len(worst))); ax.set_yticklabels(worst.index, fontsize=7)
        ax.set_xlabel("worst simultaneous |discrepancy| bound")
    ax.set_title("Per reference vs panel mean (grey)", loc="left")

    # Gate 4: bounds, not point estimates.
    ax = axes[2]
    if len(S.FALSIFICATION_INDIVIDUAL):
        ax.plot(S.FALSIFICATION_INDIVIDUAL["estimate"].abs(),
                S.FALSIFICATION_INDIVIDUAL["abs_upper"], "o", color=ACCENT, ms=4)
        lim = float(max(S.FALSIFICATION_INDIVIDUAL["abs_upper"].max(),
                        S.CFG.falsification_individual_max)) * 1.1
        ax.plot([0, lim], [0, lim], color=MUTED, lw=0.8)
        ax.axhline(S.CFG.falsification_individual_max, color=INK, ls="--", lw=1.0)
        ax.set_xlabel("|point estimate| on U_test")
        ax.set_ylabel("simultaneous upper bound")
    ax.set_title("Gate 4 decides on bounds", loc="left")

    fig.tight_layout()
    fig.savefig(S.FIGURE_DIR / "gate_diagnostics.png", bbox_inches="tight")
    plt.show()

print(f"figures written to {S.FIGURE_DIR}")
