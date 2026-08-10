"""audit_sizing — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
import math
from typing import Callable
from scipy import stats


def wilson_interval(k: int, n: int, confidence: float) -> tuple[float, float]:
    """Wilson score interval. Correct at zero events, where Wald is degenerate."""
    if n <= 0:
        return float("nan"), float("nan")
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def error_ceiling_sample_size(ceiling: float, confidence: float) -> int:
    """Retained for comparison ONLY. This is the rule v14 used, and it is wrong.

    It inverts a one-sided zero-error bound, but Gate M decides on the two-sided
    Wilson upper bound. The two disagree, and they disagree in the unsafe
    direction: this returns 59 for a 5% ceiling, and the Wilson upper bound with
    zero errors in 59 is about 0.061, which does not establish 5%.
    """
    if not 0 < ceiling < 1:
        return 0
    return int(math.ceil(math.log(1 - confidence) / math.log(1 - ceiling)))


def required_cases_for_ceiling(ceiling: float, confidence: float,
                               bound: Callable[[int, int, float], tuple[float, float]]
                               = wilson_interval, cap: int = 100_000) -> int:
    """Smallest n whose zero-error UPPER bound is at or below the ceiling.

    Obtained by numerically inverting the SAME bound function the gate applies,
    so the size that is required and the size that is sufficient cannot drift
    apart. Best case for the audit is zero observed errors, so this is a lower
    bound on what any realised sample needs.
    """
    if not 0 < ceiling < 1:
        return 0
    if cap < 1:
        raise ValueError(f"sample-size cap {cap} is not a usable search bound")
    # Decide feasibility on the cap itself. Doubling from 8 overshoots the cap
    # for most ceilings, and treating "the probe passed the cap" as "no size
    # works" rejects every requirement that sits between the last power of two
    # and the cap. The bound is monotone decreasing in n, so if the cap fails
    # nothing below it can succeed.
    if bound(0, cap, confidence)[1] > ceiling:
        raise ValueError(f"no attainable sample size at or below {cap} for a "
                         f"{ceiling:.3f} ceiling at {confidence:.0%} confidence")
    lo, hi = 1, min(8, cap)
    while hi < cap and bound(0, hi, confidence)[1] > ceiling:
        lo, hi = hi, min(hi * 2, cap)
    while lo < hi:
        mid = (lo + hi) // 2
        if bound(0, mid, confidence)[1] <= ceiling:
            hi = mid
        else:
            lo = mid + 1
    return int(lo)
