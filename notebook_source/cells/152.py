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
LIST_MARKER = re.compile(r"^\s*(?:[-*•‣▪]|\(?\d{1,2}[.)])\s+")
STRAIGHT_QUOTE = '"'
CURLY_QUOTES = ("“", "”")


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
            for part in SENTENCE_BOUNDARY.split(line)
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


# =================================================== sentence-scoped verifiers
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


# ====================================================== whole-text verifiers
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


def v_paren_pairs(text: str, n: int) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({"required": n})
    opens, closes = clean.count("("), clean.count(")")
    balanced = opens == closes
    status, binary, score = count_status(min(opens, closes), n)
    if not balanced:
        status, binary = ("violation" if status == "violation" else "partial"), 0
        score = min(score, 0.5)
    return VerificationResult(status, binary, score,
                              {"open": opens, "close": closes, "required": n,
                               "balanced": balanced})


def v_quote_pairs(text: str, n: int) -> VerificationResult:
    clean = normalize_text(text)
    if not clean:
        return _unscorable({"required": n})
    straight = clean.count(STRAIGHT_QUOTE)
    curly_open, curly_close = clean.count(CURLY_QUOTES[0]), clean.count(CURLY_QUOTES[1])
    # A pair is two straight marks, or one curly-open with one curly-close.
    pairs = straight // 2 + min(curly_open, curly_close)
    leftover = straight % 2 or (curly_open != curly_close)
    status, binary, score = count_status(pairs, n)
    if leftover:
        status, binary = ("violation" if status == "violation" else "partial"), 0
        score = min(score, 0.5)
    return VerificationResult(status, binary, score,
                              {"straight": straight, "curly_open": curly_open,
                               "curly_close": curly_close, "pairs": pairs,
                               "required": n, "unbalanced": bool(leftover)})


def v_exact_integer_count(text: str, n: int) -> VerificationResult:
    if not normalize_text(text):
        return _unscorable({"required": n})
    values = integer_tokens(text)
    status, binary, score = count_status(len(values), n)
    return VerificationResult(status, binary, score,
                              {"values": values, "required": n})


# ================================================= bridge-family verifiers
# Sentence-scoped by design. Each reads WITHIN sentences or counts sentences
# carrying a property; none reads the total number of sentences and none
# compares one sentence with another. Both claims are proved behaviourally by
# the count-invariance and order-invariance probes below.
VOWELS = "aeiouAEIOU"


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

_missing_family = sorted({c.rule_family for c in CONSTRAINTS.values()}
                         - set(VERIFIER_FACTORY))
assert not _missing_family, f"rule families without a verifier: {_missing_family}"

VERIFIERS: dict[str, Callable[[str], VerificationResult]] = {
    cid: VERIFIER_FACTORY[c.rule_family](**c.param_dict)
    for cid, c in CONSTRAINTS.items()
}
assert set(VERIFIERS) == set(CONSTRAINTS), "Every constraint needs a verifier."


def verify(text: str, constraint_id: str) -> VerificationResult:
    return VERIFIERS[constraint_id](text)


# ===================================================== pathway audit probes
_REAL_SPLIT = split_sentences
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
_WHOLE_TEXT_U = [u for u in U_CANDIDATE_IDS if CONSTRAINTS[u].u_family != "bridge"]
split_sentences = _forbidden_split  # noqa: F811  (temporary probe)
try:
    for _uid in _WHOLE_TEXT_U:
        VERIFIERS[_uid](_PROBE_TEXT)
finally:
    split_sentences = _REAL_SPLIT


def count_invariance_probe(constraint_id: str, passing_text: str,
                           neutral_sentence: str) -> bool:
    """Adding a declared neutral sentence must not change the verdict.

    A rule that reads the total number of sentences, which is exactly what A
    does, cannot survive this. It is the behavioural form of the claim that a
    bridge target carries no direct A pathway.
    """
    before = verify(passing_text, constraint_id).binary_pass
    after = verify(passing_text.rstrip() + " " + neutral_sentence,
                   constraint_id).binary_pass
    return before == after


def order_invariance_probe(constraint_id: str, passing_text: str) -> bool:
    """Reversing sentence order must not change the verdict.

    A rule that compares one sentence with another, which is exactly what B
    does, cannot survive this.
    """
    sentences = _REAL_SPLIT(passing_text)
    if len(sentences) < 2:
        return True
    reordered = " ".join(reversed([s if s.endswith((".", "!", "?")) else s + "."
                                   for s in sentences]))
    return (verify(passing_text, constraint_id).binary_pass
            == verify(reordered, constraint_id).binary_pass)


BRIDGE_PROBE_TABLE = []
for _uid in BRIDGE_IDS:
    _text = _BRIDGE_PASSING[_uid]
    _base = verify(_text, _uid)
    _count_ok = count_invariance_probe(_uid, _text, CONSTRAINTS[_uid].count_probe_sentence)
    _order_ok = order_invariance_probe(_uid, _text)
    BRIDGE_PROBE_TABLE.append({
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
    CFG.target_id, "One here. Two here. Three here. Four here.", NEUTRAL_A), (
    "the count-invariance probe does not detect A itself and is therefore vacuous")
assert not order_invariance_probe(
    CFG.focal_id, "Birds fly. Small birds fly swiftly. "
                  "Many small birds fly swiftly above wide fields."), (
    "the order-invariance probe does not detect B itself and is therefore vacuous")

print(f"{len(VERIFIERS)} verifiers built from {len(VERIFIER_FACTORY)} rule families.")
print(f"{len(_WHOLE_TEXT_U)} whole-answer unrelated targets ran with sentence "
      "segmentation disabled: none reads a sentence boundary.")
print(f"{len(BRIDGE_IDS)} bridge targets passed count-invariance and "
      "order-invariance; A and B both fail those probes, so they are not vacuous.")
display(pd.DataFrame(BRIDGE_PROBE_TABLE))
