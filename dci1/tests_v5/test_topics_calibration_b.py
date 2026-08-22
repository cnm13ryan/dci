"""§6.2's bank, §13.7's two splits, and the 96 questions that do not exist."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C
from dci1v5.topics import bank as B


def _fixture_questions(n: int = C.N_CALIBRATION_B, *, area_size: int = 8
                       ) -> list[dict]:
    out = []
    for area in C.SUBJECT_AREAS:
        for index in range(area_size):
            slug = area.replace(" ", "-")
            out.append({
                "topic_id": f"fixture-calb-{slug}-{index:02d}",
                "area": area, "set": C.CALIBRATION_B,
                "question": f"FIXTURE {slug} {index:02d}: plumbing, not a "
                            "research question",
                "authoring_rules_verified": {r: True
                                             for r in C.AUTHORING_RULES},
            })
    return out[:n]


def test_the_bank_loads_with_calibration_b_absent_and_says_so():
    loaded = B.load_bank()
    assert loaded.calibration_b_status == "NOT_AUTHORED"
    assert not loaded.complete
    assert len(loaded.topics(C.CALIBRATION_A)) == C.N_CALIBRATION_A
    assert loaded.topics(C.CALIBRATION_B) == ()
    assert loaded.hashes[C.CALIBRATION_B] is None


def test_the_v4_solo_split_is_calibration_a_under_its_new_name():
    assert B.V4_SET_NAMES["solo"] == C.CALIBRATION_A
    loaded = B.load_bank()
    assert all(t["set"] == C.CALIBRATION_A
               for t in loaded.topics(C.CALIBRATION_A))


def test_calibration_b_refuses_while_d3_is_open():
    from dci1v5.protocol import decisions

    with pytest.raises(decisions.DecisionOpenError):
        B.calibration_b_questions(_fixture_questions())


def test_a_closed_d3_still_requires_the_work(restore_decisions):
    restore_decisions.close("D3", "author_before_adoption", evidence="t",
                            decided_by="t", decided_on="t")
    with pytest.raises(ProtocolError, match="no bank was supplied"):
        B.calibration_b_questions(None)
    with pytest.raises(ProtocolError, match="96 questions"):
        B.calibration_b_questions(_fixture_questions(90))
    assert len(B.calibration_b_questions(_fixture_questions())) == 96


def test_author_after_adoption_returns_no_questions(restore_decisions):
    restore_decisions.close("D3", "author_after_adoption", evidence="t",
                            decided_by="t", decided_on="t")
    with pytest.raises(ProtocolError, match="author after adoption"):
        B.calibration_b_questions(_fixture_questions())


def test_the_two_calibration_splits_must_be_disjoint(restore_decisions):
    """§13.7's precondition, and the failure that is silent everywhere else."""
    restore_decisions.close("D3", "author_before_adoption", evidence="t",
                            decided_by="t", decided_on="t")
    loaded = B.load_bank(calibration_b=_fixture_questions())
    report = B.assert_calibration_sets_disjoint(
        {k: v for k, v in loaded.sets.items() if v})
    assert report["disjoint"] and report["n_a"] == report["n_b"] == 96

    leaked = _fixture_questions()
    borrowed = loaded.topics(C.CALIBRATION_A)[0]
    leaked[0] = {**leaked[0], "question": borrowed["question"]}
    with pytest.raises(ProtocolError, match="repeat"):
        B.load_bank(calibration_b=leaked)


def test_a_duplicated_topic_id_is_refused(restore_decisions):
    restore_decisions.close("D3", "author_before_adoption", evidence="t",
                            decided_by="t", decided_on="t")
    questions = _fixture_questions()
    borrowed = B.load_bank().topics(C.CALIBRATION_A)[0]
    questions[0] = {**questions[0], "topic_id": borrowed["topic_id"]}
    with pytest.raises(ProtocolError):
        B.load_bank(calibration_b=questions)


def test_per_area_allocation_is_enforced(restore_decisions):
    restore_decisions.close("D3", "author_before_adoption", evidence="t",
                            decided_by="t", decided_on="t")
    questions = _fixture_questions()
    questions[0] = {**questions[0], "area": questions[-1]["area"]}
    with pytest.raises(ProtocolError, match="per area"):
        B.calibration_b_questions(questions)


def test_split_identity_is_over_the_text_not_only_the_ids():
    loaded = B.load_bank()
    first = loaded.split_identity["split_hash"]
    altered = [dict(t) for t in loaded.topics("prescreen")]
    altered[0]["question"] = altered[0]["question"] + " (edited)"
    assert B.set_hash(altered) != loaded.hashes["prescreen"]
    assert first == B.load_bank().split_identity["split_hash"]


def test_rows_are_checked_against_the_bank_not_against_their_own_label():
    loaded = B.load_bank()
    a_topic = loaded.topics(C.CALIBRATION_A)[0]["topic_id"]
    prescreen = loaded.topics("prescreen")[0]["topic_id"]
    ok = B.assert_rows_single_split([{"topic_id": a_topic}], loaded,
                                    split=C.CALIBRATION_A, where="test")
    assert ok["n_rows"] == 1
    with pytest.raises(ProtocolError, match="belong to another set"):
        B.assert_rows_single_split([{"topic_id": prescreen}], loaded,
                                   split=C.CALIBRATION_A, where="test")


def test_a_pooled_table_may_not_be_presented_as_one_split(restore_decisions):
    restore_decisions.close("D3", "author_before_adoption", evidence="t",
                            decided_by="t", decided_on="t")
    loaded = B.load_bank(calibration_b=_fixture_questions())
    pooled = [{"topic_id": loaded.topics(C.CALIBRATION_A)[0]["topic_id"]},
              {"topic_id": loaded.topics(C.CALIBRATION_B)[0]["topic_id"]}]
    with pytest.raises(ProtocolError, match="pooled"):
        B.assert_not_pooled_as_split(pooled, loaded, where="test")


def test_reserved_topics_may_not_be_spent_before_the_freeze():
    loaded = B.load_bank()
    reserved = loaded.topics("confirmatory")[0]["topic_id"]
    with pytest.raises(ProtocolError, match="reserved topic"):
        B.assert_no_reserved_topic_spent([reserved], loaded.sets,
                                         stage="REGIME_SCREEN")
    B.assert_no_reserved_topic_spent(
        [loaded.topics("prescreen")[0]["topic_id"]], loaded.sets,
        stage="REGIME_SCREEN")


def test_a_calibration_binding_refuses_an_empty_split():
    loaded = B.load_bank()
    with pytest.raises(ProtocolError, match="NOT_AUTHORED"):
        B.calibration_binding(loaded, split=C.CALIBRATION_B)


def test_draw_allocation_is_equal_and_keeps_every_draw():
    loaded = B.load_bank()
    plan = B.draw_allocation(loaded.topics(C.CALIBRATION_A), draws=4,
                             stage="calibration")
    assert plan["n_topics"] == 96 and plan["n_rows_per_cell"] == 384
    assert "none selected" in plan["allocation"]


def test_provenance_declares_that_calibration_a_is_not_naive():
    record = B.provenance(B.load_bank())
    assert record[C.CALIBRATION_A]["naive"] is False
    assert record[C.CALIBRATION_B]["decision"] == "§34 D3"
