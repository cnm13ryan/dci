"""§34 D17: the construct-strength interface, with no invented threshold."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.stages import construct_strength as CS
from dci1v5.stages import regime

CURVE = {m: min(0.99, 0.05 + 0.07 * m) for m in C.FOCAL_GRID}


def test_every_quantity_declares_its_direction_and_provenance():
    for quantity in CS.QUANTITIES:
        assert quantity.direction in ("higher_is_stronger",
                                      "lower_is_stronger")
        assert quantity.formula and quantity.provenance


def test_the_report_carries_m_star_its_neighbours_and_the_whole_curve():
    report = CS.measure(CURVE, m_star=11)
    assert report["m_star"] == 11
    assert set(report["neighbours"]) == {"10", "12"}
    assert len(report["curve"]) == len(CURVE)
    assert report["at_m_star"]["quantities"]["chance_bite"]["value"] == \
        pytest.approx(1 - CURVE[11])
    assert report["red_team"] == "R14"


def test_the_grid_boundary_is_a_status():
    assert CS.grid_boundary_status(max(C.FOCAL_EXTENSION)) == [
        "OPERATING_POINT_AT_GRID_BOUNDARY"]
    assert CS.grid_boundary_status(11) == []


def test_the_floor_check_refuses_while_d17_is_open():
    with pytest.raises(decisions.DecisionOpenError):
        regime.assert_construct_floor(11, chance_compliance_at_m_star=0.4)


def test_no_floor_reports_and_refuses_nothing(restore_decisions):
    restore_decisions.close("D17", "no_floor", evidence="t", decided_by="t",
                            decided_on="t")
    out = regime.assert_construct_floor(11, chance_compliance_at_m_star=0.4,
                                        curve=CURVE)
    assert out["floor_registered"] is False
    assert out["selection_refused"] is False
    assert "whole curve" in out["reported"]


def test_the_floor_branch_refuses_without_a_derivation(restore_decisions):
    """A floor with no derivation is a threshold nobody chose."""
    restore_decisions.close("D17", "floor", evidence="t", decided_by="t",
                            decided_on="t")
    with pytest.raises(ProtocolError, match="does not invent one"):
        regime.assert_construct_floor(11, chance_compliance_at_m_star=0.4,
                                      curve=CURVE)


def test_a_registered_floor_can_refuse_a_selection(restore_decisions):
    restore_decisions.close("D17", "floor", evidence="t", decided_by="t",
                            decided_on="t")
    spec = CS.FloorSpec(quantity="chance_bite", value=0.40,
                        derivation="a researcher's derivation would go here",
                        decided_by="test", decided_on="2026-08-22")
    low = min(C.FOCAL_GRID)
    strong = regime.assert_construct_floor(
        low, chance_compliance_at_m_star=CURVE[low], curve=CURVE, floor=spec)
    assert strong["satisfied"] and not strong["selection_refused"]
    weak = regime.assert_construct_floor(
        14, chance_compliance_at_m_star=0.96, curve={**CURVE, 14: 0.96},
        floor=spec)
    assert not weak["satisfied"]
    assert weak["selection_refused"]
    assert weak["status"] == "FOCAL_RANGE_EXHAUSTED"


def test_a_floor_spec_needs_a_registered_quantity_and_a_derivation():
    with pytest.raises(ProtocolError, match="registered construct-strength"):
        CS.FloorSpec(quantity="invented", value=0.5, derivation="d",
                     decided_by="t", decided_on="t")
    with pytest.raises(ProtocolError, match="derivation"):
        CS.FloorSpec(quantity="chance_bite", value=0.5, derivation="",
                     decided_by="t", decided_on="t")


def test_a_floor_on_an_unmeasured_quantity_refuses(restore_decisions):
    restore_decisions.close("D17", "floor", evidence="t", decided_by="t",
                            decided_on="t")
    spec = CS.FloorSpec(quantity="long_word_share", value=0.2,
                        derivation="d", decided_by="t", decided_on="t")
    with pytest.raises(ProtocolError, match="not measured"):
        regime.assert_construct_floor(11, chance_compliance_at_m_star=0.4,
                                      curve=CURVE, floor=spec)
