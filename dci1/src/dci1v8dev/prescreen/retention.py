"""Deliberately spaced rung retention, per arm.

§12.7 carries every Tier-1/2 rung and the 24 Tier-3 rungs **nearest iota_A**
on the pre-screen point estimate. That ordering preserves the neighbourhood
of A and discards the shape of every Tier-3 ladder: a Tier-3 family that
straddled at the screen cannot span 0.40 at calibration by construction,
because only its nearest rungs were measured. Tier-1/2 ladders keep their
shape only because all eight rungs are carried unconditionally.

This module retains by **role** instead. For a family the screen accepted as
a spectrum candidate it carries a spaced subset of the rungs that are likely
admissible: the hard extreme, an intermediate-hard rung, the rung nearest A,
an intermediate-easy rung and the easy extreme --- as many of those as exist
(five when the ladder has them, fewer when it does not). For a family the
screen labelled a local candidate it carries the rungs most likely to sit
inside the caliper. The two arms get their own rule, a rung can serve both,
and the class and near-form arms keep the few rungs §12.6's C7 and C8 need.

Family diversity is applied here, deterministically: spectrum families are
taken in score order **preferring a feature group not yet represented**, then
by score, then by family id; the same for local families. Every choice has a
recorded reason.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci1v7.protocol import constants as C
from dci1v7.stages.selection import restrictiveness_key
from dci1v8dev import rules as R
from dci1v8dev.prescreen.geometry import DEFAULT_GEOMETRY
from dci1v8dev.prescreen.screen import LOCAL_LABEL, SCREEN_ACCEPT, SPECTRUM_LABEL

#: The offsets the spectrum needs (the screen's geometry defaults), used only
#: to record whether a retained family reaches them.
C_D_BELOW = DEFAULT_GEOMETRY.d_below
C_D_ABOVE = DEFAULT_GEOMETRY.d_above

__all__ = ["ROLES", "RetentionConfig", "retain", "spaced_subset"]

ROLES = ("HARD_EXTREME", "INTERMEDIATE_HARD", "NEAR_A", "INTERMEDIATE_EASY",
         "EASY_EXTREME", "LOCAL", "CLASS_ARM", "NEAR_FORM_ARM")


@dataclass(frozen=True)
class RetentionConfig:
    spectrum_rungs: int = R.RETENTION_SPECTRUM_RUNGS
    local_rungs: int = R.RETENTION_LOCAL_RUNGS
    #: A rung is retainable for a role when P(admissible) is at least this.
    admissible_min: float = R.RETENTION_ADMISSIBLE_MIN
    max_spectrum_families: int = R.RETENTION_MAX_SPECTRUM_FAMILIES
    #: §13.15 needs ≥ 5 families passing the full V(R); three become core
    #: references and two backups. Ten local families (three rungs each) is
    #: the budget that keeps every plausible one on the twelve stored
    #: replications (the backtest's local-recovery table) at 30 rungs.
    max_local_families: int = R.RETENTION_MAX_LOCAL_FAMILIES
    class_arm_rungs: int = R.RETENTION_CLASS_ARM_RUNGS
    near_form_rungs: int = R.RETENTION_NEAR_FORM_RUNGS
    #: Cap on the total forwarded set; None means no cap. 112 is what §12.7
    #: sends today, so a like-for-like comparison uses it.
    total_cap: int | None = None


DEFAULT_RETENTION_CONFIG = RetentionConfig()


def spaced_subset(rung_rows: Sequence[Mapping[str, Any]], *, iota_a: float,
                  n: int, admissible_min: float) -> list[dict[str, Any]]:
    """Up to ``n`` rungs by role, from those likely admissible.

    Roles are assigned in a fixed order and never duplicate a rung. With
    ``n < 5`` the roles are taken in the order HARD_EXTREME, EASY_EXTREME,
    NEAR_A, INTERMEDIATE_HARD, INTERMEDIATE_EASY, so a small budget still
    keeps the shape.
    """
    pool = [r for r in rung_rows
            if r["p_admissible"] >= admissible_min and r["iota_mean"] is not None]
    if not pool:
        return []
    by = {r["candidate"]: r for r in pool}
    chosen: dict[str, str] = {}      # candidate -> role

    def take(role: str, key, subset=None):
        cands = [r for r in (subset if subset is not None else pool)
                 if r["candidate"] not in chosen]
        if not cands:
            return
        best = min(cands, key=key)
        chosen[best["candidate"]] = role

    lo = min(r["iota_mean"] for r in pool)
    hi = max(r["iota_mean"] for r in pool)
    order = [
        ("HARD_EXTREME", lambda r: (r["iota_mean"], r["candidate"])),
        ("EASY_EXTREME", lambda r: (-r["iota_mean"], r["candidate"])),
        ("NEAR_A", lambda r: (abs(r["iota_mean"] - iota_a), r["candidate"])),
        ("INTERMEDIATE_HARD", lambda r: (abs(r["iota_mean"]
                                             - 0.5 * (lo + iota_a)),
                                         r["candidate"])),
        ("INTERMEDIATE_EASY", lambda r: (abs(r["iota_mean"]
                                             - 0.5 * (hi + iota_a)),
                                         r["candidate"])),
    ]
    for role, key in order:
        if len(chosen) >= n:
            break
        take(role, key)
    return [{"candidate": c, "role": role, "severity": by[c]["severity"],
             "iota_mean": by[c]["iota_mean"],
             "p_admissible": by[c]["p_admissible"]}
            for c, role in chosen.items()]


def _diverse_order(verdicts: Mapping[str, Mapping[str, Any]],
                   families: Sequence[str], *, score_key: str,
                   limit: int) -> list[str]:
    """Score order, preferring an unrepresented feature group first."""
    remaining = sorted(families, key=lambda k: (-verdicts[k][score_key], k))
    chosen: list[str] = []
    groups: set[str] = set()
    for kind in list(remaining):
        if len(chosen) >= limit:
            break
        if verdicts[kind]["feature_group"] not in groups:
            chosen.append(kind)
            groups.add(verdicts[kind]["feature_group"])
    for kind in remaining:
        if len(chosen) >= limit:
            break
        if kind not in chosen:
            chosen.append(kind)
    return chosen


def retain(screen: Mapping[str, Any], *, config: RetentionConfig
           ) -> dict[str, Any]:
    verdicts = screen["families"]
    iota_a = screen["iota_a"]["iota_a_mean"]
    forwarded: dict[str, dict[str, Any]] = {}

    def add(candidate: str, family: str, role: str, reason: str,
            severity: int, iota_mean):
        entry = forwarded.setdefault(candidate, {
            "candidate": candidate, "family": family, "severity": severity,
            "structural_tier": verdicts[family]["structural_tier"],
            "feature_group": verdicts[family]["feature_group"],
            "iota_mean": iota_mean, "roles": [], "reasons": []})
        if role not in entry["roles"]:
            entry["roles"].append(role)
            entry["reasons"].append(reason)

    # --- spectrum families: spaced subsets, diversity first
    spectrum_families = [k for k, v in verdicts.items()
                         if SPECTRUM_LABEL in v["labels"]
                         and v["status"] == SCREEN_ACCEPT]
    spectrum_order = _diverse_order(verdicts, spectrum_families,
                                    score_key="score_spectrum",
                                    limit=config.max_spectrum_families)
    spectrum_plan: dict[str, list[dict[str, Any]]] = {}
    for kind in spectrum_order:
        subset = spaced_subset(verdicts[kind]["rungs"], iota_a=iota_a,
                               n=config.spectrum_rungs,
                               admissible_min=config.admissible_min)
        spectrum_plan[kind] = subset
        for s in subset:
            add(s["candidate"], kind, s["role"],
                f"spectrum candidate (P={verdicts[kind]['p_spectrum']:.2f}), "
                f"role {s['role']}", s["severity"], s["iota_mean"])

    # --- local families: the rungs most likely inside the caliper
    local_families = [k for k, v in verdicts.items() if LOCAL_LABEL in v["labels"]]
    local_order = _diverse_order(verdicts, local_families,
                                 score_key="score_local",
                                 limit=config.max_local_families)
    local_plan: dict[str, list[str]] = {}
    for kind in local_order:
        rows = sorted((r for r in verdicts[kind]["rungs"]
                       if r["p_admissible"] >= config.admissible_min),
                      key=lambda r: (-r["p_local"],
                                     abs((r["iota_mean"] if r["iota_mean"]
                                          is not None else 9) - iota_a),
                                     restrictiveness_key(kind, r["severity"])))
        picks = rows[:config.local_rungs]
        local_plan[kind] = [r["candidate"] for r in picks]
        for r in picks:
            add(r["candidate"], kind, "LOCAL",
                f"local candidate (P(local)={r['p_local']:.2f})",
                r["severity"], r["iota_mean"])

    # --- class arm (C7): Tier-3 budget rungs nearest A, and near-form (C8)
    tier3_budget = [(r["p_local"], -abs((r["iota_mean"] or 9) - iota_a),
                     k, r) for k, v in verdicts.items()
                    if v["structural_tier"] == 3
                    and v["constraint_class"] == "budget"
                    for r in v["rungs"]
                    if r["p_admissible"] >= config.admissible_min]
    tier3_budget.sort(key=lambda t: (-t[0], -t[1], t[2], t[3]["severity"]))
    seen_fam: set[str] = set()
    n_class = 0
    for p_local, _, kind, r in tier3_budget:
        if n_class >= config.class_arm_rungs or kind in seen_fam:
            continue
        seen_fam.add(kind)
        n_class += 1
        add(r["candidate"], kind, "CLASS_ARM",
            f"§12.6 C7 / §13.10 class-arm candidate (P(local)={p_local:.2f})",
            r["severity"], r["iota_mean"])
    tier2 = [(r["p_local"], k, r) for k, v in verdicts.items()
             if v["structural_tier"] == 2 for r in v["rungs"]
             if r["p_admissible"] >= config.admissible_min]
    tier2.sort(key=lambda t: (-t[0], t[1], t[2]["severity"]))
    seen_groups: set[str] = set()
    n_nf = 0
    for p_local, kind, r in tier2:
        g = verdicts[kind]["feature_group"]
        if n_nf >= config.near_form_rungs or g in seen_groups:
            continue
        seen_groups.add(g)
        n_nf += 1
        add(r["candidate"], kind, "NEAR_FORM_ARM",
            f"§12.6 C8 / §13.9 near-form candidate (P(local)={p_local:.2f})",
            r["severity"], r["iota_mean"])

    # The guarantee this module exists for, recorded per spectrum family: a
    # rung at or beyond each offset is carried whenever the screen found one
    # likely admissible there, so the geometry the screen discovered reaches
    # calibration.
    geometry = {}
    for kind, subset in spectrum_plan.items():
        roles = {s["role"]: s for s in subset}
        lo = min((s["iota_mean"] for s in subset), default=None)
        hi = max((s["iota_mean"] for s in subset), default=None)
        geometry[kind] = {
            "n_rungs": len(subset), "roles": sorted(roles),
            "iota_min": lo, "iota_max": hi,
            "carries_hard_extreme": "HARD_EXTREME" in roles,
            "carries_easy_extreme": "EASY_EXTREME" in roles,
            "reaches_below_offset": lo is not None and lo <= iota_a - C_D_BELOW,
            "reaches_above_offset": hi is not None and hi >= iota_a + C_D_ABOVE,
        }
    ordered = sorted(forwarded.values(),
                     key=lambda e: (-(verdicts[e["family"]]["score_spectrum"]
                                      + verdicts[e["family"]]["score_local"]),
                                    e["family"], e["severity"]))
    dropped_for_cap: list[str] = []
    if config.total_cap is not None and len(ordered) > config.total_cap:
        dropped_for_cap = [e["candidate"] for e in ordered[config.total_cap:]]
        ordered = ordered[:config.total_cap]
    per_rung = 2 * C.N_CALIBRATION_A * C.M_CAL
    return {
        "forwarded": ordered,
        "n_forwarded": len(ordered),
        "spectrum_families": spectrum_order,
        "spectrum_plan": spectrum_plan,
        "spectrum_geometry": geometry,
        "local_families": local_order,
        "local_plan": local_plan,
        "dropped_for_cap": dropped_for_cap,
        "calibration_cost_generations": len(ordered) * per_rung,
        "per_rung_calibration_generations": per_rung,
        "config": {"spectrum_rungs": config.spectrum_rungs,
                   "local_rungs": config.local_rungs,
                   "admissible_min": config.admissible_min,
                   "max_spectrum_families": config.max_spectrum_families,
                   "max_local_families": config.max_local_families,
                   "class_arm_rungs": config.class_arm_rungs,
                   "near_form_rungs": config.near_form_rungs,
                   "total_cap": config.total_cap},
    }
