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


def component_support(gaps: pd.DataFrame, gap_se: pd.DataFrame,
                      calipers: pd.DataFrame, candidate: str) -> pd.DataFrame:
    """For every DECLARED component: is its gap present and finite, and its SE?

    The declared set is `calipers.index`. Asking the question this way round is
    the whole point: iterating over the columns that happen to exist can only
    ever find components that are there.
    """
    rows = []
    for comp, block in calipers.iterrows():
        has_gap = comp in gaps.columns and candidate in gaps.index
        has_se = comp in gap_se.columns and candidate in gap_se.index
        gap = float(gaps.at[candidate, comp]) if has_gap else float("nan")
        se = float(gap_se.at[candidate, comp]) if has_se else float("nan")
        rows.append({"component": comp, "family": str(block["family"]),
                     "gap_present": bool(has_gap), "se_present": bool(has_se),
                     "gap": gap, "se": se,
                     "gap_finite": bool(np.isfinite(gap)),
                     "se_finite": bool(np.isfinite(se))})
    frame = pd.DataFrame(rows, columns=["component", "family", "gap_present",
                                        "se_present", "gap", "se", "gap_finite",
                                        "se_finite"])
    return frame.set_index("component") if len(frame) else frame


def certificate_terms(gaps: pd.DataFrame, gap_se: pd.DataFrame,
                      calipers: pd.DataFrame, candidate: str,
                      uncertainty_q: float,
                      aggregation: Optional[dict[str, str]] = None
                      ) -> pd.DataFrame:
    """Per-family contributions for one candidate. One row per FAMILY, not component.

    Fail-closed on inputs. A declared coordinate that is absent from `gaps`, or
    whose SE is absent from `gap_se`, makes its family's contribution undefined.
    Two silent substitutions used to live here and both moved admission in the
    permissive direction:

      * a family with no present component was skipped entirely, so the total
        was a sum over FEWER families than the sensitivity model declares - an
        unmeasured coordinate scored as a matched one;
      * a missing or non-finite SE became 0.0, which is the assertion that the
        coordinate was measured with perfect precision. Absent evidence is not
        certainty, and this is the one substitution that can only ever help a
        candidate pass.
    """
    how = {**FAMILY_AGGREGATION, **(aggregation or {})}
    slopes = family_slopes(calipers)
    support = component_support(gaps, gap_se, calipers, candidate)
    rows = []
    for family, block in support.groupby("family"):
        comps = list(block.index)
        magnitudes = block["gap"].to_numpy(dtype=float)
        ses = block["se"].to_numpy(dtype=float)
        rule = how.get(str(family), "mean_abs")
        n_missing = int((~block["gap_present"]).sum())
        n_missing_se = int((~block["se_present"]).sum())
        n_undefined = int((~block["gap_finite"]).sum())
        n_nonfinite_se = int((~block["se_finite"]).sum())
        gap_term = aggregate_family(magnitudes, rule)
        # SE is aggregated the same way, which is conservative in both cases:
        # mean-of-SEs bounds the SE of a mean, and max-of-SEs bounds the SE of a
        # max. Uncertainty can therefore only make admission harder.
        se_term = (aggregate_family(ses, rule if rule != "single" else "single")
                   if not (n_missing_se or n_nonfinite_se) else float("nan"))
        complete = not (n_missing or n_missing_se or n_undefined or n_nonfinite_se)
        contribution = (float(slopes.get(family, np.nan)
                              * (gap_term + uncertainty_q * se_term))
                        if complete else float("nan"))
        rows.append({"family": str(family), "n_components": len(comps),
                     "n_undefined_components": n_undefined,
                     "n_missing_components": n_missing,
                     "n_missing_se": n_missing_se,
                     "n_nonfinite_se": n_nonfinite_se,
                     "complete": complete,
                     "aggregation": rule, "slope_used": float(slopes.get(family, np.nan)),
                     "aggregated_gap": gap_term, "aggregated_se": se_term,
                     "contribution": contribution})
    return pd.DataFrame(rows, columns=[
        "family", "n_components", "n_undefined_components",
        "n_missing_components", "n_missing_se", "n_nonfinite_se", "complete",
        "aggregation", "slope_used", "aggregated_gap", "aggregated_se",
        "contribution"])


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
        declared_families = set(calipers["family"].astype(str))
        # A family the calipers declare but the certificate never saw is the
        # worst case of all: it cannot even appear as a NaN contribution.
        unseen_families = sorted(declared_families - set(terms["family"]))
        incomplete = bool(len(finite) != len(contributions)
                          or unseen_families
                          or not bool(terms["complete"].all())
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
            "certificate_complete": not incomplete,
            "incomplete_reason": _incomplete_reason(terms, unseen_families),
            "n_families": int(len(terms)),
            "n_families_declared": int(len(declared_families)),
            "n_components": int(terms["n_components"].sum()),
            "n_components_declared": int(len(calipers.index)),
            "n_undefined_components": int(terms["n_undefined_components"].sum()),
            "n_missing_components": int(terms["n_missing_components"].sum()),
            "n_missing_se": int(terms["n_missing_se"].sum()),
            "n_nonfinite_se": int(terms["n_nonfinite_se"].sum()),
            "largest_contribution": (float(np.max(finite)) if finite.size
                                     else float("nan")),
            "largest_family": str(largest),
            **{f"contrib_{r.family}": r.contribution for r in terms.itertuples()},
            **{f"gap_{r.family}": r.aggregated_gap for r in terms.itertuples()},
        })
    columns = ["constraint_id", "budget_total", "budget_threshold", "budget_ok",
               "certificate_complete", "incomplete_reason",
               "n_families", "n_families_declared", "n_components",
               "n_components_declared", "n_undefined_components",
               "n_missing_components", "n_missing_se", "n_nonfinite_se",
               "largest_contribution", "largest_family"]
    if indexed_frame is not None:
        return indexed_frame(rows, "constraint_id", columns)
    frame = pd.DataFrame(rows)
    return frame.set_index("constraint_id") if len(frame) else frame


def _incomplete_reason(terms: pd.DataFrame, unseen_families: list) -> str:
    """Why a certificate is incomplete, in the order a reader should act on."""
    reasons = []
    if unseen_families:
        reasons.append(f"declared families absent from the gap table: "
                       f"{unseen_families}")
    for label, column in (("missing coordinates", "n_missing_components"),
                          ("non-finite coordinates", "n_undefined_components"),
                          ("missing SEs", "n_missing_se"),
                          ("non-finite SEs", "n_nonfinite_se")):
        if column in terms and int(terms[column].sum()):
            families = sorted(terms.loc[terms[column] > 0, "family"])
            reasons.append(f"{label} in {families}")
    return "; ".join(reasons)


def assert_certificate_complete(certificate: pd.DataFrame,
                                label: str = "reference certificate") -> None:
    """Refuse to proceed on an incomplete signature.

    `budget_ok` is already False for an incomplete certificate, so admission
    cannot be granted on missing evidence. This raises instead, for the callers
    that must not merely record a rejection: an incomplete signature means the
    construction data is wrong, not that the candidate is unsuitable, and the
    two must never be reported as the same outcome.
    """
    if "certificate_complete" not in certificate:
        return
    bad = certificate[~certificate["certificate_complete"].astype(bool)]
    if len(bad):
        detail = "\n".join(f"  {cid}: {reason}" for cid, reason
                           in bad["incomplete_reason"].items())
        raise ValueError(
            f"{label}: {len(bad)} candidate(s) have an incomplete reference "
            f"signature. A missing coordinate is not a matched coordinate and a "
            f"missing SE is not zero uncertainty:\n{detail}")


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
