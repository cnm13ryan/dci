plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 9,
                     "axes.grid": True, "grid.alpha": 0.25})
INK, ACCENT, MUTED, WARN = "#1f2933", "#0b6e99", "#9aa5b1", "#b44d12"

with phase("plotting"):
    fig, axes = plt.subplots(1, len(CFG.orders), figsize=(11, 4.2), sharex=True)
    for ax, o in zip(np.atleast_1d(axes), CFG.orders):
        sub = PRIMARY.query("order == @o").set_index("reference").reindex(SELECTED_REFERENCES)
        y = np.arange(len(sub))
        ax.hlines(y, sub["sim_lower"], sub["sim_upper"], color=MUTED, lw=5, alpha=0.55,
                  label="simultaneous")
        ax.hlines(y, sub["ci_lower"], sub["ci_upper"], color=ACCENT, lw=1.6,
                  label="per contrast")
        ax.plot(sub["estimate"], y, "o", color=INK, ms=5, zorder=3)
        ax.axvline(0, color=INK, lw=0.8)
        ax.axvspan(-CFG.sesoi_risk_difference, CFG.sesoi_risk_difference,
                   color=ACCENT, alpha=0.06, lw=0)
        ax.set_yticks(y); ax.set_yticklabels(sub.index); ax.invert_yaxis()
        ax.set_title(o, loc="left")
        ax.set_xlabel(r"$\tau_{j,o}$  (failure-scale risk difference)")
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle(f"Primary: adding {CFG.focal_id} versus each admitted reference, by order",
                 x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "primary_tau_matrix.png", bbox_inches="tight")
    plt.show()

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))

    # Gate 3: g1 must beat the random comparator on its own.
    ax = axes[0]
    if len(RANDOM_MAE_DISTRIBUTION):
        ax.hist(RANDOM_MAE_DISTRIBUTION, bins=20, color=MUTED, alpha=0.7,
                label="random eligible sets")
    for value, colour, label in ((G1.get("mae"), ACCENT, "g1 (primary)"),
                                 (G0.get("mae"), INK, "g0 (benchmark)"),
                                 (G2.get("mae"), WARN, "g2 (secondary)")):
        if value is not None and np.isfinite(value):
            ax.axvline(value, color=colour, lw=1.8, label=label)
    ax.axvline(CFG.ref_val_mae_max, color=INK, ls="--", lw=1.0)
    ax.set_xlabel("MAE predicting held-out burden on U_val")
    ax.set_title("Gate 3, one-shot", loc="left")
    ax.legend(frameon=False, fontsize=7)

    # Per-reference validation: what a panel mean would have hidden.
    ax = axes[1]
    if len(IND_BOUNDS):
        worst = IND_BOUNDS.groupby("reference")["abs_upper"].max().sort_values()
        ax.barh(range(len(worst)), worst.to_numpy(),
                color=[ACCENT if v <= CFG.ref_val_individual_max else WARN
                       for v in worst])
        ax.axvline(CFG.ref_val_individual_max, color=INK, ls="--", lw=1.0)
        if len(PANEL_BOUNDS):
            ax.axvline(float(PANEL_BOUNDS["abs_upper"].max()), color=MUTED, lw=2.0)
        ax.set_yticks(range(len(worst))); ax.set_yticklabels(worst.index, fontsize=7)
        ax.set_xlabel("worst simultaneous |discrepancy| bound")
    ax.set_title("Per reference vs panel mean (grey)", loc="left")

    # Gate 4: bounds, not point estimates.
    ax = axes[2]
    if len(FALSIFICATION_INDIVIDUAL):
        ax.plot(FALSIFICATION_INDIVIDUAL["estimate"].abs(),
                FALSIFICATION_INDIVIDUAL["abs_upper"], "o", color=ACCENT, ms=4)
        lim = float(max(FALSIFICATION_INDIVIDUAL["abs_upper"].max(),
                        CFG.falsification_individual_max)) * 1.1
        ax.plot([0, lim], [0, lim], color=MUTED, lw=0.8)
        ax.axhline(CFG.falsification_individual_max, color=INK, ls="--", lw=1.0)
        ax.set_xlabel("|point estimate| on U_test")
        ax.set_ylabel("simultaneous upper bound")
    ax.set_title("Gate 4 decides on bounds", loc="left")

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "gate_diagnostics.png", bbox_inches="tight")
    plt.show()

print(f"figures written to {FIGURE_DIR}")
