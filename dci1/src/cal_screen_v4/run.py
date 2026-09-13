"""Generate and score one model's calibration screen.

Writes only under evidence/cal-screen-v4/<model>/ and reports/cal_screen_v4/.
Reads evidence/dci1-v4/<model>/regime_screen.json for the model's selected cap
and its §12.2 ladder-screen curves, read only, and nothing else from the
registered tree.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import MODEL_KEYS, get_model
from dci1v4.topics.split import split_topics
from dci1v4.verifiers.compliance import NON_VACUITY_MIN_WORDS, score_constraint
from dci1v4.protocol import constants as C
from dci1v4.verifiers.constraints import REFERENCE_LADDERS, Constraint
from dci1v4.verifiers.words import alpha_runs

from bgrid_screen_v4 import focal
from cal_screen_v4 import CLASSIFICATION, STUDY_ID
from cal_screen_v4 import plan as pl
from cal_screen_v4 import protocol as proto
from fs_screen_v4 import constraints as cc

DCI1 = Path(__file__).resolve().parent.parent.parent
EVIDENCE = DCI1 / "evidence" / "cal-screen-v4"
REGISTERED = DCI1 / "evidence" / "dci1-v4"


FS_RESULTS = DCI1 / "reports" / "fs_screen_v4" / "results.json"


def floored_prescreen(model_key: str) -> dict[str, dict[int, float]]:
    """Every floored-stem pre-screen solo curve the FORM x STEM screen measured
    on the 24 pre-screen topics, read only."""
    tables = json.loads(FS_RESULTS.read_text())["severity_tables"][model_key]
    out: dict[str, dict[int, float]] = {}
    for key, entry in tables.items():
        _, stem, kind, severity = key.split("|")
        if stem == "floored":
            out.setdefault(kind, {})[int(severity)] = entry["raw"]
    return {k: dict(sorted(v.items())) for k, v in out.items()}


def select_prescreen_anchor(a_curve: Mapping[int, float]) -> float:
    """A's pre-screen solo compliance at the §12.3 rule's own choice of n,
    applied to the floored pre-screen curve. Used only to place the control
    arm; the admission anchor is the calibration-set value, never this one."""
    low, high = C.TARGET_BAND
    eligible = [(abs(v - C.TARGET_AIM), n, v) for n, v in a_curve.items()
                if low <= v <= high]
    if not eligible:
        # No in-band rung at pre-screen: fall back to the whole-curve mean so
        # the control arm still exists and the fallback is visible in the record.
        return sum(a_curve.values()) / len(a_curve)
    return min(eligible)[2]


def registered_screen(model_key: str) -> dict[str, Any]:
    record = json.loads((REGISTERED / model_key / "regime_screen.json").read_text())
    return record.get("payload", record)


def score_cell(kind: str, severity: int, text: str, *,
               truncated: bool) -> dict[str, Any]:
    """The compliance record for one screen row.

    Registered constraints go through the registered verifier unchanged. The
    two extended-focal rungs go through the B-grid screen's scorer, which the
    protocol proves is the registered rule. Candidate families go through the
    FORM screen's predicate. The §9.3 non-vacuity predicate for a candidate is
    the registered RF-family predicate — non-empty, not truncated, at least 20
    words — because a candidate occupies a reference slot.
    """
    words = len(alpha_runs(text))
    if kind in cc.CANDIDATES:
        non_vacuous = words >= NON_VACUITY_MIN_WORDS and not truncated
        passed = cc.passes(kind, severity, text)
        return {"statistic": cc.statistic(kind, text), "passed": passed,
                "graded": cc.graded(kind, severity, text),
                "non_vacuous": non_vacuous,
                "vacuous_pass": passed and not non_vacuous,
                "processing_failure": False, "word_count": words}
    if kind == "B" and severity in focal.EXTENSION:
        s = focal.screen_score(severity, text, truncated=truncated)
        return {"statistic": s["statistic"], "passed": s["passed"],
                "graded": s["graded"], "non_vacuous": s["non_vacuous"],
                "vacuous_pass": s["vacuous_pass"],
                "processing_failure": s["processing_failure"],
                "word_count": words}
    s = score_constraint(Constraint(kind, severity), text, truncated=truncated)
    return {"statistic": s.statistic, "passed": s.passed, "graded": s.graded,
            "non_vacuous": s.non_vacuous, "vacuous_pass": s.vacuous_pass,
            "processing_failure": s.processing_failure, "word_count": words}


def build_design(model_key: str) -> tuple[list[pl.ScreenCell],
                                          list[dict[str, Any]], dict[str, Any]]:
    spec = get_model(model_key)
    screen = registered_screen(model_key)
    curves = screen["ladder_screen"]["curves"]
    # The control arm is generated under the floored stem, so its rungs are
    # chosen against the floored pre-screen curves the FORM x STEM screen
    # measured on the same 24 topics, not against the §12.2 current-stem
    # ladder. §12.2's own curves are recorded below for provenance.
    floored = floored_prescreen(model_key)
    a_floored = floored.get("A", {})
    a_prescreen_floored = select_prescreen_anchor(a_floored)
    control = pl.registered_control_rungs(
        {k: {str(q): v for q, v in curve.items()}
         for k, curve in floored.items() if k in REFERENCE_LADDERS},
        a_prescreen_floored)
    topics = split_topics()["solo"]
    cells = pl.build_cells(topics, control)

    design_rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(pl.DRAWS):
            design_rows.append({
                "cell_id": cell.cell_id, "draw_index": draw,
                "row_id": f"{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash,
                "scientific_seed": pl.screen_seed(spec.model_id,
                                                  cell.prompt_hash, draw),
                "user_prompt": cell.prompt})
    context = {"selected_cap": screen["completion_cap"]["selected_cap"],
               "a_prescreen_solo_compliance_current_stem":
                   float(screen["ladder_screen"]["a_solo_compliance"]),
               "a_prescreen_solo_compliance_floored_stem": a_prescreen_floored,
               "registered_control_rungs": [list(r) for r in control],
               "prescreen_curves": curves}
    return cells, design_rows, context


def run(model_key: str, device: int, *, limit: int | None = None) -> dict[str, Any]:
    frozen = proto.load()
    spec = get_model(model_key)
    cells, design_rows, context = build_design(model_key)
    if limit:
        design_rows = design_rows[:limit]
        keep = {r["cell_id"] for r in design_rows}
        cells = [c for c in cells if c.cell_id in keep]

    cap = context["selected_cap"]
    run_dir = EVIDENCE / model_key / f"screen-cap{cap}" / "backend_runs" / "round0"
    plan = build_plan(spec, stage=pl.STAGE, max_new_tokens=cap)
    plan["chunk_size"] = 64
    outcome = run_backend(run_dir, plan, design_rows, device=device,
                          timeout_seconds=60 * 60 * 12)

    by_cell = {c.cell_id: c for c in cells}
    cache = []
    for raw, design in zip(outcome["rows"], design_rows):
        cell = by_cell[design["cell_id"]]
        text = raw.get("final_answer") or ""
        truncated = bool(raw.get("answer_truncated"))
        scored = score_cell(cell.kind, cell.severity, text, truncated=truncated)
        cache.append({
            "row_id": design["row_id"], "cell_id": cell.cell_id,
            "draw_index": design["draw_index"], "arm": cell.arm,
            "stem": cell.stem, "kind": cell.kind, "severity": cell.severity,
            "topic_id": cell.topic_id, "wording_index": cell.wording_index,
            "prompt_hash": cell.prompt_hash,
            "seed": design["scientific_seed"], "raw_response": text,
            "finish_reason": raw.get("finish_reason"),
            "token_count": raw.get("total_generated_tokens"),
            "truncated": truncated, "empty": scored["word_count"] == 0,
            "stem_satisfied": pl.stem_satisfied(scored["word_count"]),
            "model_key": model_key, "model_id": spec.model_id,
            "model_revision": spec.revision, "study_id": STUDY_ID,
            "classification": CLASSIFICATION,
            "screen_protocol_hash": frozen["screen_protocol_hash"],
            **scored})

    out_dir = EVIDENCE / model_key / f"screen-cap{cap}"
    (out_dir / "cache.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in cache))
    report = {
        "study_id": STUDY_ID, "classification": CLASSIFICATION,
        "model_key": model_key, "selected_cap": cap,
        "screen_protocol_hash": frozen["screen_protocol_hash"],
        "plan": pl.plan_summary(cells),
        "context": {k: v for k, v in context.items()
                    if k != "prescreen_curves"},
        "seed_root": pl.SCREEN_ROOT_SEED,
        "seed_domain": pl.DOMAIN_SCREEN_GENERATION,
        "rows": len(cache),
        "truncated": sum(1 for r in cache if r["truncated"]),
        "stem_satisfied_rate_floored": (
            sum(1 for r in cache if r["stem"] == "floored"
                and r["stem_satisfied"])
            / max(1, sum(1 for r in cache if r["stem"] == "floored"))),
    }
    fs.write_json(out_dir / "screen_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_KEYS)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    if args.plan_only:
        cells, design_rows, context = build_design(args.model)
        print(json.dumps({"plan": pl.plan_summary(cells),
                          "design_rows": len(design_rows),
                          "context": {k: v for k, v in context.items()
                                      if k != "prescreen_curves"}}, indent=1))
        return 0
    print(json.dumps(run(args.model, args.device, limit=args.limit), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
