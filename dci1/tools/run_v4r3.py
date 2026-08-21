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
    print(json.dumps({"outcome": record["outcome"]}, indent=1))
    return 0


def _calibration_texts(limit: int | None = None) -> list[str]:
    """Every genuine response v4r3 has produced, for §10.2's evidence.

    §6.2 lists Gate 1 validation material as a permitted use of the pre-screen
    topics, and the regime screen is where those responses come from. Reading
    them here is the registered use; no other set is touched.
    """
    from dci1v4r3 import EVIDENCE_DIRNAME
    root = REPO / "evidence" / EVIDENCE_DIRNAME
    texts: list[str] = []
    for path in sorted(root.rglob("scored.jsonl")):
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
                          "evidence": str(out / "gate1_evidence.json")},
                         indent=1))
        return 0
    fs.write_json(out / "gate1_outcome.json", record)
    print(json.dumps({"outcome": record["outcome"],
                      "measurement_basis": record["measurement_basis"]},
                     indent=1))
    return 0


def cmd_regime(args) -> int:
    from dci1v4r3.run.regime_screen import run_regime_screen
    context = registered_context()
    registration.load_manifest(context)      # §18 stage 1: fails closed
    record = run_regime_screen(args.model, device=args.device, cap=args.cap,
                               limit=args.limit)
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
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
