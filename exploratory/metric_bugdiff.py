"""Stage 0.1 — what did the colon/dash splice bug actually change?

The buggy regex is reconstructed verbatim so the difference is measured, not
recalled. It matched only `[;,]`, so the downstream character test could never
succeed for a colon or a dash and those counts were structurally 0.
"""
import glob, re, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
from dci_exploratory import extensions, mechanism
pd.set_option("display.width", 220)

BUGGY = re.compile(r"[;,]\s*([A-Za-z']+)")

def buggy_splice(text, mark):
    char = extensions.MARK_CHARS[mark][0]
    return sum(1 for m in BUGGY.finditer(str(text or ""))
               if m.group(0)[0] == char and m.group(1).lower() in extensions.CLAUSE_INITIAL)

_TERM = re.compile(r"[.!?]")

def buggy_chain(text):
    s = buggy_splice(text, "semicolon")
    c = buggy_splice(text, "colon")     # structurally 0
    d = buggy_splice(text, "dash")      # structurally 0
    t = len(_TERM.findall(text))
    b = s + c + d
    return (b / (b + t)) if (b + t) else float("nan")

rows = []
for d in sorted(glob.glob("runs/stage*/")):
    if not (Path(d) / "generations.jsonl").exists():
        continue
    f, c = mechanism.load(Path(d))
    g = f[f["response"].notna() & (f["response"].str.strip() != "")]
    if not len(g):
        continue
    old = g["response"].map(buggy_chain)
    new = g["chain_share"]
    old_sem = g["response"].map(lambda t: buggy_splice(t, "semicolon"))
    diff = (old - new).abs()
    rows.append({
        "run": c["stage"], "n": len(g),
        "rows_chain_changed": int((diff > 1e-9).sum()),
        "max_abs_change": float(diff.max()),
        "mean_chain_buggy": float(old.mean()), "mean_chain_fixed": float(new.mean()),
        "semi_splices_changed": int((old_sem != g["n_semi_splices"]).sum()),
        "colon_splices_now_nonzero": int((g["n_colon_splices"] > 0).sum()),
        "dash_splices_now_nonzero": int((g["n_dash_splices"] > 0).sum())})
out = pd.DataFrame(rows)
print(out.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print(f"\nTOTAL generations rescored: {out['n'].sum()}")
print(f"rows whose chain_share changed: {out['rows_chain_changed'].sum()} "
      f"({out['rows_chain_changed'].sum()/out['n'].sum():.2%})")
print(f"semicolon splice counts changed: {out['semi_splices_changed'].sum()}  "
      "(expected 0 — the bug could not touch semicolons)")
