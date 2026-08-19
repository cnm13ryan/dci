"""The order-stratified block bootstrap (§12, §13, §14, §20).

Each replicate draws exactly 192 block identifiers with replacement inside
each order stratum; a drawn block travels with all its arms. Each family
receives its own simultaneous 95% interval by the studentised
maximum-absolute-standardised-deviation rule; marginal percentile intervals
are reported alongside. Non-finite standard errors or bounds fail closed for
the affected quantity (§20/§52); degenerate all-identical contrasts remain
and are reported.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from dci1v3.analysis.estimators import BlockTable, Member, point_estimate
from dci1v3.errors import ProtocolError
from dci1v3.protocol import constants as C
from dci1v3.protocol.seeds import bootstrap_seed


def resample_indices(table: BlockTable, *, model_id: str, family: str,
                     resamples: int) -> dict[str, np.ndarray]:
    """Per-stratum index matrices [resamples × stratum size]; the §12
    resampling-unit assertion is executed here."""
    rng = np.random.default_rng(
        bootstrap_seed(C.BOOTSTRAP_ROOT_SEED, model_id, family))
    out: dict[str, np.ndarray] = {}
    for order in C.ORDERS:
        stratum = table.stratum(order)
        if stratum.size == 0:
            raise ProtocolError(f"empty order stratum {order}")
        draws = rng.integers(0, stratum.size,
                             size=(resamples, stratum.size))
        if draws.shape[1] != stratum.size:
            raise ProtocolError("resampling-unit assertion failed: draw "
                                "count differs from stratum size")
        out[order] = stratum[draws]
    return out


def _member_draws(member: Member, indices: dict[str, np.ndarray]
                  ) -> np.ndarray:
    if member.scope == "all":
        stacked = np.concatenate([indices[o] for o in C.ORDERS], axis=1)
        return member.values[stacked].mean(axis=1)
    return member.values[indices[member.scope]].mean(axis=1)


def family_intervals(table: BlockTable, members: list[Member], *,
                     model_id: str, resamples: int) -> dict[str, Any]:
    """Estimates plus marginal and simultaneous 95% intervals per family."""
    results: dict[str, Any] = {}
    families = sorted({m.family for m in members})
    for family in families:
        group = [m for m in members if m.family == family]
        indices = resample_indices(table, model_id=model_id, family=family,
                                   resamples=resamples)
        estimates = np.array([point_estimate(table, m) for m in group])
        draws = np.stack([_member_draws(m, indices) for m in group])
        se = draws.std(axis=1, ddof=1)
        finite = np.isfinite(se) & (se > 0)
        entries = []
        critical = None
        if finite.any():
            t = np.abs(draws[finite] - estimates[finite, None]) \
                / se[finite, None]
            critical = float(np.quantile(t.max(axis=0), C.CONFIDENCE))
        for i, member in enumerate(group):
            entry: dict[str, Any] = {
                "name": member.name, "family": family,
                "estimate": float(estimates[i]),
                "scope": member.scope,
                "standard_error": float(se[i]) if np.isfinite(se[i])
                else None,
                "marginal": [float(np.quantile(draws[i], 0.025)),
                             float(np.quantile(draws[i], 0.975))],
            }
            if not finite[i]:
                degenerate = bool(np.all(
                    member.values == member.values[0]))
                entry["status"] = ("DEGENERATE_REPORTED" if degenerate
                                   else "INCONCLUSIVE_NON_FINITE_SE")
                entry["simultaneous"] = None
            elif critical is None or not np.isfinite(critical):
                entry["status"] = "INCONCLUSIVE_NON_FINITE_BOUND"
                entry["simultaneous"] = None
            else:
                entry["status"] = "OK"
                entry["simultaneous"] = [
                    float(estimates[i] - critical * se[i]),
                    float(estimates[i] + critical * se[i])]
            entries.append(entry)
        results[family] = {"members": entries,
                           "critical_value": critical,
                           "resamples": resamples}
    return results
