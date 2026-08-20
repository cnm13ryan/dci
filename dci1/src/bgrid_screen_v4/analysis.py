"""Readouts and the §1.4 verdict for the B-grid screen.

NON-CONFIRMATORY. Every quantity here is a design diagnostic.

B solo under the current stem at m = 7 to 10 is not in this screen's own
evidence: it is the registered §12.2 ladder screen, read from evidence/dci1-v4
without regeneration. ``load_rows`` splices it in so one code path analyses the
whole curve.
"""
from __future__ import annotations

import json
import math
import random
import statistics as stt
from pathlib import Path
from typing import Any, Sequence

from dci1v4.protocol import constants as C
from dci1v4.verifiers.constraints import FOCAL_GRID, TARGET_GRID

from bgrid_screen_v4 import focal
from bgrid_screen_v4 import plan as pl

DCI1 = Path(__file__).resolve().parent.parent.parent
SCREEN = DCI1 / "evidence" / "bgrid-screen-v4"
FS_SCREEN = DCI1 / "evidence" / "fs-screen-v4"
REGISTERED = DCI1 / "evidence" / "dci1-v4"

MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
SHORT = {"gemma-3n-e2b-it": "E2B", "gemma-3n-e4b-it": "E4B",
         "qwen3-4b": "Qwen3-4B", "qwen3-4b-instruct-2507": "Qwen3-4B-Inst"}

ANALYSIS_SEED = 20260821          # an analysis seed, NOT a study seed
BOOTSTRAP_DRAWS = 2000
THRESHOLD = C.NON_VACUITY_MIN_WORDS


# ------------------------------------------------------------------ loading
def _registered_b_current(model: str) -> list[dict[str, Any]]:
    """B solo under the current stem at m = 7 to 10: the registered §12.2
    ladder screen, reused without regeneration."""
    paths = sorted((REGISTERED / model / "prescreen").glob(
        "ladder-cap*/cache.jsonl"))
    assert len(paths) == 1, paths
    out = []
    for line in paths[0].open():
        r = json.loads(line)
        parts = r["cell_type"].split(":")
        if parts[1] != "B":
            continue
        score = r["scores"][0]
        out.append({
            "role": "b_solo", "stem": "current", "kind": "B",
            "severity": int(parts[2]), "topic_id": r["topic_id"],
            "word_count": r["word_count"], "truncated": r["truncated"],
            "max_word_length": score["statistic"], "companion": None,
            "scores": [{"kind": "B", "severity": int(parts[2]),
                        "passed": score["passed"],
                        "statistic": score["statistic"]}],
            "stem_satisfied": pl.stem_satisfied(r["word_count"]),
            "source": "registered §12.2 ladder screen (reused)"})
    return out


def _fs_screen_b_floored(model: str) -> list[dict[str, Any]]:
    """The FORM x STEM screen's floored B rows, for the replication check only.
    Never mixed into this screen's own curve."""
    out = []
    for path in sorted((FS_SCREEN / model).glob("screen-cap*/cache.jsonl")):
        for line in path.open():
            r = json.loads(line)
            if (r["kind"] == "B" and r["stem"] == "floored"
                    and not r.get("companion") and r["form"] == "outcome"):
                out.append(r)
    return out


def load_rows(model: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((SCREEN / model).glob("screen-cap*/cache.jsonl")):
        rows += [json.loads(line) for line in path.open()]
    for r in rows:
        r.setdefault("source", "bgrid screen")
    return rows + _registered_b_current(model)


def score_of(row: dict[str, Any], kind: str) -> dict[str, Any] | None:
    for s in row["scores"]:
        if s["kind"] == kind:
            return s
    return None


# --------------------------------------------------------------- primitives
def qtl(xs: Sequence[float], p: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = p * (len(xs) - 1)
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (i - lo) * (xs[hi] - xs[lo])


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def cluster_se(rows: Sequence[dict], statistic, *,
               draws: int = BOOTSTRAP_DRAWS) -> dict[str, float]:
    """Topic-clustered bootstrap: topics are the resampling unit.

    Returns the bootstrap standard deviation -- the standard error the §1.4
    rule is stated in -- together with a 90% percentile interval.
    """
    rng = random.Random(ANALYSIS_SEED)
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r["topic_id"], []).append(r)
    keys = sorted(by)
    values = []
    for _ in range(draws):
        sample = [x for _ in keys for x in by[keys[rng.randrange(len(keys))]]]
        v = statistic(sample)
        if v is not None and v == v:
            values.append(v)
    if len(values) < 50:
        return {"se": float("nan"), "lo": float("nan"), "hi": float("nan"),
                "n_topics": len(keys)}
    values.sort()
    return {"se": stt.pstdev(values),
            "lo": values[int(0.05 * (len(values) - 1))],
            "hi": values[int(0.95 * (len(values) - 1))],
            "n_topics": len(keys)}


# --------------------------------------------------- per-severity readouts
def b_curve(rows: Sequence[dict], stem: str, *,
            threshold: int = THRESHOLD) -> dict[int, dict[str, Any]]:
    """§1.3 readouts for B solo, per m."""
    groups: dict[int, list] = {}
    for r in rows:
        if (r["role"] == "b_solo" and r["stem"] == stem
                and not r.get("companion")):
            groups.setdefault(r["severity"], []).append(r)
    out = {}
    for m, group in sorted(groups.items()):
        n = len(group)
        passed = [bool(score_of(r, "B")["passed"]) for r in group]
        raw = sum(passed)
        words = [r["word_count"] for r in group]
        maxlen = [r.get("max_word_length",
                        score_of(r, "B")["statistic"]) for r in group]
        nv = sum(1 for r, p in zip(group, passed)
                 if p and r["word_count"] >= threshold and not r["truncated"])
        se = cluster_se(group, lambda s: stt.fmean(
            1.0 if score_of(x, "B")["passed"] else 0.0 for x in s) if s else None)
        out[m] = {
            "n": n, "raw": raw / n, "raw_k": raw,
            "non_vacuous": nv / n,
            "vacuous_share_of_passes": (raw - nv) / raw if raw else 0.0,
            "vacuity": (raw - nv) / n,
            "truncation": sum(1 for r in group if r["truncated"]) / n,
            "stem_satisfied": sum(1 for r in group
                                  if r.get("stem_satisfied")) / n,
            "wilson": wilson(raw, n),
            "cluster": se,
            "words": {"mean": stt.fmean(words), "median": stt.median(words),
                      "q10": qtl(words, .10), "q25": qtl(words, .25),
                      "q75": qtl(words, .75), "q90": qtl(words, .90),
                      "share_under_threshold":
                          sum(1 for w in words if w < threshold) / n},
            "max_word_length": {
                "mean": stt.fmean(maxlen), "median": stt.median(maxlen),
                "q10": qtl(maxlen, .10), "q90": qtl(maxlen, .90),
                "max": max(maxlen)},
            "registered_rung": m in FOCAL_GRID,
        }
    return out


def a_curve(rows: Sequence[dict], stem: str = "floored") -> dict[int, float]:
    groups: dict[int, list] = {}
    for r in rows:
        if r["role"] == "a_solo" and r["stem"] == stem:
            groups.setdefault(r["severity"], []).append(r)
    return {n: stt.fmean(1.0 if score_of(r, "A")["passed"] else 0.0
                         for r in g) for n, g in sorted(groups.items())}


def reanchor_n(curve: dict[int, float], *,
               aim: float = C.TARGET_AIM) -> tuple[int, float]:
    """A's anchor under the registered §12.3 rule, re-measured under the stem."""
    if not curve:
        raise KeyError("no A curve")
    n = min(curve, key=lambda k: (abs(curve[k] - aim), k))
    return n, curve[n]


# ------------------------------------------------------------ decision rule
def band_verdict(curve: dict[int, dict[str, Any]], *,
                 band: tuple[float, float] = C.FOCAL_BAND) -> dict[str, Any]:
    """§1.4, applied exactly as frozen. No rung is chosen to obtain a result."""
    lo, hi = band
    in_band = []
    for m, cell in sorted(curve.items()):
        p = cell["raw"]
        if lo <= p <= hi:
            se = cell["cluster"]["se"]
            in_band.append({
                "m": m, "raw": p, "se": se,
                "distance_to_lower": p - lo, "distance_to_upper": hi - p,
                "se_to_lower": (p - lo) / se if se else float("inf"),
                "se_to_upper": (hi - p) / se if se else float("inf"),
                "clear_of_both_edges": bool(se) and (p - lo) > se and (hi - p) > se,
                "registered_rung": m in FOCAL_GRID,
            })
    if not in_band:
        return {"in_band": [], "smallest_in_band": None, "status": "FAIL",
                "reason": f"no rung in {list(band)} at m <= {focal.GRID_MAX}"}
    smallest = in_band[0]
    return {"in_band": in_band, "smallest_in_band": smallest,
            "any_clear_of_both_edges": any(r["clear_of_both_edges"]
                                           for r in in_band),
            "status": ("PASS" if any(r["clear_of_both_edges"] for r in in_band)
                       else "MARGINAL"),
            "reason": ("at least one in-band rung sits more than one clustered "
                       "standard error from both band edges"
                       if any(r["clear_of_both_edges"] for r in in_band)
                       else "every in-band rung sits within one clustered "
                            "standard error of a band edge")}


def study_verdict(per_model: dict[str, dict[str, Any]]) -> dict[str, Any]:
    statuses = {m: v["status"] for m, v in per_model.items()}
    if any(s == "FAIL" for s in statuses.values()):
        overall = "FAIL"
    elif all(s == "PASS" for s in statuses.values()):
        overall = "PASS"
    else:
        overall = "MARGINAL"
    return {"per_model": statuses, "verdict": overall,
            "rule": "§1.4, frozen before the first generation",
            "consequence": {
                "PASS": "an honest focal severity exists on all four models",
                "MARGINAL": ("an in-band rung exists on all four models but at "
                             "least one is within one standard error of a band "
                             "edge; a fresh-topic confirmation is required "
                             "before any grid amendment"),
                "FAIL": ("at least one model has no in-band rung at m <= 12; "
                         "the grid is NOT extended past 12 to obtain a pass"),
            }[overall]}


# --------------------------------------------------------------- the B side
def d_b_from_a(rows: Sequence[dict], m: int, *,
               threshold: int = THRESHOLD) -> dict[str, Any]:
    """D(B<-A) at focal severity m under the floored stem."""
    solo = {r["topic_id"]: r for r in rows
            if r["role"] == "b_solo" and r["stem"] == "floored"
            and r["severity"] == m and not r.get("companion")}
    comp = {r["topic_id"]: r for r in rows
            if r["role"] == "fixture" and r["stem"] == "floored"
            and r.get("companion") and r["companion"][1] == m}
    topics = sorted(set(solo) & set(comp))
    if not topics:
        return {"available": False, "m": m}

    def bp(r):
        return 1.0 if score_of(r, "B")["passed"] else 0.0

    p_solo = stt.fmean(bp(solo[t]) for t in topics)
    p_comp = stt.fmean(bp(comp[t]) for t in topics)
    long_s = [t for t in topics if solo[t]["word_count"] >= threshold]
    long_c = [t for t in topics if comp[t]["word_count"] >= threshold]
    ps = stt.fmean(bp(solo[t]) for t in long_s) if long_s else float("nan")
    pc = stt.fmean(bp(comp[t]) for t in long_c) if long_c else float("nan")
    passes = [t for t in topics if bp(solo[t])]
    vac = [t for t in passes if solo[t]["word_count"] < threshold]
    paired = [bp(solo[t]) - bp(comp[t]) for t in topics]
    return {
        "available": True, "m": m, "topics": len(topics),
        "b_solo": p_solo, "b_composed": p_comp,
        "D_B_from_A_raw": p_solo - p_comp,
        "D_B_from_A_long_only": ps - pc,
        "paired_se": (stt.pstdev(paired) / math.sqrt(len(paired))
                      if len(paired) > 1 else float("nan")),
        "b_solo_vacuous_share_of_passes":
            len(vac) / len(passes) if passes else 0.0,
        "solo_median_words": stt.median([solo[t]["word_count"] for t in topics]),
        "composed_median_words": stt.median(
            [comp[t]["word_count"] for t in topics]),
        "n_long_solo": len(long_s), "n_long_composed": len(long_c),
        "collider_caveat": (
            "the long-only figure conditions on word count, a post-treatment "
            "variable and a collider. It is a sensitivity diagnostic, NOT a "
            "corrected estimate of D(B<-A)."),
    }


# ------------------------------------------- replication and extrapolation
def replication_gap(model: str, curve: dict[int, dict[str, Any]]
                    ) -> dict[str, Any]:
    """This screen's independent redraw of floored B at m = 7 to 10 against the
    FORM x STEM screen's values on the same topics under the same stem."""
    fs_rows = _fs_screen_b_floored(model)
    fs: dict[int, float] = {}
    groups: dict[int, list] = {}
    for r in fs_rows:
        groups.setdefault(r["severity"], []).append(r)
    for m, g in groups.items():
        fs[m] = stt.fmean(1.0 if score_of(r, "B")["passed"] else 0.0 for r in g)
    out = {}
    for m in sorted(set(fs) & set(curve)):
        out[m] = {"fs_screen": fs[m], "bgrid_screen": curve[m]["raw"],
                  "gap": curve[m]["raw"] - fs[m]}
    gaps = [v["gap"] for v in out.values()]
    return {"per_m": out,
            "mean_abs_gap": stt.fmean([abs(g) for g in gaps]) if gaps else None,
            "mean_signed_gap": stt.fmean(gaps) if gaps else None,
            "note": ("two independent single draws per topic under different "
                     "seed roots; a gap of this size is sampling noise, not "
                     "disagreement")}


def extrapolation_gap(model: str, curve: dict[int, dict[str, Any]]
                      ) -> dict[str, Any]:
    """The FORM x STEM screen's floored B curve, extrapolated linearly in m to
    the two screen rungs, against what those rungs actually produced."""
    fs_rows = _fs_screen_b_floored(model)
    groups: dict[int, list] = {}
    for r in fs_rows:
        groups.setdefault(r["severity"], []).append(r)
    fs = {m: stt.fmean(1.0 if score_of(r, "B")["passed"] else 0.0 for r in g)
          for m, g in sorted(groups.items())}
    if len(fs) < 2:
        return {"available": False}
    xs, ys = list(fs), [fs[m] for m in fs]
    xbar, ybar = stt.fmean(xs), stt.fmean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    slope = (sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
             if denom else 0.0)
    intercept = ybar - slope * xbar
    out = {}
    for m in focal.EXTENSION:
        if m not in curve:
            continue
        pred = min(1.0, max(0.0, intercept + slope * m))
        out[m] = {"predicted": pred, "measured": curve[m]["raw"],
                  "gap": curve[m]["raw"] - pred}
    return {"available": True, "fit_on": fs, "slope": slope,
            "intercept": intercept, "per_m": out,
            "note": ("an OLS line in m fitted to four points, extrapolated two "
                     "rungs. It is reported because the brief asks for the gap, "
                     "not because it is a good model of a bounded proportion")}
