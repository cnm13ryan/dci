"""§18 stage 8: ``GATE_2_75_COMPOSED_PROBE`` --- the record, and its guards.

Two things are under test and they are not the same. The **record** is what
the stage writes at the frozen m*: the paired contrasts, their boundary
readings and their projected precision --- and the fact that nothing it
writes can end the replication or move the operating point. The **guards**
are the four independent reasons a probed cell can never be a B+R cell and
the audit that would notice if one stopped holding.

What is deliberately *not* under test is any value §34 D20 or D24 selects:
the topic split and the stand-ins are researcher decisions, every accessor
refuses while they are, and a test that supplied one would be choosing.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import random

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v7.analysis import boundary, claims, estimators
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions
from dci1v7.run import gates_run
from dci1v7.run.lifecycle import TerminalStatus, terminal_statuses_in_force
from dci1v7.stages import audit_prefreeze, composed_probe as P
from dci1v7.stages import feasibility, regime
from dci1v7.verifiers import constraints as K

from tests_v7.conftest import observation_table

TOPICS = tuple(f"fixture-topic-{i:03d}" for i in range(48))


def _m(level: float, *, jitter: float = 0.0, seed: int = 0,
       topics=TOPICS) -> dict:
    """One entry's measurement, in the shape ``contrast_record`` reads."""
    rng = random.Random(seed)
    per_topic = {t: max(0.0, min(1.0, level + jitter * (rng.random() - 0.5)))
                 for t in topics}
    values = list(per_topic.values())
    mean = sum(values) / len(values)
    return {"compliance": mean, "n_topics": len(values),
            "s2_topic": (sum((v - mean) ** 2 for v in values)
                         / max(len(values) - 1, 1)),
            "per_topic": per_topic}


def _table(b_solo: float = 0.75, *, b_under_a: float | None = None,
           a_solo: float = 0.65, a_under_b: float | None = None,
           standin_solo: float = 0.5, b_with_standin: float = 0.6,
           jitter: float = 0.3) -> dict:
    """One probed table: the determinate six plus a stand-in's cells."""
    ba = b_solo if b_under_a is None else b_under_a
    ab = a_solo if a_under_b is None else a_under_b
    return {
        "unconstrained": {"unconstrained": {"compliance": 48.0,
                                            "s2_topic": 0.0, "n_topics": 48}},
        "solo:A": {"A": _m(a_solo, jitter=jitter, seed=1)},
        "solo:B": {"B": _m(b_solo, jitter=jitter, seed=2)},
        "pair:A+B": {"A": _m(ab, jitter=jitter, seed=3),
                     "B": _m(ba, jitter=jitter, seed=4)},
        "pair:B+A": {"B": _m(ba, jitter=jitter, seed=5),
                     "A": _m(ab, jitter=jitter, seed=6)},
        "solo:P1": {"P1": _m(standin_solo, jitter=jitter, seed=7)},
        "pair:B+P1": {"B": _m(b_with_standin, jitter=jitter, seed=8),
                      "P1": _m(standin_solo, jitter=jitter, seed=9)},
        "pair:P1+B": {"B": _m(b_with_standin, jitter=jitter, seed=10),
                      "P1": _m(standin_solo, jitter=jitter, seed=11)},
    }


def _ceiling(topics=TOPICS) -> dict:
    return {"compliance": 1.0, "n_topics": len(topics), "s2_topic": 0.0,
            "per_topic": {t: 1.0 for t in topics}}


# ------------------------------------------------------- placement and shape

def test_the_probe_is_the_stage_between_gate_2_5_and_gate_3a():
    order = list(C.STAGE_SEQUENCE)
    assert order.index(C.STAGE_GATE2_75) == order.index(C.STAGE_GATE2_5) + 1
    assert order.index(C.STAGE_GATE3A) == order.index(C.STAGE_GATE2_75) + 1
    assert C.STAGE_GATE2_75 in C.GENERATION_STAGES
    assert "composed_probe" in C.VERIFIER_BOUND_ENTRY_POINTS


def test_the_cell_shape_covers_every_gate4_exposure_class():
    """Derived from Gate 4's own cell set, not listed."""
    classes = P.gate4_exposure_classes()
    assert sum(1 for key in classes if key[1]) == 10
    slots = P.probe_slots(3)
    report = P.assert_probe_covers_gate4_classes(slots)
    assert report["gate4_entries"] == 95
    assert all(e["covered"] for e in report["coverage"].values())
    assert set(report["determinate_classes"]) == {
        "solo:target", "solo:focal", "composed:target+focal",
        "composed:focal+target"}
    shape = P.probe_cell_types(slots)
    ids = [cell_id for cell_id, _a, _s in shape]
    assert ids == ["unconstrained", "solo:A", "solo:B",
                   "solo:P1", "solo:P2", "solo:P3",
                   "pair:A+B", "pair:B+A",
                   "pair:B+P1", "pair:P1+B", "pair:B+P2", "pair:P2+B",
                   "pair:B+P3", "pair:P3+B",
                   "pair:A+P1", "pair:P1+A", "pair:P1+P2", "pair:P2+P1"]


def test_a_shape_that_leaves_a_gate4_class_uncovered_is_refused():
    with pytest.raises(ProtocolError, match="unmeasured"):
        P.assert_probe_covers_gate4_classes([])
    with pytest.raises(ProtocolError):
        P.probe_slots(4)
    with pytest.raises(ProtocolError):
        P.probe_cell_types(["R1"])


def test_a_probe_slot_is_not_a_registered_design_slot():
    assert not set(P.PROBE_SLOTS) & set(C.REGISTERED_SLOT_ORDER)
    assert P.DETERMINATE_SLOTS == C.BASE_SLOTS


def test_the_probed_set_is_the_one_gate_2_recorded_as_admissible():
    record = {"focal_selection": {"eligible": [9, 10, 11]},
              "focal_admissible": [10, 11]}
    P.assert_probe_severities_are_admissible([10], record)
    with pytest.raises(ProtocolError, match="not admissible"):
        P.assert_probe_severities_are_admissible([9], record)
    with pytest.raises(ProtocolError, match="not in Gate 2's eligible"):
        P.assert_probe_severities_are_admissible([12], record)
    with pytest.raises(ProtocolError, match="recorded no"):
        P.assert_probe_severities_are_admissible(
            [10], {"focal_selection": {"eligible": [10]}})


# --------------------------------------------------------------- the record

def test_the_record_carries_every_entry_and_every_registered_contrast():
    record = P.contrast_record(_table(), seed=1, resamples=50)
    assert record["outcome"] == "PASS" and record["terminates"] is False
    # solo:A, solo:B, both orders of A+B (two slots each), solo:P1, and both
    # orders of B+P1 (two slots each).
    assert record["n_entries_evaluated"] == 11
    assert record["n_determinate_entries"] == 6
    assert record["n_standin_dependent_entries"] == 5
    expected = {f"{m}|{g}" for g, members in P.DETERMINATE_CONTRASTS.items()
                for m in members}
    assert set(record["contrasts"]) == expected
    for entry in record["contrasts"].values():
        assert entry["label"] == "PROJECTION_NOT_REGISTERED_FOR_INFERENCE"
        assert entry["n_topics"] == 48
        assert entry["marginal_lower"] <= entry["estimate"] \
            <= entry["marginal_upper"]
        assert entry["projected_confirmatory"]["projected"] is True
        assert entry["projected_confirmatory"]["t_target"] == C.N_BLOCKS
        assert entry["projected_confirmatory"]["m_target"] == C.M_DRAWS


def test_the_contrasts_are_the_estimators_algebraic_forms():
    """Each (cell, slot, weight) composition equals the registered estimator
    on a synthetic observation table --- so the probe reads the same paired
    contrast the confirmatory analysis will."""
    table = observation_table(("base",), blocks=12, m_draws=4, seed=9)
    cells = {
        "solo:A": {"A": estimators.solo_vector(table, "A")},
        "solo:B": {"B": estimators.solo_vector(table, "B")},
        "pair:A+B": {"A": estimators.composed_vector(
                         table, "A", "B", C.OUTCOME_FIRST),
                     "B": estimators.composed_vector(
                         table, "B", "A", C.OUTCOME_SECOND)},
        "pair:B+A": {"B": estimators.composed_vector(
                         table, "B", "A", C.OUTCOME_FIRST),
                     "A": estimators.composed_vector(
                         table, "A", "B", C.OUTCOME_SECOND)},
    }
    truth = {
        (C.OUTCOME_FIRST, "D(B<-A)"):
            estimators.delivery_loss(table, "B", "A", C.OUTCOME_FIRST),
        (C.OUTCOME_SECOND, "D(B<-A)"):
            estimators.delivery_loss(table, "B", "A", C.OUTCOME_SECOND),
        (C.OUTCOME_FIRST, "D(A<-B)"):
            estimators.delivery_loss(table, "A", "B", C.OUTCOME_FIRST),
        (C.OUTCOME_SECOND, "D(A<-B)"):
            estimators.delivery_loss(table, "A", "B", C.OUTCOME_SECOND),
        (C.OUTCOME_FIRST, "Lambda"):
            estimators.asymmetry(table, C.OUTCOME_FIRST),
        (C.OUTCOME_SECOND, "Lambda"):
            estimators.asymmetry(table, C.OUTCOME_SECOND),
        ("cross", "Ord_A"): estimators.ord_a(table),
        ("cross", "Ord_B"): estimators.ord_b(table),
        ("cross", "Ord_Lambda"): estimators.ord_lambda(table),
    }
    for group, members in P.DETERMINATE_CONTRASTS.items():
        for member, parts in members.items():
            derived = [sum(w * cells[cell][slot][i] for cell, slot, w in parts)
                       for i in range(len(table.blocks))]
            assert max(abs(a - b) for a, b in
                       zip(derived, truth[(group, member)])) < 1e-12, member


def test_a_ceiling_on_the_treated_arm_is_recorded_and_ends_nothing():
    """The v6 Qwen case, one step further: B is delivered under A in EVERY
    topic. v6 terminated two stages earlier on a projection of this. v7
    records what it does to the contrast --- the arm is at a boundary, the
    excess direction is compressed --- and continues."""
    table = _table(0.75)
    table["pair:A+B"]["B"] = _ceiling()
    table["pair:B+A"]["B"] = _ceiling()
    out = P.probe_disposition(m_star=10, probed={10: table}, seed=1,
                              resamples=50)
    assert out["outcome"] == "PASS"
    assert out["terminal_status"] is None
    assert out["m_star_out"] == out["m_star_in"] == 10
    record = out["verdict"]
    for group in (C.OUTCOME_FIRST, C.OUTCOME_SECOND):
        entry = record["contrasts"][f"D(B<-A)|{group}"]
        assert entry["estimate"] < 0                   # a delivery gain
        reading = entry["boundary"]
        assert reading["any_arm_at_boundary"] and not reading["structural_zero"]
        assert boundary.ARM_AT_BOUNDARY in entry["statuses"]
        assert boundary.RANGE_COMPRESSED in entry["statuses"]
        assert reading["compression"]["positive_direction_compressed"]
        assert reading["allowance_upper"] > 0 == reading["allowance_lower"]
        assert entry["decision_upper_with_allowance"] > entry["marginal_upper"]
    assert "COMPOSED_ARM_AT_BOUNDARY" in record["contrast_statuses"]


def test_a_structural_zero_is_named_and_ends_nothing():
    table = _table()
    for cell in ("solo:B", "pair:A+B", "pair:B+A"):
        table[cell]["B"] = _ceiling()
    out = P.probe_disposition(m_star=10, probed={10: table}, seed=1,
                              resamples=50)
    assert out["outcome"] == "PASS"
    record = out["verdict"]
    assert record["any_structural_zero"] is True
    for group in (C.OUTCOME_FIRST, C.OUTCOME_SECOND):
        entry = record["contrasts"][f"D(B<-A)|{group}"]
        assert entry["boundary"]["structural_zero"] is True
        assert entry["estimate"] == 0.0 and entry["degenerate"] is True
        assert boundary.STRUCTURAL_ZERO in entry["statuses"]
    assert record["contrasts"]["Ord_B|cross"]["boundary"]["structural_zero"]
    # And D(A<-B) is untouched: it reads A's cells.
    assert not record["contrasts"][f"D(A<-B)|{C.OUTCOME_FIRST}"][
        "boundary"]["structural_zero"]


def test_a_stand_in_at_a_boundary_is_proximity_and_nothing_else():
    table = _table(b_with_standin=0.99, jitter=0.02)
    record = P.contrast_record(table, seed=1, resamples=20)
    assert {e["cell"] for e in record["standin_proximity"]} == {
        "pair:B+P1", "pair:P1+B"}
    assert record["standin_proximity_gates_nothing"] is True
    assert record["outcome"] == "PASS"
    # A stand-in entry never enters a contrast.
    for entry in record["contrasts"].values():
        for cell in entry["boundary"]["constituents"]:
            assert cell["companion"] in (None, "A", "B")


def test_a_determinate_cell_without_a_per_topic_vector_is_refused():
    table = _table()
    table["pair:A+B"]["B"] = {"compliance": 0.8, "s2_topic": 0.01,
                              "n_topics": 48}
    with pytest.raises(ProtocolError, match="per-topic vector"):
        P.contrast_record(table, seed=1, resamples=20)


def test_cells_measured_on_different_topics_are_refused_not_aligned():
    table = _table()
    other = tuple(f"other-{i}" for i in range(48))
    table["pair:A+B"]["B"] = _m(0.7, topics=other)
    with pytest.raises(ProtocolError, match="different topic sets"):
        P.contrast_record(table, seed=1, resamples=20)


def test_a_missing_entry_is_refused_rather_than_skipped():
    table = _table()
    del table["pair:B+P1"]["P1"]
    with pytest.raises(ProtocolError, match="carries a measurement for"):
        P.contrast_record(table, seed=1, resamples=20)


def test_the_six_determinate_entries_are_all_required():
    table = _table()
    del table["solo:A"]
    with pytest.raises(ProtocolError, match="determinate entries"):
        P.contrast_record(table, seed=1, resamples=20)


def test_the_record_is_seeded_and_reproducible():
    a = P.contrast_record(_table(), seed=7, resamples=60)
    b = P.contrast_record(_table(), seed=7, resamples=60)
    assert a["contrasts"] == b["contrasts"]
    c = P.contrast_record(_table(), seed=8, resamples=60)
    assert c["contrasts"] != a["contrasts"]


def test_the_projected_confirmatory_precision_is_section_16_1s_form():
    """The planning constant is the family's Šidák value and the block count
    and M are the registered ones; more measured variance only widens it."""
    import math

    from dci1v7.analysis.bootstrap import sidak_critical

    record = P.contrast_record(_table(jitter=0.3), seed=1, resamples=20)
    key = f"D(B<-A)|{C.OUTCOME_FIRST}"
    entry = record["contrasts"][key]
    projected = entry["projected_confirmatory"]
    assert projected["planning_constant"] == pytest.approx(
        sidak_critical(len(C.FAMILY_MEMBERS["F1"])))
    assert record["contrasts"]["Ord_A|cross"]["projected_confirmatory"][
        "planning_constant"] == pytest.approx(
        sidak_critical(len(C.FAMILY_MEMBERS["F11"])))
    # §16.1's form, re-combined at the registered M and block count from the
    # two components the record carries.
    expected = projected["planning_constant"] * math.sqrt(
        (projected["s2_topic"] + projected["s2_draw"] / C.M_DRAWS) / C.N_BLOCKS)
    assert projected["half_width"] == pytest.approx(expected)
    assert projected["m_measured"] == C.M_CAL
    assert projected["s2_topic"] >= 0.0 and projected["s2_draw"] > 0.0
    assert entry["precision_precondition"] == C.PRECISION_PRECONDITIONS["D"]


# ----------------------------------------------------- the frozen m* (A13)

def test_the_frozen_m_star_is_returned_and_nothing_is_reselected():
    out = P.probe_disposition(m_star=10, probed={10: _table()}, seed=1,
                              resamples=20)
    assert out["reselected"] is False
    assert out["m_star_out"] == out["m_star_in"] == 10
    assert out["reselections_permitted"] == 0
    assert out["reselection_rule"] == "none"
    assert out["m_star_is_frozen"] is True
    assert out["m_star_is_frozen_at"] == C.STAGE_GATE2
    assert P.assert_m_star_unmoved(out, gate2_m_star=10) == 10


def test_a_second_severity_is_refused_not_searched():
    probed = {10: _table(), 11: _table(0.7)}
    with pytest.raises(ProtocolError, match="at no other severity"):
        P.probe_disposition(m_star=10, probed=probed, seed=1, resamples=20)
    with pytest.raises(ProtocolError):
        P.probe_disposition(m_star=10, probed={11: _table()}, seed=1,
                            resamples=20)


def test_no_function_here_can_return_an_m_star_it_was_not_given():
    tree = ast.parse(inspect.getsource(P.probe_disposition))
    assigned = [
        value for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
        for key, value in zip(node.keys, node.values)
        if isinstance(key, ast.Constant) and key.value == "m_star_out"]
    assert assigned
    for value in assigned:
        assert isinstance(value, ast.Call)
        assert value.func.id == "int"
        assert value.args[0].id == "m_star"
    assert "select_operating_point" not in inspect.getsource(
        P.probe_disposition)


def test_assert_m_star_unmoved_refuses_a_record_that_moved_it():
    out = P.probe_disposition(m_star=10, probed={10: _table()}, seed=1,
                              resamples=20)
    with pytest.raises(ProtocolError):
        P.assert_m_star_unmoved({**out, "m_star_out": 11}, gate2_m_star=10)
    with pytest.raises(ProtocolError):
        P.assert_m_star_unmoved({**out, "reselected": True}, gate2_m_star=10)


# ------------------------------------------ v7 A1: no terminal status here

def test_the_withdrawn_status_is_not_in_force_and_cannot_be_raised():
    for status in ("COMPOSED_HEADROOM_UNREACHABLE",
                   "COMPOSED_HEADROOM_FAILURE"):
        assert status in C.WITHDRAWN_STATUSES
        assert status not in C.TERMINAL_STATUSES
        assert status not in terminal_statuses_in_force()
        assert C.WITHDRAWN_STATUS_REASONS[status]
        with pytest.raises(ProtocolError, match="not a registered"):
            TerminalStatus(status, gate=C.STAGE_GATE2_75, criterion="x",
                           observed=None, strongest_permissible_statement="x")
    assert C.NEW_TERMINAL_STATUSES == ()
    assert not hasattr(P, "COMPOSED_HEADROOM_UNREACHABLE")
    assert "TerminalStatus" not in inspect.getsource(P)


def test_no_module_in_the_package_can_raise_a_withdrawn_status():
    """The converse of A8: a withdrawn status has no raise path anywhere."""
    from dci1v7.protocol import revision

    assert revision.assert_no_raise_path()["raise_paths"] == []


def test_the_probe_module_has_exactly_one_outcome():
    assert P.PROBE_OUTCOME == "PASS"
    assert audit_prefreeze.NAME_SCANNED_RECORDS[C.STAGE_GATE2_75][
        "outcomes"] == ("PASS",)
    assert audit_prefreeze.NAME_SCANNED_RECORDS[C.STAGE_GATE4][
        "outcomes"] == ("PASS",)


# ------------------------------------------------- the four B+R guarantees

def test_guarantee_1_the_probe_runs_before_any_reference_exists():
    from dci1v7.engine.transitions import PREDECESSOR

    order = list(C.STAGE_SEQUENCE)
    assert PREDECESSOR[C.STAGE_GATE2_75] == C.STAGE_GATE2_5
    assert order.index(C.STAGE_GATE2_75) < order.index(C.STAGE_GATE3B)


def test_guarantee_2_a_standin_is_refused_everywhere_a_candidate_is_chosen(
        monkeypatch):
    standin = dataclasses.replace(K.FAMILIES["MK1"], probe_only=True)
    families = {**K.FAMILIES, "MK1": standin}
    monkeypatch.setattr(K, "FAMILIES", families)
    monkeypatch.setattr(regime, "FAMILIES", families)
    monkeypatch.setattr(feasibility, "FAMILIES", families)
    assert K.is_probe_only("MK1")
    with pytest.raises(K.InstrumentError):
        regime.carry_candidate(
            kind="MK1", severity=3, prescreen_solo_compliance=0.5,
            n_prescreen_topics=24,
            structural=regime.StructuralScreen())
    with pytest.raises(K.InstrumentError):
        gates_run.slot_map_from_record({"slot_map": {"R1": ["MK1", 3]}})
    assert K.assert_no_probe_only_selection_path()["found"] == []


def test_guarantee_3_the_probe_record_is_name_scanned_like_gate_4s():
    assert C.STAGE_GATE2_75 in audit_prefreeze.NAME_SCANNED_RECORDS
    probe = {"outcome": "PASS", "m_star": 11, "reselected": False,
             audit_prefreeze.DECLARED_REFUSALS_KEY:
                 dict(P.PROBE_DECLARED_REFUSALS)}
    gate4 = {"outcome": "PASS",
             audit_prefreeze.DECLARED_REFUSALS_KEY: {
                 "no_substitution_after_a_reading": "x",
                 "no_selection_here": "x",
                 "no_composed_rate_terminates_a_replication": "x"}}
    assert audit_prefreeze._check_8(gate4, probe)[0] == "PASS"
    stripped = {k: v for k, v in probe.items()
                if k != audit_prefreeze.DECLARED_REFUSALS_KEY}
    assert audit_prefreeze._check_8(gate4, stripped)[0] == "FAIL"
    named = {**probe, "reselect_reference": "R2"}
    assert audit_prefreeze._check_8(gate4, named)[0] == "FAIL"
    assert audit_prefreeze._check_8(gate4, {**probe, "widen_band": True})[0] \
        == "FAIL"
    # A v6-shaped outcome is a record no v7 stage wrote.
    assert audit_prefreeze._check_8(
        gate4, {**probe, "outcome": "COMPOSED_HEADROOM_UNREACHABLE"})[0] \
        == "FAIL"
    assert audit_prefreeze._check_8(gate4, None)[0] == "UNRESOLVED"


def test_guarantee_4_no_function_here_reads_a_selection_record():
    report = P.assert_probe_reads_no_reference()
    assert report["found"] == []
    assert report["source_reads_no_selection_stage"] is True
    with pytest.raises(ProtocolError):
        P.assert_probe_reads_no_reference(
            {"load_reference_pool": lambda: None})


def test_the_one_name_scan_exemption_is_registered_and_must_be_exercised():
    spec = audit_prefreeze.NAME_SCANNED_RECORDS[C.STAGE_GATE2_75]
    assert set(spec["permitted_fields"]) == {"reselected"}
    assert audit_prefreeze.NAME_SCANNED_RECORDS[C.STAGE_GATE4][
        "permitted_fields"] == {}
    gate4 = {"outcome": "PASS",
             audit_prefreeze.DECLARED_REFUSALS_KEY: {
                 "no_substitution_after_a_reading": "x",
                 "no_selection_here": "x",
                 "no_composed_rate_terminates_a_replication": "x"}}
    without = {"outcome": "PASS",
               audit_prefreeze.DECLARED_REFUSALS_KEY:
                   dict(P.PROBE_DECLARED_REFUSALS)}
    verdict, detail = audit_prefreeze._check_8(gate4, without)
    assert verdict == "FAIL"
    assert detail[C.STAGE_GATE2_75]["detail"]["exempted_but_absent"] == \
        ["reselected"]


def test_the_declared_refusals_say_what_the_guarantees_are():
    keys = set(P.PROBE_DECLARED_REFUSALS)
    assert any("reference" in k for k in keys)
    assert any("substitut" in k for k in keys)
    assert any("reselection" in k for k in keys)
    assert "no_composed_rate_terminates_a_replication" in keys
    assert "no_contrast_here_licenses_a_claim" in keys
    assert "band_not_relaxed" not in keys       # there is no band to relax


def test_the_scope_limits_are_on_the_record_not_discovered_at_gate_4():
    text = " ".join(P.PROBE_SCOPE_LIMITS)
    assert "identity" in text
    assert "Delta_R" in text and "first projected at Gate 4" in text
    assert "PROJECTION" in text or "projection" in text
    assert "terminat" not in text.replace("terminates nothing", "")\
        .replace("stop the replication", "")


# ------------------------------------------ the decisions it fails closed on

@pytest.mark.parametrize("accessor,decision_id",
                         [("probe_split", "D20"), ("standins", "D24")])
def test_every_open_decision_refuses_rather_than_defaulting(
        accessor, decision_id, restore_decisions):
    restore_decisions.reopen_all_for_testing()
    assert decision_id in decisions.open_decisions()
    with pytest.raises(decisions.DecisionOpenError):
        getattr(P, accessor)()
    assert decision_id in decisions.decisions_blocking_stage(C.STAGE_GATE2_75)


def test_the_residual_allowance_decisions_are_withdrawn_with_their_consumer():
    assert set(decisions.WITHDRAWN_DECISION_IDS) == {"D23", "D26"}
    assert "D23" not in decisions.DECISION_IDS
    assert "D26" not in decisions.DECISION_IDS
    for name in ("residual_reading", "residual_allowance",
                 "projection_residual_sd", "margin_band",
                 "projected_halfwidth", "entry_verdict", "severity_verdict",
                 "RESIDUAL_SD"):
        assert not hasattr(P, name), name


def test_the_registered_standins_are_the_probe_only_families(
        restore_decisions):
    restore_decisions.override_for_testing("D24", "probe_only_in_library")
    assert P.standins() == ("PS1", "PS2", "PS3")
    assert P.PROBE_ONLY_KINDS() == K.PROBE_ONLY_FAMILY_IDS


def test_the_separate_vocabulary_branch_has_no_instruments_and_refuses(
        restore_decisions):
    restore_decisions.override_for_testing("D24", "separate_vocabulary")
    with pytest.raises(ProtocolError) as excinfo:
        P.standins()
    assert "D24" in str(excinfo.value)


# ------------------------------------------------------------ what it is not

def test_the_probe_measures_a_contrast_and_the_module_says_so():
    text = " ".join((P.__doc__ or "").split())
    assert "blind to any *reference*" in text
    assert "delivery **gain** on the treated arm" in text
    assert "one outcome, ``PASS``" in text


def test_l4a_stays_within_replication():
    assert claims.CONFIGURATION_SCOPE == "within_replication"
    with pytest.raises(claims.ClaimError):
        claims.assert_configuration_scope(
            ("gemma:outcome_first", "qwen:outcome_first"))
    assert audit_prefreeze._check_9()[0] == "PASS"


def test_a_probe_record_may_not_be_written_twice(tmp_path):
    from dci1v7.engine import transitions
    from dci1v7.engine.context import synthetic_context
    from dci1v7.engine.paths import model_tree
    from dci1v4.engine.signing import create_signing_key

    context = synthetic_context(tmp_path)
    tree = model_tree(context, "gemma-3n-e2b-it")
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(context.signing_key_path)
    payload = {"stage": C.STAGE_GATE2_75,
               "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE2_75],
               "outcome": "PASS", "m_star": 11}
    transitions.write_stage_record(tree, C.STAGE_GATE2_75, payload)
    with pytest.raises(IntegrityError):
        transitions.write_stage_record(tree, C.STAGE_GATE2_75, payload)
