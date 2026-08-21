"""The audit card is only worth reading if it cannot lie about the verifier.

Two properties carry everything. The **decomposition** must be the registered
statistic's own answer rather than a second implementation of it, on every
numerator and on the awkward text as well as the easy text. And the card's
**verdict, arithmetic and alternative readings** must be the ones the study's
own functions produce, not a restatement that could drift from them.

The rest is selection --- reproducible, coverage-greedy, and not a function of
the verdict --- and the standing, which must never claim to be §10.3.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError
from dci1v4.verifiers.target import s0_count

from dci1v4r4.stages.microcase import DEFECT_KINDS, defect_verdict
from dci1v4r4.stages.verifier_audit import (
    GRANULARITY, card, decompose, discriminating, select, tags,
)
from dci1v4r4.verifiers.boundary import ALL_CASES
from dci1v4r4.verifiers.compliance import graded, passes
from dci1v4r4.verifiers.constraints import (
    FAMILIES, Constraint, declared_range,
)
from dci1v4r4.verifiers.statistics import (
    STATISTICS, focal_statistic, word_count,
)

TOOL = Path(__file__).resolve().parents[1] / "tools" / "v4r3_verifier_audit.py"

#: The texts §10.2 authored precisely because they are where a word list can
#: go wrong: case-folding splits, ligatures, soft hyphens, zero-width joins,
#: combining marks, terminator runs, wordless answers.
AWKWARD = [case["text"] for case in ALL_CASES]


def _constraint(kind: str, severity: int) -> Constraint:
    return (Constraint(kind, severity) if kind == "A"
            else Constraint(kind, severity, extended=True, reserve=True))


# --------------------------------------------------------- the decomposition

@pytest.mark.parametrize("statistic_id", sorted(
    s for s, grain in GRANULARITY.items() if grain in ("word", "character")))
def test_the_decomposition_sums_to_the_registered_count(statistic_id):
    """On every §10.2 boundary case, not just on comfortable prose."""
    unfaithful = []
    for text in AWKWARD:
        found = decompose(statistic_id, text)
        if not found["faithful"]:
            unfaithful.append((text[:40], found["count"],
                               found["probed_total"]))
    assert not unfaithful, unfaithful


@pytest.mark.parametrize("statistic_id", sorted(
    s for s, grain in GRANULARITY.items()
    if grain == "word" and s in STATISTICS))
def test_a_matched_unit_is_one_the_registered_function_matches(statistic_id):
    """The listing is decided by the statistic itself, never by a re-read."""
    for text in AWKWARD[:60]:
        found = decompose(statistic_id, text)
        for unit in found["matched"]:
            assert STATISTICS[statistic_id](unit) == 1
        assert len(found["matched"]) == found["count"]


def test_the_target_word_decomposes_under_its_own_carried_counter():
    """A's numerator is §9.2's, which folds first and segments after."""
    for text in AWKWARD[:60]:
        found = decompose("s0", text)
        for unit in found["matched"]:
            assert s0_count(unit) == 1
        assert len(found["matched"]) == found["count"] == s0_count(text)


def test_an_unfaithful_decomposition_says_so_rather_than_guessing():
    """A statistic that does not decompose per unit must not pretend to."""
    doubled = decompose("doubled_letter", "aa bb")
    assert doubled["faithful"]
    sentence = decompose("sentence", "One. Two. Three.")
    assert sentence["matched"] == [] and "not a count of independent units" \
        in sentence["reads"]


def test_the_faithfulness_check_catches_a_statistic_that_does_not_decompose():
    """The branch the real corpus never reaches, reached deliberately.

    A statistic counting *adjacent pairs* is a perfectly good counter and a
    terrible per-unit decomposition: no single word is a pair, so every probe
    returns zero while the whole-text count does not. The card must notice and
    say so rather than display "matched: nothing" beside a count of four.
    """
    def pairs(text: str) -> int:
        words = text.split()
        return sum(1 for a, b in zip(words, words[1:]) if a == b)

    original = STATISTICS.get("b_initial")
    try:
        STATISTICS["b_initial"] = pairs
        found = decompose("b_initial", "cot cot cot bay bay")
        assert found["count"] == 3
        assert found["probed_total"] == 0
        assert found["faithful"] is False
        built = card("RF1", 1, "cot cot cot bay bay")
        assert built["numerator"]["faithful"] is False
    finally:
        STATISTICS["b_initial"] = original


def test_a_numerator_with_no_registered_decomposition_is_refused():
    with pytest.raises(ProtocolError):
        decompose("not_a_statistic", "text")


def test_every_registered_numerator_has_a_granularity():
    for kind, family in FAMILIES.items():
        assert family.statistic_id in GRANULARITY, kind
    assert {"s0", "focal"} <= set(GRANULARITY)


# ---------------------------------------------------------------- the card

def test_the_card_reports_the_verifier_s_own_verdict_and_grade():
    for kind in sorted(FAMILIES):
        severity = min(declared_range(kind))
        for text in AWKWARD[:25]:
            constraint = _constraint(kind, severity)
            statistic = STATISTICS[FAMILIES[kind].statistic_id](text)
            built = card(kind, severity, text)
            assert built["verdict"] == ("SATISFIES"
                                        if passes(constraint, statistic, text)
                                        else "VIOLATES")
            assert built["graded"] == pytest.approx(
                graded(constraint, statistic, text), abs=1e-6)
            assert built["numerator"]["count"] == statistic


def test_the_shown_arithmetic_is_the_arithmetic_the_predicate_used():
    text = "Apple orange igloo under egg and a cot cot cot"
    built = card("CR11", 12, text)
    statistic = STATISTICS["vowel_initial"](text)
    words = word_count(text)
    assert built["denominator"]["value"] == words
    assert built["derived"]["value"] == pytest.approx(
        100.0 * statistic / words)
    assert f"{statistic}" in built["derived"]["arithmetic"]
    assert f"{words}" in built["derived"]["arithmetic"]


def test_a_wordless_answer_is_shown_as_having_no_rate():
    built = card("CR11", 12, "   ")
    assert built["derived"]["value"] is None
    assert "no words" in built["derived"]["arithmetic"]
    assert built["verdict"] == "VIOLATES"


def test_the_alternative_readings_come_from_the_microcase_function():
    text = "Bay bell cot cot cot cot"
    built = card("RF1", 1, text)
    constraint = _constraint("RF1", 1)
    for defect in DEFECT_KINDS:
        expected = ("SATISFIES" if defect_verdict(constraint, text, defect)
                    else "VIOLATES")
        assert built["alternative_readings"][defect] == expected
    assert set(built["discriminates"]) == set(discriminating("RF1", 1, text))


def test_a_and_b_carry_their_own_counters():
    text = "however However howeverhowever extraordinarilylong"
    assert card("A", 3, text)["numerator"]["count"] == s0_count(text)
    assert card("B", 8, text)["numerator"]["count"] == focal_statistic(text)
    assert card("A", 3, text)["alternative_readings"] == {}


def test_the_card_names_what_the_numerator_counts_in_the_rule_s_own_words():
    built = card("CR11", 12, "apple cot")
    assert "y is not a vowel" in built["numerator"]["counts"]
    assert card("CR6", 1, "Cot cot")["numerator"]["counts"].endswith(
        "(new in v4r3, no carry-over evidence)")


# ------------------------------------------------------------- the selection

def _pool():
    pool = []
    for index, kind in enumerate(sorted(FAMILIES)):
        severity = min(declared_range(kind))
        for offset, text in enumerate(AWKWARD[:12]):
            pool.append({
                "row_id": f"row-{index:03d}-{offset:03d}", "position": 1,
                "kind": kind, "severity": severity, "wording_index": 0,
                "instrument": f"{kind}:{severity}", "response": text,
                "model_key": "model-x",
                "statistic_id": FAMILIES[kind].statistic_id,
                "form": FAMILIES[kind].form, "margin": offset % 3 or None,
                "verdict": "SATISFIES" if offset % 2 else "VIOLATES"})
    return pool


def test_the_selection_is_reproducible():
    first = select(_pool(), per_family=3)
    second = select(_pool(), per_family=3)
    assert [c["row_id"] for c in first] == [c["row_id"] for c in second]


def test_the_selection_covers_every_family_and_every_numerator_form_pair():
    chosen = select(_pool(), per_family=3)
    assert len({c["kind"] for c in chosen}) == len(FAMILIES)
    pairs = {f"{c['statistic_id']}:{c['form']}" for c in chosen}
    assert pairs == {f"{f.statistic_id}:{f.form}" for f in FAMILIES.values()}


def test_the_greedy_prefers_a_card_that_exercises_something_new():
    """Two cards from a family should not be tag-identical when they need
    not be: the second is chosen for what the first does not cover."""
    chosen = select(_pool(), per_family=3)
    for kind in sorted(FAMILIES):
        picked = [c for c in chosen if c["kind"] == kind]
        if len(picked) > 1:
            assert set(picked[0]["tags"]) != set(picked[1]["tags"])


def test_selection_does_not_read_the_verdict_as_a_preference():
    """Flipping every recorded verdict must not change which cards are drawn.

    The verdict is a *tag* for coverage, so it may influence the order within
    a family; it must never decide membership by favouring, say, failures.
    """
    pool = _pool()
    flipped = [{**i, "verdict": ("VIOLATES" if i["verdict"] == "SATISFIES"
                                 else "SATISFIES")} for i in pool]
    assert {c["row_id"] for c in select(pool, per_family=3)} == \
           {c["row_id"] for c in select(flipped, per_family=3)}


def test_tags_record_the_phenomena_a_response_actually_exhibits():
    item = {"kind": "RF1", "severity": 1, "response": "co-operate well-known",
            "statistic_id": "b_initial", "form": "count_budget",
            "margin": 1, "verdict": "SATISFIES"}
    found = tags(item)
    assert "phenomenon:hyphenated" in found
    assert "margin:one" in found
    assert "numerator-form:b_initial:count_budget" in found


# ---------------------------------------------------------------- standing

def test_the_tool_never_calls_its_output_an_agreement_rate():
    """It may *say* it is not an agreement rate; it may not emit one.

    So the check is on the field names the tool writes, not on the prose:
    no key called agreement, no Wilson bound, no measurement basis, and no
    claim about §10.3 --- because a reader who finds `"agreement": 0.94` in
    an artifact will quote it whatever the docstring beside it says.
    """
    source = TOOL.read_text()
    for forbidden in ('"agreement"', '"wilson', "wilson_upper",
                      "satisfies_section_10_3", "measurement_basis",
                      "human_validated"):
        assert forbidden not in source, forbidden
    assert "not an agreement rate" in source


def test_the_report_states_what_a_confirmed_defect_costs():
    source = TOOL.read_text()
    assert "what_a_finding_costs" in source
    assert "CHANGES_SCIENTIFIC.md" in source


def test_the_cards_artifact_binds_the_verifier_hash():
    source = TOOL.read_text()
    assert '"canonical_verifier_hash": verifier_source_hash()' in source


def test_the_pool_excludes_composed_cells():
    """Same guard as the defect-sensitivity diagnostic: load 2 never enters."""
    from dci1v4r4.stages import human_audit
    source = Path(human_audit.__file__).read_text()
    assert 'if row.get("load", 0) > 1:' in source
    assert "continue" in source.split('if row.get("load", 0) > 1:')[1][:40]


def test_the_built_cards_all_decompose_faithfully():
    """The property the build command reports, asserted rather than trusted."""
    built = [card(item["kind"], item["severity"], item["response"])
             for item in select(_pool(), per_family=2)]
    assert built
    assert all(entry["numerator"]["faithful"] for entry in built)


def test_a_stored_card_set_can_be_checked_against_its_hash():
    from dci1v4.protocol.hashing import canonical_json, sha_text
    chosen = select(_pool(), per_family=2)
    cards = [card(i["kind"], i["severity"], i["response"]) for i in chosen]
    digest = sha_text(canonical_json(cards))
    assert sha_text(canonical_json(json.loads(json.dumps(cards)))) == digest
    cards[0]["verdict"] = "SATISFIES" if cards[0]["verdict"] == "VIOLATES" \
        else "VIOLATES"
    assert sha_text(canonical_json(cards)) != digest


# ------------------------------------------------- the §7.3 lexical footprint

def _footprint():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "v4r3_lexical_footprint",
        Path(__file__).resolve().parents[1] / "tools"
        / "v4r3_lexical_footprint.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_reader_word_differs_from_the_registered_word_only_on_joiners():
    """The scope claim the footprint diagnostic rests on.

    If the two readings differed anywhere else, the measured footprint would
    be attributing to apostrophes and hyphens something they did not cause.
    """
    footprint = _footprint()
    from dci1v4r4.verifiers.words import alpha_runs
    for text in AWKWARD:
        if any(ch in text for ch in "'’-‐"):
            continue
        assert footprint.reader_words(text) == alpha_runs(text), repr(text)


def test_the_reader_word_joins_the_forms_the_registered_word_splits():
    footprint = _footprint()
    from dci1v4r4.verifiers.words import alpha_runs
    for text, joined in [("don't", ["don't"]),
                         ("well-known", ["well-known"]),
                         ("It's a state-of-the-art system",
                          ["It's", "a", "state-of-the-art", "system"])]:
        assert footprint.reader_words(text) == joined
        assert len(alpha_runs(text)) > len(joined)


@pytest.mark.parametrize("statistic_id", sorted(
    s for s in GRANULARITY if s not in ("s0", "focal", "sentence")))
def test_the_two_readings_agree_where_no_joiner_occurs(statistic_id):
    """A numerator that moved on joiner-free text would be a different rule."""
    footprint = _footprint()
    if footprint.reader_statistic(statistic_id, "cot") is None:
        pytest.skip("character-shaped numerator; the question does not apply")
    for text in AWKWARD:
        if any(ch in text for ch in "'’-‐"):
            continue
        assert footprint.reader_statistic(statistic_id, text) == \
            STATISTICS[statistic_id](text), repr(text)


def test_the_footprint_excludes_the_numerators_the_question_cannot_touch():
    footprint = _footprint()
    for statistic_id in ("comma", "semicolon", "capital_char", "sentence"):
        assert footprint.reader_statistic(statistic_id, "a, b; C. d") is None
