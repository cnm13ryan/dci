"""Ladder quality: does severity move difficulty predictably?

A severity parameter is only useful if it changes the model's difficulty in
a reasonably predictable direction. Four cheap diagnostics per family over
its measured rungs, ordered by **restrictiveness** (§13.8's structural order,
not raw severity, because a budget loosens upward and an exact count loosens
downward):

* Spearman rank correlation between restrictiveness and posterior-mean iota
  (a clean ladder is strongly negative: more restrictive is harder);
* the number of *significant* direction reversals --- consecutive steps in
  which iota rises with restrictiveness by more than one standard error of
  the step;
* a weighted least-squares slope of iota on restrictiveness rank and its SE;
* the effective difficulty range: the 68% conservative span.

The classification is coarse on purpose --- strong / usable-but-noisy / flat
/ non-monotonic --- and its cut-offs are development choices recorded in
``LADDER_CUTOFFS``. No registered rule requires monotonicity (v6 E5 says so:
"a rung that fails to move iota outward is a measurement, not an error"), and
this module does not make one; it exists so that calibration budget is not
spent on families whose severity barely changes difficulty.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from dci1v7.stages.selection import restrictiveness_key
from dci1v8dev.prescreen.statistics import conservative_span

__all__ = [
    "LADDER_CLASSES",
    "LADDER_CUTOFFS",
    "ladder_diagnostics",
    "spearman",
]

LADDER_CLASSES = ("STRONG_LADDER", "USABLE_NOISY_LADDER", "FLAT_LADDER",
                  "NON_MONOTONIC_LADDER")

#: Development cut-offs. Recorded, not registered.
LADDER_CUTOFFS = {
    "flat_range_max": 0.10,          # 68% conservative span below this
    "flat_slope_z_max": 2.0,         # and |slope| / SE below this -> flat
    "strong_rho_max": -0.80,         # rho at or below this,
    "strong_slope_z_min": 3.0,       # slope z at or above this,
    "strong_range_min": 0.30,        # range at least this -> strong
    "nonmonotonic_rho_min": -0.30,   # rho above this (weak or inverted)
    "nonmonotonic_reversals_min": 2, # or this many significant reversals
}


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None

    def ranks(v: Sequence[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx)
                    * sum((b - my) ** 2 for b in ry))
    return None if den == 0 else num / den


def ladder_diagnostics(kind: str, severities: Sequence[int],
                       iota_mean: Sequence[float], iota_sd: Sequence[float],
                       iota_intervals_68: Sequence[tuple[float, float]]
                       ) -> dict[str, Any]:
    """Diagnostics over rungs with a defined coordinate (nan-free)."""
    rows = [(restrictiveness_key(kind, q), q, m, s, iv)
            for q, m, s, iv in zip(severities, iota_mean, iota_sd,
                                   iota_intervals_68)
            if m is not None and not (isinstance(m, float) and math.isnan(m))]
    rows.sort()
    n = len(rows)
    out: dict[str, Any] = {"family": kind, "n_rungs": n,
                           "severities_by_restrictiveness": [r[1] for r in rows]}
    if n < 3:
        out.update({"rho": None, "reversals": None, "slope": None,
                    "slope_se": None, "slope_z": None, "range_68": 0.0,
                    "ladder_class": "FLAT_LADDER" if n else None,
                    "reason": "fewer than three rungs with a coordinate"})
        return out
    x = np.arange(n, dtype=float)          # restrictiveness rank
    y = np.array([r[2] for r in rows])
    s = np.array([max(r[3], 1e-6) for r in rows])
    rho = spearman(x.tolist(), y.tolist())
    steps = np.diff(y)
    step_se = np.sqrt(s[1:] ** 2 + s[:-1] ** 2)
    reversals = int(np.sum(steps > step_se))   # iota RISING with restrictiveness
    w = 1.0 / s ** 2
    xm, ym = np.average(x, weights=w), np.average(y, weights=w)
    sxx = float(np.sum(w * (x - xm) ** 2))
    slope = float(np.sum(w * (x - xm) * (y - ym)) / sxx)
    slope_se = float(math.sqrt(1.0 / sxx))
    slope_z = slope / slope_se if slope_se > 0 else 0.0
    range_68 = max(0.0, conservative_span([r[4] for r in rows]))
    cut = LADDER_CUTOFFS
    if range_68 <= cut["flat_range_max"] and abs(slope_z) < cut["flat_slope_z_max"]:
        klass = "FLAT_LADDER"
    elif (rho is not None and rho > cut["nonmonotonic_rho_min"]) \
            or reversals >= cut["nonmonotonic_reversals_min"]:
        klass = "NON_MONOTONIC_LADDER"
    elif (rho is not None and rho <= cut["strong_rho_max"]
          and -slope_z >= cut["strong_slope_z_min"]
          and range_68 >= cut["strong_range_min"]):
        klass = "STRONG_LADDER"
    else:
        klass = "USABLE_NOISY_LADDER"
    out.update({"rho": rho, "reversals": reversals, "slope": slope,
                "slope_se": slope_se, "slope_z": slope_z,
                "range_68": range_68, "ladder_class": klass,
                "cutoffs": dict(cut)})
    return out
