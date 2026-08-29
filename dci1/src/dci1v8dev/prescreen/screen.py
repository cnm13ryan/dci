"""The family screen: from pre-screen counts to probabilities, statuses, labels.

**The principle.** Do not ask "does the observed ladder span 0.40?"; ask
"how much evidence is there that the true ladder supports what the spectrum
needs?". Every rung's solo, chance and vacuity rate gets a Beta posterior
from its counts; iota_A gets one from A's grid **with §12.3's severity
selection re-run inside every draw**, because the calibrated iota_A is not
the pre-screen point but the coordinate of whichever severity calibration
then selects; and the registered calibration-basis geometry --- eligibility,
straddle, rung count, span, support below and above A, the local caliper ---
is evaluated on every joint draw. What the screen reports per family is the
share of draws in which each event holds: ``P(C4)``, ``P(support both
sides)``, ``P(local match)``, and so on.

**Three admissibility readings, deliberately.** ``eligible`` is §12.6's E2
predicate (raw solo inside [0.10, 0.90], vacuity <= 0.10, coordinate defined)
and is what C4 counts. ``local-admissible`` adds §13.4's chance ceiling
(kappa <= 0.75) and lift floor (p - kappa >= 0.20) on the same band --- what
a core reference must pass --- and is what the local event is read on.
``spectrum-admissible`` applies the same chance and lift rules on the
spectrum guard band [0.10, 0.95] (``spectrum.validity.SpectrumRule``: the
headroom band protects the reference's own composed compliance, which a
spectrum slot never reads) and is what the support-below/above events are
read on. A family whose apparent spread rests on chance-inflated Tier-3
rungs is credited with none of it under any reading.

**Statuses and labels.** A family's spectrum verdict is one of
``SCREEN_ACCEPT`` / ``SCREEN_REJECT`` / ``SCREEN_RESAMPLE`` on
``P(spectrum event)`` against two thresholds; the middle band is exactly the
set of families whose classification the pre-screen cannot settle and which
the targeted second pass (``rescreen``) buys more evidence for. Labels are
separate from statuses because the two arms want different things:
``SPECTRUM_REFERENCE_CANDIDATE`` is a family whose ladder supports both sides
of A; ``LOCAL_REFERENCE_CANDIDATE`` is a family with a rung the caliper
around A is likely to admit. A family can carry both, one, or neither.

**What the score is not.** There is no weighted composite tuned on history.
The ranking score *is* the spectrum-support probability, with the local
probability ranked separately; the other factors the task lists ---
straddling, span, uncertainty, chance risk, vacuity risk --- are inside those
probabilities by construction, monotonicity is reported as a ladder class,
and family diversity is handled at retention where it belongs.

Thresholds ``accept`` / ``reject`` are chosen from the simulation's operating
characteristics (``dci1v8dev.simulate``) and never from the historical
calibration verdicts; the backtest reports them as prospective.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.stages.selection import restrictiveness_key
from dci1v7.verifiers.constraints import FAMILIES
from dci1v8dev.prescreen.geometry import Geometry, evaluate_draws, select_iota_a
from dci1v8dev.prescreen.ladder import ladder_diagnostics
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.statistics import (
    TOPIC_ICC,
    Z_FOR_LEVEL,
    beta_interval,
    beta_mean,
    beta_params,
    beta_sd,
    conservative_span,
    effective_n,
    family_seed,
    hierarchical_draws,
    posterior_draws,
    shrink_toward_trend,
)

__all__ = [
    "LOCAL_LABEL",
    "SCREEN_ACCEPT",
    "SCREEN_REJECT",
    "SCREEN_RESAMPLE",
    "SCREEN_STATUSES",
    "SPECTRUM_EVENTS",
    "SPECTRUM_LABEL",
    "ScreenConfig",
    "a_grid_draws",
    "family_posterior",
    "screen_families",
    "screen_family",
]

SCREEN_ACCEPT = "SCREEN_ACCEPT"
SCREEN_REJECT = "SCREEN_REJECT"
SCREEN_RESAMPLE = "SCREEN_RESAMPLE"
SCREEN_STATUSES = (SCREEN_ACCEPT, SCREEN_REJECT, SCREEN_RESAMPLE)
LOCAL_LABEL = "LOCAL_REFERENCE_CANDIDATE"
SPECTRUM_LABEL = "SPECTRUM_REFERENCE_CANDIDATE"
#: The family-level events a spectrum verdict may be taken on.
SPECTRUM_EVENTS = ("support_both", "c4")


@dataclass(frozen=True)
class ScreenConfig:
    geometry: Geometry = field(default_factory=Geometry)
    #: Monte Carlo draws per family. 4000 gives a Monte Carlo SE of about
    #: 0.008 on a probability near 0.5, small against the decision bands.
    draws: int = 4000
    base_seed: int = 20260829
    icc: float = TOPIC_ICC
    #: Status thresholds on P(spectrum event).
    accept: float = 0.75
    reject: float = 0.15
    #: A rung is a local candidate when P(admissible & within caliper) is at
    #: least this; the family carries the label when any rung does.
    local_accept: float = 0.50
    spectrum_event: str = "support_both"
    chance_max: float = C.CHANCE_MAX
    lift_min: float = C.INSTRUCTION_LIFT_MIN
    #: Rungs at the band edges are reported as fragile within this margin.
    edge_margin: float = 0.05
    #: Draw each family's ladder jointly from the random-effects posterior
    #: around its trend (``statistics.hierarchical_draws``) rather than from
    #: independent per-rung posteriors. The task's §3C: a lucky extreme, or
    #: many rungs near a boundary, cannot certify a family on their own.
    shrinkage: bool = True

    def __post_init__(self):
        if self.spectrum_event not in SPECTRUM_EVENTS:
            raise ProtocolError(f"{self.spectrum_event!r} is not one of "
                                f"{SPECTRUM_EVENTS}")
        if not 0.0 <= self.reject < self.accept <= 1.0:
            raise ProtocolError("need 0 <= reject < accept <= 1")
        if self.draws < 100:
            raise ProtocolError("too few Monte Carlo draws")


DEFAULT_SCREEN_CONFIG = ScreenConfig()


def _rung_params(r: PrescreenRung, icc: float) -> dict[str, tuple[float, float]]:
    n_eff = effective_n(r.n_topics, r.draws_per_topic, icc=icc)
    # The chance basis is stated in topic units (schema), so its effective
    # size is the smaller of the stated basis and the solo effective size.
    c_eff = min(float(r.chance_n), n_eff)
    return {"p": beta_params(r.solo_k, r.solo_n, n_eff=n_eff),
            "kappa": beta_params(r.chance_k, r.chance_n, n_eff=c_eff),
            "vac": beta_params(r.vacuous_k, r.solo_n, n_eff=n_eff)}


def a_grid_draws(a_grid: Sequence[ARung], *, config: ScreenConfig
                 ) -> dict[str, Any]:
    """Posterior draws of iota_A, with §12.3's selection inside each draw."""
    grid = sorted(a_grid, key=lambda a: a.severity)
    if not grid:
        raise ProtocolError("the screen needs A's grid on the pre-screen")
    rng = np.random.default_rng(family_seed("A", base_seed=config.base_seed))
    p_params, k_params = [], []
    for a in grid:
        n_eff = effective_n(a.n_topics, a.draws_per_topic, icc=config.icc)
        p_params.append(beta_params(a.solo_k, a.solo_n, n_eff=n_eff))
        k_params.append(beta_params(a.chance_k, a.chance_n,
                                    n_eff=min(float(a.chance_n), n_eff)))
    p = posterior_draws(rng, p_params, config.draws)
    k = posterior_draws(rng, k_params, config.draws)
    iota_a, n_star = select_iota_a(p, k, [a.severity for a in grid])
    ok = ~np.isnan(iota_a)
    if not ok.any():
        raise ProtocolError("iota_A is undefined in every draw (A's chance "
                            "compliance is degenerate)")
    values, counts = np.unique(n_star[ok], return_counts=True)
    return {"iota_a": iota_a, "n_star": n_star,
            "iota_a_mean": float(np.nanmean(iota_a)),
            "iota_a_sd": float(np.nanstd(iota_a)),
            "iota_a_q05": float(np.nanpercentile(iota_a, 5)),
            "iota_a_q95": float(np.nanpercentile(iota_a, 95)),
            "n_star_distribution": {int(v): float(c) / float(ok.sum())
                                    for v, c in zip(values, counts)},
            "severities": [a.severity for a in grid]}


def family_posterior(kind: str, rungs: Sequence[PrescreenRung],
                     iota_a_draws: np.ndarray, *, config: ScreenConfig
                     ) -> dict[str, Any]:
    """Joint posterior draws of one family's rungs, evaluated geometrically."""
    if not rungs:
        raise ProtocolError(f"{kind}: no measured rung")
    if any(r.kind != kind for r in rungs):
        raise ProtocolError(f"{kind}: rungs of another family supplied")
    rungs = sorted(rungs, key=lambda r: r.severity)
    if len({r.severity for r in rungs}) != len(rungs):
        raise ProtocolError(f"{kind}: a severity appears twice")
    S = int(iota_a_draws.shape[0])
    rng = np.random.default_rng(family_seed(kind, base_seed=config.base_seed))
    params = [_rung_params(r, config.icc) for r in rungs]
    if config.shrinkage:
        # joint draws of the solo rate around the family's trend in
        # restrictiveness; chance and vacuity stay per-rung
        x = [restrictiveness_key(kind, r.severity) for r in rungs]
        means = [beta_mean(*q["p"]) for q in params]
        sds = [beta_sd(*q["p"]) for q in params]
        p = hierarchical_draws(rng, x, means, sds, S)
    else:
        p = posterior_draws(rng, [q["p"] for q in params], S)
    kappa = posterior_draws(rng, [q["kappa"] for q in params], S)
    vac = posterior_draws(rng, [q["vac"] for q in params], S)
    # A draw in which iota_A is undefined cannot place anything; drop it.
    keep = ~np.isnan(iota_a_draws)
    p, kappa, vac, ia = p[keep], kappa[keep], vac[keep], iota_a_draws[keep]
    geometry = config.geometry
    eligible_view = evaluate_draws(p, kappa, vac, ia, geometry=geometry,
                                   edge_margin=config.edge_margin)
    # §13.4's chance ceiling and lift floor: a rung failing either is pushed
    # out of the band for both admissible readings.
    extra = (kappa <= config.chance_max) & ((p - kappa) >= config.lift_min)
    p_adm = np.where(extra, p, -1.0)
    local_view = evaluate_draws(p_adm, kappa, vac, ia, geometry=geometry,
                                edge_margin=config.edge_margin)
    spectrum_view = evaluate_draws(p_adm, kappa, vac, ia, geometry=geometry,
                                   edge_margin=config.edge_margin,
                                   band=geometry.spectrum_band)
    return {"kind": kind, "rungs": rungs, "params": params, "p": p,
            "kappa": kappa, "vac": vac, "iota_a": ia,
            "eligible_view": eligible_view,
            "local_view": local_view,
            "admissible_view": spectrum_view,
            "n_draws_used": int(keep.sum())}


def _rung_summary(post: Mapping[str, Any], config: ScreenConfig
                  ) -> list[dict[str, Any]]:
    rungs = post["rungs"]
    ev, av, lv = post["eligible_view"], post["admissible_view"], post["local_view"]
    ia = post["iota_a"][:, None]
    out = []
    for j, r in enumerate(rungs):
        pa, pb = post["params"][j]["p"]
        ka, kb = post["params"][j]["kappa"]
        iota = ev.iota[:, j]
        finite = ~np.isnan(iota)
        iota_mean = float(np.mean(iota[finite])) if finite.any() else None
        iota_sd = float(np.std(iota[finite])) if finite.any() else None
        if finite.sum() > 10:
            lo, hi = np.percentile(iota[finite], [16, 84])
            lo90, hi90 = np.percentile(iota[finite], [5, 95])
        else:
            lo = hi = lo90 = hi90 = float("nan")
        out.append({
            "candidate": r.label, "severity": r.severity,
            "reserve": r.reserve,
            "solo_k": r.solo_k, "solo_n": r.solo_n,
            "solo_rate": r.solo_rate, "chance_rate": r.chance_rate,
            "point_eligible": bool(
                config.geometry.band[0] <= r.solo_rate <= config.geometry.band[1]
                and r.vacuity_rate <= config.geometry.vacuity_max
                and r.chance_rate < config.geometry.degeneracy),
            "n_topics": r.n_topics, "draws_per_topic": r.draws_per_topic,
            "p_mean": beta_mean(pa, pb), "p_sd": beta_sd(pa, pb),
            "p_interval_90": list(beta_interval(pa, pb, level=0.90)),
            "kappa_mean": beta_mean(ka, kb),
            "vacuity_rate": r.vacuity_rate,
            "iota_point": ((r.solo_rate - r.chance_rate) / (1 - r.chance_rate)
                           if r.chance_rate < config.geometry.degeneracy
                           else None),
            "iota_mean": iota_mean, "iota_sd": iota_sd,
            "iota_68": [float(lo), float(hi)],
            "iota_90": [float(lo90), float(hi90)],
            "p_eligible": float(ev.eligible[:, j].mean()),
            "p_admissible": float(av.eligible[:, j].mean()),
            "p_below_a": float((av.eligible[:, j]
                                & (av.iota[:, j] < ia[:, 0])).mean()),
            "p_above_a": float((av.eligible[:, j]
                                & (av.iota[:, j] > ia[:, 0])).mean()),
            "p_below_d": float((av.eligible[:, j] & (
                av.iota[:, j] <= ia[:, 0] - config.geometry.d_below)).mean()),
            "p_above_d": float((av.eligible[:, j] & (
                av.iota[:, j] >= ia[:, 0] + config.geometry.d_above)).mean()),
            "p_local": float(lv.local[:, j].mean()),
            "p_local_admissible": float(lv.eligible[:, j].mean()),
            "p_fragile": float(ev.fragile[:, j].mean()),
            "p_chance_over_ceiling": float(
                (post["kappa"][:, j] > config.chance_max).mean()),
        })
    return out


def _comparators(kind: str, rung_rows: Sequence[Mapping[str, Any]],
                 iota_a_point: float | None, geometry: Geometry
                 ) -> dict[str, Any]:
    """Raw max-min, conservative-interval and shrinkage spans (comparators)."""
    # Point-eligible rungs only: the same population §12.6's per-family C4
    # state reads, so the raw span here is the legacy quantity.
    with_iota = [r for r in rung_rows if r["iota_point"] is not None
                 and r["point_eligible"]]
    raw = [r["iota_point"] for r in with_iota]
    out: dict[str, Any] = {"raw_span": (max(raw) - min(raw)) if len(raw) >= 2
                           else 0.0, "n_rungs_with_coordinate": len(raw)}
    for level in (0.68, 0.80, 0.90):
        z = Z_FOR_LEVEL[level]
        intervals = []
        for r in with_iota:
            m, s = r["iota_mean"], r["iota_sd"]
            if m is None or s is None:
                continue
            intervals.append((m - z * s, m + z * s))
        out[f"conservative_span_{int(level * 100)}"] = max(
            0.0, conservative_span(intervals))
    from dci1v7.stages.selection import restrictiveness_key
    xs = [restrictiveness_key(kind, r["severity"]) for r in with_iota]
    ys = [r["iota_mean"] for r in with_iota]
    ss = [r["iota_sd"] for r in with_iota]
    if len(xs) >= 2 and None not in ys and None not in ss:
        fit = shrink_toward_trend(xs, ys, ss)
        shrunk = fit["shrunk"]
        out["shrunk_span"] = (max(shrunk) - min(shrunk)) if len(shrunk) >= 2 \
            else 0.0
        out["shrinkage_tau2"] = fit["tau2"]
        if iota_a_point is not None:
            out["shrunk_straddles"] = bool(min(shrunk) < iota_a_point
                                           < max(shrunk))
    else:
        out["shrunk_span"] = 0.0
        out["shrinkage_tau2"] = None
    return out


def screen_family(kind: str, rungs: Sequence[PrescreenRung],
                  a_draws: Mapping[str, Any], *, config: ScreenConfig,
                  iota_a_point: float | None = None) -> dict[str, Any]:
    """One family's verdict. Depends on this family's counts, A's grid and the
    config only --- never on any other family."""
    post = family_posterior(kind, rungs, a_draws["iota_a"], config=config)
    ev, av, lv = post["eligible_view"], post["admissible_view"], post["local_view"]
    rung_rows = _rung_summary(post, config)
    probs = {
        "c4": float(ev.c4.mean()),
        "c4_admissible": float(lv.c4.mean()),
        "straddle": float(av.straddles.mean()),
        "support_below": float(av.support_below.mean()),
        "support_above": float(av.support_above.mean()),
        "support_both": float(av.support_both.mean()),
        "local": float(lv.family_local.mean()),
        "n_eligible_ge_min": float(
            (ev.n_eligible >= config.geometry.min_rungs).mean()),
        "n_admissible_ge_min": float(
            (av.n_eligible >= config.geometry.min_rungs).mean()),
    }
    span = av.span
    spread = {"span_mean": float(span.mean()),
              "span_q10": float(np.percentile(span, 10)),
              "span_q50": float(np.percentile(span, 50)),
              "n_admissible_mean": float(av.n_eligible.mean())}
    p_event = probs[config.spectrum_event]
    if p_event >= config.accept:
        status = SCREEN_ACCEPT
    elif p_event <= config.reject:
        status = SCREEN_REJECT
    else:
        status = SCREEN_RESAMPLE
    # The side the family most often lacks, for the second pass's direction.
    if probs["support_below"] < probs["support_above"]:
        deficiency = "MISSING_BELOW"       # needs a HARDER rung
    elif probs["support_above"] < probs["support_below"]:
        deficiency = "MISSING_ABOVE"       # needs an EASIER rung
    else:
        deficiency = "BOTH_WEAK" if p_event < config.accept else None
    # A side the family has never measured toward is not "absent": while the
    # frozen reserve holds unmeasured severities in the deficient direction
    # and the ladder is not flat, the verdict is RESAMPLE with extension, so a
    # too-easy (or too-hard) round-0 ladder is extended rather than dropped.
    # This is the pre-screen half of `prescreen.extension` (item 3 of the
    # v8 design): the reserve is explored until the posterior says the region
    # is reached or the reserve is exhausted.
    unexplored = None
    if status == SCREEN_REJECT and deficiency in ("MISSING_BELOW", "MISSING_ABOVE"):
        from dci1v8dev.prescreen.extension import reach_picks
        side = "below" if deficiency == "MISSING_BELOW" else "above"
        picks = reach_picks(kind, measured=[r.severity for r in rungs],
                            sides=[side], n=1)
        other = probs["support_above" if side == "below" else "support_below"]
        if picks and other >= config.reject:
            status = SCREEN_RESAMPLE
            unexplored = {"side": side, "next_reserve": picks,
                          "reason": "UNEXPLORED_RESERVE"}
    local_rungs = [r["candidate"] for r in rung_rows
                   if r["p_local"] >= config.local_accept]
    labels = []
    if status == SCREEN_ACCEPT:
        labels.append(SPECTRUM_LABEL)
    if local_rungs:
        labels.append(LOCAL_LABEL)
    ladder = ladder_diagnostics(
        kind, [r["severity"] for r in rung_rows],
        [r["iota_mean"] for r in rung_rows],
        [r["iota_sd"] for r in rung_rows],
        [tuple(r["iota_68"]) for r in rung_rows])
    meta = FAMILIES[kind]
    return {
        "family": kind, "structural_tier": meta.structural_tier,
        "feature_group": meta.feature_group,
        "constraint_class": meta.constraint_class,
        "n_rungs": len(rungs),
        "n_draws": post["n_draws_used"],
        "seed": family_seed(kind, base_seed=config.base_seed),
        "probabilities": probs, "spread": spread,
        "spectrum_event": config.spectrum_event,
        "p_spectrum": p_event,
        "status": status, "deficiency": deficiency,
        "unexplored_reserve": unexplored,
        "labels": labels,
        "score_spectrum": p_event,
        "score_local": max((r["p_local"] for r in rung_rows), default=0.0),
        "local_rungs": local_rungs,
        "ladder": ladder,
        "rungs": rung_rows,
        "comparators": _comparators(kind, rung_rows, iota_a_point,
                                    config.geometry),
    }


def screen_families(table: Sequence[PrescreenRung], a_grid: Sequence[ARung],
                    *, config: ScreenConfig = DEFAULT_SCREEN_CONFIG
                    ) -> dict[str, Any]:
    """Screen every family on the table. Output order is by family id."""
    by_family: dict[str, list[PrescreenRung]] = {}
    for r in table:
        by_family.setdefault(r.kind, []).append(r)
    a_draws = a_grid_draws(a_grid, config=config)
    from dci1v8dev.prescreen.legacy import prescreen_iota_a
    iota_a_point, _ = prescreen_iota_a(a_grid)
    verdicts = {kind: screen_family(kind, rungs, a_draws, config=config,
                                    iota_a_point=iota_a_point)
                for kind, rungs in sorted(by_family.items())}
    ranking = sorted(verdicts, key=lambda k: (-verdicts[k]["score_spectrum"],
                                              k))
    local_ranking = sorted(verdicts, key=lambda k: (
        -verdicts[k]["score_local"], k))
    statuses = {s: sorted(k for k, v in verdicts.items() if v["status"] == s)
                for s in SCREEN_STATUSES}
    groups_accepted = sorted({verdicts[k]["feature_group"]
                              for k in statuses[SCREEN_ACCEPT]})
    return {
        "config": _config_dict(config),
        "iota_a": {k: v for k, v in a_draws.items()
                   if k not in ("iota_a", "n_star")},
        "iota_a_prescreen_point": iota_a_point,
        "families": verdicts,
        "ranking_spectrum": ranking,
        "ranking_local": local_ranking,
        "statuses": statuses,
        "labels": {LOCAL_LABEL: sorted(k for k, v in verdicts.items()
                                       if LOCAL_LABEL in v["labels"]),
                   SPECTRUM_LABEL: sorted(k for k, v in verdicts.items()
                                          if SPECTRUM_LABEL in v["labels"])},
        "summary": {"n_families": len(verdicts),
                    "n_accept": len(statuses[SCREEN_ACCEPT]),
                    "n_reject": len(statuses[SCREEN_REJECT]),
                    "n_resample": len(statuses[SCREEN_RESAMPLE]),
                    "feature_groups_accepted": groups_accepted,
                    "ladder_classes": {
                        k: v["ladder"]["ladder_class"]
                        for k, v in verdicts.items()}},
    }


def _config_dict(config: ScreenConfig) -> dict[str, Any]:
    g = config.geometry
    return {"draws": config.draws, "base_seed": config.base_seed,
            "icc": config.icc, "accept": config.accept,
            "reject": config.reject, "local_accept": config.local_accept,
            "spectrum_event": config.spectrum_event,
            "chance_max": config.chance_max, "lift_min": config.lift_min,
            "shrinkage": config.shrinkage,
            "geometry": {"band": list(g.band), "vacuity_max": g.vacuity_max,
                         "spectrum_band": list(g.spectrum_band),
                         "degeneracy": g.degeneracy,
                         "min_rungs": g.min_rungs, "min_span": g.min_span,
                         "d_below": g.d_below, "d_above": g.d_above,
                         "caliper": g.caliper}}
