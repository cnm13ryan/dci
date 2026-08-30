"""Stage 9, ``PILOT_REPORT``: the four prospective criteria on the records.

Reads the signed records of every earlier stage and evaluates the criteria
the manifest bound --- nothing is generated, nothing is re-estimated, and
no threshold is read from anywhere but the registration record. The report
says which criteria held, and what the freeze decision can and cannot rest
on; it never says the effect exists or that v8 works.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, gitinfo
from dci1v7.protocol import constants as C

from dci1v8dev import rules as R
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run.execute import UNCONSTRAINED_ARM
from dci1v8dev.run.lifecycle import StageOutcome, run_stage

__all__ = ["pilot_payload", "run_report", "evaluate_criteria"]


def evaluate_criteria(*, registration: Mapping[str, Any],
                      regime: Mapping[str, Any],
                      second_pass: Mapping[str, Any],
                      gate1: Mapping[str, Any], gate2: Mapping[str, Any],
                      gate3: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}

    # 1. FRAME_RELIABILITY --- Gate 1's verdict against the bound reference.
    frame = gate1["frame_criterion"]
    out["FRAME_RELIABILITY"] = {
        "passed": frame.get("passed"),
        "per_frame": frame.get("per_frame"),
        "best_v7_frame_share": frame.get("best_v7_frame_share"),
        "limit": frame.get("limit"),
        "margin": registration["frame_reliability_margin"],
        "second_pass": (gate1.get("frame_criterion_second_pass") or {}).get("passed"),
        "reason": frame.get("reason"),
    }

    # 2. LADDER_COVERAGE --- the second pass resolved within the batch bound,
    # the retention carried both extremes for at least two spectrum
    # families, and calibration found a spectrum-valid pool with two points
    # per side from two families.
    retention = second_pass["retention"]
    geometry = retention.get("spectrum_geometry") or {}
    both = sorted(k for k, g in geometry.items()
                  if g.get("carries_hard_extreme") and g.get("carries_easy_extreme"))
    reaching = sorted(k for k, g in geometry.items()
                      if g.get("reaches_below_offset") and g.get("reaches_above_offset"))
    survival = gate3["survival"]
    n_batches = second_pass["n_batches"]
    ambiguous = second_pass.get("resolved_at_max") or {}
    out["LADDER_COVERAGE"] = {
        "passed": bool(n_batches <= R.RESCREEN_MAX_BATCHES
                       and len(reaching) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE
                       and survival["spectrum_pool_ok"]),
        "spectrum_families_forwarded": retention.get("spectrum_families"),
        "families_carrying_both_extremes": both,
        "families_reaching_both_offsets_at_screen": reaching,
        "second_pass_batches": n_batches,
        "max_batches": R.RESCREEN_MAX_BATCHES,
        "ambiguous_at_max": sorted(ambiguous),
        "spectrum_valid_families_below": survival["spectrum_valid_families_below"],
        "spectrum_valid_families_above": survival["spectrum_valid_families_above"],
        "n_spectrum_valid_below": len(survival["spectrum_valid_below"]),
        "n_spectrum_valid_above": len(survival["spectrum_valid_above"]),
        "extension_measured": gate2["extension"]["measured"],
        "rule": f"batches <= {R.RESCREEN_MAX_BATCHES}; >= "
                f"{C.SUPPORT_MIN_FAMILIES_PER_SIDE} forwarded spectrum "
                "families reaching both offsets at the screen; spectrum-valid "
                f"pool >= {C.SUPPORT_MIN_BELOW}/{C.SUPPORT_MIN_ABOVE} points "
                f"from >= {C.SUPPORT_MIN_FAMILIES_PER_SIDE} families per side",
    }

    # 3. CHANCE_BASIS --- both tables measured chance on the unconstrained
    # cell, the column is not the zero column, iota_A is on the same basis.
    g2_basis = gate2["chance_basis"]
    pooled = gate2["calibration_rows"]["pooled"]
    chance_values = [float(r["chance_compliance"]) for r in pooled]
    non_zero = sum(1 for v in chance_values if v > 0)
    per_split_ok = all(
        entry.get("n_topics", 0) > 0 for entry in g2_basis["per_split"].values())
    out["CHANCE_BASIS"] = {
        "passed": bool(g2_basis["cell"] == UNCONSTRAINED_ARM
                       and regime["chance_basis"]["cell"] == UNCONSTRAINED_ARM
                       and per_split_ok
                       and (non_zero > 0 or not chance_values)
                       and gate2["iota_a_basis"].startswith("§13.2")),
        "gate2_cell": g2_basis["cell"],
        "screen_cell": regime["chance_basis"]["cell"],
        "gate2_per_split": g2_basis["per_split"],
        "n_candidates": len(chance_values),
        "n_candidates_with_nonzero_chance": non_zero,
        "n_withheld_degenerate": gate2["n_candidates_withheld_degenerate"],
        "iota_a": gate2["iota_a"],
        "iota_a_all_absent_v7_basis": gate2["iota_a_all_absent_v7_basis"],
        "iota_a_basis_discrepancy": abs(float(gate2["iota_a"])
                                        - float(gate2["iota_a_all_absent_v7_basis"])),
        "rule": "chance measured on the unconstrained cell in the screen and "
                "in every calibration split; iota_A on the same basis; the "
                "column is not identically zero",
    }

    # 4. REFERENCE_SURVIVAL --- §13.15 on the admissible basis, the core by
    # the registered kernel, the coverage gate, the backups.
    out["REFERENCE_SURVIVAL"] = {
        "passed": bool(survival["meets_min_local_families"]
                       and survival["core_identified"]
                       and survival["coverage_identified"]
                       and survival["meets_min_backups"]),
        "n_local_valid_families": survival["n_local_valid_families"],
        "min_local_families": survival["min_local_families"],
        "local_valid_families": survival["local_valid_families"],
        "core_identified": survival["core_identified"],
        "core_references": survival["core_references"],
        "coverage_identified": survival["coverage_identified"],
        "coverage_reasons": survival["coverage_reasons"],
        "projected_se_beta": survival["projected_se_beta"],
        "max_se_beta": R.SPECTRUM_MAX_SE_BETA,
        "selected_families": survival["selected_families"],
        "n_spectrum_references": survival["n_spectrum_references"],
        "backups": survival["backups"],
        "min_backups": S.MIN_BACKUPS,
    }
    return out


def _generations(regime: Mapping[str, Any], second_pass: Mapping[str, Any],
                 gate2: Mapping[str, Any], gate0: Mapping[str, Any]
                 ) -> dict[str, int]:
    screen = C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS * (
        regime["n_rungs_measured"] + 1)
    caps = len(regime["cap_selection"]["truncation_by_cap"]) * C.N_PRESCREEN * 3
    n_topics = len(gate2["calibration_topic_ids"])
    grids = n_topics * C.M_CAL * (len(gate2["solo_curves"]["A"])
                                  + len(gate2["solo_curves"]["B"]) + 2)
    candidates = n_topics * C.M_CAL * gate2["calibration_population"]["n_measured"]
    extension = gate2["extension"]["n_rows"]
    return {"gate0": gate0["rows"], "cap_selection": caps, "screen": screen,
            "second_pass": second_pass["cost_generations"],
            "calibration_grids": grids, "calibration_candidates": candidates,
            "calibration_extension": extension,
            "total": gate0["rows"] + caps + screen + second_pass["cost_generations"]
            + grids + candidates + extension}


def pilot_payload(tree: ModelTree, *, producing_commit: str,
                  gate3_record: Mapping[str, Any]) -> dict[str, Any]:
    records = {stage: transitions.read_stage_record(tree, stage)
               for stage in S.STAGE_SEQUENCE[:-2]}
    criteria = evaluate_criteria(
        registration=records[S.STAGE_REGISTERED],
        regime=records[S.STAGE_REGIME],
        second_pass=records[S.STAGE_SECOND_PASS],
        gate1=records[S.STAGE_GATE1], gate2=records[S.STAGE_GATE2],
        gate3=gate3_record)
    failed = sorted(k for k, v in criteria.items() if not v["passed"])
    return {
        "stage": S.STAGE_REPORT,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_REPORT],
        "outcome": "PASS",
        "inputs": {stage: {"stage": stage} for stage in S.STAGE_SEQUENCE[:-1]},
        "producing_commit": producing_commit,
        "manifest_hash": records[S.STAGE_REGISTERED]["manifest_hash"],
        "criteria": criteria,
        "criteria_order": list(S.PILOT_CRITERIA),
        "all_criteria_met": not failed,
        "criteria_failed": failed,
        "pilot_status": ("PILOT_CRITERIA_MET" if not failed
                         else "PILOT_CRITERIA_NOT_MET"),
        "generations": _generations(records[S.STAGE_REGIME],
                                    records[S.STAGE_SECOND_PASS],
                                    records[S.STAGE_GATE2],
                                    records[S.STAGE_GATE0]),
        "stage_record_hashes": {
            stage: fs.read_json(tree.stage_record(stage))["record_hash"]
            for stage in S.STAGE_SEQUENCE[:-1]},
        "what_this_licenses": (
            "a decision to freeze the v8 candidate rests on the four criteria "
            "above, evaluated on this replication's signed records under the "
            "thresholds the manifest bound before any row existed; it is not "
            "evidence about the effect, and the spectrum arm's B+X / X+B "
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
