#!/usr/bin/env python3
"""Analyse the matrix screen and write reports/matrix_screen_v4/results.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import gitinfo                        # noqa: E402
from dci1v4.models.registry import MODEL_KEYS            # noqa: E402
from matrix_screen_v4 import CLASSIFICATION, STUDY_ID    # noqa: E402
from matrix_screen_v4 import analysis, protocol          # noqa: E402

OUT = DCI1 / "reports" / "matrix_screen_v4"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resamples", type=int, default=10000)
    parser.add_argument("--models", nargs="+", default=list(MODEL_KEYS))
    args = parser.parse_args()

    results, frozen = {}, {}
    for model in args.models:
        try:
            results[model] = analysis.analyse(model, resamples=args.resamples)
            frozen[model] = protocol.load(model)["screen_protocol_hash"]
        except FileNotFoundError as error:
            results[model] = {"unavailable": str(error)}

    def primary(entry, name):
        try:
            return entry["compliance"]["pooled_over_orders"]["families"][
                "primary"][name]
        except (KeyError, TypeError):
            return None

    payload = {
        "study_id": STUDY_ID, "classification": CLASSIFICATION,
        "producing_commit": gitinfo.head_commit(DCI1.parent),
        "screen_protocol_hashes": frozen, "resamples": args.resamples,
        "claim_licensed": False,
        "why_no_claim": ("§17.3 precision preconditions require 384 blocks; "
                         "this screen runs on screen topics with a "
                         "provisional reference set and licenses no L1, L2 or "
                         "L3 statement"),
        "models": results,
        "summary": {model: ({
            "Delta_R": primary(entry, "Delta_R"),
            "D_B_from_A": primary(entry, "D_B_from_A"),
            "D_A_from_B": primary(entry, "D_A_from_B"),
            "Lambda": primary(entry, "Lambda"),
            "Xi": (entry.get("compliance", {}).get("pooled_over_orders", {})
                        .get("families", {}).get("reciprocal", {}).get("Xi")),
            "Delta_R_reading": (entry.get("compliance", {})
                                     .get("pooled_over_orders", {})
                                     .get("Delta_R_reading", {})
                                     .get("where_the_interval_sits")),
            "V5_A_residual": (entry.get("companion_difficulty_v5", {})
                                   .get("A_residual")),
            "rho_mean": entry.get("rho_a_versus_reference", {}).get("mean"),
        } if "unavailable" not in entry else entry)
            for model, entry in results.items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(payload["summary"], indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
