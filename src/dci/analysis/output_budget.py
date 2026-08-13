"""The output-budget artefact: is the study measuring the constraint or the cap?

WHY THIS IS NOT A NUISANCE METRIC
---------------------------------
Different added constraints imply different amounts of required output. With
A = "exactly four sentences", B = "strictly increasing sentence lengths" can be
satisfied in about ten words, while a reference requiring fifteen words per
sentence needs at least sixty. The generation ceiling is 180 TOKENS, and it is a
property of the apparatus, not of the science.

So the causal chain splits in two:

    constraint -> longer required output                 <- part of the effect
    longer required output -> hits the cap -> censored   <- an instrument artefact

The second arrow can invent or reverse a result. If the longer reference arm is
truncated more often, measured reference failure rises and tau falls; a genuine
+0.10 can present as -0.05.

WHAT THIS MODULE MAY AND MAY NOT DO
-----------------------------------
Truncation is POST-TREATMENT. Dropping truncated rows, or conditioning tau on
rows that terminated cleanly, would condition on an outcome of the treatment and
is never done here. The only permitted responses are: measure it, report it by
arm, and refuse to interpret the primary result when the preregistered condition
is breached. Nothing in this module edits an outcome.

Pre-repair, `output_cap_report` existed with zero call sites, both declared
thresholds had zero consumers, and the OUTPUT_CAP_DOMINATES status was
unreachable. The safeguard was inert.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Iterable, Optional

TERMINATION_FIELDS = ("generated_token_count", "ended_with_eos",
                      "hit_max_new_tokens", "output_truncated", "stop_reason")


def termination_coverage(scored: pd.DataFrame) -> dict[str, float]:
    """How much of the frame actually carries termination metadata.

    A cap gate that runs on missing metadata reports 0.00 truncation and passes,
    which is exactly how the pre-repair cache path would have failed open. This
    is the number that makes that impossible.
    """
    n = int(len(scored))
    if not n:
        return {"rows": 0, "with_metadata": 0, "coverage": float("nan")}
    if "output_truncated" not in scored.columns:
        return {"rows": n, "with_metadata": 0, "coverage": 0.0}
    have = int(scored["output_truncated"].notna().sum())
    return {"rows": n, "with_metadata": have, "coverage": have / n}


def termination_report(scored: pd.DataFrame, by: Iterable[str]) -> pd.DataFrame:
    """Truncation, cap-hit and length statistics per arm. Reported, never adjusted."""
    by = [c for c in by if c in scored.columns]
    if not by or "output_truncated" not in scored.columns:
        return pd.DataFrame()
    frame = scored.copy()
    for col in ("output_truncated", "hit_max_new_tokens", "ended_with_eos"):
        if col in frame.columns:
            frame[col] = frame[col].map(
                lambda v: np.nan if v is None or (isinstance(v, float) and np.isnan(v))
                else bool(v)).astype(float)
    grouped = frame.groupby(by, dropna=False).agg(
        n=("row_id", "size"),
        n_with_metadata=("output_truncated", "count"),
        truncated_share=("output_truncated", "mean"),
        hit_cap_share=("hit_max_new_tokens", "mean"),
        eos_share=("ended_with_eos", "mean"),
        mean_generated_tokens=("generated_token_count", "mean"),
        p90_generated_tokens=("generated_token_count",
                              lambda s: float(np.nanpercentile(
                                  pd.to_numeric(s, errors="coerce").dropna(), 90))
                              if pd.to_numeric(s, errors="coerce").notna().any()
                              else np.nan),
        max_generated_tokens=("generated_token_count", "max"))
    return grouped.reset_index()


def arm_gap(report: pd.DataFrame, arm_column: str, focal: str,
            references: Iterable[str], metric: str = "truncated_share"
            ) -> pd.DataFrame:
    """Focal-minus-reference difference in truncation, per reference.

    The absolute level matters, but the DIFFERENTIAL is what biases tau: a cap
    that truncates both arms equally shifts both measured failure rates, while a
    cap that truncates one arm more manufactures a contrast.
    """
    if report.empty or arm_column not in report.columns:
        return pd.DataFrame()
    keys = [c for c in report.columns
            if c not in (arm_column, "n", "n_with_metadata", "truncated_share",
                         "hit_cap_share", "eos_share", "mean_generated_tokens",
                         "p90_generated_tokens", "max_generated_tokens")]
    rows = []
    for key, block in (report.groupby(keys, dropna=False) if keys
                       else [((), report)]):
        indexed = block.set_index(arm_column)
        if focal not in indexed.index:
            continue
        focal_value = float(indexed.at[focal, metric])
        for ref in references:
            if ref not in indexed.index:
                continue
            ref_value = float(indexed.at[ref, metric])
            entry = dict(zip(keys, key if isinstance(key, tuple) else (key,)))
            rows.append({**entry, "reference": ref, "metric": metric,
                         "focal_value": focal_value, "reference_value": ref_value,
                         "gap": focal_value - ref_value,
                         "abs_gap": abs(focal_value - ref_value)})
    return pd.DataFrame(rows)


def cap_verdict(report: pd.DataFrame, gaps: pd.DataFrame, warn_share: float,
                stop_share: float, max_arm_gap: float,
                coverage: Optional[dict] = None,
                min_coverage: float = 1.0) -> dict:
    """Apply the preregistered output-budget conditions.

    Three independent triggers, each with its own reason string:
      * absolute  -- any reported cell above `stop_share` (the declared rule:
                     "above this share of truncated outputs in any reported cell
                     ... the run stops");
      * differential -- any focal-versus-reference truncation gap above
                     `max_arm_gap`, which is the condition that biases tau;
      * coverage  -- termination metadata missing, so the other two cannot be
                     evaluated and must not be reported as satisfied.
    """
    reasons: list[str] = []
    warnings: list[str] = []
    over_absolute, over_differential = pd.DataFrame(), pd.DataFrame()

    cov = coverage or {}
    coverage_value = float(cov.get("coverage", float("nan")))
    coverage_ok = bool(np.isfinite(coverage_value) and coverage_value >= min_coverage)
    if not coverage_ok:
        reasons.append(
            f"termination metadata cover {coverage_value:.3f} of rows "
            f"(required {min_coverage:.3f}); the output-cap condition cannot be "
            "evaluated and must not be recorded as satisfied")

    if not report.empty and "truncated_share" in report.columns:
        share = pd.to_numeric(report["truncated_share"], errors="coerce")
        over_absolute = report[share > stop_share]
        warn_rows = report[(share > warn_share) & (share <= stop_share)]
        if len(over_absolute):
            reasons.append(
                f"{len(over_absolute)} reported cell(s) exceed the declared stop "
                f"share {stop_share:.2f} (worst {float(share.max()):.3f})")
        if len(warn_rows):
            warnings.append(
                f"{len(warn_rows)} cell(s) above the warn share {warn_share:.2f}")

    if not gaps.empty:
        gap = pd.to_numeric(gaps["abs_gap"], errors="coerce")
        over_differential = gaps[gap > max_arm_gap]
        if len(over_differential):
            reasons.append(
                f"{len(over_differential)} focal-vs-reference truncation gap(s) "
                f"exceed {max_arm_gap:.2f} (worst {float(gap.max()):.3f}); "
                "differential censoring biases tau in the direction of the less "
                "truncated arm")

    return {
        "ok": not reasons,
        "reasons": reasons,
        "warnings": warnings,
        "coverage": coverage_value,
        "coverage_ok": coverage_ok,
        "n_cells": int(len(report)),
        "worst_truncated_share": (float(pd.to_numeric(
            report["truncated_share"], errors="coerce").max())
            if not report.empty and "truncated_share" in report.columns
            else float("nan")),
        "worst_abs_arm_gap": (float(pd.to_numeric(gaps["abs_gap"],
                                                  errors="coerce").max())
                              if not gaps.empty else float("nan")),
        "cells_over_stop_share": over_absolute,
        "gaps_over_tolerance": over_differential,
        "thresholds": {"warn_share": warn_share, "stop_share": stop_share,
                       "max_arm_gap": max_arm_gap,
                       "min_metadata_coverage": min_coverage},
    }
