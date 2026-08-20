"""Freeze the screen protocol to JSON and hash it, before the first generation.

The decision rule of §1.4 is part of the frozen payload, so the PASS / MARGINAL
/ FAIL verdict cannot be re-specified after the curve is seen.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dci1v4.engine import gitinfo
from dci1v4.protocol import constants as C
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.constraints import FOCAL_GRID, TARGET_GRID
from dci1v4.verifiers.wording_suite import TWENTY_RESPONSES

from bgrid_screen_v4 import CLASSIFICATION, STUDY_ID
from bgrid_screen_v4 import focal
from bgrid_screen_v4 import plan as pl

DCI1 = Path(__file__).resolve().parent.parent.parent
FROZEN = DCI1 / "reports" / "bgrid_screen_v4" / "screen_protocol.json"


def build(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or DCI1.parent
    return {
        "study_id": STUDY_ID,
        "classification": CLASSIFICATION,
        "status": ("NON-CONFIRMATORY DESIGN SCREEN. Not a registered v4 stage. "
                   "No Gate 1 dependency. Nothing here may enter a v4 "
                   "estimator, and evidence/bgrid-screen-v4 is outside the v4 "
                   "namespace so the positive-admission guard refuses it."),
        "producing_commit": gitinfo.head_commit(repo_root),
        "question": (
            "Under the current stem, honest B-solo compliance is 0.000 on "
            "qwen3-4b and 0.042 on qwen3-4b-instruct-2507; the apparent ~0.75 "
            "is carried entirely by sub-twenty-word answers. Under the floored "
            "stem both Qwens exhaust the registered focal grid m in {7,8,9,10}. "
            "Does an honest focal severity exist at m <= 12 on all four models?"),
        "grid": {
            "registered_focal_grid": list(FOCAL_GRID),
            "screen_focal_grid": list(focal.SCREEN_FOCAL_GRID),
            "screen_only_extension": list(focal.EXTENSION),
            "extension_is_not_registered": True,
            "rule_unchanged": ("longest alphabetic run at most m letters; only "
                               "the severity range is extended, inside this "
                               "screen only"),
            "wordings_identical_on_registered_rungs":
                focal.assert_wordings_match(),
            "scoring_identical_on_registered_rungs":
                focal.assert_scoring_matches(TWENTY_RESPONSES),
            "monotone_in_m": focal.assert_monotone_in_m(TWENTY_RESPONSES),
        },
        "stem": pl.assert_stem_identical(),
        "topics": {
            "set": "the 24 registered pre-screen topics, unchanged",
            "why": ("the registered development sample, already spent for "
                    "stem-choice purposes by the FORM x STEM screen. This "
                    "screen measures the B-solo curve and selects no reference "
                    "family, so it adds no new §13.2 condition 2 contamination "
                    "beyond what that screen already created."),
            "untouched": ["96 solo calibration", "24 composed validation",
                          "384 confirmatory", "96 sequestered"],
            "dependency_recorded": True,
        },
        "cells": {
            "b_solo_floored": list(focal.SCREEN_FOCAL_GRID),
            "b_solo_current": list(pl.CURRENT_STEM_RUNGS),
            "b_solo_current_reused": ("m = 7 to 10 from the registered §12.2 "
                                      "ladder screen, read only"),
            "a_solo_floored": list(TARGET_GRID),
            "fixture_floored": {"a_severity": pl.FIXTURE_A_N,
                                "b_severities": list(focal.SCREEN_FOCAL_GRID)},
            "draws_per_cell": 1,
            "completion_cap": "each model's own §12.1 selected cap",
            "decoding": "the registered policy, unchanged",
            "tensor_parallel_size": 1,
        },
        "readouts": [
            "raw B-solo compliance",
            "non-vacuous compliance at >= 20 words",
            "vacuous share of passes",
            "word-count distribution",
            "realised max-word-length distribution",
            "truncation rate",
            "stem-satisfaction rate",
            "smallest in-band m, its distance from each band edge, and a "
            "topic-clustered standard error on that compliance",
        ],
        "decision_rule": {
            "band": list(C.FOCAL_BAND),
            "band_is_registered": True,
            "PASS": ("every model has at least one m in the screen grid inside "
                     "the registered focal band under the floored stem, and "
                     "that rung sits MORE than one standard error from both "
                     "band edges"),
            "MARGINAL": ("every model has an in-band rung and at least one sits "
                         "within one standard error of a band edge; a "
                         "fresh-topic confirmation is then required before any "
                         "grid amendment"),
            "FAIL": "any model has no in-band rung at m <= 12",
            "no_extension_past_12": ("the grid is not extended past m = 12 to "
                                     "obtain a pass; a model needing m > 12 is "
                                     "reported as the finding"),
            "standard_error": ("topic-clustered bootstrap standard deviation of "
                               "the compliance estimate, 2000 resamples over "
                               "the 24 topics"),
            "fixed_before": "the first generation of this screen",
        },
        "prior_prediction": {
            "source": "the FORM x STEM screen's pooled extrapolation",
            "qwen3-4b": [11, 12],
            "qwen3-4b-instruct-2507": [10, 11],
            "known_bias": ("on gemma-3n-e2b-it the pooled figure ran about 0.09 "
                           "above the direct measurement, so the prediction is "
                           "treated as optimistic and the realised gap is "
                           "reported"),
        },
        "seeds": {
            "screen_root": pl.SCREEN_ROOT_SEED,
            "domain": pl.DOMAIN_SCREEN_GENERATION,
            "stage_label": pl.STAGE,
            "derivation": "domain, root, stage, model_id, prompt hash, draw",
            "distinct_from": {"v3_roots": "202608170-202608175",
                              "v4_roots": "202608190-202608195",
                              "fs_screen_root": 202608200},
        },
        "registered_values_untouched": {
            "focal_grid": list(FOCAL_GRID),
            "focal_band": list(C.FOCAL_BAND), "focal_aim": C.FOCAL_AIM,
            "target_grid": list(TARGET_GRID),
            "target_band": list(C.TARGET_BAND), "target_aim": C.TARGET_AIM,
            "non_vacuity_min_words": C.NON_VACUITY_MIN_WORDS,
            "reference_caliper": C.REFERENCE_CALIPER,
            "reference_vacuity_max": C.REFERENCE_VACUITY_MAX,
            "note": ("listed so a later diff proves the screen changed none of "
                     "them"),
        },
        "verifier_source_hash": verifier_source_hash(),
    }


def protocol_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()


def freeze(repo_root: Path | None = None) -> dict[str, Any]:
    """Write the frozen protocol once; refuse to overwrite a different one."""
    payload = build(repo_root)
    digest = protocol_hash(payload)
    record = {"screen_protocol_hash": digest, "payload": payload}
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    if FROZEN.exists():
        existing = json.loads(FROZEN.read_text())
        if existing["screen_protocol_hash"] != digest:
            raise RuntimeError(
                f"the screen protocol is already frozen at "
                f"{existing['screen_protocol_hash']} and would change to "
                f"{digest}; a frozen screen protocol is never rewritten")
        return existing
    FROZEN.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return record


def load() -> dict[str, Any]:
    return json.loads(FROZEN.read_text())
