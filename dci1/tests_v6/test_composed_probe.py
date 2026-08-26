"""§18 stage 8: ``GATE_2_75_COMPOSED_PROBE`` --- the rule, and its guards.

Two things are under test and they are not the same. The **rule** is P3.1 to
P3.6: which severities are probed, what passing the margin means, when m* is
re-selected, and when the replication terminates. The **guards** are the four
independent reasons a probed cell can never be a B+R cell and the audit that
would notice if one stopped holding.

What is deliberately *not* under test is any value §34 D20, D23 or D24
selects: the topic split, the margin and the stand-ins are open researcher
decisions, every accessor refuses while they are, and a test that supplied one
would be choosing.
"""
from __future__ import annotations

import dataclasses
import math

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v6.analysis import claims
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions
from dci1v6.run import gates_run
from dci1v6.run.lifecycle import TerminalStatus, terminal_statuses_in_force
from dci1v6.stages import audit_prefreeze, composed_probe as P
from dci1v6.stages import feasibility, regime
from dci1v6.verifiers import constraints as K

#: A residual allowance that reproduces the old fixed margin band exactly for
#: a **zero-variance** determinate entry: [0.05 + 0.05, 0.95 - 0.05]. Used so
#: that a test about P3.3 to P3.6 is about the disposition rule and not about
#: the projection, which has its own tests below.
RESIDUAL = 0.05
GATE2_CURVE = {7: 0.94, 8: 0.90, 9: 0.86, 10: 0.81, 11: 0.76, 12: 0.70,
               13: 0.64, 14: 0.58}


def _m(value: float, s2: float = 0.0, n: int = 192) -> dict:
    """One entry's measurement, in the shape ``severity_verdict`` reads."""
    return {"compliance": value, "s2_topic": s2, "n_topics": n}


def _table(b_solo: float, standin_solo: float = 0.5,
           composed_b: float | None = None, a_solo: float = 0.6,
           a_with_b: float | None = None, s2: float = 0.0) -> dict:
    """One severity's probed table, over the classes the verdict evaluates.

    ``solo:A``, ``solo:B`` and both orders of ``pair:A+B`` are **determinate**
    --- every constituent is a real registered instrument --- and gate through
    the projected interval. Everything containing a stand-in gates against
    §13.14's registered band with no margin.
    """
    composed = b_solo if composed_b is None else composed_b
    ab = b_solo if a_with_b is None else a_with_b
    return {
        "unconstrained": {"unconstrained": _m(24.0)},
        "solo:A": {"A": _m(a_solo, s2)},
        "solo:B": {"B": _m(b_solo, s2)},
        "pair:A+B": {"A": _m(a_solo, s2), "B": _m(ab, s2)},
        "pair:B+A": {"A": _m(a_solo, s2), "B": _m(ab, s2)},
        "solo:P1": {"P1": _m(standin_solo)},
        "pair:B+P1": {"B": _m(composed), "P1": _m(standin_solo)},
        "pair:P1+B": {"B": _m(composed), "P1": _m(standin_solo)},
    }


# ------------------------------------------------------- placement and shape

def test_the_probe_is_the_stage_between_gate_2_5_and_gate_3a():
    order = list(C.STAGE_SEQUENCE)
    assert order.index(C.STAGE_GATE2_75) == order.index(C.STAGE_GATE2_5) + 1
    assert order.index(C.STAGE_GATE3A) == order.index(C.STAGE_GATE2_75) + 1
    assert C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE2_75] == "calibration_record"
    assert C.STAGE_GATE2_75 in C.GENERATION_STAGES
    assert "composed_probe" in C.VERIFIER_BOUND_ENTRY_POINTS


def test_the_cell_shape_covers_every_gate4_exposure_class():
    """The probe's scope is derived from Gate 4's own cell set, not listed.

    §13.14 audits 95 cell x slot entries falling into ten slot-and-order
    classes. A hand-written probe shape is how the first version came to
    protect one slot while believing it protected the design, so the
    completeness check reads `design.cells.cell_types` and refuses a shape
    that leaves a class uncovered.
    """
    slots = P.probe_slots(3)
    shape = P.probe_cell_types(slots)
    ids = [cell_id for cell_id, _arm, _slots in shape]
    assert ids == ["unconstrained", "solo:A", "solo:B",
                   "solo:P1", "solo:P2", "solo:P3",
                   "pair:A+B", "pair:B+A",
                   "pair:B+P1", "pair:P1+B", "pair:B+P2", "pair:P2+B",
                   "pair:B+P3", "pair:P3+B",
                   "pair:A+P1", "pair:P1+A", "pair:P1+P2", "pair:P2+P1"]
    audit = P.assert_probe_covers_gate4_classes(slots)
    assert audit["gate4_entries"] == 95
    coverage = audit["coverage"]
    assert sum(1 for e in coverage.values() if e["roles"]) == 10
    assert all(e["covered"] for e in coverage.values())
    assert sorted(audit["determinate_classes"]) == [
        "composed:focal+target", "composed:target+focal",
        "solo:focal", "solo:target"]


def test_a_shape_that_leaves_a_gate4_class_uncovered_is_refused():
    """The old shape --- B solo, stand-in solo, both orders of B with a
    stand-in --- leaves six of the ten classes unmeasured, including the one
    `gemma-3n-e4b-it` terminated in."""
    old = [("unconstrained", "unconstrained", ()),
           ("solo:B", "solo", ("B",)),
           ("solo:P1", "solo", ("P1",)),
           ("pair:B+P1", "composed", ("B", "P1")),
           ("pair:P1+B", "composed", ("P1", "B"))]
    coverage = {}
    for key, gate4_cells in P.gate4_exposure_classes().items():
        arm, roles = key
        name = f"{arm}:{'+'.join(roles)}" if roles else arm
        covering = [cid for cid, cell_arm, cell_slots in old
                    if cell_arm == arm
                    and tuple(P.slot_role(x) for x in cell_slots) == roles]
        coverage[name] = bool(covering)
    assert coverage["solo:companion"] is True
    assert coverage["solo:target"] is False
    assert coverage["composed:target+focal"] is False
    assert coverage["composed:companion+companion"] is False
    assert sum(1 for name, ok in coverage.items()
               if not ok and name != "unconstrained") == 6


def test_a_probe_slot_is_not_a_registered_design_slot():
    """A stand-in has no slot in the confirmatory design, so there is no name
    a probe cell and a design cell could share."""
    assert not set(P.PROBE_SLOTS) & set(C.REGISTERED_SLOT_ORDER)
    with pytest.raises(ProtocolError):
        P.probe_cell_types(("R1",))
    with pytest.raises(ProtocolError):
        P.probe_slots(4)


# ------------------------------------------------------------ P3.1 and P3.2

def test_the_probed_set_is_the_one_gate_2_recorded_as_admissible():
    record = {"focal_selection": {"eligible": [9, 10, 11]},
              "focal_admissible": [9, 10, 11]}
    P.assert_probe_severities_are_admissible([10, 9], record)
    with pytest.raises(ProtocolError) as excinfo:
        P.assert_probe_severities_are_admissible([10, 13], record)
    assert "13" in str(excinfo.value)


def test_an_eligible_severity_that_is_not_admissible_may_not_be_probed():
    """§12.3's band is not §12.4's adequacy and not §34 D17's floor.

    Gate 2 applies the second and third **at m\\*** and terminates the
    replication when either fails. Every other eligible severity has passed
    only the band test, so a probe that re-selected over `eligible` could move
    B to an operating point Gate 2 would have refused outright.
    """
    record = {"focal_selection": {"eligible": [9, 10, 11]},
              "focal_admissible": [9, 10]}
    P.assert_probe_severities_are_admissible([10, 9], record)
    with pytest.raises(ProtocolError) as excinfo:
        P.assert_probe_severities_are_admissible([10, 11], record)
    assert "11" in str(excinfo.value) and "§12.4" in str(excinfo.value)


def test_a_record_without_the_admissible_set_is_refused_not_defaulted():
    """Falling back to `eligible` is the defect, so absence must fail."""
    with pytest.raises(ProtocolError) as excinfo:
        P.assert_probe_severities_are_admissible(
            [10], {"focal_selection": {"eligible": [9, 10, 11]}})
    assert "focal_admissible" in str(excinfo.value)


def test_a_severity_passes_only_when_every_entry_passes_its_own_test():
    inside = P.severity_verdict(_table(0.80), residual_sd=RESIDUAL)
    assert inside["passes"] and inside["failures"] == []
    # solo:A, solo:B, both orders of A+B (two slots each), solo:P1, and both
    # orders of B+P1 (two slots each).
    assert inside["n_entries_evaluated"] == 11
    assert inside["n_determinate_entries"] == 6
    assert inside["n_standin_dependent_entries"] == 5
    # A determinate entry whose projected interval leaves the band fails.
    over = P.severity_verdict(_table(0.80, a_with_b=0.93), residual_sd=RESIDUAL)
    assert not over["passes"]
    assert {f["cell"] for f in over["failures"]} == {"pair:A+B", "pair:B+A"}
    assert all(f["slot"] == "B" and f["determinate"] for f in over["failures"])


def test_a_stand_in_dependent_entry_carries_no_margin_at_all():
    """A stand-in is not the reference, so a projection from it would be a
    projection of the wrong instrument. It gates on §13.14's band itself."""
    low, high = C.COMPOSED_HEADROOM_BAND
    # 0.93 is outside the residual-contracted band and inside the registered
    # one. A determinate entry there fails; a stand-in-dependent one passes.
    near = P.severity_verdict(_table(0.80, composed_b=0.93),
                              residual_sd=RESIDUAL)
    assert near["passes"]
    assert near["standin_findings"] == []
    assert all(e["half_width"] == 0.0 for e in near["entries"]
               if not e["determinate"])
    # Outside the REGISTERED band it is a finding --- a real composed cell of
    # a real instrument beside one that is not the reference --- and under
    # focal-only reselection a finding is recorded and gates nothing.
    out = P.severity_verdict(_table(0.80, composed_b=0.97),
                             residual_sd=RESIDUAL)
    assert out["passes"], "a stand-in may not make a severity inadmissible"
    assert out["failures"] == []
    assert out["all_entries_inside_their_test"] is False
    found = out["standin_findings"]
    assert {f["cell"] for f in found} == {"pair:B+P1", "pair:P1+B"}
    assert all(f["band"] == [low, high] for f in found)
    assert out["standin_findings_gate_nothing"] is True


def test_the_projection_is_section_13_4s_device_on_section_13_14s_band():
    """Three terms and no fourth, and the band itself is never moved."""
    low, high = C.COMPOSED_HEADROOM_BAND
    verdict = P.severity_verdict(_table(0.80, s2=0.09), residual_sd=0.0)
    assert verdict["registered_band"] == [low, high]
    assert verdict["band_is_unchanged"] is True
    entry = next(e for e in verdict["entries"] if e["cell"] == "solo:B")
    expected = 1.959963984540054 * math.sqrt(0.09 / C.N_COMPOSED
                                             + 0.09 / 192 + 0.0)
    assert entry["half_width"] == pytest.approx(expected, rel=1e-12)
    assert entry["projected_low"] == pytest.approx(0.80 - expected)
    assert entry["projected_high"] == pytest.approx(0.80 + expected)
    # Gate 4's own sample size dominates: 24 topics against the probe's 192.
    assert (P.projected_halfwidth(0.09, n_probe=192, n_composed=96,
                                  residual_sd=0.0)
            < P.projected_halfwidth(0.09, n_probe=192, n_composed=24,
                                    residual_sd=0.0))
    # And more variance, or a family-wise correction, only ever widens it.
    assert (P.projected_halfwidth(0.16, n_probe=192)
            > P.projected_halfwidth(0.09, n_probe=192))
    assert (P.projected_halfwidth(0.09, n_probe=192, k=6)
            > P.projected_halfwidth(0.09, n_probe=192, k=1))


def test_the_familywise_reading_is_recorded_beside_every_determinate_entry():
    """§13.14's verdict is a conjunction, so the Bonferroni reading belongs on
    the artifact even though the criterion is §13.4's per-entry convention."""
    verdict = P.severity_verdict(_table(0.80, s2=0.09), residual_sd=0.0)
    assert verdict["level_k"] == 1
    assert verdict["familywise_k"] == P.N_DETERMINATE_ENTRIES == 6
    for entry in verdict["entries"]:
        if entry["determinate"]:
            assert entry["half_width_familywise"] > entry["half_width"]
        else:
            assert "half_width_familywise" not in entry
    assert {f["cell"] for f in verdict["would_fail_familywise"]} <= {
        "solo:A", "solo:B", "pair:A+B", "pair:B+A"}


def test_the_residual_allowance_matches_the_measurement_it_is_derived_from():
    """`RESIDUAL_SD` is not a chosen constant: it is half the measured
    calibration_a-vs-calibration_b residual, because §6.2 cuts calibration_a
    and the composed set from one seeded shuffle and §34 D3's calibration_b
    is newly authored."""
    import json
    from pathlib import Path as _P

    report = json.loads(
        (_P(__file__).resolve().parents[1] / "reports" / "dci1v6"
         / "precision_design.json").read_text())
    measured = report["authored_subsplit"]["carried_by_a_pooled_probe"]["sd"]
    assert P.RESIDUAL_SD == pytest.approx(measured, abs=5e-5)
    assert report["split_transfer"]["residual_point_estimate"] <= 0.0


# --------------------------------------------------- P3.3, P3.4, P3.5, P3.6

def test_p3_3_a_passing_m_star_stands_and_nothing_is_reselected():
    out = P.probe_disposition(m_star=10, probed={10: _table(0.81)},
                              gate2_solo_curve=GATE2_CURVE,
                              residual_sd=RESIDUAL)
    assert out["reselected"] is False
    assert out["m_star_out"] == 10
    assert out["reselections_permitted"] == 1


def test_p3_4_a_failing_m_star_reselects_once_over_gate_2s_own_curve():
    """The probe decides which severities are ADMISSIBLE, never which is
    chosen: the selection input is Gate 2's already-measured solo curve.

    Here m* = 8 fails and 11, 12 and 13 pass. ``select_operating_point`` runs
    unchanged --- FOCAL_BAND, FOCAL_AIM = 0.80, prefer_smaller --- so it takes
    11 at 0.76, the passing severity nearest the aim.
    """
    probed = {8: _table(0.90, a_with_b=0.97), 11: _table(0.76),
              12: _table(0.70), 13: _table(0.64)}
    out = P.probe_disposition(m_star=8, probed=probed,
                              gate2_solo_curve=GATE2_CURVE,
                              residual_sd=RESIDUAL)
    assert out["reselected"] is True
    assert out["passing_severities"] == [11, 12, 13]
    assert out["m_star_out"] == 11
    assert out["selection_input"] == \
        "GATE_2_FOCAL_CALIBRATION's solo B curve"
    # Unchanged rule: the same function Gate 2 used, on the same curve.
    direct = regime.select_operating_point(
        {m: GATE2_CURVE[m] for m in (11, 12, 13)}, band=C.FOCAL_BAND,
        aim=C.FOCAL_AIM, prefer_smaller=True, grid=(11, 12, 13))
    assert direct["selected"] == out["m_star_out"]


def test_p3_6_no_admissible_severity_terminates_the_replication(
        restore_decisions):
    """A repair loop with no terminal outcome is not a rule."""
    restore_decisions.override_for_testing("D6", "identification_status")
    probed = {m: _table(0.90, a_with_b=0.97) for m in (9, 10, 11)}
    with pytest.raises(TerminalStatus) as excinfo:
        P.probe_disposition(m_star=10, probed=probed,
                            gate2_solo_curve=GATE2_CURVE,
                            residual_sd=RESIDUAL)
    raised = excinfo.value
    assert raised.status == P.COMPOSED_HEADROOM_UNREACHABLE
    assert raised.gate == C.STAGE_GATE2_75
    assert raised.strongest_permissible_statement == C.TERMINAL_SENTENCE
    # §13.14's band is named in the criterion and is unchanged.
    assert str(list(C.COMPOSED_HEADROOM_BAND)) in raised.criterion


def test_m_star_must_be_probed_first():
    with pytest.raises(ProtocolError):
        P.probe_disposition(m_star=10, probed={11: _table(0.76)},
                            gate2_solo_curve=GATE2_CURVE,
                            residual_sd=RESIDUAL)


def test_the_terminal_status_is_registered_and_raisable():
    assert P.COMPOSED_HEADROOM_UNREACHABLE in C.TERMINAL_STATUSES
    assert P.COMPOSED_HEADROOM_UNREACHABLE in C.NEW_TERMINAL_STATUSES
    assert P.COMPOSED_HEADROOM_UNREACHABLE in terminal_statuses_in_force()
    raised = TerminalStatus(
        P.COMPOSED_HEADROOM_UNREACHABLE, gate=C.STAGE_GATE2_75,
        criterion="x", observed=None, strongest_permissible_statement="x")
    assert raised.status == P.COMPOSED_HEADROOM_UNREACHABLE


# ------------------------------------------------- the four B+R guarantees

def test_guarantee_1_the_probe_runs_before_any_reference_exists():
    """Temporal. Gate 3B has not run, so there is no R to compose."""
    from dci1v6.engine.transitions import PREDECESSOR

    order = list(C.STAGE_SEQUENCE)
    assert PREDECESSOR[C.STAGE_GATE2_75] == C.STAGE_GATE2_5
    assert order.index(C.STAGE_GATE2_75) < order.index(C.STAGE_GATE3B)


def test_guarantee_2_a_standin_is_refused_everywhere_a_candidate_is_chosen(
        monkeypatch):
    """Structural. A ``probe_only`` family is not in the selectable pool, so
    no probed cell can be a B+R cell even by coincidence of identity."""
    standin = dataclasses.replace(K.FAMILIES["MK1"], probe_only=True)
    families = {**K.FAMILIES, "MK1": standin}
    monkeypatch.setattr(K, "FAMILIES", families)
    monkeypatch.setattr(regime, "FAMILIES", families)
    # §13.15's structural-eligibility read moved with the criterion into
    # `stages/feasibility`, so that is where the family table is now read.
    monkeypatch.setattr(feasibility, "FAMILIES", families)
    assert K.is_probe_only("MK1")

    with pytest.raises(K.InstrumentError):
        regime.carry_candidate(
            kind="MK1", severity=3, prescreen_solo_compliance=0.5,
            n_prescreen_topics=24,
            structural=regime.StructuralScreen())
    with pytest.raises(K.InstrumentError):
        gates_run.slot_map_from_record({"slot_map": {"R1": ["MK1", 3]}})
    # And nothing exists that could promote one.
    assert K.assert_no_probe_only_selection_path()["found"] == []


def test_guarantee_3_the_probe_record_is_name_scanned_like_gate_4s():
    """Informational. Without this the probe would be the one generating
    stage whose record no §33 check reads."""
    assert C.STAGE_GATE2_75 in audit_prefreeze.NAME_SCANNED_RECORDS
    probe = {"outcome": "PASS", "m_star": 11, "reselected": False,
             audit_prefreeze.DECLARED_REFUSALS_KEY:
                 dict(P.PROBE_DECLARED_REFUSALS)}
    gate4 = {"outcome": "PASS",
             audit_prefreeze.DECLARED_REFUSALS_KEY: {
                 "no_substitution_after_failure": "x",
                 "no_selection_here": "x"}}
    assert audit_prefreeze._check_8(gate4, probe)[0] == "PASS"

    # Deleting the declared refusals fails the check.
    stripped = {k: v for k, v in probe.items()
                if k != audit_prefreeze.DECLARED_REFUSALS_KEY}
    assert audit_prefreeze._check_8(gate4, stripped)[0] == "FAIL"
    # A field that NAMES a selection fails it too.
    named = {**probe, "reselect_reference": "R2"}
    assert audit_prefreeze._check_8(gate4, named)[0] == "FAIL"
    # `widen` is another of §13.14's five tokens, and the exemption is one
    # named field rather than a pattern.
    assert audit_prefreeze._check_8(gate4, {**probe, "widen_band": True})[0] \
        == "FAIL"
    # A missing probe record is UNRESOLVED, which blocks the freeze: "we did
    # not establish this" is not "this is true".
    assert audit_prefreeze._check_8(gate4, None)[0] == "UNRESOLVED"


def test_guarantee_4_no_function_here_reads_a_selection_record():
    """Directional. The one value this stage writes that a later stage reads
    is m*, and m* is B's own severity."""
    report = P.assert_probe_reads_no_reference()
    assert report["found"] == []
    assert report["source_reads_no_selection_stage"] is True
    with pytest.raises(ProtocolError):
        P.assert_probe_reads_no_reference(
            {"load_reference_pool": lambda: None})


def test_the_one_name_scan_exemption_is_registered_and_must_be_exercised():
    """The scan found the probe's own `reselected` field, and that is the
    check working rather than a nuisance.

    P3.3 and P3.4 require the record to say whether m* was re-selected, and
    `reselect` is one of §13.14's five forbidden tokens: an outcome-driven
    selection and a registered pre-data one read identically to a name scan.
    So the exemption is **one named field with a stated reason**, it must
    actually be present, and the record must still declare that no second
    re-selection exists.
    """
    spec = audit_prefreeze.NAME_SCANNED_RECORDS[C.STAGE_GATE2_75]
    assert set(spec["permitted_fields"]) == {"reselected"}
    assert "OUTCOME-driven" in spec["permitted_fields"]["reselected"]
    assert audit_prefreeze.NAME_SCANNED_RECORDS[
        "GATE_4_COMPOSED_HEADROOM"]["permitted_fields"] == {}
    gate4 = {"outcome": "PASS",
             audit_prefreeze.DECLARED_REFUSALS_KEY: {
                 "no_substitution_after_failure": "x",
                 "no_selection_here": "x"}}
    # An exemption for a field nobody writes is an exemption nobody exercises.
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
    assert any("band_not_relaxed" == k for k in keys)


def test_the_scope_limits_are_on_the_record_not_discovered_at_gate_4():
    """READINESS §3.2: the probe protects the B slot only, and Change 1
    succeeding raises Gate-4 exposure. Both are registered expectations."""
    text = " ".join(P.PROBE_SCOPE_LIMITS)
    # The limit is no longer "one slot": it is the companion's IDENTITY, and
    # the record has to say which of the two it is.
    assert "identity" in text
    assert "no margin" in text
    assert "95" in text
    assert "0.12 to 0.19" in text


# ------------------------------------------ the decisions it fails closed on

@pytest.mark.parametrize("accessor,decision_id",
                         [("probe_split", "D20"),
                          ("residual_reading", "D23"),
                          ("residual_allowance", "D26"),
                          ("standins", "D24")])
def test_every_open_decision_refuses_rather_than_defaulting(
        accessor, decision_id, restore_decisions):
    """No caller gets a default and no stage runs while one is open."""
    restore_decisions.reopen_all_for_testing()
    assert decision_id in decisions.open_decisions()
    with pytest.raises(decisions.DecisionOpenError):
        getattr(P, accessor)()
    assert decision_id in decisions.decisions_blocking_stage(C.STAGE_GATE2_75)


def test_the_registered_standins_are_the_probe_only_families(
        restore_decisions):
    """§34 D24 at `probe_only_in_library` selects the authored population."""
    restore_decisions.override_for_testing("D24", "probe_only_in_library")
    assert P.standins() == ("PS1", "PS2", "PS3")
    assert P.PROBE_ONLY_KINDS() == K.PROBE_ONLY_FAMILY_IDS


def test_the_separate_vocabulary_branch_has_no_instruments_and_refuses(
        restore_decisions):
    """The other branch is coded and reachable, and it yields nothing here:
    a separate frozen probe vocabulary is not in this library, so a closure
    there fails loudly rather than running the probe with no companion."""
    restore_decisions.override_for_testing("D24", "separate_vocabulary")
    with pytest.raises(ProtocolError) as excinfo:
        P.standins()
    assert "D24" in str(excinfo.value)


def test_a_magnitude_that_leaves_no_interior_is_refused_at_closure(
        restore_decisions):
    """§34 D26 carries an `admissible_range`, so an out-of-range value is
    refused when the researcher writes it and not five stages later, at the
    one place it would have signed a manifest first."""
    restore_decisions.reopen_all_for_testing()
    with pytest.raises(ProtocolError) as excinfo:
        decisions.close("D26", 0.50, evidence="e", decided_by="t",
                        decided_on="t")
    assert "0.45" in str(excinfo.value)
    with pytest.raises(ProtocolError):
        restore_decisions.override_for_testing("D26", 0.50)


def test_the_magnitude_is_a_number_and_not_a_branch_name(restore_decisions):
    restore_decisions.reopen_all_for_testing()
    with pytest.raises(ProtocolError):
        decisions.close("D26", "small", evidence="e", decided_by="t",
                        decided_on="t")


def test_the_two_residual_readings_are_different_quantities(
        restore_decisions):
    """§34 D23's defect, asserted so it cannot come back: the register said
    the allowance was BEYOND the measured sd and the code passed it in AS the
    measured sd, so 0.0 deleted the term the documents promise is carried."""
    low, high = C.COMPOSED_HEADROOM_BAND
    restore_decisions.override_for_testing("D23", "projection_sd")
    restore_decisions.override_for_testing("D26", 0.0)
    # Under this reading D26's number IS the quadrature term, so 0.0 means the
    # projection is pure sampling and 0.0142 is applied nowhere.
    assert P.projection_residual_sd() == 0.0
    assert P.margin_band() == (low, high)

    restore_decisions.reopen_all_for_testing()
    restore_decisions.override_for_testing("D23", "beyond_the_measured_sd")
    restore_decisions.override_for_testing("D26", 0.0)
    # Under the other, the measured term is always carried and D26 buys band.
    assert P.projection_residual_sd() == P.RESIDUAL_SD
    assert P.margin_band() == (low, high)

    restore_decisions.reopen_all_for_testing()
    restore_decisions.override_for_testing("D23", "beyond_the_measured_sd")
    restore_decisions.override_for_testing("D26", 0.02)
    assert P.projection_residual_sd() == P.RESIDUAL_SD
    assert P.margin_band() == (low + 0.02, high - 0.02)


def test_a_standin_can_never_make_a_severity_inadmissible(restore_decisions):
    """Focal-only reselection. The rule this replaces let an instrument that
    is non-selectable by construction choose the operating point at which
    Delta_j and Delta_R are estimated, and terminate a replication."""
    table = _table(0.80, composed_b=0.99)
    verdict = P.severity_verdict(table, residual_sd=0.0)
    assert verdict["passes"] is True
    assert verdict["standin_findings"], "the finding is still recorded"
    assert verdict["all_entries_inside_their_test"] is False
    assert verdict["admissibility_decided_by"].startswith("the six")
    # And it reaches the disposition: m* stands rather than being re-selected.
    disposition = P.probe_disposition(
        m_star=10, probed={10: table}, gate2_solo_curve={10: 0.80},
        residual_sd=0.0)
    assert disposition["reselected"] is False
    assert disposition["m_star_out"] == 10
    assert disposition["reselection_rule"] == "focal_only"
    assert disposition["standin_findings_by_severity"]["10"]


def test_a_determinate_entry_still_moves_m_star_and_can_terminate():
    """Focal-only narrows what decides; it does not stop the probe deciding.
    A determinate entry outside its projected interval is exactly what the
    stage exists to catch two stages before Gate 4."""
    from dci1v6.run.lifecycle import TerminalStatus
    bad = _table(0.80, a_with_b=0.99)
    assert not P.severity_verdict(bad, residual_sd=0.0)["passes"]
    with pytest.raises(TerminalStatus) as excinfo:
        P.probe_disposition(m_star=10, probed={10: bad},
                            gate2_solo_curve={10: 0.80}, residual_sd=0.0)
    assert excinfo.value.status == P.COMPOSED_HEADROOM_UNREACHABLE
    assert "DETERMINATE" in excinfo.value.criterion


# ------------------------------------------------------------ what it is not

def test_the_probe_measures_compliance_and_the_module_says_so():
    """The proposal called it "no outcome quantity"; that is wrong and the
    correction is load-bearing.

    The probe measures compliance --- the same kind of quantity §13.14 already
    governs. What makes it interaction-blind is narrower: it is blind to any
    reference and to any composed *contrast*.
    """
    text = " ".join((P.__doc__ or "").split())
    assert "blind to any *reference* and to any *composed contrast*" in text
    assert "no available evidence bounds the difference between a stand-in " \
           "and the reference that replaces it" in text


def test_l4a_stays_within_replication():
    """Unrelated to the probe, and checked beside it because §33 check 9 now
    carries both."""
    assert claims.CONFIGURATION_SCOPE == "within_replication"
    with pytest.raises(claims.ClaimError):
        claims.assert_configuration_scope(
            ("gemma:outcome_first", "qwen:outcome_first"))
    assert audit_prefreeze._check_9()[0] == "PASS"


def test_a_probe_record_may_not_be_written_twice(tmp_path):
    """P3.5: there is no second re-selection, and the stage machine is what
    makes that true rather than a comment."""
    from dci1v6.engine import transitions
    from dci1v6.engine.context import synthetic_context
    from dci1v6.engine.paths import model_tree
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
