"""The pre-screen, re-measured at M_cal draws, so §13.2 condition 2 can be
evaluated rather than only diagnosed.

Condition 2 requires the reference-minus-A solo distance to be at most **0.15**
on the disjoint 24 pre-screen topics. Both terms come from §12.2, which
registers **one draw per cell** on 24 topics. On the FORM x STEM screen's own
floored rows the paired standard error of that difference has a median of about
**0.12** -- comparable to the caliper it is checked against -- so a reference
whose true pre-screen distance is zero is rejected by condition 2 about a fifth
of the time, and the anchor itself moves: qwen3-4b's A at n\\* = 2 reads 0.542 on
the one-draw pre-screen and 0.708 on the 96-topic calibration set, a 0.167 shift
applied to every reference at once.

That is not a reason to drop condition 2. It is a reason to measure the
quantity condition 2 reads at a precision the caliper can support. This arm
re-runs the pre-screen cells at ``M_cal = 4``, on the same 24 topics, under the
same stem, changing nothing about the criterion.

**The criterion is untouched and both readings are reported.** The registered
rule applied to registered-precision data is the primary number; the same rule
applied to four times the data is reported beside it. Which precision §12.2
should register is a decision for the researcher, and this arm is its evidence,
not its answer.
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
from dci1v4.verifiers.constraints import TARGET_GRID

from cal_screen_v4 import CLASSIFICATION, STUDY_ID
from cal_screen_v4 import plan as pl
from cal_screen_v4 import prescreen_protocol as proto
from cal_screen_v4.pool_run import shortlist
from cal_screen_v4.run import (EVIDENCE, floored_prescreen, registered_screen,
                               score_cell, select_prescreen_anchor)
from dci1v4.verifiers.constraints import REFERENCE_LADDERS
from fs_screen_v4.constraints import CANDIDATES

DCI1 = Path(__file__).resolve().parent.parent.parent

STAGE = "cal-screen-prescreen-m4"


def prescreen_seed(model_id: str, prompt_hash_value: str, draw: int) -> int:
    return domain_int(pl.DOMAIN_SCREEN_GENERATION, pl.SCREEN_ROOT_SEED, STAGE,
                      model_id, prompt_hash_value, draw)


def build_design(model_key: str) -> tuple[list[pl.ScreenCell],
                                          list[dict[str, Any]], dict[str, Any]]:
    spec = get_model(model_key)
    screen = registered_screen(model_key)
    floored = floored_prescreen(model_key)
    anchor = select_prescreen_anchor(floored.get("A", {}))
    # The §12.2 shortlist, PLUS the rungs the main arm's four-rung control
    # took: the two rules pick different rungs and condition 2 has to be
    # evaluable for every rung that could be admitted, not only for the ones
    # one of the two rules happened to choose.
    registered = shortlist(floored, anchor)
    for family, severity in pl.registered_control_rungs(
            {k: {str(q): v for q, v in curve.items()}
             for k, curve in floored.items() if k in REFERENCE_LADDERS},
            anchor):
        if severity not in registered.setdefault(family, []):
            registered[family] = sorted(registered[family] + [severity])

    topics = split_topics()["prescreen"]
    cells: list[pl.ScreenCell] = []
    for position, topic in enumerate(topics):
        index = position % pl.N_WORDINGS

        def add(kind: str, severity: int) -> None:
            line = pl.cell_wording(kind, index, severity)
            prompt = pl.render(topic["question"], [line], "floored")
            cells.append(pl.ScreenCell(
                cell_id=f"calpre:{topic['topic_id']}:floored:{kind}:{severity}",
                arm=("a_solo" if kind == "A" else
                     "candidate" if kind in CANDIDATES else "registered_pool"),
                stem="floored", kind=kind, severity=severity,
                topic_id=topic["topic_id"], prompt=prompt,
                prompt_hash=prompt_hash(prompt), wording_index=index))

        for n in TARGET_GRID:
            add("A", n)
        for family in pl.CANDIDATE_FAMILIES:
            for q in CANDIDATES[family].ladder:
                add(family, q)
        for family, severities in sorted(registered.items()):
            for q in severities:
                add(family, q)

    design_rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(pl.DRAWS):
            design_rows.append({
                "cell_id": cell.cell_id, "draw_index": draw,
                "row_id": f"{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash,
                "scientific_seed": prescreen_seed(spec.model_id,
                                                  cell.prompt_hash, draw),
                "user_prompt": cell.prompt})
    context = {"selected_cap": screen["completion_cap"]["selected_cap"],
               "a_prescreen_anchor_one_draw": anchor,
               "registered_shortlist": registered,
               "topics": len(topics), "draws": pl.DRAWS}
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
               / "prescreen_m4")
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
    (out_dir / "cache_prescreen_m4.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in cache))
    report = {"study_id": STUDY_ID, "classification": CLASSIFICATION,
              "arm": "prescreen_m4", "model_key": model_key,
              "selected_cap": cap,
              "screen_protocol_hash": frozen["screen_protocol_hash"],
              "context": context, "cells": len(cells), "rows": len(cache),
              "truncated": sum(1 for r in cache if r["truncated"])}
    fs.write_json(out_dir / "screen_report_prescreen_m4.json", report)
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
