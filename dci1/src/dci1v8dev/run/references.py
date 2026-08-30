"""Stage 8, ``GATE_3_REFERENCES``: LOCAL and SPECTRUM validity, the core
references by the registered kernel, the deterministic spectrum selection,
the coverage gate and the admissible backups.

No generation. Reads Gate 2's §13.11 tables (three splits) and evaluates:

* §13.7's folded stability per candidate (``dci1v7.stages.stability``,
  imported) --- the LOCAL rule's V_stab;
* ``dci1v8dev.spectrum.validity.classify_pool`` --- every pooled rung
  under the LOCAL rule (v7's full V(R), unchanged) and under the SPECTRUM
  rule (V_coord, unfolded V_stab, V_pos);
* §13.8's core selection by v7's kernel ``admit_core_references`` with
  ``require_spectrum=False``: the core arm is decided on its own rule and
  the spectrum is selected by v8's, so a pool that cannot straddle under
  §13.12's folded triple no longer costs the core its references;
* ``select_spectrum`` + ``selected_coverage`` (the C4 replacement) and
  ``admissible_backups`` (§13.15 on the admissible basis).

Nothing here reads a composed outcome: the closed §13.11 schema refuses one
before any rule runs, and the pilot has none to offer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import gitinfo
from dci1v7.protocol import constants as C
from dci1v7.stages import selection as v7_selection
from dci1v7.stages import stability as stability_stage
from dci1v7.stages.calibration_table import load_calibration_table

from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run.lifecycle import StageOutcome, run_stage
from dci1v8dev.run.regime import jsonable
from dci1v8dev.spectrum.backups import admissible_backups
from dci1v8dev.spectrum.selection import DEFAULT_SELECTION_RULE, select_spectrum
from dci1v8dev.spectrum.validity import DEFAULT_SPECTRUM_RULE, classify_pool

__all__ = ["gate3_payload", "run_gate3", "survival_summary"]


def survival_summary(pool: Mapping[str, Any], core: Mapping[str, Any],
                     selection: Mapping[str, Any], backups: Mapping[str, Any],
                     *, iota_a: float) -> dict[str, Any]:
    """What the report reads: the four survival facts, in one block."""
    local_families = sorted({label.split(":")[0]
                             for label, v in pool["local"].items()
                             if v["passed"]})
    valid = {label: v for label, v in pool["spectrum"].items() if v["passed"]}
    below = sorted(label for label, v in valid.items() if v["side"] == "below")
    above = sorted(label for label, v in valid.items() if v["side"] == "above")
    fam_below = sorted({label.split(":")[0] for label in below})
    fam_above = sorted({label.split(":")[0] for label in above})
    coverage = selection["coverage"]
    return {
        "local_valid_families": local_families,
        "n_local_valid_families": len(local_families),
        "meets_min_local_families": len(local_families) >= S.MIN_LOCAL_FAMILIES,
        "min_local_families": S.MIN_LOCAL_FAMILIES,
        "core_identified": bool(core["references_identified"]),
        "core_references": [{"family": e["family"], "severity": e["severity"],
                             "iota": e["iota"]}
                            for e in core["core_references"]],
        "spectrum_valid_below": below, "spectrum_valid_above": above,
        "spectrum_valid_families_below": fam_below,
        "spectrum_valid_families_above": fam_above,
        "spectrum_pool_ok": (len(below) >= C.SUPPORT_MIN_BELOW
                             and len(above) >= C.SUPPORT_MIN_ABOVE
                             and len(fam_below) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE
                             and len(fam_above) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE),
        "coverage_identified": bool(coverage["identified"]),
        "coverage_status": coverage["status"],
        "coverage_reasons": list(coverage["reasons"]),
        "projected_se_beta": coverage["projection"].get("se_beta"),
        "selected_families": list(selection["families"]),
        "n_spectrum_references": selection["n_spectrum_references"],
        "backups": list(backups["backups"]),
        "n_backups": len(backups["backups"]),
        "meets_min_backups": len(backups["backups"]) >= S.MIN_BACKUPS,
        "iota_a": iota_a,
    }


def gate3_payload(tree: ModelTree, *, producing_commit: str,
                  gate2_record: Mapping[str, Any], seed: int = 0,
                  resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
                  ) -> dict[str, Any]:
    m_star = int(gate2_record["m_star"])
    iota_a = float(gate2_record["iota_a"])
    solo_a = float(gate2_record["solo_compliance_a"])
    tables = {split: load_calibration_table(
        gate2_record["calibration_rows"][split], model_key=tree.model_key,
        m_star=m_star, split=split)
        for split in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")}
    stability_stage.assert_not_pooled(tables[C.CALIBRATION_A],
                                      split=C.CALIBRATION_A)
    stability_stage.assert_not_pooled(tables[C.CALIBRATION_B],
                                      split=C.CALIBRATION_B)
    pairs = stability_stage.split_pair(tables[C.CALIBRATION_A],
                                       tables[C.CALIBRATION_B])
    folded = {label: stability_stage.stability_verdict(
        pair, iota_a_by_split=gate2_record["iota_a_by_split"],
        solo_a_by_split=gate2_record["solo_a_by_split"], seed=seed,
        resamples=resamples) for label, pair in sorted(pairs.items())}
    a_splits = gate2_record.get("a_per_topic_by_split") or {}
    per_topic = a_splits.get("per_topic") or {}
    chance = a_splits.get("chance") or {}
    if (per_topic.get(C.CALIBRATION_A) and per_topic.get(C.CALIBRATION_B)
            and chance.get(C.CALIBRATION_A) is not None
            and chance.get(C.CALIBRATION_B) is not None):
        iota_a_stability = stability_stage.assert_iota_a_stable(
            per_topic_a=per_topic[C.CALIBRATION_A],
            per_topic_b=per_topic[C.CALIBRATION_B],
            chance_a=chance[C.CALIBRATION_A],
            chance_b=chance[C.CALIBRATION_B], seed=seed + 2,
            resamples=resamples)
    else:
        iota_a_stability = {"quantity": "iota_A", "passed": None,
                            "reason": "no per-topic vector for A on both splits"}
    pool = classify_pool(
        tables["pooled"], tables[C.CALIBRATION_A], tables[C.CALIBRATION_B],
        iota_a=iota_a, solo_compliance_a=solo_a, n_topics_a=C.N_CALIBRATION,
        folded_stability=folded, seed=seed, resamples=resamples,
        rule=DEFAULT_SPECTRUM_RULE)
    core = v7_selection.admit_core_references(
        tables["pooled"], iota_a=iota_a, solo_compliance_a=solo_a,
        n_topics_a=C.N_CALIBRATION, stability_by_candidate=folded,
        require_spectrum=False)
    core_refs = {e["family"]: int(e["severity"]) for e in core["core_references"]}
    by_label = {r.label: r for r in tables["pooled"]}
    valid_rows = [r for r in tables["pooled"] if pool["spectrum"][r.label]["passed"]]
    core_rows = [by_label[f"{f}:{q}"] for f, q in core_refs.items()
                 if f"{f}:{q}" in by_label]
    selection = select_spectrum(
        valid_rows + [r for r in core_rows if r not in valid_rows],
        iota_a=iota_a, core_references=core_refs, rule=DEFAULT_SELECTION_RULE)
    backups = admissible_backups(pool["local"], tables["pooled"], iota_a=iota_a,
                                 used_families=list(core_refs))
    summary = survival_summary(pool, core, selection, backups, iota_a=iota_a)
    return jsonable({
        "stage": S.STAGE_GATE3,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_GATE3],
        "outcome": "PASS",
        "inputs": {"gate2": {"stage": S.STAGE_GATE2, "m_star": m_star}},
        "producing_commit": producing_commit,
        "m_star": m_star, "iota_a": iota_a, "solo_compliance_a": solo_a,
        "n_rows": {split: len(rows) for split, rows in tables.items()},
        "stability": folded,
        "n_folded_stable": pool["n_folded_stable"],
        "n_unfolded_stable": pool["n_unfolded_stable"],
        "iota_a_stability": iota_a_stability,
        "unfolded_stability": pool["unfolded_stability"],
        "local": pool["local"], "spectrum": pool["spectrum"],
        "n_local_valid": pool["n_local_valid"],
        "n_spectrum_valid": pool["n_spectrum_valid"],
        "n_spectrum_valid_beyond_v7_v_head":
            pool["n_spectrum_valid_beyond_v_head"],
        "core": {k: v for k, v in core.items() if k != "family_verdicts"},
        "core_family_verdicts": core["family_verdicts"],
        "core_kernel": "dci1v7.stages.selection.admit_core_references "
                       "(§13.8, registered), require_spectrum=False: the "
                       "spectrum is selected by the v8 rule below",
        "core_references": core_refs,
        "spectrum_selection": {k: v for k, v in selection.items()
                               if k != "trace"},
        "selection_trace": selection["trace"],
        "coverage": selection["coverage"],
        "backups": backups,
        "survival": summary,
        "identification_statuses": sorted(
            set(core["identification_statuses"]) | {selection["status"]}),
        "written_at_design_time": True,
        "no_composed_cells": S.NO_COMPOSED_CELLS,
        "seed": seed, "resamples": resamples,
    })


def run_gate3(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "", seed: int = 0,
              resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
              ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return run_stage(
        tree, S.STAGE_GATE3,
        compute=lambda previous: gate3_payload(
            tree, producing_commit=commit, gate2_record=previous, seed=seed,
            resamples=resamples),
        producing_commit=commit, environment_digest=environment_digest)
