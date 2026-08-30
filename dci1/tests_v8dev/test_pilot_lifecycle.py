"""The whole pilot lifecycle, executed with no model (marked ``slow``)."""
from __future__ import annotations

import json

import pytest

from dci1v4.errors import IntegrityError
from dci1v8dev.run import STUDY_ID
from dci1v8dev.run import stages as S
from dci1v8dev.run import contracts, transitions
from dci1v8dev.verifiers import verifier_source_hash
from dci1v8dev.wordings import v8_wording_source_hash

from tests_v8dev import pilot_harness as H


@pytest.fixture(scope="module")
def walked(tmp_path_factory):
    return H.walk(tmp_path_factory.mktemp("v8-pilot-synthetic"))


@pytest.mark.slow
def test_every_stage_produced_a_signed_record(walked):
    payloads = walked["payloads"]
    assert list(payloads) == list(S.STAGE_SEQUENCE)
    tree = walked["tree"]
    for stage in S.STAGE_SEQUENCE:
        record = transitions.read_stage_record(tree, stage)
        assert record["outcome"] == "PASS"
        assert record["artifact_type"] == S.STAGE_ARTIFACT_TYPE[stage]
        assert record["study_id"] == tree.context.study_id
        assert record["verifier_hash"] == verifier_source_hash()
        assert record["wording_hash"] == v8_wording_source_hash()


@pytest.mark.slow
def test_the_producer_consumer_contract_holds_against_real_payloads(walked):
    result = contracts.audit_contracts(walked["payloads"])
    assert result["clean"], result["defects"]
    assert result["n_checked_against_payloads"] == result["n_fields"]


@pytest.mark.slow
def test_nothing_it_wrote_can_be_mistaken_for_pilot_or_v7_evidence(walked):
    tree = walked["tree"]
    assert tree.context.study_id == f"{STUDY_ID}-synthetic"
    rows = []
    for stage in S.GENERATION_STAGES:
        for path in tree.backend_runs(stage).rglob("scored.jsonl"):
            rows += [json.loads(line) for line in path.read_text().splitlines()
                     if line.strip()]
    assert rows and all(r["synthetic"] for r in rows)
    assert all(r["study_id"] == tree.context.study_id for r in rows)
    assert all(r["load"] <= 1 for r in rows), "a composed row was generated"
    assert all(r["wording_hash"] == v8_wording_source_hash() for r in rows)
    # a v7 reader refuses every record by study id
    from dci1v7.engine import transitions as v7_transitions
    v7_context = type("C", (), {"study_id": "dci1v7"})()
    with pytest.raises(IntegrityError, match="another revision"):
        v7_transitions.assert_own_study(
            type("T", (), {"context": v7_context, "model_key": "x"})(),
            "any", walked["payloads"][S.STAGE_REGIME])


@pytest.mark.slow
def test_the_v8_frames_reached_the_model(walked):
    tree = walked["tree"]
    seen = 0
    for path in tree.backend_runs(S.STAGE_REGIME).rglob("design.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["cell_id"].startswith("solo:A:") or \
                    row["cell_id"].startswith("solo:MK"):
                assert "the word " in row["user_prompt"].lower(), row["user_prompt"]
                seen += 1
    assert seen > 0


@pytest.mark.slow
def test_chance_is_read_on_the_unconstrained_cell_in_both_tables(walked):
    regime = walked["payloads"][S.STAGE_REGIME]
    gate2 = walked["payloads"][S.STAGE_GATE2]
    assert regime["chance_basis"]["cell"] == "unconstrained"
    assert gate2["chance_basis"]["cell"] == "unconstrained"
    pooled = gate2["calibration_rows"]["pooled"]
    assert pooled, "no calibrated candidate"
    # budget families answer 'at most q commas' by chance; the scripted
    # unconstrained answer carries 2-8 commas, so kappa > 0 there and the
    # column is not the zero column
    budget = [r for r in pooled if r["kind"].startswith("RF")]
    assert budget and any(r["chance_compliance"] > 0 for r in budget)
    for split, rows in gate2["calibration_rows"].items():
        for r in rows:
            assert r["chance_compliance"] < 0.99
    assert gate2["iota_a_basis"].startswith("§13.2")


@pytest.mark.slow
def test_the_second_pass_used_calibration_a_topics_disjointly(walked):
    second = walked["payloads"][S.STAGE_SECOND_PASS]
    bank = walked["bank"]
    a_ids = {t["topic_id"] for t in bank.topics("calibration_a")}
    seen: set[str] = set()
    for batch in second["batches"]:
        ids = set(batch["topic_ids"])
        assert ids <= a_ids
        assert not ids & seen
        seen |= ids
    assert second["n_batches"] <= 3
    assert second["forwarded_set"]


@pytest.mark.slow
def test_the_report_evaluates_the_four_criteria(walked):
    report = walked["payloads"][S.STAGE_REPORT]
    assert list(report["criteria"]) == list(S.PILOT_CRITERIA)
    for name, verdict in report["criteria"].items():
        assert "passed" in verdict, name
    assert report["criteria"]["FRAME_RELIABILITY"]["passed"] is True
    assert report["criteria"]["CHANCE_BASIS"]["passed"] is True
    assert report["no_composed_cells"] is True
    assert report["generations"]["total"] > 0


@pytest.mark.slow
def test_a_stage_cannot_run_twice(walked):
    from dci1v8dev.run import report as report_stage
    with pytest.raises(IntegrityError, match="write-once"):
        report_stage.run_report(walked["tree"], producing_commit="0" * 40)
