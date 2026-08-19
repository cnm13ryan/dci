"""The v4 command line: one command per registered stage (§18).

Every command routes through ``engine.dispatch.run_stage``, so the §18
preconditions — predecessor PASS record hash and signature, the §10.6 verifier
binding, a clean worktree, invoked-source membership, and the transition log —
apply identically to all of them and cannot be bypassed by calling a stage
directly from a script.

``freeze`` and ``confirmatory`` are implemented and refuse to run: the task
that produced this implementation stops before both.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from dci1v4.engine.context import registered_context, synthetic_context
from dci1v4.engine.paths import model_tree
from dci1v4.models.registry import MODEL_KEYS
from dci1v4.protocol import constants as C


def _context(args: argparse.Namespace):
    if args.namespace == "synthetic":
        if not args.base:
            raise SystemExit("--base is required in the synthetic namespace")
        return synthetic_context(args.base)
    return registered_context()


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    from dci1v4.engine import transitions
    from dci1v4.engine.verify import reached_stage

    context = _context(args)
    out = {}
    for key in MODEL_KEYS:
        tree = model_tree(context, key)
        out[key] = {
            "reached": reached_stage(tree) if tree.root.exists() else None,
            "terminal": (transitions.terminal_status(tree)
                         if tree.root.exists() else None),
            "identification":
                (transitions.identification_statuses(tree)
                 if tree.root.exists() else []),
        }
    return out


def cmd_verify(args: argparse.Namespace) -> dict[str, Any]:
    from dci1v4.engine.verify import verify_model_tree

    context = _context(args)
    return {key: verify_model_tree(model_tree(context, key))
            for key in ([args.model] if args.model else MODEL_KEYS)}


def cmd_menu(args: argparse.Namespace) -> dict[str, Any]:
    from dci1v4.analysis.variance import select_allocation
    return select_allocation()


def cmd_freeze(args: argparse.Namespace) -> dict[str, Any]:
    raise SystemExit(
        "GATE_5_FREEZE is implemented and is not executed: the protocol is "
        "not frozen, nine registered open decisions remain, and the "
        "pre-freeze checks are the researcher's to close. See "
        "docs/v4_traceability.md.")


def cmd_confirmatory(args: argparse.Namespace) -> dict[str, Any]:
    raise SystemExit(
        "CONFIRMATORY_GENERATION is implemented and is not executed: it "
        "requires a Gate 5 freeze record, and this implementation stops "
        "before the freeze.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dci1v4", description=__doc__)
    parser.add_argument("--namespace", choices=("registered", "synthetic"),
                        default="registered")
    parser.add_argument("--base", help="synthetic-namespace root")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="per-model stage and status")
    status.set_defaults(handler=cmd_status)

    verify = sub.add_parser("verify", help="full evidence verification")
    verify.add_argument("--model", choices=MODEL_KEYS)
    verify.set_defaults(handler=cmd_verify)

    menu = sub.add_parser("menu", help="what the §16.3 allocation rule selects")
    menu.set_defaults(handler=cmd_menu)

    freeze = sub.add_parser("freeze", help="Gate 5 (implemented, not executed)")
    freeze.set_defaults(handler=cmd_freeze)

    confirmatory = sub.add_parser("confirmatory",
                                  help="confirmatory generation (not executed)")
    confirmatory.set_defaults(handler=cmd_confirmatory)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = args.handler(args)
    json.dump(result, sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
