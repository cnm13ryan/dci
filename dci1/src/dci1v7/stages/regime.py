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

from itertools import zip_longest
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.analysis.intervals import interval_intersects, wilson
from dci1v7.protocol import constants as C
from dci1v7.protocol import open_items
from dci1v7.stages.calibration_table import tie_key
from dci1v7.stages.selection import restrictiveness_key
from dci1v7.verifiers.constraints import (
    FAMILIES, LADDERS, RESERVES, SELECTABLE_FAMILY_IDS,
    assert_selectable, focal_severities,
)

__all__ = ["StructuralScreen", "carry_candidate", "carried_set",
           "calibration_priority", "select_operating_point", "select_focal", "select_target",
           "assert_construct_floor", "coverage_criterion", "expansion_round",
           "run_expansion", "ELIGIBILITY_FORMULATIONS", "coverage_eligibility",
           "coverage_rows", "calibration_coverage_rows",
           "regime_adequacy", "grid_resolution",
           "C4_CONDITIONS", "family_c4_state", "family_deficiency",
           "expansion_plan_for_family", "COVERAGE_ROW_KEYS",
           "assert_coverage_shape"]


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
    """§12.2's two-rule retention verdict for one rung.

    A §34 D24 probe-only stand-in is refused here rather than returned as
    ``carried: False``: it is not a candidate that failed the screen, it is
    an instrument the screen may not see at all, and the two are different
    facts on the record.
    """
    assert_selectable(kind, where="§12.2 stages.regime.carry_candidate")
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


def grid_resolution(curve: Mapping[int, float], *, band: tuple,
                    grid: Sequence[int]) -> dict[str, Any]:
    """§12.3: does the grid jump a whole band between adjacent severities?

    §12.3 registers three diagnoses for a selection that finds nothing, and
    they are not the same fact. ``*_RANGE_EXHAUSTED`` says the model's curve
    never enters the band. ``GRID_RESOLUTION_INSUFFICIENT`` says the curve
    passes *through* the band between two adjacent registered severities
    without either of them landing in it --- the grid is too coarse, which is
    a statement about the registered ladder and not about the model. The
    section names it and no production caller could reach it.
    """
    low, high = band
    measured = [q for q in grid if q in curve]
    straddles = []
    for left, right in zip(measured, measured[1:]):
        a, b = curve[left], curve[right]
        if (a > high and b < low) or (a < low and b > high):
            straddles.append({"severities": [left, right],
                              "compliance": [a, b]})
    return {"insufficient": bool(straddles), "straddling_pairs": straddles,
            "band": [low, high], "measured": measured}


def regime_adequacy(*, solo_a: float, solo_b: float,
                    vacuity_b: float,
                    graded_shares: Mapping[str, Mapping[str, float]]
                    ) -> dict[str, Any]:
    """§12.4's three conditions, on the pooled calibration topics.

    Condition 3 is a statement about a **share** and the section says so in
    its own words, because read as a statement about the mean it fires on
    every severity §12.3 declares eligible and contradicts its own neighbour.
    ``graded_shares`` maps the outcome constraint to its measured
    ``graded_share_above`` and ``graded_share_below``.

    A replication that fails any condition records ``REGIME_NOT_FOUND``,
    which is a statement about the registered grid and never about the model
    or the hypothesis.
    """
    failures: list[dict[str, Any]] = []
    for name, value, band in (("A", solo_a, C.TARGET_BAND),
                              ("B", solo_b, C.FOCAL_BAND)):
        if value is None or not (band[0] <= value <= band[1]):
            failures.append({"condition": 1, "constraint": name,
                             "solo_compliance": value, "band": list(band),
                             "reason": f"{name}'s solo compliance is not "
                                       f"inside {list(band)}"})
    if vacuity_b is None or vacuity_b > C.REGIME_VACUITY_MAX:
        failures.append({"condition": 2, "constraint": "B",
                         "solo_vacuity": vacuity_b,
                         "max": C.REGIME_VACUITY_MAX,
                         "reason": "B's realised solo vacuity rate exceeds "
                                   f"{C.REGIME_VACUITY_MAX}"})
    for name in ("A", "B"):
        shares = dict(graded_shares.get(name) or {})
        for key in ("graded_share_above", "graded_share_below"):
            share = shares.get(key)
            if share is None or share > C.GRADED_DEGENERACY_SHARE_MAX:
                failures.append({
                    "condition": 3, "constraint": name, "share_name": key,
                    "share": share, "max": C.GRADED_DEGENERACY_SHARE_MAX,
                    "reading": C.GRADED_CLAUSE_READING,
                    "reason": f"{name}'s {key} exceeds "
                              f"{C.GRADED_DEGENERACY_SHARE_MAX}; §12.4 "
                              "condition 3 is about a share of responses, "
                              "not about the mean"})
    return {
        "adequate": not failures,
        "failures": failures,
        "conditions": {
            "1": "solo compliance of A and of B lie inside their bands",
            "2": f"realised solo vacuity for B at most {C.REGIME_VACUITY_MAX}",
            "3": "the share above 0.99 and the share below 0.01 are each at "
                 f"most {C.GRADED_DEGENERACY_SHARE_MAX}, for each outcome "
                 "constraint"},
        "measured": {"solo_a": solo_a, "solo_b": solo_b,
                     "vacuity_b": vacuity_b,
                     "graded_shares": {k: dict(v)
                                       for k, v in graded_shares.items()}},
        "bands": {"A": list(C.TARGET_BAND), "B": list(C.FOCAL_BAND)},
        "vacuity_max": C.REGIME_VACUITY_MAX,
        "graded_degeneracy_share_max": C.GRADED_DEGENERACY_SHARE_MAX,
        "graded_degeneracy_thresholds": [C.GRADED_DEGENERACY_LOW,
                                         C.GRADED_DEGENERACY_HIGH],
    }


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
                           chance_compliance_at_m_star: float,
                           **kwargs: Any) -> dict[str, Any]:
    """§34 D17: whether m* carries a construct-strength floor.

    §12.3 selects the focal severity whose *compliance* is nearest 0.80, over
    a grid now reaching m = 16. Compliance is a behavioural quantity and 0.80
    compliance at m = 13 is a real constraint on a model's writing; as a
    **construct**, *every word at most 13 letters* is close to a null
    instruction in ordinary English, and the focal band is defined on
    compliance rather than on construct strength.

    The rule lives in ``stages/construct_strength.py`` --- the named
    quantities, their provenance, the neighbour report and the floor
    specification --- and this is the name §34 D17 registers as the blocked
    call, kept so that the decision's ``blocks_calls`` entry and the function
    a caller reaches for are the same string. **No threshold is invented in
    either place**: the ``floor`` branch requires the researcher to supply
    one when they close D17, and refuses rather than guessing.
    """
    from dci1v7.stages import construct_strength

    return construct_strength.assert_construct_floor(
        m_star, chance_compliance_at_m_star=chance_compliance_at_m_star,
        **kwargs)


#: §12.6's two admissible eligibility rules, as open item U4 carries them.
#: The section names "§13's band on iota"; §13 registers its band on p_solo
#: and no band on iota, so both readings are constructed and neither runs
#: until a researcher resolves U4.
ELIGIBILITY_FORMULATIONS: dict[str, str] = {
    "E1": "iota inside [0.10, 0.90] and pre-screen solo vacuity <= 0.10",
    "E2": ("raw solo compliance inside [0.10, 0.90] and pre-screen solo "
           "vacuity <= 0.10"),
}


def coverage_eligibility(row: Mapping[str, Any], *,
                         formulation: str | None = None) -> dict[str, Any]:
    """§12.6's eligibility verdict for one pre-screen rung.

    ``coverage_criterion`` has always read ``row["eligible"]`` and nothing in
    this repository ever set it, so the criterion evaluated on an empty set
    and C1-C6 were False on every replication. Setting it requires knowing
    which quantity §13's band applies to, which is open item U4: the two
    readings admit different rungs, so they can produce different C1-C6
    verdicts, a different expansion, and a different admitted arm set.

    Passing ``formulation`` explicitly runs a **named** construction and
    records which one; passing nothing reads U4's resolution and refuses
    while it is unresolved.
    """
    name = formulation or open_items.assert_item_resolved(
        "U4", where="stages.regime.coverage_eligibility")
    if name not in ELIGIBILITY_FORMULATIONS:
        raise ProtocolError(
            f"{name!r} is not a registered §12.6 eligibility formulation; "
            f"U4 carries {sorted(ELIGIBILITY_FORMULATIONS)}")
    vacuity = row.get("vacuity")
    coordinate = row.get("iota") if name == "E1" else row.get("solo")
    low, high = C.HEADROOM_BAND
    reasons: list[str] = []
    if coordinate is None:
        reasons.append("no measured coordinate")
    elif not (low <= coordinate <= high):
        reasons.append(f"{coordinate:.4f} outside {[low, high]}")
    if vacuity is None:
        reasons.append("no measured vacuity")
    elif vacuity > C.REFERENCE_VACUITY_MAX:
        reasons.append(f"vacuity {vacuity:.4f} above "
                       f"{C.REFERENCE_VACUITY_MAX}")
    return {"eligible": not reasons, "formulation": name,
            "coordinate": coordinate, "vacuity": vacuity,
            "reason": "; ".join(reasons) or None}


def coverage_rows(table: Sequence[Mapping[str, Any]],
                  carried: Sequence[str], *,
                  formulation: str | None = None) -> list[dict[str, Any]]:
    """The pre-screen table in the shape ``coverage_criterion`` registers.

    ``coverage_criterion`` needs ``candidate``, ``family``,
    ``structural_tier``, ``feature_group``, ``constraint_class``, ``iota`` and
    ``eligible``. The production caller passed rows carrying ``kind`` and
    ``tier`` and no ``eligible``, so every condition was evaluated over zero
    rungs. The join is here, from the registered family metadata, so the
    criterion reads measured quantities rather than a caller's shape.
    """
    kept = set(carried)
    out: list[dict[str, Any]] = []
    for row in table:
        if row.get("candidate") not in kept:
            continue
        kind = row.get("kind")
        family = FAMILIES.get(kind)
        if family is None:            # A and B: outcome constraints, no tier
            continue
        verdict = coverage_eligibility(row, formulation=formulation)
        out.append({
            "candidate": row["candidate"],
            "family": kind,
            "severity": row["severity"],
            "structural_tier": family.structural_tier,
            "feature_group": family.feature_group,
            "constraint_class": family.constraint_class,
            "iota": row.get("iota"),
            "solo": row.get("solo"),
            "vacuity": row.get("vacuity"),
            "eligible": verdict["eligible"],
            "eligibility": verdict,
        })
    return out


def calibration_coverage_rows(rows: Sequence[Mapping[str, Any]], *,
                              formulation: str | None = None
                              ) -> list[dict[str, Any]]:
    """§12.6's criterion shape, built from §13.11's **calibration** table.

    §12.6 is certified on the pre-screen basis: iota over 24 pre-screen topics
    at one draw, against an ``iota_a_prescreen`` measured on the same 24. That
    is a paired comparison and it is the right one *for the certificate*. What
    reference selection then matches on is Gate 2's ``iota_a`` --- 192
    calibration topics at four draws --- and re-reading the pre-screen table
    against **that** number compares an iota measured on one sample to an
    iota_A measured on another. The difference such a comparison reports is
    part real and part the two samples, and nothing separates them.

    Gate 2 measures every calibrated candidate's solo compliance, chance
    compliance and solo vacuity on the same 192 topics and the same four draws
    it measures A on, so the criterion can be evaluated on a basis where every
    quantity in it --- iota(R), the eligibility coordinate, the vacuity and
    iota_A --- comes from one controlled set of cases. That is this function,
    and it costs no generation: the rows already exist on the Gate-2 record.

    Two differences from the pre-screen basis are real and are not defects:
    the population is §12.7's calibrated set rather than §12.2's carried set,
    which is the set the study can actually draw a reference from; and the
    measurement is 32x the draws, which is the point.

    ``coverage_eligibility`` is called unchanged, so the two bases run **one**
    formulation, not two readings of one.
    """
    out: list[dict[str, Any]] = []
    for row in rows:
        kind = row.get("kind")
        family = FAMILIES.get(kind)
        if family is None:            # A and B: outcome constraints, no tier
            continue
        solo = row.get("solo_compliance")
        chance = row.get("chance_compliance")
        iota = (None if solo is None or chance is None
                or chance >= C.CHANCE_DEGENERACY_MAX
                else (solo - chance) / (1.0 - chance))
        shaped = {"candidate": f"{kind}:{row['severity']}",
                  "kind": kind, "severity": row["severity"],
                  "iota": iota, "solo": solo,
                  "vacuity": row.get("solo_vacuity")}
        verdict = coverage_eligibility(shaped, formulation=formulation)
        out.append({
            "candidate": shaped["candidate"],
            "family": kind,
            "severity": row["severity"],
            "structural_tier": family.structural_tier,
            "feature_group": family.feature_group,
            "constraint_class": family.constraint_class,
            "iota": iota,
            "solo": solo,
            "vacuity": shaped["vacuity"],
            "eligible": verdict["eligible"],
            "eligibility": verdict,
        })
    return out


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
    # §12.6/A16: a rung whose difficulty coordinate is undefined is dropped
    # from every condition, and the drop is recorded.
    #
    # Each of C1-C8 is a position relative to iota_A --- below, above, near
    # within the caliper, straddling within a family, feature groups on each
    # side --- and `CHANCE_DEGENERACY_MAX` is the registered point at which
    # iota is not defined at all (§11.2, `DIFFICULTY_COORDINATE_DEGENERATE`).
    # A rung with no coordinate has no position, so there is no condition it
    # could truthfully serve.
    #
    # It became reachable when U4 resolved at E2. E2 judges eligibility on
    # raw solo compliance, which is measured whatever the chance level does,
    # so a rung can be eligible and coordinate-less at once; under E1 the
    # coordinate IS iota and the case cannot arise. Until 2026-08-26 this
    # line read `r["iota"]` unguarded and the stage died on a TypeError ---
    # v5 ran E2 too and never met it, because its coordinate-less rungs all
    # had solo outside the band and were ineligible for a different reason.
    #
    # **Dropping is the closed direction and that is why it is the rule.**
    # Every condition below is an existence or a count --- "there are rungs
    # on both sides", "at least N groups", "at least N rungs" --- so removing
    # a rung can only make a condition harder to meet and never easier. The
    # rule therefore cannot be what lets a replication pass §12.6, whichever
    # rungs turn out to be degenerate.
    #
    # `coverage_eligibility` is deliberately untouched: U4's registered
    # predicate still decides eligibility on the quantity E2 names, and this
    # decides only which eligible rungs carry a position.
    eligible = [r for r in table if r.get("eligible")]
    rows = [r for r in eligible if r.get("iota") is not None]
    coordinate_undefined = [r for r in eligible if r.get("iota") is None]
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
    for entries in by_family.values():
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
            # A16. Recorded, not silently absent: a reader of this record can
            # see exactly which measured rungs the criterion could not place
            # and why, and `n_eligible` above counts only the placed ones.
            "coordinate_undefined": [
                {"candidate": r["candidate"], "family": r["family"],
                 "severity": r["severity"],
                 "structural_tier": r["structural_tier"],
                 "feature_group": r["feature_group"],
                 "constraint_class": r["constraint_class"],
                 "solo": r.get("solo"), "vacuity": r.get("vacuity"),
                 "eligible_under": (r.get("eligibility") or {})
                 .get("formulation"),
                 "status": "DIFFICULTY_COORDINATE_DEGENERATE",
                 "why": "chance compliance reached CHANCE_DEGENERACY_MAX = "
                        f"{C.CHANCE_DEGENERACY_MAX}, so iota is undefined "
                        "(§11.2) and the rung has no position relative to "
                        "iota_A; §12.6's conditions are all positions, so it "
                        "is dropped from every one of them"}
                for r in sorted(coordinate_undefined,
                                key=lambda r: r["candidate"])],
            "n_coordinate_undefined": len(coordinate_undefined),
            "realised": {
                "n_eligible": len(rows),
                "n_eligible_before_coordinate_drop": len(eligible),
                "n_below": len(below),
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


#: §12.6's three C4 conditions, in the order ``coverage_criterion`` evaluates
#: them. A family's deficiency is the **first** one it fails, so exactly one
#: direction rule applies and the plan is single-valued (E1).
C4_CONDITIONS = ("MISSING_SIDE", "TOO_FEW_RUNGS", "SPAN_SHORT")


def family_c4_state(entries: Sequence[Mapping[str, Any]], *, iota_a: float
                    ) -> dict[str, Any]:
    """One family's C4 state over its **eligible** measured rungs.

    C4 counts a straddling group from rungs that passed §12.6's eligibility,
    and ``coverage_criterion`` filters on ``eligible`` before it groups by
    family. The expansion has to read the same set or it would repair a
    condition nobody is evaluating.
    """
    rows = [e for e in entries if e.get("eligible") and e.get("iota")
            is not None]
    below = [e for e in rows if tie_key(e["iota"]) < tie_key(iota_a)]
    above = [e for e in rows if tie_key(e["iota"]) > tie_key(iota_a)]
    span = (max(e["iota"] for e in rows) - min(e["iota"] for e in rows)
            if rows else 0.0)
    return {"n_rungs": len(rows), "has_below": bool(below),
            "has_above": bool(above), "span": span,
            "severities": sorted(e["severity"] for e in rows)}


def family_deficiency(state: Mapping[str, Any]) -> str | None:
    """E1: C4's first unmet condition for this family, or None if it is met.

    Order is ``coverage_criterion``'s own: straddling first, then the rung
    count, then the span. A family meeting all three already contributes a
    straddling group and the expansion skips it.
    """
    if not (state["has_below"] and state["has_above"]):
        return "MISSING_SIDE"
    if state["n_rungs"] < C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY:
        return "TOO_FEW_RUNGS"
    if state["span"] < C.COVERAGE_MIN_WITHIN_FAMILY_SPAN:
        return "SPAN_SHORT"
    return None


def _harder_than(reserve: Sequence[int], edge: int, key) -> list[int]:
    """E3: reserve rungs more restrictive than ``edge``, nearest first."""
    return sorted((q for q in reserve if key(q) > edge),
                  key=lambda q: (key(q) - edge, q))


def _easier_than(reserve: Sequence[int], edge: int, key) -> list[int]:
    """E3: reserve rungs less restrictive than ``edge``, nearest first."""
    return sorted((q for q in reserve if key(q) < edge),
                  key=lambda q: (edge - key(q), q))


def _alternate(first: Sequence[int], second: Sequence[int]) -> list[int]:
    """Interleave two ordered lists, ``first`` leading, keeping both orders."""
    out: list[int] = []
    for a, b in zip_longest(first, second):
        if a is not None:
            out.append(a)
        if b is not None:
            out.append(b)
    return out


def expansion_plan_for_family(family: str, *,
                              entries: Sequence[Mapping[str, Any]],
                              measured: Sequence[int],
                              iota_a: float) -> dict[str, Any]:
    """§12.6's per-family expansion, repaired for V6-E01 (E1-E6).

    **What v5 did and why it could not work.** v5 branched on whether the
    family's measured rungs bracketed iota_A: if they did it admitted the
    reserve rungs lying strictly *between* the two adjacent bracketing edges,
    and otherwise the rungs immediately beyond the extreme measured severity
    on the deficient side. Replayed on all four signed v5 pre-screen tables
    that rule admitted **zero** Tier-1 reserve rungs, in either round, on
    every replication --- and §7.10 had widened that reserve from 1..10 to
    1..12 for C4's within-family span specifically. Two structural reasons,
    and a third that is decisive on its own:

    1. a straddling family's bracketing edges are adjacent in the round-0
       ladder 1..8, so every rung between them is already measured and the
       pick set is empty;
    2. the one-sided families were one-sided *below* --- every measured rung
       harder than A --- so the rule went easier while the unmeasured reserve
       was harder;
    3. **interpolation cannot raise a span at all.** C4's span is
       ``max(iota) - min(iota)`` over the family's eligible rungs, and a rung
       admitted strictly between two measured edges cannot lie outside their
       range. On the one condition three v5 replications failed, the
       mechanism was incapable of helping by construction.

    **The repair.** The deficiency decides the direction, and the deficiency
    is C4's own first unmet condition (E1):

    * ``MISSING_SIDE`` --- extend toward the absent side by restrictiveness,
      exactly as v5 did. Both sides absent (a family with no eligible rung)
      extends both ways.
    * ``TOO_FEW_RUNGS`` --- interpolate between the bracketing edges, exactly
      as v5 did.
    * ``SPAN_SHORT`` --- extend **outward from both extremes**, alternating
      harder-then-easier by restrictiveness. This branch does not exist in v5
      and it is the whole repair.

    Direction is by **restrictiveness**, never by raw severity: for a budget a
    larger q is looser, and for an exact count and a lower bound a smaller q
    is (§7.10, §13.8). ``iota`` is measurably non-monotonic in severity for
    the marker families, so nothing here assumes monotonicity (E5): candidates
    are ordered by restrictiveness, a structural property of the predicate
    known before any data, and the deficiency is evaluated on measured iota
    afterwards. A rung that fails to move iota outward is a measurement, not
    an error.

    **The rule can only pick, never invent** (E6): every returned severity is
    already in the frozen reserve of §7.10, it reads iota and severity and
    nothing else, and it is deterministic given the table.
    """
    have = sorted(measured)
    reserve = [q for q in RESERVES[family] if q not in have]
    state = family_c4_state(entries, iota_a=iota_a)
    deficiency = family_deficiency(state)
    plan = {"family": family, "deficiency": deficiency, "direction": None,
            "picks": [], "state": state, "reserve_available": len(reserve)}
    if deficiency is None:
        plan["direction"] = "NONE"
        plan["reason"] = "C4 already met by this family"
        return plan
    if not have or not reserve:
        plan["direction"] = "NONE"
        plan["reason"] = ("no measured rung" if not have
                          else "frozen reserve exhausted for this family")
        return plan

    def key(q: int, _family: str = family) -> int:
        return restrictiveness_key(_family, q)

    iota_by = {e["severity"]: e["iota"] for e in entries
               if e.get("iota") is not None}
    eligible = [q for q in have if q in set(state["severities"])]
    # Edges are taken over the ELIGIBLE rungs where any exist, because those
    # are the rungs C4 counts; a family with none falls back to everything it
    # measured, so the plan is still defined.
    basis = eligible or have
    harder_edge = max(key(q) for q in basis)
    easier_edge = min(key(q) for q in basis)

    if deficiency == "TOO_FEW_RUNGS":
        below = [q for q in basis if q in iota_by
                 and tie_key(iota_by[q]) < tie_key(iota_a)]
        above = [q for q in basis if q in iota_by
                 and tie_key(iota_by[q]) > tie_key(iota_a)]
        lo, hi = sorted([max(below, key=key), min(above, key=key)], key=key)
        lo_key, hi_key = key(lo), key(hi)
        picks = sorted((q for q in reserve if lo_key < key(q) < hi_key),
                       key=lambda q: (key(q), q))
        plan["direction"] = "INTERPOLATE"
    elif deficiency == "MISSING_SIDE":
        # iota below iota_A means the rung is HARDER than A. A family with no
        # rung above iota_A needs an EASIER one, and vice versa.
        want_easier = not state["has_above"]
        want_harder = not state["has_below"]
        easier = _easier_than(reserve, easier_edge, key) if want_easier else []
        harder = _harder_than(reserve, harder_edge, key) if want_harder else []
        if want_easier and want_harder:
            picks = _alternate(harder, easier)
            plan["direction"] = "OUTWARD_BOTH"
        else:
            picks = easier or harder
            plan["direction"] = "EASIER" if want_easier else "HARDER"
    else:                                                    # SPAN_SHORT
        harder = _harder_than(reserve, harder_edge, key)
        easier = _easier_than(reserve, easier_edge, key)
        # "starting from the extreme whose unmeasured reserve is non-empty";
        # when both are, harder leads.
        picks = (_alternate(harder, easier) if harder
                 else _alternate(easier, harder))
        plan["direction"] = "OUTWARD_BOTH"

    plan["picks"] = picks[:C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND]
    if not plan["picks"]:
        plan["reason"] = ("no reserve rung lies in the direction the "
                          f"{deficiency} deficiency requires")
    return plan


def expansion_round(table: Sequence[Mapping[str, Any]], *, iota_a: float,
                    measured: Mapping[str, Sequence[int]]) -> dict[str, Any]:
    """§12.6's expansion, one round, over every registered family in order.

    Per family, ``expansion_plan_for_family`` decides the direction from C4's
    first unmet condition and picks at most
    ``EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND`` rungs from the frozen
    reserve. The per-family plans are returned beside the admitted set so the
    stage record says *why* each family was extended --- v5's record said only
    that nothing was, which is what let V6-E01 stand through a whole study.
    """
    by_family: dict[str, list[Mapping[str, Any]]] = {}
    for row in table:
        by_family.setdefault(row.get("family"), []).append(row)
    admitted: dict[str, list[int]] = {}
    plans: list[dict[str, Any]] = []
    for family in SELECTABLE_FAMILY_IDS:
        have = sorted(measured.get(family, ()))
        if not have:
            continue
        plan = expansion_plan_for_family(
            family, entries=by_family.get(family, ()), measured=have,
            iota_a=iota_a)
        plans.append(plan)
        if plan["picks"]:
            admitted[family] = sorted(plan["picks"])
    return {"admitted": admitted,
            "n_rungs": sum(len(v) for v in admitted.values()),
            "max_per_family": C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND,
            "plans": plans,
            "by_deficiency": {
                name: sorted(p["family"] for p in plans
                             if p["deficiency"] == name)
                for name in C4_CONDITIONS}}


#: The keys ``coverage_criterion`` reads from a row. A row lacking one is not
#: a row the criterion can evaluate, and in v5 it was silently **dropped**:
#: ``run_expansion`` extended its working table with raw ``difficulty_table``
#: rows, which carry ``family``, ``severity`` and ``iota`` but no
#: ``eligible``, no ``structural_tier``, no ``feature_group`` and no
#: ``constraint_class``. ``coverage_criterion`` filters on ``eligible`` first,
#: so **every rung the expansion measured was invisible to the criterion the
#: expansion exists to satisfy** (V6-E02). The invariant is asserted here,
#: on the mandatory path, so the same class of defect refuses instead of
#: passing.
COVERAGE_ROW_KEYS = ("candidate", "family", "severity", "structural_tier",
                     "feature_group", "constraint_class", "iota", "eligible")


def assert_coverage_shape(rows: Sequence[Mapping[str, Any]], *, where: str
                          ) -> None:
    """Refuse a row ``coverage_criterion`` would silently drop (V6-E02)."""
    for index, row in enumerate(rows):
        missing = [k for k in COVERAGE_ROW_KEYS if k not in row]
        if missing:
            raise ProtocolError(
                f"{where}: row {index} ({row.get('candidate')!r}) is missing "
                f"{missing}. §12.6's criterion reads "
                f"{list(COVERAGE_ROW_KEYS)} and filters on `eligible` "
                "first, so a row without them is "
                "counted as ineligible rather than refused --- which is how "
                "v5 measured 59 to 99 expansion rungs per replication that "
                "its own coverage criterion never saw. Join through "
                "`coverage_rows` before the criterion reads it")


def run_expansion(table: Sequence[Mapping[str, Any]], *, iota_a: float,
                  measured: Mapping[str, Sequence[int]],
                  measure) -> dict[str, Any]:
    """§12.6's loop, to its registered stopping rule.

    ``measure(admitted)`` generates the newly admitted rungs on the same 24
    pre-screen topics at the same cap and returns their rows **in
    ``coverage_rows``' shape**. The loop stops the moment C1-C6 pass; at most
    two rounds run.

    **The shape is a contract now, and V6-E02 is why.** v5's ``measure``
    returned raw ``difficulty_table`` rows, which carry no ``eligible`` field;
    ``coverage_criterion`` filters on ``eligible`` before anything else, so
    every rung the expansion measured was dropped from the criterion it was
    measured to satisfy. Three v5 replications measured 93 to 99 reserve rungs
    across two rounds and their recorded coverage was computed over the
    round-0 set every time. ``assert_coverage_shape`` refuses that shape here,
    on the mandatory path.

    **When it stops without passing**, the replication records
    ``REFERENCE_SUPPORT_NOT_IDENTIFIED`` at design time, runs without the core
    and spectrum arms, and never reports a Delta_R or a delta_difficulty
    obtained from an unqualified pool. This is a registered outcome and not a
    fallback to be avoided: no band is widened, no vacuity ceiling lowered and
    no severity authored to reach it.
    """
    rows = list(table)
    assert_coverage_shape(rows, where="run_expansion: the pre-screen table")
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
        # V6-E02: `measure` returns rows in the criterion's own shape, and
        # the assertion is what makes that a contract rather than a habit.
        assert_coverage_shape(
            new_rows, where=f"run_expansion: round {len(rounds)}'s new rungs")
        rows.extend(new_rows)
        for family, picks in plan["admitted"].items():
            state.setdefault(family, []).extend(picks)
        coverage = coverage_criterion(rows, iota_a=iota_a)
        rounds.append({**plan, "coverage_after": coverage["conditions"],
                       "n_measured": len(new_rows),
                       "n_eligible_after": coverage["realised"]["n_eligible"]})
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
