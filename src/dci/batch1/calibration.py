"""Stage 2 refinement, B selection, A selection and the calibration result.

Every rule here is a **proposed default** (decisions D06, D07, D08) and runs
on stand-alone pilot tables only. The order is fixed: Stage 2 is chosen from
Stage 1; after Stage 2 every decision reads both stages pooled within a cell;
B is selected from B-only compliance; then A, using B's selection, the
eligible pool and the compatibility matrix.

**Stage 2 (D06).** One bounded round. A cell is a candidate when its Stage 1
interval straddles a decision boundary, in five classes ranked in this
order:

1. ``A_HEADROOM``   --- an A cell whose Wilson interval contains an edge of
   ``a_headroom_band``;
2. ``B_BAND``       --- a B cell whose interval contains an edge of
   ``b_informative_band``;
3. ``ELIGIBILITY_20`` --- X has no cell whose lower bound clears 20%, and
   this cell's interval contains 20%. Ahead of matching because it decides
   library membership for every model, and because matching candidates
   (three A counts x 51 references x 8 model-frames) would otherwise fill
   the cap on their own;
4. ``MATCHING``     --- for some A count, the Newcombe interval of
   p_X - p_A contains +/- ``matching_tolerance``; both the X and the A cell
   are candidates. Only X with an upper bound at or above the 10% threshold
   in some model-frame are considered;
5. ``ELIGIBILITY_10`` --- the same as 3 at 10%.

Within a class, cells closest to their boundary (standardised by the
boundary's own binomial standard error) come first; ties break on the cell
key. A cell keeps its best rank. At most ``stage2_max_cells`` are selected.
There is no third stage: what is still borderline afterwards is reported as
borderline.

**B (D07, revised 2026-10-19 after audit F9; proposed).** The statistic is
each limit's explicit B-only compliance p_B(m) per model-frame, pooled over
both stages, compared in exact arithmetic. I(m) is the number of
model-frames with p_B(m) inside ``b_informative_band``. A pair (m1 < m2)
is admissible only when all of these hold, and every failed condition is
recorded:

* m2 - m1 >= ``b_min_gap`` and both limits are complete in every cell;
* **separation**: median p_B(m2) - median p_B(m1) over the model-frames is
  at least ``b_min_median_separation``;
* **consistency**: in at least ``b_min_separated_models`` models, the
  model's own separation (mean of its frames) is at least that much, so one
  model cannot carry the contrast;
* **headroom**: each limit is informative in at least
  ``b_min_informative_model_frames`` model-frames.

Admissible pairs are ranked by (I(m1) + I(m2), min(I(m1), I(m2)), median
separation); ties go to the smaller m1, then the smaller m2. No admissible
pair is ``FAILED``: no pair is selected and the run cannot be FEASIBLE.

**A (D08, revised 2026-10-19 after audit F3; proposed).** A model-frame is
*A-informative* for N when its A cell is complete and p_A lies inside
``a_headroom_band``. N is admissible only when it is informative in at
least ``a_min_informative_model_frames`` model-frames spanning at least
``a_min_informative_models`` models (with the defaults, 6 of 8 and 3 of 4:
what the 12-of-16, 3-model feasibility target needs, since a configuration
whose A is not informative never counts toward it). Among admissible N,
maximise (configurations with G1 support *and* an informative A,
informative model-frames), then prefer ``preferred_a_count``, then the
smaller N. No admissible N is ``FAILED`` (``A_HEADROOM_INADEQUATE``): no A is
selected; there is no fallback to per-model A counts and no floor- or
ceiling-level A can be selected. A selected N whose best G1 count is below
the feasibility target is flagged ``A_COVERAGE_INADEQUATE``.
"""
from __future__ import annotations

import math
import statistics
from fractions import Fraction
from typing import Any, Mapping

from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1.intervals import boundary_distance, newcombe, wilson
from dci.batch1.scoring import PilotTables

__all__ = ["STAGE2_CLASSES", "select_stage2", "select_b", "select_a",
           "finalize"]

STAGE2_CLASSES = ("A_HEADROOM", "B_BAND", "ELIGIBILITY_20", "MATCHING",
                  "ELIGIBILITY_10")


def _se(boundary: float, n: int) -> float:
    return math.sqrt(boundary * (1 - boundary) / n)


def select_stage2(tables: PilotTables, cfg: CFG.PilotConfig
                  ) -> dict[str, Any]:
    if cfg.protocol == "v2":
        from dci.batch1 import revision as REV
        return REV.select_carry(tables, cfg)
    candidates: dict[tuple[str, str, str], tuple[int, float, str]] = {}

    def offer(model, frame, cid, cls, dist):
        key = (model, frame, cid)
        entry = (STAGE2_CLASSES.index(cls), round(dist, 12), cls)
        if key not in candidates or entry < candidates[key]:
            candidates[key] = entry

    mfs = R.model_frames(cfg)
    a_ids = [c.cid for c in L.a_candidates() if c.p["n"] in cfg.a_counts]
    b_ids = [c.cid for c in L.b_candidates() if c.p["m"] in cfg.b_limits]
    refs = L.reference_library()

    def straddle(count, edges, cls, model, frame, cid):
        if not count.n:
            return
        lo, hi = wilson(count.k, count.n, cfg.z)
        for edge in edges:
            if lo <= edge <= hi:
                offer(model, frame, cid, cls,
                      boundary_distance(count.p, edge, _se(edge, count.n)))

    for model, frame in mfs:
        for cid in a_ids:
            straddle(tables.x(model, frame, cid), cfg.a_headroom_band,
                     "A_HEADROOM", model, frame, cid)
        for cid in b_ids:
            straddle(tables.x(model, frame, cid), cfg.b_informative_band,
                     "B_BAND", model, frame, cid)

    plausible = set()
    for c in refs:
        for model, frame in mfs:
            x = tables.x(model, frame, c.cid)
            if x.n and wilson(x.k, x.n, cfg.z)[1] >= cfg.extension_threshold:
                plausible.add(c.cid)
    tol = cfg.matching_tolerance
    for model, frame in mfs:
        for a_cid in a_ids:
            a = tables.x(model, frame, a_cid)
            if not a.n:
                continue
            for c in refs:
                if c.cid not in plausible:
                    continue
                x = tables.x(model, frame, c.cid)
                if not x.n:
                    continue
                lo, hi = newcombe(x.k, x.n, a.k, a.n, cfg.z)
                d = x.p - a.p
                se = math.sqrt(0.25 / x.n + 0.25 / a.n)
                for edge in (-tol, tol):
                    if lo <= edge <= hi:
                        dist = boundary_distance(d, edge, se)
                        offer(model, frame, c.cid, "MATCHING", dist)
                        offer(model, frame, a_cid, "MATCHING", dist)

    for c in refs:
        cells = [(m, f, tables.x(m, f, c.cid)) for m, f in mfs]
        for threshold, cls in ((cfg.eligibility_threshold, "ELIGIBILITY_20"),
                               (cfg.extension_threshold, "ELIGIBILITY_10")):
            if any(x.n and wilson(x.k, x.n, cfg.z)[0] >= threshold
                   for _, _, x in cells):
                continue
            for model, frame, x in cells:
                straddle(x, (threshold,), cls, model, frame, c.cid)

    ranked = sorted(candidates.items(),
                    key=lambda kv: (kv[1][0], kv[1][1], kv[0]))
    chosen = ranked[:cfg.stage2_max_cells]
    by_class: dict[str, int] = {}
    for _, (_, _, cls) in chosen:
        by_class[cls] = by_class.get(cls, 0) + 1
    return {
        "schema": "dci.batch1/stage2-selection/v1",
        "rule": "D06 (proposed)", "max_cells": cfg.stage2_max_cells,
        "n_candidates": len(candidates), "n_selected": len(chosen),
        "truncated_by_cap": len(candidates) > len(chosen),
        "by_class": by_class,
        "cells": [{"model": k[0], "frame": k[1], "condition": k[2],
                   "class": v[2], "distance": v[1]} for k, v in chosen],
        "not_selected": [{"model": k[0], "frame": k[1], "condition": k[2],
                          "class": v[2], "distance": v[1]}
                         for k, v in ranked[cfg.stage2_max_cells:]],
    }


def _f(x: float) -> Fraction:
    return Fraction(str(x))


def _in_band(count, band) -> bool:
    lo, hi = band
    return _f(lo) <= Fraction(count.k, count.n) <= _f(hi)


def select_b(tables: PilotTables, cfg: CFG.PilotConfig) -> dict[str, Any]:
    per_limit: dict[int, dict[str, Any]] = {}
    exact: dict[int, dict[tuple[str, str], Fraction]] = {}
    for c in L.b_candidates():
        m = c.p["m"]
        if m not in cfg.b_limits:
            continue
        cells, ps, ok = {}, {}, True
        for model, frame in R.model_frames(cfg):
            count = tables.x(model, frame, c.cid)
            if not R.usable(count, cfg):
                ok = False
                cells[f"{model}|{frame}"] = None
                continue
            ps[(model, frame)] = Fraction(count.k, count.n)
            cells[f"{model}|{frame}"] = {
                "p": count.p, "n": count.n,
                "ci": list(wilson(count.k, count.n, cfg.z)),
                "informative": _in_band(count, cfg.b_informative_band),
                "extreme": count.p < 0.05 or count.p > 0.95}
        exact[m] = ps
        per_limit[m] = {
            "complete": ok, "cells": cells,
            "informative": sum(1 for v in cells.values()
                               if v and v["informative"]),
            "median": float(statistics.median(ps.values())) if ps else None}
    need = _f(cfg.b_min_median_separation)
    evaluated, pairs = [], []
    limits = sorted(per_limit)
    for i, m1 in enumerate(limits):
        for m2 in limits[i + 1:]:
            a, b = per_limit[m1], per_limit[m2]
            reasons = []
            if m2 - m1 < cfg.b_min_gap:
                reasons.append(f"GAP_{m2 - m1}_BELOW_{cfg.b_min_gap}")
            if not (a["complete"] and b["complete"]):
                reasons.append("INCOMPLETE_CELLS")
                evaluated.append({"pair": [m1, m2], "admissible": False,
                                  "reasons": reasons})
                continue
            sep = statistics.median(exact[m2].values()) - \
                statistics.median(exact[m1].values())
            if sep < need:
                reasons.append(f"MEDIAN_SEPARATION_{float(sep):.3f}_BELOW_"
                               f"{cfg.b_min_median_separation}")
            by_model = {}
            for model in cfg.models:
                diffs = [exact[m2][(model, f)] - exact[m1][(model, f)]
                         for f in cfg.frames]
                by_model[model] = sum(diffs) / len(diffs)
            separated = sorted(mo for mo, d in by_model.items() if d >= need)
            if len(separated) < cfg.b_min_separated_models:
                reasons.append(f"SEPARATED_IN_{len(separated)}_MODELS_BELOW_"
                               f"{cfg.b_min_separated_models}")
            for m, info in ((m1, a), (m2, b)):
                if info["informative"] < cfg.b_min_informative_model_frames:
                    reasons.append(f"B{m}_INFORMATIVE_IN_{info['informative']}"
                                   f"_BELOW_{cfg.b_min_informative_model_frames}")
            score = (a["informative"] + b["informative"],
                     min(a["informative"], b["informative"]), float(sep))
            evaluated.append({"pair": [m1, m2], "admissible": not reasons,
                              "reasons": reasons, "score": list(score),
                              "median_separation": float(sep),
                              "separation_by_model": {
                                  mo: float(d) for mo, d in by_model.items()},
                              "separated_models": separated})
            if not reasons:
                pairs.append((score, (-m1, -m2), (m1, m2)))
    if not pairs:
        return {"status": "FAILED", "selected": None, "per_limit": per_limit,
                "evaluated": evaluated,
                "rule": "D07 (revised, proposed)",
                "reason": "no pair of B limits meets D07 (gap, separation, "
                          "cross-model consistency, headroom, completeness)"}
    pairs.sort(reverse=True)
    best = pairs[0][2]
    limitations = [f"B{m} {mf}: p={v['p']:.3f} (extreme)"
                   for m in best for mf, v in per_limit[m]["cells"].items()
                   if v and v["extreme"]]
    return {"status": "SELECTED", "selected": list(best),
            "demanding": best[0], "permissive": best[1],
            "score": list(pairs[0][0]), "per_limit": per_limit,
            "measurement_limitations": limitations, "evaluated": evaluated,
            "rule": "D07 (revised, proposed)",
            "ranking": [{"pair": list(p[2]), "score": list(p[0])}
                        for p in pairs]}


def select_a(tables: PilotTables, cfg: CFG.PilotConfig,
             compat: Mapping[str, Any], elig: Mapping[str, Any],
             b_selected: list[int]) -> dict[str, Any]:
    rows = []
    for a in L.a_candidates():
        n = a.p["n"]
        if n not in cfg.a_counts:
            continue
        informative, cells = [], {}
        for model, frame in R.model_frames(cfg):
            count = tables.x(model, frame, a.cid)
            ok = R.usable(count, cfg) and _in_band(count, cfg.a_headroom_band)
            cells[f"{model}|{frame}"] = {"p": count.p, "n": count.n,
                                         "informative": ok}
            if ok:
                informative.append((model, frame))
        models = sorted({m for m, _ in informative})
        admissible = (len(informative) >= cfg.a_min_informative_model_frames
                      and len(models) >= cfg.a_min_informative_models)
        g1_configs, g1_any, incomplete = [], [], []
        for model, frame in R.model_frames(cfg):
            for m in b_selected:
                rep = R.configuration_report(tables, cfg, compat, elig, a,
                                             model, frame, m)
                key = f"{model}|{frame}|B{m}"
                if "A_CELL_INCOMPLETE" in rep["context"]:
                    incomplete.append(key)
                if rep["coverage"]["G1"]["supported"]:
                    g1_any.append(key)
                    if rep["a_informative"]:
                        g1_configs.append(key)
        reasons = []
        if len(informative) < cfg.a_min_informative_model_frames:
            reasons.append(f"INFORMATIVE_IN_{len(informative)}_MODEL_FRAMES_"
                           f"BELOW_{cfg.a_min_informative_model_frames}")
        if len(models) < cfg.a_min_informative_models:
            reasons.append(f"INFORMATIVE_IN_{len(models)}_MODELS_BELOW_"
                           f"{cfg.a_min_informative_models}")
        rows.append({"a": a.cid, "n": n, "admissible": admissible,
                     "reasons": reasons, "cells": cells,
                     "headroom": len(informative),
                     "headroom_cells": [f"{m}|{f}" for m, f in informative],
                     "informative_models": models,
                     "g1_supported": len(g1_configs), "g1_configs": g1_configs,
                     "g1_supported_including_uninformative_a": len(g1_any),
                     "incomplete": incomplete,
                     "key": (admissible, len(g1_configs), len(informative),
                             n == cfg.preferred_a_count, -n)})
    rows.sort(key=lambda r: r["key"], reverse=True)
    for r in rows:
        r["key"] = list(r["key"])
    rule = ("D08 (revised, proposed): admissible by headroom; then G1 support "
            "with an informative A, headroom, N=preferred, smaller N")
    best = rows[0]
    if not best["admissible"]:
        return {"status": "FAILED", "selected": None, "n": None,
                "ranking": rows, "rule": rule,
                "flags": ["A_HEADROOM_INADEQUATE: no global A count is "
                          f"informative in {cfg.a_min_informative_model_frames}"
                          f" model-frames across {cfg.a_min_informative_models}"
                          " models"]}
    flags = []
    if best["g1_supported"] < cfg.feasibility_min_configs:
        flags.append("A_COVERAGE_INADEQUATE: no admissible global A count "
                     f"gives G1 support in {cfg.feasibility_min_configs} "
                     f"configurations (best: N={best['n']}, "
                     f"{best['g1_supported']})")
    if best["incomplete"]:
        flags.append(f"A cells incomplete: {best['incomplete']}")
    return {"status": "SELECTED", "selected": best["a"], "n": best["n"],
            "ranking": rows, "flags": flags, "rule": rule}


def finalize(tables: PilotTables, cfg: CFG.PilotConfig,
             compat: Mapping[str, Any], *, early_stop: bool = False
             ) -> dict[str, Any]:
    """Everything Freeze 2 needs, from stand-alone tables only. Protocol v2
    reads T2 tables only and fixes A and B (``revision.finalize_fixed``)."""
    if cfg.protocol == "v2":
        from dci.batch1 import revision as REV
        return REV.finalize_fixed(tables, cfg, compat, early_stop=early_stop)
    b = select_b(tables, cfg)
    elig = R.eligibility(tables, cfg)
    review = _f(cfg.truncation_review_share)
    truncation = sorted(key for key, c in tables.explicit.items()
                        if c.n and Fraction(c.truncated, c.n) > review)
    out: dict[str, Any] = {"schema": "dci.batch1/calibration/v2",
                           "synthetic": tables.synthetic, "b": b,
                           "eligibility": elig,
                           "truncation_review": truncation}
    if b["status"] != "SELECTED":
        out.update(status="B_SELECTION_FAILED", a=None, configurations=[],
                   feasibility=None)
        return out
    a = select_a(tables, cfg, compat, elig, b["selected"])
    if a["status"] != "SELECTED":
        out.update(status="A_SELECTION_FAILED", a=a, configurations=[],
                   feasibility=None)
        return out
    focal = L.constraint_by_id()[a["selected"]]
    reports = [R.configuration_report(tables, cfg, compat, elig, focal,
                                      model, frame, m)
               for model, frame in R.model_frames(cfg) for m in b["selected"]]
    feas = R.feasibility(reports, cfg, b["selected"])
    status = "FEASIBLE" if feas["all_feasible"] and not a["flags"] \
        else "INFEASIBLE_REVISION_REQUIRED"
    out.update(status=status, a=a, configurations=reports, feasibility=feas,
               eligible_20=sorted(R.eligible_ids(elig)),
               extension_10_only=sorted(
                   cid for cid, e in elig.items()
                   if e["status"] == R.EXTENSION_ONLY))
    return out
