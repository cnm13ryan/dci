"""Round 10: score and analyse the new reasoning conditions.

Generalises the S18 analysis over (amplifier, control) pairs so the placement,
ordering and load experiments are read by the same code, with the same paired
task-cluster bootstrap, rather than by four near-copies.

Everything is rebuilt from the stored generations, ANSWER field only. The
reasoning channel is never scored.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dci_exploratory import plotdata, plotstyle

pd.set_option("display.width", 260)


def latest(pattern: str) -> Path:
    return Path(sorted(glob.glob(pattern))[-1])


def load(*paths: Path) -> pd.DataFrame:
    """Score one or more generation files as a single experiment."""
    frames = []
    for path in paths:
        frame = plotdata.load_reasoning(path)
        frame["source"] = path.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def gate(frame: pd.DataFrame) -> pd.DataFrame:
    """The validity gate. A budget that fails this does not enter a curve."""
    return frame.groupby("reasoning_budget").agg(
        n=("answer", "size"), cap_hit=("reasoning_cap_hit", "mean"),
        closed=("closed_naturally", "mean"),
        realised_M=("reasoning_tokens", "mean"),
        answer_tokens=("answer_tokens", "mean"),
        truncated=("answer_truncated", "mean"), empty=("answer_empty", "mean"),
        scratch=("scratch_marker", "mean"))


def curve(frame: pd.DataFrame, amp: str, ctrl: str, label: str) -> pd.DataFrame:
    """τ per (budget, background) plus the paired Δ, with intervals."""
    records = []
    for budget in sorted(frame["reasoning_budget"].unique()):
        cell = frame[frame["reasoning_budget"] == budget]
        taus = {}
        for variant in (ctrl, amp):
            sub = cell[cell["variant"] == variant]
            taus[variant] = plotstyle.per_task_tau(sub)
            stats = plotstyle.summarise(taus[variant], f"{label}|tau|{budget}|{variant}")
            focal = sub[sub["arm"] == "B"]
            reference = sub[sub["arm"] != "B"]
            records.append({
                "b": budget, "variant": variant, "tau": stats["estimate"],
                "lo": stats["lo"], "hi": stats["hi"],
                "focal_A_fail": focal["a_failure"].mean(),
                "ref_A_fail": reference["a_failure"].mean(),
                "A_compliance_focal": focal["a_pass"].mean(),
                "C_compliance": sub["c_pass"].mean(),
                "joint_focal": focal["joint"].mean(),
                "cap_hit": sub["reasoning_cap_hit"].mean(),
                "realised_M": sub["reasoning_tokens"].mean()})
        delta = (taus[amp] - taus[ctrl]).dropna()
        stats = plotstyle.summarise(delta, f"{label}|delta|{budget}")
        records.append({"b": budget, "variant": "DELTA (amp − ctrl)",
                        "tau": np.nan, "lo": np.nan, "hi": np.nan,
                        "delta": stats["estimate"], "d_lo": stats["lo"],
                        "d_hi": stats["hi"]})
    return pd.DataFrame(records)


def arbitration(frame: pd.DataFrame) -> pd.DataFrame:
    focal = frame[frame["arm"] == "B"]
    return (pd.crosstab([focal["variant"], focal["reasoning_budget"]],
                        focal["arbitration"], normalize="index")
            .reindex(columns=list(plotstyle.ARBITRATION_ORDER), fill_value=0.0))


def show(title: str, frame: pd.DataFrame, amp: str, ctrl: str, label: str) -> pd.DataFrame:
    print(f"\n{'=' * 100}\n### {title}\n")
    print("VALIDITY GATE")
    print(gate(frame).to_string(float_format=lambda v: f"{v:.3f}"))
    table = curve(frame, amp, ctrl, label)
    print(f"\nτ(B→A) and Δ   [amplifier = {amp} · control = {ctrl}]")
    print(table.to_string(index=False, float_format=lambda v: f"{v:+.3f}", na_rep=""))
    print("\nARBITRATION (focal arm B)")
    print(arbitration(frame).to_string(float_format=lambda v: f"{v:.3f}"))
    return table


def main() -> int:
    runs = {}
    s18 = latest("runs/stageS18_reasoning_design_*/")
    # The re-seeded grid, and only it. This cell used to load
    # `s18_reasoning.jsonl` and append `s18_transition.jsonl`: the first shares
    # one seed across all 160 requests (390/400 byte-identical replicate pairs)
    # and the second is 98.4% duplicate pairs, so the curve mixed two sampling
    # regimes. `plotdata.load_reasoning` now refuses both by name. The transition
    # budgets have no re-seeded replacement and were deprecated as curve-shape
    # evidence, so the cell no longer advertises them in its label.
    runs["S18 · QAC k=3"] = (
        load(s18 / "s18_reseeded.jsonl"), plotstyle.AMP, plotstyle.CTRL, "s18")

    for pattern, name, amp, ctrl, tag in (
            ("runs/stageS25_placement_reasoning_*/", "S25 placement × reasoning · QAC k=3",
             "X_ANCHOR_HOWEVER_FREE2", "X_ANCHOR_HOWEVER_BEFORE2", "s25"),
            ("runs/stageS26_reasoning_ACQ_*/", "S26 reasoning × ACQ order · k=3",
             plotstyle.AMP, plotstyle.CTRL, "s26"),
            ("runs/stageS27_reasoning_k5_*/", "S27 reasoning × load k=5 · QAC",
             plotstyle.AMP, plotstyle.CTRL, "s27")):
        run = latest(pattern)
        found = sorted(run.glob("*_reasoning.jsonl"))
        if not found:
            print(f"[skip] {name}: no generations yet")
            continue
        runs[name] = (load(*found), amp, ctrl, tag)

    tables = {}
    for name, (frame, amp, ctrl, tag) in runs.items():
        tables[name] = show(name, frame, amp, ctrl, tag)

    out = Path("figures/reasoning_compute/data")
    out.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.assign(experiment=name).to_csv(
            out / f"round10_{name.split()[0].lower()}.csv", index=False)
    print(f"\nwrote {len(tables)} tidy tables to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
