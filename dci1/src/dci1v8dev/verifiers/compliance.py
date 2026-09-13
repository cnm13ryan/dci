"""The compliance-vector primitive for v8 (§7.9, §9.1, §9.3).

Only the numerator dispatch changes against v7: ``statistic`` reads
``dci1v8dev.verifiers.statistics.statistic_for``, so A is scored by
``count_marker(text, "however")`` and no longer by ``s0_count``. The five
predicate forms, the graded scores, the non-vacuity predicate, the presence
rule and both refusal checks are v7's own functions --- they take the
statistic as an argument and never compute one --- and are re-exported
rather than restated so the rule text has one source.
"""
from __future__ import annotations

from typing import Sequence

from dci1v4.errors import InstrumentError
from dci1v7.verifiers.compliance import (
    NON_VACUITY_MIN_WORDS, STEM_BAND, ConstraintScore, GenerationScores,
    assert_no_chance_in_treated, assert_presence_rule, chance_verdicts,
    graded, non_vacuous, passes, treated_verdicts,
)
from dci1v7.verifiers.constraints import Constraint

from dci1v8dev.verifiers.statistics import alpha_runs, statistic_for

__all__ = ["NON_VACUITY_MIN_WORDS", "STEM_BAND", "ConstraintScore",
           "GenerationScores", "statistic", "score_generation", "passes",
           "graded", "non_vacuous", "assert_no_chance_in_treated",
           "assert_presence_rule", "chance_verdicts", "treated_verdicts"]


def statistic(constraint: Constraint, text: str) -> int:
    """The numerator of ``constraint`` on ``text``, through the v8 dispatch."""
    return statistic_for(constraint)(text)


def _score_one(constraint: Constraint, text: str, *, truncated: bool,
               present: bool, position: int | None) -> ConstraintScore:
    try:
        value = statistic(constraint, text)
    except Exception:                                # pragma: no cover
        return ConstraintScore(constraint.kind, constraint.severity, None,
                               False, 0.0, False, False, True, present,
                               position)
    ok = passes(constraint, value, text)
    nv = non_vacuous(constraint, text, truncated=truncated)
    return ConstraintScore(
        kind=constraint.kind, severity=constraint.severity,
        statistic=value, passed=ok,
        graded=graded(constraint, value, text), non_vacuous=nv,
        vacuous_pass=bool(ok and not nv), processing_failure=False,
        present=present, position=position)


def score_generation(text: str, *, present: Sequence[Constraint],
                     absent: Sequence[Constraint] = (),
                     truncated: bool = False,
                     finish_reason: str | None = None,
                     token_count: int | None = None) -> GenerationScores:
    """The §9.1 primitive for one generation, as v7's, over the v8 numerators."""
    if len(present) > 2:
        raise InstrumentError("load is fixed at 0, 1 or 2 (§1, §8.1)")
    present_labels = [f"{c.kind}:{c.severity}" for c in present]
    overlap = [c for c in absent if f"{c.kind}:{c.severity}" in present_labels]
    if overlap:
        raise InstrumentError(
            "§9.1: an instance cannot be both present and absent in one "
            f"generation; {[f'{c.kind}:{c.severity}' for c in overlap]}")
    words = alpha_runs(text)
    scores = [
        _score_one(c, text, truncated=truncated, present=True, position=i + 1)
        for i, c in enumerate(present)
    ] + [
        _score_one(c, text, truncated=truncated, present=False, position=None)
        for c in absent
    ]
    lo, hi = STEM_BAND
    return GenerationScores(
        scores=tuple(scores), empty=not text.strip(), word_count=len(words),
        truncated=truncated, finish_reason=finish_reason,
        token_count=token_count, in_stem_band=lo <= len(words) <= hi,
        load=len(present))
