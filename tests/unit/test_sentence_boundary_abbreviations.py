"""Sentence-segmentation boundary cases for the Pair 3 target verifier.

`v_exact_sentence_count` decides the primary outcome F_A, so every segmentation
error is a scientific error, not a cosmetic one. The v19 preregistration makes
verifier validity a hard eligibility condition for a reused Pair 2/3 verifier and
requires semantic, boundary, differential and property tests; this module is the
boundary and semantic half for sentence segmentation.

Every case states the expected count explicitly. Where the intended semantics are
genuinely ambiguous the case is marked and the chosen convention is written down,
because an untested convention is how the a.m./p.m. defect survived migration.
"""
from __future__ import annotations

import pytest

from dci.verifiers.rules import split_sentences, v_exact_sentence_count


def count(text: str) -> int:
    return len(split_sentences(text))


# =========================================================== the reported defect
#
# Minimal reproducers. Each was verified to FAIL before the repair, with the
# parser splitting at the full stop inside the abbreviation.
ABBREVIATION_CASES = [
    # (text, expected_sentences, label)
    ("Sales spike at 6 a.m. when others sleep.", 1, "am_mid_sentence"),
    ("Staff finish by 8 p.m. most days.", 1, "pm_mid_sentence"),
    ("The bakery opens at 6 a.m. every weekday. Bread is ready by seven.", 2,
     "am_mid_then_real_boundary"),
    ("Sales spike at 6 a.m. when others sleep. Suppliers arrive at 5 p.m. as the "
     "shop closes. Staff finish by 8 p.m. most days. The routine repeats.", 4,
     "am_pm_multiple_inside_four_sentences"),
    ("The first batch is made at 4 a.m. to meet demand by 7 a.m. every day.", 1,
     "am_twice_one_sentence"),
    # A genuine sentence END immediately after the abbreviation must still split.
    # Convention: a following CAPITAL marks the boundary.
    ("The shop opens at 6 a.m. Customers queue outside.", 2, "am_at_true_end"),
    ("Deliveries stop at 5 p.m. Staff lock the doors.", 2, "pm_at_true_end"),
]


@pytest.mark.parametrize("text,expected,label",
                         ABBREVIATION_CASES,
                         ids=[c[2] for c in ABBREVIATION_CASES])
def test_time_abbreviations_do_not_split_sentences(text, expected, label):
    assert count(text) == expected, split_sentences(text)


def test_the_reported_defect_changes_the_scientific_outcome():
    """The defect turned a compliant four-sentence answer into a violation."""
    text = ("Sundays see fresh bread sold before stores stock up. "
            "Suppliers ship goods swiftly to support early demand. "
            "Satisfied customers seek specialty items soon after dawn. "
            "Sales spike at 6 a.m. when others sleep.")
    assert count(text) == 4
    assert v_exact_sentence_count(text, 4).binary_pass == 1


# ================================================================ common abbrevs
TITLE_CASES = [
    ("Dr. Smith opened the clinic. Mrs. Jones was first in line.", 2, "dr_mrs"),
    ("Prof. Hale marked the papers.", 1, "prof"),
    ("Mr. and Mrs. Patel arrived early. They waited.", 2, "mr_and_mrs"),
    ("The team met at approx. four. They reviewed the plan.", 2, "approx"),
    ("Bring bread, milk, etc. and then leave.", 1, "etc_mid"),
    ("Bring bread, milk, etc. Then leave.", 2, "etc_at_true_end"),
    ("Compare the two, e.g. the budget and the plan.", 1, "eg_mid"),
    ("It failed, i.e. the test did not pass.", 1, "ie_mid"),
]


@pytest.mark.parametrize("text,expected,label", TITLE_CASES,
                         ids=[c[2] for c in TITLE_CASES])
def test_common_abbreviations(text, expected, label):
    assert count(text) == expected, split_sentences(text)


# ===================================================================== initials
INITIAL_CASES = [
    ("J. R. Hartley wrote the book. He was patient.", 2, "two_initials"),
    ("A. Turing proposed the test.", 1, "single_initial"),
    ("The report cites J. Smith and R. Jones.", 1, "initials_mid_sentence"),
]


@pytest.mark.parametrize("text,expected,label", INITIAL_CASES,
                         ids=[c[2] for c in INITIAL_CASES])
def test_initials(text, expected, label):
    assert count(text) == expected, split_sentences(text)


# ============================================================ numeric punctuation
NUMERIC_CASES = [
    ("The value is 3.14 metres. It fits.", 2, "decimal"),
    ("Tolerance is 0.25 and the span is 1.5 metres.", 1, "two_decimals"),
    ("Release 2.9.1 shipped on time.", 1, "version_string"),
]


@pytest.mark.parametrize("text,expected,label", NUMERIC_CASES,
                         ids=[c[2] for c in NUMERIC_CASES])
def test_numeric_punctuation(text, expected, label):
    assert count(text) == expected, split_sentences(text)


# =============================================== quotation and closing punctuation
QUOTE_CASES = [
    ('She said "go now." He left at once.', 2, "period_inside_quotes"),
    ('He asked, "Is it ready?" She nodded.', 2, "question_inside_quotes"),
    ('The sign read "open at 6 a.m." and nobody moved.', 1, "abbrev_inside_quotes"),
    ("Rain fell on the roof (the tiles are old). Water ran to the gutter.", 2,
     "parentheses_before_boundary"),
]


@pytest.mark.parametrize("text,expected,label", QUOTE_CASES,
                         ids=[c[2] for c in QUOTE_CASES])
def test_quotation_and_closing_punctuation(text, expected, label):
    assert count(text) == expected, split_sentences(text)


# ===================================================================== ellipses
ELLIPSIS_CASES = [
    ("Rain falls on the roof... water runs to the gutter... the river rises.", 1,
     "ellipsis_within"),
    ("It ended there... Then it began again.", 2, "ellipsis_at_true_end"),
]


@pytest.mark.parametrize("text,expected,label", ELLIPSIS_CASES,
                         ids=[c[2] for c in ELLIPSIS_CASES])
def test_ellipses(text, expected, label):
    assert count(text) == expected, split_sentences(text)


# ============================== structural forms central to the exploratory result
#
# These must be UNCHANGED by the repair. They are the structures the collapse
# finding rests on, so a fix that moved any of them would invalidate the result
# it was meant to protect.
STRUCTURAL_CASES = [
    ("Alpha runs; beta walks; gamma sits; delta stands.", 1, "one_semicolon_chain"),
    ("Alpha begins; it is careful. Beta continues; she is quick. "
     "Gamma checks; he is thorough. Delta files; all agree.", 4,
     "four_sentences_each_with_semicolon"),
    ("Alpha runs, beta walks, gamma sits, delta stands.", 1, "comma_chain"),
    ("Bakeries open early because demand peaks at dawn, which means the bread "
     "must be ready before the first customers arrive, and this in turn requires "
     "the dough to be mixed overnight.", 1, "run_on"),
    ("Rain falls on the roof and water runs to the gutter. The gutter drains to "
     "a pipe and the pipe empties.", 2, "merged_two"),
    ("Rain falls. On the roof. Water runs. To the gutter.", 4, "split_fragments"),
    ("Rain falls on the roof\nWater runs to the gutter\nThe gutter drains\n"
     "The pipe empties", 4, "newline_no_terminators"),
    ("- Rain falls.\n- Water runs.\n- The gutter drains.\n- The pipe empties.", 4,
     "bulleted"),
    ("1. Rain falls.\n2. Water runs.\n3. The gutter drains.\n4. The pipe empties.",
     4, "numbered"),
    ("Rain falls! Water runs? The gutter drains. The pipe empties.", 4,
     "mixed_terminators"),
    ("", 0, "empty"),
    ("Rain.", 1, "single_short"),
]


@pytest.mark.parametrize("text,expected,label", STRUCTURAL_CASES,
                         ids=[c[2] for c in STRUCTURAL_CASES])
def test_structural_forms_are_unchanged_by_the_repair(text, expected, label):
    assert count(text) == expected, split_sentences(text)


# =============================================== documented convention boundaries
#
# Cases where the segmentation cannot be right for every reading. The convention
# is recorded here so it is a decision rather than an accident.
def test_convention_lowercase_after_abbreviation_is_a_continuation():
    """A lower-case word after `etc.` continues the sentence.

    Cost: a sentence that genuinely starts with a lower-case word after an
    abbreviation is under-counted. Accepted: the generations in this study are
    ordinary prose that starts sentences with a capital.
    """
    assert count("We bought bread, etc. and then we left.") == 1


def test_convention_capital_after_a_title_is_a_name_not_a_new_sentence():
    """`Dr. Smith` is one sentence, never two, whatever the capitalisation.

    Cost: a sentence genuinely beginning after a title-like token is
    under-counted, e.g. "He earned his Ph.D. Then he taught." Titles are a closed
    set and always take a following name, so the trade is worth it.
    """
    assert count("Dr. Smith opened the clinic.") == 1
