"""Every verifier family: valid, invalid, boundary, punctuation and
tokenisation, empty, truncated, vacuous, absent structure, both frames, and
agreement with an independent oracle."""
from __future__ import annotations

import random
import re
from collections import Counter

import pytest

from dci.batch1 import compatibility as COMPAT
from dci.batch1 import library as L
from dci.batch1 import verifiers as V

pytestmark = pytest.mark.cpu

BY_ID = L.constraint_by_id()
FILLER = ("Calm rivers carry cold water past old mills. Many people walk to "
          "work each day. Small shops open early near a stone square.")


def score(cid, text, **kw):
    c = BY_ID[cid]
    return V.score_constraint(c.cid, c.family.verifier_id, c.verifier_params(),
                              c.family.vacuity, text, present=True, **kw)


def passes(cid, text):
    c = BY_ID[cid]
    return V.VERIFIERS[c.family.verifier_id](text, **c.p).passed


# ------------------------------------------------------- every constraint

@pytest.mark.parametrize("cid", sorted(BY_ID))
def test_witness_complies_and_violation_fails(cid):
    c = BY_ID[cid]
    assert score(cid, COMPAT.build_witness(c)).compliant
    assert score(cid, COMPAT.violation_text(c)).verdict == "FAIL"


@pytest.mark.parametrize("cid", sorted(BY_ID))
def test_empty_and_truncated_responses_never_comply(cid):
    witness = COMPAT.build_witness(BY_ID[cid])
    empty = score(cid, "")
    assert empty.state == V.STATE_EMPTY and not empty.compliant
    assert score(cid, "   \n ").state == V.STATE_EMPTY
    truncated = score(cid, witness, truncated=True)
    assert truncated.state == V.STATE_TRUNCATED and truncated.scored
    assert truncated.verdict == "PASS" and not truncated.compliant


@pytest.mark.parametrize("cid", sorted(BY_ID))
def test_non_behavioural_rows_are_not_scored(cid):
    s = score(cid, "anything", behavioural=False)
    assert s.state == V.STATE_NON_BEHAVIOURAL and not s.scored
    assert s.verdict is None and not s.compliant


@pytest.mark.parametrize("cid", sorted(BY_ID))
def test_both_frames_reach_the_same_scorer(cid):
    c = BY_ID[cid]
    witness = COMPAT.build_witness(c)
    verdicts = {frame: V.score_constraint(
        c.cid, c.family.verifier_id, c.verifier_params(), c.family.vacuity,
        witness, present=True).verdict for frame in L.FRAMES}
    assert len(set(verdicts.values())) == 1


def test_a_verifier_exception_is_a_scoring_failure_not_a_fail():
    s = V.score_constraint("x", "b1.exact_word_count", {"word": "a"},
                           "forced_production", "text", present=True)
    assert not s.scored and s.verdict is None and "TypeError" in s.error


# ------------------------------------------------------------ exact counts

@pytest.mark.parametrize("text, expected", [
    ("Indeed, it is. It is indeed. INDEED.", 3),
    ("indeedy and indeed's", 1),            # whole word; apostrophe splits
    ("in-deed", 0),
    ("indeed​indeed", 2),              # zero-width space splits
    ("", 0),
])
def test_exact_word_count_tokenisation(text, expected):
    assert V.exact_word_count(text, word="indeed", n=0).statistic == expected


def test_exact_word_count_boundaries():
    two = FILLER + " Indeed, yes. Indeed, no."
    assert passes("ew.indeed.2", two)
    assert not passes("ew.indeed.2", two + " Indeed.")
    assert not passes("ew.indeed.2", FILLER + " Indeed.")
    assert passes("A.however.2", "However, x. However, y.")


def test_exact_word_count_needs_no_word_floor():
    s = score("ew.indeed.2", "Indeed. Indeed.")
    assert s.compliant and s.non_vacuous


def test_exact_char_count_reads_raw_characters():
    assert V.exact_char_count("a, b, c", char=",", n=2).passed
    assert V.exact_char_count("1,000 and 2,000", char=",", n=2).passed
    assert not V.exact_char_count("a，b", char=",", n=1).passed   # full-width
    assert V.exact_char_count("a; b", char=";", n=1).passed


def test_exact_sentence_count_uses_the_certified_segmentation():
    assert V.exact_sentence_count("Mr. Smith left. He waved. Then sat.",
                                  n=3).passed
    assert not V.exact_sentence_count("One. Two. Three. Four.", n=3).passed
    assert V.exact_sentence_count("Ends without a stop", n=1).passed


def test_exact_paragraph_count():
    assert V.exact_paragraph_count("One here.\n\nTwo here.", n=2).passed
    assert not V.exact_paragraph_count("One here.\nTwo here.", n=2).passed
    assert V.exact_paragraph_count("A.\n\n\n\nB.\n \nC.", n=3).passed


# ---------------------------------------------------- inclusion, prohibition

def test_include_words_requires_every_word_as_a_whole_word():
    assert passes("inc.window+garden", "A window and a Garden.")
    assert not passes("inc.window+garden", "Windows and gardens.")
    assert not passes("inc.window+garden", "A window only.")
    m = V.include_words("A window only.", words=("window", "garden"))
    assert m.detail["missing"] == ["garden"]


def test_forbid_words_and_vacuity():
    assert passes("pro.word.the", FILLER)
    assert not passes("pro.word.the", FILLER + " The end.")
    assert passes("pro.word.the", "Theory and thereby.")    # not the word
    short = score("pro.word.the", "Yes.")
    assert short.verdict == "PASS" and short.vacuous_pass and not short.compliant
    assert score("pro.word.the", FILLER).compliant


def test_forbid_letter_is_case_insensitive_and_reads_words_only():
    assert not passes("pro.letter.b", FILLER + " Bold.")
    assert not passes("pro.letter.b", FILLER + " a B c.")
    assert passes("pro.letter.z", FILLER)


# ------------------------------------------------------------- B and bounds

def test_b_boundary_and_vacuity():
    nine = FILLER + " Elephants wander."                 # longest: 9 letters
    assert V.max_word_length(nine, m=9).passed
    assert not V.max_word_length(nine, m=8).passed
    assert V.max_word_length("con​sequently", m=9).passed  # historical
    s = score("B.max8", "Short words.")
    assert s.verdict == "PASS" and s.vacuous_pass and not s.compliant
    assert score("B.max8", FILLER).compliant
    assert score("B.max8", "").verdict == "PASS"      # wordless passes; empty


def test_sentence_word_bounds():
    assert passes("nb.max12", FILLER)
    long = " ".join(["word"] * 13) + "."
    assert not passes("nb.max12", FILLER + " " + long.capitalize())
    assert not passes("nb.min10", FILLER)
    assert passes("nb.min10", " ".join(["Word"] + ["word"] * 9) + ".")
    assert score("nb.max20", "").state == V.STATE_EMPTY


# --------------------------------------------------------------- uniqueness

def test_no_repeated_words_counts_only_long_words():
    assert passes("unq.word5", "The cat and the dog ran home.")
    assert not passes("unq.word5", "Rivers flow. Rivers dry.")
    assert passes("unq.word5", "Rivers flow. River dries.")


def test_no_repeated_bigrams_spans_sentence_boundaries():
    assert not passes("unq.bigram", "of the sea. of the land.")
    assert not passes("unq.bigram", "Go home. Go home.")
    assert passes("unq.bigram", FILLER)


def test_distinct_openers_needs_the_stated_minimum():
    assert passes("unq.opener3", FILLER)
    assert not passes("unq.opener3", "One here. Two here.")
    assert not passes("unq.opener3", "The cat. The dog. A bird.")


# ----------------------------------------------------------------- ordering

def test_length_order_is_strict_and_needs_enough_sentences():
    inc = "Go now. We go now. We all go now. Then we all go now."
    assert passes("ord.inc4", inc)
    assert not passes("ord.inc4", "Go now. We go now. We all go now.")
    assert not passes("ord.inc4", "Go now. We go now. We go now. Then we all go.")
    assert not passes("ord.inc4", "One.")                 # never vacuous
    dec = "Then we all go now. We all go now. We go now. Go now."
    assert passes("ord.dec4", dec) and not passes("ord.inc4", dec)


def test_alphabetical_openers_is_strict():
    assert passes("ord.alpha4", "Ants go. Bees go. Cats go. Dogs go.")
    assert not passes("ord.alpha4", "Ants go. Ants go. Cats go. Dogs go.")
    assert not passes("ord.alpha4", "Bees go. Ants go. Cats go. Dogs go.")
    assert not passes("ord.alpha4", "Ants go. Bees go. Cats go.")


# --------------------------------------------------------------- relational

def test_chain_word():
    assert passes("rel.word3", "We saw the river. River water ran. Ran far.")
    assert not passes("rel.word3", "We saw the river. Water ran. Ran far.")
    assert not passes("rel.word3", "We saw the river. River water ran.")


def test_chain_letter_ignores_punctuation():
    assert passes("rel.letter3", "It was calm. Many sat. Then rain.")
    assert not passes("rel.letter3", "It was calm. Some sat. Then rain.")


def test_adjacent_shared_word():
    assert passes("rel.share4", "Rivers carry water. Water turns wheels. "
                                "Wheels grind grain.")
    assert not passes("rel.share4", "Rivers carry water. Mills turn. "
                                    "Wheels grind grain.")
    assert not passes("rel.share4", "Cat naps. Cat eats. Cat runs.")  # 4+ only


# ------------------------------------------------------------------- oracles

def _rng_texts(n=400):
    vocab = ["indeed", "Indeed", "however", "the", "The", "cat", "dog",
             "garden", "window", "bright", "zebra", "big", "a", "of"]
    seps = [" ", " ", ", ", "; ", ". ", "! ", "\n", "\n\n", " - "]
    rng = random.Random(7)
    for _ in range(n):
        parts = []
        for _ in range(rng.randint(0, 30)):
            parts += [rng.choice(vocab), rng.choice(seps)]
        yield "".join(parts)


def _oracle_words(text):
    return [w.lower() for w in re.findall(r"[^\W\d_]+", text)]


def test_counting_verifiers_agree_with_independent_oracles():
    for text in _rng_texts():
        words = _oracle_words(text)
        counts = Counter(words)
        assert V.exact_word_count(text, word="indeed", n=1).statistic == \
            counts["indeed"]
        assert V.forbid_words(text, words=("the",)).passed == (counts["the"] == 0)
        assert V.include_words(text, words=("garden", "window")).passed == \
            (counts["garden"] > 0 and counts["window"] > 0)
        assert V.forbid_letter(text, letter="z").passed == ("z" not in "".join(words))
        assert V.max_word_length(text, m=6).statistic == \
            max((len(w) for w in words), default=0)
        long = Counter(w for w in words if len(w) >= 5)
        assert V.no_repeated_words(text, min_letters=5).passed == \
            all(c == 1 for c in long.values())
        bigrams = Counter(zip(words, words[1:]))
        assert V.no_repeated_bigrams(text).passed == \
            all(c == 1 for c in bigrams.values())
        assert V.exact_char_count(text, char=",", n=0).statistic == text.count(",")


def test_bundle_hash_is_stable_and_names_every_verifier():
    assert V.verifier_bundle_hash() == V.verifier_bundle_hash()
    assert len({V.verifier_implementation_hash(v) for v in V.VERIFIERS}) == \
        len(V.VERIFIERS)
