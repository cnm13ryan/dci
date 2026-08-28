"""The invariants the operating point has to keep.

Each is stated as a property of the **production** path, not of a fixture.
The first is the one the researcher fixed on 2026-08-26 and it governs the
rest: **m\\* is selected once, by §12.3 at Gate 2, and nothing downstream may
move it.** A composed outcome may reject the frozen operating point and end
the replication; it may never choose a different one, and it may never choose
a reference.
"""
from __future__ import annotations

import ast
import inspect

import pytest

from dci1v4.errors import ProtocolError

from dci1v7.engine import transitions
from dci1v7.protocol import constants as C
from dci1v7.run import contracts, freeze_run, gates_run
from dci1v7.stages import composed_probe, feasibility


# ---- 0. m* is frozen at Gate 2 and Gate 2.75 cannot move it.

def test_the_probe_has_no_branch_that_returns_a_different_m_star():
    """The researcher's decision, executed rather than described.

    Three independent statements, each somewhere a reader can point at: the
    disposition refuses a probe table carrying any severity but m*; the only
    expression it ever writes into ``m_star_out`` is its own ``m_star``
    argument; and the module imports no function that could choose one.
    """
    source = inspect.getsource(composed_probe.probe_disposition)
    assert "and at no other severity" in source
    tree = ast.parse(source)
    returned = [value for node in ast.walk(tree)
                if isinstance(node, ast.Dict)
                for key, value in zip(node.keys, node.values)
                if isinstance(key, ast.Constant) and key.value == "m_star_out"]
    assert returned
    assert all(isinstance(v, ast.Call) and v.func.id == "int"
               and v.args[0].id == "m_star" for v in returned)
    assert "select_operating_point" not in source


def test_both_halves_of_the_frozen_invariant_are_on_the_executed_path():
    """Producing and consuming. ``gate2_75_payload`` asserts before it writes
    the record, and ``effective_m_star`` asserts on every read after it."""
    producing = inspect.getsource(gates_run.gate2_75_payload)
    assert "composed_probe.assert_m_star_unmoved(" in producing
    consuming = inspect.getsource(gates_run.effective_m_star)
    assert "assert_probe_m_star_agrees(" in consuming
    assert 'read_stage_record(tree, C.STAGE_GATE2)' in consuming
    with pytest.raises(ProtocolError):
        gates_run.assert_probe_m_star_agrees({"m_star": 11}, gate2_m_star=10)
    assert gates_run.assert_probe_m_star_agrees(
        {"m_star": 10}, gate2_m_star=10) == 10


def test_the_probe_measures_exactly_one_severity():
    """A search is a loop. There is no loop over severities left: the payload
    builds ``order = [m_star]`` and the disposition refuses anything else."""
    source = inspect.getsource(gates_run.gate2_75_payload)
    assert "order = [m_star]" in source
    with pytest.raises(ProtocolError, match="at no other severity"):
        composed_probe.probe_disposition(
            m_star=10, probed={10: {}, 11: {}}, seed=1, resamples=10)


# ---- 1. No composed outcome can select an individual reference.

def test_the_pool_at_every_candidate_is_signed_before_the_probe_generates():
    """§30. The probe selects nothing --- not a severity, not a pool.

    Gate 2 writes a kappa(R|B) column and Gate 2.5 a §13.1 qualified pool for
    every admissible severity, both **before** this stage exists, so no pool
    anywhere on the record can have been shaped by a composed outcome.
    """
    order = C.STAGE_SEQUENCE
    assert order.index(C.STAGE_GATE2) < order.index(C.STAGE_GATE2_5) \
        < order.index(C.STAGE_GATE2_75) < order.index(C.STAGE_GATE3A) \
        < order.index(C.STAGE_GATE3B)
    produced = {(f.artifact, f.field) for f in contracts.CONTRACT}
    assert (C.STAGE_GATE2, "kappa_under_b_by_severity") in produced
    assert (C.STAGE_GATE2_5, "qualification_by_severity") in produced
    assert (C.STAGE_GATE2, "operating_point_search_order") in produced
    assert (C.STAGE_GATE2_5, "operating_point_order") in produced


def test_no_selection_field_is_declared_to_flow_out_of_the_probe():
    """Whatever the probe writes, none of it is a reference."""
    from_probe = {f.field for f in contracts.CONTRACT
                  if f.artifact == C.STAGE_GATE2_75 and f.readers}
    forbidden = {"slot_map", "selection", "qualified_pool",
                 "qualified_families", "core_references", "backups"}
    assert not (from_probe & forbidden)


def test_the_probe_reads_severities_and_never_a_family_name():
    """The restriction on the order is computed at Gate 2.5 for this reason.

    Gate 2.5 knows which families qualified where. The probe is given one
    severity and nothing else, so no family name crosses the boundary into
    the stage that observes composed cells.
    """
    source = inspect.getsource(gates_run.gate2_75_payload)
    assert 'gate2_5_record.get("operating_point_order")' in source
    for name in ("qualified_families", "qualified_pool", "core_references"):
        assert name not in source
    composed_probe.assert_probe_reads_no_reference()


def test_the_composed_probe_module_still_holds_no_path_to_a_reference():
    assert composed_probe.assert_probe_reads_no_reference()["found"] == []
    refusals = composed_probe.PROBE_DECLARED_REFUSALS
    assert "no_pool_is_chosen_by_a_composed_outcome" in refusals
    assert ("the_operating_point_was_frozen_before_any_composed_row"
            in refusals)
    assert "no_reselection_of_the_operating_point_exists" in refusals


def test_the_two_gates_must_agree_about_the_operating_point():
    """Gate 2 selects m* and Gate 2.5 records an order whose head is where it
    qualified. A record whose head is not Gate 2's m* means the two gates
    disagree, and that is refused rather than repaired --- repaired silently,
    it would measure the composed contrast at a severity §12.3 did not select.

    Both paths are exercised end to end by the synthetic lifecycle and by
    ``scenario_probe_passes_at_the_frozen_m_star``; what is pinned here is
    that the refusal exists and that no default was left beside it.
    """
    for fn in (gates_run.gate2_5_payload, gates_run.gate2_75_payload):
        source = inspect.getsource(fn)
        assert "or [m_star]" not in source
        assert "raise ProtocolError(" in source
    probe = inspect.getsource(gates_run.gate2_75_payload)
    assert 'frozen = gate2_5_record.get("operating_point_order")' in probe
    assert "if int(frozen[0]) != m_star:" in probe   # asserted, not repaired
    gate2_5 = inspect.getsource(gates_run.gate2_5_payload)
    assert 'gate2_record.get("operating_point_search_order")' in gate2_5


# ---- 2. An m* change invalidates and recomputes every dependent quantity.

def test_every_m_star_dependent_quantity_is_read_at_the_operating_point():
    """kappa -> qualification -> calibration -> selection -> support.

    Each link reads the operating point from the record that chose it, and
    the two record readers refuse rather than falling back when the value
    they need was not recorded at that point.
    """
    source = inspect.getsource(gates_run.gate3a_payload)
    assert 'int(probe_record["m_star"])' in source
    # ...and it is the same value Gate 2 froze, asserted rather than assumed.
    assert 'if m_star != int(gate2_record["m_star"]):' in source
    assert "calibration_at(" in source
    kernel = inspect.getsource(feasibility.calibration_at)
    assert "calibration_rows_at(gate2_record, m_star=m_star" in kernel
    assert "qualification_at(gate2_5_record, m_star=m_star)" in kernel
    # Gate 3B and Gate 3C both carry m* forward from the record above them.
    assert 'gate3a_record["m_star"]' in inspect.getsource(
        gates_run.gate3b_payload)
    assert 'int(gate3b_record["m_star"])' in inspect.getsource(
        gates_run.gate3c_payload)
    # And the freeze binds B at the probe's m*, which `effective_m_star` and
    # `assert_m_star_unmoved` have both already checked equals Gate 2's.
    freeze = " ".join(inspect.getsource(freeze_run.assemble).split())
    assert 'm_star=probe["m_star"]' in freeze
    assert '"m_star_is_unchanged": probe["m_star_is_unchanged"]' in freeze


def test_a_quantity_from_another_operating_point_is_refused_not_reused():
    """The refusal is the invariant; a fallback would be the defect."""
    gate2 = {"m_star": 8, "calibration_rows": {"pooled": []},
             "kappa_under_b_by_severity": {"8": {"pooled": {}}}}
    with pytest.raises(ProtocolError, match="no kappa\\(R\\|B\\) column"):
        feasibility.calibration_rows_at(gate2, m_star=10, split="pooled")
    with pytest.raises(ProtocolError, match="recorded no qualified pool"):
        feasibility.qualification_at(
            {"qualification_by_severity": {"8": {}}}, m_star=10)


# ---- 3. A registered support failure cannot reopen library development.

def test_no_stage_after_the_screen_can_run_the_expansion():
    """§12.6 spends its rounds once, at the screen, and the vocabulary is
    frozen there. A support failure downstream is §34 D6's question."""
    from dci1v7.run import regime_run

    callers = []
    for module in (gates_run, freeze_run):
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = getattr(fn, "attr", getattr(fn, "id", None))
                if name in ("run_expansion", "expansion_round",
                            "expansion_plan_for_family"):
                    callers.append((module.__name__, name))
    assert callers == []
    # The one legitimate caller is the screen itself.
    assert "run_expansion(" in inspect.getsource(regime_run.regime_payload)


def test_the_lifecycle_is_linear_and_write_once():
    """There is no transition back to an earlier stage, so no downstream
    verdict can re-open one."""
    for index, stage in enumerate(C.STAGE_SEQUENCE):
        expected = C.STAGE_SEQUENCE[index - 1] if index else None
        assert transitions.PREDECESSOR[stage] == expected
    assert len(set(C.STAGE_SEQUENCE)) == len(C.STAGE_SEQUENCE)


def test_the_calibrated_coverage_failure_takes_the_registered_disposition():
    """It is §12.6's own criterion, so it is §34 D6's consequence --- not a
    new status, and not a route back to the library."""
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in \
        feasibility.CALIBRATED_COVERAGE_FAILURE
    source = inspect.getsource(feasibility.coverage_at_calibrated_iota_a)
    assert "TerminalStatus" not in source
    assert "raise" not in source


# ---- 4. The freeze needs both conditions, on one replication.

def test_the_freeze_is_downstream_of_both_support_and_the_contrast_record():
    order = C.STAGE_SEQUENCE
    assert order.index(C.STAGE_GATE3C) < order.index(C.STAGE_GATE4) \
        < order.index(C.STAGE_PREFREEZE_AUDIT) < order.index(C.STAGE_GATE5)
    # Each stage's predecessor must have recorded PASS, so reaching the
    # freeze means both gates passed on this tree.
    assert transitions.PREDECESSOR[C.STAGE_GATE5] == C.STAGE_PREFREEZE_AUDIT
    assert transitions.PREDECESSOR[C.STAGE_PREFREEZE_AUDIT] == C.STAGE_GATE4
    assert transitions.PREDECESSOR[C.STAGE_GATE4] == C.STAGE_GATE3C


def test_gate4_evaluates_every_slot_of_every_registered_cell_type():
    """"Full slot" is derived from the admitted arms, never hard-coded, so a
    slot that can fail at Gate 4 cannot be absent from the table."""
    from dci1v7.design.cells import cell_types, normalise_arms

    arms = normalise_arms(C.ARMS)
    shape = gates_run.composed_table_shape(arms)
    assert set(shape) == {t.cell_id for t in cell_types(arms)}
    for t in cell_types(arms):
        assert shape[t.cell_id] == t.slots
    # A table missing one entry is refused rather than recorded as complete.
    complete = {cell: {s: 0.5 for s in slots} or {"unconstrained": 1.0}
                for cell, slots in shape.items()}
    gates_run.assert_composed_table_complete(complete, arms)
    complete.pop("solo:R1")
    with pytest.raises(ProtocolError, match="missing cell type"):
        gates_run.assert_composed_table_complete(complete, arms)


def test_gate4_records_a_contrast_terminates_nothing_and_substitutes_nothing():
    """v7 A1: no terminal branch exists in the Gate-4 runner, and the
    projection is what it records."""
    source = inspect.getsource(gates_run.gate4_payload)
    assert "TerminalStatus" not in source
    assert "COMPOSED_HEADROOM_FAILURE" not in source
    assert "composed_contrast.projection(" in source
    assert gates_run.assert_no_substitution_path()["found"] == []
    assert C.BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4 is False
