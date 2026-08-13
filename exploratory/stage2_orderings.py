"""Stage 2 — the full S3 ordering surface, inspected before any pooling."""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 260)

f, c = mechanism.load(Path(glob.glob("runs/stageS2_orderings_*/")[0]))
g = f[f["condition"].isin(["focal", "reference"])].copy()
COLON, PAREN = "U_FMT_COLON1", "U_FMT_PAREN1"

# --- cell means ------------------------------------------------------------
cells = g.groupby(["order", "variant", "arm"]).agg(
    n=("row_id", "size"), fail=("a_failure", "mean"),
    armok=("arm_binary_pass", "mean"), sent=("n_sentences", "mean"),
    colons=("n_colons", "mean"), semis=("n_semicolons", "mean"),
    commas=("n_commas", "mean"), chain=("chain_share", "mean"),
    comma_spl=("n_comma_splices", "mean"), words=("n_words", "mean"))
print("### every cell, unpooled\n")
print(cells.to_string(float_format=lambda v: f"{v:.3f}"))

# --- manipulation check ----------------------------------------------------
print("\n### manipulation check: was the colon delivered?\n")
print(g.groupby("variant")[["n_colons"]].mean()
      .to_string(float_format=lambda v: f"{v:.3f}"))

# --- the per-permutation higher-order interaction ---------------------------
def mean_of(order, variant, arm, keys=None):
    s = g[(g["order"] == order) & (g["variant"] == variant) & (g["arm"] == arm)]
    if keys is not None:
        s = s[s["task_id"].isin(keys)]
    return s["a_failure"].mean()

rng = np.random.default_rng(20260811)
tasks = sorted(g["task_id"].unique())
# per-task cell means, so the bootstrap is a matrix op rather than 4000 regroups
per_task = (g.groupby(["order", "variant", "arm", "task_id"])["a_failure"]
            .mean().unstack("task_id").reindex(columns=tasks))
rows = []
for order in sorted(g["order"].unique()):
    d_task = ((per_task.loc[(order, COLON, "B")] - per_task.loc[(order, COLON, "C_L3")])
              - (per_task.loc[(order, PAREN, "B")] - per_task.loc[(order, PAREN, "C_L3")]))
    values = d_task.to_numpy(dtype=float)
    tau_c = float((per_task.loc[(order, COLON, "B")]
                   - per_task.loc[(order, COLON, "C_L3")]).mean())
    tau_p = float((per_task.loc[(order, PAREN, "B")]
                   - per_task.loc[(order, PAREN, "C_L3")]).mean())
    idx = rng.integers(0, len(values), size=(4000, len(values)))
    draws = values[idx].mean(axis=1)
    rows.append({"perm": order,
                 "A_pos": order.index("A") + 1, "Q_pos": order.index("Q") + 1,
                 "C_pos": order.index("C") + 1,
                 "tau|colon": tau_c, "tau|paren": tau_p,
                 "Delta": tau_c - tau_p,
                 "lo": np.percentile(draws, 2.5), "hi": np.percentile(draws, 97.5)})
d = pd.DataFrame(rows).sort_values("Delta", ascending=False)
print("\n### the six order-specific higher-order interactions\n")
print(d.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
