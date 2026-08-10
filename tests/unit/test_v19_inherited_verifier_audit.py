"""The section 14.2 audit of the inherited Pair 2 and Pair 3 verifiers.

"Pair 2 and Pair 3 existing verifier code may be reused only after hash/semantic
audit." This file is that audit, in four parts:

  * DIFFERENTIAL. The v19 adapters are run against a broad fixture bank and their
    verdicts compared with the inherited `binary_pass` on every case. The claim
    being tested is that the *verdict* is preserved exactly and only the
    representation changes, so any disagreement is an audit failure rather than a
    fixture to update.
  * SEMANTIC. Hand-authored PASS/FAIL/malformed cases with the reason each verdict
    follows from the frozen rule.
  * BOUNDARY and PROPERTY. At and either side of each decision boundary, and one
    scientific feature perturbed at a time with the expected change pinned.
  * DEFECTS. The three defects the audit demonstrated, pinned as tests so they
    cannot be quietly fixed or quietly forgotten. Section 10.6 requires a
    demonstrated defect to be repaired and re-audited before freeze, which is why
    `verifiers.inherited_reuse_decision` is a pending decision and not a
    conclusion drawn here.
"""
import pytest

from dci.v19 import verifiers as V
from dci.v19.verifiers import (
    Compliance,
    GenerationState,
    Scoring,
    Verdict,
    VerifierContractError,
)
from dci.verifiers import rules

pytestmark = pytest.mark.cpu

ZERO_WIDTH = "\u200b"
CYRILLIC_A = "а"


# A deliberately broad bank: clean cases, malformed cases, chat preambles,
# truncation shapes, Unicode, code fences, line-ending variants and empties - the
# audit material section 10.6 enumerates.
BANK = (
    "", "   ", "\n\n", "Sure!", "I cannot help with that.",
    "One sentence.", "One. Two.", "One. Two. Three.", "One. Two. Three. Four.",
    "Short. A bit longer here. Longer still by some margin.",
    "Longer still by some margin. A bit longer here. Short.",
    "Equal words here. Equal words here.",
    "- alpha\n- beta gamma\n- delta epsilon zeta",
    "1. alpha\n2. beta gamma",
    "Here is my answer:\nOne. Two. Three.",
    "The answer is 42. Or maybe 43!  Who knows?",
    "Mr. Smith went to Washington. He stayed.",
    "e.g. this is one. And another.",
    "alpha beta gamma", "alpha alpha beta", "alpha Alpha beta",
    "café café", "café cafe", f"wo{ZERO_WIDTH}rd word",
    f"{CYRILLIC_A}pple apple", "naive naïve",
    "```\ncode block\n```", "line one\r\nline two",
    "It's a test. Don't stop.", "A—dash. Another; clause.",
    "?!?", "42", "42 42",
    "Unique words only in this phrase", "the the",
    "A. B. C. D. E.",
)

MANDATORY_SETS = (("alpha",), ("alpha", "beta"), ("café",), ("word",),
                  ("apple",), ("one", "two", "three"), ("missing",))


# --------------------------------------------------------------- DIFFERENTIAL
@pytest.mark.parametrize("text", BANK)
def test_pair_two_focal_agrees_with_the_inherited_verdict(text):
    inherited = rules.v_unique_words(text)
    adapted = V.verify_all_words_unique(text)
    assert adapted.scoring is Scoring.SCORED, adapted.reason
    assert adapted.f_a == int(not inherited.binary_pass), text


@pytest.mark.parametrize("text", BANK)
@pytest.mark.parametrize("words", MANDATORY_SETS)
def test_pair_two_target_agrees_with_the_inherited_verdict(text, words):
    inherited = rules.v_require_word_set(text, words)
    adapted = V.verify_mandatory_words(text, mandatory_words=words)
    assert adapted.scoring is Scoring.SCORED, adapted.reason
    assert adapted.f_a == int(not inherited.binary_pass), (text, words)


@pytest.mark.parametrize("text", BANK)
@pytest.mark.parametrize("n", [1, 2, 3, 5])
def test_pair_three_target_agrees_with_the_inherited_verdict(text, n):
    inherited = rules.v_exact_sentence_count(text, n)
    adapted = V.verify_exact_sentence_count(text, n_sentences=n)
    assert adapted.scoring is Scoring.SCORED, adapted.reason
    assert adapted.f_a == int(not inherited.binary_pass), (text, n)


@pytest.mark.parametrize("text", BANK)
def test_pair_three_focal_agrees_with_the_inherited_verdict(text):
    inherited = rules.v_increasing_lengths(text)
    adapted = V.verify_increasing_lengths(text)
    assert adapted.scoring is Scoring.SCORED, adapted.reason
    assert adapted.f_a == int(not inherited.binary_pass), text


@pytest.mark.parametrize("text", BANK)
def test_only_the_representation_changed_not_the_verdict(text):
    """The audit's central claim, stated once over the whole bank.

    `unscorable` moves out of the compliance field and becomes a generation
    state; the compliance level keeps its three inherited values; the binary
    verdict is untouched.
    """
    inherited = rules.v_exact_sentence_count(text, 2)
    adapted = V.verify_exact_sentence_count(text, n_sentences=2)
    if inherited.status == "unscorable":
        assert adapted.generation_state in (GenerationState.UNPARSEABLE,
                                            GenerationState.EMPTY)
        assert adapted.compliance is Compliance.VIOLATION
        assert adapted.verdict is Verdict.FAIL
    else:
        assert adapted.compliance.value.lower() == inherited.status
        assert adapted.generation_state is GenerationState.SCORABLE


# ------------------------------------------------------------------- SEMANTIC
@pytest.mark.parametrize("text,verdict,why", [
    ("alpha beta gamma", Verdict.PASS, "three distinct tokens"),
    ("alpha alpha", Verdict.FAIL, "the same token twice"),
    ("alpha Alpha", Verdict.FAIL, "tokens are case-folded before comparison"),
    ("It's fine, it's fine", Verdict.FAIL,
     "the apostrophe is inside the word pattern, so both tokens are \"it's\""),
    ("42 42", Verdict.FAIL, "digits are word characters under the frozen pattern"),
])
def test_pair_two_focal_semantics(text, verdict, why):
    assert V.verify_all_words_unique(text).verdict is verdict, why


@pytest.mark.parametrize("text,words,verdict,why", [
    ("alpha and beta", ("alpha", "beta"), Verdict.PASS, "both words present"),
    ("Alpha and Beta", ("alpha", "beta"), Verdict.PASS, "matching is case-folded"),
    ("alpha only", ("alpha", "beta"), Verdict.FAIL, "beta is absent"),
    ("alphabet soup", ("alpha",), Verdict.FAIL,
     "matching is on whole tokens, not substrings"),
])
def test_pair_two_target_semantics(text, words, verdict, why):
    got = V.verify_mandatory_words(text, mandatory_words=words)
    assert got.verdict is verdict, why


@pytest.mark.parametrize("text,verdict,why", [
    ("A. Two words. Three words here.", Verdict.PASS,
     "word counts 1, 2, 3 strictly increase"),
    ("Three words here. Two words. A.", Verdict.FAIL, "the lengths decrease"),
    ("Two words. Two words.", Verdict.FAIL,
     "equal is not an increase; the frozen rule is strict"),
])
def test_pair_three_focal_semantics(text, verdict, why):
    assert V.verify_increasing_lengths(text).verdict is verdict, why


def test_the_focal_rule_is_strict_increase_not_non_decreasing():
    """`v_nondecreasing_lengths` exists inherited and is a different rule."""
    equal = "Two words. Two words."
    assert V.verify_increasing_lengths(equal).verdict is Verdict.FAIL
    assert rules.v_nondecreasing_lengths(equal).binary_pass == 1
    assert "strictly increase" in V.P3_FOCAL_SPEC.rule


# ------------------------------------------------------------------- BOUNDARY
@pytest.mark.parametrize("required", [1, 2, 3, 4, 5])
def test_the_sentence_count_boundary_at_n_minus_one_n_and_n_plus_one(required):
    for observed in range(max(1, required - 1), required + 2):
        text = " ".join(f"Sentence number {i}." for i in range(observed))
        got = V.verify_exact_sentence_count(text, n_sentences=required)
        assert got.verdict is (Verdict.PASS if observed == required
                               else Verdict.FAIL), (observed, required)


@pytest.mark.parametrize("n_words", [1, 2, 3, 8])
def test_the_mandatory_word_count_boundary(n_words):
    """One word short of the required set fails; the full set passes."""
    words = tuple(f"token{i}" for i in range(n_words))
    assert V.verify_mandatory_words(
        " ".join(words), mandatory_words=words).verdict is Verdict.PASS
    if n_words > 1:
        assert V.verify_mandatory_words(
            " ".join(words[:-1]), mandatory_words=words).verdict is Verdict.FAIL


@pytest.mark.parametrize("length", [2, 3, 4, 6])
def test_the_monotone_length_boundary_at_equality(length):
    """Equality is the boundary: n then n passes nothing, n then n+1 passes."""
    first = " ".join("w" for _ in range(length)) + "."
    equal = first + " " + " ".join("x" for _ in range(length)) + "."
    longer = first + " " + " ".join("x" for _ in range(length + 1)) + "."
    shorter = first + " " + " ".join("x" for _ in range(length - 1)) + "."
    assert V.verify_increasing_lengths(equal).verdict is Verdict.FAIL
    assert V.verify_increasing_lengths(longer).verdict is Verdict.PASS
    assert V.verify_increasing_lengths(shorter).verdict is Verdict.FAIL


def test_uniqueness_at_the_two_token_boundary():
    assert V.verify_all_words_unique("a b").verdict is Verdict.PASS
    assert V.verify_all_words_unique("a a").verdict is Verdict.FAIL


# ------------------------------------------------------------------- PROPERTY
@pytest.mark.parametrize("n", range(2, 7))
def test_merging_two_sentences_reduces_the_count_by_exactly_one(n):
    sentences = [f"Sentence number {i}." for i in range(n)]
    base = " ".join(sentences)
    merged = " ".join(["Sentence number 0 and " + sentences[1].lower()]
                      + sentences[2:])
    assert V.verify_exact_sentence_count(base, n_sentences=n).verdict is Verdict.PASS
    assert V.verify_exact_sentence_count(
        merged, n_sentences=n).verdict is Verdict.FAIL
    assert V.verify_exact_sentence_count(
        merged, n_sentences=n - 1).verdict is Verdict.PASS


@pytest.mark.parametrize("n", range(2, 7))
def test_splitting_one_sentence_raises_the_count_by_exactly_one(n):
    base = " ".join(f"Sentence number {i} here." for i in range(n))
    split = base.replace("Sentence number 0 here.", "Sentence zero. Here it is.", 1)
    assert V.verify_exact_sentence_count(base, n_sentences=n).verdict is Verdict.PASS
    assert V.verify_exact_sentence_count(
        split, n_sentences=n + 1).verdict is Verdict.PASS


@pytest.mark.parametrize("n", range(2, 8))
def test_duplicating_exactly_one_word_breaks_uniqueness(n):
    words = [f"token{i}" for i in range(n)]
    assert V.verify_all_words_unique(" ".join(words)).verdict is Verdict.PASS
    for index in range(n):
        broken = words + [words[index]]
        assert V.verify_all_words_unique(
            " ".join(broken)).verdict is Verdict.FAIL, index


@pytest.mark.parametrize("drop", range(4))
def test_removing_exactly_one_mandatory_word_fails_the_target(drop):
    words = tuple(f"token{i}" for i in range(4))
    kept = [w for i, w in enumerate(words) if i != drop]
    assert V.verify_mandatory_words(
        " ".join(kept), mandatory_words=words).verdict is Verdict.FAIL
    assert V.verify_mandatory_words(
        " ".join(words), mandatory_words=words).verdict is Verdict.PASS


@pytest.mark.parametrize("position", range(3))
def test_violating_exactly_one_length_inequality_fails(position):
    lengths = [1, 2, 3, 4]
    lengths[position], lengths[position + 1] = (lengths[position + 1],
                                                lengths[position])
    text = " ".join(" ".join("w" for _ in range(k)) + "." for k in lengths)
    assert V.verify_increasing_lengths(text).verdict is Verdict.FAIL


# ---------------------------------------------------- the shared parser (Pair 3)
def test_the_target_and_focal_verifiers_share_the_sentence_segmentation():
    """Section 4.4's principal measurement risk, made attributable."""
    assert V.P3_TARGET_SPEC.span == "sentence_segmentation"
    assert V.P3_FOCAL_SPEC.span.startswith("sentence_segmentation")
    segmentation = V.inherited_segmentation()
    assert V.P3_TARGET_SPEC.segmentation == segmentation
    assert V.P3_FOCAL_SPEC.segmentation == segmentation


@pytest.mark.parametrize("text,segments", [
    ("One. Two. Three.", 3),
    ("One! Two? Three.", 3),
    ("One.Two.Three.", 1),                        # no space: one segment
    ("Mr. Smith went home. He stayed.", 3),       # the abbreviation splits
    ("One\nTwo\nThree", 3),                       # newlines segment too
    ("- One\n- Two\n- Three", 3),                 # list markers are stripped
])
def test_a_segmentation_level_perturbation_is_visible_in_the_parse(text, segments):
    """Both Pair 3 verdicts follow this one function, so it is asserted directly."""
    assert len(rules.split_sentences(text)) == segments, text
    got = V.verify_exact_sentence_count(text, n_sentences=segments)
    assert got.verdict is Verdict.PASS
    assert got.evidence["detail"]["observed"] == segments


def test_a_conversational_preamble_changes_the_observed_count():
    """Section 4.4: preambles can affect both verdicts through segmentation."""
    bare = "Short. A bit longer. Longer than that one."
    with_preamble = "Sure, here you go. " + bare
    assert V.verify_exact_sentence_count(bare, n_sentences=3).verdict is Verdict.PASS
    assert V.verify_exact_sentence_count(
        with_preamble, n_sentences=3).verdict is Verdict.FAIL
    # And the focal verdict moves with it, from the same cause.
    assert V.verify_increasing_lengths(bare).verdict is Verdict.PASS
    assert V.verify_increasing_lengths(with_preamble).verdict is Verdict.FAIL


# --------------------------------------------------------------- THE DEFECTS
#
# Demonstrated, not hypothetical. Each is pinned so the audit's findings cannot
# drift, and section 10.6 requires each to be repaired and re-audited before
# freeze - which is why the reuse decision stays open.

def test_defect_a_zero_width_space_satisfies_the_uniqueness_rule():
    """A repeated word passes the focal rule if a zero-width space splits it."""
    assert rules.word_tokens(f"wo{ZERO_WIDTH}rd word") == ["wo", "rd", "word"]
    assert V.verify_all_words_unique(
        f"wo{ZERO_WIDTH}rd word").verdict is Verdict.PASS
    assert V.verify_all_words_unique("word word").verdict is Verdict.FAIL


def test_defect_a_homoglyph_also_satisfies_the_uniqueness_rule():
    assert V.verify_all_words_unique(
        f"{CYRILLIC_A}pple apple").verdict is Verdict.PASS
    assert V.verify_all_words_unique("apple apple").verdict is Verdict.FAIL


def test_defect_a_non_ascii_mandatory_word_can_never_be_matched():
    """Section 4.3: an impossible realisation is outside the estimand."""
    for text in ("café", "Café", "un café noir"):
        assert V.verify_mandatory_words(
            text, mandatory_words=("café",)).verdict is Verdict.FAIL, text
    assert V.verify_mandatory_words(
        "cafe", mandatory_words=("cafe",)).verdict is Verdict.PASS


def test_defect_a_bullet_list_scores_as_exactly_n_sentences():
    """The Pair 1 / Pair 3 coupling: one regex decides both spans."""
    bullets = "- alpha\n- beta gamma\n- delta epsilon zeta"
    assert V.verify_exact_sentence_count(
        bullets, n_sentences=3).verdict is Verdict.PASS
    assert V.verify_increasing_lengths(bullets).verdict is Verdict.PASS
    assert "•" in rules.LIST_MARKER.pattern


def test_the_defects_are_recorded_in_the_specification_audit_prose():
    assert "zero-width" in V.P2_FOCAL_SPEC.audit
    assert "non-ASCII" in V.P2_TARGET_SPEC.audit
    assert "bullet list" in V.P3_TARGET_SPEC.audit


def test_the_reuse_decision_is_still_open_because_of_them():
    """Section 10.6: a demonstrated defect requires repair and re-audit."""
    from dci.v19.registry import REGISTRY
    slot = REGISTRY.slots["verifiers.inherited_reuse_decision"]
    assert slot.pending and slot.status == "BLOCKED_BY_PROSPECTIVE_DECISION"
    assert "zero-width space" in slot.note and "homoglyph" in slot.note


# --------------------------------------------------- technical scoring states
@pytest.mark.parametrize("bad", [None, 0, -1, "3", 2.5, True])
def test_a_missing_sentence_count_is_not_a_behavioural_failure(bad):
    got = V.verify_exact_sentence_count("One. Two.", n_sentences=bad)
    assert got.scoring is Scoring.MISSING_METADATA
    with pytest.raises(VerifierContractError):
        _ = got.f_a


@pytest.mark.parametrize("bad", [None, (), "alpha", ("",), (1,)])
def test_a_missing_mandatory_word_set_is_not_a_behavioural_failure(bad):
    got = V.verify_mandatory_words("alpha", mandatory_words=bad)
    assert got.scoring is Scoring.MISSING_METADATA
    assert got.verdict is None


def test_an_empty_segment_is_a_failure_with_the_state_preserved():
    got = V.verify_exact_sentence_count("", n_sentences=2)
    assert got.verdict is Verdict.FAIL and got.f_a == 1
    assert got.generation_state is GenerationState.EMPTY


def test_an_unparseable_segment_is_distinguished_from_an_empty_one():
    got = V.verify_exact_sentence_count("?!?", n_sentences=2)
    assert got.generation_state is GenerationState.UNPARSEABLE
    assert got.verdict is Verdict.FAIL


def test_a_caller_supplied_truncation_survives_the_adapter():
    got = V.verify_exact_sentence_count("One. Two.", n_sentences=2,
                                        delivered_state=GenerationState.TRUNCATED)
    assert got.generation_state is GenerationState.TRUNCATED
    assert got.verdict is Verdict.PASS


def test_an_inherited_result_that_contradicts_itself_is_a_verifier_defect():
    """Reported, not resolved by preferring one of the two fields."""
    class Contradictory:
        status, binary_pass, continuous_score, detail = "violation", 1, 0.0, {}

    got = V._inherited_outcome(V.P2_FOCAL_SPEC, {}, Contradictory(), "text",
                               GenerationState.SCORABLE, exact=False)
    assert got.scoring is Scoring.VERIFIER_ERROR
    assert "disagree" in got.reason and got.verdict is None


def test_an_unscorable_result_claiming_a_pass_is_a_verifier_defect():
    class Impossible:
        status, binary_pass, continuous_score, detail = "unscorable", 1, 0.0, {}

    got = V._inherited_outcome(V.P3_TARGET_SPEC, {}, Impossible(), "text",
                               GenerationState.SCORABLE, exact=True)
    assert got.scoring is Scoring.VERIFIER_ERROR
    assert "cannot both hold" in got.reason
