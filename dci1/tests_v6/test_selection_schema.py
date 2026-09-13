"""§19 test 2: the calibration loader's closed schema (§13.11)."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v6.protocol import constants as C
from dci1v6.stages.calibration_table import (
    FORBIDDEN_CALIBRATION_FIELDS, PERMITTED_UNDER_B_FIELDS,
    load_calibration_table,
)
from tests_v6.conftest import FIXTURE_M_STAR, FIXTURE_MODEL, kappa_source

BASE = {"kind": "MK1", "severity": 3, "split": "pooled",
        "model_key": FIXTURE_MODEL, "solo_compliance": 0.70,
        "chance_compliance": 0.01, "solo_vacuity": 0.0}


def _load(**extra):
    row = {**BASE, **extra}
    return load_calibration_table([row], model_key=FIXTURE_MODEL,
                                  m_star=FIXTURE_M_STAR, split="pooled")


def test_a_clean_table_loads():
    rows = _load(kappa_under_b=0.0,
                 kappa_under_b_source=kappa_source("MK1:3"))
    assert rows[0].label == "MK1:3"
    assert rows[0].projected_compliance == pytest.approx(rows[0].iota)


@pytest.mark.parametrize("field", ["composed_compliance", "delivery_loss",
                                   "delta_r", "xi", "joint_state",
                                   "composed_uptake", "b_with_a",
                                   "interference", "gate4_rate",
                                   "order_contrast"])
def test_a_composed_field_is_refused_before_a_value_is_read(field):
    with pytest.raises(ProtocolError) as excinfo:
        _load(**{field: 0.5})
    assert "composed" in str(excinfo.value).lower()


def test_an_unknown_field_is_refused():
    """The refusal that matters: a deny list only catches what it was told."""
    with pytest.raises(ProtocolError) as excinfo:
        _load(harmless_looking_column=1.0)
    assert "closed" in str(excinfo.value)


def test_the_permitted_under_b_fields_are_named():
    assert set(PERMITTED_UNDER_B_FIELDS) == {
        "kappa_under_b", "kappa_under_b_source", "displacement",
        "projected_compliance"}
    assert len(FORBIDDEN_CALIBRATION_FIELDS) > 20


def test_the_table_refuses_a_row_from_another_model_or_split():
    with pytest.raises(ProtocolError):
        _load(model_key="another")
    with pytest.raises(ProtocolError):
        _load(split=C.CALIBRATION_A)


def test_only_a_registered_family_can_be_a_candidate():
    with pytest.raises(ProtocolError):
        load_calibration_table([{**BASE, "kind": "NOT_A_FAMILY"}],
                               model_key=FIXTURE_MODEL,
                               m_star=FIXTURE_M_STAR, split="pooled")
