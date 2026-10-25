"""The Batch 1 pilot as a sequence of deterministic steps over one run root.

    root/
      RUN.json  RUN.lock            namespace (real | synthetic), Freeze 1 hash
      freeze1.json  approvals.json  the protocol the run executes
      plan/stage1_design.jsonl      every Stage 1 row, with identity and seed
      plan/stage2_selection.json    the D06 selection, bound to Stage 1 evidence
      plan/stage2_design.jsonl
      generation/<stage>/<model>/rows.jsonl      accepted responses (append-only)
      generation/<stage>/<model>/rejected.jsonl  technical attempts (never data)
      generation/<stage>/<model>/provenance.jsonl
      scored/<stage>.jsonl          one scored record per accepted response
      tables.json                   pooled stand-alone compliance tables
      calibration.json              A, B, eligibility, G1-G6, coverage
      freeze2.json                  pilot-derived membership, evidence-bound

Each step reads only what earlier steps wrote, re-derives what it can, and
refuses what it cannot trust (``evidence``): a plan file that is not the
frozen design, an incomplete or stale stage, a Stage 2 selection computed
from other Stage 1 evidence. Stage 2 is selected only from complete Stage 1
evidence; calibration and Freeze 2 need both stages complete.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import design as D
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import revision as REV
from dci.batch1 import scoring as S
from dci.batch1 import stability as STAB
from dci.batch1.store import (
    RunError, canonical, read_jsonl, run_lock, write_jsonl,
)

__all__ = ["config_of", "split_of", "write_stage1_plan", "read_design",
           "score_stage", "evidence_bundle", "build_tables",
           "write_stage2_plan", "finalize", "freeze_membership",
           "validate_membership", "status"]

config_of = EV.config_of
split_of = EV.split_of


def _synthetic(root: Path) -> bool:
    return F.read_json(Path(root) / "RUN.json")["namespace"] == "synthetic"


def _freeze1(root: Path) -> dict[str, Any]:
    return F.read_json(Path(root) / "freeze1.json")


def read_design(root: Path, stage: str) -> list[dict[str, Any]]:
    path = Path(root) / "plan" / f"{stage}_design.jsonl"
    if not path.exists():
        raise RunError(f"no {stage} design at {path}")
    return read_jsonl(path)


def write_stage1_plan(root: Path, freeze1: Mapping[str, Any]
                      ) -> list[dict[str, Any]]:
    rows = EV.expected_design(root, freeze1, D.STAGE1)
    write_jsonl(Path(root) / "plan" / "stage1_design.jsonl", rows)
    return rows


def score_stage(root: Path, stage: str) -> list[dict[str, Any]]:
    """Score every accepted response of ``stage`` against the frozen design."""
    root = Path(root)
    freeze1 = _freeze1(root)
    with run_lock(root):
        design = EV.expected_design(root, freeze1, stage)
        if canonical(read_design(root, stage)) != canonical(design):
            raise EV.DesignAuthenticationError(
                f"the {stage} plan file differs from the frozen design")
        generation, _ = EV.load_generation(root, stage)
        scored = S.score_rows(generation.values(), design)
        write_jsonl(root / "scored" / f"{stage}.jsonl", scored)
    return scored


def evidence_bundle(root: Path, freeze1: Mapping[str, Any], *,
                    verify_scores: bool = True) -> dict[str, Any]:
    """Both stages' complete evidence, the selection that links them, and
    the namespace; refuses anything incomplete or stale."""
    ev1 = EV.stage_evidence(root, freeze1, D.STAGE1,
                            verify_scores=verify_scores)
    ev2 = EV.stage_evidence(root, freeze1, D.STAGE2,
                            verify_scores=verify_scores)
    return {"stages": {D.STAGE1: ev1, D.STAGE2: ev2},
            "selection": EV.stored_selection(root),
            "synthetic": _synthetic(root)}


def build_tables(root: Path, freeze1: Mapping[str, Any] | None = None, *,
                 bundle: Mapping[str, Any] | None = None) -> S.PilotTables:
    freeze1 = freeze1 or _freeze1(root)
    bundle = bundle or evidence_bundle(root, freeze1)
    tables = EV.tables_for(EV.decision_stages(bundle["stages"],
                                              config_of(freeze1)),
                           synthetic=bundle["synthetic"])
    F.write_json(Path(root) / "tables.json", tables.state())
    return tables


def write_stage2_plan(root: Path, freeze1: Mapping[str, Any]
                      ) -> list[dict[str, Any]]:
    """The D06 selection from complete, re-verified Stage 1 evidence."""
    root = Path(root)
    ev1 = EV.stage_evidence(root, freeze1, D.STAGE1, verify_scores=True)
    selection = EV.stage1_selection(ev1, config_of(freeze1))
    path = root / "plan" / "stage2_selection.json"
    if path.exists() and canonical(F.read_json(path)) != canonical(selection):
        raise RunError("the stored Stage 2 selection differs from the one "
                       "Stage 1 reproduces; it was edited or Stage 1 changed")
    F.write_json(path, selection)
    rows = EV.expected_design(root, freeze1, D.STAGE2)
    plan = root / "plan" / "stage2_design.jsonl"
    if plan.exists() and canonical(read_jsonl(plan)) != canonical(rows):
        raise RunError(f"{plan} differs from the design the selection gives")
    write_jsonl(plan, rows)
    return rows


def finalize(root: Path, freeze1: Mapping[str, Any]) -> dict[str, Any]:
    cfg = config_of(freeze1)
    bundle = evidence_bundle(root, freeze1)
    tables = build_tables(root, freeze1, bundle=bundle)
    matrix = COMPAT.compatibility_matrix()
    result = CAL.finalize(tables, cfg, matrix,
                          early_stop=EV.early_stopped(bundle["selection"]))
    out = dict(result)
    out["evidence"] = {stage: ev.manifest()
                       for stage, ev in bundle["stages"].items()}
    if cfg.protocol == "v2":
        out["forecast"] = bundle["selection"]["forecast"]
        out["accounting"] = EV.budget_report(root)      # reported, not a gate
        out["reporting"] = REV.reporting(
            tables, EV.tables_for([bundle["stages"][D.STAGE1]],
                                  synthetic=bundle["synthetic"]),
            cfg, matrix, result, bundle["selection"]["forecast"])
    else:
        out["sensitivity_stage1_only"] = STAB.stage1_only(
            bundle["stages"][D.STAGE1], result, cfg, matrix,
            synthetic=bundle["synthetic"])
    F.write_json(Path(root) / "calibration.json", out)
    return out


def freeze_membership(root: Path, freeze1: Mapping[str, Any],
                      approvals: Mapping[str, Any] | None, *,
                      replicates: int | None = None) -> dict[str, Any]:
    bundle = evidence_bundle(root, freeze1)
    build_tables(root, freeze1, bundle=bundle)
    manifest = F.freeze2_manifest(freeze1, bundle, approvals=approvals,
                                  allow_synthetic=bundle["synthetic"],
                                  replicates=replicates)
    F.write_json(Path(root) / "freeze2.json", manifest)
    return manifest


def validate_membership(root: Path, freeze1: Mapping[str, Any],
                        approvals: Mapping[str, Any] | None) -> list[str]:
    manifest = F.read_json(Path(root) / "freeze2.json")
    return F.validate_freeze2(
        manifest, freeze1, lambda: evidence_bundle(root, freeze1),
        approvals=approvals)


def status(root: Path, freeze1: Mapping[str, Any]) -> dict[str, Any]:
    """Where each stage stands, without refusing."""
    out: dict[str, Any] = {}
    for stage in (D.STAGE1, D.STAGE2):
        try:
            design = EV.expected_design(root, freeze1, stage)
        except RunError as error:
            out[stage] = {"state": "NOT_READY", "reason": str(error)}
            continue
        generation, repeats = EV.load_generation(root, stage)
        rejected = EV.rejected_summary(root, stage, generation)
        entry = {"design_rows": len(design), "accepted": len(generation),
                 "missing": len(design) - len(generation),
                 "repeats_collapsed": repeats, "technical": rejected}
        try:
            EV.stage_evidence(root, freeze1, stage)
            entry["state"] = "COMPLETE"
        except RunError as error:
            entry["state"] = "INCOMPLETE"
            entry["reason"] = str(error)
        out[stage] = entry
    return json.loads(json.dumps(out))
