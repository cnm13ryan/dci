"""The registered reference pool, measured on the calibration set under the
floored stem.

The main calibration arm carries the three candidate rate families plus four
registered rungs. Four is enough to show the registered pool's behaviour and
not enough to decide its fate, and its fate is decision-relevant in a way the
FORM x STEM screen could not see: **that screen never crossed the registered
pool with the calibration set.** It measured `count x floored` on 24 pre-screen
topics at one draw and found exactly two families reaching the §13.2
condition-1 ∧ condition-6 conjunction on all four models -- a near miss, not a
refutation.

The question this arm answers is the one that decides whether Amendment B is
necessary at all:

    under the floored stem, does the REGISTERED pool clear §13.2 on the 96
    solo-calibration topics at M_cal = 4?

If it does, the reference-pool failure was a length artifact that the stem
already fixes, Amendment B is unnecessary, and Gate 1's instrument freeze --
which Amendment B §5 would re-open, because new predicates and a new numerator
change the canonical verifier hash -- is preserved. That is a large saving and
it must not be assumed in either direction.

The §12.2 shortlist rule is applied verbatim: at most three severities per
family, nearest A's solo compliance, taken from the floored pre-screen curves
because the arm is generated under the floored stem.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.engine import fs
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import MODEL_KEYS, get_model
from dci1v4.protocol import constants as C
from dci1v4.protocol.hashing import domain_int
from dci1v4.topics.split import split_topics
from dci1v4.verifiers.constraints import REFERENCE_LADDERS

from cal_screen_v4 import CLASSIFICATION, STUDY_ID
from cal_screen_v4 import plan as pl
from cal_screen_v4 import pool_protocol as proto
from cal_screen_v4.run import (EVIDENCE, floored_prescreen, registered_screen,
                               score_cell, select_prescreen_anchor)

DCI1 = Path(__file__).resolve().parent.parent.parent

#: A distinct stage label, so a pool row and a main-arm row at an identical
#: prompt never share a seed.
STAGE = "cal-screen-pool"


def pool_seed(model_id: str, prompt_hash_value: str, draw_index: int) -> int:
    return domain_int(pl.DOMAIN_SCREEN_GENERATION, pl.SCREEN_ROOT_SEED, STAGE,
                      model_id, prompt_hash_value, draw_index)


def shortlist(curves: Mapping[str, Mapping[int, float]], anchor: float
              ) -> dict[str, list[int]]:
    """§12.2's rule -- at most three severities per family, nearest A -- applied
    to a pre-screen that does not cover every rung, using the monotonicity the
    families are built from.

    The floored pre-screen the FORM x STEM screen produced measured only the
    rungs inside the CURRENT-stem caliper. Taking the three nearest of those
    would confine this arm to rungs chosen under a different stem, and the
    floored stem lengthens answers, which raises every family's statistic and
    so makes a fixed q harder to satisfy.

    That argument is about the *statistic* on a fixed text, and it does not
    license a monotone compliance curve: changing q changes the instruction and
    therefore the response. The pre-screen shows exactly that -- E2B's RF6 is
    1.00 at q = 0 and 0.29 at q = 6, because "at most 0 upper-case letters" is a
    salient rule a model can obey by writing in lower case, while "at most 6" is
    a budget it has to track. So the rule below brackets on measured values and
    does not extrapolate along an assumed monotone curve:

    * ``q_lo`` -- the most permissive measured rung whose floored compliance is
      at or below the anchor;
    * ``q_hi`` -- the most restrictive measured rung whose floored compliance is
      above the anchor;
    * if both exist, the shortlist is ``q_lo``, ``q_hi`` and the ladder rung
      nearest halfway between them;
    * if no measured rung reaches the anchor -- the common case, since the
      measured rungs are current-stem-matched and the floored stem makes every
      budget harder -- the shortlist is the three most permissive rungs of the
      ladder, which is where a crossing is likeliest if there is one. A family
      that is at ceiling even at its most restrictive rung, as E2B's RF5 is,
      cannot match A at any severity, and the shortlist shows that rather than
      hiding it.

    The rule is deterministic, uses only pre-screen data, and is fixed before
    the arm generates anything.
    """
    out: dict[str, list[int]] = {}
    for family, ladder in sorted(REFERENCE_LADDERS.items()):
        curve = curves.get(family, {})
        measured = sorted(q for q in ladder if q in curve)
        if not measured:
            out[family] = sorted(ladder)[-C.LADDER_SHORTLIST_MAX:]
            continue
        below = [q for q in measured if curve[q] <= anchor]
        above = [q for q in measured if curve[q] > anchor]
        if above:
            q_lo = max(below) if below else min(measured)
            q_hi = min(above)
            middle = min(ladder, key=lambda q: (abs(q - (q_lo + q_hi) / 2), q))
            chosen = sorted({q_lo, middle, q_hi})
        else:
            chosen = sorted(ladder)[-C.LADDER_SHORTLIST_MAX:]
        # Never fewer than three when the ladder can supply them.
        for q in sorted(ladder, reverse=True):
            if len(chosen) >= C.LADDER_SHORTLIST_MAX:
                break
            if q not in chosen:
                chosen.append(q)
        out[family] = sorted(chosen)[:C.LADDER_SHORTLIST_MAX]
    return out


def build_design(model_key: str) -> tuple[list[pl.ScreenCell],
                                          list[dict[str, Any]], dict[str, Any]]:
    spec = get_model(model_key)
    screen = registered_screen(model_key)
    floored = floored_prescreen(model_key)
    anchor = select_prescreen_anchor(floored.get("A", {}))
    chosen = shortlist(floored, anchor)

    topics = split_topics()["solo"]
    cells: list[pl.ScreenCell] = []
    for position, topic in enumerate(topics):
        index = position % pl.N_WORDINGS
        for family, severities in sorted(chosen.items()):
            for q in severities:
                line = pl.cell_wording(family, index, q)
                prompt = pl.render(topic["question"], [line], "floored")
                from dci1v4.design.prompts import prompt_hash
                cells.append(pl.ScreenCell(
                    cell_id=f"calpool:{topic['topic_id']}:floored:{family}:{q}",
                    arm="registered_pool", stem="floored", kind=family,
                    severity=q, topic_id=topic["topic_id"], prompt=prompt,
                    prompt_hash=prompt_hash(prompt), wording_index=index))

    design_rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(pl.DRAWS):
            design_rows.append({
                "cell_id": cell.cell_id, "draw_index": draw,
                "row_id": f"{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash,
                "scientific_seed": pool_seed(spec.model_id, cell.prompt_hash,
                                             draw),
                "user_prompt": cell.prompt})
    context = {"selected_cap": screen["completion_cap"]["selected_cap"],
               "a_prescreen_anchor_floored": anchor,
               "shortlist": chosen,
               "shortlist_rule": ("§12.2 verbatim, at most "
                                  f"{C.LADDER_SHORTLIST_MAX} per family, "
                                  "nearest A on the floored pre-screen curve")}
    return cells, design_rows, context


def run(model_key: str, device: int, *, limit: int | None = None
        ) -> dict[str, Any]:
    spec = get_model(model_key)
    cells, design_rows, context = build_design(model_key)
    frozen = proto.freeze(model_key, context, cells)
    if limit:
        design_rows = design_rows[:limit]

    cap = context["selected_cap"]
    run_dir = EVIDENCE / model_key / f"screen-cap{cap}" / "backend_runs" / "pool"
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
    (out_dir / "cache_registered_pool.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in cache))
    report = {"study_id": STUDY_ID, "classification": CLASSIFICATION,
              "arm": "registered_pool", "model_key": model_key,
              "selected_cap": cap,
              "screen_protocol_hash": frozen["screen_protocol_hash"],
              "context": context, "cells": len(cells), "rows": len(cache),
              "truncated": sum(1 for r in cache if r["truncated"])}
    fs.write_json(out_dir / "screen_report_registered_pool.json", report)
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
