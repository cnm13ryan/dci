"""The block bootstrap and simultaneous intervals (§15, §17.1, §17.2).

Nonparametric block bootstrap, 10,000 resamples, seeded from the registration
manifest, resampling blocks with replacement and carrying **every cell mean of
each drawn block**. Cells are never resampled and no estimator sees a
draw-level index. The bootstrap random-number system is separate from the
generation one --- a different root seed and a different domain string --- so a
resample can never consume a generation seed.

Simultaneous intervals are §15's studentised maximum-modulus construction:
each member is standardised by its bootstrap standard error, the largest
absolute standardised deviation across the family is taken in each resample,
and its 95th percentile is the family's critical value.

**Why a member may be a function and not a vector.** For most members a
replicate is the mean of the drawn blocks' values, so a per-block vector is a
complete description and resampling is an average. `delta_difficulty` is not
like that: §17.2 requires every replicate to resample blocks, recompute the
cell means, recompute the sample-dependent difficulty quantities, **refit the
non-A relation, predict at A**, and recompute the residual. Fitting the curve
once and bootstrapping only the final residual would treat the fitted
coefficients as constants and understate the interval.

So a member is either a `Sequence[float]` --- one value per block, resampled by
averaging --- or a callable taking the replicate's index vector and returning
that replicate's estimate. Both kinds share **one** index draw per replicate,
which is what keeps the family's simultaneous intervals coherent: the same
resampled blocks underlie `Delta_R` and `delta_difficulty` in every replicate,
so their joint variation is the real one.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C

__all__ = ["MemberResult", "FamilyResult", "bootstrap_family",
           "sidak_critical", "assert_resample_shape", "Member"]

#: One value per block, or a function of the replicate's index vector.
Member = Sequence[float] | Callable[[Sequence[int]], float]


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
    refit_per_replicate: bool
    degenerate: bool


@dataclass(frozen=True)
class FamilyResult:
    family: str
    configuration: str
    resamples: int
    critical_value: float
    members: dict[str, MemberResult]
    blocks: int


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _percentile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        raise ProtocolError("empty bootstrap distribution")
    position = q * (len(sorted_values) - 1)
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return sorted_values[int(position)]
    weight = position - low
    return (sorted_values[low] * (1 - weight)
            + sorted_values[high] * weight)


def _is_callable_member(member: Member) -> bool:
    return callable(member)


def bootstrap_family(members: Mapping[str, Member], *, seed: int,
                     configuration: str, family: str, n_blocks: int,
                     resamples: int = C.BOOTSTRAP_RESAMPLES,
                     level: float = 0.95) -> FamilyResult:
    """Studentised maximum-modulus simultaneous intervals for one family.

    ``n_blocks`` is required rather than inferred, because a callable member
    carries no length and a family may consist only of callable members.
    """
    names = list(members)
    if not names:
        raise ProtocolError(f"family {family} has no members")
    if n_blocks < 2:
        raise ProtocolError("the block bootstrap needs at least two blocks")
    for name in names:
        member = members[name]
        if not _is_callable_member(member) and len(member) != n_blocks:
            raise ProtocolError(
                f"family {family}: member {name!r} has {len(member)} blocks, "
                f"not {n_blocks}")

    identity = list(range(n_blocks))
    estimates = {
        name: (members[name](identity) if _is_callable_member(members[name])
               else _mean(members[name]))
        for name in names}

    rng = random.Random(seed)
    replicates: dict[str, list[float]] = {name: [] for name in names}
    for _ in range(resamples):
        # ONE index draw per replicate, shared by every member of the family.
        indices = [rng.randrange(n_blocks) for _ in range(n_blocks)]
        for name in names:
            member = members[name]
            if _is_callable_member(member):
                replicates[name].append(float(member(indices)))
            else:
                replicates[name].append(
                    sum(member[i] for i in indices) / n_blocks)

    standard_errors: dict[str, float] = {}
    for name in names:
        finite = [v for v in replicates[name] if v == v and abs(v) != math.inf]
        if len(finite) < 2:
            standard_errors[name] = 0.0
            continue
        centre = _mean(finite)
        variance = sum((v - centre) ** 2 for v in finite) / (len(finite) - 1)
        standard_errors[name] = math.sqrt(variance)

    max_dev: list[float] = []
    for index in range(resamples):
        worst = 0.0
        for name in names:
            se = standard_errors[name]
            value = replicates[name][index]
            if se <= 0 or value != value:
                # A degenerate all-identical contrast, or a replicate in which
                # a refit was not identified, is retained and reported (§21).
                # It contributes no deviation rather than a non-finite one.
                continue
            worst = max(worst, abs(value - estimates[name]) / se)
        max_dev.append(worst)
    critical = _percentile(sorted(max_dev), level)

    results: dict[str, MemberResult] = {}
    alpha = (1 - level) / 2
    for name in names:
        ordered = sorted(v for v in replicates[name] if v == v)
        se = standard_errors[name]
        estimate = estimates[name]
        results[name] = MemberResult(
            name=name, estimate=estimate, standard_error=se,
            marginal_lower=_percentile(ordered, alpha) if ordered else
            float("nan"),
            marginal_upper=_percentile(ordered, 1 - alpha) if ordered else
            float("nan"),
            simultaneous_lower=estimate - critical * se,
            simultaneous_upper=estimate + critical * se,
            half_width=critical * se,
            refit_per_replicate=_is_callable_member(members[name]),
            degenerate=se <= 0)
    return FamilyResult(family=family, configuration=configuration,
                        resamples=resamples, critical_value=critical,
                        members=results, blocks=n_blocks)


def sidak_critical(k: int) -> float:
    """The conservative Šidák reference value for a family of size k.

    Reported beside the bootstrap value; the bootstrap supplies the exact
    critical value and the decision rules read that one.
    """
    from statistics import NormalDist

    if k < 1:
        raise ProtocolError("family size must be positive")
    per_member = 1 - 0.95 ** (1 / k)
    return NormalDist().inv_cdf(1 - per_member / 2)


def assert_resample_shape(table: Any, *,
                          resamples: int = C.BOOTSTRAP_RESAMPLES,
                          expected_blocks: int | None = None
                          ) -> dict[str, Any]:
    """§14.1: every drawn block carries the registered cell count."""
    blocks = table.blocks
    if expected_blocks is not None and len(blocks) != expected_blocks:
        raise ProtocolError(f"{len(blocks)} blocks, expected {expected_blocks}")
    per_block: dict[str, int] = {}
    for obs in table.observations:
        per_block[obs.block_id] = per_block.get(obs.block_id, 0) + 1
    counts = set(per_block.values())
    if len(counts) != 1:
        raise ProtocolError(
            f"blocks carry different cell-mean counts {sorted(counts)}; a "
            f"drawn block must carry the registered cell count")
    return {"blocks": len(blocks), "cell_means_per_block": counts.pop(),
            "resamples": resamples}
