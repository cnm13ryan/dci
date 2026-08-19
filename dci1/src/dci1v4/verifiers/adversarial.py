"""Targeted adversarial corpus and realised boundary-case incidence (§24).

§24 asks two different questions and this module answers both:

* item 3 — *run a targeted adversarial corpus over the enumerated cases*:
  ``build_corpus`` composes each frozen boundary case with natural filler and
  with the other cases, so the enumerated features are exercised in
  combination rather than only in isolation;
* item 4 — *quantify how often each case occurs in genuine generations from
  the calibration stages, per cell type*: ``case_incidence`` runs the same
  detectors over real responses and returns a per-cell-type frequency table.

The detectors are structural predicates over the response text. They are
diagnostic instruments only: nothing here scores a constraint, and no
detector output ever reaches a verdict or an estimand.
"""
from __future__ import annotations

import random
import unicodedata
from typing import Iterable

from dci1v4.protocol.seeds import ADVERSARIAL_SEED
from dci1v4.verifiers.boundary import FOCAL_CASES, TARGET_CASES
from dci1v4.verifiers.words import alpha_runs

TARGET = "however"

_ZERO_WIDTH = "​‌‍⁠﻿"
_UNICODE_PUNCT = "‘’“”–—…"
_LOOKALIKES = "аеорсхАЕОΗ"

FILLER = (
    "The question asks for a short explanation in plain words.",
    "Most accounts agree on the outline and differ on the detail.",
    "One useful way to think about it is to start from the ordinary case.",
)


def _has_zero_width(text: str) -> bool:
    return any(ch in _ZERO_WIDTH for ch in text)


def _has_unicode_punctuation(text: str) -> bool:
    return any(ch in _UNICODE_PUNCT for ch in text)


def _has_lookalike(text: str) -> bool:
    return any(ch in _LOOKALIKES for ch in text)


def _has_combining_mark(text: str) -> bool:
    return any(unicodedata.combining(ch) for ch in text)


def _has_soft_or_nbsp(text: str) -> bool:
    return "­" in text or " " in text


def _target_capitalised(text: str) -> bool:
    return any(run.lower() == TARGET and run != TARGET
               for run in alpha_runs(text))


def _target_in_longer_word(text: str) -> bool:
    return any(TARGET in run.lower() and run.lower() != TARGET
               for run in alpha_runs(text))


def _hyphenated(text: str) -> bool:
    return any(a.isalpha() and b == "-" for a, b in zip(text, text[1:]))


def _apostrophised(text: str) -> bool:
    return any(a.isalpha() and b in "'’" for a, b in zip(text, text[1:]))


def _non_latin(text: str) -> bool:
    return any(ch.isalpha() and not ("a" <= ch.lower() <= "z")
               for ch in text)


def _digit_adjacent(text: str) -> bool:
    return any((a.isalpha() and b.isdigit()) or (a.isdigit() and b.isalpha())
               for a, b in zip(text, text[1:]))


def _markdown(text: str) -> bool:
    return "**" in text or "__" in text or "*" in text or "_" in text


def _empty(text: str) -> bool:
    return not alpha_runs(text)


def _single_token(text: str) -> bool:
    return len(alpha_runs(text)) == 1


def _repeated_word(text: str) -> bool:
    runs = [r.lower() for r in alpha_runs(text)]
    return any(a == b for a, b in zip(runs, runs[1:]))


def _sentence_boundary_run(text: str) -> bool:
    return any(a in ".!?" and b.isalpha() for a, b in zip(text, text[1:]))


#: Enumerated §24 case -> structural detector.
DETECTORS = {
    "empty-output": _empty,
    "single-token-output": _single_token,
    "adjacent-punctuation": lambda t: any(
        a.isalpha() and b in ",.;:!?" for a, b in zip(t, t[1:])),
    "capitalisation-of-target": _target_capitalised,
    "target-inside-longer-word": _target_in_longer_word,
    "concatenated-copies": lambda t: t.lower().count(TARGET * 2) > 0,
    "hyphenation": _hyphenated,
    "apostrophised-form": _apostrophised,
    "non-latin-script": _non_latin,
    "unicode-punctuation": _has_unicode_punctuation,
    "unicode-lookalikes": _has_lookalike,
    "zero-width-characters": _has_zero_width,
    "combining-marks": _has_combining_mark,
    "non-breaking-and-soft-hyphen": _has_soft_or_nbsp,
    "digits-adjacent-to-words": _digit_adjacent,
    "markdown-emphasis": _markdown,
    "repeated-words": _repeated_word,
    "sentence-boundary-punctuation": _sentence_boundary_run,
}


def build_corpus(size_per_case: int = 4) -> list[dict]:
    """A seeded adversarial corpus exercising every enumerated case, alone and
    combined with filler and with a second case."""
    rng = random.Random(ADVERSARIAL_SEED)
    seeds = [(c["case_id"], c["text"]) for c in TARGET_CASES]
    seeds += [(c["case_id"], c["text"]) for c in FOCAL_CASES]
    corpus: list[dict] = []
    for case_id, text in seeds:
        for index in range(size_per_case):
            if index == 0:
                built = text
            elif index == 1:
                built = f"{rng.choice(FILLER)} {text}"
            elif index == 2:
                other = rng.choice(seeds)[1]
                built = f"{text} {other}"
            else:
                other = rng.choice(seeds)[1]
                built = f"{rng.choice(FILLER)} {text} {other} " \
                        f"{rng.choice(FILLER)}"
            corpus.append({"corpus_id": f"{case_id}:{index}", "seed_case":
                           case_id, "text": built})
    return corpus


def case_incidence(texts: Iterable[str]) -> dict[str, dict[str, float]]:
    """Counts and rates of every enumerated case over a set of responses."""
    texts = list(texts)
    total = len(texts)
    out: dict[str, dict[str, float]] = {}
    for label, detector in DETECTORS.items():
        hits = sum(1 for t in texts if detector(t))
        out[label] = {"count": hits,
                      "rate": (hits / total) if total else 0.0}
    return out


def incidence_by_cell_type(rows: Iterable[dict]) -> dict[str, dict]:
    """§24 item 4: realised frequency of each enumerated case per cell type."""
    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(row["cell_type"], []).append(row["raw_response"])
    return {cell_type: {"responses": len(texts),
                        "cases": case_incidence(texts)}
            for cell_type, texts in sorted(grouped.items())}


def corpus_coverage(size_per_case: int = 4) -> dict[str, int]:
    """Every enumerated case must be exercised by the built corpus."""
    corpus = build_corpus(size_per_case)
    counts = {label: sum(1 for item in corpus if detector(item["text"]))
              for label, detector in DETECTORS.items()}
    missing = [label for label, count in counts.items() if count == 0]
    if missing:
        raise AssertionError(f"adversarial corpus exercises none of {missing}")
    return counts
