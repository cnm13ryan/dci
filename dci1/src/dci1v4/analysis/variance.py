"""The variance model, the allocation menu rule, and the realised
decomposition (§16.1, §16.3, §23, check C12).

Three separate jobs live here:

* **the registered projection** — ``projected_half_widths`` implements §16.1
  exactly and reproduces the §16.2 and §16.3 tables from the registered
  constants;
* **the menu rule** — ``select_allocation`` takes the smallest entry of the
  §16.3 menu meeting every precision precondition under a supplied variance
  re-estimate. It *reports* what the rule selects; choosing the allocation is
  registered open decision V1 and is not made here;
* **the realised decomposition** — ``realised_decomposition`` estimates
  sigma^2_topic, sigma^2_draw and the two within-block correlations from data,
  which is what check C12 requires before freeze and what §23 reports beside
  every primary estimate.

Nothing here reads an effect estimate. The preconditions are absolute and come
from the smallest effect of interest (§16.3), and the pilot contributes
variance information only.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.analysis.bootstrap import sidak_critical
from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C


def components(phi: float, p_one_minus_p: float = C.P_ONE_MINUS_P
               ) -> dict[str, float]:
    """sigma^2_topic and sigma^2_draw from the share phi (§16.1)."""
    return {"sigma2_topic": phi * p_one_minus_p,
            "sigma2_draw": (1 - phi) * p_one_minus_p}


def variances(blocks: int, m: int, *, phi: float = C.PHI_PRIMARY,
              rho: float = C.RHO,
              p_one_minus_p: float = C.P_ONE_MINUS_P) -> dict[str, float]:
    """§16.1, verbatim."""
    if blocks <= 0 or m <= 0:
        raise ProtocolError("blocks and M must be positive")
    parts = components(phi, p_one_minus_p)
    topic, draw = parts["sigma2_topic"], parts["sigma2_draw"]
    return {
        "D": (2 * (1 - rho) * topic + 2 * draw / m) / blocks,
        "Delta_R": (2 * (1 - rho) * topic
                    + draw * (1 / m + 1 / (3 * m))) / blocks,
        "Lambda": (4 * (1 - rho) * topic + 4 * draw / m) / blocks,
        # Delta_j differences two composed cells for one reference, so it
        # carries the D variance and the family-of-six critical value.
        "Delta_j": (2 * (1 - rho) * topic + 2 * draw / m) / blocks,
        **parts,
    }


#: Family size each quantity's simultaneous interval is taken within (§15).
FAMILY_SIZE = {"D": 4, "Delta_R": 4, "Lambda": 4, "Delta_j": 6}


def projected_half_widths(blocks: int, m: int, *, phi: float = C.PHI_PRIMARY,
                          rho: float = C.RHO) -> dict[str, float]:
    """Projected simultaneous half-widths at the Šidák critical values."""
    var = variances(blocks, m, phi=phi, rho=rho)
    return {name: sidak_critical(FAMILY_SIZE[name]) * math.sqrt(var[name])
            for name in FAMILY_SIZE}


def detectable_effect(blocks: int, m: int, quantity: str = "D", *,
                      phi: float = C.PHI_PRIMARY, rho: float = C.RHO,
                      power: float = 0.80) -> float:
    """The effect this allocation detects at the stated power (§16.2)."""
    from statistics import NormalDist

    var = variances(blocks, m, phi=phi, rho=rho)[quantity]
    critical = sidak_critical(FAMILY_SIZE[quantity])
    z_power = NormalDist().inv_cdf(power)
    return (critical + z_power) * math.sqrt(var)


def menu_table(*, phi: float = C.PHI_PRIMARY, rho: float = C.RHO,
               cells: int = C.N_CELLS_FULL) -> list[dict[str, Any]]:
    """The §16.3 menu with its costs and projected half-widths."""
    rows = []
    for entry in C.ALLOCATION_MENU:
        blocks, m = entry["blocks"], entry["M"]
        rows.append({"blocks": blocks, "M": m,
                     "generations_per_model": blocks * cells * m,
                     **{f"hw_{k}": v for k, v in
                        projected_half_widths(blocks, m, phi=phi,
                                              rho=rho).items()}})
    return rows


def meets_preconditions(blocks: int, m: int, *, phi: float, rho: float
                        ) -> bool:
    hw = projected_half_widths(blocks, m, phi=phi, rho=rho)
    return all(hw[name] <= C.PRECISION_PRECONDITIONS[name] for name in hw)


def select_allocation(*, phi_settings: Sequence[float] = (C.PHI_PRIMARY,
                                                          C.PHI_ALTERNATE),
                      rho: float = C.RHO, cells: int = C.N_CELLS_FULL
                      ) -> dict[str, Any]:
    """The registered menu rule (§16.3): the smallest entry meeting every
    precision precondition under the pre-freeze variance re-estimate.

    "Smallest" is cost, measured in generations per model. Every menu row is a
    live entry: nothing here bans an allocation, and the selection carries the
    evidence that chose it. **This reports; V1 decides.**
    """
    candidates = []
    for entry in C.ALLOCATION_MENU:
        blocks, m = entry["blocks"], entry["M"]
        ok = {phi: meets_preconditions(blocks, m, phi=phi, rho=rho)
              for phi in phi_settings}
        candidates.append({
            "blocks": blocks, "M": m,
            "generations_per_model": blocks * cells * m,
            "meets_preconditions": ok,
            "meets_all": all(ok.values()),
            "half_widths": {str(phi): projected_half_widths(blocks, m,
                                                            phi=phi, rho=rho)
                            for phi in phi_settings},
        })
    qualifying = [c for c in candidates if c["meets_all"]]
    if not qualifying:
        return {"selected": None, "rule": "smallest entry meeting every "
                "precision precondition under every carried variance setting",
                "candidates": candidates,
                "note": ("no registered menu entry meets every precondition "
                         "under the supplied variance estimate; §16.3 requires "
                         "moving up the menu, and the menu is exhausted")}
    selected = min(qualifying, key=lambda c: c["generations_per_model"])
    return {
        "selected": {"blocks": selected["blocks"], "M": selected["M"],
                     "generations_per_model":
                         selected["generations_per_model"]},
        "rule": ("smallest entry meeting every precision precondition under "
                 "every carried variance setting (§16.3)"),
        "phi_settings": list(phi_settings), "rho": rho,
        "preconditions": dict(C.PRECISION_PRECONDITIONS),
        "candidates": candidates,
        "decision_status": ("REPORTED, NOT DECIDED: the allocation and the "
                            "number of models carried to confirmation are "
                            "registered open decision V1"),
    }


# --------------------------------------------------------------- realised
def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    centre = _mean(values)
    return sum((v - centre) ** 2 for v in values) / (len(values) - 1)


def _covariance(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    ma, mb = _mean(a), _mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (len(a) - 1)


def realised_decomposition(cell_means: Mapping[str, Sequence[float]],
                           within_cell_variance: float, m: int
                           ) -> dict[str, Any]:
    """§23 / check C12: sigma^2_topic, sigma^2_draw and phi from cell means.

    ``cell_means`` maps a cell key to its per-block cell mean vector, and
    ``within_cell_variance`` is the mean over cells of the draw-level variance
    of the indicator inside a cell. Var(cell mean) = sigma^2_topic +
    sigma^2_draw / M, so the topic component is what remains once the draw
    component is removed.
    """
    if not cell_means:
        raise ProtocolError("no cell means supplied")
    sigma2_draw = float(within_cell_variance)
    total = _mean([_variance(list(v)) for v in cell_means.values()])
    sigma2_topic = max(0.0, total - sigma2_draw / m)
    denominator = sigma2_topic + sigma2_draw
    phi = (sigma2_topic / denominator) if denominator > 0 else 0.0
    return {"sigma2_topic": sigma2_topic, "sigma2_draw": sigma2_draw,
            "phi": phi, "mean_cell_mean_variance": total, "M": m,
            "cells": len(cell_means)}


def realised_correlation(pairs: Iterable[tuple[Sequence[float],
                                               Sequence[float]]],
                         sigma2_topic: float) -> dict[str, Any]:
    """The within-block correlation of the topic component between two cells.

    Draw noise is independent across cells, so the covariance of two cell means
    estimates rho * sigma^2_topic directly and needs no draw-noise correction.
    Check C12 requires two of these estimated separately: the among-reference
    correlation, and the correlation between a cell containing A and a cell
    containing a reference with the same outcome constraint.
    """
    covariances = [_covariance(list(a), list(b)) for a, b in pairs]
    if not covariances:
        raise ProtocolError("no cell pairs supplied")
    mean_cov = _mean(covariances)
    rho = (mean_cov / sigma2_topic) if sigma2_topic > 0 else float("nan")
    return {"pairs": len(covariances), "mean_covariance": mean_cov,
            "sigma2_topic": sigma2_topic, "rho": rho,
            "rho_clipped": min(1.0, max(-1.0, rho)) if sigma2_topic > 0
            else None}
