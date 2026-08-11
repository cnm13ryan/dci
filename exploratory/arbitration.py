"""R6-C: decompose each model into disposition / competence / arbitration.

Deliberately NOT a single 'does it replicate' number. The 2x2 of (target met) x
(semicolon instruction met) says WHICH instruction gave way, which an excess
figure cannot.
"""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 250)

SEMI = ("X_SEMICOLON_TOTAL4", "X_SEMICOLON_EACH")
rows, arb = [], []
dirs = sorted(glob.glob("runs/stageR6C_*nothink*/") + glob.glob("runs/stageR6C_qwen3_4b_*/")) + sorted(glob.glob("runs/stageE6_gemma_*/"))
for d in dirs:
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    model = c["model"]["model_id"]
    prim = f[f["condition"] == "primitive"]
    target = c["selection"]["target"]
    comp = prim[prim["arm"] == target]["a_failure"].mean()
    ex = mechanism.paired_excess(f, "C_L3", "a_failure", by=["order"], n_boot=4000)
    ex = ex.groupby("arm")["excess"].mean().to_frame("excess") if len(ex) else None

    contrast = f[f["condition"].isin(["focal", "reference"])]
    for arm in SEMI + ("X_COMMA_TOTAL4",):
        g = contrast[contrast["arm"] == arm]
        p = prim[prim["arm"] == arm]
        if not len(g):
            continue
        rows.append({
            "model": model.split("/")[-1], "arm": arm,
            "D_m sentences alone": p["n_sentences"].mean(),
            "D_m chain alone": p["chain_share"].mean(),
            "target competence (fail)": comp,
            "joint target fail": g["a_failure"].mean(),
            "excess": ex.loc[arm, "excess"] if ex is not None and arm in ex.index else np.nan,
            "joint semicolon compliance": g["arm_binary_pass"].mean(),
            "sentences": g["n_sentences"].mean(),
            "semis": g["n_semicolons"].mean(),
            "chain": g["chain_share"].mean(),
            "words": g["n_words"].mean()})
        if arm in SEMI:
            ok_t = g["a_failure"] == 0
            ok_a = g["arm_binary_pass"] == 1
            n = len(g)
            arb.append({"model": model.split("/")[-1], "arm": arm, "n": n,
                        "both met": (ok_t & ok_a).mean(),
                        "target only (arm sacrificed)": (ok_t & ~ok_a).mean(),
                        "arm only (TARGET sacrificed)": (~ok_t & ok_a).mean(),
                        "neither": (~ok_t & ~ok_a).mean()})

print("### per-model decomposition\n")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\n### ARBITRATION under conflict — which instruction gives way?\n")
print(pd.DataFrame(arb).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
