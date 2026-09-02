"""The confirmatory command line: one stage, one command, in order.

    python -m dci1v8dev.confirm.cli status --model <key> --root <dir>
    python -m dci1v8dev.confirm.cli run --stage <STAGE> --model <key> --root <dir>
        [--pilot-root <dir>]... [--device N] [--synthetic]

``--pilot-root MODEL=DIR`` binds a pilot root per model at registration
(every model of the study, once per root). ``--device`` is placement only.
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from dci1v4.engine.signing import create_signing_key
from dci1v4.errors import IntegrityError

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import (analysis, freeze, generation, membership,
                               registration, report, topup)
from dci1v8dev.run.context import REPO_ROOT

RUNNERS: dict[str, Callable[..., Any]] = {
    L.STAGE_REGISTERED: registration.run_registration,
    L.STAGE_TOPUP: topup.run_topup,
    L.STAGE_MEMBERSHIP: membership.run_membership,
    L.STAGE_FROZEN: freeze.run_freeze,
    L.STAGE_GENERATION: generation.run_generation,
    L.STAGE_ANALYSIS: analysis.run_analysis,
    L.STAGE_REPORT: report.run_report,
}
assert set(RUNNERS) == set(L.STAGE_SEQUENCE)


def _tree(args: argparse.Namespace) -> L.ConfirmTree:
    ctx = L.confirm_context(Path(args.root).resolve(), synthetic=args.synthetic,
                            repo_root=args.repo_root)
    return L.confirm_tree(ctx, args.model)


def _accepts(stage: str, parameter: str) -> bool:
    return parameter in inspect.signature(RUNNERS[stage]).parameters


def generating_stages() -> tuple[str, ...]:
    return tuple(s for s in L.STAGE_SEQUENCE if _accepts(s, "device"))


assert set(generating_stages()) == set(L.GENERATION_STAGES)


def status(args: argparse.Namespace) -> dict[str, Any]:
    tree = _tree(args)
    reached = L.stage_reached(tree)
    nxt = (L.STAGE_SEQUENCE[L.STAGE_SEQUENCE.index(reached) + 1]
           if reached and reached != L.STAGE_SEQUENCE[-1]
           else L.STAGE_SEQUENCE[0] if reached is None else None)
    return {"model_key": args.model, "study_id": tree.context.study_id,
            "namespace": tree.context.namespace, "stage_reached": reached,
            "next_stage": nxt, "terminal_status": L.terminal_status(tree)}


def run(args: argparse.Namespace) -> dict[str, Any]:
    tree = _tree(args)
    key = tree.context.signing_key_path
    if not key.exists():
        if tree.registration_manifest.exists():
            raise IntegrityError("signing key missing and a manifest exists")
        create_signing_key(key)
    runner = RUNNERS[args.stage]
    kw: dict[str, Any] = {}
    if _accepts(args.stage, "repo_root"):
        kw["repo_root"] = Path(args.repo_root) if args.repo_root else REPO_ROOT
    if _accepts(args.stage, "pilot_roots"):
        kw["pilot_roots"] = dict(p.split("=", 1) for p in (args.pilot_root or []))
    if args.device is not None:
        if not _accepts(args.stage, "device"):
            raise ValueError(f"--device passed to {args.stage}")
        kw["device"] = args.device
    out = runner(tree, producing_commit=args.commit,
                 environment_digest=args.environment or "", **kw)
    return {"stage": out.stage, "outcome": out.outcome,
            "record": str(out.record_path)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dci1v8dev.confirm", description=__doc__)
    parser.add_argument("--repo-root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("status", status), ("run", run)):
        p = sub.add_parser(name)
        p.add_argument("--model", required=True)
        p.add_argument("--root", required=True)
        p.add_argument("--synthetic", action="store_true")
        if name == "run":
            p.add_argument("--stage", required=True, choices=list(L.STAGE_SEQUENCE))
            p.add_argument("--pilot-root", action="append", default=None,
                           help="MODEL=DIR, repeatable")
            p.add_argument("--commit", default=None)
            p.add_argument("--environment", default=None)
            p.add_argument("--device", type=int, default=None)
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except Exception as error:                               # noqa: BLE001
        print(json.dumps({"error": type(error).__name__,
                          "message": str(error)}, indent=2))
        return 1
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
