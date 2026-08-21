"""The v4r4 stage driver: register, qualify, gate 0, regime screen, gate 1.

One entry point per stage so that each is a separate, logged, resumable
command, exactly as §18 requires. Nothing here decides anything scientific;
the rules live in ``dci1v4r4``.

    ./.venv/bin/python tools/run_v4r4.py register
    ./.venv/bin/python tools/run_v4r4.py qualify
    ./.venv/bin/python tools/run_v4r4.py gate0 --model qwen3-4b --carry
    ./.venv/bin/python tools/run_v4r4.py regime --model qwen3-4b --carry
    ./.venv/bin/python tools/run_v4r4.py gate1

``--carry`` is the flag that makes a stage read the superseded revision's
generations instead of calling the backend. It is never the default: a stage
carries evidence when a person says so, and the record it writes says so too.
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
from dci1v4r4.engine.context import registered_context          # noqa: E402
from dci1v4r4.stages import registration                        # noqa: E402


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True,
                          check=True).stdout.strip()


ADOPTION = {
    "protocol_version": registration.PROTOCOL_VERSION,
    "adopted": True,
    "adopted_on": "2026-08-21",
    "authority": "the researcher's session brief of 2026-08-21, recorded in "
                 "dci1/DECISIONS_V4R4.md entry B0",
    "record": "dci1/DECISIONS_V4R4.md",
    "version_boundary_argument":
        "v4r3 was never frozen and produced no confirmatory data. It "
        "terminated at Gate 1 under the measurement criterion registered at "
        "the time, and that outcome stands. v4r4 is a prospective revision "
        "adopted before Gate 2 and before any confirmatory scientific outcome "
        "was observed; it is not a re-reading of v4r3's Gate 1",
    "supersedes": {
        "revision": "v4r3",
        "terminal_stage": "GATE_1_MEASUREMENT",
        "terminal_status": "MEASUREMENT_EVIDENCE_INSUFFICIENT",
        "preserved_at": "dci1/evidence/dci1v4r3, dci1/durable_root/dci1v4r3, "
                        "dci1/reports/dci1v4r3, dci1/DECISIONS_V4R3.md",
        "is_not_a_retroactive_pass":
            "v4r3's Gate-1 records are unmodified and none of them is "
            "described as having passed",
    },
    "amendments": [
        {"id": "R4-1", "section": "§10.7", "date": "2026-08-21",
         "what": "Gate 1's measurement criterion is deterministic "
                 "specification and implementation validation; reviewer "
                 "agreement is a diagnostic and can move no gate",
         "registered_before": "any v4r4 stage record existed"},
        {"id": "R4-2", "section": "§7.0-R4", "date": "2026-08-21",
         "what": "CP4 and CP7 are removed from the candidate population on a "
                 "specification-ambiguity finding; §12.6's coverage criterion "
                 "was re-evaluated on the existing pre-screen table first",
         "registered_before": "any v4r4 generation was scored"},
        {"id": "R4-3", "section": "§10.7 A'", "date": "2026-08-21",
         "what": "every model-facing wording must expose the comparison "
                 "direction of the predicate that scores it",
         "registered_before": "any v4r4 stage record existed"},
    ],
    "withheld": [
        "any retrospective change to v4r3 or earlier evidence",
        "any description of v4r3's Gate 1 as having passed",
        "any weakening of a gate after observing a failure",
        "any selection of a control from a composed outcome",
        "measurement_basis = human_validated, which v4r4 never establishes "
        "and which §10.7 refuses to write",
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


SUPERSEDED_EVIDENCE = REPO / "evidence" / "dci1v4r3"


def carried_root(model_key: str, stage: str):
    """The superseded revision's stage directory for this model.

    Returned only when it exists. A stage asked to carry from a directory that
    is not there fails loudly rather than silently generating: the caller
    checks the return value, because "carry" and "generate" are different
    experiments and choosing between them by accident is the failure this
    whole path exists to prevent.
    """
    path = SUPERSEDED_EVIDENCE / model_key / stage
    return path if path.exists() else None


def cmd_qualify(args) -> int:
    """§18 stage 1. Reports every check, and fails closed on any."""
    from dci1v4.engine import fs
    from dci1v4.errors import TerminalStatus
    from dci1v4r4.stages.qualification import qualification_payload

    context = registered_context()
    registration.load_manifest(context)
    out = REPO / "reports" / "dci1v4r4"
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
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import write_stage_record
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.regime_screen import mirror_records

    written = []
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        if not tree.stage_record(C.STAGE_QUALIFIED).exists():
            write_stage_record(tree, C.STAGE_QUALIFIED,
                               {**record, "model_key": model_key,
                                "scope": "study-wide; the same record is "
                                         "written to every replication tree"})
            written.append(model_key)
        # Outside the write-once branch on purpose. `evidence/` is gitignored,
        # so an unmirrored record has exactly one copy; this command used to
        # skip mirroring entirely, and the four qualification records were the
        # only signed records in the study with no durable copy. Mirroring is
        # idempotent and byte-verified, so doing it every time is free.
        mirror_records(model_key, C.STAGE_QUALIFIED)
    print(json.dumps({"outcome": record["outcome"],
                      "stage_records_written": written,
                      "durable_mirror": "verified for every replication"},
                     indent=1))
    return 0


def _calibration_texts(limit: int | None = None) -> list[str]:
    """Every genuine response v4r3 has produced, for §10.2's evidence.

    §6.2 lists Gate 1 validation material as a permitted use of the pre-screen
    topics, and the regime screen is where those responses come from. Reading
    them here is the registered use; no other set is touched.
    """
    from dci1v4r4 import EVIDENCE_DIRNAME
    from dci1v4r4.engine.paths import current_files
    root = REPO / "evidence" / EVIDENCE_DIRNAME
    texts: list[str] = []
    for path in current_files(root, "scored.jsonl"):
        for line in path.read_text().splitlines():
            if line.strip():
                texts.append(json.loads(line)["raw_response"])
                if limit and len(texts) >= limit:
                    return texts
    return texts


def _supplementary_diagnostics() -> dict[str, object]:
    """v4r3's reviewer evidence, labelled, and never read by the rule.

    It is carried because it is real, it was expensive, and a reader deciding
    whether to trust v4r4's criterion is entitled to see what the criterion it
    replaced actually returned. Each entry names its own recorded outcome.
    Nothing here is described as having succeeded, and nothing here is a
    criterion input: `gate1_payload` takes this whole mapping opaquely.
    """
    reports = REPO / "reports" / "dci1v4r3"
    entries = {
        "section_10_3": (
            "section_10_4_plan.json",
            "the independent-human pathway. No independent annotator was "
            "available and none could be obtained; author-performed labels "
            "are not independent validation"),
        "section_10_4": (
            "section_10_4_development.json",
            "the autorater pathway, first attempt"),
        "section_10_4R": (
            "section_10_4R_outcome.json",
            "the repaired autorater task (operationalization audit)"),
        "section_10_4R2": (
            "section_10_4R2_outcome.json",
            "the microcase validator. FAILED its own criterion 5 and stopped "
            "by rule"),
        "validator_diagnosis": (
            "validator_diagnosis.json",
            "why R2 failed: convention access, not competence"),
        "natural_response_defect_sensitivity": (
            "defect_sensitivity.json",
            "what each registered defect would cost on real screen responses. "
            "A consequence measurement, never semantic validation"),
        "superseded_decision_under_the_former_rule": (
            "gate1_decision.json",
            "v4r3's Gate-1 decision under §18 stage 4 as it stood: "
            "MEASUREMENT_EVIDENCE_INSUFFICIENT. Preserved unmodified"),
    }
    out: dict[str, object] = {
        "role": "SUPPLEMENTARY / DIAGNOSTIC. Preserved v4r3 evidence, "
                "reclassified rather than deleted. No number under this key "
                "is read by v4r4's Gate 1, in either direction",
        "source_study": "dci1v4r3",
    }
    from dci1v4.protocol.hashing import sha_file
    for name, (filename, headline) in entries.items():
        path = reports / filename
        out[name] = {"path": str(path.relative_to(REPO.parent))
                     if path.exists() else f"{path} (absent)",
                     "hash": sha_file(path) if path.exists() else "MISSING",
                     "what_it_is": headline}
    return out


def _provenance(context) -> dict[str, object]:
    """§10.7 condition 10, assembled from the lifecycle itself."""
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import read_stage_record
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.stages.audit import (assert_reserved_sets_unspent,
                                       audit_evidence_tree)
    from dci1v4r4.verifiers.carryover import carry_over_record
    from dci1v4r4 import EVIDENCE_DIRNAME

    per_model: dict[str, object] = {}
    verified = True
    already = False
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        try:
            payload = read_stage_record(tree, C.STAGE_REGIME)
            per_model[model_key] = {
                "predecessor": C.STAGE_REGIME,
                "outcome": payload.get("outcome"),
                "study_id": payload.get("study_id"),
                "signature": "verified"}
            verified = verified and payload.get("outcome") == "PASS"
        except Exception as refusal:                       # noqa: BLE001
            per_model[model_key] = {"predecessor": C.STAGE_REGIME,
                                    "error": f"{type(refusal).__name__}: "
                                             f"{refusal}"}
            verified = False
        already = already or tree.stage_record(C.STAGE_GATE1).exists()

    audit = assert_reserved_sets_unspent(
        audit_evidence_tree(REPO / "evidence" / EVIDENCE_DIRNAME))
    carry = carry_over_record()
    return {
        "predecessor_verified": verified,
        "per_model": per_model,
        "carry_over_passed": carry["composition_equivalence"]["checked"] > 0,
        "carry_over": {k: v for k, v in carry.items()
                       if k != "sources"},
        "reserved_sets_unspent": True,
        "topic_audit": audit,
        "producing_commit": _commit(),
        "no_gate1_record_exists_yet": not already,
    }


def cmd_gate1(args) -> int:
    """§10.7: collect A-E and put them to the gate.

    Everything the rule reads is written out whatever the outcome, because the
    evidence is what a reader needs in order to disagree with the decision.
    """
    from dci1v4.engine import fs
    from dci1v4.errors import TerminalStatus
    from dci1v4r4.protocol.revision import protocol_hash, revision_record
    from dci1v4r4.stages.gate1 import (
        collect_evidence, collect_specification_evidence, gate1_payload,
        measurement_rule_hash,
    )
    from dci1v4r4.stages.specification import (
        assert_direction_lexicon_is_exhaustive,
    )
    from dci1v4r4.verifiers import verifier_source_hash
    from dci1v4r4.verifiers.boundary import instrument_population

    context = registered_context()
    registration.load_manifest(context)
    out = REPO / "reports" / "dci1v4r4"
    out.mkdir(parents=True, exist_ok=True)

    # A' before anything expensive: a wording the invariant cannot resolve is
    # a blocker whatever the implementation evidence says, and finding that
    # out first costs nothing.
    lexicon_exhaustive = True
    lexicon_error = ""
    try:
        assert_direction_lexicon_is_exhaustive()
    except Exception as refusal:                           # noqa: BLE001
        lexicon_exhaustive, lexicon_error = False, str(refusal)

    texts = _calibration_texts(args.responses)
    evidence = collect_evidence(texts,
                               determinism_sample=args.determinism_sample,
                               verdict_sample=args.verdict_sample)
    spec = collect_specification_evidence()
    provenance = _provenance(context)
    provenance["direction_lexicon_exhaustive"] = lexicon_exhaustive
    if lexicon_error:
        provenance["direction_lexicon_error"] = lexicon_error

    fs.write_json(out / "gate1_evidence.json", evidence)
    fs.write_json(out / "specification_audit.json", spec["specification_audit"])
    fs.write_json(out / "mutation_validation.json", spec["mutation_validation"])
    fs.write_json(out / "wording_review.json", spec["wording_review"])

    binding = {
        "protocol_hash": protocol_hash(),
        "revision": revision_record(),
        "measurement_rule_hash": measurement_rule_hash(),
        "canonical_verifier_hash": verifier_source_hash(),
        "wordings_hash": spec["wordings_hash"],
        "specification_hash": spec["specification_hash"],
        "mutation_hash": spec["mutation_hash"],
        "instrument_population": len(instrument_population()),
        "calibration_responses": len(texts),
    }
    try:
        record = gate1_payload(
            evidence=evidence, specification_evidence=spec,
            provenance=provenance,
            supplementary_diagnostics=_supplementary_diagnostics())
    except TerminalStatus as terminal:
        blocked = {**terminal.record, **binding,
                   "producing_commit": _commit()}
        fs.write_json(out / "gate1_decision.json", _compact(blocked))
        print(json.dumps({"outcome": "REFUSED",
                          "status": terminal.status,
                          "failed_conditions":
                              terminal.record.get("failed_conditions"),
                          "observed": terminal.record.get("observed"),
                          "written": str(out / "gate1_decision.json")},
                         indent=1))
        return 1
    record = {**record, **binding}
    fs.write_json(out / "gate1_decision.json", _compact(record))
    print(json.dumps({"outcome": record["outcome"],
                      "measurement_basis": record["measurement_basis"],
                      "instruments": record["instruments"],
                      "verifier_hash": binding["canonical_verifier_hash"][:12],
                      "wordings_hash": binding["wordings_hash"][:12],
                      "specification_hash":
                          binding["specification_hash"][:12],
                      "mutation_hash": binding["mutation_hash"][:12],
                      "protocol_hash": binding["protocol_hash"][:12],
                      "per_model": _gate1_record_per_model(context, record)},
                     indent=1))
    return 0


def _compact(record: dict) -> dict:
    """The written decision, with the bulk trimmed and the hashes kept.

    The three audits are large -- per-family cases, per-wording rows, per-
    defect examples -- and they are already written beside this file under
    their own names and covered by their own hashes. What stays here is what a
    reader needs to see the decision and to find the rest.
    """
    from dci1v4.protocol.hashing import canonical_json, sha_text
    out = dict(record)
    spec = dict(out.get("specification_audit") or {})
    if spec:
        spec["families"] = {
            k: {key: v[key] for key in
                ("form", "specification_complete", "ambiguous",
                 "unresolved_readings", "passed")
                if key in v}
            for k, v in spec.get("families", {}).items()}
        spec["full_artifact"] = "reports/dci1v4r4/specification_audit.json"
        out["specification_audit"] = spec
    mutation = dict(out.get("mutation_validation") or {})
    if mutation:
        mutation["families"] = {
            k: {key: v[key] for key in ("form", "undetected",
                                        "contradictions") if key in v}
            for k, v in mutation.get("families", {}).items()}
        mutation["full_artifact"] = "reports/dci1v4r4/mutation_validation.json"
        out["mutation_validation"] = mutation
    wordings = dict(out.get("wording_review") or {})
    if wordings:
        wordings.pop("findings", None)
        wordings["full_artifact"] = "reports/dci1v4r4/wording_review.json"
        out["wording_review"] = wordings
    out["decision_hash_covers"] = (
        "this file as written. The full audits are covered by "
        "specification_hash, mutation_hash and wordings_hash")
    out["decision_hash"] = sha_text(canonical_json(out))
    return out


def _gate1_record_per_model(context, record) -> dict[str, str]:
    """§10.2's evidence is study-wide; §18's record is not.

    The instrument population, the boundary suites and the reimplementation
    are one body of evidence about one verifier hash, so they are collected
    once. The *stage* is per replication, because §18's machine is, so a
    passing gate writes one signed record per model that has reached it and a
    refusing gate logs the refusal against each of them --- an attempted
    transition that was refused is exactly what §18's log exists to show.
    """
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
    )
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.regime_screen import mirror_records

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
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
        write_terminal_report,
    )
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.regime_screen import mirror_records, run_regime_screen
    context = registered_context()
    registration.load_manifest(context)      # §18 stage 1: fails closed
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, C.STAGE_REGIME)
    source = carried_root(args.model, C.STAGE_REGIME) if args.carry else None
    if args.carry and source is None:
        print(json.dumps({"outcome": "REFUSED", "reason":
                          "--carry was given and the superseded revision "
                          f"holds no REGIME_SCREEN for {args.model}"},
                         indent=1))
        return 1
    record = run_regime_screen(args.model, device=args.device, cap=args.cap,
                               limit=args.limit, carried_root=source)
    if source is not None and record.get("outcome") != "TERMINAL":
        record = {**record, "evidence_provenance": {
            "generations": "CARRIED from dci1v4r3",
            "source": str(source),
            "recomputed_here": [
                "every compliance, vacuity and graded verdict, under this "
                "study's verifier hash",
                "the §12.2 difficulty table and its instructed-compliance "
                "coordinate",
                "§12.6's coverage criterion and the vocabulary freeze",
                "§12.3's shortlist"],
            "population_difference": "CP4 and CP7 are not in this revision's "
                                     "population, so their carried rows score "
                                     "no v4r4 instrument and are absent from "
                                     "this table (§7.0-R4)",
            "ledger": "stages/reuse.py, RECOMPUTED_FROM_EXISTING_RAW_DATA",
        }}
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
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import supersede_stage_records
    from dci1v4r4.protocol import constants as C

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
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import (
        stage_reached, terminal_status, transition_rows,
    )
    from dci1v4r4.protocol import constants as C

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
    print(json.dumps({"study": "dci1v4r4", "sequence": list(C.STAGE_SEQUENCE),
                      "models": out}, indent=1))
    return 0


def cmd_gate0(args) -> int:
    """§19's procedural pilot, under the stage machine."""
    from dci1v4.errors import TerminalStatus
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
        write_terminal_report,
    )
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.pilot_run import run_pilot

    context = registered_context()
    registration.load_manifest(context)
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, C.STAGE_GATE0)
    try:
        source = carried_root(args.model, C.STAGE_GATE0) if args.carry \
            else None
        if args.carry and source is None:
            print(json.dumps({"outcome": "REFUSED", "reason":
                              "--carry was given and the superseded "
                              "revision holds no GATE_0_APPARATUS for "
                              f"{args.model}"}, indent=1))
            return 1
        payload = run_pilot(args.model, tree, device=args.device,
                            cap=args.cap, carried_root=source)
        if source is not None:
            payload = {**payload, "evidence_provenance": {
                "generations": "CARRIED from dci1v4r3",
                "source": str(source),
                "recomputed_here": [
                    "scoring under this study's verifier",
                    "the observation table and its within-block check",
                    "the redacted structural analysis and support verdict",
                    "the masking cycle in this study's namespace",
                    "cache deletion and durable restore",
                    "the byte-mutation refusal"],
                "not_exercised": "the backend call itself. The pinned "
                                 "inference stack, the model revision and the "
                                 "decoding configuration are unchanged and "
                                 "every prompt renders byte-identically, "
                                 "which is checked per row, but no new "
                                 "generation was made by this revision at "
                                 "this stage",
                "ledger": "stages/reuse.py, RECOMPUTED_FROM_EXISTING_RAW_DATA",
            }}
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
    from dci1v4r4.run.regime_screen import mirror_records
    mirror_records(args.model, C.STAGE_GATE0)
    log_transition(tree, stage=C.STAGE_GATE0, outcome="PASS",
                   producing_commit=_commit(), environment_digest="-",
                   detail={"cached_draws": payload["cached_draws"]})
    print(json.dumps({"outcome": payload["outcome"],
                      "cached_draws": payload["cached_draws"],
                      "cells": payload["cells"]}, indent=1))
    return 0


def _stage_payload(tree, stage):
    from dci1v4r4.engine.transitions import read_stage_record
    return read_stage_record(tree, stage)


def _run_stage(args, stage: str, build, *, summary_keys=()) -> int:
    """One stage, under the machine: legal, run, sign, mirror, log.

    Every stage command in this tool goes through here, so the order --- check
    the predecessor, then generate, then sign, then mirror, then log --- is the
    same for all of them and a new stage cannot quietly skip a step.
    """
    from dci1v4.errors import TerminalStatus
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
        write_terminal_report,
    )
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.regime_screen import (
        mirror_records, mirror_terminal_report,
    )

    context = registered_context()
    registration.load_manifest(context)
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, stage)
    try:
        payload = build(tree, context)
    except TerminalStatus as terminal:
        # `terminal.status`, not `terminal.args[0]`: the two subclasses of
        # `TerminalStatus` in this codebase put different things in `args` ---
        # one the bare status, the other "STATUS: replication stops" --- and
        # `write_terminal_report` refuses a status that is not registered.
        # Both define `.status`.
        record = {**terminal.record, "model_key": args.model, "gate": stage,
                  "criterion": terminal.record.get("criterion",
                                                   terminal.status),
                  "observed": terminal.record.get("observed",
                                                  terminal.record),
                  "producing_commit": _commit(),
                  "strongest_permissible_statement": C.TERMINAL_SENTENCE}
        record.setdefault("status", terminal.status)
        write_terminal_report(tree, record)
        # A terminal report is a result, and `evidence/` is gitignored, so
        # without this the record of a failed gate is the one class of v4r4
        # artifact that lives in a single copy.
        mirror_terminal_report(args.model)
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
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.gates_run import run_gate2

    def build(tree, context):
        regime = _stage_payload(tree, C.STAGE_REGIME)
        return run_gate2(args.model, tree, regime_record=regime,
                         device=args.device)

    return _run_stage(args, C.STAGE_GATE2, build,
                      summary_keys=("n_star", "m_star", "iota_a",
                                    "calibration_rows"))


def cmd_gate3(args) -> int:
    """§13.4, §13.6 and §13.7, from Gate 2's solo calibration table."""
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.gates_run import run_gate3

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
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.gates_run import run_gate4

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
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import (
        assert_transition_legal, log_transition, write_stage_record,
    )
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.freeze_run import run_freeze
    from dci1v4r4.run.regime_screen import mirror_records

    context = registered_context()
    manifest = registration.load_manifest(context)
    tree = model_tree(context, args.model)
    assert_transition_legal(tree, C.STAGE_GATE5)
    records = {stage: _stage_payload(tree, stage)
               for stage in (C.STAGE_REGIME, C.STAGE_GATE2, C.STAGE_GATE3,
                             C.STAGE_GATE4)}
    # The Gate 1 basis comes from the model's own *signed* stage record. It
    # used to be read from `reports/dci1v4r4/gate1_measurement.json` --- the
    # name of the stage-record file, not of any report this study writes ---
    # so the path never existed, the basis was always UNKNOWN, §33's D9 never
    # closed and no replication could freeze.
    gate1 = _stage_payload(tree, C.STAGE_GATE1)
    durable_path = REPO / "reports" / "dci1v4r4" / "durability.json"
    durability = (json.loads(durable_path.read_text())
                  if durable_path.exists() else None)
    provenance_path = REPO / "reports" / "dci1v4r4" / "backend_provenance.json"
    if not provenance_path.exists():
        print(json.dumps({"outcome": "REFUSED", "model": args.model,
                          "why": "§18.1 binds the chat template hash, the "
                                 "hardware record and both dependency "
                                 "digests; run tools/"
                                 "v4r4_backend_provenance.py first",
                          "missing": str(provenance_path)}, indent=1))
        return 1
    provenance = json.loads(provenance_path.read_text())
    record = run_freeze(args.model, manifest=manifest, records=records,
                        gate1=gate1, durability=durability,
                        provenance=provenance,
                        producing_commit=_commit())
    out = REPO / "reports" / "dci1v4r4"
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
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.confirmatory_run import run_confirmatory

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
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.analysis_run import run_masked_analysis
    from dci1v4r4.run.confirmatory_run import collect_rows

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
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.analysis_run import run_unmasking

    def build(tree, context):
        masked = _stage_payload(tree, C.STAGE_MASKED_ANALYSIS)
        return run_unmasking(args.model, tree, masked_record=masked)

    return _run_stage(args, C.STAGE_UNMASKING,
                      build, summary_keys=("mask_key_hash",
                                           "masked_outputs_hash"))


def cmd_final_analysis(args) -> int:
    """§15 and §17: the fixed analysis, then the frozen claim ladder."""
    from dci1v4r4.protocol import constants as C
    from dci1v4r4.run.analysis_run import run_unmasked_analysis
    from dci1v4r4.run.confirmatory_run import collect_rows

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
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.engine.transitions import adopt_out_of_order
    from dci1v4r4.protocol import constants as C

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
            reason=("generated 2026-08-21 before dci1v4r4/engine/transitions "
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
    from dci1v4r4.engine.paths import model_tree
    from dci1v4r4.stages import cap_probe

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
    regime.add_argument("--carry", action="store_true",
                        help="carry the superseded revision's generations "
                             "instead of calling the backend, and recompute "
                             "every verdict here")
    regime.set_defaults(func=cmd_regime)
    gate1 = sub.add_parser("gate1")
    gate1.add_argument("--responses", type=int, default=None,
                       help="cap the calibration corpus; default all")
    gate1.add_argument("--determinism-sample", type=int, default=400)
    gate1.add_argument("--verdict-sample", type=int, default=1200)
    gate1.set_defaults(func=cmd_gate1)
    sub.add_parser("qualify").set_defaults(func=cmd_qualify)
    sub.add_parser("status").set_defaults(func=cmd_status)
    gate0 = sub.add_parser("gate0")
    gate0.add_argument("--model", required=True, choices=MODEL_KEYS)
    gate0.add_argument("--device", type=int, default=0)
    gate0.add_argument("--cap", type=int, default=512)
    gate0.add_argument("--carry", action="store_true",
                       help="carry the superseded revision's pilot "
                            "generations and run every other §19 check here")
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
        from dci1v4r4.protocol import constants as C
        args.resamples = C.BOOTSTRAP_RESAMPLES
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
