"""The claim ladder and its guarded emitters (§3, §17.3-§17.5, §28.1).

Every statement this study is allowed to make is produced here, by one guarded
emitter per claim level, and by no other path. The guards are executable, not
editorial:

* an emitter **refuses a member name not registered to it**, so a secondary
  quantity can never appear inside an L1, L2 or L3 statement;
* a statement missing any of the seven machine fields is refused;
* a statement quoting a scalar without its configuration is refused;
* the equivalence emitter's precondition is the interval region **and** the
  half-width precondition, and reaching it with the precondition false aborts
  the analysis rather than downgrading the statement;
* **L5 has no emitter.** Semantic identity-specificity, universal pair
  properties, arbitration, mechanism and generalisation are permanently
  withheld, and there is no code path that emits them (§3, §29).

Failure to exclude zero is never reported as absence (§3). An absence statement
requires ``emit_equivalence`` and its precondition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from dci1v4.analysis.bootstrap import MemberResult
from dci1v4.errors import ClaimError
from dci1v4.protocol import constants as C

#: §17.5: the machine fields every emitted statement carries.
REQUIRED_FIELDS = ("claim_level", "configuration", "family", "interval_type",
                   "identification_status", "measurement_basis",
                   "outcome_position")

#: Which F1 members each level may name. An emitter refuses anything else.
LEVEL_MEMBERS = {
    "L1": ("D(B<-A)", "D(A<-B)"),
    "L2": ("Lambda",),
    "L3a": ("Delta_R",),
    "L3b": ("Delta_R",),
    "L3c": ("Delta_R",),
    "L4": ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R"),
}

#: §28.1, the fifteen-row outcome vocabulary: the fixed mapping from interval
#: geometry to licensed statement. Nothing outside this table is emittable.
OUTCOME_VOCABULARY: dict[str, str] = {
    "delivery_loss_resolved":
        "Composing {outcome} with {companion} reduced delivery of {outcome} "
        "in this configuration, with {outcome} stated in position "
        "{outcome_position}",
    "delivery_gain_resolved":
        "Composing {outcome} with {companion} raised delivery of {outcome} "
        "in this configuration",
    "meaningful_magnitude":
        "The change exceeds the smallest effect of interest",
    "equivalence":
        "Any change is smaller than the smallest effect of interest, at "
        "adequate precision",
    "asymmetry_resolved":
        "The loss is directionally asymmetric between A and B in this "
        "configuration",
    "excess_above_generic_load_threshold":
        "A costs B more than companions matched to A on solo compliance do, "
        "by more than the registered generic-load threshold",
    "pair_specific_threshold_reached":
        "The excess reaches the source memo's pair-specific threshold",
    "generic_compositional_load":
        "The excess is below the registered generic-load threshold; the "
        "delivery loss is attributable to composition rather than to this "
        "companion",
    "indeterminate_at_a_threshold":
        "The design did not separate the two readings at that threshold in "
        "this configuration",
    "insufficient_precision":
        "The design did not achieve the registered precision; equivalence and "
        "threshold statements are withheld",
    "reference_heterogeneity":
        "The L3 statement is emitted with the disagreeing reference named",
    "companion_difficulty_qualifier":
        "The L3 statement is emitted with the reference and its realised gap "
        "named, and the §23 sensitivity reported beside it",
    "vacuity_asymmetry":
        "Composition changed how often the constraint could bind; claims "
        "follow both partial-identification bounds",
    "replication":
        "The classification is stable across the registered configurations",
    "configuration_dependence":
        "The quantity is configuration-dependent; the table is reported and "
        "no pooled scalar is quoted",
}
assert len(OUTCOME_VOCABULARY) == 15


@dataclass(frozen=True)
class Statement:
    """One emitted statement with its machine fields (§17.5)."""

    claim_level: str
    outcome: str
    vocabulary_key: str
    text: str
    configuration: str
    family: str
    interval_type: str
    identification_status: tuple[str, ...]
    measurement_basis: str
    outcome_position: int
    member: str
    estimate: float
    lower: float
    upper: float
    half_width: float
    markers: tuple[str, ...] = ()
    qualifiers: tuple[str, ...] = ()
    scope_sentence: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def as_record(self) -> dict[str, Any]:
        record = {
            "claim_level": self.claim_level, "outcome": self.outcome,
            "vocabulary_key": self.vocabulary_key, "statement": self.text,
            "configuration": self.configuration, "family": self.family,
            "interval_type": self.interval_type,
            "identification_status": list(self.identification_status),
            "measurement_basis": self.measurement_basis,
            "outcome_position": self.outcome_position, "member": self.member,
            "estimate": self.estimate, "lower": self.lower,
            "upper": self.upper, "half_width": self.half_width,
            "markers": list(self.markers), "qualifiers": list(self.qualifiers),
            "detail": dict(self.detail),
        }
        if self.scope_sentence:
            record["scope_sentence"] = self.scope_sentence
        return record


@dataclass(frozen=True)
class ClaimContext:
    """Everything an emitter needs that is not the interval itself."""

    configuration: str
    measurement_basis: str
    identification_status: tuple[str, ...] = ()
    #: F6 gate outcome; when False, §17.4 requires both bounds to agree.
    vacuity_gate_clean: bool = True
    #: The vacuity-forced recomputation's simultaneous interval per member.
    vacuity_forced: Mapping[str, MemberResult] = field(default_factory=dict)
    #: Realised per-reference gaps (§13.2) and Delta_j intervals (§13.4).
    realised_gaps: Mapping[str, float] = field(default_factory=dict)
    delta_j_intervals: Mapping[str, MemberResult] = field(default_factory=dict)

    def __post_init__(self):
        if self.measurement_basis not in C.MEASUREMENT_BASES:
            raise ClaimError(
                f"measurement basis {self.measurement_basis!r} is not one of "
                f"{C.MEASUREMENT_BASES}")
        for status in self.identification_status:
            if status not in C.IDENTIFICATION_STATUSES:
                raise ClaimError(f"{status!r} is not a registered "
                                 f"identification status")

    @property
    def scope_sentence(self) -> str | None:
        """§10.5: attached verbatim while the basis is not human_validated."""
        if self.measurement_basis == "human_validated":
            return None
        return C.SCOPE_SENTENCE


def _assert_member(level: str, member: str) -> None:
    allowed = LEVEL_MEMBERS[level]
    if member not in allowed:
        raise ClaimError(
            f"{level} may not name {member!r}; it is registered for {allowed}. "
            f"A secondary quantity never appears inside an L1, L2 or L3 "
            f"statement (§17.5)")


def _precision_key(member: str) -> str:
    if member.startswith("D("):
        return "D"
    if member.startswith("Delta_R"):
        return "Delta_R"
    if member.startswith("Lambda"):
        return "Lambda"
    if member.startswith("Delta_"):
        return "Delta_j"
    raise ClaimError(f"no registered precision precondition for {member!r}")


def precision_ok(member: str, result: MemberResult) -> bool:
    return result.half_width <= C.PRECISION_PRECONDITIONS[
        _precision_key(member)]


def assert_statement_complete(record: Mapping[str, Any]) -> None:
    """§17.5 check one: refuse a statement missing a machine field."""
    missing = [f for f in REQUIRED_FIELDS if record.get(f) in (None, "")]
    if missing:
        raise ClaimError(f"emitted statement is missing {missing}")


def assert_scalar_carries_configuration(record: Mapping[str, Any]) -> None:
    """§17.5 check two: refuse a statement quoting a scalar without its
    configuration."""
    quotes_scalar = any(record.get(k) is not None
                        for k in ("estimate", "lower", "upper"))
    if quotes_scalar and not record.get("configuration"):
        raise ClaimError("a scalar is quoted without its configuration (§5)")


def _finalise(statement: Statement) -> Statement:
    record = statement.as_record()
    assert_statement_complete(record)
    assert_scalar_carries_configuration(record)
    return statement


def _partial_identification_agrees(level_test, member: str,
                                   context: ClaimContext) -> tuple[bool, str]:
    """§17.4: a claim is licensed only when the primary and the vacuity-forced
    recomputation license the same claim."""
    if context.vacuity_gate_clean:
        return True, "F6 gate clean; the primary is reported without "\
                     "qualification"
    forced = context.vacuity_forced.get(f"{member}|vacuity_forced")
    if forced is None:
        return False, ("the F6 gate fired and no vacuity-forced recomputation "
                       "was supplied; the axis is reported unresolved with "
                       "both bounds")
    if level_test(forced):
        return True, "both the primary and the vacuity-forced bound license "\
                     "the same claim"
    return False, ("the primary and the vacuity-forced bound do not license "
                   "the same claim; the axis is reported unresolved with both "
                   "bounds (§17.4)")


# ------------------------------------------------------------------- emitters
def emit_l1(member: str, result: MemberResult, context: ClaimContext, *,
            outcome: str, companion: str, outcome_position: int,
            has_solo_headroom: bool) -> Statement | None:
    """L1: compositional delivery loss exists (§3).

    Gate: the outcome constraint has solo headroom and the §11.4 position
    caveat is stated. Every L1 statement names the position of its outcome
    constraint, and in the configuration where the outcome is stated second the
    statement carries POSITION_CONFOUNDED and the registered wording.
    """
    _assert_member("L1", member)
    if not has_solo_headroom:
        return None
    statuses = list(context.identification_status)
    qualifiers: list[str] = []
    if outcome_position != 1:
        if "POSITION_CONFOUNDED" not in statuses:
            statuses.append("POSITION_CONFOUNDED")
        qualifiers.append(C.POSITION_WORDING)

    markers: list[str] = []
    if not precision_ok(member, result):
        markers.append("INSUFFICIENT_PRECISION")

    if result.simultaneous_lower > 0:
        key = "delivery_loss_resolved"
    elif result.simultaneous_upper < 0:
        key = "delivery_gain_resolved"
    else:
        return None      # failure to exclude zero is never reported as absence

    licensed, note = _partial_identification_agrees(
        lambda forced: (forced.simultaneous_lower > 0
                        if key == "delivery_loss_resolved"
                        else forced.simultaneous_upper < 0),
        member, context)
    if not licensed:
        markers.append("PARTIAL_IDENTIFICATION_UNRESOLVED")
        qualifiers.append(note)
        return _finalise(Statement(
            claim_level="L1", outcome=outcome, vocabulary_key="vacuity_asymmetry",
            text=OUTCOME_VOCABULARY["vacuity_asymmetry"],
            configuration=context.configuration, family=C.PRIMARY_FAMILY,
            interval_type="simultaneous",
            identification_status=tuple(statuses),
            measurement_basis=context.measurement_basis,
            outcome_position=outcome_position, member=member,
            estimate=result.estimate, lower=result.simultaneous_lower,
            upper=result.simultaneous_upper, half_width=result.half_width,
            markers=tuple(markers), qualifiers=tuple(qualifiers),
            scope_sentence=context.scope_sentence,
            detail={"partial_identification": note}))

    if (result.simultaneous_lower > C.SMALLEST_EFFECT_OF_INTEREST
            or result.simultaneous_upper < -C.SMALLEST_EFFECT_OF_INTEREST):
        if "INSUFFICIENT_PRECISION" not in markers:
            qualifiers.append(OUTCOME_VOCABULARY["meaningful_magnitude"])

    text = OUTCOME_VOCABULARY[key].format(
        outcome=outcome, companion=companion,
        outcome_position=outcome_position)
    return _finalise(Statement(
        claim_level="L1", outcome=outcome, vocabulary_key=key, text=text,
        configuration=context.configuration, family=C.PRIMARY_FAMILY,
        interval_type="simultaneous", identification_status=tuple(statuses),
        measurement_basis=context.measurement_basis,
        outcome_position=outcome_position, member=member,
        estimate=result.estimate, lower=result.simultaneous_lower,
        upper=result.simultaneous_upper, half_width=result.half_width,
        markers=tuple(markers), qualifiers=tuple(qualifiers),
        scope_sentence=context.scope_sentence,
        detail={"partial_identification": note}))


def emit_l2(result: MemberResult, context: ClaimContext, *,
            l1_both_sides: bool, outcome_position: int) -> Statement | None:
    """L2: the loss is directionally asymmetric (§3). Gate: L1 conditions for
    both D(B<-A) and D(A<-B)."""
    member = "Lambda"
    _assert_member("L2", member)
    if not l1_both_sides:
        return None
    if result.simultaneous_lower <= 0 <= result.simultaneous_upper:
        return None
    markers = ([] if precision_ok(member, result)
               else ["INSUFFICIENT_PRECISION"])
    licensed, note = _partial_identification_agrees(
        lambda forced: not (forced.simultaneous_lower <= 0
                            <= forced.simultaneous_upper), member, context)
    if not licensed:
        return None
    return _finalise(Statement(
        claim_level="L2", outcome="A vs B",
        vocabulary_key="asymmetry_resolved",
        text=OUTCOME_VOCABULARY["asymmetry_resolved"],
        configuration=context.configuration, family=C.PRIMARY_FAMILY,
        interval_type="simultaneous",
        identification_status=tuple(context.identification_status),
        measurement_basis=context.measurement_basis,
        outcome_position=outcome_position, member=member,
        estimate=result.estimate, lower=result.simultaneous_lower,
        upper=result.simultaneous_upper, half_width=result.half_width,
        markers=tuple(markers), qualifiers=(),
        scope_sentence=context.scope_sentence,
        detail={"partial_identification": note}))


def emit_l3(result: MemberResult, context: ClaimContext, *,
            outcome_position: int) -> Statement | None:
    """L3a/L3b/L3c: the companion-identity level (§3).

    Gate: three references admitted; otherwise EXCESS_NOT_IDENTIFIED and no
    statement. An interval spanning a threshold records INDETERMINATE with both
    bounds. The §13.4 reference-heterogeneity block and the §13.2
    companion-difficulty block are attached here.
    """
    member = "Delta_R"
    _assert_member("L3a", member)
    if "EXCESS_NOT_IDENTIFIED" in context.identification_status:
        return None

    lower, upper = result.simultaneous_lower, result.simultaneous_upper
    generic = C.DELTA_R_GENERIC_THRESHOLD
    specific = C.DELTA_R_PAIR_SPECIFIC_THRESHOLD

    markers: list[str] = []
    if not precision_ok(member, result):
        # §17.3: withhold every equivalence and threshold statement, still
        # report a resolved direction if one exists.
        markers.append("INSUFFICIENT_PRECISION")
        if lower > 0:
            key, level = "delivery_loss_resolved", "L3a"
        elif upper < 0:
            key, level = "delivery_gain_resolved", "L3a"
        else:
            return None
        return _finalise(Statement(
            claim_level=level, outcome="B", vocabulary_key=key,
            text=OUTCOME_VOCABULARY["insufficient_precision"],
            configuration=context.configuration, family=C.PRIMARY_FAMILY,
            interval_type="simultaneous",
            identification_status=tuple(context.identification_status),
            measurement_basis=context.measurement_basis,
            outcome_position=outcome_position, member=member,
            estimate=result.estimate, lower=lower, upper=upper,
            half_width=result.half_width, markers=tuple(markers),
            qualifiers=(), scope_sentence=context.scope_sentence))

    if lower > specific:
        key, level = "pair_specific_threshold_reached", "L3b"
    elif lower > generic:
        key, level = "excess_above_generic_load_threshold", "L3a"
    elif upper < generic:
        key, level = "generic_compositional_load", "L3c"
    else:
        markers.append("INDETERMINATE")
        spanned = [t for t in (generic, specific) if lower <= t <= upper]
        return _finalise(Statement(
            claim_level="L3a", outcome="B",
            vocabulary_key="indeterminate_at_a_threshold",
            text=OUTCOME_VOCABULARY["indeterminate_at_a_threshold"],
            configuration=context.configuration, family=C.PRIMARY_FAMILY,
            interval_type="simultaneous",
            identification_status=tuple(context.identification_status),
            measurement_basis=context.measurement_basis,
            outcome_position=outcome_position, member=member,
            estimate=result.estimate, lower=lower, upper=upper,
            half_width=result.half_width, markers=tuple(markers),
            qualifiers=tuple(_l3_qualifiers(context, lower, upper)),
            scope_sentence=context.scope_sentence,
            detail={"thresholds_spanned": spanned,
                    "both_bounds": [lower, upper]}))

    threshold = specific if level == "L3b" else generic
    licensed, note = _partial_identification_agrees(
        lambda forced: (forced.simultaneous_lower > threshold
                        if level != "L3c"
                        else forced.simultaneous_upper < generic),
        member, context)
    if not licensed:
        markers.append("PARTIAL_IDENTIFICATION_UNRESOLVED")
        return _finalise(Statement(
            claim_level=level, outcome="B",
            vocabulary_key="vacuity_asymmetry",
            text=OUTCOME_VOCABULARY["vacuity_asymmetry"],
            configuration=context.configuration, family=C.PRIMARY_FAMILY,
            interval_type="simultaneous",
            identification_status=tuple(context.identification_status),
            measurement_basis=context.measurement_basis,
            outcome_position=outcome_position, member=member,
            estimate=result.estimate, lower=lower, upper=upper,
            half_width=result.half_width, markers=tuple(markers),
            qualifiers=tuple(_l3_qualifiers(context, lower, upper)),
            scope_sentence=context.scope_sentence,
            detail={"partial_identification": note}))

    return _finalise(Statement(
        claim_level=level, outcome="B", vocabulary_key=key,
        text=OUTCOME_VOCABULARY[key], configuration=context.configuration,
        family=C.PRIMARY_FAMILY, interval_type="simultaneous",
        identification_status=tuple(context.identification_status),
        measurement_basis=context.measurement_basis,
        outcome_position=outcome_position, member=member,
        estimate=result.estimate, lower=lower, upper=upper,
        half_width=result.half_width, markers=tuple(markers),
        qualifiers=tuple(_l3_qualifiers(context, lower, upper)),
        scope_sentence=context.scope_sentence,
        detail={"partial_identification": note}))


def _l3_qualifiers(context: ClaimContext, lower: float, upper: float
                   ) -> list[str]:
    """§13.4 reference heterogeneity and §13.2 companion difficulty."""
    qualifiers: list[str] = []
    threshold = (C.DELTA_R_PAIR_SPECIFIC_THRESHOLD
                 if lower > C.DELTA_R_PAIR_SPECIFIC_THRESHOLD
                 else C.DELTA_R_GENERIC_THRESHOLD)
    sides = set()
    disagreeing: list[str] = []
    for name, member in sorted(context.delta_j_intervals.items()):
        if member.simultaneous_lower > threshold:
            side = "above"
        elif member.simultaneous_upper < threshold:
            side = "below"
        else:
            side = "spans"
        sides.add(side)
        disagreeing.append(f"{name}={member.estimate:+.4f} [{side}]")
    if len(sides) > 1:
        qualifiers.append(
            f"{OUTCOME_VOCABULARY['reference_heterogeneity']}: "
            f"{'; '.join(disagreeing)}")
    for name, gap in sorted(context.realised_gaps.items()):
        if abs(gap) > C.REALISED_GAP_QUALIFIER:
            qualifiers.append(
                f"{OUTCOME_VOCABULARY['companion_difficulty_qualifier']}: "
                f"{name} realised gap {gap:+.4f} exceeds "
                f"{C.REALISED_GAP_QUALIFIER}")
    return qualifiers


def emit_equivalence(member: str, result: MemberResult,
                     context: ClaimContext, *, outcome_position: int
                     ) -> Statement:
    """§17.3: the single guarded function that produces an absence statement.

    Its precondition is the interval region **and** the half-width
    precondition. Reaching it with the precondition false aborts the analysis;
    it never downgrades to a weaker statement, because a downgrade is exactly
    the failure mode the guard exists to prevent.
    """
    region = C.EQUIVALENCE_REGION
    inside = (-region <= result.simultaneous_lower
              and result.simultaneous_upper <= region)
    precise = precision_ok(member, result)
    if not (inside and precise):
        raise ClaimError(
            f"the equivalence emitter was reached for {member} in "
            f"{context.configuration} with its precondition false "
            f"(interval [{result.simultaneous_lower:.4f}, "
            f"{result.simultaneous_upper:.4f}] inside ±{region}: {inside}; "
            f"half-width {result.half_width:.4f} at or below "
            f"{C.PRECISION_PRECONDITIONS[_precision_key(member)]}: {precise}). "
            f"The analysis aborts (§17.3)")
    return _finalise(Statement(
        claim_level="L1", outcome=member, vocabulary_key="equivalence",
        text=OUTCOME_VOCABULARY["equivalence"],
        configuration=context.configuration, family=C.PRIMARY_FAMILY,
        interval_type="simultaneous",
        identification_status=tuple(context.identification_status),
        measurement_basis=context.measurement_basis,
        outcome_position=outcome_position, member=member,
        estimate=result.estimate, lower=result.simultaneous_lower,
        upper=result.simultaneous_upper, half_width=result.half_width,
        scope_sentence=context.scope_sentence))


def emit_l4(classifications: Mapping[str, Mapping[str, str]],
            context: ClaimContext) -> Statement | None:
    """L4: the result replicates across configurations (§3).

    ``classifications`` maps a configuration to {member: vocabulary_key}. The
    level is licensed only when every registered configuration reached the
    corresponding level with the same classification.
    """
    for member in LEVEL_MEMBERS["L4"]:
        _assert_member("L4", member)
    if len(classifications) < 2:
        return None
    keys = {frozenset(sorted(v.items())) for v in classifications.values()}
    stable = len(keys) == 1
    key = "replication" if stable else "configuration_dependence"
    return _finalise(Statement(
        claim_level="L4", outcome="all", vocabulary_key=key,
        text=OUTCOME_VOCABULARY[key], configuration="ALL_REGISTERED",
        family=C.PRIMARY_FAMILY, interval_type="simultaneous",
        identification_status=tuple(context.identification_status),
        measurement_basis=context.measurement_basis, outcome_position=0,
        member="classification", estimate=float(stable), lower=0.0, upper=0.0,
        half_width=0.0, scope_sentence=context.scope_sentence,
        detail={"classifications": {k: dict(v)
                                    for k, v in classifications.items()}}))


def assert_no_l5_emitter() -> None:
    """§3, §29: L5 is permanently withheld and no code path emits it."""
    emitters = [name for name in globals()
                if name.startswith("emit_") and "l5" in name.lower()]
    if emitters:
        raise ClaimError(f"an L5 emitter exists: {emitters}; L5 is "
                         f"permanently withheld")
