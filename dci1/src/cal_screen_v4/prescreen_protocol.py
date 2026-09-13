"""Freeze the pre-screen-at-M_cal arm's protocol, per model."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from dci1v4.engine import gitinfo
from dci1v4.protocol import constants as C
from dci1v4.verifiers import verifier_source_hash

from cal_screen_v4 import CLASSIFICATION, STUDY_ID

DCI1 = Path(__file__).resolve().parent.parent.parent
FROZEN_DIR = DCI1 / "reports" / "cal_screen_v4"


def frozen_path(model: str) -> Path:
    return FROZEN_DIR / f"screen_protocol_prescreen_m4_{model}.json"


def build(model: str, context: dict[str, Any], cells: Sequence[Any]
          ) -> dict[str, Any]:
    from cal_screen_v4 import prescreen_run
    return {
        "study_id": STUDY_ID, "classification": CLASSIFICATION,
        "arm": "prescreen_m4", "model": model,
        "status": ("NON-CONFIRMATORY DESIGN SCREEN, third arm. Not a "
                   "registered §12.2 record."),
        "producing_commit": gitinfo.head_commit(DCI1.parent),
        "question": ("§13.2 condition 2 bounds a quantity at 0.15 that §12.2 "
                     "measures at one draw on 24 topics. Does the condition "
                     "decide differently when the quantity it reads is "
                     "measured at M_cal = 4 on the same topics?"),
        "what_is_not_changed": (
            "the criterion. The 0.15 caliper, the topic set, the stem, the "
            "wordings and the verifier are all identical to the registered "
            "condition. Only the number of draws behind the estimate changes, "
            "which is a precision change and not a criterion change. The "
            "registered-precision result is reported as the primary number and "
            "this arm beside it."),
        "why_this_is_not_weakening": (
            "§31 forbids an amendment that weakens a criterion so a gate "
            "passes. Measuring the same quantity more precisely against the "
            "same threshold is the opposite move: it can reject a reference "
            "the one-draw estimate would have admitted, and on these models it "
            "does both. Nothing here is adopted."),
        "arms": {
            "A": "the full n grid",
            "candidates": "CR7, CR4, CR6 full ladders",
            "registered_pool": context["registered_shortlist"],
        },
        "a_prescreen_anchor_one_draw": context["a_prescreen_anchor_one_draw"],
        "cells": len(cells), "draws_per_cell": C.M_CAL,
        "topics": "the 24 registered pre-screen topics, unchanged",
        "stem": "floored",
        "seeds": {"stage_label": prescreen_run.STAGE,
                  "note": "a distinct stage label, so no row of this arm can "
                          "share a seed with the main arm, the pool arm or the "
                          "FORM x STEM screen at an identical prompt"},
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
