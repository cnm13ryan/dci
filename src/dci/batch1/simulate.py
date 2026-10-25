"""Calibration-precision simulation (audit F6). Offline, CPU-only, never
pilot evidence; not part of Freeze 1.

Each replicate is a simulated pilot passed through the **real** Batch 1
rules: Stage 1 counts -> ``calibration.select_stage2`` -> Stage 2 counts ->
``calibration.finalize``. What is simulated is only the data:

* a **compliance surface** gives each (model, frame, condition) a typical
  compliance probability (``SURFACES``; invented, not measured);
* **topic heterogeneity**: response j on topic t has probability
  ``expit(logit(p) + u_mt + e_ct)``, with ``u_mt ~ N(0, TOPIC_SD)`` shared by
  every condition of model m on topic t and ``e_ct ~ N(0, CELL_TOPIC_SD)``
  specific to the cell, so responses that share a topic are dependent, as
  in the pilot (every cell of a stage shares its topics);
* the **truth** of a cell is its population mean over topics (Gauss-Hermite),
  and the noise-free reference result is ``finalize`` on those means.

**Allocations** (``ALLOCATIONS``) change only sample sizes: the Stage 1
topics of A and B cells, and the Stage 2 cap. Every other rule --- ±0.10,
the 20% OR rule, G1-G6, P1-P3, D06-D08 --- is held at its proposed value.

Metrics, against the noise-free result: selected A and B, the verdict
(false FEASIBLE / false INFEASIBLE), and with the true A and B held fixed,
G1/G3/G5 Jaccard overlap and false inclusions/exclusions, matching errors
for references near the tolerance edge (true |p_X - p_A| within 0.05 of
0.10) and far from it, and the number of configurations supporting P1-P3.
Run: ``python -m dci.batch1.simulate --reps 40 --out <file>``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Any, Callable

import numpy as np

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1 import synthetic as SY
from dci.batch1.scoring import Count, PilotTables, _key

__all__ = ["SURFACES", "CHALLENGE_SURFACES", "ALL_SURFACES", "ALLOCATIONS",
           "Allocation", "one_pilot", "run", "surface_fn", "truth_tables"]

TOPIC_SD = 0.5          # shared by every condition of a model on a topic
CELL_TOPIC_SD = 0.3     # specific to a cell on a topic
STAGE1_TOPICS, STAGE2_TOPICS = 32, 64

CFG0 = CFG.DEFAULT_CONFIG
BY_ID = L.constraint_by_id()
CIDS = ([c.cid for c in L.a_candidates()] + [c.cid for c in L.b_candidates()]
        + [c.cid for c in L.reference_library()])
FOCAL = {c.cid for c in L.a_candidates() + L.b_candidates()}
WORD_OP = BY_ID["ew.indeed.2"].operation


def _h(*parts: Any) -> float:
    """A deterministic number in [-0.5, 0.5) from the parts."""
    d = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(d[:6], "big") / 2 ** 48 - 0.5


def _clip(p: float) -> float:
    return min(0.98, max(0.01, p))


def _moderate(m, f, cid):
    return SY.default_truth(m, f, cid)


def _model_differences(m, f, cid):
    shift = {"gemma-3n-e2b-it": -0.16, "gemma-3n-e4b-it": 0.04,
             "qwen3-4b": 0.12, "qwen3-4b-instruct-2507": 0.20}[m]
    return _clip(SY.default_truth(m, f, cid) + shift)


def _frame_differences(m, f, cid):
    p = SY.default_truth(m, f, cid)
    if f == "F1" and BY_ID[cid].role != "B":
        p += -0.10 + 0.16 * _h("frame", cid)
    return _clip(p)


def _boundary_cluster(m, f, cid):
    c = BY_ID[cid]
    if c.role == "reference" and c.operation == WORD_OP:
        p_a = SY.default_truth(m, f, "A.however.4")
        side = 1 if _h("side", cid) >= 0 else -1
        return _clip(p_a + side * (0.10 + 0.06 * _h("gap", cid)))
    return SY.default_truth(m, f, cid)


def _low_followability(m, f, cid):
    p = SY.default_truth(m, f, cid)
    return _clip(p - 0.15) if BY_ID[cid].role == "reference" else p


def _other_operation_harder(m, f, cid):
    c = BY_ID[cid]
    p = SY.default_truth(m, f, cid)
    if c.role == "reference" and c.operation != WORD_OP:
        return _clip(p - 0.20)
    return p


SURFACES: dict[str, Callable[[str, str, str], float]] = {
    "moderate": _moderate,
    "model_differences": _model_differences,
    "frame_differences": _frame_differences,
    "boundary_cluster": _boundary_cluster,
    "low_followability": _low_followability,
    "other_operation_harder": _other_operation_harder,
}


# --------------------------------------------- challenge surfaces (D11 study)
# These place references by their *population-mean* distance from A (the
# truth the pilot estimates), so "truly matched" means exactly what D10 says
# it means. A_REF is the A the six surfaces above select in truth.
A_REF = "A.however.4"
_OTHER_OP = sorted((c.cid for c in L.reference_library()
                    if c.operation != WORD_OP), key=lambda c: _h("grade", c))


@lru_cache(maxsize=None)
def inverse_population_mean(target: float) -> float:
    """The typical p whose population mean over topics is ``target``."""
    lo, hi = 1e-4, 1 - 1e-4
    for _ in range(60):
        mid = (lo + hi) / 2
        if population_mean(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _at(m: str, f: str, distance: float) -> float:
    """The typical p of a reference ``distance`` above A's true rate."""
    p_a = population_mean(SY.default_truth(m, f, A_REF))
    return inverse_population_mean(min(0.97, max(0.02, p_a + distance)))


def _strong_model_sensitivity(m, f, cid):
    """Large model shifts plus a model x operation interaction of up to
    +/-0.15, so which operations are matchable differs by model."""
    shift = {"gemma-3n-e2b-it": -0.20, "gemma-3n-e4b-it": 0.0,
             "qwen3-4b": 0.10, "qwen3-4b-instruct-2507": 0.22}[m]
    c = BY_ID[cid]
    p = SY.default_truth(m, f, cid) + shift
    if c.role == "reference":
        p += 0.30 * _h("mxo", m, c.operation)
    return _clip(p)


def _strong_paraphrase_sensitivity(m, f, cid):
    """Under F1 every non-B condition, A included, moves by up to +/-0.25."""
    p = SY.default_truth(m, f, cid)
    if f == "F1" and BY_ID[cid].role != "B":
        p += 0.50 * _h("para", m, cid)
    return _clip(p)


def _edge_crowded(m, f, cid):
    """Every reference outside A's operation-object group sits 0.06-0.14
    from A in truth: about half inside the tolerance, all near its edge."""
    c = BY_ID[cid]
    if c.role != "reference" or (c.operation == WORD_OP
                                 and c.object_type == "word"):
        return SY.default_truth(m, f, cid)
    side = 1 if _h("edge-side", m, f, cid) >= 0 else -1
    return _at(m, f, side * (0.10 + 0.08 * _h("edge-gap", m, f, cid)))


#: Truly matched other-operation references per model-frame.
_GRADED = {("gemma-3n-e2b-it", "F0"): 1, ("gemma-3n-e2b-it", "F1"): 2,
           ("gemma-3n-e4b-it", "F0"): 2, ("gemma-3n-e4b-it", "F1"): 3,
           ("qwen3-4b", "F0"): 3, ("qwen3-4b", "F1"): 4,
           ("qwen3-4b-instruct-2507", "F0"): 4,
           ("qwen3-4b-instruct-2507", "F1"): 5}


def _graded(m, f, cid, j):
    c = BY_ID[cid]
    if c.role != "reference" or c.operation == WORD_OP:
        return SY.default_truth(m, f, cid)
    if _OTHER_OP.index(cid) < j:                      # truly matched
        return _at(m, f, 0.12 * _h("graded-in", m, f, cid))
    return _at(m, f, -(0.14 + 0.16 * (_h("graded-out", m, f, cid) + 0.5)))


def _graded_coverage(m, f, cid):
    """1-5 truly matched other-operation references, by model-frame; the
    rest 0.14-0.30 below A. True P3 support: 14/16 at a minimum of 2,
    10/16 at 3, 6/16 at 4, 2/16 at 5."""
    return _graded(m, f, cid, _GRADED[(m, f)])


def _graded_coverage_sparse(m, f, cid):
    """As graded_coverage with one fewer matched reference everywhere:
    true P3 support 10/16 at a minimum of 2, so INFEASIBLE in truth."""
    return _graded(m, f, cid, _GRADED[(m, f)] - 1)


_SINGLE_OP = "ordering"


def _single_operation_coverage(m, f, cid):
    """Only the four ordering references match A; every other operation is
    0.14-0.30 below it. Count rules see 4 additions; a rule asking for two
    operations sees one."""
    c = BY_ID[cid]
    if c.role != "reference" or c.operation == WORD_OP:
        return SY.default_truth(m, f, cid)
    if c.operation == _SINGLE_OP:
        return _at(m, f, 0.12 * _h("single-in", m, f, cid))
    return _at(m, f, -(0.14 + 0.16 * (_h("single-out", m, f, cid) + 0.5)))


CHALLENGE_SURFACES: dict[str, Callable[[str, str, str], float]] = {
    "strong_model_sensitivity": _strong_model_sensitivity,
    "strong_paraphrase_sensitivity": _strong_paraphrase_sensitivity,
    "edge_crowded": _edge_crowded,
    "graded_coverage": _graded_coverage,
    "graded_coverage_sparse": _graded_coverage_sparse,
    "single_operation_coverage": _single_operation_coverage,
}
ALL_SURFACES = {**SURFACES, **CHALLENGE_SURFACES}


@dataclass(frozen=True)
class Allocation:
    name: str
    focal_stage1_topics: int      # A and B cells in Stage 1 (32 or 96)
    stage2_cap: int
    uniform: int = 0              # every cell this many topics, no Stage 2
    stage2_draws: int = 1         # draws per Stage 2 topic (same topics)

    def max_rows(self, cfg: CFG.PilotConfig = CFG0) -> int:
        per_mf = len(cfg.frames) * len(cfg.models)
        task_only = len(cfg.models) * STAGE1_TOPICS * cfg.task_only_draws
        if self.uniform:
            return per_mf * len(CIDS) * self.uniform + task_only
        focal = per_mf * len(FOCAL) * self.focal_stage1_topics
        refs = per_mf * (len(CIDS) - len(FOCAL)) * STAGE1_TOPICS
        return (focal + refs + task_only
                + self.stage2_cap * STAGE2_TOPICS * self.stage2_draws)


ALLOCATIONS = (
    Allocation("current_32_plus_240x64", 32, 240),
    Allocation("focal96_plus_240x64", 96, 240),
    Allocation("current_32_plus_360x64", 32, 360),
    Allocation("focal96_plus_360x64", 96, 360),
    Allocation("current_32_plus_480x64", 32, 480),
    Allocation("current_32_plus_240x64x2draws", 32, 240, stage2_draws=2),
    Allocation("uniform_96_no_stage2", 96, 0, uniform=96),
)

_GH = np.polynomial.hermite.hermgauss(24)


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def population_mean(p: float) -> float:
    sd = math.hypot(TOPIC_SD, CELL_TOPIC_SD)
    x, w = _GH
    z = _logit(p) + sd * math.sqrt(2) * x
    return float(np.sum(w / (1 + np.exp(-z))) / math.sqrt(math.pi))


@lru_cache(maxsize=None)
def _matrix() -> dict[str, Any]:
    return COMPAT.compatibility_matrix()


@lru_cache(maxsize=None)
def surface_fn(surface: str) -> Callable[[str, str, str], float]:
    """The surface's typical-p function, memoised (the challenge surfaces
    invert the topic mixture for every cell)."""
    return lru_cache(maxsize=None)(ALL_SURFACES[surface])


def truth_tables(surface: str, cfg: CFG.PilotConfig = CFG0) -> PilotTables:
    truth = surface_fn(surface)
    t = PilotTables(synthetic=True)
    n = 10 ** 6
    for m in cfg.models:
        for f in cfg.frames:
            for cid in CIDS:
                k = round(population_mean(truth(m, f, cid)) * n)
                t.explicit[_key(m, f, cid)] = Count(k=k, n=n, planned=n)
    return t


#: Per-topic outcomes of the current pilot, when ``one_pilot`` keeps them:
#: (model, frame, cid) -> [(topic index, compliant)].
_KEEP: dict[tuple, list] | None = None


def _sample(rng: np.random.Generator, logits: np.ndarray, u: np.ndarray,
            topics: slice, keys: list[tuple] | None = None) -> np.ndarray:
    """Compliant counts for cells (rows of ``logits``) over ``topics``."""
    ut = u[topics]
    e = rng.normal(0.0, CELL_TOPIC_SD, size=(len(logits), len(ut)))
    p = 1 / (1 + np.exp(-(logits[:, None] + ut[None, :] + e)))
    hits = rng.random(p.shape) < p
    if _KEEP is not None and keys is not None:
        idx = range(topics.start, topics.stop)
        for k, row in zip(keys, hits):
            if k is not None:
                _KEEP.setdefault(k, []).extend(zip(idx, row.tolist()))
    return hits.sum(axis=1)


def _stage2(sel: dict[str, Any], alloc: Allocation) -> list[tuple]:
    ranked = sel["cells"] + sel["not_selected"]
    if alloc.focal_stage1_topics >= STAGE1_TOPICS + STAGE2_TOPICS:
        ranked = [c for c in ranked if c["condition"] not in FOCAL]
    return [(c["model"], c["frame"], c["condition"])
            for c in ranked[:alloc.stage2_cap]]


def one_pilot(surface: str, alloc: Allocation, seed: int,
              cfg: CFG.PilotConfig = CFG0) -> dict[str, Any]:
    truth = surface_fn(surface)
    rng = np.random.default_rng(seed)
    big = replace_cap(cfg, 10 ** 6)
    k1: dict[tuple, list[int]] = {}
    logits: dict[str, np.ndarray] = {}
    u: dict[str, np.ndarray] = {}
    keys: dict[str, list[tuple]] = {}
    for m in cfg.models:
        u[m] = rng.normal(0.0, TOPIC_SD, size=STAGE1_TOPICS + STAGE2_TOPICS)
        keys[m] = [(m, f, cid) for f in cfg.frames for cid in CIDS]
        logits[m] = np.array([_logit(truth(*k)) for k in keys[m]])
        if alloc.uniform:
            counts = _sample(rng, logits[m], u[m], slice(0, alloc.uniform),
                             keys[m])
            for k, c in zip(keys[m], counts):
                k1[k] = [int(c), alloc.uniform]
            continue
        s1 = _sample(rng, logits[m], u[m], slice(0, STAGE1_TOPICS), keys[m])
        focal_keys = [k if k[2] in FOCAL and
                      alloc.focal_stage1_topics > STAGE1_TOPICS else None
                      for k in keys[m]]
        extra = _sample(rng, logits[m], u[m],
                        slice(STAGE1_TOPICS, STAGE1_TOPICS + STAGE2_TOPICS),
                        focal_keys)
        for k, c, x in zip(keys[m], s1, extra):
            k1[k] = [int(c), STAGE1_TOPICS]
            if k[2] in FOCAL and alloc.focal_stage1_topics > STAGE1_TOPICS:
                k1[k][0] += int(x)
                k1[k][1] += STAGE2_TOPICS
    tables = _tables(k1)
    refined = 0
    if not alloc.uniform:
        sel = CAL.select_stage2(tables, big)
        chosen = _stage2(sel, alloc)
        refined = len(chosen)
        index = {m: {k: i for i, k in enumerate(keys[m])} for m in cfg.models}
        for m in cfg.models:
            mine = [k for k in chosen if k[0] == m]
            if not mine:
                continue
            lg = np.array([logits[m][index[m][k]] for k in mine])
            for _ in range(alloc.stage2_draws):
                add = _sample(rng, lg, u[m],
                              slice(STAGE1_TOPICS, STAGE1_TOPICS + STAGE2_TOPICS),
                              mine)
                for k, c in zip(mine, add):
                    k1[k][0] += int(c)
                    k1[k][1] += STAGE2_TOPICS
        tables = _tables(k1)
    result = CAL.finalize(tables, cfg, _matrix())
    return {"tables": tables, "result": result, "refined": refined}


def replace_cap(cfg: CFG.PilotConfig, cap: int) -> CFG.PilotConfig:
    state = cfg.state()
    state["stage2_max_cells"] = cap
    return CFG.PilotConfig(**{k: tuple(v) if isinstance(v, list) else v
                              for k, v in state.items()})


def _tables(counts: dict[tuple, list[int]]) -> PilotTables:
    t = PilotTables(synthetic=True)
    for (m, f, cid), (k, n) in counts.items():
        t.explicit[_key(m, f, cid)] = Count(k=k, n=n, planned=n)
    return t


def _d14_task(args: tuple) -> list[dict[str, Any]]:
    """Point verdict and the D14 stable-member verdict for simulated pilots."""
    global _KEEP
    from dci.batch1 import stability as STAB
    surface, alloc, seeds, boot, full = args
    out = []
    for seed in seeds:
        _KEEP = {}
        try:
            sim = one_pilot(surface, alloc, seed)
            kept = _KEEP
        finally:
            _KEEP = None
        rows = []
        for (m, f, cid), outcomes in kept.items():
            for t, ok in outcomes:
                if ok is None:
                    continue
                stage = "stage1" if t < STAGE1_TOPICS else "stage2"
                rows.append({"stage": stage, "topic_id": f"t{t}", "model": m,
                             "frame": f, "condition": cid,
                             "scores": {cid: [True, "PASS" if ok else "FAIL",
                                              bool(ok), True, 0, ""]}})
        point = sim["result"]
        rec = {"seed": seed, "status": point["status"]}
        if point.get("configurations"):
            diag = STAB.diagnostics(rows, point, CFG0, _matrix(),
                                    synthetic=True, replicates=boot,
                                    full_selection=full)
            stable = diag["stable_member_feasibility"]
            rec["stable_feasible"] = stable["all_feasible"]
            rec["stable_by_threshold"] = {
                str(th): STAB.stable_member_feasibility(
                    point, diag["membership"], CFG0, th)["all_feasible"]
                for th in STABLE_THRESHOLDS}
            rec["bootstrap_feasible_share"] = diag["selection"]["feasible_share"]
            rec["stable_supported"] = {p: stable[p]["supported_configurations"]
                                       for p in ("P1", "P2", "P3")}
            rec["unstable_memberships"] = sum(
                len(v) for g in diag["unstable"].values() for v in g.values())
        out.append(rec)
    return out


STABLE_THRESHOLDS = (0.5, 0.6, 0.7, 0.8)


def d14_validation(n_pilots: int, boot: int, *, surfaces, workers: int = 8,
                   seed: int = 20261020, full: bool = True) -> dict[str, Any]:
    alloc = ALLOCATIONS[0]
    tasks = []
    for s in surfaces:
        seeds = [int.from_bytes(hashlib.sha256(
            f"{seed}|d14|{s}|{i}".encode()).digest()[:4], "big")
            for i in range(n_pilots)]
        tasks += [(s, alloc, seeds[i::workers], boot, full)
                  for i in range(workers) if seeds[i::workers]]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_d14_task, tasks))
    grouped: dict[str, list] = {}
    for (s, *_), recs in zip(tasks, results):
        grouped.setdefault(s, []).extend(recs)
    out = {}
    for s, recs in grouped.items():
        truth = CAL.finalize(truth_tables(s), CFG0, _matrix())["status"]
        n = len(recs)
        point_f = sum(r["status"] == "FEASIBLE" for r in recs)
        stable_f = sum(r["status"] == "FEASIBLE" and r.get("stable_feasible")
                       for r in recs)
        def both(pred):
            return round(sum(r["status"] == "FEASIBLE" and pred(r)
                             for r in recs) / n, 4)
        shares = [r["bootstrap_feasible_share"] for r in recs
                  if r.get("bootstrap_feasible_share") is not None]
        out[s] = {"pilots": n, "bootstrap_replicates": boot,
                  "allocation": alloc.name, "true_status": truth,
                  "point_feasible_share": round(point_f / n, 4),
                  "feasible_and_stable_share": round(stable_f / n, 4),
                  "feasible_and_stable_by_threshold": {
                      str(th): both(lambda r, th=th: r.get(
                          "stable_by_threshold", {}).get(str(th)))
                      for th in STABLE_THRESHOLDS},
                  "feasible_and_bootstrap_share_at_least": {
                      str(c): both(lambda r, c=c: (r.get(
                          "bootstrap_feasible_share") or 0) >= c)
                      for c in (0.5, 0.65, 0.8)},
                  "mean_bootstrap_feasible_share": _mean(shares),
                  "mean_unstable_memberships": _mean(
                      [r.get("unstable_memberships", 0) for r in recs])}
    return out


#: B surfaces for the D07 threshold sensitivity: p_B(m) before model shifts.
B_SURFACES: dict[str, Callable[[int], float]] = {
    "default": lambda m: 0.08 + 0.15 * (m - 8),
    "steep": lambda m: 0.05 + 0.18 * (m - 8),
    "shallow": lambda m: 0.30 + 0.04 * (m - 8),
    "plateau": lambda m: {8: .16, 9: .165, 10: .17, 11: .88, 12: .93,
                          13: .96}[m],
}


def d07_sensitivity(n_pilots: int, *, thresholds=(0.10, 0.15, 0.20),
                    n_b: int = 96, seed: int = 20261021) -> dict[str, Any]:
    """How often D07 selects a pair, and how far apart the selected limits
    truly are, at each separation threshold, under pilot-scale noise."""
    shift = {"gemma-3n-e2b-it": -0.08, "gemma-3n-e4b-it": 0.02,
             "qwen3-4b": 0.06, "qwen3-4b-instruct-2507": 0.10}
    out: dict[str, Any] = {}
    for name, base in B_SURFACES.items():
        truth = {(mo, f, m): _clip(base(m) + shift[mo])
                 for mo in CFG0.models for f in CFG0.frames
                 for m in CFG0.b_limits}
        true_median = {m: statistics.median(population_mean(truth[(mo, f, m)])
                                            for mo in CFG0.models
                                            for f in CFG0.frames)
                       for m in CFG0.b_limits}
        rng = np.random.default_rng(seed)
        res = {t: {"selected": 0, "pairs": {}, "true_separation": []}
               for t in thresholds}
        for _ in range(n_pilots):
            t = PilotTables(synthetic=True)
            for mo in CFG0.models:
                u = rng.normal(0.0, TOPIC_SD, size=n_b)
                for f in CFG0.frames:
                    for m in CFG0.b_limits:
                        lg = np.array([_logit(truth[(mo, f, m)])])
                        k = int(_sample(rng, lg, u, slice(0, n_b))[0])
                        t.explicit[_key(mo, f, f"B.max{m}")] = Count(
                            k=k, n=n_b, planned=n_b)
            for th in thresholds:
                cfg = CFG.PilotConfig(b_min_median_separation=th)
                b = CAL.select_b(t, cfg)
                r = res[th]
                pair = b["selected"]
                key = "-".join(map(str, pair)) if pair else "none"
                r["pairs"][key] = r["pairs"].get(key, 0) + 1
                if pair:
                    r["selected"] += 1
                    r["true_separation"].append(true_median[pair[1]]
                                                - true_median[pair[0]])
        out[name] = {"true_median": {m: round(v, 3)
                                     for m, v in true_median.items()},
                     "n_per_cell": n_b, "pilots": n_pilots, "thresholds": {
            str(th): {"selected_share": round(r["selected"] / n_pilots, 4),
                      "pairs": dict(sorted(r["pairs"].items())),
                      "mean_true_separation": _mean(r["true_separation"]),
                      "min_true_separation": (round(min(r["true_separation"]), 3)
                                              if r["true_separation"] else None)}
            for th, r in res.items()}}
    return out


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 1.0


def _membership(tables: PilotTables, truth: PilotTables,
                true_result: dict[str, Any], cfg: CFG.PilotConfig
                ) -> dict[str, Any]:
    """With the true A and B held fixed: memberships and matching errors."""
    a = BY_ID[true_result["a"]["selected"]]
    b_sel = true_result["b"]["selected"]
    elig = R.eligibility(tables, cfg)
    t_elig = R.eligibility(truth, cfg)
    out = {"jaccard": {"G1": [], "G3": [], "G5": []}, "g1_false_in": [],
           "g1_false_out": [], "near_errors": 0, "near_total": 0,
           "far_errors": 0, "far_total": 0, "supported": {},
           "supported_by_model": {}, "eligibility_errors": 0}
    out["eligibility_errors"] = sum(
        (elig[c]["status"] == R.ELIGIBLE) != (t_elig[c]["status"] == R.ELIGIBLE)
        for c in elig)
    tol = Fraction(1, 10)
    supported = {p: 0 for p in ("P1", "P2", "P3")}
    by_model: dict[str, int] = {}
    for m, f in R.model_frames(cfg):
        for lim in b_sel:
            est = R.configuration_report(tables, cfg, _matrix(), elig, a, m, f, lim)
            tru = R.configuration_report(truth, cfg, _matrix(), t_elig, a, m, f, lim)
            for g in ("G1", "G3", "G5"):
                out["jaccard"][g].append(_jaccard(set(est["populations"][g]),
                                                  set(tru["populations"][g])))
            e1, t1 = set(est["populations"]["G1"]), set(tru["populations"]["G1"])
            out["g1_false_in"].append(len(e1 - t1))
            out["g1_false_out"].append(len(t1 - e1))
            ta = truth.x(m, f, a.cid)
            for cid in COMPAT.compatible_ids(_matrix(), lim):
                if cid not in est["matching"]:
                    continue                      # an A candidate
                tx = truth.x(m, f, cid)
                true_diff = abs(Fraction(tx.k, tx.n) - Fraction(ta.k, ta.n))
                near = abs(true_diff - tol) <= Fraction(1, 20)
                wrong = (true_diff <= tol) != bool(est["matching"][cid]["raw"])
                if near:
                    out["near_total"] += 1
                    out["near_errors"] += wrong
                else:
                    out["far_total"] += 1
                    out["far_errors"] += wrong
            for p in supported:
                if est["coverage"][p]["supported"] and est["a_informative"]:
                    supported[p] += 1
                    if p == "P1":
                        by_model[m] = by_model.get(m, 0) + 1
    out["supported"] = supported
    out["supported_by_model"] = by_model
    return out


def _task(args: tuple) -> list[dict[str, Any]]:
    surface, alloc, seeds = args
    truth = truth_tables(surface)
    true_result = CAL.finalize(truth, CFG0, _matrix())
    fixed = true_result["status"] == "FEASIBLE" or (
        true_result.get("a") and true_result["a"].get("selected")
        and true_result["b"].get("selected"))
    out = []
    for seed in seeds:
        sim = one_pilot(surface, alloc, seed)
        r = sim["result"]
        rec = {"seed": seed, "status": r["status"], "refined": sim["refined"],
               "a": (r.get("a") or {}).get("selected"),
               "b": (r.get("b") or {}).get("selected")}
        if fixed:
            rec["membership"] = _membership(sim["tables"], truth, true_result,
                                            CFG0)
        out.append(rec)
    return out


def _mean(xs):
    return round(statistics.mean(xs), 4) if xs else None


def _summarise(records: list[dict[str, Any]], true_result: dict[str, Any],
               alloc: Allocation) -> dict[str, Any]:
    n = len(records)
    true_status = true_result["status"]
    true_a = (true_result.get("a") or {}).get("selected")
    true_b = (true_result.get("b") or {}).get("selected")
    feasible = sum(r["status"] == "FEASIBLE" for r in records)
    out = {"reps": n, "max_rows": alloc.max_rows(),
           "mean_refined_cells": _mean([r["refined"] for r in records]),
           "true": {"status": true_status, "a": true_a, "b": true_b},
           "feasible_share": round(feasible / n, 4),
           "false_feasible": (round(feasible / n, 4)
                              if true_status != "FEASIBLE" else 0.0),
           "false_infeasible": (round(1 - feasible / n, 4)
                                if true_status == "FEASIBLE" else 0.0),
           "a_agrees": round(sum(r["a"] == true_a for r in records) / n, 4),
           "b_agrees": round(sum(r["b"] == true_b for r in records) / n, 4),
           "a_counts": dict(sorted(_count(r["a"] or "none" for r in records))),
           "b_counts": dict(sorted(_count("-".join(map(str, r["b"]))
                                          if r["b"] else "none"
                                          for r in records)))}
    mem = [r["membership"] for r in records if "membership" in r]
    if mem:
        out["membership"] = {
            "g1_jaccard": _mean([x for m in mem for x in m["jaccard"]["G1"]]),
            "g3_jaccard": _mean([x for m in mem for x in m["jaccard"]["G3"]]),
            "g5_jaccard": _mean([x for m in mem for x in m["jaccard"]["G5"]]),
            "g1_false_inclusions_per_config":
                _mean([x for m in mem for x in m["g1_false_in"]]),
            "g1_false_exclusions_per_config":
                _mean([x for m in mem for x in m["g1_false_out"]]),
            "near_boundary_error_rate": round(
                sum(m["near_errors"] for m in mem)
                / max(1, sum(m["near_total"] for m in mem)), 4),
            "far_from_boundary_error_rate": round(
                sum(m["far_errors"] for m in mem)
                / max(1, sum(m["far_total"] for m in mem)), 4),
            "eligibility_errors_per_pilot":
                _mean([m["eligibility_errors"] for m in mem]),
            "supported_mean": {p: _mean([m["supported"][p] for m in mem])
                               for p in ("P1", "P2", "P3")},
            "supported_sd": {p: round(statistics.pstdev(
                [m["supported"][p] for m in mem]), 3) for p in ("P1", "P2", "P3")},
            "p1_support_by_model": {
                model: _mean([m["supported_by_model"].get(model, 0)
                              for m in mem]) for model in CFG0.models}}
    return out


def _count(items):
    c: dict[str, int] = {}
    for i in items:
        c[i] = c.get(i, 0) + 1
    return c.items()


def run(reps: int, *, surfaces=None, allocations=ALLOCATIONS, workers: int = 8,
        seed: int = 20261019) -> dict[str, Any]:
    surfaces = list(surfaces or SURFACES)
    tasks = []
    for s in surfaces:
        for a in allocations:
            seeds = [int.from_bytes(hashlib.sha256(
                f"{seed}|{s}|{a.name}|{i}".encode()).digest()[:4], "big")
                for i in range(reps)]
            chunks = [seeds[i::workers] for i in range(workers) if seeds[i::workers]]
            tasks += [(s, a, c) for c in chunks]
    started = time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_task, tasks))
    grouped: dict[tuple[str, str], list] = {}
    for (s, a, _), recs in zip(tasks, results):
        grouped.setdefault((s, a.name), []).extend(recs)
    out: dict[str, Any] = {
        "schema": "dci.batch1/calibration-precision/v1",
        "note": "SIMULATED: invented compliance surfaces passed through the "
                "real selection code; not an empirical finding",
        "reps": reps, "seed": seed, "topic_sd": TOPIC_SD,
        "cell_topic_sd": CELL_TOPIC_SD,
        "allocations": {a.name: {"focal_stage1_topics": a.focal_stage1_topics,
                                 "stage2_cap": a.stage2_cap,
                                 "uniform": a.uniform,
                                 "stage2_draws": a.stage2_draws,
                                 "max_rows": a.max_rows()}
                        for a in allocations},
        "surfaces": {}}
    for s in surfaces:
        true_result = CAL.finalize(truth_tables(s), CFG0, _matrix())
        out["surfaces"][s] = {a.name: _summarise(grouped[(s, a.name)],
                                                 true_result, a)
                              for a in allocations}
    out["seconds"] = round(time.time() - started, 1)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m dci.batch1.simulate")
    p.add_argument("--reps", type=int, default=40)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--surfaces", nargs="*")
    p.add_argument("--out", required=True)
    p.add_argument("--d14-pilots", type=int, default=0,
                   help="also validate the D14 stable-member verdict on this "
                        "many pilots per surface")
    p.add_argument("--d14-boot", type=int, default=50)
    p.add_argument("--only-extras", action="store_true",
                   help="keep the main study in --out and recompute only the "
                        "D07 and D14 sections")
    args = p.parse_args(argv)
    if args.only_extras:
        with open(args.out) as fh:
            result = json.load(fh)
    else:
        result = run(args.reps, surfaces=args.surfaces, workers=args.workers)
    result["d07_sensitivity"] = {
        "n96": d07_sensitivity(200, n_b=96), "n32": d07_sensitivity(200, n_b=32)}
    if args.d14_pilots:
        result["d14_validation"] = d14_validation(
            args.d14_pilots, args.d14_boot,
            surfaces=args.surfaces or list(SURFACES), workers=args.workers)
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps({"written": args.out, "seconds": result["seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
