"""The regime pre-screen (§18.2, items 28–30): completion cap, severity
curves, conservative elimination, and the natural Gate 1 reservoir.

A fixed subject-balanced 96-prompt set runs at each registered cap with
identical prompt identities; the smallest cap with truncation at most 0.10
is selected, else RESPONSE_LENGTH_INCOMPATIBLE. At the selected cap the
complete target, focal, and family severity curves are estimated with one
response per severity cell. Point estimates select nothing; only interval
rules eliminate. No A+B composition and no focal-to-reference target
contrast exists at this stage.
"""
from __future__ import annotations

from typing import Any

from dci1v3.analysis.stats import (
    intersects,
    newcombe_interval,
    wilson_interval,
)
from dci1v3.engine import fs
from dci1v3.engine.dispatch import Job, operation
from dci1v3.errors import TerminalStatus
from dci1v3.generation.cache import cache_rows, fill_cache
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import Cell, prompt_plan, solo_cells
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_obj
from dci1v3.topics.split import split_topics

#: The registered subject-balanced cap-selection kinds: 8 prompts per
#: stratum, kind k drawn on pre-screen topic k mod 2 (DECISIONS_V3 V05).
CAP_SET_KINDS: tuple[tuple[str, int], ...] = (
    ("A", 2), ("A", 8), ("B", 7), ("B", 10),
    ("RF1", 5), ("RF5", 8), ("RF7", 16), ("RF4", 4))


def _all_kinds() -> list[tuple[str, int]]:
    kinds: list[tuple[str, int]] = [("A", n) for n in C.TARGET_GRID]
    kinds += [("B", m) for m in C.FOCAL_GRID]
    for family, grid in C.REFERENCE_FAMILIES.items():
        kinds += [(family, q) for q in grid]
    return kinds


def _cap_set_cells(all_cells: list[Cell]) -> list[Cell]:
    """96 prompts: per stratum, kind k on pre-screen topic k mod 2."""
    split = split_topics()
    per_area: dict[str, list[str]] = {}
    for topic in split["prescreen"]:
        per_area.setdefault(topic["area"], []).append(topic["topic_id"])
    by_key = {(c.topic_id, c.constraint_id if c.constraint_id else "A",
               c.severity if c.severity is not None else c.n): c
              for c in all_cells}
    chosen: list[Cell] = []
    for area in C.SUBJECT_AREAS:
        topics = per_area[area]
        for k, (constraint_id, severity) in enumerate(CAP_SET_KINDS):
            chosen.append(by_key[(topics[k % 2], constraint_id, severity)])
    if len(chosen) != C.PRESCREEN_CAP_PROMPTS:
        raise TerminalStatus("QUALIFICATION_FAILURE", {
            "criterion": "cap-set derivation",
            "observed": len(chosen)})
    return chosen


def _generate_fn(job: Job):
    if job.context.namespace == "synthetic":
        from dci1v3.generation.synthetic import synthetic_generate
        return synthetic_generate
    from dci1v3.generation.backend import run_backend
    return run_backend


def _quantiles(lengths: list[int]) -> dict[str, float]:
    import numpy as np
    if not lengths:
        return {}
    a = np.array(lengths, dtype=float)
    return {f"p{q}": float(np.quantile(a, q / 100))
            for q in (50, 90, 95, 99)}


def _failure(row: dict[str, Any]) -> bool:
    verdicts = row["verdicts"]
    if row["constraint_id"] is None:            # target-solo cell
        return verdicts["s0"] != row["n"]
    return not verdicts["added_pass"]


def _curve(rows: list[dict[str, Any]], key_fn) -> dict[Any, dict[str, Any]]:
    grouped: dict[Any, list[bool]] = {}
    for row in rows:
        grouped.setdefault(key_fn(row), []).append(_failure(row))
    curve = {}
    for key, fails in sorted(grouped.items()):
        k, n = sum(fails), len(fails)
        low, high = wilson_interval(k, n)
        curve[key] = {"failures": k, "trials": n, "rate": k / n,
                      "wilson": [low, high]}
    return curve


@operation("prescreen", stage=C.STAGE_REGIME)
def run_prescreen(job: Job) -> dict[str, Any]:
    split = split_topics()
    all_cells = solo_cells("prescreen", split["prescreen"], _all_kinds(),
                           draws=C.CALIBRATION_DRAWS_PER_CELL)
    cap_cells = _cap_set_cells(all_cells)

    # ---- completion-cap selection over the registered grid --------------
    cap_reports: dict[int, dict[str, Any]] = {}
    selected_cap: int | None = None
    stage_root = job.tree.data_dir("prescreen")
    for cap in C.CAP_GRID:
        stage = f"prescreen_cap{cap}"
        cap_dir = stage_root / f"cap{cap}"
        cap_dir.mkdir(parents=True, exist_ok=True)
        if not (cap_dir / "prompt_plan.json").exists():
            fs.write_json_once(cap_dir / "prompt_plan.json",
                               prompt_plan(cap_cells))
        fill_cache(cap_dir, cap_cells, spec=job.spec, stage=stage,
                   generation_root=C.GENERATION_ROOT_SEED,
                   plan=backend_plan(job.spec, cap=cap),
                   generate_fn=_generate_fn(job),
                   environment=job.environment)
        rows = cache_rows(cap_dir)
        truncated = sum(1 for r in rows if r["finish_reason"] == "length")
        cap_reports[cap] = {
            "prompts": len(rows),
            "truncation_rate": truncated / len(rows),
            "finish_reasons": _finish_counts(rows),
            "length_quantiles": _quantiles(
                [r["token_count"] for r in rows]),
        }
        if selected_cap is None and \
                cap_reports[cap]["truncation_rate"] <= C.TRUNCATION_MAX:
            selected_cap = cap
    if selected_cap is None:
        raise TerminalStatus("RESPONSE_LENGTH_INCOMPATIBLE", {
            "criterion": f"truncation at most {C.TRUNCATION_MAX} at some "
                         f"registered cap",
            "cap_reports": {str(k): v for k, v in cap_reports.items()}})

    # ---- full severity curves at the selected cap -----------------------
    full_dir = stage_root / "full"
    full_dir.mkdir(parents=True, exist_ok=True)
    if not (full_dir / "prompt_plan.json").exists():
        fs.write_json_once(full_dir / "prompt_plan.json",
                           prompt_plan(all_cells))
    fill_cache(full_dir, all_cells, spec=job.spec, stage="prescreen",
               generation_root=C.GENERATION_ROOT_SEED,
               plan=backend_plan(job.spec, cap=selected_cap),
               generate_fn=_generate_fn(job),
               environment=job.environment)
    rows = cache_rows(full_dir)

    target_rows = [r for r in rows if r["constraint_id"] is None]
    focal_rows = [r for r in rows if r["constraint_id"] == "B"]
    target_curve = _curve(target_rows, lambda r: r["n"])
    focal_curve = _curve(focal_rows, lambda r: r["severity"])
    family_curves = {
        family: _curve([r for r in rows if r["constraint_id"] == family],
                       lambda r: r["severity"])
        for family in C.FAMILY_IDS}

    payload = {
        "selected_cap": selected_cap,
        "cap_reports": {str(k): v for k, v in cap_reports.items()},
        "target_curve": {str(k): v for k, v in target_curve.items()},
        "focal_curve": {str(k): v for k, v in focal_curve.items()},
        "family_curves": {f: {str(k): v for k, v in curve.items()}
                          for f, curve in family_curves.items()},
    }

    # ---- conservative early elimination (interval rules only) -----------
    _reject_exhausted_grid(target_curve, C.TARGET_BAND,
                           "TARGET_RANGE_EXHAUSTED", payload)
    _reject_exhausted_grid(focal_curve, C.FOCAL_BAND,
                           "FOCAL_RANGE_EXHAUSTED", payload)

    plausible_focal = [m for m, entry in focal_curve.items()
                       if intersects(tuple(entry["wilson"]),
                                     C.PRESCREEN_FOCAL_BAND)]
    plausible_families = []
    for family, curve in family_curves.items():
        found = False
        for q, entry in curve.items():
            for m in plausible_focal:
                fe = focal_curve[m]
                interval = newcombe_interval(
                    entry["failures"], entry["trials"],
                    fe["failures"], fe["trials"])
                if intersects(interval, C.PRESCREEN_NEWCOMBE_BAND):
                    found = True
                    break
            if found:
                break
        if found:
            plausible_families.append(family)
    payload["plausible_focal"] = plausible_focal
    payload["plausible_families"] = plausible_families
    if len(plausible_families) < C.N_FINAL_REFERENCES:
        raise TerminalStatus("REFERENCE_POOL_MISMATCH", {
            "criterion": "at least three provisionally plausible families",
            **payload})

    return {"status": "PASSED", "body": payload,
            "input_hashes": {"prompt_plan": sha_obj(prompt_plan(all_cells))},
            "output_hashes": {"curves": sha_obj(payload)}}


def _finish_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["finish_reason"]] = counts.get(row["finish_reason"],
                                                  0) + 1
    return counts


def _reject_exhausted_grid(curve: dict[Any, dict[str, Any]],
                           band: tuple[float, float], status: str,
                           payload: dict[str, Any]) -> None:
    """Reject only when every Wilson interval lies entirely on the same
    inadmissible side of the band (§18.2)."""
    intervals = [tuple(entry["wilson"]) for entry in curve.values()]
    if all(high < band[0] for _low, high in intervals):
        side = "below"
    elif all(low > band[1] for low, _high in intervals):
        side = "above"
    else:
        return
    raise TerminalStatus(status, {
        "criterion": f"every severity interval entirely {side} the band "
                     f"{band}", "side": side, **payload})
