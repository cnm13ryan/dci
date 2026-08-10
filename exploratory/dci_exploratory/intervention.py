"""Read out the two discriminating interventions.

D2 (anti-collapse scaffold): does removing the suspected mediator remove the
effect? The readout is NOT whether A-failure falls — a scaffold that makes
segmentation easier should lower it everywhere. The readout is whether the
EXCESS of B and S_SEMICOLON over the low-interference reference shrinks.

D3 (semicolon variants): which property of "a semicolon in every sentence" does
the damage — the mark, the per-sentence scope, or generic formatting burden?
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from dci_exploratory.analysis import _bootstrap_ci
from dci_exploratory.forensics import classify_failure, structural_features


def _prepared(run_dir: Path) -> tuple[pd.DataFrame, dict[str, Any], int]:
    run_dir = Path(run_dir)
    frame = pd.read_json(run_dir / "generations.jsonl", lines=True)
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    n_target = int(config["harvest_provenance"]["exact_sentence_count"])
    feats = structural_features(frame[frame["condition"].isin(["focal", "reference"])])
    feats = feats[feats["scorable"]].copy()
    feats["collapse"] = feats["observed_sentences"] <= 2
    feats["mode"] = feats.apply(classify_failure, axis=1, n_target=n_target)
    if "scaffold" not in feats.columns:
        feats["scaffold"] = ""
    feats["scaffold"] = feats["scaffold"].fillna("")
    return feats, config, n_target


def cell_table(run_dir: Path) -> pd.DataFrame:
    """A-failure, collapse and structure per (scaffold, order, arm)."""
    feats, _, _ = _prepared(run_dir)
    rows = []
    for (scaffold, order, arm), group in feats.groupby(["scaffold", "order", "arm"]):
        rows.append({
            "scaffold": scaffold or "none", "order": order, "arm": arm,
            "n": len(group),
            "a_failure_rate": float(group["a_failure"].mean()),
            "collapse_rate": float(group["collapse"].mean()),
            "overshoot_rate": float((group["observed_sentences"] > 4).mean()),
            "mean_periods": float(group["n_periods"].mean()),
            "mean_semicolons": float(group["n_semicolons"].mean()),
            "mean_newlines": float(group["n_newlines"].mean()),
            "mean_tokens": float(group["generated_token_count"].mean()),
        })
    return pd.DataFrame(rows).sort_values(["scaffold", "order", "arm"])


def excess_over_control(run_dir: Path, control: str = "C_L3",
                        n_boot: int = 10000) -> pd.DataFrame:
    """Paired excess A-failure of each arm over the control, within scaffold.

    Paired on `pair_key` so the control row shares the task, order, replicate and
    system message. This is the quantity D2 is designed to move.
    """
    feats, _, _ = _prepared(run_dir)
    rows = []
    for (scaffold, order), group in feats.groupby(["scaffold", "order"]):
        control_rows = group[group["arm"] == control].set_index("pair_key")
        for arm in sorted(group["arm"].unique()):
            if arm == control:
                continue
            arm_rows = group[group["arm"] == arm].set_index("pair_key")
            keys = sorted(set(arm_rows.index) & set(control_rows.index))
            if not keys:
                continue
            diffs = (arm_rows.loc[keys, "a_failure"].to_numpy(float)
                     - control_rows.loc[keys, "a_failure"].to_numpy(float))
            clusters = arm_rows.loc[keys, "task_id"].to_numpy()
            low, high = _bootstrap_ci(diffs, clusters, n_boot=n_boot)
            rows.append({
                "scaffold": scaffold or "none", "order": order, "arm": arm,
                "control": control, "n_pairs": len(keys),
                "arm_failure": float(arm_rows.loc[keys, "a_failure"].mean()),
                "control_failure": float(control_rows.loc[keys, "a_failure"].mean()),
                "excess": float(diffs.mean()),
                "ci_low": low, "ci_high": high,
            })
    return pd.DataFrame(rows)


def scaffold_effect(run_dir: Path, n_boot: int = 10000) -> pd.DataFrame:
    """Within arm and order, what did the scaffold do?

    Not paired at the row level — the scaffold changes the generation, so the
    scaffolded and unscaffolded rows for one (task, replicate) are different
    draws. Clustered on task, which is the unit uncertainty is quoted over.
    """
    feats, _, _ = _prepared(run_dir)
    rows = []
    for (arm, order), group in feats.groupby(["arm", "order"]):
        base = group[group["scaffold"] == ""]
        scaffolded = group[group["scaffold"] != ""]
        if base.empty or scaffolded.empty:
            continue
        # Task-mean difference, so the bootstrap resamples whole tasks.
        base_by_task = base.groupby("task_id")["a_failure"].mean()
        scaf_by_task = scaffolded.groupby("task_id")["a_failure"].mean()
        shared = sorted(set(base_by_task.index) & set(scaf_by_task.index))
        diffs = (scaf_by_task.loc[shared].to_numpy(float)
                 - base_by_task.loc[shared].to_numpy(float))
        low, high = _bootstrap_ci(diffs, np.array(shared), n_boot=n_boot)
        rows.append({
            "arm": arm, "order": order, "n_tasks": len(shared),
            "failure_without_scaffold": float(base["a_failure"].mean()),
            "failure_with_scaffold": float(scaffolded["a_failure"].mean()),
            "delta": float(diffs.mean()), "ci_low": low, "ci_high": high,
            "collapse_without": float(base["collapse"].mean()),
            "collapse_with": float(scaffolded["collapse"].mean()),
        })
    return pd.DataFrame(rows)


def mode_table(run_dir: Path) -> pd.DataFrame:
    feats, _, _ = _prepared(run_dir)
    return (feats.groupby(["scaffold", "order", "arm", "mode"]).size()
            .unstack("mode", fill_value=0))


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Read out an intervention run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--control", default="C_L3")
    parser.add_argument("--n-boot", type=int, default=10000)
    args = parser.parse_args(argv)
    pd.set_option("display.width", 240)

    cells = cell_table(args.run_dir)
    excess = excess_over_control(args.run_dir, args.control, args.n_boot)
    modes = mode_table(args.run_dir)

    print("\n=== CELLS ===")
    print(cells.round(4).to_string(index=False))
    print(f"\n=== PAIRED EXCESS OVER {args.control} (positive = arm costs more A) ===")
    print(excess.round(4).to_string(index=False))
    print("\n=== FAILURE MODES ===")
    print(modes.to_string())

    out = Path(args.run_dir) / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    cells.to_csv(out / "intervention_cells.csv", index=False)
    excess.to_csv(out / "intervention_excess.csv", index=False)
    modes.to_csv(out / "intervention_modes.csv")

    config = json.loads((Path(args.run_dir) / "config.json").read_text(encoding="utf-8"))
    if len(config.get("scaffolds", [""])) > 1:
        effect = scaffold_effect(args.run_dir, args.n_boot)
        print("\n=== SCAFFOLD EFFECT (with minus without) ===")
        print(effect.round(4).to_string(index=False))
        effect.to_csv(out / "intervention_scaffold_effect.csv", index=False)
    print(f"\nartifacts: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
