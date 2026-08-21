"""Reference, spectrum and class selection (v4r3 §13.3-§13.7, §13.9).

Everything in this module reads **solo and chance quantities on the
calibration topics, and nothing else**. It could have been executed before a
single composed cell existed anywhere in this programme, and
``CalibrationRow`` is the structure that makes that true rather than
asserted: it has no field in which a composed outcome could be carried, and
``load_calibration_table`` refuses a mapping that offers one.

That is §13.9's executable form, and it exists because a design with an
iterative difficulty-coverage step has a route to outcome-adaptive selection
that a single-caliper design does not.

The order is fixed and each stage feeds the next:

    eligibility  ->  core admission (§13.4)  ->  spectrum triples (§13.6)
                 ->  class companion (§13.7)

with a retry loop between the second and third: a family that cannot supply a
strictly straddling triple cannot be a core reference, so it is dropped and
the next admitted family takes its slot.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r3.protocol import constants as C
from dci1v4r3.verifiers.constraints import (
    FAMILIES, assert_reference_slot_allowed, family_class, feature_group,
)

__all__ = ["CalibrationRow", "instructed_compliance", "load_calibration_table",
           "FORBIDDEN_CALIBRATION_FIELDS", "eligible", "admit_family",
           "admit_core_references", "select_spectrum_triple",
           "select_spectrum", "admit_class_companion", "SelectionResult",
           "select_all", "tie_key", "newcombe_interval"]

#: §13.9. Any of these in a calibration table means the table has been built
#: from composed cells, and a selection rule must never see one. The list is
#: deliberately generous: a near-miss name is refused too, because the point
#: is to make the mistake impossible rather than to catch the exact spelling.
FORBIDDEN_CALIBRATION_FIELDS = (
    "composed", "composed_compliance", "delivery_loss", "d_b_from", "loss",
    "delta_r", "delta_j", "delta", "xi", "companion", "pair", "joint",
    "joint_state", "joint_success", "uptake", "composed_uptake",
    "b_with", "with_b", "interference", "delta_difficulty", "residual",
)


def tie_key(value: float) -> float:
    """Registered tie-breaks fire on exact ties that binary floats do not
    represent. Every selection key is rounded through this first."""
    return round(value, 12)


def instructed_compliance(solo: float, chance: float) -> float:
    """§13.3's registered difficulty coordinate.

    ``(solo - chance) / (1 - chance)``: the share of the achievable
    improvement over chance that stating the constraint actually delivers.

    A is an exact-count production constraint and is never satisfied by
    accident, so ``chance`` is 0.000 and ``iota`` equals its solo compliance.
    Every count budget is prefix-closed and is satisfied by accident often, so
    for those two the coordinate differs sharply -- which is the whole reason
    it is registered. A negative value means stating the constraint made the
    model satisfy it *less* often than not stating it; that is a real
    measurement and §13.5's band makes such a rung ineligible everywhere.
    """
    if not 0.0 <= chance <= 1.0 or not 0.0 <= solo <= 1.0:
        raise ProtocolError(f"compliance out of range: solo={solo}, "
                            f"chance={chance}")
    if chance >= C.CHANCE_DEGENERACY_MAX:
        raise ProtocolError(
            f"chance compliance {chance} is at or above "
            f"{C.CHANCE_DEGENERACY_MAX}: iota is not defined and §11.2 "
            "records DIFFICULTY_COORDINATE_DEGENERATE instead")
    return (solo - chance) / (1.0 - chance)


@dataclass(frozen=True)
class CalibrationRow:
    """One candidate severity, measured on solo and unconstrained cells only.

    There is no field here in which a composed outcome could travel. That is
    the point (§13.9).
    """

    kind: str
    severity: int
    #: §12.3's 96 solo-calibration topics at M_cal draws.
    solo_compliance: float
    #: §25's unconstrained cell on the same topics.
    chance_compliance: float
    solo_vacuity: float
    #: §12.2's disjoint 24 pre-screen topics, one draw. §13.4 condition 2.
    prescreen_solo_compliance: float
    prescreen_chance_compliance: float
    #: §7.5's wording caliper against A, and §13.4 condition 5's witnesses.
    wording_within_caliper: bool
    witnesses_pass: bool
    parse_independent: bool = True
    #: draw-level pass counts for the §13.4 condition-1 Newcombe interval.
    n_topics: int = C.N_SOLO
    n_draws: int = C.M_CAL
    #: diagnostics, reported and never selected on
    median_words: float | None = None
    graded_mean: float | None = None

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.severity}"

    @property
    def iota(self) -> float:
        return instructed_compliance(self.solo_compliance,
                                     self.chance_compliance)

    @property
    def prescreen_iota(self) -> float:
        return instructed_compliance(self.prescreen_solo_compliance,
                                     self.prescreen_chance_compliance)

    @property
    def lift(self) -> float:
        return self.solo_compliance - self.chance_compliance

    @property
    def constraint_class(self) -> str:
        return family_class(self.kind)


def load_calibration_table(rows: Iterable[Mapping[str, Any]]
                           ) -> list[CalibrationRow]:
    """§13.9: build the selection input, refusing any composed field.

    The refusal is on the *schema*, before a value is read, so a table that
    merely carries a composed column is rejected even if no rule would have
    used it.
    """
    out: list[CalibrationRow] = []
    for row in rows:
        offending = sorted(k for k in row
                           if any(bad in k.lower()
                                  for bad in FORBIDDEN_CALIBRATION_FIELDS))
        if offending:
            raise ProtocolError(
                "§13.9: a selection rule may read only solo and chance "
                "quantities on the calibration topics; this table carries "
                f"composed fields {offending}")
        known = {f.name for f in CalibrationRow.__dataclass_fields__.values()}
        unknown = sorted(set(row) - known)
        if unknown:
            raise ProtocolError(
                f"unknown calibration fields {unknown}; the selection input "
                "schema is closed so that a new column cannot smuggle in a "
                "composed quantity")
        out.append(CalibrationRow(**row))
    return out


def newcombe_interval(p1: float, n1: int, p2: float, n2: int, *,
                      z: float = 1.959963985) -> tuple[float, float]:
    """Newcombe's hybrid-score interval for a difference of proportions.

    §13.4 condition 1 requires this interval, computed on the underlying
    compliance rates, to intersect +/- REFERENCE_NEWCOMBE_REGION.
    """
    def wilson(p: float, n: int) -> tuple[float, float]:
        if n <= 0:
            return (0.0, 1.0)
        centre = (p + z * z / (2 * n)) / (1 + z * z / n)
        half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
                / (1 + z * z / n))
        return (max(0.0, centre - half), min(1.0, centre + half))

    l1, u1 = wilson(p1, n1)
    l2, u2 = wilson(p2, n2)
    lower = (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = (p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (lower, upper)


def eligible(row: CalibrationRow) -> tuple[bool, list[str]]:
    """§13.5's eligibility, common to references, spectrum and class.

    Conditions 3 to 6 of §13.4 plus the registered band on iota. The band is
    what makes an anti-productive rung -- one whose chance compliance meets or
    exceeds its solo compliance -- ineligible everywhere, in the core set, in
    the spectrum, and in the class arm alike.
    """
    reasons: list[str] = []
    if not row.wording_within_caliper:
        reasons.append("wording outside the 20% caliper against A")
    if not row.parse_independent:
        reasons.append("parse independence not established")
    if not row.witnesses_pass:
        reasons.append("joint-satisfiability or non-entailment witness failed")
    if row.solo_vacuity > C.REFERENCE_VACUITY_MAX:
        reasons.append(f"solo vacuity {row.solo_vacuity:.3f} above "
                       f"{C.REFERENCE_VACUITY_MAX}")
    if row.chance_compliance >= C.CHANCE_DEGENERACY_MAX:
        reasons.append("chance compliance at or above "
                       f"{C.CHANCE_DEGENERACY_MAX}: iota undefined")
    else:
        lo, hi = C.SPECTRUM_ELIGIBILITY_BAND
        if not lo <= row.iota <= hi:
            reasons.append(
                f"instructed compliance {row.iota:.3f} outside the registered "
                f"band [{lo}, {hi}]"
                + (" (the instruction is anti-productive)"
                   if row.iota <= 0 else ""))
    return (not reasons, reasons)


@dataclass(frozen=True)
class FamilyAdmission:
    """§13.4's per-family verdict, with every rejection reason kept."""

    family: str
    admitted: bool
    severity: int | None
    iota: float | None
    distance: float | None
    rungs: tuple[dict[str, Any], ...] = ()


def admit_family(family: str, rows: Sequence[CalibrationRow], *,
                 iota_a: float, prescreen_iota_a: float,
                 solo_compliance_a: float) -> FamilyAdmission:
    """§13.4's six conditions, on the registered difficulty coordinate.

    Condition 7 -- the family must be budget class -- is enforced before
    anything is measured, by ``assert_reference_slot_allowed``.
    """
    assert_reference_slot_allowed(family)
    candidates: list[dict[str, Any]] = []
    for row in [r for r in rows if r.kind == family]:
        ok, reasons = eligible(row)
        distance = None
        if row.chance_compliance < C.CHANCE_DEGENERACY_MAX:
            distance = abs(row.iota - iota_a)
            if distance > C.REFERENCE_CALIPER:
                reasons.append(
                    f"instructed-compliance distance {distance:.3f} above the "
                    f"{C.REFERENCE_CALIPER} caliper")
            lo, hi = newcombe_interval(row.solo_compliance, row.n_topics,
                                       solo_compliance_a, row.n_topics)
            region = C.REFERENCE_NEWCOMBE_REGION
            if lo > region or hi < -region:
                reasons.append(
                    f"the Newcombe interval [{lo:.3f}, {hi:.3f}] does not "
                    f"intersect +/-{region}")
            pre = abs(row.prescreen_iota - prescreen_iota_a)
            if pre > C.REFERENCE_PRESCREEN_CALIPER:
                reasons.append(
                    f"pre-screen distance {pre:.3f} above the "
                    f"{C.REFERENCE_PRESCREEN_CALIPER} caliper")
        candidates.append({"severity": row.severity, "iota": row.iota
                           if distance is not None else None,
                           "distance": distance, "admissible": not reasons,
                           "reasons": reasons})
    passing = [c for c in candidates if c["admissible"]]
    if not passing:
        return FamilyAdmission(family, False, None, None, None,
                               tuple(candidates))
    # minimise the distance; the LESS restrictive severity breaks an exact tie
    best = min(passing, key=lambda c: (tie_key(c["distance"]), -c["severity"]))
    return FamilyAdmission(family, True, best["severity"], best["iota"],
                           best["distance"], tuple(candidates))


def select_spectrum_triple(family: str, rows: Sequence[CalibrationRow], *,
                           core_severity: int, iota_a: float
                           ) -> dict[str, Any] | None:
    """§13.6: one rung strictly below A and one strictly above, or nothing.

    Strictness is the rule, not an accident of the targets. Selecting "the two
    rungs nearest iota_A +/- 0.20" without it permits both rungs on the same
    side of A, which is what a difficulty-spanning arm run at screen scale
    actually produced on two of four models -- one point below A and four
    above. One strictly below and one strictly above in every family
    guarantees three below and three above, which is what §13.8's support rule
    needs and what keeps the fit centred on A.
    """
    pool = [r for r in rows
            if r.kind == family and r.severity != core_severity
            and eligible(r)[0]]
    below = [r for r in pool if tie_key(r.iota) < tie_key(iota_a)]
    above = [r for r in pool if tie_key(r.iota) > tie_key(iota_a)]
    if not below or not above:
        return None
    lower_target = iota_a - C.SPECTRUM_OFFSET
    upper_target = iota_a + C.SPECTRUM_OFFSET
    lower = min(below, key=lambda r: (tie_key(abs(r.iota - lower_target)),
                                      -r.severity))
    upper = min(above, key=lambda r: (tie_key(abs(r.iota - upper_target)),
                                      -r.severity))
    return {"family": family, "core_severity": core_severity,
            "lower": {"severity": lower.severity, "iota": lower.iota,
                      "target": lower_target},
            "upper": {"severity": upper.severity, "iota": upper.iota,
                      "target": upper_target}}


def admit_core_references(rows: Sequence[CalibrationRow], *, iota_a: float,
                          prescreen_iota_a: float, solo_compliance_a: float
                          ) -> dict[str, Any]:
    """§13.4 and §13.6 together: three families that each supply a triple.

    A family that cannot straddle A cannot be a core reference, because its
    core rung would contribute a point to the fit with no siblings on one
    side. So admission and spectrum feasibility are decided together, and the
    next admitted family takes a dropped family's slot.

    **The three come from three different feature groups** (§7.0), not merely
    three different families. RF7 and CR7 are two families and one
    measurement; admitting both would give the §11.7 fit three intercepts over
    two properties of an answer, and it would put in one cell a pair whose
    non-entailment obligation §7.5 cannot discharge. The witness suite is what
    found this, and the rule is checked against it rather than beside it.
    """
    families = sorted({r.kind for r in rows
                       if FAMILIES.get(r.kind, None) is not None
                       and FAMILIES[r.kind].role == "reference"})
    verdicts = [admit_family(f, rows, iota_a=iota_a,
                             prescreen_iota_a=prescreen_iota_a,
                             solo_compliance_a=solo_compliance_a)
                for f in families]
    admitted = sorted([v for v in verdicts if v.admitted],
                      key=lambda v: (tie_key(v.distance), v.family))

    chosen: list[FamilyAdmission] = []
    triples: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    groups_taken: set[str] = set()
    for verdict in admitted:
        if len(chosen) == C.N_CORE_REFERENCES:
            break
        group = feature_group(verdict.family)
        if group in groups_taken:
            dropped.append({"family": verdict.family,
                            "reason": f"the {group} feature group is already "
                                      "represented; §13.4 admits three "
                                      "different measurements, not three "
                                      "different families"})
            continue
        triple = select_spectrum_triple(verdict.family, rows,
                                        core_severity=verdict.severity,
                                        iota_a=iota_a)
        if triple is None:
            dropped.append({"family": verdict.family,
                            "reason": "no eligible severity strictly on one "
                                      "side of A: the family cannot straddle"})
            continue
        chosen.append(verdict)
        groups_taken.add(group)
        triples.append(triple)

    identified = len(chosen) == C.N_CORE_REFERENCES
    return {
        "admitted_families": [v.family for v in admitted],
        "family_verdicts": [v.__dict__ for v in verdicts],
        "core_references": [
            {"slot": f"R{i + 1}", "family": v.family, "severity": v.severity,
             "iota": v.iota, "distance": v.distance,
             "feature_group": feature_group(v.family)}
            for i, v in enumerate(chosen)],
        "feature_groups": sorted(groups_taken),
        "spectrum_triples": triples,
        "dropped_for_no_triple": dropped,
        "references_identified": identified,
        "identification_statuses": (
            [] if identified else
            ["EXCESS_NOT_IDENTIFIED", "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]),
        "design": "full" if identified else "reduced",
    }


def select_spectrum(triples: Sequence[Mapping[str, Any]]
                    ) -> list[dict[str, Any]]:
    """The six spectrum companions, in registered slot order."""
    out: list[dict[str, Any]] = []
    for index, triple in enumerate(triples, start=1):
        for side, mark in (("lower", "-"), ("upper", "+")):
            out.append({"slot": f"R{index}{mark}", "family": triple["family"],
                        "severity": triple[side]["severity"],
                        "iota": triple[side]["iota"],
                        "target": triple[side]["target"], "side": side})
    return out


def admit_class_companion(rows: Sequence[CalibrationRow], *, iota_a: float
                          ) -> dict[str, Any]:
    """§13.7: one production-class companion, or CLASS_ARM_NOT_AVAILABLE.

    It never enters the core set, the spectrum, the fit, Delta_R, Rbar or Xi.
    Including it in the fit would let the line absorb the very quantity the
    arm exists to expose, which is why the exclusion is a rule in
    ``analysis.spectrum`` and not a preference here.
    """
    pool = [r for r in rows
            if FAMILIES.get(r.kind, None) is not None
            and FAMILIES[r.kind].role == "class_control"
            and eligible(r)[0]]
    if not pool:
        return {"available": False, "companion": None,
                "identification_statuses": ["CLASS_ARM_NOT_AVAILABLE"]}
    best = min(pool, key=lambda r: (tie_key(abs(r.iota - iota_a)), r.kind,
                                    -r.severity))
    return {"available": True,
            "companion": {"slot": C.CLASS_SLOT, "family": best.kind,
                          "severity": best.severity, "iota": best.iota,
                          "distance": abs(best.iota - iota_a),
                          "constraint_class": best.constraint_class},
            "identification_statuses": []}


@dataclass
class SelectionResult:
    """Everything Gate 3 decides, in one record."""

    core: dict[str, Any]
    spectrum: list[dict[str, Any]] = field(default_factory=list)
    klass: dict[str, Any] = field(default_factory=dict)

    @property
    def design(self) -> str:
        return self.core["design"]

    @property
    def identification_statuses(self) -> list[str]:
        return sorted(set(self.core["identification_statuses"]
                          + self.klass.get("identification_statuses", [])
                          # §28.2: attached to every L3 statement, always,
                          # because the reference pool is budget class and A
                          # is production class.
                          + ["COMPANION_CLASS_NOT_MATCHED"]))

    def slot_map(self) -> dict[str, tuple[str, int]]:
        out: dict[str, tuple[str, int]] = {}
        for entry in self.core["core_references"]:
            out[entry["slot"]] = (entry["family"], entry["severity"])
        for entry in self.spectrum:
            out[entry["slot"]] = (entry["family"], entry["severity"])
        if self.klass.get("available"):
            c = self.klass["companion"]
            out[C.CLASS_SLOT] = (c["family"], c["severity"])
        return out


def select_all(rows: Sequence[CalibrationRow], *, iota_a: float,
               prescreen_iota_a: float, solo_compliance_a: float
               ) -> SelectionResult:
    """§13.4, §13.6 and §13.7 in the registered order."""
    core = admit_core_references(rows, iota_a=iota_a,
                                 prescreen_iota_a=prescreen_iota_a,
                                 solo_compliance_a=solo_compliance_a)
    spectrum = (select_spectrum(core["spectrum_triples"])
                if core["references_identified"] else [])
    klass = admit_class_companion(rows, iota_a=iota_a)
    return SelectionResult(core=core, spectrum=spectrum, klass=klass)
