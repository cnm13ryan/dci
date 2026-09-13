"""Freeze the lower-bound arm's protocol, per model."""
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
    return FROZEN_DIR / f"screen_protocol_lower_bound_{model}.json"


def build(model: str, context: dict[str, Any], cells: Sequence[Any]
          ) -> dict[str, Any]:
    from cal_screen_v4 import lowerbound_run
    return {
        "study_id": STUDY_ID, "classification": CLASSIFICATION,
        "arm": "lower_bound", "model": model,
        "status": ("NON-CONFIRMATORY DESIGN SCREEN, fourth arm. Not a "
                   "registered §12.3 record. Amendment B's recommended set is "
                   "unchanged and nothing here is adopted."),
        "producing_commit": gitinfo.head_commit(DCI1.parent),
        "question": ("A is the only PRODUCTION constraint in the v4 pool; B "
                     "and every reference, registered or candidate, is a "
                     "budget. So a positive Delta_R is equally consistent with "
                     "'A is unusually damaging to B' and with 'a production "
                     "constraint is damaging to a budget outcome, and A is the "
                     "only one available'. The lower-bound families are the "
                     "only candidates that share A's class. Does one of them "
                     "clear §13.2 on the calibration set, so that the "
                     "class-matched contrast D(B<-A) against D(B<-CL) becomes "
                     "estimable?"),
        "why_amendment_B_set_it_aside": (
            "Amendment B §6: a lower bound imposes a length FLOOR, pushing "
            "length up while B pushes it down. That objection was written for "
            "the current stem. Under the floored stem the stem already imposes "
            "a length floor on every cell, so the mirror-image confound is "
            "weaker; this arm measures it rather than assuming either way."),
        "families": context["families"], "ladders": context["ladders"],
        "cells": len(cells), "draws_per_cell": C.M_CAL,
        "stem": "floored",
        "topics": "the 96 registered solo-calibration topics, unchanged",
        "seeds": {"stage_label": lowerbound_run.STAGE},
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
