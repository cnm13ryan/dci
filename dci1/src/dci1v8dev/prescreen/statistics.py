"""Uncertainty for binomial compliance measurements, kept deliberately simple.

Three tools, all transparent:

* **Beta posteriors** for a rate from ``k`` of ``n`` draws under Jeffreys'
  prior Beta(1/2, 1/2), with the draw count replaced by a **topic-clustered
  effective sample size** when a topic was drawn more than once;
* **posterior draws** from a seeded generator, so that every probability the
  screen reports is a Monte Carlo average with a fixed, reproducible seed
  derived from the family's identity and nothing else --- the order in which
  families are handed to the screen cannot move a result;
* **conservative intervals** (Beta quantiles by bisection on the regularised
  incomplete beta, no SciPy) and a **within-family shrinkage** estimator, both
  offered as comparators to the posterior-predictive statistic.

Why an effective sample size and where its constant comes from. §12.2's
screen is one draw per topic, so a 24-topic estimate is a plain binomial on
24 draws --- but a re-screen batch that adds draws on the *same* topics buys
less than a fresh topic would, because topics differ systematically. On the
stored development calibration rows (96 topics x 4 draws per split, three
completed rehearsals, 2026-08-29) the topic-level intraclass correlation of
solo compliance has median 0.33-0.42 across rungs. ``TOPIC_ICC`` records
0.40 with that derivation; it is a development constant a v8 registration
would have to adopt or re-measure, and the tests pin it so that it cannot
drift silently.
"""
from __future__ import annotations

import math
import zlib
from collections.abc import Sequence

import numpy as np

from dci1v7.analysis.intervals import wilson

__all__ = [
    "JEFFREYS",
    "TOPIC_ICC",
    "Z_FOR_LEVEL",
    "beta_cdf",
    "beta_interval",
    "beta_mean",
    "beta_params",
    "beta_ppf",
    "beta_sd",
    "conservative_span",
    "effective_n",
    "family_seed",
    "posterior_draws",
    "shrink_toward_trend",
    "wilson",
]

#: Topic-level intraclass correlation of solo compliance, measured on the
#: development calibration rows (see module docstring). Used ONLY to compute
#: the effective sample size of a rung measured with more than one draw per
#: topic; at one draw per topic it has no effect.
TOPIC_ICC = 0.40

#: Jeffreys' prior for a binomial rate.
JEFFREYS = (0.5, 0.5)

#: Two-sided normal quantiles for the conservative-interval comparator.
Z_FOR_LEVEL = {0.50: 0.6745, 0.68: 0.9945, 0.80: 1.2816, 0.90: 1.6449,
               0.95: 1.9600}


def effective_n(n_topics: int, draws_per_topic: int, *,
                icc: float = TOPIC_ICC) -> float:
    """Effective independent draws under a topic design effect.

    ``n / (1 + (M - 1) * icc)``: exact for a one-way random-effects model of
    the topic mean. At ``M = 1`` it is ``n`` regardless of the ICC.
    """
    if n_topics <= 0 or draws_per_topic <= 0:
        raise ValueError("sample layout must be positive")
    n = n_topics * draws_per_topic
    return n / (1.0 + (draws_per_topic - 1) * icc)


def beta_params(k: float, n: float, *, n_eff: float | None = None,
                prior: tuple[float, float] = JEFFREYS) -> tuple[float, float]:
    """Beta posterior (a, b) for ``k`` of ``n`` with the counts rescaled to
    the effective sample size, so a clustered batch is not over-counted.
    ``k`` may be a real-valued effective count (see ``schema.PrescreenRung``)."""
    if n <= 0 or not 0 <= k <= n + 1e-9:
        raise ValueError(f"bad counts k={k}, n={n}")
    k = min(float(k), float(n))
    scale = 1.0 if n_eff is None else n_eff / n
    return prior[0] + k * scale, prior[1] + (n - k) * scale


def beta_mean(a: float, b: float) -> float:
    return a / (a + b)


def beta_sd(a: float, b: float) -> float:
    return math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1.0)))


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta (Numerical Recipes)."""
    max_iter, eps, fpmin = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = fpmin if abs(d) < fpmin else d
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = fpmin if abs(d) < fpmin else d
        c = 1.0 + aa / c
        c = fpmin if abs(c) < fpmin else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = fpmin if abs(d) < fpmin else d
        c = 1.0 + aa / c
        c = fpmin if abs(c) < fpmin else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def beta_cdf(x: float, a: float, b: float) -> float:
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def beta_ppf(q: float, a: float, b: float, *, tol: float = 1e-10) -> float:
    """Beta quantile by bisection: monotone, deterministic, SciPy-free."""
    if not 0.0 <= q <= 1.0:
        raise ValueError("quantile level outside [0, 1]")
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if beta_cdf(mid, a, b) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def beta_interval(a: float, b: float, *, level: float
                  ) -> tuple[float, float]:
    """Central posterior interval at ``level``."""
    alpha = 1.0 - level
    return beta_ppf(alpha / 2.0, a, b), beta_ppf(1.0 - alpha / 2.0, a, b)


def family_seed(name: str, *, base_seed: int) -> int:
    """A seed that depends on the family's identity and the base seed only.

    CRC-32 of the name folded into the base seed. Two families never share a
    draw stream, and the same family gets the same stream whatever else is on
    the table --- the property ``tests_v8dev`` asserts as order invariance.
    """
    return (int(base_seed) * 1_000_003 + zlib.crc32(name.encode("utf-8"))) \
        % (2 ** 63 - 1)


def posterior_draws(rng: np.random.Generator, params: Sequence[tuple[float, float]],
                    size: int) -> np.ndarray:
    """Independent Beta draws, shape ``(size, len(params))``."""
    if not params:
        return np.zeros((size, 0))
    a = np.array([p[0] for p in params], dtype=float)
    b = np.array([p[1] for p in params], dtype=float)
    return rng.beta(a, b, size=(size, len(params)))


def conservative_span(intervals: Sequence[tuple[float, float]]) -> float:
    """``max(lower bounds) - min(upper bounds)``: a span the data support at
    the interval's level even if the apparent extremes are lucky.

    Zero or negative means no supported span. This is the §3A comparator; it
    is conservative twice over (it does not pool evidence across rungs), which
    is why the posterior-predictive statistic is preferred.
    """
    if not intervals:
        return 0.0
    return max(lo for lo, _ in intervals) - min(hi for _, hi in intervals)


def shrink_toward_trend(x: Sequence[float], y: Sequence[float],
                        se: Sequence[float]) -> dict[str, object]:
    """Empirical-Bayes shrinkage of per-rung estimates toward the family's
    weighted linear trend in restrictiveness.

    Between-rung variance beyond the trend, ``tau^2``, is estimated by the
    method of moments (weighted residual variance minus mean squared SE,
    floored at zero); each rung is then pulled toward the fitted line with
    weight ``se^2 / (se^2 + tau^2)``. A single lucky extreme, whose SE is the
    size of its deviation, is pulled most; a ladder whose rungs genuinely
    disagree with a line (large ``tau^2``) is left alone. Returns the fit, the
    shrunk values and the shrinkage weights, so a reader can see what moved.
    """
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    ss = np.asarray(se, dtype=float)
    n = len(xs)
    if n == 0:
        return {"shrunk": [], "fitted": [], "weight_on_data": [],
                "slope": None, "intercept": None, "tau2": None}
    if n == 1 or np.allclose(xs, xs[0]):
        return {"shrunk": ys.tolist(), "fitted": ys.tolist(),
                "weight_on_data": [1.0] * n, "slope": None,
                "intercept": float(ys.mean()), "tau2": None}
    w = 1.0 / np.maximum(ss, 1e-6) ** 2
    xm = np.average(xs, weights=w)
    ym = np.average(ys, weights=w)
    sxx = float(np.sum(w * (xs - xm) ** 2))
    slope = float(np.sum(w * (xs - xm) * (ys - ym)) / sxx) if sxx > 0 else 0.0
    intercept = float(ym - slope * xm)
    fitted = intercept + slope * xs
    resid = ys - fitted
    dof = max(n - 2, 1)
    resid_var = float(np.sum(w * resid ** 2) / np.sum(w) * n / dof)
    tau2 = max(0.0, resid_var - float(np.mean(ss ** 2)))
    weight_on_data = tau2 / (tau2 + ss ** 2) if tau2 > 0 else np.zeros(n)
    shrunk = weight_on_data * ys + (1.0 - weight_on_data) * fitted
    # covariance of the fitted line (WLS): X (X'WX)^-1 X'
    X = np.column_stack([np.ones(n), xs])
    xtwx_inv = np.linalg.inv(X.T @ (w[:, None] * X))
    sigma2 = max(resid_var, float(np.mean(ss ** 2)))
    line_cov = sigma2 * X @ xtwx_inv @ X.T
    return {"shrunk": shrunk.tolist(), "fitted": fitted.tolist(),
            "weight_on_data": np.asarray(weight_on_data).tolist(),
            "slope": slope, "intercept": intercept, "tau2": tau2,
            "line_cov": line_cov.tolist()}


def hierarchical_draws(rng: np.random.Generator, x: Sequence[float],
                       y: Sequence[float], se: Sequence[float], size: int
                       ) -> np.ndarray:
    """Joint posterior draws of a family's rung coordinates under a
    random-effects model around the family's trend in restrictiveness.

    ``y_i = f(x_i) + u_i + e_i`` with ``f`` linear in restrictiveness rank,
    ``u_i ~ N(0, tau^2)`` the rung's genuine departure from the line and
    ``e_i ~ N(0, se_i^2)`` measurement error. Given the data the rung's true
    coordinate is ``w_i y_i + (1 - w_i) f_i`` with variance ``w_i se_i^2``
    (``w_i = tau^2 / (tau^2 + se_i^2)``), and the line ``f`` is itself
    uncertain with the WLS covariance --- shared across rungs, which is the
    point: a draw moves the whole ladder together, so the *union* event
    "some rung reaches the region" is no longer inflated by a dozen
    independent tails. With ``tau^2`` large (a ladder that genuinely departs
    from a line, e.g. a non-monotone one) ``w -> 1`` and the draws reduce to
    the independent ones; with ``tau^2 = 0`` the ladder is the line plus its
    uncertainty. A family with fewer than three rungs gets independent draws.
    Returns ``(size, n)`` on the y scale (clipped to [0, 1]).
    """
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    ss = np.asarray(se, dtype=float)
    n = len(xs)
    if n < 3 or np.allclose(xs, xs[0]):
        return np.clip(ys + rng.normal(size=(size, n)) * ss, 0.0, 1.0)
    fit = shrink_toward_trend(xs, ys, ss)
    w = np.asarray(fit["weight_on_data"])
    fitted = np.asarray(fit["fitted"])
    cov = np.asarray(fit["line_cov"])
    line = rng.multivariate_normal(fitted, cov, size=size,
                                   method="eigh")           # (size, n)
    resid = rng.normal(size=(size, n)) * np.sqrt(w) * ss
    draws = w * ys + (1.0 - w) * line + resid
    return np.clip(draws, 0.0, 1.0)
