#!/usr/bin/env python3
"""Counterfactual replay of the pre-screen retention policies on the stored,
unprotected pre-freeze pilot evidence: legacy pooled, legacy + LOCAL_TOPUP,
and the frame-aware policy against two targets.

Zero generation, read-only. Reads the signed pilot records (``REGIME_SCREEN``,
``SECOND_PASS_SCREEN``, ``GATE_1_INSTRUMENT``, ``GATE_2_CALIBRATION``,
``GATE_3_REFERENCES``) and the screen's scored rows (loads 0 and 1) of the
four study roots, and the signed ``LOCAL_TOPUP`` record of the frozen
confirmatory root (a pre-freeze stage). Opens no protected stage: no
``CONFIRMATORY_GENERATION``, ``CONFIRMATORY_ANALYSIS`` or ``FINAL_REPORT``
directory is read, and the tool refuses a path under one.

**Systems compared, per model x frame.**

1. ``legacy`` --- the frame-pooled screen and retention the pilot ran
   (reproduced from the recorded counts through ``policy.LegacyPooledPolicy``
   and asserted equal to the signed forwarded set);
2. ``legacy_topup`` --- (1) plus the rungs the confirmatory ``LOCAL_TOPUP``
   rule added on the frames where it fired, with the re-verdict that
   record carries;
3. ``fa_proxy`` --- ``policy.FrameAwarePolicy`` on each frame's own screen
   evidence (the frame's share of the same rows: six topics per frame at
   round 0, plus every recorded batch absorbed on the frame's own blocks),
   ranked against the frame's own screen-proxy iota_A(f);
4. ``fa_cal`` --- the same evidence ranked against Gate 2's own iota_A(f)
   (``screen.coordinate_target`` at the coordinate's topic-level SE), the
   target every later caliper is measured against.

**The counterfactual discipline.** A rung the pilot did not calibrate has
no downstream verdict: it is ``NOT_IDENTIFIABLE`` and is never credited.
What *is* measured with realised outcomes is the forwarded set the pilot
calibrated under every frame: on those rungs each policy's retained subset
is scored against the frame's realised Gate-3 LOCAL / SPECTRUM verdicts,
and Gate 3 is re-run by the pilot's own kernel on the retained subset alone
(the frame's table restricted to it) to give each policy's *downstream
identification* --- core, LOCAL-valid families, backups, coverage --- as it
would have stood had only that subset been calibrated. Rungs a policy would
forward beyond the calibrated set are counted, and their standing is
reported as not identifiable.

Writes ``prescreen_counterfactual.csv`` (one row per model x frame x
candidate rung), ``counterfactual.<model>.json``, ``summary.json`` and the
tables ``prescreen_feasibility_tables.md`` under
``reports/dci1v8dev/frame_aware_prescreen/`` (the reading of the tables is
``prescreen_feasibility.md``, authored beside them).

    dci1/.venv/bin/python tools/v8_prescreen_counterfactual.py --all [--jobs 4]
    dci1/.venv/bin/python tools/v8_prescreen_counterfactual.py \\
        --root evidence/dci1v8-pilot-r12 --model gemma-3n-e2b-it
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import pathlib
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.engine import fs                                       # noqa: E402
from dci1v4.engine.signing import verify_signed                    # noqa: E402
from dci1v4.errors import IntegrityError, ProtocolError            # noqa: E402
from dci1v7.protocol import constants as C                         # noqa: E402
from dci1v7.stages.calibration_table import (instructed_compliance,  # noqa: E402
                                             tie_key)
from dci1v7.verifiers.constraints import FAMILIES, Constraint      # noqa: E402
from dci1v8dev import rules as R                                   # noqa: E402
from dci1v8dev.confirm.pilot_import import PilotSource, open_pilot  # noqa: E402
from dci1v8dev.prescreen.evidence import (FrameEvidence, ScreenEvidence,  # noqa: E402
                                          evidence_from_rows)
from dci1v8dev.prescreen.policy import (FrameAwarePolicy,           # noqa: E402
                                        LegacyPooledPolicy)
from dci1v8dev.prescreen.rescreen import RescreenConfig, apply_batch, run_rescreen  # noqa: E402
from dci1v8dev.prescreen.retention import RetentionConfig          # noqa: E402
from dci1v8dev.prescreen.screen import (ScreenConfig, coordinate_target,  # noqa: E402
                                        screen_families)
from dci1v8dev.run import EVIDENCE_DIRNAME                         # noqa: E402
from dci1v8dev.run import eligibility as EL                        # noqa: E402
from dci1v8dev.run import references as REF                        # noqa: E402
from dci1v8dev.run import stages as PS                             # noqa: E402
from dci1v8dev.run.execute import frame_of_block                   # noqa: E402
from dci1v8dev.run.regime import jsonable, prescreen_counts, prescreen_input  # noqa: E402

DCI1 = HERE.parent
OUT = DCI1 / "reports" / "dci1v8dev" / "frame_aware_prescreen"
PROTECTED = ("CONFIRMATORY_GENERATION", "CONFIRMATORY_ANALYSIS", "FINAL_REPORT")
CALIPER = C.REFERENCE_CALIPER

#: The four study roots bound by the frozen confirmatory manifest
#: (docs/DCI1_preregistration_v8.md, Appendix B), and the confirmatory root
#: whose pre-freeze LOCAL_TOPUP record supplies system 2.
STUDY_ROOTS: dict[str, str] = {
    "qwen3-4b": "dci1v8-pilot-r9",
    "qwen3-4b-instruct-2507": "dci1v8-pilot-r10",
    "gemma-3n-e2b-it": "dci1v8-pilot-r12",
    "gemma-3n-e4b-it": "dci1v8-pilot-r13",
}
CONFIRM_ROOT = "dci1v8-confirm-r2"
SYSTEMS = ("legacy", "legacy_topup", "fa_proxy", "fa_cal")
TIERS_ELIGIBLE = (1, 2)
#: Topic resamples for the retention-stability measurement.
STABILITY_RESAMPLES = 20


# ------------------------------------------------------------------ reading
def _assert_unprotected(path: pathlib.Path) -> pathlib.Path:
    if any(p in path.parts for p in PROTECTED):
        raise SystemExit(f"refusing a protected path: {path}")
    return path


def second_pass_record(root: pathlib.Path, model_key: str) -> dict[str, Any]:
    base = root / "evidence" / EVIDENCE_DIRNAME
    key = base / "keys" / "signing.key"
    path = _assert_unprotected(
        base / model_key / PS.STAGE_SECOND_PASS / "records"
        / PS.STAGE_RECORD_FILES[PS.STAGE_SECOND_PASS])
    if not path.exists():
        raise IntegrityError(f"{model_key}: no signed SECOND_PASS_SCREEN at {path}")
    return verify_signed(fs.read_json(path), key,
                         where=f"{model_key}:SECOND_PASS_SCREEN")


def topup_record(confirm_root: pathlib.Path, model_key: str) -> dict[str, Any] | None:
    """The signed LOCAL_TOPUP record of the confirmatory root (pre-freeze;
    unprotected), or None when the root holds none for this model."""
    base = confirm_root / "evidence" / EVIDENCE_DIRNAME
    key = base / "keys" / "signing.key"
    stage_dir = base / model_key / "LOCAL_TOPUP" / "records"
    if not stage_dir.exists():
        return None
    files = sorted(p for p in stage_dir.glob("*.json"))
    if not files:
        return None
    path = _assert_unprotected(files[0])
    return verify_signed(fs.read_json(path), key, where=f"{model_key}:LOCAL_TOPUP")


def scored_rows(model_dir: pathlib.Path, stage: str, run: str
                ) -> list[dict[str, Any]]:
    path = _assert_unprotected(model_dir / stage / "backend_runs" / run / "scored.jsonl")
    if not path.exists():
        raise IntegrityError(f"no scored rows at {path}")
    rows = [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]
    for row in rows:
        if len([s for s in row["scores"] if s.get("present")]) > 1:
            raise ProtocolError(f"{row['row_id']}: a composed row was read")
    return rows


def rungs_of(counts: Sequence[Mapping[str, Any]]) -> list[Constraint]:
    return [Constraint(r["kind"], int(r["severity"]), reserve=bool(r.get("reserve")))
            for r in counts]


def _screen_config(cfg: Mapping[str, Any]) -> ScreenConfig:
    return ScreenConfig(draws=cfg["draws"], base_seed=cfg["base_seed"],
                        icc=cfg["icc"], accept=cfg["accept"],
                        reject=cfg["reject"], local_accept=cfg["local_accept"],
                        spectrum_event=cfg["spectrum_event"],
                        chance_max=cfg["chance_max"], lift_min=cfg["lift_min"],
                        shrinkage=cfg["shrinkage"])


def _label(kind: str, q: Any) -> str:
    return f"{kind}:{int(q)}"


# ----------------------------------------------------------- the evidence
def legacy_final_screen(second: Mapping[str, Any], regime: Mapping[str, Any]
                        ) -> dict[str, Any]:
    """The legacy second pass replayed from the recorded batch counts through
    the production loop (the recorded batches must be what the loop plans)."""
    table, a_grid = prescreen_input(regime["prescreen_table"])
    batches = {int(k): v for k, v in second["batch_counts"].items()}
    recorded = {b["index"]: b for b in second["batches"]}

    def measure(batch):
        rec = recorded[batch.index]
        planned = sorted({_label(k, q) for k, fam in batch.families.items()
                          for q in list(fam["severities"]) + list(fam["reserve_picks"])}
                         | ({_label("A", q) for q in C.TARGET_GRID} if batch.a_grid
                            else set()))
        if planned != sorted(rec["rungs"]):
            raise ProtocolError(f"batch {batch.index}: the loop planned "
                                f"{len(planned)} rungs and the record holds "
                                f"{len(rec['rungs'])}; the legacy path moved")
        return prescreen_input(batches[batch.index])

    rc = second["rescreen_config"]
    result = run_rescreen(
        table, a_grid, screen_config=_screen_config(second["screen"]["config"]),
        config=RescreenConfig(max_batches=rc["max_batches"], layout=rc["layout"],
                              batch_topics=rc["batch_topics"],
                              batch_draws=rc["batch_draws"],
                              reserve_picks_per_batch=rc["reserve_picks_per_batch"],
                              include_a_grid=rc["include_a_grid"],
                              final_accept_at=rc["final_accept_at"]),
        measure=measure)
    return result


def frame_evidence_final(ladder_rows: Sequence[Mapping[str, Any]],
                         batch_rows: Mapping[int, Sequence[Mapping[str, Any]]],
                         regime: Mapping[str, Any], second: Mapping[str, Any]
                         ) -> tuple[ScreenEvidence, ScreenEvidence]:
    """Round-0 evidence per frame, and the final evidence with every
    recorded batch absorbed on each frame's own blocks (the union-batch
    semantics of the frame-aware loop: a batch is data for every frame)."""
    rungs = rungs_of(regime["prescreen_table"])
    round0 = evidence_from_rows(ladder_rows, rungs,
                                provenance={"stage": "REGIME_SCREEN"})
    by_frame: dict[int, FrameEvidence] = {}
    for f, e in round0.by_frame.items():
        table, grid = list(e.table), list(e.a_grid)
        for index in sorted(batch_rows):
            counts = second["batch_counts"][str(index)]
            b_rungs = rungs_of(counts)
            frame_rows = [r for r in batch_rows[index] if frame_of_block(r) == f]
            if not frame_rows:
                continue
            per = prescreen_counts(frame_rows, b_rungs)
            for row in per:
                row["reserve"] = (row["kind"] not in ("A", "B")
                                  and row["severity"] not in FAMILIES[row["kind"]].ladder)
            new_rungs, new_a = prescreen_input(per)
            table, grid = apply_batch(table, grid, new_rungs, new_a, layout="topics")
        by_frame[f] = e.replaced(table, grid)
    final = ScreenEvidence(by_frame=by_frame, pooled=round0.pooled,
                           provenance={"stage": "SECOND_PASS_SCREEN",
                                       "batches_absorbed": sorted(batch_rows),
                                       "layout": "topics"})
    return round0, final


def calibration_targets(gate2: Mapping[str, Any], *, draws: int, seed: int
                        ) -> dict[int, dict[str, Any]]:
    """Gate 2's iota_A(f) with its topic-level SE, per supported frame."""
    out: dict[int, dict[str, Any]] = {}
    for w in gate2["supported_frames"]:
        f2 = gate2["by_frame"][str(w)]
        per_topic = []
        for split, vec in (f2.get("a_per_topic_by_split") or {}).get("per_topic", {}).items():
            per_topic += list(vec)
        kappa = float(f2["kappa_a"])
        if len(per_topic) > 1 and kappa < C.CHANCE_DEGENERACY_MAX:
            se = statistics.stdev(per_topic) / math.sqrt(len(per_topic)) / (1.0 - kappa)
        else:
            se = 0.0
        out[int(w)] = coordinate_target(float(f2["iota_a"]), se,
                                        n_star=int(f2["n_star"]), draws=draws,
                                        seed=seed, basis=f"gate2:frame{w}")
        out[int(w)]["se_iota_a"] = se
        out[int(w)]["n_topics_a"] = len(per_topic)
    return out


# ------------------------------------------------------- downstream re-verdict
def restricted_gate3(gate2: Mapping[str, Any], frame: int, subset: Iterable[str],
                     *, model_key: str, seed: int, resamples: int) -> dict[str, Any]:
    """Gate 3 by the pilot's own kernel on frame ``frame``'s table restricted
    to ``subset``: the identification that frame would have reached had only
    those rungs been calibrated."""
    keep = set(subset)
    g2 = copy.deepcopy(dict(gate2))
    block = g2["by_frame"][str(frame)]
    for split, rows in block["calibration_rows"].items():
        block["calibration_rows"][split] = [
            r for r in rows if _label(r["kind"], r["severity"]) in keep]
    if not block["calibration_rows"]["pooled"]:
        return {"empty": True, "core_identified": False,
                "n_local_valid_families": 0, "local_valid_families": [],
                "n_backups": 0, "backups": [], "coverage_identified": False,
                "local_supported": False, "state": "NEITHER",
                "spectrum_valid_below": [], "spectrum_valid_above": []}
    out = REF.frame_references(g2, frame, model_key=model_key, seed=seed,
                               resamples=resamples)
    s = out["survival"]
    return {"empty": False,
            "core_identified": bool(s["core_identified"]),
            "core_references": [f"{c['family']}:{c['severity']}"
                                for c in s["core_references"]],
            "n_local_valid_families": s["n_local_valid_families"],
            "local_valid_families": list(s["local_valid_families"]),
            "n_backups": s["n_backups"], "backups": list(s["backups"]),
            "coverage_identified": bool(s["coverage_identified"]),
            "coverage_status": s["coverage_status"],
            "selected_families": list(s["selected_families"]),
            "n_spectrum_references": s["n_spectrum_references"],
            "spectrum_valid_below": list(s["spectrum_valid_below"]),
            "spectrum_valid_above": list(s["spectrum_valid_above"]),
            "local_supported": bool(EL.local_support(s, frame=frame)["local_supported"]),
            "state": out["state"],
            "n_local_valid": out["n_local_valid"],
            "n_spectrum_valid": out["n_spectrum_valid"]}


def realised(gate3: Mapping[str, Any], frame: int) -> dict[str, Any]:
    f3 = gate3["by_frame"][str(frame)]
    if f3.get("status") != PS.FRAME_SUPPORTED:
        return {"supported": False}
    s = f3["survival"]
    return {"supported": True,
            "local_valid": {k for k, v in f3["local"].items() if v["passed"]},
            "spectrum_valid": {k for k, v in f3["spectrum"].items() if v["passed"]},
            "spectrum_side": {k: v.get("side") for k, v in f3["spectrum"].items()
                              if v["passed"]},
            "local_first_failing": {k: v.get("first_failing_component")
                                    for k, v in f3["local"].items()},
            "core_references": [f"{c['family']}:{c['severity']}"
                                for c in s["core_references"]],
            "local_valid_families": set(s["local_valid_families"]),
            "backups": list(s["backups"]), "coverage_identified": s["coverage_identified"],
            "core_identified": s["core_identified"],
            "local_supported": bool(EL.local_support(s, frame=frame)["local_supported"]),
            "state": f3["state"]}


# --------------------------------------------------------------- ranking
def rank_by_distance(iota_by_label: Mapping[str, float | None], target: float
                     ) -> dict[str, int]:
    entries = [(tie_key(abs(float(v) - target)), label)
               for label, v in iota_by_label.items() if v is not None]
    entries.sort()
    return {label: i + 1 for i, (_, label) in enumerate(entries)}


def _rung_rows(screen: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {r["candidate"]: {**r, "family": kind,
                             "family_status": v["status"],
                             "family_labels": list(v["labels"])}
            for kind, v in screen["families"].items() for r in v["rungs"]}


def _roles(plan_entry: Mapping[str, Any]) -> dict[str, list[str]]:
    return {e["candidate"]: list(e["roles"])
            for e in plan_entry["retention"]["forwarded"]}


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float | None:
    a, b = set(a), set(b)
    return (len(a & b) / len(a | b)) if (a | b) else None


# ------------------------------------------------------------- stability
def _resampled_rows(rows: Sequence[Mapping[str, Any]], topics: Sequence[str],
                    rng: np.random.Generator) -> list[dict[str, Any]]:
    """Rows of a with-replacement topic resample; a repeated topic gets a
    distinct id so the count kernel sees it as another topic."""
    picks = rng.choice(len(topics), size=len(topics), replace=True)
    out: list[dict[str, Any]] = []
    for j, i in enumerate(picks):
        tid = topics[int(i)]
        for r in rows:
            if r["topic_id"] == tid:
                out.append({**r, "topic_id": f"{tid}#{j}"})
    return out


def retention_stability(ladder_rows: Sequence[Mapping[str, Any]],
                        rungs: Sequence[Constraint], *,
                        screen_config: ScreenConfig,
                        retention_config: RetentionConfig,
                        resamples: int, seed: int) -> dict[str, Any]:
    """How stable each policy's round-0 forwarded set is under a topic
    resample of its own evidence: the frame-aware set on the frame's six
    topics, the pooled set on its twenty-four, and --- to separate the
    topic count from the frame --- the pooled set on a random six of them."""
    rng = np.random.default_rng(seed)
    legacy = LegacyPooledPolicy(screen_config=screen_config,
                                retention_config=retention_config)
    aware = FrameAwarePolicy(screen_config=screen_config,
                             retention_config=retention_config)
    base = evidence_from_rows(ladder_rows, rungs)
    base_plan_l = legacy.plan(base)
    base_plan_f = aware.plan(base)
    topics_by_frame = {f: sorted({r["topic_id"] for r in ladder_rows
                                  if frame_of_block(r) == f}) for f in base.frames}
    all_topics = sorted({r["topic_id"] for r in ladder_rows})
    j_frame: dict[int, list[float]] = {f: [] for f in base.frames}
    j_pooled: list[float] = []
    j_pooled_six: list[float] = []
    for _ in range(resamples):
        # (a) each frame resampled on its own topics
        per_frame_rows: list[dict[str, Any]] = []
        for f in base.frames:
            frame_rows = [r for r in ladder_rows if frame_of_block(r) == f]
            per_frame_rows += _resampled_rows(frame_rows, topics_by_frame[f], rng)
        ev = evidence_from_rows(per_frame_rows, rungs)
        plan = aware.plan(ev)
        for f in base.frames:
            j = _jaccard(plan.forwarded(f), base_plan_f.forwarded(f))
            if j is not None:
                j_frame[f].append(j)
        # (b) the pooled screen resampled on all 24 topics
        pooled_rows = _resampled_rows(ladder_rows, all_topics, rng)
        ev = evidence_from_rows(pooled_rows, rungs)
        j = _jaccard(legacy.plan(ev).union, base_plan_l.union)
        if j is not None:
            j_pooled.append(j)
        # (c) the pooled screen on six of its topics (no replacement)
        six = [all_topics[int(i)] for i in rng.choice(len(all_topics), size=6,
                                                      replace=False)]
        six_rows = [r for r in ladder_rows if r["topic_id"] in six]
        ev = evidence_from_rows(six_rows, rungs)
        j = _jaccard(legacy.plan(ev).union, base_plan_l.union)
        if j is not None:
            j_pooled_six.append(j)
    mean = lambda v: (statistics.fmean(v) if v else None)  # noqa: E731
    return {"resamples": resamples,
            "frame_aware_six_topics": {str(f): mean(v) for f, v in j_frame.items()},
            "frame_aware_six_topics_mean": mean([x for v in j_frame.values() for x in v]),
            "pooled_twenty_four_topics": mean(j_pooled),
            "pooled_six_topics_subsample": mean(j_pooled_six),
            "statistic": "mean Jaccard overlap of the round-0 forwarded set "
                         "with the unresampled one, over topic resamples of "
                         "the same rows",
            "base_sizes": {"frame_aware": {str(f): len(base_plan_f.forwarded(f))
                                           for f in base.frames},
                           "pooled": len(base_plan_l.union)}}


# ----------------------------------------------------------------- one model
def replay(model_key: str, root: pathlib.Path, *, confirm_root: pathlib.Path,
           resamples: int | None = None,
           stability_resamples: int = STABILITY_RESAMPLES) -> dict[str, Any]:
    source: PilotSource = open_pilot(root, model_key)
    regime, gate1, gate2, gate3 = (source.regime, source.gate1, source.gate2,
                                   source.gate3)
    second = second_pass_record(root, model_key)
    topup = topup_record(confirm_root, model_key)
    model_dir = source.model_dir
    ladder_rows = scored_rows(model_dir, PS.STAGE_REGIME, "ladder")
    batch_rows = {b["index"]: scored_rows(model_dir, PS.STAGE_SECOND_PASS, b["run"])
                  for b in second["batches"]}
    rungs = rungs_of(regime["prescreen_table"])
    screen_cfg = _screen_config(second["screen"]["config"])
    ret_cfg = RetentionConfig(**second["retention"]["config"])
    seed3 = int(gate3["seed"])
    resamples3 = int(resamples if resamples is not None else gate3["resamples"])

    # ---- 1. legacy, reproduced
    legacy_loop = legacy_final_screen(second, regime)
    legacy_policy = LegacyPooledPolicy(screen_config=screen_cfg,
                                       retention_config=ret_cfg)
    legacy_plan = legacy_policy.plan_from_screen(legacy_loop["screen"],
                                                 n_topics=C.N_PRESCREEN)
    forwarded_record = list(second["forwarded_set"])
    if legacy_plan.union != forwarded_record:
        raise ProtocolError(f"{model_key}: the legacy replay forwards "
                            f"{len(legacy_plan.union)} rungs and the record "
                            f"{len(forwarded_record)}")
    legacy_rungs = _rung_rows(legacy_loop["screen"])
    pooled_iota_a = float(legacy_loop["screen"]["iota_a"]["iota_a_mean"])

    # ---- 3/4. frame-aware on the frame's own evidence, two targets
    round0, final = frame_evidence_final(ladder_rows, batch_rows, regime, second)
    aware = FrameAwarePolicy(screen_config=screen_cfg, retention_config=ret_cfg)
    targets = calibration_targets(gate2, draws=screen_cfg.draws,
                                  seed=screen_cfg.base_seed)
    plan_proxy = aware.plan(final)
    plan_cal = (aware.plan(ScreenEvidence(
        by_frame={f: e for f, e in final.by_frame.items() if f in targets},
        pooled=final.pooled, provenance=final.provenance), targets=targets)
        if targets else None)
    plan_proxy_r0 = aware.plan(round0)
    screens_proxy = {f: screen_families(list(final.by_frame[f].table),
                                        list(final.by_frame[f].a_grid),
                                        config=screen_cfg)
                     for f in final.frames}
    screens_cal = {f: screen_families(list(final.by_frame[f].table), (),
                                      config=screen_cfg, target=targets[f])
                   for f in targets}

    # ---- 2. legacy + top-up, from the confirmatory root's pre-freeze record
    topup_added: dict[int, list[str]] = {}
    topup_reverdict: dict[int, dict[str, Any]] = {}
    if topup is not None:
        for w in topup["plan"]["frames_running"]:
            fp = topup["plan"]["by_frame"][str(w)]
            topup_added[int(w)] = sorted(
                r["candidate"] for fam in fp["candidate_families"].values() for r in fam)
            g3f = topup["reverdicted_gate3"]["by_frame"][str(w)]
            s = g3f["survival"]
            topup_reverdict[int(w)] = {
                "core_identified": bool(s["core_identified"]),
                "n_local_valid_families": s["n_local_valid_families"],
                "local_valid_families": list(s["local_valid_families"]),
                "n_backups": s["n_backups"],
                "coverage_identified": bool(s["coverage_identified"]),
                "local_supported": bool(EL.local_support(s, frame=int(w))["local_supported"]),
                "state": g3f["state"],
                "local_valid": sorted(k for k, v in g3f["local"].items() if v["passed"]),
                "spectrum_valid": sorted(k for k, v in g3f["spectrum"].items()
                                         if v["passed"])}

    # ---- per frame
    calibrated = {}
    for w in gate2["supported_frames"]:
        calibrated[int(w)] = {_label(r["kind"], r["severity"]): r
                              for r in gate2["by_frame"][str(w)]["calibration_rows"]["pooled"]}
    withheld = {int(w): {_label(r["kind"], r["severity"])
                         for r in gate2["by_frame"][str(w)]["calibration_rows_withheld"].get("pooled", [])}
                for w in gate2["supported_frames"]}
    by_frame: dict[str, Any] = {}
    rows_out: list[dict[str, Any]] = []
    self_check: dict[str, Any] = {}
    for f in PS.FRAMES:
        supported = f in calibrated
        real = realised(gate3, f) if supported else {"supported": False}
        entry: dict[str, Any] = {"frame": f, "gate2_supported": supported}
        proxy_entry = plan_proxy.by_frame.get(str(f))
        cal_entry = plan_cal.by_frame.get(str(f)) if plan_cal else None
        proxy_rungs = _rung_rows(screens_proxy[f]) if f in screens_proxy else {}
        cal_rungs = _rung_rows(screens_cal[f]) if f in screens_cal else {}
        sets = {
            "legacy": set(legacy_plan.union),
            "legacy_topup": set(legacy_plan.union) | set(topup_added.get(f, ())),
            "fa_proxy": set(proxy_entry["forwarded"]) if proxy_entry else set(),
            "fa_cal": set(cal_entry["forwarded"]) if cal_entry else set(),
        }
        roles = {"legacy": _roles(legacy_plan.by_frame[str(f)]),
                 "fa_proxy": _roles(proxy_entry) if proxy_entry else {},
                 "fa_cal": _roles(cal_entry) if cal_entry else {}}
        # rankings by distance, Tier-1/2 only, per target
        t12 = {lab for lab, r in proxy_rungs.items()
               if FAMILIES[r["family"]].structural_tier in TIERS_ELIGIBLE}
        rank_pooled = rank_by_distance(
            {lab: legacy_rungs[lab]["iota_mean"] for lab in t12 if lab in legacy_rungs},
            pooled_iota_a)
        rank_proxy = rank_by_distance(
            {lab: proxy_rungs[lab]["iota_mean"] for lab in t12},
            float(screens_proxy[f]["iota_a"]["iota_a_mean"])) if f in screens_proxy else {}
        rank_cal = rank_by_distance(
            {lab: cal_rungs[lab]["iota_mean"] for lab in t12},
            float(targets[f]["iota_a_mean"])) if f in targets else {}
        # the per-candidate rows
        labels = sorted(set(legacy_rungs) | set(proxy_rungs) | set(cal_rungs)
                        | set(calibrated.get(f, {})) | set(topup_added.get(f, ())))
        for lab in labels:
            kind = lab.rpartition(":")[0]
            fam = FAMILIES.get(kind)
            pr = proxy_rungs.get(lab) or {}
            cr = cal_rungs.get(lab) or {}
            lr = legacy_rungs.get(lab) or {}
            cal_row = calibrated.get(f, {}).get(lab)
            is_cal = cal_row is not None
            cal_iota = (instructed_compliance(float(cal_row["solo_compliance"]),
                                              float(cal_row["chance_compliance"]))
                        if is_cal and float(cal_row["chance_compliance"]) < C.CHANCE_DEGENERACY_MAX
                        else None)
            in_topup = lab in topup_added.get(f, ())
            later_local = ((lab in real["local_valid"]) if (supported and is_cal)
                           else (lab in topup_reverdict[f]["local_valid"]
                                 if in_topup and f in topup_reverdict else None))
            later_spectrum = ((lab in real["spectrum_valid"]) if (supported and is_cal)
                              else (lab in topup_reverdict[f]["spectrum_valid"]
                                    if in_topup and f in topup_reverdict else None))
            identifiable = later_local is not None
            row = {
                "model": model_key, "root": root.name, "frame": f,
                "gate2_status": "SUPPORTED" if supported else "UNSUPPORTED",
                "candidate": lab, "family": kind, "severity": int(lab.rpartition(":")[2]),
                "tier": fam.structural_tier if fam else None,
                "feature_group": fam.feature_group if fam else None,
                "screen_n_topics_f": pr.get("n_topics"),
                "screen_p_f": pr.get("solo_rate"), "screen_kappa_f": pr.get("chance_rate"),
                "screen_iota_f": pr.get("iota_point"),
                "screen_iota_mean_f": pr.get("iota_mean"),
                "screen_iota_sd_f": pr.get("iota_sd"),
                "screen_p_admissible_f": pr.get("p_admissible"),
                "screen_p_local_proxy_f": pr.get("p_local"),
                "screen_p_local_cal_f": cr.get("p_local"),
                "pooled_n_topics": lr.get("n_topics"),
                "pooled_p": lr.get("solo_rate"), "pooled_kappa": lr.get("chance_rate"),
                "pooled_iota": lr.get("iota_point"), "pooled_iota_mean": lr.get("iota_mean"),
                "pooled_iota_sd": lr.get("iota_sd"), "pooled_p_local": lr.get("p_local"),
                "pooled_iota_a": pooled_iota_a,
                "proxy_iota_a_f": (float(screens_proxy[f]["iota_a"]["iota_a_mean"])
                                   if f in screens_proxy else None),
                "proxy_iota_a_sd_f": (float(screens_proxy[f]["iota_a"]["iota_a_sd"])
                                      if f in screens_proxy else None),
                "gate2_iota_a_f": float(targets[f]["iota_a_mean"]) if f in targets else None,
                "gate2_se_iota_a_f": targets[f]["se_iota_a"] if f in targets else None,
                "dist_pooled": (abs(lr["iota_mean"] - pooled_iota_a)
                                if lr.get("iota_mean") is not None else None),
                "dist_proxy_f": (abs(pr["iota_mean"] - float(screens_proxy[f]["iota_a"]["iota_a_mean"]))
                                 if pr.get("iota_mean") is not None and f in screens_proxy else None),
                "dist_cal_f": (abs(pr["iota_mean"] - float(targets[f]["iota_a_mean"]))
                               if pr.get("iota_mean") is not None and f in targets else None),
                "rank_pooled_t12": rank_pooled.get(lab),
                "rank_proxy_f_t12": rank_proxy.get(lab),
                "rank_cal_f_t12": rank_cal.get(lab),
                "legacy_family_status": lr.get("family_status"),
                "legacy_family_labels": "|".join(lr.get("family_labels", [])),
                "legacy_retained": lab in sets["legacy"],
                "legacy_roles": "|".join(roles["legacy"].get(lab, [])),
                "topup_added": in_topup,
                "fa_proxy_family_status": pr.get("family_status"),
                "fa_proxy_family_labels": "|".join(pr.get("family_labels", [])),
                "fa_proxy_retained": lab in sets["fa_proxy"],
                "fa_proxy_roles": "|".join(roles["fa_proxy"].get(lab, [])),
                "fa_cal_family_status": cr.get("family_status"),
                "fa_cal_family_labels": "|".join(cr.get("family_labels", [])),
                "fa_cal_retained": lab in sets["fa_cal"],
                "fa_cal_roles": "|".join(roles["fa_cal"].get(lab, [])),
                "calibrated_in_pilot": is_cal,
                "withheld_degenerate": lab in withheld.get(f, set()),
                "cal_iota_f": cal_iota,
                "cal_inside_caliper_f": (tie_key(abs(cal_iota - float(targets[f]["iota_a_mean"]))) <= CALIPER
                                         if cal_iota is not None and f in targets else None),
                "later_local_valid_f": later_local,
                "later_spectrum_valid_f": later_spectrum,
                "later_spectrum_side_f": (real["spectrum_side"].get(lab)
                                          if supported and is_cal else None),
                "local_first_failing_f": (real["local_first_failing"].get(lab)
                                          if supported and is_cal else None),
                "downstream_identifiable": identifiable,
                "legacy_omitted_fa_proxy_forwards": (lab in sets["fa_proxy"]) and (lab not in sets["legacy"]),
                "legacy_omitted_fa_cal_forwards": (lab in sets["fa_cal"]) and (lab not in sets["legacy"]),
                "fa_proxy_forwards_useless": (lab in sets["fa_proxy"] and identifiable
                                              and not later_local and not later_spectrum),
                "fa_cal_forwards_useless": (lab in sets["fa_cal"] and identifiable
                                            and not later_local and not later_spectrum),
                "legacy_forwards_useless": (lab in sets["legacy"] and identifiable
                                            and not later_local and not later_spectrum),
            }
            rows_out.append(row)
        # ---- the per-system summary on this frame
        systems: dict[str, Any] = {}
        truth_local = real["local_valid"] if supported else set()
        truth_spec = real["spectrum_valid"] if supported else set()
        for name in SYSTEMS:
            s = sets[name]
            if name == "fa_cal" and cal_entry is None:
                systems[name] = {"available": False,
                                 "why": "no Gate-2 operating point on this frame"}
                continue
            cal_known = set(calibrated.get(f, {})) | set(withheld.get(f, set()))
            if name == "legacy_topup":
                cal_known |= set(topup_added.get(f, ()))
            retained_cal = s & cal_known
            not_ident = s - cal_known
            hit_local = s & truth_local
            hit_spec = s & truth_spec
            fam_local = {l.rpartition(":")[0] for l in hit_local}
            summary = {
                "available": True,
                "n_retained": len(s), "n_retained_calibrated": len(retained_cal),
                "n_not_identifiable": len(not_ident),
                "not_identifiable": sorted(not_ident),
                "n_local_valid_retained": len(hit_local),
                "recall_local_valid": (len(hit_local) / len(truth_local)) if truth_local else None,
                "n_spectrum_valid_retained": len(hit_spec),
                "recall_spectrum_valid": (len(hit_spec) / len(truth_spec)) if truth_spec else None,
                "n_local_valid_families_retained": len(fam_local),
                "feature_groups_local_valid_retained": sorted(
                    {FAMILIES[k].feature_group for k in fam_local}),
                "n_inside_caliper_retained": sum(
                    1 for lab in retained_cal if lab in calibrated.get(f, {})
                    and (r := next(x for x in rows_out if x["candidate"] == lab
                                   and x["frame"] == f and x["model"] == model_key))
                    and r["cal_inside_caliper_f"]),
                "n_useless_retained": sum(
                    1 for lab in retained_cal if lab in calibrated.get(f, {})
                    and lab not in truth_local and lab not in truth_spec),
                "calibration_generations": len(s) * R.calibration_generations_per_rung(model_key) // C.N_WORDINGS
                if name.startswith("fa_") else len(s) * R.calibration_generations_per_rung(model_key),
            }
            if supported:
                if name == "legacy_topup" and f in topup_reverdict:
                    summary["downstream"] = {**topup_reverdict[f],
                                             "basis": "LOCAL_TOPUP re-verdict on the record"}
                elif name == "legacy":
                    summary["downstream"] = {
                        "core_identified": real["core_identified"],
                        "core_references": real["core_references"],
                        "n_local_valid_families": len(real["local_valid_families"]),
                        "local_valid_families": sorted(real["local_valid_families"]),
                        "n_backups": len(real["backups"]),
                        "coverage_identified": real["coverage_identified"],
                        "local_supported": real["local_supported"],
                        "state": real["state"], "basis": "GATE_3_REFERENCES record"}
                elif name == "legacy_topup":
                    summary["downstream"] = {**systems["legacy"]["downstream"],
                                             "basis": "no top-up fired: the legacy record"}
                else:
                    summary["downstream"] = {
                        **restricted_gate3(gate2, f, retained_cal, model_key=model_key,
                                           seed=seed3, resamples=resamples3),
                        "basis": "Gate 3 by the pilot's kernel on the frame's "
                                 "table restricted to the retained calibrated "
                                 "rungs; forwarded-but-uncalibrated rungs are "
                                 "NOT_IDENTIFIABLE and absent"}
            systems[name] = summary
        if supported:
            check = restricted_gate3(gate2, f, set(calibrated[f]), model_key=model_key,
                                     seed=seed3, resamples=resamples3)
            self_check[str(f)] = {
                "restricted_to_full_table_reproduces_record": (
                    check["core_references"] == real["core_references"]
                    and set(check["local_valid_families"]) == real["local_valid_families"]
                    and check["n_backups"] == len(real["backups"])
                    and check["coverage_identified"] == real["coverage_identified"]),
                "record": {"core": real["core_references"],
                           "families": sorted(real["local_valid_families"]),
                           "backups": len(real["backups"]),
                           "coverage": real["coverage_identified"]},
                "recomputed": {"core": check["core_references"],
                               "families": check["local_valid_families"],
                               "backups": check["n_backups"],
                               "coverage": check["coverage_identified"]}}
        entry.update({
            "iota_a": {"pooled_screen": pooled_iota_a,
                       "proxy_screen_f": (float(screens_proxy[f]["iota_a"]["iota_a_mean"])
                                          if f in screens_proxy else None),
                       "proxy_screen_sd_f": (float(screens_proxy[f]["iota_a"]["iota_a_sd"])
                                             if f in screens_proxy else None),
                       "gate2_f": float(targets[f]["iota_a_mean"]) if f in targets else None,
                       "gate2_se_f": targets[f]["se_iota_a"] if f in targets else None},
            "screen_n_topics": {"round0": round0.by_frame[f].n_topics,
                                "final": final.by_frame[f].n_topics},
            "n_calibrated": len(calibrated.get(f, {})),
            "realised": ({"n_local_valid": len(truth_local),
                          "n_spectrum_valid": len(truth_spec),
                          "local_valid_families": sorted(real["local_valid_families"]),
                          "state": real["state"],
                          "local_supported": real["local_supported"]}
                         if supported else None),
            "sets": {k: sorted(v) for k, v in sets.items()},
            "set_overlap": {
                "fa_proxy_vs_legacy": _jaccard(sets["fa_proxy"], sets["legacy"]),
                "fa_cal_vs_legacy": _jaccard(sets["fa_cal"], sets["legacy"]),
                "fa_proxy_vs_fa_cal": _jaccard(sets["fa_proxy"], sets["fa_cal"])},
            "round0_fa_proxy": sorted(plan_proxy_r0.forwarded(f)) if str(f) in plan_proxy_r0.by_frame else [],
            "systems": systems,
        })
        by_frame[str(f)] = entry

    # ---- cross-frame set overlap and cost
    def _overlap(plan) -> dict[str, Any]:
        if plan is None:
            return {"available": False}
        fr = plan.frames
        pairs = {f"{a}-{b}": _jaccard(plan.forwarded(a), plan.forwarded(b))
                 for i, a in enumerate(fr) for b in fr[i + 1:]}
        return {"available": True, "pairwise_jaccard": pairs,
                "mean_pairwise_jaccard": (statistics.fmean(v for v in pairs.values()
                                                           if v is not None)
                                          if pairs else None),
                "n_union": len(plan.union),
                "n_by_frame": {str(f): len(plan.forwarded(f)) for f in fr},
                "n_selected_by_all_frames": sum(
                    1 for v in plan.selected_by_frames.values() if len(v) == len(fr)),
                "cost": plan.cost}
    per_rung_all = R.calibration_generations_per_rung(model_key)
    screen_gens_1pass = C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS * (len(rungs) + 1)
    compute = {
        "legacy_calibration_generations": len(legacy_plan.union) * per_rung_all,
        "legacy_topup_generations": sum(len(v) for v in topup_added.values()) * per_rung_all // C.N_WORDINGS,
        "fa_proxy_calibration_generations": plan_proxy.cost["total"],
        "fa_cal_calibration_generations": plan_cal.cost["total"] if plan_cal else None,
        "worst_case_per_frame_rungs": (R.RETENTION_MAX_SPECTRUM_FAMILIES * R.RETENTION_SPECTRUM_RUNGS
                                       + R.RETENTION_MAX_LOCAL_FAMILIES * R.RETENTION_LOCAL_RUNGS
                                       + R.RETENTION_CLASS_ARM_RUNGS + R.RETENTION_NEAR_FORM_RUNGS),
        "worst_case_legacy_generations": 93 * per_rung_all,
        "worst_case_frame_aware_generations": 93 * per_rung_all,   # 4 frames x 93 x per-frame cost
        "screen_generations_one_pass": screen_gens_1pass,
        "screen_generations_four_pass": screen_gens_1pass * C.N_WORDINGS,
        "second_pass_generations_recorded": second["cost_generations"],
        "second_pass_generations_four_pass": second["cost_generations"] * C.N_WORDINGS,
        "gate2_grid_generations": len(gate2["calibration_topic_ids"]) * R.calibration_passes(model_key)
        * C.M_CAL * (len(C.TARGET_GRID) + 1 + len(C.FOCAL_GRID) + 1),
    }
    stability = retention_stability(ladder_rows, rungs, screen_config=screen_cfg,
                                    retention_config=ret_cfg,
                                    resamples=stability_resamples,
                                    seed=screen_cfg.base_seed + 1)
    return {
        "model_key": model_key, "root": root.name, "study_id": source.study_id,
        "record_hashes": source.record_hashes,
        "topup_record": (topup["inputs"] if topup else None),
        "topup_frames_fired": sorted(topup_added),
        "reads": ["REGIME_SCREEN", "SECOND_PASS_SCREEN", "GATE_1_INSTRUMENT",
                  "GATE_2_CALIBRATION", "GATE_3_REFERENCES",
                  f"{CONFIRM_ROOT}/LOCAL_TOPUP (pre-freeze)"],
        "opens_protected_stage": False, "generations": 0,
        "gate3_kernel": {"seed": seed3, "resamples": resamples3,
                         "recorded_resamples": int(gate3["resamples"])},
        "self_check": self_check,
        "screen_config": second["screen"]["config"],
        "retention_config": second["retention"]["config"],
        "legacy": {"n_forwarded": len(legacy_plan.union),
                   "forwarded": legacy_plan.union,
                   "pooled_iota_a": pooled_iota_a},
        "fa_proxy": _overlap(plan_proxy),
        "fa_cal": _overlap(plan_cal),
        "by_frame": by_frame,
        "compute": compute,
        "stability": stability,
        "rows": rows_out,
    }


# --------------------------------------------------------------- summary
def _f(v: Any, nd: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def summarise(models: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    per_system: dict[str, dict[str, list]] = {s: {"recall_local": [], "recall_spectrum": [],
                                                  "n_local_fam": [], "n_backups": [],
                                                  "coverage": [], "local_supported": [],
                                                  "n_not_ident": [], "n_useless": [],
                                                  "n_retained": [], "gens": []}
                                              for s in SYSTEMS}
    frames_counted = 0
    for m in models:
        for f, b in m["by_frame"].items():
            if not b["gate2_supported"]:
                continue
            frames_counted += 1
            for s in SYSTEMS:
                x = b["systems"][s]
                if not x.get("available"):
                    continue
                d = x.get("downstream") or {}
                acc = per_system[s]
                acc["recall_local"].append(x["recall_local_valid"])
                acc["recall_spectrum"].append(x["recall_spectrum_valid"])
                acc["n_local_fam"].append(d.get("n_local_valid_families"))
                acc["n_backups"].append(d.get("n_backups"))
                acc["coverage"].append(d.get("coverage_identified"))
                acc["local_supported"].append(d.get("local_supported"))
                acc["n_not_ident"].append(x["n_not_identifiable"])
                acc["n_useless"].append(x["n_useless_retained"])
                acc["n_retained"].append(x["n_retained"])
                acc["gens"].append(x["calibration_generations"])
    mean = lambda v: (statistics.fmean([x for x in v if x is not None])  # noqa: E731
                      if any(x is not None for x in v) else None)
    count_true = lambda v: sum(1 for x in v if x)  # noqa: E731
    out = {"frames_with_operating_point": frames_counted, "by_system": {}}
    for s, acc in per_system.items():
        out["by_system"][s] = {
            "frames": len(acc["n_retained"]),
            "mean_recall_local_valid": mean(acc["recall_local"]),
            "mean_recall_spectrum_valid": mean(acc["recall_spectrum"]),
            "mean_n_local_valid_families": mean(acc["n_local_fam"]),
            "mean_n_backups": mean(acc["n_backups"]),
            "frames_coverage_identified": count_true(acc["coverage"]),
            "frames_local_supported": count_true(acc["local_supported"]),
            "mean_n_not_identifiable": mean(acc["n_not_ident"]),
            "mean_n_useless_retained": mean(acc["n_useless"]),
            "mean_n_retained": mean(acc["n_retained"]),
            "total_calibration_generations": sum(g for g in acc["gens"] if g is not None),
        }
    out["stability"] = {m["model_key"]: m["stability"] for m in models}
    out["iota_a_drift"] = {
        m["model_key"]: {f: {"proxy_minus_gate2": (
            (b["iota_a"]["proxy_screen_f"] - b["iota_a"]["gate2_f"])
            if b["iota_a"]["gate2_f"] is not None and b["iota_a"]["proxy_screen_f"] is not None else None),
            "pooled_minus_gate2": ((b["iota_a"]["pooled_screen"] - b["iota_a"]["gate2_f"])
                                   if b["iota_a"]["gate2_f"] is not None else None),
            "proxy_sd": b["iota_a"]["proxy_screen_sd_f"]}
            for f, b in m["by_frame"].items()}
        for m in models}
    return out


def render_feasibility(models: Sequence[Mapping[str, Any]], summary: Mapping[str, Any]) -> str:
    L: list[str] = []
    A = L.append
    A("# DCI-1 v8 — pre-screen retention policies replayed on the stored pilot evidence (tables)")
    A("")
    A("> Generated by `dci1/tools/v8_prescreen_counterfactual.py` on the signed, "
      "unprotected pre-freeze records of the four study roots and the "
      "pre-freeze `LOCAL_TOPUP` record of `dci1v8-confirm-r2`. Zero generation; "
      "no protected stage opened; nothing written into any evidence tree. "
      "A rung the pilot never calibrated is `NOT_IDENTIFIABLE` and is never "
      "credited with an outcome.")
    A("")
    A("## Systems")
    A("")
    A("| system | evidence | ranking target | forwarded set |")
    A("|---|---|---|---|")
    A("| `legacy` | pooled counts (24 topics) | pooled screen ι_A | one set for all frames (reproduced from the record) |")
    A("| `legacy_topup` | `legacy` + the confirmatory `LOCAL_TOPUP` rungs where it fired | Gate-2 ι_A(f) for the top-up | per frame |")
    A("| `fa_proxy` | each frame's own counts (6 topics at round 0 + its share of every recorded batch) | the frame's own screen-proxy ι_A(f) | per frame |")
    A("| `fa_cal` | the same per-frame counts | Gate-2 ι_A(f) at its topic-level SE | per frame |")
    A("")
    A("## Downstream identification per system (frames with an operating point)")
    A("")
    A("Recall is over the rungs the pilot calibrated under the frame (the only "
      "rungs whose per-frame validity is known); the downstream columns are "
      "Gate 3 re-run by the pilot's own kernel on the frame's table restricted "
      "to the system's retained *calibrated* rungs.")
    A("")
    A("| system | frames | recall LOCAL-valid | recall SPECTRUM-valid | LOCAL-valid families | backups | frames coverage identified | frames LOCAL_SUPPORTED | forwarded-uncalibrated (mean) | useless retained (mean) | retained (mean) | calibration generations |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for s in SYSTEMS:
        x = summary["by_system"][s]
        A(f"| `{s}` | {x['frames']} | {_f(x['mean_recall_local_valid'])} | "
          f"{_f(x['mean_recall_spectrum_valid'])} | {_f(x['mean_n_local_valid_families'])} | "
          f"{_f(x['mean_n_backups'])} | {x['frames_coverage_identified']} | "
          f"{x['frames_local_supported']} | {_f(x['mean_n_not_identifiable'], 1)} | "
          f"{_f(x['mean_n_useless_retained'], 1)} | {_f(x['mean_n_retained'], 1)} | "
          f"{x['total_calibration_generations']:,} |")
    A("")
    A("## Per model × frame")
    A("")
    A("| model | f | Gate-2 | ι_A pooled screen | ι_A proxy(f) ± sd | ι_A Gate-2(f) | calibrated | LOCAL-valid / SPECTRUM-valid realised | legacy: fam/bk/cov/LOCAL | topup: fam/bk/cov/LOCAL | fa_proxy: recall L/S, fam/bk/cov/LOCAL, uncal | fa_cal: recall L/S, fam/bk/cov/LOCAL, uncal |")
    A("|---|---:|---|---:|---|---:|---:|---|---|---|---|---|")
    for m in models:
        for f, b in sorted(m["by_frame"].items()):
            ia = b["iota_a"]
            if not b["gate2_supported"]:
                A(f"| `{m['model_key']}` | {f} | UNSUPPORTED | {_f(ia['pooled_screen'])} | "
                  f"{_f(ia['proxy_screen_f'])} ± {_f(ia['proxy_screen_sd_f'])} | — | — | — | — | — | — | — |")
                continue

            def cell(name):
                x = b["systems"][name]
                if not x.get("available"):
                    return "—"
                d = x.get("downstream") or {}
                core = f"{d.get('n_local_valid_families', '—')}/{d.get('n_backups', '—')}/" \
                       f"{'C' if d.get('coverage_identified') else 'c'}/" \
                       f"{'L' if d.get('local_supported') else 'l'}"
                if name.startswith("fa_"):
                    return (f"{_f(x['recall_local_valid'])}/{_f(x['recall_spectrum_valid'])}, "
                            f"{core}, {x['n_not_identifiable']}")
                return core
            r = b["realised"]
            A(f"| `{m['model_key']}` | {f} | SUPPORTED | {_f(ia['pooled_screen'])} | "
              f"{_f(ia['proxy_screen_f'])} ± {_f(ia['proxy_screen_sd_f'])} | "
              f"{_f(ia['gate2_f'])} | {b['n_calibrated']} | "
              f"{r['n_local_valid']} / {r['n_spectrum_valid']} | "
              f"{cell('legacy')} | {cell('legacy_topup')} | {cell('fa_proxy')} | {cell('fa_cal')} |")
    A("")
    A("Legend: fam = LOCAL-valid families on the retained calibrated set; bk = "
      "admissible backups; C/c = coverage identified / not; L/l = "
      "`LOCAL_SUPPORTED` / not; uncal = rungs the policy forwards that the pilot "
      "never calibrated (`NOT_IDENTIFIABLE`).")
    A("")
    A("## ι_A: the proxy against the coordinate the caliper is measured on")
    A("")
    A("| model | f | pooled screen − Gate-2(f) | frame proxy(f) − Gate-2(f) | proxy sd (6 topics + batches) | Gate-2 SE |")
    A("|---|---:|---:|---:|---:|---:|")
    for m in models:
        for f, b in sorted(m["by_frame"].items()):
            ia = b["iota_a"]
            if ia["gate2_f"] is None:
                continue
            A(f"| `{m['model_key']}` | {f} | {_f(ia['pooled_screen'] - ia['gate2_f'], 3)} | "
              f"{_f(ia['proxy_screen_f'] - ia['gate2_f'], 3)} | {_f(ia['proxy_screen_sd_f'], 3)} | "
              f"{_f(ia['gate2_se_f'], 3)} |")
    A("")
    A("## Stability of the round-0 forwarded set under topic resampling")
    A("")
    A("| model | frame-aware on 6 topics (per frame) | mean | pooled on 24 topics | pooled on a random 6 of the 24 |")
    A("|---|---|---:|---:|---:|")
    for m in models:
        st = m["stability"]
        per = "; ".join(f"f{f}={_f(v)}" for f, v in sorted(st["frame_aware_six_topics"].items()))
        A(f"| `{m['model_key']}` | {per} | {_f(st['frame_aware_six_topics_mean'])} | "
          f"{_f(st['pooled_twenty_four_topics'])} | {_f(st['pooled_six_topics_subsample'])} |")
    A("")
    A("Mean Jaccard overlap between the forwarded set on a with-replacement "
      "topic resample of the same rows and the set on the rows themselves "
      f"({STABILITY_RESAMPLES} resamples). The third column isolates the topic "
      "count: the pooled rule on six of its own twenty-four topics is as "
      "unstable as a frame's six, so the instability is the sample size, not "
      "the frame.")
    A("")
    A("## Cross-frame overlap of the frame-aware sets, and compute")
    A("")
    A("| model | fa_proxy: mean pairwise Jaccard | union | per frame | selected by all | fa_cal: mean pairwise Jaccard | union | legacy gens | fa_proxy gens | fa_cal gens | screen ×4 gens | second pass ×4 gens |")
    A("|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for m in models:
        p, c, k = m["fa_proxy"], m["fa_cal"], m["compute"]
        A(f"| `{m['model_key']}` | {_f(p['mean_pairwise_jaccard'])} | {p['n_union']} | "
          f"{p['n_by_frame']} | {p['n_selected_by_all_frames']} | "
          f"{_f(c.get('mean_pairwise_jaccard')) if c.get('available') else '—'} | "
          f"{c.get('n_union', '—')} | {k['legacy_calibration_generations']:,} | "
          f"{k['fa_proxy_calibration_generations']:,} | "
          f"{k['fa_cal_calibration_generations'] or '—'} | "
          f"{k['screen_generations_four_pass']:,} | {k['second_pass_generations_four_pass']:,} |")
    A("")
    A("Calibration generations: legacy = |set| × 3,072 (every rung on every "
      "frame's 192 topics × 4 draws); frame-aware = Σ_f |S(f)| × 768. The "
      "worst case is identical for both (93 rungs per frame × 768 × 4 = 93 × "
      "3,072). A four-pass screen (every pre-screen topic under every frame) "
      "multiplies the screen and second-pass generation by four; against one "
      "model's Gate-2 grids (≈ 55k) and candidates (≈ 180k) that is the "
      "last two columns.")
    A("")
    return "\n".join(L)


CSV_COLUMNS = [
    "model", "root", "frame", "gate2_status", "candidate", "family", "severity",
    "tier", "feature_group", "screen_n_topics_f", "screen_p_f", "screen_kappa_f",
    "screen_iota_f", "screen_iota_mean_f", "screen_iota_sd_f",
    "screen_p_admissible_f", "screen_p_local_proxy_f", "screen_p_local_cal_f",
    "pooled_n_topics", "pooled_p", "pooled_kappa", "pooled_iota", "pooled_iota_mean",
    "pooled_iota_sd", "pooled_p_local", "pooled_iota_a", "proxy_iota_a_f",
    "proxy_iota_a_sd_f", "gate2_iota_a_f", "gate2_se_iota_a_f", "dist_pooled",
    "dist_proxy_f", "dist_cal_f", "rank_pooled_t12", "rank_proxy_f_t12",
    "rank_cal_f_t12", "legacy_family_status", "legacy_family_labels",
    "legacy_retained", "legacy_roles", "topup_added", "fa_proxy_family_status",
    "fa_proxy_family_labels", "fa_proxy_retained", "fa_proxy_roles",
    "fa_cal_family_status", "fa_cal_family_labels", "fa_cal_retained",
    "fa_cal_roles", "calibrated_in_pilot", "withheld_degenerate", "cal_iota_f",
    "cal_inside_caliper_f", "later_local_valid_f", "later_spectrum_valid_f",
    "later_spectrum_side_f", "local_first_failing_f", "downstream_identifiable",
    "legacy_omitted_fa_proxy_forwards", "legacy_omitted_fa_cal_forwards",
    "fa_proxy_forwards_useless", "fa_cal_forwards_useless",
    "legacy_forwards_useless",
]


def _job(args: tuple[str, str, str, int | None, int]) -> dict[str, Any]:
    model_key, root, confirm, resamples, stab = args
    return jsonable(replay(model_key, pathlib.Path(root),
                           confirm_root=pathlib.Path(confirm),
                           resamples=resamples, stability_resamples=stab))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=pathlib.Path)
    ap.add_argument("--model")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--confirm-root", type=pathlib.Path,
                    default=DCI1 / "evidence" / CONFIRM_ROOT)
    ap.add_argument("--resamples", type=int, default=None,
                    help="Gate-3 bootstrap resamples for the restricted "
                         "re-verdicts (default: the record's)")
    ap.add_argument("--stability-resamples", type=int, default=STABILITY_RESAMPLES)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--out", type=pathlib.Path, default=OUT)
    args = ap.parse_args(argv)
    if args.all:
        pairs = [(m, DCI1 / "evidence" / r) for m, r in STUDY_ROOTS.items()]
    elif args.root and args.model:
        root = args.root if args.root.is_absolute() else DCI1 / args.root
        pairs = [(args.model, root)]
    else:
        ap.error("give --all, or both --root and --model")
    args.out.mkdir(parents=True, exist_ok=True)
    jobs = [(m, str(r.resolve()), str(args.confirm_root.resolve()),
             args.resamples, args.stability_resamples) for m, r in pairs]
    if args.jobs > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            models = list(pool.map(_job, jobs))
    else:
        models = [_job(j) for j in jobs]
    rows: list[dict[str, Any]] = []
    for m in models:
        path = args.out / f"counterfactual.{m['model_key']}.json"
        slim = {k: v for k, v in m.items() if k != "rows"}
        path.write_text(json.dumps(slim, indent=1, sort_keys=True) + "\n")
        rows += m["rows"]
        print(f"wrote {path}")
    with (args.out / "prescreen_counterfactual.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in CSV_COLUMNS})
    print(f"wrote {args.out / 'prescreen_counterfactual.csv'} ({len(rows)} rows)")
    summary = summarise(models)
    summary["models"] = {m["model_key"]: {"root": m["root"], "self_check": m["self_check"],
                                          "topup_frames_fired": m["topup_frames_fired"]}
                         for m in models}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    (args.out / "prescreen_feasibility_tables.md").write_text(
        render_feasibility(models, summary))
    print(f"wrote {args.out / 'summary.json'} and prescreen_feasibility_tables.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
