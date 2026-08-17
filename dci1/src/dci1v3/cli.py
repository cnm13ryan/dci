"""The canonical registered execution interface (item 3).

Every public command names an operation and dispatches through the one
canonical state machine and evidence architecture; no command calls
generation, storage, selection, masking, analysis, or reporting
implementations directly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dci1v3.engine import fs
from dci1v3.engine.context import (
    StudyContext,
    registered_context,
    synthetic_context,
)
from dci1v3.engine.dispatch import dispatch
from dci1v3.errors import V3Error
from dci1v3.models.registry import MODEL_KEYS
import dci1v3.stages  # noqa: F401  — populates the operation registry

MODEL_OPERATIONS = (
    "qualify", "pilot", "prescreen", "carry-over", "gate1-dev",
    "gate1-calibrate", "gate1", "human-audit", "gate2a",
    "gate2b", "freeze", "generate", "select-primary", "mask",
    "masked-analysis", "unmask", "final-analysis", "pseudo-runs", "greedy",
    "verify-evidence",
)


def _context(args: argparse.Namespace) -> StudyContext:
    if args.synthetic_root:
        return synthetic_context(Path(args.synthetic_root),
                                 Path(args.repo_root))
    return registered_context()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dci1v3")
    parser.add_argument("--synthetic-root", default=None,
                        help="run in the synthetic namespace rooted here")
    parser.add_argument("--repo-root", default=None,
                        help="repository root for the synthetic namespace")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("register", help="create the signed study registration")
    vfreeze = sub.add_parser(
        "verifier-freeze",
        help="study-level: freeze the verifier for held-out calibration "
             "(runs the verifier regression suite first)")
    vfreeze.add_argument("--autorater-config", default=None)
    signoff = sub.add_parser(
        "gate1-signoff",
        help="study-level: the cross-model inspection summary "
             "(development before the freeze, calibration before "
             "approval); --notes attaches the researcher's inspection "
             "record")
    signoff.add_argument("--phase", required=True,
                         choices=("development", "calibration"))
    signoff.add_argument("--notes", default=None)
    signoff.add_argument("--autorater-config", default=None)
    readiness = sub.add_parser("readiness", help="the item-65 report")
    readiness.add_argument("--out", default=None)
    for name in MODEL_OPERATIONS:
        cmd = sub.add_parser(name)
        cmd.add_argument("--model", required=True, choices=MODEL_KEYS)
        cmd.add_argument("--device", type=int, default=0,
                         help="GPU device for backend runs (operational "
                              "routing only; both cards are the same "
                              "registered hardware class)")
        if name in ("gate1-dev", "gate1-calibrate"):
            cmd.add_argument("--autorater-config", default=None)
        if name == "gate1":
            cmd.add_argument("--approve-autorater-calibration",
                             action="store_true",
                             help="explicit researcher approval of the "
                                  "inspected calibration report")
        if name == "human-audit":
            cmd.add_argument("--annotations", required=True,
                             help="the reviewer-GUI export (independent "
                                  "human labels)")
        if name == "pseudo-runs":
            cmd.add_argument("--runs", type=int, default=None)
        if name == "verify-evidence":
            cmd.add_argument("--expected", default=None)

    args = parser.parse_args(argv)
    context = _context(args)
    try:
        if args.command == "register":
            from dci1v3.stages.registration import register_study
            outcome = register_study(context)
        elif args.command == "verifier-freeze":
            from dci1v3.stages.gate1 import verifier_freeze
            outcome = verifier_freeze(
                context, autorater_config=args.autorater_config)
        elif args.command == "gate1-signoff":
            from dci1v3.stages.gate1 import gate1_signoff
            outcome = gate1_signoff(
                context, phase=args.phase, notes_path=args.notes,
                autorater_config=args.autorater_config)
        elif args.command == "readiness":
            from dci1v3.stages.report import readiness_report
            outcome = readiness_report(context)
            if args.out:
                fs.write_json(Path(args.out), outcome)
        else:
            options = {}
            for key in ("annotations", "runs", "expected", "device",
                        "autorater_config",
                        "approve_autorater_calibration"):
                if getattr(args, key, None):
                    options[key] = getattr(args, key)
            outcome = dispatch(context, args.command, args.model, **options)
    except V3Error as error:
        print(json.dumps({"error": type(error).__name__,
                          "detail": str(error)}, indent=2))
        return 1
    print(json.dumps(outcome, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
