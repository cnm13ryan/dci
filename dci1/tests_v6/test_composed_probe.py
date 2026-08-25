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

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v6.analysis import claims
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions
from dci1v6.run import gates_run
from dci1v6.run.lifecycle import TerminalStatus, terminal_statuses_in_force
from dci1v6.stages import audit_prefreeze, composed_probe as P
from dci1v6.stages import regime
from dci1v6.verifiers import constraints as K

BAND = (0.10, 0.90)          # a margin band, not §13.14's --- see below
GATE2_CURVE = {7: 0.94, 8: 0.90, 9: 0.86, 10: 0.81, 11: 0.76, 12: 0.70,
               13: 0.64, 14: 0.58}


def _table(b_solo: float, standin_solo: float = 0.5,
           composed_b: float | None = None) -> dict:
    """One severity's probed table, in the shape ``severity_verdict`` reads."""
    composed = b_solo if composed_b is None else composed_b
    return {
        "unconstrained": {"unconstrained": 24.0},
        "solo:B": {"B": b_solo},
        "solo:P1": {"P1": standin_solo},
        "pair:B+P1": {"B": composed, "P1": standin_solo},
        "pair:P1+B": {"B": composed, "P1": standin_solo},
    }


# ------------------------------------------------------- placement and shape

def test_the_probe_is_the_stage_between_gate_2_5_and_gate_3a():
    order = list(C.STAGE_SEQUENCE)
    assert order.index(C.STAGE_GATE2_75) == order.index(C.STAGE_GATE2_5) + 1
    assert order.index(C.STAGE_GATE3A) == order.index(C.STAGE_GATE2_75) + 1
    assert C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE2_75] == "calibration_record"
    assert C.STAGE_GATE2_75 in C.GENERATION_STAGES
    assert "composed_probe" in C.VERIFIER_BOUND_ENTRY_POINTS


def test_the_cell_shape_is_derived_and_includes_the_standin_solo_cells():
    """S4 reads each stand-in's operating point from its own solo curve.

    So the stand-in solo cells are not optional, and the composed lift is
    measured against them. Two cells plus three per stand-in.
    """
    shape = P.probe_cell_types(P.probe_slots(3))
    ids = [cell_id for cell_id, _arm, _slots in shape]
    assert ids == ["unconstrained", "solo:B", "solo:P1", "solo:P2", "solo:P3",
                   "pair:B+P1", "pair:P1+B", "pair:B+P2", "pair:P2+B",
                   "pair:B+P3", "pair:P3+B"]
    assert len(shape) == 2 + 3 * 3
    # Stand-ins are never paired with each other: the quantity is the lift on
    # B, and a stand-in pair would measure something no rule reads.
    pairs = [slots for _id, arm, slots in shape if arm == "composed"]
    assert all("B" in slots for slots in pairs)


def test_a_probe_slot_is_not_a_registered_design_slot():
    """A stand-in has no slot in the confirmatory design, so there is no name
    a probe cell and a design cell could share."""
    assert not set(P.PROBE_SLOTS) & set(C.REGISTERED_SLOT_ORDER)
    with pytest.raises(ProtocolError):
        P.probe_cell_types(("R1",))
    with pytest.raises(ProtocolError):
        P.probe_slots(4)


# ------------------------------------------------------------ P3.1 and P3.2

def test_the_probed_set_is_the_one_gate_2_recorded_as_eligible():
    record = {"focal_selection": {"eligible": [9, 10, 11]}}
    P.assert_probe_severities_are_gate2_eligible([10, 9], record)
    with pytest.raises(ProtocolError) as excinfo:
        P.assert_probe_severities_are_gate2_eligible([10, 13], record)
    assert "13" in str(excinfo.value)


def test_a_severity_passes_only_when_every_cell_and_every_slot_is_inside():
    inside = P.severity_verdict(_table(0.80), band=BAND)
    assert inside["passes"] and inside["failures"] == []
    # One slot of one cell over the margin is enough to fail the severity.
    over = P.severity_verdict(_table(0.80, composed_b=0.93), band=BAND)
    assert not over["passes"]
    assert {f["cell"] for f in over["failures"]} == {"pair:B+P1", "pair:P1+B"}
    assert all(f["slot"] == "B" for f in over["failures"])
    # The unconstrained cell carries no constraint and is recorded, not
    # evaluated.
    assert inside["n_cells_evaluated"] == 4


def test_the_margin_band_is_strictly_inside_the_registered_band():
    """delta is a margin INSIDE §13.14's band, never a change to it."""
    low, high = C.COMPOSED_HEADROOM_BAND
    verdict = P.severity_verdict(_table(0.80), band=BAND)
    assert verdict["registered_band"] == [low, high]
    assert low <= BAND[0] and BAND[1] <= high


# --------------------------------------------------- P3.3, P3.4, P3.5, P3.6

def test_p3_3_a_passing_m_star_stands_and_nothing_is_reselected():
    out = P.probe_disposition(m_star=10, probed={10: _table(0.81)},
                              gate2_solo_curve=GATE2_CURVE, band=BAND)
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
    probed = {8: _table(0.90, composed_b=0.97), 11: _table(0.76),
              12: _table(0.70), 13: _table(0.64)}
    out = P.probe_disposition(m_star=8, probed=probed,
                              gate2_solo_curve=GATE2_CURVE, band=BAND)
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
    probed = {m: _table(0.90, composed_b=0.97) for m in (9, 10, 11)}
    with pytest.raises(TerminalStatus) as excinfo:
        P.probe_disposition(m_star=10, probed=probed,
                            gate2_solo_curve=GATE2_CURVE, band=BAND)
    raised = excinfo.value
    assert raised.status == P.COMPOSED_HEADROOM_UNREACHABLE
    assert raised.gate == C.STAGE_GATE2_75
    assert raised.strongest_permissible_statement == C.TERMINAL_SENTENCE
    # §13.14's band is named in the criterion and is unchanged.
    assert str(list(C.COMPOSED_HEADROOM_BAND)) in raised.criterion


def test_m_star_must_be_probed_first():
    with pytest.raises(ProtocolError):
        P.probe_disposition(m_star=10, probed={11: _table(0.76)},
                            gate2_solo_curve=GATE2_CURVE, band=BAND)


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
    monkeypatch.setattr(gates_run, "FAMILIES", families)
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
    assert "B slot only" in text
    assert "gemma-3n-e4b-it" in text
    assert "95" in text


# ------------------------------------------ the decisions it fails closed on

@pytest.mark.parametrize("accessor,decision_id",
                         [("probe_split", "D20"), ("margin", "D23"),
                          ("standins", "D24")])
def test_every_open_decision_refuses_rather_than_defaulting(
        accessor, decision_id, restore_decisions):
    """No caller gets a default and no stage runs while one is open."""
    restore_decisions.reopen_all_for_testing()
    assert decision_id in decisions.open_decisions()
    with pytest.raises(decisions.DecisionOpenError):
        getattr(P, accessor)()
    assert decision_id in decisions.decisions_blocking_stage(C.STAGE_GATE2_75)


def test_no_standin_is_registered_and_the_probe_says_so(restore_decisions):
    """§34 D24 closed does not conjure an instrument.

    Which stand-ins exist is the researcher's, and authoring one changes
    ``assert_library_sizes``' counts --- which is the visibility R6 asks for.
    """
    restore_decisions.override_for_testing("D24", "probe_only_in_library")
    assert K.PROBE_ONLY_FAMILY_IDS == ()
    with pytest.raises(ProtocolError) as excinfo:
        P.standins()
    assert "D24" in str(excinfo.value)


def test_a_margin_that_leaves_no_interior_is_refused(restore_decisions):
    restore_decisions.override_for_testing("D23", 0.50)
    with pytest.raises(ProtocolError):
        P.margin()


def test_the_margin_is_a_number_and_not_a_branch_name(restore_decisions):
    restore_decisions.override_for_testing("D23", "small")
    with pytest.raises(ProtocolError):
        P.margin()


# ------------------------------------------------------------ what it is not

def test_the_probe_measures_compliance_and_the_module_says_so():
    """The proposal called it "no outcome quantity"; that is wrong and the
    correction is load-bearing.

    The probe measures compliance --- the same kind of quantity §13.14 already
    governs. What makes it interaction-blind is narrower: it is blind to any
    reference and to any composed *contrast*.
    """
    text = " ".join((P.__doc__ or "").split())
    assert "It is *not* free of outcomes and this module never says it is" \
        in text
    assert "blind to any *reference* and to any *composed contrast*" in text


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
