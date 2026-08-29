"""v8: A and MK1--MK8 are counted by one function, and what that changes.

Three obligations. (1) The unification is structural: A's numerator and every
marker numerator are the same function object bound to different words.
(2) Behaviour is preserved everywhere v7's two rules agreed --- every frozen
boundary expectation, the wording-suite corpus, and the whole Unicode range
except U+0130 --- and the divergence on U+0130 is exactly the one the change
was made for, in the stated direction. (3) The scoring path uses it.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import InstrumentError
from dci1v4.verifiers.target import s0_count
from dci1v7.verifiers import boundary as B7
from dci1v7.verifiers import compliance as C7
from dci1v7.verifiers import statistics as S7
from dci1v7.verifiers import verifier_source_hash as v7_hash
from dci1v7.verifiers.constraints import Constraint, MARKER_WORDS, TARGET_WORD
from dci1v7.verifiers.wording_suite import SUITE_RESPONSES

from dci1v8.verifiers import verifier_source_hash as v8_hash
from dci1v8.verifiers import compliance as C8
from dci1v8.verifiers import statistics as S8
from dci1v8.verifiers.words import (
    assert_marker_word, case_folding_splitters, count_marker,
)

I_DOT = "İ"          # İ, the one case-folding splitter
ACUTE = "́"          # combining acute accent
SHY = "­"            # soft hyphen
ZWSP = "​"           # zero-width space
NBSP = " "


# ------------------------------------------------------ (1) one function

def test_a_and_every_marker_family_share_the_counting_function():
    assert S8.TARGET_STATISTIC.func is count_marker
    assert S8.TARGET_STATISTIC.keywords == {"marker": TARGET_WORD}
    for statistic_id, word in MARKER_WORDS.items():
        counter = S8.MARKER_STATISTICS[statistic_id]
        assert counter.func is count_marker
        assert counter.keywords == {"marker": word}
    assert S8.statistic_for(Constraint("A", 3)) is S8.TARGET_STATISTIC
    assert S8.statistic_for(Constraint("MK1", 3)) is S8.MARKER_STATISTICS["marker_thus"]


def test_the_fourteen_non_marker_numerators_are_v7s_own():
    for statistic_id, fn in S8.CARRIED_STATISTICS.items():
        assert statistic_id not in MARKER_WORDS
        assert fn is S7.STATISTICS[statistic_id]
    assert len(S8.CARRIED_STATISTICS) == 14


@pytest.mark.parametrize("bad", ["", "However", "over-all", "thus far",
                                 "thus.", "ｔｈｕｓ".upper(), "1thus"])
def test_a_marker_that_no_word_could_equal_is_refused(bad):
    with pytest.raises(InstrumentError):
        assert_marker_word(bad)
    with pytest.raises(InstrumentError):
        count_marker("thus thus", bad)


# --------------------------------------------- (2) regression: the rule

CASES = [
    # case
    ("However, however; HOWEVER.", "however", 3),
    ("THUS Thus tHuS thus", "thus", 4),
    ("Overall,", "overall", 1),
    # punctuation and separators
    ("(however)", "however", 1),
    ("hence hence, hence; hence.", "hence", 4),
    ("“however”, he said.", "however", 1),
    ("however\nhowever\thowever", "however", 3),
    (f"however{NBSP}however", "however", 2),
    ("however2however", "however", 2),
    ("thus's", "thus", 1),
    ("然而 however 然而", "however", 1),
    # hyphens
    ("over-all", "overall", 0),
    ("how-ever", "however", 0),
    ("thus-far", "thus", 1),
    ("though-provoking", "though", 1),
    (f"however{SHY}however", "however", 2),
    (f"thus{ZWSP}thus", "thus", 2),
    # substrings never count
    ("howevers", "however", 0),
    ("thowever", "however", 0),
    ("howeverhowever", "however", 0),
    ("Howeverhowever", "however", 0),
    ("thusly", "thus", 0),
    ("henceforth", "hence", 0),
    ("whence", "hence", 0),
    ("although", "though", 0),
    ("overalls", "overall", 0),
    ("indeedy", "indeed", 0),
    ("insteadly", "instead", 0),
    ("namelycheck", "namely", 0),
    ("h o w e v e r", "however", 0),
    ("ｈｏｗｅｖｅｒ", "however", 0),
    ("Ｈowever", "however", 0),
    # combining characters end a run
    (f"however{ACUTE} rain", "however", 1),
    (f"how{ACUTE}ever", "however", 0),
    (f"thus{ACUTE} thus", "thus", 2),
    (f"t{ACUTE}hus", "thus", 0),
    # empty and wordless
    ("", "however", 0),
    ("  \n\t ", "thus", 0),
    (",,,", "hence", 0),
]


@pytest.mark.parametrize("text,marker,expected", CASES)
def test_count_marker_regression(text, marker, expected):
    assert count_marker(text, marker) == expected


@pytest.mark.parametrize("text,marker,expected", CASES)
def test_v8_marker_count_agrees_with_v7_marker_count(text, marker, expected):
    """The eight MK numerators are unchanged: v7 already used the lexical
    rule for them. A's numerator now agrees with them on every case here."""
    assert S7.marker_count(text, marker) == expected
    if I_DOT not in text:
        assert count_marker(text, "however") == s0_count(text)


# U+0130: the one place the two v7 rules disagreed, and the direction v8 takes.
I_DOT_CASES = [
    # text, marker, v8 (unified, lexical), v7-A (fold-first s0) on 'however'
    (f"{I_DOT}however", "however", 0, 1),
    # a trailing İ folds to `i` + U+0307, so fold-first reads `howeveri`:
    # both rules give 0 and the divergence is one-directional
    (f"however{I_DOT}", "however", 0, 0),
    (f"{I_DOT}HOWEVER", "however", 0, 1),
    (f"{I_DOT}however however", "however", 1, 2),
    (f"{I_DOT} however", "however", 1, 1),
    (f"{I_DOT}stanbul however", "however", 1, 1),
    (f"{I_DOT}{I_DOT}{I_DOT}", "however", 0, 0),
]


@pytest.mark.parametrize("text,marker,v8_expected,v7_s0", I_DOT_CASES)
def test_u0130_adjacent_to_the_marker_no_longer_counts(text, marker,
                                                       v8_expected, v7_s0):
    assert count_marker(text, marker) == v8_expected
    assert s0_count(text) == v7_s0                       # v7's A, unchanged
    # and MK was already lexical: 'thus' in the same position behaves as v8 A
    thus_text = text.replace("however", "thus").replace("HOWEVER", "THUS")
    assert count_marker(thus_text, "thus") == v8_expected
    assert S7.marker_count(thus_text, "thus") == v8_expected


def test_u0130_is_the_only_code_point_that_separates_the_two_rules():
    """Whole-Unicode differential: prefix and suffix every code point to the
    marker; the lexical rule and the fold-first rule disagree on U+0130 alone.
    """
    assert case_folding_splitters() == (I_DOT,)
    disagree = set()
    for codepoint in range(0x110000):
        ch = chr(codepoint)
        for text in (ch + "however", "however" + ch, ch + " however"):
            if count_marker(text, "however") != s0_count(text):
                disagree.add(ch)
                break
    assert disagree == {I_DOT}


# -------------------------------- (2) regression: the frozen expectations

def test_every_frozen_a_expectation_is_preserved():
    """The 48 carried A cases (v3's forty and v4's eight) carry an s0 column;
    none contains U+0130, so the unified counter reproduces all of them."""
    assert B7.CARRIED_TARGET_CASES
    for case in B7.CARRIED_TARGET_CASES:
        assert I_DOT not in case["text"], case["case_id"]
        assert count_marker(case["text"], "however") == case["s0"], case["case_id"]
        assert s0_count(case["text"]) == case["s0"], case["case_id"]


def test_every_frozen_marker_expectation_is_preserved():
    """Every boundary case with frozen marker statistics --- v4r3's, R3's and
    v5's authored marker cases --- scores identically under the shared
    function, including the two cases that contain U+0130."""
    checked = 0
    for case in B7.ALL_CASES:
        stats = case.get("stats") or {}
        for statistic_id, word in MARKER_WORDS.items():
            if statistic_id in stats:
                assert S8.STATISTICS[statistic_id](case["text"]) == stats[statistic_id], \
                    (case["case_id"], word)
                checked += 1
    assert checked > 100


def test_wording_suite_corpus_verdicts_are_unchanged_for_a():
    """The twenty-response wording corpus (which contains `İstanbul is big`)
    scores A identically under both rules: the İ there is not adjacent to
    the marker."""
    for text in SUITE_RESPONSES:
        assert count_marker(text, "however") == s0_count(text)


# ------------------------------------------------- (3) the scoring path

def test_score_generation_scores_a_through_the_shared_function():
    text = f"{I_DOT}however however"
    a1 = Constraint("A", 1)
    v8 = C8.score_generation(text, present=[a1]).scores[0]
    v7 = C7.score_generation(text, present=[a1]).scores[0]
    assert (v8.statistic, v8.passed) == (1, True)
    assert (v7.statistic, v7.passed) == (2, False)
    # the same text with the marker swapped scores identically in both
    mk = Constraint("MK1", 1)
    thus = text.replace("however", "thus")
    assert C8.score_generation(thus, present=[mk]).scores[0].statistic == 1
    assert C7.score_generation(thus, present=[mk]).scores[0].statistic == 1


def test_score_generation_matches_v7_off_u0130():
    present = [Constraint("A", 3), Constraint("MK3", 2)]
    absent = [Constraint("B", 9), Constraint("RF1", 2), Constraint("XC1", 1)]
    for text in list(SUITE_RESPONSES) + [t for t, _, _ in CASES]:
        a = C8.score_generation(text, present=present, absent=absent)
        b = C7.score_generation(text, present=present, absent=absent)
        assert a == b


def test_graded_vacuity_and_presence_rules_are_v7s():
    assert C8.passes is C7.passes and C8.graded is C7.graded
    assert C8.non_vacuous is C7.non_vacuous
    assert C8.assert_presence_rule is C7.assert_presence_rule


def test_the_v8_verifier_hash_is_new_and_stable():
    assert v8_hash() == v8_hash()
    assert v8_hash() != v7_hash()
