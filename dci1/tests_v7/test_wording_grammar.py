"""Grammatical number in every rendered wording, and the Tier-1 / A identity.

Two claims, both mechanical. Every Tier-1 wording is A's wording with the
marker substituted and nothing else changed (§7.8). And every wording of
every registered constraint pairs its numeral with the right grammatical
number at every severity of its declared range --- *1 semicolon*,
*2 semicolons*, *0 words*, *1 word contains* --- which the non-marker
templates did not do before 2026-08-29 (``CHANGES_SCIENTIFIC.md``).
"""
from __future__ import annotations

import pytest

from dci1v4.protocol.wordings import _FAMILY_TEMPLATES as V4_TEMPLATES
from dci1v7.protocol import wordings as W
from dci1v7.verifiers import constraints as K
from dci1v7.verifiers import wording_suite

# ------------------------------------------------------- Tier-1 is A's form

def test_every_tier1_wording_is_a_s_with_only_the_marker_substituted():
    for kind in K.TIER1_FAMILY_IDS:
        marker = K.FAMILIES[kind].marker
        for q in K.declared_range(kind):
            n = q if q in K.TARGET_GRID else 2
            a_wordings = W.target_wordings(n)
            expected = tuple(
                w.replace(f" {n} ", f" {q} ").replace(K.TARGET_WORD, marker)
                for w in a_wordings)
            assert W.family_wordings(kind, q) == expected, (kind, q)
            for a, r in zip(a_wordings, W.family_wordings(kind, q)):
                changed = [(x, y) for x, y in zip(a.split(), r.split())
                           if x != y]
                for x, y in changed:
                    assert (x.strip(".") == K.TARGET_WORD
                            and y.strip(".") == marker) \
                        or (x == str(n) and y == str(q)), (kind, q, x, y)


def test_a_and_the_markers_share_grammatical_number():
    for kind in ("A",) + K.TIER1_FAMILY_IDS:
        assert all(" 1 time" in w and "times" not in w
                   for w in W.wordings(kind, 1))
        assert all(" 2 times" in w for w in W.wordings(kind, 2))


# ------------------------------------------------------- number everywhere

def test_no_registered_wording_pairs_a_numeral_with_the_wrong_number():
    checked = W.assert_grammatical_number()
    assert set(checked) == {"A", "B"} | set(K.FAMILIES)
    expected = 4 * (len(K.TARGET_GRID) + len(K.focal_severities(extended=True))
                    + sum(len(K.declared_range(f)) for f in K.FAMILIES))
    assert sum(checked.values()) == expected


@pytest.mark.parametrize("text,q", [
    ("Your answer must use exactly 1 semicolons.", 1),
    ("At most 1 words may begin with b.", 1),
    ("At least 1 words must end with y.", 1),
    ("Use at most 1 upper-case English letters.", 1),
    ("Use exactly 1 semicolon characters in your answer.", 1),
    ("At most 1 word contain a doubled letter.", 1),
    ("Your answer must use exactly 2 semicolon.", 2),
    ("At most 2 words contains a doubled letter.", 2),
    ("At most 0 word may begin with b.", 0),
])
def test_the_checker_catches_the_defects_it_exists_for(text, q):
    assert W.grammatical_number_defects(text, q)


@pytest.mark.parametrize("text,q", [
    ("Use 1 or more words ending with y.", 1),
    ("At most 1 percent of words begin with b.", 1),
    ("Words ending with y: 1 percent at least.", 1),
    ("At most 0 words may begin with b.", 0),
    ("Use the word however exactly 1 time.", 1),
    ("Use the word thus exactly 2 times.", 2),
    ("Every word in the answer must have at most 7 letters.", 7),
    ("At most 1 word contains the letter a.", 1),
    ("Use at most 1 word containing the letter a.", 1),
    ("At most 2 words contain the letter a.", 2),
    ("Keep commas to 1 per hundred words.", 1),
    ("Limit words beginning with b to 1.", 1),
])
def test_the_checker_accepts_correct_english(text, q):
    assert W.grammatical_number_defects(text, q) == []


@pytest.mark.parametrize("kind,q,index,expected", [
    ("XC1", 1, 0, "Your answer must use exactly 1 semicolon."),
    ("XC1", 2, 0, "Your answer must use exactly 2 semicolons."),
    ("XC1", 1, 1, "Use exactly 1 semicolon character in your answer."),
    ("XC2", 1, 2, "Exactly 1 comma must appear in your answer."),
    ("XC3", 1, 0, "Your answer must have exactly 1 sentence."),
    ("XC3", 3, 0, "Your answer must have exactly 3 sentences."),
    ("RF12", 1, 0, "Your answer may use at most 1 sentence."),
    ("RF12", 8, 3, "Do not write more than 8 sentences."),
    ("RF4", 1, 0, "At most 1 word contains a doubled letter."),
    ("RF4", 0, 0, "At most 0 words contain a doubled letter."),
    ("RF4", 2, 2, "No more than 2 words contain a doubled letter."),
    ("RF7", 1, 1, "Use at most 1 word containing the letter a."),
    ("RF6", 1, 0, "Use at most 1 upper-case English letter."),
    ("RF5", 1, 3, "Do not use more than 1 comma character."),
    ("RF1", 1, 0, "At most 1 word may begin with b."),
    ("RF1", 0, 0, "At most 0 words may begin with b."),
    ("RF9", 1, 2, "No more than 1 word may start with t."),
    ("CL8", 1, 0, "At least 1 word must end with y."),
    ("CL8", 1, 2, "Use 1 or more words ending with y."),
    ("CL8", 2, 3, "Your answer needs 2 words ending with y."),
    ("CR5", 1, 0, "Use at most 1 comma per hundred words."),
    ("CR12", 1, 1, "At most 1 sentence per hundred words."),
    ("PS1", 1, 0, "Use exactly 1 capitalised word in your answer."),
    ("PS2", 1, 0, "Use at least 1 semicolon in your answer."),
    ("PS2", 1, 3, "Include at least 1 semicolon character in your answer."),
    ("PS3", 2, 0, "Words ending with y: 2 percent at least."),
    ("MK1", 1, 0, "Use the word thus exactly 1 time."),
    ("A", 1, 0, "Use the word however exactly 1 time."),
])
def test_rendered_wordings_at_the_singular_and_plural_boundary(
        kind, q, index, expected):
    assert W.wording(kind, index, q) == expected


# ----------------------------------------------- what the change preserved

def test_the_rf_wordings_are_v4r2s_except_for_number_at_q_1():
    differences = W.assert_rf_wordings_are_carried()
    assert set(differences) == set(V4_TEMPLATES)
    for items in differences.values():
        for item in items:
            assert item["v4r2"] != item["rendered"]
            assert W.grammatical_number_defects(item["v4r2"], 1)
            assert not W.grammatical_number_defects(item["rendered"], 1)
    for family, templates in V4_TEMPLATES.items():
        for q in K.declared_range(family):
            if q != 1:
                assert W.family_wordings(family, q) == \
                    tuple(t.format(q=q) for t in templates)


def test_number_placeholders_move_no_word_count():
    """A numeral is not an alphabetic run and ``s`` adds none, so §7.5's
    caliper and §12.6's expansion premise are untouched."""
    W.assert_severity_invariance()
    W.assert_rule_vocabulary()
    assert len(W.assert_caliper_feasible()) == len(K.FAMILIES)
    assert W.number_fields(1) == {"s": "", "v": "s"}
    assert W.number_fields(0) == {"s": "s", "v": ""}
    assert W.number_fields(2) == {"s": "s", "v": ""}


def test_one_verifier_still_decides_all_four_wordings():
    result = wording_suite.run_wording_suite()
    assert result["disagreements"] == [] if "disagreements" in result \
        else result
