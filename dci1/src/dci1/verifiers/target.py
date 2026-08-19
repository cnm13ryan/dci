"""Target-constraint scoring rules S0–S3 (prereg §9) and the graded count.

Every rule is a deterministic pure function of the response text (S3 also of
the active constraint wordings, which are design quantities fixed before
generation). None receives an arm label, an added-constraint identity, or any
other verifier's output (prereg §10, discriminant validity).

Failure semantics: the *caller* maps a count to pass/failure via ``s0_pass``
etc.; an empty response, a refusal, or a truncated response simply yields its
literal count (usually 0 ≠ n → failure), exactly as §9 requires — no state is
ever removed from the analysis.
"""
from __future__ import annotations

from dci1.verifiers.words import alpha_runs

TARGET_WORD = "however"


def s0_count(text: str) -> int:
    """S0: lower-case, maximal alphabetic runs, count runs equal to 'however'."""
    return sum(1 for run in alpha_runs(text.lower()) if run == TARGET_WORD)


def s1_count(text: str) -> int:
    """S1: the same procedure without the lower-casing step."""
    return sum(1 for run in alpha_runs(text) if run == TARGET_WORD)


def s2_count(text: str) -> int:
    """S2: non-overlapping occurrences of the substring anywhere, lower-cased."""
    return text.lower().count(TARGET_WORD)


def s3_preprocess(text: str, constraint_wordings: tuple[str, ...]) -> str:
    """S3 preprocessing (D17).

    (1) While the first line with non-empty stripped text ends with a colon,
    delete that line. (2) Delete every line whose lower-cased text contains the
    lower-cased full text of any active constraint wording. Then S0 applies.
    """
    lines = text.split("\n")
    while lines:
        first_nonempty = next((i for i, l in enumerate(lines) if l.strip()), None)
        if first_nonempty is None:
            break
        if lines[first_nonempty].strip().endswith(":"):
            del lines[first_nonempty]
        else:
            break
    lowered_wordings = tuple(w.lower() for w in constraint_wordings if w)
    kept = [l for l in lines
            if not any(w in l.lower() for w in lowered_wordings)]
    return "\n".join(kept)


def s3_count(text: str, constraint_wordings: tuple[str, ...]) -> int:
    return s0_count(s3_preprocess(text, constraint_wordings))


def graded(count: int, n: int) -> int:
    """The recorded graded quantity |count − n| (prereg §9)."""
    return abs(count - n)


def passes(count: int, n: int) -> bool:
    """Pass exactly when the count equals n; every other state is failure."""
    return count == n
