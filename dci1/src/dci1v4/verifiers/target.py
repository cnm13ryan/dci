"""Exact-count rules S0–S3 for the target word (v4r2 §9.2).

S0 is the registered rule for constraint A and applies unchanged in every
cell; S1–S3 are declared alternatives for the robustness family and never
redefine X_A. The construct string and every counting-function source are
carried byte-identically from the closed v3 instrument
(dci1v3/verifiers/target.py) under the §10.2 carry-over rule;
``dci1v4.carryover`` verifies the identity and refuses on drift. Pass and
graded-score mappings live in ``dci1v4.compliance`` (§7.4), not here.
"""
from __future__ import annotations

from dci1v4.verifiers.words import alpha_runs

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
