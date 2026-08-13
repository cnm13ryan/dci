"""How much does the SHARED background move each arm's measured interference?

A background identical across arms cannot bias tau. This table asks the other
question: does it decide whether tau exists? Every row is a run in which the
target, the arms, the tasks, the wording, the load, the orders and the decoding
are the same, and only the background set differs.
"""
import glob, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import mechanism
pd.set_option("display.width", 260)

rows = []
for d in sorted(glob.glob("runs/stage*/")):
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    sel = c["selection"]
    if sel["target"] != "A" or c["model"]["model_id"] != "Qwen/Qwen3-4B-Instruct-2507":
        continue
    if "S_SEMICOLON" not in sel["references"] or "C_L3" not in sel["references"]:
        continue
    if c.get("scaffolds", [""]) != [""] and len(c.get("scaffolds", [""])) > 1:
        f = f[f["scaffold"] == ""]           # baseline cell only
    ex = mechanism.paired_excess(f, "C_L3", "a_failure", by=["order"], n_boot=4000)
    ex = ex.set_index(["order", "arm"])
    for arm in ("S_SEMICOLON", "B"):
        for o in ("o_A", "o_Q"):
            if (o, arm) not in ex.index:
                continue
            rows.append({"run": c["stage"], "background": " + ".join(sel["background"]),
                         "arm": arm, "order": o,
                         "excess": ex.loc[(o, arm), "excess"],
                         "lo": ex.loc[(o, arm), "ci_low"], "hi": ex.loc[(o, arm), "ci_high"]})
out = pd.DataFrame(rows)
for arm in ("S_SEMICOLON", "B"):
    sub = out[out["arm"] == arm].pivot_table(index=["background", "run"],
                                             columns="order", values="excess")
    print(f"\n=== {arm}: paired excess over C_L3, by background set ===")
    print(sub.to_string(float_format=lambda v: f"{v:+.3f}"))
