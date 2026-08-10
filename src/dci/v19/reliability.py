"""The Tier-1/Tier-2 reliability architecture, and the interval it cannot freeze.

Section 10.4 is \\FIXED on the architecture and explicit about one gap:

    "The 5% Tier-1 ceiling, 20% Tier-2 per-stratum ceiling, pooled 5% system
    certificate, and inherited 73-per-truth-class Tier-1 planning count are
    preserved. The exact two-sided binomial interval implementation used by the
    inherited gate must be recovered from the authoritative code/specification and
    frozen at Stage 2; if it is not uniquely recoverable, its choice is a \\PFD
    within register item D9 rather than an implementer decision."

Recovery was performed and it succeeded. The result contradicts the sentence that
asked for it, so this module implements the *evidence* and refuses to make the
choice. `recover_inherited_interval()` returns the arithmetic; `WILSON` and
`CLOPPER_PEARSON` are both implemented so the decision can be checked rather than
recalled; nothing here selects one.

WHAT RECOVERY FOUND
-------------------
The only interval in the inherited code is `measurement.audit_sizing.wilson_interval`,
and it is the default `bound` of `required_cases_for_ceiling`, which is the
inversion the inherited gate uses. That inversion reproduces the preserved
planning count exactly:

    smallest_zero_error_n(0.05, 0.95, WILSON)          == 73
    WILSON.upper(0, 73, 0.95) == 0.049992…  <= 0.05
    WILSON.upper(0, 72, 0.95) == 0.050651…  >  0.05

So "73" is not a convention of unknown provenance: it is the Wilson score
interval inverted at a 5% ceiling and 95% confidence. But Wilson is a
normal-approximation interval - the family section 6.2 rejects, citing Brown, Cai
and DasGupta, when it requires "the exact two-sided 95% Clopper-Pearson interval"
for parameter calibration. The exact Clopper-Pearson zero-error bound reaches 0.05
at n = 72, not 73.

The interval is therefore uniquely recoverable AND what it recovers to is not an
"exact two-sided binomial interval". Both halves of section 10.4's sentence cannot
hold, so the choice is an investigator decision:

  1. freeze Wilson - preserves the 73 the section says is preserved, and accepts
     a normal-approximation ceiling on the primary outcome's verifier while
     parameter calibration uses an exact one;
  2. adopt Clopper-Pearson - satisfies "exact two-sided binomial" and section
     6.2's stated rationale, and changes the preserved count from 73 to 72.

A second defect sits in the same sentence: it assigns the decision to "register
item D9", but D9 in the section 17 register is the construction bootstrap
("complete U_i clusters; exactly 10,000 replicates"). No register row covers this,
so it needs one before Stage 14 can freeze it.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from scipy import stats

# ---------------------------------------------------------------- the ceilings
#
# Section 10.4, all \\FIXED and all preserved from the inherited protocol.

TIER1_CEILING = 0.05
TIER2_PER_STRATUM_CEILING = 0.20
POOLED_SYSTEM_CEILING = 0.05
CONFIDENCE = 0.95

# "the inherited 73-per-truth-class Tier-1 planning count"
INHERITED_TIER1_PER_TRUTH_CLASS = 73

# "With three pairs and six target/focal verifier units, this alone implies 876
# adjudicated labels before broader reference-verifier strata are counted."
TIER1_VERIFIER_UNITS = 6
TIER1_TRUTH_CLASSES = ("true_failures", "true_passes")
INHERITED_TIER1_TOTAL_LABELS = 876


class ReliabilityBlocked(RuntimeError):
    """A reliability computation was attempted before its interval was frozen."""


@dataclass(frozen=True)
class IntervalImplementation:
    """One two-sided binomial-proportion interval, named and citable."""
    name: str
    exact: bool
    description: str
    citation: str
    _interval: Callable[[int, int, float], tuple[float, float]]

    def interval(self, k: int, n: int, confidence: float = CONFIDENCE
                 ) -> tuple[float, float]:
        if isinstance(k, bool) or isinstance(n, bool):
            raise ValueError("counts must be integers, not booleans")
        if not isinstance(k, int) or not isinstance(n, int):
            raise ValueError(f"counts must be integers, got k={k!r}, n={n!r}")
        if n < 1:
            raise ValueError(
                f"a denominator of {n} is missing evidence, not zero error "
                "(section 10.4); there is no interval to report")
        if not 0 <= k <= n:
            raise ValueError(f"{k} errors out of {n} is not a possible count")
        if not 0 < confidence < 1:
            raise ValueError(f"confidence {confidence} is outside (0, 1)")
        return self._interval(k, n, confidence)

    def upper(self, k: int, n: int, confidence: float = CONFIDENCE) -> float:
        return self.interval(k, n, confidence)[1]

    def state(self) -> dict[str, Any]:
        return {"name": self.name, "exact": self.exact,
                "description": self.description, "citation": self.citation}


def _wilson(k: int, n: int, confidence: float) -> tuple[float, float]:
    """The inherited `measurement.audit_sizing.wilson_interval`, re-expressed.

    Written out rather than imported so that a change to the inherited helper
    surfaces as a differential-test failure instead of silently redefining what
    v19 recovered. `test_v19_reliability_recovery` asserts the two agree.
    """
    z = float(stats.norm.ppf(1 - (1 - confidence) / 2))
    p = k / n
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _clopper_pearson(k: int, n: int, confidence: float) -> tuple[float, float]:
    """The exact two-sided Clopper-Pearson interval, in its Beta-quantile form.

    Section 6.2 already requires exactly this for boundary parameter calibration,
    so the implementation is shared rather than duplicated in spirit: lower is the
    alpha/2 quantile of Beta(k, n-k+1) and upper the 1-alpha/2 quantile of
    Beta(k+1, n-k), degenerate at the endpoints.
    """
    alpha = 1 - confidence
    lower = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2, k, n - k + 1))
    upper = 1.0 if k == n else float(
        stats.beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lower, upper


WILSON = IntervalImplementation(
    name="wilson_score",
    exact=False,
    description=("Wilson score interval; a normal-approximation interval on the "
                 "logit-free score scale, correct at zero events where Wald is "
                 "degenerate"),
    citation="inherited: dci.measurement.audit_sizing.wilson_interval",
    _interval=_wilson)

CLOPPER_PEARSON = IntervalImplementation(
    name="clopper_pearson",
    exact=True,
    description=("exact two-sided Clopper-Pearson interval by Beta quantile "
                 "inversion of the binomial cdf"),
    citation="section 6.2; Brown, Cai and DasGupta (2001)",
    _interval=_clopper_pearson)

INTERVAL_IMPLEMENTATIONS: Mapping[str, IntervalImplementation] = {
    WILSON.name: WILSON, CLOPPER_PEARSON.name: CLOPPER_PEARSON}


def smallest_zero_error_n(ceiling: float, confidence: float,
                          implementation: IntervalImplementation,
                          cap: int = 100_000) -> int:
    """Smallest n whose zero-error upper bound is at or below `ceiling`.

    The same inversion the inherited gate performs: best case for an audit is
    zero observed errors, so this is a lower bound on any realised sample. The
    bound is monotone decreasing in n, so infeasibility is decided at the cap.
    """
    if not 0 < ceiling < 1:
        raise ValueError(f"ceiling {ceiling} is outside (0, 1)")
    if implementation.upper(0, cap, confidence) > ceiling:
        raise ValueError(f"no attainable sample size at or below {cap} for a "
                         f"{ceiling:.3f} ceiling at {confidence:.0%} confidence")
    low, high = 1, cap
    while low < high:
        mid = (low + high) // 2
        if implementation.upper(0, mid, confidence) <= ceiling:
            high = mid
        else:
            low = mid + 1
    return low


def recover_inherited_interval(ceiling: float = TIER1_CEILING,
                               confidence: float = CONFIDENCE) -> dict[str, Any]:
    """The section 10.4 recovery attempt, as auditable arithmetic.

    Returns the evidence rather than a decision. `uniquely_recoverable` says
    whether the inherited code identifies one implementation;
    `satisfies_exact_binomial_description` says whether that implementation is
    what section 10.4 calls it. When those disagree the sentence cannot be
    satisfied as written and `conflict` explains why.
    """
    from dci.measurement import audit_sizing

    inherited_default = audit_sizing.required_cases_for_ceiling.__defaults__
    uses_wilson = audit_sizing.wilson_interval in (inherited_default or ())
    inherited_n = audit_sizing.required_cases_for_ceiling(ceiling, confidence)
    by_implementation = {
        name: {"n_at_zero_errors": smallest_zero_error_n(ceiling, confidence, imp),
               "upper_at_inherited_n": imp.upper(
                   0, INHERITED_TIER1_PER_TRUTH_CLASS, confidence),
               "upper_one_below": imp.upper(
                   0, INHERITED_TIER1_PER_TRUTH_CLASS - 1, confidence),
               "exact": imp.exact}
        for name, imp in INTERVAL_IMPLEMENTATIONS.items()}
    reproduces = [name for name, row in by_implementation.items()
                  if row["n_at_zero_errors"] == INHERITED_TIER1_PER_TRUTH_CLASS]
    identified = WILSON.name if uses_wilson else ""
    conflict = ""
    if identified and not INTERVAL_IMPLEMENTATIONS[identified].exact:
        conflict = (
            f"the inherited gate's interval is uniquely recoverable and is "
            f"{identified!r}, which is not an exact binomial interval. Section "
            f"10.4 both calls it 'the exact two-sided binomial interval "
            f"implementation' and preserves the inherited "
            f"{INHERITED_TIER1_PER_TRUTH_CLASS}-per-truth-class count, which only "
            f"{reproduces} reproduces; the exact Clopper-Pearson bound reaches "
            f"the {ceiling} ceiling at "
            f"{by_implementation[CLOPPER_PEARSON.name]['n_at_zero_errors']} "
            "instead. Both halves of that sentence cannot hold, so the choice is "
            "an investigator decision, not an implementer one")
    return {"ceiling": ceiling, "confidence": confidence,
            "inherited_module": "dci.measurement.audit_sizing",
            "inherited_inversion_result": inherited_n,
            "identified_implementation": identified,
            "uniquely_recoverable": bool(identified),
            "satisfies_exact_binomial_description":
                bool(identified) and INTERVAL_IMPLEMENTATIONS[identified].exact,
            "reproduces_inherited_count": sorted(reproduces),
            "preserved_count": INHERITED_TIER1_PER_TRUTH_CLASS,
            "by_implementation": by_implementation,
            "conflict": conflict,
            "register_row_cited": "D9",
            "register_row_actual_subject":
                "construction bootstrap: complete U_i clusters, 10,000 replicates",
            "register_row_matches": False}


def frozen_interval(slots) -> IntervalImplementation:
    """The frozen interval implementation, or a fail-closed explanation.

    `slots` is any object supporting `[name]` over the registry's slot table. The
    slot is `verifiers.binomial_interval_implementation`; while it is pending this
    raises, so no reliability bound can be computed against a guessed interval.
    """
    slot = slots["verifiers.binomial_interval_implementation"]
    if not slot.resolved:
        evidence = recover_inherited_interval()
        raise ReliabilityBlocked(
            "the two-sided binomial interval for the Tier-1/Tier-2 reliability "
            "gates is not frozen, so no reliability bound can be computed.\n"
            f"  {evidence['conflict']}\n"
            "  Minimum decision required: freeze 'wilson_score' (preserves "
            f"{INHERITED_TIER1_PER_TRUTH_CLASS}) or 'clopper_pearson' (satisfies "
            "'exact', changes the preserved count to "
            f"{evidence['by_implementation'][CLOPPER_PEARSON.name]['n_at_zero_errors']}"
            "), and add the register row section 10.4 mis-cites as D9.")
    name = slot.get()
    if name not in INTERVAL_IMPLEMENTATIONS:
        raise ReliabilityBlocked(
            f"{name!r} is not an implemented interval; known: "
            f"{sorted(INTERVAL_IMPLEMENTATIONS)}")
    return INTERVAL_IMPLEMENTATIONS[name]


# ------------------------------------------------------- the Tier-1 certificate

@dataclass(frozen=True)
class ClassBound:
    """One conditional error bound, or an explicit statement that it is absent."""
    truth_class: str
    errors: int | None
    denominator: int
    upper: float | None
    ceiling: float
    available: bool
    reason: str

    @property
    def passed(self) -> bool:
        return self.available and self.upper is not None and self.upper <= self.ceiling

    def describe(self) -> dict[str, Any]:
        return {"truth_class": self.truth_class, "errors": self.errors,
                "denominator": self.denominator, "upper": self.upper,
                "ceiling": self.ceiling, "available": self.available,
                "passed": self.passed, "reason": self.reason}


@dataclass(frozen=True)
class TierCertificate:
    """A verifier unit's reliability result under one frozen interval."""
    unit: str
    interval: str
    ceiling: float
    confidence: float
    bounds: tuple[ClassBound, ...]

    @property
    def passed(self) -> bool:
        """Both truth classes must be present and both bounds must hold."""
        return len(self.bounds) == len(TIER1_TRUTH_CLASSES) and all(
            b.passed for b in self.bounds)

    @property
    def unavailable(self) -> tuple[str, ...]:
        return tuple(b.truth_class for b in self.bounds if not b.available)

    def describe(self) -> dict[str, Any]:
        return {"unit": self.unit, "interval": self.interval,
                "ceiling": self.ceiling, "confidence": self.confidence,
                "passed": self.passed, "unavailable": list(self.unavailable),
                "bounds": [b.describe() for b in self.bounds]}


def _class_bound(truth_class: str, errors: int | None, denominator: int,
                 implementation: IntervalImplementation, ceiling: float,
                 confidence: float) -> ClassBound:
    if denominator <= 0:
        return ClassBound(
            truth_class=truth_class, errors=errors, denominator=denominator,
            upper=None, ceiling=ceiling, available=False,
            reason=(f"no adjudicated {truth_class}: a missing denominator is "
                    "missing evidence, not zero error, so this bound is "
                    "unavailable and the unit cannot pass (section 10.4)"))
    if errors is None:
        return ClassBound(
            truth_class=truth_class, errors=None, denominator=denominator,
            upper=None, ceiling=ceiling, available=False,
            reason=(f"{denominator} adjudicated {truth_class} but no error count; "
                    "the bound cannot be computed"))
    upper = implementation.upper(errors, denominator, confidence)
    return ClassBound(
        truth_class=truth_class, errors=errors, denominator=denominator,
        upper=upper, ceiling=ceiling, available=True,
        reason=(f"{errors}/{denominator} adjudicated {truth_class} misclassified; "
                f"{implementation.name} upper bound {upper:.6f} "
                f"{'<=' if upper <= ceiling else '>'} ceiling {ceiling}"))


def tier_certificate(unit: str, *, false_passes: int | None,
                     true_failures: int, false_fails: int | None,
                     true_passes: int, implementation: IntervalImplementation,
                     ceiling: float = TIER1_CEILING,
                     confidence: float = CONFIDENCE) -> TierCertificate:
    """Certify one verifier unit against a conditional error ceiling.

    Section 10.4: "A false-pass bound requires adjudicated examples that truly
    fail the constraint. A false-fail bound requires adjudicated examples that
    truly pass. If either required class is absent, the corresponding reliability
    bound is unavailable and the unit cannot pass that gate."

    So both classes are always reported, an absent class is `available=False`
    rather than a bound of zero, and `passed` requires both. The interval is a
    required argument: while `verifiers.binomial_interval_implementation` is
    unfrozen there is nothing to default to.
    """
    if not isinstance(implementation, IntervalImplementation):
        raise ReliabilityBlocked(
            "tier_certificate needs an explicit interval implementation; the "
            "section 10.4 interval is not frozen, so there is no default. Use "
            "frozen_interval(registry.slots) once the decision is recorded")
    return TierCertificate(
        unit=unit, interval=implementation.name, ceiling=ceiling,
        confidence=confidence,
        bounds=(_class_bound("true_failures", false_passes, true_failures,
                             implementation, ceiling, confidence),
                _class_bound("true_passes", false_fails, true_passes,
                             implementation, ceiling, confidence)))


def tier1_planning_count(implementation: IntervalImplementation,
                         ceiling: float = TIER1_CEILING,
                         confidence: float = CONFIDENCE) -> int:
    """Adjudicated labels needed per truth class under a given interval."""
    return smallest_zero_error_n(ceiling, confidence, implementation)


def tier1_total_labels(implementation: IntervalImplementation) -> int:
    """Across six target/focal units and two truth classes each."""
    return (tier1_planning_count(implementation) * TIER1_VERIFIER_UNITS
            * len(TIER1_TRUTH_CLASSES))
