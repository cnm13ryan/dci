"""The lower-bound candidate families, on the calibration set.

**Why this arm exists, and why it is not a fourth try at the same question.**

Every constraint in the v4 design except A is a *budget*: B is "every word at
most m letters", the eight registered families are "at most q", and the three
rate families this screen's main arm carries are "at most q% of words". A is the
only *production* constraint in the pool -- "use the word however exactly n
times" -- and it is the only one a model can fail by writing less.

That makes the registered companion swap confounded in a way neither the
caliper nor the vacuity condition touches. Delta_R contrasts A against
difficulty-matched budgets, so a positive Delta_R is equally consistent with

    H_pair          A is unusually damaging to B specifically, and
    H_class         a production constraint is damaging to a budget outcome,
                    and A is the only production constraint in the pool.

The B+R pilot's own numbers make H_class live rather than hypothetical. On
gemma-3n-E4B the pilot reports D(B<-Rbar) = **-0.059**: composing B with a
matched reference *raises* B's compliance. A companion that helps is not a
generic-load baseline, and the pilot's Delta = D(B<-A) - D(B<-Rbar) is then
"A's damage plus the references' help" rather than A's excess damage.

The lower-bound families CL1, CL7 and CL8 are the only candidates that share
A's structural class: they are satisfied by producing something, not by
withholding it. Admitting one alongside the matched budgets makes the
comparison

    D(B<-A)  against  D(B<-CL)   at matched companion difficulty

available, and that contrast separates the two hypotheses in a way Xi cannot,
because Xi varies the outcome while this varies the companion's class.

Amendment B §6 recommended against the lower-bound families on the ground that
"a lower bound imposes a length *floor* -- pushing length up while B pushes it
down, which replaces one length confound with its mirror image". That objection
was written for the current stem. Under the floored stem the length floor is
already imposed on every cell by the stem itself, so the mirror-image confound
is much weaker, and this arm measures it instead of assuming either way.

Nothing here is adopted. Amendment B's recommended set is unchanged.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dci1v4.design.prompts import prompt_hash
from dci1v4.engine import fs
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import MODEL_KEYS, get_model
from dci1v4.protocol.hashing import domain_int
from dci1v4.topics.split import split_topics

from cal_screen_v4 import CLASSIFICATION, STUDY_ID
from cal_screen_v4 import lowerbound_protocol as proto
from cal_screen_v4 import plan as pl
from cal_screen_v4.run import EVIDENCE, registered_screen, score_cell
from fs_screen_v4.constraints import CANDIDATES

DCI1 = Path(__file__).resolve().parent.parent.parent

STAGE = "cal-screen-lowerbound"
LOWER_BOUND_FAMILIES: tuple[str, ...] = ("CL1", "CL7", "CL8")


def seed(model_id: str, prompt_hash_value: str, draw: int) -> int:
    return domain_int(pl.DOMAIN_SCREEN_GENERATION, pl.SCREEN_ROOT_SEED, STAGE,
                      model_id, prompt_hash_value, draw)


def build_design(model_key: str) -> tuple[list[pl.ScreenCell],
                                          list[dict[str, Any]], dict[str, Any]]:
    spec = get_model(model_key)
    screen = registered_screen(model_key)
    topics = split_topics()["solo"]
    cells: list[pl.ScreenCell] = []
    for position, topic in enumerate(topics):
        index = position % pl.N_WORDINGS
        for family in LOWER_BOUND_FAMILIES:
            for q in CANDIDATES[family].ladder:
                line = pl.cell_wording(family, index, q)
                prompt = pl.render(topic["question"], [line], "floored")
                cells.append(pl.ScreenCell(
                    cell_id=f"calcl:{topic['topic_id']}:floored:{family}:{q}",
                    arm="lower_bound", stem="floored", kind=family, severity=q,
                    topic_id=topic["topic_id"], prompt=prompt,
                    prompt_hash=prompt_hash(prompt), wording_index=index))
    design_rows = [
        {"cell_id": c.cell_id, "draw_index": d, "row_id": f"{c.cell_id}:{d}",
         "prompt_hash": c.prompt_hash,
         "scientific_seed": seed(spec.model_id, c.prompt_hash, d),
         "user_prompt": c.prompt}
        for c in cells for d in range(pl.DRAWS)]
    context = {"selected_cap": screen["completion_cap"]["selected_cap"],
               "families": list(LOWER_BOUND_FAMILIES),
               "ladders": {f: list(CANDIDATES[f].ladder)
                           for f in LOWER_BOUND_FAMILIES}}
    return cells, design_rows, context


def run(model_key: str, device: int, *, limit: int | None = None
        ) -> dict[str, Any]:
    spec = get_model(model_key)
    cells, design_rows, context = build_design(model_key)
    frozen = proto.freeze(model_key, context, cells)
    if limit:
        design_rows = design_rows[:limit]
    cap = context["selected_cap"]
    run_dir = (EVIDENCE / model_key / f"screen-cap{cap}" / "backend_runs"
               / "lower_bound")
    plan = build_plan(spec, stage=STAGE, max_new_tokens=cap)
    plan["chunk_size"] = 64
    outcome = run_backend(run_dir, plan, design_rows, device=device,
                          timeout_seconds=60 * 60 * 12)

    by_cell = {c.cell_id: c for c in cells}
    cache = []
    for raw, row in zip(outcome["rows"], design_rows):
        cell = by_cell[row["cell_id"]]
        text = raw.get("final_answer") or ""
        truncated = bool(raw.get("answer_truncated"))
        scored = score_cell(cell.kind, cell.severity, text, truncated=truncated)
        cache.append({
            "row_id": row["row_id"], "cell_id": cell.cell_id,
            "draw_index": row["draw_index"], "arm": cell.arm,
            "stem": cell.stem, "kind": cell.kind, "severity": cell.severity,
            "topic_id": cell.topic_id, "wording_index": cell.wording_index,
            "prompt_hash": cell.prompt_hash, "seed": row["scientific_seed"],
            "raw_response": text, "finish_reason": raw.get("finish_reason"),
            "token_count": raw.get("total_generated_tokens"),
            "truncated": truncated, "empty": scored["word_count"] == 0,
            "stem_satisfied": pl.stem_satisfied(scored["word_count"]),
            "model_key": model_key, "model_id": spec.model_id,
            "model_revision": spec.revision, "study_id": STUDY_ID,
            "classification": CLASSIFICATION,
            "screen_protocol_hash": frozen["screen_protocol_hash"],
            **scored})

    out_dir = EVIDENCE / model_key / f"screen-cap{cap}"
    (out_dir / "cache_lower_bound.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in cache))
    report = {"study_id": STUDY_ID, "classification": CLASSIFICATION,
              "arm": "lower_bound", "model_key": model_key,
              "selected_cap": cap,
              "screen_protocol_hash": frozen["screen_protocol_hash"],
              "context": context, "cells": len(cells), "rows": len(cache),
              "truncated": sum(1 for r in cache if r["truncated"])}
    fs.write_json(out_dir / "screen_report_lower_bound.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_KEYS)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    if args.plan_only:
        cells, rows, context = build_design(args.model)
        print(json.dumps({"cells": len(cells), "rows": len(rows),
                          "context": context}, indent=1))
        return 0
    print(json.dumps(run(args.model, args.device, limit=args.limit), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
