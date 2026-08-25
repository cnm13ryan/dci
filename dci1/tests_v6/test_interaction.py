"""E. §13.6's interaction machinery, and the seven source refusals."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v6.protocol import constants as C
from dci1v6.stages import interaction as I
from dci1v6.stages.calibration_table import load_calibration_table
from tests_v6.conftest import FIXTURE_M_STAR, FIXTURE_MODEL, kappa_source


def test_projection_and_displacement_are_the_registered_arithmetic():
    assert I.projected_compliance(0.0, 0.66) == pytest.approx(0.66)
    assert I.projected_compliance(0.5, 0.5) == pytest.approx(0.75)
    assert I.displacement(0.10, 0.83) == pytest.approx(0.73)
    # as kappa(R|B) -> 1 the projection -> 1 whatever iota is
    assert I.projected_compliance(0.999, 0.01) > 0.99


def test_rf11s_pattern_is_caught_before_composition():
    """v4r4's `gemma-3n-e2b-it` terminated on `RF11`, composed 0.969."""
    verdict = I.interaction_verdict(kappa=0.10, kappa_b=0.83, iota=0.66)
    assert not verdict.passed
    assert "projected composed compliance" in verdict.reason
    assert verdict.projected_compliance > C.PROJECTED_COMPLIANCE_BAND[1]


def test_the_floor_direction_is_caught_by_displacement():
    """`CL7:30` on qwen3-4b moved from kappa 0.849 to kappa(R|B) 0.122."""
    verdict = I.interaction_verdict(kappa=0.849, kappa_b=0.122, iota=0.50)
    assert not verdict.passed
    assert "displacement" in verdict.reason
    assert abs(verdict.displacement) > C.DISPLACEMENT_MAX


def test_a_chance_free_candidate_passes_unchanged():
    verdict = I.interaction_verdict(kappa=0.0, kappa_b=0.0, iota=0.66)
    assert verdict.passed
    assert verdict.projected_compliance == pytest.approx(0.66)


def test_kappa_under_b_needs_verdicts_and_refuses_absence():
    assert I.kappa_under_b([True, False, True, True]) == pytest.approx(0.75)
    with pytest.raises(ProtocolError):
        I.kappa_under_b([])


@pytest.mark.parametrize("bad,expected", [
    ({"load": 2}, "load one"),
    ({"present": ("B:9", "MK1:3")}, "B-solo cell"),
    ({"present": ("A:3",)}, "B-solo cell"),
    ({"model_key": "another-model"}, "ONE model"),
    ({"m_star": 11, "present": ("B:9",)}, "operating point"),
    ({"split": "calibration_a"}, "split"),
    ({"n_topics": 7}, "topics"),
])
def test_the_source_refusals(bad, expected):
    """§13.11's seven hard assertions, each refused by name."""
    source = kappa_source("MK1:3", **bad)
    with pytest.raises(ProtocolError) as excinfo:
        I.assert_kappa_under_b_source(
            source, model_key=FIXTURE_MODEL, m_star=FIXTURE_M_STAR,
            split="pooled", candidate="MK1:3", n_topics=C.N_CALIBRATION)
    assert expected in str(excinfo.value)


def test_r_must_be_absent_in_the_cell_it_is_read_from():
    source = I.KappaUnderBSource(
        load=1, present=("MK1:3",), candidate="MK1:3",
        model_key=FIXTURE_MODEL, m_star=FIXTURE_M_STAR, split="pooled",
        n_topics=C.N_CALIBRATION, n_draws=C.M_CAL)
    with pytest.raises(ProtocolError):
        I.assert_kappa_under_b_source(source, model_key=FIXTURE_MODEL,
                                      m_star=FIXTURE_M_STAR, split="pooled",
                                      candidate="MK1:3")


def test_a_composed_row_cannot_supply_kappa_under_b_through_the_loader():
    row = {"kind": "MK1", "severity": 3, "split": "pooled",
           "model_key": FIXTURE_MODEL, "solo_compliance": 0.7,
           "chance_compliance": 0.0, "solo_vacuity": 0.0,
           "kappa_under_b": 0.0,
           "kappa_under_b_source": kappa_source("MK1:3", load=2,
                                                present=("B:9", "MK1:3"))}
    with pytest.raises(ProtocolError):
        load_calibration_table([row], model_key=FIXTURE_MODEL,
                               m_star=FIXTURE_M_STAR, split="pooled")


def test_a_value_without_a_source_is_refused():
    row = {"kind": "MK1", "severity": 3, "split": "pooled",
           "model_key": FIXTURE_MODEL, "solo_compliance": 0.7,
           "chance_compliance": 0.0, "solo_vacuity": 0.0,
           "kappa_under_b": 0.0}
    with pytest.raises(ProtocolError):
        load_calibration_table([row], model_key=FIXTURE_MODEL,
                               m_star=FIXTURE_M_STAR, split="pooled")


def test_measure_interaction_reports_a_missing_value_as_a_failure():
    out = I.measure_interaction(
        [{"candidate": "MK1:3", "kappa": 0.0, "iota": 0.6,
          "kappa_under_b": None, "source": None}],
        model_key=FIXTURE_MODEL, m_star=FIXTURE_M_STAR, split="pooled")
    assert out["n_failed"] == 1
    assert "never read as a pass" in out["verdicts"][0]["reason"]


def test_realised_drift_is_an_identification_status_not_a_terminal_one():
    out = I.realised_drift(calibration_kappa_b=0.05,
                           confirmatory_kappa_b=0.40, iota=0.6,
                           reference="R1")
    assert out["identification_statuses"] == ["INTERACTION_ESTIMATE_DRIFTED"]
    assert out["terminal"] is False
    quiet = I.realised_drift(calibration_kappa_b=0.05,
                            confirmatory_kappa_b=0.09, iota=0.6,
                            reference="R1")
    assert quiet["identification_statuses"] == []
