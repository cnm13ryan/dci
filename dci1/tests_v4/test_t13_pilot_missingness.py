"""T13. Pilot, missingness, contamination, provenance of thresholds.

Gate 0's eight acceptance conditions including the redacted structural result,
the byte-mutation refusal and the durable restore; retry and fail-closed
behaviour on a short cell; the 0.01 missingness report and the 0.05 duplicate
qualification failure; the canary string and the release manifest counts; and
an assertion that every registered threshold, region, precondition and caliper
carries its provenance field.
"""
from __future__ import annotations

import json

import pytest

from dci1v4 import SYNTHETIC_STUDY_ID
from dci1v4.analysis import diagnostics
from dci1v4.design.cells import design_cells
from dci1v4.errors import IntegrityError, TerminalStatus
from dci1v4.generation.backend import build_plan
from dci1v4.generation.cache import cache_rows, fill_cache
from dci1v4.generation.synthetic import synthetic_generate
from dci1v4.models.registry import get_model
from dci1v4.protocol import constants as C
from dci1v4.stages import pilot
from dci1v4.stages.freeze import assert_threshold_provenance
from dci1v4.topics.split import pilot_blocks, split_topics

SPEC = get_model("gemma-3n-e2b-it")


def test_the_pilot_is_twelve_topics_and_1200_cached_draws():
    blocks = pilot_blocks(split_topics())
    cells = design_cells("pilot", blocks, pilot.pilot_slot_map(),
                         draws=C.PILOT_DRAWS)
    assert len(blocks) == 12
    assert len(cells) == 12 * C.N_CELLS_FULL == 300
    assert sum(c.draws for c in cells) == 1200


def test_the_pilot_fixtures_cannot_become_calibration_evidence():
    slot_map = pilot.pilot_slot_map()
    assert slot_map["A"] == ("A", 3) and slot_map["B"] == ("B", 8)
    payload = pilot.pilot_payload(
        draws=1200, cells=300, structural_result={"compliance": 0.5},
        acceptance_report={"passed": True}, pilot_dir=".")
    assert "cannot become calibration evidence" in payload["fixtures_note"]
    assert payload["exposes_no_rate"] is True


def test_the_pilot_result_is_persisted_fully_redacted():
    structural = {"D(B<-A)": 0.42,
                  "cells": {"pair:A+B:c1_first": {"compliance": 0.7, "n": 12}},
                  "families": [{"member": "Lambda", "estimate": -0.1}],
                  "status": "COMPLETE", "clean": True}
    payload = pilot.pilot_payload(draws=1200, cells=300,
                                  structural_result=structural,
                                  acceptance_report={"passed": True},
                                  pilot_dir=".")
    redacted = payload["redacted_result"]
    pilot.assert_fully_redacted(redacted)
    assert redacted["D(B<-A)"] == pilot.REDACTED
    assert redacted["status"] == "COMPLETE"        # structure survives
    assert redacted["clean"] is True               # booleans are not numbers
    with pytest.raises(AssertionError, match="exposes a numeric value"):
        pilot.assert_fully_redacted({"leak": 0.42})


def test_all_eight_acceptance_conditions_are_named_and_checked():
    good = dict(committed_once=True, cells_complete=True,
                technical_failures=0, codebook_valid=True,
                structural_result={"x": 1}, byte_mutation_refused=True,
                durable_restore_matches=True, pilot_mask_isolated=True)
    report = pilot.acceptance(**good)
    assert len(report["conditions"]) == 8
    assert report["passed"] is True
    for field in good:
        broken = dict(good)
        broken[field] = 1 if field == "technical_failures" else False
        with pytest.raises(TerminalStatus) as excinfo:
            pilot.acceptance(**broken)
        assert excinfo.value.status == "APPARATUS_FAILURE"
        assert "requires qualification and the pilot to run again" in \
            excinfo.value.record["strongest_permissible_statement"]


def test_a_short_cell_fails_the_run_closed_and_imputes_nothing(tmp_path):
    blocks = pilot_blocks(split_topics())[:2]
    cells = design_cells("pilot", blocks, pilot.pilot_slot_map(), draws=4)
    plan = build_plan(SPEC, stage="pilot", max_new_tokens=768)

    def refuses_one(run_dir, plan_, design_rows):
        outcome = synthetic_generate(run_dir, plan_, design_rows)
        outcome["rows"] = [r for r in outcome["rows"]
                           if not r["row_id"].endswith(":3")]
        return outcome

    with pytest.raises(IntegrityError, match="fails closed"):
        fill_cache(tmp_path / "pilot", cells, spec=SPEC, stage="pilot",
                   slot_map=pilot.pilot_slot_map(),
                   study_id=SYNTHETIC_STUDY_ID, plan=plan,
                   generate_fn=refuses_one,
                   environment={"python_executable": "p",
                                "dependency_digest": "d"},
                   max_repair_rounds=1)


def test_a_retry_regenerates_under_the_registered_seed(tmp_path):
    blocks = pilot_blocks(split_topics())[:1]
    cells = design_cells("pilot", blocks, pilot.pilot_slot_map(), draws=4)
    plan = build_plan(SPEC, stage="pilot", max_new_tokens=768)
    state = {"failed": False}

    def fails_once(run_dir, plan_, design_rows):
        outcome = synthetic_generate(run_dir, plan_, design_rows)
        if not state["failed"]:
            state["failed"] = True
            outcome["rows"] = outcome["rows"][:-3]
        return outcome

    report = fill_cache(tmp_path / "pilot", cells, spec=SPEC, stage="pilot",
                        slot_map=pilot.pilot_slot_map(),
                        study_id=SYNTHETIC_STUDY_ID, plan=plan,
                        generate_fn=fails_once,
                        environment={"python_executable": "p",
                                     "dependency_digest": "d"})
    assert report["status"] == "COMPLETE"
    assert report["draws"] == len(cells) * 4


def test_the_missingness_report_and_its_threshold():
    report = diagnostics.missingness_report(
        expected={"solo:A": 100, "pair:A+B:c1_first": 100},
        observed={"solo:A": 100, "pair:A+B:c1_first": 97})
    assert report["per_cell_type"]["solo:A"]["report_beside_primary"] is False
    composed = report["per_cell_type"]["pair:A+B:c1_first"]
    assert composed["missing_rate"] == pytest.approx(0.03)
    assert composed["report_beside_primary"] is True
    assert report["arm_differential"] == pytest.approx(0.03)
    assert C.MISSINGNESS_REPORT_THRESHOLD == 0.01


def test_the_duplicate_rate_threshold_is_a_qualification_failure():
    from dci1v4.generation.cache import duplicate_report

    rows = [{"cell_id": "c", "response_content_hash": "h"} for _ in range(4)]
    assert duplicate_report(rows)["overall_rate"] > \
        C.DUPLICATE_QUALIFICATION_MAX
    assert C.DUPLICATE_QUALIFICATION_MAX == 0.05


def test_the_release_manifest_carries_a_canary_and_the_withheld_count():
    from dci1v4.stages.release import build_release

    release = build_release()
    assert release["topics_released"] == 528
    assert release["topics_withheld"] == 96
    assert release["topics_authored"] == 624
    assert release["canary"]
    assert release["canary"] in json.dumps(release["dataset"])
    assert "96 of the 624 are withheld" in release["manifest_note"]


def test_the_v3_sequestered_ninety_six_remain_withheld():
    from dci1v4.stages.release import build_release

    release = build_release()
    assert release["v3_sequestered"] == "withheld and untouched"


def test_every_threshold_region_precondition_and_caliper_has_provenance():
    table = assert_threshold_provenance()
    for name, entry in table.items():
        assert entry["provenance"], name
        assert entry["value"] is not None, name
    assert len(table) >= 8
