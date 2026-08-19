"""Manipulation, compliance and arm-symmetry checks (prereg §16).

Every check is computed separately from the primary estimate; none is a
covariate, filter, stratifier or weight in any primary formula. The §16
consequences are fixed interpretation blocks and, on scorability asymmetry,
partial identification bounds.
"""
from __future__ import annotations

from typing import Any

from dci1.analysis.bootstrap import family_intervals, run_bootstrap
from dci1.analysis.claims import interval_excludes_zero
from dci1.analysis.families import assemble_stats
from dci1.protocol.constants import (
    ARMS,
    NON_BEHAVIOURAL_DIFFERENCE_THRESHOLD,
    PRIMARY_ARMS,
    UPTAKE_DIFFERENCE_THRESHOLD,
)

INTERPRETATION_UPTAKE = (
    "the compared arms delivered their treatments at materially different "
    "rates; the estimate stands unchanged because it is an intention-to-treat "
    "quantity")
INTERPRETATION_SCORABILITY = (
    "part of the contrast reflects a difference in how often a response was "
    "scorable; partial identification bounds are reported beside the estimate")


def uptake_check(check_results: dict[str, Any]) -> dict[str, Any]:
    """§16 manipulation check on the three focal-to-reference uptake
    differences (simultaneous interval within the check family)."""
    triggered = []
    members = check_results.get("members", {})
    for name, entry in members.items():
        if entry.get("status") != "OK" or entry.get("degenerate"):
            continue
        if abs(entry["estimate"]) > UPTAKE_DIFFERENCE_THRESHOLD and \
                interval_excludes_zero(entry["simultaneous"]):
            triggered.append(name)
    return {"triggered": triggered,
            "interpretation_block": INTERPRETATION_UPTAKE if triggered
            else None,
            "members": members}


def symmetry_check(f6_results: dict[str, Any]) -> dict[str, Any]:
    """§16 arm symmetry over family F6; decides partial identification."""
    triggered = []
    for name, entry in f6_results.get("members", {}).items():
        if entry.get("status") != "OK" or entry.get("degenerate"):
            continue
        if abs(entry["estimate"]) > NON_BEHAVIOURAL_DIFFERENCE_THRESHOLD \
                and interval_excludes_zero(entry["simultaneous"]):
            triggered.append(name)
    return {"triggered": triggered,
            "interpretation_block": INTERPRETATION_SCORABILITY if triggered
            else None,
            "partial_identification_required": bool(triggered)}


def compliance_flags(scored_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """§16 passive measures: short-response and truncation flag rates per arm."""
    per_arm: dict[str, dict[str, float]] = {}
    for arm in ARMS:
        rows = [r for r in scored_rows if r["arm"] == arm]
        if not rows:
            continue
        per_arm[arm] = {
            "rows": len(rows),
            "short_rate": sum(r["short_flag"] for r in rows) / len(rows),
            "truncation_rate": sum(r["truncated"] for r in rows) / len(rows),
            "empty_rate": sum(r["empty"] for r in rows) / len(rows),
            "non_behavioural_rate": sum(r["non_behavioural"]
                                        for r in rows) / len(rows),
        }
    return per_arm


def partial_identification(scored_rows: list[dict[str, Any]], *,
                           seed: int, n_resamples: int) -> dict[str, Any]:
    """§16 bounds: every primary estimand recalculated twice — every
    non-behavioural response treated as a target pass, then as a target
    failure — with full simultaneous intervals for each recalculation."""
    out: dict[str, Any] = {}
    for label, imputed in (("all_pass", 0), ("all_fail", 1)):
        variant = []
        for row in scored_rows:
            v = dict(row)
            if row["arm"] in PRIMARY_ARMS and row["non_behavioural"]:
                v["f_s0"] = imputed
            variant.append(v)
        assembled = assemble_stats(variant)
        result = run_bootstrap(assembled["stats"], seed=seed,
                               n_resamples=n_resamples)
        from dci1.analysis.families import family_members

        out[label] = family_intervals(result, family_members()["F1"])
    widths = {}
    for label in out:
        if out[label].get("status") == "OK":
            widths[label] = sum(
                m["simultaneous"][1] - m["simultaneous"][0]
                for m in out[label]["members"].values())
    # §16/§26: the claim rules are applied to the narrower of the two bounds.
    narrower = min(widths, key=widths.get) if widths else None
    out["narrower_bound"] = narrower
    return out
