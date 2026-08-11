"""Stage 0.3 — stratified reproducible sample for a HUMAN read of chain_share."""
import glob, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 200)

frames = []
for d in sorted(glob.glob("runs/stage*/")):
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    f = f[f["response"].notna() & f["chain_share"].notna()].copy()
    f["run"] = c["stage"]
    frames.append(f[["run", "row_id", "arm", "condition", "chain_share",
                     "n_semi_splices", "n_colon_splices", "n_dash_splices",
                     "n_terminal_marks", "n_sentences", "response"]])
all_rows = pd.concat(frames, ignore_index=True)
all_rows["stratum"] = pd.cut(all_rows["chain_share"], [-.001, .15, .40, 1.001],
                             labels=["low", "medium", "high"])
print("stratum sizes:", all_rows["stratum"].value_counts().to_dict())

rng = np.random.default_rng(20260811)
picks = []
for s in ("low", "medium", "high"):
    pool = all_rows[all_rows["stratum"] == s].sort_values("row_id")
    idx = rng.choice(len(pool), size=6, replace=False)
    picks.append(pool.iloc[sorted(idx)])
sample = pd.concat(picks, ignore_index=True)
sample.to_json("chain_audit_sample.jsonl", orient="records", lines=True)

for _, r in sample.iterrows():
    print("=" * 78)
    print(f"[{r['stratum'].upper()}] chain_share={r['chain_share']:.3f}  "
          f"semi={r['n_semi_splices']} colon={r['n_colon_splices']} "
          f"dash={r['n_dash_splices']} term={r['n_terminal_marks']} "
          f"sentences={r['n_sentences']}  {r['run']}/{r['arm']}/{r['condition']}")
    print((r["response"] or "")[:620])
