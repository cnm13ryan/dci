"""A backup is a backup only if it could replace a core reference: full
LOCAL rule (folded V_stab and V_diff included) from a core-admissible tier."""
from __future__ import annotations

from dci1v8dev.spectrum.backups import admissible_backups
from dci1v8dev.spectrum.validity import local_validity

from .conftest import calibration_row

IOTA_A = 0.68
SOLO_A = 0.68


def _local(rows, folded):
    return {r.label: local_validity(r, iota_a=IOTA_A, solo_compliance_a=SOLO_A,
                                    n_topics_a=192, folded_stability=folded[r.label])
            for r in rows}


def test_tier_three_perfectly_matched_and_stable_is_not_a_backup():
    rows = [calibration_row("MK1", 5, solo=0.67, per_topic=(0.67,) * 192),
            calibration_row("CR5", 4, solo=0.68, per_topic=(0.68,) * 192)]
    folded = {r.label: {"passed": True} for r in rows}
    out = admissible_backups(_local(rows, folded), rows, iota_a=IOTA_A,
                             used_families=["MK1"], gate2_5_qualified=["MK1", "CR5"],
                             recorded_backups=["CR5"])
    assert out["backups"] == [] and out["recorded_backups_inadmissible"] == ["CR5"]
    assert out["fully_admissible_families"] == ["MK1"]


def test_a_family_failing_the_folded_stability_is_not_a_backup():
    rows = [calibration_row("MK1", 5, solo=0.67, per_topic=(0.67,) * 192),
            calibration_row("MK2", 4, solo=0.69, per_topic=(0.69,) * 192)]
    folded = {"MK1:5": {"passed": True}, "MK2:4": {"passed": False, "reason": "split"}}
    out = admissible_backups(_local(rows, folded), rows, iota_a=IOTA_A,
                             used_families=["MK1"], recorded_backups=["MK2"])
    assert out["backups"] == [] and out["recorded_backups_inadmissible"] == ["MK2"]


def test_a_family_outside_the_caliper_is_not_a_backup_however_stable():
    rows = [calibration_row("MK1", 5, solo=0.67, per_topic=(0.67,) * 192),
            calibration_row("MK3", 2, solo=0.84, per_topic=(0.84,) * 192)]
    folded = {r.label: {"passed": True} for r in rows}
    out = admissible_backups(_local(rows, folded), rows, iota_a=IOTA_A, used_families=["MK1"])
    assert out["backups"] == []


def test_backups_are_the_nearest_unused_admissible_families_in_order():
    rows = [calibration_row("MK1", 5, solo=0.67, per_topic=(0.67,) * 192),
            calibration_row("MK2", 4, solo=0.71, per_topic=(0.71,) * 192),
            calibration_row("MK4", 6, solo=0.66, per_topic=(0.66,) * 192),
            calibration_row("XC1", 3, solo=0.74, per_topic=(0.74,) * 192)]
    folded = {r.label: {"passed": True} for r in rows}
    out = admissible_backups(_local(rows, folded), rows, iota_a=IOTA_A, used_families=["MK1"])
    assert out["backups"] == ["MK4", "MK2"] and out["n_spare_admissible"] == 3
    assert out["meets_min_qualified"] is False and out["n_fully_admissible"] == 4
