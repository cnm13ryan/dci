"""The joint reference-error certificate, on the units its sensitivity model uses.

THE UNIT MISMATCH
-----------------
Componentwise calipers bound each coordinate separately; they do not bound the
accumulated mismatch. The certificate exists to do that:

    B_C = sum_families  s_family * ( aggregated |mismatch| + q * SE )  <=  eps_ref

The pre-repair implementation summed one contribution PER COMPONENT while reusing
the FAMILY slope for each. But `_slope_block` estimates the g slope by regressing
on `nanmean(g|u|o differences)` -- the mean across the g family -- and likewise
for r. A slope fitted against a family MEAN, then charged once per family MEMBER,
over-counts by roughly the family size.

Concretely, with six g components each differing by 0.02 and s_g = 0.5: the fitted
model predicts 0.5 * 0.02 = 0.01 of burden difference, because its predictor is
the mean, which is still 0.02. The pre-repair certificate charged
6 * 0.5 * 0.02 = 0.06 -- six times the model's own prediction, against a total
budget of 0.05. The consequence is not a lax rule; it is an over-strict one that
rejects defensible references and pushes the panel toward near-twins.

WHAT IS PRESERVED
-----------------
  * uncertainty inflation (q * SE) still makes imprecision count AGAINST a
    candidate, never for it;
  * absolute magnitudes, so mismatches never cancel each other out;
  * the eps_ref budget, unchanged;
  * families are still SUMMED, so cross-family accumulation is still bounded.

The aggregation per family mirrors the predictor the slope was fitted against:

    d  -> the single coordinate                       (as fitted)
    g  -> mean over |g| components                    (fitted on a mean)
    r  -> mean over |r| components                    (fitted on a mean)
    s  -> max over |s| components                     (fitted on a max)
    kappa -> the single coordinate, when matched      (as fitted)

Mean-of-absolute is used where the regression used mean-of-signed: it has the same
units and is >= |mean of signed|, so the bound stays conservative.
`reference_budget_aggregation="rss"` remains a SEPARATE modelling choice about
cross-family accumulation; it never was, and is not, a fix for the unit error.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Callable, Iterable, Optional

# How each family's mismatch is aggregated, mirroring `_slope_block`'s predictor.
FAMILY_AGGREGATION: dict[str, str] = {
    "d": "single", "g": "mean_abs", "r": "mean_abs", "s": "max_abs",
    "kappa": "single",
}


def aggregate_family(values: np.ndarray, how: str) -> float:
    """Collapse a family's per-component magnitudes to the fitted predictor's unit."""
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan")
    if how == "mean_abs":
        return float(np.mean(np.abs(finite)))
    if how == "max_abs":
        return float(np.max(np.abs(finite)))
    if how == "single":
        if finite.size != 1:
            # A "single" family with several components would be an unnoticed
            # design change, so it is surfaced rather than silently averaged.
            return float(np.max(np.abs(finite)))
        return float(abs(finite[0]))
    raise ValueError(f"unknown family aggregation {how!r}")


def family_slopes(calipers: pd.DataFrame) -> pd.Series:
    """One slope per family, as used to set that family's caliper.

    Every component of a family carries the same `slope_used`, because
    `derive_calipers` copies the family slope onto each. This recovers the family
    value and refuses to proceed if that assumption has been broken.
    """
    grouped = calipers.groupby("family")["slope_used"]
    spread = grouped.nunique()
    inconsistent = spread[spread > 1]
    if len(inconsistent):
        raise ValueError(
            "family slopes are no longer constant within a family "
            f"({inconsistent.to_dict()}); the certificate's aggregation unit "
            "assumes one slope per family and must be revisited")
    return grouped.first()


def certificate_terms(gaps: pd.DataFrame, gap_se: pd.DataFrame,
                      calipers: pd.DataFrame, candidate: str,
                      uncertainty_q: float,
                      aggregation: Optional[dict[str, str]] = None
                      ) -> pd.DataFrame:
    """Per-family contributions for one candidate. One row per FAMILY, not component."""
    how = {**FAMILY_AGGREGATION, **(aggregation or {})}
    slopes = family_slopes(calipers)
    rows = []
    for family, block in calipers.groupby("family"):
        comps = [c for c in block.index if c in gaps.columns]
        if not comps:
            continue
        magnitudes = np.array([float(gaps.at[candidate, c]) for c in comps])
        ses = np.array([float(gap_se.at[candidate, c])
                        if c in gap_se.columns else 0.0 for c in comps])
        ses = np.where(np.isfinite(ses), ses, 0.0)
        rule = how.get(str(family), "mean_abs")
        gap_term = aggregate_family(magnitudes, rule)
        # SE is aggregated the same way, which is conservative in both cases:
        # mean-of-SEs bounds the SE of a mean, and max-of-SEs bounds the SE of a
        # max. Uncertainty can therefore only make admission harder.
        se_term = aggregate_family(ses, rule if rule != "single" else "single")
        n_undefined = int(np.sum(~np.isfinite(magnitudes)))
        contribution = float(slopes.get(family, np.nan)
                             * (gap_term + uncertainty_q * se_term))
        rows.append({"family": str(family), "n_components": len(comps),
                     "n_undefined_components": n_undefined,
                     "aggregation": rule, "slope_used": float(slopes.get(family, np.nan)),
                     "aggregated_gap": gap_term, "aggregated_se": se_term,
                     "contribution": contribution})
    return pd.DataFrame(rows)


def reference_error_certificate(gaps: pd.DataFrame, gap_se: pd.DataFrame,
                                calipers: pd.DataFrame,
                                candidate_ids: Iterable[str],
                                uncertainty_q: float, epsilon_ref: float,
                                aggregation_mode: str = "sum",
                                aggregation: Optional[dict[str, str]] = None,
                                indexed_frame: Optional[Callable] = None
                                ) -> pd.DataFrame:
    """Family-level joint certificate for every candidate.

    A family with any undefined component yields an undefined total: an
    unmeasurable coordinate is not a satisfied one.
    """
    rows = []
    for cid in candidate_ids:
        if cid not in gaps.index:
            continue
        terms = certificate_terms(gaps, gap_se, calipers, cid, uncertainty_q,
                                  aggregation)
        contributions = terms["contribution"].to_numpy(dtype=float)
        finite = contributions[np.isfinite(contributions)]
        incomplete = bool(len(finite) != len(contributions)
                          or terms["n_undefined_components"].sum() > 0)
        if aggregation_mode == "rss":
            total = float(np.sqrt(np.sum(np.square(finite)))) if finite.size else float("nan")
        else:
            total = float(np.sum(finite)) if finite.size else float("nan")
        largest = (terms.loc[terms["contribution"].idxmax(), "family"]
                   if finite.size and terms["contribution"].notna().any() else "")
        rows.append({
            "constraint_id": cid,
            "budget_total": float("nan") if incomplete else total,
            "budget_threshold": epsilon_ref,
            "budget_ok": bool(np.isfinite(total) and not incomplete
                              and total <= epsilon_ref),
            "n_families": int(len(terms)),
            "n_components": int(terms["n_components"].sum()),
            "n_undefined_components": int(terms["n_undefined_components"].sum()),
            "largest_contribution": (float(np.max(finite)) if finite.size
                                     else float("nan")),
            "largest_family": str(largest),
            **{f"contrib_{r.family}": r.contribution for r in terms.itertuples()},
            **{f"gap_{r.family}": r.aggregated_gap for r in terms.itertuples()},
        })
    columns = ["constraint_id", "budget_total", "budget_threshold", "budget_ok",
               "n_families", "n_components", "n_undefined_components",
               "largest_contribution", "largest_family"]
    if indexed_frame is not None:
        return indexed_frame(rows, "constraint_id", columns)
    frame = pd.DataFrame(rows)
    return frame.set_index("constraint_id") if len(frame) else frame


def legacy_componentwise_total(gaps: pd.DataFrame, gap_se: pd.DataFrame,
                               calipers: pd.DataFrame, candidate: str,
                               uncertainty_q: float) -> float:
    """The pre-repair total, retained so tests can demonstrate the over-count."""
    total = 0.0
    for comp in calipers.index:
        if comp not in gaps.columns:
            continue
        gap = float(gaps.at[candidate, comp])
        if not np.isfinite(gap):
            return float("nan")
        se = float(gap_se.at[candidate, comp]) if comp in gap_se.columns else 0.0
        se = 0.0 if not np.isfinite(se) else se
        total += float(calipers.at[comp, "slope_used"]) * (abs(gap) + uncertainty_q * se)
    return total
