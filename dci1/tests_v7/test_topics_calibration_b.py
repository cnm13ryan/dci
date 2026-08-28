"""§6.2's bank, §13.7's two splits, and the 96 questions now authored."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C
from dci1v7.topics import bank as B
from dci1v7.topics import calibration_b


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


def test_the_bank_is_complete_now_that_calibration_b_is_authored():
    """§34 D3 closed at ``author_before_adoption``, and the bank exists."""
    loaded = B.load_bank()
    assert loaded.calibration_b_status == "AUTHORED"
    assert loaded.complete
    assert len(loaded.topics(C.CALIBRATION_A)) == C.N_CALIBRATION_A
    assert len(loaded.topics(C.CALIBRATION_B)) == C.N_CALIBRATION_B
    assert loaded.hashes[C.CALIBRATION_B]


def test_the_status_distinguishes_absent_from_undecided(restore_decisions):
    """Three states, because two of them are different kinds of not-ready."""
    assert B.calibration_b_status() == "AUTHORED"
    restore_decisions.override_for_testing("D3", "author_after_adoption")
    assert B.calibration_b_status() == "AUTHORED_PENDING_D3"
    assert B.load_bank().topics(C.CALIBRATION_B) == ()


def test_the_v4_solo_split_is_calibration_a_under_its_new_name():
    assert B.V4_SET_NAMES["solo"] == C.CALIBRATION_A
    loaded = B.load_bank()
    assert all(t["set"] == C.CALIBRATION_A
               for t in loaded.topics(C.CALIBRATION_A))


def test_a_closed_d3_still_requires_the_work(restore_decisions):
    with pytest.raises(ProtocolError, match="no bank was supplied"):
        B.calibration_b_questions(None)
    with pytest.raises(ProtocolError, match="96 questions"):
        B.calibration_b_questions(_fixture_questions(90))
    assert len(B.calibration_b_questions(_fixture_questions())) == 96


def test_author_after_adoption_returns_no_questions(restore_decisions):
    restore_decisions.override_for_testing("D3", "author_after_adoption")
    with pytest.raises(ProtocolError, match="author after adoption"):
        B.calibration_b_questions(_fixture_questions())


def test_the_two_calibration_splits_must_be_disjoint():
    """§13.7's precondition, and the failure that is silent everywhere else."""
    loaded = B.load_bank(calibration_b=_fixture_questions())
    report = B.assert_calibration_sets_disjoint(
        {k: v for k, v in loaded.sets.items() if v})
    assert report["disjoint"] and report["n_a"] == report["n_b"] == 96

    leaked = _fixture_questions()
    borrowed = loaded.topics(C.CALIBRATION_A)[0]
    leaked[0] = {**leaked[0], "question": borrowed["question"]}
    with pytest.raises(ProtocolError, match="repeat"):
        B.load_bank(calibration_b=leaked)


def test_a_duplicated_topic_id_is_refused():
    questions = _fixture_questions()
    borrowed = B.load_bank().topics(C.CALIBRATION_A)[0]
    questions[0] = {**questions[0], "topic_id": borrowed["topic_id"]}
    with pytest.raises(ProtocolError):
        B.load_bank(calibration_b=questions)


def test_per_area_allocation_is_enforced():
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


def test_a_pooled_table_may_not_be_presented_as_one_split():
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


def test_a_calibration_binding_refuses_an_empty_split(restore_decisions):
    restore_decisions.override_for_testing("D3", "author_after_adoption")
    loaded = B.load_bank()
    with pytest.raises(ProtocolError, match="AUTHORED_PENDING_D3"):
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


# ------------------------------------------------ the authored bank itself

def test_the_authored_bank_is_ninety_six_stratified_questions():
    rows = calibration_b.load_calibration_b()
    assert len(rows) == C.N_CALIBRATION_B
    summary = calibration_b.allocation_summary()
    assert set(summary["per_area"].values()) == {C.CALIBRATION_B_PER_AREA}
    assert len(set(r["topic_id"] for r in rows)) == C.N_CALIBRATION_B
    for row in rows:
        B.assert_topic_schema(row, where="authored")
        assert row["set"] == C.CALIBRATION_B


def test_the_authored_bank_is_disjoint_from_every_other_set():
    """Not only from Calibration-A: a reserved topic's text is spent too."""
    loaded = B.load_bank()
    report = B.assert_calibration_sets_disjoint(
        {k: v for k, v in loaded.sets.items() if v})
    assert report["disjoint"] and report["n_a"] == report["n_b"] == 96
    B.assert_sets_disjoint({k: v for k, v in loaded.sets.items() if v})


def test_the_authored_bank_carries_no_form_requirement_in_its_text():
    """§6.2 rule 4, the one rule a machine can check.

    It is checked over the ``question`` field. Reading ``text`` --- which is
    what this did --- scanned the empty string for every topic in the bank,
    so the rule had never rejected anything.
    """
    from dci1v7.topics import assert_authoring_rules

    report = assert_authoring_rules(calibration_b.load_calibration_b())
    assert report["questions"] == 96
    with pytest.raises(ProtocolError, match="form_requirement_tokens"):
        assert_authoring_rules([
            {"topic_id": "x", "question": "How many letters does it use?",
             "authoring_rules_verified": {r: True for r in
                                          C.AUTHORING_RULES}}])


def test_every_authored_question_records_all_four_verifications():
    rows = calibration_b.load_calibration_b()
    assert all(set(r["authoring_rules_verified"]) == set(C.AUTHORING_RULES)
               for r in rows)
    from dci1v7.topics import assert_authoring_rules

    with pytest.raises(ProtocolError, match="unverified_rules"):
        assert_authoring_rules(calibration_b.load_calibration_b(
            verified=False))


def test_the_bank_hash_is_stable_and_over_the_text():
    first = calibration_b.calibration_b_bank_hash()
    assert first == calibration_b.calibration_b_bank_hash()
    rows = calibration_b.load_calibration_b(verified=False)
    edited = [dict(r) for r in rows]
    edited[0]["question"] += " (edited)"
    assert B.set_hash(edited) != first


def test_the_provenance_states_when_it_was_authored_and_against_what():
    record = calibration_b.provenance_record()
    assert record["decision"] == "§34 D3"
    assert record["bank_hash"] == calibration_b.calibration_b_bank_hash()
    assert record["authored_on"] == calibration_b.AUTHORED_ON
    assert any("Calibration-A measurement" in s
               for s in record["authored_before"])
    assert any("compliance measurement" in s
               for s in record["what_was_not_used"])
