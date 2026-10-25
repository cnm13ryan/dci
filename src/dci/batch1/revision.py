"""Protocol v2 (revision 2026-10): screen on T1, decide membership on T2.

The researcher's decisions R1-R13 of 2026-10-26
(``docs/batch1/revision/APPROVALS_2026-10-26.md``) change *how* the pilot is
measured, not the scientific rules:

* **Stage A (``stage1``, T1, 48 topics)** screens every library-v2
  reference, A at 4, 5 and 6 (4 and 5 are diagnostics only, R3), B at 8 and
  10, and the task alone.
* **Stage B (``forecast``)** draws every T1 cell's compliance from its Beta
  posterior and applies D08-D11 exactly as written to each draw: the
  probability that a perfectly measured study would be feasible. If it is
  below ``forecast_min_feasible`` for any contrast the run stops before T2
  (R8): that is a statement about the library, not about noise. A draw is
  feasible only if the fixed A is admissible (D08) and each fixed B limit
  informative (R4) in it as well.
* **The carry rule (``select_carry``)** sends to T2 every reference that is
  plausibly eligible on T1 and plausibly matched to A in at least one
  model-frame (posterior P(|p_X - p_A| <= tol) >= ``carry_min_posterior``),
  at most ``carry_max_references`` of them and within the run's budget.
  Generous on purpose: pruning hard on T1 would select noise.
* **Stage C (``stage2``, T2, 96 topics)** measures the carried references,
  A x 6, B 8 and 10 and the task alone, all at the same n on the same
  topics. T2 alone decides eligibility, matching and membership; T1 never
  enters it (no winner's curse).
* **Stage D (``finalize_fixed``)**: A and B are fixed, not selected (R3,
  R4). A must still be admissible under D08's informativeness rule on T2,
  and each B limit informative under D07's band, or the verdict is
  ``A_NOT_ADMISSIBLE`` / ``B_NOT_INFORMATIVE``. D09-D11 are unchanged.

The forecast's rule code is a vectorised transcription of
``references.coverage``/``feasibility``; ``tests/batch1/test_revision.py``
checks that, on point estimates, it gives exactly what those functions give.
"""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from typing import Any, Mapping

import numpy as np

from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1.intervals import wilson
from dci.batch1.scoring import PilotTables

__all__ = ["forecast", "select_carry", "finalize_fixed", "check_fixed_b",
           "truncation_review"]

CONTRASTS = ("P1", "P2", "P3")


def _cells(tables: PilotTables, cfg: CFG.PilotConfig, cids: list[str]
           ) -> tuple[np.ndarray, np.ndarray]:
    mfs = R.model_frames(cfg)
    k = np.array([[tables.x(m, f, c).k for m, f in mfs] for c in cids], float)
    n = np.array([[tables.x(m, f, c).n for m, f in mfs] for c in cids], float)
    return k, n


class _Rules:
    """D08-D11 on arrays of true (or point) compliance, one row per
    reference, one column per model-frame."""

    def __init__(self, cfg: CFG.PilotConfig, compat: Mapping[str, Any]):
        self.cfg = cfg
        self.refs = list(L.reference_library())
        a = L.constraint_by_id()[cfg.fixed_a]
        self.mfs = R.model_frames(cfg)
        self.same = np.array([c.operation == a.operation and
                              c.object_type == a.object_type for c in self.refs])
        self.oobj = np.array([c.operation == a.operation and
                              c.object_type != a.object_type for c in self.refs])
        self.oop = np.array([c.operation != a.operation for c in self.refs])
        self.comp = {}
        for m in cfg.b_limits:
            ok = COMPAT.compatible_ids(dict(compat), m)
            self.comp[m] = np.array([c.cid in ok for c in self.refs])
        words = sorted({c.p["word"] for c in self.refs
                        if c.family_id == "exact_word_count"})
        self.word_of = np.array([[c.family_id == "exact_word_count" and
                                  c.p.get("word") == w for c in self.refs]
                                 for w in words])

    def supported(self, theta: np.ndarray, theta_a: np.ndarray
                  ) -> dict[str, list[tuple[str, int]]]:
        cfg, tol = self.cfg, cfg_tol(self.cfg)
        eligible = (theta >= cfg.eligibility_threshold).any(axis=1)
        lo, hi = cfg.a_headroom_band
        out: dict[str, list[tuple[str, int]]] = {p: [] for p in CONTRASTS}
        for j, (model, _) in enumerate(self.mfs):
            if not (lo <= theta_a[j] <= hi):
                continue                      # D08: uninformative A never counts
            matched = np.abs(theta[:, j] - theta_a[j]) <= tol
            for m in cfg.b_limits:
                pool = eligible & self.comp[m]
                g1 = pool & self.same & matched
                g2 = pool & self.same
                g3 = pool & (self.same | self.oobj) & matched
                g5 = pool & matched
                words = int(self.word_of[:, g1].any(axis=1).sum())
                g1_ok = words >= cfg.g1_min_distinct_words
                ok = {
                    "P1": g1_ok and int((g2 & ~g1).sum()) >= cfg.p1_min_additional,
                    "P2": g1_ok and int((g3 & ~g1 & self.oobj).sum())
                    >= cfg.p2_min_additional_other_object,
                    "P3": int(g3.sum()) >= cfg.p3_min_g3 and
                    int((g5 & ~g3 & self.oop).sum())
                    >= cfg.p3_min_additional_other_operation}
                for p in CONTRASTS:
                    if ok[p]:
                        out[p].append((model, m))
        return out

    def gates(self, theta_a: np.ndarray, theta_b: np.ndarray) -> bool:
        """D08's admissibility of the fixed A and R4's informativeness of
        each fixed B limit (rows of ``theta_b`` follow ``cfg.b_limits``)."""
        cfg = self.cfg
        lo, hi = cfg.a_headroom_band
        a_ok = (lo <= theta_a) & (theta_a <= hi)
        models = {self.mfs[j][0] for j in np.flatnonzero(a_ok)}
        blo, bhi = cfg.b_informative_band
        b_ok = ((blo <= theta_b) & (theta_b <= bhi)).sum(axis=1)
        return (int(a_ok.sum()) >= cfg.a_min_informative_model_frames
                and len(models) >= cfg.a_min_informative_models
                and bool((b_ok >= cfg.b_min_informative_model_frames).all()))

    def feasible(self, supported: list[tuple[str, int]]) -> bool:
        cfg = self.cfg
        return (len(supported) >= cfg.feasibility_min_configs
                and len({s[0] for s in supported}) >= cfg.feasibility_min_models
                and sorted({s[1] for s in supported}) == sorted(cfg.b_limits))


def _b_ids(cfg: CFG.PilotConfig) -> list[str]:
    by_m = {b.p["m"]: b.cid for b in L.b_candidates()}
    return [by_m[m] for m in cfg.b_limits]


def cfg_tol(cfg: CFG.PilotConfig) -> float:
    # Exact-rational |diff| <= 0.10 in D10; a 1e-12 slack reproduces it on
    # the floats of a draw (point estimates k/n differ by multiples of 1/96).
    return float(cfg.matching_tolerance) + 1e-12


def forecast(tables: PilotTables, cfg: CFG.PilotConfig,
             compat: Mapping[str, Any]) -> dict[str, Any]:
    """Stage B: posterior coverage at perfect precision, from T1."""
    rules = _Rules(cfg, compat)
    cids = [c.cid for c in rules.refs]
    k, n = _cells(tables, cfg, cids)
    ka, na = _cells(tables, cfg, [cfg.fixed_a])
    kb, nb = _cells(tables, cfg, _b_ids(cfg))
    if (n == 0).any() or (na == 0).any() or (nb == 0).any():
        raise ValueError("the forecast needs every T1 cell measured")
    point = rules.supported(k / n, (ka / na)[0])
    point_gates = rules.gates((ka / na)[0], kb / nb)
    rng = np.random.default_rng(cfg.forecast_seed)
    counts = {p: [] for p in CONTRASTS}
    feasible = {p: 0 for p in CONTRASTS}
    every = 0
    for _ in range(cfg.forecast_draws):
        theta = rng.beta(k + 1, n - k + 1)
        theta_a = rng.beta(ka + 1, na - ka + 1)[0]
        gates = rules.gates(theta_a, rng.beta(kb + 1, nb - kb + 1))
        sup = rules.supported(theta, theta_a)
        flags = {p: gates and rules.feasible(sup[p]) for p in CONTRASTS}
        for p in CONTRASTS:
            counts[p].append(len(sup[p]))
            feasible[p] += flags[p]
        every += all(flags.values())
    draws = cfg.forecast_draws
    contrasts = {p: {"point_supported": len(point[p]),
                     "mean_supported": round(float(np.mean(counts[p])), 3),
                     "interval_90": [int(np.percentile(counts[p], 5)),
                                     int(np.percentile(counts[p], 95))],
                     "p_feasible": round(feasible[p] / draws, 4)}
                 for p in CONTRASTS}
    stop = [p for p in CONTRASTS
            if contrasts[p]["p_feasible"] < cfg.forecast_min_feasible]
    return {"schema": "dci.batch1/forecast/v1", "draws": draws,
            "seed": cfg.forecast_seed, "threshold": cfg.forecast_min_feasible,
            "contrasts": contrasts, "point_gates_pass": point_gates,
            "p_all_feasible": round(every / draws, 4),
            "early_stop": bool(stop), "library_limited": stop}


def select_carry(tables: PilotTables, cfg: CFG.PilotConfig) -> dict[str, Any]:
    """The T1 -> T2 selection: the Stage B forecast, then the carried set."""
    compat = COMPAT.compatibility_matrix()
    fc = forecast(tables, cfg, compat)
    mfs = R.model_frames(cfg)
    refs = list(L.reference_library())
    compatible = set().union(*(COMPAT.compatible_ids(compat, m)
                               for m in cfg.b_limits))
    k, n = _cells(tables, cfg, [c.cid for c in refs])
    ka, na = _cells(tables, cfg, [cfg.fixed_a])
    rng = np.random.default_rng(cfg.forecast_seed + 1)
    draws = cfg.forecast_draws
    hits = np.zeros(k.shape)
    for _ in range(draws):
        theta = rng.beta(k + 1, n - k + 1)
        theta_a = rng.beta(ka + 1, na - ka + 1)
        hits += np.abs(theta - theta_a) <= cfg_tol(cfg)
    p_match = hits / draws
    ranked = []
    for i, c in enumerate(refs):
        plausibly_eligible = any(
            wilson(int(k[i, j]), int(n[i, j]), cfg.z)[1]
            >= cfg.eligibility_threshold for j in range(len(mfs)))
        best = float(p_match[i].max())
        if c.cid in compatible and plausibly_eligible and \
                best >= cfg.carry_min_posterior:
            ranked.append((-best, c.cid, best))
    ranked.sort()
    stage1_rows = sum(c.n for c in tables.explicit.values()) + \
        sum(c.n for c in tables.task_only.values())
    per_ref = len(mfs) * cfg.stage2_topics * cfg.stage2_draws
    fixed = (1 + len(cfg.b_limits)) * len(mfs) * cfg.stage2_topics * \
        cfg.stage2_draws + len(cfg.models) * cfg.stage2_topics
    room = max(0, (cfg.max_total_rows - stage1_rows - fixed) // per_ref)
    cap = min(cfg.carry_max_references, room)
    carried = ranked[:cap]
    cells = []
    if not fc["early_stop"]:
        for _, cid, best in carried:
            cells += [{"model": m, "frame": f, "condition": cid,
                       "class": "CARRY", "distance": round(best, 4)}
                      for m, f in mfs]
        for cid in [cfg.fixed_a] + _b_ids(cfg):
            cells += [{"model": m, "frame": f, "condition": cid,
                       "class": "FIXED", "distance": 0.0} for m, f in mfs]
        cells += [{"model": m, "frame": None, "condition": "task_only",
                   "class": "TASK_ONLY", "distance": 0.0} for m in cfg.models]
    return {
        "schema": "dci.batch1/carry-selection/v1",
        "rule": "R7 carry rule; R8 early stop",
        "status": "EARLY_STOP" if fc["early_stop"] else "CARRIED",
        "forecast": fc,
        "n_candidates": len(ranked), "cap": cap,
        "truncated_by_cap": len(ranked) > cap,
        "carried": [{"condition": cid, "max_posterior_match": round(best, 4)}
                    for _, cid, best in carried],
        "not_carried": [{"condition": cid, "max_posterior_match": round(best, 4)}
                        for _, cid, best in ranked[cap:]],
        "max_stage2_rows": len(cells) and (len(carried) * per_ref + fixed),
        "cells": cells,
    }


def check_fixed_b(tables: PilotTables, cfg: CFG.PilotConfig) -> dict[str, Any]:
    """R4: B is fixed; each limit must be informative (D07's band) in at
    least ``b_min_informative_model_frames`` model-frames on T2."""
    lo, hi = (Fraction(str(x)) for x in cfg.b_informative_band)
    per_limit, failing = {}, []
    for b in L.b_candidates():
        m = b.p["m"]
        if m not in cfg.b_limits:
            continue
        cells, informative = {}, 0
        for model, frame in R.model_frames(cfg):
            count = tables.x(model, frame, b.cid)
            ok = R.usable(count, cfg) and \
                lo <= Fraction(count.k, count.n) <= hi
            cells[f"{model}|{frame}"] = {"p": count.p, "n": count.n,
                                         "informative": ok}
            informative += ok
        per_limit[str(m)] = {"cells": cells, "informative": informative}
        if informative < cfg.b_min_informative_model_frames:
            failing.append(m)
    status = "SELECTED" if not failing else "FAILED"
    return {"status": status, "selected": sorted(cfg.b_limits) if not failing
            else None, "rule": "R4: fixed, informativeness checked",
            "per_limit": per_limit,
            "flags": [f"B_NOT_INFORMATIVE: limits {failing}"] if failing else []}


def truncation_review(tables: PilotTables, cfg: CFG.PilotConfig
                      ) -> list[str]:
    """Cells whose truncated share exceeds ``truncation_review_share``, with
    at least ``truncation_review_min_rows`` truncated rows (R11)."""
    share = Fraction(str(cfg.truncation_review_share))
    return sorted(key for key, c in tables.explicit.items()
                  if c.n and c.truncated >= cfg.truncation_review_min_rows
                  and Fraction(c.truncated, c.n) > share)


def finalize_fixed(tables: PilotTables, cfg: CFG.PilotConfig,
                   compat: Mapping[str, Any], *, early_stop: bool = False
                   ) -> dict[str, Any]:
    """Stage D: D09-D11 on T2, with A and B fixed (R3, R4). After an early
    stop (R8) there is no T2 evidence and the verdict is
    ``EARLY_STOP_LIBRARY_LIMITED``."""
    from dci.batch1 import calibration as CAL
    out: dict[str, Any] = {"schema": "dci.batch1/calibration/v3-fixed",
                           "synthetic": tables.synthetic}
    if early_stop:
        out.update(status="EARLY_STOP_LIBRARY_LIMITED", eligibility={},
                   truncation_review=[], a=None,
                   b={"status": "NOT_MEASURED", "selected": None},
                   configurations=[], feasibility=None)
        return out
    elig = R.eligibility(tables, cfg)
    out.update(eligibility=elig, truncation_review=truncation_review(tables, cfg))
    b = check_fixed_b(tables, cfg)
    out["b"] = b
    if b["status"] != "SELECTED":
        out.update(status="B_NOT_INFORMATIVE", a=None, configurations=[],
                   feasibility=None)
        return out
    a_counts = (L.constraint_by_id()[cfg.fixed_a].p["n"],)
    a = CAL.select_a(tables, replace(cfg, a_counts=a_counts), compat, elig,
                     b["selected"])
    out["a"] = a
    if a["status"] != "SELECTED":
        out.update(status="A_NOT_ADMISSIBLE", configurations=[],
                   feasibility=None)
        return out
    focal = L.constraint_by_id()[cfg.fixed_a]
    reports = [R.configuration_report(tables, cfg, compat, elig, focal,
                                      model, frame, m)
               for model, frame in R.model_frames(cfg) for m in b["selected"]]
    feas = R.feasibility(reports, cfg, b["selected"])
    status = "FEASIBLE" if feas["all_feasible"] and not a["flags"] \
        else "INFEASIBLE_REVISION_REQUIRED"
    out.update(status=status, configurations=reports, feasibility=feas,
               eligible_20=sorted(R.eligible_ids(elig)),
               extension_10_only=sorted(
                   cid for cid, e in elig.items()
                   if e["status"] == R.EXTENSION_ONLY))
    return out
