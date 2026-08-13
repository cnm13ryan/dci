"""Compute-response curves for the reasoning-budget experiment.

Empirical points with uncertainty. No curve is fitted, nothing is extrapolated
beyond the tested range, and monotonicity is never assumed — the b = 256 dip is
drawn as observed.

Assigned budget is the causal x-axis and gets its own panels; realised reasoning
and wall-clock are post-treatment and appear only on panels labelled descriptive.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PATH = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("figures/reasoning_compute.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

frame = pd.read_json(PATH, lines=True)
AMP, CTRL = "X_SEMICOLON_FREE", "X_PAREN_FREE"
LABEL = {AMP: "amplifier (exactly 1 semicolon)", CTRL: "control (exactly 1 bracket pair)"}
COLOR = {AMP: "#c0392b", CTRL: "#2c6fbb"}
budgets = sorted(frame["reasoning_budget"].unique())
rng = np.random.default_rng(20260811)


def boot(values, draws=4000):
    values = np.asarray(values, float)
    if len(values) == 0:
        return np.nan, np.nan
    idx = rng.integers(0, len(values), size=(draws, len(values)))
    resampled = values[idx].mean(axis=1)
    return np.percentile(resampled, 2.5), np.percentile(resampled, 97.5)


def cluster_rate(sub, column):
    """Task-clustered mean and interval for a 0/1 column."""
    per_task = sub.groupby("task_id")[column].mean().to_numpy(float)
    return per_task.mean(), *boot(per_task)


x = np.arange(len(budgets))
labels = [("0\n(native\nno-think)" if b == 0 else str(b)) for b in budgets]
fig, axes = plt.subplots(2, 4, figsize=(20, 9))

# --- row 1: compliance curves, focal (B) arm -------------------------------
panels = [("a_pass", "P(A compliant) — target"),
          ("arm_pass", "P(B compliant) — focal"),
          ("c_pass", "P(C compliant) — background"),
          ("joint", "P(A and B and C) — joint")]
for ax, (column, title) in zip(axes[0], panels):
    for variant in (AMP, CTRL):
        means, los, his = [], [], []
        for b in budgets:
            sub = frame[(frame["reasoning_budget"] == b)
                        & (frame["variant"] == variant) & (frame["arm"] == "B")]
            m, lo, hi = cluster_rate(sub, column)
            means.append(m), los.append(lo), his.append(hi)
        ax.errorbar(x, means, yerr=[np.array(means) - los, np.array(his) - means],
                    marker="o", capsize=3, color=COLOR[variant], label=LABEL[variant])
    ax.set_title(title + "\n(focal arm B)", fontsize=10)
    ax.set_xticks(x), ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(-0.05, 1.05), ax.grid(alpha=.3)
    ax.set_xlabel("assigned reasoning budget b (causal)")
axes[0][0].set_ylabel("compliance rate")
axes[0][0].legend(fontsize=8, loc="lower right")

# --- row 2 panel 1: the interference curve ---------------------------------
ax = axes[1][0]
per_task = (frame.groupby(["reasoning_budget", "variant", "arm", "task_id"])
            ["a_failure"].mean())
tau_store = {}
for variant in (AMP, CTRL):
    means, los, his = [], [], []
    for b in budgets:
        tau = (per_task.loc[(b, variant, "B")] - per_task.loc[(b, variant, "C_L3")]).dropna()
        tau_store[(b, variant)] = tau
        means.append(tau.mean())
        lo, hi = boot(tau.to_numpy(float))
        los.append(lo), his.append(hi)
    ax.errorbar(x, means, yerr=[np.array(means) - los, np.array(his) - means],
                marker="o", capsize=3, color=COLOR[variant], label=LABEL[variant])
ax.axhline(0, color="k", lw=.8)
ax.set_title("τ(B→A): directional interference", fontsize=10)
ax.set_xticks(x), ax.set_xticklabels(labels, fontsize=8), ax.grid(alpha=.3)
ax.set_ylabel("τ = paired excess A-failure"), ax.legend(fontsize=8)
ax.set_xlabel("assigned reasoning budget b (causal)")

# --- row 2 panel 2: the amplification curve --------------------------------
ax = axes[1][1]
means, los, his = [], [], []
for b in budgets:
    delta = (tau_store[(b, AMP)] - tau_store[(b, CTRL)]).dropna().to_numpy(float)
    means.append(delta.mean())
    lo, hi = boot(delta)
    los.append(lo), his.append(hi)
ax.errorbar(x, means, yerr=[np.array(means) - los, np.array(his) - means],
            marker="s", capsize=3, color="#7d3c98")
ax.axhline(0, color="k", lw=.8)
ax.set_title("Δ amplification = τ(amplifier) − τ(control)", fontsize=10)
ax.set_xticks(x), ax.set_xticklabels(labels, fontsize=8), ax.grid(alpha=.3)
ax.set_ylabel("Δ"), ax.set_xlabel("assigned reasoning budget b (causal)")

# --- row 2 panel 3: arbitration --------------------------------------------
ax = axes[1][2]
b_arm = frame[frame["arm"] == "B"].copy()
b_arm["state"] = np.select(
    [(b_arm["a_pass"] == 1) & (b_arm["arm_pass"] == 1),
     (b_arm["a_pass"] == 1) & (b_arm["arm_pass"] == 0),
     (b_arm["a_pass"] == 0) & (b_arm["arm_pass"] == 1)],
    ["both", "target only", "focal only"], default="neither")
styles = {"both": "-", "target only": "--", "focal only": ":", "neither": "-."}
for variant in (AMP, CTRL):
    for state, style in styles.items():
        rates = [(b_arm[(b_arm["reasoning_budget"] == b)
                        & (b_arm["variant"] == variant)]["state"] == state).mean()
                 for b in budgets]
        ax.plot(x, rates, style, color=COLOR[variant], marker=".",
                label=f"{state} · {'amp' if variant == AMP else 'ctl'}")
ax.set_title("Conflict arbitration (focal arm B)", fontsize=10)
ax.set_xticks(x), ax.set_xticklabels(labels, fontsize=8), ax.grid(alpha=.3)
ax.set_ylabel("P(state)"), ax.legend(fontsize=6, ncol=2)
ax.set_xlabel("assigned reasoning budget b (causal)")

# --- row 2 panel 4: DESCRIPTIVE, realised reasoning ------------------------
ax = axes[1][3]
for variant in (AMP, CTRL):
    for arm, marker in (("B", "o"), ("C_L3", "^")):
        sub = frame[(frame["variant"] == variant) & (frame["arm"] == arm)]
        realised = [sub[sub["reasoning_budget"] == b]["reasoning_tokens"].mean()
                    for b in budgets]
        failure = [sub[sub["reasoning_budget"] == b]["a_failure"].mean()
                   for b in budgets]
        ax.plot(realised, failure, marker=marker, color=COLOR[variant], alpha=.8,
                label=f"{'amp' if variant == AMP else 'ctl'} · {arm}")
ax.set_title("DESCRIPTIVE ONLY: A-failure vs REALISED reasoning M\n"
             "(M is post-treatment — not randomly assigned)", fontsize=9)
ax.set_xlabel("realised reasoning tokens M"), ax.set_ylabel("A-failure rate")
ax.grid(alpha=.3), ax.legend(fontsize=7)

fig.suptitle("Test-time reasoning compute and directional constraint interference\n"
             "Qwen3-4B (thinking), vLLM 0.15.1+rocm720, TP=2, bf16, T=0.7 — "
             "π = QAC, k = 3, 20 tasks × 2 replicates, 800 generations",
             fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print("wrote", OUT)
