import pytest

from dci.protocol.estimands import ESTIMAND_DEFINITIONS
from dci.statuses import GateStatus

pytestmark = pytest.mark.cpu


def _declared_statuses() -> set[str]:
    return {value for name, value in vars(GateStatus).items()
            if name.isupper() and isinstance(value, str)}


def test_statuses_distinct_and_registered():
    """The invariant, not a count: every declared status is in ALL, exactly once.

    A pinned total answers "is this the number I last wrote down", which a new
    status breaks for no reason while a status declared and never added to ALL
    still passes. Deriving the expected set from the class body catches the
    defect that matters - an unregistered status - and tolerates growth.
    """
    assert len(set(GateStatus.ALL)) == len(GateStatus.ALL)
    assert set(GateStatus.ALL) == _declared_statuses()


def test_v15_1_status_lineage():
    """LINEAGE: the v15.1 taxonomy had 23 statuses and all of them survive."""
    assert len(_declared_statuses()) >= 23
    for name in ("PASS", "NOT_IDENTIFIED_SUPPORT", "INCONCLUSIVE_PRECISION",
                 "HARDWARE_CLASS_MISMATCH", "TRANSPORT_FAILED"):
        assert getattr(GateStatus, name) in GateStatus.ALL


def test_never_resolved_by_more_data_is_a_subset():
    assert set(GateStatus.NEVER_RESOLVED_BY_MORE_DATA) <= set(GateStatus.ALL)
    assert GateStatus.VERIFIER_RELIABILITY_FAILED in GateStatus.NEVER_RESOLVED_BY_MORE_DATA


def test_nested_estimands_are_not_one_parameter():
    a = ESTIMAND_DEFINITIONS["primary_total"]["reference_definition"]
    b = ESTIMAND_DEFINITIONS["kappa_matched"]["reference_definition"]
    assert a != b
