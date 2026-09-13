"""POST-HOC DIAGNOSTIC. Not registered. Read-only.

Q1/Q2/Q3/Q7 raw material: per-cell compliance, vacuity and response-length
tables computed directly from the signed confirmatory `scored.jsonl` rows of
both surviving replications, with no estimator, no ObservationTable and no
bootstrap. Registered effects are read from the signed UNMASKED_ANALYSIS
record; the raw tables here exist so every registered number can be checked
against the rows it came from.

Writes 04_confirmatory_raw.json.
"""
import json, sys, pathlib, statistics, collections
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4r4.protocol import constants as C

OUT = pathlib.Path(__file__).resolve().parent / "04_confirmatory_raw.json"
SURVIVORS = ("qwen3-4b", "gemma-3n-e4b-it")
EV = DCI1 / "evidence" / "dci1v4r4"


def load(model):
    root = EV / model / "CONFIRMATORY_GENERATION" / "backend_runs"
    scored, raw = {}, {}
    for f in sorted(root.glob("blocks-*/scored.jsonl")):
        for line in f.open():
            r = json.loads(line)
            scored[r["row_id"]] = r
    for f in sorted(root.glob("blocks-*/rows.jsonl")):
        for line in f.open():
            r = json.loads(line)
            raw[r["row_id"]] = r
    return scored, raw


def cell_key(row):
    """(sorted present kinds with positions) identifies the registered cell."""
    return tuple(sorted((s["kind"], s["position"])
                        for s in row["scores"] if s["present"]))


rec = {"_provenance": "POST-HOC DIAGNOSTIC; computed directly from signed "
                      "confirmatory scored.jsonl rows, no estimator involved",
       "models": {}}
for model in SURVIVORS:
    scored, raw = load(model)
    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    lengths = collections.defaultdict(list)
    meta = collections.defaultdict(lambda: collections.Counter())
    for rid, r in scored.items():
        key = cell_key(r)
        rr = raw[rid]
        lengths[key].append({
            "words": r["word_count"], "tokens": r["token_count"],
            "chars": len(rr["final_answer"]),
            "final_answer_tokens": rr["final_answer_tokens"],
            "truncated": bool(rr["answer_truncated"]),
            "finish_reason": rr["finish_reason"]})
        meta[key]["n"] += 1
        meta[key]["truncated"] += int(bool(rr["answer_truncated"]))
        meta[key]["empty"] += int(not rr["final_answer"].strip())
        meta[key][f"finish:{rr['finish_reason']}"] += 1
        for s in r["scores"]:
            if not s["present"]:
                continue
            cells[key][s["kind"]].append(
                {"passed": bool(s["passed"]), "graded": s["graded"],
                 "vacuous_pass": bool(s["vacuous_pass"]),
                 "non_vacuous": bool(s["non_vacuous"]),
                 "words": r["word_count"], "row_id": rid})
    out_cells = {}
    for key, per_kind in cells.items():
        label = "+".join(f"{k}@pos{p}" for k, p in key) or "unconstrained"
        wl = [x["words"] for x in lengths[key]]
        tl = [x["tokens"] for x in lengths[key]]
        cl = [x["chars"] for x in lengths[key]]
        entry = {"cell_signature": [list(k) for k in key], "n_rows": meta[key]["n"],
                 "slots": {},
                 "length": {
                     "words_mean": statistics.fmean(wl),
                     "words_median": statistics.median(wl),
                     "words_p10": sorted(wl)[len(wl) // 10],
                     "words_p90": sorted(wl)[-max(1, len(wl) // 10)],
                     "tokens_mean": statistics.fmean(tl),
                     "tokens_median": statistics.median(tl),
                     "chars_mean": statistics.fmean(cl)},
                 "truncated": meta[key]["truncated"], "empty": meta[key]["empty"],
                 "finish_reasons": {k.split(":", 1)[1]: v
                                    for k, v in meta[key].items()
                                    if k.startswith("finish:")}}
        for kind, obs in per_kind.items():
            n = len(obs)
            entry["slots"][kind] = {
                "n": n,
                "compliance": sum(o["passed"] for o in obs) / n,
                "graded_mean": statistics.fmean(o["graded"] for o in obs),
                "vacuous_pass_rate": sum(o["vacuous_pass"] for o in obs) / n,
                "non_vacuous_rate": sum(o["non_vacuous"] for o in obs) / n}
        out_cells[label] = entry
    rec["models"][model] = {"n_rows": len(scored), "cells": out_cells}
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
