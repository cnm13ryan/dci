"""The compliance-vector primitive (v4r2 §7.4, §9.1, §9.3).

For a generation whose prompt contains constraints c1…ck, the primitive
observation is the vector of per-constraint scores — boolean pass X_c,
graded score G_c in [0,1], non-vacuity, and processing state — plus the
generation-level degeneracy record: emptiness, word count, token count,
finish reason, truncation, and the accidental count of the exact-count
target word in cells where A is absent. Nothing is marginalised at record
time and no constraint is privileged (§9.1).

Vacuous passes stay passes (§9.3): response shortening under composition is
a candidate mechanism, so the predicate flags them for the vacuity family
and the partial-identification recomputation instead of filtering them.
A verifier-processing failure fails closed: pass False, graded 0.0.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from dci1v4.constraints import Constraint
from dci1v4.errors import InstrumentError
from dci1v4.statistics import FAMILY_STATISTICS, focal_statistic
from dci1v4.target import s0_count
from dci1v4.words import alpha_runs, words_lower

#: §9.3: below this many words a non-violation pass is vacuous. The topic
#: space asks for 60–120 word answers; the value is fixed pre-freeze and is
#: never tuned to a realised rate.
NON_VACUITY_MIN_WORDS = 20


@dataclass(frozen=True)
class ConstraintScore:
    """One component of the compliance vector."""

    kind: str
    severity: int
    statistic: int | None       # realised count / max word length; None on failure
    passed: bool                # X_c
    graded: float               # G_c in [0, 1]
    non_vacuous: bool           # §9.3 predicate for this constraint form
    vacuous_pass: bool          # passed and not non_vacuous
    processing_failure: bool    # verifier raised; scored fail-closed
    position: int | None = None  # 1-based position in the prompt's list


@dataclass(frozen=True)
class GenerationScores:
    """The full per-generation record: vector plus degeneracy flags."""

    scores: tuple[ConstraintScore, ...]
    empty: bool
    word_count: int
    truncated: bool
    finish_reason: str | None
    token_count: int | None
    accidental_s0: int | None   # only recorded where A is absent (§9.3)


def _statistic(constraint: Constraint, text: str) -> int:
    if constraint.kind == "A":
        return s0_count(text)
    if constraint.kind == "B":
        return focal_statistic(text)
    return FAMILY_STATISTICS[constraint.kind](text)


def _passed(constraint: Constraint, statistic: int) -> bool:
    if constraint.kind == "A":
        return statistic == constraint.severity
    return statistic <= constraint.severity


def _graded(constraint: Constraint, statistic: int, text: str) -> float:
    """§7.4, verbatim per constraint form."""
    if constraint.kind == "A":
        n = constraint.severity
        return max(0.0, 1.0 - abs(statistic - n) / n)
    if constraint.kind == "B":
        words = words_lower(text)
        if not words:
            return 0.0
        over = sum(1 for w in words if len(w) > constraint.severity)
        return 1.0 - over / len(words)
    q = constraint.severity
    if q == 0:
        return 1.0 if statistic == 0 else 0.0
    return min(1.0, q / max(q, statistic))


def _non_vacuous(constraint: Constraint, word_count: int,
                 truncated: bool) -> bool:
    """§9.3 predicate per constraint form."""
    if constraint.kind == "A":
        return word_count > 0 and not truncated
    return (word_count > 0 and not truncated
            and word_count >= NON_VACUITY_MIN_WORDS)


def score_constraint(constraint: Constraint, text: str, *,
                     truncated: bool) -> ConstraintScore:
    """Score one constraint on one response; deterministic and fail-closed."""
    word_count = len(alpha_runs(text))
    non_vacuous = _non_vacuous(constraint, word_count, truncated)
    try:
        statistic = _statistic(constraint, text)
        passed = _passed(constraint, statistic)
        graded = _graded(constraint, statistic, text)
    except Exception:
        return ConstraintScore(
            kind=constraint.kind, severity=constraint.severity,
            statistic=None, passed=False, graded=0.0, non_vacuous=False,
            vacuous_pass=False, processing_failure=True)
    return ConstraintScore(
        kind=constraint.kind, severity=constraint.severity,
        statistic=statistic, passed=passed, graded=graded,
        non_vacuous=non_vacuous, vacuous_pass=passed and not non_vacuous,
        processing_failure=False)


def compliance_vector(constraints: Sequence[Constraint], text: str, *,
                      truncated: bool, finish_reason: str | None = None,
                      token_count: int | None = None) -> GenerationScores:
    """Score every constraint present in the prompt (§9.1)."""
    if not constraints:
        raise InstrumentError("a generation carries at least one constraint")
    kinds = [c.kind for c in constraints]
    if len(set(kinds)) != len(kinds):
        raise InstrumentError(f"duplicate constraint kinds in {kinds}")
    scores = tuple(
        replace(score_constraint(c, text, truncated=truncated), position=i)
        for i, c in enumerate(constraints, start=1))
    word_count = len(alpha_runs(text))
    return GenerationScores(
        scores=scores,
        empty=word_count == 0,
        word_count=word_count,
        truncated=truncated,
        finish_reason=finish_reason,
        token_count=token_count,
        accidental_s0=None if "A" in kinds else s0_count(text))
