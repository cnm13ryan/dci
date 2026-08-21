"""The §11 estimands, computed from block-level cell means.

Every quantity in §11.3 and §11.5 that the 25-cell matrix supplies is here, on
the registered scale (vacuous passes count as passes, §9.3) and on the §17.4
vacuity-forced scale, in each configuration and pooled. Nothing is conditioned
on response length: §13.3 and §22 register length as a mediator, so it is
reported beside the estimand and never inside it.

Uncertainty is a block bootstrap. The block is the unit (§14.1), so a resample
moves every cell of a block together; the order contrast stays paired within
block because §8.4 puts both order variants of every pair in the same block.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from itertools import permutations
from typing import Any, Callable, Mapping, Sequence

REFERENCE_ROLES = ("R1", "R2", "R3")

#: §8.4's registered order. A configuration is not "A first" -- that is only
#: defined for pairs containing A. It is "the constituent earlier in this order
#: is stated first", which applies uniformly to all ten pairs and is what §11.1
#: means by a configuration.
REGISTERED_ORDER = ("A", "B", "R1", "R2", "R3")
CONFIGURATIONS = ("registered_first", "registered_second")


def order_label(roles: tuple[str, str], configuration: str) -> str:
    """The cell's own order label for one configuration of one unordered pair."""
    first, second = sorted(roles, key=REGISTERED_ORDER.index)
    if configuration == "registered_first":
        return f"{first}_first"
    if configuration == "registered_second":
        return f"{second}_first"
    raise ValueError(f"unknown configuration {configuration!r}")


# ------------------------------------------------------------- the cell table
def cell_table(rows: Sequence[Mapping[str, Any]], *, scale: str
               ) -> dict[tuple[str, str, str], dict[str, float]]:
    """(cell key, order label, outcome role) -> {block: mean over draws}.

    ``scale`` is "compliance" for the registered primary scale, or
    "vacuity_forced" for the §17.4 recomputation in which every vacuous pass
    becomes a failure. ``scale`` may also be "vacuity" or "words", which read
    the corresponding per-row field and are diagnostics, never estimands.
    """
    def value(score: Mapping[str, Any]) -> float:
        if scale == "compliance":
            return 1.0 if score["passed"] else 0.0
        if scale == "vacuity_forced":
            return 1.0 if (score["passed"] and score["non_vacuous"]) else 0.0
        if scale == "vacuity":
            return 1.0 if score["vacuous_pass"] else 0.0
        if scale == "graded":
            return float(score["graded"])
        raise ValueError(f"unknown scale {scale!r}")

    buckets: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    for row in rows:
        key = row["cell_key"]
        for score in row["scores"]:
            if scale == "words":
                buckets[(key, row["order_label"], score["role"])][
                    row["topic_id"]].append(float(row["word_count"]))
            else:
                buckets[(key, row["order_label"], score["role"])][
                    row["topic_id"]].append(value(score))
    return {k: {t: sum(v) / len(v) for t, v in blocks.items()}
            for k, blocks in buckets.items()}


def solo_key(role: str) -> str:
    return role


def pair_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


# -------------------------------------------------------- per-block estimands
def per_block_contributions(table: Mapping[tuple[str, str, str], Mapping[str, float]],
                            blocks: Sequence[str], *, order: str | None
                            ) -> dict[str, list[float]]:
    """Every §11 quantity the matrix supplies, as a per-block contribution.

    ``order`` is a §11.1 configuration -- ``"registered_first"`` or
    ``"registered_second"`` -- or ``None``, which averages the two within block.
    Averaging within block is what "pooled" means when order is a within-block
    factor (§8.4); it is not a pooled estimate over two disjoint samples.
    """
    def solo(role: str) -> list[float]:
        cells = table[(solo_key(role), "solo", role)]
        return [cells[b] for b in blocks]

    def composed(outcome: str, companion: str) -> list[float]:
        key = pair_key(outcome, companion)
        if order is not None:
            cells = table[(key, order_label((outcome, companion), order),
                           outcome)]
            return [cells[b] for b in blocks]
        first = table[(key, f"{outcome}_first", outcome)]
        second = table[(key, f"{companion}_first", outcome)]
        return [(first[b] + second[b]) / 2 for b in blocks]

    def loss(outcome: str, companion: str) -> list[float]:
        s, c = solo(outcome), composed(outcome, companion)
        return [a - b for a, b in zip(s, c)]

    n = len(blocks)
    out: dict[str, list[float]] = {}

    out["D_B_from_A"] = loss("B", "A")
    out["D_A_from_B"] = loss("A", "B")
    out["Lambda"] = [x - y for x, y in zip(out["D_B_from_A"], out["D_A_from_B"])]
    out["p_A_solo"] = solo("A")
    out["p_B_solo"] = solo("B")
    out["p_B_with_A"] = composed("B", "A")
    out["p_A_with_B"] = composed("A", "B")

    # §8.6: under the reduced design there are no reference cells, so every
    # reference-dependent quantity is simply absent. §13.5 says that is an
    # identification status and not a failure, and the three quantities above
    # are exactly the ones it says remain available.
    present = {role for (key, _, role) in table if key == role}
    if not set(REFERENCE_ROLES) <= present:
        out["_reduced_design"] = [1.0] * n
        return out

    for j in REFERENCE_ROLES:
        out[f"D_B_from_{j}"] = loss("B", j)
        out[f"D_A_from_{j}"] = loss("A", j)
        out[f"D_{j}_from_A"] = loss(j, "A")
        out[f"D_{j}_from_B"] = loss(j, "B")

    # Delta_R: the solo baseline cancels (§11.3), so it is written that way.
    comp_b_a = composed("B", "A")
    comp_b_r = [composed("B", j) for j in REFERENCE_ROLES]
    out["Delta_R"] = [sum(c[i] for c in comp_b_r) / 3 - comp_b_a[i]
                      for i in range(n)]
    for k, j in enumerate(REFERENCE_ROLES):
        out[f"Delta_{j}"] = [comp_b_r[k][i] - comp_b_a[i] for i in range(n)]

    comp_a_b = composed("A", "B")
    comp_a_r = [composed("A", j) for j in REFERENCE_ROLES]
    out["Delta_A_side"] = [sum(c[i] for c in comp_a_r) / 3 - comp_a_b[i]
                           for i in range(n)]

    # Interference-matrix completion (§11.5).
    out["D_Rbar_from_A"] = [sum(out[f"D_{j}_from_A"][i] for j in REFERENCE_ROLES) / 3
                            for i in range(n)]
    out["D_Rbar_from_B"] = [sum(out[f"D_{j}_from_B"][i] for j in REFERENCE_ROLES) / 3
                            for i in range(n)]
    ordered_pairs = [(j, k) for j, k in permutations(REFERENCE_ROLES, 2)]
    rr = [loss(j, k) for j, k in ordered_pairs]
    out["D_Rbar_from_Rbar_prime"] = [sum(c[i] for c in rr) / len(rr)
                                     for i in range(n)]
    out["Xi"] = [out["Delta_R"][i]
                 - (out["D_Rbar_from_A"][i] - out["D_Rbar_from_Rbar_prime"][i])
                 for i in range(n)]

    # Levels, reported beside the contrasts.
    for role in REFERENCE_ROLES:
        out[f"p_{role}_solo"] = solo(role)
    for k, j in enumerate(REFERENCE_ROLES):
        out[f"p_B_with_{j}"] = comp_b_r[k]
        out[f"p_A_with_{j}"] = comp_a_r[k]
    return out


def spanning_contributions(table, blocks, spanning_roles: Sequence[str]
                           ) -> dict[str, list[float]]:
    """The V5 arm: D(B<-g) with B stated first, and g's own solo compliance."""
    out: dict[str, list[float]] = {}
    for role in spanning_roles:
        solo_cells = table[(solo_key(role), "solo", role)]
        comp = table[(pair_key("B", role), "B_first", "B")]
        b_solo = table[(solo_key("B"), "solo", "B")]
        out[f"p_{role}_solo"] = [solo_cells[b] for b in blocks]
        out[f"D_B_from_{role}"] = [b_solo[b] - comp[b] for b in blocks]
    return out


def class_control_contributions(table, blocks, role: str) -> dict[str, list[float]]:
    """The production-class companion arm.

    ``Delta_class = D(B<-A) - D(B<-CL)`` is the companion swap with the
    companion's structural class held fixed instead of only its difficulty. A
    large Delta_R with a small Delta_class says the excess belongs to the class;
    a large Delta_class says it does not.
    """
    def solo(r):
        cells = table[(solo_key(r), "solo", r)]
        return [cells[b] for b in blocks]

    def composed(outcome, companion):
        key = pair_key(outcome, companion)
        first = table[(key, f"{outcome}_first", outcome)]
        second = table[(key, f"{companion}_first", outcome)]
        return [(first[b] + second[b]) / 2 for b in blocks]

    def loss(outcome, companion):
        return [a - b for a, b in zip(solo(outcome), composed(outcome, companion))]

    out = {
        f"p_{role}_solo": solo(role),
        f"D_B_from_{role}": loss("B", role),
        f"D_A_from_{role}": loss("A", role),
        f"D_{role}_from_B": loss(role, "B"),
        f"D_{role}_from_A": loss(role, "A"),
    }
    out["Delta_class"] = [a - b for a, b in
                          zip(loss("B", "A"), out[f"D_B_from_{role}"])]
    out["Delta_class_A_side"] = [a - b for a, b in
                                 zip(loss("A", "B"), out[f"D_A_from_{role}"])]
    return out


# ----------------------------------------------------------------- inference
def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def _se(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1) / n)


def bootstrap(contributions: Mapping[str, Sequence[float]], *, resamples: int,
              seed: int, family: Sequence[str] | None = None) -> dict[str, Any]:
    """Block bootstrap with studentised maximum-modulus simultaneous intervals
    over ``family`` (default: every key)."""
    names = list(contributions)
    family = list(family or names)
    n = len(contributions[names[0]])
    point = {k: {"estimate": _mean(v), "se": _se(v)}
             for k, v in contributions.items()}
    rng = random.Random(seed)
    draws: dict[str, list[float]] = {k: [] for k in names}
    t_max: list[float] = []
    for _ in range(resamples):
        picked = rng.choices(range(n), k=n)
        worst = 0.0
        for name in names:
            column = contributions[name]
            sample = [column[i] for i in picked]
            estimate = _mean(sample)
            draws[name].append(estimate)
            if name in family:
                se = _se(sample)
                if se and not math.isnan(se) and se > 0:
                    worst = max(worst,
                                abs(estimate - point[name]["estimate"]) / se)
        t_max.append(worst)
    t_max.sort()
    critical = t_max[min(len(t_max) - 1,
                         int(math.ceil(0.95 * len(t_max))) - 1)]
    out: dict[str, Any] = {}
    for name in names:
        column = sorted(draws[name])
        lo = column[max(0, int(math.floor(0.025 * len(column))) - 1)]
        hi = column[min(len(column) - 1,
                        int(math.ceil(0.975 * len(column))) - 1)]
        se = point[name]["se"]
        entry = {"estimate": point[name]["estimate"], "clustered_se": se,
                 "ci95_percentile": [lo, hi],
                 "half_width": (hi - lo) / 2, "blocks": n}
        if name in family and se and not math.isnan(se):
            entry["ci95_simultaneous"] = [
                point[name]["estimate"] - critical * se,
                point[name]["estimate"] + critical * se]
        out[name] = entry
    out["_simultaneous_critical_value"] = critical
    out["_family"] = family
    out["_resamples"] = resamples
    return out


def correlation(x: Sequence[float], y: Sequence[float]) -> float:
    n = len(x)
    mx, my = _mean(x), _mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def bootstrap_statistic(fn: Callable[[Sequence[int]], float], n: int, *,
                        resamples: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    point = fn(list(range(n)))
    draws = sorted(fn(rng.choices(range(n), k=n)) for _ in range(resamples))
    draws = [d for d in draws if not math.isnan(d)]
    if not draws:
        return {"estimate": point, "ci95_percentile": [float("nan")] * 2}
    lo = draws[max(0, int(math.floor(0.025 * len(draws))) - 1)]
    hi = draws[min(len(draws) - 1, int(math.ceil(0.975 * len(draws))) - 1)]
    return {"estimate": point, "ci95_percentile": [lo, hi],
            "resamples": len(draws)}


def weighted_least_squares(xs: Sequence[float], ys: Sequence[float]
                           ) -> dict[str, float]:
    """The companion-difficulty line: D(B<-g) regressed on g's solo compliance."""
    n = len(xs)
    mx, my = _mean(xs), _mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return {"slope": float("nan"), "intercept": float("nan"), "n": n}
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return {"slope": slope, "intercept": my - slope * mx, "n": n}


__all__ = ["REFERENCE_ROLES", "REGISTERED_ORDER", "CONFIGURATIONS",
           "order_label", "class_control_contributions", "cell_table", "per_block_contributions",
           "spanning_contributions", "bootstrap", "bootstrap_statistic",
           "correlation", "weighted_least_squares", "solo_key", "pair_key"]
