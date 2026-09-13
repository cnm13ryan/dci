"""Spectrum eligibility at its boundaries: each guard passes at its
threshold and fails one step past it; the headroom band is gone."""
from __future__ import annotations

from dci1v7.protocol import constants as C
from dci1v8dev import rules as R
from dci1v8dev.spectrum.validity import coordinate_verdict, spectrum_validity

from .conftest import calibration_row

IOTA_A = 0.60


def _row(**kw):
    per = kw.pop("per_topic", None)
    solo = kw.get("solo", 0.5)
    if per is None:
        per = (solo,) * 192
    return calibration_row(kw.pop("kind", "MK1"), kw.pop("severity", 3), per_topic=per, **kw)


def _first(row):
    return spectrum_validity(row, iota_a=IOTA_A, unfolded={"passed": True})["first_failing_component"]


def test_guard_band_edges():
    lo, hi = R.SPECTRUM_GUARD_BAND
    assert coordinate_verdict(_row(solo=hi))["passed"]
    assert not coordinate_verdict(_row(solo=hi + 0.001))["passed"]
    # at the low edge the lift floor fails first; the band reason appears
    # only once the point is below the band
    assert "guard band" not in (coordinate_verdict(_row(solo=lo, severity=8))["reason"] or "")
    assert "guard band" in (coordinate_verdict(_row(solo=lo - 0.001, severity=8))["reason"] or "")
    # the v7 headroom band would have refused 0.90 < p <= 0.95; the spectrum keeps it
    v = spectrum_validity(_row(solo=0.93), iota_a=IOTA_A, unfolded={"passed": True})
    assert v["passed"] and not v["passes_v7_v_head"]


def test_chance_ceiling_and_lift_floor_edges():
    # inside the guard band (p <= 0.95) a chance rate above the 0.75 ceiling
    # always leaves a lift below the 0.20 floor, so V_coord fails first;
    # at the ceiling exactly, with lift exactly 0.20, the point passes
    assert _first(_row(solo=0.90, chance=0.70, kappa_b=0.70)) is None                # lift 0.20
    assert _first(_row(solo=0.95, chance=C.CHANCE_MAX + 0.01, kappa_b=0.76)) == "V_coord"
    assert _first(_row(solo=0.50, chance=0.30, kappa_b=0.30)) is None                # lift 0.20
    assert _first(_row(solo=0.49, chance=0.30, kappa_b=0.30)) == "V_coord"           # lift 0.19
    # the registered V_chance component is still evaluated and still fails
    # on its own values (Wilson upper above 0.85) when the lift is fine
    v = spectrum_validity(_row(solo=0.95, chance=0.72, kappa_b=0.72, n_topics=24,
                               per_topic=(0.95,) * 24), iota_a=IOTA_A, unfolded={"passed": True})
    names = [c["component"] for c in v["components"] if c["passed"] is False]
    assert "V_chance" in names


def test_vacuity_and_degeneracy_edges():
    assert _first(_row(solo=0.80, vacuity=C.REFERENCE_VACUITY_MAX)) is None
    assert _first(_row(solo=0.80, vacuity=C.REFERENCE_VACUITY_MAX + 0.001)) == "V_coord"
    v = spectrum_validity(_row(solo=0.995, chance=C.CHANCE_DEGENERACY_MAX),
                          iota_a=IOTA_A, unfolded={"passed": True})
    assert not v["passed"] and v["side"] == "undefined"


def test_coordinate_precision_edge():
    # per-topic values with SD s give SE(iota) = s / sqrt(192) (chance 0)
    import math
    n = 24                     # small enough that the per-topic spread stays inside [0, 1]
    for se, ok in ((R.SPECTRUM_MAX_SE_IOTA - 0.001, True), (R.SPECTRUM_MAX_SE_IOTA + 0.003, False)):
        s = se * math.sqrt(n) * math.sqrt((n - 1) / n)     # sample SD with ddof=1
        per = tuple(0.5 + (s if i % 2 else -s) for i in range(n))
        v = coordinate_verdict(_row(solo=0.5, per_topic=per, n_topics=n))
        assert v["passed"] == ok, (se, v["values"]["se_iota"])


def test_position_rule_edge():
    d = R.SPECTRUM_D_MIN
    assert _first(_row(solo=IOTA_A + d)) is None
    assert _first(_row(solo=IOTA_A + d - 0.001)) == "V_pos"
    assert _first(_row(solo=IOTA_A - d, severity=6)) is None
