"""Severity-range exploration: reach the difficulty region, do not stop early.

**The audit.** The Tier-1 ladders are q = 1..8 with a frozen reserve to 12
(§7.10). On the 2507 checkpoint 27-29 Tier-1/2 rungs sit above 0.90 solo,
and on every replication §12.6's expansion --- the only rule that measures
the reserve --- never ran, because the 24-topic certificate said C1-C6 held.
So the harder end of every marker ladder has never been generated.

**The rule (prospective).** Two deterministic extension steps, both bounded:

1. *Pre-screen reach.* A family is ``REACH_DEFICIENT`` on a side when the
   posterior probability that it has an admissible rung at or beyond the
   side's offset (``P(support_below)`` / ``P(support_above)``) is below
   ``p_reach``. The second pass then admits, in that family's batch, the
   next ``picks_per_batch`` reserve severities in the deficient direction by
   restrictiveness (v6 E3's ordering), whatever the point estimate says ---
   a noisy 24-topic sample that *appears* to reach the region does not stop
   the extension until the posterior says it does. Bounded by the frozen
   reserve and by ``max_batches``.
2. *Calibration reach.* After calibration, a spectrum-candidate family whose
   admissible rungs still do not reach the region on a side, and whose
   reserve has unmeasured severities in that direction, receives one
   calibration round of up to ``calibration_picks`` reserve rungs on that
   side, at calibration precision. One round, capped, recorded.

``expected_severity_to_reach`` extrapolates a family's calibrated ladder
(logit-linear in severity) to estimate the severity at which it would reach
the region --- a diagnostic of whether the registered reserve is long enough.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci1v7.stages.selection import restrictiveness_key
from dci1v7.verifiers.constraints import LADDERS, RESERVES

__all__ = [
    "ExtensionRule",
    "calibration_extension_plan",
    "expected_severity_to_reach",
    "reach_deficiency",
    "reach_picks",
]


@dataclass(frozen=True)
class ExtensionRule:
    p_reach: float = 0.80
    picks_per_batch: int = 2
    calibration_picks: int = 2
    d_below: float = 0.15
    d_above: float = 0.10


def reach_deficiency(verdict: Mapping[str, Any], *, rule: ExtensionRule
                     ) -> list[str]:
    """Which sides a screened family has not (yet) been shown to reach."""
    p = verdict["probabilities"]
    out = []
    if p["support_below"] < rule.p_reach:
        out.append("below")           # needs HARDER rungs
    if p["support_above"] < rule.p_reach:
        out.append("above")           # needs EASIER rungs
    return out


def _direction_key(kind: str, side: str):
    # below A = harder = more restrictive; above A = easier = less restrictive
    sign = 1 if side == "below" else -1
    return lambda q: sign * restrictiveness_key(kind, q)


def reach_picks(kind: str, *, measured: Sequence[int], sides: Sequence[str],
                n: int) -> list[int]:
    """The next ``n`` unmeasured reserve severities beyond the measured
    extreme on each deficient side, by restrictiveness; deterministic."""
    have = set(measured)
    reserve = [q for q in RESERVES[kind] if q not in have]
    picks: list[int] = []
    for side in sides:
        key = _direction_key(kind, side)
        edge = max(key(q) for q in have) if have else -math.inf
        beyond = sorted((q for q in reserve if key(q) > edge),
                        key=lambda q: (key(q), q))
        picks.extend(beyond[:n])
    return sorted(set(picks))


def calibration_extension_plan(families: Mapping[str, Mapping[str, Any]], *,
                               rule: ExtensionRule) -> dict[str, Any]:
    """``families``: kind -> {"measured": [severities], "reaches_below": bool,
    "reaches_above": bool, "spectrum_candidate": bool}. Returns the reserve
    rungs to calibrate, per family, one round."""
    plan: dict[str, list[int]] = {}
    for kind, f in sorted(families.items()):
        if not f.get("spectrum_candidate"):
            continue
        sides = [s for s in ("below", "above") if not f.get(f"reaches_{s}")]
        if not sides:
            continue
        picks = reach_picks(kind, measured=f["measured"], sides=sides,
                            n=rule.calibration_picks)
        if picks:
            plan[kind] = picks
    return {"round": 1, "picks": plan,
            "n_rungs": sum(len(v) for v in plan.values()),
            "rule": {"calibration_picks": rule.calibration_picks,
                     "d_below": rule.d_below, "d_above": rule.d_above}}


def expected_severity_to_reach(kind: str, ladder: Mapping[int, float], *,
                               target: float) -> dict[str, Any]:
    """Logit-linear extrapolation of solo compliance in severity: the
    severity at which the ladder is expected to cross ``target``."""
    pts = [(q, p) for q, p in sorted(ladder.items()) if 0.01 < p < 0.99]
    if len(pts) < 3:
        return {"family": kind, "estimate": None, "reason": "too few interior rungs"}
    xs = [float(q) for q, _ in pts]
    ys = [math.log(p / (1 - p)) for _, p in pts]
    xm, ym = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - xm) ** 2 for x in xs)
    slope = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    if abs(slope) < 1e-6:
        return {"family": kind, "estimate": None, "reason": "flat ladder",
                "slope": slope}
    intercept = ym - slope * xm
    logit_t = math.log(target / (1 - target))
    q_star = (logit_t - intercept) / slope
    reserve_max = max(RESERVES[kind])
    return {"family": kind, "estimate": q_star, "slope_logit_per_severity": slope,
            "within_ladder": min(LADDERS[kind]) <= q_star <= max(LADDERS[kind]),
            "within_reserve": min(RESERVES[kind]) <= q_star <= reserve_max,
            "reserve_max": reserve_max, "target": target}
