"""Stage 152 — migrated from notebook cell 152.py (verifiers).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/152.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.verifiers.rules import VerificationResult, split_sentences, v_alliteration, v_alphabetical_starts, v_caps_sentence_count, v_caps_word, v_comma_and_min_words, v_commas_per_sentence, v_distinct_integers, v_exact_char_total, v_exact_integer_count, v_exact_sentence_count, v_forbid_word_set, v_increasing_lengths, v_integer_sum, v_long_word_each_sentence, v_max_integer_count, v_min_integer_count, v_min_long_words_per_sentence, v_min_sentence_words, v_no_char, v_no_digits, v_no_suffix, v_nondecreasing_lengths, v_paren_pairs, v_percent_count, v_question_sentence_count, v_quote_pairs, v_require_word, v_require_word_set, v_semicolon_each, v_sentence_ends_long, v_sentence_initial, v_sentence_initial_forbidden_word, v_unique_words, v_vowel_words_per_sentence, v_word_band  # noqa: F401























# =================================================== sentence-scoped verifiers


























# ====================================================== whole-text verifiers




























# ================================================= bridge-family verifiers
# Sentence-scoped by design. Each reads WITHIN sentences or counts sentences
# carrying a property; none reads the total number of sentences and none
# compares one sentence with another. Both claims are proved behaviourally by
# the count-invariance and order-invariance probes below.


















# ============================================== rule-family dispatch table
# The family name dispatches BOTH the verifier and the paraphrase templates.
# A constraint whose family is missing from either table raises at import, so
# a wording and the check it describes cannot drift apart.
VERIFIER_FACTORY: dict[str, Callable[..., Callable[[str], VerificationResult]]] = {
    "exact_sentence_count": lambda n: (lambda t: v_exact_sentence_count(t, n)),
    "increasing_lengths": lambda: v_increasing_lengths,
    "nondecreasing_lengths": lambda: v_nondecreasing_lengths,
    "sentence_initial_letter": lambda letter: (lambda t: v_sentence_initial(t, letter)),
    "min_words_per_sentence": lambda n: (lambda t: v_min_sentence_words(t, n)),
    "alphabetical_starts": lambda: v_alphabetical_starts,
    "long_word_per_sentence": lambda letters: (lambda t: v_long_word_each_sentence(t, letters)),
    "sentence_ends_long": lambda letters: (lambda t: v_sentence_ends_long(t, letters)),
    "commas_per_sentence": lambda n: (lambda t: v_commas_per_sentence(t, n)),
    "n_long_words_per_sentence": lambda letters, n: (
        lambda t: v_min_long_words_per_sentence(t, letters, n)),
    "word_band_per_sentence": lambda low, high: (lambda t: v_word_band(t, low, high)),
    "semicolon_per_sentence": lambda: v_semicolon_each,
    "comma_and_min_words": lambda n: (lambda t: v_comma_and_min_words(t, n)),
    "unique_words": lambda: v_unique_words,
    "integer_sum": lambda count, total: (lambda t: v_integer_sum(t, count, total)),
    "distinct_integers": lambda count: (lambda t: v_distinct_integers(t, count)),
    "forbid_word_set": lambda words: (lambda t: v_forbid_word_set(t, words)),
    "require_word_set": lambda words: (lambda t: v_require_word_set(t, words)),
    "require_word": lambda word: (lambda t: v_require_word(t, word)),
    "no_suffix": lambda suffix: (lambda t: v_no_suffix(t, suffix)),
    "alliteration": lambda letter, n: (lambda t: v_alliteration(t, letter, n)),
    "caps_word": lambda n, letters: (lambda t: v_caps_word(t, n, letters)),
    "exact_char_total": lambda char, n: (lambda t: v_exact_char_total(t, char, n)),
    "no_char": lambda char: (lambda t: v_no_char(t, char)),
    "paren_pairs": lambda n: (lambda t: v_paren_pairs(t, n)),
    "quote_pairs": lambda n: (lambda t: v_quote_pairs(t, n)),
    "exact_integer_count": lambda n: (lambda t: v_exact_integer_count(t, n)),
    "min_integer_count": lambda n: (lambda t: v_min_integer_count(t, n)),
    "max_integer_count": lambda n: (lambda t: v_max_integer_count(t, n)),
    "no_digits": lambda: v_no_digits,
    # bridge family
    "vowel_words_per_sentence": lambda n: (lambda t: v_vowel_words_per_sentence(t, n)),
    "caps_sentence_count": lambda n, letters: (
        lambda t: v_caps_sentence_count(t, n, letters)),
    "sentence_initial_forbidden_word": lambda word: (
        lambda t: v_sentence_initial_forbidden_word(t, word)),
    "question_sentence_count": lambda n: (lambda t: v_question_sentence_count(t, n)),
    "percent_count": lambda n: (lambda t: v_percent_count(t, n)),
}

_missing_family = sorted({c.rule_family for c in S.CONSTRAINTS.values()}
                         - set(VERIFIER_FACTORY))
assert not _missing_family, f"rule families without a verifier: {_missing_family}"

VERIFIERS: dict[str, Callable[[str], VerificationResult]] = {
    cid: VERIFIER_FACTORY[c.rule_family](**c.param_dict)
    for cid, c in S.CONSTRAINTS.items()
}
assert set(VERIFIERS) == set(S.CONSTRAINTS), "Every constraint needs a verifier."


def verify(text: str, constraint_id: str) -> VerificationResult:
    return VERIFIERS[constraint_id](text)
S.verify = verify


# ===================================================== pathway audit probes
S._REAL_SPLIT = split_sentences
_PROBE_TEXT = ('Consider PUMPS. Pressure pushes past packed pores; pumps '
               'persist: "steady flow" (mostly) 40 60 and 12% evidence '
               'threshold gradual.')
_BRIDGE_PASSING = {
    "U_BRG_VOWEL3": ("An open estimate arrives early. Every autumn an old "
                     "estimate is available. Under an inch of open air, "
                     "estimates arrive early anyway."),
    "U_BRG_CAPS1": ("Rivers rise slowly. The NASA report is clear. Levels "
                    "settle again."),
    "U_BRG_NOTHE": ("Rivers rise slowly. Levels settle again. Water finds a "
                    "path."),
    "U_BRG_QMARK": ("Rivers rise slowly. What follows next? Levels settle "
                    "again."),
}


def _forbidden_split(_text: Any) -> list[str]:
    raise AssertionError("a whole-text verifier reached split_sentences")


# 1. Whole-answer unrelated targets must never segment at all.
_WHOLE_TEXT_U = [u for u in S.U_CANDIDATE_IDS if S.CONSTRAINTS[u].u_family != "bridge"]
import dci.verifiers.rules as _rules_mod
_rules_mod.split_sentences = _forbidden_split  # noqa  (temporary probe)
try:
    for _uid in _WHOLE_TEXT_U:
        VERIFIERS[_uid](_PROBE_TEXT)
finally:
    _rules_mod.split_sentences = S._REAL_SPLIT


def count_invariance_probe(constraint_id: str, passing_text: str,
                           neutral_sentence: str) -> bool:
    """Adding a declared neutral sentence must not change the verdict.

    A rule that reads the total number of sentences, which is exactly what A
    does, cannot survive this. It is the behavioural form of the claim that a
    bridge target carries no direct A pathway.
    """
    before = S.verify(passing_text, constraint_id).binary_pass
    after = S.verify(passing_text.rstrip() + " " + neutral_sentence,
                   constraint_id).binary_pass
    return before == after


def order_invariance_probe(constraint_id: str, passing_text: str) -> bool:
    """Reversing sentence order must not change the verdict.

    A rule that compares one sentence with another, which is exactly what B
    does, cannot survive this.
    """
    sentences = S._REAL_SPLIT(passing_text)
    if len(sentences) < 2:
        return True
    reordered = " ".join(reversed([s if s.endswith((".", "!", "?")) else s + "."
                                   for s in sentences]))
    return (S.verify(passing_text, constraint_id).binary_pass
            == S.verify(reordered, constraint_id).binary_pass)


S.BRIDGE_PROBE_TABLE = []
for _uid in S.BRIDGE_IDS:
    _text = _BRIDGE_PASSING[_uid]
    _base = S.verify(_text, _uid)
    _count_ok = count_invariance_probe(_uid, _text, S.CONSTRAINTS[_uid].count_probe_sentence)
    _order_ok = order_invariance_probe(_uid, _text)
    S.BRIDGE_PROBE_TABLE.append({
        "constraint_id": _uid, "passes_reference_text": bool(_base.binary_pass),
        "count_invariant": _count_ok, "order_invariant": _order_ok})
    assert _base.binary_pass == 1, (
        f"{_uid}: the declared reference text must satisfy the rule, or neither "
        "probe means anything")
    assert _count_ok, (
        f"{_uid} changes verdict when a neutral sentence is appended, so it "
        "reads the sentence count and carries a direct A pathway. Reject it "
        "rather than documenting the pathway away.")
    assert _order_ok, (
        f"{_uid} changes verdict when sentence order is reversed, so it "
        "compares across sentences and carries a direct B pathway.")

# Control: A and B must FAIL these probes. If they passed, the probes would be
# vacuous and would certify anything.
assert not count_invariance_probe(
    S.CFG.target_id, "One here. Two here. Three here. Four here.", S.NEUTRAL_A), (
    "the count-invariance probe does not detect A itself and is therefore vacuous")
assert not order_invariance_probe(
    S.CFG.focal_id, "Birds fly. Small birds fly swiftly. "
                  "Many small birds fly swiftly above wide fields."), (
    "the order-invariance probe does not detect B itself and is therefore vacuous")

print(f"{len(VERIFIERS)} verifiers built from {len(VERIFIER_FACTORY)} rule families.")
print(f"{len(_WHOLE_TEXT_U)} whole-answer unrelated targets ran with sentence "
      "segmentation disabled: none reads a sentence boundary.")
print(f"{len(S.BRIDGE_IDS)} bridge targets passed count-invariance and "
      "order-invariance; A and B both fail those probes, so they are not vacuous.")
display(pd.DataFrame(S.BRIDGE_PROBE_TABLE))
