"""The claim ladder and §17.6's joint reading (v4r3 §3.2, §17.2-§17.6, §28).

Two estimands answer the study's third question -- ``Delta_R`` locally,
``delta_difficulty`` against a fitted relation -- and a third, ``Xi``, decides
how either may be worded. The point of this module is that all of that is
decided *before* a number is seen, so ``joint_reading`` is a lookup rather
than a judgement.

Adding a second route to L3 does not make a positive result easier to reach.
In the two rows where the estimands disagree, **neither** claim is emitted:
agreement is necessary, so the v4r3 ladder is strictly harder to climb than
v4r2's, not easier.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r4.protocol import constants as C

__all__ = ["Interval", "ClaimError", "position_status", "delta_r_reading",
           "delta_difficulty_reading", "xi_gate", "joint_reading",
           "emit_l1", "emit_l2", "emit_l3", "emit_l4",
           "assert_no_l5_emitter", "LEVEL_MEMBERS",
           "assert_statement_complete"]


class ClaimError(Exception):
    """A guarded emitter was reached with its precondition false."""


#: §17.5: one emitter per level, each refusing a member not registered to it.
LEVEL_MEMBERS: dict[str, tuple[str, ...]] = {
    "L1": ("D(B<-A)", "D(A<-B)"),
    "L2": ("Lambda",),
    "L3a": ("Delta_R",), "L3b": ("Delta_R",), "L3c": ("Delta_R",),
    "L3d": ("delta_difficulty",), "L3e": ("delta_difficulty",),
    "L4": ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R", "delta_difficulty"),
}

#: §17.5's machine fields. Every emitted statement carries all of them.
REQUIRED_FIELDS = ("claim_level", "configuration", "family", "interval_type",
                   "identification_status", "measurement_basis",
                   "difficulty_coordinate", "outcome_position")


@dataclass(frozen=True)
class Interval:
    """One simultaneous interval, with the realised half-width §17.3 reads."""

    member: str
    estimate: float
    lower: float
    upper: float

    @property
    def half_width(self) -> float:
        return (self.upper - self.lower) / 2.0

    def excludes_zero_from_below(self) -> bool:
        return self.lower > 0.0

    def wholly_inside(self, region: float) -> bool:
        return -region <= self.lower and self.upper <= region

    def meets_precondition(self) -> bool:
        precondition = C.PRECISION_PRECONDITIONS.get(_precondition_key(
            self.member))
        if precondition is None:
            raise ProtocolError(
                f"{self.member} has no registered precision precondition. Xi "
                "deliberately has none: §11.8 registers it as a direction-only "
                "gate, and an unresolved direction is A_GENERAL_NOT_EXCLUDED, "
                "not a comparison against a magnitude it does not have.")
        return self.half_width <= precondition


def _precondition_key(member: str) -> str:
    if member.startswith("D(") and "<-" in member:
        return "Delta_j" if member.startswith("D(B<-R") else "D"
    return member


def position_status(outcome_position: int) -> list[str]:
    """§11.4: L1 in the position-shifted configuration is confounded."""
    return [] if outcome_position == 1 else ["POSITION_CONFOUNDED"]


def delta_r_reading(interval: Interval) -> dict[str, Any]:
    """§3.2's L3a / L3b / L3c geometry against the two memo thresholds."""
    if interval.member != "Delta_R":
        raise ClaimError(f"{interval.member} is not Delta_R")
    generic = C.DELTA_R_GENERIC_THRESHOLD
    specific = C.DELTA_R_PAIR_SPECIFIC_THRESHOLD
    levels: list[str] = []
    markers: list[str] = []
    if not interval.meets_precondition():
        markers.append("INSUFFICIENT_PRECISION")
        return {"levels": [], "markers": markers,
                "direction_resolved": interval.excludes_zero_from_below()}
    if interval.lower > generic:
        levels.append("L3a")
        if interval.lower > specific:
            levels.append("L3b")
        elif interval.upper > specific:
            markers.append("INDETERMINATE@0.25")
    elif interval.upper < generic:
        levels.append("L3c")
    else:
        markers.append("INDETERMINATE@0.10")
    return {"levels": levels, "markers": markers,
            "direction_resolved": interval.excludes_zero_from_below()}


def delta_difficulty_reading(interval: Interval, support: Mapping[str, Any]
                             ) -> dict[str, Any]:
    """§3.2's L3d / L3e, gated on §13.8's support.

    ``delta_difficulty`` licenses a DIRECTION claim and an EQUIVALENCE claim
    and no pair-specific claim at any magnitude. The memo's 0.25 was defined
    for a difference between two observed losses; this quantity differences an
    observed loss against a fitted prediction, and transferring the number
    would be inventing a threshold in someone else's provenance (§11.8).
    """
    if interval.member != "delta_difficulty":
        raise ClaimError(f"{interval.member} is not delta_difficulty")
    if not support.get("holds"):
        return {"levels": [], "markers": [],
                "statuses": ["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"],
                "note": ("the fit extrapolates to A; the point estimate is "
                         "descriptive and is not a null")}
    if not interval.meets_precondition():
        return {"levels": [], "markers": ["INSUFFICIENT_PRECISION"],
                "statuses": [],
                "direction_resolved": interval.excludes_zero_from_below()}
    levels: list[str] = []
    if interval.excludes_zero_from_below():
        levels.append("L3d")
    elif interval.wholly_inside(C.EQUIVALENCE_REGION):
        levels.append("L3e")
    return {"levels": levels, "markers": [], "statuses": []}


def xi_gate(interval: Interval) -> dict[str, Any]:
    """§3.2: Xi decides the *wording*, not whether a statement is emitted."""
    if interval.member != "Xi":
        raise ClaimError(f"{interval.member} is not Xi")
    specific = interval.excludes_zero_from_below()
    return {
        "outcome_specific": specific,
        "statuses": [] if specific else ["A_GENERAL_NOT_EXCLUDED"],
        "wording": ("the excess is specific to the outcome B" if specific else
                    "the excess is not distinguishable from A being generally "
                    "disruptive as a companion"),
    }


def joint_reading(*, delta_r: Interval, delta_difficulty: Interval,
                  xi: Interval, support: Mapping[str, Any]) -> dict[str, Any]:
    """§17.6's table, applied in advance of any number.

    The two mixed rows -- a local excess the spectrum does not see, and a
    spectrum excess the local set does not see -- emit **neither** claim and
    record `LOCAL_AND_SPECTRUM_DISAGREE`. A disagreement is a result, is
    reported as one with both quantities and the diagnostics that distinguish
    them, and never resolves toward whichever estimand crossed a threshold.
    """
    local = delta_r_reading(delta_r)
    spectrum = delta_difficulty_reading(delta_difficulty, support)
    gate = xi_gate(xi)

    statuses = sorted(set(spectrum.get("statuses", []) + gate["statuses"]
                          # §28.2: always, because the pool is budget class
                          # and A is production class.
                          + ["COMPANION_CLASS_NOT_MATCHED"]))
    markers = sorted(set(local["markers"] + spectrum["markers"]))

    local_positive = "L3a" in local["levels"]
    local_null = "L3c" in local["levels"]
    spectrum_positive = "L3d" in spectrum["levels"]
    spectrum_null = "L3e" in spectrum["levels"]

    disagree = ((local_positive and spectrum_null)
                or (local_null and spectrum_positive))
    if disagree:
        statuses.append("LOCAL_AND_SPECTRUM_DISAGREE")
        return {
            "levels": [], "markers": markers,
            "identification_statuses": sorted(set(statuses)),
            "row": ("local excess, spectrum null" if local_positive else
                    "local null, spectrum excess"),
            "reading": (
                "the three local references were unrepresentative of the "
                "difficulty relation" if local_positive else
                "the local matches resemble A unusually closely relative to "
                "the relation"),
            "both_reported": {"Delta_R": delta_r.__dict__,
                              "delta_difficulty": delta_difficulty.__dict__},
        }

    levels = sorted(set(local["levels"] + spectrum["levels"]))
    return {
        "levels": levels, "markers": markers,
        "identification_statuses": sorted(set(statuses)),
        "row": ("both null" if (local_null and spectrum_null) else
                "both positive" if (local_positive and spectrum_positive) else
                "partially resolved"),
        "outcome_specific": gate["outcome_specific"],
        "wording": gate["wording"],
        "class_sentence": C.CLASS_SENTENCE,
    }


def assert_statement_complete(statement: Mapping[str, Any]) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in statement]
    if missing:
        raise ClaimError(f"an emitted statement is missing {missing}")
    if statement["claim_level"] in C.WITHHELD_CLAIM_LEVELS:
        raise ClaimError(f"{statement['claim_level']} is permanently withheld")


def emit_l3(*, configuration: str, outcome_position: int,
            measurement_basis: str, delta_r: Interval,
            delta_difficulty: Interval, xi: Interval,
            support: Mapping[str, Any],
            references_identified: bool,
            heterogeneity_disagrees: bool = False,
            realised_gaps: Mapping[str, float] | None = None,
            vacuity_forced_agrees: bool = True) -> list[dict[str, Any]]:
    """The guarded L3 emitter. Returns one statement per licensed sub-level.

    Every returned statement carries `COMPANION_CLASS_NOT_MATCHED` and
    §28.2's fixed sentence, at every sub-level, without exception: the
    reference pool is budget class by construction (§7.3) and A is production
    class, so this study's excess is never an excess relative to companions of
    A's own class.
    """
    reading = joint_reading(delta_r=delta_r,
                            delta_difficulty=delta_difficulty, xi=xi,
                            support=support)
    statuses = list(reading["identification_statuses"])
    if not references_identified:
        statuses.append("EXCESS_NOT_IDENTIFIED")
    if not vacuity_forced_agrees:
        # §17.4: a claim is licensed only when the primary and the
        # vacuity-forced recomputation license the same claim.
        return [{"claim_level": "L3", "configuration": configuration,
                 "family": C.PRIMARY_FAMILY, "interval_type": "simultaneous",
                 "identification_status": sorted(set(statuses)),
                 "measurement_basis": measurement_basis,
                 "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
                 "outcome_position": outcome_position,
                 "emitted": False,
                 "reason": ("§17.4: the primary and the vacuity-forced "
                            "recomputation do not license the same claim; the "
                            "axis is unresolved with both bounds")}]

    statements: list[dict[str, Any]] = []
    for level in reading["levels"]:
        if level in ("L3a", "L3b", "L3c") and not references_identified:
            continue
        statement = {
            "claim_level": level,
            "configuration": configuration,
            "family": C.PRIMARY_FAMILY,
            "interval_type": "simultaneous",
            "identification_status": sorted(set(statuses)),
            "measurement_basis": measurement_basis,
            "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
            "outcome_position": outcome_position,
            "emitted": True,
            "class_sentence": C.CLASS_SENTENCE,
            "outcome_specificity_wording": reading.get("wording"),
            "markers": reading["markers"],
        }
        if level in ("L3a", "L3b") and heterogeneity_disagrees:
            statement["heterogeneity_qualifier"] = (
                "the three Delta_j intervals do not agree on one side of the "
                "threshold used")
        gaps = {k: v for k, v in (realised_gaps or {}).items()
                if abs(v) > C.REALISED_GAP_QUALIFIER}
        if gaps:
            statement["companion_difficulty_qualifier"] = gaps
        assert_statement_complete(statement)
        statements.append(statement)
    if not statements:
        statements.append({
            "claim_level": "L3", "configuration": configuration,
            "family": C.PRIMARY_FAMILY, "interval_type": "simultaneous",
            "identification_status": sorted(set(statuses)),
            "measurement_basis": measurement_basis,
            "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
            "outcome_position": outcome_position,
            "emitted": False, "markers": reading["markers"],
            "reason": reading.get("reading", "no L3 sub-level is licensed"),
        })
    return statements


def _direction_statuses(interval: Interval, outcome_position: int,
                        extra: Sequence[str] = ()) -> list[str]:
    """§17.3 and §11.4, as statuses on a direction statement.

    A direction claim survives a half-width above the precondition --- §17.3
    withholds equivalence and threshold statements and "still reports a
    resolved direction if one exists" --- so `INSUFFICIENT_PRECISION` attaches
    here rather than suppressing the statement.
    """
    statuses = list(extra) + position_status(outcome_position)
    if not interval.meets_precondition():
        statuses.append("INSUFFICIENT_PRECISION")
    return sorted(set(statuses))


def _vacuity_agrees(primary: Interval, forced: Interval | None,
                    licensed: bool) -> bool:
    """§17.4: the primary and the vacuity-forced recomputation must agree.

    "A claim is licensed only when the primary and the vacuity-forced
    recomputation license the same claim; otherwise the axis is reported
    unresolved with both bounds." Agreement is on the *claim*, not on the
    numbers, so it is the licensing predicate that is compared.
    """
    if forced is None:
        return True
    return licensed == forced.excludes_zero_from_below()


def _vacuity_qualification(vacuity_gate_binds: bool,
                           forced: Interval | None) -> dict[str, Any]:
    """§17.4's *reporting* half, which is separate from its licensing half.

    "Otherwise they are reported with a fixed block stating that composition
    changed how often the outcome constraint could bind, and the F5
    vacuity-forced recomputation is reported beside them as
    partial-identification bounds." The licensing half --- primary and forced
    must license the same claim --- is `_vacuity_agrees`. The gate was
    computed and reported in the result table and travelled with no statement.
    """
    if not vacuity_gate_binds:
        return {}
    out: dict[str, Any] = {
        "vacuity_qualification": C.VACUITY_QUALIFICATION_SENTENCE,
        "f6_vacuity_gate_binds": True}
    if forced is not None:
        out["partial_identification_bounds"] = [forced.lower, forced.upper]
    return out


def emit_l1(*, configuration: str, outcome_position: int,
            measurement_basis: str, member: str, interval: Interval,
            solo_headroom: bool,
            identification_statuses: Sequence[str] = (),
            vacuity_forced: Interval | None = None,
            vacuity_gate_binds: bool = False) -> dict[str, Any]:
    """§3.2 L1: compositional delivery loss exists, for one named D(c <- g).

    §17.5 registers one guarded emitter per level and this one did not exist.
    `_claims` short-circuited to a single non-emitted L3 statement whenever
    Delta_R or Xi were unidentified, so a replication running §8.6's reduced
    design --- whose entire identified estimand set is L1 and L2 --- produced
    no claim at all, while §28's status table says in terms that "L1 and L2
    proceed under the reduced design". Both v4r4 replications that survive
    Gate 4 run that design.
    """
    if member not in LEVEL_MEMBERS["L1"]:
        raise ClaimError(f"{member} is not registered to L1; L1 names "
                         f"{LEVEL_MEMBERS['L1']}")
    licensed = interval.excludes_zero_from_below()
    statuses = _direction_statuses(interval, outcome_position,
                                   identification_statuses)
    statement = {
        "claim_level": "L1", "configuration": configuration,
        "family": C.PRIMARY_FAMILY, "member": member,
        "interval_type": "simultaneous",
        "identification_status": statuses,
        "measurement_basis": measurement_basis,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "outcome_position": outcome_position,
        "interval": [interval.lower, interval.upper],
        "estimate": interval.estimate,
        "half_width": interval.half_width,
        "class_sentence": C.CLASS_SENTENCE,
        **_vacuity_qualification(vacuity_gate_binds, vacuity_forced),
    }
    if not solo_headroom:
        return {**statement, "emitted": False,
                "reason": "§12: the outcome constraint has no solo headroom, "
                          "so the L1 identification gate does not hold"}
    if not _vacuity_agrees(interval, vacuity_forced, licensed):
        return {**statement, "emitted": False,
                "reason": "§17.4: the primary and the vacuity-forced "
                          "recomputation do not license the same claim; the "
                          "axis is unresolved with both bounds",
                "vacuity_forced_interval": [vacuity_forced.lower,
                                            vacuity_forced.upper]}
    if not licensed:
        return {**statement, "emitted": False,
                "reason": f"the F1 simultaneous interval for {member} does "
                          f"not have a lower bound above 0"}
    assert_statement_complete(statement)
    return {**statement, "emitted": True,
            "statement": f"composing the two instructions costs {member} a "
                         "delivery loss whose simultaneous interval lies "
                         "wholly above zero"}


def emit_l2(*, configuration: str, outcome_position: int,
            measurement_basis: str, interval: Interval,
            l1_licensed: Mapping[str, bool],
            identification_statuses: Sequence[str] = (),
            vacuity_forced: Interval | None = None,
            vacuity_gate_binds: bool = False) -> dict[str, Any]:
    """§3.2 L2: the loss is directionally asymmetric.

    Gate: L1's conditions for **both** `D(B<-A)` and `D(A<-B)`. Licensing: the
    F1 simultaneous interval for Lambda excludes 0 --- from either side, since
    asymmetry has a direction and the level is about its existence.
    """
    if interval.member not in LEVEL_MEMBERS["L2"]:
        raise ClaimError(f"{interval.member} is not registered to L2; L2 "
                         f"names {LEVEL_MEMBERS['L2']}")
    excludes_zero = interval.lower > 0.0 or interval.upper < 0.0
    statuses = _direction_statuses(interval, outcome_position,
                                   identification_statuses)
    statement = {
        "claim_level": "L2", "configuration": configuration,
        "family": C.PRIMARY_FAMILY, "member": interval.member,
        "interval_type": "simultaneous",
        "identification_status": statuses,
        "measurement_basis": measurement_basis,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "outcome_position": outcome_position,
        "interval": [interval.lower, interval.upper],
        "estimate": interval.estimate,
        "half_width": interval.half_width,
        "class_sentence": C.CLASS_SENTENCE,
        "l1_licensed": dict(l1_licensed),
        **_vacuity_qualification(vacuity_gate_binds, vacuity_forced),
    }
    missing = sorted(m for m in LEVEL_MEMBERS["L1"] if not l1_licensed.get(m))
    if missing:
        return {**statement, "emitted": False,
                "reason": f"L2's gate is L1 for both directions and {missing} "
                          "did not reach L1"}
    if not _vacuity_agrees(interval, vacuity_forced, excludes_zero):
        return {**statement, "emitted": False,
                "reason": "§17.4: the primary and the vacuity-forced "
                          "recomputation do not license the same claim; the "
                          "axis is unresolved with both bounds",
                "vacuity_forced_interval": [vacuity_forced.lower,
                                            vacuity_forced.upper]}
    if not excludes_zero:
        return {**statement, "emitted": False,
                "reason": "the F1 simultaneous interval for Lambda does not "
                          "exclude 0"}
    assert_statement_complete(statement)
    direction = ("B <- A" if interval.estimate > 0 else "A <- B")
    return {**statement, "emitted": True,
            "statement": "the delivery loss is directionally asymmetric; the "
                         f"larger loss is on {direction}"}


def emit_l4(*, per_configuration: Mapping[str, Sequence[str]],
            measurement_basis: str,
            identification_statuses: Sequence[str] = ()) -> dict[str, Any]:
    """§3.2 L4: the same L1/L2/L3 classification in every configuration.

    Stated across configurations, so it is emitted once per replication rather
    than once per configuration. `per_configuration` maps each registered
    configuration to the levels it reached.
    """
    configurations = sorted(per_configuration)
    reached = {k: sorted(set(v)) for k, v in per_configuration.items()}
    statement = {
        "claim_level": "L4", "configuration": "|".join(configurations),
        "family": C.PRIMARY_FAMILY, "interval_type": "simultaneous",
        "identification_status": sorted(set(identification_statuses)),
        "measurement_basis": measurement_basis,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "outcome_position": 0,
        "levels_by_configuration": reached,
        "class_sentence": C.CLASS_SENTENCE,
    }
    if set(configurations) != set(C.CONFIGURATIONS):
        return {**statement, "emitted": False,
                "reason": "not every registered configuration was analysed, "
                          "so replication across them cannot be read"}
    values = list(reached.values())
    if not values[0]:
        return {**statement, "emitted": False,
                "reason": "no configuration reached a level, so there is no "
                          "classification to replicate"}
    if any(v != values[0] for v in values[1:]):
        return {**statement, "emitted": False,
                "reason": "the configurations did not reach the same "
                          "classification, so §3.2's L4 gate does not hold"}
    assert_statement_complete(statement)
    return {**statement, "emitted": True,
            "statement": "the same classification holds in every registered "
                         f"configuration: {values[0]}"}


def assert_no_l5_emitter(namespace: Mapping[str, Any]) -> None:
    """§3.2: L5 is permanently withheld and no code path emits it."""
    offenders = [name for name in namespace
                 if name.startswith("emit_") and "l5" in name.lower()]
    if offenders:
        raise ClaimError(f"L5 is permanently withheld; found {offenders}")
