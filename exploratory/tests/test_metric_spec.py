"""Freeze the structural-strategy metrics against METRIC_SPEC.md.

Every case here corresponds to a row or a statement in that document. If one of
these fails, the specification and the implementation have diverged and one of
them is wrong — which is the point of writing them down together.
"""
from __future__ import annotations

import math

import pytest

from dci_exploratory import extensions
from dci_exploratory.mechanism import clause_chain_features as ccf

FOUR_PLAIN = "Rain falls. Rivers rise. Wind blows. Leaves turn."
FOUR_JOINED = ("Rain falls; this soaks the ground. Rivers rise; they spill over. "
               "Wind blows; it scatters seed. Leaves turn; they fall.")
ONE_CHAIN = "Rain falls; this soaks the ground; it then drains; they spill over."


# ------------------------------------------------------------ reference points
@pytest.mark.parametrize("text,splice,chain", [
    (FOUR_PLAIN, 0.0, 0.0),
    (FOUR_JOINED, 0.5, 0.5),
    (ONE_CHAIN, 0.75, 0.75),
])
def test_reference_points_from_the_spec(text, splice, chain):
    d = ccf(text)
    assert d["splice_share"] == pytest.approx(splice)
    assert d["chain_share"] == pytest.approx(chain)


# ------------------------------------------------------------------ the marks
@pytest.mark.parametrize("mark,text,expected", [
    ("semicolon", "a; this b", 1),
    ("colon", "a: this b", 1),
    ("dash", "a — this b", 1),
    ("dash", "a – this b", 1),
    ("dash", "a -- this b", 1),
    ("comma", "a, this b", 1),
])
def test_every_registered_mark_is_detectable(mark, text, expected):
    assert extensions.splice_count(text, mark) == expected


def test_the_double_hyphen_is_matched_whole():
    """`--` is first in the alternation; otherwise it cannot match at all."""
    assert extensions.splice_count("a -- this b", "dash") == 1
    assert extensions.splice_count("a - this b", "dash") == 0


def test_the_colon_and_dash_bug_stays_fixed():
    """The regression that made colon and dash structurally 0 for every input."""
    text = "Bakeries open early : This timing helps — it works; this holds."
    assert extensions.splice_count(text, "colon") == 1
    assert extensions.splice_count(text, "dash") == 1
    assert extensions.splice_count(text, "semicolon") == 1


# --------------------------------------------------- the closed word list
def test_determiners_are_excluded_so_a_list_is_not_a_splice():
    assert extensions.splice_count("The parts are a lever; a spring; a base.",
                                   "semicolon") == 0


def test_a_determiner_initial_join_is_recovered_by_segment_length():
    """The Stage 0.3 recall failure. Long segment -> counted despite `the`."""
    assert extensions.splice_count(
        "The lever moves; the spring returns to its original position.",
        "semicolon") == 1


def test_a_short_determiner_initial_segment_is_still_not_a_splice():
    """Below MIN_CLAUSE_WORDS, so a list item cannot sneak back in."""
    assert extensions.splice_count("The lever moves; the spring returns.",
                                   "semicolon") == 0


def test_the_audit_false_negative_is_repaired():
    """One sentence, six joins, previously scored 0.000."""
    text = ("A stapler binds sheets by driving a metal staple through the "
            "edges; the staple is pushed into the paper with force; once it is "
            "fully inserted, it holds the sheets together securely; (this is "
            "especially useful in office environments); the design allows for "
            "quick and consistent results.")
    assert extensions.splice_count(text, "semicolon") >= 4
    assert ccf(text)["chain_share"] > 0.7


def test_a_join_behind_a_bracket_is_not_missed():
    """`; (this ...)` did not match the old mark-plus-letter anchor at all."""
    assert extensions.splice_count("The staple is set; (this action repeats).",
                                   "semicolon") == 1


def test_a_time_of_day_colon_is_not_a_splice():
    assert extensions.splice_count("The train leaves at 8:00 sharp.", "colon") == 0


def test_clause_initial_is_matched_case_insensitively():
    assert extensions.splice_count("a; This b", "semicolon") == 1
    assert extensions.splice_count("a; this b", "semicolon") == 1


# ----------------------------------------------------------------- edge cases
def test_no_boundary_at_all_is_nan_not_zero():
    d = ccf("plain words with no punctuation")
    assert math.isnan(d["splice_share"])
    assert math.isnan(d["chain_share"])


def test_splices_without_a_terminal_is_one():
    d = ccf("a; this b; it c")
    assert d["splice_share"] == pytest.approx(1.0)


def test_terminals_without_a_splice_is_zero():
    assert ccf("One. Two. Three.")["splice_share"] == pytest.approx(0.0)


def test_none_is_zero_splices():
    assert extensions.splice_count(None, "semicolon") == 0


def test_abbreviations_inflate_the_terminal_count_and_deflate_the_share():
    """Documented bias: T is a raw [.!?] count and does not use the segmenter."""
    plain = ccf("Rain falls; this soaks in.")
    abbrev = ccf("Dr. Ellis notes rain falls; this soaks in.")
    assert abbrev["n_terminal_marks"] > plain["n_terminal_marks"]
    assert abbrev["splice_share"] < plain["splice_share"]


# ------------------------------------------------- comma exclusion from chain
def test_the_comma_is_excluded_from_chain_share_but_still_reported():
    d = ccf("Rain falls, this soaks the ground.")
    assert d["n_comma_splices"] == 1
    assert d["chain_share"] == pytest.approx(0.0), (
        "a comma cannot stand where a terminator stands, so it must not enter "
        "a measure of boundary substitution")


def test_a_comma_run_on_is_visible_as_something_other_than_chaining():
    comma = ccf("Rain falls, this soaks in, it then drains, they spill over.")
    semi = ccf(ONE_CHAIN)
    assert comma["chain_share"] == pytest.approx(0.0)
    assert semi["chain_share"] > 0.5
    assert comma["n_comma_splices"] == 3


# --------------------------------------------- independence from the outcome
def test_the_metrics_never_consult_the_segmenter_or_a_target():
    import inspect
    source = inspect.getsource(ccf)
    for forbidden in ("split_sentences", "n_target", "a_failure", "verify"):
        assert forbidden not in source, (
            f"{forbidden} appears in the strategy measure; it must be computable "
            "on a row whose target verdict is unknown")


def test_high_share_and_target_success_can_coexist():
    """The arithmetic permits it; the corpus confirms it (E5a: 0.456 / 0.013)."""
    text = ("Rain falls; this soaks in. Rivers rise; they spill. "
            "Wind blows; it scatters. Leaves turn; they fall.")
    from dci.verifiers.rules import split_sentences
    assert ccf(text)["chain_share"] == pytest.approx(0.5)
    assert len(split_sentences(text)) == 4          # a 4-sentence target passes
