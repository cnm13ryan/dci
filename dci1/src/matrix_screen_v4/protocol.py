"""Freeze the matrix screen's protocol, including the constraint set itself.

The constraint set is part of the frozen payload and not a runtime argument.
That is the point: §13.3 exists because selecting a control on what it does to
the outcome is circular, and a screen is exactly where that would happen
unnoticed. The references, n*, m* and the spanning rungs are read once from the
calibration screen's §13.2 output, hashed here, and may not be revised on
anything this screen produces.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dci1v4.engine import gitinfo
from dci1v4.protocol import constants as C
from dci1v4.verifiers import verifier_source_hash

from matrix_screen_v4 import CLASSIFICATION, STUDY_ID
from matrix_screen_v4 import plan as pl

DCI1 = Path(__file__).resolve().parent.parent.parent
CAL_RESULTS = DCI1 / "reports" / "cal_screen_v4" / "results.json"
FROZEN_DIR = DCI1 / "reports" / "matrix_screen_v4"


def frozen_path(model: str) -> Path:
    return FROZEN_DIR / f"screen_protocol_{model}.json"


NO_REVISION_DECLARATION = (
    "The reference set, n*, m* and the spanning rungs below are inputs to this "
    "screen and outputs of the calibration screen. No reference family, no "
    "reference severity, no n*, no m*, and no amendment may be revised, "
    "reordered or reconsidered on any evidence this screen produces. §13.3: "
    "selecting a control on the outcome it is meant to counterfactual is "
    "circular, and a pre-freeze screen is where that would happen unnoticed. "
    "If this screen's numbers were to change a reference decision, the "
    "reference decision would have to be remade from the calibration evidence "
    "alone, on a fresh topic sample, and this screen discarded.")


def build(model: str, design: dict[str, Any],
          repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or DCI1.parent
    cal = json.loads(CAL_RESULTS.read_text())
    return {
        "study_id": STUDY_ID,
        "classification": CLASSIFICATION,
        "model": model,
        "status": ("NON-CONFIRMATORY DESIGN SCREEN. Not a registered v4 stage. "
                   "It runs the registered §8.1 cell set at screen scale on "
                   "screen topics, so it cannot meet the §17.3 precision "
                   "preconditions and licenses no L1, L2 or L3 statement."),
        "producing_commit": gitinfo.head_commit(repo_root),
        "no_revision_declaration": NO_REVISION_DECLARATION,
        "design": design["design"],
        "m_star_source": design["m_star_source"],
        "admitted_families": design["admitted_families"],
        "admission_disposition": design["admission_disposition"],
        "reference_slot_rule": design["reference_slot_rule"],
        "reference_slots_exclude_lower_bound_families": (
            "the three R slots are drawn from the BUDGET families in §13.2's "
            "own order and the lower-bound families are reserved for the class "
            "arm. A lower-bound reference would make Delta_R a mixed-class "
            "contrast and would blur the distinction the class arm draws; on "
            "some models it would also put one family in both slots."),
        "reference_pool_selected_from": (
            "the eight registered families plus the three candidate rate "
            "families, with §13.2's own selection rule unchanged. Neither "
            "Amendment B nor any other amendment is adopted by this screen; "
            "the enlarged pool is what §13.2 would rank if it were, and "
            "restricting to candidates alone would be a selection rule the "
            "protocol does not contain."),
        "n_references_admitted": design["n_references_admitted"],
        "constraint_set": design["constraint_set"],
        "class_control_arm": {
            "purpose": ("A is the only PRODUCTION constraint in the registered "
                        "pool; B and every reference are budgets. Delta_R "
                        "against budgets alone cannot separate 'A damages B' "
                        "from 'a production companion damages a budget "
                        "outcome'. This arm adds the best-admitted lower-bound "
                        "family, composed with BOTH outcome constraints in "
                        "both orders, so Delta_class = D(B<-A) - D(B<-CL) is "
                        "estimable with the companion's class held fixed."),
            "companion": design["class_control"],
            "cells": ("one solo cell and four composed cells per block: "
                      "B+CL and A+CL, each in both orders"),
        },
        "spanning_arm": {
            "purpose": ("registered open decision V5: matched-only references "
                        "cannot estimate the relationship between companion "
                        "solo difficulty and delivery loss, because they hold "
                        "difficulty fixed by construction. This arm varies it."),
            "rule": ("per admitted family, the ladder rungs whose calibration "
                     f"solo compliance is nearest the matched rung's plus "
                     f"{list(pl.SPANNING_OFFSETS)}, among rungs meeting the "
                     f"same §13.2 vacuity condition; ties toward the less "
                     f"restrictive severity"),
            "orders": ("one, B stated first, so each spanning loss is "
                       "position-matched to B's solo cell (§11.4)"),
            "rungs": design["spanning"],
            "family": design.get("spanning_family"),
            "selection": design.get("spanning_rule"),
        },
        "witnesses": design["witnesses"],
        "cell_set": {
            "source": "§8.1 verbatim: 5 solo cells and 10 unordered pairs in "
                      "both orders",
            "wording_allocation": "§8.4 verbatim",
            "prompt_template": "§8.5, with the screen stem inserted after the "
                               "topic question",
            "stem": design["stem"],
            "draws_per_cell": pl.DRAWS,
            "summary": design["plan_summary"],
            "allocation_assertion": design["allocation"],
        },
        "topics": design["topics"],
        "topic_set_authority": design["topic_set_authority"],
        "inputs_from_the_calibration_screen": {
            "path": str(CAL_RESULTS.relative_to(DCI1)),
            "sha256": hashlib.sha256(CAL_RESULTS.read_bytes()).hexdigest(),
            "screen_protocol_hash": cal.get("screen_protocol_hash"),
            "admission_status": design["admission_status"],
        },
        "seeds": {
            "screen_root": pl.SCREEN_ROOT_SEED,
            "domain": pl.DOMAIN_SCREEN_GENERATION,
            "stage_label": pl.STAGE,
            "distinct_from": {"v3_roots": "202608170-202608175",
                              "v4_roots": "202608190-202608195",
                              "fs_screen_root": 202608200,
                              "bgrid_screen_root": 202608210,
                              "cal_screen_root": 202608220},
        },
        "what_this_can_and_cannot_support": {
            "can": ["whether the registered design identifies Delta_R, Xi and "
                    "the reciprocal losses at all",
                    "the sign and rough size of Delta_R for THIS reference set",
                    "the companion-difficulty relationship of decision V5",
                    "the A-versus-reference block correlation the §16.1 "
                    "variance model needs"],
            "cannot": ["any L1, L2 or L3 claim: the §17.3 precision "
                       "preconditions need the 384 confirmatory blocks",
                       "outcome specificity: Xi's half-width at screen scale "
                       "is far wider than the interval that would separate "
                       "the hypotheses",
                       "anything about a reference set other than this one: "
                       "if Gate 3 later admits different families or "
                       "severities, every per-reference number here is about "
                       "constraints that are not in the study"],
        },
        "registered_values_untouched": {
            "delta_R_generic_load_threshold": C.DELTA_R_GENERIC_THRESHOLD,
            "delta_R_pair_specific_threshold":
                C.DELTA_R_PAIR_SPECIFIC_THRESHOLD,
            "equivalence_region": C.EQUIVALENCE_REGION,
            "m_draws": C.M_DRAWS, "n_blocks_registered": C.N_BLOCKS,
            "note": ("listed so a later diff proves the screen changed none of "
                     "them; both Delta_R thresholds predate every observation "
                     "in this constraint vocabulary (§11.6)"),
        },
        "verifier_source_hash": verifier_source_hash(),
    }


def freeze(model: str, design: dict[str, Any]) -> dict[str, Any]:
    payload = build(model, design)
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
