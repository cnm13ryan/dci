"""Freeze the registered-pool arm's protocol, per model.

Separately hashed from the main arm so neither pass can invalidate the other's
provenance, and so the shortlist -- which is model-specific and derived from
pre-screen data -- is on the record before the arm generates anything.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from dci1v4.engine import gitinfo
from dci1v4.protocol import constants as C
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.constraints import REFERENCE_LADDERS

from cal_screen_v4 import CLASSIFICATION, STUDY_ID

DCI1 = Path(__file__).resolve().parent.parent.parent
FROZEN_DIR = DCI1 / "reports" / "cal_screen_v4"


def frozen_path(model: str) -> Path:
    return FROZEN_DIR / f"screen_protocol_registered_pool_{model}.json"


def build(model: str, context: dict[str, Any], cells: Sequence[Any]
          ) -> dict[str, Any]:
    from cal_screen_v4 import pool_run
    return {
        "study_id": STUDY_ID, "classification": CLASSIFICATION,
        "arm": "registered_pool", "model": model,
        "status": ("NON-CONFIRMATORY DESIGN SCREEN, second arm. Not a "
                   "registered §12.3 record."),
        "producing_commit": gitinfo.head_commit(DCI1.parent),
        "question": ("under the floored stem, does the REGISTERED reference "
                     "pool clear §13.2 on the 96 solo-calibration topics at "
                     "M_cal = 4? If it does, the pool's failure was a length "
                     "artifact the stem already fixes and Amendment B is "
                     "unnecessary, which preserves Gate 1's instrument freeze."),
        "why_it_was_not_already_answered": (
            "the FORM x STEM screen measured count x floored on 24 pre-screen "
            "topics at one draw and found exactly two families reaching the "
            "conjunction on all four models. Two is a near miss against a "
            "requirement of three, at one-family resolution on a sample its "
            "own report calls unstable. §13.2 admits against the calibration "
            "set and that crossing has never been run."),
        "shortlist": context["shortlist"],
        "shortlist_rule": context["shortlist_rule"],
        "a_prescreen_anchor_floored": context["a_prescreen_anchor_floored"],
        "cells": len(cells),
        "draws_per_cell": C.M_CAL,
        "stem": "floored",
        "topics": "the 96 registered solo-calibration topics, unchanged",
        "seeds": {"stage_label": pool_run.STAGE,
                  "note": "a distinct stage label, so a pool row and a "
                          "main-arm row at an identical prompt never share a "
                          "seed"},
        "registered_values_untouched": {
            "reference_ladders": {k: list(v)
                                  for k, v in REFERENCE_LADDERS.items()},
            "ladder_shortlist_max": C.LADDER_SHORTLIST_MAX,
            "reference_caliper": C.REFERENCE_CALIPER,
            "reference_vacuity_max": C.REFERENCE_VACUITY_MAX},
        "verifier_source_hash": verifier_source_hash(),
    }


def freeze(model: str, context: dict[str, Any], cells: Sequence[Any]
           ) -> dict[str, Any]:
    payload = build(model, context, cells)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["screen_protocol_hash"] = hashlib.sha256(
        blob.encode("utf-8")).hexdigest()
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    frozen_path(model).write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return payload


def load(model: str) -> dict[str, Any]:
    path = frozen_path(model)
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; freeze before generating")
    return json.loads(path.read_text())
