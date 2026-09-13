"""Stage 1, `QUALIFIED`: §18's non-scientific preconditions (§19).

Qualification reads **no behavioural rate**. It asks whether the apparatus is
in a state in which a run can be attributed to something: a clean tree, a
commit that contains the code that ran, resolved model revisions, a dependency
manifest, a schema-valid prompt plan, the §7.5 suites, the class labelling, a
reachable durable store, and hashable environment and commit.

Every check reports its own verdict. A failure returns `QUALIFICATION_FAILURE`
with the complete list rather than the first entry, because "the study is not
qualified" is not useful and "the worktree is dirty, and here is everything
else that is fine" is.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from dci1v4.engine import gitinfo
from dci1v4.errors import TerminalStatus

from dci1v4r3.design.prompts import assert_stem_present, render
from dci1v4r3.engine.context import StudyContext
from dci1v4r3.protocol import constants as C
from dci1v4r3.protocol.wordings import wording
from dci1v4r3.topics import split_topics
from dci1v4r3.verifiers import verifier_source_hash
from dci1v4r3.verifiers.constraints import (
    FAMILIES, TARGET_GRID, declared_range, family_class,
    focal_severities,
)
from dci1v4r3.verifiers.witnesses import run_witness_suite
from dci1v4r3.verifiers.wording_suite import run_wording_suite

__all__ = ["CHECKS", "run_checks", "qualification_payload"]

CHECKS = ("clean_worktree", "tracked_implementation", "resolved_revisions",
          "dependency_manifest", "prompt_plan_schema", "wording_suite",
          "witness_suite", "class_labelling", "durable_store_reachable",
          "environment_hashable", "commit_hashable")


def _check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"check": name, "passed": bool(ok), "detail": detail}


def run_checks(context: StudyContext) -> list[dict[str, Any]]:
    repo = Path(context.repo_root)
    results: list[dict[str, Any]] = []

    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                           capture_output=True, text=True).stdout.strip()
    results.append(_check(
        "clean_worktree", not dirty,
        {"changed_paths": len(dirty.splitlines()),
         "why_it_matters": "a run whose producing commit does not contain the "
                           "code that produced it has no provenance"}))

    try:
        commit = gitinfo.head_commit(repo)
    except Exception as error:                              # pragma: no cover
        commit = None
        results.append(_check("commit_hashable", False, str(error)))
    else:
        results.append(_check("commit_hashable", True, commit))

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "dci1/src/dci1v4r3"], cwd=repo,
        capture_output=True, text=True)
    results.append(_check(
        "tracked_implementation", tracked.returncode == 0,
        "dci1/src/dci1v4r3 is not tracked" if tracked.returncode
        else "tracked"))

    from dci1v4.models.registry import MODELS
    resolved = {m.model_key: len(m.revision) == 40 for m in MODELS}
    results.append(_check("resolved_revisions", all(resolved.values()),
                          resolved))

    lock = repo / "dci1" / "uv.lock"
    results.append(_check("dependency_manifest",
                          lock.exists() and lock.stat().st_size > 0,
                          str(lock.relative_to(repo))))

    topic = split_topics()["prescreen"][0]
    prompts = []
    for lines in ([], [wording("A", 0, 4)],
                  [wording("A", 0, 4), wording("B", 0, 9)]):
        prompt = render(topic["question"], lines)
        assert_stem_present(prompt)
        prompts.append(prompt)
    results.append(_check("prompt_plan_schema",
                          all(p.endswith("Answer:") for p in prompts),
                          {"loads": [0, 1, 2],
                           "stem": C.STEM_SENTENCE}))

    wordings = run_wording_suite()
    results.append(_check("wording_suite", wordings["passed"],
                          {"instruments": wordings["instruments"],
                           "verdicts_checked": wordings["verdicts_checked"]}))

    witnesses = run_witness_suite()
    results.append(_check("witness_suite", witnesses["passed"],
                          {"pairs": witnesses["pairs"]}))

    labelling = {kind: family_class(kind) == FAMILIES[kind].constraint_class
                 for kind in FAMILIES}
    results.append(_check("class_labelling", all(labelling.values()),
                          {"families": len(labelling)}))

    durable = Path(context.durable_root)
    reachable = durable.exists() or durable.parent.exists()
    results.append(_check("durable_store_reachable", reachable, str(durable)))

    from dci1v4.engine.environment import interpreter_identity
    identity = interpreter_identity()
    results.append(_check("environment_hashable", bool(identity), identity))
    return results


def qualification_payload(context: StudyContext, *, producing_commit: str
                          ) -> dict[str, Any]:
    """§18 stage 1. Fails closed with the whole list of reasons."""
    results = run_checks(context)
    failed = [r for r in results if not r["passed"]]
    population = (len(TARGET_GRID) + len(focal_severities(extended=True))
                  + sum(len(declared_range(k)) for k in FAMILIES))
    payload = {
        "stage": C.STAGE_QUALIFIED,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_QUALIFIED],
        "producing_commit": producing_commit,
        "canonical_verifier_hash": verifier_source_hash(),
        "instrument_population": population,
        "checks": results,
        "reads_no_behavioural_rate": True,
    }
    if failed:
        raise TerminalStatus("QUALIFICATION_FAILURE", {
            **payload, "outcome": "TERMINAL",
            "status": "QUALIFICATION_FAILURE",
            "failed": [r["check"] for r in failed],
            "observed": failed,
            "terminal_sentence": C.TERMINAL_SENTENCE})
    return {**payload, "outcome": "PASS"}
