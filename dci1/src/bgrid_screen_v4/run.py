"""Generate and score one model's B-grid screen.

Writes only under evidence/bgrid-screen-v4/<model>/ and reports/bgrid_screen_v4/.
Reads evidence/dci1-v4/<model>/regime_screen.json for the model's §12.1 selected
cap, and nothing else from the registered tree.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dci1v4.engine import fs
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import MODEL_KEYS, get_model
from dci1v4.topics.split import split_topics
from dci1v4.verifiers.compliance import score_constraint
from dci1v4.verifiers.constraints import Constraint, FOCAL_GRID
from dci1v4.verifiers.statistics import focal_statistic
from dci1v4.verifiers.words import alpha_runs

from bgrid_screen_v4 import CLASSIFICATION, STUDY_ID
from bgrid_screen_v4 import focal
from bgrid_screen_v4 import plan as pl
from bgrid_screen_v4 import protocol as proto

DCI1 = Path(__file__).resolve().parent.parent.parent
EVIDENCE = DCI1 / "evidence" / "bgrid-screen-v4"
REGISTERED = DCI1 / "evidence" / "dci1-v4"


def selected_cap(model_key: str) -> int:
    record = json.loads(
        (REGISTERED / model_key / "regime_screen.json").read_text())
    return record.get("payload", record)["completion_cap"]["selected_cap"]


def score_row(cell: pl.ScreenCell, text: str, *,
              truncated: bool) -> dict[str, Any]:
    """The compliance vector for one screen row.

    B at a registered severity goes through the registered verifier untouched;
    B at m in {11, 12} goes through the screen scorer, which ``focal`` proves
    verdict-identical to it on every registered rung. The §9.3 predicate is
    recorded both as registered (asymmetric: A needs only a non-empty untruncated
    answer) and symmetrically (>= 20 words for every kind), so neither reading is
    imposed on the analysis.
    """
    words = len(alpha_runs(text))
    parts: list[tuple[str, int]] = [(cell.kind, cell.severity)]
    if cell.companion:
        parts.append(cell.companion)
    scores = []
    for kind, severity in parts:
        if kind == "B" and severity not in FOCAL_GRID:
            s = focal.screen_score(severity, text, truncated=truncated)
            passed, graded = s["passed"], s["graded"]
            statistic, registered_nv = s["statistic"], s["non_vacuous"]
            scorer = "screen (extension rung)"
        else:
            r = score_constraint(Constraint(kind, severity), text,
                                 truncated=truncated)
            passed, graded = r.passed, r.graded
            statistic, registered_nv = r.statistic, r.non_vacuous
            scorer = "registered verifier"
        symmetric_nv = words >= 20 and not truncated
        scores.append({
            "kind": kind, "severity": severity, "statistic": statistic,
            "passed": passed, "graded": graded, "scorer": scorer,
            "non_vacuous_registered": registered_nv,
            "non_vacuous_symmetric": symmetric_nv,
            "vacuous_pass_registered": passed and not registered_nv,
            "vacuous_pass_symmetric": passed and not symmetric_nv,
        })
    return {"scores": scores, "word_count": words, "truncated": truncated,
            "empty": words == 0,
            "max_word_length": focal_statistic(text),
            "stem_satisfied": pl.stem_satisfied(words)}


def run(model_key: str, device: int, *,
        limit: int | None = None) -> dict[str, Any]:
    frozen = proto.load()
    spec = get_model(model_key)
    cap = selected_cap(model_key)

    topics = split_topics()["prescreen"]
    cells = pl.build_cells(topics)
    if limit:
        cells = cells[:limit]

    design_rows = []
    for cell in cells:
        seed = pl.screen_seed(spec.model_id, cell.prompt_hash, 0)
        design_rows.append({
            "cell_id": cell.cell_id, "draw_index": 0,
            "row_id": f"{cell.cell_id}:0", "prompt_hash": cell.prompt_hash,
            "scientific_seed": seed, "user_prompt": cell.prompt})

    run_dir = (EVIDENCE / model_key / f"screen-cap{cap}" / "backend_runs"
               / "round0")
    plan = build_plan(spec, stage=pl.STAGE, max_new_tokens=cap)
    plan["chunk_size"] = 32
    outcome = run_backend(run_dir, plan, design_rows, device=device,
                          timeout_seconds=60 * 60 * 8)

    by_row = {r["row_id"]: r for r in outcome["rows"]}
    cache = []
    for cell, design in zip(cells, design_rows):
        raw = by_row[design["row_id"]]
        text = raw.get("final_answer") or ""
        scored = score_row(cell, text,
                           truncated=bool(raw.get("answer_truncated")))
        cache.append({
            "row_id": design["row_id"], "cell_id": cell.cell_id,
            "role": cell.role, "stem": cell.stem, "kind": cell.kind,
            "severity": cell.severity, "topic_id": cell.topic_id,
            "companion": list(cell.companion) if cell.companion else None,
            "prompt_hash": cell.prompt_hash, "seed": design["scientific_seed"],
            "raw_response": text, "finish_reason": raw.get("finish_reason"),
            "token_count": raw.get("total_generated_tokens"),
            "model_key": model_key, "model_id": spec.model_id,
            "model_revision": spec.revision, "study_id": STUDY_ID,
            "classification": CLASSIFICATION,
            "screen_protocol_hash": frozen["screen_protocol_hash"],
            **scored})

    out_dir = EVIDENCE / model_key / f"screen-cap{cap}"
    (out_dir / "cache.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in cache))
    floored = [r for r in cache if r["stem"] == "floored"]
    report = {
        "study_id": STUDY_ID, "classification": CLASSIFICATION,
        "model_key": model_key, "selected_cap": cap,
        "screen_protocol_hash": frozen["screen_protocol_hash"],
        "screen_focal_grid": list(focal.SCREEN_FOCAL_GRID),
        "screen_only_extension": list(focal.EXTENSION),
        "plan": pl.plan_summary(cells),
        "seed_root": pl.SCREEN_ROOT_SEED,
        "seed_domain": pl.DOMAIN_SCREEN_GENERATION,
        "rows": len(cache),
        "truncated": sum(1 for r in cache if r["truncated"]),
        "empty": sum(1 for r in cache if r["empty"]),
        "stem_satisfied_rate": (sum(1 for r in floored if r["stem_satisfied"])
                                / max(1, len(floored))),
    }
    fs.write_json(out_dir / "screen_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_KEYS)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(run(args.model, args.device, limit=args.limit), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
