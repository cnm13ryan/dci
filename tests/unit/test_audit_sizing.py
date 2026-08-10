"""Gate M sizing: the bound the gate applies is the bound the size inverts."""
import pytest

from dci.measurement.audit_sizing import (error_ceiling_sample_size,
                                          required_cases_for_ceiling,
                                          wilson_interval)

pytestmark = pytest.mark.cpu


def test_wilson_zero_events_known_values():
    assert round(wilson_interval(0, 59, 0.95)[1], 4) == 0.0611
    assert wilson_interval(0, 73, 0.95)[1] <= 0.05 < wilson_interval(0, 72, 0.95)[1]


def test_inversion_is_tight():
    n = required_cases_for_ceiling(0.05, 0.95)
    assert n == 73
    assert wilson_interval(0, n, 0.95)[1] <= 0.05
    assert wilson_interval(0, n - 1, 0.95)[1] > 0.05


def test_v14_formula_retained_only_as_the_documented_mistake():
    assert error_ceiling_sample_size(0.05, 0.95) == 59  # provably insufficient


def test_stratum_ceiling():
    n = required_cases_for_ceiling(0.20, 0.95)
    assert wilson_interval(0, n, 0.95)[1] <= 0.20
