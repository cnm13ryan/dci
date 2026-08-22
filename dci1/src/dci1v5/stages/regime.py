"""The regime screen, operating-point selection and coverage (§12).

**The screen's purpose is recall, not selection, and that is v5's change.**
v4r4 used the same screen as a hard selector: §12.3 shortlisted six reference
families by point-estimate distance from iota_A and §13.4 then re-measured
only the shortlist, so a candidate discarded here could never return. The
measured cost is in the development analysis: the two stages' iota estimates
disagree by a median of 0.071 and **35.7% of candidates move further between
them than the whole width of the caliper they then have to clear**, while
iota_A itself moves by up to 0.048.

**The v5 retention rule.** A candidate rung is carried into calibration when
either

1. it survives the **structural** screen --- the checks no amount of data will
   change --- *and* its pre-screen 95% Wilson interval for raw solo compliance
   intersects [0.05, 0.95]; or
2. its family is Tier 1 or Tier 2, in which case **every** rung of its round-0
   ladder is carried regardless of its pre-screen estimate.

Rule 2 exists because the core pool is small, its rungs are cheap to measure,
and a Tier-1 family's difficulty is tunable through q: discarding a rung on 24
topics at one draw would discard the tuning. **No candidate is discarded on a
pre-screen point estimate of iota, and no pre-screen quantity enters any
admission decision in §13.** v4r4's pre-screen distance caliper is deleted.

**Bracketing, new in v5.** m* was the last measured rung on **all four** v4r4
replications, and on `qwen3-4b` it was the top of the extension. A selected
severity is *bracketed* when both neighbouring severities of its grid are
measured at calibration precision; when the selected m* is the top of the
registered grid the extension is measured and selection re-runs over the
union; when it is still the top, ``OPERATING_POINT_AT_GRID_BOUNDARY`` is
recorded --- an identification status, not a terminal one.

**One thing here is a researcher decision and is not taken in code.** §34 D17
asks whether a *construct* floor is registered for m*. §12.3 selects the rung
whose **compliance** is nearest 0.80 over a grid now reaching m = 16; on
`qwen3-4b`'s v4r4 curve that points at m* = 13 --- *every word at most 13
letters* --- which is a real behavioural constraint and a weak construct.
``assert_construct_floor`` expresses both branches and refuses until D17 is
closed.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.analysis.intervals import interval_intersects, wilson
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.stages.calibration_table import tie_key
from dci1v5.stages.selection import restrictiveness_key
from dci1v5.verifiers.constraints import (
    FAMILIES, LADDERS, RESERVES, focal_severities,
)

__all__ = ["StructuralScreen", "carry_candidate", "carried_set",
           "calibration_priority", "select_operating_point", "select_focal", "select_target",
           "assert_construct_floor", "coverage_criterion", "expansion_round",
           "run_expansion"]


class StructuralScreen:
    """§12.4's structural checks: the ones no amount of data will change."""

    __slots__ = ("tier_admissible", "wording_within_caliper",
                 "parse_independent", "formal_witness", "realistic_witness",
                 "metadata_consistent")

    def __init__(self, *, tier_admissible: bool = True,
                 wording_within_caliper: bool = True,
                 parse_independent: bool = True, formal_witness: bool = True,
                 realistic_witness: bool = True,
                 metadata_consistent: bool = True):
        self.tier_admissible = tier_admissible
        self.wording_within_caliper = wording_within_caliper
        self.parse_independent = parse_independent
        self.formal_witness = formal_witness
        self.realistic_witness = realistic_witness
        self.metadata_consistent = metadata_consistent

    def failures(self) -> list[str]:
        names = ("tier_admissible", "wording_within_caliper",
                 "parse_independent", "formal_witness", "realistic_witness",
                 "metadata_consistent")
        return [n for n in names if not getattr(self, n)]

    @property
    def passed(self) -> bool:
        return not self.failures()


def carry_candidate(*, kind: str, severity: int,
                    prescreen_solo_compliance: float | None,
                    n_prescreen_topics: int,
                    structural: StructuralScreen) -> dict[str, Any]:
    """§12.2's two-rule retention verdict for one rung."""
    family = FAMILIES[kind]
    tier = family.structural_tier
    if tier in (1, 2):
        in_ladder = severity in LADDERS[kind]
        return {"candidate": f"{kind}:{severity}",
                "carried": bool(in_ladder or severity in RESERVES[kind]),
                "rule": 2,
                "reason": "§12.2 rule 2 carries every Tier-1 and Tier-2 rung "
                          "unconditionally: the core pool is small, its rungs "
                          "are cheap, and a marker family's difficulty is "
                          "tunable through q, so discarding a rung on 24 "
                          "topics at one draw would discard the tuning",
                "structural_failures": structural.failures()}
    failures = structural.failures()
    if failures:
        return {"candidate": f"{kind}:{severity}", "carried": False,
                "rule": 1, "reason": f"structural screen failed: {failures}",
                "structural_failures": failures}
    if prescreen_solo_compliance is None:
        return {"candidate": f"{kind}:{severity}", "carried": False,
                "rule": 1,
                "reason": "no pre-screen measurement, and rule 1 needs one",
                "structural_failures": []}
    interval = wilson(prescreen_solo_compliance, n_prescreen_topics)
    ok = interval_intersects(interval, C.PRESCREEN_RETENTION_BAND)
    return {"candidate": f"{kind}:{severity}", "carried": ok, "rule": 1,
            "prescreen_wilson": list(interval),
            "reason": None if ok else
            (f"the pre-screen Wilson interval "
             f"[{interval[0]:.3f}, {interval[1]:.3f}] does not intersect "
             f"{list(C.PRESCREEN_RETENTION_BAND)}"),
            "structural_failures": []}


def carried_set(verdicts: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted(v["candidate"] for v in verdicts if v["carried"])


def calibration_priority(carried: Sequence[Mapping[str, Any]], *,
                         iota_a_prescreen: float,
                         tier3_cap: int = C.CALIBRATION_TIER3_CAP
                         ) -> dict[str, Any]:
    """§12.7's budget: every Tier-1/Tier-2 rung, plus at most 24 Tier-3 rungs.

    **This is the one place a pre-screen point estimate still decides
    anything, and it decides only which Tier-3 rungs are measured when the
    budget binds.** Never admission, and never anything about Tier 1 or Tier
    2. The cap, the priority and the realised list go on the Gate-2 record.

    ``carried`` entries need ``candidate``, ``family``, ``structural_tier``
    and ``prescreen_iota``.
    """
    tier12 = [c for c in carried if c["structural_tier"] in (1, 2)]
    tier3 = [c for c in carried if c["structural_tier"] == 3]
    ranked = sorted(
        tier3,
        key=lambda c: (tie_key(abs((c.get("prescreen_iota") if
                                    c.get("prescreen_iota") is not None
                                    else 1e9) - iota_a_prescreen)),
                       c["candidate"]))
    admitted3 = ranked[:tier3_cap]
    return {"tier12": [c["candidate"] for c in tier12],
            "tier3_measured": [c["candidate"] for c in admitted3],
            "tier3_dropped_for_budget":
                [c["candidate"] for c in ranked[tier3_cap:]],
            "tier3_cap": tier3_cap,
            "n_measured": len(tier12) + len(admitted3),
            "note": "the pre-screen ordering decides which Tier-3 rungs are "
                    "MEASURED when the budget binds, never which candidates "
                    "are admitted; §13 reads no pre-screen quantity"}


def select_operating_point(curve: Mapping[int, float], *, band: tuple,
                           aim: float, prefer_smaller: bool,
                           grid: Sequence[int]) -> dict[str, Any]:
    """§12.3: the eligible severity nearest the aim, with the bracketing test.

    ``curve`` maps severity -> raw solo compliance on the pooled calibration
    topics. Selection is on **raw solo compliance**, not on iota, because the
    bands exist to give an outcome constraint room to fall under composition,
    which is a statement about its realised compliance.
    """
    eligible = [q for q in grid
                if q in curve and band[0] <= curve[q] <= band[1]]
    if not eligible:
        return {"selected": None, "eligible": [], "curve": dict(curve),
                "bracketed": False,
                "reason": "no severity of the measured grid puts solo "
                          f"compliance inside {list(band)}"}
    tie = (lambda q: q) if prefer_smaller else (lambda q: -q)
    selected = min(eligible, key=lambda q: (tie_key(abs(curve[q] - aim)),
                                            tie(q)))
    measured = sorted(curve)
    bracketed = (selected - 1 in curve) and (selected + 1 in curve)
    boundary_reason = None
    if not bracketed:
        side = ("easy" if selected - 1 not in curve else "hard")
        boundary_reason = (
            f"the selected severity {selected} is at the {side} edge of the "
            f"measured range {measured[0]}..{measured[-1]}, so §12.3's "
            "bracketing rule cannot be met")
    return {"selected": selected, "eligible": eligible, "curve": dict(curve),
            "bracketed": bracketed,
            "at_grid_top": selected == max(grid),
            "identification_statuses":
                [] if bracketed else ["OPERATING_POINT_AT_GRID_BOUNDARY"],
            "reason": boundary_reason}


def select_focal(curve_registered: Mapping[int, float],
                 curve_extension: Mapping[int, float] | None = None
                 ) -> dict[str, Any]:
    """§12.3 and §7.2's escalation, in the registered order.

    The extension {15, 16} is measured **only** when selection finds no
    eligible severity in the registered grid, or when the selected severity is
    the top of the registered grid and the bracketing rule therefore cannot be
    met. Where the registered grid works the extension is never measured, so a
    new rung cannot move m* on a replication whose registered grid already
    supplies a bracketed operating point.
    """
    first = select_operating_point(curve_registered, band=C.FOCAL_BAND,
                                   aim=C.FOCAL_AIM, prefer_smaller=True,
                                   grid=C.FOCAL_GRID)
    needs_extension = (first["selected"] is None
                       or first.get("at_grid_top", False))
    if not needs_extension:
        return {**first, "extension_measured": False}
    if curve_extension is None:
        return {**first, "extension_measured": False,
                "extension_required": True,
                "reason": (first.get("reason") or "") +
                          "; §7.2's extension {15, 16} must be measured "
                          "before selection can re-run"}
    union = {**dict(curve_registered), **dict(curve_extension)}
    second = select_operating_point(
        union, band=C.FOCAL_BAND, aim=C.FOCAL_AIM, prefer_smaller=True,
        grid=focal_severities(extended=True))
    if second["selected"] is None:
        return {**second, "extension_measured": True,
                "terminal_status": "FOCAL_RANGE_EXHAUSTED"}
    return {**second, "extension_measured": True}


def select_target(curve: Mapping[int, float]) -> dict[str, Any]:
    """§12.3's n*: A's eligible severity nearest 0.70, smaller n breaking a tie.

    **A's construct has a genuine floor at n = 1.** n = 0 is a well-formed
    exact count whose chance compliance is the probability that an
    unconstrained answer contains no *however* --- near one --- so it is
    chance-degenerate and is not in the grid. Where n* = 1 the bracketing rule
    cannot be met on the easy side and the record carries
    ``OPERATING_POINT_AT_GRID_BOUNDARY`` with that reason, which is a
    statement about the construct and not about the model.
    """
    result = select_operating_point(curve, band=C.TARGET_BAND, aim=C.TARGET_AIM,
                                    prefer_smaller=True, grid=C.TARGET_GRID)
    if result["selected"] == min(C.TARGET_GRID) and not result["bracketed"]:
        result = {**result,
                  "reason": "n* = 1 is the floor of A's construct: n = 0 is a "
                            "prohibition whose chance compliance is near one "
                            "and is not in the grid, so the bracketing rule "
                            "cannot be met on the easy side"}
    if result["selected"] is None:
        result = {**result, "terminal_status": "TARGET_RANGE_EXHAUSTED"}
    return result


def assert_construct_floor(m_star: int, *,
                           chance_compliance_at_m_star: float) -> dict[str, Any]:
    """§34 D17: whether m* carries a construct-strength floor.

    §12.3 selects the focal severity whose *compliance* is nearest 0.80, over
    a grid now reaching m = 16. Compliance is a behavioural quantity and 0.80
    compliance at m = 13 is a real constraint on a model's writing; as a
    **construct**, *every word at most 13 letters* is close to a null
    instruction in ordinary English, and the focal band is defined on
    compliance rather than on construct strength.

    Both branches exist and neither is reachable while D17 is open. The
    standing proposal registers no floor and instead reports the realised m*,
    B's chance compliance at m*, and B's whole curve, with §29 stating that a
    high m* makes B a weak instrument on that model. **No threshold is
    invented here**: the ``floor`` branch requires the researcher to supply
    one when they close D17, and this call refuses rather than guessing.
    """
    def _no_floor() -> dict[str, Any]:
        return {"floor_registered": False, "m_star": m_star,
                "chance_compliance_at_m_star": chance_compliance_at_m_star,
                "reported": "the realised m*, B's chance compliance at m*, "
                            "and B's whole curve",
                "limitation": "a high m* makes B a weak instrument on this "
                              "model (§29)"}

    def _floor() -> dict[str, Any]:
        raise ProtocolError(
            "§34 D17 was closed at 'floor' and no threshold accompanies it. "
            "A construct floor is a registered value with a derivation; this "
            "implementation does not invent one, and the closure must supply "
            "the threshold and the quantity it applies to")

    return decisions.choice("D17", {"no_floor": _no_floor, "floor": _floor},
                            where="stages.regime.assert_construct_floor")()


def coverage_criterion(table: Sequence[Mapping[str, Any]], *, iota_a: float
                       ) -> dict[str, Any]:
    """§12.6's eight identification-coverage conditions.

    ``table`` entries carry ``candidate``, ``family``, ``structural_tier``,
    ``feature_group``, ``constraint_class``, ``iota`` and ``eligible``.
    C1-C6 are decisive for the core and spectrum arms; **C7 and C8 are not**
    --- failing C7 drops the broad-class arm with ``CLASS_ARM_NOT_AVAILABLE``
    and failing C8 drops the near-form arm with
    ``NEAR_FORM_ARM_NOT_AVAILABLE``, and neither stops the study.

    C4's "three spare" is the direct repair of v4r4's F5: v4r4 registered four
    straddling families against a requirement of three --- one spare --- and
    lost 50% to 100% of them between the pre-screen and calibration on every
    replication.
    """
    rows = [r for r in table if r.get("eligible")]
    by_family: dict[str, list[Mapping[str, Any]]] = {}
    for r in rows:
        by_family.setdefault(r["family"], []).append(r)

    below = [r for r in rows if tie_key(r["iota"]) < tie_key(iota_a)]
    above = [r for r in rows if tie_key(r["iota"]) > tie_key(iota_a)]
    tier12 = [r for r in rows if r["structural_tier"] in (1, 2)]
    groups_below = {r["feature_group"] for r in below
                    if r["structural_tier"] in (1, 2)}
    groups_above = {r["feature_group"] for r in above
                    if r["structural_tier"] in (1, 2)}
    near = [r for r in rows
            if abs(r["iota"] - iota_a) <= C.COVERAGE_NEAR_CALIPER]
    near_groups = {r["feature_group"] for r in near}

    straddling_groups = set()
    for family, entries in by_family.items():
        fam_below = [e for e in entries
                     if tie_key(e["iota"]) < tie_key(iota_a)]
        fam_above = [e for e in entries
                     if tie_key(e["iota"]) > tie_key(iota_a)]
        if not fam_below or not fam_above:
            continue
        if len(entries) < C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY:
            continue
        span = max(e["iota"] for e in entries) - min(e["iota"]
                                                     for e in entries)
        if span >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN:
            straddling_groups.add(entries[0]["feature_group"])

    tier12_families = {r["family"] for r in tier12}
    tier12_groups = {r["feature_group"] for r in tier12}
    tier3_budget_near = [r for r in near if r["structural_tier"] == 3
                         and r["constraint_class"] == "budget"]
    tier2_rows = [r for r in rows if r["structural_tier"] == 2]
    tier2_groups = {r["feature_group"] for r in tier2_rows}

    conditions = {
        "C1": bool(below) and bool(above),
        "C2": (len(groups_below) >= C.COVERAGE_MIN_FAMILIES_PER_SIDE
               and len(groups_above) >= C.COVERAGE_MIN_FAMILIES_PER_SIDE),
        "C3": (len(near) >= C.COVERAGE_MIN_NEAR_RUNGS
               and len(near_groups) >= C.COVERAGE_MIN_NEAR_FAMILIES),
        "C4": len(straddling_groups) >= C.COVERAGE_MIN_STRADDLING_FAMILIES,
        "C5": len(rows) >= C.COVERAGE_MIN_ELIGIBLE_RUNGS,
        "C6": (len(tier12_families) >= C.COVERAGE_MIN_TIER12_FAMILIES
               and len(tier12_groups) >= C.COVERAGE_MIN_TIER12_GROUPS),
        "C7": bool(tier3_budget_near),
        "C8": (len(tier2_rows) >= C.COVERAGE_MIN_TIER2_RUNGS
               and len(tier2_groups) >= C.COVERAGE_MIN_TIER2_RUNGS),
    }
    decisive_met = all(conditions[c] for c in C.COVERAGE_DECISIVE)
    statuses = []
    if not conditions["C7"]:
        statuses.append("CLASS_ARM_NOT_AVAILABLE")
    if not conditions["C8"]:
        statuses.append("NEAR_FORM_ARM_NOT_AVAILABLE")
    return {"conditions": conditions,
            "decisive": list(C.COVERAGE_DECISIVE),
            "decisive_met": decisive_met,
            "realised": {
                "n_eligible": len(rows), "n_below": len(below),
                "n_above": len(above),
                "tier12_groups_below": sorted(groups_below),
                "tier12_groups_above": sorted(groups_above),
                "near_rungs": len(near), "near_groups": sorted(near_groups),
                "straddling_groups": sorted(straddling_groups),
                "tier12_families": sorted(tier12_families),
                "tier12_groups": sorted(tier12_groups),
                "tier2_rungs": len(tier2_rows),
                "tier3_budget_near": [r["candidate"]
                                      for r in tier3_budget_near]},
            "identification_statuses": statuses}


def expansion_round(table: Sequence[Mapping[str, Any]], *, iota_a: float,
                    measured: Mapping[str, Sequence[int]]) -> dict[str, Any]:
    """§12.6's expansion, one round.

    Per family, in registered family order: if the family's measured rungs
    bracket iota_A, admit the reserve rungs lying strictly between the two
    adjacent measured severities whose iota values bracket it; otherwise admit
    the reserve rungs immediately beyond the family's extreme measured
    severity on the deficient side. At most four rungs per family per round.

    **The rule can only pick, never invent.** Everything it returns is already
    in the frozen reserve of §7.10; it reads iota and severity and nothing
    else; and it is deterministic given the table.
    """
    iota_by = {(r["family"], r["severity"]): r["iota"] for r in table}
    admitted: dict[str, list[int]] = {}
    for family in FAMILIES:
        have = sorted(measured.get(family, ()))
        if not have:
            continue
        reserve = [q for q in RESERVES[family] if q not in have]
        if not reserve:
            continue
        pairs = [(q, iota_by.get((family, q))) for q in have]
        pairs = [(q, v) for q, v in pairs if v is not None]
        if not pairs:
            continue
        below = [q for q, v in pairs if tie_key(v) < tie_key(iota_a)]
        above = [q for q, v in pairs if tie_key(v) > tie_key(iota_a)]
        # Direction is by RESTRICTIVENESS, not by severity value: for a
        # budget a larger q is looser, and for an exact count and a lower
        # bound a smaller q is (§7.10, §13.8). Reading the raw severity would
        # extend a marker ladder in the wrong direction, which is the
        # deficient side §7.10 widened the reserve to reach.
        def key(q: int, _family: str = family) -> int:
            return restrictiveness_key(_family, q)

        if below and above:
            edges = sorted([max(below, key=key), min(above, key=key)],
                           key=key)
            lo_key, hi_key = key(edges[0]), key(edges[1])
            picks = [q for q in reserve if lo_key < key(q) < hi_key]
        elif below:
            # every measured rung is HARDER than A (iota below): go easier,
            # which is the less restrictive direction.
            edge = min(key(q) for q in have)
            picks = sorted((q for q in reserve if key(q) < edge), key=key,
                           reverse=True)
        else:
            # every measured rung is EASIER than A: go harder.
            edge = max(key(q) for q in have)
            picks = sorted((q for q in reserve if key(q) > edge), key=key)
        picks = picks[:C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND]
        if picks:
            admitted[family] = sorted(picks)
    return {"admitted": admitted,
            "n_rungs": sum(len(v) for v in admitted.values()),
            "max_per_family": C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND}


def run_expansion(table: Sequence[Mapping[str, Any]], *, iota_a: float,
                  measured: Mapping[str, Sequence[int]],
                  measure) -> dict[str, Any]:
    """§12.6's loop, to its registered stopping rule.

    ``measure(admitted)`` generates the newly admitted rungs on the same 24
    pre-screen topics at the same cap and returns their table rows. The loop
    stops the moment C1-C6 pass; at most two rounds run.

    **When it stops without passing**, the replication records
    ``REFERENCE_SUPPORT_NOT_IDENTIFIED`` at design time, runs without the core
    and spectrum arms, and never reports a Delta_R or a delta_difficulty
    obtained from an unqualified pool. This is a registered outcome and not a
    fallback to be avoided: no band is widened, no vacuity ceiling lowered and
    no severity authored to reach it.
    """
    rows = list(table)
    state = dict({k: list(v) for k, v in measured.items()})
    rounds: list[dict[str, Any]] = []
    coverage = coverage_criterion(rows, iota_a=iota_a)
    for _ in range(C.EXPANSION_MAX_ROUNDS):
        if coverage["decisive_met"]:
            break
        plan = expansion_round(rows, iota_a=iota_a, measured=state)
        if not plan["admitted"]:
            rounds.append({**plan, "stopped": "CANDIDATE_RESERVE_EXHAUSTED"})
            break
        new_rows = list(measure(plan["admitted"]))
        rows.extend(new_rows)
        for family, picks in plan["admitted"].items():
            state.setdefault(family, []).extend(picks)
        coverage = coverage_criterion(rows, iota_a=iota_a)
        rounds.append({**plan, "coverage_after": coverage["conditions"]})
    statuses = list(coverage["identification_statuses"])
    if not coverage["decisive_met"]:
        statuses += ["REFERENCE_SUPPORT_NOT_IDENTIFIED",
                     "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]
        if any(r.get("stopped") == "CANDIDATE_RESERVE_EXHAUSTED"
               for r in rounds):
            statuses.append("CANDIDATE_RESERVE_EXHAUSTED")
    return {"rounds": rounds, "coverage": coverage,
            "measured": {k: sorted(v) for k, v in state.items()},
            "identification_statuses": sorted(set(statuses)),
            "vocabulary_frozen": True,
            "note": "the regime-screen record names every measured rung; "
                    "every later stage selects from that named set, and "
                    "Gate 1 certifies exactly the instruments the freeze "
                    "contains"}
