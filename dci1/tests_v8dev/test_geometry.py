from __future__ import annotations

import numpy as np
import pytest

from dci1v8dev.prescreen.geometry import Geometry, evaluate_draws, select_iota_a


def _view(p, iota_a=0.68, **kw):
    p = np.array([p], dtype=float)
    return evaluate_draws(p, np.zeros_like(p), np.zeros_like(p),
                          np.array([iota_a]), geometry=Geometry(**kw))


def test_c4_needs_straddle_three_eligible_rungs_and_the_span():
    ok = _view([0.30, 0.55, 0.85])
    assert bool(ok.c4[0]) and ok.n_eligible[0] == 3 and ok.span[0] == pytest.approx(0.55)
    assert not bool(_view([0.30, 0.55, 0.95]).c4[0])       # 0.95 ineligible
    assert not bool(_view([0.30, 0.55, 0.60]).c4[0])       # no rung above A
    assert not bool(_view([0.50, 0.60, 0.75]).c4[0])       # span < 0.40


def test_support_needs_a_rung_meaningfully_below_and_above_a():
    v = _view([0.50, 0.80], d_below=0.15, d_above=0.10)
    assert bool(v.support_below[0]) and bool(v.support_above[0]) and bool(v.support_both[0])
    v = _view([0.60, 0.80], d_below=0.15, d_above=0.10)      # 0.60 is only 0.08 below
    assert not bool(v.support_below[0]) and not bool(v.support_both[0])
    v = _view([0.50, 0.75], d_below=0.15, d_above=0.10)      # 0.75 is only 0.07 above
    assert not bool(v.support_above[0])


def test_local_is_inside_the_caliper_and_eligible():
    v = _view([0.62, 0.92])
    assert v.local[0].tolist() == [True, False]


def test_a_rung_at_the_band_edge_is_fragile_and_a_degenerate_chance_has_no_coordinate():
    p = np.array([[0.88, 0.50]])
    v = evaluate_draws(p, np.array([[0.0, 0.995]]), np.zeros((1, 2)),
                       np.array([0.68]))
    assert v.fragile[0].tolist() == [True, False]
    assert np.isnan(v.iota[0, 1]) and not bool(v.eligible[0, 1])


def test_vacuity_above_the_ceiling_makes_a_rung_ineligible():
    p = np.array([[0.5]])
    v = evaluate_draws(p, np.zeros((1, 1)), np.array([[0.2]]), np.array([0.68]))
    assert not bool(v.eligible[0, 0])


def test_select_iota_a_applies_the_band_and_the_smaller_severity_tie_break():
    grid = np.array([[0.90, 0.75, 0.68, 0.40]])
    iota, n = select_iota_a(grid, np.zeros_like(grid), [1, 2, 3, 4])
    assert n[0] == 3 and iota[0] == pytest.approx(0.68)
    tie = np.array([[0.90, 0.75, 0.65, 0.40]])          # 2 and 3 equidistant
    _, n = select_iota_a(tie, np.zeros_like(tie), [1, 2, 3, 4])
    assert n[0] == 2
    none = np.array([[0.95, 0.92, 0.30, 0.20]])         # nothing in [0.50, 0.85]
    iota, n = select_iota_a(none, np.zeros_like(none), [1, 2, 3, 4])
    assert n[0] == 2 and iota[0] == pytest.approx(0.92)  # nearest the aim
