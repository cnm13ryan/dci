#!/usr/bin/env python3
"""Does the frame-pooled early screen lose useful frame-specific candidates?

Approach A (`docs/V8_FRAME_CONDITIONING.md`) decides every difficulty,
validity and selection **within** a wording frame, but the regime screen and
the second pass stay **pooled over frames**, as a measurement budget: at 24
topics x 1 draw a frame holds six topics, and the design note's §5 argues no
posterior on six topics can steer anything. That is an argument, not a
measurement. This tool measures it, retrospectively and outcome-blind, on a
completed pilot's own rows.

What it does, all on production kernels and stored evidence:

1.  **The frame-specific screen that was never run.** ``regime.prescreen_counts``
    and ``regime.prescreen_input`` are re-applied to the screen's scored rows
    *filtered to one frame's blocks*, and ``screen.screen_families`` --- the
    production screen, same config, same thresholds --- is run on each
    frame's counts. That gives, per (family, frame), the status
    (ACCEPT/REJECT/RESAMPLE) and the labels (spectrum / local candidate) a
    frame-aware screen would have produced.
2.  **What the pooled screen actually did.** The pooled statuses and labels
    are read off the signed `REGIME_SCREEN` record, and the forwarded set
    off `SECOND_PASS_SCREEN` --- the set Gate 2 then calibrated.
3.  **What the frames later did with it.** For every *forwarded* rung,
    `GATE_3_REFERENCES.by_frame` holds the realised per-frame LOCAL and
    SPECTRUM verdicts, the selected core, the spectrum points and the
    backups. This is measurement, not counterfactual: those rungs were
    calibrated under every frame.

**The counterfactual discipline.** A family the pooled screen rejected was
never calibrated, so *nothing* in this repository knows whether it would
have been LOCAL- or SPECTRUM-valid under any frame. Every such cell is
reported as ``NOT_IDENTIFIABLE`` and is never counted as a realised loss.
What can be measured on the rejected set is only its *size*: how many
(family, frame) cells a frame-aware screen would have promoted that the
pooled screen did not forward. What can be measured with realised outcomes
is the **forwarded** set, and that is where the load-bearing question is
answered: on rungs where both screens have an opinion and the truth is
known, does the frame-specific label carry information about per-frame
validity that the pooled label does not? If it does not, a frame-aware
screen has no measured case even if the rejected set is large.

Reads `REGIME_SCREEN`, `SECOND_PASS_SCREEN`, `GATE_2_CALIBRATION` (for the
allocation only) and `GATE_3_REFERENCES`. Refuses any scored row with more
than one present constraint, reads no stage past Gate 3, and names no
composed or interference quantity. Nothing is written to the evidence tree.

    python3 tools/v8_screen_frame_audit.py --root <pilot root> --model <key>

Writes `reports/dci1v8dev/screen_frame_audit.<root>.<model>.{md,json}`.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.errors import ProtocolError                            # noqa: E402
from dci1v7.protocol import constants as C                         # noqa: E402
from dci1v7.verifiers.constraints import Constraint, FAMILIES      # noqa: E402
from dci1v8dev.prescreen import screen as SCREEN                   # noqa: E402
from dci1v8dev.run import regime as REGIME                         # noqa: E402
from dci1v8dev.run import stages as S                              # noqa: E402
from dci1v8dev.run.execute import frame_of_block                   # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev"
STAGES_READ = (S.STAGE_REGIME, S.STAGE_SECOND_PASS, S.STAGE_GATE2, S.STAGE_GATE3)

#: The reporting convention this tool classifies with. It is **not** a
#: scientific threshold and admits nothing: it names, in advance, how the
#: printed counts map onto the four words the audit is asked for, and it is
#: keyed to quantities that are already registered --- §13.15's five
#: LOCAL-valid families and §13.13's minimum families per spectrum side ---
#: rather than to a number chosen after seeing the table. Every count it
#: reads is printed beside it so a reader can reclassify.
LOSS_CLASSES = ("NEGLIGIBLE_LOSS", "MODEST_LOSS", "MATERIAL_LOSS",
                "NOT_IDENTIFIABLE_FROM_CURRENT_DATA")


# --------------------------------------------------------------- reading
def _payload(path: pathlib.Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    return record.get("payload", record)


def _model_dir(root: pathlib.Path, model: str) -> pathlib.Path:
    for base in (root / "evidence" / "dci1v8", root / "dci1v8"):
        if (base / model).is_dir():
            return base / model
    raise SystemExit(f"no model tree for {model!r} under {root}")


def _record(model_dir: pathlib.Path, stage: str) -> dict[str, Any]:
    path = model_dir / stage / S.STAGE_RECORD_FILES[stage]
    if not path.exists():
        raise SystemExit(f"{stage} has no record at {path}: run the pilot first")
    return _payload(path)


def _screen_rows(model_dir: pathlib.Path) -> list[dict[str, Any]]:
    path = model_dir / S.STAGE_REGIME / "backend_runs" / "ladder" / "scored.jsonl"
    if not path.exists():
        raise SystemExit(f"no screen rows at {path}")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    for row in rows:
        present = [s for s in row["scores"] if s.get("present")]
        if len(present) > 1:
            raise ProtocolError(
                f"{row['row_id']}: {len(present)} present constraints; this "
                "audit reads load-0 and load-1 rows only and no composed cell "
                "exists before a freeze")
    return rows


# ------------------------------------------- the frame-specific screen
def frame_screen(rows: Sequence[Mapping[str, Any]],
                 counts: Sequence[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    """The production screen re-run on each frame's own six topics.

    Same kernels, same config, same thresholds as the stage: only the row
    set changes. ``counts`` is the stage's recorded ``prescreen_table``,
    used for the rung list so the frame screens see exactly the rungs the
    pooled screen saw.
    """
    rungs = [Constraint(row["kind"], int(row["severity"]),
                        reserve=bool(row.get("reserve")))
             for row in counts]
    out: dict[int, dict[str, Any]] = {}
    for frame in S.FRAMES:
        frame_rows = [r for r in rows if frame_of_block(r) == frame]
        if not frame_rows:
            continue
        per_frame = REGIME.prescreen_counts(frame_rows, rungs)
        table, a_grid = REGIME.prescreen_input(per_frame)
        result = SCREEN.screen_families(table, a_grid)
        out[frame] = {
            "n_rows": len(frame_rows),
            "n_topics": len({r["topic_id"] for r in frame_rows}),
            "statuses": result["statuses"],
            "labels": result["labels"],
            "iota_a_point": result["iota_a_prescreen_point"],
            "score_spectrum": {k: v["score_spectrum"]
                               for k, v in result["families"].items()},
            "score_local": {k: v["score_local"]
                            for k, v in result["families"].items()},
            "status_by_family": {k: v["status"]
                                 for k, v in result["families"].items()},
            "labels_by_family": {k: list(v["labels"])
                                 for k, v in result["families"].items()},
        }
    return out


# ------------------------------------------------------------- the audit
def _forwarded(second_pass: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    labels = {str(x) for x in second_pass["forwarded_set"]}
    families = {label.rpartition(":")[0] for label in labels}
    return labels, {f for f in families if f in FAMILIES}


def _realised(gate3: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    """Per frame, what the calibrated rungs actually did. Measurement."""
    out: dict[int, dict[str, Any]] = {}
    for frame in gate3.get("supported_frames", []):
        block = gate3["by_frame"][str(frame)]
        local = block.get("local") or {}
        spectrum = block.get("spectrum") or {}
        survival = block.get("survival") or {}
        out[int(frame)] = {
            "local_valid": sorted(k for k, v in local.items() if v.get("passed")),
            "spectrum_valid": sorted(k for k, v in spectrum.items()
                                     if v.get("passed")),
            "local_valid_families": sorted(survival.get("local_valid_families") or ()),
            "core_references": sorted((block.get("core_references") or {})),
            "backups": sorted(str(b) for b in
                              ((block.get("backups") or {}).get("backups") or ())),
            "spectrum_below": sorted(survival.get("spectrum_valid_below") or ()),
            "spectrum_above": sorted(survival.get("spectrum_valid_above") or ()),
            "state": block.get("state"),
            "local_first_failing": {k: v.get("first_failing_component")
                                    for k, v in local.items()},
            "spectrum_first_failing": {k: v.get("first_failing_component")
                                       for k, v in spectrum.items()},
        }
    return out


def audit(model: str, *, regime: Mapping[str, Any],
          second_pass: Mapping[str, Any], gate2: Mapping[str, Any],
          gate3: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
          ) -> dict[str, Any]:
    pooled_statuses = regime["screen_statuses"]
    pooled_labels = regime["screen_labels"]
    pooled_status_by_family = {k: status
                               for status, ks in pooled_statuses.items()
                               for k in ks}
    pooled_label_by_family = {k: [lab for lab, ks in pooled_labels.items()
                                  if k in ks]
                              for k in pooled_status_by_family}
    by_frame = frame_screen(rows, regime["prescreen_table"])
    fwd_labels, fwd_families = _forwarded(second_pass)
    realised = _realised(gate3)
    supported = sorted(realised)

    # ---- 1. promising cells, and which of them the pooled screen carried
    cells: list[dict[str, Any]] = []
    for frame, screen in sorted(by_frame.items()):
        for family, status in sorted(screen["status_by_family"].items()):
            labels = screen["labels_by_family"][family]
            promising = (status == SCREEN.SCREEN_ACCEPT) or bool(labels)
            carried = family in fwd_families
            cells.append({
                "frame": frame, "family": family,
                "frame_status": status, "frame_labels": labels,
                "pooled_status": pooled_status_by_family.get(family),
                "pooled_labels": pooled_label_by_family.get(family, []),
                "frame_promising": promising,
                "forwarded_by_pooled_screen": carried,
                "lost": bool(promising and not carried),
                "over_forwarded": bool(carried and not promising),
                "score_spectrum": screen["score_spectrum"].get(family),
                "score_local": screen["score_local"].get(family),
            })

    lost = [c for c in cells if c["lost"]]
    promising = [c for c in cells if c["frame_promising"]]
    by_frame_counts = {
        str(frame): {
            "n_families_screened": sum(1 for c in cells if c["frame"] == frame),
            "n_frame_promising": sum(1 for c in promising if c["frame"] == frame),
            "n_lost": sum(1 for c in lost if c["frame"] == frame),
            "lost_families": sorted(c["family"] for c in lost
                                    if c["frame"] == frame),
            "n_over_forwarded": sum(1 for c in cells
                                    if c["frame"] == frame and c["over_forwarded"]),
        } for frame in sorted(by_frame)}
    by_family_counts: dict[str, Any] = {}
    for c in cells:
        entry = by_family_counts.setdefault(
            c["family"], {"frames_promising": [], "frames_lost": [],
                          "forwarded": c["forwarded_by_pooled_screen"],
                          "pooled_status": c["pooled_status"]})
        if c["frame_promising"]:
            entry["frames_promising"].append(c["frame"])
        if c["lost"]:
            entry["frames_lost"].append(c["frame"])

    # ---- 2. the measured half: does the frame label predict per-frame
    #         validity better than the pooled label, on rungs where the
    #         truth is known (the forwarded set, calibrated under every frame)?
    predictive: dict[str, Any] = {"per_frame": {}, "rule":
                                  "on the forwarded families only --- the "
                                  "ones every frame calibrated --- the "
                                  "frame-specific and the pooled screen "
                                  "label are each scored against the frame's "
                                  "realised Gate-3 verdicts. No "
                                  "counterfactual: both labels and the truth "
                                  "exist for every cell counted here"}
    for frame in supported:
        screen = by_frame.get(frame)
        if screen is None:
            continue
        truth_local = {lab.rpartition(":")[0]
                       for lab in realised[frame]["local_valid"]}
        truth_spectrum = {lab.rpartition(":")[0]
                          for lab in realised[frame]["spectrum_valid"]}
        rowsp = []
        for family in sorted(fwd_families):
            if family not in screen["status_by_family"]:
                continue
            rowsp.append({
                "family": family,
                "frame_spectrum_label": SCREEN.SPECTRUM_LABEL in
                                        screen["labels_by_family"][family],
                "pooled_spectrum_label": family in
                                         pooled_labels.get(SCREEN.SPECTRUM_LABEL, []),
                "frame_local_label": SCREEN.LOCAL_LABEL in
                                     screen["labels_by_family"][family],
                "pooled_local_label": family in
                                      pooled_labels.get(SCREEN.LOCAL_LABEL, []),
                "realised_spectrum_valid": family in truth_spectrum,
                "realised_local_valid": family in truth_local,
            })

        def _score(pred: str, truth: str) -> dict[str, Any]:
            tp = sum(1 for r in rowsp if r[pred] and r[truth])
            fp = sum(1 for r in rowsp if r[pred] and not r[truth])
            fn = sum(1 for r in rowsp if not r[pred] and r[truth])
            tn = sum(1 for r in rowsp if not r[pred] and not r[truth])
            return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                    "agreement": (tp + tn) / len(rowsp) if rowsp else None,
                    "recall": tp / (tp + fn) if (tp + fn) else None}

        predictive["per_frame"][str(frame)] = {
            "n_forwarded_families_scored": len(rowsp),
            "n_realised_local_valid_families": len(truth_local & fwd_families),
            "n_realised_spectrum_valid_families": len(truth_spectrum & fwd_families),
            "spectrum": {"frame_label": _score("frame_spectrum_label",
                                               "realised_spectrum_valid"),
                         "pooled_label": _score("pooled_spectrum_label",
                                                "realised_spectrum_valid")},
            "local": {"frame_label": _score("frame_local_label",
                                            "realised_local_valid"),
                      "pooled_label": _score("pooled_local_label",
                                             "realised_local_valid")},
            "disagreements": sorted(
                r["family"] for r in rowsp
                if r["frame_spectrum_label"] != r["pooled_spectrum_label"]
                or r["frame_local_label"] != r["pooled_local_label"]),
        }

    # ---- 3. what a lost cell's downstream standing is: unknowable
    not_identifiable = {
        "n_lost_cells": len(lost),
        "n_lost_families": len({c["family"] for c in lost}),
        "downstream_validity": "NOT_IDENTIFIABLE",
        "why": "a family the pooled screen did not forward was never "
               "calibrated, so no record in this study says whether any of "
               "its rungs would have been LOCAL-valid, SPECTRUM-valid, "
               "selected as core, admitted as a backup, or useful below or "
               "above A under any frame. This audit therefore counts lost "
               "cells and never credits them with a downstream outcome",
    }

    # ---- 4. the classification
    classification = _classify(lost=lost, by_frame_counts=by_frame_counts,
                               predictive=predictive, realised=realised,
                               supported=supported)

    return {
        "model_key": model,
        "stages_read": list(STAGES_READ),
        "reads_no_composed_outcome": True,
        "calibration_allocation": gate2.get("calibration_allocation"),
        "screen_shape": {
            "topics": C.N_PRESCREEN, "draws": C.LADDER_SCREEN_DRAWS,
            "topics_per_frame": C.N_PRESCREEN // C.N_WORDINGS,
            "note": "the pooled screen is a budget rule "
                    "(V8_FRAME_CONDITIONING.md §5); the frame screens below "
                    "are what the same production kernels say on a frame's "
                    "own six topics"},
        "pooled": {"statuses": pooled_statuses, "labels": pooled_labels,
                   "n_forwarded_rungs": len(fwd_labels),
                   "n_forwarded_families": len(fwd_families),
                   "forwarded_families": sorted(fwd_families)},
        "by_frame_screen": {str(k): v for k, v in by_frame.items()},
        "supported_frames": supported,
        "cells": cells,
        "by_frame_counts": by_frame_counts,
        "by_family_counts": by_family_counts,
        "predictive_on_the_forwarded_set": predictive,
        "lost_cells_downstream": not_identifiable,
        "classification": classification,
    }


def _classify(*, lost, by_frame_counts, predictive, realised, supported
              ) -> dict[str, Any]:
    """Map the counts onto the four words, by a convention fixed here."""
    n_lost_families = len({c["family"] for c in lost})
    frames_with_loss = [f for f, v in by_frame_counts.items() if v["n_lost"]]
    # does the frame label beat the pooled one where the truth is known?
    gains = []
    for frame, block in predictive["per_frame"].items():
        for arm in ("spectrum", "local"):
            frame_score = block[arm]["frame_label"]["agreement"]
            pooled_score = block[arm]["pooled_label"]["agreement"]
            if frame_score is not None and pooled_score is not None:
                gains.append({"frame": frame, "arm": arm,
                              "frame_agreement": frame_score,
                              "pooled_agreement": pooled_score,
                              "frame_better": frame_score > pooled_score})
    n_better = sum(1 for g in gains if g["frame_better"])
    # a frame that failed its arm *for want of families* is the only place a
    # lost family could have mattered; count them.
    starved = sorted(
        f for f in supported
        if len(realised[f]["local_valid_families"]) < S.MIN_LOCAL_FAMILIES
        or len(realised[f]["spectrum_below"]) < C.SUPPORT_MIN_BELOW
        or len(realised[f]["spectrum_above"]) < C.SUPPORT_MIN_ABOVE)
    if not lost:
        verdict = "NEGLIGIBLE_LOSS"
        why = ("no frame's own screen promotes a family the pooled screen "
               "did not forward; the pooled budget rule loses nothing a "
               "frame-aware screen would have found")
    elif n_lost_families >= S.MIN_LOCAL_FAMILIES and starved:
        verdict = "MATERIAL_LOSS"
        why = (f"{n_lost_families} families are promising to some frame's own "
               f"screen and were not forwarded, at least §13.15's minimum of "
               f"{S.MIN_LOCAL_FAMILIES}, while frames {starved} failed an arm "
               "for want of families. Their downstream validity is still not "
               "identifiable; what is measured is that the loss is large "
               "enough to matter if any of it were valid")
    else:
        verdict = "MODEST_LOSS"
        why = (f"{n_lost_families} family/families are promising to some "
               f"frame's own screen and were not forwarded (frames "
               f"{frames_with_loss}), fewer than §13.15's minimum of "
               f"{S.MIN_LOCAL_FAMILIES}, so even if every one were valid it "
               "could not by itself identify an arm that failed")
    return {
        "vocabulary": list(LOSS_CLASSES),
        "verdict": verdict,
        "why": why,
        "caveat": "\"failed an arm for want of families\" counts a frame "
                  "with too few LOCAL-valid families or too few spectrum "
                  "points on a side. At an allocation where the coordinate "
                  "precision floor is itself refusing rungs, every frame is "
                  "starved for that reason and the condition carries no "
                  "information about the reference pool. Read this verdict "
                  "beside the LOCAL/SPECTRUM diagnosis: it is informative "
                  "only where precision is no longer the binding constraint",
        "convention": "fixed in tools/v8_screen_frame_audit.py before the "
                      "counts are read, keyed to registered minima "
                      "(§13.15's five LOCAL-valid families, §13.13's minimum "
                      "points per spectrum side). It is a reporting "
                      "convention, not a scientific threshold: it admits "
                      "nothing and every count it reads is printed",
        "n_lost_cells": len(lost),
        "n_lost_families": n_lost_families,
        "frames_with_loss": frames_with_loss,
        "frames_starved_of_families": starved,
        "predictive_comparisons": gains,
        "n_comparisons_where_the_frame_label_beats_the_pooled_one": n_better,
        "n_comparisons": len(gains),
        "recommendation_rule": "a frame-aware screen is recommended only "
                               "when the loss is MATERIAL *and* the frame "
                               "label carries information the pooled label "
                               "does not where the truth is known",
    }


# ----------------------------------------------------------- the report
def markdown(rep: Mapping[str, Any]) -> str:
    out: list[str] = []
    p = out.append
    p("# DCI-1 v8 — is the frame-pooled early screen losing frame-specific candidates?\n")
    p("> Generated by `dci1/tools/v8_screen_frame_audit.py`. Do not edit by hand.\n")
    p("> **Outcome-blind and retrospective.** Reads the regime screen's own "
      "scored rows, the second pass's forwarded set and Gate 3's per-frame "
      "verdicts. No composed or interference outcome is read or named. A "
      "family the pooled screen did not forward was never calibrated, so its "
      "downstream validity is reported as `NOT_IDENTIFIABLE` and is never "
      "counted as a realised loss.\n")
    alloc = rep.get("calibration_allocation") or {}
    # a record written before the allocation amendment carries no block; one
    # pass over the calibration topics is what ran.
    per_frame = alloc.get("topics_per_frame", C.N_CALIBRATION // C.N_WORDINGS)
    p(f"Model `{rep['model_key']}`; screen {rep['screen_shape']['topics']} topics "
      f"x {rep['screen_shape']['draws']} draw "
      f"({rep['screen_shape']['topics_per_frame']} topics per frame); "
      f"calibration at {per_frame} topics per frame over "
      f"{alloc.get('passes', 1)} pass(es). Supported frames "
      f"{rep['supported_frames']}.\n")

    cl = rep["classification"]
    p(f"## Verdict: `{cl['verdict']}`\n")
    p(cl["why"] + "\n")
    p(f"- lost (family, frame) cells: **{cl['n_lost_cells']}**; distinct "
      f"families: **{cl['n_lost_families']}**")
    p(f"- frames with any loss: {cl['frames_with_loss'] or '—'}")
    p(f"- frames that failed an arm for want of families: "
      f"{cl['frames_starved_of_families'] or '—'}")
    p(f"- comparisons where the frame-specific label beats the pooled one on "
      f"realised per-frame validity: "
      f"**{cl['n_comparisons_where_the_frame_label_beats_the_pooled_one']} of "
      f"{cl['n_comparisons']}**")
    p(f"- recommendation rule: {cl['recommendation_rule']}\n")

    p("## 1. What each frame's own screen says, against the pooled one\n")
    p("| frame | families screened | promising to this frame | not forwarded (lost) | forwarded but not promising here |")
    p("|---|---:|---:|---:|---:|")
    for frame, v in sorted(rep["by_frame_counts"].items()):
        p(f"| f{frame} | {v['n_families_screened']} | {v['n_frame_promising']} | "
          f"{v['n_lost']} ({', '.join(v['lost_families']) or '—'}) | "
          f"{v['n_over_forwarded']} |")
    p("")

    p("## 2. Families a frame's own screen promotes, by family\n")
    p("| family | pooled status | forwarded? | frames promoting it | frames where it is lost |")
    p("|---|---|---|---|---|")
    for family, v in sorted(rep["by_family_counts"].items()):
        if not v["frames_promising"] and not v["frames_lost"]:
            continue
        p(f"| {family} | {v['pooled_status']} | "
          f"{'yes' if v['forwarded'] else 'no'} | "
          f"{v['frames_promising'] or '—'} | {v['frames_lost'] or '—'} |")
    p("")

    p("## 3. The measured half: does the frame label know something the pooled label does not?\n")
    p(rep["predictive_on_the_forwarded_set"]["rule"] + "\n")
    p("| frame | arm | label | tp | fp | fn | tn | agreement | recall |")
    p("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for frame, block in sorted(rep["predictive_on_the_forwarded_set"]["per_frame"].items()):
        for arm in ("spectrum", "local"):
            for which in ("frame_label", "pooled_label"):
                s = block[arm][which]
                agree = "—" if s["agreement"] is None else f"{s['agreement']:.2f}"
                rec = "—" if s["recall"] is None else f"{s['recall']:.2f}"
                p(f"| f{frame} | {arm} | {which.replace('_', ' ')} | {s['tp']} | "
                  f"{s['fp']} | {s['fn']} | {s['tn']} | {agree} | {rec} |")
    p("")
    p("Families whose frame-specific and pooled labels disagree, per frame:\n")
    for frame, block in sorted(rep["predictive_on_the_forwarded_set"]["per_frame"].items()):
        p(f"- f{frame}: {', '.join(block['disagreements']) or 'none'} "
          f"({block['n_realised_local_valid_families']} families realised "
          f"LOCAL-valid, {block['n_realised_spectrum_valid_families']} "
          f"SPECTRUM-valid)")
    p("")

    nid = rep["lost_cells_downstream"]
    p("## 4. What this audit cannot say\n")
    p(nid["why"] + f" ({nid['n_lost_cells']} cells, "
      f"{nid['n_lost_families']} families).\n")
    return "\n".join(out) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    model_dir = _model_dir(root, args.model)
    rep = audit(
        args.model,
        regime=_record(model_dir, S.STAGE_REGIME),
        second_pass=_record(model_dir, S.STAGE_SECOND_PASS),
        gate2=_record(model_dir, S.STAGE_GATE2),
        gate3=_record(model_dir, S.STAGE_GATE3),
        rows=_screen_rows(model_dir))
    rep["root"] = str(root)
    out = pathlib.Path(args.out) if args.out else REPORTS
    out.mkdir(parents=True, exist_ok=True)
    # named by root as well as model: a later allocation's report must not
    # overwrite an earlier one's, and the file name should say which run it
    # describes.
    stem = f"screen_frame_audit.{root.name}.{args.model}"
    (out / f"{stem}.json").write_text(
        json.dumps(rep, indent=1, sort_keys=True) + "\n")
    (out / f"{stem}.md").write_text(markdown(rep))
    print(f"wrote {out / (stem + '.md')}")
    print(f"verdict: {rep['classification']['verdict']} "
          f"({rep['classification']['n_lost_cells']} lost cells, "
          f"{rep['classification']['n_lost_families']} families)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
