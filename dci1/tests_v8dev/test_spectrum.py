"""Local vs spectrum validity, the selected-coverage rule, the deterministic
selection, admissible backups, the cell design and the precision projection."""
from __future__ import annotations

import random

import pytest

from dci1v7.protocol import constants as C
from dci1v7.stages import stability as v7_stability
from dci1v8dev.spectrum import precision as P
from dci1v8dev.spectrum.backups import admissible_backups
from dci1v8dev.spectrum.coverage import CoverageRule, selected_coverage
from dci1v8dev.spectrum.design import (
    spectrum_cells,
    spectrum_generation_cost,
    v7_spectrum_orders_present,
)
from dci1v8dev.spectrum.selection import SelectionRule, select_spectrum
from dci1v8dev.spectrum.validity import (
    SPECTRUM_COMPONENTS,
    classify_pool,
    coordinate_verdict,
    local_validity,
    spectrum_validity,
    unfolded_stability,
)

from .conftest import calibration_row, split_rows

IOTA_A = 0.68


def _pool(spec):
    pooled, a, b = [], [], []
    for kind, ladder in spec.items():
        for q, (p, kw) in ladder.items():
            pooled.append(calibration_row(kind, q, solo=p, **kw))
            ra, rb = split_rows(kind, q, solo_a=min(0.999, p + 0.01),
                                solo_b=max(0.001, p - 0.01), **kw)
            a.append(ra)
            b.append(rb)
    return pooled, a, b


def test_the_leak_is_the_folded_v_diff_and_the_unfolded_rule_removes_it():
    """A rung 0.25 below A: stable by every measure, failed by v7's folded
    §13.7 on V_diff alone, passed by the unfolded one."""
    ra, rb = split_rows("MK1", 8, solo_a=0.44, solo_b=0.42)
    pair = v7_stability.SplitPair("MK1:8", ra, rb)
    folded = v7_stability.stability_verdict(
        pair, iota_a_by_split={C.CALIBRATION_A: IOTA_A, C.CALIBRATION_B: IOTA_A},
        solo_a_by_split={C.CALIBRATION_A: IOTA_A, C.CALIBRATION_B: IOTA_A},
        seed=0, resamples=300)
    assert not folded["passed"] and "V_diff" in folded["reason"]
    unfolded = unfolded_stability(pair, seed=0, resamples=300)
    assert unfolded["passed"] and unfolded["split_components"] == \
        ["V_coord", "V_chance", "V_inter_s"]
    assert v7_stability.SPLIT_ADMISSIBILITY_COMPONENTS[-1] == "V_diff"   # the leak, pinned


def test_local_validity_is_v7s_full_rule_unchanged():
    row = calibration_row("MK1", 5, solo=0.66, per_topic=(0.66,) * 192)
    v = local_validity(row, iota_a=IOTA_A, solo_compliance_a=0.68, n_topics_a=192,
                       folded_stability={"passed": True})
    assert v["passed"] and [c["component"] for c in v["components"]] == \
        list(C.VALIDITY_COMPONENTS)
    far = calibration_row("MK1", 8, solo=0.40, per_topic=(0.40,) * 192)
    v = local_validity(far, iota_a=IOTA_A, solo_compliance_a=0.68, n_topics_a=192,
                       folded_stability={"passed": True})
    assert not v["passed"] and v["first_failing_component"] == "V_diff"


def test_spectrum_validity_admits_an_extreme_stable_rung_and_rejects_degenerates():
    per = tuple([1.0] * 180 + [0.0] * 12)          # p = 0.9375, precise
    easy = calibration_row("MK1", 1, solo=0.9375, per_topic=per)
    v = spectrum_validity(easy, iota_a=IOTA_A, unfolded={"passed": True})
    assert v["passed"] and not v["passes_v7_v_head"]      # beyond V_head
    assert [c["component"] for c in v["components"]] == list(SPECTRUM_COMPONENTS)
    vac = calibration_row("RF7", 2, solo=0.80, vacuity=0.30, per_topic=(0.8,) * 192)
    assert spectrum_validity(vac, iota_a=IOTA_A, unfolded={"passed": True})[
        "first_failing_component"] == "V_coord"
    chance = calibration_row("CR5", 3, solo=0.90, chance=0.80, kappa_b=0.80,
                             per_topic=(0.9,) * 192)
    assert spectrum_validity(chance, iota_a=IOTA_A, unfolded={"passed": True})[
        "first_failing_component"] == "V_coord"          # lift 0.10 < 0.20
    degenerate = calibration_row("RF6", 1, solo=0.995, chance=0.995,
                                 per_topic=(0.995,) * 192)
    v = spectrum_validity(degenerate, iota_a=IOTA_A, unfolded={"passed": True})
    assert not v["passed"] and v["side"] == "undefined"
    near = calibration_row("MK1", 5, solo=0.70, per_topic=(0.7,) * 192)
    assert spectrum_validity(near, iota_a=IOTA_A, unfolded={"passed": True})[
        "first_failing_component"] == "V_pos"
    noisy = calibration_row("MK2", 4, solo=0.50,
                            per_topic=tuple([1.0, 0.0] * 96))   # SE ~0.036
    assert coordinate_verdict(noisy)["values"]["se_iota"] < 0.05
    wild = calibration_row("MK2", 4, solo=0.50, n_topics=24,
                           per_topic=tuple([1.0, 0.0] * 12))    # SE ~0.10
    assert not coordinate_verdict(wild)["passed"]


def test_classify_pool_reports_both_rules_and_the_headroom_window():
    pooled, a, b = _pool({"MK1": {2: (0.93, {}), 5: (0.68, {}), 8: (0.45, {})}})
    folded = {r.label: {"passed": abs(r.iota - IOTA_A) <= 0.1} for r in pooled}
    out = classify_pool(pooled, a, b, iota_a=IOTA_A, solo_compliance_a=0.68,
                        n_topics_a=192, folded_stability=folded, resamples=300)
    assert out["n_local_valid"] == 1 and out["n_spectrum_valid"] == 2
    assert out["n_spectrum_valid_beyond_v_head"] == 1


def test_selected_coverage_replaces_c4_with_the_selected_sets_geometry():
    pts = [{"candidate": "MK1:8", "family": "MK1", "iota": 0.48},
           {"candidate": "MK1:2", "family": "MK1", "iota": 0.82},
           {"candidate": "MK2:8", "family": "MK2", "iota": 0.50},
           {"candidate": "MK2:2", "family": "MK2", "iota": 0.80}]
    cov = selected_coverage(pts, iota_a=IOTA_A)
    assert cov["identified"] and cov["projection"]["se_beta"] < 0.05
    one_side = selected_coverage(pts[:1] + pts[2:3], iota_a=IOTA_A)
    assert not one_side["identified"] and any("above" in r for r in one_side["reasons"])
    single = selected_coverage([pts[0], pts[3]], iota_a=IOTA_A)
    assert single["projection"]["se_beta"] is None          # one point per family
    imprecise = selected_coverage([{**p, "se_iota": 0.2} for p in pts], iota_a=IOTA_A)
    assert any("coordinate SE" in r for r in imprecise["reasons"])


def test_selection_is_deterministic_order_invariant_and_diverse():
    pooled, _, _ = _pool({
        "MK1": {2: (0.85, {}), 5: (0.68, {}), 8: (0.48, {})},
        "MK2": {2: (0.83, {}), 8: (0.50, {})},
        "MK3": {2: (0.86, {}), 8: (0.40, {})},
        "MK4": {8: (0.30, {})},                         # one-sided, one point
        "XC1": {1: (0.84, {}), 7: (0.47, {})}})
    valid = [r for r in pooled if abs(r.iota - IOTA_A) >= 0.05]
    core = [r for r in pooled if r.label == "MK1:5"]      # the centre point
    one = select_spectrum(valid + core, iota_a=IOTA_A, core_references={"MK1": 5})
    shuffled = list(valid + core)
    random.Random(2).shuffle(shuffled)
    two = select_spectrum(shuffled, iota_a=IOTA_A, core_references={"MK1": 5})
    assert one["points"] == two["points"] and one["families"] == two["families"]
    assert one["identified"] and one["coverage"]["n_families"] >= 2
    assert "MK4" not in one["families"]                 # one point: no leverage
    roles = {p["candidate"]: p["role"] for p in one["points"]}
    assert roles["MK1:5"] == "CORE_CENTRE"
    assert all(v["n_points"] >= 2 for v in one["per_family"].values())
    # a family whose two rungs are nearly identical never becomes a pair
    dup, _, _ = _pool({"MK5": {3: (0.50, {}), 4: (0.49, {})},
                       "MK6": {2: (0.85, {}), 8: (0.45, {})}})
    sel = select_spectrum(dup, iota_a=IOTA_A,
                          rule=SelectionRule(coverage=CoverageRule(
                              min_families_per_side=2)))
    assert "MK5" not in sel["families"]


def test_spectrum_support_without_any_family_meeting_old_c4():
    """Three families each spanning ~0.30: old C4 needs 0.40 per family (and
    six groups); the selected set is identified."""
    pooled, _, _ = _pool({"MK1": {2: (0.82, {}), 8: (0.52, {})},
                          "MK2": {2: (0.80, {}), 8: (0.50, {})},
                          "MK3": {2: (0.84, {}), 8: (0.55, {})}})
    sel = select_spectrum(pooled, iota_a=IOTA_A)
    assert sel["identified"]
    assert all(v["max_iota"] - v["min_iota"] < 0.40 for v in sel["per_family"].values())


def test_backups_count_only_fully_admissible_core_candidates():
    pooled = [calibration_row("MK1", 5, solo=0.66, per_topic=(0.66,) * 192),
              calibration_row("MK2", 4, solo=0.70, per_topic=(0.70,) * 192),
              calibration_row("MK3", 6, solo=0.45, per_topic=(0.45,) * 192),
              calibration_row("CR6", 3, solo=0.67, per_topic=(0.67,) * 192)]
    local = {r.label: local_validity(r, iota_a=IOTA_A, solo_compliance_a=0.68,
                                     n_topics_a=192,
                                     folded_stability={"passed": True})
             for r in pooled}
    out = admissible_backups(local, pooled, iota_a=IOTA_A, used_families=["MK1"],
                             gate2_5_qualified=["MK1", "MK2", "MK3", "CR6", "RF1"],
                             recorded_backups=["CR6", "MK3"])
    assert out["fully_admissible_families"] == ["MK1", "MK2"]   # CR6 is Tier 3
    assert out["backups"] == ["MK2"]
    assert out["recorded_backups_inadmissible"] == ["CR6", "MK3"]
    assert not out["meets_min_qualified"] and out["n_gate2_5_qualified"] == 5


def test_the_v7_cell_set_already_pairs_b_with_every_spectrum_slot_in_both_orders():
    assert v7_spectrum_orders_present()["ok"]
    cells = spectrum_cells(["X1", "X2"])
    ids = [c["cell_id"] for c in cells]
    assert ids == ["unconstrained", "solo:B", "solo:X1", "pair:B+X1", "pair:X1+B",
                   "solo:X2", "pair:B+X2", "pair:X2+B"]
    cost = spectrum_generation_cost(6)
    assert cost["generations"] == 6 * 3 * C.N_BLOCKS * 8


def test_precision_projection_matches_monte_carlo_and_a_single_point_has_no_leverage():
    pts = [("F1:0", "F1", 0.53), ("F1:1", "F1", 0.68), ("F1:2", "F1", 0.78),
           ("F2:0", "F2", 0.50), ("F2:1", "F2", 0.68), ("F2:2", "F2", 0.80)]
    proj = P.projected_se_beta([(f, d) for _, f, d in pts])
    mc = P.simulate_design(pts, d_a=0.68, beta_true=0.4, n_sims=400, se_d=0.0)
    assert abs(mc["beta_sd"] - proj["se_beta"]) < 0.35 * proj["se_beta"]
    assert abs(mc["beta_bias"]) < 0.02
    assert P.projected_se_beta([("F1", 0.5), ("F2", 0.7), ("F3", 0.9)])["se_beta"] is None
    lev = P.leverage_for_se(0.05)
    assert P.projected_se_beta([("F1", 0.68 - (lev / 2) ** 0.5),
                                ("F1", 0.68 + (lev / 2) ** 0.5)])["se_beta"] \
        == pytest.approx(0.05, rel=1e-6)
    dd = P.projected_se_delta_diff(pts, d_a=0.68)
    assert dd["meets_precondition"]
