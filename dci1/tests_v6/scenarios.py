"""Conditional branches of the v5 lifecycle, each driven to its registered end.

One happy-path walk is not an execution-path audit. Every defect in the
V5-E2/E6/E8/E9-E12 family lived on a branch the happy path never took: a
terminal status with no production raiser, an escalation nothing triggered, a
family nobody computed, a claim emitter with no caller. A suite that runs the
normal path and reports green is exactly the instrument that missed them.

So each scenario here puts the **production** path into one registered branch
and records what the production path decided. Scenarios branch from a real
signed prefix walk (``synthetic_lifecycle.walk(..., stop_after=...)``) rather
than from a record assembled by hand, so the stage under test reads the same
shapes it reads in a real replication.

The fixture knobs (``RATE_OVERRIDES``, ``COMPOSED_OVERRIDES``,
``SHORT_ANSWER_LABELS``) shape the *fixture*, never a rule. Nothing here
changes a threshold, a population, an estimator or a claim; what they buy is a
harness in which a registered branch can be reached at all.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v6.engine.context import synthetic_context
from dci1v6.engine.paths import model_tree
from dci1v6.protocol import constants as C
from dci1v6.engine import transitions
from dci1v6.run import (field_access, freeze_run, gates_run,
                        prefreeze_run)
from dci1v6.run.lifecycle import TerminalStatus

from tests_v6 import synthetic_lifecycle as SL

__all__ = ["SCENARIOS", "run_scenario", "run_all", "prefix_walk"]


# --------------------------------------------------------------- machinery

class Prefix:
    """A signed prefix of a replication, copyable so branches are cheap."""

    def __init__(self, root: Path, state: Mapping[str, Any]):
        self.root = root
        self.state = dict(state)

    @property
    def payloads(self) -> dict[str, Any]:
        return self.state["payloads"]

    def branch(self, into: Path) -> tuple[Any, dict[str, Any]]:
        """A private copy of the tree, and the context to drive it."""
        shutil.copytree(self.root, into, dirs_exist_ok=True)
        repo_root = Path(self.state["repo_root"])
        context = synthetic_context(into, repo_root=repo_root)
        tree = model_tree(context, SL.MODEL_KEY)
        return tree, {"commit": self.state["commit"],
                      "bank": self.state["bank"], "repo_root": repo_root}


#: One prefix per stop stage, shared by every scenario that branches from it.
#: Five scenarios branch from GATE_1 and each would otherwise pay for its own
#: walk to get there; a prefix is signed evidence and copying it is what
#: `Prefix.branch` does, so sharing it changes nothing a scenario observes.
_PREFIXES: dict[str, Prefix] = {}


def prefix_walk(root: Path, stop_after: str, **kwargs: Any) -> Prefix:
    """Run the lifecycle to ``stop_after`` and keep the tree."""
    if not kwargs and stop_after in _PREFIXES:
        return _PREFIXES[stop_after]
    try:
        SL.walk(root, stop_after=stop_after, **kwargs)
    except SL.WalkStopped as stopped:
        prefix = Prefix(root, stopped.state)
        if not kwargs:
            _PREFIXES[stop_after] = prefix
        return prefix
    raise AssertionError(f"the walk did not stop after {stop_after}")


def _gate2(tree: Any, ctx: Mapping[str, Any], rungs: Any) -> dict[str, Any]:
    """Gate 2 on a branched tree, through the production runner.

    The backend's lookup carries §7.2's extension rungs as well as the
    registered grid. It has to: a scripted responder that cannot recognise
    `B:15` in a prompt writes an answer under no length budget at all, whose
    realised compliance is the natural-length distribution --- which put the
    curve ABOVE the focal band at 15 and below it at 14, and the production
    path then correctly diagnosed a grid that jumps the band. A fixture that
    cannot render the branch under test does not test it.
    """
    from dci1v6.verifiers.constraints import Constraint

    lookup = list(rungs) + [Constraint("B", q, extended=True)
                            for q in C.FOCAL_EXTENSION]
    return gates_run.run_gate2(
        tree, producing_commit=ctx["commit"], environment_digest="scenario",
        bank=ctx["bank"], generate=SL._scripted_for(lookup),
        topic_limit=96).payload


def _terminal(fn: Callable[[], Any]) -> dict[str, Any]:
    """Run something expected to reach a registered terminal status."""
    try:
        fn()
    except TerminalStatus as terminal:
        return {"terminal": terminal.status, "criterion": terminal.criterion,
                "observed": terminal.observed}
    except (ProtocolError, IntegrityError) as refused:
        return {"refused": f"{type(refused).__name__}: {refused}"}
    return {"terminal": None}


# --------------------------------------------------------------- scenarios

def scenario_normal_full_path(root: Path) -> dict[str, Any]:
    """1. The ordinary replication, with every field read recorded.

    This is also the payload and consumption source for the runtime contract
    audit: a declared reader that never reads is only visible against a run.
    """
    with field_access.recording():
        result = SL.walk(root)
        reads = field_access.observed()
    payloads = result["payloads"]
    return {"branch": "the full eighteen-stage path",
            "stages": sorted(payloads),
            "n_stages": len(payloads),
            "payloads": payloads, "reads": reads,
            "outcome": payloads[C.STAGE_FINAL_REPORT]["outcome"]}


def scenario_no_viable_regime(root: Path) -> dict[str, Any]:
    """2. §12.4 condition 2 fails: B's realised solo vacuity exceeds 0.10.

    Condition 1 is implied by §12.3's own selection --- both read the same
    pooled curve --- so conditions 2 and 3 are the operative routes to
    ``REGIME_NOT_FOUND``, and this takes condition 2.
    """
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE1)
    tree, ctx = prefix.branch(root / "branch")
    rungs = SL.screen_rungs()
    SL.SHORT_ANSWER_LABELS.update(f"B:{q}" for q in C.FOCAL_GRID)
    try:
        observed = _terminal(lambda: _gate2(tree, ctx, rungs))
    finally:
        SL.clear_overrides()
    return {"branch": "§12.4's regime-adequacy conditions", **observed,
            "expected": "REGIME_NOT_FOUND"}


def scenario_focal_extension_required(root: Path) -> dict[str, Any]:
    """3. §7.2's extension {15, 16} is measured, because §12.3 escalated."""
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE1)
    tree, ctx = prefix.branch(root / "branch")
    rungs = SL.screen_rungs()
    # Nothing in the registered grid reaches the focal band; 15 and 16 do.
    SL.RATE_OVERRIDES.update({f"B:{q}": 0.30 for q in C.FOCAL_GRID})
    SL.RATE_OVERRIDES.update({f"B:{q}": 0.78 for q in C.FOCAL_EXTENSION})
    payload: dict[str, Any] = {}
    try:
        observed = _terminal(
            lambda: payload.update(_gate2(tree, ctx, rungs)))
    finally:
        SL.clear_overrides()
    # What §7.2 registers is that the EXTENSION IS MEASURED when §12.3
    # escalates. Whether the re-selection then finds a rung is the model's
    # business and §12.3's other two diagnoses cover the cases where it does
    # not, so both outcomes are reported here rather than one being an error.
    # A terminal status carries whatever the rule that raised it recorded ---
    # §12.3's a curve, §34 D17's a sentence --- so the curve is read where it
    # is and its absence is not an error.
    raw = observed.get("observed") if observed.get("terminal") else None
    curve = (raw or {}).get("curve") if isinstance(raw, Mapping) else None
    if curve is None:
        curve = (payload.get("focal_selection") or {}).get("curve") or {}
    measured = sorted(int(q) for q in curve)
    return {"branch": "§12.3 and §7.2's focal escalation",
            "terminal": observed.get("terminal"),
            "criterion": observed.get("criterion"),
            "observed": (observed.get("observed")
                         if isinstance(observed.get("observed"), str)
                         else None),
            "extension_measured": payload.get("focal_extension_measured"),
            "severities_measured": measured,
            "extension_in_the_curve": [q for q in C.FOCAL_EXTENSION
                                       if q in measured],
            "m_star": payload.get("m_star"),
            "expected": "§7.2's {15, 16} are measured, which they never were "
                        "before A3 restored the caller and A4 made the branch "
                        "runnable"}


def scenario_focal_range_exhausted(root: Path) -> dict[str, Any]:
    """4. The extension is measured and still nothing is eligible."""
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE1)
    tree, ctx = prefix.branch(root / "branch")
    rungs = SL.screen_rungs()
    SL.RATE_OVERRIDES.update(
        {f"B:{q}": 0.30 for q in tuple(C.FOCAL_GRID) + tuple(C.FOCAL_EXTENSION)})
    try:
        observed = _terminal(lambda: _gate2(tree, ctx, rungs))
    finally:
        SL.clear_overrides()
    return {"branch": "§12.3's exhausted focal range", **observed,
            "expected": "FOCAL_RANGE_EXHAUSTED"}


def scenario_grid_resolution_insufficient(root: Path) -> dict[str, Any]:
    """4b. Two adjacent registered severities on opposite sides of the band.

    A different fact from an exhausted range, registered as its own status,
    and no production caller could reach it.
    """
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE1)
    tree, ctx = prefix.branch(root / "branch")
    rungs = SL.screen_rungs()
    grid = list(C.FOCAL_GRID) + list(C.FOCAL_EXTENSION)
    half = len(grid) // 2
    SL.RATE_OVERRIDES.update({f"B:{q}": 0.99 for q in grid[:half]})
    SL.RATE_OVERRIDES.update({f"B:{q}": 0.01 for q in grid[half:]})
    try:
        observed = _terminal(lambda: _gate2(tree, ctx, rungs))
    finally:
        SL.clear_overrides()
    return {"branch": "§12.3's grid resolution", **observed,
            "expected": "GRID_RESOLUTION_INSUFFICIENT"}


def scenario_calibration_population(root: Path) -> dict[str, Any]:
    """5. Gate 2 measures §12.7's population and not §12.2's carried set."""
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE1)
    regime = prefix.payloads[C.STAGE_REGIME]
    tree, ctx = prefix.branch(root / "branch")
    payload = _gate2(tree, ctx, SL.screen_rungs())
    priority = regime["calibration_priority"]
    population = payload["calibration_population"]
    return {"branch": "§12.7's calibration population",
            "carried_by_the_screen": len(regime["carried_set"]),
            "tier12": len(priority["tier12"]),
            "tier3_measured": len(priority["tier3_measured"]),
            "tier3_dropped_for_budget":
                len(priority["tier3_dropped_for_budget"]),
            "n_measured": population["n_measured"],
            "consumed_calibration_priority":
                population["n_measured"] == (len(priority["tier12"])
                                             + len(priority["tier3_measured"])),
            "expected": "n_measured is the priority population, never the "
                        "carried set"}


def scenario_reserve_expansion(root: Path) -> dict[str, Any]:
    """6. §12.6's expansion runs and its rounds are on the record."""
    prefix = prefix_walk(root / "prefix", C.STAGE_REGIME)
    regime = prefix.payloads[C.STAGE_REGIME]
    expansion = regime.get("expansion") or {}
    return {"branch": "§12.6's candidate expansion",
            "rounds": len(expansion.get("rounds") or ()),
            "coverage_met": (expansion.get("coverage") or {}).get(
                "decisive_met"),
            "identification_statuses": regime["identification_statuses"],
            "expected": "the expansion is reachable and its verdict is on "
                        "the record"}


def scenario_reference_support_not_identified(root: Path) -> dict[str, Any]:
    """7. §13.15 unmet: D6's irreversible NOT_IDENTIFIED, not a repair."""
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE2_5)
    tree, ctx = prefix.branch(root / "branch")
    from dci1v6.protocol import identification
    from dci1v6.stages import support
    report = support.evaluate_support(
        model_key=SL.MODEL_KEY,
        structurally_eligible_tier12_families=["MK1"],
        qualified_families=["MK1"],
        selection={"core_references": [], "identification_statuses": []},
        near_form_available=False, class_available=False,
        spectrum_identified=False)
    blocked = set(report["not_identified_members"])
    return {"branch": "§13.15 unmet, §34 D6",
            "support_met": report["support_met"],
            "disposition": report["disposition"],
            "admitted_arms": report["admitted_arms"],
            "n_not_identified": len(blocked),
            "delta_r_blocked": "Delta_R" in blocked,
            "d_b_from_a_still_identified":
                "D(B<-A)" in identification.UNAFFECTED_ESTIMANDS,
            "irreversible": bool(report["non_identification"]),
            "expected": "core and spectrum arms dropped, Delta_R "
                        "NOT_IDENTIFIED, D(B<-A) still identified"}


def scenario_composed_headroom_failure(root: Path) -> dict[str, Any]:
    """8. §13.14: a composed cell outside the band ends the replication."""
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE3C)
    tree, ctx = prefix.branch(root / "branch")
    designed = SL.screen_rungs() + SL._bound_constraints(tree)
    for constraint in designed:
        SL.COMPOSED_OVERRIDES[constraint.label] = 0.01
    try:
        observed = _terminal(lambda: gates_run.run_gate4(
            tree, producing_commit=ctx["commit"],
            environment_digest="scenario", bank=ctx["bank"],
            generate=SL._scripted_for(designed)))
    finally:
        SL.clear_overrides()
    return {"branch": "§13.14's composed-headroom validation", **observed,
            "expected": "COMPOSED_HEADROOM_FAILURE"}


def scenario_near_form_unavailable(root: Path) -> dict[str, Any]:
    """9. Without the near-form arm the strong L3c is unreachable (D18)."""
    from dci1v6.analysis import claims
    # §34 D18: the precondition for `strong` is that the arm RAN and produced
    # an interval, not that the interval reached a classification --- letting
    # a secondary quantity's precision decide a primary conclusion is what
    # D18 was closed to prevent. So the arm-present case supplies an interval
    # and deliberately an unclassified one.
    strong = claims.l3c_disposition(
        near_form_available=True,
        delta_near=claims.Interval("Delta_near", 0.04, -0.02, 0.10))
    without = claims.l3c_disposition(near_form_available=False,
                                     delta_near=None)
    interval = claims.Interval("Delta_R", 0.02, -0.01, 0.05)
    statements = claims.emit_l3(
        configuration=C.OUTCOME_FIRST, cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS, delta_r=interval,
        delta_difficulty=claims.Interval("delta_difficulty", 0.0, -0.02, 0.02),
        xi=claims.Interval("Xi", 0.0, -0.02, 0.02),
        support={"met": True}, references_identified=True,
        near_form_available=False)
    l3c = [s for s in statements if s.get("claim_level") == "L3c"]
    with_arm = claims.emit_l3(
        configuration=C.OUTCOME_FIRST, cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS, delta_r=interval,
        delta_difficulty=claims.Interval("delta_difficulty", 0.0, -0.02, 0.02),
        xi=claims.Interval("Xi", 0.0, -0.02, 0.02),
        support={"met": True}, references_identified=True,
        delta_near=claims.Interval("Delta_near", 0.04, -0.02, 0.10),
        near_form_available=True)
    return {"branch": "§34 D18's L3c scope",
            "with_arm_scope": strong["scope"],
            "without_arm_scope": without["scope"],
            "emitted_l3c_scope": [s.get("l3c_scope") for s in l3c],
            "emitted_l3c_scope_with_arm": [
                s.get("l3c_scope") for s in with_arm
                if s.get("claim_level") == "L3c"],
            "expected": "same_form_only without the arm; the strong "
                        "conclusion is unreachable"}


def scenario_broad_class_unavailable(root: Path) -> dict[str, Any]:
    """10. The class arm's absence is a named status, not a missing row."""
    from dci1v6.stages import support
    report = support.evaluate_support(
        model_key=SL.MODEL_KEY,
        structurally_eligible_tier12_families=["MK1", "MK2", "MK3", "MK4",
                                               "MK5", "MK6", "MK7", "MK8"],
        qualified_families=["MK1", "MK2", "MK3", "MK4", "MK5"],
        selection={"core_references": [
            {"structural_tier": 1, "feature_group": "marker_thus",
             "family": "MK1"},
            {"structural_tier": 1, "feature_group": "marker_hence",
             "family": "MK2"},
            {"structural_tier": 2, "feature_group": "semicolon",
             "family": "XC1"}], "identification_statuses": []},
        near_form_available=True, class_available=False,
        spectrum_identified=True)
    return {"branch": "§13.10's broad-class arm",
            "statuses": report["identification_statuses"],
            "admitted_arms": report["admitted_arms"],
            "expected": "CLASS_ARM_NOT_AVAILABLE is recorded and the arm is "
                        "not admitted"}


def scenario_a2_spectrum_fit(root: Path) -> dict[str, Any]:
    """11. §11.8's secondary under U2's adopted A2, and F8's members."""
    from dci1v6.analysis import spectrum
    points = []
    for index, family in enumerate(("F_a", "F_b", "F_c")):
        for offset in (-1, 0, 1):
            slot = f"R{index + 1}{'-' if offset < 0 else '+' if offset else ''}"
            difficulty = 0.5 + 0.1 * offset + 0.05 * index
            points.append(spectrum.SpectrumPoint(
                slot=slot, family=family, difficulty=difficulty,
                loss=0.10 + 0.30 * difficulty + 0.02 * index))
    for k in (1, 2, 3):
        points.append(spectrum.SpectrumPoint(
            slot=f"N{k}", family="F_near", difficulty=0.45 + 0.05 * k,
            loss=0.10 + 0.30 * (0.45 + 0.05 * k) + 0.08))
    tiers = {p.slot: (2 if p.slot.startswith("N") else 1) for p in points}
    fit = spectrum.assert_adopted_formulation(
        spectrum.fit_with_tier_indicator(points, tiers),
        where="scenario_a2_spectrum_fit")
    return {"branch": "§11.8 / U2 = A2, family F8",
            "formulation": fit.formulation, "adopted": fit.adopted,
            "n_points": fit.n_points, "beta": fit.slope,
            "gamma_tier": fit.gamma, "n_intercepts": len(fit.intercepts),
            "expected": "twelve points, three core intercepts, beta and "
                        "gamma recovered under A2"}


def scenario_unmask_is_one_shot(root: Path) -> dict[str, Any]:
    """12. The second unmask is refused, by the write-once stage record."""
    prefix = prefix_walk(root / "prefix", C.STAGE_UNMASKING)
    tree, _ctx = prefix.branch(root / "branch")
    from dci1v6.run import analysis_run
    observed = _terminal(lambda: analysis_run.run_unmasking(
        tree, producing_commit=prefix.state["commit"],
        environment_digest="scenario"))
    return {"branch": "§20's one-shot unmask", **observed,
            "expected": "the second invocation is refused"}


#: §17.6's coordinate-agreement fixture. Three families whose CHANCE rates
#: differ, and a loss that is linear in raw solo compliance: iota reorders
#: the points and rescales the spread, so the two registered coordinates fit
#: different lines and predict A differently. The jitter on p(B | A+B) is
#: what gives both intervals a realised half-width inside §16.2's precision
#: precondition; without it the intervals collapse and both readings are L3d.
_COORDINATE_PLAN = {"F_a": (0.10, (0.30, 0.50, 0.70)),
                    "F_b": (0.30, (0.35, 0.55, 0.75)),
                    "F_c": (0.55, (0.60, 0.66, 0.80))}


def _coordinate_input(n_blocks: int = 12):
    from dci1v6.analysis import spectrum

    family_of, companion_solo, companion_chance, b_with = {}, {}, {}, {}
    for family, (chance, solos) in _COORDINATE_PLAN.items():
        for index, solo in enumerate(solos):
            slot = f"{family}_{index}"
            family_of[slot] = family
            companion_solo[slot] = [solo] * n_blocks
            companion_chance[slot] = [chance] * n_blocks
            b_with[slot] = [0.80 - (0.05 + 0.40 * solo)] * n_blocks
    base = 0.80 - (0.05 + 0.40 * 0.55) - 0.06
    b_with["A"] = [base - (-1) ** i * 0.045 * (1 + (i % 3)) / 2
                   for i in range(n_blocks)]
    return spectrum.SpectrumInput(
        blocks=tuple(f"b{i}" for i in range(n_blocks)), family_of=family_of,
        b_solo=[0.80] * n_blocks, b_with=b_with,
        companion_solo=companion_solo, companion_chance=companion_chance,
        a_solo=[0.55] * n_blocks, a_chance=[0.05] * n_blocks)


def scenario_coordinate_dependent(root: Path) -> dict[str, Any]:
    """14. §17.6's coordinate agreement and §34 D14, on a real disagreement.

    The registered coordinate reads L3e and the raw-coordinate replication
    reads L3d. §17.6 registers exactly this: the statement carries
    `DIFFICULTY_COORDINATE_DEPENDENT`, both readings are reported, **the
    registered coordinate decides which classification is emitted** and the
    secondary decides only whether the status rides on it. So what this
    asserts is not only that the status appears --- it is that the emitted
    level is still the primary's.
    """
    from dci1v6.analysis import claims, spectrum
    from dci1v6.run import analysis_run

    data = _coordinate_input()
    readings = {}
    for coordinate in (C.DIFFICULTY_COORDINATE,
                       C.SECONDARY_DIFFICULTY_COORDINATE):
        # 300 resamples, not §14.1's 10,000: this scenario exists to drive
        # §17.6's comparison, and the audit runs it under a profiler that
        # costs about two orders of magnitude per call. The classification is
        # stable from 200 upward on this fixture.
        boot = spectrum.bootstrap_spectrum(data, resamples=300, seed=7,
                                           coordinate=coordinate)
        low, high = boot["ci95_percentile"]
        readings[coordinate] = (
            claims.Interval("delta_difficulty", boot["estimate"], low, high),
            boot["support"])
    primary, primary_support = readings[C.DIFFICULTY_COORDINATE]
    secondary, secondary_support = readings[C.SECONDARY_DIFFICULTY_COORDINATE]

    # The production reader, on the shape the stripped record carries.
    result = {"raw_coordinate_secondary": {"configurations": {"outcome_first": {
        "status": "IDENTIFIED", "point": secondary.estimate,
        "marginal_ci95": [secondary.lower, secondary.upper],
        "support": dict(secondary_support)}}}}
    read = analysis_run._raw_coordinate_reading(result, "outcome_first")
    agreement = claims.coordinate_agreement(
        delta_difficulty=primary, support=primary_support, **read)

    statements = claims.emit_l3(
        configuration="outcome_first", cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS,
        delta_r=claims.Interval("Delta_R", 0.02, -0.01, 0.05),
        delta_difficulty=primary,
        xi=claims.Interval("Xi", 0.09, 0.04, 0.14),
        support=primary_support, references_identified=True,
        delta_near=claims.Interval("Delta_near", 0.02, -0.01, 0.05),
        coordinate_statuses=agreement["statuses"])
    emitted = [s for s in statements if s.get("emitted")]
    return {
        "branch": "§17.6's coordinate agreement, §34 D14",
        "primary_levels": agreement["primary_levels"],
        "secondary_levels": agreement["secondary_levels"],
        "agrees": agreement["agrees"],
        "statuses": agreement["statuses"],
        "emitted_levels": sorted(s["claim_level"] for s in emitted),
        "status_on_every_statement": all(
            "DIFFICULTY_COORDINATE_DEPENDENT" in s["identification_status"]
            for s in emitted),
        "expected": "primary L3e, raw L3d, DIFFICULTY_COORDINATE_DEPENDENT "
                    "on the emitted statement, and the emitted level is the "
                    "PRIMARY's",
    }


def scenario_coordinate_secondary_not_computable(root: Path
                                                 ) -> dict[str, Any]:
    """15. No raw replication is not a disagreement.

    §17.6 compares two classifications; with one, the status cannot be
    earned. The masked phase is the ordinary way this happens --- A's point
    is inside the permuted group on either coordinate --- and a rule that
    treated "absent" as "different" would attach a status to every masked
    replication.
    """
    from dci1v6.analysis import claims, spectrum
    from dci1v6.run import analysis_run

    data = _coordinate_input()
    boot = spectrum.bootstrap_spectrum(
        data, resamples=200, seed=7, coordinate=C.DIFFICULTY_COORDINATE)
    low, high = boot["ci95_percentile"]
    primary = claims.Interval("delta_difficulty", boot["estimate"], low, high)

    masked = analysis_run._raw_coordinate_secondary(
        {"outcome_first": data}, seed=7, resamples=200, post_unmask=False)
    read = analysis_run._raw_coordinate_reading(
        {"raw_coordinate_secondary": masked}, "outcome_first")
    agreement = claims.coordinate_agreement(
        delta_difficulty=primary, support=boot["support"], **read)
    return {
        "branch": "§17.6 with no secondary, §20",
        "masked_step_9": masked["step_9"],
        "masked_step_12": masked["step_12"],
        "compared": agreement["compared"],
        "statuses": agreement["statuses"],
        "expected": "the masked phase computes no raw replication and the "
                    "comparison records that rather than a disagreement",
    }


def scenario_probe_terminates_at_the_frozen_m_star(root: Path
                                                  ) -> dict[str, Any]:
    """16. §18 stage 8 refuses the frozen m\\*, and the replication stops.

    **This is v6's answer to v5's Gate-4 problem, in the form the researcher
    adopted on 2026-08-26**: composed headroom is measured two stages before
    Gate 4, and it decides *whether* the registered design is viable at the
    operating point §12.3 chose --- never *where* the estimand is measured.
    m\\* is frozen at ``GATE_2_FOCAL_CALIBRATION``, so a failure here is a
    terminal scientific outcome and not a search for a friendlier severity.

    The knob is a fixture composed rate for B **at m\\* alone**. Nothing here
    changes a band, a margin, a threshold or a rule. The scenario asserts two
    things the earlier reselection branch could not: that the stage raises,
    and that no record anywhere carries an operating point other than Gate
    2's.
    """
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE2_5)
    tree, ctx = prefix.branch(root / "branch")
    gate2 = prefix.payloads[C.STAGE_GATE2]
    m_in = int(gate2["m_star"])
    SL.COMPOSED_OVERRIDES[f"B:{m_in}"] = 0.99
    standins = list(SL.FIXTURE_STANDINS)
    try:
        observed = _terminal(lambda: gates_run.run_gate2_75(
            tree, producing_commit=ctx["commit"],
            environment_digest="scenario", bank=ctx["bank"],
            standins=SL.FIXTURE_STANDINS, block_limit=24,
            generate=SL._scripted_for(SL.screen_rungs() + standins)))
    finally:
        SL.clear_overrides()
    # No successor may exist: a terminal stage writes no PASS record, so
    # there is no operating point for a later stage to read.
    probe_record = tree.stage_record(C.STAGE_GATE2_75)
    return {
        "branch": "P3.6: the frozen m* has no composed headroom",
        **observed,
        "m_star_frozen_at_gate2": m_in,
        "gate2_5_order_head": int(
            prefix.payloads[C.STAGE_GATE2_5]["operating_point_order"][0]),
        "no_passing_probe_record": not probe_record.exists(),
        "expected": "COMPOSED_HEADROOM_UNREACHABLE, and m* never moves",
    }


def scenario_probe_passes_at_the_frozen_m_star(root: Path) -> dict[str, Any]:
    """17. The other side of the same rule: the probe passes, and every later
    stage runs at **Gate 2's** m\\*.

    The reselection scenario this replaces existed to drive the downstream
    path after m\\* moved. m\\* cannot move, so what needs driving is the
    invariant itself: ``effective_m_star`` refuses a probe record that
    disagrees with Gate 2, and this walks Gate 3A through the freeze checking
    every record's own operating point against the one §12.3 chose.
    """
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE2_5)
    tree, ctx = prefix.branch(root / "branch")
    gate2 = prefix.payloads[C.STAGE_GATE2]
    m_in = int(gate2["m_star"])
    standins = list(SL.FIXTURE_STANDINS)
    probe = gates_run.run_gate2_75(
        tree, producing_commit=ctx["commit"],
        environment_digest="scenario", bank=ctx["bank"],
        standins=SL.FIXTURE_STANDINS, block_limit=24,
        generate=SL._scripted_for(SL.screen_rungs() + standins)).payload
    for run in (gates_run.run_gate3a, gates_run.run_gate3b,
                gates_run.run_gate3c):
        run(tree, producing_commit=ctx["commit"],
            environment_digest="scenario")
    designed = SL.screen_rungs() + SL._bound_constraints(tree)
    gate4 = gates_run.run_gate4(
        tree, producing_commit=ctx["commit"],
        environment_digest="scenario", bank=ctx["bank"],
        generate=SL._scripted_for(designed)).payload
    prefreeze_run.run_prefreeze_audit_stage(
        tree, producing_commit=ctx["commit"],
        environment_digest="scenario", repo_root=ctx["repo_root"],
        bank=ctx["bank"])
    freeze = freeze_run.run_freeze(
        tree, producing_commit=ctx["commit"],
        environment_digest="scenario").payload
    gate3a = transitions.read_stage_record(tree, C.STAGE_GATE3A)
    gate3c = transitions.read_stage_record(tree, C.STAGE_GATE3C)
    # The consuming half of the invariant, driven against a tampered record.
    tampered = _terminal(lambda: gates_run.assert_probe_m_star_agrees(
        {"m_star": m_in + 1}, gate2_m_star=m_in))
    return {
        "branch": "P3.3: the frozen m* has composed headroom",
        "m_star_frozen_at_gate2": m_in,
        "probe_m_star_in": int(probe["m_star_in"]),
        "probe_m_star_out": int(probe["m_star"]),
        "reselected": bool(probe["reselected"]),
        "reselections_permitted":
            int(probe["disposition"]["reselections_permitted"]),
        "severities_probed": list(probe["disposition"]["probed_severities"]),
        "admissible_severities": list(probe["admissible_severities"]),
        # Every later stage's own record of the operating point it ran at.
        "gate3a_m_star": int(gate3a["m_star"]),
        "gate3a_qualified_at": int(gate3a["qualified_at_m_star"]),
        "gate3c_support_met": bool(gate3c["support"]["support_met"]),
        "gate4_m_star": int(gate4["slot_map"]["B"][1]),
        "freeze_m_star": int(freeze["m_star"]),
        "freeze_slot_map_b": int(freeze["slot_map"]["B"][1]),
        "a_disagreeing_probe_record_is_refused": tampered,
        "expected": "no reselection, one probed severity, and Gate 3A, Gate "
                    "4 and the freeze all at Gate 2's m*",
    }


SCENARIOS: dict[str, Callable[[Path], dict[str, Any]]] = {
    "normal_full_path": scenario_normal_full_path,
    "no_viable_regime": scenario_no_viable_regime,
    "focal_extension_required": scenario_focal_extension_required,
    "focal_range_exhausted": scenario_focal_range_exhausted,
    "grid_resolution_insufficient": scenario_grid_resolution_insufficient,
    "calibration_population": scenario_calibration_population,
    "reserve_expansion": scenario_reserve_expansion,
    "reference_support_not_identified":
        scenario_reference_support_not_identified,
    "composed_headroom_failure": scenario_composed_headroom_failure,
    "near_form_unavailable": scenario_near_form_unavailable,
    "broad_class_unavailable": scenario_broad_class_unavailable,
    "a2_spectrum_fit": scenario_a2_spectrum_fit,
    "unmask_is_one_shot": scenario_unmask_is_one_shot,
    "coordinate_dependent": scenario_coordinate_dependent,
    "coordinate_secondary_not_computable":
        scenario_coordinate_secondary_not_computable,
    "probe_terminates_at_the_frozen_m_star":
        scenario_probe_terminates_at_the_frozen_m_star,
    "probe_passes_at_the_frozen_m_star":
        scenario_probe_passes_at_the_frozen_m_star,
}


def run_scenario(name: str, root: Path | None = None) -> dict[str, Any]:
    here = Path(root or tempfile.mkdtemp(prefix=f"scenario-{name}-"))
    here.mkdir(parents=True, exist_ok=True)
    return {"scenario": name, **SCENARIOS[name](here)}


def run_all(root: Path | None = None,
            only: tuple[str, ...] = ()) -> dict[str, Any]:
    base = Path(root or tempfile.mkdtemp(prefix="scenarios-"))
    out: dict[str, Any] = {}
    for name in SCENARIOS:
        if only and name not in only:
            continue
        out[name] = run_scenario(name, base / name)
    return out
