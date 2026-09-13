"""§34 D17: the construct-strength interface, with no invented threshold."""
from __future__ import annotations

import json
import pathlib

import pytest

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions
from dci1v6.run.execute import instance_rates
from dci1v6.stages import construct_strength as CS
from dci1v6.stages import regime

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


# ------------------------------------------- the floor the researcher took

def test_the_registered_floor_is_the_one_the_record_carries():
    """§34 D17 is closed at `floor`, and the floor comes from the record.

    Not from this module: `construct_strength` carries no threshold, and the
    quantity, the value, the semantics and the derivation are all read from
    `researcher_decisions.json`. Changing the number that refuses an operating
    point is a §32 amendment to a committed file, not an edit to a line.
    """
    assert decisions.value_of("D17") == "floor"
    floor = CS.registered_floor()
    assert floor.quantity == "chance_compliance"
    assert floor.value == 0.50
    assert floor.direction == "lower_is_stronger"
    assert floor.semantics == CS.POINT_REFUSES
    assert "0.398" in floor.derivation and "0.586" in floor.derivation
    # And nothing in the source names the number.
    source = (pathlib.Path(CS.__file__)).read_text()
    assert "0.50" not in source and "0.5\n" not in source


def test_the_floor_admits_just_below_and_refuses_just_above():
    """The three cases a threshold has: below, exactly on it, above."""
    below = regime.assert_construct_floor(
        11, chance_compliance_at_m_star=0.49, curve={**CURVE, 11: 0.49})
    exactly = regime.assert_construct_floor(
        11, chance_compliance_at_m_star=0.50, curve={**CURVE, 11: 0.50})
    above = regime.assert_construct_floor(
        11, chance_compliance_at_m_star=0.51, curve={**CURVE, 11: 0.51})
    assert below["satisfied"] and not below["selection_refused"]
    # A ceiling written `<= 0.50` admits 0.50. Which way the boundary falls is
    # part of the rule and not a rounding detail.
    assert exactly["satisfied"] and not exactly["selection_refused"]
    assert not above["satisfied"] and above["selection_refused"]
    assert above["status"] == "FOCAL_RANGE_EXHAUSTED"
    assert "chance_compliance = 0.51 against 0.5" in above["reason"]


def test_the_verdict_reads_the_point_and_the_interval_is_reported_beside_it():
    """§34 D17's registered semantics, and the case that distinguishes them.

    kappa_B = 0.47 on 96 topics has a Wilson upper bound of about 0.57, so a
    rule that refused on the interval would refuse this operating point and
    the registered rule admits it. The disagreement is recorded rather than
    adjudicated silently.
    """
    out = regime.assert_construct_floor(
        11, chance_compliance_at_m_star=0.47, curve={**CURVE, 11: 0.47},
        n_topics=96)
    low, high = out["wilson"]
    assert low < 0.50 < high, "the fixture must straddle for this to test"
    assert out["satisfied"] and not out["selection_refused"]
    assert out["marginal"] is True
    assert CS.MARGINAL_STATUS in out["statuses"]
    assert CS.MARGINAL_STATUS in C.IDENTIFICATION_STATUSES


def test_a_refusal_can_be_marginal_too():
    """Marginality is about the data, not about which way the verdict fell."""
    out = regime.assert_construct_floor(
        11, chance_compliance_at_m_star=0.53, curve={**CURVE, 11: 0.53},
        n_topics=96)
    assert out["selection_refused"] and out["marginal"] is True
    assert CS.MARGINAL_STATUS in out["statuses"]


def test_a_comfortable_operating_point_is_not_marginal():
    out = regime.assert_construct_floor(
        9, chance_compliance_at_m_star=0.10, curve={**CURVE, 9: 0.10},
        n_topics=96)
    assert out["satisfied"] and out["marginal"] is False
    assert CS.MARGINAL_STATUS not in out["statuses"]


def test_without_a_denominator_the_verdict_stands_and_the_interval_does_not():
    """`n_topics` is optional and costs only the marginality record.

    The verdict reads the point estimate, so it cannot depend on how many
    topics there were --- but a Wilson interval invented from an unknown n
    would be a number with the right shape and no meaning.
    """
    out = regime.assert_construct_floor(
        11, chance_compliance_at_m_star=0.47, curve={**CURVE, 11: 0.47})
    assert out["satisfied"] and out["wilson"] is None
    assert out["marginal"] is False


def test_the_floor_reads_the_load_zero_denominator_not_every_absent_row():
    """The estimator the threshold was calibrated on, made explicit.

    `present=False` collects every row where B was not stated, and in Gate 2's
    focal grid that includes the B-solo cells at the other seven severities ---
    answers written under a stated length budget, which satisfy a looser
    budget far more often than an unconstrained answer does. Both rates are
    computed; the floor takes the load-zero one.
    """
    rows = [
        {"topic_id": "t1", "arm": "unconstrained", "word_count": 80,
         "truncated": False, "topic_split": None,
         "scores": [{"kind": "B", "severity": 9, "present": False,
                     "passed": False, "vacuous_pass": False, "graded": 0.0}]},
        {"topic_id": "t1", "arm": "solo", "word_count": 80,
         "truncated": False, "topic_split": None,
         "scores": [{"kind": "B", "severity": 9, "present": False,
                     "passed": True, "vacuous_pass": False, "graded": 1.0}]},
        {"topic_id": "t1", "arm": "solo", "word_count": 80,
         "truncated": False, "topic_split": None,
         "scores": [{"kind": "B", "severity": 9, "present": True,
                     "passed": True, "vacuous_pass": False, "graded": 1.0}]},
    ]
    rates = instance_rates(rows, kind="B", severity=9,
                           unconstrained_arm="unconstrained")
    assert rates["chance"] == pytest.approx(0.5)          # pooled
    assert rates["chance_unconstrained"] == pytest.approx(0.0)
    assert rates["n_topics_unconstrained"] == 1


# ------------------------------------- the branch the researcher did not take

def test_no_floor_reports_and_refuses_nothing(restore_decisions):
    """The standing proposal, non-adopted, and still executed by a test."""
    restore_decisions.override_for_testing("D17", "no_floor")
    out = regime.assert_construct_floor(11, chance_compliance_at_m_star=0.4,
                                        curve=CURVE)
    assert out["floor_registered"] is False
    assert out["selection_refused"] is False
    assert "whole curve" in out["reported"]
    # And a severity the adopted floor refuses is admitted under it.
    weak = regime.assert_construct_floor(14, chance_compliance_at_m_star=0.96,
                                         curve={**CURVE, 14: 0.96})
    assert weak["selection_refused"] is False


def test_the_floor_branch_refuses_a_closure_that_carries_no_spec(
        tmp_path, monkeypatch):
    """A floor with no derivation is a threshold nobody chose.

    Exercised against a record *file* rather than by reopening the registry,
    because it is the record that has to carry the spec: a `floor` closure
    that arrives without one is a decision to have a rule and no rule.
    """
    record = tmp_path / "researcher_decisions.json"
    record.write_text(json.dumps({
        "closures": [{"id": "D17", "value": "floor", "evidence": "e",
                      "decided_by": "t", "decided_on": "t"}]}))
    assert decisions.recorded_spec("D17", record) is None
    monkeypatch.setattr(decisions, "RECORD_PATH", record)
    with pytest.raises(ProtocolError, match="does not invent"):
        CS.registered_floor()


def test_a_floor_spec_needs_a_registered_quantity_and_a_derivation():
    with pytest.raises(ProtocolError, match="registered construct-strength"):
        CS.FloorSpec(quantity="invented", value=0.5, derivation="d",
                     decided_by="t", decided_on="t")
    with pytest.raises(ProtocolError, match="derivation"):
        CS.FloorSpec(quantity="chance_bite", value=0.5, derivation="",
                     decided_by="t", decided_on="t")
    with pytest.raises(ProtocolError, match="registered floor semantics"):
        CS.FloorSpec(quantity="chance_bite", value=0.5, derivation="d",
                     decided_by="t", decided_on="t",
                     semantics="wilson_upper_bound_refuses")


def test_a_floor_on_an_unmeasured_quantity_refuses():
    spec = CS.FloorSpec(quantity="long_word_share", value=0.2,
                        derivation="d", decided_by="t", decided_on="t")
    with pytest.raises(ProtocolError, match="not measured"):
        regime.assert_construct_floor(11, chance_compliance_at_m_star=0.4,
                                      curve=CURVE, floor=spec)


def test_a_floor_on_a_non_proportion_gets_no_interval():
    """Only the two proportions have a Wilson interval that means anything."""
    spec = CS.FloorSpec(quantity="grid_headroom", value=2.0,
                        derivation="d", decided_by="t", decided_on="t")
    out = regime.assert_construct_floor(
        11, chance_compliance_at_m_star=0.4, curve=CURVE, n_topics=96,
        floor=spec)
    assert out["satisfied"] and out["wilson"] is None


def test_the_complement_reads_the_same_boundary_from_the_other_side():
    """C2 in the packet: identical rule, different sign, so it must agree."""
    spec = CS.FloorSpec(quantity="chance_bite", value=0.50,
                        derivation="the complement of the adopted ceiling",
                        decided_by="t", decided_on="t")
    for kappa, admitted in ((0.49, True), (0.50, True), (0.51, False)):
        out = regime.assert_construct_floor(
            11, chance_compliance_at_m_star=kappa,
            curve={**CURVE, 11: kappa}, n_topics=96, floor=spec)
        assert out["satisfied"] is admitted
