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

import functools
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v7.engine.context import synthetic_context
from dci1v7.engine.paths import model_tree
from dci1v7.protocol import constants as C
from dci1v7.engine import transitions
from dci1v7.run import (field_access, freeze_run, gates_run,
                        prefreeze_run)
from dci1v7.run.lifecycle import TerminalStatus

from tests_v7 import synthetic_lifecycle as SL

__all__ = ["SCENARIOS", "run_scenario", "run_all", "prefix_walk",
           "run_scenarios_parallel", "instrument_calls"]


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
    from dci1v7.verifiers.constraints import Constraint

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


# ------------------------------------------- v7 A6/A7/A8: D6 end to end

#: Cached walks for the two non-identified branches, keyed by branch. Two
#: scenarios read each (the end-to-end one and the audit-conditionality one),
#: and a walk to the pre-freeze audit with overrides is signed evidence that
#: copying does not change.
_D6_PREFIXES: dict[str, Prefix] = {}


def _tier12_labels() -> list[str]:
    from dci1v7.verifiers.constraints import FAMILIES
    return [f"{kind}:{q}" for kind in SL.SCREEN_FAMILIES
            if FAMILIES[kind].structural_tier in (1, 2)
            for q in FAMILIES[kind].ladder]


def _flattened_ladders(iota_a: float, *, half_gap: float) -> dict[str, float]:
    """Every Tier-1/2 rung within ``half_gap`` of ``iota_a``, alternating
    sides by severity: each family straddles iota_A (C1, C2), every rung is
    inside §13.8's caliper (C3), and no family's span reaches 0.40 (C4)."""
    out: dict[str, float] = {}
    for label in _tier12_labels():
        q = int(label.rpartition(":")[2])
        out[label] = iota_a + (half_gap if q % 2 == 0 else -half_gap)
    return out


#: The eight rung offsets of the full-design fixture, by ladder position.
#: Two rungs each side INSIDE §13.8's 0.10 caliper, because §13.7
#: condition 1 requires every V_stab candidate --- spectrum rungs included
#: --- to be independently admissible under V_diff on each split, so a
#: §13.12 rung is selectable only inside the caliper whatever its +/-0.20
#: target says (the real gemma-3n-e2b-it triples sat within 0.08 of iota_A
#: for the same reason; see RESEARCH_STATE §4an). The outer rungs supply
#: C4's 0.40 span on the calibrated basis and nothing else.
_SPREAD_OFFSETS: tuple[float, ...] = (-0.28, -0.20, -0.06, -0.02,
                                      0.02, 0.06, 0.20, 0.28)


def _spread_ladders(iota_a: float) -> dict[str, float]:
    """Every Tier-1/2 family's ladder spread across iota_A by
    ``_SPREAD_OFFSETS`` and kept inside the solo band: each family
    straddles iota_A with a span above 0.40 (C1-C6 on the calibrated basis),
    §13.12 finds a qualifying rung strictly below and above iota_A inside
    the caliper, and §13.8 holds a matched rung --- the full 56-cell
    design, which the ordinary fixture never reaches because its default
    ladders exhaust §13.12."""
    out: dict[str, float] = {}
    for label in _tier12_labels():
        q = int(label.rpartition(":")[2])
        offset = _SPREAD_OFFSETS[min(q, len(_SPREAD_OFFSETS)) - 1]
        out[label] = min(0.88, max(0.12, iota_a + offset))
    return out


def _d6_overrides(branch: str, iota_a: float) -> dict[str, float]:
    if branch == "core_lost":
        # Every Tier-1/2 rung far below iota_A: C1 and C3 fail on the
        # calibrated basis and §13.8 finds no companion inside its caliper,
        # so §13.15 is unmet on the counts too --- the v5 shape.
        return {label: 0.30 for label in _tier12_labels()}
    if branch == "spectrum_lost":
        # Every Tier-1/2 family straddles iota_A tightly: matched companions
        # exist and qualify, and no ladder spans 0.40 --- the v7 shape.
        return _flattened_ladders(iota_a, half_gap=0.04)
    if branch == "spectrum_found":
        return _spread_ladders(iota_a)
    raise ValueError(branch)


def _d6_prefix(root: Path, branch: str) -> Prefix:
    """A signed tree driven through PREFREEZE_AUDIT under one of two override
    sets, branched from the shared GATE_1 prefix so the regime screen ---
    where §12.6's certificate passed on every real v7 replication --- is the
    ordinary one and only the calibrated basis differs."""
    if branch in _D6_PREFIXES:
        return _D6_PREFIXES[branch]
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE1)
    into = root / f"{branch}-tree"
    tree, ctx = prefix.branch(into)
    iota_a = float(prefix.payloads[C.STAGE_REGIME]["iota_a_prescreen"])
    SL.RATE_OVERRIDES.update(_d6_overrides(branch, iota_a))
    try:
        payloads = SL.continue_walk(
            tree, commit=ctx["commit"], the_bank=ctx["bank"],
            repo_root=ctx["repo_root"], after=C.STAGE_GATE1,
            rungs=SL.screen_rungs(), stop_after=C.STAGE_PREFREEZE_AUDIT)
    finally:
        SL.clear_overrides()
    state = {**prefix.state, "payloads": {**prefix.payloads, **payloads},
             "overrides": branch}
    _D6_PREFIXES[branch] = Prefix(into, state)
    return _D6_PREFIXES[branch]


def _d6_finish(root: Path, branch: str) -> dict[str, Any]:
    """Freeze, generate, mask, unmask, analyse and report on a branch of the
    cached pre-freeze tree, under the same overrides."""
    prefix = _d6_prefix(root, branch)
    tree, ctx = prefix.branch(root / f"{branch}-finish")
    iota_a = float(prefix.payloads[C.STAGE_REGIME]["iota_a_prescreen"])
    SL.RATE_OVERRIDES.update(_d6_overrides(branch, iota_a))
    try:
        later = SL.continue_walk(
            tree, commit=ctx["commit"], the_bank=ctx["bank"],
            repo_root=ctx["repo_root"], after=C.STAGE_PREFREEZE_AUDIT,
            rungs=SL.screen_rungs())
    finally:
        SL.clear_overrides()
    return {"tree": tree, "payloads": {**prefix.payloads, **later}}


def _estimand_status(unmasked: Mapping[str, Any], member: str) -> str | None:
    buckets = (unmasked.get("estimands") or {}).get("configurations") or {}
    first = buckets.get(C.OUTCOME_FIRST) or {}
    entry = first.get(member) or {}
    return entry.get("status")


def _estimand_reason(unmasked: Mapping[str, Any], member: str) -> str | None:
    buckets = (unmasked.get("estimands") or {}).get("configurations") or {}
    entry = (buckets.get(C.OUTCOME_FIRST) or {}).get(member) or {}
    return entry.get("reason")


def _tamper_refused(block: Mapping[str, Any] | None, member: str) -> bool:
    from dci1v7.protocol import identification
    try:
        identification.assert_not_rehabilitated(
            {"estimands": {member: {"estimate": 0.1}}}, gate3c=block,
            where="scenario tamper")
    except ProtocolError:
        return True
    return False


def scenario_reference_support_not_identified(root: Path) -> dict[str, Any]:
    """7. §13.15 unmet: D6's irreversible NOT_IDENTIFIED, END TO END.

    Until 2026-08-28 this scenario built a Gate-3C report by hand and stopped
    there, so the pre-freeze check that ended seven real replications on
    exactly this branch was never walked. Now the production path is driven
    from a signed GATE_1 prefix, under a calibration in which no Tier-1/2
    companion sits within §13.8's caliper, through Gate 3C
    (`REFERENCE_SUPPORT_NOT_IDENTIFIED`, core and spectrum dropped), Gate 4,
    the pre-freeze audit (PASS: the record is consistent), the freeze,
    confirmatory generation, both analyses and the final report --- and the
    base-arm estimands come out IDENTIFIED while every reference-dependent
    member stays NOT_IDENTIFIED and cannot be offered by a later record.
    """
    from dci1v7.protocol import identification
    finished = _d6_finish(root, "core_lost")
    p = finished["payloads"]
    gate3c, audit = p[C.STAGE_GATE3C], p[C.STAGE_PREFREEZE_AUDIT]
    freeze, unmasked = p[C.STAGE_GATE5], p[C.STAGE_UNMASKED_ANALYSIS]
    report = p[C.STAGE_FINAL_REPORT]
    checks = {c["check"]: c["verdict"] for c in audit["artifact_checks"]}
    blocked = set(gate3c["not_identified_members"])
    return {"branch": "§13.15 unmet, §34 D6, end to end",
            "gate3c_statuses": gate3c["identification_statuses"],
            "support_met": gate3c["support"]["support_met"],
            "disposition": gate3c["support"]["disposition"],
            "admitted_arms": gate3c["admitted_arms"],
            "n_not_identified": len(blocked),
            "delta_r_blocked": "Delta_R" in blocked,
            "irreversible": bool(gate3c["non_identification"]["irreversible"]),
            "prefreeze_outcome": audit["outcome"],
            "prefreeze_support_met_required": audit["support_met_required"],
            "prefreeze_checks": {k: checks[k] for k in (
                "support_recorded", "d6_disposition_registered",
                "arms_match_identification", "no_rehabilitation_path",
                "freeze_fields_explained", "selected_references_valid",
                "calibration_stability_satisfied")},
            "freeze_admitted_arms": freeze["admitted_arms"],
            "freeze_block_status": (freeze["non_identification"] or {}).get(
                "status"),
            "confirmatory_rows": p[C.STAGE_CONFIRMATORY]["n_rows"],
            "d_b_from_a": _estimand_status(unmasked, "D(B<-A)"),
            "lambda": _estimand_status(unmasked, "Lambda"),
            "delta_r": _estimand_status(unmasked, "Delta_R"),
            "delta_r_reason": _estimand_reason(unmasked, "Delta_R"),
            "final_report_outcome": report["outcome"],
            "final_report_rows": report.get("n_result_rows"),
            "tamper_delta_r_refused": _tamper_refused(
                freeze["non_identification"], "Delta_R"),
            "still_identified_includes_base_arm": set(
                identification.BASE_ARM_ESTIMANDS) <= set(
                gate3c["non_identification"]["still_identified_members"]),
            "expected": "core and spectrum arms dropped, Delta_R "
                        "NOT_IDENTIFIED irreversibly, D(B<-A) IDENTIFIED, "
                        "and the replication reaches FINAL_REPORT"}


def scenario_c4_lost_core_kept(root: Path) -> dict[str, Any]:
    """7b. v7 A7: C4 lost on the calibrated basis with every core condition
    met keeps the core arm and Delta_R, drops the spectrum arm and marks the
    spectrum-dependent members NOT_IDENTIFIED irreversibly --- end to end.

    This is the shape of all four real v7 replications.
    """
    from dci1v7.protocol import identification
    finished = _d6_finish(root, "spectrum_lost")
    p = finished["payloads"]
    gate3a, gate3c = p[C.STAGE_GATE3A], p[C.STAGE_GATE3C]
    audit, freeze = p[C.STAGE_PREFREEZE_AUDIT], p[C.STAGE_GATE5]
    unmasked, report = p[C.STAGE_UNMASKED_ANALYSIS], p[C.STAGE_FINAL_REPORT]
    checks = {c["check"]: c["verdict"] for c in audit["artifact_checks"]}
    coverage = gate3a["coverage_at_calibrated_iota_a"]
    blocked = set(gate3c["not_identified_members"])
    return {"branch": "§12.6 C4 lost on the calibrated basis, core kept (A7)",
            "calibrated_conditions": coverage["conditions"],
            "calibrated_core_met": coverage["core_met"],
            "calibrated_spectrum_met": coverage["spectrum_met"],
            "calibrated_core_failures": gate3a["calibrated_coverage_failures"],
            "calibrated_spectrum_failures":
                gate3a["calibrated_spectrum_failures"],
            "gate3c_statuses": gate3c["identification_statuses"],
            "support_met": gate3c["support"]["support_met"],
            "spectrum_met": gate3c["support"]["spectrum_met"],
            "admitted_arms": gate3c["admitted_arms"],
            "block_status": (gate3c["non_identification"] or {}).get("status"),
            "n_not_identified": len(blocked),
            "blocked_is_the_spectrum_set":
                blocked == set(identification.SPECTRUM_ESTIMANDS),
            "delta_r_blocked": "Delta_R" in blocked,
            "prefreeze_outcome": audit["outcome"],
            "prefreeze_checks": {k: checks[k] for k in (
                "support_recorded", "d6_disposition_registered",
                "arms_match_identification", "no_rehabilitation_path",
                "freeze_fields_explained", "selected_references_valid",
                "calibration_stability_satisfied")},
            "freeze_admitted_arms": freeze["admitted_arms"],
            "delta_r": _estimand_status(unmasked, "Delta_R"),
            "delta_difficulty": _estimand_status(unmasked,
                                                 "delta_difficulty"),
            "delta_difficulty_reason": _estimand_reason(
                unmasked, "delta_difficulty"),
            "d_b_from_r1_minus": _estimand_status(unmasked, "D(B<-R1-)"),
            "final_report_outcome": report["outcome"],
            "tamper_delta_difficulty_refused": _tamper_refused(
                freeze["non_identification"], "delta_difficulty"),
            "tamper_delta_r_allowed": not _tamper_refused(
                freeze["non_identification"], "Delta_R"),
            "expected": "core retained, spectrum dropped, Delta_R IDENTIFIED, "
                        "delta_difficulty NOT_IDENTIFIED "
                        "(DIFFICULTY_SUPPORT_NOT_IDENTIFIED), FINAL_REPORT "
                        "reached"}


def scenario_full_support_unchanged(root: Path) -> dict[str, Any]:
    """7c. Both supports met: the full 56-cell design, end to end, and the
    audit's support checks all PASS with nothing NOT_APPLICABLE.

    The ordinary fixture never reaches this --- its default ladders exhaust
    §13.12 and the walk runs base + core + class --- so the branch spreads
    every Tier-1/2 ladder across iota_A and drives the production runners
    from Gate 2 to the final report with every arm admitted. A6 and A7
    change nothing on this path, which is what "unchanged" means here.
    """
    finished = _d6_finish(root, "spectrum_found")
    p = finished["payloads"]
    gate3a, gate3c = p[C.STAGE_GATE3A], p[C.STAGE_GATE3C]
    audit, freeze = p[C.STAGE_PREFREEZE_AUDIT], p[C.STAGE_GATE5]
    unmasked, report = p[C.STAGE_UNMASKED_ANALYSIS], p[C.STAGE_FINAL_REPORT]
    coverage = gate3a["coverage_at_calibrated_iota_a"]
    return {"branch": "every support requirement met (the full design)",
            "calibrated_core_met": coverage["core_met"],
            "calibrated_spectrum_met": coverage["spectrum_met"],
            "support_met": gate3c["support"]["support_met"],
            "spectrum_met": gate3c["support"]["spectrum_met"],
            "admitted_arms": gate3c["admitted_arms"],
            "derived_cell_count": gate3c["derived_cell_count"],
            "non_identification": gate3c["non_identification"],
            "gate3c_statuses": gate3c["identification_statuses"],
            "prefreeze_outcome": audit["outcome"],
            "n_not_applicable": audit["n_artifact_not_applicable"],
            "freeze_admitted_arms": freeze["admitted_arms"],
            "confirmatory_rows": p[C.STAGE_CONFIRMATORY]["n_rows"],
            "delta_r": _estimand_status(unmasked, "Delta_R"),
            "delta_difficulty": _estimand_status(unmasked,
                                                 "delta_difficulty"),
            "delta_difficulty_reason": _estimand_reason(
                unmasked, "delta_difficulty"),
            "d_b_from_r1_minus": _estimand_status(unmasked, "D(B<-R1-)"),
            "final_report_outcome": report["outcome"],
            "expected": "all five arms, 56 cells, no block, PASS with no "
                        "NOT_APPLICABLE check, Delta_R and delta_difficulty "
                        "IDENTIFIED, FINAL_REPORT reached"}


def scenario_base_arm_is_unconditional(root: Path) -> dict[str, Any]:
    """7d. A8: no Gate-3 verdict removes the base arm, and there is no
    registered terminal status for 'no useful estimand remains' --- the
    exits before confirmatory generation are §28.3's and nothing else."""
    from dci1v7.design import cells
    from dci1v7.protocol import identification
    from dci1v7.stages import support
    report = support.evaluate_support(
        model_key=SL.MODEL_KEY,
        structurally_eligible_tier12_families=["MK1"],
        qualified_families=["MK1"],
        selection={"core_references": [], "identification_statuses": []},
        near_form_available=False, class_available=False,
        spectrum_identified=False)
    return {"branch": "§8.1's unconditional base arm and §28.3's exits",
            "arms_when_everything_else_is_lost": report["admitted_arms"],
            "derived_cell_count": report["derived_cell_count"],
            "normalise_arms_of_nothing": list(cells.normalise_arms([])),
            "base_arm_estimands_still_identified": all(
                m in report["non_identification"]["still_identified_members"]
                for m in identification.BASE_ARM_ESTIMANDS),
            "terminal_statuses_about_support": [
                s for s in C.TERMINAL_STATUSES if "SUPPORT" in s],
            "terminal_statuses_in_force": list(C.TERMINAL_STATUSES),
            "expected": "base arm only, 5 cells, D(B<-A)/D(A<-B)/Lambda/"
                        "Ord_* identified, and no terminal status for a lost "
                        "arm"}


def scenario_unsupported_estimands_cannot_reappear(root: Path
                                                   ) -> dict[str, Any]:
    """7e. The two non-identification blocks refuse a later estimate for a
    member they name, and admit one for a member they do not."""
    from dci1v7.protocol import identification
    core = identification.non_identification(
        model_key=SL.MODEL_KEY, support_met=False, failures=["§13.15"])
    spectrum = identification.non_identification(
        model_key=SL.MODEL_KEY, support_met=True, spectrum_identified=False,
        spectrum_failures=["C4"])
    return {"branch": "§34 D6's irreversibility, both blocks",
            "core_block_refuses_delta_r": _tamper_refused(core, "Delta_R"),
            "core_block_refuses_delta_difficulty": _tamper_refused(
                core, "delta_difficulty"),
            "core_block_admits_d_b_from_a": not _tamper_refused(
                core, "D(B<-A)"),
            "spectrum_block_refuses_delta_difficulty": _tamper_refused(
                spectrum, "delta_difficulty"),
            "spectrum_block_refuses_spectrum_loss": _tamper_refused(
                spectrum, "D(B<-R2+)"),
            "spectrum_block_admits_delta_r": not _tamper_refused(
                spectrum, "Delta_R"),
            "rehabilitation_paths_refused": sorted(
                identification.REHABILITATION_PATHS),
            "expected": "every named member refused, every other admitted"}


def scenario_reference_checks_conditional(root: Path) -> dict[str, Any]:
    """7f. A6: the reference-specific pre-freeze checks are NOT_APPLICABLE
    when the core arm is absent and applicable when it is present."""
    core_lost = _d6_prefix(root, "core_lost").payloads[C.STAGE_PREFREEZE_AUDIT]
    spectrum_lost = _d6_prefix(root, "spectrum_lost").payloads[
        C.STAGE_PREFREEZE_AUDIT]

    def verdicts(audit):
        return {c["check"]: (c["verdict"], (c.get("detail") or {}).get(
            "explained_by") if isinstance(c.get("detail"), Mapping) else None)
            for c in audit["artifact_checks"]
            if c["check"] in ("selected_references_valid",
                              "calibration_stability_satisfied")}
    return {"branch": "A6: reference-specific checks follow the core arm",
            "without_core_arm": verdicts(core_lost),
            "without_core_arm_outcome": core_lost["outcome"],
            "without_core_arm_not_applicable":
                core_lost["n_artifact_not_applicable"],
            "with_core_arm": verdicts(spectrum_lost),
            "with_core_arm_outcome": spectrum_lost["outcome"],
            "with_core_arm_not_applicable":
                spectrum_lost["n_artifact_not_applicable"],
            "expected": "NOT_APPLICABLE naming REFERENCE_SUPPORT_NOT_"
                        "IDENTIFIED without the core arm; PASS with it; both "
                        "audits PASS"}


def scenario_gate4_records_a_boundary(root: Path) -> dict[str, Any]:
    """8. v7 §13.14: a composed cell at the floor is RECORDED, and the
    replication continues to the pre-freeze audit.

    Under v5/v6 this branch ended the replication
    ``COMPOSED_HEADROOM_FAILURE``. The same fixture now drives the production
    Gate 4 to a PASS whose projection names what the floor does to every
    contrast that reads that cell.
    """
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE3C)
    tree, ctx = prefix.branch(root / "branch")
    designed = SL.screen_rungs() + SL._bound_constraints(tree)
    for constraint in designed:
        SL.COMPOSED_OVERRIDES[constraint.label] = 0.0
    try:
        gate4 = gates_run.run_gate4(
            tree, producing_commit=ctx["commit"],
            environment_digest="scenario", bank=ctx["bank"],
            resamples=60, generate=SL._scripted_for(designed)).payload
    finally:
        SL.clear_overrides()
    audit = prefreeze_run.run_prefreeze_audit_stage(
        tree, producing_commit=ctx["commit"],
        environment_digest="scenario", repo_root=ctx["repo_root"],
        bank=ctx["bank"]).payload
    return {"branch": "v7 §13.14: a composed cell at a boundary",
            "outcome": gate4["outcome"],
            "terminates_nothing": gate4["terminates_nothing"],
            "cells_near_a_boundary": len(gate4["cells_near_a_boundary"]),
            "contrast_statuses": gate4["contrast_statuses"],
            "any_structural_zero": gate4["any_structural_zero"],
            "prefreeze_outcome": audit["outcome"],
            "expected": "PASS with the boundary statuses recorded, and the "
                        "pre-freeze audit reached"}


def scenario_near_form_unavailable(root: Path) -> dict[str, Any]:
    """9. Without the near-form arm the strong L3c is unreachable (D18)."""
    from dci1v7.analysis import claims
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
    from dci1v7.stages import support
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
    from dci1v7.analysis import spectrum
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
    from dci1v7.run import analysis_run
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
    from dci1v7.analysis import spectrum

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
    from dci1v7.analysis import claims, spectrum
    from dci1v7.run import analysis_run

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
    from dci1v7.analysis import claims, spectrum
    from dci1v7.run import analysis_run

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


def scenario_probe_records_a_ceiling_on_the_treated_arm(root: Path
                                                       ) -> dict[str, Any]:
    """16. v7 A1: B delivered under A at the ceiling is RECORDED at the
    frozen m*, and the replication continues.

    **This is the v6 Qwen case.** Under v6 the projected Gate-4 interval of
    ``pair:B+A`` crossed 0.95 and the stage terminated
    ``COMPOSED_HEADROOM_UNREACHABLE``. The same fixture now drives the
    production stage to a PASS whose record names the arm at a boundary and
    the compressed direction of D(B<-A), and m* is exactly Gate 2's.
    """
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE2_5)
    tree, ctx = prefix.branch(root / "branch")
    gate2 = prefix.payloads[C.STAGE_GATE2]
    m_in = int(gate2["m_star"])
    SL.COMPOSED_OVERRIDES[f"B:{m_in}"] = 1.0
    standins = list(SL.FIXTURE_STANDINS)
    try:
        probe = gates_run.run_gate2_75(
            tree, producing_commit=ctx["commit"],
            environment_digest="scenario", bank=ctx["bank"],
            standins=SL.FIXTURE_STANDINS, block_limit=24, resamples=60,
            generate=SL._scripted_for(SL.screen_rungs() + standins)).payload
    finally:
        SL.clear_overrides()
    contrasts = probe["composed_contrast"]["contrasts"]
    first = contrasts[f"D(B<-A)|{C.OUTCOME_FIRST}"]
    return {
        "branch": "v7 A1: the treated arm at the ceiling is recorded",
        "outcome": probe["outcome"],
        "terminal_status": probe["disposition"]["terminal_status"],
        "m_star_frozen_at_gate2": m_in,
        "probe_m_star": int(probe["m_star"]),
        "reselected": bool(probe["reselected"]),
        "d_b_from_a_estimate": first["estimate"],
        "d_b_from_a_statuses": first["statuses"],
        "arm_at_boundary": first["boundary"]["any_arm_at_boundary"],
        "positive_direction_compressed":
            first["boundary"]["compression"]["positive_direction_compressed"],
        "contrast_statuses": probe["contrast_statuses"],
        "probe_record_exists": tree.stage_record(C.STAGE_GATE2_75).exists(),
        "expected": "PASS, no terminal status, m* unmoved, "
                    "COMPOSED_ARM_AT_BOUNDARY and "
                    "COMPOSED_CONTRAST_RANGE_COMPRESSED on D(B<-A)",
    }


def scenario_probe_passes_at_the_frozen_m_star(root: Path) -> dict[str, Any]:
    """17. The probe records at the frozen m\\*, and every later stage runs
    at **Gate 2's** m\\*.

    What needs driving is the invariant itself: ``effective_m_star`` refuses
    a probe record that disagrees with Gate 2, and this walks Gate 3A
    through the freeze checking every record's own operating point against
    the one §12.3 chose --- and, in v7, that Gate 4 records rather than
    decides on the way.
    """
    prefix = prefix_walk(root / "prefix", C.STAGE_GATE2_5)
    tree, ctx = prefix.branch(root / "branch")
    gate2 = prefix.payloads[C.STAGE_GATE2]
    m_in = int(gate2["m_star"])
    standins = list(SL.FIXTURE_STANDINS)
    probe = gates_run.run_gate2_75(
        tree, producing_commit=ctx["commit"],
        environment_digest="scenario", bank=ctx["bank"],
        standins=SL.FIXTURE_STANDINS, block_limit=24, resamples=60,
        generate=SL._scripted_for(SL.screen_rungs() + standins)).payload
    for run in (gates_run.run_gate3a, gates_run.run_gate3b,
                gates_run.run_gate3c):
        run(tree, producing_commit=ctx["commit"],
            environment_digest="scenario")
    designed = SL.screen_rungs() + SL._bound_constraints(tree)
    gate4 = gates_run.run_gate4(
        tree, producing_commit=ctx["commit"],
        environment_digest="scenario", bank=ctx["bank"], resamples=60,
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
        "branch": "A13: the frozen m* is measured, recorded and carried",
        "m_star_frozen_at_gate2": m_in,
        "probe_m_star_in": int(probe["m_star_in"]),
        "probe_m_star_out": int(probe["m_star"]),
        "reselected": bool(probe["reselected"]),
        "reselections_permitted":
            int(probe["disposition"]["reselections_permitted"]),
        "severities_probed": list(probe["disposition"]["probed_severities"]),
        "admissible_severities": list(probe["admissible_severities"]),
        "probe_outcome": probe["outcome"],
        "gate4_outcome": gate4["outcome"],
        "gate4_contrast_statuses": gate4["contrast_statuses"],
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


# ------------------------------------------------- A15: stage 1, both ways

def _draft_root(root: Path) -> Path:
    """A repository root whose two governed documents declare themselves
    drafts. Not the study's own: a scenario that read the real preregistration
    would start passing or failing on a marker it has no business depending
    on."""
    from dci1v7 import PREREGISTRATION, REFERENCE_DESIGN_SPEC
    from dci1v7.protocol.manifest import DRAFT_MARKER
    import json as _json

    root.mkdir(parents=True, exist_ok=True)
    prereg = root / PREREGISTRATION
    prereg.parent.mkdir(parents=True, exist_ok=True)
    prereg.write_text(f"# SCENARIO PLACEHOLDER\n\nstatus: {DRAFT_MARKER}\n")
    spec = root / REFERENCE_DESIGN_SPEC
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(_json.dumps({"_what": "SCENARIO PLACEHOLDER",
                                 "_status": DRAFT_MARKER}) + "\n")
    return root


def _stage_one(tree: Any, *, repo_root: Path, commit: str,
               bank: Any) -> Any:
    """Stage 1 through the production runner, at a named repository root."""
    from dci1v7.run import registration_run

    return registration_run.run_registration(
        tree, producing_commit=commit,
        adoption={"status": "SYNTHETIC", "note": "scenario"},
        repo_root=repo_root, environment_digest="scenario", bank=bank)


def scenario_stage_one_readiness_is_retryable(root: Path) -> dict[str, Any]:
    """18. A15: a readiness blocker refuses, and the retry succeeds.

    The branch the 2026-08-26 incident took, driven twice on **one** tree.
    Under the old rule the first call ended the replication; under the
    registered one it leaves a REFUSED row and nothing else, and the second
    call --- identical but for a root whose documents are adopted --- passes.

    The criterion is untouched: both calls run the same
    ``signing_blockers``, and what separates them is whether the documents
    declare themselves drafts.
    """
    from dci1v7.run.lifecycle import ReadinessRefusal

    repo, commit = SL.synthetic_repo(root / "adopted")
    context = synthetic_context(root / "evidence", repo_root=repo)
    tree = model_tree(context, SL.MODEL_KEY)
    tree.root.mkdir(parents=True, exist_ok=True)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    from dci1v4.engine.signing import create_signing_key
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    the_bank = SL.bank()

    refused: dict[str, Any] = {}
    try:
        _stage_one(tree, repo_root=_draft_root(root / "draft"),
                   commit=commit, bank=the_bank)
    except ReadinessRefusal as refusal:
        refused = {"status": refusal.status,
                   "blockers": [b["kind"] for b in refusal.observed]}
    rows = transitions.transition_rows(tree)
    after_refusal = {
        "terminal_report": tree.terminal_report.exists(),
        "stage_record": tree.stage_record(C.STAGE_REGISTERED).exists(),
        "transition_outcomes": [r["outcome"] for r in rows],
    }
    retry = _stage_one(tree, repo_root=repo, commit=commit, bank=the_bank)
    return {"branch": "§18 stage 1's readiness verdict (A15)",
            "refused": refused, "after_refusal": after_refusal,
            "retry_outcome": retry.outcome,
            "expected": "REFUSED then PASS, with no terminal report"}


def scenario_stage_one_apparatus_fault_is_retired(root: Path
                                                  ) -> dict[str, Any]:
    """19. A15's recovery: the exact 2026-08-26 record, retired and bound.

    The terminal report is reconstructed by signing the payload directly,
    because ``write_terminal_report`` now refuses a readiness status --- that
    refusal is the amendment, so a scenario about recovering the historical
    record cannot use the current writer to produce one.

    What it drives is the production path: the replication is refused while
    the record stands, ``retire_apparatus_fault`` retains it under
    ``superseded/apparatus_fault/<record hash>/``, stage 1 then passes, and
    the manifest it signs carries the retired hash inside its own signature.
    """
    import json as _json

    from dci1v4.engine.signing import create_signing_key, sign_payload
    from dci1v4.protocol.hashing import sha_bytes
    from dci1v7.protocol import manifest as manifest_mod
    from dci1v7.run import registration_run

    repo, commit = SL.synthetic_repo(root / "adopted")
    context = synthetic_context(root / "evidence", repo_root=repo)
    tree = model_tree(context, SL.MODEL_KEY)
    tree.root.mkdir(parents=True, exist_ok=True)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    the_bank = SL.bank()

    payload = {"status": "REGISTRATION_INCOMPLETE", "model_key": SL.MODEL_KEY,
               "gate": C.STAGE_REGISTERED, "criterion": "§34",
               "observed": [{"kind": "DRAFT_DOCUMENT", "n": 2}],
               "producing_commit": commit,
               "strongest_permissible_statement": C.TERMINAL_SENTENCE,
               "terminal_sentence": C.TERMINAL_SENTENCE}
    tree.terminal_report.write_text(_json.dumps(
        sign_payload(payload, context.signing_key_path),
        indent=2, sort_keys=True) + "\n")
    record_hash = sha_bytes(tree.terminal_report.read_bytes())
    original = tree.terminal_report.read_bytes()

    blocked = _terminal(lambda: _stage_one(tree, repo_root=repo,
                                           commit=commit, bank=the_bank))
    retirement = registration_run.retire_apparatus_fault(
        tree, record_hash=record_hash,
        reason="a caller's configuration defect, not a verdict about a model",
        defect="the CLI did not forward --repo-root to run_registration",
        amendment={"id": "A15", "document": "scenario"},
        producing_commit=commit, decided_by="scenario",
        decided_on="2026-08-26")
    retained = Path(retirement["retained_at"]) / tree.terminal_report.name
    outcome = _stage_one(tree, repo_root=repo, commit=commit, bank=the_bank)
    bound = manifest_mod.load_manifest(context)["apparatus_faults"]
    return {"branch": "§32/A15's pre-manifest retirement",
            "blocked_before_retirement": blocked,
            "retired_record_hash": retirement["retired_record_hash"],
            "retained_bytes_identical": retained.read_bytes() == original,
            "live_path_cleared": not tree.terminal_report.exists(),
            "transition_outcomes": [r["outcome"] for r in
                                    transitions.transition_rows(tree)],
            "stage_one_outcome": outcome.outcome,
            "bound_into_the_manifest": [f["retired_record_hash"]
                                        for f in bound["retired"]],
            "expected": "refused, retired, then PASS with the hash bound"}


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
    "c4_lost_core_kept": scenario_c4_lost_core_kept,
    "full_support_unchanged": scenario_full_support_unchanged,
    "base_arm_is_unconditional": scenario_base_arm_is_unconditional,
    "unsupported_estimands_cannot_reappear":
        scenario_unsupported_estimands_cannot_reappear,
    "reference_checks_conditional": scenario_reference_checks_conditional,
    "gate4_records_a_boundary": scenario_gate4_records_a_boundary,
    "near_form_unavailable": scenario_near_form_unavailable,
    "broad_class_unavailable": scenario_broad_class_unavailable,
    "a2_spectrum_fit": scenario_a2_spectrum_fit,
    "unmask_is_one_shot": scenario_unmask_is_one_shot,
    "coordinate_dependent": scenario_coordinate_dependent,
    "coordinate_secondary_not_computable":
        scenario_coordinate_secondary_not_computable,
    "probe_records_a_ceiling_on_the_treated_arm":
        scenario_probe_records_a_ceiling_on_the_treated_arm,
    "probe_passes_at_the_frozen_m_star":
        scenario_probe_passes_at_the_frozen_m_star,
    "stage_one_readiness_is_retryable":
        scenario_stage_one_readiness_is_retryable,
    "stage_one_apparatus_fault_is_retired":
        scenario_stage_one_apparatus_fault_is_retired,
}


def run_scenario(name: str, root: Path | None = None) -> dict[str, Any]:
    here = Path(root or tempfile.mkdtemp(prefix=f"scenario-{name}-"))
    here.mkdir(parents=True, exist_ok=True)
    return {"scenario": name, **SCENARIOS[name](here)}


# ------------------------------------------ parallel execution (2026-08-28)

def instrument_calls(names: Sequence[str], seen: set) -> list:
    """Record every call to the named functions, wherever they are bound.

    Moved here from the audit tool so that a worker process can instrument
    the same rules the serial audit instruments. It wraps the target
    functions **and every alias of them** across the loaded ``dci1v7`` and
    ``tests_v7`` modules --- ``from x import y`` binds the object into the
    importing module and a patch on the defining module alone would never be
    reached --- and the wrapper delegates unchanged, so the run it observes
    is the run that would have happened. Returns the undo list.
    """
    import importlib
    import sys as _sys

    targets: dict = {}
    for dotted in names:
        module_name, _, attr = dotted.rpartition(".")
        try:
            original = getattr(importlib.import_module(module_name), attr,
                               None)
        except Exception:                                    # pragma: no cover
            original = None
        if callable(original):
            targets[original] = dotted

    def wrap(original, dotted):
        # `functools.wraps` keeps the original's identity --- __module__,
        # __qualname__, __doc__ and __wrapped__ --- which matters beyond
        # cosmetics: `composed_probe.assert_probe_reads_no_reference`
        # resolves its own module through `inspect.getmodule` of a wrapped
        # function and scans that module's source. A wrapper that reported
        # this module would make it scan the scenario file instead and
        # refuse every walk at Gate 2.75; with the identity preserved,
        # `inspect` unwraps to the real source and the check reads what it
        # was registered to read. (Found by a parallel review, 2026-08-28.)
        @functools.wraps(original)
        def recorded(*args, **kwargs):
            seen.add(dotted)
            return original(*args, **kwargs)
        return recorded

    undo = []
    for module in list(_sys.modules.values()):
        if module is None or not getattr(module, "__name__", "").startswith(
                ("dci1v7", "tests_v7")):
            continue
        for attr, value in list(vars(module).items()):
            dotted = targets.get(value) if callable(value) else None
            if dotted is None:
                continue
            setattr(module, attr, wrap(value, dotted))
            undo.append((module, attr, value))
    return undo


def _scenario_worker(name: str, root: str, instrument: Sequence[str]
                     ) -> dict[str, Any]:
    """One scenario in its own process: its own temporary root, its own
    harness closures, its own instrumentation, cleaned up on exit.

    Returns the scenario result (payloads and reads included, for the
    scenario that carries them), the set of instrumented functions that
    executed here, and the §34 values the walk ran under --- exactly what
    the serial audit accumulates in-process, gathered per scenario so the
    parent can merge them deterministically.
    """
    import shutil

    from dci1v7.protocol import decisions as _decisions

    here = Path(root)
    here.mkdir(parents=True, exist_ok=True)
    # A worker process runs one scenario and exits (``max_tasks_per_child``
    # below), and the prefix caches are cleared here as well: a cached
    # prefix is a path into a tree this worker's previous scenario would
    # already have removed, and a branch copied from it would fail.
    _PREFIXES.clear()
    _D6_PREFIXES.clear()
    seen: set[str] = set()
    SL.resolved_manifest()
    undo = instrument_calls(list(instrument), seen) if instrument else []
    try:
        result = run_scenario(name, here)
        ran_under = {k: _decisions.value_of(k) for k in _decisions.DECISION_IDS}
    finally:
        for module, attr, original in undo:
            setattr(module, attr, original)
        SL.restore()
        shutil.rmtree(here, ignore_errors=True)
    return {"name": name, "result": result, "seen": sorted(seen),
            "decisions": ran_under}


def run_scenarios_parallel(names: Sequence[str], *, workers: int = 5,
                           root: Path | None = None,
                           instrument: Sequence[str] = ()
                           ) -> dict[str, Any]:
    """Run independent scenarios in separate processes, results in the
    order ``names`` gives them.

    Each scenario is an independent branch of the lifecycle: it builds the
    signed prefix it needs in its own temporary root, so no two workers
    share a tree, a cache, a mask namespace or a repository. The cost is
    that a prefix two scenarios share in-process is walked once per
    process; the gain is wall-clock time bounded by the longest scenario
    rather than the sum. Workers are spawned, not forked, so each starts
    from a clean interpreter and the harness closures are made per process.

    Returns ``{"results": {name: result}, "seen": set, "decisions": dict}``
    with ``results`` keyed in the given order whatever the completion
    order --- the same aggregation the serial path produces.
    """
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    base = Path(root or tempfile.mkdtemp(prefix="scenarios-parallel-"))
    base.mkdir(parents=True, exist_ok=True)
    context = mp.get_context("spawn")
    outcomes: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=max(1, int(workers)),
                             mp_context=context,
                             max_tasks_per_child=1) as pool:
        futures = {name: pool.submit(_scenario_worker, name,
                                     str(base / name), list(instrument))
                   for name in names}
        for name in names:
            outcomes[name] = futures[name].result()
    seen: set[str] = set()
    decisions_ran_under: dict[str, Any] = {}
    for name in names:
        seen |= set(outcomes[name]["seen"])
        if name == "normal_full_path" or not decisions_ran_under:
            decisions_ran_under = dict(outcomes[name]["decisions"])
    return {"results": {name: outcomes[name]["result"] for name in names},
            "seen": seen, "decisions": decisions_ran_under}


def run_all(root: Path | None = None,
            only: tuple[str, ...] = ()) -> dict[str, Any]:
    base = Path(root or tempfile.mkdtemp(prefix="scenarios-"))
    out: dict[str, Any] = {}
    for name in SCENARIOS:
        if only and name not in only:
            continue
        out[name] = run_scenario(name, base / name)
    return out
