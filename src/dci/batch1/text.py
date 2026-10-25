"""Batch 1 text semantics: one word, one sentence and one paragraph rule for
every verifier in the library.

**Word.** A word is a maximal run of Unicode-alphabetic characters
(``str.isalpha``), read from the raw response. ``alpha_runs`` below is a
byte-identical copy of ``dci1v4.verifiers.words.alpha_runs``, the rule every
DCI-1 revision from v3 to v8.1 used for B; ``tests/batch1/test_text.py``
compares the two sources, so the copy cannot drift silently. Consequences,
each pinned by a test:

* digits, punctuation, whitespace, apostrophes and hyphens end a word:
  ``don't`` is ``don`` + ``t``, ``well-known`` is ``well`` + ``known``,
  ``COVID19`` is ``COVID``;
* accented and non-Latin letters are letters: ``café`` has four;
* a zero-width space (U+200B, category Cf) is not alphabetic, so it SPLITS a
  word. That is the historical behaviour and it is kept for the primary B
  verdict; ``format_characters`` counts such characters so a response that
  could exploit it is visible in the record rather than silently scored;
* no Unicode normalisation: a ligature such as U+FB01 is one letter.

Comparisons fold each word with ``str.lower`` after segmenting (the v5-v8
marker convention). Historical A folded the whole response first; the two
differ only on text containing U+0130, which is recorded as design decision
D03 in ``config.py``.

**Sentence.** Each line is split with the certified boundary rule and
abbreviation guard, ``dci.verifiers.rules.split_line``, imported rather than
copied. A part survives if it contains at least one word. A line break
always ends a sentence, so a list item or a heading is a sentence.

**Paragraph.** A maximal block of non-blank lines that contains a word.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

from dci.provenance.hashes import sha, sha_file
from dci.verifiers import rules

__all__ = ["alpha_runs", "words", "folded_words", "word_count",
           "max_word_letters", "sentences", "sentence_words", "first_word",
           "last_word", "paragraphs", "char_count", "format_characters",
           "TEXT_SEMANTICS", "text_semantics_hash"]


def alpha_runs(text: str) -> list[str]:
    """Maximal runs of alphabetic characters, in order of appearance."""
    runs: list[str] = []
    current: list[str] = []
    for ch in text:
        if ch.isalpha():
            current.append(ch)
        elif current:
            runs.append("".join(current))
            current = []
    if current:
        runs.append("".join(current))
    return runs


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def words(text: Any) -> list[str]:
    """Words as they appear, case preserved."""
    return alpha_runs(_text(text))


def folded_words(text: Any) -> list[str]:
    """Words as they are compared: segmented first, then lower-cased."""
    return [w.lower() for w in alpha_runs(_text(text))]


def word_count(text: Any) -> int:
    return len(alpha_runs(_text(text)))


def max_word_letters(text: Any) -> int:
    """B's statistic: the longest word's letter count, 0 for a wordless text."""
    return max((len(w) for w in alpha_runs(_text(text))), default=0)


def sentences(text: Any) -> list[str]:
    """Sentence spans, in order. See the module docstring for the rule."""
    out: list[str] = []
    for line in _text(text).splitlines():
        line = line.strip()
        if not line:
            continue
        for part in rules.split_line(line, guarded=True):
            part = part.strip()
            if alpha_runs(part):
                out.append(part)
    return out


def sentence_words(text: Any) -> list[list[str]]:
    """Folded words of each sentence."""
    return [folded_words(s) for s in sentences(text)]


def first_word(sentence: str) -> str:
    found = folded_words(sentence)
    return found[0] if found else ""


def last_word(sentence: str) -> str:
    found = folded_words(sentence)
    return found[-1] if found else ""


def paragraphs(text: Any) -> list[str]:
    """Blocks of consecutive non-blank lines that contain a word."""
    blocks: list[list[str]] = [[]]
    for line in _text(text).splitlines():
        if line.strip():
            blocks[-1].append(line)
        elif blocks[-1]:
            blocks.append([])
    return ["\n".join(b) for b in blocks if b and alpha_runs("\n".join(b))]


def char_count(text: Any, char: str) -> int:
    """Raw occurrences of one character. No normalisation: a full-width comma
    is not a comma, and the comma in ``1,000`` is one."""
    if len(char) != 1:
        raise ValueError(f"{char!r} is not a single character")
    return _text(text).count(char)


def format_characters(text: Any) -> int:
    """Diagnostic: characters of Unicode category Cf (zero-width space, soft
    hyphen, joiners, BOM). They split words under the rule above; this count
    gates nothing and is recorded so the effect is never invisible."""
    return sum(1 for ch in _text(text) if unicodedata.category(ch) == "Cf")


#: The declared semantics, hashed into every verifier specification.
TEXT_SEMANTICS: dict[str, Any] = {
    "word": "maximal run of str.isalpha characters over the raw response "
            "(dci1v4.verifiers.words.alpha_runs, byte-identical copy)",
    "fold": "segment, then str.lower per word",
    "normalisation": "none",
    "format_characters": "split words; counted as a diagnostic only",
    "sentence": "per line (str.splitlines), dci.verifiers.rules.split_line "
                "with the abbreviation guard; parts without a word dropped",
    "paragraph": "maximal block of non-blank lines containing a word",
    "char_count": "raw str.count of one character",
    "rules_boundary_pattern": rules.SENTENCE_BOUNDARY.pattern,
    "rules_title_abbreviations": sorted(rules.TITLE_ABBREVIATIONS),
    "rules_medial_abbreviations": sorted(rules.MEDIAL_ABBREVIATIONS),
}

_HERE = Path(__file__).resolve()


def text_semantics_hash() -> str:
    """The declaration plus the bytes of both modules that implement it."""
    return sha(["batch1/text-semantics", TEXT_SEMANTICS,
                sha_file(_HERE), sha_file(Path(rules.__file__).resolve())])
