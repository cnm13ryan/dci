"""Free versus fixed placement of a single mark: does fixing WHERE remove the amplifier?

Round 8 left free placement and single-character atomicity confounded. This
holds the mark fixed and varies only whether its position is chosen or given.

τ is the paired focal−reference difference in A-failure, bootstrapped over tasks.
The comparison of interest is τ(free) − τ(fixed) within one mark, so the free arm
is the length-matched `*_FREE` wording, not Round 8's bare wording.

Manipulation compliance is printed beside every τ: a fixed arm whose own rule
was not followed licenses NO conclusion about placement.
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import extensions, harvest, mechanism

# `runner.run` scores the target and the arm constraint, not the background
# variant, so the manipulation check is scored here from the registry. Doing it
# from the stored response keeps it a property of the preserved generation.
extensions.register()
_STATE = harvest.load()


def score_variant(frame: pd.DataFrame) -> pd.Series:
    """Did each row obey its own background variant?"""
    return pd.Series(
        [_STATE.verify(text, variant).binary_pass if isinstance(text, str) else np.nan
         for text, variant in zip(frame["response"], frame["variant"])],
        index=frame.index, dtype=float)

pd.set_option("display.width", 250)

stage = sys.argv[1] if len(sys.argv) > 1 else "S15_placement_semi"
free_variant = sys.argv[2] if len(sys.argv) > 2 else "X_SEMICOLON_FREE"
run = Path(sorted(glob.glob(f"runs/stage{stage}_*/"))[-1])
frame, _ = mechanism.load(run)
g = frame[frame["condition"].isin(["focal", "reference"])].copy()
g["variant_binary_pass"] = score_variant(g)

tasks = sorted(g["task_id"].unique())
per_task = (g.groupby(["variant", "arm", "task_id"])["a_failure"].mean()
            .unstack("task_id").reindex(columns=tasks))
rng = np.random.default_rng(20260811)


def boot(values: np.ndarray, draws: int = 4000) -> tuple[float, float]:
    idx = rng.integers(0, len(values), size=(draws, len(values)))
    resampled = values[idx].mean(axis=1)
    return float(np.percentile(resampled, 2.5)), float(np.percentile(resampled, 97.5))


rows = []
tau_by_variant = {}
for variant in per_task.index.get_level_values("variant").unique():
    tau = (per_task.loc[(variant, "B")] - per_task.loc[(variant, "C_L3")]).dropna()
    tau_by_variant[variant] = tau
    sub = g[g["variant"] == variant]
    lo, hi = boot(tau.to_numpy(float))
    rows.append({
        "variant": variant,
        "placement": ("free" if variant.endswith("FREE")
                      else "fixed-window" if "FIRST" in variant else "fixed-index"),
        "own_compliance": sub["variant_binary_pass"].mean(),
        "ref_arm_A_fail": sub[sub["arm"] == "C_L3"]["a_failure"].mean(),
        "B_arm_A_fail": sub[sub["arm"] == "B"]["a_failure"].mean(),
        "tau": float(tau.mean()), "lo": lo, "hi": hi,
        "B_sentences": sub[sub["arm"] == "B"]["n_sentences"].mean(),
        "B_chain_share": sub[sub["arm"] == "B"]["chain_share"].mean(),
    })

table = pd.DataFrame(rows).sort_values("tau", ascending=False)
print(f"### {run.name}\n")
order = "/".join(sorted(g["order"].astype(str).unique()))
load = g["load"].iloc[0]
print(f"τ(B→A) by placement condition, π = {order}, k = {load}\n")
print(table.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

print(f"\n\n### Paired contrast against the length-matched free arm ({free_variant})\n")
contrasts = []
for variant, tau in tau_by_variant.items():
    if variant == free_variant:
        continue
    delta = (tau - tau_by_variant[free_variant]).dropna().to_numpy(float)
    lo, hi = boot(delta)
    contrasts.append({"variant": variant, "delta_tau_vs_free": delta.mean(),
                      "lo": lo, "hi": hi,
                      "removes_amplification": "yes" if hi < 0 else "no"})
print(pd.DataFrame(contrasts).to_string(index=False,
                                        float_format=lambda v: f"{v:+.3f}"))

print("\n\n### Task-level heterogeneity of τ (min / median / max per variant)\n")
het = pd.DataFrame({v: [t.min(), t.median(), t.max()] for v, t in tau_by_variant.items()},
                   index=["min", "median", "max"]).T
print(het.to_string(float_format=lambda v: f"{v:+.3f}"))
