"""``python -m dci.batch1 <command>`` --- every Batch 1 step, deterministic.

Validation and planning commands run anywhere and touch no model. The two
generation commands (``execute``, ``resume``) refuse unless the Freeze 1
manifest validates, every decision in the approvals file is APPROVED against
its payload hash, the execution environment was attested on the generation
host and still matches, and ``--authorize`` repeats the manifest hash;
``--synthetic`` replaces the backend with the CPU stand-in instead and marks
the run root synthetic. ``smoke`` is the only other command that can start a
model, and it needs its own plan hash and stays within a hard row limit.

Every command refuses (exit 3) unless it runs under CPython
``config.ORCHESTRATOR_PYTHON`` (D12).

Exit codes: 0 done; 1 a check found problems; 3 refused; 4 generation ran
but rows remain open (technical failures) --- ``resume`` continues.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import environment as ENV
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import library as L
from dci.batch1 import pipeline as P
from dci.batch1 import report as REP
from dci.batch1 import runner as RUN
from dci.batch1 import scoring as S
from dci.batch1 import smoke as SMOKE
from dci.batch1 import synthetic as SY
from dci.batch1 import topics as TOP
from dci.batch1 import verifiers as V

_REPO = Path(__file__).resolve().parents[3]
DOCS = _REPO / "docs" / "batch1"


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=1, sort_keys=True, default=str))


def verifier_selfcheck() -> dict[str, Any]:
    """Witness compliant, violation fails, empty and truncated never comply,
    and both frames reach the same scorer, for every constraint."""
    problems = []
    for c in L.all_constraints():
        w = COMPAT.build_witness(c)
        args = (c.cid, c.family.verifier_id, c.verifier_params(),
                c.family.vacuity)
        if not V.score_constraint(*args, w, present=True).compliant:
            problems.append(f"{c.cid}: witness not compliant")
        if V.score_constraint(*args, COMPAT.violation_text(c),
                              present=True).verdict != "FAIL":
            problems.append(f"{c.cid}: violation text passes")
        if V.score_constraint(*args, "", present=True).compliant:
            problems.append(f"{c.cid}: empty response complies")
        if V.score_constraint(*args, w, present=True,
                              truncated=True).compliant:
            problems.append(f"{c.cid}: truncated response complies")
        tw = COMPAT.task_witness(c)
        if tw is not None and not V.score_constraint(*args, tw,
                                                     present=True).compliant:
            problems.append(f"{c.cid}: full-length witness not compliant")
        if c.render("F0") == c.render("F1"):
            problems.append(f"{c.cid}: frames identical")
    return {"constraints": len(L.all_constraints()), "problems": problems,
            "ok": not problems,
            "verifier_bundle_hash": V.verifier_bundle_hash()}


def _freeze1(root: Path) -> dict[str, Any]:
    return F.read_json(Path(root) / "freeze1.json")


def _approvals(path: str | None) -> dict[str, Any]:
    return F.load_approvals(Path(path) if path else None)


def cmd_write_review_artifacts(args) -> int:
    out = Path(args.out)
    manifest = L.library_manifest()
    matrix = COMPAT.compatibility_matrix()
    bank = TOP.load_bank()
    split = TOP.split_bank(bank, pilot_topics=CFG.DEFAULT_CONFIG.pilot_topics,
                           stage1_topics=CFG.DEFAULT_CONFIG.stage1_topics)
    est = D.estimate(split=split)
    approvals = F.approvals_template()
    f1 = F.freeze1_manifest(approvals=approvals)
    F.write_json(out / "library_manifest.json", manifest)
    F.write_json(out / "compatibility_matrix.json", matrix)
    F.write_json(out / "topic_split.json", split.manifest())
    F.write_json(out / "topic_overlap.json", TOP.overlap_report(bank))
    F.write_json(out / "topic_hygiene.json", TOP.hygiene_report(bank, split))
    F.write_json(out / "estimate.json", est)
    F.write_json(out / "approvals_template.json", approvals)
    F.write_json(out / "freeze1_proposed.json", f1)
    (out / "library_review.md").write_text(REP.library_review(manifest, matrix))
    (out / "compatibility_review.md").write_text(
        REP.compatibility_review(matrix))
    (out / "estimate.md").write_text(REP.estimate_review(est))
    (out / "decisions.md").write_text(REP.decisions_review(approvals))
    revisions = json.loads(TOP.SOURCE_PATH.read_text()).get("revisions", [])
    (out / "topic_screen_report.md").write_text(REP.topic_review(
        TOP.overlap_report(bank), TOP.hygiene_report(bank, split), revisions,
        {t.topic_id: t.question for t in bank}, TOP.load_semantic_review()))
    # TOPIC_REVIEW.md is written by hand except its replacement tables,
    # which are generated into the marked block (D05 2026-10-25: they cite
    # each overlapped question as it stood when it was reviewed).
    released, _, _ = TOP._historical()
    history: dict[str, list[str]] = {}
    for r in released:
        names = history.setdefault(" ".join(r["question"].lower().split()), [])
        if r["source"] not in names:
            names.append(r["source"])
    tables = REP.topic_replacements(
        revisions, {t.topic_id: t.question for t in bank},
        {t.topic_id: split.split_of(t.topic_id) for t in bank},
        {t.topic_id: t.area for t in bank}, TOP.load_semantic_review(),
        {q: ",".join(sorted(v)) for q, v in history.items()})
    (out / "TOPIC_REVIEW.md").write_text(REP.splice_generated(
        (DOCS / "TOPIC_REVIEW.md").read_text(), tables))
    _print({"written": str(out), "freeze1_hash": f1["manifest_hash"],
            "pilot_authorizable": f1["authorization"]["pilot_authorizable"]})
    return 0


def cmd_validate_library(args) -> int:
    _print(L.validate_library())
    return 0


def cmd_validate_verifiers(args) -> int:
    result = verifier_selfcheck()
    _print(result)
    return 0 if result["ok"] else 1


def cmd_check_compatibility(args) -> int:
    matrix = COMPAT.compatibility_matrix()
    if args.out:
        F.write_json(Path(args.out), matrix)
    _print({"counts": matrix["counts"],
            "task_level": matrix["task_level"]["counts"],
            "task_level_unresolved": matrix["task_level"]["unresolved"],
            "per_limit": {m: len(v) for m, v in
                          matrix["compatible_by_limit"].items()}})
    return 0 if not (matrix["counts"]["UNRESOLVED"]
                     or matrix["task_level"]["unresolved"]) else 1


def cmd_attest_environment(args) -> int:
    found = ENV.probe(args.backend_python or RUN.BackendSpec.python)
    if found.get("status") != "AVAILABLE":
        print(f"refused: {found.get('reason')}", file=sys.stderr)
        return 3
    try:
        lock = ENV.lock_from_probe(found)
    except ValueError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    F.write_json(Path(args.out), lock)
    _print({"written": args.out, "identity_hash": lock["identity_hash"],
            "identity": lock["identity"]})
    return 0


def cmd_freeze_protocol(args) -> int:
    approvals = _approvals(args.approvals)
    lock = F.read_json(Path(args.environment_lock)) \
        if args.environment_lock else None
    manifest = F.freeze1_manifest(approvals=approvals, environment_lock=lock)
    root = Path(args.root)
    F.write_json(root / "freeze1.json", manifest)
    F.write_json(root / "approvals.json", approvals)
    _print({"manifest_hash": manifest["manifest_hash"],
            "authorization": manifest["authorization"]})
    return 0


def cmd_validate_freeze(args) -> int:
    root = Path(args.root)
    f1 = _freeze1(root)
    approvals = F.read_json(root / "approvals.json")
    problems = F.validate_freeze1(f1, approvals)
    result: dict[str, Any] = {"freeze1": f1["manifest_hash"],
                              "freeze1_problems": problems}
    if (root / "freeze2.json").exists():
        result["freeze2"] = F.read_json(root / "freeze2.json")["manifest_hash"]
        result["freeze2_problems"] = P.validate_membership(root, f1, approvals)
    _print(result)
    return 0 if not problems and not result.get("freeze2_problems") else 1


def cmd_plan(args) -> int:
    root = Path(args.root)
    f1 = _freeze1(root)
    if args.stage == D.STAGE1:
        rows = P.write_stage1_plan(root, f1)
    else:
        rows = P.write_stage2_plan(root, f1)
    cfg = P.config_of(f1)
    _print({"stage": args.stage, "rows": len(rows),
            "by_model": {m: sum(1 for r in rows if r["model"] == m)
                         for m in cfg.models}})
    return 0


def cmd_estimate(args) -> int:
    cfg = CFG.DEFAULT_CONFIG
    _print(D.estimate(cfg, split=P.split_of(cfg)))
    return 0


def cmd_execute(args) -> int:
    root = Path(args.root)
    f1 = _freeze1(root)
    approvals = F.read_json(root / "approvals.json")
    design = P.read_design(root, args.stage)
    devices = tuple(int(d) for d in args.devices.split(","))
    if args.synthetic:
        summary = RUN.execute(root, design, freeze1=f1, approvals=approvals,
                              generate=SY.synthetic_generate(),
                              devices=devices)
    else:
        backend = RUN.BackendSpec(
            python=args.backend_python or RUN.BackendSpec.python,
            visibility_var=("CUDA_VISIBLE_DEVICES" if args.accelerator == "cuda"
                            else "HIP_VISIBLE_DEVICES"),
            device=devices[0])
        summary = RUN.execute(root, design, freeze1=f1, approvals=approvals,
                              token=args.authorize, backend=backend,
                              devices=devices)
    _print(summary)
    return 0 if summary["complete"] else 4


def cmd_status(args) -> int:
    root = Path(args.root)
    _print(P.status(root, _freeze1(root)))
    return 0


def cmd_smoke_plan(args) -> int:
    plan = SMOKE.smoke_plan(args.models or tuple(CFG.MODEL_BY_KEY))
    _print({"plan_hash": plan["plan_hash"], "rows": len(plan["rows"]),
            "max_rows": plan["max_rows"],
            "per_model": {m: sum(1 for r in plan["rows"] if r["model"] == m)
                          for m in (args.models or CFG.MODEL_BY_KEY)}})
    return 0


def cmd_smoke(args) -> int:
    backend = RUN.BackendSpec(
        python=args.backend_python or RUN.BackendSpec.python,
        visibility_var=("CUDA_VISIBLE_DEVICES" if args.accelerator == "cuda"
                        else "HIP_VISIBLE_DEVICES"),
        device=args.device)
    lock = F.read_json(Path(args.environment_lock)) \
        if args.environment_lock else None
    report = SMOKE.run_smoke(Path(args.root), token=args.authorize,
                             max_rows=args.max_rows,
                             models=args.models or tuple(CFG.MODEL_BY_KEY),
                             backend=backend, environment_lock=lock)
    _print(report)
    # Exit 0 only when D12's smoke condition is met (computed, smoke.py).
    if not report.get("d12_pass"):
        failed = {k: m.get("d12_problems") for k, m in report["models"].items()
                  if not m.get("d12_pass")}
        print(f"smoke FAILED D12: environment "
              f"{report.get('d12', {}).get('environment_problems')}; models "
              f"{failed}; see smoke_report.json and each model's backend.log",
              file=sys.stderr)
        return 4
    return 0


def cmd_score(args) -> int:
    scored = P.score_stage(Path(args.root), args.stage)
    _print({"stage": args.stage, "scored": len(scored)})
    return 0


def cmd_select_refinement(args) -> int:
    root = Path(args.root)
    rows = P.write_stage2_plan(root, _freeze1(root))
    sel = F.read_json(root / "plan" / "stage2_selection.json")
    _print({"cells": sel["n_selected"], "candidates": sel["n_candidates"],
            "by_class": sel["by_class"], "rows": len(rows)})
    return 0


def cmd_finalize(args) -> int:
    root = Path(args.root)
    f1 = _freeze1(root)
    result = P.finalize(root, f1)
    tables = S.PilotTables.from_state(F.read_json(root / "tables.json"))
    (root / "reference_selection.md").write_text(
        REP.selection_report(result, tables, P.config_of(f1)))
    _print({"status": result["status"], "b": result["b"].get("selected"),
            "a": (result["a"] or {}).get("selected"),
            "feasibility": {p: result["feasibility"][p]["feasible"]
                            for p in ("P1", "P2", "P3")}
            if result["feasibility"] else None})
    return 0


def cmd_report_coverage(args) -> int:
    root = Path(args.root)
    result = F.read_json(root / "calibration.json")
    tables = S.PilotTables.from_state(F.read_json(root / "tables.json"))
    text = REP.selection_report(result, tables, P.config_of(_freeze1(root)))
    (root / "reference_selection.md").write_text(text)
    print(text)
    return 0


def cmd_freeze_membership(args) -> int:
    root = Path(args.root)
    approvals = F.read_json(root / "approvals.json")
    manifest = P.freeze_membership(root, _freeze1(root), approvals)
    _print({"manifest_hash": manifest["manifest_hash"],
            "state": manifest["state"], "selected": manifest["selected"],
            "synthetic": manifest["synthetic"]})
    return 0


def cmd_demo(args) -> int:
    """The whole pilot on the synthetic stand-in, in a fresh root."""
    root = Path(args.root)
    if (root / "RUN.json").exists():
        print(f"{root} already holds a run; choose an empty directory",
              file=sys.stderr)
        return 2
    approvals = F.approvals_template()
    f1 = F.freeze1_manifest(approvals=approvals)
    F.write_json(root / "freeze1.json", f1)
    F.write_json(root / "approvals.json", approvals)
    gen = SY.synthetic_generate(empty_rate=0.005)
    for stage in (D.STAGE1, D.STAGE2):
        design = P.write_stage1_plan(root, f1) if stage == D.STAGE1 \
            else P.write_stage2_plan(root, f1)
        RUN.execute(root, design, freeze1=f1, approvals=approvals,
                    generate=gen)
        P.score_stage(root, stage)
    result = P.finalize(root, f1)
    tables = S.PilotTables.from_state(F.read_json(root / "tables.json"))
    (root / "reference_selection.md").write_text(
        REP.selection_report(result, tables, P.config_of(f1)))
    f2 = P.freeze_membership(root, f1, approvals,
                             replicates=args.replicates)
    _print({"root": str(root), "status": result["status"],
            "stability": f2["stability"]["selection"],
            "selected": f2["selected"], "freeze2": f2["manifest_hash"],
            "freeze2_state": f2["state"], "synthetic": f2["synthetic"]})
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m dci.batch1",
                                description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, fn, *, root=False, stage=False):
        sp = sub.add_parser(name)
        sp.set_defaults(fn=fn)
        if root:
            sp.add_argument("--root", required=True)
        if stage:
            sp.add_argument("--stage", choices=(D.STAGE1, D.STAGE2),
                            required=True)
        return sp

    add("validate-library", cmd_validate_library)
    add("validate-verifiers", cmd_validate_verifiers)
    add("check-compatibility", cmd_check_compatibility).add_argument("--out")
    add("estimate", cmd_estimate)
    add("write-review-artifacts", cmd_write_review_artifacts).add_argument(
        "--out", default=str(DOCS))
    ae = add("attest-environment", cmd_attest_environment)
    ae.add_argument("--backend-python")
    ae.add_argument("--out", required=True)
    fp = add("freeze-protocol", cmd_freeze_protocol, root=True)
    fp.add_argument("--approvals", help="researcher-edited approvals.json")
    fp.add_argument("--environment-lock",
                    help="environment_lock.json from attest-environment")
    add("status", cmd_status, root=True)
    sp = add("smoke-plan", cmd_smoke_plan)
    sp.add_argument("--models", nargs="*")
    sm = add("smoke", cmd_smoke, root=True)
    sm.add_argument("--authorize", help="the smoke plan hash")
    sm.add_argument("--max-rows", type=int, required=True)
    sm.add_argument("--models", nargs="*")
    sm.add_argument("--backend-python")
    sm.add_argument("--accelerator", choices=("rocm", "cuda"), default="rocm")
    sm.add_argument("--device", type=int, default=0)
    sm.add_argument("--environment-lock",
                    help="environment_lock.json from attest-environment; D12's "
                         "smoke condition needs it")
    add("validate-freeze", cmd_validate_freeze, root=True)
    add("plan", cmd_plan, root=True, stage=True)
    for name in ("execute", "resume"):
        ep = add(name, cmd_execute, root=True, stage=True)
        ep.add_argument("--authorize", help="the Freeze 1 manifest hash")
        ep.add_argument("--synthetic", action="store_true")
        ep.add_argument("--backend-python")
        ep.add_argument("--accelerator", choices=("rocm", "cuda"),
                        default="rocm")
        ep.add_argument("--devices", default="0",
                        help="comma-separated GPU indices; one worker per "
                             "GPU (D12), e.g. 0,1")
    add("score", cmd_score, root=True, stage=True)
    add("select-refinement", cmd_select_refinement, root=True)
    add("finalize-calibration", cmd_finalize, root=True)
    add("construct-references", cmd_finalize, root=True)
    add("report-coverage", cmd_report_coverage, root=True)
    add("freeze-membership", cmd_freeze_membership, root=True)
    add("demo", cmd_demo, root=True).add_argument(
        "--replicates", type=int, default=None,
        help="stability resamples (default: the configured number)")
    args = p.parse_args(argv)
    try:
        ENV.require_orchestrator()
        return args.fn(args)
    except (F.AuthorizationError, F.FreezeError, RUN.RunError,
            S.ScoringError) as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
