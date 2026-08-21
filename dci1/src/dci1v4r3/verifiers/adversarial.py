"""§10.2's adversarial corpus and §24's realised-frequency report.

Agreement between two implementations on a corpus of easy text is weak
evidence. The corpus below is built to be hard: every enumerated boundary
phenomenon appears, and the realised frequency of each in **genuine
generations** is reported beside it, so a reader can see which of the hard
cases the models actually produce and which are hypothetical.

The realised-frequency half is the part that matters and the part that is easy
to skip. A phenomenon with realised frequency zero -- U+0130 is the example
this revision turns on -- is one the instrument has never been tested on by
the data, and saying so is more useful than a corpus that quietly implies
otherwise.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

from dci1v4r3.verifiers.boundary import ALL_CASES
from dci1v4r3.verifiers.statistics import STATISTICS, word_count

__all__ = ["PHENOMENA", "realised_frequency", "run_adversarial_corpus"]

#: §24's enumeration as detectors over response text. Each is a predicate, so
#: the same definition drives both the corpus check and the frequency report
#: and the two cannot drift.
PHENOMENA: dict[str, Any] = {
    "empty": lambda t: not t.strip(),
    "wordless": lambda t: bool(t.strip()) and word_count(t) == 0,
    "single_word": lambda t: word_count(t) == 1,
    "adjacent_punctuation": lambda t: bool(re.search(r"\w[,.;:!?]\w", t)),
    "hyphenated": lambda t: "-" in t,
    "apostrophised": lambda t: "'" in t or "’" in t,
    "non_latin_script": lambda t: any(ord(c) > 0x2FF and c.isalpha()
                                      for c in t),
    "unicode_punctuation": lambda t: any(c in "–—‘’"
                                         "“”…" for c in t),
    "zero_width": lambda t: any(c in "​‌‍﻿" for c in t),
    "soft_hyphen": lambda t: "­" in t,
    "non_breaking_space": lambda t: " " in t,
    "combining_mark": lambda t: any(0x300 <= ord(c) <= 0x36F for c in t),
    "non_decimal_numeric": lambda t: any(c.isnumeric() and not c.isdigit()
                                         for c in t),
    "fullwidth": lambda t: any(0xFF01 <= ord(c) <= 0xFF5E for c in t),
    "markdown_emphasis": lambda t: "**" in t or "__" in t,
    "case_folding_split": lambda t: "İ" in t,
    "repeated_word": lambda t: bool(re.search(r"\b(\w+)\s+\1\b", t.lower())),
    "capitalisation": lambda t: STATISTICS["capital_char"](t) > 0,
}


def realised_frequency(texts: Iterable[str]) -> dict[str, Any]:
    """How often each enumerated phenomenon occurs in real responses."""
    counts = {name: 0 for name in PHENOMENA}
    total = 0
    for text in texts:
        total += 1
        for name, detector in PHENOMENA.items():
            if detector(text):
                counts[name] += 1
    return {"responses": total,
            "counts": counts,
            "rates": {k: (v / total if total else 0.0)
                      for k, v in counts.items()},
            "never_observed": sorted(k for k, v in counts.items() if v == 0)}


def run_adversarial_corpus(genuine_texts: Iterable[str] = ()) -> dict[str, Any]:
    """The corpus check, plus §24's realised-frequency report."""
    corpus = [case["text"] for case in ALL_CASES]
    covered = {name: sum(1 for t in corpus if detector(t))
               for name, detector in PHENOMENA.items()}
    uncovered = sorted(k for k, v in covered.items() if v == 0)
    return {"corpus_size": len(corpus),
            "corpus_coverage": covered,
            "uncovered_by_corpus": uncovered,
            "realised": realised_frequency(genuine_texts),
            "passed": not uncovered}
