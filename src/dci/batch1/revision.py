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
           "reporting",
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
    coverage_only = {p: 0 for p in CONTRASTS}
    every = gates_passed = 0
    for _ in range(cfg.forecast_draws):
        theta = rng.beta(k + 1, n - k + 1)
        theta_a = rng.beta(ka + 1, na - ka + 1)[0]
        gates = rules.gates(theta_a, rng.beta(kb + 1, nb - kb + 1))
        gates_passed += gates
        sup = rules.supported(theta, theta_a)
        covered = {p: rules.feasible(sup[p]) for p in CONTRASTS}
        flags = {p: gates and covered[p] for p in CONTRASTS}
        for p in CONTRASTS:
            counts[p].append(len(sup[p]))
            feasible[p] += flags[p]
            coverage_only[p] += covered[p]
        every += all(flags.values())
    draws = cfg.forecast_draws
    contrasts = {p: {"point_supported": len(point[p]),
                     "mean_supported": round(float(np.mean(counts[p])), 3),
                     "interval_90": [int(np.percentile(counts[p], 5)),
                                     int(np.percentile(counts[p], 95))],
                     "p_feasible": round(feasible[p] / draws, 4),
                     "p_coverage_ignoring_gates":
                         round(coverage_only[p] / draws, 4)}
                 for p in CONTRASTS}
    stop = [p for p in CONTRASTS
            if contrasts[p]["p_feasible"] < cfg.forecast_min_feasible]
    p_gates = round(gates_passed / draws, 4)
    # Whom an early stop blames (audit, minor): the library, or the fixed
    # A and B, which no library can rescue.
    library = [p for p in stop if contrasts[p]["p_coverage_ignoring_gates"]
               < cfg.forecast_min_feasible]
    return {"schema": "dci.batch1/forecast/v2", "draws": draws,
            "seed": cfg.forecast_seed, "threshold": cfg.forecast_min_feasible,
            "numpy": np.__version__,
            "contrasts": contrasts, "point_gates_pass": point_gates,
            "p_fixed_gates_pass": p_gates,
            "p_all_feasible": round(every / draws, 4),
            "early_stop": bool(stop), "stopped_contrasts": stop,
            "library_limited": library,
            "fixed_gates_limited": p_gates < cfg.forecast_min_feasible}


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
        if cfg.carry_mode == "all" or (
                c.cid in compatible and plausibly_eligible
                and best >= cfg.carry_min_posterior):
            ranked.append((-best, c.cid, best))
    ranked.sort()
    # A task-only row is scored against every constraint, so tables hold one
    # task-only count per (model, constraint): count a model's rows once.
    task_rows = {}
    for key, c in tables.task_only.items():
        model = key.split("|")[0]
        task_rows[model] = max(task_rows.get(model, 0), c.n)
    stage1_rows = sum(c.n for c in tables.explicit.values()) + \
        sum(task_rows.values())
    per_ref = len(mfs) * cfg.stage2_topics * cfg.stage2_draws
    fixed = (1 + len(cfg.b_limits)) * len(mfs) * cfg.stage2_topics * \
        cfg.stage2_draws + len(cfg.models) * cfg.stage2_topics
    room = max(0, (cfg.max_total_rows - stage1_rows - fixed) // per_ref)
    cap = min(cfg.carry_max_references, room)
    if cfg.carry_mode == "all" and cap < len(ranked):
        raise ValueError(f"carry mode 'all' needs {len(ranked)} references "
                         f"on T2 but the budget max_total_rows="
                         f"{cfg.max_total_rows} leaves room for {cap}")
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
        "rule": ("v2.1: every reference on T2 (audit B1); R8 early stop"
                 if cfg.carry_mode == "all" else
                 "R7 carry rule; R8 early stop"),
        "carry_mode": cfg.carry_mode, "stage1_rows": stage1_rows,
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


# ---------------------------------------------------------------- reporting

def _support(feas: Mapping[str, Any]) -> dict[str, Any]:
    return {**{p: {"supported": feas[p]["supported_configurations"],
                   "feasible": feas[p]["feasible"]} for p in CONTRASTS},
            "all_feasible": feas["all_feasible"]}


def _matched_coverage(result: Mapping[str, Any], cfg: CFG.PilotConfig,
                      compat: Mapping[str, Any], elig: Mapping[str, Any],
                      matched_of) -> dict[str, Any]:
    """D11 on the primary pools with another matched set per configuration."""
    focal = L.constraint_by_id()[cfg.fixed_a]
    refs = L.reference_library()
    eligible = R.eligible_ids(elig)
    reports = []
    for rep in result["configurations"]:
        ok = COMPAT.compatible_ids(dict(compat), rep["b_limit"])
        pool = [c for c in refs if c.cid in eligible and c.cid in ok]
        pops = R.populations(focal, pool, matched_of(rep))
        reports.append({"model": rep["model"], "frame": rep["frame"],
                        "b_limit": rep["b_limit"],
                        "a_informative": rep["a_informative"],
                        "coverage": R.coverage(focal, pops, rep["funnel"],
                                               cfg)})
    return _support(R.feasibility(reports, cfg, result["b"]["selected"]))


def _two_by_two(pairs) -> dict[str, int]:
    out = {"both": 0, "t1_only": 0, "t2_only": 0, "neither": 0}
    for a, b in pairs:
        out["both" if a and b else "t1_only" if a else
            "t2_only" if b else "neither"] += 1
    return out


def reporting(t2: PilotTables, t1: PilotTables, cfg: CFG.PilotConfig,
              compat: Mapping[str, Any], result: Mapping[str, Any],
              forecast_record: Mapping[str, Any]) -> dict[str, Any]:
    """What protocol v2 reports beside its verdict, never deciding it:

    * R5(a): coverage on T2 under matching at +/-0.15 and +/-0.20, under
      confident matching (Newcombe interval inside +/-0.10) and under iota
      matching; posterior P(match) per reference and model-frame on T2;
    * section 5.2 D: T1-versus-T2 agreement on eligibility, on raw matching
      to A, and of the forecast's point coverage with the verdict's (a
      winner's-curse diagnostic);
    * R3: A x 4, x 5 and x 6 on T1 (D08 headroom and G1 support), as
      diagnostics only."""
    from dci.batch1 import calibration as CAL
    out: dict[str, Any] = {"schema": "dci.batch1/v2-reporting/v1",
                           "deciding": False}
    mfs = R.model_frames(cfg)
    elig1 = R.eligibility(t1, cfg)
    a_diag = CAL.select_a(t1, cfg, compat, elig1, list(cfg.b_limits))
    out["a_diagnostics_t1"] = [
        {k: v for k, v in row.items() if k != "cells"}
        for row in a_diag["ranking"]]
    if not result.get("configurations"):
        out.update(sensitivities=None, posterior_match_t2=None,
                   agreement=None)
        return out
    elig2 = result["eligibility"]
    focal = L.constraint_by_id()[cfg.fixed_a]
    sens = {}
    for tol in CFG.V2_MATCHING_REPORTS["tolerances"]:
        c2 = replace(cfg, matching_tolerance=tol)
        reps = [R.configuration_report(t2, c2, compat, elig2, focal,
                                       model, frame, m)
                for model, frame in mfs for m in result["b"]["selected"]]
        sens[f"tolerance_{tol}"] = _support(
            R.feasibility(reps, c2, result["b"]["selected"]))
    sens["confident"] = _matched_coverage(
        result, cfg, compat, elig2, lambda rep: {
            cid for cid, mt in rep["matching"].items()
            if mt.get("within_tolerance_with_confidence")})
    sens["iota"] = _matched_coverage(
        result, cfg, compat, elig2, lambda rep: {
            cid for cid, mt in rep["matching"].items() if mt.get("iota")})
    sens["primary"] = _support(result["feasibility"])
    out["sensitivities"] = sens
    measured = sorted({key.split("|")[-1] for key in t2.explicit}
                      & {c.cid for c in L.reference_library()})
    k, n = _cells(t2, cfg, measured)
    ka, na = _cells(t2, cfg, [cfg.fixed_a])
    rng = np.random.default_rng(cfg.forecast_seed + 2)
    hits = np.zeros(k.shape)
    for _ in range(cfg.forecast_draws):
        hits += np.abs(rng.beta(k + 1, n - k + 1)
                       - rng.beta(ka + 1, na - ka + 1)) <= cfg_tol(cfg)
    p = hits / cfg.forecast_draws
    out["posterior_match_t2"] = {
        "draws": cfg.forecast_draws, "seed": cfg.forecast_seed + 2,
        "numpy": np.__version__,
        "by_model_frame": {f"{mo}|{fr}": {cid: round(float(p[i, j]), 4)
                                          for i, cid in enumerate(measured)
                                          if p[i, j] > 0}
                           for j, (mo, fr) in enumerate(mfs)}}
    eligible1, eligible2 = R.eligible_ids(elig1), R.eligible_ids(elig2)
    match_pairs = []
    for model, frame in mfs:
        for cid in measured:
            m1 = R.match(t1, cfg, model, frame, cfg.fixed_a, cid)["raw"]
            m2 = R.match(t2, cfg, model, frame, cfg.fixed_a, cid)["raw"]
            match_pairs.append((bool(m1), bool(m2)))
    out["agreement"] = {
        "references": len(measured),
        "eligibility": _two_by_two((cid in eligible1, cid in eligible2)
                                   for cid in measured),
        "raw_match_to_a": _two_by_two(match_pairs),
        "coverage": {p_: {"forecast_point": forecast_record["contrasts"][p_]
                          ["point_supported"],
                          "forecast_mean": forecast_record["contrasts"][p_]
                          ["mean_supported"],
                          "verdict": result["feasibility"][p_]
                          ["supported_configurations"]}
                     for p_ in CONTRASTS}}
    return out
