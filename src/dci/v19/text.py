"""One text semantics for every layer that reads a final-answer segment.

The adversarial audit found the same fault three times over: each layer had its own
idea of what a word is and how to compare two of them.

  * `dci.verifiers.rules.WORD_PATTERN` is `[A-Za-z0-9]+`, so "café" tokenised as
    "caf", a zero-width space split one word into two, and a mandatory word
    containing a non-ASCII letter could never be matched;
  * `rules.normalize_text` collapsed `\\s` runs, which does not include U+200B or
    the soft hyphen, so invisible characters survived into the tokens;
  * the encoding folded with `str.casefold` while the verifiers compared with
    `str.lower`, so a clause could require one distinct mandatory token where the
    verifier looked for two;
  * `split_sentences` kept only segments containing an ASCII alphanumeric, so a
    list item written in Cyrillic was an item and not a sentence - which made the
    solver's `n_sentences >= n_items` axiom unsound.

`TextPolicy` fixes all of that in one hashed object, and every v19 layer -
encoding, parser, witness constructor, and all six verifiers - reads it. That is
what makes "the same semantics across layers" checkable rather than hoped for.

WHY THIS IS A CORRECTION AND NOT A REWRITE
------------------------------------------
Section 14.2 permits reuse of the Pair 2/3 implementations "only after hash/semantic
audit", and section 10.6 is explicit about the outcome of an audit that finds
something: "A demonstrated semantic or verifier defect requires repair and re-audit
before freeze; collecting more confirmatory data is not a remedy for invalid
measurement." Three defects were demonstrated, so repair is what the protocol
requires. The inherited module is left untouched - the v15.1 pipeline and its
regression fixtures still depend on it - and the v19 verifiers move onto this layer
with new specification hashes and a recorded lineage.

WHAT IS DELIBERATELY NOT ATTEMPTED
----------------------------------
Confusable detection. A Cyrillic "а" is a different character from a Latin "a" and
NFKC does not merge them, so "аpple apple" is two distinct words under this policy.
That is a defensible reading - they are different strings - and it is a strict
improvement on the old behaviour, which silently split the word into "pple" and
counted it as unique. Section 10.6 lists homoglyphs as human *audit material*, not
as an automated rule, so the audit bank keeps them and no code decides them.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from dci.provenance.hashes import sha
from dci.verifiers import rules

NORMALISATIONS = ("none", "NFC", "NFD", "NFKC", "NFKD")
CASE_RULES = ("casefold", "lower", "none")

# Unicode general categories removed before tokenisation. Cf is "format": it holds
# the zero-width space, the zero-width joiner and non-joiner, the soft hyphen and
# the byte-order mark - every character the audit used to defeat a verifier while
# remaining invisible to a reader. Cc is "control".
INVISIBLE_CATEGORIES = ("Cf", "Cc")

# A Unicode-aware word: runs of letters and digits, optionally joined by an
# apostrophe or hyphen. `[^\W_]` is "word character but not underscore", which is
# alphanumeric in any script.
UNICODE_WORD_PATTERN = r"[^\W_]+(?:['’\-][^\W_]+)*"

# Sentence boundaries, taken FROM `rules.SENTENCE_BOUNDARY` rather than re-typed
# from it. The previous literal here claimed to be verbatim and was not: it
# allowed at most one closing mark from a three-character set, which is the
# PRE-repair class, so `**Bold.** Next.` and `(Aside.) Next.` stopped splitting.
#
# Re-declaring the pattern also dropped the abbreviation guard that wraps it in
# `rules.split_line`, so "Mr. Smith went to Washington. He stayed." segmented as
# three sentences instead of two. Both halves of the Pair 3 segmentation now come
# from the one certified implementation; see `sentence_abbreviation_guard`.
SENTENCE_BOUNDARY_PATTERN = rules.SENTENCE_BOUNDARY.pattern

#: Provenance of the boundary-disambiguation rule applied on top of the pattern.
#: Named (not a bool) so the specification hash records WHICH guard ran, and so a
#: future policy that legitimately wants raw regex splitting has to say so.
ABBREVIATION_GUARD = "dci.verifiers.rules.ends_sentence"
NO_ABBREVIATION_GUARD = "none"
ABBREVIATION_GUARDS = (ABBREVIATION_GUARD, NO_ABBREVIATION_GUARD)


class TextPolicyError(ValueError):
    """A text policy that cannot be applied as declared."""


@dataclass(frozen=True)
class TextPolicy:
    """The frozen normalisation, tokenisation and comparison rule."""
    policy_id: str
    provenance: str
    unicode_normalisation: str
    removed_categories: tuple[str, ...]
    case_rule: str
    word_pattern: str
    sentence_boundary: str
    collapse_whitespace: bool
    #: Which boundary-disambiguation rule runs on top of `sentence_boundary`.
    #: A regex alone cannot decide "Mr. Smith" or "6 a.m. when", and a policy that
    #: does not name a guard is declaring that it wants the raw split.
    sentence_abbreviation_guard: str = ABBREVIATION_GUARD

    def __post_init__(self):
        if not self.policy_id or not self.provenance:
            raise TextPolicyError("a text policy needs an id and a provenance note")
        if self.sentence_abbreviation_guard not in ABBREVIATION_GUARDS:
            raise TextPolicyError(
                f"{self.policy_id}: {self.sentence_abbreviation_guard!r} is not one "
                f"of {ABBREVIATION_GUARDS}")
        if self.unicode_normalisation not in NORMALISATIONS:
            raise TextPolicyError(
                f"{self.policy_id}: {self.unicode_normalisation!r} is not one of "
                f"{NORMALISATIONS}")
        if self.case_rule not in CASE_RULES:
            raise TextPolicyError(
                f"{self.policy_id}: {self.case_rule!r} is not one of {CASE_RULES}")
        for pattern in (self.word_pattern, self.sentence_boundary):
            try:
                re.compile(pattern)
            except re.error as error:
                raise TextPolicyError(
                    f"{self.policy_id}: {pattern!r} is not a usable regular "
                    f"expression ({error})") from error
        for category in self.removed_categories:
            if len(category) != 2 or not category[0].isupper():
                raise TextPolicyError(
                    f"{self.policy_id}: {category!r} is not a Unicode general "
                    "category")

    def state(self) -> dict[str, Any]:
        return {"policy_id": self.policy_id,
                "unicode_normalisation": self.unicode_normalisation,
                "removed_categories": list(self.removed_categories),
                "case_rule": self.case_rule,
                "word_pattern": self.word_pattern,
                "sentence_boundary": self.sentence_boundary,
                "sentence_abbreviation_guard": self.sentence_abbreviation_guard,
                "collapse_whitespace": self.collapse_whitespace}

    @property
    def policy_hash(self) -> str:
        return sha(["v19/text-policy", self.state()])


# The frozen v19 text semantics. Every field is a correction of a demonstrated
# defect, named in `provenance` so the amendment is auditable from the object.
CANONICAL_TEXT_POLICY = TextPolicy(
    policy_id="v19:text-policy.canonical",
    provenance=(
        "corrects the inherited v15.1 text semantics under sections 10.6 and 14.2: "
        "NFKC normalisation so compatibility variants and decomposed accents "
        "compare equal; removal of format and control characters so a zero-width "
        "space or soft hyphen cannot split a word; a Unicode-aware word pattern so "
        "a non-ASCII mandatory word is matchable and a non-ASCII sentence is a "
        "sentence; and one case rule, casefold, replacing the mixture of casefold "
        "and str.lower that let the encoding and the verifier disagree"),
    unicode_normalisation="NFKC",
    removed_categories=INVISIBLE_CATEGORIES,
    case_rule="casefold",
    word_pattern=UNICODE_WORD_PATTERN,
    sentence_boundary=SENTENCE_BOUNDARY_PATTERN,
    collapse_whitespace=True)


def abbreviation_guard_state(policy: TextPolicy) -> dict[str, Any]:
    """What the named guard is actually made of, for the specification hash.

    `sentence_abbreviation_guard` records WHICH guard runs. That is not enough to
    freeze the measurement: the guard lives in `dci.verifiers.rules`, outside this
    module, and its decision is driven by two abbreviation tables, a trailing-token
    pattern and an opening-punctuation set. Adding one entry to
    `TITLE_ABBREVIATIONS` changes sentence counts — and therefore F_A — while the
    guard's NAME, the v19 helpers' source, and every hash derived from them stay
    identical.

    That gap opened the moment Pair 3 stopped carrying its own segmentation and
    delegated to the certified implementation. Delegation is right; leaving the
    delegate outside the frozen closure is not. So the substance travels with the
    name, and a future guard repair cannot retain the frozen bundle identity.

    A policy that declares no guard has no guard state: the raw regex split is
    fully described by `sentence_boundary`, which is already a policy field.
    """
    policy = require_policy(policy)
    if policy.sentence_abbreviation_guard != ABBREVIATION_GUARD:
        return {"guard": policy.sentence_abbreviation_guard}
    return {
        "guard": policy.sentence_abbreviation_guard,
        "boundary_pattern": rules.SENTENCE_BOUNDARY.pattern,
        "title_abbreviations": sorted(rules.TITLE_ABBREVIATIONS),
        "medial_abbreviations": sorted(rules.MEDIAL_ABBREVIATIONS),
        "trailing_abbreviation_pattern": rules.TRAILING_ABBREVIATION.pattern,
        "opening_punctuation": "".join(sorted(rules.OPENING_PUNCTUATION)),
    }


def require_policy(policy: Any) -> TextPolicy:
    """Refuse anything but an explicit text policy."""
    if not isinstance(policy, TextPolicy):
        raise TextPolicyError(
            f"an explicit TextPolicy is required, got {type(policy).__name__}; "
            "the text semantics are a frozen scientific commitment and there is no "
            "default to fall back on")
    return policy


def normalise(text: Any, policy: TextPolicy) -> str:
    """Normalise, strip invisibles, collapse whitespace. Idempotent by design."""
    policy = require_policy(policy)
    raw = "" if text is None else str(text)
    if policy.unicode_normalisation != "none":
        raw = unicodedata.normalize(cast(Any, policy.unicode_normalisation), raw)
    if policy.removed_categories:
        removed = set(policy.removed_categories)
        # Whitespace is never removed even when its category is in the set: a
        # newline is category Cc, and deleting it would collapse a list into one
        # line. Whitespace is handled by the collapse step below, which is where
        # tabs, non-breaking spaces and ideographic spaces lose their identity.
        raw = "".join(c for c in raw
                      if c.isspace() or unicodedata.category(c) not in removed)
    if policy.collapse_whitespace:
        # Everything that is whitespace but not a newline collapses to one space, so
        # tabs, non-breaking spaces and ideographic spaces stop being
        # distinguishable. Newlines survive because the list grammar segments on
        # them, and leading space survives as a single space because indentation is
        # what the nesting rule reads - stripping it would delete a scientific
        # feature in the name of tidying.
        raw = re.sub(r"[^\S\n]+", " ", raw)
        raw = "\n".join(line.rstrip() for line in raw.split("\n"))
    return raw


def fold(value: str, policy: TextPolicy) -> str:
    """The one case rule, applied everywhere a comparison happens."""
    policy = require_policy(policy)
    if policy.case_rule == "casefold":
        return value.casefold()
    if policy.case_rule == "lower":
        return value.lower()
    return value


def word_tokens(text: Any, policy: TextPolicy) -> list[str]:
    """Word tokens of the normalised text, in order, not case-folded."""
    policy = require_policy(policy)
    return re.findall(policy.word_pattern, normalise(text, policy))


def folded_tokens(text: Any, policy: TextPolicy) -> list[str]:
    """Word tokens as they are compared: normalised, then folded."""
    return [fold(token, policy) for token in word_tokens(text, policy)]


def split_sentences(text: Any, policy: TextPolicy,
                    strip_markers: Sequence[str] = ()) -> list[str]:
    """Sentence segments of the normalised text.

    `strip_markers` receives the list-marker patterns the frozen list grammar
    admits, so the sentence and list spans agree about what a marker is instead of
    each carrying its own regex. A segment survives only if it contains a word
    token, and "word token" now means the same thing it means everywhere else -
    which is what makes a non-ASCII item a sentence too.
    """
    policy = require_policy(policy)
    clean = normalise(text, policy)
    if not clean:
        return []
    marker = re.compile("|".join(strip_markers)) if strip_markers else None
    boundary = re.compile(policy.sentence_boundary)
    word = re.compile(policy.word_pattern)
    guarded = policy.sentence_abbreviation_guard == ABBREVIATION_GUARD
    parts: list[str] = []
    for line in clean.split("\n"):
        if marker is not None:
            line = marker.sub("", line, count=1)
        line = line.strip()
        if not line:
            continue
        parts.extend(part.strip()
                     for part in rules.split_line(line, boundary, guarded=guarded)
                     if word.search(part))
    if parts:
        return parts
    return [clean] if word.search(clean) else []


def sentence_lengths(text: Any, policy: TextPolicy,
                     strip_markers: Sequence[str] = ()) -> list[int]:
    """The frozen length unit: word tokens per sentence, in order."""
    return [len(word_tokens(part, policy))
            for part in split_sentences(text, policy, strip_markers)]


def token_multiset(text: Any, policy: TextPolicy) -> Mapping[str, int]:
    """Folded token -> occurrence count, the feature the clauses constrain."""
    counts: dict[str, int] = {}
    for token in folded_tokens(text, policy):
        counts[token] = counts.get(token, 0) + 1
    return counts


# ------------------------------------------------------- the inheritance audit
#
# Every place the corrected semantics differ from the inherited ones, with the
# demonstrated defect each difference repairs. Section 11.3 requires a differential
# disagreement to be "justified as an intentional correction"; this is that
# justification, in a form a test can range over.

INTENTIONAL_CORRECTIONS: tuple[Mapping[str, str], ...] = (
    {"id": "unicode-word-pattern",
     "inherited": r"WORD_PATTERN = [A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*",
     "corrected": "a Unicode-aware word pattern",
     "defect": ("'café' tokenised as 'caf', so a mandatory word containing a "
                "non-ASCII letter could never be matched and that parameter "
                "realisation was an impossible composition (section 4.3)")},
    {"id": "strip-format-characters",
     "inherited": "whitespace collapse over \\s, which excludes U+200B and U+00AD",
     "corrected": "remove Unicode categories Cf and Cc before tokenising",
     "defect": ("a zero-width space split a repeated word into distinct tokens, so "
                "the Pair 2 focal rule passed while a word repeated; section 10.6 "
                "names zero-width characters as required audit material")},
    {"id": "single-case-rule",
     "inherited": "str.lower in the verifiers, str.casefold in the encoding",
     "corrected": "casefold everywhere",
     "defect": ("the encoding required one distinct mandatory token where the "
                "verifier looked for two, for example the set ('ß', 'SS')")},
    {"id": "unicode-sentence-survival",
     "inherited": r"a segment survives only if it matches [A-Za-z0-9]",
     "corrected": "a segment survives if it contains a word token",
     "defect": ("a list item written in a non-Latin script was an item and not a "
                "sentence, which made the solver's n_sentences >= n_items axiom "
                "unsound and produced unsat for compositions both verifiers accept")},
    {"id": "shared-marker-definition",
     "inherited": "LIST_MARKER hard-coded inside split_sentences",
     "corrected": "the frozen list grammar supplies its markers to the segmenter",
     "defect": ("the sentence span and the list span carried two independent "
                "notions of a marker, so changing the list grammar silently changed "
                "Pair 3's sentence count")},
)
