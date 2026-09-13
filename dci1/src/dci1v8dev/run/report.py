"""Stage 9, ``PILOT_REPORT``: the four prospective criteria on the records,
per frame. Approach A (``dci1/docs/V8_FRAME_CONDITIONING.md``).

Reads the signed records of every earlier stage and evaluates the criteria
the manifest bound --- nothing is generated, nothing is re-estimated, and
no threshold is read from anywhere but the registration record. Each
decided criterion is evaluated on every frame Gate 2 supported and
recorded per frame; the run-level ``passed`` follows
``stages.REPORT_AGGREGATION`` ("at least one supported frame passes") with
every frame's verdict beside it. The report says which criteria held on
which frames, and what the freeze decision can and cannot rest on; it never
says the effect exists or that v8 works.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C

from dci1v8dev import rules as R
from dci1v8dev.run import FRAME_DOCUMENT
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run.execute import UNCONSTRAINED_ARM
from dci1v8dev.run.lifecycle import StageOutcome, run_stage

__all__ = ["pilot_payload", "run_report", "evaluate_criteria", "aggregate"]


def aggregate(by_frame: Mapping[str, bool]) -> dict[str, Any]:
    """The run-level verdict over the supported frames' verdicts."""
    passing = sorted(int(w) for w, ok in by_frame.items() if ok)
    failing = sorted(int(w) for w, ok in by_frame.items() if not ok)
    return {"passed": bool(passing),
            "frames_passing": passing, "frames_failing": failing,
            "passed_on_every_supported_frame": not failing and bool(passing),
            "aggregation": S.REPORT_AGGREGATION}


def evaluate_criteria(*, registration: Mapping[str, Any],
                      regime: Mapping[str, Any],
                      second_pass: Mapping[str, Any],
                      gate1: Mapping[str, Any], gate2: Mapping[str, Any],
                      gate3: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    supported = [int(w) for w in gate2["supported_frames"]]
    g3_frames = gate3["by_frame"]
    g2_frames = gate2["by_frame"]

    # 1. WORDING_DIAGNOSTIC --- the four frames separately, at every basis
    # that measured them; no pass/fail rule exists, so `passed` is None. The
    # wording policy was decided on 2026-08-30 (frame = condition); the
    # diagnostic stays descriptive and the per-frame states say what each
    # frame identified.
    def _ladder_classes(ladders: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        return {frame: {"n_families": len(fams),
                        "classes": {k: sorted(f for f, d in fams.items()
                                              if d.get("ladder_class") == k)
                                    for k in ("STRONG_LADDER",
                                              "USABLE_NOISY_LADDER",
                                              "FLAT_LADDER",
                                              "NON_MONOTONIC_LADDER")}}
                for frame, fams in sorted(ladders.items())}

    stability_cal = gate2["split_stability_by_frame"]
    stability_screen = gate1.get("stability_screen_vs_second_pass")
    out["WORDING_DIAGNOSTIC"] = {
        "passed": None,
        "judgment": "DESCRIPTIVE_ONLY",
        "wording_policy": registration.get("wording_policy"),
        "frame_conditioning": gate2["frame_conditioning"]["policy"],
        "frames_measured_separately": True,
        "frame_states": gate3["frame_states"],
        "operating_points_by_frame": {
            str(w): {"status": g2_frames[str(w)]["status"],
                     "n_star": g2_frames[str(w)].get("n_star"),
                     "m_star": g2_frames[str(w)].get("m_star"),
                     "iota_a": g2_frames[str(w)].get("iota_a"),
                     "unsupported_reason": g2_frames[str(w)].get("unsupported_reason")}
            for w in S.FRAMES},
        "ladders_per_frame": {
            "calibration": _ladder_classes(gate2["ladders_by_frame_pooled"]),
            "screen": _ladder_classes(gate1["ladders_by_frame_screen"])},
        "stability_across_fresh_topics": {
            "calibration_splits": {k: stability_cal[k] for k in
                                   ("n_compared", "n_inside_bound",
                                    "share_inside_bound", "reference_bound")},
            "screen_vs_second_pass": ({k: stability_screen[k] for k in
                                       ("n_compared", "n_inside_bound",
                                        "share_inside_bound")}
                                      if stability_screen else None)},
        "wording_dependence": {
            "calibration": gate2["wording_dependence_pooled"],
            "screen": gate1["wording_dependence_screen"]},
        "survival_by_frame": {
            str(w): {k: g3_frames[str(w)]["survival"][k] for k in
                     ("n_local_valid_families", "spectrum_pool_ok",
                      "core_identified", "coverage_identified")}
            for w in supported},
        "wording_sensitive_rungs_by_frame": {
            str(w): g3_frames[str(w)]["wording_sensitive_rungs"]["by_class"]
            for w in supported},
        "sensitive_rungs_touching_reference_set_by_frame": {
            str(w): g3_frames[str(w)]["wording_sensitive_rungs"]["touching_reference_set"]
            for w in supported},
        "frame_reliability_descriptive": gate1["frame_reliability"],
        "reference_bound": S.WORDING_REFERENCE_BOUND,
        "rule": "no pass/fail rule: the per-frame tables are on the Gate-1 "
                "and Gate-2 records; the wording policy is decided (the "
                "frame is part of the experimental condition, "
                f"{FRAME_DOCUMENT}) and the cross-frame comparison is the "
                "secondary analysis",
    }

    # 2. LADDER_COVERAGE --- the second pass resolved within the batch bound
    # and the retention carried both extremes for at least two spectrum
    # families (frame-free: a measurement budget), and, per frame,
    # calibration found a spectrum-valid pool with two points per side from
    # two families.
    plan_frames = (gate2["calibration_population"].get("forwarding_plan") or {}
                   ).get("by_frame") or {}
    n_batches = second_pass["n_batches"]
    ambiguous = second_pass.get("resolved_at_max") or {}
    both_by_frame, reaching_by_frame, screen_ok_by_frame = {}, {}, {}
    for w in supported:
        geometry = (plan_frames.get(str(w)) or {}).get("retention", {}).get(
            "spectrum_geometry") or {}
        both_by_frame[str(w)] = sorted(
            k for k, g in geometry.items()
            if g.get("carries_hard_extreme") and g.get("carries_easy_extreme"))
        reaching_by_frame[str(w)] = sorted(
            k for k, g in geometry.items()
            if g.get("reaches_below_offset") and g.get("reaches_above_offset"))
        screen_ok_by_frame[str(w)] = bool(
            n_batches <= R.RESCREEN_MAX_BATCHES
            and len(reaching_by_frame[str(w)]) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE)
    ladder_by_frame = {
        str(w): bool(screen_ok_by_frame[str(w)]
                     and g3_frames[str(w)]["survival"]["spectrum_pool_ok"])
        for w in supported}
    out["LADDER_COVERAGE"] = {
        **aggregate(ladder_by_frame),
        "by_frame": {
            str(w): {"passed": ladder_by_frame[str(w)],
                     "screen_and_second_pass_ok": screen_ok_by_frame[str(w)],
                     "spectrum_families_forwarded":
                         (plan_frames.get(str(w)) or {}).get("spectrum_families"),
                     "families_carrying_both_extremes": both_by_frame[str(w)],
                     "families_reaching_both_offsets_at_screen":
                         reaching_by_frame[str(w)],
                     "spectrum_pool_ok": g3_frames[str(w)]["survival"]["spectrum_pool_ok"],
                     "spectrum_valid_families_below":
                         g3_frames[str(w)]["survival"]["spectrum_valid_families_below"],
                     "spectrum_valid_families_above":
                         g3_frames[str(w)]["survival"]["spectrum_valid_families_above"],
                     "n_spectrum_valid_below":
                         len(g3_frames[str(w)]["survival"]["spectrum_valid_below"]),
                     "n_spectrum_valid_above":
                         len(g3_frames[str(w)]["survival"]["spectrum_valid_above"])}
            for w in supported},
        "screen_and_second_pass_ok_by_frame": screen_ok_by_frame,
        "second_pass_batches": n_batches,
        "max_batches": R.RESCREEN_MAX_BATCHES,
        "ambiguous_at_max": {str(w): sorted(v) for w, v in ambiguous.items()},
        "extension_measured": gate2["extension"]["measured"],
        "retention_policy": gate2["calibration_population"].get("policy"),
        "rule": f"batches <= {R.RESCREEN_MAX_BATCHES}; per frame, >= "
                f"{C.SUPPORT_MIN_FAMILIES_PER_SIDE} forwarded spectrum "
                "families reaching both offsets at the screen against the "
                "frame's own iota_A(f); per frame, a "
                f"spectrum-valid pool >= {C.SUPPORT_MIN_BELOW}/{C.SUPPORT_MIN_ABOVE} "
                f"points from >= {C.SUPPORT_MIN_FAMILIES_PER_SIDE} families per side",
    }

    # 3. CHANCE_BASIS --- per frame, the table measured chance on the
    # unconstrained cell of the frame's own blocks, the column is not the
    # zero column, iota_A(f) is on the same basis; the screen likewise.
    chance_by_frame: dict[str, dict[str, Any]] = {}
    for w in supported:
        g2 = g2_frames[str(w)]
        basis = g2["chance_basis"]
        pooled = g2["calibration_rows"]["pooled"]
        values = [float(r["chance_compliance"]) for r in pooled]
        non_zero = sum(1 for v in values if v > 0)
        per_split_ok = all(entry.get("n_topics", 0) > 0
                           for entry in basis["per_split"].values())
        chance_by_frame[str(w)] = {
            "passed": bool(basis["cell"] == UNCONSTRAINED_ARM
                           and regime["chance_basis"]["cell"] == UNCONSTRAINED_ARM
                           and per_split_ok
                           and (non_zero > 0 or not values)
                           and g2["iota_a_basis"].startswith("§13.2")),
            "gate2_cell": basis["cell"], "gate2_per_split": basis["per_split"],
            "n_candidates": len(values),
            "n_candidates_with_nonzero_chance": non_zero,
            "n_withheld_degenerate": g2["n_candidates_withheld_degenerate"],
            "iota_a": g2["iota_a"], "kappa_a": g2["kappa_a"],
            "iota_a_all_absent_v7_basis": g2["iota_a_all_absent_v7_basis"],
            "iota_a_basis_discrepancy": abs(float(g2["iota_a"])
                                            - float(g2["iota_a_all_absent_v7_basis"])),
            "kappa_a_all_frames_blocks": g2["kappa_a_all_frames_blocks"],
        }
    out["CHANCE_BASIS"] = {
        **aggregate({w: v["passed"] for w, v in chance_by_frame.items()}),
        "by_frame": chance_by_frame,
        "screen_cell": regime["chance_basis"]["cell"],
        "rule": "chance measured on the unconstrained cell in the screen and, "
                "per frame, in every calibration split on the frame's own "
                "blocks; iota_A(f) on the same basis; the column is not "
                "identically zero",
    }

    # 4. REFERENCE_SURVIVAL --- per frame: §13.15 on the admissible basis,
    # the core by the registered kernel, the coverage gate, the backups.
    survival_by_frame: dict[str, dict[str, Any]] = {}
    for w in supported:
        s = g3_frames[str(w)]["survival"]
        survival_by_frame[str(w)] = {
            "passed": bool(s["meets_min_local_families"] and s["core_identified"]
                           and s["coverage_identified"] and s["meets_min_backups"]),
            "state": g3_frames[str(w)]["state"],
            # This criterion's `passed` spans both arms --- it requires the
            # spectrum coverage gate as well --- while LOCAL inclusion
            # (V8_FRAME_CONDITIONING.md §4d) is the LOCAL arm's three
            # requirements alone. Both are recorded so the two readings of
            # "survival" are never confused for one another.
            "local_supported": s["local_supported"],
            "local_unsupported_reason": s["local_unsupported_reason"],
            "n_local_valid_families": s["n_local_valid_families"],
            "local_valid_families": s["local_valid_families"],
            "core_identified": s["core_identified"],
            "core_references": s["core_references"],
            "coverage_identified": s["coverage_identified"],
            "coverage_reasons": s["coverage_reasons"],
            "projected_se_beta": s["projected_se_beta"],
            "projected_se_beta_at_full_allocation":
                s["projected_se_beta_at_full_allocation"],
            "n_blocks_projected": s["n_blocks_projected"],
            "selected_families": s["selected_families"],
            "n_spectrum_references": s["n_spectrum_references"],
            "backups": s["backups"], "n_backups": s["n_backups"],
        }
    out["REFERENCE_SURVIVAL"] = {
        **aggregate({w: v["passed"] for w, v in survival_by_frame.items()}),
        "by_frame": survival_by_frame,
        "min_local_families": S.MIN_LOCAL_FAMILIES,
        "min_backups": S.MIN_BACKUPS,
        "max_se_beta": R.SPECTRUM_MAX_SE_BETA,
        "n_blocks_per_frame": R.CONFIRMATORY_BLOCKS_PER_FRAME,
        "rule": f">= {S.MIN_LOCAL_FAMILIES} LOCAL-valid families, three core "
                "references by §13.8, selected coverage identified with the "
                f"projected SE(beta) <= {R.SPECTRUM_MAX_SE_BETA} at the frame's "
                f"{R.CONFIRMATORY_BLOCKS_PER_FRAME} blocks, >= {S.MIN_BACKUPS} "
                "admissible backups --- per frame. LOCAL *inclusion* "
                f"({FRAME_DOCUMENT} §4d) is the LOCAL arm's three "
                "requirements alone, without the coverage gate: see "
                "`local_supported` here and `local_eligibility` on the record",
    }
    return out


def _generations(regime: Mapping[str, Any], second_pass: Mapping[str, Any],
                 gate2: Mapping[str, Any], gate0: Mapping[str, Any]
                 ) -> dict[str, int]:
    screen_passes = int((regime.get("screen_allocation") or {}).get("passes") or 1)
    screen = C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS * (
        regime["n_rungs_measured"] + 1) * screen_passes
    caps = len(regime["cap_selection"]["truncation_by_cap"]) * C.N_PRESCREEN * 3
    grids_spec = gate2["grids"]
    n_topics = len(gate2["calibration_topic_ids"])
    # Every Gate-2 run is laid out over one pass per frame offset, so a
    # block count is the topic count times the passes (calibration.
    # calibration_blocks). Reading the record's own allocation rather than
    # a constant keeps this arithmetic true of the run it describes.
    allocation = gate2.get("calibration_allocation") or {}
    if not allocation.get("passes"):
        # `calibration_allocation` is a required Gate-2 contract field, so a
        # record without it is malformed rather than old. Defaulting to one
        # pass here would silently under-count the run's generations by the
        # pass factor, which is exactly the kind of stale number this
        # accounting exists to catch.
        raise ProtocolError(
            f"{S.STAGE_GATE2} did not record a calibration_allocation with a "
            "pass count; the report cannot state a generation total it "
            "cannot derive")
    passes = int(allocation["passes"])
    n_blocks = n_topics * passes
    cells = (len(grids_spec["A"]) + 1) + (len(grids_spec["B"]) + 1) + (
        (len(grids_spec["B_extension"]) + 1)
        if grids_spec["focal_extension_measured"] else 0)
    grids = n_blocks * C.M_CAL * cells
    population = gate2["calibration_population"]
    # Per-frame forwarding: each frame's rungs on that frame's blocks, so
    # the candidate rows are what the record counted, not union x blocks.
    candidates = int(population.get("n_candidate_rows",
                                    n_blocks * C.M_CAL * population["n_measured"]))
    comparator = int(population.get("n_comparator_rows", 0))
    extension = gate2["extension"]["n_rows"]
    return {"gate0": gate0["rows"], "cap_selection": caps, "screen": screen,
            "screen_passes": screen_passes,
            "second_pass": second_pass["cost_generations"],
            "calibration_passes": passes,
            "calibration_blocks_per_run": n_blocks,
            "calibration_grids": grids, "calibration_candidates": candidates,
            "calibration_comparator": comparator,
            "calibration_extension": extension,
            "total": gate0["rows"] + caps + screen + second_pass["cost_generations"]
            + grids + candidates + comparator + extension}


def pilot_payload(tree: ModelTree, *, producing_commit: str,
                  gate3_record: Mapping[str, Any]) -> dict[str, Any]:
    records = {stage: transitions.read_stage_record(tree, stage)
               for stage in S.STAGE_SEQUENCE[:-2]}
    gate2 = records[S.STAGE_GATE2]
    criteria = evaluate_criteria(
        registration=records[S.STAGE_REGISTERED],
        regime=records[S.STAGE_REGIME],
        second_pass=records[S.STAGE_SECOND_PASS],
        gate1=records[S.STAGE_GATE1], gate2=gate2,
        gate3=gate3_record)
    supported = [int(w) for w in gate2["supported_frames"]]
    meeting = sorted(w for w in supported
                     if all(criteria[k]["by_frame"][str(w)]["passed"]
                            for k in S.DECIDED_CRITERIA))
    failed = sorted(k for k in S.DECIDED_CRITERIA if not criteria[k]["passed"])
    open_judgments = sorted(k for k, v in criteria.items()
                            if v["passed"] is None)
    return {
        "stage": S.STAGE_REPORT,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_REPORT],
        "outcome": "PASS",
        "inputs": {stage: {"stage": stage} for stage in S.STAGE_SEQUENCE[:-1]},
        "producing_commit": producing_commit,
        "manifest_hash": records[S.STAGE_REGISTERED]["manifest_hash"],
        "frame_conditioning": gate2["frame_conditioning"],
        "frames": list(S.FRAMES),
        "supported_frames": supported,
        "unsupported_frames": gate2.get("unsupported_frames") or {},
        "frame_states": gate3_record["frame_states"],
        # The LOCAL inclusion verdict, carried from Gate 3 rather than
        # recomputed: which frames the LOCAL confirmatory arm would run, and
        # whether the model has the two independently supported frames the
        # rule requires (V8_FRAME_CONDITIONING.md §4d). Not a criterion --- it
        # decides inclusion, not whether the pilot passed --- so the
        # aggregation of §7 is untouched.
        "local_eligibility": gate3_record["local_eligibility"],
        "criteria": criteria,
        "criteria_order": list(S.PILOT_CRITERIA),
        "decided_criteria": list(S.DECIDED_CRITERIA),
        "aggregation": S.REPORT_AGGREGATION,
        "frames_meeting_all_decided_criteria": meeting,
        "frames_failing_some_decided_criterion": sorted(
            w for w in supported if w not in meeting),
        "all_decided_criteria_met": bool(meeting),
        "criteria_failed": failed,
        "open_judgments": open_judgments,
        "pilot_status": ("PILOT_DECIDED_CRITERIA_MET" if meeting
                         else "PILOT_DECIDED_CRITERIA_NOT_MET"),
        "wording_judgment": {
            "status": S.WORDING_POLICY_STATUS,
            "policy": S.WORDING_POLICY,
            "decided": "2026-08-30, researcher decision: the wording frame is "
                       "part of the experimental condition (Approach A, "
                       f"{FRAME_DOCUMENT}); no frame retained or discarded on "
                       "the diagnostic",
            "options": list(S.WORDING_POLICY_OPTIONS),
            "evidence_admissible": "solo, pre-screen and calibration records "
                                   "of this pilot; no composed outcome exists "
                                   "or may be inspected before the v8 design "
                                   "is frozen"},
        "estimands": gate3_record["estimands"],
        "generations": _generations(records[S.STAGE_REGIME],
                                    records[S.STAGE_SECOND_PASS],
                                    gate2, records[S.STAGE_GATE0]),
        "stage_record_hashes": {
            stage: fs.read_json(tree.stage_record(stage))["record_hash"]
            for stage in S.STAGE_SEQUENCE[:-1]},
        "what_this_licenses": (
            "a decision to freeze the v8 candidate rests on the three decided "
            "criteria above, evaluated per frame on this replication's signed "
            "records under the rules the manifest bound before any row "
            "existed; a freeze is per frame (a frame can be frozen with its "
            "own operating points and references, or the researcher can "
            "require agreement across frames), and the run-level status is "
            f"the '{S.REPORT_AGGREGATION}' aggregate, not a freeze rule; it is "
            "not evidence about the effect, and the spectrum arm's B+X / X+B "
            "cells are a post-freeze experiment this layer cannot generate"),
        "no_composed_cells": S.NO_COMPOSED_CELLS,
    }


def run_report(tree: ModelTree, *, producing_commit: str | None = None,
               environment_digest: str = "") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return run_stage(
        tree, S.STAGE_REPORT,
        compute=lambda previous: pilot_payload(
            tree, producing_commit=commit, gate3_record=previous),
        producing_commit=commit, environment_digest=environment_digest)
