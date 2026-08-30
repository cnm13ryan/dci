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
    assert gate2["supported_frames"], "no supported frame"
    for w in gate2["supported_frames"]:
        block = gate2["by_frame"][str(w)]
        pooled = block["calibration_rows"]["pooled"]
        assert pooled, f"frame {w}: no calibrated candidate"
        # budget families answer 'at most q commas' by chance; the scripted
        # unconstrained answer carries 2-8 commas, so kappa > 0 there and
        # the column is not the zero column
        budget = [r for r in pooled if r["kind"].startswith("RF")]
        assert budget and any(r["chance_compliance"] > 0 for r in budget)
        for split, rows in block["calibration_rows"].items():
            for r in rows:
                assert r["chance_compliance"] < 0.99
        assert block["iota_a_basis"].startswith("§13.2")
        assert block["chance_basis"]["cell"] == "unconstrained"


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
    assert report["criteria"]["CHANCE_BASIS"]["passed"] is True
    wording = report["criteria"]["WORDING_DIAGNOSTIC"]
    assert wording["passed"] is None
    assert wording["judgment"] == "DESCRIPTIVE_ONLY"
    assert report["wording_judgment"]["status"] == "DECIDED"
    assert report["wording_judgment"]["policy"] == S.WORDING_POLICY
    assert "WORDING_DIAGNOSTIC" in report["open_judgments"]
    assert report["decided_criteria"] == list(S.DECIDED_CRITERIA)
    for name in S.DECIDED_CRITERIA:
        verdict = report["criteria"][name]
        assert set(verdict["by_frame"]) == {str(w) for w in report["supported_frames"]}
        assert verdict["aggregation"] == S.REPORT_AGGREGATION
    assert report["frame_states"] and report["estimands"]["generated_here"] is False
    assert wording["ladders_per_frame"]["calibration"].keys() >= {"0", "1", "2", "3"}
    assert wording["stability_across_fresh_topics"]["calibration_splits"]["n_compared"] > 0
    assert wording["wording_dependence"]["calibration"]["n_rungs_compared"] > 0
    assert report["no_composed_cells"] is True
    assert report["generations"]["total"] > 0


@pytest.mark.slow
def test_every_generated_row_reaches_scoring_and_carries_its_provenance(walked):
    """Every design row is generated and scored, compliant or not; every
    scored row names its frame, family/q, topic, split, run and outcome."""
    import json
    from dci1v8dev.run.execute import row_accounting
    tree = walked["tree"]
    seen_runs = 0
    for stage in S.GENERATION_STAGES:
        for run in sorted(tree.backend_runs(stage).iterdir()):
            acc = row_accounting(run)
            assert acc["every_row_scored"], (stage, run.name, acc)
            assert acc["n_present_non_compliant"] > 0 or run.name.startswith("cap"), run
            seen_runs += 1
            for line in (run / "scored.jsonl").read_text().splitlines():
                row = json.loads(line)
                assert row["run"] == run.name
                assert row["topic_id"] and row["topic_split"]
                if row["load"] == 1:
                    assert row["frame"] in (0, 1, 2, 3)
                    present = [s for s in row["scores"] if s["present"]]
                    assert len(present) == 1
                    assert "statistic" in present[0] and "passed" in present[0]
                else:
                    assert row["frame"] is None
    assert seen_runs >= 6
    # the records carry the same accounting
    for stage in (S.STAGE_REGIME, S.STAGE_SECOND_PASS, S.STAGE_GATE2):
        acc = walked["payloads"][stage]["row_accounting"]
        assert acc and all(v["every_row_scored"] for v in acc.values())


@pytest.mark.slow
def test_second_pass_rows_carry_batch_split_topic_and_never_a_prescreen_or_b_topic(walked):
    import json
    tree = walked["tree"]
    bank = walked["bank"]
    second = walked["payloads"][S.STAGE_SECOND_PASS]
    prescreen = {t["topic_id"] for t in bank.topics("prescreen")}
    cal_b = {t["topic_id"] for t in bank.topics("calibration_b")}
    by_batch = {b["run"]: set(b["topic_ids"]) for b in second["batches"]}
    assert second["topic_isolation"]["n_topics_used"] == 24 * second["n_batches"]
    for run in sorted(tree.backend_runs(S.STAGE_SECOND_PASS).iterdir()):
        for line in (run / "scored.jsonl").read_text().splitlines():
            row = json.loads(line)
            assert row["run"] == run.name and row["run"] in by_batch
            assert row["topic_split"] == "calibration_a"
            assert row["topic_id"] in by_batch[row["run"]]
            assert row["topic_id"] not in prescreen and row["topic_id"] not in cal_b


@pytest.mark.slow
def test_gate2_measures_every_frame_of_every_candidate_separately(walked):
    gate2 = walked["payloads"][S.STAGE_GATE2]
    pooled = gate2["wording_by_frame"]["pooled"]
    frames = {}
    for e in pooled:
        frames.setdefault(e["candidate"], set()).add(e["frame"])
    candidates = {f"{r['kind']}:{r['severity']}"
                  for w in gate2["supported_frames"]
                  for r in gate2["by_frame"][str(w)]["calibration_rows"]["pooled"]}
    for label in candidates:
        assert frames[label] == {0, 1, 2, 3}, label
    for e in pooled:
        assert e["n_rows"] == e["k_exact_compliant"] + (e["n_rows"] - e["k_exact_compliant"])
        assert e["chance"] is not None and e["se_iota"] is not None
    comparison = gate2["frame_comparison_pooled"]
    assert all(c["n_frames_measured"] == 4 for l, c in comparison.items()
               if l in candidates)
    assert set(gate2["rungs_by_wording_class"]) == {"CONSISTENT", "UNRESOLVED",
                                                     "WORDING_SENSITIVE"}
    gate3 = walked["payloads"][S.STAGE_GATE3]
    for w in gate3["supported_frames"]:
        assert gate3["by_frame"][str(w)]["wording_sensitive_rungs"]["selection_rule"] is None


@pytest.mark.slow
def test_a_stage_cannot_run_twice(walked):
    from dci1v8dev.run import report as report_stage
    with pytest.raises(IntegrityError, match="write-once"):
        report_stage.run_report(walked["tree"], producing_commit="0" * 40)


@pytest.mark.slow
def test_the_wording_decision_report_builds_on_gate2_and_gate3_only(walked, tmp_path):
    """tools/v8_wording_decision.py answers the researcher's five questions
    from the signed Gate-2/Gate-3 records and the Gate-2 rows, refuses a
    root without Gate 2, reads no composed outcome and chooses no frame."""
    import importlib.util
    import pathlib
    import re

    from dci1v7.protocol import constants as C

    path = pathlib.Path(__file__).resolve().parents[1] / "tools" / "v8_wording_decision.py"
    spec = importlib.util.spec_from_file_location("v8_wording_decision", path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    source = path.read_text()
    assert not re.search(r"Delta_R|delta_diff|composed_contrast|CONFIRMATORY", source)
    assert tool.STAGES_READ == (S.STAGE_GATE2, S.STAGE_GATE3)

    tree = walked["tree"]
    rep = tool.build(tree.context.evidence_root.parent, model_key=tree.model_key,
                     namespace="synthetic", n_cases=2, per_frame=2)
    assert rep["available"] and rep["synthetic"] and not rep["composed_outcomes_read"]
    rungs = rep["item1_rungs"]
    gate2 = walked["payloads"][S.STAGE_GATE2]
    assert {r["candidate"] for r in rungs} == set(gate2["frame_comparison_pooled"])
    for r in rungs:
        assert set(r["frames"]) == {str(w) for w in range(C.N_WORDINGS)}
        assert r["class"] in (None, *tool.W.CLASSES)
        assert set(r["class_by_split"]) == {C.CALIBRATION_A, C.CALIBRATION_B}
    outliers = rep["item2_frame_outliers"]["by_frame"]
    assert set(outliers) == {str(w) for w in range(C.N_WORDINGS)}
    assert abs(sum(o["share_hardest"] for o in outliers.values()) - 1.0) < 1e-9
    assert rep["item3_split_replication"]["gate2_split_stability"]["n_compared"] == \
        gate2["split_stability_by_frame"]["n_compared"]
    exposure = rep["item4_reference_exposure"]
    assert exposure["available"]
    assert set(exposure["sets"]) == {"local_valid_candidates", "spectrum_valid_candidates",
                                     "selected_local_references_core",
                                     "selected_spectrum_points",
                                     "backup_family_rungs_local_valid"}
    gate3 = walked["payloads"][S.STAGE_GATE3]
    assert set(exposure["by_frame"]) == {str(w) for w in gate3["supported_frames"]}
    for w in gate3["supported_frames"]:
        assert exposure["by_frame"][str(w)]["sets"]["selected_local_references_core"]["n"] == \
            len(gate3["by_frame"][str(w)]["core_references"])
    cases = rep["item5_exemplars"]["cases"]
    assert cases
    for case in cases:
        sentences = [f["constraint_sentence"] for f in case["frames"].values()]
        assert len(sentences) == C.N_WORDINGS and len(set(sentences)) == C.N_WORDINGS
        for f in case["frames"].values():
            assert f["full_prompt_example"] and f["constraint_sentence"] in f["full_prompt_example"]
            assert 0 <= f["k_exact_compliant"] <= f["n_rows"]
            assert sum(f["observed_count_distribution"].values()) == f["n_rows"]
            assert all("observed_count" in o and "exact_compliant" in o for o in f["outputs"])
    assert rep["options"]["decision_made_here"] is None
    assert rep["options"]["no_frame_discarded"] is True
    assert tool.render(rep).startswith("# DCI-1 v8 pilot — wording-policy decision report")

    empty = tool.build(tmp_path / "no-gate2", model_key=tree.model_key,
                       namespace="synthetic", n_cases=1, per_frame=1)
    assert empty["available"] is False
    assert empty["must_finish"][-1] == S.STAGE_GATE2
    assert "NOT AVAILABLE" in tool.render(empty)
