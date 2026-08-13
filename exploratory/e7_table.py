"""E7: the double dissociation, read across the three prohibition conditions."""
import glob, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import extensions, mechanism
pd.set_option("display.width", 250)

rows = []
for d in sorted(glob.glob("runs/stageE7*/")):
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    prohibition = c["selection"]["background"][-1]
    # E7 and E7c use the same three prohibitions against different backgrounds;
    # without this the two blocks' rows are indistinguishable in the table.
    block = "colon-bg" if c["stage"].startswith("E7c") else "paren-free-bg"
    contrast = f[f["condition"].isin(["focal", "reference"])].copy()
    # Compliance with the prohibition, measured not assumed. The splice proxy
    # can only under-count; the raw mark counts are exact.
    contrast["semi_splices"] = [extensions.splice_count(t or "", "semicolon")
                                for t in contrast["response"]]
    contrast["comma_splices"] = [extensions.splice_count(t or "", "comma")
                                 for t in contrast["response"]]
    ct = mechanism.cell_table(f, ["order", "arm"]).set_index(["order", "arm"])
    ex = mechanism.paired_excess(f, "C_L3", "a_failure", by=["order"],
                                 n_boot=10000).set_index(["order", "arm"])
    for (o, a), g in contrast.groupby(["order", "arm"]):
        rows.append({
            "block": block,
            "prohibition": prohibition.replace("X_NO_", ""), "order": o, "arm": a,
            "failure": ct.loc[(o, a), "a_failure"],
            "collapse": ct.loc[(o, a), "severe_collapse"],
            "excess": ex.loc[(o, a), "excess"] if (o, a) in ex.index else 0.0,
            "semis": ct.loc[(o, a), "mean_n_semicolons"],
            "commas": ct.loc[(o, a), "mean_n_commas"],
            "semi_splice": g["semi_splices"].mean(),
            "comma_splice": g["comma_splices"].mean(),
            "sent": ct.loc[(o, a), "mean_n_sentences"]})
out = pd.DataFrame(rows).sort_values(["block", "arm", "order", "prohibition"])
print(out.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
