"""rules — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
import math
import re
import numpy as np
from dataclasses import dataclass
from typing import Any, Literal


OutcomeStatus = Literal["full", "partial", "violation", "unscorable"]


@dataclass
class VerificationResult:
    status: OutcomeStatus
    binary_pass: int
    continuous_score: float
    detail: dict[str, Any]


WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")


INTEGER_PATTERN = re.compile(r"(?<![A-Za-z0-9])-?\d+(?![A-Za-z0-9])")


DIGIT_PATTERN = re.compile(r"\d")


PERCENT_PATTERN = re.compile(r"\d+(?:\.\d+)?\s?%")


SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])["”’]?\s+')


# --------------------------------------------------------------------------
# Abbreviation handling for sentence segmentation.
#
# `SENTENCE_BOUNDARY` alone treats every full stop before whitespace as a
# sentence end, so "Sales spike at 6 a.m. when others sleep." was two sentences.
# Because `v_exact_sentence_count` decides the primary outcome F_A, that is a
# scientific error and not a cosmetic one: it manufactured sentence-count
# OVERSHOOT and turned compliant answers into violations.
#
# Two closed tables, because the two classes behave differently:
#
#   TITLE_ABBREVIATIONS  are always followed by a name, so a following capital
#                        is NOT a new sentence. "Dr. Smith" is one sentence.
#   MEDIAL_ABBREVIATIONS can legitimately end a sentence, so the following
#                        capital is what decides. "at 6 a.m. when ..." continues;
#                        "at 6 a.m. Customers ..." is a boundary.
#
# Both are matched case-insensitively against the token stripped of its internal
# full stops, so "a.m", "A.M" and "am" resolve alike. The tables are deliberately
# closed rather than a general heuristic: an open-ended rule is what would make
# the semantics untestable.
#
# Documented costs of the convention, accepted and covered by tests:
#   * a sentence that genuinely begins with a lower-case word after a medial
#     abbreviation is under-counted;
#   * a sentence that genuinely begins after a title-like token is under-counted;
#   * a single letter before a full stop is read as an initial ("J. R. Smith"),
#     so a sentence ending in a bare capital letter is under-counted.
# --------------------------------------------------------------------------
TITLE_ABBREVIATIONS = frozenset({
    "mr", "mrs", "ms", "messrs", "dr", "prof", "rev", "hon", "st", "sr", "jr",
    "capt", "sgt", "lt", "col", "gen", "fr", "mt",
})

MEDIAL_ABBREVIATIONS = frozenset({
    "am", "pm", "eg", "ie", "etc", "vs", "approx", "no", "fig", "cf", "al",
    "inc", "ltd", "co", "dept", "est", "vol", "pp", "ed", "eds", "min", "max",
    "avg", "ca", "viz", "resp",
})

# The contiguous letter-and-dot run ending at the candidate full stop: "a.m"
# from "... 6 a.m.", "Dr" from "Dr.", "weekday" from "... every weekday.".
TRAILING_ABBREVIATION = re.compile(r"([A-Za-z](?:\.?[A-Za-z])*)\.$")


def _ends_sentence(left: str, right: str) -> bool:
    """Whether the terminator ending `left` really closes a sentence.

    `left` includes the terminator; `right` is what follows the whitespace.
    """
    terminator = left[-1:]
    if terminator in "!?":
        return True                       # never ambiguous
    following = right.lstrip()
    follows_capital = bool(following) and following[0].isupper()

    if left.endswith(".."):                # an ellipsis, not a full stop
        return follows_capital

    match = TRAILING_ABBREVIATION.search(left)
    if match is None:
        return True
    token = match.group(1)
    if len(token) == 1:                    # an initial, as in "J. R. Smith"
        return False
    bare = token.replace(".", "").lower()
    if bare in TITLE_ABBREVIATIONS:
        return False
    if bare in MEDIAL_ABBREVIATIONS:
        return follows_capital
    return True


def _split_line(line: str) -> list[str]:
    """Split one line at the boundaries that survive `_ends_sentence`."""
    parts: list[str] = []
    start = 0
    for match in SENTENCE_BOUNDARY.finditer(line):
        if _ends_sentence(line[:match.start()], line[match.end():]):
            parts.append(line[start:match.start()])
            start = match.end()
    parts.append(line[start:])
    return parts


LIST_MARKER = re.compile(r"^\s*(?:[-*•‣▪]|\(?\d{1,2}[.)])\s+")


STRAIGHT_QUOTE = '"'


CURLY_QUOTES = ("“", "”")


VOWELS = "aeiouAEIOU"


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    return re.sub(r"[^\S\n]+", " ", str(text)).strip()


def split_sentences(text: Any) -> list[str]:
    clean = normalize_text(text)
    if not clean:
        return []
    parts: list[str] = []
    for line in clean.split("\n"):
        line = LIST_MARKER.sub("", line).strip()
        if not line:
            continue
        parts.extend(
            part.strip()
            for part in _split_line(line)
            if re.search(r"[A-Za-z0-9]", part))
    if parts:
        return parts
    return [clean] if re.search(r"[A-Za-z0-9]", clean) else []


def word_tokens(text: Any) -> list[str]:
    return WORD_PATTERN.findall(normalize_text(text))


def integer_tokens(text: Any) -> list[int]:
    return [int(v) for v in INTEGER_PATTERN.findall(normalize_text(text))]


def fraction_status(score: float) -> OutcomeStatus:
    if math.isclose(score, 1.0):
        return "full"
    return "partial" if score > 0 else "violation"


def count_status(observed: int, target: int) -> tuple[OutcomeStatus, int, float]:
    """Shared scoring for 'exactly n of something' over the whole answer.

    Producing none of a required thing is a violation, not partial credit, even
    when the target is one and the distance is therefore one.
    """
    distance = abs(observed - target)
    score = max(0.0, 1.0 - distance / max(target, 1))
    if observed == 0 and target > 0:
        return "violation", 0, float(score)
    status: OutcomeStatus = (
        "full" if distance == 0 else ("partial" if distance == 1 else "violation"))
    return status, int(distance == 0), float(score)


def _unscorable(detail: dict[str, Any]) -> VerificationResult:
    return VerificationResult("unscorable", 0, 0.0, detail)


def _per_sentence(text: str, predicate, detail_key: str, extra=None) -> VerificationResult:
    sentences = split_sentences(text)
    if not sentences:
        return _unscorable({detail_key: []})
    values = [predicate(s) for s in sentences]
    score = float(np.mean([bool(v) for v in values]))
    detail = {detail_key: values}
    if extra:
        detail.update(extra)
    return VerificationResult(fraction_status(score), int(all(values)), score, detail)


def v_exact_sentence_count(text: str, n: int) -> VerificationResult:
    sentences = split_sentences(text)
    observed = len(sentences)
    if observed == 0:
        return _unscorable({"observed": 0, "target": n})
    status, binary, score = count_status(observed, n)
    return VerificationResult(status, binary, score, {"observed": observed, "target": n})


def v_increasing_lengths(text: str) -> VerificationResult:
    lengths = [len(word_tokens(s)) for s in split_sentences(text)]
    if len(lengths) < 2:
        return _unscorable({"word_counts": lengths})
    checks = [b > a for a, b in zip(lengths, lengths[1:])]
    score = float(np.mean(checks))
    return VerificationResult(fraction_status(score), int(all(checks)), score,
                              {"word_counts": lengths, "checks": checks})


def v_nondecreasing_lengths(text: str) -> VerificationResult:
    lengths = [len(word_tokens(s)) for s in split_sentences(text)]
    if len(lengths) < 2:
        return _unscorable({"word_counts": lengths})
    checks = [b >= a for a, b in zip(lengths, lengths[1:])]
    score = float(np.mean(checks))
    return VerificationResult(fraction_status(score), int(all(checks)), score,
                              {"word_counts": lengths, "checks": checks})


def v_sentence_initial(text: str, letter: str = "S") -> VerificationResult:
    target = letter.lower()

    def first_letter(sentence: str) -> str:
        m = re.search(r"[A-Za-z]", sentence)
        return m.group(0).lower() if m else ""

    sentences = split_sentences(text)
    if not sentences:
        return _unscorable({"initials": []})
    initials = [first_letter(s) for s in sentences]
    checks = [i == target for i in initials]
    score = float(np.mean(checks))
    return VerificationResult(fraction_status(score), int(all(checks)), score,
                              {"initials": initials, "required": target})


def v_min_sentence_words(text: str, n: int) -> VerificationResult:
    lengths = [len(word_tokens(s)) for s in split_sentences(text)]
    if not lengths:
        return _unscorable({"word_counts": []})
    checks = [k >= n for k in lengths]
    score = float(np.mean(checks))
    return VerificationResult(fraction_status(score), int(all(checks)), score,
                              {"word_counts": lengths, "minimum": n})


def v_alphabetical_starts(text: str) -> VerificationResult:
    sentences = split_sentences(text)
    if len(sentences) < 2:
        return _unscorable({"first_words": []})
    firsts = [(word_tokens(s) or [""])[0].lower() for s in sentences]
    checks = [b >= a for a, b in zip(firsts, firsts[1:])]
    score = float(np.mean(checks))
    return VerificationResult(fraction_status(score), int(all(checks)), score,
                              {"first_words": firsts, "checks": checks})


def v_long_word_each_sentence(text: str, letters: int) -> VerificationResult:
    return _per_sentence(text, lambda s: any(len(w) >= letters for w in word_tokens(s)),
                         "has_long_word", {"letters": letters})


def v_sentence_ends_long(text: str, letters: int) -> VerificationResult:
    def ends_long(sentence: str) -> bool:
        tokens = word_tokens(sentence)
        return bool(tokens) and len(tokens[-1]) >= letters

    return _per_sentence(text, ends_long, "ends_long", {"letters": letters})


def v_commas_per_sentence(text: str, n: int) -> VerificationResult:
    return _per_sentence(text, lambda s: s.count(",") == n, "comma_ok", {"required": n})


def v_min_long_words_per_sentence(text: str, letters: int, n: int) -> VerificationResult:
    return _per_sentence(
        text, lambda s: sum(len(w) >= letters for w in word_tokens(s)) >= n,
        "long_word_count_ok", {"letters": letters, "minimum": n})


def v_word_band(text: str, low: int, high: int) -> VerificationResult:
    return _per_sentence(text, lambda s: low <= len(word_tokens(s)) <= high,
                         "in_band", {"low": low, "high": high})


def v_semicolon_each(text: str) -> VerificationResult:
    return _per_sentence(text, lambda s: ";" in s, "semicolon_ok")


def v_comma_and_min_words(text: str, n: int) -> VerificationResult:
    return _per_sentence(text, lambda s: ("," in s) and len(word_tokens(s)) >= n,
                         "comma_and_length_ok", {"minimum": n})


def v_unique_words(text: str) -> VerificationResult:
    tokens = [t.lower() for t in word_tokens(text)]
    if not tokens:
        return _unscorable({"token_count": 0})
    unique = len(set(tokens))
    score = unique / len(tokens)
    passed = unique == len(tokens)
    return VerificationResult("full" if passed else fraction_status(score),
                              int(passed), float(score),
                              {"token_count": len(tokens), "unique_count": unique})


def v_integer_sum(text: str, count: int, total: int) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"values": []})
    values = integer_tokens(text)
    passed = len(values) == count and sum(values) == total
    count_score = max(0.0, 1.0 - abs(len(values) - count) / max(count, 1))
    sum_score = 1.0 / (1.0 + abs(sum(values) - total) / max(abs(total), 1))
    score = float((count_score + sum_score) / 2)
    return VerificationResult("full" if passed else fraction_status(score),
                              int(passed), score,
                              {"values": values, "expected_count": count,
                               "expected_sum": total})


def v_distinct_integers(text: str, count: int) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"values": []})
    values = integer_tokens(text)
    distinct = len(set(values))
    passed = len(values) == count and distinct == count
    score = float((max(0.0, 1.0 - abs(len(values) - count) / max(count, 1))
                   + min(distinct, count) / max(count, 1)) / 2)
    return VerificationResult("full" if passed else fraction_status(score),
                              int(passed), score,
                              {"values": values, "distinct": distinct,
                               "expected_count": count})


def v_forbid_word_set(text: str, words: tuple[str, ...]) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"words": list(words)})
    lowered = [t.lower() for t in word_tokens(text)]
    hits = {w: lowered.count(w.lower()) for w in words}
    offending = sum(1 for w, k in hits.items() if k > 0)
    score = 1.0 - offending / max(len(words), 1)
    return VerificationResult(fraction_status(score), int(offending == 0),
                              float(score), {"occurrences": hits})


def v_require_word_set(text: str, words: tuple[str, ...]) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"words": list(words)})
    lowered = [t.lower() for t in word_tokens(text)]
    present = {w: lowered.count(w.lower()) >= 1 for w in words}
    score = float(np.mean(list(present.values()))) if present else 0.0
    return VerificationResult(fraction_status(score), int(all(present.values())),
                              score, {"present": present})


def v_require_word(text: str, word: str) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"word": word})
    hits = sum(1 for t in word_tokens(text) if t.lower() == word.lower())
    return VerificationResult("full" if hits >= 1 else "violation",
                              int(hits >= 1), float(hits >= 1),
                              {"word": word, "occurrences": hits})


def v_no_suffix(text: str, suffix: str) -> VerificationResult:
    """No word ends in the given letters. Orthographic, not part-of-speech."""
    tokens = word_tokens(text)
    if not tokens:
        return _unscorable({"suffix": suffix})
    offenders = [t for t in tokens if t.lower().endswith(suffix.lower())]
    score = 1.0 - len(offenders) / len(tokens)
    return VerificationResult("full" if not offenders else fraction_status(score),
                              int(not offenders), float(score),
                              {"suffix": suffix, "offenders": offenders[:20],
                               "n_offenders": len(offenders)})


def v_alliteration(text: str, letter: str, n: int) -> VerificationResult:
    tokens = word_tokens(text)
    if not tokens:
        return _unscorable({"letter": letter, "minimum": n})
    hits = sum(1 for t in tokens if t[:1].lower() == letter.lower())
    score = min(1.0, hits / max(n, 1))
    return VerificationResult("full" if hits >= n else fraction_status(score),
                              int(hits >= n), float(score),
                              {"letter": letter, "minimum": n, "observed": hits})


def v_caps_word(text: str, n: int, letters: int) -> VerificationResult:
    tokens = word_tokens(text)
    if not tokens:
        return _unscorable({"required": n})
    hits = [t for t in tokens if t.isalpha() and t.isupper() and len(t) >= letters]
    status, binary, score = count_status(len(hits), n)
    return VerificationResult(status, binary, score,
                              {"required": n, "letters": letters,
                               "observed": len(hits), "words": hits[:10]})


def v_exact_char_total(text: str, char: str, n: int) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({"char": char, "required": n})
    observed = clean.count(char)
    status, binary, score = count_status(observed, n)
    return VerificationResult(status, binary, score,
                              {"char": char, "required": n, "observed": observed})


def v_no_char(text: str, char: str) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({"char": char})
    observed = clean.count(char)
    return VerificationResult("full" if observed == 0 else "violation",
                              int(observed == 0), float(observed == 0),
                              {"char": char, "observed": observed})


def matched_pairs(text: str, opener: str, closer: str) -> tuple[int, bool]:
    """Pairs closed in order, and whether the running depth stayed non-negative.

    Counting openers and closers separately cannot tell ")(" from "()": both
    have one of each. A delimiter requirement is a requirement about structure,
    so it is decided by a left-to-right scan in which a closer only pairs with
    an opener that is still unmatched. `ordered` is False as soon as a closer
    appears at depth zero; nesting itself is permitted.
    """
    depth = pairs = 0
    ordered = True
    for char in text:
        if char == opener:
            depth += 1
        elif char == closer:
            if depth == 0:
                ordered = False
            else:
                depth -= 1
                pairs += 1
    return pairs, ordered


def v_paren_pairs(text: str, n: int) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({"required": n})
    opens, closes = clean.count("("), clean.count(")")
    balanced = opens == closes
    pairs, ordered = matched_pairs(clean, "(", ")")
    status, binary, score = count_status(pairs, n)
    if not ordered:
        # A negative running depth is not a near miss to be scored down; the
        # sequence is malformed and cannot satisfy the requirement at all.
        status, binary = "violation", 0
        score = min(score, 0.5)
    elif not balanced:
        status, binary = ("violation" if status == "violation" else "partial"), 0
        score = min(score, 0.5)
    return VerificationResult(status, binary, score,
                              {"open": opens, "close": closes, "required": n,
                               "balanced": balanced, "ordered": ordered,
                               "pairs": pairs})


def v_quote_pairs(text: str, n: int) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({"required": n})
    straight = clean.count(STRAIGHT_QUOTE)
    curly_open, curly_close = clean.count(CURLY_QUOTES[0]), clean.count(CURLY_QUOTES[1])
    # A pair is two straight marks, or one curly-open with a LATER curly-close.
    # Straight marks are their own opener and closer so order cannot be wrong;
    # directional marks can be, and reversed marks are not a pair.
    curly_pairs, ordered = matched_pairs(clean, CURLY_QUOTES[0], CURLY_QUOTES[1])
    pairs = straight // 2 + curly_pairs
    leftover = straight % 2 or (curly_open != curly_close)
    status, binary, score = count_status(pairs, n)
    if not ordered:
        status, binary = "violation", 0
        score = min(score, 0.5)
    elif leftover:
        status, binary = ("violation" if status == "violation" else "partial"), 0
        score = min(score, 0.5)
    return VerificationResult(status, binary, score,
                              {"straight": straight, "curly_open": curly_open,
                               "curly_close": curly_close, "pairs": pairs,
                               "required": n, "unbalanced": bool(leftover),
                               "ordered": ordered})


def v_exact_integer_count(text: str, n: int) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"required": n})
    values = integer_tokens(text)
    status, binary, score = count_status(len(values), n)
    return VerificationResult(status, binary, score,
                              {"values": values, "required": n})


def v_vowel_words_per_sentence(text: str, n: int) -> VerificationResult:
    return _per_sentence(
        text,
        lambda s: sum(1 for w in word_tokens(s) if w[:1] in VOWELS) >= n,
        "vowel_initial_ok", {"minimum": n})


def v_caps_sentence_count(text: str, n: int, letters: int) -> VerificationResult:
    sentences = split_sentences(text)
    if not sentences:
        return _unscorable({"required": n})
    carrying = sum(
        1 for s in sentences
        if any(w.isalpha() and w.isupper() and len(w) >= letters
               for w in word_tokens(s)))
    status, binary, score = count_status(carrying, n)
    return VerificationResult(status, binary, score,
                              {"sentences_with_caps": carrying, "required": n,
                               "letters": letters})


def v_sentence_initial_forbidden_word(text: str, word: str) -> VerificationResult:
    def ok(sentence: str) -> bool:
        tokens = word_tokens(sentence)
        return not tokens or tokens[0].lower() != word.lower()

    return _per_sentence(text, ok, "opening_ok", {"forbidden": word})


def v_question_sentence_count(text: str, n: int) -> VerificationResult:
    sentences = split_sentences(text)
    if not sentences:
        return _unscorable({"required": n})
    asking = sum(1 for s in sentences if s.rstrip().endswith("?"))
    status, binary, score = count_status(asking, n)
    return VerificationResult(status, binary, score,
                              {"question_sentences": asking, "required": n})


def v_min_integer_count(text: str, n: int) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"minimum": n})
    values = integer_tokens(text)
    score = min(1.0, len(values) / max(n, 1))
    passed = len(values) >= n
    return VerificationResult("full" if passed else fraction_status(score),
                              int(passed), float(score),
                              {"values": values, "minimum": n})


def v_max_integer_count(text: str, n: int) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"maximum": n})
    values = integer_tokens(text)
    excess = max(0, len(values) - n)
    passed = excess == 0
    score = 1.0 if passed else max(0.0, 1.0 - excess / max(n, 1))
    return VerificationResult("full" if passed else fraction_status(score),
                              int(passed), float(score),
                              {"values": values, "maximum": n})


def v_no_digits(text: str) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({})
    hits = len(DIGIT_PATTERN.findall(clean))
    return VerificationResult("full" if hits == 0 else "violation",
                              int(hits == 0), float(hits == 0),
                              {"digit_count": hits})


def v_percent_count(text: str, n: int) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({"required": n})
    hits = PERCENT_PATTERN.findall(clean)
    status, binary, score = count_status(len(hits), n)
    return VerificationResult(status, binary, score,
                              {"required": n, "observed": len(hits),
                               "matches": hits[:10]})
