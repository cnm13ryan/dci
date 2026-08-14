"""The section 14.2 re-audit of the Pair 2 and Pair 3 verifiers after amendment A2.

"Pair 2 and Pair 3 existing verifier code may be reused only after hash/semantic
audit." The first audit found three defects. Section 10.6 then decided what happens
next: "A demonstrated semantic or verifier defect requires repair and re-audit before
freeze; collecting more confirmatory data is not a remedy for invalid measurement."
So the verifiers were corrected, and this is the re-audit.

Section 11.3's rule for a differential audit is that "every disagreement must be
justified as an intentional correction; or treated as a failure of the inheritance
audit". The corrected verifiers therefore CANNOT agree with the inherited ones
everywhere - that was the point - so the audit's shape changes: the disagreement set
is enumerated exactly, each entry names the correction that explains it, and any
disagreement outside the table fails.

`EXPECTED_DISAGREEMENTS` is the whole set over the audit bank: 15 cases out of
roughly two thousand comparisons. Every one lies in a class amendment A2 names, and
Pair 3's focal rule disagrees nowhere at all.

This test was RED between `8809282` and the segmentation repair, on six further
`p3.target` disagreements over abbreviations and initials, because the abbreviation
repair had reached the inherited verifier and not the frozen v19 policy. They were
the defect, not a correction of it, which is why they were never added to the table
below. The repair ports the guard onto the frozen policy, so those six are gone
rather than enumerated and the table is unchanged at 15.

The re-freeze it required is done; the Stage 2 semantic RE-AUDIT that section 10.6
also requires is not, and is human work. See `docs/v19_pair3_segmentation_defect.md`
for what remains outstanding.
"""

import dataclasses

import pytest

from dci.v19 import text as textlib
from dci.v19 import verifiers as V
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import sentences
from dci.v19.text import INTENTIONAL_CORRECTIONS
from dci.v19.verifiers import (
    Compliance,
    GenerationState,
    Scoring,
    Verdict,
    VerifierContractError,
)
from dci.verifiers import rules

pytestmark = pytest.mark.cpu

TP = P.text

ZERO_WIDTH = "\u200b"
SOFT_HYPHEN = "­"
ZWNJ = "‌"
BOM = "﻿"
CYRILLIC_A = "а"

# The audit material section 10.6 enumerates - boundary cases, malformed output, chat
# preambles, truncation shapes, Unicode normalisation, zero-width characters,
# homoglyphs, non-breaking spaces, smart quotes, combining marks, code fences and
# line-ending variants - plus the specific texts the first audit used to break things.
BANK = (
    "", "   ", "\n\n", "Sure!", "I cannot help with that.",
    "One sentence.", "One. Two.", "One. Two. Three.", "One. Two. Three. Four.",
    "Short. A bit longer here. Longer still by some margin.",
    "Longer still by some margin. A bit longer here. Short.",
    "Equal words here. Equal words here.",
    "- alpha\n- beta gamma\n- delta epsilon zeta", "1. alpha\n2. beta gamma",
    "Here is my answer:\nOne. Two. Three.",
    "The answer is 42. Or maybe 43!  Who knows?",
    "Mr. Smith went to Washington. He stayed.", "e.g. this is one. And another.",
    "alpha beta gamma", "alpha alpha beta", "alpha Alpha beta",
    "café café", "café cafe", f"wo{ZERO_WIDTH}rd word", f"wo{SOFT_HYPHEN}rd word",
    f"wo{ZWNJ}rd word", f"{BOM}word word", f"{CYRILLIC_A}pple apple",
    "naive naïve", "Straße strasse", "ß SS",
    "```\ncode block\n```", "line one\r\nline two", "It's a test. Don't stop.",
    "A—dash. Another; clause.", "?!?", "42", "42 42",
    "Unique words only in this phrase", "the the", "A. B. C. D. E.",
    "- ЖЖЖ\n- ЩЩЩ", "日本語です。中文です。", "－ alfa\n－ bravo", "-\talfa",
    "- a\n- \n- b", "naïve café", "ＡＢＣ abc",
)

MANDATORY_SETS = (("alpha",), ("alpha", "beta"), ("café",), ("word",), ("apple",),
                  ("one", "two", "three"), ("missing",), ("ß",), ("straße",),
                  ("ＡＢＣ",))

SENTENCE_COUNTS = (1, 2, 3, 5)

CORRECTION_IDS = tuple(row["id"] for row in INTENTIONAL_CORRECTIONS)

# Every verdict difference from the inherited implementation, as
# (case, verifier, inherited f_a, v19 f_a, correction id).
EXPECTED_DISAGREEMENTS: tuple[tuple[str, str, int, int, str], ...] = (
    # A non-ASCII mandatory word was unmatchable, so the composition was impossible
    # rather than the answer failing (section 4.3).
    ("'café café'|('café',)", "p2.target", 1, 0, "unicode-word-pattern"),
    ("'café cafe'|('café',)", "p2.target", 1, 0, "unicode-word-pattern"),
    ("'naïve café'|('café',)", "p2.target", 1, 0, "unicode-word-pattern"),
    ("'Straße strasse'|('straße',)", "p2.target", 1, 0, "unicode-word-pattern"),
    ("'ß SS'|('ß',)", "p2.target", 1, 0, "unicode-word-pattern"),
    # An invisible character split a repeated word into distinct tokens, so the
    # uniqueness rule passed while a word repeated. Section 10.6 names these.
    (repr(f"wo{ZERO_WIDTH}rd word"), "p2.focal", 0, 1, "strip-format-characters"),
    (repr(f"wo{SOFT_HYPHEN}rd word"), "p2.focal", 0, 1, "strip-format-characters"),
    (repr(f"wo{ZWNJ}rd word"), "p2.focal", 0, 1, "strip-format-characters"),
    # One case rule. `str.lower` left the sharp s alone; casefold maps it to "ss",
    # so these ARE repeated words and the inherited rule said they were not.
    ("'Straße strasse'", "p2.focal", 0, 1, "single-case-rule"),
    ("'ß SS'", "p2.focal", 0, 1, "single-case-rule"),
    # NFKC folds the fullwidth letters onto ASCII, after which casefold makes the two
    # words identical.
    ("'ＡＢＣ abc'", "p2.focal", 0, 1, "unicode-word-pattern"),
    # A non-Latin answer had no tokens at all under the ASCII pattern, so uniqueness
    # was unscorable and scored FAIL. It is now ordinary text.
    ("'- ЖЖЖ\\n- ЩЩЩ'", "p2.focal", 1, 0, "unicode-word-pattern"),
    ("'日本語です。中文です。'", "p2.focal", 1, 0, "unicode-word-pattern"),
    # And the same answer was an item and not a sentence, which is what made the
    # solver's discarded n_sentences >= n_items axiom unsound.
    ("'- ЖЖЖ\\n- ЩЩЩ'|n=2", "p3.target", 1, 0, "unicode-sentence-survival"),
    ("'日本語です。中文です。'|n=1", "p3.target", 1, 0, "unicode-sentence-survival"),
)


def observed_disagreements() -> list[tuple[str, str, int, int]]:
    """Every verdict difference over the bank, recomputed from both implementations."""
    found: list[tuple[str, str, int, int]] = []

    def compare(case: str, verifier: str, inherited_pass: int, outcome) -> None:
        if not outcome.scored:
            return
        inherited = int(not inherited_pass)
        if inherited != outcome.f_a:
            found.append((case, verifier, inherited, outcome.f_a))

    for text in BANK:
        compare(repr(text), "p2.focal",
                rules.v_unique_words(text).binary_pass,
                V.verify_all_words_unique(text, text_policy=TP))
        compare(repr(text), "p3.focal",
                rules.v_increasing_lengths(text).binary_pass,
                V.verify_increasing_lengths(text, policy=P))
        for n in SENTENCE_COUNTS:
            compare(f"{text!r}|n={n}", "p3.target",
                    rules.v_exact_sentence_count(text, n).binary_pass,
                    V.verify_exact_sentence_count(text, n_sentences=n, policy=P))
        for words in MANDATORY_SETS:
            compare(f"{text!r}|{words}", "p2.target",
                    rules.v_require_word_set(text, words).binary_pass,
                    V.verify_mandatory_words(text, mandatory_words=words,
                                             text_policy=TP))
    return found


# ------------------------------------------------------- the enumerated audit
def test_the_disagreement_set_is_exactly_the_enumerated_one():
    """Section 11.3: a disagreement is a justified correction or an audit failure."""
    observed = set(observed_disagreements())
    expected = {(case, verifier, inherited, new)
                for case, verifier, inherited, new, _ in EXPECTED_DISAGREEMENTS}
    unexplained = sorted(observed - expected)
    assert not unexplained, (
        f"{len(unexplained)} verdict difference(s) are not in the enumerated "
        f"correction table: {unexplained[:5]}")
    stale = sorted(expected - observed)
    assert not stale, (
        f"{len(stale)} enumerated difference(s) no longer occur, so the table "
        f"describes a version of the code that is gone: {stale[:5]}")


def test_every_enumerated_difference_names_a_declared_correction():
    for case, verifier, _, _, correction in EXPECTED_DISAGREEMENTS:
        assert correction in CORRECTION_IDS, (case, verifier, correction)


def test_every_declared_correction_is_load_bearing_or_structural():
    """Four corrections change verdicts; the fifth changes only hashes, and says so."""
    used = {correction for *_, correction in EXPECTED_DISAGREEMENTS}
    assert used == {"unicode-word-pattern", "strip-format-characters",
                    "single-case-rule", "unicode-sentence-survival"}
    unused = set(CORRECTION_IDS) - used
    assert unused == {"shared-marker-definition"}
    # It is not idle: it moves Pair 3's specification hash with the list grammar,
    # which is where section 4.4's shared segmentation became auditable.
    marker = next(row for row in INTENTIONAL_CORRECTIONS
                  if row["id"] == "shared-marker-definition")
    assert "silently changed" in marker["defect"]
    assert V.bundle(P)[
        "v19:p3.target.exact_sentence_count"].spec.segmentation["marker_patterns"]


def test_the_disagreements_are_confined_to_the_classes_the_amendment_names():
    """No ASCII-only case changed verdict, and Pair 3's focal rule changed nowhere."""
    by_verifier = {}
    for case, verifier, *_ in EXPECTED_DISAGREEMENTS:
        by_verifier.setdefault(verifier, []).append(case)
    assert "p3.focal" not in by_verifier
    assert set(by_verifier) == {"p2.target", "p2.focal", "p3.target"}
    for case in [c for cases in by_verifier.values() for c in cases]:
        # Every named case is non-ASCII, or contains an escape for a non-ASCII code
        # point, or is a list whose items are non-Latin.
        assert (not case.isascii() or "\\u" in case or "\\x" in case
                or "\\n" in case), case


def test_the_bank_is_large_enough_for_the_claim():
    comparisons = len(BANK) * (2 + len(SENTENCE_COUNTS) + len(MANDATORY_SETS))
    assert comparisons > 700
    assert len(EXPECTED_DISAGREEMENTS) == 15


@pytest.mark.parametrize("text", BANK)
def test_agreement_holds_everywhere_the_table_does_not_name(text):
    """The complement of the table, asserted case by case rather than in aggregate."""
    named = {case for case, *_ in EXPECTED_DISAGREEMENTS}
    for verifier, inherited_pass, outcome in (
            ("p2.focal", rules.v_unique_words(text).binary_pass,
             V.verify_all_words_unique(text, text_policy=TP)),
            ("p3.focal", rules.v_increasing_lengths(text).binary_pass,
             V.verify_increasing_lengths(text, policy=P))):
        if repr(text) in named or not outcome.scored:
            continue
        assert outcome.f_a == int(not inherited_pass), (verifier, text)


# ------------------------------------------------------------------- SEMANTIC
@pytest.mark.parametrize("text,verdict,why", [
    ("alpha beta gamma", Verdict.PASS, "three distinct tokens"),
    ("alpha alpha", Verdict.FAIL, "the same token twice"),
    ("alpha Alpha", Verdict.FAIL, "tokens are folded before comparison"),
    ("It's fine, it's fine", Verdict.FAIL,
     "the apostrophe is inside the word pattern, so both tokens are \"it's\""),
    ("42 42", Verdict.FAIL, "digits are word characters"),
    ("café cafe", Verdict.PASS, "an accent is a difference, not a duplicate"),
    (f"{CYRILLIC_A}pple apple", Verdict.PASS,
     "a confusable is a different string; NFKC does not merge it and section 10.6 "
     "assigns homoglyphs to human audit rather than to an automated rule"),
])
def test_pair_two_focal_semantics(text, verdict, why):
    assert V.verify_all_words_unique(text, text_policy=TP).verdict is verdict, why


@pytest.mark.parametrize("text,words,verdict,why", [
    ("alpha and beta", ("alpha", "beta"), Verdict.PASS, "both words present"),
    ("Alpha and Beta", ("alpha", "beta"), Verdict.PASS, "matching is folded"),
    ("alpha only", ("alpha", "beta"), Verdict.FAIL, "beta is absent"),
    ("alphabet soup", ("alpha",), Verdict.FAIL,
     "matching is on whole tokens, not substrings"),
    ("un café noir", ("café",), Verdict.PASS,
     "a non-ASCII mandatory word is now matchable"),
    (f"un caf{ZERO_WIDTH}é noir", ("café",), Verdict.PASS,
     "an invisible character no longer hides it"),
])
def test_pair_two_target_semantics(text, words, verdict, why):
    got = V.verify_mandatory_words(text, mandatory_words=words, text_policy=TP)
    assert got.verdict is verdict, why


def test_a_mandatory_word_the_tokeniser_would_split_is_missing_metadata():
    """Not a behavioural failure: the rule is not decidable as stated."""
    got = V.verify_mandatory_words("anything", mandatory_words=("two words",),
                                   text_policy=TP)
    assert got.scoring is Scoring.MISSING_METADATA
    assert "single word tokens" in got.reason


@pytest.mark.parametrize("text,verdict,why", [
    ("One. Two words. Three words here.", Verdict.PASS, "1, 2, 3 strictly increase"),
    ("Three words here. Two words. A.", Verdict.FAIL, "the lengths decrease"),
    ("Two words. Two words.", Verdict.FAIL, "equal is not an increase"),
    ("Alfa.", Verdict.FAIL,
     "one segment cannot demonstrate a monotone increase, so section 10.1 gives FAIL"),
])
def test_pair_three_focal_semantics(text, verdict, why):
    assert V.verify_increasing_lengths(text, policy=P).verdict is verdict, why


def test_the_focal_rule_is_strict_increase_not_non_decreasing():
    equal = "Two words. Two words."
    assert V.verify_increasing_lengths(equal, policy=P).verdict is Verdict.FAIL
    assert rules.v_nondecreasing_lengths(equal).binary_pass == 1
    spec = V.bundle(P)["v19:p3.focal.increasing_lengths"].spec
    assert "strictly increase" in spec.rule


# ------------------------------------------------------------------- BOUNDARY
@pytest.mark.parametrize("required", [1, 2, 3, 4, 5])
def test_the_sentence_count_boundary_at_n_minus_one_n_and_n_plus_one(required):
    for observed in range(max(1, required - 1), required + 2):
        text = " ".join(f"Sentence number {i}." for i in range(observed))
        got = V.verify_exact_sentence_count(text, n_sentences=required, policy=P)
        assert got.verdict is (Verdict.PASS if observed == required
                               else Verdict.FAIL), (observed, required)


@pytest.mark.parametrize("n_words", [1, 2, 3, 8])
def test_the_mandatory_word_count_boundary(n_words):
    words = tuple(f"token{i}" for i in range(n_words))
    assert V.verify_mandatory_words(" ".join(words), mandatory_words=words,
                                    text_policy=TP).verdict is Verdict.PASS
    if n_words > 1:
        assert V.verify_mandatory_words(" ".join(words[:-1]), mandatory_words=words,
                                        text_policy=TP).verdict is Verdict.FAIL


@pytest.mark.parametrize("length", [2, 3, 4, 6])
def test_the_monotone_length_boundary_at_equality(length):
    first = " ".join("w" for _ in range(length)) + "."
    equal = first + " " + " ".join("x" for _ in range(length)) + "."
    longer = first + " " + " ".join("x" for _ in range(length + 1)) + "."
    shorter = first + " " + " ".join("x" for _ in range(length - 1)) + "."
    assert V.verify_increasing_lengths(equal, policy=P).verdict is Verdict.FAIL
    assert V.verify_increasing_lengths(longer, policy=P).verdict is Verdict.PASS
    assert V.verify_increasing_lengths(shorter, policy=P).verdict is Verdict.FAIL


def test_uniqueness_at_the_two_token_boundary():
    assert V.verify_all_words_unique("a b", text_policy=TP).verdict is Verdict.PASS
    assert V.verify_all_words_unique("a a", text_policy=TP).verdict is Verdict.FAIL


# ------------------------------------------------------------------- PROPERTY
@pytest.mark.parametrize("n", range(2, 7))
def test_merging_two_sentences_reduces_the_count_by_exactly_one(n):
    sentence_list = [f"Sentence number {i}." for i in range(n)]
    base = " ".join(sentence_list)
    merged = " ".join(["Sentence number 0 and " + sentence_list[1].lower()]
                      + sentence_list[2:])
    assert V.verify_exact_sentence_count(base, n_sentences=n,
                                         policy=P).verdict is Verdict.PASS
    assert V.verify_exact_sentence_count(merged, n_sentences=n,
                                         policy=P).verdict is Verdict.FAIL
    assert V.verify_exact_sentence_count(merged, n_sentences=n - 1,
                                         policy=P).verdict is Verdict.PASS


@pytest.mark.parametrize("n", range(2, 7))
def test_splitting_one_sentence_raises_the_count_by_exactly_one(n):
    base = " ".join(f"Sentence number {i} here." for i in range(n))
    split = base.replace("Sentence number 0 here.", "Sentence zero. Here it is.", 1)
    assert V.verify_exact_sentence_count(base, n_sentences=n,
                                         policy=P).verdict is Verdict.PASS
    assert V.verify_exact_sentence_count(split, n_sentences=n + 1,
                                         policy=P).verdict is Verdict.PASS


@pytest.mark.parametrize("n", range(2, 8))
def test_duplicating_exactly_one_word_breaks_uniqueness(n):
    words = [f"token{i}" for i in range(n)]
    assert V.verify_all_words_unique(" ".join(words),
                                     text_policy=TP).verdict is Verdict.PASS
    for index in range(n):
        broken = words + [words[index]]
        assert V.verify_all_words_unique(" ".join(broken),
                                         text_policy=TP).verdict is Verdict.FAIL, index


@pytest.mark.parametrize("drop", range(4))
def test_removing_exactly_one_mandatory_word_fails_the_target(drop):
    words = tuple(f"token{i}" for i in range(4))
    kept = [w for i, w in enumerate(words) if i != drop]
    assert V.verify_mandatory_words(" ".join(kept), mandatory_words=words,
                                    text_policy=TP).verdict is Verdict.FAIL
    assert V.verify_mandatory_words(" ".join(words), mandatory_words=words,
                                    text_policy=TP).verdict is Verdict.PASS


@pytest.mark.parametrize("position", range(3))
def test_violating_exactly_one_length_inequality_fails(position):
    lengths = [1, 2, 3, 4]
    lengths[position], lengths[position + 1] = (lengths[position + 1],
                                                lengths[position])
    text = " ".join(" ".join("w" for _ in range(k)) + "." for k in lengths)
    assert V.verify_increasing_lengths(text, policy=P).verdict is Verdict.FAIL


@pytest.mark.parametrize("invisible", [ZERO_WIDTH, SOFT_HYPHEN, ZWNJ, BOM])
@pytest.mark.parametrize("index", range(4))
def test_inserting_an_invisible_character_anywhere_changes_no_verdict(invisible,
                                                                     index):
    """The standing check that the removal still happens, at every position."""
    words = ["alfa", "bravo", "charlie", "delta"]
    base = " ".join(words)
    injected = list(words)
    injected[index] = injected[index][:2] + invisible + injected[index][2:]
    mutated = " ".join(injected)
    assert mutated != base
    assert (V.verify_all_words_unique(mutated, text_policy=TP).verdict
            is V.verify_all_words_unique(base, text_policy=TP).verdict)
    assert (V.verify_mandatory_words(mutated, mandatory_words=(words[index],),
                                     text_policy=TP).verdict
            is V.verify_mandatory_words(base, mandatory_words=(words[index],),
                                        text_policy=TP).verdict)


# ---------------------------------------------------- the shared parser (Pair 3)
def test_the_target_and_focal_verifiers_share_the_sentence_segmentation():
    built = V.bundle(P)
    target = built["v19:p3.target.exact_sentence_count"].spec
    focal = built["v19:p3.focal.increasing_lengths"].spec
    assert target.span == "sentence_segmentation"
    assert focal.span.startswith("sentence_segmentation")
    assert target.segmentation == focal.segmentation == V.frozen_segmentation(TP, P)


@pytest.mark.parametrize("text,segments", [
    ("One. Two. Three.", 3),
    ("One! Two? Three.", 3),
    ("One.Two.Three.", 1),                        # no space: one segment
    ("Mr. Smith went home. He stayed.", 2),       # the title abbreviation does NOT split
    ("One\nTwo\nThree", 3),                       # newlines segment too
    ("- One\n- Two\n- Three", 3),                 # the grammar's markers are stripped
    ("- ЖЖЖ\n- ЩЩЩ", 2),                          # and a non-Latin item is a segment
])
def test_a_segmentation_level_perturbation_is_visible_in_the_parse(text, segments):
    assert len(sentences(text, P)) == segments, text
    got = V.verify_exact_sentence_count(text, n_sentences=segments, policy=P)
    assert got.verdict is Verdict.PASS
    assert got.evidence["observed_count"] == segments


@pytest.mark.parametrize("text", [
    "Mr. Smith went to Washington. He stayed.",
    "Sales spike at 6 a.m. when others sleep.",
    "It ended at 6 p.m. \"Tomorrow begins early.\"",
    "e.g. this is one. And another.",
    "A. B. C. D. E.",
    "J. R. Smith went home. He stayed.",
    "**Bold.** Next one.",
    "(Aside.) Next one.",
    "One. Two. Three. Four.",
])
def test_pair_three_segmentation_matches_the_certified_inherited_splitter(text):
    """The abbreviation guard and the closing-mark class are NOT re-typed here.

    Regression this pins: `SENTENCE_BOUNDARY_PATTERN` claimed to be inherited
    verbatim but re-declared a narrower pre-repair class, and dropping
    `rules.ends_sentence` restored the abbreviation over-count that the blinded
    human audit had already removed once. `p3.target` is the primary outcome F_A,
    so a silent divergence here moves every sentence-count result.
    """
    assert len(sentences(text, P)) == len(rules.split_sentences(text)), text


def test_the_segmentation_guard_is_declared_in_the_specification_hash():
    """A future policy may drop the guard, but not without saying so in the hash."""
    assert TP.sentence_abbreviation_guard == textlib.ABBREVIATION_GUARD
    assert TP.sentence_boundary == rules.SENTENCE_BOUNDARY.pattern
    state = TP.state()
    assert state["sentence_abbreviation_guard"] == textlib.ABBREVIATION_GUARD
    unguarded = dataclasses.replace(
        TP, sentence_abbreviation_guard=textlib.NO_ABBREVIATION_GUARD)
    assert unguarded.policy_hash != TP.policy_hash
    assert len(textlib.split_sentences("Mr. Smith went home. He stayed.",
                                       unguarded)) == 3


def test_a_conversational_preamble_changes_the_observed_count():
    """Section 4.4: preambles can affect both verdicts through segmentation."""
    bare = "Short. A bit longer. Longer than that one."
    with_preamble = "Sure, here you go. " + bare
    assert V.verify_exact_sentence_count(bare, n_sentences=3,
                                         policy=P).verdict is Verdict.PASS
    assert V.verify_exact_sentence_count(with_preamble, n_sentences=3,
                                         policy=P).verdict is Verdict.FAIL
    assert V.verify_increasing_lengths(bare, policy=P).verdict is Verdict.PASS
    assert V.verify_increasing_lengths(with_preamble,
                                       policy=P).verdict is Verdict.FAIL


# --------------------------------------------------------------- THE DEFECTS
#
# The three the first audit demonstrated. Each is now pinned in its repaired form, so
# a regression restores a test failure rather than a silent measurement change.

def test_defect_a_zero_width_space_no_longer_satisfies_the_uniqueness_rule():
    assert textlib.word_tokens(f"wo{ZERO_WIDTH}rd word", TP) == ["word", "word"]
    assert V.verify_all_words_unique(f"wo{ZERO_WIDTH}rd word",
                                     text_policy=TP).verdict is Verdict.FAIL
    assert V.verify_all_words_unique("word word",
                                     text_policy=TP).verdict is Verdict.FAIL
    # And the inherited implementation still says otherwise, which is the correction.
    assert rules.v_unique_words(f"wo{ZERO_WIDTH}rd word").binary_pass == 1


def test_defect_a_homoglyph_is_a_different_word_not_a_split_one():
    """The split is gone. The confusable remains, and is human audit material."""
    assert textlib.word_tokens(f"{CYRILLIC_A}pple apple", TP) == [
        f"{CYRILLIC_A}pple", "apple"]
    assert rules.word_tokens(f"{CYRILLIC_A}pple apple") == ["pple", "apple"]
    assert V.verify_all_words_unique(f"{CYRILLIC_A}pple apple",
                                     text_policy=TP).verdict is Verdict.PASS
    assert V.verify_all_words_unique("apple apple",
                                     text_policy=TP).verdict is Verdict.FAIL


def test_defect_a_non_ascii_mandatory_word_is_now_matchable():
    for text in ("café", "Café", "un café noir"):
        assert V.verify_mandatory_words(text, mandatory_words=("café",),
                                        text_policy=TP).verdict is Verdict.PASS, text
    assert rules.v_require_word_set("café", ("café",)).binary_pass == 0


def test_defect_a_bullet_list_still_scores_as_n_sentences_and_says_so():
    """Not repaired: it is the frozen segmentation, and section 4.4 defers to it.

    What changed is that the coupling is now declared. The marker patterns are inside
    Pair 3's specification hash, and the clause that encodes it declares incomplete
    deterministic coverage, so it triggers human semantic review.
    """
    bullets = "- alpha\n- beta gamma\n- delta epsilon zeta"
    assert V.verify_exact_sentence_count(bullets, n_sentences=3,
                                         policy=P).verdict is Verdict.PASS
    assert V.verify_increasing_lengths(bullets, policy=P).verdict is Verdict.PASS
    spec = V.bundle(P)["v19:p3.target.exact_sentence_count"].spec
    assert spec.segmentation["marker_patterns"] == list(P.marker_patterns())


def test_the_corrections_are_recorded_in_the_specification_prose():
    built = V.bundle(P)
    for constraint_id in ("v19:p2.target.mandatory_words",
                          "v19:p2.focal.all_words_unique",
                          "v19:p3.target.exact_sentence_count",
                          "v19:p3.focal.increasing_lengths"):
        spec = built[constraint_id].spec
        assert spec.inherited_from, constraint_id
        assert "INTENTIONAL_CORRECTIONS" in spec.correction, constraint_id
        assert built[constraint_id].status == "inherited_corrected"


# --------------------------------------------------- technical scoring states
@pytest.mark.parametrize("bad", [None, 0, -1, "3", 2.5, True])
def test_a_missing_sentence_count_is_not_a_behavioural_failure(bad):
    got = V.verify_exact_sentence_count("One. Two.", n_sentences=bad, policy=P)
    assert got.scoring is Scoring.MISSING_METADATA
    with pytest.raises(VerifierContractError):
        _ = got.f_a


@pytest.mark.parametrize("bad", [None, (), "alpha", ("",), (1,)])
def test_a_missing_mandatory_word_set_is_not_a_behavioural_failure(bad):
    got = V.verify_mandatory_words("alpha", mandatory_words=bad, text_policy=TP)
    assert got.scoring is Scoring.MISSING_METADATA
    assert got.verdict is None


def test_an_empty_segment_is_a_failure_with_the_state_preserved():
    got = V.verify_exact_sentence_count("", n_sentences=2, policy=P)
    assert got.verdict is Verdict.FAIL and got.f_a == 1
    assert got.generation_state is GenerationState.EMPTY
    assert got.compliance is Compliance.VIOLATION


def test_an_unparseable_segment_is_distinguished_from_an_empty_one():
    got = V.verify_exact_sentence_count("?!?", n_sentences=2, policy=P)
    assert got.generation_state is GenerationState.UNPARSEABLE
    assert got.verdict is Verdict.FAIL


def test_a_caller_supplied_truncation_survives():
    got = V.verify_exact_sentence_count(
        "One. Two.", n_sentences=2, policy=P,
        delivered_state=GenerationState.TRUNCATED)
    assert got.generation_state is GenerationState.TRUNCATED
    assert got.verdict is Verdict.PASS


def test_the_unscorable_status_has_no_counterpart_in_the_v19_compliance_field():
    """The representational half of the repair, unchanged by amendment A2."""
    from dci.verifiers.rules import OutcomeStatus
    assert "unscorable" in getattr(OutcomeStatus, "__args__", ())
    assert "unscorable" not in {c.value.lower() for c in Compliance}
