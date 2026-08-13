"""Sentence boundaries must survive an opening quote, bracket or Markdown mark.

Defect: `_ends_sentence` decided the ambiguous cases — a medial abbreviation, or
an ellipsis — by testing `following[0].isupper()`. When the next sentence opens
with punctuation rather than its first letter, `following[0]` is that
punctuation, which is never upper-case, so the boundary was rejected and two
sentences were counted as one.

This is load-bearing: exact sentence count is the primary outcome, so a merged
pair moves `A_pass` directly. It also has an arm-asymmetry risk, which is the
thing the framework warns about most sharply — a verifier can be accurate
overall and still bias tau if its errors fall more often in the focal arm than
the reference arm.

Classification: verifier/parser error, with a construct-validity consequence for
every sentence-count estimate.
"""
from __future__ import annotations

import pytest

from dci.verifiers import rules

QUOTES = ['"', "'", "“", "‘", "«", "‹"]
BRACKETS = ["(", "[", "{"]
MARKDOWN = ["*", "_", "**", "`"]


class TestMedialAbbreviationFollowedByOpeningPunctuation:
    @pytest.mark.parametrize("opener", QUOTES + BRACKETS + MARKDOWN)
    def test_boundary_survives_opening_punctuation(self, opener: str) -> None:
        closer = {"(": ")", "[": "]", "{": "}"}.get(opener, "")
        text = f'It ended at 6 p.m. {opener}Tomorrow begins early.{closer}'
        assert len(rules.split_sentences(text)) == 2, repr(text)

    def test_the_reviewed_case_exactly(self) -> None:
        text = 'It ended at 6 p.m. "Tomorrow begins early."'
        assert len(rules.split_sentences(text)) == 2

    @pytest.mark.parametrize("abbrev", ["a.m.", "p.m.", "e.g.", "i.e.", "etc."])
    def test_every_medial_abbreviation_behaves_the_same(self, abbrev: str) -> None:
        text = f'The list closed at 6 {abbrev} "Tomorrow begins early."'
        assert len(rules.split_sentences(text)) == 2, repr(text)


class TestEllipsisFollowedByOpeningPunctuation:
    def test_ellipsis_boundary_survives_a_quote(self) -> None:
        text = 'He waited... "Then it began."'
        assert len(rules.split_sentences(text)) == 2

    def test_ellipsis_before_lowercase_still_continues(self) -> None:
        text = 'He waited... then it began.'
        assert len(rules.split_sentences(text)) == 1


class TestNoRegressionOnEstablishedBehaviour:
    """The repair must not turn the closed convention into an open heuristic."""

    def test_medial_abbreviation_before_lowercase_still_continues(self) -> None:
        assert len(rules.split_sentences("It ran from 6 a.m. to 9 a.m. daily.")) == 1

    def test_medial_abbreviation_before_lowercase_in_brackets_continues(self) -> None:
        assert len(rules.split_sentences("Roughly 6 approx. (see note) items.")) == 1

    def test_title_abbreviation_never_ends_a_sentence(self) -> None:
        assert len(rules.split_sentences('Dr. "Smith" arrived.')) == 1

    def test_plain_boundary_before_a_quote_is_unchanged(self) -> None:
        assert len(rules.split_sentences('The meeting ran late. "We will resume."')) == 2

    def test_initials_are_still_not_boundaries(self) -> None:
        assert len(rules.split_sentences("J. R. Smith arrived.")) == 1

    def test_ordinary_four_sentence_answer_is_unchanged(self) -> None:
        text = ("Alpha beta. Gamma delta epsilon. "
                "Zeta eta theta iota. Kappa lambda mu nu xi.")
        assert len(rules.split_sentences(text)) == 4


class TestOpenerDoesNotManufactureBoundaries:
    def test_bare_opening_punctuation_at_end_is_not_a_boundary(self) -> None:
        assert len(rules.split_sentences('It ended at 6 p.m. "')) == 1

    def test_opening_punctuation_then_lowercase_is_not_a_boundary(self) -> None:
        assert len(rules.split_sentences('It ended at 6 p.m. "tomorrow" came.')) == 1
