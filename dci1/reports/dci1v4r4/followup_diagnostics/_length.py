"""POST-HOC DESCRIPTIVE / MECHANISTIC DIAGNOSTIC. Not registered.

Q3. Response length is POST-TREATMENT: composition changes it. Nothing here
conditions on length and reinterprets a residual as a causal effect. What it
does is describe (a) how length moves across cells and (b) how compliance
varies with length *within* a cell, so a reader can see whether the
registered directional effects travel with a length shift.

Writes 05_length_strategy.json.
"""
import json, sys, pathlib, statistics, collections
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))

OUT = pathlib.Path(__file__).resolve().parent / "05_length_strategy.json"
SURVIVORS = ("qwen3-4b", "gemma-3n-e4b-it")
EV = DCI1 / "evidence" / "dci1v4r4"
BINS = [(0, 30), (30, 45), (45, 60), (60, 80), (80, 110), (110, 150), (150, 10**6)]


def label(key):
    return "+".join(f"{k}@pos{p}" for k, p in key) or "unconstrained"


rec = {"_provenance": "POST-HOC DESCRIPTIVE / MECHANISTIC DIAGNOSTIC. Length "
                      "is post-treatment; no causal reading is licensed.",
       "word_bins": [list(b) for b in BINS], "models": {}}
for model in SURVIVORS:
    root = EV / model / "CONFIRMATORY_GENERATION" / "backend_runs"
    raw = {}
    for f in sorted(root.glob("blocks-*/rows.jsonl")):
        for line in f.open():
            r = json.loads(line)
            raw[r["row_id"]] = r
    rows = []
    for f in sorted(root.glob("blocks-*/scored.jsonl")):
        for line in f.open():
            rows.append(json.loads(line))
    by_cell = collections.defaultdict(list)
    for r in rows:
        key = tuple(sorted((s["kind"], s["position"])
                           for s in r["scores"] if s["present"]))
        by_cell[key].append(r)

    cells = {}
    for key, rs in by_cell.items():
        lab = label(key)
        words = [r["word_count"] for r in rs]
        entry = {"n": len(rs),
                 "words_mean": statistics.fmean(words),
                 "words_median": statistics.median(words),
                 "words_sd": statistics.pstdev(words),
                 "truncated": sum(bool(raw[r["row_id"]]["answer_truncated"])
                                  for r in rs),
                 "empty": sum(not raw[r["row_id"]]["final_answer"].strip()
                              for r in rs),
                 "finish_reasons": dict(collections.Counter(
                     raw[r["row_id"]]["finish_reason"] for r in rs)),
                 "compliance_by_word_bin": {}}
        for kind, _pos in key:
            per_bin = {}
            for lo, hi in BINS:
                sel = [r for r in rs if lo <= r["word_count"] < hi]
                if not sel:
                    continue
                obs = [s for r in sel for s in r["scores"]
                       if s["kind"] == kind and s["present"]]
                per_bin[f"{lo}-{hi if hi < 10**6 else 'inf'}"] = {
                    "n": len(obs),
                    "compliance": sum(bool(o["passed"]) for o in obs) / len(obs),
                    "words_median": statistics.median(
                        [r["word_count"] for r in sel])}
            entry["compliance_by_word_bin"][kind] = per_bin
        cells[lab] = entry

    # pooled within-model association, reported as a description only
    pooled = {}
    for kind in {k for key in by_cell for k, _ in key}:
        per_bin = {}
        for lo, hi in BINS:
            obs = [s for key, rs in by_cell.items() for r in rs
                   for s in r["scores"]
                   if s["kind"] == kind and s["present"]
                   and lo <= r["word_count"] < hi]
            if obs:
                per_bin[f"{lo}-{hi if hi < 10**6 else 'inf'}"] = {
                    "n": len(obs),
                    "compliance": sum(bool(o["passed"]) for o in obs) / len(obs)}
        pooled[kind] = per_bin
    rec["models"][model] = {
        "cells": cells,
        "pooled_compliance_by_word_bin_ACROSS_CELLS": pooled,
        "pooled_caveat": "pooling mixes cells with different companions and "
                         "different lengths; it describes an association, not "
                         "an effect, and the within-cell tables above are the "
                         "ones that hold the companion fixed"}
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
