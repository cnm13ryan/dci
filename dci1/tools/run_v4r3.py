"""The v4r3 stage driver: register, qualify, regime screen.

One entry point per stage so that each is a separate, logged, resumable
command, exactly as §18 requires. Nothing here decides anything scientific;
the rules live in ``dci1v4r3``.

    ./.venv/bin/python tools/run_v4r3.py register
    ./.venv/bin/python tools/run_v4r3.py regime --model qwen3-4b --device 0
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dci1v4.models.registry import MODEL_KEYS                   # noqa: E402
from dci1v4r3.engine.context import registered_context          # noqa: E402
from dci1v4r3.stages import registration                        # noqa: E402


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True,
                          check=True).stdout.strip()


ADOPTION = {
    "protocol_version": registration.PROTOCOL_VERSION,
    "adopted": True,
    "adopted_on": "2026-08-21",
    "authority": "the researcher's session brief of 2026-08-21, recorded in "
                 "dci1/DECISIONS_V4R3.md entry A0",
    "record": "dci1/DECISIONS_V4R3.md",
    "version_boundary_argument":
        "v4r2 §31 makes any pre-freeze change a revision; v4r2 was never "
        "frozen and produced no confirmatory data, so v4r3 is a revision and "
        "not a new protocol version",
    "amendments": [
        {"id": "R1", "section": "§10.4-R", "changelog": "C26",
         "date": "2026-08-21",
         "what": "the autorater's judging task is replaced by an "
                 "operationalization audit with planted defects",
         "registered_before": "any card was judged"},
        {"id": "R3", "section": "§7.0-R3", "changelog": "C27",
         "date": "2026-08-21",
         "what": "six counted statistics, six feature groups, a fifth "
                 "predicate form and ten families are added to the candidate "
                 "library; no criterion, caliper or admission rule changes",
         "registered_before": "any solo compliance of any added family was "
                              "measured on any model"},
    ],
    "withheld": [
        "any retrospective change to v4r2 or earlier evidence",
        "any weakening of a gate after observing a failure",
        "any selection of a control from a composed outcome",
        "§10.4's measurement_basis = autorater_calibration_approved, which "
        "Gate 1 cannot pass without and which no agent may write on the "
        "researcher's behalf",
    ],
}


def cmd_register(args) -> int:
    context = registered_context()
    if context.registration_manifest.exists() and not args.supersede:
        print(json.dumps({"already_registered": True,
                          "path": str(context.registration_manifest)},
                         indent=1))
        return 0
    supersedes = None
    if args.supersede:
        supersedes = registration.load_manifest(context)["manifest_hash"]
    manifest = registration.register(context, producing_commit=_commit(),
                                     adoption=ADOPTION, supersedes=supersedes)
    print(json.dumps({"registered": True,
                      "manifest_hash": manifest["manifest_hash"],
                      "path": str(context.registration_manifest)}, indent=1))
    return 0


def cmd_show(args) -> int:
    context = registered_context()
    print(json.dumps(registration.load_manifest(context), indent=1)[:4000])
    return 0


def cmd_qualify(args) -> int:
    """§18 stage 1. Reports every check, and fails closed on any."""
    from dci1v4.engine import fs
    from dci1v4.errors import TerminalStatus
    from dci1v4r3.stages.qualification import qualification_payload

    context = registered_context()
    registration.load_manifest(context)
    out = REPO / "reports" / "dci1v4r3"
    out.mkdir(parents=True, exist_ok=True)
    try:
        record = qualification_payload(context, producing_commit=_commit())
    except TerminalStatus as terminal:
        fs.write_json(out / "qualification.json", terminal.record)
        print(json.dumps({"outcome": "TERMINAL",
                          "status": terminal.status,
                          "failed": terminal.record["failed"],
                          "passed": [c["check"] for c in
                                     terminal.record["checks"]
                                     if c["passed"]]}, indent=1))
        return 0
    fs.write_json(out / "qualification.json", record)
    # §18 stage 1 is study-wide -- its checks are about the worktree, the
    # environment and the instrument population, none of which is per-model --
    # but the stage machine is per-replication, so each tree gets the same
    # signed record. Without it GATE_0 has no predecessor to verify and the
    # sequence could not start.
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import write_stage_record
    from dci1v4r3.protocol import constants as C

    written = []
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        if tree.stage_record(C.STAGE_QUALIFIED).exists():
            continue
        write_stage_record(tree, C.STAGE_QUALIFIED,
                           {**record, "model_key": model_key,
                            "scope": "study-wide; the same record is written "
                                     "to every replication tree"})
        written.append(model_key)
    print(json.dumps({"outcome": record["outcome"],
                      "stage_records_written": written}, indent=1))
    return 0


def _calibration_texts(limit: int | None = None) -> list[str]:
    """Every genuine response v4r3 has produced, for §10.2's evidence.

    §6.2 lists Gate 1 validation material as a permitted use of the pre-screen
    topics, and the regime screen is where those responses come from. Reading
    them here is the registered use; no other set is touched.
    """
    from dci1v4r3 import EVIDENCE_DIRNAME
    from dci1v4r3.engine.paths import current_files
    root = REPO / "evidence" / EVIDENCE_DIRNAME
    texts: list[str] = []
    for path in current_files(root, "scored.jsonl"):
        for line in path.read_text().splitlines():
            if line.strip():
                texts.append(json.loads(line)["raw_response"])
                if limit and len(texts) >= limit:
                    return texts
    return texts


def cmd_gate1(args) -> int:
    """Collect §10.2's evidence and put it to the gate.

    The gate is *expected* to refuse while the measurement basis is
    ``human_validation_unavailable``: §10.3 routes an absent annotator to
    §10.4, and §10.4 ends in an explicit researcher approval. The refusal is
    the correct outcome and the evidence is written either way, because the
    evidence is what the researcher needs in order to decide.
    """
    from dci1v4.engine import fs
    from dci1v4.errors import TerminalStatus
    from dci1v4r3.stages.gate1 import collect_evidence, gate1_payload
    from dci1v4r3.stages.audit import (assert_reserved_sets_unspent,
                                       audit_evidence_tree)
    from dci1v4r3 import EVIDENCE_DIRNAME

    context = registered_context()
    registration.load_manifest(context)
    audit = assert_reserved_sets_unspent(
        audit_evidence_tree(REPO / "evidence" / EVIDENCE_DIRNAME))
    texts = _calibration_texts(args.responses)
    evidence = collect_evidence(texts,
                                determinism_sample=args.determinism_sample,
                                verdict_sample=args.verdict_sample)
    evidence["topic_audit"] = audit
    out = REPO / "reports" / "dci1v4r3"
    out.mkdir(parents=True, exist_ok=True)
    fs.write_json(out / "gate1_evidence.json", evidence)

    try:
        record = gate1_payload(evidence=evidence,
                               measurement_basis=args.measurement_basis,
                               identification_statuses=[
                                   "HUMAN_VALIDATION_UNAVAILABLE"])
    except TerminalStatus as terminal:
        fs.write_json(out / "gate1_outcome.json", terminal.record)
        print(json.dumps({"outcome": "REFUSED",
                          "status": terminal.status,
                          "observed": terminal.record.get("observed"),
                          "per_model": _gate1_record_per_model(context, None),
                          "evidence": str(out / "gate1_evidence.json")},
                         indent=1))
        return 0
    fs.write_json(out / "gate1_outcome.json", record)
    print(json.dumps({"outcome": record["outcome"],
                      "measurement_basis": record["measurement_basis"],
                      "per_model": _gate1_record_per_model(context, record)},
                     indent=1))
    return 0


def _gate1_record_per_model(context, record) -> dict[str, str]:
    """§10.2's evidence is study-wide; §18's record is not.

    The instrument population, the boundary suites and the reimplementation
    are one body of evidence about one verifier hash, so they are collected
    once. The *stage* is per replication, because §18's machine is, so a
    passing gate writes one signed record per model that has reached it and a
    refusing gate logs the refusal against each of them --- an attempted
    transition that was refused is exactly what §18's log exists to show.
    """
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
    )
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.regime_screen import mirror_records

    out: dict[str, str] = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        try:
            assert_transition_legal(tree, C.STAGE_GATE1)
        except Exception as refusal:
            out[model_key] = f"NOT_ELIGIBLE: {type(refusal).__name__}"
            continue
        if record is None:
            log_transition(tree, stage=C.STAGE_GATE1, outcome="REFUSED",
                           producing_commit=_commit(),
                           environment_digest="-",
                           detail={"status": "MEASUREMENT_EVIDENCE_"
                                             "INSUFFICIENT"})
            out[model_key] = "REFUSED"
            continue
        write_stage_record(tree, C.STAGE_GATE1, {**record,
                                                 "model_key": model_key})
        mirror_records(model_key, C.STAGE_GATE1)
        log_transition(tree, stage=C.STAGE_GATE1, outcome="PASS",
                       producing_commit=_commit(), environment_digest="-",
                       detail={"measurement_basis":
                               record["measurement_basis"]})
        out[model_key] = "PASS"
    return out


def cmd_regime(args) -> int:
    """§12, under the stage machine: Gate 0 must have passed first."""
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
        write_terminal_report,
    )
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.regime_screen import mirror_records, run_regime_screen
    context = registered_context()
    registration.load_manifest(context)      # §18 stage 1: fails closed
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, C.STAGE_REGIME)
    record = run_regime_screen(args.model, device=args.device, cap=args.cap,
                               limit=args.limit)
    if record.get("outcome") == "TERMINAL":
        write_terminal_report(tree, {
            **record, "model_key": args.model, "gate": C.STAGE_REGIME,
            "criterion": record.get("completion_cap", {}).get("criterion", ""),
            "observed": record.get("completion_cap", {}).get("table", {}),
            "producing_commit": _commit(),
            "strongest_permissible_statement": C.TERMINAL_SENTENCE})
        log_transition(tree, stage=C.STAGE_REGIME, outcome="TERMINAL",
                       producing_commit=_commit(), environment_digest="-",
                       detail={"status": record.get("status")})
        print(json.dumps({"outcome": "TERMINAL",
                          "status": record.get("status")}, indent=1))
        return 1
    write_stage_record(tree, C.STAGE_REGIME, record)
    mirror_records(args.model, C.STAGE_REGIME)
    log_transition(tree, stage=C.STAGE_REGIME, outcome=record["outcome"],
                   producing_commit=_commit(), environment_digest="-",
                   detail={"rows": record.get("rows_generated"),
                           "coverage_passed":
                               record.get("expansion", {}).get("passed")})
    summary = {k: record[k] for k in
               ("outcome", "model_key", "selected_cap", "iota_a_prescreen")
               if k in record}
    summary["status"] = record.get("status")
    if "expansion" in record:
        summary["coverage_passed"] = record["expansion"]["passed"]
        summary["rounds_run"] = record["expansion"]["rounds_run"]
        summary["statuses"] = record["expansion"]["statuses"]
        summary["rows"] = record["rows_generated"]
    print(json.dumps(summary, indent=1))
    return 0


def cmd_restart(args) -> int:
    """Retire stage records from ``--from`` onward so they can be re-run.

    A prospective amendment changes the executable code, and §18's own rule
    --- a record binds to its producing commit --- then makes every record
    produced under the earlier code unusable as a predecessor. Retiring them
    is the registered way to say so: the directories move to
    ``superseded/<commit>/``, keeping every generated row exactly where a
    reader can still find it, and the transition log gains a SUPERSEDED row.
    Nothing is deleted and nothing is edited.
    """
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import supersede_stage_records
    from dci1v4r3.protocol import constants as C

    context = registered_context()
    order = list(C.STAGE_SEQUENCE)
    if args.from_stage not in order:
        print(json.dumps({"error": f"{args.from_stage} is not a stage",
                          "sequence": order}, indent=1))
        return 2
    stages = order[order.index(args.from_stage):]
    out = {}
    for model_key in ([args.model] if args.model else MODEL_KEYS):
        tree = model_tree(context, model_key)
        out[model_key] = supersede_stage_records(
            tree, stages, reason=args.reason,
            superseded_by_commit=_commit())
    print(json.dumps({"superseded_from": args.from_stage,
                      "commit": _commit(), "models": out}, indent=1))
    return 0


def cmd_status(args) -> int:
    """Where each replication stands in the registered stage sequence."""
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import (
        stage_reached, terminal_status, transition_rows,
    )
    from dci1v4r3.protocol import constants as C

    context = registered_context()
    out = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        records = {}
        for stage in C.STAGE_SEQUENCE:
            path = tree.stage_record(stage)
            if path.exists():
                import json as _json
                payload = _json.loads(path.read_text())
                payload = payload.get("payload", payload)
                records[stage] = payload.get("outcome")
        out[model_key] = {
            "reached": stage_reached(tree),
            "terminal": terminal_status(tree),
            "records": records,
            "transitions": len(transition_rows(tree)),
        }
    print(json.dumps({"study": "dci1v4r3", "sequence": list(C.STAGE_SEQUENCE),
                      "models": out}, indent=1))
    return 0


def cmd_gate0(args) -> int:
    """§19's procedural pilot, under the stage machine."""
    from dci1v4.errors import TerminalStatus
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
        write_terminal_report,
    )
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.pilot_run import run_pilot

    context = registered_context()
    registration.load_manifest(context)
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, C.STAGE_GATE0)
    try:
        payload = run_pilot(args.model, tree, device=args.device,
                            cap=args.cap)
    except TerminalStatus as terminal:
        record = {**terminal.record, "model_key": args.model,
                  "producing_commit": _commit()}
        write_terminal_report(tree, record)
        log_transition(tree, stage=C.STAGE_GATE0, outcome="TERMINAL",
                       producing_commit=_commit(), environment_digest="-",
                       detail={"status": record.get("status")})
        print(json.dumps({"outcome": "TERMINAL",
                          "status": record.get("status")}, indent=1))
        return 1
    write_stage_record(tree, C.STAGE_GATE0, payload)
    from dci1v4r3.run.regime_screen import mirror_records
    mirror_records(args.model, C.STAGE_GATE0)
    log_transition(tree, stage=C.STAGE_GATE0, outcome="PASS",
                   producing_commit=_commit(), environment_digest="-",
                   detail={"cached_draws": payload["cached_draws"]})
    print(json.dumps({"outcome": payload["outcome"],
                      "cached_draws": payload["cached_draws"],
                      "cells": payload["cells"]}, indent=1))
    return 0


def _stage_payload(tree, stage):
    from dci1v4r3.engine.transitions import read_stage_record
    return read_stage_record(tree, stage)


def _run_stage(args, stage: str, build, *, summary_keys=()) -> int:
    """One stage, under the machine: legal, run, sign, mirror, log.

    Every stage command in this tool goes through here, so the order --- check
    the predecessor, then generate, then sign, then mirror, then log --- is the
    same for all of them and a new stage cannot quietly skip a step.
    """
    from dci1v4.errors import TerminalStatus
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
        write_terminal_report,
    )
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.regime_screen import mirror_records

    context = registered_context()
    registration.load_manifest(context)
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, stage)
    try:
        payload = build(tree, context)
    except TerminalStatus as terminal:
        record = {**terminal.record, "model_key": args.model, "gate": stage,
                  "criterion": terminal.record.get("criterion",
                                                   terminal.args[0]),
                  "observed": terminal.record.get("observed",
                                                  terminal.record),
                  "producing_commit": _commit(),
                  "strongest_permissible_statement": C.TERMINAL_SENTENCE}
        record.setdefault("status", terminal.args[0])
        write_terminal_report(tree, record)
        log_transition(tree, stage=stage, outcome="TERMINAL",
                       producing_commit=_commit(), environment_digest="-",
                       detail={"status": record.get("status")})
        print(json.dumps({"model": args.model, "stage": stage,
                          "outcome": "TERMINAL",
                          "status": record.get("status")}, indent=1))
        return 1
    if payload.get("outcome") != "PASS":
        print(json.dumps({"model": args.model, "stage": stage,
                          **{k: payload.get(k) for k in
                             ("outcome", "status", *summary_keys)}}, indent=1))
        return 1
    write_stage_record(tree, stage, payload)
    mirror_records(args.model, stage)
    log_transition(tree, stage=stage, outcome="PASS",
                   producing_commit=_commit(), environment_digest="-",
                   detail={k: payload.get(k) for k in summary_keys})
    print(json.dumps({"model": args.model, "stage": stage, "outcome": "PASS",
                      **{k: payload.get(k) for k in summary_keys}},
                     indent=1, default=str))
    return 0


def cmd_gate2(args) -> int:
    """§12.3 and §12.4, on the 96 calibration topics."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.gates_run import run_gate2

    def build(tree, context):
        regime = _stage_payload(tree, C.STAGE_REGIME)
        return run_gate2(args.model, tree, regime_record=regime,
                         device=args.device)

    return _run_stage(args, C.STAGE_GATE2, build,
                      summary_keys=("n_star", "m_star", "iota_a",
                                    "calibration_rows"))


def cmd_gate3(args) -> int:
    """§13.4, §13.6 and §13.7, from Gate 2's solo calibration table."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.gates_run import run_gate3

    def build(tree, context):
        gate2 = _stage_payload(tree, C.STAGE_GATE2)
        regime = _stage_payload(tree, C.STAGE_REGIME)
        return run_gate3(args.model, tree, gate2_record=gate2,
                         regime_record=regime,
                         calibration=gate2["calibration_table"])

    return _run_stage(args, C.STAGE_GATE3, build,
                      summary_keys=("design", "design_variant", "class_arm",
                                    "core_references", "spectrum",
                                    "identification_statuses"))


def cmd_gate4(args) -> int:
    """§13.10's viability predicate, on the 24 composed-validation topics."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.gates_run import run_gate4

    def build(tree, context):
        return run_gate4(args.model, tree,
                         gate2_record=_stage_payload(tree, C.STAGE_GATE2),
                         gate3_record=_stage_payload(tree, C.STAGE_GATE3),
                         regime_record=_stage_payload(tree, C.STAGE_REGIME),
                         device=args.device)

    return _run_stage(args, C.STAGE_GATE4, build,
                      summary_keys=("rows", "cells", "design_variant", "band"))


def cmd_gate5(args) -> int:
    """§18.1's freeze: assemble from what is signed, then put it to the rule."""
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
    )
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.freeze_run import run_freeze
    from dci1v4r3.run.regime_screen import mirror_records

    context = registered_context()
    manifest = registration.load_manifest(context)
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, C.STAGE_GATE5)
    records = {stage: _stage_payload(tree, stage)
               for stage in (C.STAGE_REGIME, C.STAGE_GATE2, C.STAGE_GATE3,
                             C.STAGE_GATE4)}
    gate1_path = REPO / "reports" / "dci1v4r3" / "gate1_measurement.json"
    gate1 = json.loads(gate1_path.read_text()) if gate1_path.exists() else None
    durable_path = REPO / "reports" / "dci1v4r3" / "durability.json"
    durability = (json.loads(durable_path.read_text())
                  if durable_path.exists() else None)
    record = run_freeze(args.model, manifest=manifest, records=records,
                        gate1=gate1, durability=durability,
                        producing_commit=_commit())
    out = REPO / "reports" / "dci1v4r3"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"freeze_{args.model}.json").write_text(
        json.dumps(record, indent=1, sort_keys=True, default=str) + "\n")
    if record.get("outcome") != "PASS":
        log_transition(tree, stage=C.STAGE_GATE5, outcome="REFUSED",
                       producing_commit=_commit(), environment_digest="-",
                       detail={"missing": record.get("missing_fields"),
                               "unclosed": record.get("unclosed_decisions")})
        print(json.dumps({k: record.get(k) for k in
                          ("model_key", "outcome", "missing_fields",
                           "unclosed_decisions", "incomplete_checks")},
                         indent=1))
        return 1
    write_stage_record(tree, C.STAGE_GATE5, record)
    mirror_records(args.model, C.STAGE_GATE5)
    log_transition(tree, stage=C.STAGE_GATE5, outcome="PASS",
                   producing_commit=_commit(), environment_digest="-",
                   detail={"design_variant": record["design_variant"]})
    print(json.dumps({"model": args.model, "outcome": "PASS",
                      "design_variant": record["design_variant"]}, indent=1))
    return 0


def cmd_confirmatory(args) -> int:
    """§21's generation. Licensed by the freeze and by nothing else."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.confirmatory_run import run_confirmatory

    def build(tree, context):
        freeze = _stage_payload(tree, C.STAGE_GATE5)
        return run_confirmatory(args.model, tree, freeze_record=freeze,
                                device=args.device,
                                batch_size=args.batch_blocks)

    return _run_stage(args, C.STAGE_CONFIRMATORY, build,
                      summary_keys=("rows", "blocks_generated",
                                    "completeness"))


def cmd_masked_analysis(args) -> int:
    """§20 and §15: the masked view, analysed and sealed."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.analysis_run import run_masked_analysis
    from dci1v4r3.run.confirmatory_run import collect_rows

    def build(tree, context):
        freeze = _stage_payload(tree, C.STAGE_GATE5)
        _stage_payload(tree, C.STAGE_CONFIRMATORY)
        return run_masked_analysis(args.model, tree, freeze_record=freeze,
                                   rows=collect_rows(tree),
                                   resamples=args.resamples)

    return _run_stage(args, C.STAGE_MASKED_ANALYSIS, build,
                      summary_keys=("masked_artifact_hash", "blocks",
                                    "mask_effectiveness"))


def cmd_unmask(args) -> int:
    """§20's irreversible unmask, bound to the sealed masked artifact."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.analysis_run import run_unmasking

    def build(tree, context):
        masked = _stage_payload(tree, C.STAGE_MASKED_ANALYSIS)
        return run_unmasking(args.model, tree, masked_record=masked)

    return _run_stage(args, C.STAGE_UNMASKING,
                      build, summary_keys=("mask_key_hash",
                                           "masked_outputs_hash"))


def cmd_final_analysis(args) -> int:
    """§15 and §17: the fixed analysis, then the frozen claim ladder."""
    from dci1v4r3.protocol import constants as C
    from dci1v4r3.run.analysis_run import run_unmasked_analysis
    from dci1v4r3.run.confirmatory_run import collect_rows

    def build(tree, context):
        freeze = _stage_payload(tree, C.STAGE_GATE5)
        masked = _stage_payload(tree, C.STAGE_MASKED_ANALYSIS)
        _stage_payload(tree, C.STAGE_UNMASKING)
        return run_unmasked_analysis(args.model, tree, freeze_record=freeze,
                                     rows=collect_rows(tree),
                                     masked_record=masked,
                                     resamples=args.resamples)

    return _run_stage(args, C.STAGE_UNMASKED_ANALYSIS, build,
                      summary_keys=("blocks", "design_variant",
                                    "analysis_code_hash"))


def cmd_adopt_regime(args) -> int:
    """Record the existing §12.2 evidence as ADOPTED_OUT_OF_ORDER.

    It was generated before the stage machine existed, so it cannot satisfy
    Gate 1's predecessor requirement. Recording that is honest; letting it
    count would not be.
    """
    from dci1v4.engine import fs
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.engine.transitions import adopt_out_of_order
    from dci1v4r3.protocol import constants as C

    context = registered_context()
    done = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        source = tree.stage_dir(C.STAGE_REGIME) / "regime_record.json"
        if not source.exists():
            continue
        canonical = tree.stage_record(C.STAGE_REGIME)
        if canonical.exists():
            existing = fs.read_json(canonical)
            if "signature" in existing:
                continue                      # already a real stage record
            # `_mirror` wrote an UNSIGNED byte copy of the reader file into
            # the stage-record slot before the stage machine existed. It is a
            # duplicate of `regime_record.json`, not raw evidence, and leaving
            # it there would let `status` report a PASS the stage machine
            # never granted. Replaced only after confirming it is that copy.
            if canonical.read_bytes() != source.read_bytes():
                raise SystemExit(
                    f"{canonical} is not a byte copy of {source}; refusing to "
                    f"replace it")
            canonical.unlink()
        payload = fs.read_json(source)
        payload = {**payload,
                   "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_REGIME]}
        adopt_out_of_order(
            tree, C.STAGE_REGIME, payload,
            reason=("generated 2026-08-21 before dci1v4r3/engine/transitions "
                    "existed; no guard could refuse an out-of-order stage"),
            produced_before_commit="6954dd6")
        done[model_key] = "ADOPTED_OUT_OF_ORDER"
    print(json.dumps({"adopted": done,
                      "consequence": "does not satisfy any later stage's "
                                     "predecessor requirement"}, indent=1))
    return 0


def cmd_seal_cap_probe(args) -> int:
    """Derive §12.1's restricted truncation artifact for every replication.

    The regime record already carries the registered truncation table and
    nothing else from the probe, so this reads that block rather than the raw
    scored rows. It exists so the artifact a later stage consumes is a file
    with no outcome-bearing field in it, not a projection some caller has to
    remember to apply.
    """
    from dci1v4.engine import fs
    from dci1v4r3.engine.paths import model_tree
    from dci1v4r3.stages import cap_probe

    context = registered_context()
    written = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        record_path = tree.stage_dir("REGIME_SCREEN") / "regime_record.json"
        if not record_path.exists():
            continue
        record = fs.read_json(record_path)
        cap = record.get("completion_cap", {})
        table = {int(k): v for k, v in (cap.get("table") or {}).items()}
        artifact = cap_probe.cap_probe_artifact(
            table, model_key=model_key,
            selected_cap=cap.get("selected_cap"))
        fs.write_json(tree.cap_probe_truncation, artifact)
        written[model_key] = str(tree.cap_probe_truncation)
    print(json.dumps({"sealed": written}, indent=1))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    register_cmd = sub.add_parser("register")
    register_cmd.add_argument(
        "--supersede", action="store_true",
        help="re-issue the manifest, retaining the previous one beside it and "
             "naming its hash. §26's artifact model marks a superseded record "
             "rather than deleting or editing it.")
    register_cmd.set_defaults(func=cmd_register)
    sub.add_parser("show").set_defaults(func=cmd_show)
    regime = sub.add_parser("regime")
    regime.add_argument("--model", required=True, choices=MODEL_KEYS)
    regime.add_argument("--device", type=int, default=0)
    regime.add_argument("--cap", type=int, default=None)
    regime.add_argument("--limit", type=int, default=None)
    regime.set_defaults(func=cmd_regime)
    gate1 = sub.add_parser("gate1")
    gate1.add_argument("--responses", type=int, default=None,
                       help="cap the calibration corpus; default all")
    gate1.add_argument("--determinism-sample", type=int, default=400)
    gate1.add_argument("--verdict-sample", type=int, default=1200)
    gate1.add_argument("--measurement-basis", default="human_validation_unavailable",
                       choices=("human_validation_unavailable",
                                "autorater_calibration_approved",
                                "human_validated"))
    gate1.set_defaults(func=cmd_gate1)
    sub.add_parser("qualify").set_defaults(func=cmd_qualify)
    sub.add_parser("status").set_defaults(func=cmd_status)
    gate0 = sub.add_parser("gate0")
    gate0.add_argument("--model", required=True, choices=MODEL_KEYS)
    gate0.add_argument("--device", type=int, default=0)
    gate0.add_argument("--cap", type=int, default=512)
    gate0.set_defaults(func=cmd_gate0)
    restart = sub.add_parser("restart")
    restart.add_argument("--from", dest="from_stage", required=True)
    restart.add_argument("--reason", required=True)
    restart.add_argument("--model", default=None, choices=sorted(MODEL_KEYS))
    restart.set_defaults(func=cmd_restart)
    for name, func in (("gate2", cmd_gate2), ("gate3", cmd_gate3),
                       ("gate4", cmd_gate4)):
        cmd = sub.add_parser(name)
        cmd.add_argument("--model", required=True, choices=sorted(MODEL_KEYS))
        cmd.add_argument("--device", type=int, default=0)
        cmd.set_defaults(func=func)
    gate5 = sub.add_parser("gate5")
    gate5.add_argument("--model", required=True, choices=sorted(MODEL_KEYS))
    gate5.set_defaults(func=cmd_gate5)
    conf = sub.add_parser("confirmatory")
    conf.add_argument("--model", required=True, choices=sorted(MODEL_KEYS))
    conf.add_argument("--device", type=int, default=0)
    conf.add_argument("--batch-blocks", type=int, default=16)
    conf.set_defaults(func=cmd_confirmatory)
    for name, func in (("masked-analysis", cmd_masked_analysis),
                       ("final-analysis", cmd_final_analysis)):
        cmd = sub.add_parser(name)
        cmd.add_argument("--model", required=True, choices=sorted(MODEL_KEYS))
        cmd.add_argument("--resamples", type=int, default=None)
        cmd.set_defaults(func=func)
    unmask = sub.add_parser("unmask")
    unmask.add_argument("--model", required=True, choices=sorted(MODEL_KEYS))
    unmask.set_defaults(func=cmd_unmask)
    sub.add_parser("adopt-regime").set_defaults(func=cmd_adopt_regime)
    sub.add_parser("seal-cap-probe").set_defaults(func=cmd_seal_cap_probe)
    args = parser.parse_args()
    if getattr(args, "resamples", "absent") is None:
        from dci1v4r3.protocol import constants as C
        args.resamples = C.BOOTSTRAP_RESAMPLES
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
