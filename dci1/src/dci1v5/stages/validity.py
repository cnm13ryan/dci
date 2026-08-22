"""V(R): the eight-component reference-validity conjunction (§13).

v4r4 answered *"does this candidate resemble A?"* with one number --- a
caliper on instructed compliance --- and §2.3 records the five ways that
failed. v5 answers it with a conjunction of registered components, evaluated
in a registered **lexicographic order**::

    V(R) = V_spec AND V_sat AND V_head AND V_chance
           AND V_struct AND V_inter AND V_stab AND V_diff

**The order decides which reason is recorded and not which candidates pass.**
A conjunction's truth value does not depend on evaluation order, so no
candidate is admitted or rejected because of where a component sits in the
sequence. The order is a *reporting* rule, registered because a rejection
reason that varies with implementation detail is not evidence. This module
therefore evaluates **every** component that has data --- so the record
carries all the measured values --- and reports the **earliest** failing one
as ``first_failing_component``. A reader who wants "later components are not
evaluated" gets the same rejection reason and more information.

**V_diff is last, and that is v5's central structural change.** In v4r4 iota
proximity was effectively the whole of admission, and a rung at raw solo
compliance 0.9740 with chance compliance 0.9323 was admitted *because its
iota was the closest available* --- and terminated its replication on its own
solo cell. iota is retained as the difficulty coordinate because it is the
only coordinate comparable across constraint classes and because the
difficulty-response relation must be read against something. It is demoted
because a ratio of two estimated quantities with a denominator approaching
zero is not a certificate of comparability.

**There is no weighted composite score, and none is registered.** A weighted
score needs weights, weights need to be fixed before v5 data, and the
development evidence is four models --- not enough to fix weights that would
generalise to an unseen candidate family. §34 D5 records the alternative as a
decision this document does not take, and ``assert_no_composite_score``
refuses one at qualification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.analysis.intervals import (
    interval_inside, interval_intersects, newcombe_interval, wilson,
)
from dci1v5.protocol import constants as C
from dci1v5.protocol.taxonomy import assert_tier_admits_slot
from dci1v5.stages.calibration_table import CalibrationRow, tie_key
from dci1v5.stages.interaction import interaction_verdict
from dci1v5.verifiers.constraints import CLASS_BUDGET, assert_slot_allowed

__all__ = ["ComponentResult", "ReferenceValidity", "VALIDITY_COMPONENTS",
           "GATE_2_5_COMPONENTS", "evaluate_validity",
           "assert_no_composite_score", "assert_lexicographic_order"]

#: §13.1's registered order. Imported from constants so there is one copy.
VALIDITY_COMPONENTS = C.VALIDITY_COMPONENTS
#: §18 stage 7 evaluates the components that need no split table and no
#: caliper against A: everything up to and including V_inter.
GATE_2_5_COMPONENTS = ("V_spec", "V_sat", "V_head", "V_chance", "V_struct",
                       "V_inter")


@dataclass(frozen=True)
class ComponentResult:
    """One component's verdict, with every value it measured.

    ``evaluated`` is False when the component's inputs were not available at
    this stage --- Gate 2.5 has no split table, so V_stab is unevaluated
    there. An unevaluated component is **never** a pass: ``ReferenceValidity``
    treats it as "not yet established", which is what §13.6 means when it says
    absence is never read as a pass.
    """

    name: str
    evaluated: bool
    passed: bool | None
    reason: str | None = None
    values: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"component": self.name, "evaluated": self.evaluated,
                "passed": self.passed, "reason": self.reason,
                "values": dict(self.values)}


@dataclass(frozen=True)
class ReferenceValidity:
    """The first-class validity object §13 decides on.

    ``passed`` is the conjunction over every evaluated component and is
    ``False`` when any component was not evaluated, because an unestablished
    component is not a satisfied one.
    """

    candidate: str
    slot: str
    structural_tier: int
    feature_group: str
    discourse_role: str
    split: str
    model_key: str
    components: tuple[ComponentResult, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def evaluated_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.components if c.evaluated)

    @property
    def unevaluated_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.components if not c.evaluated)

    @property
    def failing_components(self) -> tuple[str, ...]:
        """Every failing component, in registered order. Reported beside the
        earliest one so a reader sees whether a candidate failed once or
        everywhere."""
        return tuple(c.name for c in self.components
                     if c.evaluated and c.passed is False)

    @property
    def first_failing_component(self) -> str | None:
        """§13.1: the earliest failing component in the registered order."""
        failing = self.failing_components
        return failing[0] if failing else None

    @property
    def passed(self) -> bool:
        if self.unevaluated_names:
            return False
        return all(c.passed for c in self.components)

    @property
    def reason(self) -> str | None:
        if self.unevaluated_names:
            return (f"components not established at this stage: "
                    f"{list(self.unevaluated_names)}")
        first = self.first_failing_component
        if first is None:
            return None
        return next(c.reason for c in self.components if c.name == first)

    def value(self, component: str, key: str) -> Any:
        for c in self.components:
            if c.name == component:
                return c.values.get(key)
        raise ProtocolError(f"{component!r} is not a registered component")

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate, "slot": self.slot,
            "structural_tier": self.structural_tier,
            "feature_group": self.feature_group,
            "discourse_role": self.discourse_role,
            "split": self.split, "model_key": self.model_key,
            "passed": self.passed,
            "first_failing_component": self.first_failing_component,
            "failing_components": list(self.failing_components),
            "reason": self.reason,
            "components": [c.as_dict() for c in self.components],
            "provenance": dict(self.provenance),
        }


def _v_spec(row: CalibrationRow) -> ComponentResult:
    """§13.5: a complete §10.7 A record, A''s direction invariant, the 20%
    wording caliper against A, and parse independence."""
    problems = []
    if not row.specification_complete:
        problems.append("no complete §10.7 A specification record")
    if not row.wording_within_caliper:
        problems.append(f"wording outside the "
                        f"{C.WORDING_LENGTH_TOLERANCE:.0%} caliper against A")
    if not row.parse_independent:
        problems.append("parse independence not established")
    return ComponentResult(
        "V_spec", True, not problems, "; ".join(problems) or None,
        {"specification_complete": row.specification_complete,
         "wording_within_caliper": row.wording_within_caliper,
         "parse_independent": row.parse_independent})


def _v_sat(row: CalibrationRow) -> ComponentResult:
    """§13.5: formal joint-satisfiability and non-entailment, **and** §7.7's
    realistic witness against B at m* inside §8.5's stem band.

    The realistic obligation is new in v5 and it is narrow. A formal witness
    certifies only that a pair is not contradictory --- not that it is
    satisfiable by a response of the length the task asks for. `CL7`'s frozen
    reserve runs to 140: *at least 130 words must contain the letter a* cannot
    be met by any answer of at most 120 words. It does **not** catch a
    constraint that is reachable in principle and that B pushes into a
    degenerate region: `CL7:80` is reachable and was reached at 0.609 and
    0.662 under composition on `gemma-3n-e4b-it`. §13.6's interaction gate,
    and not this one, measures that class of risk.
    """
    problems = []
    if not row.witnesses_pass:
        problems.append("formal joint-satisfiability or non-entailment "
                        "witness failed")
    if not row.realistic_witness_pass:
        problems.append(f"no realistic witness inside the "
                        f"{C.STEM_BAND[0]}-{C.STEM_BAND[1]} word stem band "
                        "at this severity")
    return ComponentResult(
        "V_sat", True, not problems, "; ".join(problems) or None,
        {"witnesses_pass": row.witnesses_pass,
         "realistic_witness_pass": row.realistic_witness_pass})


def _v_head(row: CalibrationRow) -> ComponentResult:
    """§13.4: raw solo headroom, instruction lift, solo vacuity.

    The band [0.10, 0.90] is §13.14's composed-headroom band (0.05, 0.95)
    contracted by 0.05 on each side, and the contraction is applied to the
    **interval** rather than the point, so an imprecisely measured candidate
    cannot sit on the boundary.

    The lift floor exists because ``D(R <- B) <= H_R``: a reference cannot
    lose more compliance under composition than stating it ever bought. The
    registered smallest effect of interest is 0.10, so a reference with
    H < 0.20 cannot exhibit a reciprocal loss of two SESOI however the model
    behaves, and family F7's reciprocal estimands would be bounded by the
    design rather than by the model.
    """
    interval = wilson(row.solo_compliance, row.n_topics)
    problems = []
    if not interval_inside(interval, C.HEADROOM_BAND):
        problems.append(
            f"the 95% Wilson interval for raw solo compliance "
            f"[{interval[0]:.4f}, {interval[1]:.4f}] is not inside "
            f"{list(C.HEADROOM_BAND)}")
    if row.lift < C.INSTRUCTION_LIFT_MIN:
        problems.append(
            f"instruction lift {row.lift:.4f} below "
            f"{C.INSTRUCTION_LIFT_MIN}: stating this constraint buys less "
            "than two smallest-effects-of-interest, so its reciprocal loss "
            "would be bounded by the design rather than by the model")
    if row.solo_vacuity > C.REFERENCE_VACUITY_MAX:
        problems.append(f"solo vacuity {row.solo_vacuity:.4f} above "
                        f"{C.REFERENCE_VACUITY_MAX}")
    return ComponentResult(
        "V_head", True, not problems, "; ".join(problems) or None,
        {"solo_compliance": row.solo_compliance,
         "wilson_lower": interval[0], "wilson_upper": interval[1],
         "band": list(C.HEADROOM_BAND), "instruction_lift": row.lift,
         "solo_vacuity": row.solo_vacuity})


def _v_chance(row: CalibrationRow) -> ComponentResult:
    """§13.4: kappa at most 0.75, with a Wilson upper bound at most 0.85.

    iota's sampling variance carries a 1/(1-kappa) amplification: 4 at
    kappa = 0.75 and 10 at 0.90. The measured split-half |Delta iota| on
    v4r4's calibration data rises from 0.044 for chance-free candidates
    through 0.110 in [0.25, 0.75) to 0.195 at kappa >= 0.75. The ceiling sits
    where the empirical instability reaches roughly three times the
    chance-free value while the amplification factor is still single digit.

    v4r4's value was **0.99**, which is a degeneracy guard and not a ceiling;
    ``CHANCE_DEGENERACY_MAX`` keeps that meaning and decides nothing here.
    """
    upper = wilson(row.chance_compliance, row.n_topics)[1]
    problems = []
    if row.chance_compliance > C.CHANCE_MAX:
        problems.append(f"chance compliance {row.chance_compliance:.4f} above "
                        f"{C.CHANCE_MAX}")
    if upper > C.CHANCE_WILSON_UPPER_MAX:
        problems.append(f"the 95% Wilson upper bound on chance compliance "
                        f"{upper:.4f} above {C.CHANCE_WILSON_UPPER_MAX}")
    return ComponentResult(
        "V_chance", True, not problems, "; ".join(problems) or None,
        {"chance_compliance": row.chance_compliance, "wilson_upper": upper,
         "point_max": C.CHANCE_MAX,
         "wilson_upper_max": C.CHANCE_WILSON_UPPER_MAX})


def _v_struct(row: CalibrationRow, slot: str,
              core_family_tier: int | None) -> ComponentResult:
    """§13.5: the family's declared tier admits the slot it is considered for.

    The core set's own conditions --- at least two Tier-1 members from three
    distinct feature groups --- are a property of the **set** and are checked
    in ``stages/selection.py`` where the set exists.
    """
    try:
        assert_slot_allowed(row.kind, slot, core_family_tier=core_family_tier)
    except Exception as exc:
        return ComponentResult(
            "V_struct", True, False, str(exc),
            {"structural_tier": row.structural_tier, "slot": slot,
             "feature_group": row.feature_group,
             "discourse_role": row.discourse_role,
             "constraint_class": row.constraint_class})
    return ComponentResult(
        "V_struct", True, True, None,
        {"structural_tier": row.structural_tier, "slot": slot,
         "feature_group": row.feature_group,
         "discourse_role": row.discourse_role,
         "constraint_class": row.constraint_class})


def _v_inter(row: CalibrationRow) -> ComponentResult:
    """§13.6, evaluated through ``stages/interaction.py``.

    A candidate whose kappa(R|B) is missing is **not admitted**; absence is
    never read as a pass, so a missing value is a *failure* here and not an
    unevaluated component.
    """
    if row.kappa_under_b is None:
        return ComponentResult(
            "V_inter", True, False,
            "kappa(R|B) was not measured; §13.6 does not admit a candidate "
            "whose interaction quantity is missing, and absence is never read "
            "as a pass", {"kappa_under_b": None})
    verdict = interaction_verdict(kappa=row.chance_compliance,
                                 kappa_b=row.kappa_under_b, iota=row.iota,
                                 candidate=row.label)
    return ComponentResult(
        "V_inter", True, verdict.passed, verdict.reason,
        {"kappa_under_b": verdict.kappa_under_b,
         "displacement": verdict.displacement,
         "projected_compliance": verdict.projected_compliance,
         "band": list(C.PROJECTED_COMPLIANCE_BAND),
         "displacement_max": C.DISPLACEMENT_MAX})


def _v_stab(stability: Mapping[str, Any] | None) -> ComponentResult:
    """§13.7, computed in ``stages/stability.py`` and read here.

    Three conditions: independently admissible on Calibration-A **and** on
    Calibration-B, each evaluated on that split alone; and the 95%
    percentile-bootstrap interval for the split difference of iota, and of raw
    solo compliance, wholly inside +/- 0.20.
    """
    if stability is None:
        return ComponentResult("V_stab", False, None,
                               "no two-split table at this stage", {})
    return ComponentResult(
        "V_stab", True, bool(stability["passed"]), stability.get("reason"),
        {k: v for k, v in stability.items() if k not in ("passed", "reason")})


def _v_diff(row: CalibrationRow, *, iota_a: float, solo_compliance_a: float,
            n_topics_a: int) -> ComponentResult:
    """§13.8's three conditions, evaluated **last**.

    1. |iota_R - iota_A| at most the registered caliper. **The caliper does
       not move from v4r4's 0.10, deliberately.** The paired standard error of
       iota over 192 topics at M_cal = 4 is about 0.034, so 0.10 is about 2.96
       SE where v4r4's was 2.10: what changed is the sample, not the number.
       Tightening it would select harder on a coordinate whose error is the
       size of the window, which is the defect §12.2 measures.
    2. the 95% Newcombe hybrid-score interval for the paired difference of the
       underlying solo compliance rates **intersects** the registered region.
    3. |p_solo(R) - p_solo(A)| at most the secondary-coordinate caliper. New
       in v5, and meaningful only because the core pool is same-form and
       same-class with A: raw solo compliance is not comparable across the
       production/budget divide, which is why it is a secondary coordinate and
       a check on the primary rather than the selector.
    """
    distance = abs(row.iota - iota_a)
    newcombe = newcombe_interval(row.solo_compliance, row.n_topics,
                                 solo_compliance_a, n_topics_a)
    region = (-C.REFERENCE_NEWCOMBE_REGION, C.REFERENCE_NEWCOMBE_REGION)
    secondary = abs(row.solo_compliance - solo_compliance_a)
    problems = []
    if tie_key(distance) > C.REFERENCE_CALIPER:
        problems.append(f"instructed-compliance distance {distance:.4f} above "
                        f"the {C.REFERENCE_CALIPER} caliper")
    if not interval_intersects(newcombe, region):
        problems.append(f"the Newcombe interval [{newcombe[0]:.4f}, "
                        f"{newcombe[1]:.4f}] does not intersect "
                        f"+/-{C.REFERENCE_NEWCOMBE_REGION}")
    if tie_key(secondary) > C.SECONDARY_COORDINATE_CALIPER:
        problems.append(f"raw solo-compliance distance {secondary:.4f} above "
                        f"the {C.SECONDARY_COORDINATE_CALIPER} secondary "
                        "caliper")
    return ComponentResult(
        "V_diff", True, not problems, "; ".join(problems) or None,
        {"iota": row.iota, "iota_a": iota_a, "distance": distance,
         "caliper": C.REFERENCE_CALIPER,
         "newcombe_lower": newcombe[0], "newcombe_upper": newcombe[1],
         "newcombe_region": C.REFERENCE_NEWCOMBE_REGION,
         "secondary_distance": secondary,
         "secondary_caliper": C.SECONDARY_COORDINATE_CALIPER})


def evaluate_validity(row: CalibrationRow, *, slot: str,
                      iota_a: float | None = None,
                      solo_compliance_a: float | None = None,
                      n_topics_a: int | None = None,
                      stability: Mapping[str, Any] | None = None,
                      core_family_tier: int | None = None,
                      components: Sequence[str] = VALIDITY_COMPONENTS,
                      provenance: Mapping[str, Any] | None = None,
                      ) -> ReferenceValidity:
    """Evaluate V(R) for one candidate on one table.

    ``components`` selects which to evaluate --- Gate 2.5 passes
    ``GATE_2_5_COMPONENTS`` because it has no split table and no admitted
    operating comparison against A yet. Components not selected are recorded
    ``evaluated=False``, and ``ReferenceValidity.passed`` is False while any
    is unevaluated: an unestablished component is not a satisfied one.

    A spectrum candidate is deliberately **not** subject to ``V_diff``, whose
    whole purpose is proximity to iota_A and which a spectrum rung exists to
    violate in a controlled direction (§13.12). The caller expresses that by
    omitting ``V_diff`` from ``components``; this function does not decide it,
    because the exemption is a registered scientific rule and belongs where
    the selection is.
    """
    unknown = [c for c in components if c not in VALIDITY_COMPONENTS]
    if unknown:
        raise ProtocolError(
            f"{unknown} are not registered validity components; §13.1 "
            f"registers {list(VALIDITY_COMPONENTS)}")
    wanted = set(components)
    builders = {
        "V_spec": lambda: _v_spec(row),
        "V_sat": lambda: _v_sat(row),
        "V_head": lambda: _v_head(row),
        "V_chance": lambda: _v_chance(row),
        "V_struct": lambda: _v_struct(row, slot, core_family_tier),
        "V_inter": lambda: _v_inter(row),
        "V_stab": lambda: _v_stab(stability),
        "V_diff": lambda: (
            _v_diff(row, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
                    n_topics_a=n_topics_a or row.n_topics)
            if iota_a is not None and solo_compliance_a is not None
            else ComponentResult("V_diff", False, None,
                                 "no comparison against A at this stage", {})),
    }
    results = []
    for name in VALIDITY_COMPONENTS:          # always the registered order
        if name in wanted:
            results.append(builders[name]())
        else:
            results.append(ComponentResult(
                name, False, None, "not evaluated at this stage", {}))
    return ReferenceValidity(
        candidate=row.label, slot=slot, structural_tier=row.structural_tier,
        feature_group=row.feature_group, discourse_role=row.discourse_role,
        split=row.split, model_key=row.model_key,
        components=tuple(results), provenance=dict(provenance or {}))


def assert_lexicographic_order(validity: ReferenceValidity) -> None:
    """§19 test 3: the recorded reason is the **earliest** failing component.

    Checked on the object rather than on the algorithm, so a future
    implementation that evaluated components in a different order would still
    have to record the registered one.
    """
    order = list(VALIDITY_COMPONENTS)
    names = [c.name for c in validity.components]
    if names != order:
        raise ProtocolError(
            f"§13.1 registers the component order {order} and this record "
            f"carries {names}")
    first = validity.first_failing_component
    if first is None:
        return
    failing = validity.failing_components
    if order.index(first) != min(order.index(f) for f in failing):
        raise ProtocolError(
            f"{validity.candidate}: recorded {first!r} as the first failing "
            f"component, and {list(failing)} contains an earlier one")


def assert_no_composite_score(namespace: Mapping[str, Any]) -> None:
    """§13.1 and §34 D5: no weighted composite validity score exists.

    Checked over a module namespace at qualification, in the same shape as
    ``assert_no_l5_emitter``: the guarantee §33 check 4 asks for is that the
    path does not exist, not that it is unused.
    """
    offenders = sorted(
        name for name in namespace
        if any(token in name.lower()
               for token in ("composite_score", "weighted_validity",
                             "validity_score", "score_weights")))
    if offenders:
        raise ProtocolError(
            "§13.1 registers a lexicographic conjunction and no weighted "
            f"composite score; found {offenders}. §34 D5 records the "
            "alternative as a decision this protocol does not take")
