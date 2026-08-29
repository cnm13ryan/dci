"""Every rule module defaults to ``rules.py``, and the values that a
simulation chose equal the recorded choice in its report."""
from __future__ import annotations

import json
import pathlib

import pytest

from dci1v8dev import rules as R
from dci1v8dev.prescreen.extension import ExtensionRule
from dci1v8dev.prescreen.geometry import Geometry
from dci1v8dev.prescreen.rescreen import RescreenConfig
from dci1v8dev.prescreen.retention import RetentionConfig
from dci1v8dev.prescreen.screen import ScreenConfig
from dci1v8dev.spectrum.coverage import CoverageRule
from dci1v8dev.spectrum.selection import SelectionRule
from dci1v8dev.spectrum.validity import SpectrumRule

REPORTS = pathlib.Path(__file__).resolve().parents[1] / "reports" / "dci1v8dev"


def test_defaults_come_from_rules():
    g, c, s, v, e = Geometry(), CoverageRule(), SelectionRule(), SpectrumRule(), ExtensionRule()
    assert (g.d_below, g.d_above) == (R.SPECTRUM_OFFSET_BELOW, R.SPECTRUM_OFFSET_ABOVE)
    assert (c.d_below, c.d_above, c.min_total_span, c.max_se_iota, c.max_se_beta) == (
        R.SPECTRUM_OFFSET_BELOW, R.SPECTRUM_OFFSET_ABOVE, R.SPECTRUM_MIN_TOTAL_SPAN,
        R.SPECTRUM_MAX_SE_IOTA, R.SPECTRUM_MAX_SE_BETA)
    assert (s.d_min, s.target_below, s.target_above, s.max_families) == (
        R.SPECTRUM_D_MIN, R.SELECTION_TARGET_BELOW, R.SELECTION_TARGET_ABOVE,
        R.SELECTION_MAX_FAMILIES)
    assert (v.band, v.d_min, v.max_se_iota) == (R.SPECTRUM_GUARD_BAND, R.SPECTRUM_D_MIN,
                                                 R.SPECTRUM_MAX_SE_IOTA)
    assert (e.d_below, e.d_above, e.p_reach) == (R.SPECTRUM_OFFSET_BELOW,
                                                 R.SPECTRUM_OFFSET_ABOVE, R.EXTENSION_P_REACH)
    sc, rc, rt = ScreenConfig(), RescreenConfig(), RetentionConfig()
    assert (sc.accept, sc.reject, sc.local_accept) == (R.SCREEN_ACCEPT, R.SCREEN_REJECT,
                                                       R.LOCAL_LABEL_MIN)
    assert (rc.max_batches, rc.final_accept_at) == (R.RESCREEN_MAX_BATCHES,
                                                    R.RESCREEN_FINAL_ACCEPT_AT)
    assert (rt.spectrum_rungs, rt.local_rungs, rt.max_local_families) == (
        R.RETENTION_SPECTRUM_RUNGS, R.RETENTION_LOCAL_RUNGS, R.RETENTION_MAX_LOCAL_FAMILIES)


def test_coverage_thresholds_equal_the_simulations_recorded_choice():
    path = REPORTS / "coverage_simulation.json"
    if not path.exists():
        pytest.skip("coverage_simulation.json not generated")
    chosen = json.loads(path.read_text())["threshold_choice"]["chosen"]
    assert chosen["d_below"] == R.SPECTRUM_OFFSET_BELOW
    assert chosen["d_above"] == R.SPECTRUM_OFFSET_ABOVE
    assert chosen["min_total_span"] == R.SPECTRUM_MIN_TOTAL_SPAN
    assert chosen["max_se_iota"] == R.SPECTRUM_MAX_SE_IOTA


def test_screen_thresholds_equal_the_simulations_recorded_choice():
    path = REPORTS / "prescreen" / "simulation.json"
    if not path.exists():
        pytest.skip("simulation.json not generated")
    chosen = json.loads(path.read_text())["chosen"]["chosen"]
    assert (chosen["d_below"], chosen["d_above"]) == (R.SPECTRUM_OFFSET_BELOW,
                                                      R.SPECTRUM_OFFSET_ABOVE)
    assert (chosen["accept"], chosen["reject"], chosen["final_accept_at"]) == (
        R.SCREEN_ACCEPT, R.SCREEN_REJECT, R.RESCREEN_FINAL_ACCEPT_AT)
