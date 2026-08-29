from __future__ import annotations

import math

import numpy as np
import pytest

from dci1v8dev.prescreen import statistics as st


def test_topic_icc_is_the_recorded_development_constant():
    assert st.TOPIC_ICC == 0.40


def test_effective_n_is_exact_at_one_draw_and_shrinks_with_draws():
    assert st.effective_n(24, 1) == 24
    assert st.effective_n(24, 4) == pytest.approx(96 / (1 + 3 * 0.4))
    assert st.effective_n(48, 1) > st.effective_n(24, 4)     # fresh topics win


def test_beta_cdf_and_quantile_agree_with_closed_forms():
    assert st.beta_cdf(0.5, 1, 1) == pytest.approx(0.5)
    assert st.beta_cdf(0.25, 2, 1) == pytest.approx(0.0625)   # x^2
    assert st.beta_ppf(0.0625, 2, 1) == pytest.approx(0.25, abs=1e-8)
    lo, hi = st.beta_interval(12.5, 12.5, level=0.90)
    assert lo < 0.5 < hi and hi - lo == pytest.approx(2 * (0.5 - lo), abs=1e-6)


def test_beta_params_rescale_counts_to_the_effective_size():
    a, b = st.beta_params(18, 24, n_eff=12)
    assert (a, b) == (0.5 + 9, 0.5 + 3)
    with pytest.raises(ValueError):
        st.beta_params(30, 24)


def test_conservative_span_is_zero_when_intervals_overlap():
    assert st.conservative_span([(0.2, 0.5), (0.4, 0.8)]) <= 0.0
    assert st.conservative_span([(0.2, 0.3), (0.7, 0.8)]) == pytest.approx(0.4)


def test_shrinkage_pulls_a_lone_outlier_more_than_a_consistent_trend():
    x = list(range(8))
    y = [0.95, 0.90, 0.85, 0.40, 0.75, 0.70, 0.65, 0.60]   # one outlier
    se = [0.09] * 8
    fit = st.shrink_toward_trend(x, y, se)
    moved = [abs(s - v) for s, v in zip(fit["shrunk"], y)]
    assert moved[3] == max(moved)
    clean = st.shrink_toward_trend(x, [0.95 - 0.05 * i for i in x], se)
    assert max(abs(s - v) for s, v in zip(clean["shrunk"],
                                          [0.95 - 0.05 * i for i in x])) < 0.02


def test_family_seed_depends_only_on_the_name_and_base_seed():
    assert st.family_seed("MK1", base_seed=1) == st.family_seed("MK1", base_seed=1)
    assert st.family_seed("MK1", base_seed=1) != st.family_seed("MK2", base_seed=1)
    assert st.family_seed("MK1", base_seed=1) != st.family_seed("MK1", base_seed=2)


def test_posterior_draws_are_reproducible_and_shaped():
    a = st.posterior_draws(np.random.default_rng(3), [(2, 2), (5, 1)], 100)
    b = st.posterior_draws(np.random.default_rng(3), [(2, 2), (5, 1)], 100)
    assert a.shape == (100, 2) and np.array_equal(a, b)
    assert math.isclose(a[:, 1].mean(), 5 / 6, abs_tol=0.05)
