"""Readouts for the FORM x STEM screen (§2.3 of the screen brief).

NON-CONFIRMATORY. Every quantity here is a design diagnostic.

The `count x current` cell is not in this screen's own evidence: it is the
registered §12.2 ladder screen, read from evidence/dci1-v4 without
regeneration. `load_cells` splices it in so all four FORM x STEM cells are
analysed by one code path.
"""
from __future__ import annotations

import json
import math
import random
import statistics as stt
from pathlib import Path
from typing import Any, Iterable, Sequence

from dci1v4.protocol import constants as C
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          TARGET_GRID)

from fs_screen_v4 import constraints as cc
from fs_screen_v4 import plan as pl

DCI1 = Path(__file__).resolve().parent.parent.parent
SCREEN = DCI1 / "evidence" / "fs-screen-v4"
REGISTERED = DCI1 / "evidence" / "dci1-v4"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
SHORT = {"gemma-3n-e2b-it": "E2B", "gemma-3n-e4b-it": "E4B",
         "qwen3-4b": "Qwen3-4B", "qwen3-4b-instruct-2507": "Qwen3-4B-Inst"}

ANALYSIS_SEED = 20260820        # arbitrary analysis seed, NOT a study seed


# ------------------------------------------------------------------ loading
def _registered_rows(model: str) -> list[dict[str, Any]]:
    """The registered ladder screen, normalised onto the screen row schema."""
    path = sorted((REGISTERED / model / "prescreen").glob(
        "ladder-cap*/cache.jsonl"))
    assert len(path) == 1, path
    out = []
    for line in path[0].open():
        r = json.loads(line)
        kind, severity = r["cell_type"].split(":")[1:3]
        score = r["scores"][0]
        out.append({
            "form": "outcome" if kind in ("A", "B") else "count",
            "stem": "current", "kind": kind, "severity": int(severity),
            "topic_id": r["topic_id"], "word_count": r["word_count"],
            "truncated": r["truncated"], "companion": None,
            "raw_response": r["raw_response"],
            "scores": [{"kind": kind, "severity": int(severity),
                        "passed": score["passed"],
                        "statistic": score["statistic"]}],
            "stem_satisfied": pl.stem_satisfied(r["word_count"]),
            "source": "registered ladder screen (reused, not regenerated)"})
    return out


def _registered_capscreen(model: str) -> list[dict[str, Any]]:
    """The §12.1 cap-selection set at the selected cap: the ONLY registered
    source of an A+B fixture cell and a B-solo cell on the same topics under
    the CURRENT stem. Without it the STEM contrast has no baseline."""
    record = json.loads(
        (REGISTERED / model / "regime_screen.json").read_text())
    cap = record.get("payload", record)["completion_cap"]["selected_cap"]
    path = REGISTERED / model / "prescreen" / f"capscreen-cap{cap}" / "cache.jsonl"
    out = []
    for line in path.open():
        r = json.loads(line)
        if r["cell_type"] == "cap:load1:B":
            kind, severity, companion = "B", pl.FIXTURE_B_M, None
        elif r["cell_type"] == "cap:load2:A+B":
            kind, severity, companion = "A", pl.FIXTURE_A_N, ["B", pl.FIXTURE_B_M]
        else:
            continue
        out.append({
            "form": "outcome", "stem": "current", "kind": kind,
            "severity": severity, "topic_id": r["topic_id"],
            "word_count": r["word_count"], "truncated": r["truncated"],
            "companion": companion, "raw_response": r["raw_response"],
            "scores": [{"kind": s["kind"], "severity": s["severity"],
                        "passed": s["passed"], "statistic": s["statistic"]}
                       for s in r["scores"]],
            "stem_satisfied": pl.stem_satisfied(r["word_count"]),
            "source": "registered §12.1 cap set (reused, not regenerated)",
            "fixture_only": True})
    return out


def load_cells(model: str) -> list[dict[str, Any]]:
    screen = sorted((SCREEN / model).glob("screen-cap*/cache.jsonl"))
    rows = list(_registered_rows(model)) + _registered_capscreen(model)
    for path in screen:
        rows += [json.loads(line) for line in path.open()]
    return rows


def outcome_score(row: dict[str, Any], kind: str) -> dict[str, Any] | None:
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


def cluster_ci(rows: Sequence[dict], statistic, *, draws: int = 1000,
               lo: float = 0.05, hi: float = 0.95) -> tuple[float, float]:
    """Topic-clustered bootstrap interval. Topics are the resampling unit."""
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
        return (float("nan"), float("nan"))
    values.sort()
    return (values[int(lo * (len(values) - 1))],
            values[int(hi * (len(values) - 1))])


# --------------------------------------------------- per-severity readouts
def severity_table(rows: Sequence[dict], *, threshold: int = 20
                   ) -> dict[tuple[str, str, str, int], dict[str, Any]]:
    """§2.3 per-severity readouts, keyed by (form, stem, kind, severity)."""
    groups: dict[tuple, list] = {}
    for r in rows:
        if r.get("companion") or r.get("fixture_only"):
            continue      # composed cells, and cap-set fixtures, are separate
        groups.setdefault((r["form"], r["stem"], r["kind"], r["severity"]),
                          []).append(r)
    out = {}
    for key, group in groups.items():
        kind = key[2]
        passed = [bool(outcome_score(r, kind)["passed"]) for r in group]
        words = [r["word_count"] for r in group]
        n = len(group)
        nv = sum(1 for r, p in zip(group, passed)
                 if p and r["word_count"] >= threshold and not r["truncated"])
        raw = sum(passed)
        short = [r for r in group if r["word_count"] < threshold]
        long = [r for r in group if r["word_count"] >= threshold]
        p_short = (sum(1 for r in short if outcome_score(r, kind)["passed"])
                   / len(short)) if short else float("nan")
        p_long = (sum(1 for r in long if outcome_score(r, kind)["passed"])
                  / len(long)) if long else float("nan")
        out[key] = {
            "n": n, "raw": raw / n, "non_vacuous": nv / n,
            "vacuous_share_of_passes": (raw - nv) / raw if raw else 0.0,
            "vacuity": (raw - nv) / n,
            "truncation": sum(1 for r in group if r["truncated"]) / n,
            "p_pass_short": p_short, "n_short": len(short),
            "p_pass_long": p_long, "n_long": len(long),
            "wilson_short": wilson(
                sum(1 for r in short if outcome_score(r, kind)["passed"]),
                len(short)),
            "wilson_long": wilson(
                sum(1 for r in long if outcome_score(r, kind)["passed"]),
                len(long)),
            "words": {"mean": stt.fmean(words), "median": stt.median(words),
                      "q10": qtl(words, .10), "q25": qtl(words, .25),
                      "q75": qtl(words, .75), "q90": qtl(words, .90),
                      "share_under_threshold":
                          sum(1 for w in words if w < threshold) / n},
            "stem_satisfied": sum(1 for r in group
                                  if r.get("stem_satisfied")) / n,
        }
    return out


# ------------------------------------------------- the conjunction criterion
def families_meeting_conjunction(table: dict, *, form: str, stem: str,
                                 anchor: float,
                                 caliper: float = C.REFERENCE_CALIPER,
                                 vacuity_max: float = C.REFERENCE_VACUITY_MAX,
                                 threshold: int = 20) -> dict[str, Any]:
    """§2.3: families carrying a rung inside the caliper AND at vacuity <=
    the maximum, AT THE SAME SEVERITY. This is the quantity the registered
    pool fails 0 of 64 times."""
    families = (REFERENCE_LADDERS if form == "count" else cc.CANDIDATES)
    hits: dict[str, list] = {}
    for family in families:
        for q in (REFERENCE_LADDERS[family] if form == "count"
                  else cc.CANDIDATES[family].ladder):
            cell = table.get((form, stem, family, q))
            if cell is None:
                continue
            in_caliper = abs(cell["raw"] - anchor) <= caliper
            low_vacuity = cell["vacuity"] <= vacuity_max
            if in_caliper and low_vacuity:
                hits.setdefault(family, []).append(
                    {"severity": q, "raw": cell["raw"],
                     "vacuity": cell["vacuity"],
                     "distance": abs(cell["raw"] - anchor)})
    return {"families": sorted(hits), "n_families": len(hits),
            "rungs": hits, "anchor": anchor,
            "meets_criterion": len(hits) >= C.N_FINAL_REFERENCES}


def anchor_for(table: dict, stem: str, *, aim: float = C.TARGET_AIM) -> tuple[int, float]:
    """A's pre-screen compliance under the registered §12.3 anchor rule."""
    curve = {n: table[("outcome", stem, "A", n)]["raw"]
             for n in TARGET_GRID if ("outcome", stem, "A", n) in table}
    if not curve:
        raise KeyError(f"no A curve for stem={stem}")
    n = min(curve, key=lambda k: (abs(curve[k] - aim), k))
    return n, curve[n]


# --------------------------------------------------------------- the B side
def b_side(rows: Sequence[dict], stem: str, *, threshold: int = 20
           ) -> dict[str, Any]:
    """B-solo compliance and vacuity, and D(B<-A) at the fixture severities."""
    solo = {r["topic_id"]: r for r in rows
            if r["form"] == "outcome" and r["stem"] == stem
            and r["kind"] == "B" and r["severity"] == pl.FIXTURE_B_M
            and not r.get("companion")}
    composed = {r["topic_id"]: r for r in rows
                if r.get("companion") and r["stem"] == stem
                and r["severity"] == pl.FIXTURE_A_N}
    topics = sorted(set(solo) & set(composed))
    if not topics:
        return {"available": False, "stem": stem}

    def b_pass(r):
        return bool(outcome_score(r, "B")["passed"])

    p_solo = stt.fmean(1.0 if b_pass(solo[t]) else 0.0 for t in topics)
    p_comp = stt.fmean(1.0 if b_pass(composed[t]) else 0.0 for t in topics)
    long_solo = [t for t in topics if solo[t]["word_count"] >= threshold]
    long_comp = [t for t in topics if composed[t]["word_count"] >= threshold]
    ps = (stt.fmean(1.0 if b_pass(solo[t]) else 0.0 for t in long_solo)
          if long_solo else float("nan"))
    pc = (stt.fmean(1.0 if b_pass(composed[t]) else 0.0 for t in long_comp)
          if long_comp else float("nan"))
    passes = [t for t in topics if b_pass(solo[t])]
    vac = [t for t in passes if solo[t]["word_count"] < threshold]
    return {
        "available": True, "stem": stem, "topics": len(topics),
        "b_solo_compliance": p_solo,
        "b_solo_vacuous_share_of_passes": len(vac) / len(passes) if passes else 0.0,
        "b_solo_median_words": stt.median(
            [solo[t]["word_count"] for t in topics]),
        "composed_median_words": stt.median(
            [composed[t]["word_count"] for t in topics]),
        "p_b_given_composed": p_comp,
        "D_B_from_A_raw": p_solo - p_comp,
        "D_B_from_A_long_only": ps - pc,
        "n_long_solo": len(long_solo), "n_long_composed": len(long_comp),
        "collider_caveat": (
            "the long-only figure conditions on word count, a post-treatment "
            "variable and a collider. It is a sensitivity diagnostic, NOT a "
            "corrected estimate of D(B<-A), and must not be used as one."),
    }


# ------------------------------------------------------------- sensitivity
def sensitivity_map(rows: Sequence[dict], *, form: str, stem: str,
                    calipers=(0.05, 0.10, 0.15),
                    thresholds=(10, 20, 30)) -> dict[str, Any]:
    """A MAP, not a search. The registered values are 0.10 and 20 and this
    screen does not change them."""
    out = {}
    for t in thresholds:
        table = severity_table(rows, threshold=t)
        try:
            _, anchor = anchor_for(table, stem)
        except KeyError:
            continue
        for cal in calipers:
            r = families_meeting_conjunction(table, form=form, stem=stem,
                                             anchor=anchor, caliper=cal,
                                             threshold=t)
            out[f"T={t},caliper={cal}"] = {"n_families": r["n_families"],
                                           "families": r["families"]}
    return out
