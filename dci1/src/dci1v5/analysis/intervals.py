"""Interval constructions the v5 admission rules read (§13.4, §13.7, §13.8).

Three of them, each registered for a different job and none interchangeable:

* **Wilson** --- a one-sample score interval on a proportion. §13.4 requires
  the 95% Wilson interval for raw solo compliance to lie *inside* the
  admissible band, applied to the interval and not to the point, so that an
  imprecisely measured candidate cannot sit on the boundary. §13.4 also caps
  the Wilson **upper** bound on chance compliance.
* **Newcombe's hybrid score** --- a two-sample interval for a difference of
  proportions. §13.8 condition 2 requires it to *intersect* the registered
  region, which is an inclusion test in the opposite direction from Wilson's
  and is deliberate: condition 2 asks whether the two rates are *compatible*,
  and Wilson's containment asks whether one rate is *pinned*.
* **The percentile bootstrap over topics within split** --- §13.7's
  equivalence test on the split difference. It resamples topics, not draws,
  because the topic is the unit at calibration exactly as the block is at
  confirmation.

**Why §13.7 is an equivalence rule and not a threshold on the difference.** A
threshold on the point difference *rewards* an imprecisely measured
candidate, whose difference is small by luck as often as by stability.
Requiring the interval to lie inside a bound *penalises* imprecision, which is
the correct direction for a gate whose question is "can this candidate's
coordinate be shown stable?".
"""
from __future__ import annotations

import math
from typing import Sequence

from dci1v4.errors import ProtocolError

__all__ = ["Z_95", "wilson", "newcombe_interval", "percentile_interval",
           "bootstrap_difference", "interval_inside", "interval_intersects"]

#: Two-sided 95%.
Z_95 = 1.959963985


def wilson(p: float, n: int, *, z: float = Z_95) -> tuple[float, float]:
    """The Wilson score interval for a proportion.

    ``n`` is the number of independent units the proportion was measured over
    --- topics at calibration, blocks at confirmation --- and never the number
    of draws, because draws within a topic are not independent.
    """
    if not 0.0 <= p <= 1.0:
        raise ProtocolError(f"proportion out of range: {p}")
    if n <= 0:
        return (0.0, 1.0)
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
            / (1 + z * z / n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe_interval(p1: float, n1: int, p2: float, n2: int, *,
                      z: float = Z_95) -> tuple[float, float]:
    """Newcombe's hybrid-score interval for ``p1 - p2``."""
    l1, u1 = wilson(p1, n1, z=z)
    l2, u2 = wilson(p2, n2, z=z)
    lower = (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = (p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (lower, upper)


def percentile_interval(values: Sequence[float], *, level: float = 0.95
                        ) -> tuple[float, float]:
    """The percentile interval of a bootstrap distribution."""
    if not values:
        raise ProtocolError("no bootstrap replicates")
    ordered = sorted(values)
    n = len(ordered)
    alpha = (1.0 - level) / 2.0
    lo = ordered[max(0, min(n - 1, int(math.floor(alpha * n))))]
    hi = ordered[max(0, min(n - 1, int(math.ceil((1.0 - alpha) * n)) - 1))]
    return (lo, hi)


def bootstrap_difference(a: Sequence[float], b: Sequence[float], *,
                         resamples: int, seed: int,
                         level: float = 0.95) -> dict[str, float]:
    """§13.7's percentile bootstrap for the difference of two split means.

    ``a`` and ``b`` are per-topic values on the two splits. Topics are
    resampled **within** split, with replacement, at the split's own size, so
    the interval is about the difference of two independently measured
    quantities rather than about a paired contrast the design does not have:
    the two splits are disjoint topic sets and no topic appears in both.

    Deterministic under the registered seed: the same inputs and seed give the
    same interval, which is what makes an admission verdict reproducible.
    """
    import random

    if not a or not b:
        raise ProtocolError("§13.7 needs values on both calibration splits")
    if resamples <= 0:
        raise ProtocolError("the registered resample count is positive")
    rng = random.Random(seed)
    na, nb = len(a), len(b)
    reps: list[float] = []
    for _ in range(resamples):
        sa = sum(a[rng.randrange(na)] for _ in range(na)) / na
        sb = sum(b[rng.randrange(nb)] for _ in range(nb)) / nb
        reps.append(sa - sb)
    lower, upper = percentile_interval(reps, level=level)
    point = sum(a) / na - sum(b) / nb
    return {"point": point, "lower": lower, "upper": upper,
            "resamples": float(resamples)}


def interval_inside(interval: tuple[float, float],
                    band: tuple[float, float]) -> bool:
    """The whole interval lies inside the band (§13.4, §13.7)."""
    lo, hi = interval
    band_lo, band_hi = band
    return band_lo <= lo and hi <= band_hi


def interval_intersects(interval: tuple[float, float],
                        band: tuple[float, float]) -> bool:
    """The interval and the band overlap (§13.8 condition 2)."""
    lo, hi = interval
    band_lo, band_hi = band
    return not (lo > band_hi or hi < band_lo)
