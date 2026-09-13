"""The compliance-vector primitive (§7.9, §9.1, §9.3).

For a generation the primitive observation is the vector of per-constraint
scores --- boolean pass ``X_c``, graded score ``G_c`` in [0, 1], non-vacuity,
processing state --- plus the generation-level degeneracy record.

**§9.1's presence rule is load-bearing in v5 in a way it was not in v4r4**,
and this module is where that becomes executable. §13.6's interaction gate
reads the verdict of every candidate instance on the *B-solo* calibration
cells, so it needs kappa(R|B) to exist in the records. v4r4's calibration
stage scored load-one rows on the present instance only, so that quantity did
not exist and had to be recomputed from raw responses for v5's development
analysis. ``assert_presence_rule`` puts the requirement on the mandatory path
of **every** generative stage, which is what makes §13.6 cost zero extra
generations.

A verdict on an absent constraint is a **chance** observation. It is marked
``present = False``, no estimand reads it as a treated one, and
``assert_no_chance_in_treated`` refuses the mistake where it would be made.
The reverse mistake --- relabelling an absent-constraint score as a treatment
--- is refused by ``assert_presence_rule``, which compares the presence flags
against the cell's own stated constraints rather than against the row's
claims about itself.

**Five predicate forms.** Count budgets pass at ``S <= q``; rate budgets at
``100*S/W <= q``, and a wordless answer has no rate and fails; count lower
bounds at ``S >= q``; rate lower bounds at ``100*S/W >= q``, unused in v5;
exact counts at ``S == q``, which take A's graded shape over their own
numerator and carry no word-count vacuity clause, because a rule demanding q
occurrences of something cannot be satisfied by writing nothing.

Vacuous passes stay passes (§9.3). A verifier-processing failure fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from dci1v4.errors import InstrumentError

from dci1v6.verifiers.constraints import (
    FAMILIES, FORM_COUNT, FORM_EXACT, FORM_LOWER_BOUND, FORM_RATE,
    FORM_RATE_LOWER_BOUND, LOWER_BOUND_FORMS, Constraint,
)
from dci1v6.verifiers.statistics import (
    alpha_runs, family_statistic, focal_statistic, s0_count, word_count,
)

__all__ = ["NON_VACUITY_MIN_WORDS", "STEM_BAND", "ConstraintScore",
           "GenerationScores", "score_generation", "passes", "graded",
           "non_vacuous", "assert_no_chance_in_treated",
           "assert_presence_rule", "chance_verdicts", "treated_verdicts"]

#: §9.3: below this many words a budget pass is vacuous. The topic space asks
#: for 60-120 word answers and §8.5's stem says so to the model. Fixed
#: pre-freeze and never tuned to a realised rate.
NON_VACUITY_MIN_WORDS = 20

#: §8.5's diagnostic band, recorded per row and per load. Gates nothing ---
#: with the one registered exception that §7.7's *realistic* witness
#: obligation uses the band as a design constant.
STEM_BAND = (60, 120)


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
    #: §9.1. False means this verdict came from a prompt that did **not**
    #: state the constraint: a CHANCE observation, never a treated one.
    present: bool = True
    position: int | None = None  # 1-based position in the prompt's list

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.severity}"


@dataclass(frozen=True)
class GenerationScores:
    """The full per-generation record: vector plus degeneracy flags."""

    scores: tuple[ConstraintScore, ...]
    empty: bool
    word_count: int
    truncated: bool
    finish_reason: str | None
    token_count: int | None
    in_stem_band: bool
    load: int                    # 0, 1 or 2 numbered constraints

    def present_labels(self) -> tuple[str, ...]:
        return tuple(s.label for s in self.scores if s.present)

    def absent_labels(self) -> tuple[str, ...]:
        return tuple(s.label for s in self.scores if not s.present)


def _statistic(constraint: Constraint, text: str) -> int:
    if constraint.kind == "A":
        return s0_count(text)
    if constraint.kind == "B":
        return focal_statistic(text)
    return family_statistic(constraint.kind, text)


def passes(constraint: Constraint, statistic: int, text: str) -> bool:
    """§7.3's five predicate forms, and the two outcome rules."""
    q = constraint.severity
    if constraint.kind == "A":
        return statistic == q
    if constraint.kind == "B":
        return statistic <= q
    form = FAMILIES[constraint.kind].form
    if form == FORM_COUNT:
        return statistic <= q
    if form == FORM_EXACT:
        return statistic == q
    if form == FORM_LOWER_BOUND:
        return statistic >= q
    if form in (FORM_RATE, FORM_RATE_LOWER_BOUND):
        words = word_count(text)
        if words == 0:
            # A wordless answer has no rate. It fails, and that is the whole
            # point of the form: the empty string passes most count
            # severities and no rate severity.
            return False
        rate = 100.0 * statistic / words
        return rate <= q if form == FORM_RATE else rate >= q
    raise InstrumentError(f"unknown predicate form {form!r}")


def graded(constraint: Constraint, statistic: int, text: str) -> float:
    """§7.9, verbatim per constraint form."""
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
    if form == FORM_EXACT:
        # A's shape over the family's own numerator. Every registered
        # exact-count severity is at least one, so the division is total.
        return max(0.0, 1.0 - abs(statistic - q) / q)
    if form == FORM_COUNT:
        return (min(1.0, q / max(q, statistic)) if q > 0
                else float(statistic == 0))
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

    An exact count and a lower bound carry no word-count clause: their own
    rules force production, so a 20-word clause would be redundant rather
    than protective.
    """
    if not text.strip():
        return False
    if truncated:
        return False
    if constraint.kind == "A":
        return True
    if constraint.kind != "B" and FAMILIES[constraint.kind].form in \
            LOWER_BOUND_FORMS + (FORM_EXACT,):
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
        statistic=statistic, passed=ok,
        graded=graded(constraint, statistic, text), non_vacuous=nv,
        vacuous_pass=bool(ok and not nv), processing_failure=False,
        present=present, position=position)


def score_generation(text: str, *, present: Sequence[Constraint],
                     absent: Sequence[Constraint] = (),
                     truncated: bool = False,
                     finish_reason: str | None = None,
                     token_count: int | None = None) -> GenerationScores:
    """The §9.1 primitive for one generation.

    ``present`` are the numbered constraints the prompt stated, in prompt
    order; ``absent`` are the other registered instances this replication
    uses, scored on the same response to give the chance verdicts of §25 ---
    and, on a B-solo cell, the kappa(R|B) of §13.6.
    """
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


def chance_verdicts(scores: Iterable[ConstraintScore]
                    ) -> tuple[ConstraintScore, ...]:
    return tuple(s for s in scores if not s.present)


def treated_verdicts(scores: Iterable[ConstraintScore]
                     ) -> tuple[ConstraintScore, ...]:
    return tuple(s for s in scores if s.present)


def assert_no_chance_in_treated(scores: Iterable[ConstraintScore]) -> None:
    """§9.1: a treated estimand never reads a chance verdict.

    Called by every estimator that forms a delivery loss, so a chance
    observation cannot reach one by being handed to the wrong function.
    """
    stray = [s.label for s in scores if not s.present]
    if stray:
        raise InstrumentError(
            "these verdicts came from prompts that did not state the "
            f"constraint and are chance observations, not treated ones: "
            f"{stray}")


def assert_presence_rule(generation: GenerationScores, *,
                         stated: Sequence[Constraint],
                         instances_in_use: Sequence[Constraint],
                         where: str) -> None:
    """§9.1 at **every** generative stage, checked against the cell.

    Three failures are distinguished because they mean different things:

    * a stated constraint scored as absent, or an unstated one scored as
      present --- the row's presence flags disagree with the prompt, which is
      how a chance observation becomes a treatment label;
    * an instance the replication uses that carries no verdict at all ---
      v4r4's gap, and the reason kappa(R|B) did not exist in its records;
    * a verdict for an instance the replication does not use.

    ``instances_in_use`` is the replication's whole registered set, so the
    check is against the *design* rather than against whatever the row
    happened to carry.
    """
    stated_labels = {f"{c.kind}:{c.severity}" for c in stated}
    in_use = {f"{c.kind}:{c.severity}" for c in instances_in_use}
    if not stated_labels <= in_use:
        raise InstrumentError(
            f"{where}: the cell states {sorted(stated_labels - in_use)}, "
            "which the replication's registered instance set does not carry")
    scored = {s.label: s for s in generation.scores}
    mislabelled = sorted(
        label for label, score in scored.items()
        if score.present != (label in stated_labels))
    if mislabelled:
        raise InstrumentError(
            f"{where}: §9.1's presence flag disagrees with the prompt for "
            f"{mislabelled}. A verdict on an absent constraint is a chance "
            "observation and is never a treated one")
    missing = sorted(in_use - set(scored))
    if missing:
        raise InstrumentError(
            f"{where}: §9.1 requires a verdict for every registered instance "
            f"the replication uses; {missing} carry none. This is the gap "
            "that left kappa(R|B) out of v4r4's records and made §13.6's "
            "gate look expensive")
    extra = sorted(set(scored) - in_use)
    if extra:
        raise InstrumentError(
            f"{where}: verdicts for instances the replication does not use: "
            f"{extra}")
    if generation.load != len(stated_labels):
        raise InstrumentError(
            f"{where}: the row records load {generation.load} and the cell "
            f"states {len(stated_labels)} constraints")
