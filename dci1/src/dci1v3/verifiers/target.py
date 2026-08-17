"""Target scoring rules S0–S3 (§9) and the graded count.

Each rule is a deterministic pure function of the response text (S3 also of
the active constraint wordings, design quantities fixed before generation).
None receives an arm label, an added-constraint identity, or another
verifier's output (§10, discriminant validity; §24 of the implementation
prompt). The caller maps a count to pass/failure via ``passes``; every
non-pass state — wrong count, empty response, refusal, truncation,
verifier-processing failure — is failure and stays in the analysis.

``s0_count`` is byte-identical (function source) to the v2 instrument that
produced the E2B Gate 1 packet (§10 carry-over rule).
"""
from __future__ import annotations

from dci1v3.verifiers.words import alpha_runs

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
    """S3 preprocessing (§9): registered removal of leading colon-ended
    preamble lines and constraint-restatement lines, then S0 applies.

    (1) While the first line with non-empty stripped text ends with a colon,
    delete that line. (2) Delete every line whose lower-cased text contains
    the lower-cased full text of any active constraint wording.
    """
    lines = text.split("\n")
    while lines:
        first_nonempty = next((i for i, l in enumerate(lines) if l.strip()),
                              None)
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
    """The recorded graded quantity |count − n| (§9)."""
    return abs(count - n)


def passes(count: int, n: int) -> bool:
    """Pass exactly when the count equals n; every other state is failure."""
    return count == n
