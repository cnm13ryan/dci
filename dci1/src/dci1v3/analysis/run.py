"""The fixed-order confirmatory analysis (§20), also exercised by the pilot
in structural mode and by the masked phase on permuted labels.

Order: load and screen rows -> assert the complete draw matrix -> assert one
accepted primary per cell -> score S0 -> compliance and arm-symmetry checks
-> block contrasts -> stratified 10,000-resample block bootstrap ->
simultaneous intervals per family -> claim rules with the §16
interpretation and partial-identification rules. Fails closed per quantity;
output is deterministic (no wall-clock state).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from dci1v3.analysis import claims as claims_mod
from dci1v3.analysis.bootstrap import family_intervals
from dci1v3.analysis.estimators import (
    BlockTable,
    from_primary_rows,
    family_members,
    point_estimate,
    uptake_members,
)
from dci1v3.errors import ProtocolError
from dci1v3.protocol import constants as C


def _quantiles(values: list[int]) -> dict[str, float]:
    if not values:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
    array = np.array(values, dtype=float)
    return {f"p{q}": float(np.quantile(array, q / 100))
            for q in (50, 90, 95, 99)}


def _interval(entry: dict[str, Any]) -> tuple[float, float] | None:
    if entry.get("status") != "OK" or entry.get("simultaneous") is None:
        return None
    return tuple(entry["simultaneous"])


def _partial_identification(rows: list[dict[str, Any]], *, n: int,
                            model_id: str, resamples: int
                            ) -> dict[str, Any]:
    """§16: recompute the primary estimands treating every non-behavioural
    response as pass and as failure; claims follow both recalculations."""
    variants: dict[str, Any] = {}
    for label, forced in (("non_behavioural_as_pass", 0.0),
                          ("non_behavioural_as_failure", 1.0)):
        adjusted = []
        for row in rows:
            if row["arm"] in C.PRIMARY_ARMS and row["non_behavioural"]:
                verdicts = dict(row["verdicts"])
                verdicts["s0"] = n if forced == 0.0 else n + 1
                adjusted.append({**row, "verdicts": verdicts})
            else:
                adjusted.append(row)
        table = from_primary_rows(adjusted, n=n)
        members = [m for m in family_members(table) if m.family == "F1"]
        result = family_intervals(table, members, model_id=model_id,
                                  resamples=resamples)
        variants[label] = result["F1"]["members"]
    return variants


def analyse(primary_rows: list[dict[str, Any]], *, model_id: str, n: int,
            resamples: int, matrix: dict[str, int] | None = None,
            expected_blocks: int | None = None) -> dict[str, Any]:
    if matrix is not None:
        expected = {"blocks": C.N_BLOCKS, "arms": len(C.ARMS),
                    "draws_per_cell": C.M_DRAWS}
        if matrix != expected:
            raise ProtocolError(f"cache matrix {matrix} != {expected}; the "
                                f"analysis fails closed")
    table = from_primary_rows(primary_rows, n=n)     # steps 3–4, fail-closed
    if expected_blocks is not None and table.n_blocks != expected_blocks:
        raise ProtocolError(f"{table.n_blocks} blocks, expected "
                            f"{expected_blocks}")

    # ---- step 5: compliance checks and arm symmetry (§16) ---------------
    per_arm: dict[str, dict[str, Any]] = {}
    lengths_all: list[int] = []
    for arm in C.ARMS:
        arm_rows = [r for r in primary_rows if r["arm"] == arm]
        lengths = [int(r.get("token_count", 0)) for r in arm_rows]
        lengths_all.extend(lengths)
        per_arm[arm] = {
            "rows": len(arm_rows),
            "truncated": sum(1 for r in arm_rows
                             if r.get("finish_reason") == "length"),
            "short": sum(1 for r in arm_rows
                         if len(r.get("raw_response", "").split())
                         <= C.SHORT_RESPONSE_WORDS),
            "finish_reasons": _count_by(arm_rows, "finish_reason"),
            "length_quantiles": _quantiles(lengths),
            "uptake": (float(np.mean([
                r["verdicts"].get("added_pass", False)
                for r in arm_rows])) if arm in C.PRIMARY_ARMS else None),
            "graded_mean": float(np.mean([
                abs(r["verdicts"]["s0"] - n) for r in arm_rows]))
            if arm_rows else None,
        }

    members = family_members(table)
    intervals = family_intervals(table, members, model_id=model_id,
                                 resamples=resamples)
    uptake = family_intervals(table, uptake_members(table),
                              model_id=model_id, resamples=resamples)

    uptake_flagged = [
        e["name"] for e in uptake["uptake"]["members"]
        if abs(e["estimate"]) > C.UPTAKE_DIFFERENCE_FLAG
        and _interval(e) is not None
        and (_interval(e)[0] > 0 or _interval(e)[1] < 0)]

    f6 = intervals["F6"]["members"]
    asymmetry_flagged = [
        e["name"] for e in f6
        if abs(e["estimate"]) > C.F6_ASYMMETRY_FLAG
        and _interval(e) is not None
        and (_interval(e)[0] > 0 or _interval(e)[1] < 0)]

    # ---- step 9: claim rules (§15) with §16 interpretation --------------
    f1 = intervals["F1"]["members"]
    primary_claims = {e["name"]: claims_mod.primary_claims(_interval(e))
                      for e in f1}
    exchangeability = claims_mod.exchangeability_holds(
        [_interval(e) for e in intervals["F2"]["members"]])

    partial = None
    if asymmetry_flagged:
        partial = _partial_identification(
            primary_rows, n=n, model_id=model_id, resamples=resamples)
        for name in list(primary_claims):
            variant_claims = []
            for variant in partial.values():
                entry = next(e for e in variant if e["name"] == name)
                variant_claims.append(
                    claims_mod.primary_claims(_interval(entry)))
            agree = all(c == variant_claims[0] for c in variant_claims[1:])
            primary_claims[name] = (
                variant_claims[0] if agree else
                {"direction": claims_mod.DIRECTION_UNRESOLVED,
                 "magnitude": claims_mod.MAGNITUDE_UNRESOLVED,
                 "status": "PARTIAL_IDENTIFICATION_BOUNDS"})

    solo_failure = float(table.target_alone_failure.mean())
    item = {
        "floor_share": float(np.mean(
            table.f["s0"].mean(axis=1) == 1.0)),
        "ceiling_share": float(np.mean(
            table.f["s0"].mean(axis=1) == 0.0)),
        "identical_share": float(np.mean([
            len(set(table.f["s0"][i])) == 1
            for i in range(table.n_blocks)])),
    }

    return {
        "n": n, "blocks": table.n_blocks, "resamples": resamples,
        "measurement_scope": C.MEASUREMENT_SCOPE,
        "families": intervals,
        "uptake_intervals": uptake,
        "uptake_flagged": uptake_flagged,
        "arm_symmetry_flagged": asymmetry_flagged,
        "partial_identification": partial,
        "primary_claims": primary_claims,
        "exchangeability_holds": exchangeability,
        "per_arm": per_arm,
        "length_quantiles": _quantiles(lengths_all),
        "target_alone_failure": solo_failure,
        "target_alone_in_band": (C.TARGET_BAND[0] <= solo_failure
                                 <= C.TARGET_BAND[1]),
        "topic_alone_pass_rate": float(table.topic_alone_pass.mean()),
        "item_behaviour": item,
        "failure_categories": _category_table(table),
        "secondary": _secondary(table),
    }


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row.get(key, ""))] = counts.get(str(row.get(key, "")), 0) + 1
    return counts


def _category_table(table: BlockTable) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for j, arm in enumerate(C.PRIMARY_ARMS):
        out[arm] = {cat: float(np.mean(table.category[:, j] == cat))
                    for cat in C.FAILURE_CATEGORIES}
    return out


def _secondary(table: BlockTable) -> dict[str, Any]:
    from dci1v3.analysis.estimators import Member, contrast_vector
    d = contrast_vector(table)
    tf, af = table.stratum(C.TARGET_FIRST), table.stratum(C.ADDED_FIRST)
    pooled = float(d.mean())
    interaction = float(d[tf].mean() - d[af].mean()) if tf.size and af.size \
        else None
    return {"pooled_swap_effect": pooled, "order_interaction": interaction}


def redact_structural(result: dict[str, Any]) -> dict[str, Any]:
    """§17: the pilot's structurally complete result with every scientific
    rate and contrast withheld."""
    def scrub(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: scrub(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [scrub(v) for v in obj]
        if isinstance(obj, float):
            return "REDACTED"
        return obj
    scrubbed = scrub(result)
    scrubbed["structural_only"] = True
    return scrubbed
