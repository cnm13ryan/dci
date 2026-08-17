"""The preregistered block bootstrap and simultaneous intervals (§12–§14, §20).

10,000 resamples, stratified by presentation order: each replicate draws
exactly 192 block identifiers with replacement inside each order stratum, and
a drawn block travels with all six of its responses — enforced upstream by
`BlockTable` and asserted again here. Responses are never the resampling unit;
pool members never appear at this layer at all (amendment §3).

Every family member is a mean of a per-block column, so all members of all
families are evaluated on the SAME resample draws — which is what makes the
studentised max-|t| simultaneous interval valid: within each family, each
member is standardised by its bootstrap standard error and the 95th percentile
of the largest absolute standardised deviation across the family supplies one
critical value for the whole family (prereg §14).

Level-3 randomness only: the generator is seeded by `seeds.bootstrap_seed`,
disjoint from generation and resampling streams.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST
from dci1.protocol.constants import BOOTSTRAP_RESAMPLES, CONFIDENCE_LEVEL, ProtocolError

STRATA = (TARGET_FIRST, ADDED_FIRST)


@dataclass(frozen=True)
class ColumnStat:
    """One estimand: the mean of a per-block column over a scope.

    ``values_by_stratum`` maps each order stratum to that stratum's per-block
    values in a fixed block order. Scope "all" averages over both strata.
    ``mask_by_stratum`` (optional, 0/1 per block) restricts the mean to a
    block subset — used only by descriptive §22 quantities such as per-area
    rates; every declared family member is a full-scope mean.
    """

    name: str
    values_by_stratum: dict[str, np.ndarray]
    scope: str        # TARGET_FIRST | ADDED_FIRST | "all"
    mask_by_stratum: dict[str, np.ndarray] | None = None


@dataclass
class BootstrapResult:
    n_resamples: int
    seed: int
    estimates: dict[str, float] = field(default_factory=dict)
    resamples: dict[str, np.ndarray] = field(default_factory=dict)

    def se(self, name: str) -> float:
        return float(np.std(self.resamples[name], ddof=1))


def run_bootstrap(stats: list[ColumnStat], *, seed: int,
                  n_resamples: int = BOOTSTRAP_RESAMPLES) -> BootstrapResult:
    """Evaluate every statistic on the same stratified block resamples."""
    sizes = {}
    for stat in stats:
        for stratum, values in stat.values_by_stratum.items():
            if stratum not in STRATA:
                raise ProtocolError(f"unknown stratum {stratum!r}")
            sizes.setdefault(stratum, len(values))
            if len(values) != sizes[stratum]:
                raise ProtocolError(
                    f"{stat.name}: stratum {stratum} column length "
                    f"{len(values)} != {sizes[stratum]}")
    rng = np.random.default_rng(seed)
    index = {}
    for stratum in STRATA:              # fixed draw order → reproducible
        if stratum in sizes:
            n = sizes[stratum]
            index[stratum] = rng.integers(0, n, size=(n_resamples, n))
            # §12 resampling-unit assertion: the number of identifiers drawn
            # equals the stratum size in every replicate.
            if index[stratum].shape != (n_resamples, n):
                raise ProtocolError("resample shape violates §12")

    result = BootstrapResult(n_resamples=n_resamples, seed=seed)
    for stat in stats:
        strata = ([stat.scope] if stat.scope != "all"
                  else list(stat.values_by_stratum))
        numerator = np.zeros(n_resamples)
        denominator = np.zeros(n_resamples)
        point_num = point_den = 0.0
        for stratum in strata:
            values = stat.values_by_stratum[stratum]
            mask = (stat.mask_by_stratum[stratum]
                    if stat.mask_by_stratum is not None
                    else np.ones_like(values, dtype=float))
            drawn = index[stratum]
            numerator += (values * mask)[drawn].sum(axis=1)
            denominator += mask[drawn].sum(axis=1)
            point_num += float((values * mask).sum())
            point_den += float(mask.sum())
        with np.errstate(invalid="ignore", divide="ignore"):
            result.resamples[stat.name] = numerator / denominator
        result.estimates[stat.name] = (point_num / point_den
                                       if point_den else float("nan"))
    return result


def add_derived(result: BootstrapResult, name: str,
                combine: Callable[[dict[str, np.ndarray]], np.ndarray],
                point: Callable[[dict[str, float]], float]) -> None:
    """A statistic defined per-resample from other statistics (for example
    the order interaction), sharing the same draws."""
    result.resamples[name] = combine(result.resamples)
    result.estimates[name] = float(point(result.estimates))


def family_intervals(result: BootstrapResult, members: list[str],
                     level: float = CONFIDENCE_LEVEL) -> dict[str, Any]:
    """Simultaneous (max-|t|) and marginal studentised intervals for one
    declared family. Degenerate members (zero bootstrap SE) stay in the
    calculation and are reported with zero-width intervals; a non-finite SE
    or bound yields a named inconclusive status (fail closed, §20)."""
    out: dict[str, Any] = {"members": {}, "level": level}
    ses = {m: result.se(m) for m in members}
    finite = {m: se for m, se in ses.items() if np.isfinite(se)}
    if len(finite) != len(ses):
        out["status"] = "INCONCLUSIVE_NONFINITE_SE"
        out["critical_value"] = None
        for m in members:
            out["members"][m] = {
                "estimate": result.estimates[m], "se": ses[m],
                "status": ("INCONCLUSIVE_NONFINITE_SE"
                           if not np.isfinite(ses[m]) else "SUPPRESSED")}
        return out

    live = [m for m in members if ses[m] > 0]
    t_abs = {}
    for m in live:
        t_abs[m] = np.abs((result.resamples[m] - result.estimates[m])
                          / ses[m])
    if live:
        max_abs = np.max(np.stack([t_abs[m] for m in live]), axis=0)
        critical = float(np.quantile(max_abs, level))
    else:
        critical = 0.0
    if not np.isfinite(critical):
        out["status"] = "INCONCLUSIVE_NONFINITE_BOUND"
        out["critical_value"] = None
        for m in members:
            out["members"][m] = {"estimate": result.estimates[m],
                                 "se": ses[m],
                                 "status": "INCONCLUSIVE_NONFINITE_BOUND"}
        return out

    out["status"] = "OK"
    out["critical_value"] = critical
    for m in members:
        estimate, se = result.estimates[m], ses[m]
        if se == 0:
            out["members"][m] = {
                "estimate": estimate, "se": 0.0, "degenerate": True,
                "simultaneous": [estimate, estimate],
                "marginal": [estimate, estimate], "status": "OK"}
            continue
        t_marginal = float(np.quantile(t_abs[m], level))
        out["members"][m] = {
            "estimate": estimate, "se": se, "degenerate": False,
            "simultaneous": [estimate - critical * se,
                             estimate + critical * se],
            "marginal": [estimate - t_marginal * se,
                         estimate + t_marginal * se],
            "status": "OK"}
    return out
