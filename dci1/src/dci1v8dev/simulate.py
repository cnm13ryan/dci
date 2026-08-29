"""Synthetic families: the operating characteristics of the screens.

Seven archetypes, each a ladder of **true** difficulty coordinates over the
family's severities (round-0 ladder plus §7.10's reserve, so a re-screen
that extends into the reserve has a truth to draw from):

1. ``wide``            genuinely wide, straddling A on both sides;
2. ``narrow_noisy``    true span below the target, extremes that noise can
                       push past it;
3. ``borderline``      true span at the target, with support just reaching
                       the offsets;
4. ``one_sided``       wide but entirely below A;
5. ``flat``            severity barely moves difficulty;
6. ``outlier``         a useful ladder with one rung that is genuinely off
                       the trend;
7. ``ceiling``         extremes at the eligibility ceiling/floor.

A's curve is the truth for iota_A: A's true solo compliance over its grid,
with §12.3's selection applied to the *estimated* curve at each stage, so
iota_A moves between the screen and calibration exactly as it does in the
study. Topic heterogeneity uses a Beta-Binomial with the measured ICC
(``statistics.TOPIC_ICC``): topic rates ``p_t ~ Beta(p*phi, (1-p)*phi)``
with ``phi = 1/ICC - 1``.

For each archetype and replicate the simulation records: the legacy
per-family C4 verdict on the 24-topic point estimates (the v7 certificate's
own rule), the new screen's stage-1 status, its status after the targeted
second pass (batches drawn from the truth), the **calibrated** verdict
(192 topics x 4 draws, evaluated with the registered point rules at the
calibrated iota_A) and the **true** verdict. From those come the false
positive and false negative rates, the fraction resampled, the expected
re-screen cost, and P(survives calibration | forwarded) for both screens.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from dci1v7.protocol import constants as C
from dci1v7.verifiers.constraints import LADDERS, RESERVES
from dci1v8dev.prescreen import legacy
from dci1v8dev.prescreen.geometry import Geometry, evaluate_draws, select_iota_a
from dci1v8dev.prescreen.rescreen import (
    DEFAULT_RESCREEN_CONFIG,
    RescreenBatch,
    RescreenConfig,
    run_rescreen,
)
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.screen import (
    DEFAULT_SCREEN_CONFIG,
    SCREEN_ACCEPT,
    ScreenConfig,
    _config_dict,
    screen_families,
)
from dci1v8dev.prescreen.statistics import TOPIC_ICC

__all__ = [
    "ARCHETYPES",
    "A_CURVE_2507",
    "A_CURVE_QWEN",
    "Archetype",
    "simulate_all",
    "simulate_case",
    "true_verdict",
]

#: A's true solo compliance over TARGET_GRID, shaped like the calibrated
#: curves of the registered v7 replications (2026-08-28): qwen3-4b-like
#: (iota_A lands near 0.68) and qwen-2507-like (near 0.55).
A_CURVE_QWEN = {1: 0.91, 2: 0.69, 3: 0.56, 4: 0.58, 5: 0.48, 6: 0.45,
                7: 0.41, 8: 0.35}
A_CURVE_2507 = {1: 0.99, 2: 0.99, 3: 0.96, 4: 0.88, 5: 0.57, 6: 0.55,
                7: 0.44, 8: 0.55}


@dataclass(frozen=True)
class Archetype:
    name: str
    #: family id whose ladder/reserve structure is borrowed (a Tier-1 marker
    #: by default: chance-free, 8 ladder rungs, reserve to 12).
    family: str
    #: true solo compliance by severity, over the family's declared range
    true_p: dict[int, float]
    kappa: float = 0.0
    vacuity: float = 0.0
    expectation: str = ""


def _ladder(values: Sequence[float], family: str = "MK1",
            reserve_values: Sequence[float] = ()) -> dict[int, float]:
    sev = list(LADDERS[family]) + [q for q in RESERVES[family]
                                   if q not in LADDERS[family]]
    vals = list(values) + list(reserve_values)
    if len(vals) < len(sev):
        vals += [vals[-1]] * (len(sev) - len(vals))
    return {q: float(min(0.995, max(0.005, v))) for q, v in zip(sev, vals)}


ARCHETYPES: dict[str, Archetype] = {
    # Values run over the DECLARED range: the 8 ladder rungs first, then the
    # reserve (9..12 for a marker family). The truth is evaluated over the
    # whole range because the second pass may admit reserve rungs.
    "wide": Archetype(
        "wide", "MK1",
        _ladder([0.98, 0.92, 0.86, 0.78, 0.68, 0.56, 0.44, 0.30],
                reserve_values=[0.22, 0.16, 0.11, 0.08]),
        expectation="retained with high probability"),
    "narrow_noisy": Archetype(
        "narrow_noisy", "MK2",
        _ladder([0.82, 0.79, 0.76, 0.73, 0.70, 0.67, 0.64, 0.62],
                reserve_values=[0.61, 0.60, 0.60, 0.59]),
        expectation="raw max-min passes often by noise; new method rejects "
                    "or resamples"),
    "borderline": Archetype(
        "borderline", "MK3",
        _ladder([0.88, 0.85, 0.81, 0.76, 0.70, 0.64, 0.58, 0.54],
                reserve_values=[0.53, 0.52, 0.52, 0.51]),
        expectation="routed to the second pass"),
    "one_sided": Archetype(
        "one_sided", "MK4",
        _ladder([0.62, 0.55, 0.48, 0.42, 0.35, 0.28, 0.22, 0.16],
                reserve_values=[0.13, 0.11, 0.09, 0.07]),
        expectation="wide but not spectrum support: no rung above A"),
    "flat": Archetype(
        "flat", "MK5",
        _ladder([0.70, 0.69, 0.68, 0.67, 0.67, 0.66, 0.65, 0.64],
                reserve_values=[0.64, 0.63, 0.63, 0.62]),
        expectation="rejected early"),
    "outlier": Archetype(
        "outlier", "MK6",
        _ladder([0.96, 0.90, 0.84, 0.40, 0.68, 0.57, 0.46, 0.33],
                reserve_values=[0.25, 0.18, 0.13, 0.09]),
        expectation="not discarded: the rest of the ladder is strong"),
    "ceiling": Archetype(
        "ceiling", "MK7",
        _ladder([0.93, 0.91, 0.89, 0.80, 0.70, 0.55, 0.35, 0.12],
                reserve_values=[0.09, 0.07, 0.05, 0.04]),
        expectation="recognised as fragile: extremes sit at the band edges"),
    # 2507-like: q = 1..8 stays too easy; the hard region is in the reserve.
    "too_easy_reserve": Archetype(
        "too_easy_reserve", "MK8",
        _ladder([0.99, 0.98, 0.96, 0.93, 0.90, 0.85, 0.79, 0.72],
                reserve_values=[0.64, 0.55, 0.46, 0.38]),
        expectation="the reserve extension recovers the hard side; the "
                    "round-0 ladder alone cannot"),
}


def _phi(icc: float) -> float:
    return 1.0 / icc - 1.0


def _topic_rates(rng: np.random.Generator, p: float, n_topics: int,
                 icc: float) -> np.ndarray:
    if icc <= 0:
        return np.full(n_topics, p)
    phi = _phi(icc)
    return rng.beta(max(p * phi, 1e-3), max((1 - p) * phi, 1e-3),
                    size=n_topics)


def _draw_counts(rng: np.random.Generator, p: float, n_topics: int,
                 draws: int, icc: float) -> tuple[int, int]:
    rates = _topic_rates(rng, p, n_topics, icc)
    k = int(rng.binomial(draws, rates).sum().item())
    return k, n_topics * draws


def _screen_table(rng: np.random.Generator, arch: Archetype,
                  a_curve: dict[int, float], *, n_topics: int, draws: int,
                  icc: float, severities: Sequence[int] | None = None,
                  reserve: bool = False
                  ) -> tuple[list[PrescreenRung], list[ARung]]:
    table = []
    for q in (severities if severities is not None else LADDERS[arch.family]):
        k, n = _draw_counts(rng, arch.true_p[q], n_topics, draws, icc)
        ck, cn = _draw_counts(rng, arch.kappa, n_topics, draws, icc)
        vk, _ = _draw_counts(rng, arch.vacuity, n_topics, draws, icc)
        table.append(PrescreenRung(
            kind=arch.family, severity=q, solo_k=k, solo_n=n,
            chance_k=float(ck), chance_n=float(cn), vacuous_k=min(vk, k),
            n_topics=n_topics, draws_per_topic=draws,
            reserve=reserve or q not in LADDERS[arch.family]))
    a_grid = []
    for q, p in sorted(a_curve.items()):
        k, n = _draw_counts(rng, p, n_topics, draws, icc)
        a_grid.append(ARung(severity=q, solo_k=k, solo_n=n, chance_k=0.0,
                            chance_n=float(n), n_topics=n_topics,
                            draws_per_topic=draws))
    return table, a_grid


def _point_verdict(table: Sequence[PrescreenRung], a_grid: Sequence[ARung],
                   *, geometry: Geometry, calibrated_selection: bool,
                   chance_max: float, lift_min: float) -> dict[str, Any]:
    """The registered point rules on one table (legacy certificate style
    when ``calibrated_selection`` is False, calibration re-read when True)."""
    if calibrated_selection:
        p = np.array([[a.solo_rate for a in a_grid]])
        k = np.array([[a.chance_rate for a in a_grid]])
        iota_a, _ = select_iota_a(p, k, [a.severity for a in a_grid])
        iota_a = float(iota_a[0])
    else:
        iota_a, _ = legacy.prescreen_iota_a(a_grid)
    rows = sorted(table, key=lambda r: r.severity)
    p = np.array([[r.solo_rate for r in rows]])
    kappa = np.array([[r.chance_rate for r in rows]])
    vac = np.array([[r.vacuity_rate for r in rows]])
    ia = np.array([iota_a])
    ev = evaluate_draws(p, kappa, vac, ia, geometry=geometry)
    extra = (kappa <= chance_max) & ((p - kappa) >= lift_min)
    lv = evaluate_draws(np.where(extra, p, -1.0), kappa, vac, ia,
                        geometry=geometry)
    av = evaluate_draws(np.where(extra, p, -1.0), kappa, vac, ia,
                        geometry=geometry, band=geometry.spectrum_band)
    return {"iota_a": iota_a, "c4": bool(ev.c4[0]),
            "support_both": bool(av.support_both[0]),
            "support_below": bool(av.support_below[0]),
            "support_above": bool(av.support_above[0]),
            "local": bool(lv.family_local[0]),
            "n_eligible": int(ev.n_eligible[0]), "span": float(ev.span[0])}


def true_verdict(arch: Archetype, a_curve: dict[int, float], *,
                 geometry: Geometry, chance_max: float, lift_min: float,
                 severities: Sequence[int] | None = None) -> dict[str, Any]:
    """The events on the TRUE parameters (calibrated selection of n*)."""
    sev = list(severities if severities is not None
               else sorted(arch.true_p))
    table = [PrescreenRung(kind=arch.family, severity=q,
                           solo_k=round(arch.true_p[q] * 1000),
                           solo_n=1000, chance_k=arch.kappa * 1000.0,
                           chance_n=1000.0,
                           vacuous_k=round(arch.vacuity * 1000),
                           n_topics=1000, draws_per_topic=1)
             for q in sev]
    a_grid = [ARung(severity=q, solo_k=round(p * 1000), solo_n=1000,
                    chance_k=0.0, chance_n=1000.0, n_topics=1000,
                    draws_per_topic=1) for q, p in sorted(a_curve.items())]
    return _point_verdict(table, a_grid, geometry=geometry,
                          calibrated_selection=True, chance_max=chance_max,
                          lift_min=lift_min)


def simulate_case(arch: Archetype, a_curve: dict[int, float], *,
                  n_sims: int = 200, seed: int = 1,
                  screen_config: ScreenConfig = DEFAULT_SCREEN_CONFIG,
                  rescreen_config: RescreenConfig = DEFAULT_RESCREEN_CONFIG,
                  icc: float = TOPIC_ICC,
                  n_prescreen_topics: int = C.N_PRESCREEN,
                  n_calibration_topics: int = C.N_CALIBRATION,
                  calibration_draws: int = C.M_CAL) -> dict[str, Any]:
    geometry = screen_config.geometry
    truth = true_verdict(arch, a_curve, geometry=geometry,
                         chance_max=screen_config.chance_max,
                         lift_min=screen_config.lift_min)
    truth_event = truth[screen_config.spectrum_event]
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for i in range(n_sims):
        table, a_grid = _screen_table(rng, arch, a_curve,
                                      n_topics=n_prescreen_topics, draws=1,
                                      icc=icc)
        leg = _point_verdict(table, a_grid, geometry=geometry,
                             calibrated_selection=False,
                             chance_max=screen_config.chance_max,
                             lift_min=screen_config.lift_min)
        stage1 = screen_families(table, a_grid, config=screen_config)
        v1 = stage1["families"][arch.family]

        def measure(batch: RescreenBatch, _rng=rng):
            fam = batch.families[arch.family]
            sev = list(fam["severities"]) + list(fam["reserve_picks"])
            new_table, new_a = _screen_table(
                _rng, arch, a_curve, n_topics=batch.n_topics,
                draws=batch.draws_per_topic, icc=icc, severities=sev)
            return new_table, (new_a if batch.a_grid else [])

        stage2 = run_rescreen(table, a_grid, screen_config=screen_config,
                              config=rescreen_config, measure=measure)
        v2 = stage2["screen"]["families"][arch.family]
        # calibration: 192 topics x M_cal, on the round-0 ladder plus any
        # reserve rung the second pass admitted (the forwarded set)
        cal_sev = sorted({r.severity for r in stage2["table"]})
        cal_table, cal_a = _screen_table(
            rng, arch, a_curve, n_topics=n_calibration_topics,
            draws=calibration_draws, icc=icc, severities=cal_sev)
        cal = _point_verdict(cal_table, cal_a, geometry=geometry,
                             calibrated_selection=True,
                             chance_max=screen_config.chance_max,
                             lift_min=screen_config.lift_min)
        rows.append({
            "legacy_pass": leg["c4"],
            "legacy_iota_a": leg["iota_a"],
            "stage1_status": v1["status"], "stage1_p": v1["p_spectrum"],
            "final_status": v2["status"], "final_p": v2["p_spectrum"],
            "batches": stage2["batches_used"].get(arch.family, 0),
            "rescreen_cost": stage2["cost_generations"],
            "calibrated_c4": cal["c4"],
            "calibrated_event": cal[screen_config.spectrum_event],
            "calibrated_iota_a": cal["iota_a"],
            "ladder_class": v2["ladder"]["ladder_class"],
        })
    n = len(rows)

    def rate(pred) -> float:
        return sum(1 for r in rows if pred(r)) / n

    legacy_pass = rate(lambda r: r["legacy_pass"])
    new_accept = rate(lambda r: r["final_status"] == SCREEN_ACCEPT)
    out = {
        "archetype": arch.name, "family": arch.family,
        "expectation": arch.expectation,
        "true": truth, "true_event": truth_event,
        "true_c4": truth["c4"],
        "n_sims": n,
        "legacy": {
            "pass_rate": legacy_pass,
            "false_positive_rate": (rate(lambda r: r["legacy_pass"]
                                         and not truth["c4"])),
            "false_negative_rate": (rate(lambda r: not r["legacy_pass"]
                                         and truth["c4"])),
            "calibrated_c4_given_pass": (
                rate(lambda r: r["legacy_pass"] and r["calibrated_c4"])
                / legacy_pass if legacy_pass else None),
        },
        "new": {
            "stage1": {s: rate(lambda r, s=s: r["stage1_status"] == s)
                       for s in ("SCREEN_ACCEPT", "SCREEN_REJECT",
                                 "SCREEN_RESAMPLE")},
            "accept_rate": new_accept,
            "false_positive_rate": rate(
                lambda r: r["final_status"] == SCREEN_ACCEPT
                and not truth_event),
            "false_negative_rate": rate(
                lambda r: r["final_status"] != SCREEN_ACCEPT and truth_event),
            "fraction_resampled": rate(lambda r: r["batches"] > 0),
            "mean_batches": sum(r["batches"] for r in rows) / n,
            "mean_rescreen_cost": sum(r["rescreen_cost"] for r in rows) / n,
            "calibrated_event_given_accept": (
                rate(lambda r: r["final_status"] == SCREEN_ACCEPT
                     and r["calibrated_event"]) / new_accept
                if new_accept else None),
            "calibrated_c4_given_accept": (
                rate(lambda r: r["final_status"] == SCREEN_ACCEPT
                     and r["calibrated_c4"]) / new_accept
                if new_accept else None),
            "ladder_classes": {
                k: rate(lambda r, k=k: r["ladder_class"] == k)
                for k in sorted({r["ladder_class"] for r in rows})},
        },
        "calibrated": {"c4_rate": rate(lambda r: r["calibrated_c4"]),
                       "event_rate": rate(lambda r: r["calibrated_event"])},
        "mean_stage1_p": sum(r["stage1_p"] for r in rows) / n,
        "mean_final_p": sum(r["final_p"] for r in rows) / n,
    }
    return out


def simulate_all(*, a_curve: dict[int, float] = A_CURVE_QWEN,
                 n_sims: int = 200, seed: int = 1,
                 screen_config: ScreenConfig = DEFAULT_SCREEN_CONFIG,
                 rescreen_config: RescreenConfig = DEFAULT_RESCREEN_CONFIG,
                 archetypes: Sequence[str] = tuple(ARCHETYPES)
                 ) -> dict[str, Any]:
    results = {}
    for i, name in enumerate(archetypes):
        results[name] = simulate_case(
            ARCHETYPES[name], a_curve, n_sims=n_sims, seed=seed + 1000 * i,
            screen_config=screen_config, rescreen_config=rescreen_config)
    return {"a_curve": {str(k): v for k, v in a_curve.items()},
            "n_sims": n_sims, "seed": seed,
            "screen_config": _config_dict(screen_config),
            "rescreen_config": {"max_batches": rescreen_config.max_batches,
                                "layout": rescreen_config.layout,
                                "batch_topics": rescreen_config.batch_topics,
                                "batch_draws": rescreen_config.batch_draws,
                                "reserve_picks_per_batch":
                                    rescreen_config.reserve_picks_per_batch,
                                "include_a_grid":
                                    rescreen_config.include_a_grid},
            "results": results}
