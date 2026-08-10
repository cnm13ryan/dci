"""Exploratory analysis of one run directory.

Everything here is descriptive and labelled so. No multiplicity control, no
simultaneous inference, no hierarchical model, no sequential testing — those are
the confirmatory pipeline's job and importing them would dress an exploratory
look up as evidence.

The one thing this module is strict about is **pairing**. Contrasts are formed
by joining focal to reference rows on `pair_key`, which encodes (task, order,
replicate). Nothing is ever paired by position, and a focal row whose matching
reference row is missing or unscorable is dropped from that contrast with the
drop counted, rather than silently compared against a different instance.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

EXPLORATORY_NOTE = ("EXPLORATORY — descriptive only. Intervals are paired "
                    "bootstrap percentiles over task clusters, not inferential "
                    "guarantees, and carry no multiplicity control.")


def load_run(run_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    run_dir = Path(run_dir)
    frame = pd.read_json(run_dir / "generations.jsonl", lines=True)
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    return frame, config


# ------------------------------------------------------------ condition table
def condition_table(frame: pd.DataFrame) -> pd.DataFrame:
    """n, valid generations, technical failures, A-failures, lengths, truncation."""
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    rows = []
    for (order, arm), group in contrast.groupby(["order", "arm"], dropna=False):
        scorable = group[group["scorable"]]
        rows.append({
            "order": order,
            "arm": arm,
            "condition": group["condition"].iloc[0],
            "n": len(group),
            "n_valid": int(len(scorable)),
            "n_technical_failures": int(group["technical_failure"].sum()),
            "n_unscorable": int((~group["scorable"] & ~group["technical_failure"]).sum()),
            "n_a_failures": int(scorable["a_failure"].sum()),
            "a_failure_rate": float(scorable["a_failure"].mean()) if len(scorable) else np.nan,
            "mean_generated_tokens": float(group["generated_token_count"].mean()),
            "median_generated_tokens": float(group["generated_token_count"].median()),
            "mean_response_words": float(group["response_words"].mean()),
            "n_truncated": int(group["output_truncated"].fillna(False).sum()),
            "truncation_rate": float(group["output_truncated"].fillna(False).mean()),
        })
    return pd.DataFrame(rows).sort_values(["order", "condition", "arm"],
                                          ascending=[True, True, True])


def primitive_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Isolated single-instruction difficulty, per constraint.

    This is the competence check for A and, for the arms, the cheap probe of
    whether the references are matched to B on measured difficulty rather than
    only on construction.
    """
    primitives = frame[frame["condition"] == "primitive"]
    rows = []
    for arm, group in primitives.groupby("arm"):
        scorable = group[group["scorable"]]
        rows.append({
            "constraint": arm,
            "n": len(group),
            "n_valid": int(len(scorable)),
            "n_failures": int(scorable["a_failure"].sum()),
            "failure_rate": float(scorable["a_failure"].mean()) if len(scorable) else np.nan,
            "mean_generated_tokens": float(group["generated_token_count"].mean()),
            "n_truncated": int(group["output_truncated"].fillna(False).sum()),
        })
    return pd.DataFrame(rows).sort_values("constraint")


# ------------------------------------------------------------------ contrasts
def paired_units(frame: pd.DataFrame, focal_id: str, reference: str,
                 order: Optional[str] = None) -> pd.DataFrame:
    """One row per matched (task, order, replicate) with both outcomes present."""
    contrast = frame[frame["condition"].isin(["focal", "reference"])]
    if order is not None:
        contrast = contrast[contrast["order"] == order]
    focal = contrast[(contrast["arm"] == focal_id) & contrast["scorable"]]
    ref = contrast[(contrast["arm"] == reference) & contrast["scorable"]]
    merged = focal.merge(
        ref, on="pair_key", suffixes=("_focal", "_reference"), how="inner",
        validate="one_to_one")
    # The join key already forces this, but an assertion here is what stops a
    # future change to pair_key from silently pairing different instances.
    assert (merged["task_id_focal"] == merged["task_id_reference"]).all()
    assert (merged["order_focal"] == merged["order_reference"]).all()
    merged["diff"] = merged["a_failure_focal"] - merged["a_failure_reference"]
    return merged


def _bootstrap_ci(values: np.ndarray, clusters: np.ndarray, n_boot: int = 10000,
                  alpha: float = 0.05, seed: int = 20260810) -> tuple[float, float]:
    """Percentile CI from a CLUSTER bootstrap resampling whole tasks.

    Replicates of the same task are not independent draws — they share the topic
    — so resampling rows would understate the spread. Tasks are the unit.
    """
    rng = np.random.default_rng(seed)
    unique = np.unique(clusters)
    if len(unique) < 2:
        return float("nan"), float("nan")
    by_cluster = {c: values[clusters == c] for c in unique}
    draws = np.empty(n_boot)
    for i in range(n_boot):
        picked = rng.choice(unique, size=len(unique), replace=True)
        draws[i] = np.concatenate([by_cluster[c] for c in picked]).mean()
    return float(np.quantile(draws, alpha / 2)), float(np.quantile(draws, 1 - alpha / 2))


def contrast_table(frame: pd.DataFrame, config: dict[str, Any],
                   n_boot: int = 10000) -> pd.DataFrame:
    """Per-reference paired contrasts tau_j, per order and pooled over orders."""
    focal_id = config["selection"]["focal"]
    references = config["selection"]["references"]
    orders = [*config["orders"], None]           # None = pooled across orders

    rows = []
    for order in orders:
        for reference in references:
            paired = paired_units(frame, focal_id, reference, order)
            if paired.empty:
                continue
            diffs = paired["diff"].to_numpy(dtype=float)
            clusters = paired["task_id_focal"].to_numpy()
            low, high = _bootstrap_ci(diffs, clusters, n_boot=n_boot)
            rows.append({
                "order": order or "pooled",
                "reference": reference,
                "n_pairs": len(paired),
                "n_tasks": int(len(np.unique(clusters))),
                "focal_failure_rate": float(paired["a_failure_focal"].mean()),
                "reference_failure_rate": float(paired["a_failure_reference"].mean()),
                "tau": float(diffs.mean()),
                "tau_ci_low": low,
                "tau_ci_high": high,
                "n_focal_fail_ref_pass": int(((paired["a_failure_focal"] == 1)
                                              & (paired["a_failure_reference"] == 0)).sum()),
                "n_focal_pass_ref_fail": int(((paired["a_failure_focal"] == 0)
                                              & (paired["a_failure_reference"] == 1)).sum()),
                "n_concordant": int((paired["a_failure_focal"]
                                     == paired["a_failure_reference"]).sum()),
            })
    return pd.DataFrame(rows)


def aggregate_contrast(frame: pd.DataFrame, config: dict[str, Any],
                       n_boot: int = 10000) -> pd.DataFrame:
    """The weighted aggregate and the v19-shaped conservative minimum.

    `tau_weighted` uses UNIFORM weights and is descriptive only — see
    `Selection.reference_weights`. `tau_min` is `min_j tau_j`, the shape v19's
    headline actually takes: B must beat EVERY reference, not their average.
    """
    focal_id = config["selection"]["focal"]
    references = config["selection"]["references"]
    weights = config["selection"]["reference_weights"]
    rows = []

    for order in [*config["orders"], None]:
        # Build a per-unit weighted reference outcome, keeping only units where
        # the focal row and ALL four reference rows are scorable. Dropping
        # incomplete units keeps the weighted average over a constant reference
        # set instead of letting it drift with whichever arms happened to score.
        per_reference = {}
        for reference in references:
            paired = paired_units(frame, focal_id, reference, order)
            if paired.empty:
                per_reference = {}
                break
            per_reference[reference] = paired.set_index("pair_key")
        if not per_reference:
            continue
        common = set.intersection(*(set(p.index) for p in per_reference.values()))
        if not common:
            continue
        keys = sorted(common)
        focal_outcome = per_reference[references[0]].loc[keys, "a_failure_focal"].to_numpy(float)
        clusters = per_reference[references[0]].loc[keys, "task_id_focal"].to_numpy()
        weighted_reference = np.zeros(len(keys))
        per_reference_tau = {}
        for reference in references:
            outcome = per_reference[reference].loc[keys, "a_failure_reference"].to_numpy(float)
            weighted_reference += weights[reference] * outcome
            per_reference_tau[reference] = float((focal_outcome - outcome).mean())

        diffs = focal_outcome - weighted_reference
        low, high = _bootstrap_ci(diffs, clusters, n_boot=n_boot)
        worst = min(per_reference_tau, key=per_reference_tau.get)
        rows.append({
            "order": order or "pooled",
            "n_complete_units": len(keys),
            "n_tasks": int(len(np.unique(clusters))),
            "focal_failure_rate": float(focal_outcome.mean()),
            "weighted_reference_failure_rate": float(weighted_reference.mean()),
            "tau_weighted": float(diffs.mean()),
            "tau_weighted_ci_low": low,
            "tau_weighted_ci_high": high,
            "tau_min_over_references": per_reference_tau[worst],
            "tau_min_reference": worst,
            "tau_max_over_references": max(per_reference_tau.values()),
        })
    return pd.DataFrame(rows)


# -------------------------------------------------------------------- figures
def _subtitle(config: dict[str, Any], frame: pd.DataFrame) -> str:
    sel = config["selection"]
    return (f"{config['model']['model_id']} @ {config['model']['revision'][:8]} | "
            f"pair A={sel['target']} B={sel['focal']} | load k={config['load']} | "
            f"{config['n_tasks']} tasks x {config['replicates']} reps x "
            f"{len(config['orders'])} orders | n={len(frame)} generations")


def figures(frame: pd.DataFrame, config: dict[str, Any], out_dir: Path) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    focal_id = config["selection"]["focal"]
    references = config["selection"]["references"]
    subtitle = _subtitle(config, frame)

    # --- 1: A-failure rate per arm, focal vs each individual reference -------
    table = condition_table(frame)
    pooled = table.groupby("arm").apply(
        lambda g: pd.Series({
            "a_failure_rate": g["n_a_failures"].sum() / max(g["n_valid"].sum(), 1),
            "n_valid": g["n_valid"].sum()}), include_groups=False).reset_index()
    order = [focal_id, *references]
    pooled = pooled.set_index("arm").loc[order].reset_index()

    fig, ax = plt.subplots(figsize=(9, 5.5))
    colours = ["#c2410c"] + ["#475569"] * len(references)
    bars = ax.bar(pooled["arm"], pooled["a_failure_rate"], color=colours)
    for bar, (_, row) in zip(bars, pooled.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015,
                f"{row['a_failure_rate']:.2f}\n(n={int(row['n_valid'])})",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylabel(f"Failure rate on A ({_a_text(config)})")
    ax.set_xlabel("Instruction added alongside A  —  focal B (orange) vs matched references")
    ax.set_title("Does adding B cost more A-compliance than comparable instructions?\n"
                 + subtitle, fontsize=10)
    ax.set_ylim(0, min(1.0, max(pooled["a_failure_rate"].max() * 1.35, 0.1)))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = out_dir / "fig1_failure_rate_by_arm.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(path)

    # --- 2: paired focal-minus-reference contrasts with bootstrap CIs --------
    contrasts = contrast_table(frame, config)
    pooled_contrasts = contrasts[contrasts["order"] == "pooled"]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    y = np.arange(len(pooled_contrasts))
    ax.errorbar(pooled_contrasts["tau"], y,
                xerr=[pooled_contrasts["tau"] - pooled_contrasts["tau_ci_low"],
                      pooled_contrasts["tau_ci_high"] - pooled_contrasts["tau"]],
                fmt="o", color="#c2410c", capsize=4, markersize=7)
    ax.axvline(0, color="#111827", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"B − {r}" for r in pooled_contrasts["reference"]])
    ax.set_xlabel("tau = paired mean(A-failure with B) − mean(A-failure with reference)\n"
                  "positive = B costs more A-compliance than that reference")
    ax.set_title("Paired focal-minus-reference effect, per reference\n" + subtitle,
                 fontsize=10)
    ax.text(0.99, 0.02, "95% cluster-bootstrap CI over tasks — descriptive, exploratory",
            transform=ax.transAxes, ha="right", fontsize=8, color="#475569")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    path = out_dir / "fig2_paired_contrasts.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(path)

    # --- 3: per-task paired outcomes ----------------------------------------
    fig, axes = plt.subplots(1, len(references), figsize=(4 * len(references), 5),
                             sharey=True)
    axes = np.atleast_1d(axes)
    for ax, reference in zip(axes, references):
        paired = paired_units(frame, focal_id, reference)
        per_task = paired.groupby("task_id_focal")[
            ["a_failure_focal", "a_failure_reference"]].mean()
        for task, row in per_task.iterrows():
            ax.plot([0, 1], [row["a_failure_reference"], row["a_failure_focal"]],
                    marker="o", alpha=0.5,
                    color="#c2410c" if row["a_failure_focal"] > row["a_failure_reference"]
                    else ("#475569" if row["a_failure_focal"] < row["a_failure_reference"]
                          else "#cbd5e1"))
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"A+{reference}", "A+B"])
        ax.set_title(f"B vs {reference}", fontsize=10)
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel("Per-task mean A-failure rate")
    fig.suptitle("Per-task paired outcomes (orange = B worse, grey = reference worse)\n"
                 + subtitle, fontsize=10)
    fig.tight_layout()
    path = out_dir / "fig3_per_task_paired.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(path)

    # --- 4: generated-length diagnostic -------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    contrast_rows = frame[frame["condition"].isin(["focal", "reference"])]
    data = [contrast_rows[contrast_rows["arm"] == arm]["generated_token_count"].dropna()
            for arm in order]
    parts = ax.boxplot(data, tick_labels=order, showmeans=True)
    ax.axhline(config["model"]["max_new_tokens"], color="#b91c1c", linestyle="--",
               linewidth=1, label=f"output cap ({config['model']['max_new_tokens']} tokens)")
    ax.set_ylabel("Generated tokens")
    ax.set_xlabel("Instruction added alongside A")
    ax.set_title("Output-length diagnostic: is response length a competing explanation?\n"
                 + subtitle, fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = out_dir / "fig4_length_diagnostic.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(path)
    return paths


def _a_text(config: dict[str, Any]) -> str:
    n = config.get("harvest_provenance", {}).get("exact_sentence_count", "N")
    return f"exactly {n} sentences"


def analyse(run_dir: Path, n_boot: int = 10000) -> dict[str, Any]:
    """Write every table and figure for one run. Returns the headline numbers."""
    run_dir = Path(run_dir)
    frame, config = load_run(run_dir)
    out = run_dir / "analysis"
    out.mkdir(parents=True, exist_ok=True)

    conditions = condition_table(frame)
    primitives = primitive_table(frame)
    contrasts = contrast_table(frame, config, n_boot=n_boot)
    aggregate = aggregate_contrast(frame, config, n_boot=n_boot)

    conditions.to_csv(out / "table_conditions.csv", index=False)
    primitives.to_csv(out / "table_primitives.csv", index=False)
    contrasts.to_csv(out / "table_contrasts.csv", index=False)
    aggregate.to_csv(out / "table_aggregate.csv", index=False)
    figure_paths = figures(frame, config, out)

    headline = {
        "note": EXPLORATORY_NOTE,
        "run_dir": str(run_dir),
        "n_generations": int(len(frame)),
        "n_technical_failures": int(frame["technical_failure"].sum()),
        "n_unscorable": int((~frame["scorable"] & ~frame["technical_failure"]).sum()),
        "primitive_A_failure_rate": float(
            primitives.set_index("constraint").at[config["selection"]["target"],
                                                  "failure_rate"]),
        "contrasts": contrasts.to_dict("records"),
        "aggregate": aggregate.to_dict("records"),
        "figures": [str(p) for p in figure_paths],
    }
    (out / "headline.json").write_text(json.dumps(headline, indent=2), encoding="utf-8")
    return headline


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Analyse one exploratory run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--n-boot", type=int, default=10000)
    args = parser.parse_args(argv)

    frame, config = load_run(args.run_dir)
    headline = analyse(args.run_dir, n_boot=args.n_boot)

    pd.set_option("display.width", 200)
    print("\n=== CONDITIONS (A-failure by arm) ===")
    print(condition_table(frame).to_string(index=False))
    print("\n=== PRIMITIVES (isolated difficulty) ===")
    print(primitive_table(frame).to_string(index=False))
    print("\n=== PER-REFERENCE CONTRASTS ===")
    print(contrast_table(frame, config, n_boot=args.n_boot).to_string(index=False))
    print("\n=== AGGREGATE ===")
    print(aggregate_contrast(frame, config, n_boot=args.n_boot).to_string(index=False))
    print(f"\n{EXPLORATORY_NOTE}")
    print(f"figures: {headline['figures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
