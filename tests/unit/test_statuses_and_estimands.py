import pytest

from dci.protocol.estimands import ESTIMAND_DEFINITIONS
from dci.statuses import GateStatus

pytestmark = pytest.mark.cpu


def test_statuses_distinct_and_complete():
    assert len(set(GateStatus.ALL)) == len(GateStatus.ALL) == 23


def test_never_resolved_by_more_data_is_a_subset():
    assert set(GateStatus.NEVER_RESOLVED_BY_MORE_DATA) <= set(GateStatus.ALL)
    assert GateStatus.VERIFIER_RELIABILITY_FAILED in GateStatus.NEVER_RESOLVED_BY_MORE_DATA


def test_nested_estimands_are_not_one_parameter():
    a = ESTIMAND_DEFINITIONS["primary_total"]["reference_definition"]
    b = ESTIMAND_DEFINITIONS["kappa_matched"]["reference_definition"]
    assert a != b
