"""Verifiers and Gate 1 machinery (item 62): scoring rules, family
verifiers, the frozen boundary suite, witnesses, wording equivalence,
parse independence, determinism, and the Wilson/Newcombe machinery."""
from __future__ import annotations

import inspect

import pytest

from dci1v3.analysis.stats import (
    newcombe_interval,
    wilson_interval,
    wilson_upper_one_sided,
)
from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import FOCAL_GRID, REFERENCE_FAMILIES
from dci1v3.verifiers import families, target
from dci1v3.verifiers.boundary import (
    BOUNDARY_CASES,
    COVERAGE,
    evaluate_suite,
)
from dci1v3.verifiers.witnesses import verify_all_witnesses
from dci1v3.verifiers.wording_suite import check_equivalence, parse_wording


def test_s0_semantics():
    assert target.s0_count("However, however!") == 2
    assert target.s0_count("Howeverhowever") == 0
    assert target.s0_count("") == 0
    assert target.s1_count("However however") == 1
    assert target.s2_count("Howeverhowever") == 2
    assert target.passes(3, 3) and not target.passes(2, 3)
    assert target.graded(5, 3) == 2


def test_s3_preamble_removal():
    text = "Here is my answer:\nhowever the plan works."
    assert target.s0_count(text) == 1
    assert target.s3_count(text, ()) == 1
    wording = "Use the word however exactly 2 times."
    restated = f"{wording}\nhowever alone."
    assert target.s3_count(restated, (wording,)) == 1
    assert target.s0_count(restated) == 2


def test_family_statistics():
    assert families.family_statistic("RF1", "Bright blue sky") == 2
    assert families.family_statistic("RF2", "singing and dancing") == 2
    assert families.family_statistic("RF3", "a b see") == 2
    assert families.family_statistic("RF4", "coffee book") == 2
    assert families.family_statistic("RF5", "a, b, c") == 2
    assert families.family_statistic("RF6", "AbC dEf") == 3
    assert families.family_statistic("RF7", "cat dog bat") == 2
    assert families.family_statistic("RF8", "very happy dog") == 2
    assert families.focal_statistic("hi extraordinary") == 13
    assert families.focal_passes("small words", 7)
    assert not families.focal_passes("extraordinary", 10)


def test_boundary_suite_forty_of_forty():
    result = evaluate_suite()
    assert result["cases"] == 40
    assert result["handled_as_specified"] == 40, result["failures"]
    covered = {cid for ids in COVERAGE.values() for cid in ids}
    assert covered <= {c["case_id"] for c in BOUNDARY_CASES}
    assert len(COVERAGE) == 8


def test_witnesses_all_compositions():
    report = verify_all_witnesses()
    assert report["compositions"] == 8 * (4 + 32)
    assert report["witnesses_verified"]


def test_wording_equivalence_suites():
    report = check_equivalence()
    assert report["combinations"] == 44
    assert report["suite_size"] == 20


def test_parse_independence_by_signature():
    """The target verifier receives response text (and n via the caller);
    no arm, added-constraint, or verifier-output parameter exists."""
    for fn in (target.s0_count, target.s1_count, target.s2_count):
        params = list(inspect.signature(fn).parameters)
        assert params == ["text"]
    added = list(inspect.signature(families.added_verifier).parameters)
    assert added == ["constraint_id", "severity"]


def test_wording_binding_unambiguous():
    assert parse_wording("Use the word however exactly 4 times.") == ("A", 4)
    assert parse_wording(
        "Every word in the answer must have at most 9 letters.") == ("B", 9)
    assert parse_wording(
        "No more than 4 commas may appear in the answer.") == ("RF5", 4)
    with pytest.raises(ProtocolError):
        parse_wording("This is not a registered wording.")


def test_family_severity_guards():
    with pytest.raises(ProtocolError):
        families.family_passes("RF1", "text", 3)     # not on the grid
    with pytest.raises(ProtocolError):
        families.focal_passes("text", 6)             # not on the grid
    assert set(REFERENCE_FAMILIES) == {f"RF{i}" for i in range(1, 9)}
    assert FOCAL_GRID == (7, 8, 9, 10)


def test_wilson_and_newcombe():
    low, high = wilson_interval(3, 10)
    assert 0.0 < low < 0.3 < high < 0.7
    assert wilson_upper_one_sided(0, 150) < 0.03
    assert wilson_upper_one_sided(20, 150) > 0.10
    lo, hi = newcombe_interval(3, 24, 5, 24)
    assert lo < 0 < hi


def test_determinism_worker_digest_stable():
    from dci1v3.stages.determinism_worker import verdict_digest
    items = [{"item_id": "x", "response_text": "however but Big words"}]
    assert verdict_digest(items) == verdict_digest(items)
