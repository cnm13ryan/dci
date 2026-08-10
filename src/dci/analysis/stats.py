"""stats — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from typing import Any, Callable, Iterable, Optional
from scipy import stats


def bootstrap_functional(table: pd.DataFrame,
                         fn: Callable[[pd.Series], dict[str, float]],
                         reps: int, seed: int) -> tuple[pd.Series, pd.DataFrame]:
    """Resample task rows, recompute `fn` on the column means.

    Every quantity `fn` produces comes from the SAME resample, so their joint
    covariance is preserved. Computing them from separate resamples would
    discard exactly the correlation induced by a shared arm.
    """
    observed = fn(table.mean(axis=0))
    keys = list(observed)
    values = table.to_numpy(dtype=float)
    index = list(table.columns)
    n = values.shape[0]
    rng = np.random.default_rng(seed)
    draws = np.empty((reps, len(keys)))
    for r in range(reps):
        idx = rng.integers(0, n, size=n)
        means = pd.Series(np.nanmean(values[idx], axis=0), index=index)
        result = fn(means)
        draws[r] = [result[k] for k in keys]
    return pd.Series(observed, dtype=float), pd.DataFrame(draws, columns=keys)


def bootstrap_se(draws: pd.DataFrame) -> pd.Series:
    """Bootstrap standard error, with an exactly-zero SD mapped to NaN.

    The NaN is a NUMERICAL necessity: studentising by zero is undefined. It is
    NOT a licence to drop the column. A zero empirical resampling variance is a
    DEGENERATE contrast -- every resample produced the identical value -- and a
    degenerate contrast is an unanswered hypothesis, not an absent one. Callers
    must consult `degenerate_components` and fail closed; see
    dci.analysis.claim.reference_robust_claim for the enforcement point.
    """
    return draws.std(axis=0, ddof=1).replace(0.0, np.nan)


def degenerate_components(draws: pd.DataFrame) -> list[str]:
    """Columns whose bootstrap SD is zero or non-finite, in column order.

    These are exactly the columns that a skipna reduction over the max-T family
    would silently omit. Reported so that omission becomes a decision.
    """
    sd = draws.std(axis=0, ddof=1)
    bad = ~np.isfinite(sd.to_numpy(dtype=float)) | (sd.to_numpy(dtype=float) == 0.0)
    return [str(c) for c, flag in zip(draws.columns, bad) if flag]


def percentile_ci(draws: pd.DataFrame, level: float) -> pd.DataFrame:
    a = 1 - level
    return pd.DataFrame({"ci_lower": draws.quantile(a / 2),
                         "ci_upper": draws.quantile(1 - a / 2)})


def simultaneous_bounds(point: pd.Series, draws: pd.DataFrame,
                        level: float) -> pd.DataFrame:
    """Studentised max-T simultaneous intervals over every column at once.

    The returned frame carries the family's own dimensionality in `attrs`, so a
    caller can verify that the family it asked for is the family that was
    calibrated. A degenerate column (zero bootstrap SD) cannot be studentised,
    contributes nothing to the max statistic, and receives NaN bounds; it is
    listed in `attrs["degenerate"]` rather than quietly shrinking the family.
    """
    se = bootstrap_se(draws)
    centred = draws.subtract(point, axis=1)
    studentised = centred.divide(se, axis=1).abs()
    critical = float(np.nanquantile(studentised.max(axis=1).to_numpy(), level))
    out = pd.DataFrame({"estimate": point, "se": se,
                        "sim_lower": point - critical * se,
                        "sim_upper": point + critical * se})
    degenerate = degenerate_components(draws)
    out.attrs["critical_value"] = critical
    out.attrs["n_family_requested"] = int(len(draws.columns))
    out.attrs["n_family_calibrated"] = int(len(draws.columns) - len(degenerate))
    out.attrs["degenerate"] = degenerate
    return out


def simultaneous_abs_upper(point: pd.Series, draws: pd.DataFrame,
                           level: float) -> pd.DataFrame:
    """Simultaneous upper bound on |quantity| for each component.

    This is what an equivalence gate needs: not "is the estimate small" but
    "allowing for uncertainty, and simultaneously across every component, is
    every one of them still small". Averaging cannot rescue a component here,
    because the bound is taken componentwise.
    """
    bounds = simultaneous_bounds(point, draws, level)
    bounds["abs_upper"] = np.maximum(bounds["sim_upper"].abs(),
                                     bounds["sim_lower"].abs())
    return bounds


def bootstrap_p(point: pd.Series, draws: pd.DataFrame, reps: int) -> pd.Series:
    centred = draws.subtract(point, axis=1).abs()
    return centred.ge(point.abs(), axis=1).mean(axis=0).clip(lower=1.0 / max(reps, 1))


def paired_advantage(draws_a: pd.Series, draws_b: pd.Series,
                     level: float) -> dict[str, float]:
    """Is A better (smaller) than B, on the same resample?

    Comparing two point estimates says nothing about whether the difference is
    real. Because both are computed from the same task resample, their paired
    difference has a bootstrap distribution and therefore a bound.
    """
    diff = np.asarray(draws_a, dtype=float) - np.asarray(draws_b, dtype=float)
    return {"mean_difference": float(np.mean(diff)),
            "upper_bound": float(np.quantile(diff, level)),
            "prob_a_not_better": float(np.mean(diff >= 0))}


def holm(pvalues: Iterable[float]) -> list[float]:
    values = list(pvalues)
    order = np.argsort(values)
    n, adjusted, running = len(values), [0.0] * len(values), 0.0
    for rank, idx in enumerate(order):
        running = max(running, (n - rank) * values[idx])
        adjusted[idx] = min(1.0, running)
    return adjusted


def within_sesoi(lower: float, upper: float, sesoi: float) -> bool:
    return bool(lower > -sesoi and upper < sesoi)


def indexed_frame(rows: list[dict[str, Any]], index: str,
                  columns: Optional[list[str]] = None) -> pd.DataFrame:
    """DataFrame.set_index that survives an empty row list.

    Empty is a legitimate result throughout this notebook -- no admissible
    candidate, no hard-eligible constraint -- and it must reach the gate that
    reports it rather than raising a KeyError three frames earlier.
    """
    columns = columns or ([index] if not rows else list(rows[0].keys()))
    if index not in columns:
        columns = [index, *columns]
    return pd.DataFrame(rows, columns=columns).set_index(index)
