import sys, glob
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 240)
rows = []
for d in sorted(glob.glob("runs/stageE3_N*/")):
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    ct = mechanism.cell_table(f, ["order", "arm"])
    ex = mechanism.paired_excess(f, "C_L3", "a_failure", by=["order"],
                                 n_boot=4000).set_index(["order", "arm"])
    cx = mechanism.paired_excess(f, "C_L3", "severe_collapse", by=["order"],
                                 n_boot=4000).set_index(["order", "arm"])
    for _, r in ct.iterrows():
        key = (r["order"], r["arm"])
        rows.append({
            "N": f.attrs["n_target"], "order": r["order"], "arm": r["arm"],
            "failure": r["a_failure"], "collapse": r["severe_collapse"],
            "excess_fail": ex.loc[key, "excess"] if key in ex.index else 0.0,
            "ci": (f"[{ex.loc[key,'ci_low']:+.2f},{ex.loc[key,'ci_high']:+.2f}]"
                   if key in ex.index else ""),
            "excess_collapse": cx.loc[key, "excess"] if key in cx.index else 0.0,
            "mean_sent": r["mean_n_sentences"], "semis": r["mean_n_semicolons"],
            "own_rule": r["arm_compliance"], "words": r["mean_n_words"]})
out = pd.DataFrame(rows).sort_values(["arm", "order", "N"])
print(out.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
