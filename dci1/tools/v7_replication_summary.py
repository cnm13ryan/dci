#!/usr/bin/env python3
"""Per-replication summary of the v7 study, from the SIGNED records only.

    python3 tools/v7_replication_summary.py

Writes ``reports/dci1v7/replication_summary.json``: for each registered
replication the stage reached, the terminal status and the audit checks it
blocked on, m* and n* from Gate 2, the probe's determinate entries and the
paired contrasts it projected (labelled as the probe labels them: a
projection that decides nothing), Gate 3A's §12.6 verdict on the calibration
basis, Gate 3C's identification statuses and admitted arms, Gate 4's row
count and contrast statuses, and the transition-log timeline. It performs no
estimation, opens no masked quantity and re-reads no row; every number is
read from a record whose signature is verified on read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DCI1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1_ROOT / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.models.registry import MODELS                        # noqa: E402
from dci1v7.engine import transitions                            # noqa: E402
from dci1v7.engine.context import (development_context,          # noqa: E402
                                   registered_context)
from dci1v7.engine.paths import model_tree                       # noqa: E402
from dci1v7.protocol import constants as C                       # noqa: E402

OUT = DCI1_ROOT / "reports" / "dci1v7" / "replication_summary.json"


def _r(x):
    return round(x, 4) if isinstance(x, float) else x


def summarise(tree) -> dict:
    s: dict = {"model_key": tree.model_key}
    s["stage_reached"] = transitions.stage_reached(tree)
    s["terminal_status"] = transitions.terminal_status(tree)
    if tree.terminal_report.exists():
        p = fs.read_json(tree.terminal_report)["payload"]
        obs = p.get("observed") or {}
        s["terminal_gate"] = p.get("gate")
        s["blocked_checks"] = obs.get("blocked")
        s["artifact_checks"] = {"n": obs.get("n_artifact_checks"),
                                "failed": obs.get("n_artifact_failed"),
                                "unresolved": obs.get("n_artifact_unresolved")}

    def rec(stage):
        return (transitions.read_stage_record(tree, stage)
                if tree.stage_record(stage).exists() else None)

    g2 = rec(C.STAGE_GATE2)
    if g2:
        s["m_star"], s["n_star"] = g2.get("m_star"), g2.get("n_star")
    pr = rec(C.STAGE_GATE2_75)
    if pr:
        cc = pr["composed_contrast"]
        s["probe"] = {
            "what_this_is": cc.get("what_this_is"),
            "decides": cc.get("decides"),
            "determinate_entries": {
                f"{e['cell']}@{e.get('configuration')}": _r(e["compliance"])
                for e in cc["entries"] if e.get("determinate")},
            "contrast_statuses": cc.get("contrast_statuses"),
            "contrasts": {
                name: {"estimate": _r(e.get("estimate")),
                       "statuses": (e.get("boundary") or {}).get("statuses")}
                for name, e in cc["contrasts"].items()},
        }
    g3a = rec(C.STAGE_GATE3A)
    if g3a:
        cov = g3a["coverage_at_calibrated_iota_a"]
        realised = cov.get("realised") or {}
        s["coverage_12_6"] = {
            "iota_a": _r(g3a.get("iota_a")),
            "certified_conditions": cov.get("certified_conditions"),
            "conditions_on_calibration_basis": cov.get("conditions"),
            "conditions_moved_by_the_basis":
                cov.get("conditions_moved_by_the_basis"),
            "decisive_met": cov.get("decisive_met"),
            "core_met": cov.get("core_met"),
            "spectrum_met": cov.get("spectrum_met"),
            "straddling_groups": realised.get("straddling_groups"),
            "n_eligible": realised.get("n_eligible"),
        }
    g3c = rec(C.STAGE_GATE3C)
    if g3c:
        sup = g3c["support"]
        s["identification_statuses"] = g3c["identification_statuses"]
        s["support"] = {"disposition": sup.get("disposition"),
                        "support_met": sup.get("support_met"),
                        "failures": sup.get("failures"),
                        "realised": sup.get("realised")}
        s["admitted_arms"] = g3c["admitted_arms"]
        s["derived_cell_count"] = g3c.get("derived_cell_count")
        s["delta_r_identified"] = (
            "EXCESS_NOT_IDENTIFIED" not in g3c["identification_statuses"])
    g4 = rec(C.STAGE_GATE4)
    if g4:
        s["gate4"] = {"rows": g4.get("rows"),
                      "contrast_statuses": g4.get("contrast_statuses"),
                      "any_structural_zero": g4.get("any_structural_zero"),
                      "terminates_nothing": g4.get("terminates_nothing")}
        # v7 A7: the spectrum's own verdict and the D6 block, beside the core's.
        s["support"]["spectrum_met"] = sup.get("spectrum_met")
        s["support"]["spectrum_failures"] = sup.get("spectrum_failures")
        block = g3c.get("non_identification") or {}
        s["non_identification"] = {
            "status": block.get("status"),
            "irreversible": block.get("irreversible"),
            "n_members": len(block.get("not_identified_members") or ())}
    g5 = rec(C.STAGE_GATE5)
    if g5:
        fz = g5.get("freeze") or {}
        s[C.STAGE_GATE5] = {
            "outcome": g5.get("outcome"),
            "admitted_arms": g5.get("admitted_arms"),
            "identification_statuses": g5.get("identification_statuses"),
            "blocks": g5.get("blocks"), "cells_per_block":
                g5.get("cells_per_block"), "M": g5.get("M"),
            "bound": {k: len(fz.get(k) or ()) for k in
                      ("core_references", "spectrum_severities",
                       "near_form_controls", "frozen_backup_families")},
            "non_identification_status":
                (g5.get("non_identification") or {}).get("status")}
    cg = rec(C.STAGE_CONFIRMATORY)
    if cg:
        s[C.STAGE_CONFIRMATORY] = {"outcome": cg.get("outcome"),
                                   "n_rows": cg.get("n_rows"),
                                   "completeness": cg.get("completeness")}
    ua = rec(C.STAGE_UNMASKED_ANALYSIS)
    if ua:
        statements = ua.get("statements") or []
        estimands = ua.get("estimands") or {}
        members = {}
        for cfg, bucket in (estimands.get("configurations") or {}).items():
            members[cfg] = {
                "identified": sorted(m for m, v in bucket.items()
                                     if isinstance(v, dict)
                                     and v.get("status") == "IDENTIFIED"),
                "not_identified": {
                    m: v.get("reason") for m, v in bucket.items()
                    if isinstance(v, dict)
                    and v.get("status") == "NOT_IDENTIFIED"}}
        cross = estimands.get("cross_configuration") or {}
        members["cross"] = {m: v.get("status") for m, v in cross.items()
                            if isinstance(v, dict)}
        levels: dict[str, int] = {}
        for st in statements:
            if isinstance(st, dict) and st.get("emitted", True):
                key = str(st.get("claim_level"))
                levels[key] = levels.get(key, 0) + 1
        sc = ua.get("success_criterion") or {}
        s[C.STAGE_UNMASKED_ANALYSIS] = {
            "outcome": ua.get("outcome"),
            "identification_statuses": ua.get("identification_statuses"),
            "section_26_verdict": sc.get("verdict"),
            "n_statements": len(statements),
            "emitted_levels": levels,
            "members": members,
            "points": {cfg: {m: _r(bucket[m].get("point"))
                             for m in ("Delta_R", "Xi", "D(B<-A)",
                                       "D(A<-B)", "Lambda")
                             if isinstance(bucket.get(m), dict)
                             and bucket[m].get("status") == "IDENTIFIED"}
                       for cfg, bucket in
                       (estimands.get("configurations") or {}).items()}}
    fr = rec(C.STAGE_FINAL_REPORT)
    if fr:
        checks = fr.get("final_report_checks") or []
        s[C.STAGE_FINAL_REPORT] = {
            "outcome": fr.get("outcome"),
            "checks_passed": fr.get("n_final_report_passed"),
            "checks": fr.get("n_final_report_checks"),
            "non_passing_checks": [
                (c.get("check"), c.get("verdict")) for c in checks
                if isinstance(c, dict)
                and c.get("verdict") not in ("PASS", "NOT_APPLICABLE")],
            "n_result_rows": fr.get("n_result_rows"),
            "scope_sentence": fr.get("scope_sentence")}
    s["timeline"] = [
        {"at": row.get("timestamp"), "stage": row.get("stage"),
         "outcome": row.get("outcome"),
         "commit": (row.get("producing_commit") or "")[:12]}
        for row in transitions.transition_rows(tree)]
    rows = 0
    for produced in tree.root.rglob("rows.jsonl"):
        rows += sum(1 for line in produced.open() if line.strip())
    s["behavioural_rows"] = rows
    return s


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dev-root", default=None,
                    help="summarise the development-namespace tree rooted "
                         "here (study id dci1v7-development) instead of the "
                         "registered study; requires --out")
    ap.add_argument("--out", default=None,
                    help="where to write (default: the registered study's "
                         "reports/dci1v7/replication_summary.json; required "
                         "with --dev-root so a rehearsal never overwrites it)")
    args = ap.parse_args()
    if args.dev_root and not args.out:
        ap.error("--dev-root requires --out")
    ctx = (development_context(Path(args.dev_root)) if args.dev_root
           else registered_context())
    target = Path(args.out) if args.out else OUT
    what = ("per-replication summary of a DEVELOPMENT REHEARSAL of v7 "
            "(namespace development, study id dci1v7-development): not the "
            "registered study, not confirmatory evidence; read from its "
            "signed records; no estimation, no pooling"
            if args.dev_root else
            "per-replication summary of the v7 study, read from signed "
            "records; no estimation, no pooling")
    out = {"_what": what,
           "study_id": ctx.study_id, "namespace": ctx.namespace,
           "replications": {m.model_key: summarise(model_tree(ctx, m.model_key))
                            for m in MODELS}}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=1, sort_keys=True, default=str)
                      + "\n")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
