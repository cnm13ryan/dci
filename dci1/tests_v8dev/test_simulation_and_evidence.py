"""Quick simulation smoke tests, and evidence-dependent checks that skip
without a stored tree."""
from __future__ import annotations

import pytest

from dci1v8dev import simulate as S
from dci1v8dev.prescreen.screen import ScreenConfig


def test_archetype_truths_match_their_names():
    cfg = ScreenConfig()
    t = {k: S.true_verdict(a, S.A_CURVE_QWEN, geometry=cfg.geometry,
                           chance_max=cfg.chance_max, lift_min=cfg.lift_min)
         for k, a in S.ARCHETYPES.items()}
    assert t["wide"]["support_both"] and t["wide"]["c4"]
    assert not t["flat"]["support_both"] and not t["flat"]["c4"]
    assert not t["one_sided"]["support_above"]
    assert not t["narrow_noisy"]["c4"]
    assert t["outlier"]["support_both"]
    # the 2507-like ladder reaches the hard side only through the reserve
    full = t["too_easy_reserve"]
    ladder_only = S.true_verdict(S.ARCHETYPES["too_easy_reserve"], S.A_CURVE_QWEN,
                                 geometry=cfg.geometry, chance_max=cfg.chance_max,
                                 lift_min=cfg.lift_min, severities=range(1, 9))
    assert full["support_below"] and not ladder_only["support_below"]


def test_simulate_case_runs_and_reports_every_metric():
    r = S.simulate_case(S.ARCHETYPES["flat"], S.A_CURVE_QWEN, n_sims=4, seed=2,
                        screen_config=ScreenConfig(draws=500))
    for key in ("legacy", "new", "calibrated", "true_event"):
        assert key in r
    assert r["new"]["accept_rate"] <= 0.5
    assert 0 <= r["new"]["fraction_resampled"] <= 1


def test_reserve_extension_recovers_the_hard_side_in_simulation():
    r = S.simulate_case(S.ARCHETYPES["too_easy_reserve"], S.A_CURVE_QWEN,
                        n_sims=6, seed=3, screen_config=ScreenConfig(draws=600))
    assert r["new"]["fraction_resampled"] > 0.5


def test_backtest_reproduces_the_signed_certificate(evidence_root):
    from dci1v8dev import backtest as B
    from dci1v8dev.prescreen import legacy
    rep = B.load_replication(evidence_root, "dci1v7/qwen3-4b")
    table, a_grid = B.prescreen_input(rep["regime"])
    cert = legacy.legacy_certificate(table, a_grid)
    signed = rep["regime"]["coverage"]
    assert cert["coverage"]["conditions"] == signed["conditions"]
    assert cert["coverage"]["realised"]["straddling_groups"] == \
        signed["realised"]["straddling_groups"]
    assert cert["iota_a_prescreen"] == pytest.approx(rep["regime"]["iota_a_prescreen"])
    truth = B.calibrated_truth(rep["gate2"], rep["regime"],
                               geometry=ScreenConfig().geometry,
                               chance_max=0.75, lift_min=0.20)
    assert truth["coverage"]["conditions"]["C4"] == \
        rep["gate3a"]["coverage_at_calibrated_iota_a"]["conditions"]["C4"]


def test_spectrum_replay_local_valid_is_a_subset_of_folded_stable(evidence_root):
    from dci1v8dev import backtest as B
    rep = B.load_replication(evidence_root, "dci1v7/qwen3-4b")
    out = B.spectrum_backtest(rep, label="v7", model="qwen3-4b", resamples=300)
    assert out["n_local_valid"] <= out["n_folded_stable"]
    assert out["n_spectrum_valid"] >= out["n_local_valid"]
    assert out["spectrum_valid_range"][1] - out["spectrum_valid_range"][0] > \
        out["folded_pool_range"]["span"]
