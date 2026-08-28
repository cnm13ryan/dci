#!/usr/bin/env python3
"""v7 §13.14 boundary audit: does the registered interval procedure cover?

The question is not whether the code implements the intended rule --- the
tests say it does --- but whether the rule itself is valid: when v7 reports a
95% decision interval for ``Delta_R`` with one or more composed rates at or
near 0 or 1, does it contain the true ``Delta_R`` about 95% of the time?

Everything downstream of the data-generating process is the **production
code**: ``ObservationTable`` -> the registered estimators -> ``bootstrap_
family`` at the registered resample count with the F1 family's studentised
maximum-modulus critical value -> ``boundary.contrast_boundary_from_table``
-> ``boundary.apply_allowance`` -> ``claims.Interval`` ->
``claims.delta_r_reading`` / ``claims.contrast_direction``. No estimator,
interval or rule is re-implemented here.

The data-generating process is a paired block design at the registered size
(384 blocks x 8 draws): a topic effect shared by every cell of a block, a
cell-by-topic deviation, and Bernoulli draws --- so the block bootstrap has
something to do, and the paired contrast cancels what pairing is meant to
cancel. A target rate of exactly 0 or 1 is rendered deterministically (a
cell the model genuinely cannot fail or pass); a ``clustered`` rate is a
mixture of perfect blocks and half-rate blocks, which is the worst case for
a block-level boundary bound.

Outputs (machine-readable, under ``dci1/reports/dci1v7/boundary_audit/``):

* ``simulation_<tag>.json``   --- per-scenario aggregates;
* ``replicates_<tag>.jsonl``  --- one line per simulated experiment (gzipped
  after the run to keep the reports tree small);
* ``toy_cases.json``          --- deterministic direction / sign checks.

The counterfactual under a lifted structural-zero veto is carried in every
replicate and aggregate (``counterfactual`` / ``counterfactual_lifted_veto``).

Usage::

    dci1/.venv/bin/python dci1/tools/v7_boundary_audit.py [--reps 1000]
        [--resamples 10000] [--workers 22] [--only high_099,ceil_both]
        [--tau 1.0] [--omega 0.5] [--tag baseline]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from multiprocessing import Pool
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve()
DCI1 = HERE.parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v7.analysis import boundary, claims, estimators
from dci1v7.analysis.bootstrap import bootstrap_family
from dci1v7.analysis.observations import Observation, ObservationTable
from dci1v7.protocol import constants as C

OUT_DIR = DCI1 / "reports" / "dci1v7" / "boundary_audit"
CFG = C.OUTCOME_FIRST
REFS = tuple(C.CORE_SLOTS)
PAIRS = tuple((j, k) for j in REFS for k in REFS if j != k)

# --------------------------------------------------------------- the DGP


@dataclass(frozen=True)
class Rate:
    """A cell's target rate. ``exact`` 0/1 is deterministic; ``clustered``
    is a mixture: a share of blocks at 1 (or 0) and the rest at ``other``."""

    target: float
    clustered_share: float | None = None
    other: float = 0.5

    @property
    def exact(self) -> bool:
        return self.clustered_share is None and self.target in (0.0, 1.0)

    @property
    def mean(self) -> float:
        if self.clustered_share is None:
            return self.target
        edge = 1.0 if self.target >= 0.5 else 0.0
        return (self.clustered_share * edge
                + (1 - self.clustered_share) * self.other)


def R(x: float) -> Rate:
    return Rate(float(x))


@dataclass(frozen=True)
class Scenario:
    name: str
    a: Rate                          # P(B | B+A)
    refs: tuple[Rate, Rate, Rate]    # P(B | B+R_j)
    note: str = ""
    solo_b: Rate = field(default_factory=lambda: R(0.95))
    solo_a: Rate = field(default_factory=lambda: R(0.80))
    a_under_b: Rate = field(default_factory=lambda: R(0.70))
    solo_r: Rate = field(default_factory=lambda: R(0.80))
    r_under_a: Rate = field(default_factory=lambda: R(0.70))
    r_under_r: Rate = field(default_factory=lambda: R(0.72))

    @property
    def true_delta_r(self) -> float:
        return sum(r.mean for r in self.refs) / 3 - self.a.mean

    def true_members(self) -> dict[str, float]:
        """Every F1 member simulated, by linearity of the cell means."""
        d_ba = self.solo_b.mean - self.a.mean
        d_ab = self.solo_a.mean - self.a_under_b.mean
        d_rbar_a = self.solo_r.mean - self.r_under_a.mean
        d_rbar_rbar = self.solo_r.mean - self.r_under_r.mean
        return {"D(B<-A)": d_ba, "D(A<-B)": d_ab, "Lambda": d_ba - d_ab,
                "Delta_R": self.true_delta_r,
                "Xi": self.true_delta_r - (d_rbar_a - d_rbar_rbar)}


def same(x: float) -> tuple[Rate, Rate, Rate]:
    return (R(x), R(x), R(x))


def clustered(share: float, other: float = 0.5, *, edge: float = 1.0) -> Rate:
    return Rate(edge, clustered_share=share, other=other)


SCENARIOS: list[Scenario] = [
    # ---- interior: the reference behaviour of the procedure
    Scenario("interior_null", R(0.70), same(0.70), "Delta_R = 0, interior"),
    Scenario("interior_pos_030", R(0.60), same(0.90), "+0.30: A harms more"),
    Scenario("interior_neg_030", R(0.90), same(0.60), "-0.30: A better"),
    Scenario("sesoi_pos_010", R(0.80), same(0.90), "+0.10 exactly at SESOI"),
    Scenario("sesoi_neg_010", R(0.90), same(0.80), "-0.10 exactly at -SESOI"),
    Scenario("inside_equiv_005", R(0.80), same(0.85), "+0.05 inside region"),
    Scenario("inside_equiv_008", R(0.80), same(0.88), "+0.08 inside region"),
    Scenario("specific_025", R(0.60), same(0.85), "+0.25 at the L3b threshold"),
    Scenario("hetero_refs", R(0.80), (R(0.95), R(0.85), R(0.75)),
             "heterogeneous references, Delta_R = +0.05"),
    # ---- near the ceiling, nothing exact
    Scenario("high_090", R(0.90), same(0.90)),
    Scenario("high_095", R(0.95), same(0.95)),
    Scenario("high_099", R(0.99), same(0.99)),
    Scenario("high_0995", R(0.995), same(0.995)),
    Scenario("high_0999", R(0.999), same(0.999)),
    Scenario("high_09995", R(0.9995), same(0.9995),
             "expected ~1.5 failures per cell; exact tables are common"),
    Scenario("near_ceiling_pos", R(0.85), same(0.99), "+0.14 near ceiling"),
    Scenario("near_ceiling_neg", R(0.99), same(0.85), "-0.14 near ceiling"),
    Scenario("high_unequal_0999_099", R(0.999), same(0.99),
             "-0.009, both arms near ceiling, neither exact"),
    # ---- exact ceilings
    Scenario("ceil_A_099", R(1.0), same(0.99), "A exact, refs 0.99: -0.01"),
    Scenario("ceil_A_095", R(1.0), same(0.95), "A exact, refs 0.95: -0.05"),
    Scenario("ceil_A_090", R(1.0), same(0.90), "A exact, refs 0.90: -0.10"),
    Scenario("ceil_A_0995", R(1.0), same(0.995), "A exact, refs 0.995"),
    Scenario("ceil_A_09995", R(1.0), same(0.9995),
             "A exact, refs 0.9995: structural zero sometimes"),
    Scenario("ceil_R_099", R(0.99), same(1.0), "refs exact, A 0.99: +0.01"),
    Scenario("ceil_both", R(1.0), same(1.0), "shared exact ceiling"),
    Scenario("ceil_A_mixed_refs", R(1.0), (R(1.0), R(1.0), R(0.97)),
             "A and two refs exact, one ref at 0.97: -0.01"),
    # ---- clustered ceilings: the worst case for a block-level bound
    Scenario("ceil_A_clustered_R_001", R(1.0), (clustered(0.99),) * 3,
             "A exact; 1% of blocks half-rate for every ref: -0.005"),
    Scenario("ceil_A_clustered_R_002", R(1.0), (clustered(0.98),) * 3,
             "A exact; 2% of blocks half-rate: -0.01"),
    Scenario("clustered_both_001", clustered(0.99), (clustered(0.99),) * 3,
             "1% half-rate blocks on every arm, Delta_R = 0"),
    # ---- floors (mirror images)
    Scenario("low_010", R(0.10), same(0.10)),
    Scenario("low_005", R(0.05), same(0.05)),
    Scenario("low_001", R(0.01), same(0.01)),
    Scenario("low_0005", R(0.005), same(0.005)),
    Scenario("floor_A_001", R(0.0), same(0.01), "A exact floor, refs 0.01"),
    Scenario("floor_A_005", R(0.0), same(0.05), "A exact floor, refs 0.05"),
    Scenario("floor_R_001", R(0.01), same(0.0), "refs exact floor, A 0.01"),
    Scenario("floor_both", R(0.0), same(0.0), "shared exact floor"),
    Scenario("near_floor_pos", R(0.01), same(0.15), "+0.14 near floor"),
    Scenario("near_floor_neg", R(0.15), same(0.01), "-0.14 near floor"),
]
BY_NAME = {s.name: s for s in SCENARIOS}
assert len(BY_NAME) == len(SCENARIOS)

# Gauss-Hermite nodes for E_z[expit(alpha + s z)], z ~ N(0, 1).
_GH_X, _GH_W = np.polynomial.hermite_e.hermegauss(96)
_GH_W = _GH_W / _GH_W.sum()


def _expit(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def solve_alpha(target: float, s: float) -> float:
    """The logit intercept whose marginal mean under N(0, s^2) is ``target``."""
    if s <= 0:
        return math.log(target / (1 - target))
    lo, hi = -60.0, 60.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        mean = float(np.sum(_GH_W * _expit(mid + s * _GH_X)))
        if mean < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _cell_means(rate: Rate, u: np.ndarray, rng: np.random.Generator, *,
                tau: float, omega: float, m: int) -> np.ndarray:
    n = len(u)
    if rate.clustered_share is not None:
        edge = 1.0 if rate.target >= 0.5 else 0.0
        perfect = rng.random(n) < rate.clustered_share
        p = np.where(perfect, edge, rate.other)
        draws = rng.binomial(m, p) / m
        return np.where(perfect, edge, draws)
    if rate.exact:
        return np.full(n, rate.target)
    alpha = solve_alpha(rate.target, math.sqrt(tau * tau + omega * omega))
    e = rng.normal(0.0, omega, n) if omega > 0 else np.zeros(n)
    p = _expit(alpha + u + e)
    return rng.binomial(m, p) / m


def _obs(block: str, cell: str, outcome: str, companion: str | None,
         value: float, m: int) -> Observation:
    return Observation(
        block_id=block, cell_id=cell, arm="core", outcome_slot=outcome,
        companion_slot=companion, position=1,
        configuration=None if companion is None else CFG, draws=m,
        compliance=float(value), graded=float(value), vacuity=0.0,
        truncation=0.0, non_vacuous_compliance=float(value),
        graded_threshold=float(value), response_words=40.0,
        processing_failures=0, present=True)


def simulate_table(sc: Scenario, rng: np.random.Generator, *, tau: float,
                   omega: float, n: int = C.N_BLOCKS, m: int = C.M_DRAWS
                   ) -> ObservationTable:
    u = rng.normal(0.0, tau, n) if tau > 0 else np.zeros(n)
    kw = {"tau": tau, "omega": omega, "m": m}
    cells: dict[tuple[str, str | None], np.ndarray] = {}
    cells[("B", None)] = _cell_means(sc.solo_b, u, rng, **kw)
    cells[("A", None)] = _cell_means(sc.solo_a, u, rng, **kw)
    cells[("B", "A")] = _cell_means(sc.a, u, rng, **kw)
    cells[("A", "B")] = _cell_means(sc.a_under_b, u, rng, **kw)
    for r, rate in zip(REFS, sc.refs):
        cells[(r, None)] = _cell_means(sc.solo_r, u, rng, **kw)
        cells[("B", r)] = _cell_means(rate, u, rng, **kw)
        cells[(r, "A")] = _cell_means(sc.r_under_a, u, rng, **kw)
    for j, k in PAIRS:
        cells[(j, k)] = _cell_means(sc.r_under_r, u, rng, **kw)
    observations = []
    for b in range(n):
        block = f"b{b:03d}"
        for (outcome, companion), vec in cells.items():
            cell = (f"solo:{outcome}" if companion is None
                    else f"composed:{outcome}+{companion}")
            observations.append(_obs(block, cell, outcome, companion,
                                     vec[b], m))
    return ObservationTable(observations)


def deterministic_table(a: float, refs: tuple[float, float, float], *,
                        n: int = C.N_BLOCKS, m: int = C.M_DRAWS,
                        spread: float = 0.05, nuisance: float = 0.75
                        ) -> ObservationTable:
    """A table whose cell means are fixed numbers: a rate ``r`` alternates
    ``r - spread`` / ``r + spread`` across blocks (mean exactly ``r``), and
    an exact 0 or 1 is exactly that in every block."""
    phases = iter(range(1000))

    def vec(rate: float) -> np.ndarray:
        """Block values with mean exactly ``rate``; each cell gets its own
        phase so the paired contrasts are not constant across blocks."""
        if rate in (0.0, 1.0):
            return np.full(n, rate)
        lo, hi = max(0.0, rate - spread), min(1.0, rate + spread)
        phase = next(phases)
        v = np.where((np.arange(n) * (phase + 2)) % 5 < 2, lo, hi)
        return np.clip(v + (rate - v.mean()), 0.0, 1.0)
    cells = {("B", None): vec(0.95), ("A", None): vec(nuisance),
             ("B", "A"): vec(a), ("A", "B"): vec(nuisance - 0.05)}
    for r, rate in zip(REFS, refs):
        cells[(r, None)] = vec(nuisance)
        cells[("B", r)] = vec(rate)
        cells[(r, "A")] = vec(nuisance - 0.05)
    for j, k in PAIRS:
        cells[(j, k)] = vec(nuisance - 0.03)
    observations = []
    for b in range(n):
        block = f"b{b:03d}"
        for (outcome, companion), v in cells.items():
            cell = (f"solo:{outcome}" if companion is None
                    else f"composed:{outcome}+{companion}")
            observations.append(_obs(block, cell, outcome, companion,
                                     v[b], m))
    return ObservationTable(observations)


# ------------------------------------------------ the production procedure

F1_SIMULATED = ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R", "Xi")


def f1_vectors(table: ObservationTable) -> dict[str, list[float]]:
    return {
        "D(B<-A)": estimators.delivery_loss(table, "B", "A", CFG),
        "D(A<-B)": estimators.delivery_loss(table, "A", "B", CFG),
        "Lambda": estimators.asymmetry(table, CFG),
        "Delta_R": estimators.delta_r(table, CFG),
        "Xi": estimators.xi(table, CFG),
    }


def lifted_veto(reading: dict[str, Any] | None) -> dict[str, Any] | None:
    """The same boundary record with the structural-zero veto removed and
    nothing else changed: the counterfactual rule §2 of the audit asks about."""
    if not reading or not reading.get("structural_zero"):
        return reading
    out = dict(reading)
    out["structural_zero"] = False
    out["statuses"] = [s for s in reading["statuses"]
                       if s != boundary.STRUCTURAL_ZERO]
    return out


def analyse(table: ObservationTable, *, seed: int, resamples: int
            ) -> dict[str, Any]:
    """Run the registered F1 interval procedure on one table and read it."""
    vectors = f1_vectors(table)
    fam = bootstrap_family(vectors, seed=seed, configuration=CFG, family="F1",
                           n_blocks=len(table.blocks), resamples=resamples)
    alone = bootstrap_family({"Delta_R": vectors["Delta_R"]}, seed=seed,
                             configuration=CFG, family="F1",
                             n_blocks=len(table.blocks), resamples=resamples)
    out: dict[str, Any] = {"critical_value": fam.critical_value,
                           "critical_value_alone": alone.critical_value,
                           "members": {}}
    for name, member in fam.members.items():
        reading = boundary.contrast_boundary_from_table(table, name, CFG)
        lower, upper = boundary.apply_allowance(
            member.simultaneous_lower, member.simultaneous_upper, reading)
        out["members"][name] = {
            "estimate": member.estimate, "se": member.standard_error,
            "sim": [member.simultaneous_lower, member.simultaneous_upper],
            "marginal": [member.marginal_lower, member.marginal_upper],
            "decision": [lower, upper],
            "degenerate": member.degenerate,
            "statuses": list(reading["statuses"]) if reading else [],
            "structural_zero": bool(reading and reading["structural_zero"]),
            "allowance": ([reading["allowance_lower"],
                           reading["allowance_upper"]] if reading
                          else [0.0, 0.0]),
        }
    d = fam.members["Delta_R"]
    reading = boundary.contrast_boundary_from_table(table, "Delta_R", CFG)
    lower, upper = boundary.apply_allowance(d.simultaneous_lower,
                                            d.simultaneous_upper, reading)
    interval = claims.Interval("Delta_R", d.estimate, lower, upper,
                               boundary=reading)
    read = claims.delta_r_reading(interval)
    direction = claims.contrast_direction(interval)
    cf = claims.Interval("Delta_R", d.estimate, lower, upper,
                         boundary=lifted_veto(reading))
    cf_read = claims.delta_r_reading(cf)
    cf_dir = claims.contrast_direction(cf)
    a_alone = alone.members["Delta_R"]
    lo_alone, up_alone = boundary.apply_allowance(
        a_alone.simultaneous_lower, a_alone.simultaneous_upper, reading)
    out["delta_r"] = {
        "estimate": d.estimate, "se": d.standard_error,
        "decision": [lower, upper], "sim": [d.simultaneous_lower,
                                            d.simultaneous_upper],
        "marginal": [d.marginal_lower, d.marginal_upper],
        "alone_decision": [lo_alone, up_alone],
        "alone_sim": [a_alone.simultaneous_lower, a_alone.simultaneous_upper],
        "half_width": interval.half_width,
        "meets_precondition": interval.meets_precondition(),
        "levels": read["levels"], "markers": read["markers"],
        "direction": direction["direction"],
        "beyond_sesoi": direction["beyond_sesoi"],
        "statuses": read["statuses"],
        "structural_zero": bool(reading and reading["structural_zero"]),
        "allowance": ([reading["allowance_lower"], reading["allowance_upper"]]
                      if reading else [0.0, 0.0]),
        "compression": ({k: reading["compression"].get(k) for k in
                         ("positive_arm", "negative_arm",
                          "positive_direction_compressed",
                          "negative_direction_compressed")}
                        if reading else None),
        "counterfactual": {"levels": cf_read["levels"],
                           "markers": cf_read["markers"],
                           "direction": cf_dir["direction"]},
    }
    return out


# ------------------------------------------------------------ one replicate

def run_one(args: tuple[str, int, int, float, float]) -> dict[str, Any]:
    name, rep, resamples, tau, omega = args
    sc = BY_NAME[name]
    root = int.from_bytes(name.encode("utf-8")[:8].ljust(8, b"\0"), "big")
    rng = np.random.default_rng([root & 0xFFFFFFFF, rep, 7])
    table = simulate_table(sc, rng, tau=tau, omega=omega)
    boot_seed = (root * 1_000_003 + rep) & 0x7FFFFFFF
    result = analyse(table, seed=boot_seed, resamples=resamples)
    truth = sc.true_members()
    result["scenario"] = name
    result["rep"] = rep
    result["truth"] = truth
    # coverage of every simulated member's simultaneous and decision interval
    for m, entry in result["members"].items():
        t = truth[m]
        entry["covers_sim"] = entry["sim"][0] <= t <= entry["sim"][1]
        entry["covers_decision"] = (entry["decision"][0] <= t
                                    <= entry["decision"][1])
    return result


# --------------------------------------------------------------- aggregation

def _rate(flags: list[bool]) -> float:
    return sum(1 for f in flags if f) / len(flags) if flags else float("nan")


def _mc_se(p: float, n: int) -> float:
    return math.sqrt(max(p * (1 - p), 1e-12) / n) if n else float("nan")


def aggregate(name: str, rows: list[dict[str, Any]], *, tau: float,
              omega: float) -> dict[str, Any]:
    sc = BY_NAME[name]
    t = sc.true_delta_r
    d = [r["delta_r"] for r in rows]
    n = len(rows)

    def covers(key: str) -> list[bool]:
        return [x[key][0] <= t <= x[key][1] for x in d]

    def width(key: str) -> float:
        return float(np.mean([x[key][1] - x[key][0] for x in d]))

    excl = [x["decision"][0] > 0 or x["decision"][1] < 0 for x in d]
    wrong = [((x["decision"][0] > 0 and t <= 0)
              or (x["decision"][1] < 0 and t >= 0)) for x in d]
    right = [((x["decision"][0] > 0 and t > 0)
              or (x["decision"][1] < 0 and t < 0)) for x in d]
    levels: dict[str, int] = {}
    markers: dict[str, int] = {}
    cf_levels: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for x in d:
        for lv in x["levels"]:
            levels[lv] = levels.get(lv, 0) + 1
        for mk in x["markers"]:
            markers[mk] = markers.get(mk, 0) + 1
        for lv in x["counterfactual"]["levels"]:
            cf_levels[lv] = cf_levels.get(lv, 0) + 1
        for st in x["statuses"]:
            statuses[st] = statuses.get(st, 0) + 1
    sim_all = [all(r["members"][m]["covers_sim"] for m in F1_SIMULATED)
               for r in rows]
    dec_all = [all(r["members"][m]["covers_decision"] for m in F1_SIMULATED)
               for r in rows]
    sz = [x["structural_zero"] for x in d]
    cov_dec = _rate(covers("decision"))
    return {
        "scenario": name, "note": sc.note, "n_reps": n,
        "tau": tau, "omega": omega,
        "rates": {"P(B|B+A)": sc.a.mean,
                  "P(B|B+R_j)": [r.mean for r in sc.refs],
                  "exact_A": sc.a.exact,
                  "exact_refs": [r.exact for r in sc.refs]},
        "true_delta_r": t,
        "coverage": {
            "decision_interval": cov_dec,
            "decision_interval_mc_se": _mc_se(cov_dec, n),
            "simultaneous_no_allowance": _rate(covers("sim")),
            "marginal_percentile": _rate(covers("marginal")),
            "delta_r_alone_decision": _rate(covers("alone_decision")),
            "delta_r_alone_no_allowance": _rate(covers("alone_sim")),
            "family_simultaneous_no_allowance": _rate(sim_all),
            "family_simultaneous_decision": _rate(dec_all),
        },
        "width": {
            "decision_interval": width("decision"),
            "simultaneous_no_allowance": width("sim"),
            "marginal_percentile": width("marginal"),
            "delta_r_alone_decision": width("alone_decision"),
            "mean_half_width": float(np.mean([x["half_width"] for x in d])),
            "mean_allowance": [float(np.mean([x["allowance"][0] for x in d])),
                               float(np.mean([x["allowance"][1] for x in d]))],
        },
        "estimate": {"mean": float(np.mean([x["estimate"] for x in d])),
                     "bias": float(np.mean([x["estimate"] for x in d])) - t,
                     "sd": float(np.std([x["estimate"] for x in d], ddof=1))
                     if n > 1 else float("nan"),
                     "mean_bootstrap_se": float(np.mean([x["se"]
                                                         for x in d]))},
        "critical_value": {
            "family_mean": float(np.mean([r["critical_value"] for r in rows])),
            "alone_mean": float(np.mean([r["critical_value_alone"]
                                         for r in rows]))},
        "direction": {
            "claim_rate": _rate(excl),
            "wrong_direction_rate": _rate(wrong),
            "right_direction_rate": _rate(right),
            "labels": {lab: sum(1 for x in d if x["direction"] == lab) / n
                       for lab in claims.DELTA_R_DIRECTIONS},
        },
        "precision_precondition_met": _rate([x["meets_precondition"]
                                             for x in d]),
        "structural_zero_rate": _rate(sz),
        "arm_at_boundary_rate": _rate([boundary.ARM_AT_BOUNDARY in x["statuses"]
                                       for x in d]),
        "range_compressed_rate": _rate([boundary.RANGE_COMPRESSED
                                        in x["statuses"] for x in d]),
        "levels": {k: v / n for k, v in sorted(levels.items())},
        "markers": {k: v / n for k, v in sorted(markers.items())},
        "statuses": {k: v / n for k, v in sorted(statuses.items())},
        "counterfactual_lifted_veto": {
            "levels": {k: v / n for k, v in sorted(cf_levels.items())},
            "l3c_rate": cf_levels.get("L3c", 0) / n,
            "l3c_rate_current": levels.get("L3c", 0) / n,
            "true_inside_equivalence": abs(t) < C.EQUIVALENCE_REGION,
        },
    }


# ----------------------------------------------------------------- toy cases

TOY_CASES = [
    ("case1_A090_R060", 0.90, (0.60, 0.60, 0.60),
     "A permits BETTER B delivery than the references: Delta_R = -0.30"),
    ("case2_A060_R090", 0.60, (0.90, 0.90, 0.90),
     "A does MORE damage to B than the references: Delta_R = +0.30"),
    ("case3_A092_R060", 0.92, (0.60, 0.60, 0.60),
     "as case 1 with the A arm above the 0.90 compression level"),
    ("case4_A060_R092", 0.60, (0.92, 0.92, 0.92),
     "as case 2 with the reference arm above the compression level"),
    ("exact_zero_interior", 0.70, (0.70, 0.70, 0.70),
     "Delta_R = 0 with block variation: no direction"),
    ("near_zero_pos", 0.70, (0.72, 0.72, 0.72), "Delta_R = +0.02"),
    ("near_zero_neg", 0.72, (0.70, 0.70, 0.70), "Delta_R = -0.02"),
    ("shared_ceiling", 1.0, (1.0, 1.0, 1.0), "structural zero at 1"),
    ("shared_floor", 0.0, (0.0, 0.0, 0.0), "structural zero at 0"),
    ("A_ceiling_only", 1.0, (0.95, 0.95, 0.95),
     "A exact ceiling, refs 0.95: Delta_R = -0.05, A better"),
    ("R_ceiling_only", 0.95, (1.0, 1.0, 1.0),
     "refs exact ceiling, A 0.95: Delta_R = +0.05, A harms more"),
    ("A_floor_only", 0.0, (0.05, 0.05, 0.05),
     "A exact floor, refs 0.05: Delta_R = +0.05"),
]


def toy_cases(*, resamples: int) -> list[dict[str, Any]]:
    from dci1v7.protocol import decisions

    # The toy cases run the real L3 emitter, which reads §34 D18. The draft
    # registration has not closed it, so it is forced here to the standing
    # proposal (v5's adopted value) --- a test-only override that writes
    # nothing and is undone below.
    decisions.override_for_testing("D18", "precondition")
    out = []
    for name, a, refs, meaning in TOY_CASES:
        table = deterministic_table(a, refs)
        res = analyse(table, seed=12345, resamples=resamples)
        d = res["delta_r"]
        vec = estimators.delta_r(table, CFG)
        statement = None
        try:
            statement = claims.emit_l3(
                configuration=CFG, cell="B|B+A", outcome_position=1,
                measurement_basis=C.MEASUREMENT_BASIS,
                delta_r=claims.Interval("Delta_R", d["estimate"],
                                        d["decision"][0], d["decision"][1],
                                        boundary=boundary
                                        .contrast_boundary_from_table(
                                            table, "Delta_R", CFG)),
                delta_difficulty=None,
                xi=claims.Interval("Xi", res["members"]["Xi"]["estimate"],
                                   *res["members"]["Xi"]["decision"]),
                support={"holds": False}, references_identified=True,
                delta_near=None, near_form_available=False)
            statement = [{k: s.get(k) for k in
                          ("claim_level", "emitted", "direction", "markers",
                           "identification_status", "l3c_scope",
                           "l3c_scope_sentence", "structural_zero_sentence",
                           "reason")}
                         for s in statement]
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            statement = f"emit_l3 unavailable here: {type(exc).__name__}: {exc}"
        out.append({
            "case": name, "meaning": meaning,
            "P(B|B+A)": a, "P(B|B+R_j)": list(refs),
            "expected_delta_r": sum(refs) / 3 - a,
            "estimator_mean_of_block_vector": float(np.mean(vec)),
            "estimate": d["estimate"],
            "decision_interval": d["decision"],
            "direction_label": d["direction"],
            "direction_reading": claims.contrast_direction(
                claims.Interval("Delta_R", d["estimate"], *d["decision"],
                                boundary=boundary.contrast_boundary_from_table(
                                    table, "Delta_R", CFG)))["reading"],
            "beyond_sesoi": d["beyond_sesoi"],
            "levels": d["levels"], "markers": d["markers"],
            "statuses": d["statuses"],
            "structural_zero": d["structural_zero"],
            "allowance": d["allowance"],
            "compression": d["compression"],
            "counterfactual_lifted_veto": d["counterfactual"],
            "l3_statements": statement,
        })
    decisions.reopen_all_for_testing()
    return out


# ------------------------------------------------------------------- driver

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--resamples", type=int, default=C.BOOTSTRAP_RESAMPLES)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 2))
    ap.add_argument("--only", type=str, default="")
    ap.add_argument("--tau", type=float, default=1.0,
                    help="topic effect sd on the logit scale")
    ap.add_argument("--omega", type=float, default=0.5,
                    help="cell-by-topic deviation sd on the logit scale")
    ap.add_argument("--tag", type=str, default="baseline")
    ap.add_argument("--skip-toys", action="store_true")
    ap.add_argument("--toys-only", action="store_true")
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = ([n for n in args.only.split(",") if n] if args.only
             else [s.name for s in SCENARIOS])
    unknown = [n for n in names if n not in BY_NAME]
    if unknown:
        raise SystemExit(f"unknown scenarios {unknown}")

    started = time.time()
    if not args.skip_toys:
        toys = toy_cases(resamples=args.resamples)
        (OUT_DIR / "toy_cases.json").write_text(json.dumps(
            {"resamples": args.resamples, "n_blocks": C.N_BLOCKS,
             "cases": toys}, indent=1))
        print(f"toy cases written ({time.time() - started:.0f}s)", flush=True)
        if args.toys_only:
            return 0

    jobs = [(n, r, args.resamples, args.tau, args.omega)
            for n in names for r in range(args.reps)]
    print(f"{len(jobs)} experiments on {args.workers} workers "
          f"({args.resamples} resamples each)", flush=True)
    rows_by: dict[str, list[dict[str, Any]]] = {n: [] for n in names}
    rep_path = OUT_DIR / f"replicates_{args.tag}.jsonl"
    with rep_path.open("w") as fh, Pool(args.workers) as pool:
        for done, result in enumerate(
                pool.imap_unordered(run_one, jobs, chunksize=4), start=1):
            rows_by[result["scenario"]].append(result)
            fh.write(json.dumps({
                "scenario": result["scenario"], "rep": result["rep"],
                "delta_r": result["delta_r"],
                "critical_value": result["critical_value"],
                "members": {m: {k: e[k] for k in
                                ("estimate", "sim", "decision", "degenerate",
                                 "structural_zero", "covers_sim",
                                 "covers_decision")}
                            for m, e in result["members"].items()}}) + "\n")
            if done % 500 == 0:
                print(f"  {done}/{len(jobs)} ({time.time() - started:.0f}s)",
                      flush=True)
    summary = {
        "tag": args.tag, "reps": args.reps, "resamples": args.resamples,
        "n_blocks": C.N_BLOCKS, "m_draws": C.M_DRAWS,
        "tau": args.tau, "omega": args.omega,
        "family_simulated": list(F1_SIMULATED),
        "family_registered": list(C.FAMILY_MEMBERS["F1"]),
        "procedure": ("ObservationTable -> estimators -> bootstrap_family "
                      "(studentised max-modulus, F1) -> "
                      "boundary.contrast_boundary_from_table -> "
                      "apply_allowance -> claims.delta_r_reading"),
        "boundary_halfwidth_at_n_blocks": boundary.boundary_halfwidth(
            C.N_BLOCKS),
        "sesoi": C.SMALLEST_EFFECT_OF_INTEREST,
        "precision_precondition_delta_r": C.PRECISION_PRECONDITIONS["Delta_R"],
        "seconds": time.time() - started,
        "scenarios": [aggregate(n, rows_by[n], tau=args.tau, omega=args.omega)
                      for n in names],
    }
    (OUT_DIR / f"simulation_{args.tag}.json").write_text(
        json.dumps(summary, indent=1))
    print(f"wrote {OUT_DIR / f'simulation_{args.tag}.json'} "
          f"({time.time() - started:.0f}s)")
    for s in summary["scenarios"]:
        c = s["coverage"]
        print(f"{s['scenario']:>28} true={s['true_delta_r']:+.4f} "
              f"cov(dec)={c['decision_interval']:.3f} "
              f"cov(sim)={c['simultaneous_no_allowance']:.3f} "
              f"cov(alone)={c['delta_r_alone_decision']:.3f} "
              f"fam={c['family_simultaneous_decision']:.3f} "
              f"w={s['width']['decision_interval']:.4f} "
              f"sz={s['structural_zero_rate']:.3f} "
              f"wrong={s['direction']['wrong_direction_rate']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
