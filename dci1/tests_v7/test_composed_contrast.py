"""Gate 4 (v7) projects the composed contrast; the analysis realises it.

Gate 4 reads its rows as the confirmatory analysis reads rows, forms every
registered contrast by the registered estimators, and records the boundary
reading and the projected precision. The analysis attaches the same readings
to statements, reads decision intervals widened by the allowance, and
withholds every classification from a structural zero. Nothing in either
place terminates.
"""
from __future__ import annotations

import inspect

import pytest
from dci1v7.analysis import boundary as B
from dci1v7.analysis import claims
from dci1v7.protocol import constants as C
from dci1v7.run import analysis_run, gates_run
from dci1v7.stages import composed_contrast as CC
from dci1v7.stages import support

from tests_v7.conftest import observation_table, synthetic_rows

ARMS = ("base", "core", "spectrum", "nearform", "class")


def _families():
    sf = {slot: f"MK{index + 1}" for index, slot in enumerate(C.CORE_SLOTS)}
    for index, slot in enumerate(C.SPECTRUM_SLOTS):
        sf[slot] = f"MK{index // 2 + 1}"
    for index, slot in enumerate(C.NEAR_FORM_SLOTS):
        sf[slot] = f"XC{index + 1}"
    return sf


# ---------------------------------------------------------------- Gate 4

def test_the_projection_covers_every_projectable_family_and_terminates_nothing():
    table = observation_table(ARMS, blocks=24, m_draws=4, seed=5)
    out = CC.projection(table, arms=ARMS, seed=11, resamples=60)
    assert out["outcome"] == "PASS" and out["terminates"] is False
    assert out["label"] == "PROJECTION_NOT_REGISTERED_FOR_INFERENCE"
    assert out["read_by"] == []
    keys = set(out["families"])
    for family in CC.PROJECTED_FAMILIES:
        if family in C.CROSS_CONFIGURATION_FAMILIES:
            assert f"{family}:cross" in keys
        else:
            for configuration in C.CONFIGURATIONS:
                assert f"{family}:{configuration}" in keys
    f1 = out["families"][f"F1:{C.OUTCOME_FIRST}"]
    assert "delta_difficulty" not in f1["members"]
    assert set(f1["members"]) >= {"D(B<-A)", "D(A<-B)", "Lambda", "Delta_R",
                                  "Xi"}
    entry = f1["members"]["Delta_R"]
    assert entry["boundary"]["member"] == "Delta_R"
    assert entry["projected_confirmatory"]["projected"] is True
    assert entry["precision_precondition"] == C.PRECISION_PRECONDITIONS[
        "Delta_R"]
    assert isinstance(entry["projected_meets_precondition"], bool)
    assert entry["label"] == "PROJECTION_NOT_REGISTERED_FOR_INFERENCE"


def test_a_missing_arm_is_recorded_not_computable_and_nothing_else():
    table = observation_table(("base", "class"), blocks=12, m_draws=4, seed=2)
    out = CC.projection(table, arms=("base", "class"), seed=1, resamples=30)
    assert out["outcome"] == "PASS"
    assert any(k.endswith(":Delta_R") for k in out["not_computable"])
    assert "Delta_broad" in out["families"][f"F10:{C.OUTCOME_FIRST}"][
        "members"]
    assert out["families"][f"F2:{C.OUTCOME_FIRST}"]["members"] == {}


def test_a_ceiling_on_b_under_a_is_recorded_on_the_projection():
    rates = {("B", "A", C.OUTCOME_FIRST): 1.0, ("B", "A", C.OUTCOME_SECOND): 1.0}
    table = observation_table(ARMS, blocks=24, m_draws=4, seed=5, rates=rates)
    out = CC.projection(table, arms=ARMS, seed=11, resamples=60)
    entry = out["families"][f"F1:{C.OUTCOME_FIRST}"]["members"]["Delta_R"]
    assert entry["estimate"] < 0
    assert B.ARM_AT_BOUNDARY in entry["statuses"]
    assert B.RANGE_COMPRESSED in entry["statuses"]
    assert entry["decision_upper_with_allowance"] > entry["marginal_upper"]
    assert not entry["boundary"]["structural_zero"]
    # Ord_B differences the two B-under-A cells, and both are at the ceiling,
    # so THAT contrast is a structural zero --- recorded, and terminal for
    # nothing.
    ord_b = out["families"]["F11:cross"]["members"]["Ord_B"]
    assert ord_b["boundary"]["structural_zero"] is True
    assert out["any_structural_zero"] is True
    assert out["outcome"] == "PASS"


def test_the_gate4_runner_has_no_terminal_branch_and_builds_the_table_the_analysis_reads():
    source = inspect.getsource(gates_run.gate4_payload)
    assert "TerminalStatus" not in source
    assert "build_observations(" in source
    assert "composed_contrast.projection(" in source
    assert 'outcome": composed_contrast.GATE4_OUTCOME' in source
    assert CC.GATE4_OUTCOME == "PASS"


def test_the_descriptive_table_and_proximity_gate_nothing():
    from dci1v7.verifiers.constraints import Constraint

    rows = synthetic_rows(("base",), blocks=4, m_draws=2, seed=1)
    for row in rows:
        for score in row["scores"]:
            score["passed"] = True
    shape = gates_run.composed_table_shape(("base",))
    slot_map = {"A": Constraint("A", 3), "B": Constraint("B", 9)}
    for row in rows:
        for score in row["scores"]:
            score["kind"] = score["slot"]
            score["severity"] = slot_map[score["slot"]].severity
    table = CC.composed_table(rows, shape, slot_map)
    assert table["solo:A"]["A"] == 1.0
    proximity = CC.cell_proximity(table, shape)
    assert all(p["near_boundary"] == "ceiling" for p in proximity)
    # and still: nothing here raises, nothing here is a verdict
    gates_run.assert_composed_table_complete(table, ("base",))


# ------------------------------------------------- the confirmatory analysis

def test_the_analysis_widens_decision_bounds_and_attaches_the_statuses():
    rates = {("B", "A", C.OUTCOME_FIRST): 1.0, ("B", "A", C.OUTCOME_SECOND): 1.0}
    table = observation_table(ARMS, blocks=16, m_draws=4, seed=7, rates=rates)
    estimates = analysis_run.estimate_all(
        table, statuses=[], arms=ARMS, seed=3, resamples=40,
        slot_families=_families())
    entry = estimates["intervals"][f"F1:{C.OUTCOME_FIRST}"]["Delta_R"]
    assert entry["boundary"]["any_arm_at_boundary"]
    assert entry["decision_upper"] > entry["upper"]
    assert entry["decision_lower"] == entry["lower"]
    assert B.ARM_AT_BOUNDARY in entry["boundary_statuses"]
    # F5's recodings carry no reading: they are on another scale.
    recoded = estimates["intervals"][f"F5:{C.OUTCOME_FIRST}"][
        "Delta_R|vacuity_forced"]
    assert recoded["boundary"] is None
    interval = analysis_run._interval(
        analysis_run._strip_vectors(estimates), "F1", C.OUTCOME_FIRST,
        "Delta_R")
    assert interval.upper == entry["decision_upper"]
    assert B.ARM_AT_BOUNDARY in claims.boundary_statuses(interval)
    summary = analysis_run._boundary_summary(
        analysis_run._strip_vectors(estimates), projected=None)
    assert B.ARM_AT_BOUNDARY in summary["statuses"]
    assert summary["terminates"] is False


def test_a_structural_zero_in_the_analysis_has_no_direction_and_reads_by_block_count():
    """v7 §13.14 (revised 2026-08-28, V10). On a 12-block synthetic table the
    allowance is +/-0.242, so Delta_R's structural zero reads no level under
    INSUFFICIENT_PRECISION; the directional emitters withhold with the
    marker; and at the registered block count the same reading is L3c."""
    rates = {("B", None, "solo"): 1.0}
    for companion in ("A",) + C.CORE_SLOTS + C.SPECTRUM_SLOTS \
            + C.NEAR_FORM_SLOTS + (C.CLASS_SLOT,):
        for configuration in C.CONFIGURATIONS:
            rates[("B", companion, configuration)] = 1.0
    table = observation_table(ARMS, blocks=12, m_draws=4, seed=7, rates=rates)
    estimates = analysis_run.estimate_all(
        table, statuses=[], arms=ARMS, seed=3, resamples=30,
        slot_families=_families())
    stripped = analysis_run._strip_vectors(estimates)
    delta_r = analysis_run._interval(stripped, "F1", C.OUTCOME_FIRST,
                                     "Delta_R")
    assert claims.is_structural_zero(delta_r)
    read = claims.delta_r_reading(delta_r)
    assert read["levels"] == []
    assert {"STRUCTURAL_ZERO", "INSUFFICIENT_PRECISION"} <= set(read["markers"])
    assert delta_r.lower == pytest.approx(-B.boundary_halfwidth(12))
    assert delta_r.upper == pytest.approx(B.boundary_halfwidth(12))
    assert not read["direction_resolved"]
    # At the registered block count the same allowance interval lies inside
    # the equivalence region and meets the precondition: L3c, marked.
    half = B.boundary_halfwidth(C.N_BLOCKS)
    at_384 = claims.Interval("Delta_R", 0.0, -half, half,
                             boundary=delta_r.boundary)
    read_384 = claims.delta_r_reading(at_384)
    assert read_384["levels"] == ["L3c"]
    assert "STRUCTURAL_ZERO" in read_384["markers"]
    assert read_384["direction"]["direction"] == "DIRECTION_UNRESOLVED"
    d_b = analysis_run._interval(stripped, "F1", C.OUTCOME_FIRST, "D(B<-A)")
    assert claims.is_structural_zero(d_b)
    l1 = claims.emit_l1(configuration=C.OUTCOME_FIRST, cell="pair:A+B",
                        outcome_position=1,
                        measurement_basis=C.MEASUREMENT_BASIS,
                        member="D(B<-A)", interval=d_b, solo_headroom=True)
    assert l1["emitted"] is False and "STRUCTURAL_ZERO" in l1["markers"]
    ord_b = analysis_run._interval(stripped, "F11", "cross", "Ord_B")
    l4b = claims.emit_l4b(member="Ord_B", interval=ord_b,
                          measurement_basis=C.MEASUREMENT_BASIS,
                          both_configurations_analysed=True)
    assert l4b["emitted"] is False and "STRUCTURAL_ZERO" in l4b["markers"]
    # D(A<-B) reads A's cells and is untouched.
    d_a = analysis_run._interval(stripped, "F1", C.OUTCOME_FIRST, "D(A<-B)")
    assert not claims.is_structural_zero(d_a)


def test_l3_names_the_direction_and_carries_the_boundary():
    better = claims.Interval("Delta_R", -0.20, -0.24, -0.16,
                             boundary={"statuses": [B.RANGE_COMPRESSED],
                                       "structural_zero": False})
    out = claims.emit_l3(
        configuration=C.OUTCOME_FIRST, cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS, delta_r=better,
        delta_difficulty=None, xi=claims.Interval("Xi", 0.0, -0.1, 0.1),
        support={"holds": False}, references_identified=True)
    emitted = [s for s in out if s["emitted"]]
    assert [s["claim_level"] for s in emitted] == ["L3c"]
    assert emitted[0]["direction"]["direction"] == "A_COMPARATIVELY_BETTER"
    assert emitted[0]["direction"]["beyond_sesoi"] is True
    assert B.RANGE_COMPRESSED in emitted[0]["identification_status"]
    assert emitted[0]["boundary"]["statuses"] == [B.RANGE_COMPRESSED]
    worse = claims.Interval("Delta_R", 0.30, 0.26, 0.34)
    out = claims.emit_l3(
        configuration=C.OUTCOME_FIRST, cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS, delta_r=worse,
        delta_difficulty=None, xi=claims.Interval("Xi", 0.2, 0.1, 0.3),
        support={"holds": False}, references_identified=True)
    assert {s["claim_level"] for s in out if s["emitted"]} == {"L3a", "L3b"}
    assert out[0]["direction"]["direction"] == "A_HARMS_MORE"


def test_the_direction_vocabulary_is_registered_and_reads_the_sesoi():
    assert claims.DELTA_R_DIRECTIONS == (
        "A_HARMS_MORE", "A_COMPARATIVELY_BETTER", "DIRECTION_UNRESOLVED")
    zero = claims.contrast_direction(claims.Interval("Delta_R", 0.0, -0.05,
                                                     0.05))
    assert zero["direction"] == "DIRECTION_UNRESOLVED"
    small = claims.contrast_direction(claims.Interval("Delta_R", -0.05, -0.08,
                                                      -0.02))
    assert small["direction"] == "A_COMPARATIVELY_BETTER"
    assert small["beyond_sesoi"] is False


def test_the_success_criterion_reads_the_gate4_projection():
    out = support.methodological_success({"support_met": True, "realised": {}})
    assert out["stage"] == "pre_gate_4" and out["verdict"] == "MET"
    assert "gate4_contrast" in inspect.signature(
        support.methodological_success).parameters
    assert "gate4_passed" not in inspect.signature(
        support.methodological_success).parameters


def test_the_v7_statuses_are_registered_identification_statuses():
    for status in C.V7_IDENTIFICATION_STATUSES:
        assert status in C.IDENTIFICATION_STATUSES
        assert status not in C.TERMINAL_STATUSES
    assert "STRUCTURAL_ZERO" in C.RESULT_MARKERS
    with pytest.raises(claims.ClaimError):
        claims.boundary_statuses(claims.Interval(
            "Delta_R", 0, 0, 0, boundary={"statuses": ["INVENTED"]}))


def test_a_structural_zero_at_the_registered_block_count_is_an_l3c_that_says_so():
    """v7 §13.14 (revised 2026-08-28, V10). At 384 blocks the allowance
    interval is +/-0.0099: L3c is read, the statement carries the status,
    the marker and the registered sentence, no direction is named, and the
    vacuity-forced recoding is compared exactly as for any other claim."""
    half = B.boundary_halfwidth(C.N_BLOCKS)
    zero = claims.Interval("Delta_R", 0.0, -half, half,
                           boundary={"statuses": [B.STRUCTURAL_ZERO,
                                                  B.ARM_AT_BOUNDARY],
                                     "structural_zero": True})
    forced = claims.Interval("Delta_R", -0.30, -0.34, -0.26)   # also L3c
    assert claims.l3_vacuity_agrees(zero, forced) is True
    out = claims.emit_l3(
        configuration=C.OUTCOME_FIRST, cell="pair:A+B", outcome_position=1,
        measurement_basis=C.MEASUREMENT_BASIS, delta_r=zero,
        delta_difficulty=None, xi=claims.Interval("Xi", 0.0, -0.1, 0.1),
        support={"holds": False}, references_identified=True,
        near_form_available=False,
        vacuity_forced_agrees=claims.l3_vacuity_agrees(zero, forced))
    emitted = [s for s in out if s["emitted"]]
    assert [s["claim_level"] for s in emitted] == ["L3c"]
    l3c = emitted[0]
    assert "STRUCTURAL_ZERO" in l3c["markers"]
    assert B.STRUCTURAL_ZERO in l3c["identification_status"]
    assert l3c["structural_zero_sentence"] == C.STRUCTURAL_ZERO_SENTENCE
    assert "not observed variation" in l3c["structural_zero_sentence"]
    assert l3c["direction"]["direction"] == "DIRECTION_UNRESOLVED"
    assert l3c["l3c_scope"] == "same_form_only"
    # A recoding that reads a different level is a disagreement, as for any
    # claim: the structural zero no longer short-circuits §17.4.
    excess = claims.Interval("Delta_R", 0.20, 0.15, 0.25)          # L3a
    assert claims.l3_vacuity_agrees(zero, excess) is False


def test_a_structural_zero_can_never_license_a_direction():
    """The allowance interval is symmetric about zero at every block count,
    so no lower bound above zero and no upper bound below zero exists."""
    parts = B.composition("Delta_R")
    for n in (2, 24, 192, C.N_BLOCKS, 5000):
        for level in (0.0, 1.0):
            out = B.contrast_boundary(
                "Delta_R", [(p, [level] * n) for p in parts],
                configuration=C.OUTCOME_FIRST)
            lower, upper = B.apply_allowance(0.0, 0.0, out)
            assert lower < 0.0 < upper and lower == pytest.approx(-upper)
            interval = claims.Interval("Delta_R", 0.0, lower, upper,
                                       boundary=out)
            assert not interval.excludes_zero()
            read = claims.delta_r_reading(interval)
            assert not {"L3a", "L3b"} & set(read["levels"])
            assert claims.contrast_direction(interval)["direction"] == \
                "DIRECTION_UNRESOLVED"
