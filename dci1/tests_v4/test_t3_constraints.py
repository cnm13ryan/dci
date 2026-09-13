"""T3. Constraints, graded scores, predicates, witnesses.

Every ladder value; the graded-score functions at every severity; the
non-vacuity predicates including the empty and short-answer cases; S1, S2 and
S3 against hand-derived expectations; witnesses and bidirectional
non-entailment for all ten pairs; four wordings each; the wording-length
caliper measured against A and its severity-invariance.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import InstrumentError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol import wordings as W
from dci1v4.verifiers import target, witnesses
from dci1v4.verifiers.compliance import NON_VACUITY_MIN_WORDS, score_constraint
from dci1v4.verifiers.constraints import (
    FOCAL_GRID,
    REFERENCE_LADDERS,
    Constraint,
    TARGET_GRID,
    registered_severities,
)


def test_every_registered_ladder_value_is_constructible():
    total = 0
    for family, ladder in REFERENCE_LADDERS.items():
        assert list(ladder) == list(range(0, ladder[-1] + 1))
        for q in ladder:
            assert Constraint(family, q).severity == q
            total += 1
        with pytest.raises(InstrumentError):
            Constraint(family, ladder[-1] + 1)
    assert total == C.N_LADDER_SEVERITIES == 94
    assert tuple(TARGET_GRID) == tuple(range(1, 9))
    assert tuple(FOCAL_GRID) == (7, 8, 9, 10)
    with pytest.raises(InstrumentError):
        registered_severities("RF9")


@pytest.mark.parametrize("n", TARGET_GRID)
def test_graded_score_of_the_exact_count_at_every_severity(n):
    """§7.4: max(0, 1 - |s0 - n| / n), hand-derived."""
    carrier = "however "
    for realised in range(0, 12):
        text = carrier * realised
        score = score_constraint(Constraint("A", n), text, truncated=False)
        assert score.statistic == realised
        expected = max(0.0, 1.0 - abs(realised - n) / n)
        assert score.graded == pytest.approx(expected)
        assert score.passed is (realised == n)


@pytest.mark.parametrize("m", FOCAL_GRID)
def test_graded_score_of_the_word_length_rule_at_every_severity(m):
    """§7.4: 1 - (words longer than m) / (total words); 0 for an empty answer."""
    assert score_constraint(Constraint("B", m), "", truncated=False).graded \
        == 0.0
    text = "a bb ccc extraordinarily supercalifragilisticexpialidocious"
    score = score_constraint(Constraint("B", m), text, truncated=False)
    words = text.split()
    over = sum(1 for w in words if len(w) > m)
    assert score.graded == pytest.approx(1.0 - over / len(words))
    assert score.passed is (over == 0)


@pytest.mark.parametrize("family", sorted(REFERENCE_LADDERS))
def test_graded_score_of_every_family_at_every_severity(family):
    """§7.4: min(1, q / max(q, count)) for q > 0; 1[count = 0] for q = 0."""
    from dci1v4.verifiers.statistics import FAMILY_STATISTICS

    texts = ["", "bold bold bold going going o o coffee, Q cat cat grey grey",
             "the river runs west then it drifts to the north."]
    for text in texts:
        count = FAMILY_STATISTICS[family](text)
        for q in REFERENCE_LADDERS[family]:
            score = score_constraint(Constraint(family, q), text,
                                     truncated=False)
            assert score.statistic == count
            expected = (1.0 if count == 0 else 0.0) if q == 0 else \
                min(1.0, q / max(q, count))
            assert score.graded == pytest.approx(expected), (family, q, text)
            assert score.passed is (count <= q)


def test_non_vacuity_predicates_including_empty_and_short_answers():
    """§9.3, per constraint form."""
    long_answer = " ".join(["word"] * NON_VACUITY_MIN_WORDS)
    short_answer = " ".join(["word"] * (NON_VACUITY_MIN_WORDS - 1))

    a = score_constraint(Constraint("A", 3), long_answer, truncated=False)
    assert a.non_vacuous is True            # A needs only non-empty, untruncated
    assert score_constraint(Constraint("A", 3), short_answer,
                            truncated=False).non_vacuous is True
    assert score_constraint(Constraint("A", 3), "", truncated=False)\
        .non_vacuous is False
    assert score_constraint(Constraint("A", 3), long_answer, truncated=True)\
        .non_vacuous is False

    for kind, severity in (("B", 8), ("RF1", 3), ("RF7", 10)):
        assert score_constraint(Constraint(kind, severity), long_answer,
                                truncated=False).non_vacuous is True
        assert score_constraint(Constraint(kind, severity), short_answer,
                                truncated=False).non_vacuous is False
        assert score_constraint(Constraint(kind, severity), "",
                                truncated=False).non_vacuous is False


def test_a_vacuous_pass_is_still_a_pass():
    """§9.3: vacuous passes are counted as passes in the primary estimand."""
    score = score_constraint(Constraint("B", 8), "Yes.", truncated=False)
    assert score.passed is True
    assert score.non_vacuous is False
    assert score.vacuous_pass is True


def test_s1_s2_s3_against_hand_derived_expectations():
    """§9.2's three registered alternatives."""
    assert target.s0_count("However however HOWEVER") == 3
    assert target.s1_count("However however HOWEVER") == 1
    assert target.s2_count("Howeverhowever") == 2
    assert target.s0_count("Howeverhowever") == 0

    preamble = ("Here is my answer:\n"
                "Use the word however exactly 2 times.\n"
                "however and however")
    wording = ("Use the word however exactly 2 times.",)
    assert target.s0_count(preamble) == 3
    assert target.s3_count(preamble, wording) == 2


def test_all_ten_pair_types_carry_witnesses_and_both_non_entailments():
    report = witnesses.verify_all_witnesses()
    assert report["witnesses_verified"] is True
    assert report["pairs"] == 4910
    # 10 constraint kinds -> 45 distinct kind pairs, a superset of the ten
    # unordered slot pairs the confirmatory design runs.
    assert report["kind_pairs"] == 45


def test_witness_tokens_move_exactly_one_statistic():
    witnesses.assert_token_orthogonality()


def test_four_distinct_wordings_per_constraint():
    for n in TARGET_GRID:
        assert len(set(W.target_wordings(n))) == W.N_WORDINGS
    for m in FOCAL_GRID:
        assert len(set(W.focal_wordings(m))) == W.N_WORDINGS
    for family, ladder in REFERENCE_LADDERS.items():
        for q in ladder:
            assert len(set(W.family_wordings(family, q))) == W.N_WORDINGS


def test_the_length_caliper_is_measured_against_A_and_is_feasible():
    feasible = W.assert_caliper_feasible()
    assert set(feasible) == set(REFERENCE_LADDERS)
    for family, ladder in REFERENCE_LADDERS.items():
        assert len(feasible[family]) == len(ladder), family


def test_the_caliper_is_severity_invariant_because_numerals_are_not_words():
    counts = W.assert_severity_invariance()
    assert counts["A:0"] == 6
    for family in REFERENCE_LADDERS:
        first = W.length_caliper_ok(family, REFERENCE_LADDERS[family][0], 3)
        last = W.length_caliper_ok(family, REFERENCE_LADDERS[family][-1], 3)
        assert first == last, family


def test_the_caliper_would_refuse_an_over_long_wording(monkeypatch):
    long_wording = ("At most {q} words in the answer may begin with the "
                    "letter b and nothing else may.")
    monkeypatch.setitem(W._FAMILY_TEMPLATES, "RF1",
                        (long_wording,) + W._FAMILY_TEMPLATES["RF1"][1:])
    assert W.length_caliper_ok("RF1", 3, 3) is False
    with pytest.raises(ProtocolError):
        W.assert_caliper_feasible()


def test_every_authored_family_wording_states_its_registered_rule():
    W.assert_rule_vocabulary()
    assert set(W.FAMILY_RULE_STATEMENTS) == set(REFERENCE_LADDERS)
