"""The compliance-vector primitive (v4r3 §7.6, §9.1, §9.3).

For a generation the primitive observation is the vector of per-constraint
scores -- boolean pass ``X_c``, graded score ``G_c`` in [0, 1], non-vacuity,
processing state -- plus the generation-level degeneracy record.

Two things differ from v4r2's version and both are registered:

**Presence.** §9.1 records a verdict for every registered constraint instance
the replication uses, marked ``present`` or not. A verdict on an absent
constraint is a *chance* observation (§25) and is the numerator of the
registered difficulty coordinate (§13.3). No estimand reads a chance
observation as a treated one, and ``assert_no_chance_in_treated`` puts that on
the mandatory path.

**Four predicate forms.** Count budgets pass at ``S <= q``; rate budgets at
``100*S/W <= q``, and **a wordless answer has no rate and fails**, which is
the property the rate form was added for; count lower bounds pass at
``S >= q``; rate lower bounds at ``100*S/W >= q``, and a wordless answer
fails those too.

Vacuous passes stay passes (§9.3). A verifier-processing failure fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from dci1v4.errors import InstrumentError
from dci1v4.verifiers.target import s0_count

from dci1v4r3.verifiers.constraints import (
    FAMILIES, FORM_COUNT, FORM_LOWER_BOUND, FORM_RATE, FORM_RATE_LOWER_BOUND,
    LOWER_BOUND_FORMS, Constraint,
)
from dci1v4r3.verifiers.statistics import (
    alpha_runs, family_statistic, focal_statistic, word_count,
)

__all__ = ["NON_VACUITY_MIN_WORDS", "ConstraintScore", "GenerationScores",
           "score_generation", "passes", "graded", "non_vacuous",
           "assert_no_chance_in_treated"]

#: §9.3: below this many words a budget pass is vacuous. The topic space asks
#: for 60-120 word answers and, from v4r3 on, the prompt says so (§8.5). The
#: value is fixed pre-freeze and is never tuned to a realised rate.
NON_VACUITY_MIN_WORDS = 20


@dataclass(frozen=True)
class ConstraintScore:
    """One component of the compliance vector."""

    kind: str
    severity: int
    statistic: int | None
    passed: bool                 # X_c
    graded: float                # G_c in [0, 1]
    non_vacuous: bool
    vacuous_pass: bool
    processing_failure: bool
    #: §9.1. False means this verdict came from a prompt that did not state
    #: the constraint: a CHANCE observation, never a treated one.
    present: bool = True
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
    #: §8.5's diagnostic: did the answer land in the stem's 60-120 word band?
    in_stem_band: bool
    load: int                    # 0, 1 or 2 numbered constraints


def _statistic(constraint: Constraint, text: str) -> int:
    if constraint.kind == "A":
        return s0_count(text)
    if constraint.kind == "B":
        return focal_statistic(text)
    return family_statistic(constraint.kind, text)


def passes(constraint: Constraint, statistic: int, text: str) -> bool:
    """§7.3's four predicate forms, and the two outcome rules."""
    q = constraint.severity
    if constraint.kind == "A":
        return statistic == q
    if constraint.kind == "B":
        return statistic <= q
    form = FAMILIES[constraint.kind].form
    if form == FORM_COUNT:
        return statistic <= q
    if form == FORM_LOWER_BOUND:
        return statistic >= q
    if form in (FORM_RATE, FORM_RATE_LOWER_BOUND):
        words = word_count(text)
        if words == 0:
            # A wordless answer has no rate. It fails, and that is the whole
            # point of the form: the empty string passes 94 of 94 count
            # severities and none of the rate severities.
            return False
        rate = 100.0 * statistic / words
        return rate <= q if form == FORM_RATE else rate >= q
    raise InstrumentError(f"unknown predicate form {form!r}")


def graded(constraint: Constraint, statistic: int, text: str) -> float:
    """§7.6, verbatim per constraint form."""
    q = constraint.severity
    if constraint.kind == "A":
        return max(0.0, 1.0 - abs(statistic - q) / q)
    if constraint.kind == "B":
        words = alpha_runs(text)
        if not words:
            return 0.0
        over = sum(1 for w in words if len(w) > q)
        return 1.0 - over / len(words)
    form = FAMILIES[constraint.kind].form
    if form == FORM_COUNT:
        return min(1.0, q / max(q, statistic)) if q > 0 else float(statistic == 0)
    if form == FORM_LOWER_BOUND:
        return min(1.0, statistic / q) if q > 0 else 1.0
    if form == FORM_RATE:
        words = word_count(text)
        if words == 0:
            return 0.0
        rate = 100.0 * statistic / words
        return min(1.0, q / max(q, rate)) if rate else 1.0
    if form == FORM_RATE_LOWER_BOUND:
        words = word_count(text)
        if words == 0:
            return 0.0
        rate = 100.0 * statistic / words
        return min(1.0, rate / q) if q > 0 else 1.0
    raise InstrumentError(f"unknown predicate form {form!r}")


def non_vacuous(constraint: Constraint, text: str, *, truncated: bool) -> bool:
    """§9.3's predicate, by constraint form.

    A lower-bound constraint carries no word-count clause: its own rule
    already forces length upward, so a 20-word clause would be redundant
    rather than protective.
    """
    if not text.strip():
        return False
    if truncated:
        return False
    if constraint.kind == "A":
        return True
    if constraint.kind != "B" and \
            FAMILIES[constraint.kind].form in LOWER_BOUND_FORMS:
        return True
    return word_count(text) >= NON_VACUITY_MIN_WORDS


def _score_one(constraint: Constraint, text: str, *, truncated: bool,
               present: bool, position: int | None) -> ConstraintScore:
    try:
        statistic = _statistic(constraint, text)
    except Exception:                                # pragma: no cover
        return ConstraintScore(constraint.kind, constraint.severity, None,
                               False, 0.0, False, False, True, present,
                               position)
    ok = passes(constraint, statistic, text)
    nv = non_vacuous(constraint, text, truncated=truncated)
    return ConstraintScore(
        kind=constraint.kind, severity=constraint.severity,
        statistic=statistic, passed=ok, graded=graded(constraint, statistic, text),
        non_vacuous=nv, vacuous_pass=bool(ok and not nv),
        processing_failure=False, present=present, position=position)


def score_generation(text: str, *, present: Sequence[Constraint],
                     absent: Sequence[Constraint] = (),
                     truncated: bool = False,
                     finish_reason: str | None = None,
                     token_count: int | None = None) -> GenerationScores:
    """The §9.1 primitive for one generation.

    ``present`` are the numbered constraints the prompt stated, in prompt
    order; ``absent`` are the other registered instances this replication
    uses, scored to give §25's chance verdicts on the same rows.
    """
    if len(present) > 2:
        raise InstrumentError("load is fixed at 0, 1 or 2 (§1, §8.1)")
    words = alpha_runs(text)
    scores = [
        _score_one(c, text, truncated=truncated, present=True, position=i + 1)
        for i, c in enumerate(present)
    ] + [
        _score_one(c, text, truncated=truncated, present=False, position=None)
        for c in absent
    ]
    return GenerationScores(
        scores=tuple(scores), empty=not text.strip(), word_count=len(words),
        truncated=truncated, finish_reason=finish_reason,
        token_count=token_count,
        in_stem_band=60 <= len(words) <= 120, load=len(present))


def assert_no_chance_in_treated(scores: Iterable[ConstraintScore]) -> None:
    """§9.1: a treated estimand never reads a chance verdict.

    Called by every estimator that forms a delivery loss, so a chance
    observation cannot reach one by being handed to the wrong function.
    """
    stray = [f"{s.kind}:{s.severity}" for s in scores if not s.present]
    if stray:
        raise InstrumentError(
            "these verdicts came from prompts that did not state the "
            f"constraint and are chance observations, not treated ones: "
            f"{stray}")
