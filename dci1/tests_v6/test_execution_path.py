"""One regression per execution-path defect found by the stage 3-18 sweep.

Each test names the defect, states the registered rule, and fails if the
production path stops honouring it. They are deliberately about *reachability
and consumption*, not about arithmetic: every one of V5-E9 through V5-E21 had
correct arithmetic sitting behind a caller that never called it, or a caller
that called it with the wrong input.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v6.analysis import claims, spectrum
from dci1v6.protocol import constants as C
from dci1v6.protocol import open_items
from dci1v6.run import analysis_run, contracts, gates_run, regime_run
from dci1v6.stages import regime, support

from tests_v6.conftest import observation_table

SRC = Path(__file__).resolve().parent.parent / "src" / "dci1v6"


# ------------------------------------------------------------------ V5-E9

def _estimates(arms=("base", "core", "spectrum", "nearform", "class")):
    table = observation_table(arms, blocks=6)
    slot_families = {slot: f"MK{index + 1}"
                     for index, slot in enumerate(C.CORE_SLOTS)}
    for index, slot in enumerate(C.SPECTRUM_SLOTS):
        slot_families[slot] = f"MK{index // 2 + 1}"
    for index, slot in enumerate(C.NEAR_FORM_SLOTS):
        slot_families[slot] = f"XC{index + 1}"
    return analysis_run.estimate_all(
        table, statuses=[], arms=arms, seed=3, resamples=40,
        slot_families=slot_families)


def test_every_registered_family_member_is_accounted_for():
    """V5-E9. §15 registers 78 members; four families reached no record.

    F5, F6, F7 and F8 were computed nowhere and declared neither
    NOT_IDENTIFIED nor NOT_COMPUTABLE: they were absent, which reads as a
    family that does not exist rather than one the design did not identify.
    """
    estimates = _estimates()
    accounted = set(estimates["not_identified"]) | set(
        estimates["not_computable"])
    for bucket in estimates["configurations"].values():
        accounted |= set(bucket)
    accounted |= set(estimates["cross_configuration"])
    for family, members in C.FAMILY_MEMBERS.items():
        missing = sorted(set(members) - accounted)
        assert not missing, f"{family} has unaccounted members {missing}"


@pytest.mark.parametrize("family", ["F5", "F6", "F7", "F8"])
def test_the_four_silent_families_are_computed(family):
    """V5-E9, per family. Each has at least one estimated member."""
    estimates = _estimates()
    members = C.FAMILY_MEMBERS[family]
    identified = [
        m for m in members
        for bucket in estimates["configurations"].values()
        if bucket.get(m, {}).get("status") == "IDENTIFIED"]
    assert identified, f"{family} produced no identified member"


def test_a_family_with_no_computable_member_says_so():
    """V5-E9. `_intervals` skipped an empty family in silence."""
    estimates = _estimates(arms=("base", "core"))
    intervals = estimates["intervals"]
    for family in ("F8", "F9", "F10"):
        keys = [k for k in intervals if k.startswith(f"{family}:")]
        assert keys, f"{family} has no interval entry at all"
        for key in keys:
            entry = intervals[key]
            if "reason" in entry:
                assert entry["status"] == analysis_run.NOT_IDENTIFIED
                assert entry["members"] == list(C.FAMILY_MEMBERS[family])


def test_f5_reads_the_draw_level_recodings():
    """V5-E9. §17.4's recoding is a different estimand, not a rescaling."""
    assert analysis_run.F5_RECODINGS["vacuity_forced"] == \
        "non_vacuous_compliance"
    assert analysis_run.F5_RECODINGS["graded_0.99"] == "graded_threshold"
    built = {f"{m}|{k}" for k, ms in analysis_run.F5_MEMBERS.items()
             for m in ms}
    assert built == set(C.FAMILY_MEMBERS["F5"])


def test_f8_uses_the_adopted_a2_formulation():
    """V5-E9. §11.8's secondary must run under U2's adopted reading."""
    source = inspect.getsource(spectrum.tier_estimate)
    assert "assert_adopted_formulation" in source


# ----------------------------------------------------------------- V5-E10

def test_every_claim_emitter_has_a_production_caller():
    """V5-E10. L2, L3 and L4b were implemented, tested and unreachable."""
    source = inspect.getsource(analysis_run._statements)
    for emitter in ("emit_l1", "emit_l2", "emit_l3", "emit_l4a", "emit_l4b"):
        assert f"claims.{emitter}(" in source, f"{emitter} has no caller"


def test_the_l3_emitter_receives_the_vacuity_forced_verdict():
    """V5-E10 with V5-E9. §17.4 licenses a claim only when the primary and
    the recomputation agree, and the verdict has to be formed from F5."""
    source = inspect.getsource(analysis_run._statements)
    assert "l3_vacuity_agrees" in source
    primary = claims.Interval("Delta_R", 0.30, 0.20, 0.40)
    same = claims.Interval("Delta_R", 0.31, 0.21, 0.41)
    different = claims.Interval("Delta_R", 0.02, -0.01, 0.05)
    assert claims.l3_vacuity_agrees(primary, same)
    assert not claims.l3_vacuity_agrees(primary, different)


def test_no_unregistered_l5_emitter():
    claims.assert_no_l5_emitter(vars(claims))


# ----------------------------------------------------------------- V5-E11

def test_regime_adequacy_is_a_verdict_and_reads_a_share():
    """V5-E11. §12.4 condition 3 is about a SHARE, and the section says so."""
    ok = regime.regime_adequacy(
        solo_a=0.70, solo_b=0.80, vacuity_b=0.02,
        graded_shares={n: {"graded_share_above": 0.5,
                           "graded_share_below": 0.2} for n in ("A", "B")})
    assert ok["adequate"]
    vacuous = regime.regime_adequacy(
        solo_a=0.70, solo_b=0.80, vacuity_b=0.5,
        graded_shares={n: {"graded_share_above": 0.5,
                           "graded_share_below": 0.2} for n in ("A", "B")})
    assert not vacuous["adequate"]
    assert vacuous["failures"][0]["condition"] == 2
    degenerate = regime.regime_adequacy(
        solo_a=0.70, solo_b=0.80, vacuity_b=0.02,
        graded_shares={"A": {"graded_share_above": 1.0,
                             "graded_share_below": 0.0},
                       "B": {"graded_share_above": 0.5,
                             "graded_share_below": 0.2}})
    assert not degenerate["adequate"]
    assert degenerate["failures"][0]["reading"] == "share"


def test_regime_not_found_has_a_production_raiser():
    source = inspect.getsource(gates_run.gate2_payload)
    assert '"REGIME_NOT_FOUND"' in source
    assert "regime_adequacy(" in source


def test_grid_resolution_insufficient_has_a_production_raiser():
    """V5-E11. A grid that jumps a whole band is not an exhausted range."""
    straddling = regime.grid_resolution({1: 0.99, 2: 0.01}, band=(0.5, 0.85),
                                        grid=(1, 2))
    assert straddling["insufficient"]
    exhausted = regime.grid_resolution({1: 0.01, 2: 0.02}, band=(0.5, 0.85),
                                       grid=(1, 2))
    assert not exhausted["insufficient"]
    source = inspect.getsource(gates_run.gate2_payload)
    assert '"GRID_RESOLUTION_INSUFFICIENT"' in source


def test_the_graded_shares_are_produced_at_response_level():
    from dci1v6.run.execute import cell_rates
    rows = [{"topic_id": f"t{i}", "topic_split": "pooled", "arm": "solo",
             "word_count": 80, "truncated": False,
             "scores": [{"kind": "B", "severity": 9, "present": True,
                         "passed": True, "vacuous_pass": False,
                         "graded": 1.0 if i else 0.5}]}
            for i in range(10)]
    rates = cell_rates(rows, kind="B", severity=9, present=True)
    assert rates["graded_share_above"] == pytest.approx(0.9)
    assert rates["graded_share_below"] == 0.0
    assert rates["graded_share_reading"] == "share"


# ----------------------------------------------------------------- V5-E12

def test_the_expansion_has_a_production_caller():
    """V5-E12. §12.6's reserve mechanism could not operate."""
    source = inspect.getsource(regime_run.regime_payload)
    assert "run_expansion(" in source
    assert "coverage_rows(" in source


def test_the_coverage_verdict_reaches_gate3c():
    """V5-E12. C1-C6 unmet must drop the core and spectrum arms."""
    source = inspect.getsource(gates_run.gate3c_payload)
    assert "regime_record.get(\"identification_statuses\")" in source
    report = support.evaluate_support(
        model_key="fixture-model",
        structurally_eligible_tier12_families=["MK1"] * 8,
        qualified_families=["MK1", "MK2", "MK3", "MK4", "MK5"],
        selection={"core_references": [], "identification_statuses": []},
        near_form_available=True, class_available=True,
        spectrum_identified=True,
        design_time_failures=["§12.6: the criterion was not met"])
    assert not report["support_met"]
    assert "core" not in report["admitted_arms"]
    assert "spectrum" not in report["admitted_arms"]


# ----------------------------------------------------------------- V5-E13

def test_the_screen_can_drop_an_arm_selection_would_have_admitted():
    """V5-E13. §12.6's C7 and C8 decide arm availability at the screen."""
    source = inspect.getsource(gates_run.gate3c_payload)
    assert "CLASS_ARM_NOT_AVAILABLE" in source
    assert "NEAR_FORM_ARM_NOT_AVAILABLE" in source


# ----------------------------------------------------------------- V5-E14

def test_the_algebraic_form_checks_run():
    """V5-E14. Three registered executable checks had no caller."""
    source = inspect.getsource(analysis_run._algebraic_form_checks)
    for name in ("assert_delta_r_forms", "assert_order_forms",
                 "assert_algebraic_forms_agree"):
        assert name in source
    estimates = _estimates()
    checks = estimates["algebraic_form_checks"]["checks"]
    assert checks, "no algebraic form check ran"
    for name, result in checks.items():
        assert "worst" in result or "not_available" in result, name


# ----------------------------------------------------------------- V5-E15

def test_the_projection_audit_has_a_production_caller():
    """V5-E15. §23's prospective record was the empty list on every path.

    The rows themselves need kappa(c|B), which exists only on a table whose
    B-solo cells carry absent verdicts --- so the populated case is asserted
    on the real lifecycle payload in ``test_synthetic_lifecycle``, and what
    is asserted here is that the field has a producer at all.
    """
    source = inspect.getsource(analysis_run.unmasked_payload)
    assert "_projection_audit(" in source
    assert "\"projection_audit\": []" not in inspect.getsource(analysis_run)
    # A table with no counterfactual-chance verdicts yields no rows, and says
    # so by yielding none rather than by raising.
    table = observation_table(("base", "core"), blocks=6)
    assert analysis_run._projection_audit(table) == []


# ----------------------------------------------------------------- V5-E16

def test_the_report_row_names_its_own_claim_level_and_cell():
    """V5-E16. Every per-configuration row was L1 and pair:A+B."""
    assert analysis_run.CLAIM_LEVEL_OF_MEMBER["Lambda"] == "L2"
    assert analysis_run.CLAIM_LEVEL_OF_MEMBER["Delta_R"] == "L3"
    assert analysis_run.CLAIM_LEVEL_OF_MEMBER["Ord_A"] == "L4b"
    assert "Delta_1" not in analysis_run.CLAIM_LEVEL_OF_MEMBER
    # The row carries what the statements say the member REACHED, and None
    # where they say nothing: an L3a and an L3c are different findings about
    # the same member, so the level cannot be mapped from the name.
    reached = analysis_run._levels_reached([
        {"emitted": True, "claim_level": "L3a", "configuration": "outcome_first"},
        {"emitted": True, "claim_level": "L1", "member": "D(B<-A)",
         "configuration": "outcome_first"},
        {"emitted": False, "claim_level": "L2", "member": "Lambda",
         "configuration": "outcome_first"}])
    assert reached[("Delta_R", "outcome_first")] == "L3a"
    assert reached[("D(B<-A)", "outcome_first")] == "L1"
    assert ("Lambda", "outcome_first") not in reached
    assert analysis_run._cell_of_member("D(B<-R1)") == "pair:B+R1"
    assert analysis_run._cell_of_member("D(R1<-A)") == "pair:A+R1"
    assert analysis_run._cell_of_member("D(A<-B)") == "pair:A+B"
    assert analysis_run._cell_of_member(
        "vac(B|B+R1-)-vac(B solo)") == "pair:B+R1-"


# ----------------------------------------------------------------- V5-E17

def test_the_lexicographic_order_check_runs_in_production():
    from dci1v6.stages import qualification_gate
    source = inspect.getsource(qualification_gate.qualify_candidates)
    assert "assert_lexicographic_order(" in source


# ----------------------------------------------------------------- V5-E19

def test_iota_a_stability_runs_in_production():
    source = inspect.getsource(gates_run.gate3a_payload)
    assert "assert_iota_a_stable(" in source
    assert "a_per_topic_by_split" in inspect.getsource(gates_run.gate2_payload)


# ----------------------------------------------------------------- V5-E21

def test_iota_a_is_read_at_the_severity_nearest_the_aim():
    """V5-E21. §12.6 defines iota_A at the severity nearest §12.3's aim and
    the runner took the first row of the table."""
    source = inspect.getsource(regime_run.regime_payload)
    assert "TARGET_AIM" in source
    assert 'next((r["iota"] for r in table if r["kind"] == "A")' not in source


# -------------------------------------------------------------------- U4

def test_the_coverage_eligibility_rule_reads_the_resolution():
    """U4 is closed at E2 and the rule reads the RESOLUTION, not a literal.

    The distinction is the whole design of `open_items`: a rule that hardcoded
    E2 would keep running if the resolution went away, and the resolution is
    what makes it a researcher's choice rather than an implementer's.
    """
    row = {"candidate": "MK1:3", "kind": "MK1", "severity": 3,
           "iota": 0.5, "solo": 0.6, "vacuity": 0.01}
    assert open_items.get_item("U4").resolution == "E2"
    assert regime.coverage_eligibility(row)["formulation"] == "E2"
    for name in regime.ELIGIBILITY_FORMULATIONS:
        verdict = regime.coverage_eligibility(row, formulation=name)
        assert verdict["formulation"] == name
    with pytest.raises(ProtocolError):
        regime.coverage_eligibility(row, formulation="E9")


def test_the_coverage_eligibility_rule_still_fails_closed(restore_open_items):
    """Provoked: with U4 reopened the rule refuses rather than defaulting."""
    row = {"candidate": "MK1:3", "kind": "MK1", "severity": 3,
           "iota": 0.5, "solo": 0.6, "vacuity": 0.01}
    restore_open_items.reopen_one_for_testing("U4")
    with pytest.raises(open_items.OpenItemError):
        regime.coverage_eligibility(row)


def test_the_two_eligibility_readings_can_disagree():
    """Why U4 blocked at all: the readings admit different rungs.

    E2 is adopted, so this rung is eligible; under E1 it would not have been,
    and the eligible set decides C1-C6, the admitted arm set and therefore
    whether Delta_R is identified. Kept as a live demonstration that the
    resolution had consequences rather than being a formatting choice.
    """
    row = {"candidate": "MK1:3", "kind": "MK1", "severity": 3,
           "iota": 0.95, "solo": 0.5, "vacuity": 0.01}
    assert not regime.coverage_eligibility(row, formulation="E1")["eligible"]
    assert regime.coverage_eligibility(row, formulation="E2")["eligible"]
    assert regime.coverage_eligibility(row)["eligible"]


# ------------------------------------------------------- the contract audit

def test_the_contract_declares_gate2_a_reader_of_calibration_priority():
    """V5-E6's shape, as a permanent regression on the registry itself.

    Gate 2 reads `carried_set` for one thing --- to report §12.2's total
    beside §12.7's measured population --- so the registry declares it and
    the rule that matters is enforced by VALUE below. The population is what
    went wrong in V5-E6, not the read.
    """
    for entry in contracts.CONTRACT:
        if entry.artifact == C.STAGE_REGIME \
                and entry.field == "calibration_priority":
            assert C.STAGE_GATE2 in entry.readers


def test_the_runtime_audit_fails_when_gate2_consumes_the_carried_set():
    """The canonical regression: 326 carried, 112 in the population."""
    regime_payload = {
        "carried_set": [f"MK1:{i}" for i in range(326)],
        "calibration_priority": {
            "tier12": [f"MK1:{i}" for i in range(88)],
            "tier3_measured": [f"RF1:{i}" for i in range(24)],
            "tier3_dropped_for_budget": [f"RF2:{i}" for i in range(214)],
            "tier3_cap": 24},
        "identification_statuses": [],
    }
    good = {C.STAGE_REGIME: regime_payload,
            C.STAGE_GATE2: {"calibration_population": {"n_measured": 112}}}
    reads = {C.STAGE_GATE2: {C.STAGE_REGIME: ["calibration_priority"]}}
    audit = contracts.audit_contracts(good, reads)
    wrong = [d for d in audit["defects"] if d.get("kind") == "WRONG_INPUT_FIELD"]
    assert not wrong, wrong

    bad = {C.STAGE_REGIME: regime_payload,
           C.STAGE_GATE2: {"calibration_population": {"n_measured": 326}}}
    bad_reads = {C.STAGE_GATE2: {C.STAGE_REGIME: ["carried_set"]}}
    audit = contracts.audit_contracts(bad, bad_reads)
    checks = {d.get("check") for d in audit["defects"]}
    assert "gate2_measures_the_calibration_population" in checks
    assert "gate2_did_not_measure_the_carried_set" in checks

    # And the case the count alone cannot separate: Gate 2 measured exactly
    # as many rungs as the screen carried, and the screen carried more than
    # §12.7's population. That is V5-E6 on the real screen --- 326 against
    # 112 --- and it is caught on the value, not on which key was touched.
    assert any(d.get("check") == "gate2_did_not_measure_the_carried_set"
               and d["observed"] == 326 for d in audit["defects"])


def test_a_payload_audit_that_checks_nothing_is_a_failure():
    with pytest.raises(ProtocolError):
        contracts.assert_contracts_clean({}, {})


def test_the_semantic_audit_notices_a_missing_family():
    payloads = {C.STAGE_UNMASKED_ANALYSIS: {
        "estimands": {"configurations": {}, "cross_configuration": {},
                      "not_identified": [], "not_computable": []}}}
    audit = contracts.audit_contracts(payloads, {})
    families = {d.get("family") for d in audit["defects"]
                if d.get("check") == "every_registered_family_member_is_"
                                     "accounted_for"}
    assert families == set(C.FAMILY_MEMBERS)


# --------------------------------------------------- one stage per invocation

def test_no_stage_runner_launches_its_successor():
    """A completed stage returns control. The v5 CLI runs one stage per
    invocation, and no runner may start the next one in the same process."""
    from dci1v6.run import cli

    runners = {fn.__name__ for fn in cli.RUNNERS.values()}
    for path in sorted((SRC / "run").glob("*.py")):
        if path.name == "cli.py":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (func.id if isinstance(func, ast.Name)
                    else func.attr if isinstance(func, ast.Attribute)
                    else None)
            if name in runners:
                raise AssertionError(
                    f"{path.name} calls the stage runner {name}; a stage may "
                    "not launch its successor in the same process")


def test_gate0_does_not_launch_the_regime_screen():
    from dci1v6.run import qualification_run

    source = inspect.getsource(qualification_run.run_gate0)
    assert "run_regime_screen" not in source
    assert "regime_payload" not in source


# ----------------------------------------------------------------- V5-E24

def test_a_family_that_cannot_straddle_keeps_its_core_slot():
    """V5-E24. §13.12 drops the SPECTRUM on exhaustion; §8.1 keeps the core.

    Three qualifying families, each with exactly one rung inside §13.8's
    caliper and nothing strictly above iota_A, so no family can supply a
    triple. The registered outcome is three core references, no spectrum arm
    and `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` --- not an empty core set.
    """
    from dci1v6.stages import selection

    from tests_v6.conftest import calibration_row

    iota_a = 0.70
    rows = []
    # §13.8 also wants two declared discourse roles: thus is consecutive,
    # though is contrastive.
    for index, kind in enumerate(("MK1", "MK3", "XC1")):
        for severity, solo in ((3, 0.705), (5, 0.55), (7, 0.40)):
            rows.append(calibration_row(kind, severity, solo=solo,
                                        chance=0.005))
    stability = {r.label: {"passed": True, "stable": True,
                           "equivalent": True, "admissible_on_both": True}
                 for r in rows}
    result = selection.select_all(
        rows, iota_a=iota_a, solo_compliance_a=0.70,
        n_topics_a=C.N_CALIBRATION, stability_by_candidate=stability)
    core = result.core
    assert core["references_identified"], core.get("dropped")
    assert len(core["core_references"]) == C.N_CORE_REFERENCES
    assert not core["spectrum_identified"]
    assert core.get("spectrum_exhausted") is True
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in core["identification_statuses"]
    assert result.spectrum == []


# ----------------------------------------------------------------- V5-E25

def test_the_prescreen_measures_a_and_b():
    """V5-E25. §12.6 defines iota_A on the pre-screen; A was never on it."""
    rungs = regime_run._screen_rungs()
    kinds = {c.kind for c in rungs}
    assert "A" in kinds and "B" in kinds
    assert {c.severity for c in rungs if c.kind == "A"} == set(C.TARGET_GRID)
    assert {c.severity for c in rungs if c.kind == "B"} == set(C.FOCAL_GRID)

    from dci1v6.design import budget

    assert budget.screen_rungs() == len(rungs), (
        "the budget and the runner must not disagree about what the screen "
        "measures")


# ----------------------------------------------------------------- V5-E26

def test_the_masked_phase_withholds_a_recoding_of_a_withheld_member():
    """V5-E26. §20 withholds a member by what it is, not by its exact name."""
    from dci1v6.analysis import masking

    assert "gamma_tier" in masking.MASKED_PHASE_FORBIDDEN_MEMBERS
    estimates = analysis_run.estimate_all(
        observation_table(("base", "core", "spectrum"), blocks=6),
        statuses=[], arms=("base", "core", "spectrum"), seed=5, resamples=20)
    for configuration, bucket in estimates["configurations"].items():
        for member, entry in bucket.items():
            if member.split("|")[0] in masking.MASKED_PHASE_FORBIDDEN_MEMBERS:
                assert entry.get("point") is None, (
                    f"{member} carries a masked-phase value")
    masking.assert_delta_difficulty_not_masked(
        analysis_run._strip_vectors(estimates))


def test_l3_stands_alone_when_the_difficulty_support_fails():
    """§17.6 row 5: `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, L3a/L3b/L3c only.

    §13.12's exhaustion drops the spectrum arm and §8.1 keeps Delta_R, so a
    replication without a fit must still reach L3's local sub-levels. The
    emitter required a delta_difficulty interval, so it reached none.
    """
    statements = claims.emit_l3(
        configuration=C.OUTCOME_FIRST, cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS,
        delta_r=claims.Interval("Delta_R", 0.30, 0.27, 0.33),
        delta_difficulty=None,
        xi=claims.Interval("Xi", 0.20, 0.17, 0.23),
        support={}, references_identified=True, near_form_available=True)
    emitted = [s for s in statements if s.get("emitted")]
    levels = {s["claim_level"] for s in emitted}
    assert levels and levels <= {"L3a", "L3b", "L3c"}
    for statement in emitted:
        assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in \
            statement["identification_status"]


# ----------------------------------------------------------------- V5-E28

def test_the_focal_extension_can_actually_be_measured():
    """V5-E28. A3 gave §12.3's escalation a caller and the branch refused.

    §7.2's {15, 16} are outside B's registered grid by construction, and
    `Constraint` refuses them unless the caller says `extended` --- which
    §12.3 is the only rule allowed to do. Gate 2 built the extension grid
    without it, so the first replication that actually needed the escalation
    would have died in the instrument layer, and every later reconstruction
    of B at an extension m* would have died too.
    """
    from dci1v6.verifiers.constraints import Constraint

    with pytest.raises(Exception):
        Constraint("B", C.FOCAL_EXTENSION[0])
    for severity in C.FOCAL_EXTENSION:
        assert gates_run.focal_constraint(severity).extended
    for severity in C.FOCAL_GRID:
        assert not gates_run.focal_constraint(severity).extended
    source = inspect.getsource(gates_run.gate2_payload)
    assert "extended=extended" in source
    assert 'Constraint("B", m_star)' not in source
    # And every later reconstruction of B from a recorded m*, which is where
    # the escalation would have died three stages after producing it.
    rebuilt = gates_run.slot_map_from_record(
        {"slot_map": {"B": ["B", C.FOCAL_EXTENSION[-1]], "R1": ["MK1", 9]}})
    assert rebuilt["B"].extended and not rebuilt["R1"].extended


# ----------------------------------------------------------------- V5-E27

def test_the_raw_coordinate_replication_is_computed_and_reported():
    """V5-E27. §18 step 14 repeats steps 9 and 12 on the raw coordinate.

    Step 9 is executed. Step 12 is not, and the reason is recorded rather
    than left as an omission: §15 registers the raw-coordinate replication
    among the quantities "reported with marginal intervals only and
    supporting no claim", and §15's F1-F11 declares no family containing a
    raw-coordinate member, so a simultaneous interval would need a
    multiplicity set nobody registered. Inventing one is what §33 forbids.
    """
    from tests_v6.scenarios import _coordinate_input

    payload = analysis_run._raw_coordinate_secondary(
        {"outcome_first": _coordinate_input()}, seed=7, resamples=500,
        post_unmask=True)
    assert payload["coordinate"] == C.SECONDARY_DIFFICULTY_COORDINATE
    assert payload["step_9"] == "executed"
    assert payload["step_12"] == "NOT_REGISTERED_FOR_INFERENCE"
    entry = payload["configurations"]["outcome_first"]
    assert entry["status"] == "IDENTIFIED"
    assert entry["simultaneous_ci95"] is None
    assert entry["simultaneous_ci95_reason"] == "NOT_REGISTERED_FOR_INFERENCE"
    # Step 9 in full: the fit, both algebraic forms, the support conditions
    # and the block bootstrap, all on the raw coordinate.
    assert entry["algebraic_forms_worst"] is not None
    assert entry["marginal_ci95"][0] < entry["point"] < entry["marginal_ci95"][1]
    assert set(entry["support"]) and entry["refit_per_replicate"]


def test_no_raw_coordinate_family_was_invented():
    """The conservative half of V5-E27's disposition, as a regression.

    §15's declared families are the multiplicity structure. If a later change
    ever adds a raw-coordinate member to one, the simultaneous intervals of
    that family change and every claim it carries changes width --- so the
    absence is asserted rather than assumed.
    """
    members = {m for members in C.FAMILY_MEMBERS.values() for m in members}
    assert not [m for m in members
                if "raw" in m.lower() or m.endswith("|raw_solo")]


def test_the_raw_replication_is_withheld_in_the_masked_phase():
    """§20: A's point is inside the permuted group on either coordinate."""
    from tests_v6.scenarios import _coordinate_input

    payload = analysis_run._raw_coordinate_secondary(
        {"outcome_first": _coordinate_input()}, seed=7, resamples=50,
        post_unmask=False)
    assert payload["step_9"] == "MASKED_PHASE"
    assert payload["configurations"] == {}


def test_the_record_carries_the_raw_replication_through_the_strip():
    """The OUTPUT_DROPPED class, on the function that caused it.

    `_strip_vectors` has an explicit key list and it is where §11.3/§11.7's
    agreement checks were lost once already. `_statements` reads the raw
    replication off the STRIPPED result, so a key dropped here silently
    disables §17.6's coordinate rule rather than raising.
    """
    source = inspect.getsource(analysis_run._strip_vectors)
    assert "raw_coordinate_secondary" in source
    assert "raw_coordinate_secondary" in inspect.getsource(
        analysis_run._statements) or "_raw_coordinate_reading" in \
        inspect.getsource(analysis_run._statements)


def test_the_coordinate_rule_attaches_a_status_and_never_a_level():
    """§17.6 / §34 D14: the registered coordinate decides the classification.

    A raw replication that read L3d where the primary reads L3e must not
    promote the statement. It attaches DIFFICULTY_COORDINATE_DEPENDENT and
    the emitted level stays the primary's --- which is the difference
    between reporting a disagreement and resolving toward whichever estimand
    crossed a threshold.
    """
    from dci1v6.analysis import claims

    support = {"holds": True}
    primary = claims.Interval("delta_difficulty", 0.005, -0.023, 0.033)
    secondary = claims.Interval("delta_difficulty", 0.060, 0.032, 0.088)
    agreement = claims.coordinate_agreement(
        delta_difficulty=primary, support=support, secondary=secondary,
        secondary_support=support)
    assert agreement["primary_levels"] == ["L3e"]
    assert agreement["secondary_levels"] == ["L3d"]
    assert agreement["statuses"] == ["DIFFICULTY_COORDINATE_DEPENDENT"]

    statements = claims.emit_l3(
        configuration="outcome_first", cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS,
        delta_r=claims.Interval("Delta_R", 0.02, -0.01, 0.05),
        delta_difficulty=primary,
        xi=claims.Interval("Xi", 0.09, 0.04, 0.14), support=support,
        references_identified=True,
        delta_near=claims.Interval("Delta_near", 0.02, -0.01, 0.05),
        coordinate_statuses=agreement["statuses"])
    emitted = [s for s in statements if s.get("emitted")]
    assert emitted
    assert "L3d" not in {s["claim_level"] for s in emitted}
    for statement in emitted:
        assert "DIFFICULTY_COORDINATE_DEPENDENT" in \
            statement["identification_status"]
    # An unregistered status cannot ride in on this argument.
    with pytest.raises(claims.ClaimError):
        claims.emit_l3(
            configuration="outcome_first", cell="pair:A+B",
            outcome_position=1, measurement_basis=C.MEASUREMENT_BASIS,
            delta_r=claims.Interval("Delta_R", 0.02, -0.01, 0.05),
            delta_difficulty=primary,
            xi=claims.Interval("Xi", 0.09, 0.04, 0.14), support=support,
            references_identified=True,
            coordinate_statuses=("MADE_UP_STATUS",))


def test_agreement_is_not_claimed_when_there_is_nothing_to_compare():
    """§17.6 compares two classifications; with one, no status is earned."""
    from dci1v6.analysis import claims

    agreement = claims.coordinate_agreement(
        delta_difficulty=claims.Interval("delta_difficulty", 0.06, 0.03, 0.09),
        support={"holds": True}, secondary=None, secondary_support=None)
    assert agreement["compared"] is False
    assert agreement["statuses"] == []
