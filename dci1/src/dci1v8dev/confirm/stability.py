"""How stable the selected operating point is under the calibration topics.

The audit of 2026-09-01 found that §12.3's n*(f) --- the eligible severity
of A nearest 0.70 --- is chosen among five to eight near-tied rungs by a
point estimate whose standard error is of the order of the gaps between
them, and moved 3 -> 6 on one frame when the calibration was doubled. The
rule is registered and is not changed here. What this module adds, before
the freeze and at no generation cost, is the **measurement** of that
fragility: a topic-level bootstrap (clustered on the frame's calibration
topics, re-running §12.3 verbatim on each resample) giving the
distribution of the selected severity and of iota_A(f), so that the
freeze can state Delta_R(f) as *conditional on the frozen n*(f)* with the
reproduction probability on the record. No threshold is attached and no
selection is changed by it.
"""
from __future__ import annotations

import collections
import random
from typing import Any, Mapping, Sequence

from dci1v7.protocol import constants as C
from dci1v7.stages.regime import select_operating_point

from dci1v8dev.run.execute import frame_of_block

__all__ = ["per_topic_curves", "operating_point_stability",
           "frame_stability"]


def per_topic_curves(rows: Sequence[Mapping[str, Any]], *, kind: str,
                     frame: int) -> tuple[dict[int, dict[str, float]],
                                          dict[int, dict[str, float]]]:
    """Per (severity) -> topic -> mean passed, for the solo cells of
    ``kind`` and (for A) its chance on the unconstrained cells, on one
    frame's grid rows."""
    solo: dict[int, dict[str, list[float]]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    chance: dict[int, dict[str, list[float]]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    for row in rows:
        if frame_of_block(row) != frame:
            continue
        by = {(s["kind"], int(s["severity"])): s for s in row["scores"]}
        if row.get("arm") == "solo":
            cid = str(row["cell_id"])
            k, _, q = cid.partition(":")[2].rpartition(":")
            if k != kind:
                continue
            entry = by.get((kind, int(q)))
            if entry is None:
                continue
            solo[int(q)][row["topic_id"]].append(1.0 if entry["passed"] else 0.0)
        elif row.get("arm") == "unconstrained":
            for (k, q), entry in by.items():
                if k == kind:
                    chance[q][row["topic_id"]].append(
                        1.0 if entry["passed"] else 0.0)
    fold = lambda d: {q: {t: sum(v) / len(v) for t, v in topics.items()}  # noqa: E731
                      for q, topics in d.items()}
    return fold(solo), fold(chance)


def operating_point_stability(solo: Mapping[int, Mapping[str, float]],
                              chance: Mapping[int, Mapping[str, float]] | None,
                              *, grid: Sequence[int], band: tuple,
                              aim: float, selected: int | None,
                              resamples: int, seed: int) -> dict[str, Any]:
    grid = [q for q in grid if q in solo]
    if not grid:
        return {"n_topics": 0, "resamples": 0, "distribution": {},
                "p_selected_reproduced": None}
    topics = sorted(set.intersection(*(set(solo[q]) for q in grid)))
    n = len(topics)
    rng = random.Random(seed)
    counts: collections.Counter = collections.Counter()
    iotas: list[float] = []
    for _ in range(resamples):
        picks = [topics[rng.randrange(n)] for _ in range(n)]
        curve = {q: sum(solo[q][t] for t in picks) / n for q in grid}
        sel = select_operating_point(curve, band=band, aim=aim,
                                     prefer_smaller=True, grid=grid)
        s = sel["selected"]
        counts[s] += 1
        if s is not None and chance is not None and s in chance:
            k = sum(chance[s].get(t, 0.0) for t in picks) / n
            if k < 1.0:
                iotas.append((curve[s] - k) / (1.0 - k))
    dist = {str(k): v / resamples for k, v in sorted(
        counts.items(), key=lambda kv: (kv[0] is None, kv[0]))}
    out: dict[str, Any] = {
        "n_topics": n, "resamples": resamples, "seed": seed,
        "selected": selected, "distribution": dist,
        "p_selected_reproduced": (counts[selected] / resamples
                                  if selected is not None else None),
        "modal": max(counts, key=counts.get) if counts else None,
        "rule": "§12.3 re-run on each topic resample (clustered on the "
                "frame's calibration topics); no threshold attached",
    }
    if iotas:
        iotas.sort()
        m = sum(iotas) / len(iotas)
        out["iota_a_bootstrap"] = {
            "mean": m,
            "sd": (sum((x - m) ** 2 for x in iotas) / len(iotas)) ** 0.5,
            "p2_5": iotas[int(0.025 * len(iotas))],
            "p97_5": iotas[min(len(iotas) - 1, int(0.975 * len(iotas)))]}
    return out


def frame_stability(grid_a_rows: Sequence[Mapping[str, Any]],
                    grid_b_rows: Sequence[Mapping[str, Any]], *, frame: int,
                    n_star: int | None, m_star: int | None,
                    resamples: int = 2000, seed: int = 0) -> dict[str, Any]:
    solo_a, chance_a = per_topic_curves(grid_a_rows, kind="A", frame=frame)
    solo_b, _ = per_topic_curves(grid_b_rows, kind="B", frame=frame)
    b_grid = list(C.FOCAL_GRID) + [q for q in C.FOCAL_EXTENSION if q in solo_b]
    return {
        "frame": frame,
        "n_star": operating_point_stability(
            solo_a, chance_a, grid=list(C.TARGET_GRID), band=C.TARGET_BAND,
            aim=C.TARGET_AIM, selected=n_star, resamples=resamples,
            seed=seed * 7919 + frame),
        "m_star": operating_point_stability(
            solo_b, None, grid=b_grid, band=C.FOCAL_BAND, aim=C.FOCAL_AIM,
            selected=m_star, resamples=resamples, seed=seed * 7919 + 100 + frame),
        "reading": "Delta_R(f) is conditional on the frozen n*(f) and m*(f); "
                   "p_selected_reproduced is the share of topic resamples "
                   "on which §12.3 selects the frozen severity",
    }
