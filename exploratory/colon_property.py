"""Which property of the colon instruction amplifies B -> A?"""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 250)

f, c = mechanism.load(Path(sorted(glob.glob("runs/stageS14_markproperty_*/"))[-1]))
g = f[f["condition"].isin(["focal", "reference"])].copy()
BASE = "U_FMT_PAREN1"
tasks = sorted(g["task_id"].unique())
pt = (g.groupby(["variant", "arm", "task_id"])["a_failure"].mean()
      .unstack("task_id").reindex(columns=tasks))
rng = np.random.default_rng(20260811)
rows = []
for v in g["variant"].unique():
    tau = (pt.loc[(v, "B")] - pt.loc[(v, "C_L3")])
    sub = g[(g["variant"] == v)]
    d = (tau - (pt.loc[(BASE, "B")] - pt.loc[(BASE, "C_L3")])).dropna()
    vals = d.to_numpy(float)
    idx = rng.integers(0, len(vals), size=(4000, len(vals)))
    dr = vals[idx].mean(axis=1)
    rows.append({
        "variant": v,
        "object": ("single char" if v in ("U_FMT_COLON1", "X_SEMI_EXACT1")
                   else "paired construct"),
        "B_fail": sub[sub["arm"] == "B"]["a_failure"].mean(),
        "ctl_fail": sub[sub["arm"] == "C_L3"]["a_failure"].mean(),
        "tau": float(tau.mean()),
        "Delta_vs_paren": vals.mean(),
        "lo": np.percentile(dr, 2.5), "hi": np.percentile(dr, 97.5),
        "variant_compliance": sub["variant_binary_pass"].mean()
        if "variant_binary_pass" in sub else np.nan,
        "B_chain": sub[sub["arm"] == "B"]["chain_share"].mean(),
        "B_sent": sub[sub["arm"] == "B"]["n_sentences"].mean()})
out = pd.DataFrame(rows).sort_values("tau", ascending=False)
print("### QAC, k=3: tau(B->A) under four matched exactly-one background variants\n")
print(out.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
