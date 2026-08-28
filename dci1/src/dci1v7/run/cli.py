"""The v5 command line: one stage, one command, in registered order.

    python -m dci1v7.run.cli status  --model <key>
    python -m dci1v7.run.cli plan
    python -m dci1v7.run.cli run     --stage <STAGE> --model <key> [--device N]
    python -m dci1v7.run.cli audit   [--matrix]
    python -m dci1v7.run.cli retire-apparatus-fault --model <key> ...

**Every command refuses before it does anything.** ``run`` goes through
``run/lifecycle.run_stage``, which asserts the transition --- order, once,
predecessor passed, no open decision --- and logs the refusal.

``run`` passes **no** generation callable, and that is deliberate: in the
registered namespace ``execute.resolve_generate`` turns its absence into the
pinned backend and refuses a substitute outright. Four runners used to read
``generate or fake_backend(...)`` instead, so this command would have signed
fabricated text into the registered evidence tree.

``--supersedes`` carries §32's chain link into the replacement manifest. ``build_manifest`` folds it in before the hash, so without it a re-registration is signed unlinked and the chain stops being readable from the payload; ``manifest.assert_links_supersession`` now refuses that outright.

``retire-apparatus-fault`` is amendment A15's recovery path and the narrowest
command here: it retires a ``PROTOCOL_REGISTERED`` **readiness** verdict that
an apparatus fault wrote as a §28.3 terminal report, by the hash of the exact
record, and refuses for any other gate, any §28 terminal status, once a
manifest exists, and once any row has been generated. It deletes nothing.

``--device`` selects which card a generating stage runs on. It is placement
and nothing else: the runners already threaded ``device`` down to
``backend_env``, which clears inherited ``ROCR_``/``HIP_``/``CUDA_``
visibility variables and sets ``HIP_VISIBLE_DEVICES`` itself --- so a shell
export cannot move a lane, and before this flag existed the documented entry
point could only ever reach card 0. It changes no measured quantity: the
prompts, decoding policy, cap, seeds and verifiers are all read from the
signed records. On a stage that generates nothing it is **refused** rather
than ignored, so a mistyped lane cannot look like it was honoured. Two TP=1
lanes are how this host uses both cards; the backend's per-device flock keeps
them independent.

``plan`` and ``status`` and ``audit`` write nothing and are safe now: they are
how a researcher sees what adoption would bind, how far a replication has got,
and whether every artifact field has a producer.
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from dci1v4.engine import gitinfo
from dci1v4.engine.signing import create_signing_key
from dci1v4.errors import IntegrityError

from dci1v7 import PREREGISTRATION
from dci1v7.engine import transitions
from dci1v7.engine.context import (REPO_ROOT, registered_context,
                                   synthetic_context)
from dci1v7.engine.paths import ModelTree, model_tree
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions, open_items
from dci1v7.run import (analysis_run, confirmatory_run, freeze_run, gates_run,
                        prefreeze_run, qualification_run, regime_run,
                        registration_run)
from dci1v7.run.contracts import audit_contracts, matrix_markdown

__all__ = ["ensure_signing_key", "repo_root_of", "retire", "RUNNERS", "main"]

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
    C.STAGE_GATE2_75: gates_run.run_gate2_75,
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


def repo_root_of(args: argparse.Namespace) -> Path:
    """The repository a stage binds: ``--repo-root`` if given, else the one
    this package lives in. Never the process's working directory."""
    return Path(args.repo_root) if args.repo_root else REPO_ROOT


def plan(args: argparse.Namespace) -> dict[str, Any]:
    return registration_run.plan_registration(repo_root=repo_root_of(args))


def audit(args: argparse.Namespace) -> Any:
    if args.matrix:
        return matrix_markdown()
    return audit_contracts()


def stages_accepting(parameter: str) -> tuple[str, ...]:
    """The stages whose runner takes ``parameter``, in registered order.

    Derived from the signatures rather than listed, so a runner that gains or
    loses one cannot leave a stale list behind.
    """
    return tuple(
        stage for stage in C.STAGE_SEQUENCE
        if parameter in inspect.signature(RUNNERS[stage]).parameters)


def generating_stages() -> tuple[str, ...]:
    """The stages with a generative seam: the ones that can be given a card."""
    return stages_accepting("device")


#: CLI flag -> the runner keyword it forwards. Each is refused on a stage
#: whose runner does not take it, rather than dropped: a flag that looks
#: honoured and did nothing is worse than one that failed.
FORWARDED = {"device": "device", "supersedes": "supersedes"}

#: Forwarded to every runner that takes it, and **not** refused on the rest.
#: Unlike the flags above it is not a per-stage instruction: it names the
#: repository whose governed documents and head commit a stage binds, and the
#: stages that do not read one are simply not affected.
#:
#: It is forwarded because it was not. ``run_registration`` takes
#: ``repo_root`` and defaults it to ``"."``, so `run --stage
#: PROTOCOL_REGISTERED` bound whatever directory the process happened to be
#: in --- from ``dci1/`` the preregistration is not at
#: ``user-notes/DCI1_preregistration_v7.md`` and stage 1 returned
#: REGISTRATION_INCOMPLETE with a DRAFT_DOCUMENT blocker naming a file that
#: exists one level up. A registration whose content depends on the caller's
#: working directory is not a registration, so the default is now the
#: repository this package lives in and never the cwd. Which stages receive
#: it is derived from their signatures by ``stages_accepting``.


def ensure_signing_key(tree: ModelTree) -> dict[str, Any]:
    """Create the study's signing key, once, before the first stage.

    Every stage record is signed at write and verified at read, so without a
    key the documented entry point cannot run **any** stage --- including
    stage 1. v4's runner created it explicitly and v6's had no equivalent, so
    `run --stage PROTOCOL_REGISTERED` failed on a missing key: the same shape
    as V5-E2, a registered study its own CLI could not execute.

    **It is created only when the study has no signed registration.** After
    a manifest exists, a missing key is a *lost* key, and minting a new one
    would leave every existing record unverifiable while looking repaired.
    That case refuses, and says which it is.

    Creating a key changes no measured quantity: it authenticates records, it
    does not produce them.
    """
    path = tree.context.signing_key_path
    if path.exists():
        return {"signing_key": "present"}
    if tree.context.registration_manifest.exists():
        raise IntegrityError(
            f"the signing key is missing at {path} and "
            f"{tree.context.registration_manifest} exists. A key that "
            "disappears after a study is registered is a LOST key, not an "
            "uninitialised one; a new key would fail to verify every record "
            "already signed, so this refuses rather than minting one")
    path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(path)
    return {"signing_key": "created", "path": str(path)}


def run(args: argparse.Namespace) -> dict[str, Any]:
    tree = _tree(args.model, args.root)
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
                f"take {parameter!r}. Accepting it silently would make a "
                f"mistyped invocation look honoured. Stages that take it: "
                f"{', '.join(accepted) or 'none'}")
        forwarded[parameter] = value
    outcome = runner(tree, producing_commit=args.commit,
                     environment_digest=args.environment or "", **forwarded)
    return {"stage": outcome.stage, "outcome": outcome.outcome,
            "record": str(outcome.record_path), **key}


def retire(args: argparse.Namespace) -> dict[str, Any]:
    """A15: retire a stage-1 readiness verdict an apparatus fault wrote.

    Six preconditions refuse it and they live in
    ``registration_run.retire_apparatus_fault``, not here; this only supplies
    the hash the researcher named, the reason, the defect and the amendment,
    so a retirement cannot be performed with any of them left blank.
    """
    tree = _tree(args.model, args.root)
    ensure_signing_key(tree)
    return registration_run.retire_apparatus_fault(
        tree, record_hash=args.record_hash, reason=args.reason,
        defect=args.defect, amendment={"id": args.amendment,
                                       "document": PREREGISTRATION},
        producing_commit=args.commit or gitinfo.head_commit(
            repo_root_of(args)),
        decided_by=args.decided_by, decided_on=args.decided_on)


def amend(args: argparse.Namespace) -> dict[str, Any]:
    """v7 A4: bind a post-registration amendment as a signed chain record.

    The preconditions live in ``registration_run.amend_registration``: the
    documents on disk must differ from the chain head, the direction must be
    declared, the sections named, the §32.2 disclosure written, and no §13
    section may be named once any replication holds a Gate-2.5 record.
    """
    from dci1v4.models.registry import MODELS

    tree = _tree(args.model or MODELS[0].model_key, args.root)
    ensure_signing_key(tree)
    return registration_run.amend_registration(
        tree.context, amendment_id=args.id, reason=args.reason,
        direction=args.direction,
        sections=[s.strip() for s in args.sections.split(",")],
        declaration=args.declaration,
        model_keys=[m.model_key for m in MODELS],
        producing_commit=args.commit or gitinfo.head_commit(
            repo_root_of(args)),
        repo_root=repo_root_of(args),
        decided_by=args.decided_by, decided_on=args.decided_on)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dci1v7", description=__doc__)
    parser.add_argument("--repo-root", default=None,
                        help="the repository whose governed documents and "
                             "head commit a stage binds. Defaults to the one "
                             "this package lives in, never the cwd")
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
    p_run.add_argument("--device", type=int, default=None,
                       help="card for a generating stage; refused elsewhere")
    p_run.add_argument("--supersedes", default=None,
                       help="manifest hash this registration replaces (§32); "
                            "refused outside PROTOCOL_REGISTERED")
    p_run.set_defaults(func=run)

    p_amend = sub.add_parser(
        "amend",
        help="bind a post-registration amendment (§32, v7 A4): a signed "
             "append-only record linking the document hashes in force to "
             "the amended ones. Refuses a §13 section once any replication "
             "holds a Gate-2.5 record")
    p_amend.add_argument("--id", required=True)
    p_amend.add_argument("--reason", required=True)
    p_amend.add_argument("--direction", required=True,
                         choices=["tightening", "loosening", "neutral"])
    p_amend.add_argument("--sections", required=True,
                         help="comma-separated, each '§N...'")
    p_amend.add_argument("--declaration", required=True,
                         help="the §32.2 disclosure, in the researcher's words")
    p_amend.add_argument("--decided-by", required=True)
    p_amend.add_argument("--decided-on", required=True)
    p_amend.add_argument("--model", default=None)
    p_amend.add_argument("--root", default=None)
    p_amend.add_argument("--commit", default=None)
    p_amend.set_defaults(func=amend)

    p_retire = sub.add_parser(
        "retire-apparatus-fault",
        help="retire a PROTOCOL_REGISTERED readiness verdict written as a "
             "terminal report by an apparatus fault (A15). Refuses for any "
             "other gate, any §28 terminal status, once a manifest exists, "
             "and once any row has been generated")
    p_retire.add_argument("--model", required=True)
    p_retire.add_argument("--root", default=None)
    p_retire.add_argument("--commit", default=None)
    p_retire.add_argument("--record-hash", required=True,
                          help="sha256 of the terminal report being retired")
    p_retire.add_argument("--reason", required=True)
    p_retire.add_argument("--defect", required=True,
                          help="the apparatus defect that produced it")
    p_retire.add_argument("--amendment", required=True,
                          help="the amendment this is performed under")
    p_retire.add_argument("--decided-by", required=True)
    p_retire.add_argument("--decided-on", required=True)
    p_retire.set_defaults(func=retire)

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
