"""§12.6's coverage criterion on v4r4's own difficulty landscape (phase 10).

Reads the four signed v4r4 `REGIME_SCREEN` records --- hash and signature
verified, `study_id` checked --- and reports, per replication: `iota_A`, the
selected completion cap, the eligible rungs, easier and harder support, local
density around `iota_A`, family and feature-group diversity, spectrum support,
class candidates, core-reference availability, leave-one-family-out robustness,
and the counterfactual against the population before §7.0-R4.

Solo and chance compliance only. Nothing here reads a composed cell.

    ./.venv/bin/python tools/v4r4_coverage.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.models.registry import MODEL_KEYS                    # noqa: E402

from dci1v4r4.engine.context import registered_context           # noqa: E402
from dci1v4r4.engine.paths import model_tree                     # noqa: E402
from dci1v4r4.engine.transitions import read_stage_record        # noqa: E402
from dci1v4r4.protocol import constants as C                     # noqa: E402
from dci1v4r4.stages import library as lib                       # noqa: E402
from dci1v4r4.verifiers.constraints import (                     # noqa: E402
    FAMILIES, REMOVED_IN_V4R4, feature_group,
)

OUT = DCI1 / "reports" / "dci1v4r4" / "coverage.json"
PRIOR = DCI1 / "reports" / "dci1v4r4" / "cp4_cp7_analysis.json"


def _rows(record: dict[str, Any]) -> list[lib.LibraryRow]:
    rounds = {label: entry
              for entry in record["expansion"].get("history", [])
              for label in entry.get("admitted", [])}
    out = []
    for label, entry in sorted(record["difficulty_table"].items()):
        if entry["kind"] in ("A", "B"):
            continue
        out.append(lib.LibraryRow(
            kind=entry["kind"], severity=entry["severity"],
            solo_compliance=entry["solo"],
            chance_compliance=min(entry["chance"], 0.9899),
            solo_vacuity=entry["solo_vacuity"],
            admitted_in_round=rounds.get(label, 0),
            median_words=entry["median_words"],
            graded_mean=entry["graded_mean"]))
    return out


def _support(rows, iota_a: float) -> dict[str, Any]:
    eligible = [r for r in rows
                if r.role == "reference" and lib.eligible_prescreen(r)]
    below = [r for r in eligible if r.iota < iota_a]
    above = [r for r in eligible if r.iota > iota_a]
    near = [r for r in eligible
            if abs(r.iota - iota_a) <= C.COVERAGE_NEAR_CALIPER]
    cls = [r for r in rows
           if r.role == "class_control" and lib.eligible_prescreen(r)]
    class_near = sorted(
        (r for r in cls
         if abs(r.iota - iota_a) <= C.CLASS_MATCH_CALIPER),
        key=lambda r: abs(r.iota - iota_a))
    straddling = sorted({
        k for k in {r.kind for r in eligible}
        if any(r.iota < iota_a for r in eligible if r.kind == k)
        and any(r.iota > iota_a for r in eligible if r.kind == k)})
    return {
        "eligible_reference_rungs": len(eligible),
        "easier_support": {
            "rungs": len(below),
            "feature_groups": sorted({feature_group(r.kind) for r in below}),
            "meets_min": len(below) >= C.SUPPORT_MIN_BELOW},
        "harder_support": {
            "rungs": len(above),
            "feature_groups": sorted({feature_group(r.kind) for r in above}),
            "meets_min": len(above) >= C.SUPPORT_MIN_ABOVE},
        "local_density": {
            "caliper": C.COVERAGE_NEAR_CALIPER,
            "rungs": len(near), "labels": [r.label for r in near],
            "feature_groups": sorted({feature_group(r.kind) for r in near})},
        "family_diversity": {
            "families": len({r.kind for r in eligible}),
            "feature_groups":
                len({feature_group(r.kind) for r in eligible})},
        "spectrum_support": {
            "straddling_families": straddling,
            "straddling_feature_groups":
                sorted({feature_group(k) for k in straddling}),
            "needed": C.N_CORE_REFERENCES,
            "sufficient_for_a_full_spectrum":
                len({feature_group(k) for k in straddling})
                >= C.N_CORE_REFERENCES},
        "core_reference_availability": {
            "eligible_families": sorted({r.kind for r in eligible}),
            "shortlist_needs": C.SHORTLIST_REFERENCE_FAMILIES},
        "class_candidates": {
            "caliper": C.CLASS_MATCH_CALIPER,
            "matched": [r.label for r in class_near],
            "nearest": class_near[0].label if class_near else None,
            "families": sorted({r.kind for r in class_near})},
    }


def _leave_one_out(rows, iota_a: float) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for dropped in sorted({r.kind for r in rows}):
        report = lib.coverage_report([r for r in rows if r.kind != dropped],
                                     iota_a)
        out[dropped] = {
            "passed": report.passed,
            "failed": sorted(k for k, v in report.conditions.items()
                             if not v["met"] and k != "C7_class_matched")}
    fragile = sorted(k for k, v in out.items() if not v["passed"])
    return {"per_family": out, "load_bearing_families": fragile,
            "robust": not fragile}


def main() -> int:
    context = registered_context()
    prior = fs.read_json(PRIOR) if PRIOR.exists() else {}
    models: dict[str, Any] = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        record = read_stage_record(tree, C.STAGE_REGIME)
        iota_a = record["iota_a_prescreen"]
        rows = _rows(record)
        report = lib.coverage_report(rows, iota_a)
        counterfactual = (prior.get("models", {}).get(model_key, {})
                          .get("coverage_with_cp4_cp7", {}))
        models[model_key] = {
            "study_id": record["study_id"],
            "outcome": record["outcome"],
            "selected_cap": record["selected_cap"],
            "iota_a_prescreen": iota_a,
            "eligible_rungs_measured": len(rows),
            "rounds_run": record["expansion"]["rounds_run"],
            "identification_statuses": record["expansion"]["statuses"],
            "coverage": report.as_dict(),
            "support": _support(rows, iota_a),
            "leave_one_family_out": _leave_one_out(rows, iota_a),
            "counterfactual_before_r4": {
                "population": "v4r3's 30 families, on the same measured table",
                "passed": counterfactual.get("passed"),
                "conditions_that_moved": prior.get("models", {})
                    .get(model_key, {}).get("conditions_that_moved", []),
            },
            "evidence_provenance": record.get("evidence_provenance"),
        }

    passed = all(m["coverage"]["passed"] for m in models.values())
    report = {
        "artifact_type": "v4r4-coverage",
        "reads": "the four signed v4r4 REGIME_SCREEN records; solo and chance "
                 "compliance only",
        "reads_no_composed_outcome": True,
        "population": {"families": len(FAMILIES),
                       "removed_in_v4r4": sorted(REMOVED_IN_V4R4)},
        "criterion": "§12.6: C1 to C6 are decisive; C7 is not terminal, and "
                     "an unmatched class companion attaches "
                     "COMPANION_CLASS_NOT_MATCHED and the study proceeds",
        "models": models,
        "every_model_passes": passed,
        "identification_status": None if passed
        else "DIFFICULTY_SUPPORT_NOT_IDENTIFIED",
        "leave_one_family_out_note":
            "C4 requires four well-formed straddling feature groups. Where a "
            "model has exactly four, every one of them is load-bearing and "
            "the sweep says so. This is a property of the reference pool that "
            "v4r3 already had; the counterfactual above shows the same "
            "families. §12.6's registered expansion draws from the frozen "
            "reserve and is available if the researcher judges the margin too "
            "thin --- it is not invoked here, because invoking it after "
            "seeing a coverage result is a decision the protocol reserves",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, report)
    print(json.dumps({
        "every_model_passes": passed,
        "models": {k: {
            "iota_A": round(v["iota_a_prescreen"], 4),
            "cap": v["selected_cap"],
            "C1-C7": {c: v["coverage"]["conditions"][c]["met"]
                      for c in sorted(v["coverage"]["conditions"])},
            "eligible_reference_rungs":
                v["support"]["eligible_reference_rungs"],
            "near_rungs": v["support"]["local_density"]["rungs"],
            "straddling_groups":
                v["support"]["spectrum_support"]["straddling_feature_groups"],
            "class_nearest": v["support"]["class_candidates"]["nearest"],
            "leave_one_out_robust": v["leave_one_family_out"]["robust"],
            "load_bearing": v["leave_one_family_out"]["load_bearing_families"],
        } for k, v in models.items()},
        "written": str(OUT),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
