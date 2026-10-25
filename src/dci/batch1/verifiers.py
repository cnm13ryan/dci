"""Deterministic verifiers for the Batch 1 library, and the scoring contract.

Every family is a pure function ``text, **parameters -> Measurement``. The
words, sentences and paragraphs they read come from ``text.py`` and nowhere
else, so the 51 candidates, A and B share one segmentation.

The scoring contract follows the v19 verifier architecture
(``dci.v19.verifiers``): the behavioural verdict, the generation state and
the scoring state are separate fields, a verifier exception is a scoring
failure and never a FAIL, and every record says why. It is a Batch 1-native
contract rather than an import because ``VerifierSpec`` refuses identifiers
that are not ``v19:``.

**Compliance** (design decision D04, proposed): a response complies with a
constraint when the verdict is PASS, the response is neither empty nor
truncated, and it is non-vacuous. Non-vacuity is per family:

* ``forced_production`` --- the rule cannot be met by writing nothing (an
  exact count of at least one, a required word, an ordering or relation over
  a stated minimum of sentences), so non-empty and untruncated suffices;
* ``min_words`` --- the rule is met by writing little or nothing (B, the
  prohibitions, the uniqueness rules, the sentence-length bounds), so the
  response must also hold at least ``NON_VACUITY_MIN_WORDS`` words, the
  historical DCI-1 floor (``dci1v7/verifiers/compliance.py``).

Historically a vacuous pass stayed a pass; here it is recorded and is not
compliance. A PASS that is not compliance names its one reason
(``pass_excluded_by``): ``vacuous`` (a scorable answer under the word
floor), ``truncated`` or ``empty``. So literal compliance (the verdict) and
the primary measure (``compliant``) can both be recomputed from the stored
record, and truncation is never counted as vacuity.
"""
from __future__ import annotations

import inspect
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from dci.batch1 import text as T
from dci.provenance.hashes import sha, sha_file

__all__ = ["Measurement", "VERIFIERS", "VACUITY_RULES", "NON_VACUITY_MIN_WORDS",
           "STATE_SCORABLE", "STATE_EMPTY", "STATE_TRUNCATED",
           "STATE_NON_BEHAVIOURAL", "ConstraintScore", "score_constraint",
           "verifier_implementation_hash", "verifier_bundle_hash"]

#: The historical DCI-1 floor (v4r3 §9.3, carried to v8.1). A min-words
#: family's pass is vacuous below it.
NON_VACUITY_MIN_WORDS = 20

STATE_SCORABLE = "SCORABLE"
STATE_EMPTY = "EMPTY"
STATE_TRUNCATED = "TRUNCATED"
#: No behavioural answer stands behind the row. ``outcomes.classify`` keeps
#: such rows out of scoring altogether; the state remains for direct calls.
STATE_NON_BEHAVIOURAL = "NON_BEHAVIOURAL"

VACUITY_RULES = ("forced_production", "min_words")


@dataclass(frozen=True)
class Measurement:
    passed: bool
    statistic: Any
    detail: Mapping[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------ exact counts

def exact_word_count(text: str, *, word: str, n: int) -> Measurement:
    count = T.folded_words(text).count(word)
    return Measurement(count == n, count)


def exact_char_count(text: str, *, char: str, n: int) -> Measurement:
    count = T.char_count(text, char)
    return Measurement(count == n, count)


def exact_sentence_count(text: str, *, n: int) -> Measurement:
    count = len(T.sentences(text))
    return Measurement(count == n, count)


def exact_paragraph_count(text: str, *, n: int) -> Measurement:
    count = len(T.paragraphs(text))
    return Measurement(count == n, count)


# ------------------------------------------------------ inclusion, prohibition

def include_words(text: str, *, words: tuple[str, ...]) -> Measurement:
    present = set(T.folded_words(text))
    missing = [w for w in words if w not in present]
    return Measurement(not missing, len(words) - len(missing),
                       {"missing": missing})


def forbid_words(text: str, *, words: tuple[str, ...]) -> Measurement:
    counts = Counter(T.folded_words(text))
    found = {w: counts[w] for w in words if counts[w]}
    return Measurement(not found, sum(found.values()), {"found": found})


def forbid_letter(text: str, *, letter: str) -> Measurement:
    count = sum(w.count(letter) for w in T.folded_words(text))
    return Measurement(count == 0, count)


# ------------------------------------------------------------- B and bounds

def max_word_length(text: str, *, m: int) -> Measurement:
    longest = T.max_word_letters(text)
    over = sum(1 for w in T.words(text) if len(w) > m)
    return Measurement(longest <= m, longest, {"words_over": over})


def sentence_word_bound(text: str, *, bound: str, k: int) -> Measurement:
    lengths = [len(s) for s in T.sentence_words(text)]
    if bound == "max":
        bad = [n for n in lengths if n > k]
    elif bound == "min":
        bad = [n for n in lengths if n < k]
    else:
        raise ValueError(f"bound {bound!r} is not 'max' or 'min'")
    return Measurement(not bad, len(bad), {"lengths": lengths})


# --------------------------------------------------------------- uniqueness

def no_repeated_words(text: str, *, min_letters: int) -> Measurement:
    counts = Counter(w for w in T.folded_words(text) if len(w) >= min_letters)
    repeated = sorted(w for w, c in counts.items() if c > 1)
    return Measurement(not repeated, len(repeated), {"repeated": repeated})


def no_repeated_bigrams(text: str) -> Measurement:
    seq = T.folded_words(text)
    counts = Counter(zip(seq, seq[1:]))
    repeated = sorted(" ".join(b) for b, c in counts.items() if c > 1)
    return Measurement(not repeated, len(repeated), {"repeated": repeated})


def distinct_openers(text: str, *, min_sentences: int) -> Measurement:
    openers = [T.first_word(s) for s in T.sentences(text)]
    ok = len(openers) >= min_sentences and len(set(openers)) == len(openers)
    return Measurement(ok, len(openers), {"openers": openers})


# ----------------------------------------------------------------- ordering

def length_order(text: str, *, direction: str, min_sentences: int
                 ) -> Measurement:
    lengths = [len(s) for s in T.sentence_words(text)]
    pairs = list(zip(lengths, lengths[1:]))
    if direction == "increasing":
        ordered = all(b > a for a, b in pairs)
    elif direction == "decreasing":
        ordered = all(b < a for a, b in pairs)
    else:
        raise ValueError(f"direction {direction!r}")
    return Measurement(len(lengths) >= min_sentences and ordered, len(lengths),
                       {"lengths": lengths})


def alphabetical_openers(text: str, *, min_sentences: int) -> Measurement:
    openers = [T.first_word(s) for s in T.sentences(text)]
    ordered = all(b > a for a, b in zip(openers, openers[1:]))
    return Measurement(len(openers) >= min_sentences and ordered,
                       len(openers), {"openers": openers})


# --------------------------------------------------------------- relational

def chain_word(text: str, *, min_sentences: int) -> Measurement:
    spans = T.sentences(text)
    links = [T.first_word(b) == T.last_word(a) for a, b in zip(spans, spans[1:])]
    return Measurement(len(spans) >= min_sentences and all(links), len(spans),
                       {"links": links})


def chain_letter(text: str, *, min_sentences: int) -> Measurement:
    spans = T.sentences(text)
    links = [T.first_word(b)[:1] == T.last_word(a)[-1:]
             for a, b in zip(spans, spans[1:])]
    return Measurement(len(spans) >= min_sentences and all(links), len(spans),
                       {"links": links})


def adjacent_shared_word(text: str, *, min_sentences: int, min_letters: int
                         ) -> Measurement:
    sets = [{w for w in s if len(w) >= min_letters} for s in T.sentence_words(text)]
    links = [bool(a & b) for a, b in zip(sets, sets[1:])]
    return Measurement(len(sets) >= min_sentences and all(links), len(sets),
                       {"links": links})


#: verifier_id -> implementation. The id is what a constraint names; the
#: function's source enters that constraint's specification hash.
VERIFIERS: dict[str, Callable[..., Measurement]] = {
    "b1.exact_word_count": exact_word_count,
    "b1.exact_char_count": exact_char_count,
    "b1.exact_sentence_count": exact_sentence_count,
    "b1.exact_paragraph_count": exact_paragraph_count,
    "b1.include_words": include_words,
    "b1.forbid_words": forbid_words,
    "b1.forbid_letter": forbid_letter,
    "b1.max_word_length": max_word_length,
    "b1.sentence_word_bound": sentence_word_bound,
    "b1.no_repeated_words": no_repeated_words,
    "b1.no_repeated_bigrams": no_repeated_bigrams,
    "b1.distinct_openers": distinct_openers,
    "b1.length_order": length_order,
    "b1.alphabetical_openers": alphabetical_openers,
    "b1.chain_word": chain_word,
    "b1.chain_letter": chain_letter,
    "b1.adjacent_shared_word": adjacent_shared_word,
}


# ------------------------------------------------------------------ scoring

@dataclass(frozen=True)
class ConstraintScore:
    """One constraint scored on one response."""
    cid: str
    present: bool                # stated in the prompt (False = spontaneous)
    state: str                   # SCORABLE | EMPTY | TRUNCATED | NON_BEHAVIOURAL
    scored: bool                 # False on a verifier error or no answer
    verdict: str | None          # PASS | FAIL | None when not scored
    statistic: Any
    non_vacuous: bool
    compliant: bool
    #: Why a PASS is not compliance: "", "vacuous", "truncated" or "empty".
    pass_excluded_by: str = ""
    error: str = ""

    @property
    def vacuous_pass(self) -> bool:
        return self.pass_excluded_by == "vacuous"

    def row(self) -> dict[str, Any]:
        return {"cid": self.cid, "present": self.present, "state": self.state,
                "scored": self.scored, "verdict": self.verdict,
                "statistic": self.statistic, "non_vacuous": self.non_vacuous,
                "compliant": self.compliant,
                "pass_excluded_by": self.pass_excluded_by, "error": self.error}


def generation_state(text: Any, *, truncated: bool, behavioural: bool) -> str:
    if not behavioural:
        return STATE_NON_BEHAVIOURAL
    if text is None or not str(text).strip():
        return STATE_EMPTY
    if truncated:
        return STATE_TRUNCATED
    return STATE_SCORABLE


def score_constraint(cid: str, verifier_id: str, parameters: Mapping[str, Any],
                     vacuity: str, text: Any, *, present: bool,
                     truncated: bool = False, behavioural: bool = True
                     ) -> ConstraintScore:
    if vacuity not in VACUITY_RULES:
        raise ValueError(f"{cid}: vacuity rule {vacuity!r}")
    state = generation_state(text, truncated=truncated, behavioural=behavioural)
    if state == STATE_NON_BEHAVIOURAL:
        return ConstraintScore(cid, present, state, False, None, None, False,
                               False, error="no behavioural answer")
    body = "" if text is None else str(text)
    try:
        m = VERIFIERS[verifier_id](body, **dict(parameters))
    except Exception as error:   # fail closed: a scoring failure, never FAIL
        return ConstraintScore(cid, present, state, False, None, None, False,
                               False, error=f"{type(error).__name__}: {error}")
    non_vacuous = state == STATE_SCORABLE and (
        vacuity == "forced_production"
        or T.word_count(body) >= NON_VACUITY_MIN_WORDS)
    passed = bool(m.passed)
    excluded = "" if not passed or non_vacuous else {
        STATE_SCORABLE: "vacuous", STATE_TRUNCATED: "truncated",
        STATE_EMPTY: "empty"}[state]
    return ConstraintScore(
        cid=cid, present=present, state=state, scored=True,
        verdict="PASS" if passed else "FAIL", statistic=m.statistic,
        non_vacuous=non_vacuous, compliant=passed and non_vacuous,
        pass_excluded_by=excluded)


_HERE = Path(__file__).resolve()


def verifier_implementation_hash(verifier_id: str) -> str:
    """Source of one family's function plus the shared text semantics."""
    fn = VERIFIERS[verifier_id]
    return sha(["batch1/verifier", verifier_id, inspect.getsource(fn),
                T.text_semantics_hash()])


def verifier_bundle_hash() -> str:
    """Every byte that decides a Batch 1 verdict or compliance value."""
    return sha(["batch1/verifier-bundle", sha_file(_HERE),
                T.text_semantics_hash(),
                {v: verifier_implementation_hash(v) for v in sorted(VERIFIERS)}])
