"""Stage 1 — does the q~3 transition survive greedy decoding?"""
import glob, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 250)

def q_of(a):
    m = re.match(r"X_SEMICOLON_TOTAL(\d+)$", a)
    return int(m.group(1)) if m else (0 if a == "C_L3" else None)

runs = {"T=0.0 (greedy)": glob.glob("runs/stageS1_Tgreedy_*/")[0],
        "T=0.3": glob.glob("runs/stageS1_Tt03_*/")[0],
        "T=0.7": glob.glob("runs/stageR6A_N4_*/")[0]}
rows, dist = [], []
for label, d in runs.items():
    f, c = mechanism.load(Path(d))
    cfg = c["model"]
    contrast = f[f["condition"].isin(["focal", "reference"])]
    for arm, g in contrast.groupby("arm"):
        q = q_of(arm)
        if q is None or q not in (0, 2, 3, 4):
            continue
        rows.append({"decoding": label, "do_sample": cfg["do_sample"],
                     "T": cfg["temperature"], "q": q, "n": len(g),
                     "A_failure": g["a_failure"].mean(),
                     "semi_compliance": g["arm_binary_pass"].mean(),
                     "sentences": g["n_sentences"].mean(),
                     "semis": g["n_semicolons"].mean(),
                     "splice_share": g["splice_share"].mean(),
                     "chain_share": g["chain_share"].mean()})
        vc = g["n_sentences"].value_counts(normalize=True)
        dist.append({"decoding": label, "q": q,
                     **{f"n={k}": round(v, 3) for k, v in sorted(vc.items())[:6]}})
    # determinism manipulation check: are the two replicates identical at T=0?
    if not cfg["do_sample"]:
        key = contrast.assign(k=contrast["task_id"] + "|" + contrast["order"]
                              + "|" + contrast["arm"])
        pairs = key.groupby("k")["response"].nunique()
        print(f"[manipulation check] {label}: replicate pairs with identical "
              f"text: {(pairs == 1).sum()}/{len(pairs)}")

out = pd.DataFrame(rows).sort_values(["q", "decoding"])
print("\n### the q transition at three decoding settings (N=4)\n")
print(out.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\n### sentence-count DISTRIBUTION, not just the mean\n")
print(pd.DataFrame(dist).sort_values(["q", "decoding"]).fillna("")
      .to_string(index=False))
