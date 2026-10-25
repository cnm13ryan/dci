"""A bounded, authorised model smoke test. Never pilot evidence.

Before the pilot runs on a new host, each model is loaded once and asked a
handful of fixed prompts, to measure what the cost estimate and D12 need:
backend health (exit code, blocked state), model load time, throughput,
outcome classes, answer length and truncation share at the frozen cap.

Isolation, by construction:

* the prompts use ``SMOKE_QUESTIONS``, written for this purpose and checked
  to be outside the topic bank (pilot and reserved) by a test;
* a smoke root's ``RUN.json`` namespace is ``smoke``; the pilot runner and
  every pilot step refuse such a root, and a smoke run refuses a pilot root;
* no verifier is run: the report has lengths, outcomes and timings, never a
  compliance rate, so nothing here can inform A, B, eligibility or matching;
* no A or B candidate is ever prompted, so its raw answers cannot be read
  for the focal instructions before D07 and D08 are approved.

Authorisation: ``smoke_plan`` prints the plan and its hash; ``run_smoke``
refuses unless that hash is passed as the token, the plan stays within
``SMOKE_MAX_ROWS`` (a hard limit, not a default), and the stated maximum
is not exceeded.
"""
from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import environment as ENV
from dci.batch1 import library as L
from dci.batch1 import outcomes as OUT
from dci.batch1 import runner as RUN
from dci.batch1 import text as T
from dci.batch1.store import RunError, append_jsonl, record_hash, run_lock
from dci.provenance.hashes import sha, sha_text

__all__ = ["SMOKE_MAX_ROWS", "SMOKE_QUESTIONS", "SMOKE_CONDITIONS",
           "smoke_plan", "run_smoke"]

#: Hard ceiling on one smoke run, over all models.
SMOKE_MAX_ROWS = 96
SMOKE_STAGE = "smoke"
SMOKE_QUESTIONS = (
    "How do lighthouse keepers keep a lamp burning through a long storm?",
    "Why do some city parks close their gates at sunset?",
    "How does a weather vane show which way the wind blows?",
)
#: Task-only and the reference instructions likeliest to lengthen an answer
#: (the cap's worst case). No A or B candidate (re-audit R4.2): the smoke
#: test runs before Freeze 1, and its raw answers must say nothing about the
#: focal instructions D07 and D08 select from.
SMOKE_CONDITIONS = (D.TASK_ONLY, "ord.inc6", "es.7", "ep.3", "nb.min10",
                    "inc.silver+morning+quiet")


def smoke_plan(models: Sequence[str] = tuple(CFG.MODEL_BY_KEY),
               frame: str = "F0") -> dict[str, Any]:
    by_id = L.constraint_by_id()
    focal = [c for c in SMOKE_CONDITIONS
             if c != D.TASK_ONLY and by_id[c].role != "reference"]
    if focal:
        raise RunError(f"the smoke test may not use A or B candidates: {focal}")
    rows = []
    for key in models:
        model = CFG.MODEL_BY_KEY[key]
        for qi, question in enumerate(SMOKE_QUESTIONS):
            for cond in SMOKE_CONDITIONS:
                c = None if cond == D.TASK_ONLY else by_id[cond]
                f = None if c is None else frame
                prompt = D.render_prompt(question, c, f)
                identity = {"study_id": CFG.STUDY_ID, "stage": SMOKE_STAGE,
                            "model": key, "frame": f, "condition": cond,
                            "topic_id": f"smoke-{qi}", "draw": 0}
                rows.append({
                    "row_id": "b1s-" + sha(["batch1/smoke-row", identity])[:24],
                    **identity, "cell_id": f"smoke|{key}|{f or '-'}|{cond}",
                    "load": 0 if c is None else 1, "user_prompt": prompt,
                    "prompt_hash": sha_text(prompt),
                    "scientific_seed": D.generation_seed(
                        CFG.DEFAULT_CONFIG, stage=SMOKE_STAGE, model=model,
                        prompt_hash=sha_text(prompt), draw=0),
                    "protocol_hash": "smoke",
                    "identity_hash": sha(["batch1/smoke-identity", identity,
                                          sha_text(prompt)])})
    body = {"rows": rows, "decoding": CFG.DECODING,
            "models": [CFG.MODEL_BY_KEY[k].__dict__ for k in models]}
    return {**body, "plan_hash": record_hash(body), "max_rows": SMOKE_MAX_ROWS}


def _summary(rows: list[Mapping[str, Any]], provenance: Mapping[str, Any],
             wall: float) -> dict[str, Any]:
    classes: dict[str, int] = {}
    words, tokens = [], []
    truncated = 0
    for r in rows:
        cls = OUT.classify(r)
        classes[cls.kind] = classes.get(cls.kind, 0) + 1
        if cls.behavioural:
            words.append(T.word_count(r.get("final_answer") or ""))
            tokens.append(int(r.get("total_generated_tokens") or 0))
            truncated += bool(r.get("answer_truncated"))
    gen_seconds = provenance.get("generation_seconds")
    n = len(words)
    return {"rows": len(rows), "outcome_classes": classes,
            "load_seconds": provenance.get("load_seconds"),
            "generation_seconds": gen_seconds, "wall_seconds": round(wall, 1),
            "rows_per_second": (round(n / gen_seconds, 3)
                                if gen_seconds else None),
            "truncation_share": round(truncated / n, 4) if n else None,
            "answer_words": ({"min": min(words), "median": statistics.median(words),
                              "max": max(words)} if words else None),
            "generated_tokens": ({"median": statistics.median(tokens),
                                  "max": max(tokens)} if tokens else None)}


def run_smoke(root: Path, *, token: str | None, max_rows: int,
              models: Sequence[str] = tuple(CFG.MODEL_BY_KEY),
              backend: RUN.BackendSpec | None = None,
              generate: RUN.GenerateFn | None = None) -> dict[str, Any]:
    ENV.require_orchestrator()
    plan = smoke_plan(models)
    rows = plan["rows"]
    if max_rows > SMOKE_MAX_ROWS or len(rows) > min(max_rows, SMOKE_MAX_ROWS):
        raise RunError(f"the smoke plan has {len(rows)} rows; the stated "
                       f"maximum is {max_rows} and the hard limit "
                       f"{SMOKE_MAX_ROWS}")
    if token != plan["plan_hash"]:
        raise RunError("pass the smoke plan hash (smoke-plan) as --authorize "
                       "to run the smoke test")
    spec = backend or RUN.BackendSpec()
    environment = ENV.probe(spec.python) if generate is None else \
        {"status": "STAND_IN"}
    if generate is None:
        generate = RUN.subprocess_backend(spec)
    RUN.init_root(root, synthetic=False, freeze1_hash="none",
                  namespace="smoke")
    report: dict[str, Any] = {"schema": "dci.batch1/smoke/v1",
                              "plan_hash": plan["plan_hash"],
                              "environment": environment, "models": {},
                              "note": "smoke test: never pilot evidence; no "
                                      "compliance is computed"}
    with run_lock(root):
        for key in models:
            mine = [r for r in rows if r["model"] == key]
            run_dir = Path(root) / "smoke" / key
            started = time.time()
            out = generate(run_dir, RUN.seam_plan(CFG.MODEL_BY_KEY[key],
                                                  SMOKE_STAGE),
                           RUN.seam_design_rows(mine))
            wall = time.time() - started
            append_jsonl(run_dir / "rows.jsonl", out["rows"])
            prov = dict(out.get("provenance") or {})
            entry = _summary(out["rows"], prov, wall)
            entry.update(returncode=out.get("returncode", 0),
                         blocked=bool(prov.get("blocked")))
            report["models"][key] = entry
    from dci.batch1 import freeze as F
    F.write_json(Path(root) / "smoke_report.json", report)
    return report
