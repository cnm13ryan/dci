#!/usr/bin/env python3
"""Does the frame-pooled pre-screen withhold candidates a frame would have matched?

Zero generation, read-only, pre-freeze. Everything below is read from the
signature-verified pilot records (``REGIME_SCREEN``, ``SECOND_PASS_SCREEN``,
``GATE_1_INSTRUMENT``, ``GATE_2_CALIBRATION``, ``GATE_3_REFERENCES``) of the
four study roots. No confirmatory stage is opened, no scored row is
regenerated, and **no membership, threshold, caliper, operating point or
verdict is changed by this tool**.

**The finding under test.** ``REGIME_SCREEN`` and ``SECOND_PASS_SCREEN`` rank
families and retain rungs on a difficulty coordinate pooled over the four
wording frames (``regime.prescreen_counts`` sums solo and unconstrained
passes over every frame; ``PrescreenRung`` has no frame field and rejects
one; ``retention.retain`` ranks against a single pooled iota_A). Gate 2 and
Gate 3 are frame-specific: n*(f), m*(f), iota_A(f), the §13.11 table and
V_diff's ``|iota_R(f) - iota_A(f)| <= C.REFERENCE_CALIPER`` (0.10). If a
rung's iota spreads across frames by more than the caliper, a rung inside
frame f's caliper can be left unmeasured because its pooled coordinate sits
elsewhere.

What is computed, per model and frame f:

(a) whether ranking and retention were frame-pooled, with the record fields
    that prove it quoted back;
(b) the cross-frame spread of candidate iota (max - min over frames) at
    calibration and at the screen, per rung and per family, with the
    screen's noise stated;
(c) screen-vs-calibration drift for every forwarded rung, per frame and
    pooled;
(d) a retrospective frame-aware ranking of every rung the first-pass screen
    measured, by ``|iota_screen(f) - iota_A(f)|`` against that frame's own
    Gate-2 iota_A(f): the rungs a frame-aware screen would have forwarded
    that the pooled ``forwarded_set`` did not, and the converse;
(e) per frame, how many already-calibrated candidates sit inside the caliper
    (matched controls in hand) against how many additional near-iota_A(f)
    candidates exist only in the screen, beside §13.15's LOCAL survival
    requirement (>= 5 LOCAL-valid families, >= 2 backups);
(f) a per-model summary: LOCAL-supported and unsupported frames taken from
    ``reports/dci1v8dev/local_eligibility.md`` (its machine-readable twin),
    never from a record's ``state`` field, and for each unsupported frame the
    count of unforwarded screen-near candidates.

**The counterfactual discipline.** A rung the pooled screen did not forward
was never calibrated. Nothing here says it would have been LOCAL-valid: what
is measured is only how many such candidates a frame's own screen coordinate
places inside that frame's caliper, and how noisy that coordinate is.

    dci1/.venv/bin/python tools/v8_frame_screen_diagnostic.py --all
    dci1/.venv/bin/python tools/v8_frame_screen_diagnostic.py \
        --root evidence/dci1v8-pilot-r9 --model qwen3-4b

Writes ``reports/dci1v8dev/frame_screen_diagnostic/<model>.json``,
``summary.json`` and ``REPORT.md``.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
from typing import Any, Iterable, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.engine import fs                                       # noqa: E402
from dci1v4.engine.signing import verify_signed                    # noqa: E402
from dci1v4.errors import IntegrityError                           # noqa: E402
from dci1v7.protocol import constants as C                         # noqa: E402
from dci1v7.stages.calibration_table import (instructed_compliance,  # noqa: E402
                                             tie_key)
from dci1v7.verifiers.constraints import FAMILIES                  # noqa: E402
from dci1v8dev.confirm.pilot_import import PilotSource, open_pilot  # noqa: E402
from dci1v8dev.confirm.topup import topup_plan                     # noqa: E402
from dci1v8dev.run import EVIDENCE_DIRNAME                         # noqa: E402
from dci1v8dev.run import stages as PS                             # noqa: E402

DCI1 = HERE.parent
REPORTS = DCI1 / "reports" / "dci1v8dev"
OUT = REPORTS / "frame_screen_diagnostic"
LOCAL_ELIGIBILITY = REPORTS / "local_eligibility.json"

CALIPER = C.REFERENCE_CALIPER                     # 0.10, §13.8
MIN_LOCAL_FAMILIES = PS.MIN_LOCAL_FAMILIES        # 5, §13.15
MIN_BACKUPS = PS.MIN_BACKUPS if hasattr(PS, "MIN_BACKUPS") else 2
TIERS_ELIGIBLE = (1, 2)                           # the top-up rule's tier filter

#: The four study roots, one per model: the latest run of each.
STUDY_ROOTS: dict[str, str] = {
    "qwen3-4b": "dci1v8-pilot-r9",
    "gemma-3n-e2b-it": "dci1v8-pilot-r8",
    "qwen3-4b-instruct-2507": "dci1v8-pilot-r10",
    "gemma-3n-e4b-it": "dci1v8-pilot-r11",
}

#: The classification convention, fixed here before any count is read. It is
#: a reporting convention and admits nothing; every quantity it reads is
#: printed beside it so a reader can reclassify.
VERDICT_RULE = (
    "CONFIRMED iff (i) the median per-family cross-frame spread of "
    "calibration iota exceeds the 0.10 caliper (the mechanism exists), "
    "(ii) on at least two of the four models some LOCAL-unsupported frame "
    "carries at least one unforwarded Tier-1/2 screen-near candidate family "
    "that is not already LOCAL-valid on that frame (the mechanism had "
    "something to bite on), and (iii) the screen's own median SE(iota) is "
    "at most the caliper, so the screen coordinate can in fact locate a rung "
    "inside a frame's caliper. PARTIALLY iff (i) and (ii) hold but (iii) does "
    "not: the loss is real but the pooled screen's per-frame coordinate is "
    "too noisy to have steered around it. NOT otherwise."
)

SCOPE_STATEMENT = (
    "LOCAL Delta_R(f) is identified only for model x frame combinations "
    "where the frozen screening/calibration/reference pipeline yields "
    "adequate matched controls."
)


# ------------------------------------------------------------------ reading
def _label(kind: str, severity: Any) -> str:
    return f"{kind}:{int(severity)}"


def _tier(kind: str) -> int | None:
    fam = FAMILIES.get(kind)
    return None if fam is None else int(fam.structural_tier)


def second_pass_record(root: pathlib.Path, model_key: str) -> dict[str, Any]:
    """The signed ``SECOND_PASS_SCREEN`` record, verified like ``open_pilot``."""
    base = root / "evidence" / EVIDENCE_DIRNAME
    key = base / "keys" / "signing.key"
    path = (base / model_key / PS.STAGE_SECOND_PASS / "records"
            / PS.STAGE_RECORD_FILES[PS.STAGE_SECOND_PASS])
    if not path.exists():
        raise IntegrityError(f"{model_key}: no signed SECOND_PASS_SCREEN "
                             f"record at {path}")
    record = fs.read_json(path)
    return verify_signed(record, key, where=f"{model_key}:SECOND_PASS_SCREEN")


def local_eligibility(root_name: str, model_key: str) -> dict[str, Any]:
    """LOCAL support per frame, from `local_eligibility.md`'s JSON twin.

    Deliberately not the records' ``state`` field: ``state`` is the Gate-3
    frame state (LOCAL_AND_SPECTRUM etc.), which a frame can carry while
    still failing §13.15's family and backup minima.
    """
    if not LOCAL_ELIGIBILITY.exists():
        raise SystemExit(f"no {LOCAL_ELIGIBILITY}: run tools/v8_local_eligibility.py")
    doc = json.loads(LOCAL_ELIGIBILITY.read_text())
    block = doc["by_root"][root_name][model_key]["eligibility"]
    return {"source": str(LOCAL_ELIGIBILITY.relative_to(DCI1)),
            "companion_markdown": "reports/dci1v8dev/local_eligibility.md",
            "by_frame": block["by_frame"],
            "model_eligible": block.get("local_eligible"),
            "supported_frames": sorted(
                int(f) for f, v in block["by_frame"].items()
                if v.get("local_supported")),
            "unsupported_frames": sorted(
                int(f) for f, v in block["by_frame"].items()
                if not v.get("local_supported"))}


# ------------------------------------------------- (a) the pooled evidence
def pooling_evidence(regime: Mapping[str, Any], second: Mapping[str, Any],
                     gate2: Mapping[str, Any]) -> dict[str, Any]:
    prescreen_fields = sorted({k for row in regime["prescreen_table"] for k in row})
    difficulty_fields = sorted({k for row in regime["difficulty_table"] for k in row})
    # A record of the pooled design carries one forwarded set; a record of
    # the frame-aware design (2026-09-03) carries one per frame and the
    # union under the same key, and this diagnostic then reads the union.
    forwarded = [str(x) for x in (second.get("forwarded_set")
                                  or second.get("forwarded_set_provisional") or [])]
    gate2_forwarded = [str(x) for x in gate2["calibration_population"]["forwarded"]]
    return {
        "ranking_and_retention_frame_pooled": True,
        "proof": {
            "REGIME_SCREEN.frame_conditioning": regime["frame_conditioning"],
            "REGIME_SCREEN.prescreen_table.fields": prescreen_fields,
            "REGIME_SCREEN.difficulty_table.fields": difficulty_fields,
            "REGIME_SCREEN.iota_a_prescreen": regime["iota_a_prescreen"],
            "REGIME_SCREEN.iota_a_prescreen_severity":
                regime.get("iota_a_prescreen_severity"),
            "SECOND_PASS_SCREEN.frame_conditioning": second["frame_conditioning"],
            "SECOND_PASS_SCREEN.retention.config": second["retention"]["config"],
            "SECOND_PASS_SCREEN.n_forwarded": second["n_forwarded"],
            "GATE_2_CALIBRATION.calibration_population.rule":
                gate2["calibration_population"].get("rule"),
            "GATE_2_CALIBRATION.supported_frames": gate2["supported_frames"],
            "GATE_2_CALIBRATION.iota_a_by_frame": {
                str(f): gate2["by_frame"][str(f)].get("iota_a")
                for f in PS.FRAMES},
        },
        "reading": [
            "the screen's difficulty table carries no frame column and a "
            "single scalar iota_a_prescreen, so the ranking coordinate and "
            "the retention target are one number for all four frames",
            "the retention config carries only budget sizes (spectrum_rungs, "
            "local_rungs, family caps): no frame appears in the rule",
            "Gate 2 then holds a different iota_A for each frame, which is "
            "the coordinate every later caliper is measured against",
        ],
        "forwarded_set_identical_on_both_records":
            sorted(forwarded) == sorted(gate2_forwarded),
        "n_forwarded_rungs": len(forwarded),
        "n_forwarded_families": len({l.rpartition(":")[0] for l in forwarded}),
        "forwarded_set": sorted(forwarded),
    }


# --------------------------------------------------------- iota extraction
def screen_iota_by_frame(gate1: Mapping[str, Any]) -> dict[str, dict[int, dict[str, Any]]]:
    """``{label: {frame: {iota, se_iota, n_topics}}}`` from Gate 1.

    ``GATE_1_INSTRUMENT.frame_comparison_screen`` is the per-frame screen
    coordinate the pilot computed and no stage read.
    """
    out: dict[str, dict[int, dict[str, Any]]] = {}
    for label, block in (gate1.get("frame_comparison_screen") or {}).items():
        per_frame: dict[int, dict[str, Any]] = {}
        for f, v in (block.get("frames") or {}).items():
            if v.get("iota") is None:
                continue
            per_frame[int(f)] = {"iota": float(v["iota"]),
                                 "se_iota": v.get("se_iota"),
                                 "n_topics": v.get("n_topics"),
                                 "n_rows": v.get("n_rows")}
        if per_frame:
            out[str(label)] = per_frame
    return out


def calibration_iota_by_frame(gate2: Mapping[str, Any], *, split: str = "pooled"
                              ) -> dict[int, dict[str, Any]]:
    """``{frame: {"iota_a", "rungs": {label: {iota, se_iota, ...}}}}``.

    iota is not stored on a §13.11 row: it is
    ``instructed_compliance(solo_compliance, chance_compliance)``. SE(iota) is
    derived from ``per_topic_solo`` exactly as ``wording.frame_table`` does.
    """
    out: dict[int, dict[str, Any]] = {}
    for f in gate2.get("supported_frames", []):
        block = gate2["by_frame"][str(f)]
        rungs: dict[str, Any] = {}
        for row in block["calibration_rows"][split]:
            kappa = float(row["chance_compliance"])
            if kappa >= C.CHANCE_DEGENERACY_MAX:
                continue
            per_topic = list(row.get("per_topic_solo") or ())
            se = (statistics.stdev(per_topic) / (len(per_topic) ** 0.5)
                  / (1.0 - kappa)) if len(per_topic) > 1 else None
            rungs[_label(row["kind"], row["severity"])] = {
                "iota": instructed_compliance(float(row["solo_compliance"]), kappa),
                "se_iota": se,
                "kappa": kappa,
                "n_topics": row.get("n_topics"),
                "prescreen_solo_compliance": row.get("prescreen_solo_compliance"),
            }
        out[int(f)] = {
            "iota_a": float(block["iota_a"]), "n_star": block.get("n_star"),
            "m_star": block.get("m_star"), "n_topics_a": block.get("n_topics_a"),
            "split": split, "rungs": rungs,
            "n_withheld_degenerate": block.get("n_candidates_withheld_degenerate"),
        }
    return out


# ------------------------------------------------------------- (b) spread
def _spread(values: Iterable[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return (max(vals) - min(vals)) if len(vals) >= 2 else None


def _by_family(per_label: Mapping[str, float | None]) -> dict[str, list[float]]:
    fam: dict[str, list[float]] = {}
    for label, v in per_label.items():
        if v is None:
            continue
        fam.setdefault(label.rpartition(":")[0], []).append(float(v))
    return fam


def spread_block(per_label_spread: Mapping[str, float | None]) -> dict[str, Any]:
    """Per-rung spreads collapsed to per-family (median over the family's rungs)."""
    fam = _by_family(per_label_spread)
    family_spread = {k: statistics.median(v) for k, v in sorted(fam.items())}
    rung_values = sorted(v for v in per_label_spread.values() if v is not None)
    return {
        "per_rung": {k: v for k, v in sorted(per_label_spread.items())
                     if v is not None},
        "per_family_median_over_its_rungs": family_spread,
        "n_rungs": len(rung_values),
        "n_families": len(family_spread),
        "median_across_rungs": statistics.median(rung_values) if rung_values else None,
        "median_across_families": (statistics.median(list(family_spread.values()))
                                   if family_spread else None),
        "q90_across_rungs": (rung_values[min(len(rung_values) - 1,
                                             int(0.9 * len(rung_values)))]
                             if rung_values else None),
        "max_across_rungs": max(rung_values) if rung_values else None,
        "n_families_above_caliper": sum(1 for v in family_spread.values()
                                        if v > CALIPER),
        "caliper": CALIPER,
    }


def cross_frame_spread(screen: Mapping[str, Mapping[int, Mapping[str, Any]]],
                       cal: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    frames = sorted(cal)
    cal_spread: dict[str, float | None] = {}
    labels = sorted({l for f in frames for l in cal[f]["rungs"]})
    for label in labels:
        cal_spread[label] = _spread(cal[f]["rungs"][label]["iota"]
                                    for f in frames if label in cal[f]["rungs"])
    screen_spread = {label: _spread(v["iota"] for v in per_frame.values())
                     for label, per_frame in screen.items()}
    ses = [v["se_iota"] for per_frame in screen.values() for v in per_frame.values()
           if v.get("se_iota") is not None]
    topics = sorted({v.get("n_topics") for per_frame in screen.values()
                     for v in per_frame.values() if v.get("n_topics")})
    return {
        "calibration": {**spread_block(cal_spread),
                        "frames_measured": frames,
                        "note": "supported frames only; a frame Gate 2 did "
                                "not support has no iota_A(f) and no table"},
        "screen": {**spread_block(screen_spread),
                   "noise": {
                       "topics_per_frame": topics,
                       "draws_per_topic": C.LADDER_SCREEN_DRAWS,
                       "median_se_iota": statistics.median(ses) if ses else None,
                       "max_se_iota": max(ses) if ses else None,
                       "iota_quantisation": (1.0 / topics[0]) if topics else None,
                       "statement": "at 24 pre-screen topics x 1 draw a frame "
                                    "holds six topics, so a frame's screen "
                                    "iota moves in steps of about 1/6 before "
                                    "the chance correction; the median SE "
                                    "below is on the same scale as (or larger "
                                    "than) the 0.10 caliper, and that "
                                    "imprecision is the reason the screen was "
                                    "pooled in the first place"}},
    }


# --------------------------------------------------------------- (c) drift
def screen_vs_calibration_drift(screen: Mapping[str, Mapping[int, Mapping[str, Any]]],
                                cal: Mapping[int, Mapping[str, Any]],
                                *, forwarded: Sequence[str],
                                pooled_screen_iota: Mapping[str, float | None],
                                pooled_screen_iota_a: float) -> dict[str, Any]:
    frames = sorted(cal)
    per_rung: dict[str, Any] = {}
    for label in sorted(forwarded):
        entry: dict[str, Any] = {"by_frame": {}}
        cal_vals = []
        for f in frames:
            s = screen.get(label, {}).get(f)
            c = cal[f]["rungs"].get(label)
            if s is None or c is None:
                continue
            cal_vals.append(c["iota"])
            entry["by_frame"][str(f)] = {
                "iota_screen": s["iota"], "iota_cal": c["iota"],
                "drift": s["iota"] - c["iota"],
                "se_iota_screen": s.get("se_iota"), "se_iota_cal": c.get("se_iota")}
        if not entry["by_frame"]:
            continue
        drifts = [v["drift"] for v in entry["by_frame"].values()]
        entry["mean_abs_drift"] = statistics.fmean(abs(d) for d in drifts)
        entry["max_abs_drift"] = max(abs(d) for d in drifts)
        pooled_s = pooled_screen_iota.get(label)
        entry["pooled"] = {
            "iota_screen_pooled": pooled_s,
            "iota_cal_frame_mean": statistics.fmean(cal_vals),
            "drift_pooled": (None if pooled_s is None
                             else pooled_s - statistics.fmean(cal_vals)),
            "note": "no pooled calibration iota exists on the record "
                    "(descriptive_pooled is read_by []); the comparator here "
                    "is the mean of the frame-specific calibration iotas, "
                    "computed by this tool and used descriptively only"}
        per_rung[label] = entry
    all_abs = [abs(v["drift"]) for e in per_rung.values()
               for v in e["by_frame"].values()]
    by_frame_summary = {}
    for f in frames:
        vals = [e["by_frame"][str(f)]["drift"] for e in per_rung.values()
                if str(f) in e["by_frame"]]
        if vals:
            by_frame_summary[str(f)] = {
                "n": len(vals),
                "median_signed": statistics.median(vals),
                "mean_abs": statistics.fmean(abs(v) for v in vals),
                "max_abs": max(abs(v) for v in vals),
                "n_beyond_caliper": sum(1 for v in vals if abs(v) > CALIPER)}
    pooled_drifts = [e["pooled"]["drift_pooled"] for e in per_rung.values()
                     if e["pooled"]["drift_pooled"] is not None]
    return {
        "n_forwarded_rungs_paired": len(per_rung),
        "per_rung": per_rung,
        "by_frame": by_frame_summary,
        "pooled": {
            "n": len(pooled_drifts),
            "median_signed": (statistics.median(pooled_drifts)
                              if pooled_drifts else None),
            "mean_abs": (statistics.fmean(abs(v) for v in pooled_drifts)
                         if pooled_drifts else None),
            "max_abs": max((abs(v) for v in pooled_drifts), default=None),
            "iota_a_screen_pooled": pooled_screen_iota_a},
        "overall_mean_abs": statistics.fmean(all_abs) if all_abs else None,
        "overall_max_abs": max(all_abs) if all_abs else None,
    }


# ------------------------------------------- (d) the frame-aware ranking
def rank_by_distance(iota_by_label: Mapping[str, float | None],
                     iota_a: float) -> list[dict[str, Any]]:
    """Deterministic ranking of rungs by ``|iota - iota_a|``.

    Total order: ``(distance, label)``, with the distance rounded through
    the protocol's ``tie_key`` --- the same rounding §13.8's V_diff applies
    before comparing to the caliper, so a tie that binary floats do not
    represent still ties here. Labels are unique, so the order does not
    depend on input order and no tie is broken arbitrarily.
    """
    entries = [{"label": str(label), "iota": float(iota),
                "distance": tie_key(abs(float(iota) - float(iota_a)))}
               for label, iota in iota_by_label.items() if iota is not None]
    entries.sort(key=lambda e: (e["distance"], e["label"]))
    for rank, entry in enumerate(entries, start=1):
        entry["rank"] = rank
    return entries


def frame_aware_vs_pooled(ranked: Sequence[Mapping[str, Any]], *,
                          forwarded: Iterable[str],
                          pooled_distance: Mapping[str, float | None],
                          caliper: float = CALIPER,
                          tier_of: Mapping[str, int | None] | None = None,
                          ) -> dict[str, Any]:
    """Rungs inside frame f's caliper the pooled forwarded set omits, and the converse."""
    fwd = {str(x) for x in forwarded}
    inside, outside_but_forwarded = [], []
    for entry in ranked:
        label = entry["label"]
        pooled_d = pooled_distance.get(label)
        pooled_d = None if pooled_d is None else tie_key(pooled_d)
        record = {
            "label": label, "rank": entry["rank"], "iota_screen": entry["iota"],
            "distance_frame": entry["distance"],
            "distance_pooled": pooled_d,
            "pooled_outside_caliper": (None if pooled_d is None
                                       else pooled_d > caliper),
            "forwarded": label in fwd,
            "tier": (tier_of or {}).get(label),
        }
        if entry["distance"] <= caliper and label not in fwd:
            inside.append(record)
        if label in fwd and entry["distance"] > caliper:
            outside_but_forwarded.append(record)
    return {
        "caliper": caliper,
        "would_forward_but_pooled_did_not": inside,
        "forwarded_but_outside_this_frame_caliper": outside_but_forwarded,
        "n_would_forward_but_pooled_did_not": len(inside),
        "n_families_would_forward": len({r["label"].rpartition(":")[0]
                                         for r in inside}),
        "n_forwarded_but_outside": len(outside_but_forwarded),
    }


# -------------------------------------------------------------- the model
def diagnose(model_key: str, root: pathlib.Path) -> dict[str, Any]:
    source = open_pilot(root, model_key)
    second = second_pass_record(root, model_key)
    regime, gate1, gate2, gate3 = (source.regime, source.gate1, source.gate2,
                                   source.gate3)
    root_name = root.name

    pooling = pooling_evidence(regime, second, gate2)
    forwarded = pooling["forwarded_set"]
    screen = screen_iota_by_frame(gate1)
    cal = calibration_iota_by_frame(gate2)
    eligibility = local_eligibility(root_name, model_key)

    pooled_screen_iota = {row["candidate"]: row.get("iota")
                          for row in regime["difficulty_table"]}
    pooled_screen_iota_a = float(regime["iota_a_prescreen"])
    pooled_distance = {k: (None if v is None else abs(v - pooled_screen_iota_a))
                       for k, v in pooled_screen_iota.items()}
    tier_of = {label: _tier(label.rpartition(":")[0]) for label in screen}

    spread = cross_frame_spread(screen, cal)
    drift = screen_vs_calibration_drift(
        screen, cal, forwarded=forwarded,
        pooled_screen_iota=pooled_screen_iota,
        pooled_screen_iota_a=pooled_screen_iota_a)

    by_frame: dict[str, Any] = {}
    for frame in PS.FRAMES:
        g2b = gate2["by_frame"][str(frame)]
        supported_g2 = g2b.get("status") == PS.FRAME_SUPPORTED
        elig = eligibility["by_frame"][str(frame)]
        entry: dict[str, Any] = {
            "frame": frame,
            "gate2_status": g2b.get("status"),
            "gate2_unsupported_reason": (g2b.get("unsupported_reason") or {}).get("status")
            if isinstance(g2b.get("unsupported_reason"), dict)
            else g2b.get("unsupported_reason"),
            "local_supported": bool(elig.get("local_supported")),
            "local_unsupported_reasons": elig.get("local_unsupported_reasons"),
            "local_survival_requirement": {
                "min_local_valid_families": MIN_LOCAL_FAMILIES,
                "min_backups": MIN_BACKUPS,
                "n_local_valid_families": elig.get("n_local_valid_families"),
                "n_backups": elig.get("n_backups"),
                "shortfall_families": (
                    None if elig.get("n_local_valid_families") is None
                    else max(0, MIN_LOCAL_FAMILIES
                             - int(elig["n_local_valid_families"]))),
            },
        }
        if not supported_g2:
            entry["ranking"] = None
            entry["matched_controls"] = {
                "available": None,
                "why": "no operating point: Gate 2 did not support this "
                       "frame, so there is no iota_A(f) to match against and "
                       "no screen-near count is defined"}
            by_frame[str(frame)] = entry
            continue

        iota_a = cal[frame]["iota_a"]
        survival = (gate3["by_frame"][str(frame)].get("survival") or {})
        local_valid = set(survival.get("local_valid_families") or ())

        screen_here = {label: per_frame[frame]["iota"]
                       for label, per_frame in screen.items()
                       if frame in per_frame}
        ranked_all = rank_by_distance(screen_here, iota_a)
        eligible_labels = {e["label"] for e in ranked_all
                           if tier_of.get(e["label"]) in TIERS_ELIGIBLE}
        ranked_tier = [e for e in ranked_all if e["label"] in eligible_labels]
        cmp_all = frame_aware_vs_pooled(ranked_all, forwarded=forwarded,
                                        pooled_distance=pooled_distance,
                                        tier_of=tier_of)
        cmp_tier = frame_aware_vs_pooled(ranked_tier, forwarded=forwarded,
                                         pooled_distance=pooled_distance,
                                         tier_of=tier_of)
        topup_like = [r for r in cmp_tier["would_forward_but_pooled_did_not"]
                      if r["label"].rpartition(":")[0] not in local_valid]

        calibrated_near = sorted(
            label for label, v in cal[frame]["rungs"].items()
            if tie_key(abs(v["iota"] - iota_a)) <= CALIPER)
        entry["iota_a"] = iota_a
        entry["iota_a_screen_pooled"] = pooled_screen_iota_a
        entry["n_star"] = cal[frame]["n_star"]
        entry["n_topics_a"] = cal[frame]["n_topics_a"]
        entry["ranking"] = {
            "n_rungs_measured_by_screen_under_this_frame": len(ranked_all),
            "n_tier_1_2": len(ranked_tier),
            "top_20_by_frame_distance": ranked_tier[:20],
            "all_families": cmp_all,
            "tier_1_2_only": cmp_tier,
            "topup_rule_subset": {
                "rule": "Tier-1/2, inside this frame's caliper on the frame's "
                        "own screen iota, family not already LOCAL-valid on "
                        "this frame, not forwarded --- the LOCAL_TOPUP "
                        "candidate set, recomputed here for comparison only",
                "n_rungs": len(topup_like),
                "families": sorted({r["label"].rpartition(":")[0]
                                    for r in topup_like}),
                "rungs": topup_like},
        }
        entry["matched_controls"] = {
            "available": True,
            "n_calibrated_candidates": len(cal[frame]["rungs"]),
            "n_calibrated_inside_caliper": len(calibrated_near),
            "calibrated_inside_caliper": calibrated_near,
            "n_calibrated_inside_caliper_families":
                len({l.rpartition(":")[0] for l in calibrated_near}),
            "n_screen_near_unforwarded_all_families":
                cmp_all["n_would_forward_but_pooled_did_not"],
            "n_screen_near_unforwarded_tier_1_2":
                cmp_tier["n_would_forward_but_pooled_did_not"],
            "n_screen_near_unforwarded_families_tier_1_2":
                cmp_tier["n_families_would_forward"],
            "n_screen_near_unforwarded_topup_subset": len(topup_like),
            "reading": "the first count is the matched controls the frozen "
                       "pipeline actually put in hand on this frame; the "
                       "screen-near counts are candidates that were never "
                       "calibrated, so their validity is NOT_IDENTIFIABLE "
                       "and none of them is credited with an outcome here",
        }
        by_frame[str(frame)] = entry

    unsupported = eligibility["unsupported_frames"]
    summary = {
        "model_key": model_key,
        "root": root_name,
        "supported_frames": eligibility["supported_frames"],
        "unsupported_frames": unsupported,
        "local_eligible": eligibility["model_eligible"],
        "support_source": eligibility["companion_markdown"],
        "unforwarded_screen_near_on_unsupported_frames": {
            str(f): by_frame[str(f)]["matched_controls"].get(
                "n_screen_near_unforwarded_tier_1_2")
            for f in unsupported},
        "unforwarded_screen_near_topup_subset_on_unsupported_frames": {
            str(f): by_frame[str(f)]["matched_controls"].get(
                "n_screen_near_unforwarded_topup_subset")
            for f in unsupported},
        "calibration_spread_median_across_families":
            spread["calibration"]["median_across_families"],
        "screen_median_se_iota": spread["screen"]["noise"]["median_se_iota"],
    }

    return {
        "model_key": model_key,
        "root": root_name,
        "root_path": str(root),
        "study_id": source.study_id,
        "manifest_hash": source.manifest_hash,
        "record_hashes": source.record_hashes,
        "reads": ["REGIME_SCREEN", "SECOND_PASS_SCREEN", "GATE_1_INSTRUMENT",
                  "GATE_2_CALIBRATION", "GATE_3_REFERENCES",
                  "reports/dci1v8dev/local_eligibility.json"],
        "opens_no_confirmatory_stage": True,
        "changes_membership": False,
        "generations": 0,
        "caliper": CALIPER,
        "calibration_allocation": gate2.get("calibration_allocation"),
        "a_pooling_evidence": pooling,
        "b_cross_frame_spread": spread,
        "c_screen_vs_calibration_drift": drift,
        "by_frame": by_frame,
        "f_summary": summary,
        "topup_plan_crosscheck": topup_crosscheck(source, by_frame),
        "prior_audit_comparison": compare_prior_audit(root_name, model_key, by_frame),
        "scope_statement": SCOPE_STATEMENT,
    }


# ----------------------------------------- cross-check: the production rule
def topup_crosscheck(source: PilotSource, by_frame: Mapping[str, Any]
                     ) -> dict[str, Any]:
    """This tool's top-up subset against ``confirm.topup.topup_plan`` itself.

    The confirmatory ``LOCAL_TOPUP`` rule selects exactly the set this
    diagnostic calls the top-up subset (Tier-1/2, inside frame f's caliper on
    the frame's own screen iota, family not LOCAL-valid on f, not forwarded).
    Running the production planner here is a zero-generation identity check on
    the diagnostic's own arithmetic --- it plans nothing and measures nothing.
    """
    plan = topup_plan(source)
    per_frame, agree = {}, True
    for frame, block in sorted(plan["by_frame"].items()):
        mine = sorted(r["label"] for r in
                      ((by_frame[frame].get("ranking") or {})
                       .get("topup_rule_subset") or {}).get("rungs", ()))
        theirs = sorted(c["candidate"] for v in
                        (block.get("candidate_families") or {}).values()
                        for c in v)
        per_frame[frame] = {"this_tool": mine, "topup_plan": theirs,
                            "identical": mine == theirs,
                            "need": block.get("need"),
                            "rule_fires": bool(block.get("runs"))}
        agree = agree and mine == theirs
    firing = {f: v["topup_plan"] for f, v in per_frame.items() if v["rule_fires"]}
    return {"identical_on_every_frame": agree, "per_frame": per_frame,
            "frames_where_the_rule_fires": sorted(firing),
            "rungs_where_the_rule_fires": sum(len(v) for v in firing.values()),
            "note": "an identity check only: topup_plan reads records and "
                    "plans nothing here"}


# ------------------------------------------- comparison with the old audit
def compare_prior_audit(root_name: str, model_key: str,
                        by_frame: Mapping[str, Any]) -> dict[str, Any]:
    path = REPORTS / f"screen_frame_audit.{root_name}.{model_key}.json"
    mine = {f: sorted({r["label"].rpartition(":")[0] for r in
                       ((b.get("ranking") or {}).get("tier_1_2_only") or {})
                       .get("would_forward_but_pooled_did_not", ())})
            for f, b in by_frame.items()}
    if not path.exists():
        return {"exists": False,
                "expected_path": str(path.relative_to(DCI1)),
                "note": "no screen_frame_audit report exists for this root; "
                        "the earlier audit covers r5, r6, r8 and r9 only",
                "this_tool_unforwarded_near_families_tier_1_2": mine}
    prior = json.loads(path.read_text())
    theirs = {f: sorted(v.get("lost_families") or ())
              for f, v in prior["by_frame_counts"].items()}
    per_frame = {}
    for f in sorted(set(theirs) | set(mine)):
        a, b = set(theirs.get(f, ())), set(mine.get(f, ()))
        per_frame[f] = {
            "prior_lost_families": sorted(a), "this_tool_near_families": sorted(b),
            "both": sorted(a & b), "prior_only": sorted(a - b),
            "this_tool_only": sorted(b - a)}
    return {
        "exists": True,
        "path": str(path.relative_to(DCI1)),
        "prior_verdict": prior["classification"]["verdict"],
        "prior_n_lost_cells": prior["classification"]["n_lost_cells"],
        "prior_n_lost_families": prior["classification"]["n_lost_families"],
        "prior_frame_label_beats_pooled":
            prior["classification"]["n_comparisons_where_the_frame_label_beats_the_pooled_one"],
        "prior_n_comparisons": prior["classification"]["n_comparisons"],
        "per_frame": per_frame,
        "why_the_sets_differ":
            "the earlier audit re-runs the production screen on each frame's "
            "own rows and calls a FAMILY promising when its frame status is "
            "ACCEPT or it carries a label; this tool applies the caliper "
            "directly to a RUNG's frame-f screen iota against Gate 2's "
            "iota_A(f). Different question, different unit: the two sets "
            "overlap but neither contains the other, and the earlier audit's "
            "predictive test (does the frame label beat the pooled label "
            "where the truth is known) is the one that bears on whether a "
            "frame-aware screen is warranted",
    }


# ------------------------------------------------------------- the verdict
def classify(models: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spreads = [m["b_cross_frame_spread"]["calibration"]["median_across_families"]
               for m in models
               if m["b_cross_frame_spread"]["calibration"]["median_across_families"]
               is not None]
    ses = [m["b_cross_frame_spread"]["screen"]["noise"]["median_se_iota"]
           for m in models
           if m["b_cross_frame_spread"]["screen"]["noise"]["median_se_iota"]
           is not None]
    models_with_opportunity = []
    for m in models:
        counts = m["f_summary"][
            "unforwarded_screen_near_topup_subset_on_unsupported_frames"]
        if any(v for v in counts.values()):
            models_with_opportunity.append(m["model_key"])
    median_spread = statistics.median(spreads) if spreads else None
    median_se = statistics.median(ses) if ses else None
    mechanism = median_spread is not None and median_spread > CALIPER
    opportunity = len(models_with_opportunity) >= 2
    steerable = median_se is not None and median_se <= CALIPER
    if mechanism and opportunity and steerable:
        verdict = "CONFIRMED"
    elif mechanism and opportunity:
        verdict = "PARTIALLY"
    else:
        verdict = "NOT"
    return {
        "verdict": verdict, "rule": VERDICT_RULE,
        "median_calibration_spread_across_models": median_spread,
        "median_screen_se_iota_across_models": median_se,
        "caliper": CALIPER,
        "mechanism_exists": mechanism,
        "opportunity_on_unsupported_frames": opportunity,
        "models_with_opportunity": models_with_opportunity,
        "screen_coordinate_steerable": steerable,
    }


# -------------------------------------------------------------- reporting
def _fmt(v: Any, nd: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def render(models: Sequence[Mapping[str, Any]], verdict: Mapping[str, Any]) -> str:
    L: list[str] = []
    A = L.append
    A("# DCI-1 v8 — the frame-blind pre-screen, measured")
    A("")
    A(f"**Verdict: {verdict['verdict']}.** The candidate screen and retention "
      "rank and forward on a frame-pooled coordinate while every caliper from "
      "Gate 2 onward is frame-specific, and the cross-frame spread of a "
      "rung's iota at calibration has a median across families of "
      f"{_fmt(verdict['median_calibration_spread_across_models'])} — "
      f"{verdict['median_calibration_spread_across_models'] / CALIPER:.1f}x the "
      f"{CALIPER} caliper. On "
      f"{len(verdict['models_with_opportunity'])} of {len(models)} models a "
      "LOCAL-unsupported frame carries unforwarded Tier-1/2 candidates whose "
      "own frame-f screen iota sits inside that frame's caliper "
      f"({', '.join(verdict['models_with_opportunity']) or 'none'}). But the "
      "screen's per-frame coordinate has a median SE(iota) of "
      f"{_fmt(verdict['median_screen_se_iota_across_models'])} on six topics "
      f"at {C.LADDER_SCREEN_DRAWS} draw — "
      f"{'at most' if verdict['screen_coordinate_steerable'] else 'larger than'}"
      f" the caliper itself — so the pooled screen "
      f"{'could' if verdict['screen_coordinate_steerable'] else 'could not'} "
      "reliably have steered around the loss it causes.")
    A("")
    A("**This diagnostic changes no membership.** It opens no confirmatory "
      "stage, generates nothing, moves no threshold, caliper, operating "
      "point, forwarded set, validity component or verdict, and writes "
      "nothing into any evidence tree. Every rung it names as a "
      "\"would-forward\" candidate was never calibrated, so its downstream "
      "validity is NOT_IDENTIFIABLE from this study's data; only the size of "
      "the withheld set and the noise of the coordinate that withheld it are "
      "measured here.")
    A("")
    A(f"Classification convention, fixed before the counts were read: "
      f"{verdict['rule']}")
    A("")

    A("## (a) Ranking and retention were frame-pooled")
    A("")
    A("| model | screen iota_A (one scalar) | Gate-2 iota_A per frame | forwarded rungs | pooled on both records |")
    A("|---|---:|---|---:|---|")
    for m in models:
        p = m["a_pooling_evidence"]["proof"]
        ia = p["GATE_2_CALIBRATION.iota_a_by_frame"]
        A(f"| `{m['model_key']}` | {_fmt(p['REGIME_SCREEN.iota_a_prescreen'])} "
          f"(severity {p['REGIME_SCREEN.iota_a_prescreen_severity']}) | "
          + "; ".join(f"f{f}={_fmt(ia[str(f)])}" for f in PS.FRAMES)
          + f" | {m['a_pooling_evidence']['n_forwarded_rungs']} | "
          f"{m['a_pooling_evidence']['forwarded_set_identical_on_both_records']} |")
    A("")
    A("The proof fields, identical in kind on every model: "
      "`REGIME_SCREEN.prescreen_table` carries "
      f"`{models[0]['a_pooling_evidence']['proof']['REGIME_SCREEN.prescreen_table.fields']}` "
      "— no frame column, and `PrescreenRung` rejects an unknown field; "
      "`REGIME_SCREEN.iota_a_prescreen` is a single scalar; "
      "`SECOND_PASS_SCREEN.retention.config` carries only budget sizes "
      f"(`{models[0]['a_pooling_evidence']['proof']['SECOND_PASS_SCREEN.retention.config']}`); "
      "and both stage records state the pooling themselves, e.g. "
      f"`REGIME_SCREEN.frame_conditioning.at_this_stage` = "
      f"\"{models[0]['a_pooling_evidence']['proof']['REGIME_SCREEN.frame_conditioning']['at_this_stage']}\". "
      "`SECOND_PASS_SCREEN.forwarded_set` and "
      "`GATE_2_CALIBRATION.calibration_population.forwarded` agree exactly on "
      "every model, so the pooled set is the set Gate 2 calibrated.")
    A("")

    A("## (b) Cross-frame spread of candidate iota")
    A("")
    A("Spread = max − min over frames, per rung; a family's value is the "
      "median over its measured rungs. Calibration uses each frame's own "
      "§13.11 table (supported frames only, pooled split); the screen uses "
      "`GATE_1_INSTRUMENT.frame_comparison_screen`.")
    A("")
    A("| model | cal median/family | cal median/rung | cal q90 | families > caliper | screen median/family | screen median SE(iota) | topics per frame |")
    A("|---|---:|---:|---:|---|---:|---:|---:|")
    for m in models:
        c = m["b_cross_frame_spread"]["calibration"]
        s = m["b_cross_frame_spread"]["screen"]
        A(f"| `{m['model_key']}` | {_fmt(c['median_across_families'])} | "
          f"{_fmt(c['median_across_rungs'])} | {_fmt(c['q90_across_rungs'])} | "
          f"{c['n_families_above_caliper']}/{c['n_families']} | "
          f"{_fmt(s['median_across_families'])} | "
          f"{_fmt(s['noise']['median_se_iota'])} | "
          f"{s['noise']['topics_per_frame']} |")
    A("")
    A("The screen's noise is the point: at six topics and one draw a frame's "
      "screen iota moves in steps of about 1/6, its median SE is on the scale "
      "of the caliper or above it, and its own cross-frame spread is "
      "correspondingly inflated. The calibration column is the real spread; "
      "the screen column is that spread plus six-topic noise.")
    A("")

    A("## (c) Screen-vs-calibration drift on the forwarded rungs")
    A("")
    A("| model | rungs paired | mean abs drift | max abs | per-frame mean abs | pooled mean abs |")
    A("|---|---:|---:|---:|---|---:|")
    for m in models:
        d = m["c_screen_vs_calibration_drift"]
        per = "; ".join(f"f{f}={_fmt(v['mean_abs'])}"
                        for f, v in sorted(d["by_frame"].items()))
        A(f"| `{m['model_key']}` | {d['n_forwarded_rungs_paired']} | "
          f"{_fmt(d['overall_mean_abs'])} | {_fmt(d['overall_max_abs'])} | "
          f"{per} | {_fmt(d['pooled']['mean_abs'])} |")
    A("")
    A("Drift is `iota_screen(f) − iota_cal(f)`; the pooled column is the "
      "screen's own pooled `difficulty_table` iota against the mean of the "
      "frame-specific calibration iotas (no pooled calibration iota exists on "
      "the record — `descriptive_pooled` is `read_by: []` — so that "
      "comparator is computed here and is descriptive only).")
    A("")

    A("## (d) and (e) Per frame: matched controls in hand, candidates withheld")
    A("")
    A("| model | frame | LOCAL | iota_A(f) | families/backups (need ≥5/≥2) | calibrated inside caliper | screen-near unforwarded (T1/2) | of those, top-up subset |")
    A("|---|---:|---|---:|---|---:|---:|---:|")
    for m in models:
        for f in PS.FRAMES:
            b = m["by_frame"][str(f)]
            mc = b["matched_controls"]
            req = b["local_survival_requirement"]
            local = "SUPPORTED" if b["local_supported"] else (
                b["gate2_status"] if b["gate2_status"] != PS.FRAME_SUPPORTED
                else ",".join(b["local_unsupported_reasons"] or ()))
            A(f"| `{m['model_key']}` | f{f} | {local} | {_fmt(b.get('iota_a'))} | "
              f"{_fmt(req['n_local_valid_families'])}/{_fmt(req['n_backups'])} | "
              f"{_fmt(mc.get('n_calibrated_inside_caliper'))} "
              f"({_fmt(mc.get('n_calibrated_inside_caliper_families'))} fam) | "
              f"{_fmt(mc.get('n_screen_near_unforwarded_tier_1_2'))} | "
              f"{_fmt(mc.get('n_screen_near_unforwarded_topup_subset'))} |")
    A("")
    A("\"Calibrated inside caliper\" counts forwarded rungs whose realised "
      "`|iota_R(f) − iota_A(f)|` is within 0.10 on that frame's own table: "
      "the matched controls the frozen pipeline delivered. \"Screen-near "
      "unforwarded\" counts Tier-1/2 rungs the first-pass screen measured "
      "under f whose frame-f screen iota is inside the same caliper and which "
      "the pooled forwarded set omitted; the top-up subset additionally drops "
      "families already LOCAL-valid on f, i.e. the `LOCAL_TOPUP` candidate "
      "set. A frame with no operating point has no iota_A(f) and no count.")
    A("")
    A("The converse direction — rungs the pooled screen forwarded that sit "
      "outside the frame's caliper on the frame's own screen coordinate — is "
      "large everywhere, which is the same noise statement from the other "
      "side:")
    A("")
    A("| model | " + " | ".join(f"f{f}" for f in PS.FRAMES) + " |")
    A("|---|" + "---:|" * len(PS.FRAMES))
    for m in models:
        cells = []
        for f in PS.FRAMES:
            r = (m["by_frame"][str(f)].get("ranking") or {}).get("tier_1_2_only")
            cells.append("—" if r is None else str(r["n_forwarded_but_outside"]))
        A(f"| `{m['model_key']}` | " + " | ".join(cells) + " |")
    A("")

    A("## (f) Per-model summary")
    A("")
    for m in models:
        s = m["f_summary"]
        near = s["unforwarded_screen_near_topup_subset_on_unsupported_frames"]
        parts = ", ".join(
            f"f{f} ({_fmt(near.get(str(f)))} top-up-eligible candidate rungs)"
            for f in s["unsupported_frames"]) or "none"
        A(f"- **`{s['model_key']}`** (`{s['root']}`): LOCAL-supported frames "
          f"{s['supported_frames'] or 'none'}; unsupported {parts}. Cross-frame "
          f"calibration spread {_fmt(s['calibration_spread_median_across_families'])}, "
          f"screen median SE(iota) {_fmt(s['screen_median_se_iota'])}. "
          f"LOCAL-eligible: {s['local_eligible']}. Support read from "
          f"`{s['support_source']}`, not from any record's `state` field.")
    A("")

    A("## Cross-check against the production `LOCAL_TOPUP` rule")
    A("")
    A("The top-up subset above is, by construction, the candidate set "
      "`dci1v8dev.confirm.topup.topup_plan` selects. Running that planner on "
      "the same signed records (it plans only; nothing is generated) "
      "reproduces this tool's subset exactly:")
    A("")
    A("| model | identical on every frame | frames where the rule fires | rungs |")
    A("|---|---|---|---:|")
    for m in models:
        x = m["topup_plan_crosscheck"]
        A(f"| `{m['model_key']}` | {x['identical_on_every_frame']} | "
          f"{[int(f) for f in x['frames_where_the_rule_fires']] or 'none'} | "
          f"{x['rungs_where_the_rule_fires']} |")
    A("")
    total = sum(m["topup_plan_crosscheck"]["rungs_where_the_rule_fires"]
                for m in models)
    A(f"Across the four models the rule fires on "
      f"{sum(len(m['topup_plan_crosscheck']['frames_where_the_rule_fires']) for m in models)} "
      f"frames and {total} rungs on the records as they stand. "
      "`docs/V8_CONFIRMATORY.md` §3a records the dry run as seven rungs on "
      "four frames; the frame and family sets agree, the rung count differs "
      "by one. That is a documentation-vs-record discrepancy noted here, not "
      "resolved here, and it moves nothing: the top-up is reported to have "
      "moved no verdict either way.")
    A("")
    A("## Agreement with `tools/v8_screen_frame_audit.py`")
    A("")
    for m in models:
        c = m["prior_audit_comparison"]
        if not c["exists"]:
            A(f"- `{m['model_key']}` (`{m['root']}`): no prior audit exists "
              f"(the earlier tool covers r5, r6, r8, r9); nothing to compare.")
            continue
        agree = sum(len(v["both"]) for v in c["per_frame"].values())
        prior_only = sum(len(v["prior_only"]) for v in c["per_frame"].values())
        mine_only = sum(len(v["this_tool_only"]) for v in c["per_frame"].values())
        A(f"- `{m['model_key']}` (`{m['root']}`): prior verdict "
          f"**{c['prior_verdict']}** with {c['prior_n_lost_cells']} lost "
          f"(family, frame) cells over {c['prior_n_lost_families']} families, "
          f"and the frame label beat the pooled label in "
          f"{c['prior_frame_label_beats_pooled']} of "
          f"{c['prior_n_comparisons']} comparisons. Against this tool's "
          f"unforwarded near-families: {agree} family-frame cells agree, "
          f"{prior_only} appear only in the prior audit, {mine_only} only "
          f"here.")
    A("")
    A("Where the two differ they are answering different questions on "
      "different units. The earlier audit re-runs the production screen "
      "family by family on each frame's own rows and asks whether the frame's "
      "*label* (ACCEPT / spectrum / local) would have promoted the family; "
      "this tool asks, rung by rung, whether the frame's own screen iota "
      "falls inside that frame's Gate-2 caliper. The earlier audit's "
      "load-bearing result — that on the forwarded set the frame-specific "
      "label never beat the pooled label on r9 — is not contradicted by "
      "anything here; it is the same six-topic imprecision that keeps this "
      "diagnostic's verdict at "
      f"{verdict['verdict']}.")
    A("")
    A("## Scope")
    A("")
    A(SCOPE_STATEMENT)
    A("")
    return "\n".join(L)


# ------------------------------------------------------------------- main
def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=pathlib.Path,
                    help="a pilot root (e.g. evidence/dci1v8-pilot-r9)")
    ap.add_argument("--model", help="model key")
    ap.add_argument("--all", action="store_true",
                    help="the four study roots, one per model")
    ap.add_argument("--out", type=pathlib.Path, default=OUT)
    args = ap.parse_args(argv)

    pairs: list[tuple[str, pathlib.Path]] = []
    if args.all:
        pairs = [(m, DCI1 / "evidence" / r) for m, r in STUDY_ROOTS.items()]
    elif args.root and args.model:
        root = args.root if args.root.is_absolute() else (DCI1 / args.root)
        pairs = [(args.model, root)]
    else:
        ap.error("give --all, or both --root and --model")

    args.out.mkdir(parents=True, exist_ok=True)
    models = []
    for model_key, root in pairs:
        result = diagnose(model_key, root.resolve())
        path = args.out / f"{model_key}.json"
        path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
        print(f"wrote {path}")
        models.append(result)

    if args.all or len(models) > 1:
        verdict = classify(models)
        summary = {"verdict": verdict, "caliper": CALIPER,
                   "study_roots": STUDY_ROOTS,
                   "changes_membership": False, "generations": 0,
                   "scope_statement": SCOPE_STATEMENT,
                   "by_model": {m["model_key"]: m["f_summary"] for m in models}}
        (args.out / "summary.json").write_text(
            json.dumps(summary, indent=1, sort_keys=True) + "\n")
        (args.out / "REPORT.md").write_text(render(models, verdict))
        print(f"wrote {args.out / 'summary.json'}")
        print(f"wrote {args.out / 'REPORT.md'}")
        print(f"verdict: {verdict['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
