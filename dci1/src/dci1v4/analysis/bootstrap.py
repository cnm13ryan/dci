"""The block bootstrap and simultaneous intervals (§15, §17.1).

Nonparametric block bootstrap, 10,000 resamples, seeded from the registration
manifest, resampling the 384 blocks with replacement and carrying **every cell
mean of each drawn block**. Cells are never resampled and no estimator sees a
draw-level index.

Simultaneous intervals are the studentised maximum-modulus construction of
§15: each member is standardised by its bootstrap standard error, the largest
absolute standardised deviation across the family is taken in each resample,
and its 95th percentile is the family's critical value. Marginal percentile
intervals are reported alongside; the decision rules read the simultaneous
intervals.

The bootstrap random-number system is separate from the generation one: a
different root seed and a different domain string (protocol/seeds.py), so a
resample can never consume a generation seed.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C


@dataclass(frozen=True)
class MemberResult:
    name: str
    estimate: float
    standard_error: float
    marginal_lower: float
    marginal_upper: float
    simultaneous_lower: float
    simultaneous_upper: float
    half_width: float


@dataclass(frozen=True)
class FamilyResult:
    family: str
    configuration: str
    resamples: int
    critical_value: float
    members: dict[str, MemberResult]


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _percentile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        raise ProtocolError("empty bootstrap distribution")
    position = q * (len(sorted_values) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return sorted_values[int(position)]
    weight = position - low
    return (sorted_values[low] * (1 - weight)
            + sorted_values[high] * weight)


def bootstrap_family(members: Mapping[str, Sequence[float]], *, seed: int,
                     configuration: str, family: str,
                     resamples: int = C.BOOTSTRAP_RESAMPLES,
                     level: float = 0.95) -> FamilyResult:
    """Studentised maximum-modulus simultaneous intervals for one family."""
    names = list(members)
    if not names:
        raise ProtocolError(f"family {family} has no members")
    lengths = {len(members[name]) for name in names}
    if len(lengths) != 1:
        raise ProtocolError(f"family {family}: members disagree on the block "
                            f"count {sorted(lengths)}")
    n_blocks = lengths.pop()
    if n_blocks < 2:
        raise ProtocolError("the block bootstrap needs at least two blocks")

    estimates = {name: _mean(members[name]) for name in names}
    rng = random.Random(seed)
    replicates: dict[str, list[float]] = {name: [] for name in names}
    index_draws: list[list[int]] = []
    for _ in range(resamples):
        indices = [rng.randrange(n_blocks) for _ in range(n_blocks)]
        index_draws.append(indices)
        for name in names:
            values = members[name]
            replicates[name].append(
                sum(values[i] for i in indices) / n_blocks)

    standard_errors: dict[str, float] = {}
    for name in names:
        centre = _mean(replicates[name])
        variance = sum((v - centre) ** 2 for v in replicates[name]) / (
            resamples - 1)
        standard_errors[name] = math.sqrt(variance)

    max_dev: list[float] = []
    for index in range(resamples):
        worst = 0.0
        for name in names:
            se = standard_errors[name]
            if se <= 0:
                # A degenerate all-identical contrast is retained and reported
                # (§21); it contributes no deviation rather than a non-finite
                # one.
                continue
            worst = max(worst, abs(replicates[name][index] - estimates[name])
                        / se)
        max_dev.append(worst)
    critical = _percentile(sorted(max_dev), level)

    results: dict[str, MemberResult] = {}
    alpha = (1 - level) / 2
    for name in names:
        ordered = sorted(replicates[name])
        se = standard_errors[name]
        estimate = estimates[name]
        lower_sim = estimate - critical * se
        upper_sim = estimate + critical * se
        results[name] = MemberResult(
            name=name, estimate=estimate, standard_error=se,
            marginal_lower=_percentile(ordered, alpha),
            marginal_upper=_percentile(ordered, 1 - alpha),
            simultaneous_lower=lower_sim, simultaneous_upper=upper_sim,
            half_width=(upper_sim - lower_sim) / 2)
    return FamilyResult(family=family, configuration=configuration,
                        resamples=resamples, critical_value=critical,
                        members=results)


def sidak_critical(k: int) -> float:
    """The conservative Šidák reference value for a family of size k (§1).

    Reported beside the bootstrap value; the bootstrap supplies the exact
    critical value and the decision rules read that one.
    """
    from statistics import NormalDist

    if k < 1:
        raise ProtocolError("family size must be positive")
    per_member = 1 - 0.95 ** (1 / k)
    return NormalDist().inv_cdf(1 - per_member / 2)


def assert_resample_shape(table, resamples: int = C.BOOTSTRAP_RESAMPLES,
                          expected_blocks: int | None = None) -> dict[str, Any]:
    """§14.1: each replicate draws exactly the registered number of block
    identifiers with replacement, and each carries the registered cell count."""
    blocks = table.blocks
    if expected_blocks is not None and len(blocks) != expected_blocks:
        raise ProtocolError(f"{len(blocks)} blocks, expected {expected_blocks}")
    per_block: dict[str, int] = {}
    for obs in table.observations:
        per_block[obs.block_id] = per_block.get(obs.block_id, 0) + 1
    counts = set(per_block.values())
    if len(counts) != 1:
        raise ProtocolError(f"blocks carry different cell-mean counts "
                            f"{sorted(counts)}; a drawn block must carry the "
                            f"registered cell count")
    return {"blocks": len(blocks), "cell_means_per_block": counts.pop(),
            "resamples": resamples}
