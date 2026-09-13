"""The geometry the spectrum and the local arm need, evaluated per draw.

Everything the registered calibration-basis re-read asks of a family is a
statement about **positions on the iota axis relative to iota_A**: which rungs
are eligible (raw solo inside the band, vacuity under the ceiling, a defined
coordinate), whether the family straddles, how many eligible rungs it has and
how far they span (§12.6 C4), and --- what the difficulty-response analysis
actually consumes --- whether there is an eligible rung *meaningfully below*
and one *meaningfully above* iota_A. This module evaluates all of it on one
array of posterior draws at a time, so that the screen can report
``P(event)`` rather than ``event(point estimate)``.

Vectorised: ``p``, ``kappa`` and ``vac`` are ``(S, R)`` arrays of S posterior
draws for R rungs; ``iota_a`` is ``(S,)``. Every output is an ``(S,)`` boolean
or float array, or ``(S, R)`` for the per-rung ones.

The thresholds default to the registered v7 values (``HEADROOM_BAND``,
``REFERENCE_VACUITY_MAX``, ``CHANCE_DEGENERACY_MAX``, C4's rung and span
floors, §13.8's caliper) and are parameters here only so that the simulation
and the backtest can evaluate alternatives *prospectively* and say so.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dci1v7.protocol import constants as C
from dci1v8dev import rules as R

__all__ = ["DEFAULT_GEOMETRY", "DrawGeometry", "Geometry", "evaluate_draws",
           "select_iota_a"]


@dataclass(frozen=True)
class Geometry:
    """The thresholds one evaluation reads. Defaults are v7's registered ones."""

    band: tuple[float, float] = C.HEADROOM_BAND
    #: The spectrum-admissibility guard band (v5's registered, never-applied
    #: SPECTRUM_ELIGIBILITY_BAND): a spectrum point may sit up to 0.95 raw
    #: solo, where V_head's headroom band stops at 0.90 on the interval. The
    #: support-below/above events are read on this band; the local event and
    #: C4 keep the registered bands.
    spectrum_band: tuple[float, float] = C.SPECTRUM_ELIGIBILITY_BAND
    vacuity_max: float = C.REFERENCE_VACUITY_MAX
    degeneracy: float = C.CHANCE_DEGENERACY_MAX
    min_rungs: int = C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY
    min_span: float = C.COVERAGE_MIN_WITHIN_FAMILY_SPAN
    #: §4 of the task: support *meaningfully* below and above A. The two
    #: offsets are separate because the band is asymmetric around a typical
    #: iota_A (~0.70): the easy side has only ~0.20 of room to the 0.90 edge.
    d_below: float = R.SPECTRUM_OFFSET_BELOW
    d_above: float = R.SPECTRUM_OFFSET_ABOVE
    caliper: float = C.REFERENCE_CALIPER


DEFAULT_GEOMETRY = Geometry()


@dataclass(frozen=True)
class DrawGeometry:
    """Per-draw results. Booleans are ``(S,)`` unless noted."""

    eligible: np.ndarray           # (S, R)
    iota: np.ndarray               # (S, R), nan where undefined
    n_eligible: np.ndarray         # (S,)
    straddles: np.ndarray
    span: np.ndarray               # (S,), 0 where < 2 eligible
    c4: np.ndarray                 # straddle & n>=min_rungs & span>=min_span
    support_below: np.ndarray      # some eligible rung <= iota_a - d_below
    support_above: np.ndarray      # some eligible rung >= iota_a + d_above
    support_both: np.ndarray
    local: np.ndarray              # (S, R): eligible & |iota - iota_a|<=caliper
    family_local: np.ndarray       # (S,)
    fragile: np.ndarray            # (S, R): eligible but within one band edge


def evaluate_draws(p: np.ndarray, kappa: np.ndarray, vac: np.ndarray,
                   iota_a: np.ndarray, *, geometry: Geometry = DEFAULT_GEOMETRY,
                   edge_margin: float = 0.05,
                   band: tuple[float, float] | None = None) -> DrawGeometry:
    """``band`` overrides the eligibility band (the spectrum reading passes
    ``geometry.spectrum_band``); everything else reads ``geometry``."""
    p = np.asarray(p, dtype=float)
    kappa = np.asarray(kappa, dtype=float)
    vac = np.asarray(vac, dtype=float)
    iota_a = np.asarray(iota_a, dtype=float)
    if p.ndim != 2 or kappa.shape != p.shape or vac.shape != p.shape:
        raise ValueError("p, kappa and vac must share shape (S, R)")
    if iota_a.shape != (p.shape[0],):
        raise ValueError("iota_a must have shape (S,)")
    low, high = band if band is not None else geometry.band
    defined = kappa < geometry.degeneracy
    with np.errstate(divide="ignore", invalid="ignore"):
        iota = np.where(defined, (p - kappa) / (1.0 - kappa), np.nan)
    eligible = (p >= low) & (p <= high) & (vac <= geometry.vacuity_max) \
        & defined
    ia = iota_a[:, None]
    below = eligible & (iota < ia)
    above = eligible & (iota > ia)
    n_eligible = eligible.sum(axis=1)
    masked = np.where(eligible, iota, np.nan)
    with np.errstate(all="ignore"):
        hi = np.nanmax(np.where(eligible, iota, -np.inf), axis=1)
        lo = np.nanmin(np.where(eligible, iota, np.inf), axis=1)
    span = np.where(n_eligible >= 2, hi - lo, 0.0)
    straddles = below.any(axis=1) & above.any(axis=1)
    c4 = straddles & (n_eligible >= geometry.min_rungs) \
        & (span >= geometry.min_span)
    support_below = (eligible & (iota <= ia - geometry.d_below)).any(axis=1)
    support_above = (eligible & (iota >= ia + geometry.d_above)).any(axis=1)
    local = eligible & (np.abs(iota - ia) <= geometry.caliper)
    fragile = eligible & ((p > high - edge_margin) | (p < low + edge_margin))
    del masked
    return DrawGeometry(
        eligible=eligible, iota=iota, n_eligible=n_eligible,
        straddles=straddles, span=span, c4=c4,
        support_below=support_below, support_above=support_above,
        support_both=support_below & support_above, local=local,
        family_local=local.any(axis=1), fragile=fragile)


def select_iota_a(p_grid: np.ndarray, kappa_grid: np.ndarray,
                  severities: list[int], *, band: tuple[float, float] = C.TARGET_BAND,
                  aim: float = C.TARGET_AIM) -> tuple[np.ndarray, np.ndarray]:
    """§12.3's n* selection applied to every draw of A's grid.

    Per draw: eligible severities put raw solo inside ``band``; among them the
    one nearest ``aim`` wins, the smaller severity breaking a tie; with none
    eligible the severity nearest the aim is used (the replication would
    record ``TARGET_RANGE_EXHAUSTED`` --- the screen still needs a point).
    Returns ``(iota_a, n_star)`` of shape ``(S,)`` each.
    """
    p_grid = np.asarray(p_grid, dtype=float)
    kappa_grid = np.asarray(kappa_grid, dtype=float)
    if p_grid.ndim != 2 or p_grid.shape != kappa_grid.shape:
        raise ValueError("A's grid draws must share shape (S, G)")
    sev = np.asarray(severities, dtype=float)
    dist = np.abs(p_grid - aim)
    eligible = (p_grid >= band[0]) & (p_grid <= band[1])
    # smaller severity breaks an exact tie: add a tiny severity-ordered term
    key = dist + 1e-9 * sev[None, :]
    key_eligible = np.where(eligible, key, np.inf)
    any_eligible = eligible.any(axis=1)
    pick = np.where(any_eligible, key_eligible.argmin(axis=1),
                    key.argmin(axis=1))
    rows = np.arange(p_grid.shape[0])
    p_star = p_grid[rows, pick]
    k_star = kappa_grid[rows, pick]
    with np.errstate(divide="ignore", invalid="ignore"):
        iota_a = np.where(k_star < C.CHANCE_DEGENERACY_MAX,
                          (p_star - k_star) / (1.0 - k_star), np.nan)
    return iota_a, sev[pick].astype(int)
