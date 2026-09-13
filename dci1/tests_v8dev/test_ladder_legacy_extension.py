from __future__ import annotations

import pytest

from dci1v8dev.prescreen import extension as E
from dci1v8dev.prescreen.ladder import ladder_diagnostics
from dci1v8dev.prescreen.legacy import legacy_certificate, legacy_rows, prescreen_iota_a

from .conftest import a_grid, ladder


def _diag(iotas, sd=0.05):
    sev = list(range(1, len(iotas) + 1))
    return ladder_diagnostics("MK1", sev, iotas, [sd] * len(iotas),
                              [(v - sd, v + sd) for v in iotas])


def test_ladder_classes():
    assert _diag([0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25])["ladder_class"] \
        == "STRONG_LADDER"
    assert _diag([0.70, 0.69, 0.68, 0.68, 0.67, 0.67, 0.66, 0.66])["ladder_class"] \
        == "FLAT_LADDER"
    assert _diag([0.40, 0.60, 0.45, 0.70, 0.50, 0.75, 0.55, 0.80])["ladder_class"] \
        == "NON_MONOTONIC_LADDER"
    noisy = _diag([0.90, 0.80, 0.82, 0.70, 0.60, 0.62, 0.50, 0.40], sd=0.09)
    assert noisy["ladder_class"] in ("USABLE_NOISY_LADDER", "STRONG_LADDER")
    assert _diag([0.5, 0.4])["ladder_class"] == "FLAT_LADDER"


def test_the_legacy_certificate_is_the_v7_rule_on_the_same_input():
    table = (ladder("MK1", [0.95, 0.90, 0.84, 0.76, 0.66, 0.54, 0.42, 0.30])
             + ladder("MK2", [0.70] * 8))
    cert = legacy_certificate(table, a_grid())
    iota_a, sev = prescreen_iota_a(a_grid())
    assert cert["iota_a_prescreen"] == iota_a and sev == 2
    fam = cert["families"]
    # rates are k/24 counts: 0.84 -> 20/24, 0.30 -> 7/24
    assert fam["MK1"]["c4_met"] and fam["MK1"]["span"] == pytest.approx(13 / 24)
    assert not fam["MK2"]["c4_met"] and fam["MK2"]["deficiency"] == "MISSING_SIDE"
    rows = legacy_rows(table)
    assert all(set(r) >= {"candidate", "family", "structural_tier",
                          "feature_group", "constraint_class", "iota",
                          "eligible"} for r in rows)
    # rungs above 0.90 are ineligible under E2
    assert not next(r for r in rows if r["candidate"] == "MK1:1")["eligible"]


def test_reach_picks_extend_beyond_the_measured_extreme_in_the_right_direction():
    assert E.reach_picks("MK1", measured=range(1, 9), sides=["below"], n=2) == [9, 10]
    assert E.reach_picks("MK1", measured=range(1, 9), sides=["above"], n=2) == []
    assert E.reach_picks("MK1", measured=[3, 4, 5], sides=["below", "above"], n=1) \
        == [2, 6]
    # a budget loosens upward: 'harder' is a SMALLER q for RF1 (at most q ...)
    picks = E.reach_picks("RF1", measured=[3, 4, 5], sides=["below"], n=1)
    assert picks == [2]


def test_calibration_extension_plans_one_bounded_round_for_spectrum_candidates():
    plan = E.calibration_extension_plan({
        "MK1": {"measured": list(range(1, 9)), "reaches_below": False,
                "reaches_above": True, "spectrum_candidate": True},
        "MK2": {"measured": list(range(1, 9)), "reaches_below": False,
                "reaches_above": False, "spectrum_candidate": False},
        "MK3": {"measured": list(range(1, 13)), "reaches_below": False,
                "reaches_above": True, "spectrum_candidate": True}},
        rule=E.ExtensionRule(calibration_picks=2))
    assert plan["picks"] == {"MK1": [9, 10]}       # MK3: reserve exhausted
    assert plan["n_rungs"] == 2 and plan["round"] == 1


def test_extrapolation_says_whether_the_reserve_is_long_enough():
    easy = {1: 0.99, 2: 0.98, 3: 0.96, 4: 0.93, 5: 0.90, 6: 0.85, 7: 0.79, 8: 0.72}
    est = E.expected_severity_to_reach("MK8", easy, target=0.45)
    assert est["estimate"] > 8 and est["within_reserve"]
    assert E.expected_severity_to_reach("MK8", {1: 0.7, 2: 0.7, 3: 0.7},
                                        target=0.45)["estimate"] is None
