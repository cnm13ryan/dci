"""Property and mutation tests for the Pair 3 sentence-count verifier.

The v19 preregistration requires semantic, boundary, DIFFERENTIAL and PROPERTY
testing of a reused Pair 2/3 verifier. `test_sentence_boundary_abbreviations`
covers semantic and boundary cases; this module covers the invariants and the
mutation bank around the measurement boundary.

Randomised cases carry a fixed seed and print the failing example, because a
property test that cannot show you its counterexample is not much use.
"""
from __future__ import annotations

import random

import pytest

from dci.verifiers.rules import split_sentences

SEED = 20260810


def count(text: str) -> int:
    return len(split_sentences(text))


# A bank of valid four-sentence outputs, in the register the model actually
# produces, used as the source for every mutation below.
FOUR_SENTENCE_BANK = [
    "Rain falls on the roof. Water runs to the gutter. "
    "The gutter drains to a pipe. The pipe empties into a drain.",
    "A hinge connects the door to the frame. The pin carries the weight. "
    "The leaves rotate around that pin. The door swings freely.",
    "Bakers start before dawn. Dough proves in the warm kitchen. "
    "Loaves bake until the crust darkens. Customers arrive at opening.",
    "A whisk moves quickly through the mixture. Tines drag air beneath the "
    "surface. Bubbles form and remain trapped. The batter grows lighter.",
    "Hikers follow the marked route. Signs appear at every junction. "
    "The path avoids the steepest ground. Walkers reach the summit safely.",
]


# ==================================================================== properties
@pytest.mark.parametrize("base", FOUR_SENTENCE_BANK)
def test_the_bank_is_actually_four_sentences(base):
    assert count(base) == 4, split_sentences(base)


@pytest.mark.parametrize("abbrev", ["a.m.", "p.m.", "e.g.", "i.e.", "etc.",
                                    "approx.", "vs.", "cf."])
def test_inserting_an_abbreviation_inside_a_sentence_does_not_change_the_count(abbrev):
    """Property 1: an abbreviation mid-sentence is not a boundary."""
    for base in FOUR_SENTENCE_BANK:
        first, rest = base.split(". ", 1)
        mutated = f"{first} at 6 {abbrev} on most days. {rest}"
        assert count(mutated) == 4, (abbrev, split_sentences(mutated))


@pytest.mark.parametrize("title", ["Dr.", "Mr.", "Mrs.", "Prof."])
def test_a_title_followed_by_a_name_is_not_a_boundary(title):
    """Property 2: an abbreviation-preserving rewrite leaves the count alone."""
    for base in FOUR_SENTENCE_BANK:
        first, rest = base.split(". ", 1)
        mutated = f"{first}, according to {title} Hale. {rest}"
        assert count(mutated) == 4, (title, split_sentences(mutated))


@pytest.mark.parametrize("number", ["3.14", "0.25", "2.9.1"])
def test_a_decimal_point_never_creates_a_sentence(number):
    """Property 3: interior numeric punctuation is not a boundary."""
    for base in FOUR_SENTENCE_BANK:
        first, rest = base.split(". ", 1)
        mutated = f"{first} measuring {number} metres. {rest}"
        assert count(mutated) == 4, (number, split_sentences(mutated))


def test_replacing_a_boundary_with_a_semicolon_reduces_the_count_by_one():
    """Property 4: a semicolon joins two sentences into one."""
    for base in FOUR_SENTENCE_BANK:
        head, tail = base.split(". ", 1)
        mutated = f"{head}; {tail[0].lower()}{tail[1:]}"
        assert count(mutated) == count(base) - 1, split_sentences(mutated)


def test_adding_one_sentence_increases_the_count_by_exactly_one():
    """Property 5."""
    for base in FOUR_SENTENCE_BANK:
        assert count(base + " The work then stops.") == count(base) + 1


def test_merging_two_sentences_reduces_the_count_by_exactly_one():
    """Property 6."""
    for base in FOUR_SENTENCE_BANK:
        head, tail = base.split(". ", 1)
        merged = f"{head} and {tail[0].lower()}{tail[1:]}"
        assert count(merged) == count(base) - 1, split_sentences(merged)


def test_splitting_one_sentence_increases_the_count_by_exactly_one():
    """Property 7."""
    for base in FOUR_SENTENCE_BANK:
        head, tail = base.split(". ", 1)
        head_words = head.split()
        pivot = len(head_words) // 2
        split = (" ".join(head_words[:pivot]) + ". "
                 + " ".join(head_words[pivot:]).capitalize())
        mutated = f"{split}. {tail}"
        assert count(mutated) == count(base) + 1, split_sentences(mutated)


def test_randomised_abbreviation_insertion_is_count_preserving():
    """Property 1, randomised over insertion point and abbreviation."""
    rng = random.Random(SEED)
    abbreviations = ["a.m.", "p.m.", "e.g.", "i.e.", "etc.", "approx.", "cf.",
                     "vs.", "Dr. Hale", "Mr. Patel", "J. R. Hartley"]
    for _ in range(300):
        base = rng.choice(FOUR_SENTENCE_BANK)
        sentences = [s for s in base.split(". ") if s]
        index = rng.randrange(len(sentences))
        abbrev = rng.choice(abbreviations)
        sentences[index] = f"{sentences[index].rstrip('.')} near {abbrev} today"
        mutated = ". ".join(s.rstrip(".") for s in sentences) + "."
        assert count(mutated) == 4, (abbrev, index, mutated, split_sentences(mutated))


# ============================================================== mutation bank
#
# Each mutation applies ONE transformation to a four-sentence source and states
# the expected change in sentence count. Three of these expectations were wrong
# on the first pass and the verifier was right; they are corrected here, and the
# convention each one pins is named, because a mutation whose expected value was
# fitted to the observed output tests nothing.

SEMICOLON_BANK = [
    "Rain falls on the roof; the tiles are old. Water runs to the gutter. "
    "The gutter drains to a pipe. The pipe empties into a drain.",
    "A hinge connects the door; the pin carries the weight. The leaves rotate. "
    "The door swings freely. The frame stays square.",
]


def _split_first_sentence(text: str) -> str:
    """Split the first sentence at its midpoint. Applies to any prose."""
    head, tail = text.split(". ", 1)
    words = head.split()
    pivot = max(1, len(words) // 2)
    left, right = " ".join(words[:pivot]), " ".join(words[pivot:])
    return f"{left}. {right[0].upper()}{right[1:]}. {tail}"


def _ellipsis_lowercase(text: str) -> str:
    """Replace a boundary with an ellipsis and a LOWER-CASE continuation."""
    head, tail = text.split(". ", 1)
    return f"{head}... {tail[0].lower()}{tail[1:]}"


def _boundary_to_abbreviation(text: str) -> str:
    """Replace a real boundary with `a.m.` + a LOWER-CASE continuation.

    This is the defect class itself: before the repair the parser split here
    anyway, inventing a sentence. Expected delta is -1, because a boundary is
    genuinely removed.
    """
    head, tail = text.split(". ", 1)
    return f"{head} at 6 a.m. {tail[0].lower()}{tail[1:]}"


MUTATIONS = {
    # name: (transform, expected delta, the convention it pins)
    "insert_abbreviation_midsentence": (
        lambda t: t.replace(" on the ", " on the 6 a.m. ", 1)
        if " on the " in t else t.replace(". ", " near 6 a.m. today. ", 1),
        0, "an abbreviation inside a sentence is not a boundary"),
    "boundary_becomes_abbreviation_lowercase": (
        _boundary_to_abbreviation, -1,
        "abbreviation + lower-case continuation removes the boundary"),
    "boundary_keeps_abbreviation_capital": (
        lambda t: t.replace(". ", " at 6 a.m. ", 1), 0,
        "abbreviation + capital still ends the sentence"),
    "insert_title": (
        lambda t: t.replace(". ", ", says Dr. Hale. ", 1), 0,
        "a title takes a name, never a boundary"),
    "insert_initials": (
        lambda t: t.replace(". ", ", per J. R. Hartley. ", 1), 0,
        "initials are not boundaries"),
    "insert_decimal": (
        lambda t: t.replace(". ", " over 3.14 metres. ", 1), 0,
        "interior numeric punctuation is not a boundary"),
    "period_to_semicolon": (
        lambda t: t.replace(". ", "; ", 1), -1,
        "a semicolon joins two sentences"),
    "merge_two": (
        lambda t: t.replace(". ", " and ", 1), -1, "merging removes one"),
    "split_one": (
        _split_first_sentence, +1, "splitting adds exactly one"),
    "add_quotes": (
        lambda t: '"' + t.replace(". ", '." ', 1), 0,
        "a full stop inside quotes still ends the sentence"),
    "newline_layout": (
        lambda t: t.replace(". ", ".\n", 1), 0,
        "a newline layout does not change the count"),
    "bullet_markers": (
        lambda t: "- " + t.replace(". ", ".\n- "), 0,
        "list markers are stripped, not counted"),
    "numbered_markers": (
        lambda t: "1. " + t.replace(". ", ".\n2. ", 1), 0,
        "numeric list markers are stripped, not counted"),
    "add_preamble": (
        lambda t: "Here is the answer. " + t, +1, "a preamble is a sentence"),
    "ellipsis_at_boundary_capital": (
        lambda t: t.replace(". ", "... ", 1), 0,
        "an ellipsis before a capital still ends the sentence"),
    "ellipsis_midsentence_lowercase": (
        lambda t: _ellipsis_lowercase(t), -1,
        "an ellipsis before a lower-case word continues the sentence"),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_mutation_bank_moves_the_count_as_specified(name):
    mutate, delta, convention = MUTATIONS[name]
    bank = SEMICOLON_BANK if name == "semicolon_to_period" else FOUR_SENTENCE_BANK
    for base in bank:
        mutated = mutate(base)
        assert mutated != base, f"{name} was a no-op on {base!r}"
        expected = count(base) + delta
        assert count(mutated) == expected, (
            f"{name} ({convention}): expected {expected}, got {count(mutated)}\n"
            f"  source:  {base!r}\n  mutated: {mutated!r}\n"
            f"  segments: {split_sentences(mutated)!r}")


def test_semicolon_to_period_adds_a_sentence():
    """The converse mutation, on a bank that actually contains semicolons."""
    for base in SEMICOLON_BANK:
        mutated = base.replace("; ", ". ", 1)
        head = mutated.split(". ", 1)[1]
        mutated = mutated.split(". ", 1)[0] + ". " + head[0].upper() + head[1:]
        assert mutated != base
        assert count(mutated) == count(base) + 1, split_sentences(mutated)


def test_the_semicolon_bank_is_four_sentences():
    for base in SEMICOLON_BANK:
        assert count(base) == 4, split_sentences(base)
