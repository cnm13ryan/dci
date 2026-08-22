"""The v5 command line: one stage, one command, in registered order.

    python -m dci1v5.run.cli status  --model <key>
    python -m dci1v5.run.cli plan
    python -m dci1v5.run.cli run     --stage <STAGE> --model <key>
    python -m dci1v5.run.cli audit   [--matrix]

**Every command refuses before it does anything.** ``run`` goes through
``run/lifecycle.run_stage``, which asserts the transition --- order, once,
predecessor passed, no open decision --- and logs the refusal. So today every
``run`` command ends the same way, with ``REGISTRATION_INCOMPLETE`` and the
list of decisions that are open, and that is the correct behaviour rather than
a limitation of the CLI.

``plan`` and ``status`` and ``audit`` write nothing and are safe now: they are
how a researcher sees what adoption would bind, how far a replication has got,
and whether every artifact field has a producer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from dci1v5.engine import transitions
from dci1v5.engine.context import registered_context, synthetic_context
from dci1v5.engine.paths import ModelTree, model_tree
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions, open_items
from dci1v5.run import (analysis_run, confirmatory_run, freeze_run, gates_run,
                        prefreeze_run, qualification_run, regime_run,
                        registration_run)
from dci1v5.run.contracts import audit_contracts, matrix_markdown

__all__ = ["RUNNERS", "main"]

#: stage -> the runner that produces its record. Every registered stage has
#: one, and ``assert_every_stage_has_a_runner`` is what stops a stage being
#: added to §18 without one.
RUNNERS: dict[str, Callable[..., Any]] = {
    C.STAGE_REGISTERED: registration_run.run_registration,
    C.STAGE_QUALIFIED: qualification_run.run_qualification,
    C.STAGE_GATE0: qualification_run.run_gate0,
    C.STAGE_REGIME: regime_run.run_regime_screen,
    C.STAGE_GATE1: regime_run.run_gate1,
    C.STAGE_GATE2: gates_run.run_gate2,
    C.STAGE_GATE2_5: gates_run.run_gate2_5,
    C.STAGE_GATE3A: gates_run.run_gate3a,
    C.STAGE_GATE3B: gates_run.run_gate3b,
    C.STAGE_GATE3C: gates_run.run_gate3c,
    C.STAGE_GATE4: gates_run.run_gate4,
    C.STAGE_PREFREEZE_AUDIT: prefreeze_run.run_prefreeze_audit_stage,
    C.STAGE_GATE5: freeze_run.run_freeze,
    C.STAGE_CONFIRMATORY: confirmatory_run.run_confirmatory,
    C.STAGE_MASKED_ANALYSIS: analysis_run.run_masked_analysis,
    C.STAGE_UNMASKING: analysis_run.run_unmasking,
    C.STAGE_UNMASKED_ANALYSIS: analysis_run.run_unmasked_analysis,
    C.STAGE_FINAL_REPORT: analysis_run.run_final_report,
}


def assert_every_stage_has_a_runner() -> None:
    """§18: a stage with no runner is a lifecycle with a hole in it."""
    missing = [s for s in C.STAGE_SEQUENCE if s not in RUNNERS]
    extra = [s for s in RUNNERS if s not in C.STAGE_SEQUENCE]
    if missing or extra:
        raise AssertionError(
            f"stages without a runner: {missing}; runners without a stage: "
            f"{extra}")


assert_every_stage_has_a_runner()


def _tree(model_key: str, root: str | None) -> ModelTree:
    context = (synthetic_context(Path(root)) if root
               else registered_context())
    return model_tree(context, model_key)


def status(args: argparse.Namespace) -> dict[str, Any]:
    tree = _tree(args.model, args.root)
    reached = transitions.stage_reached(tree)
    return {
        "model_key": args.model,
        "study_id": tree.context.study_id,
        "stage_reached": reached,
        "next_stage": (C.STAGE_SEQUENCE[C.STAGE_SEQUENCE.index(reached) + 1]
                       if reached and reached != C.STAGE_SEQUENCE[-1]
                       else C.STAGE_SEQUENCE[0] if reached is None else None),
        "terminal_status": transitions.terminal_status(tree),
        "open_decisions": list(decisions.open_decisions()),
        "blocking_specification_questions": list(open_items.blocking_items()),
        "transitions_logged": len(transitions.transition_rows(tree)),
    }


def plan(args: argparse.Namespace) -> dict[str, Any]:
    return registration_run.plan_registration(repo_root=args.repo_root)


def audit(args: argparse.Namespace) -> Any:
    if args.matrix:
        return matrix_markdown()
    return audit_contracts()


def run(args: argparse.Namespace) -> dict[str, Any]:
    tree = _tree(args.model, args.root)
    runner = RUNNERS[args.stage]
    outcome = runner(tree, producing_commit=args.commit,
                     environment_digest=args.environment or "")
    return {"stage": outcome.stage, "outcome": outcome.outcome,
            "record": str(outcome.record_path)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dci1v5", description=__doc__)
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("--model", required=True)
    p_status.add_argument("--root", default=None)
    p_status.set_defaults(func=status)

    p_plan = sub.add_parser("plan")
    p_plan.set_defaults(func=plan)

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--matrix", action="store_true")
    p_audit.set_defaults(func=audit)

    p_run = sub.add_parser("run")
    p_run.add_argument("--stage", required=True, choices=list(C.STAGE_SEQUENCE))
    p_run.add_argument("--model", required=True)
    p_run.add_argument("--root", default=None)
    p_run.add_argument("--commit", default=None)
    p_run.add_argument("--environment", default=None)
    p_run.set_defaults(func=run)

    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except Exception as error:
        print(json.dumps({"error": type(error).__name__,
                          "message": str(error)}, indent=2))
        return 1
    print(result if isinstance(result, str)
          else json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(main())
