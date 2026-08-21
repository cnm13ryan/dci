"""The candidate library, its coverage criterion and its expansion (§7.0, §12.6).

v4r2 asked a small question of the reference pool -- *are there three
approximately matched controls?* -- and answered it with a caliper. v4r3 asks
a larger one -- *does the pool support an empirical difficulty-response
relation at A's difficulty?* -- and a caliper cannot answer it. This module is
where the larger question is decided, and it is decided **before any composed
cell exists**.

Three populations are kept distinct and are never confused:

``CANDIDATE LIBRARY``
    every (family, severity) the grammar of §7.0 declares: the round-0 ladders
    plus the frozen reserves, 334 severities in 20 families. Development may
    measure any of them on the §12.5 development topics.

``MEASURED VOCABULARY``
    the severities §12.2 has actually measured for a model: the 190 round-0
    rungs, plus whatever §12.6's expansion admitted. This is the population
    §12.3's shortlist ranks and §13's rules select from, and it is frozen at
    the end of the regime screen.

``FINAL SPECTRUM``
    the nine fit points and the three core references §13.4 and §13.6 choose
    at Gate 3 from the calibration table.

**The expansion is a restriction of a frozen enumeration, not new authoring.**
A round may admit reserve rungs and nothing else; the rule that picks them is
deterministic, reads only pre-screen solo and chance quantities, and is
registered here before any measurement. Wordings are severity-invariant, so a
reserve rung inherits its family's four frozen wordings and its §10.2 boundary
cases exactly -- which is why the expansion can happen after qualification
without any instrument gaining a severity that carries no evidence.

**What the expansion may never read** is enforced structurally: ``LibraryRow``
has no field a composed outcome could occupy, and ``load_prescreen_table``
refuses a mapping that offers one, by schema, before a value is read.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r3.protocol import constants as C
from dci1v4r3.stages.selection import (
    FORBIDDEN_CALIBRATION_FIELDS, instructed_compliance, tie_key,
)
from dci1v4r3.verifiers.constraints import (
    FAMILIES, REFERENCE_FAMILY_IDS, CLASS_FAMILY_IDS,
    RESERVES, feature_group,
)

__all__ = ["LibraryRow", "load_prescreen_table", "candidate_library_size",
           "round_zero_plan", "eligible_prescreen", "CoverageReport",
           "coverage_report", "expansion_plan", "run_expansion",
           "VocabularyFreeze", "freeze_vocabulary"]


@dataclass(frozen=True)
class LibraryRow:
    """One candidate severity as §12.2 measures it: solo and chance only."""

    kind: str
    severity: int
    #: 24 pre-screen topics, one draw (§12.2).
    solo_compliance: float
    chance_compliance: float
    solo_vacuity: float
    #: which expansion round admitted this rung; 0 is the registered ladder.
    admitted_in_round: int = 0
    median_words: float | None = None
    graded_mean: float | None = None

    def __post_init__(self):
        family = FAMILIES.get(self.kind)
        if family is None:
            raise ProtocolError(f"{self.kind!r} is not a registered family")
        if self.severity not in RESERVES[self.kind]:
            raise ProtocolError(
                f"{self.label} is outside the frozen candidate library of "
                f"§7.0; expansion may admit reserve rungs and nothing else")

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.severity}"

    @property
    def role(self) -> str:
        return FAMILIES[self.kind].role

    @property
    def iota(self) -> float:
        return instructed_compliance(self.solo_compliance,
                                     self.chance_compliance)


def load_prescreen_table(rows: Iterable[Mapping[str, Any]]) -> list[LibraryRow]:
    """§13.9's guard, applied to the pre-screen table as well.

    The expansion loop is the one place in v4r3 where a rule iterates while
    looking at data, so it is the one place where an outcome-adaptive
    vocabulary could enter. The loader refuses a composed field by name,
    before any value is read, and refuses an unknown field too -- a table
    carrying something this schema does not model has not been built by the
    registered pipeline.
    """
    allowed = set(LibraryRow.__dataclass_fields__)
    out: list[LibraryRow] = []
    for row in rows:
        offending = sorted(k for k in row
                           if k.lower() in FORBIDDEN_CALIBRATION_FIELDS)
        if offending:
            raise ProtocolError(
                f"§12.6 forbids a composed quantity in the candidate table; "
                f"{offending} would make the vocabulary outcome-adaptive")
        unknown = sorted(set(row) - allowed)
        if unknown:
            raise ProtocolError(
                f"the candidate table carries fields this schema does not "
                f"model: {unknown}")
        out.append(LibraryRow(**row))
    return out


def candidate_library_size() -> dict[str, int]:
    """The declared library, by role. Reported, never a stopping rule."""
    return {
        "families": len(FAMILIES),
        "reference_families": len(REFERENCE_FAMILY_IDS),
        "class_families": len(CLASS_FAMILY_IDS),
        "declared_severities": sum(len(v) for v in RESERVES.values()),
        "round_zero_severities": sum(len(f.ladder) for f in FAMILIES.values()),
    }


def round_zero_plan() -> list[tuple[str, int]]:
    """§12.2's round-0 measurement list, in a fixed order."""
    return [(kind, q) for kind in FAMILIES for q in FAMILIES[kind].ladder]


# ------------------------------------------------------------- eligibility
def eligible_prescreen(row: LibraryRow) -> bool:
    """§13.5's band applied to the pre-screen coordinate (§12.3).

    Only the band and the vacuity ceiling are decidable here: the wording
    caliper is a property of the family and is asserted for the whole declared
    range at qualification, and the witness suites likewise. Conditions that
    need the 96-topic sample are §13.4's and are not evaluated at pre-screen.
    """
    if row.chance_compliance >= C.CHANCE_DEGENERACY_MAX:
        return False
    low, high = C.SPECTRUM_ELIGIBILITY_BAND
    return (low <= row.iota <= high
            and row.solo_vacuity <= C.REFERENCE_VACUITY_MAX)


# --------------------------------------------------------------- coverage
@dataclass(frozen=True)
class CoverageReport:
    """§12.6's identification-coverage criterion, condition by condition."""

    iota_a: float
    conditions: dict[str, dict[str, Any]]
    passed: bool
    n_eligible_reference_rungs: int
    n_eligible_families: int
    straddling_families: tuple[str, ...]
    class_matched: bool

    def as_dict(self) -> dict[str, Any]:
        return {"iota_a": self.iota_a, "passed": self.passed,
                "conditions": self.conditions,
                "n_eligible_reference_rungs": self.n_eligible_reference_rungs,
                "n_eligible_families": self.n_eligible_families,
                "straddling_families": list(self.straddling_families),
                "class_matched": self.class_matched}


def _by_family(rows: Sequence[LibraryRow], role: str
               ) -> dict[str, list[LibraryRow]]:
    out: dict[str, list[LibraryRow]] = {}
    for row in rows:
        if row.role == role:
            out.setdefault(row.kind, []).append(row)
    for rungs in out.values():
        rungs.sort(key=lambda r: r.severity)
    return out


def _straddles(rungs: Sequence[LibraryRow], iota_a: float) -> bool:
    return (any(r.iota < iota_a for r in rungs)
            and any(r.iota > iota_a for r in rungs))


def coverage_report(rows: Sequence[LibraryRow], iota_a: float
                    ) -> CoverageReport:
    """Evaluate §12.6's criterion on a measured pre-screen table.

    Seven conditions. Six are about the reference pool and decide whether
    ``delta_difficulty`` can be identified at all; the seventh is about the
    class arm and is never terminal -- an unmatched class companion attaches
    ``COMPANION_CLASS_NOT_MATCHED`` and the study proceeds.
    """
    ref = [r for r in rows if r.role == "reference" and eligible_prescreen(r)]
    by_family = _by_family(ref, "reference")
    # §13.4 admits three different *measurements*, so the coverage criterion
    # counts feature groups wherever it is asking whether the design has
    # enough independent companions. Counting families would let eight
    # families over four groups look like eight independent controls.
    below = {feature_group(k) for k, v in by_family.items()
             if any(r.iota < iota_a for r in v)}
    above = {feature_group(k) for k, v in by_family.items()
             if any(r.iota > iota_a for r in v)}
    straddling = tuple(sorted(k for k, v in by_family.items()
                              if _straddles(v, iota_a)))
    near = [r for r in ref if abs(r.iota - iota_a) <= C.COVERAGE_NEAR_CALIPER]
    near_families = {feature_group(r.kind) for r in near}

    def _span(rungs: Sequence[LibraryRow]) -> float:
        values = [r.iota for r in rungs]
        return max(values) - min(values) if values else 0.0

    well_formed = tuple(sorted(
        k for k in straddling
        if len(by_family[k]) >= C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY
        and _span(by_family[k]) >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN))
    well_formed_groups = sorted({feature_group(k) for k in well_formed})
    eligible_groups = sorted({feature_group(k) for k in by_family})

    cls = [r for r in rows if r.role == "class_control"
           and eligible_prescreen(r)]
    class_near = [r for r in cls
                  if abs(r.iota - iota_a) <= C.CLASS_MATCH_CALIPER]

    conditions: dict[str, dict[str, Any]] = {
        "C1_bracketed": {
            "rule": "an eligible reference rung strictly below iota_A and one "
                    "strictly above",
            "observed": {"below": bool(below), "above": bool(above)},
            "met": bool(below) and bool(above)},
        "C2_groups_per_side": {
            "rule": f"at least {C.COVERAGE_MIN_FAMILIES_PER_SIDE} eligible "
                    "reference FEATURE GROUPS on each side of iota_A",
            "observed": {"below": sorted(below), "above": sorted(above)},
            "met": (len(below) >= C.COVERAGE_MIN_FAMILIES_PER_SIDE
                    and len(above) >= C.COVERAGE_MIN_FAMILIES_PER_SIDE)},
        "C3_near_density": {
            "rule": f"at least {C.COVERAGE_MIN_NEAR_RUNGS} eligible rungs "
                    f"within {C.COVERAGE_NEAR_CALIPER} of iota_A, from at "
                    f"least {C.COVERAGE_MIN_NEAR_FAMILIES} feature groups",
            "observed": {"rungs": [r.label for r in near],
                         "families": sorted(near_families)},
            "met": (len(near) >= C.COVERAGE_MIN_NEAR_RUNGS
                    and len(near_families) >= C.COVERAGE_MIN_NEAR_FAMILIES)},
        "C4_straddling_families": {
            "rule": f"at least {C.COVERAGE_MIN_STRADDLING_FAMILIES} reference "
                    "families straddle iota_A with at least "
                    f"{C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY} eligible "
                    f"rungs spanning {C.COVERAGE_MIN_WITHIN_FAMILY_SPAN:.2f} "
                    "in iota, from that many distinct feature groups",
            "observed": {"straddling": list(straddling),
                         "well_formed": list(well_formed),
                         "well_formed_groups": well_formed_groups},
            "met": (len(well_formed_groups)
                    >= C.COVERAGE_MIN_STRADDLING_FAMILIES)},
        "C5_total_points": {
            "rule": f"at least {C.COVERAGE_MIN_ELIGIBLE_RUNGS} eligible "
                    "reference rungs in total",
            "observed": {"n": len(ref)},
            "met": len(ref) >= C.COVERAGE_MIN_ELIGIBLE_RUNGS},
        "C6_shortlist_feasible": {
            "rule": f"at least {C.SHORTLIST_REFERENCE_FAMILIES} eligible "
                    "reference families, from at least "
                    f"{C.COVERAGE_MIN_STRADDLING_FAMILIES} feature groups, so "
                    "§12.3's shortlist is not short before it starts",
            "observed": {"families": sorted(by_family),
                         "groups": eligible_groups},
            "met": (len(by_family) >= C.SHORTLIST_REFERENCE_FAMILIES
                    and len(eligible_groups)
                    >= C.COVERAGE_MIN_STRADDLING_FAMILIES)},
        "C7_class_matched": {
            "rule": "at least one eligible class rung within "
                    f"{C.CLASS_MATCH_CALIPER} of iota_A. NOT terminal: an "
                    "unmatched class companion attaches "
                    "COMPANION_CLASS_NOT_MATCHED and the study proceeds",
            "observed": {"rungs": [r.label for r in class_near]},
            "met": bool(class_near),
            "terminal": False},
    }
    decisive = [v["met"] for k, v in conditions.items() if k != "C7_class_matched"]
    return CoverageReport(
        iota_a=tie_key(iota_a), conditions=conditions, passed=all(decisive),
        n_eligible_reference_rungs=len(ref), n_eligible_families=len(by_family),
        straddling_families=straddling, class_matched=bool(class_near))


# -------------------------------------------------------------- expansion
def expansion_plan(rows: Sequence[LibraryRow], iota_a: float, *,
                   round_index: int) -> list[tuple[str, int]]:
    """The rungs round ``round_index`` measures. Deterministic, reserve-only.

    Per family, in registered family order:

    * if the family's **measured** rungs bracket ``iota_A``, admit the reserve
      rungs lying strictly between the two adjacent measured severities whose
      iota values bracket it -- bisecting where the curve crosses A;
    * otherwise admit the reserve rungs immediately beyond the family's
      extreme measured severity on the deficient side -- extending toward A.

    At most ``EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND`` per family per round,
    taken nearest the target first, then by severity. The rule reads iota and
    severity and nothing else, and it cannot invent a rung: everything it
    returns is already in the frozen reserve of §7.0.
    """
    if not 1 <= round_index <= C.EXPANSION_MAX_ROUNDS:
        raise ProtocolError(
            f"§12.6 registers {C.EXPANSION_MAX_ROUNDS} expansion rounds; "
            f"round {round_index} is outside them")
    measured: dict[str, list[LibraryRow]] = {}
    for row in rows:
        measured.setdefault(row.kind, []).append(row)
    plan: list[tuple[str, int]] = []
    for kind in FAMILIES:
        reserve = RESERVES[kind]
        have = sorted(measured.get(kind, []), key=lambda r: r.severity)
        if not have:
            continue
        seen = {r.severity for r in have}
        free = [q for q in reserve if q not in seen]
        if not free:
            continue
        ordered = sorted(have, key=lambda r: r.iota)
        lo = [r for r in ordered if r.iota < iota_a]
        hi = [r for r in ordered if r.iota > iota_a]
        if lo and hi:
            a, b = sorted((lo[-1].severity, hi[0].severity))
            picks = [q for q in free if a < q < b]
            target = (a + b) / 2.0
        elif hi:                       # everything above A: go further out
            edge = max(r.severity for r in have)
            other = min(r.severity for r in have)
            picks = [q for q in free if q > edge or q < other]
            target = edge
        else:                          # everything below A
            edge = min(r.severity for r in have)
            other = max(r.severity for r in have)
            picks = [q for q in free if q < edge or q > other]
            target = edge
        picks.sort(key=lambda q: (tie_key(abs(q - target)), q))
        plan.extend((kind, q) for q in
                    picks[:C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND])
    return plan


def run_expansion(rows: Sequence[LibraryRow], iota_a: float, *,
                  measure) -> dict[str, Any]:
    """§12.6's loop: measure, check coverage, expand, stop.

    ``measure(plan, round_index)`` generates and scores the named rungs on the
    24 pre-screen topics and returns their ``LibraryRow``s. The loop stops the
    moment coverage passes and never runs a round it does not need, so the
    number of rounds is a *result* and not a parameter.
    """
    history: list[dict[str, Any]] = []
    exhausted = False
    table = list(rows)
    report = coverage_report(table, iota_a)
    history.append({"round": 0, "measured": len(table),
                    "coverage": report.as_dict()})
    round_index = 0
    while not report.passed and round_index < C.EXPANSION_MAX_ROUNDS:
        round_index += 1
        plan = expansion_plan(table, iota_a, round_index=round_index)
        if not plan:
            history.append({"round": round_index, "plan": [],
                            "note": "the frozen reserve is exhausted"})
            exhausted = True
            break
        new = list(measure(plan, round_index))
        for row in new:
            if row.admitted_in_round != round_index:
                raise ProtocolError(
                    f"{row.label} claims round {row.admitted_in_round} but "
                    f"was measured in round {round_index}")
        table.extend(new)
        report = coverage_report(table, iota_a)
        history.append({"round": round_index,
                        "plan": [f"{k}:{q}" for k, q in plan],
                        "measured": len(table),
                        "coverage": report.as_dict()})
    statuses: list[str] = []
    if not report.passed:
        statuses.append("DIFFICULTY_SUPPORT_NOT_IDENTIFIED")
        if exhausted:
            # Which of the two was binding matters: an exhausted reserve says
            # the library was too small, a completed round budget says the
            # model's curves do not straddle A wherever the library looked.
            statuses.append("CANDIDATE_RESERVE_EXHAUSTED")
    if not report.class_matched:
        statuses.append("CLASS_ARM_NOT_MATCHED")
    return {"rounds_run": round_index, "history": history,
            "coverage": report.as_dict(), "passed": report.passed,
            "reserve_exhausted": exhausted,
            "measured_vocabulary": sorted(r.label for r in table),
            "statuses": statuses}


# ------------------------------------------------------- vocabulary freeze
@dataclass(frozen=True)
class VocabularyFreeze:
    """§12.6's freeze: what the rest of the study may select from."""

    model_key: str
    measured_vocabulary: tuple[str, ...]
    rounds_run: int
    coverage: dict[str, Any]
    iota_a_prescreen: float
    statuses: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"model_key": self.model_key,
                "measured_vocabulary": list(self.measured_vocabulary),
                "rounds_run": self.rounds_run, "coverage": self.coverage,
                "iota_a_prescreen": self.iota_a_prescreen,
                "statuses": list(self.statuses)}


def freeze_vocabulary(model_key: str, result: Mapping[str, Any], *,
                      iota_a: float) -> VocabularyFreeze:
    """Close the vocabulary. After this no family or severity may change.

    The record names every measured rung, so a later selection over a rung
    this freeze does not name is a set difference rather than an argument.
    """
    statuses = tuple(result.get("statuses", ()))
    return VocabularyFreeze(
        model_key=model_key,
        measured_vocabulary=tuple(result["measured_vocabulary"]),
        rounds_run=int(result["rounds_run"]),
        coverage=dict(result["coverage"]),
        iota_a_prescreen=tie_key(iota_a),
        statuses=statuses)
