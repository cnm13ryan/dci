"""The pilot of 2026-10-25 as a regression fixture (revision 2026-10).

The fixture is that run's own stand-alone tables, its Freeze 1 and an
excerpt of its Freeze 2 (``tests/batch1/fixtures/pilot_2026_10_25b``). The
code must reproduce the run's scientific decisions from its data, and, since
the interval fix, the stored calibration hash on any platform: the hash was
made on Linux, and macOS used to differ in the last digit of four reported
interval bounds because ``x ** 2`` went through the C library's ``pow``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import intervals as I
from dci.batch1 import scoring as S
from dci.provenance.hashes import sha

pytestmark = pytest.mark.cpu
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pilot_2026_10_25b"


@pytest.fixture(scope="module")
def pilot():
    freeze1 = json.loads((FIXTURE / "freeze1.json").read_text())
    tables = S.PilotTables.from_state(
        json.loads((FIXTURE / "tables.json").read_text()))
    stored = json.loads((FIXTURE / "freeze2_excerpt.json").read_text())
    result = CAL.finalize(tables, EV.config_of(freeze1),
                          COMPAT.compatibility_matrix())
    return {"freeze1": freeze1, "tables": tables, "stored": stored,
            "result": result}


def test_the_fixture_is_the_frozen_pilot(pilot):
    stored = pilot["stored"]
    assert stored["freeze1_hash"] == pilot["freeze1"]["manifest_hash"] == \
        "93ef9aacc59e033f1681880f07e1443ac2d9aa7c5657a9a48b23391d0431bf3e"
    assert stored["manifest_hash"] == \
        "4946c194bd3abb6f232d7455ed3ee1bded7294d73e5014bea66038392174ad7e"
    assert F.tables_hash(pilot["tables"]) == stored["tables_hash"]


def test_the_pilot_decisions_are_reproduced(pilot):
    result, stored = pilot["result"], pilot["stored"]
    assert result["status"] == stored["calibration_status"] == \
        "INFEASIBLE_REVISION_REQUIRED"
    assert result["a"]["selected"] == stored["selected"]["a"] == "A.however.6"
    assert result["b"]["selected"] == stored["selected"]["b_limits"] == [8, 10]
    assert sorted(result["eligible_20"]) == sorted(stored["eligible_20"])
    assert sorted(result["extension_10_only"]) == \
        sorted(stored["extension_10_only"])
    for p in ("P1", "P2", "P3"):
        assert result["feasibility"][p]["supported_configurations"] == \
            stored["feasibility"][p]["supported_configurations"]
    assert [result["feasibility"][p]["supported_configurations"]
            for p in ("P1", "P2", "P3")] == [7, 0, 1]
    for rep in result["configurations"]:
        key = f"{rep['model']}|{rep['frame']}|B{rep['b_limit']}"
        assert rep["populations"] == stored["configurations"][key]["populations"]
        assert {p: rep["coverage"][p]["supported"] for p in ("P1", "P2", "P3")} \
            == stored["configurations"][key]["supported"]


def test_the_calibration_hash_is_reproduced_on_any_platform(pilot):
    """The stored hash was made on Linux; with squares as products the same
    value is computed here, whatever this platform's libm does."""
    assert sha(["batch1/calibration", pilot["result"]]) == \
        pilot["stored"]["calibration_hash"] == \
        "ba07458e45e6b62170405828d11f76fa6a2839d4b354ffc2de52da2654aaae1e"


def test_newcombe_uses_only_exactly_rounded_operations():
    """Squares are products: the result equals the product form exactly."""
    import math
    z = 1.959963984540054
    for k1, n1, k2, n2 in ((54, 96, 53, 96), (17, 32, 61, 96), (0, 32, 96, 96)):
        l1, u1 = I.wilson(k1, n1, z)
        l2, u2 = I.wilson(k2, n2, z)
        p1, p2 = k1 / n1, k2 / n2
        a, b, c, e = p1 - l1, u2 - p2, u1 - p1, p2 - l2
        want = (max(-1.0, p1 - p2 - math.sqrt(a * a + b * b)),
                min(1.0, p1 - p2 + math.sqrt(c * c + e * e)))
        assert I.newcombe(k1, n1, k2, n2, z) == want
