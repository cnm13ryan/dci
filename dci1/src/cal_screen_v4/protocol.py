"""Freeze the screen protocol to JSON and hash it, before the first generation.

The hash is recorded on every row. A screen whose protocol hash does not match
the frozen file is not this screen.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dci1v4.engine import gitinfo
from dci1v4.protocol import constants as C
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          TARGET_GRID)

from cal_screen_v4 import CLASSIFICATION, STUDY_ID
from cal_screen_v4 import admission as ad
from cal_screen_v4 import plan as pl
from fs_screen_v4 import suite, witnesses
from fs_screen_v4.constraints import CANDIDATES
from fs_screen_v4.wordings import candidate_wordings, caliper_table

DCI1 = Path(__file__).resolve().parent.parent.parent
FROZEN = DCI1 / "reports" / "cal_screen_v4" / "screen_protocol.json"


def build(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or DCI1.parent
    return {
        "study_id": STUDY_ID,
        "classification": CLASSIFICATION,
        "status": ("NON-CONFIRMATORY DESIGN SCREEN. Not a registered v4 stage. "
                   "Gate 1 is not approved and the canonical verifier hash is "
                   "not frozen, so nothing generated here is a §12.3 record. "
                   "It writes only under evidence/cal-screen-v4, outside the "
                   "v4 namespace, where the positive-admission guard refuses "
                   "it."),
        "producing_commit": gitinfo.head_commit(repo_root),
        "questions": {
            "Q1_reference": ("do the three candidate rate families reach the "
                             "§13.2 condition-1 ∧ condition-6 conjunction on "
                             "the 96 solo-calibration topics at M_cal = 4 — "
                             "the confirmation Amendment B §9 makes a "
                             "precondition of adoption"),
            "Q2_focal_grid": ("does an honest focal severity exist under the "
                              "floored stem on the calibration set — the "
                              "fresh-topic confirmation the B-grid screen's "
                              "MARGINAL verdict requires"),
            "Q3_regime": ("does §12.4 regime adequacy hold under the current "
                          "stem, under the floored stem, or under neither — "
                          "the pre-screen B-solo vacuity rates of 0.29-0.71 "
                          "against a 0.10 maximum have never been measured on "
                          "the calibration set"),
        },
        "arms": {
            "a_solo": {"stem": "floored", "kind": "A",
                       "severities": list(TARGET_GRID)},
            "b_solo_floored": {"stem": "floored", "kind": "B",
                               "severities": list(ad.focal.SCREEN_FOCAL_GRID)},
            "b_solo_current": {"stem": "current", "kind": "B",
                               "severities": list(ad.focal.SCREEN_FOCAL_GRID)},
            "candidate": {"stem": "floored",
                          "families": list(pl.CANDIDATE_FAMILIES),
                          "ladders": {f: list(CANDIDATES[f].ladder)
                                      for f in pl.CANDIDATE_FAMILIES}},
            "registered_control": {
                "stem": "floored",
                "rungs": pl.REGISTERED_CONTROL_RUNGS,
                "rule": ("one rung per family, from the families whose best "
                         "FLOORED-stem pre-screen rung is nearest A's "
                         "floored-stem pre-screen solo compliance at the "
                         "§12.3 choice of n on that curve; ties by family "
                         "identifier then by the less restrictive severity. "
                         "Measured under the same stem the arm is generated "
                         "under, so the registered pool gets its best shot "
                         "rather than a rung picked on a different stem"),
                "source": ("reports/fs_screen_v4/results.json, the FORM x STEM "
                           "screen's floored-stem curves on the same 24 "
                           "pre-screen topics, read only"),
            },
        },
        "what_is_deliberately_absent": {
            "candidate_families_under_the_current_stem": (
                "the current stem's B-solo vacuity is 0.29-0.71 at pre-screen "
                "against a §12.4 maximum of 0.10, so reference admission "
                "under it is moot unless Q3 reverses on 96 topics; if it "
                "does, this arm is the follow-up"),
            "a_solo_under_the_current_stem": (
                "n* under the current stem is moot for the same reason; the "
                "FORM x STEM screen carries it at 24 topics"),
            "lower_bound_candidate_families": (
                "Amendment B §6: a lower bound imposes a length floor, "
                "pushing length up while B pushes it down"),
            "composed_cells": (
                "this screen calibrates; the pairwise matrix screen estimates"),
        },
        "inherited": pl.assert_inherited_definitions(),
        "extended_grid_is_the_registered_rule":
            ad.assert_extended_grid_is_registered_rule(),
        "admission_is_the_registered_admission":
            ad.assert_equivalent_to_registered(),
        "discipline": {
            "wordings_per_constraint": pl.N_WORDINGS,
            "wording_allocation": "the registered §8.4 solo rule, i mod 4",
            "length_caliper_against": "A",
            "length_caliper_tolerance": 0.20,
            "wording_equivalence_verdicts": suite.assert_wording_equivalence(),
            "parse_independence": "asserted on the callable signatures",
            "witness_compositions_certified":
                witnesses.verify_all()["compositions_certified"],
            "caliper_table_at_n4": caliper_table(4),
        },
        "seeds": {
            "screen_root": pl.SCREEN_ROOT_SEED,
            "domain": pl.DOMAIN_SCREEN_GENERATION,
            "stage_label": pl.STAGE,
            "derivation": "domain, root, stage, model_id, prompt hash, draw",
            "distinct_from": {"v3_roots": "202608170-202608175",
                              "v4_roots": "202608190-202608195",
                              "fs_screen_root": 202608200,
                              "bgrid_screen_root": 202608210},
        },
        "generation": {
            "topics": "the 96 registered solo-calibration topics, unchanged",
            "draws_per_cell": pl.DRAWS,
            "completion_cap": "each model's own §12.1 selected cap",
            "decoding": "the registered policy, unchanged",
            "tensor_parallel_size": 1,
            "models": "all four registered replications",
        },
        "success_criteria": {
            "Q1": ("at least three candidate families carrying a rung that "
                   "clears every §13.2 condition at the same severity, on all "
                   "four models; fewer than three on any model is the "
                   "Amendment B §8 discard condition for that model"),
            "Q2": ("B solo compliance inside the registered [0.60, 0.95] band "
                   "at some m <= 12 under the floored stem, on all four "
                   "models, with the selected rung more than one clustered "
                   "standard error inside the band"),
            "Q3": ("B solo vacuity at m* at most 0.10, and both graded "
                   "distributions inside [0.01, 0.99]"),
            "fixed_before": "the first generation of this screen",
            "not_permitted": ("widening the caliper, lowering the vacuity "
                              "maximum, extending a ladder, or dropping a "
                              "model to make a criterion pass"),
        },
        "registered_values_untouched": {
            "reference_caliper": C.REFERENCE_CALIPER,
            "reference_newcombe_region": C.REFERENCE_NEWCOMBE_REGION,
            "reference_prescreen_caliper": C.REFERENCE_PRESCREEN_CALIPER,
            "reference_vacuity_max": C.REFERENCE_VACUITY_MAX,
            "regime_vacuity_max": C.REGIME_VACUITY_MAX,
            "non_vacuity_min_words": C.NON_VACUITY_MIN_WORDS,
            "target_band": list(C.TARGET_BAND), "target_aim": C.TARGET_AIM,
            "focal_band": list(C.FOCAL_BAND), "focal_aim": C.FOCAL_AIM,
            "n_final_references": C.N_FINAL_REFERENCES,
            "m_cal": C.M_CAL,
            "target_grid": list(TARGET_GRID), "focal_grid": list(FOCAL_GRID),
            "reference_ladders": {k: list(v)
                                  for k, v in REFERENCE_LADDERS.items()},
            "note": ("listed so a later diff proves the screen changed none of "
                     "them"),
        },
        "verifier_source_hash": verifier_source_hash(),
        "fixture_verdict_table": suite.fixture_verdict_table(),
    }


def freeze(repo_root: Path | None = None) -> dict[str, Any]:
    payload = build(repo_root)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["screen_protocol_hash"] = hashlib.sha256(
        blob.encode("utf-8")).hexdigest()
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    FROZEN.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return payload


def load() -> dict[str, Any]:
    if not FROZEN.exists():
        raise FileNotFoundError(
            f"{FROZEN} is missing; freeze the screen protocol before "
            f"generating")
    return json.loads(FROZEN.read_text())


if __name__ == "__main__":
    print(freeze()["screen_protocol_hash"])
