"""§8.1 scoring-rule semantics, verifier boundaries, wordings, witnesses."""
import pytest

pytestmark = pytest.mark.cpu

from dci1.constraints.definitions import CANDIDATE_IDS, added_verifier
from dci1.constraints.witnesses import certify_composition
from dci1.constraints.wording_check_responses import WORDING_CHECK_RESPONSES
from dci1.constraints.wordings import all_wordings, wording
from dci1.verifiers import target
from dci1.verifiers.boundary_suite import BOUNDARY_CASES, evaluate_suite
from dci1.verifiers.registry import assert_blindness, verifier_source_hash


def test_boundary_suite_all_forty():
    result = evaluate_suite()
    assert result["cases"] == 40
    assert result["handled_as_specified"] == 40, result["failures"]


def test_s0_semantics():
    assert target.s0_count("However, however; HOWEVER!") == 3
    assert target.s0_count("howeverhowever") == 0
    assert target.s0_count("how-ever") == 0
    assert target.passes(2, 2) and not target.passes(1, 2)
    assert target.graded(0, 2) == 2 and target.graded(3, 2) == 1


def test_s1_is_case_sensitive():
    assert target.s1_count("However however HOWEVER") == 1


def test_s2_counts_substrings():
    assert target.s2_count("howeverhowever plus However.") == 3


def test_s3_preprocessing():
    wordings = ("Use the word however exactly 2 times.",)
    text = ("My answer follows below:\n"
            "Use the word however exactly 2 times.\n"
            "However, this stays. However, so does this.")
    assert target.s3_count(text, wordings) == 2
    # The same text under S0 keeps the restated line (which contains one
    # 'however'), so the counts differ by construction.
    assert target.s0_count(text) == 3


def test_verifier_blindness_and_hash_stability():
    assert_blindness()
    assert verifier_source_hash() == verifier_source_hash()


def test_wordings_four_each_and_equivalent_verdicts():
    for cid in ("A", "B") + CANDIDATE_IDS:
        kwargs = {"n": 2} if cid == "A" else ({"m": 8} if cid == "B" else {})
        texts = all_wordings(cid, **kwargs)
        assert len(texts) == 4 and len(set(texts)) == 4
    # All four wordings of a constraint map to one verifier, hence identical
    # verdicts on the fixed twenty-response check set (D21).
    for cid in CANDIDATE_IDS:
        verdicts = []
        for index in range(4):
            _ = wording(cid, index)
            verifier = added_verifier(cid)
            verdicts.append([verifier(r) for r in WORDING_CHECK_RESPONSES])
        assert all(v == verdicts[0] for v in verdicts)


def test_wording_zero_is_canonical():
    assert wording("A", 0, n=2) == "Use the word however exactly 2 times."
    assert wording("A", 0, n=1) == "Use the word however exactly 1 time."
    assert wording("B", 0, m=8) == \
        "Every word in the answer must have at most 8 letters."
    assert wording("C3", 0) == \
        "No word in the answer may begin with the letter b."


def test_all_witness_certifications():
    for n in (1, 2, 3):
        for cid in CANDIDATE_IDS:
            certificate = certify_composition(cid, n)
            assert certificate["jointly_satisfiable"]
            assert certificate["non_entailment_bidirectional"]
        for m in (7, 8, 9, 10):
            assert certify_composition("B", n, m)["jointly_satisfiable"]


def test_empty_response_is_vacuous_pool_pass_and_target_failure():
    for cid in CANDIDATE_IDS:
        assert added_verifier(cid)("") is True
    assert target.s0_count("") == 0        # fails any n >= 1


def test_boundary_cases_cover_required_phenomena():
    covers = {case["covers"] for case in BOUNDARY_CASES}
    for needed in ("empty", "punctuation", "capitalisation", "hyphenation",
                   "inside-longer-word", "repeated", "non-latin",
                   "cut-off-mid-word"):
        assert any(needed in c for c in covers), needed
