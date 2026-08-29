"""What replaces C4: coverage of the **selected** spectrum set.

§12.6's C4 asked for six feature groups each containing a family with three
eligible rungs spanning 0.40 --- a statement about the candidate *bank*, on
a within-family span the registered spectrum could not use (its rungs had to
sit inside the folded ±0.10 caliper). It was neither necessary nor sufficient
for the arm it gated.

The replacement is stated on the set the spectrum actually runs, before any
composed cell exists, in the shape §13.13 already uses on the confirmatory
data and with a precision floor that follows from the registered fit:

1. at least ``min_points_below`` spectrum-valid points strictly below A and
   at least ``min_points_above`` strictly above (interpolation, not
   extrapolation);
2. from at least ``min_families_per_side`` families on each side (so one
   family's level does not carry a side);
3. at least one point at or beyond ``d_below`` below A and one at or beyond
   ``d_above`` above (meaningful offsets, asymmetric because the band is);
4. the selected design's projected standard error of the common slope
   under §11.8's family-intercept model, computed from the registered
   confirmatory allocation (384 blocks x M = 8) and the measured
   per-point precision and block correlation, is at most
   ``max_se_beta``; equivalently the within-family leverage
   ``sum_f sum_s (d_fs - dbar_f)^2`` is at least the floor that implies.

Condition 4 is the one that makes "how much spread is needed" a computed
quantity rather than 0.40 by assertion: ``precision.projected_se_beta``.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci1v7.protocol import constants as C
from dci1v7.stages.calibration_table import tie_key
from dci1v8dev import rules as R
from dci1v8dev.spectrum import precision

__all__ = ["DEFAULT_COVERAGE_RULE", "CoverageRule", "selected_coverage"]


@dataclass(frozen=True)
class CoverageRule:
    min_points_below: int = R.SPECTRUM_MIN_POINTS_BELOW          # 2
    min_points_above: int = R.SPECTRUM_MIN_POINTS_ABOVE          # 2
    min_families_per_side: int = R.SPECTRUM_MIN_FAMILIES_PER_SIDE   # 2
    d_below: float = R.SPECTRUM_OFFSET_BELOW
    d_above: float = R.SPECTRUM_OFFSET_ABOVE
    #: Precision floor on the common slope (per unit iota). 0.05 means a 95%
    #: half-width of about 0.10 per unit iota --- the slope resolved to one
    #: SESOI (0.10 of compliance) per unit of difficulty, i.e. to 0.01 over
    #: §13.8's 0.10 caliper. At the registered allocation (384 x 8) and the
    #: measured precision it needs within-family leverage >= 0.027: three
    #: families x two points at ±0.07, or two families at ±0.085
    #: (``precision.design_table``). The old 0.40 span was ~4x that and
    #: unreachable on the easy side of a 0.70-aimed A.
    max_se_beta: float = R.SPECTRUM_MAX_SE_BETA
    #: The selected set's total span (farthest above minus farthest below)
    #: must reach the two offsets together.
    min_total_span: float = R.SPECTRUM_MIN_TOTAL_SPAN
    #: Every selected point's coordinate must be pinned to this SE (from its
    #: per-topic values), the same floor ``validity.SpectrumRule`` applies.
    max_se_iota: float = R.SPECTRUM_MAX_SE_IOTA
    se_point: float = precision.MEASURED["se_point"]
    block_corr: float = precision.MEASURED["block_corr"]


DEFAULT_COVERAGE_RULE = CoverageRule()


def selected_coverage(points: Sequence[Mapping[str, Any]], *, iota_a: float,
                      rule: CoverageRule = DEFAULT_COVERAGE_RULE) -> dict[str, Any]:
    """``points``: ``{"candidate", "family", "iota"}`` for every point the
    fit would use (spectrum references and any core rung of a selected
    family)."""
    below = [p for p in points if tie_key(p["iota"]) < tie_key(iota_a)]
    above = [p for p in points if tie_key(p["iota"]) > tie_key(iota_a)]
    fam_below = {p["family"] for p in below}
    fam_above = {p["family"] for p in above}
    farthest_below = min((p["iota"] for p in below), default=None)
    farthest_above = max((p["iota"] for p in above), default=None)
    reasons: list[str] = []
    if len(below) < rule.min_points_below:
        reasons.append(f"{len(below)} points below A; "
                       f"{rule.min_points_below} required")
    if len(above) < rule.min_points_above:
        reasons.append(f"{len(above)} points above A; "
                       f"{rule.min_points_above} required")
    if len(fam_below) < rule.min_families_per_side:
        reasons.append(f"{len(fam_below)} families below A; "
                       f"{rule.min_families_per_side} required")
    if len(fam_above) < rule.min_families_per_side:
        reasons.append(f"{len(fam_above)} families above A; "
                       f"{rule.min_families_per_side} required")
    if farthest_below is None or iota_a - farthest_below < rule.d_below:
        reasons.append(f"no point at or beyond {rule.d_below} below A")
    if farthest_above is None or farthest_above - iota_a < rule.d_above:
        reasons.append(f"no point at or beyond {rule.d_above} above A")
    total_span = ((farthest_above - farthest_below)
                  if farthest_above is not None and farthest_below is not None
                  else 0.0)
    if total_span < rule.min_total_span:
        reasons.append(f"total span {total_span:.3f} below {rule.min_total_span}")
    imprecise = [p["candidate"] for p in points
                 if p.get("se_iota") is not None and p["se_iota"] > rule.max_se_iota]
    if imprecise:
        reasons.append(f"coordinate SE above {rule.max_se_iota} for {imprecise}")
    proj = precision.projected_se_beta(
        [(p["family"], p["iota"]) for p in points],
        se_point=rule.se_point, block_corr=rule.block_corr)
    if proj["se_beta"] is None or proj["se_beta"] > rule.max_se_beta:
        reasons.append(
            f"projected SE(beta) {proj['se_beta']} above {rule.max_se_beta} "
            f"(within-family leverage {proj['leverage']:.4f})")
    return {"identified": not reasons, "reasons": reasons,
            "n_points": len(points), "n_below": len(below),
            "n_above": len(above), "families_below": sorted(fam_below),
            "families_above": sorted(fam_above),
            "farthest_below": farthest_below, "farthest_above": farthest_above,
            "total_span": total_span, "imprecise": imprecise,
            "n_families": len({p["family"] for p in points}),
            "offset_below": (None if farthest_below is None
                             else iota_a - farthest_below),
            "offset_above": (None if farthest_above is None
                             else farthest_above - iota_a),
            "projection": proj,
            "status": ("DIFFICULTY_SUPPORT_IDENTIFIED" if not reasons
                       else "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"),
            "rule": {"min_points_below": rule.min_points_below,
                     "min_points_above": rule.min_points_above,
                     "min_families_per_side": rule.min_families_per_side,
                     "d_below": rule.d_below, "d_above": rule.d_above,
                     "max_se_beta": rule.max_se_beta,
                     "min_total_span": rule.min_total_span,
                     "max_se_iota": rule.max_se_iota,
                     "se_point": rule.se_point,
                     "block_corr": rule.block_corr}}
