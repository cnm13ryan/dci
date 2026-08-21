#!/usr/bin/env python3
"""Analyse the calibration screen and write reports/cal_screen_v4/results.json.

Usage: python tools/cal_screen_report_v4.py [--resamples 10000]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DCI1 / "src"))

from cal_screen_v4 import CLASSIFICATION, STUDY_ID   # noqa: E402
from cal_screen_v4 import analysis, protocol         # noqa: E402
from dci1v4.engine import gitinfo                    # noqa: E402
from dci1v4.models.registry import MODEL_KEYS        # noqa: E402

OUT = DCI1 / "reports" / "cal_screen_v4"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resamples", type=int, default=10000)
    parser.add_argument("--models", nargs="+", default=list(MODEL_KEYS))
    args = parser.parse_args()

    frozen = protocol.load()
    results = {}
    for model in args.models:
        try:
            results[model] = analysis.analyse(model, resamples=args.resamples)
        except FileNotFoundError as error:
            results[model] = {"unavailable": str(error)}

    payload = {
        "study_id": STUDY_ID, "classification": CLASSIFICATION,
        "screen_protocol_hash": frozen["screen_protocol_hash"],
        "producing_commit": gitinfo.head_commit(DCI1.parent),
        "resamples": args.resamples,
        "criteria": frozen["success_criteria"],
        "models": results,
        "summary": {
            model: {
                "Q1_candidate_families_admitted":
                    entry.get("admission", {}).get("candidates", {})
                         .get("n_admitted"),
                "Q1_registered_control_admitted":
                    entry.get("admission", {}).get("registered_control", {})
                         .get("n_admitted"),
                "Q1_lower_bound_admitted":
                    entry.get("admission", {}).get("lower_bound", {})
                         .get("n_admitted"),
                "Q1_enlarged_pool_families":
                    entry.get("admission", {}).get("enlarged_pool", {})
                         .get("admitted_families"),
                "class_matched_companion":
                    (entry.get("admission", {})
                          .get("class_matched_companion", {}) or {})
                         .get("selected"),
                "condition_2_sensitivity_enlarged":
                    (entry.get("admission", {})
                          .get("condition_2_sensitivity", {}) or {})
                         .get("enlarged_pool", {}).get("n_admitted"),
                "condition_2_at_M_cal_enlarged":
                    (entry.get("admission", {})
                          .get("condition_2_at_M_cal", {}) or {})
                         .get("enlarged_pool", {}).get("n_admitted"),
                "feasible_rungs_floored_mean_reading": [
                    x["m"] for x in entry.get("regime_adequacy_by_rung", {})
                    .get("floored", []) if x["feasible_mean_reading"]],
                "feasible_rungs_floored_share_reading": [
                    x["m"] for x in entry.get("regime_adequacy_by_rung", {})
                    .get("floored", []) if x["feasible_share_reading"]],
                "feasible_rungs_current_any_reading": [
                    x["m"] for x in entry.get("regime_adequacy_by_rung", {})
                    .get("current", [])
                    if x["feasible_mean_reading"] or x["feasible_share_reading"]],
                "Q2_m_star_registered_grid":
                    entry.get("verdicts", {})
                         .get("Q2_honest_focal_severity", {})
                         .get("registered_grid_m_star"),
                "Q2_m_star_extended_grid":
                    entry.get("verdicts", {})
                         .get("Q2_honest_focal_severity", {})
                         .get("extended_grid_m_star"),
                "Q3_regime_adequacy": entry.get("verdicts", {})
                                           .get("Q3_regime_adequacy"),
                "Q1_enlarged_pool_admitted":
                    entry.get("admission", {}).get("enlarged_pool", {})
                         .get("n_admitted"),
                "n_star_floored": entry.get("admission", {})
                                       .get("anchor", {}).get("n_star"),
            } if "unavailable" not in entry else entry
            for model, entry in results.items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(payload["summary"], indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
