"""The v8 pilot command line: one stage, one command, in order.

    python -m dci1v8dev.run.cli status --model <key> --root <dir> [--namespace pilot|synthetic]
    python -m dci1v8dev.run.cli plan   --root <dir> [--namespace ...]
    python -m dci1v8dev.run.cli run    --stage <STAGE> --model <key> --root <dir> [--device N]
    python -m dci1v8dev.run.cli audit  [--matrix]

``--root`` is always required: there is no registered v8 root. ``--namespace``
defaults to ``pilot`` (the pinned backend and the real model; a generation
callable is refused); ``synthetic`` admits the stand-in generator and the
scale knobs the lifecycle test uses. ``--device`` is placement only and is
refused on a stage that generates nothing. ``run`` passes no generation
callable; ``execute.resolve_generate`` turns its absence into the pinned
backend in the pilot namespace.
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

from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import (REPO_ROOT, ModelTree, model_tree,
                                   pilot_context, synthetic_context)
from dci1v8dev.run import (calibration, instrument, qualification, references,
                           regime, registration, report, rescreen)
from dci1v8dev.run.contracts import audit_contracts, matrix_markdown

__all__ = ["RUNNERS", "ROOTED_NAMESPACES", "stages_accepting",
           "generating_stages", "ensure_signing_key", "main"]

RUNNERS: dict[str, Callable[..., Any]] = {
    S.STAGE_REGISTERED: registration.run_registration,
    S.STAGE_QUALIFIED: qualification.run_qualification,
    S.STAGE_GATE0: qualification.run_gate0,
    S.STAGE_REGIME: regime.run_regime_screen,
    S.STAGE_SECOND_PASS: rescreen.run_second_pass,
    S.STAGE_GATE1: instrument.run_gate1,
    S.STAGE_GATE2: calibration.run_gate2,
    S.STAGE_GATE3: references.run_gate3,
    S.STAGE_REPORT: report.run_report,
}


def assert_every_stage_has_a_runner() -> None:
    missing = [s for s in S.STAGE_SEQUENCE if s not in RUNNERS]
    extra = [s for s in RUNNERS if s not in S.STAGE_SEQUENCE]
    if missing or extra:
        raise AssertionError(f"stages without a runner: {missing}; runners "
                             f"without a stage: {extra}")


assert_every_stage_has_a_runner()

ROOTED_NAMESPACES = {"pilot": pilot_context, "synthetic": synthetic_context}


def _context(root: str | None, namespace: str | None):
    if root is None:
        raise ValueError("--root is required: the v8 pilot has no registered "
                         "root and never writes into one")
    return ROOTED_NAMESPACES[namespace or "pilot"](Path(root))


def _tree(model_key: str, root: str | None, namespace: str | None) -> ModelTree:
    return model_tree(_context(root, namespace), model_key)


def stages_accepting(parameter: str) -> tuple[str, ...]:
    return tuple(stage for stage in S.STAGE_SEQUENCE
                 if parameter in inspect.signature(RUNNERS[stage]).parameters)


def generating_stages() -> tuple[str, ...]:
    return stages_accepting("device")


assert set(generating_stages()) == set(S.GENERATION_STAGES), (
    generating_stages(), S.GENERATION_STAGES)


def repo_root_of(args: argparse.Namespace) -> Path:
    return Path(args.repo_root) if args.repo_root else REPO_ROOT


def ensure_signing_key(tree: ModelTree) -> dict[str, Any]:
    path = tree.context.signing_key_path
    if path.exists():
        return {"signing_key": "present"}
    if tree.context.registration_manifest.exists():
        raise IntegrityError(
            f"the signing key is missing at {path} and the pilot manifest "
            "exists: a lost key, not an uninitialised one; refusing to mint")
    path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(path)
    return {"signing_key": "created", "path": str(path)}


def status(args: argparse.Namespace) -> dict[str, Any]:
    tree = _tree(args.model, args.root, args.namespace)
    reached = transitions.stage_reached(tree)
    return {
        "model_key": args.model,
        "study_id": tree.context.study_id,
        "namespace": tree.context.namespace,
        "stage_reached": reached,
        "next_stage": (S.STAGE_SEQUENCE[S.STAGE_SEQUENCE.index(reached) + 1]
                       if reached and reached != S.STAGE_SEQUENCE[-1]
                       else S.STAGE_SEQUENCE[0] if reached is None else None),
        "terminal_status": transitions.terminal_status(tree),
        "transitions_logged": len(transitions.transition_rows(tree)),
    }


def plan(args: argparse.Namespace) -> dict[str, Any]:
    context = _context(args.root, args.namespace)
    out = registration.plan_registration(context, repo_root=repo_root_of(args))
    out.pop("manifest", None)
    return out


def audit(args: argparse.Namespace) -> Any:
    if args.matrix:
        return matrix_markdown()
    return audit_contracts()


FORWARDED = {"device": "device"}


def run(args: argparse.Namespace) -> dict[str, Any]:
    tree = _tree(args.model, args.root, args.namespace)
    key = ensure_signing_key(tree)
    runner = RUNNERS[args.stage]
    forwarded: dict[str, Any] = {}
    if args.stage in stages_accepting("repo_root"):
        forwarded["repo_root"] = repo_root_of(args)
    for flag, parameter in FORWARDED.items():
        value = getattr(args, flag)
        if value is None:
            continue
        accepted = stages_accepting(parameter)
        if args.stage not in accepted:
            raise ValueError(
                f"--{flag} was passed to {args.stage}, whose runner does not "
                f"take {parameter!r}; stages that take it: "
                f"{', '.join(accepted) or 'none'}")
        forwarded[parameter] = value
    outcome = runner(tree, producing_commit=args.commit,
                     environment_digest=args.environment or "", **forwarded)
    return {"stage": outcome.stage, "outcome": outcome.outcome,
            "record": str(outcome.record_path), **key}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dci1v8dev.run", description=__doc__)
    parser.add_argument("--repo-root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    def _rooted(p: argparse.ArgumentParser) -> None:
        p.add_argument("--root", required=True)
        p.add_argument("--namespace", default=None,
                       choices=list(ROOTED_NAMESPACES))

    p_status = sub.add_parser("status")
    p_status.add_argument("--model", required=True)
    _rooted(p_status)
    p_status.set_defaults(func=status)

    p_plan = sub.add_parser("plan")
    _rooted(p_plan)
    p_plan.set_defaults(func=plan)

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--matrix", action="store_true")
    p_audit.set_defaults(func=audit)

    p_run = sub.add_parser("run")
    p_run.add_argument("--stage", required=True, choices=list(S.STAGE_SEQUENCE))
    p_run.add_argument("--model", required=True)
    _rooted(p_run)
    p_run.add_argument("--commit", default=None)
    p_run.add_argument("--environment", default=None)
    p_run.add_argument("--device", type=int, default=None)
    p_run.set_defaults(func=run)

    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except Exception as error:                               # noqa: BLE001
        print(json.dumps({"error": type(error).__name__,
                          "message": str(error)}, indent=2))
        return 1
    print(result if isinstance(result, str)
          else json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
