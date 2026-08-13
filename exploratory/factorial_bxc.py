"""R6-B: the B x colon 2x2, with both interaction estimates and a manip check."""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 240)

cells, boot = {}, {}
for d in sorted(glob.glob("runs/stageR6B_load*/")):
    f, c = mechanism.load(Path(d))
    tag = "withC" if c["selection"]["background"] else "noC"
    contrast = f[f["condition"].isin(["focal", "reference"])]
    for arm, g in contrast.groupby("arm"):
        cells[(tag, arm)] = g["a_failure"].mean()
        boot[(tag, arm)] = g.set_index("pair_key")["a_failure"]
    prim = f[(f["condition"] == "primitive") & (f["arm"] == c["selection"]["target"])]
    cells[(tag, "A_alone")] = prim["a_failure"].mean()
    # manipulation check
    print(f"{tag}: colons produced per arm — "
          + ", ".join(f"{a}={g['n_colons'].mean():.2f}"
                      for a, g in contrast.groupby("arm")))

print("\n### the four cells (A-failure, both orders pooled)\n")
print(f"  F(A)            = {cells[('noC','A_alone')]:.3f}   (target alone, load 1)")
print(f"  F(A+B)          = {cells[('noC','B')]:.3f}")
print(f"  F(A+ctrl)       = {cells[('noC','C_L3')]:.3f}   (C_L3 as inert filler)")
print(f"  F(A+C)          = {cells[('noC','U_FMT_COLON1')]:.3f}")
print(f"  F(A+C+B)        = {cells[('withC','B')]:.3f}")
print(f"  F(A+C+ctrl)     = {cells[('withC','C_L3')]:.3f}")
print(f"  F(A+semi)       = {cells[('noC','S_SEMICOLON')]:.3f}   positive control, load 2")
print(f"  F(A+C+semi)     = {cells[('withC','S_SEMICOLON')]:.3f}   positive control, load 3")

raw = ((cells[("withC", "B")] - cells[("noC", "U_FMT_COLON1")])
       - (cells[("noC", "B")] - cells[("noC", "A_alone")]))
matched = ((cells[("withC", "B")] - cells[("withC", "C_L3")])
           - (cells[("noC", "B")] - cells[("noC", "C_L3")]))
print(f"\n  raw interaction      [F(A+C+B)-F(A+C)] - [F(A+B)-F(A)]           = {raw:+.3f}")
print(f"  count-matched        [F(A+C+B)-F(A+C+ctrl)] - [F(A+B)-F(A+ctrl)] = {matched:+.3f}")

# cluster bootstrap on the count-matched interaction, pairing within run on task
rng = np.random.default_rng(20260811)
tasks = sorted({k.split("|")[0] for k in boot[("withC", "B")].index})
def cell_mean(tag, arm, picked):
    s = boot[(tag, arm)]
    vals = [s[[k for k in s.index if k.startswith(t + "|")]] for t in picked]
    return float(pd.concat(vals).mean())
draws = []
for _ in range(4000):
    picked = list(rng.choice(tasks, size=len(tasks), replace=True))
    draws.append((cell_mean("withC", "B", picked) - cell_mean("withC", "C_L3", picked))
                 - (cell_mean("noC", "B", picked) - cell_mean("noC", "C_L3", picked)))
print(f"  count-matched 95% CI = [{np.percentile(draws,2.5):+.3f}, "
      f"{np.percentile(draws,97.5):+.3f}]  (cluster bootstrap over {len(tasks)} tasks)")
