"""The q x N phase diagram: failure and chain_share on the (q, N) grid."""
import glob, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 240)

def q_of(arm):
    m = re.match(r"X_SEMICOLON_TOTAL(\d+)$", arm)
    if m:
        return int(m.group(1))
    return 0 if arm in ("X_COMMA_TOTAL4", "C_L3") else None

rows, prims = [], []
for d in sorted(glob.glob("runs/stageR6A_N*/")) + sorted(glob.glob("runs/stageE4b_totals_*/")):
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    N = f.attrs["n_target"]
    ex = mechanism.paired_excess(f, "C_L3", "a_failure", by=["order"],
                                 n_boot=4000).set_index(["order", "arm"])
    ct = mechanism.cell_table(f, ["arm"]).set_index("arm")
    for arm in ct.index:
        q = q_of(arm)
        if q is None:
            continue
        exc = np.mean([ex.loc[(o, arm), "excess"] for o in ("o_A", "o_Q")
                       if (o, arm) in ex.index]) if arm != "C_L3" else 0.0
        rows.append({"run": c["stage"], "N": N, "arm": arm, "q": q,
                     "failure": ct.loc[arm, "a_failure"],
                     "excess": exc,
                     "chain_share": ct.loc[arm, "mean_chain_share"],
                     "sentences": ct.loc[arm, "mean_n_sentences"],
                     "semis": ct.loc[arm, "mean_n_semicolons"],
                     "arm_ok": ct.loc[arm, "arm_compliance"]})
    p = f[f["condition"] == "primitive"]
    for arm, g in p.groupby("arm"):
        if q_of(arm) is None and arm != c["selection"]["target"]:
            continue
        prims.append({"run": c["stage"], "arm": arm, "q": q_of(arm),
                      "sentences": g["n_sentences"].mean(),
                      "chain_share": g["chain_share"].mean(),
                      "own_failure": g["a_failure"].mean()})

out = pd.DataFrame(rows)
sem = out[out["arm"].str.startswith("X_SEMICOLON")]
print("### A-FAILURE on the (q, N) grid — semicolon floors, both orders pooled\n")
print(sem.pivot_table(index="q", columns="N", values="failure")
      .to_string(float_format=lambda v: f"{v:.3f}"))
print("\n### paired EXCESS over C_L3 on the same grid\n")
print(sem.pivot_table(index="q", columns="N", values="excess")
      .to_string(float_format=lambda v: f"{v:+.3f}"))
print("\n### CHAIN_SHARE (the strategy) on the same grid\n")
print(sem.pivot_table(index="q", columns="N", values="chain_share")
      .to_string(float_format=lambda v: f"{v:.3f}"))
print("\n### mean SENTENCES produced\n")
print(sem.pivot_table(index="q", columns="N", values="sentences")
      .to_string(float_format=lambda v: f"{v:.2f}"))
print("\n### the q = 0 controls (must be flat and low)\n")
print(out[out["q"] == 0].pivot_table(index="arm", columns="N", values="failure")
      .to_string(float_format=lambda v: f"{v:.3f}"))
if prims:
    print("\n### isolated primitives (arm alone; N-independent by construction)\n")
    print(pd.DataFrame(prims).groupby("arm")
          .agg(runs=("run", "size"), sentences=("sentences", "mean"),
               chain=("chain_share", "mean"), own_fail=("own_failure", "mean"))
          .to_string(float_format=lambda v: f"{v:.3f}"))
