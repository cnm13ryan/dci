"""Is `splice_share` a strategy measure independent of the sentence-count outcome?

The test the definition has to pass is not that the two correlate. It is that
they can COME APART: a condition with a high splice share and no target failure
proves the measure is not a redescription of the failure.
"""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 250)

rows = []
for d in sorted(glob.glob("runs/stage*/")):
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    unit = f.attrs.get("unit", "n_sentences")
    sub = f[f["condition"].isin(["focal", "reference", "primitive"])]
    for (cond, arm), g in sub.groupby(["condition", "arm"]):
        g = g[g["splice_share"].notna()]
        if not len(g):
            continue
        rows.append({
            "run": c["stage"], "model": c["model"]["model_id"].split("/")[-1],
            "target": c["selection"]["target"], "cond": cond, "arm": arm,
            "n": len(g),
            "splice_share": g["splice_share"].mean(),
            "semi_splices": g["n_semi_splices"].mean(),
            "units": g[unit].mean() if unit in g else np.nan,
            "failure": g["a_failure"].mean() if cond != "primitive" else np.nan})
out = pd.DataFrame(rows)

print("### the decisive cells: HIGH splice share, LOW target failure\n")
hi = out[(out["splice_share"] > 0.30) & out["failure"].notna()].sort_values("failure")
print(hi[["run", "model", "target", "arm", "n", "splice_share", "units", "failure"]]
      .head(14).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("\n### and the converse: LOW splice share, HIGH failure\n")
lo = out[(out["splice_share"] < 0.10) & (out["failure"] > 0.20)]
print(lo[["run", "model", "target", "arm", "n", "splice_share", "units", "failure"]]
      .to_string(index=False, float_format=lambda v: f"{v:.3f}") if len(lo) else "  (none)")

print("\n### correlation across all contrast cells (descriptive)\n")
c = out[out["failure"].notna()]
print(f"  cells={len(c)}  pearson(splice_share, failure) = "
      f"{c['splice_share'].corr(c['failure']):+.3f}")
print("  (a correlation is expected; the point of the two tables above is that "
      "the measure is not FORCED to it by arithmetic)")
