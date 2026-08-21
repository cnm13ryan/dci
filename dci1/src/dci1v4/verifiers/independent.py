"""Independent reimplementation of every registered v4 instrument (§10.2, C1).

**Source material: the registered prose of v4r2 §7.1, §7.2, §7.4, §9.2 and
§9.3, and nothing else.** This module deliberately imports nothing from
``dci1v4.verifiers`` and nothing from any DCI implementation, so it cannot
inherit a defect from the primary source by construction; ``tests_v4`` asserts
that emptiness of its import set. It is written against a different mechanism
— ``unicodedata`` category tests and grouped runs rather than the primary's
``str.isalpha`` accumulator loop — so an agreement of exactly 1.000 is evidence
about the rule rather than about a shared line of code.

The prose it implements, transcribed:

* §7.2 — "A word is a maximal run of alphabetic characters; suffix and letter
  tests use the lower-cased word; comma and upper-case counts read raw
  characters."

**Segmentation, corrected 2026-08-20.** This module first read "alphabetic" as
the regular-expression class ``[^\\W\\d_]`` --- a word character that is neither a
decimal digit nor an underscore. That is not the alphabetic characters. It also
admits every non-decimal numeric: 1,151 characters in categories ``No`` and
``Nl``, among them the subscripts, superscripts, fractions and Roman numerals.
The registered prose says alphabetic, and the primary agrees with the prose, so
the defect was here and not there. It surfaced on a genuine generation, the
text ``Answer: H2O`` with a subscript two, where the class ran ``H``, the
subscript and ``O`` together into one word and RF3 --- at most q words with one
letter --- then read 0 where the primary reads 2. Segmentation now consults
``unicodedata.category``: Python defines ``str.isalpha`` as general category
``Lm``, ``Lt``, ``Lu``, ``Ll`` or ``Lo``, so the category test is the same
registered property reached by a route that shares no code with the primary's
``ch.isalpha()`` accumulator loop.
* §7.1 — A: "Use the word *however* exactly n times." B: "Every word in the
  answer must have at most m letters."
* §7.2 table — RF1 begin with the letter b; RF2 end with the letters ing;
  RF3 have one letter; RF4 contain two identical adjacent letters; RF5 comma
  characters; RF6 upper-case English letters; RF7 contain the letter a;
  RF8 end with the letter y. All of the form "at most q".
* §9.2 — S0: "take the whole response, lower-case it, find every maximal run
  of alphabetic characters, count the runs equal to `however`, and pass when
  the count equals n." S1 omits the lower-casing step; S2 counts
  non-overlapping substring occurrences in the lower-cased text; S3 applies
  S0 after deleting a leading colon-terminated line and any line repeating an
  active constraint wording.
* §7.4 — graded scores: A, max(0, 1 - |s0 - n| / n); B, 1 - (words longer
  than m) / (total words), and 0 for an empty answer; RF, min(1, q / max(q,
  realised count)) for q > 0 and 1[count = 0] for q = 0.
* §9.3 — non-vacuity: A, non-empty and not truncated; B and RF, non-empty,
  not truncated, and at least 20 words.
"""
from __future__ import annotations

import unicodedata
from itertools import groupby

TARGET = "however"
MIN_WORDS_NON_VACUOUS = 20


def _alphabetic(ch: str) -> bool:
    """§7.2's "alphabetic": Unicode general category L (see the module note)."""
    return unicodedata.category(ch).startswith("L")


def words(text: str) -> list[str]:
    """Maximal runs of alphabetic characters, grouped rather than scanned."""
    return ["".join(run) for is_alpha, run in groupby(text, _alphabetic)
            if is_alpha]


def lower_words(text: str) -> list[str]:
    return words(text.lower())


# ------------------------------------------------------------------ §9.2 S0-S3
def s0(text: str) -> int:
    return lower_words(text).count(TARGET)


def s1(text: str) -> int:
    return words(text).count(TARGET)


def s2(text: str) -> int:
    lowered, count, start = text.lower(), 0, 0
    while True:
        found = lowered.find(TARGET, start)
        if found < 0:
            return count
        count += 1
        start = found + len(TARGET)


def s3(text: str, active_wordings: tuple[str, ...]) -> int:
    lines = text.split("\n")
    while lines:
        first = next((i for i, line in enumerate(lines) if line.strip()), None)
        if first is None or not lines[first].strip().endswith(":"):
            break
        del lines[first]
    active = [w.lower() for w in active_wordings if w]
    kept = [line for line in lines
            if not any(w in line.lower() for w in active)]
    return s0("\n".join(kept))


# ------------------------------------------------------- §7.1-§7.2 statistics
def longest_word(text: str) -> int:
    return max((len(w) for w in lower_words(text)), default=0)


def rf_count(family: str, text: str) -> int:
    if family == "RF5":
        return text.count(",")
    if family == "RF6":
        return sum(1 for ch in text if "A" <= ch <= "Z")
    ws = lower_words(text)
    if family == "RF1":
        return sum(1 for w in ws if w[:1] == "b")
    if family == "RF2":
        return sum(1 for w in ws if w[-3:] == "ing")
    if family == "RF3":
        return sum(1 for w in ws if len(w) == 1)
    if family == "RF4":
        return sum(1 for w in ws
                   if any(w[i] == w[i + 1] for i in range(len(w) - 1)))
    if family == "RF7":
        return sum(1 for w in ws if "a" in w)
    if family == "RF8":
        return sum(1 for w in ws if w[-1:] == "y")
    raise ValueError(f"unknown family {family!r}")


# -------------------------------------------------------------- pass verdicts
def passes(kind: str, severity: int, text: str) -> bool:
    if kind == "A":
        return s0(text) == severity
    if kind == "B":
        return all(len(w) <= severity for w in lower_words(text))
    return rf_count(kind, text) <= severity


# ---------------------------------------------------------------- §7.4 graded
def graded(kind: str, severity: int, text: str) -> float:
    if kind == "A":
        return max(0.0, 1.0 - abs(s0(text) - severity) / severity)
    if kind == "B":
        ws = lower_words(text)
        if len(ws) == 0:
            return 0.0
        return 1.0 - sum(1 for w in ws if len(w) > severity) / len(ws)
    count = rf_count(kind, text)
    if severity == 0:
        return 1.0 if count == 0 else 0.0
    return min(1.0, severity / max(severity, count))


# --------------------------------------------------------- §9.3 non-vacuity
def non_vacuous(kind: str, text: str, truncated: bool) -> bool:
    n_words = len(words(text))
    if n_words == 0 or truncated:
        return False
    if kind == "A":
        return True
    return n_words >= MIN_WORDS_NON_VACUOUS
