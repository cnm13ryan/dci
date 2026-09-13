"""Wilson and Newcombe intervals (§10.3, §13.2).

Two registered interval methods live here and nowhere else:

* the **one-sided 95% Wilson upper bound** on human-to-verifier disagreement
  (§10.3), computed per verifier class and, within the fail class, separately
  on items whose realised margin is exactly one and on items with larger
  margins;
* the **95% Newcombe interval for a paired difference** (§13.2 condition 1),
  which the reference caliper requires to intersect ±0.05.

Newcombe's method for paired proportions needs a paired 2x2 table, and the
calibration data are cell means over M draws rather than single Bernoulli
trials. The registered pairing is stated here rather than left implicit: a
draw of the A solo cell is paired with the draw of the same index on the same
topic, giving 96 x M paired observations. Draws are exchangeable within a cell,
so the index is a labelling convention and not a scientific choice; the
clustered paired standard error is reported beside the interval so the
dependence the pairing ignores stays visible.
"""
from __future__ import annotations

import math
from typing import Sequence

from dci1v4.errors import ProtocolError

_Z_95_TWO_SIDED = 1.959963984540054
_Z_95_ONE_SIDED = 1.6448536269514722


def wilson_interval(successes: int, total: int, *,
                    z: float = _Z_95_TWO_SIDED) -> tuple[float, float]:
    """The Wilson score interval for a binomial proportion."""
    if total <= 0:
        raise ProtocolError("Wilson interval needs a positive denominator")
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    spread = (z * math.sqrt(p * (1 - p) / total
                            + z * z / (4 * total * total)) / denominator)
    return max(0.0, centre - spread), min(1.0, centre + spread)


def wilson_upper_bound(successes: int, total: int, *,
                       z: float = _Z_95_ONE_SIDED) -> float:
    """The one-sided 95% Wilson upper bound (§10.3)."""
    return wilson_interval(successes, total, z=z)[1]


def paired_table(a: Sequence[int], b: Sequence[int]) -> tuple[int, int, int,
                                                              int]:
    """The paired 2x2 table (n11, n12, n21, n22) from two 0/1 sequences."""
    if len(a) != len(b):
        raise ProtocolError("paired sequences differ in length")
    n11 = sum(1 for x, y in zip(a, b) if x and y)
    n12 = sum(1 for x, y in zip(a, b) if x and not y)
    n21 = sum(1 for x, y in zip(a, b) if not x and y)
    n22 = sum(1 for x, y in zip(a, b) if not x and not y)
    return n11, n12, n21, n22


def newcombe_paired(n11: int, n12: int, n21: int, n22: int, *,
                    z: float = _Z_95_TWO_SIDED) -> dict[str, float]:
    """Newcombe's hybrid score interval for a paired difference of
    proportions, with the correlation correction.

    ``p1`` is the row proportion (n11 + n12) / n and ``p2`` the column
    proportion (n11 + n21) / n; the interval is for ``p1 - p2``.
    """
    n = n11 + n12 + n21 + n22
    if n <= 0:
        raise ProtocolError("the paired table is empty")
    p1 = (n11 + n12) / n
    p2 = (n11 + n21) / n
    l1, u1 = wilson_interval(n11 + n12, n, z=z)
    l2, u2 = wilson_interval(n11 + n21, n, z=z)

    denominator = ((n11 + n12) * (n21 + n22) * (n11 + n21) * (n12 + n22))
    if denominator <= 0:
        phi = 0.0
    else:
        phi = (n11 * n22 - n12 * n21) / math.sqrt(denominator)
        phi = max(-1.0, min(1.0, phi))

    lower_term = ((p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2)
                  + (u2 - p2) ** 2)
    upper_term = ((u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2)
                  + (p2 - l2) ** 2)
    lower = (p1 - p2) - math.sqrt(max(0.0, lower_term))
    upper = (p1 - p2) + math.sqrt(max(0.0, upper_term))
    return {"difference": p1 - p2, "lower": lower, "upper": upper,
            "p1": p1, "p2": p2, "phi": phi, "n": n}


def intersects(interval: dict[str, float], region: float) -> bool:
    """Whether an interval intersects the symmetric region ±``region``."""
    return not (interval["upper"] < -region or interval["lower"] > region)


def clustered_paired_se(differences: Sequence[float]) -> float:
    """The paired standard error over blocks, ignoring nothing.

    Reported beside the Newcombe interval: the Newcombe pairing treats draws as
    independent, and this figure carries the topic-level dependence that
    §13.2's 0.038 estimate refers to.
    """
    if len(differences) < 2:
        return float("nan")
    mean = sum(differences) / len(differences)
    variance = sum((d - mean) ** 2 for d in differences) / (
        len(differences) - 1)
    return math.sqrt(variance / len(differences))
