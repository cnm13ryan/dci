"""Q3, qualitative half. POST-HOC DESCRIPTIVE.

Representative confirmatory responses from every cell of both survivors, on
three fixed topics chosen by position in the registered block order (not by
outcome), with each slot's verifier statistic beside them. Illustrative
only: no rate, no claim, no selection on compliance.
Writes 10_response_samples.json.
"""
import json, sys, pathlib, collections
DCI1 = pathlib.Path(__file__).resolve().parents[3]
EV = DCI1 / "evidence" / "dci1v4r4"
OUT = pathlib.Path(__file__).resolve().parent / "10_response_samples.json"
SURVIVORS = ("qwen3-4b", "gemma-3n-e4b-it")
N_TOPICS, DRAW = 3, 0

rec = {"_provenance": "POST-HOC DESCRIPTIVE. Topics chosen by position in the "
                      "registered block order and draw index 0, never by "
                      "compliance. Illustrative; no rate and no claim.",
       "draw_index": DRAW, "models": {}}
for model in SURVIVORS:
    root = EV / model / "CONFIRMATORY_GENERATION" / "backend_runs"
    raw = {}
    for f in sorted(root.glob("blocks-*/rows.jsonl")):
        for line in f.open():
            r = json.loads(line); raw[r["row_id"]] = r
    rows = [json.loads(l) for f in sorted(root.glob("blocks-*/scored.jsonl"))
            for l in f.open()]
    topics = sorted({r["topic_id"] for r in rows})[:N_TOPICS]
    by = collections.defaultdict(dict)
    for r in rows:
        if r["topic_id"] not in topics or int(r["draw_index"]) != DRAW:
            continue
        cell = "+".join(f"{k}@pos{p}" for k, p in
                        sorted((s["kind"], s["position"])
                               for s in r["scores"] if s["present"])) \
            or "unconstrained"
        rr = raw[r["row_id"]]
        by[r["topic_id"]][cell] = {
            "row_id": r["row_id"], "word_count": r["word_count"],
            "token_count": r["token_count"],
            "finish_reason": rr["finish_reason"],
            "truncated": bool(rr["answer_truncated"]),
            "scores": {s["kind"]: {"severity": s["severity"],
                                   "statistic": s["statistic"],
                                   "passed": bool(s["passed"]),
                                   "vacuous_pass": bool(s["vacuous_pass"])}
                       for s in r["scores"] if s["present"]},
            "final_answer": rr["final_answer"]}
    rec["models"][model] = {"topics": topics, "cells_by_topic": dict(by)}
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
