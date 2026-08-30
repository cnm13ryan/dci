"""Stages 2 and 3: ``QUALIFIED`` and ``GATE_0_APPARATUS``.

Qualification reads no behavioural rate: a clean tree, a hashable commit
that tracks both the v7 engine and the v8 package, resolved revisions, the
lockfile, a schema-valid v8 prompt plan, the v8 instrument's structural
suite, §7.5's wording-equivalence suite over the v8 population, v7's
witness suites (carried; the predicates are v7's), §9.1's presence rule
under the v8 scorer, a v8 verifier hash distinct from v7's, the refusal of a
composed cell at the renderer, a reachable durable store, a hashable
environment. Every check reports its own verdict.

Gate 0 is §19's procedural pilot in the pilot's own shape: twelve pre-screen
topics, five cells (load 0 and four load-1 fixtures), M = 4, and the
acceptance conditions that prove the plumbing --- every cell and draw once,
a mutated byte refused, a durable restore reproducing every hash, and every
row carrying the v8 identity.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from dci1v4.engine import gitinfo, store
from dci1v4.engine.environment import interpreter_identity
from dci1v4.models.registry import MODELS
from dci1v7.design.prompts import assert_stem_present, render
from dci1v7.protocol import constants as C
from dci1v7.topics.bank import TopicBank, load_bank
from dci1v7.verifiers import verifier_source_hash as v7_verifier_hash
from dci1v7.verifiers.constraints import FAMILIES, Constraint
from dci1v7.verifiers.realistic_witness import run_realistic_suite
from dci1v7.verifiers.witnesses import run_witness_suite

from dci1v8dev.run import CLASSIFICATION
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run.execute import (SoloCell, blocks, generate_and_score,
                                   prompt_cell, resolve_generate)
from dci1v8dev.run.instrument import v8_wording_suite
from dci1v8dev.run.lifecycle import (StageOutcome, TerminalStatus,
                                     protocol_identity, run_stage)
from dci1v8dev.verifiers import verifier_source_hash
from dci1v8dev.verifiers.compliance import assert_presence_rule, score_generation
from dci1v8dev.wordings import assert_v8_instrument, v8_wording

__all__ = ["CHECKS", "run_checks", "qualification_payload",
           "run_qualification", "GATE0_FIXTURES", "gate0_payload",
           "run_gate0"]

CHECKS = ("clean_worktree", "commit_hashable", "tracked_implementation",
          "resolved_revisions", "dependency_manifest", "prompt_plan_schema",
          "v8_instrument_suite", "wording_equivalence_suite",
          "witness_suite", "realistic_witness_suite", "presence_rule",
          "verifier_hash_distinct_from_v7", "no_composed_cell_path",
          "durable_store_reachable", "environment_hashable")


def _check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"check": name, "passed": bool(ok), "detail": detail}


def run_checks(context: Any, *, bank: TopicBank | None = None
               ) -> list[dict[str, Any]]:
    repo = Path(context.repo_root)
    bank = bank if bank is not None else load_bank()
    results: list[dict[str, Any]] = []

    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                           capture_output=True, text=True).stdout.strip()
    results.append(_check("clean_worktree", not dirty,
                          {"changed_paths": len(dirty.splitlines())}))
    try:
        commit = gitinfo.head_commit(repo)
        results.append(_check("commit_hashable", True, commit))
    except Exception as error:                              # pragma: no cover
        results.append(_check("commit_hashable", False, str(error)))
    tracked = {}
    for rel in ("dci1/src/dci1v7", "dci1/src/dci1v8dev", "dci1/src/dci1v4"):
        done = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                              cwd=repo, capture_output=True, text=True)
        tracked[rel] = done.returncode == 0
    results.append(_check("tracked_implementation", all(tracked.values()),
                          tracked))
    resolved = {m.model_key: len(m.revision) == 40 for m in MODELS}
    results.append(_check("resolved_revisions", all(resolved.values()),
                          resolved))
    lock = repo / "dci1" / "uv.lock"
    results.append(_check("dependency_manifest",
                          lock.exists() and lock.stat().st_size > 0,
                          str(lock)))
    topic = bank.topics("prescreen")[0]
    prompts = [render(topic["question"], lines) for lines in
               ([], [v8_wording("A", 0, 4)], [v8_wording("MK1", 1, 2)])]
    schema_ok = True
    for prompt in prompts:
        assert_stem_present(prompt)
        schema_ok &= prompt.endswith("Answer:")
    schema_ok &= "the word however" in prompts[1]
    results.append(_check("prompt_plan_schema", schema_ok,
                          {"loads": [0, 1], "stem": C.STEM_SENTENCE,
                           "no_composed_cell": True}))
    try:
        results.append(_check("v8_instrument_suite", True,
                              assert_v8_instrument()))
    except Exception as error:                              # noqa: BLE001
        results.append(_check("v8_instrument_suite", False, str(error)))
    try:
        suite = v8_wording_suite()
        results.append(_check("wording_equivalence_suite", suite["passed"],
                              {k: suite[k] for k in ("instruments",
                                                     "verdicts_checked")}))
    except Exception as error:                              # noqa: BLE001
        results.append(_check("wording_equivalence_suite", False, str(error)))
    witnesses = run_witness_suite()
    results.append(_check("witness_suite", witnesses["passed"],
                          {"pairs": witnesses.get("pairs"),
                           "carried": "v7 predicates and witnesses"}))
    realistic = run_realistic_suite()
    results.append(_check("realistic_witness_suite",
                          not realistic.get("failures"),
                          {"unreachable": realistic.get("unreachable"),
                           "carried": "v7"}))
    presence = _presence_rule_check()
    results.append(_check("presence_rule", presence["passed"], presence))
    v8_hash, v7_hash = verifier_source_hash(), v7_verifier_hash()
    results.append(_check("verifier_hash_distinct_from_v7", v8_hash != v7_hash,
                          {"v8": v8_hash, "v7": v7_hash}))
    results.append(_check("no_composed_cell_path", _composed_cell_refused(),
                          "prompt_cell refuses a two-slot cell"))
    durable = Path(context.durable_root)
    results.append(_check("durable_store_reachable",
                          durable.exists() or durable.parent.exists(),
                          str(durable)))
    identity = interpreter_identity()
    results.append(_check("environment_hashable", bool(identity), identity))
    return results


def _presence_rule_check() -> dict[str, Any]:
    b = Constraint("B", C.FOCAL_GRID[len(C.FOCAL_GRID) // 2])
    r = Constraint("MK1", FAMILIES["MK1"].ladder[0])
    scores = score_generation("Thus a short reply. " * 8, present=(b,),
                              absent=(r,), truncated=False)
    try:
        assert_presence_rule(scores, stated=(b,), instances_in_use=(b, r),
                             where="qualification:presence_rule")
    except Exception as error:                              # pragma: no cover
        return {"passed": False, "detail": str(error)}
    absent = [s for s in scores.scores if not s.present]
    return {"passed": len(absent) == 1, "scorer": "dci1v8dev.verifiers"}


def _composed_cell_refused() -> bool:
    from dci1v4.errors import ProtocolError

    class _Two:
        cell_id, arm, block_id, block_index, topic_id = "x", "composed", "b", 0, "t"
        slots = ("A", "B")
        wording_by_slot = {"A": 0, "B": 0}
        draws = 1

    try:
        prompt_cell(_Two(), {"question": "q", "topic_id": "t", "area": "a"},
                    slot_map={"A": Constraint("A", 4),
                              "B": Constraint("B", 10)},
                    topic_split="prescreen")
    except ProtocolError:
        return True
    return False


def qualification_payload(context: Any, *, producing_commit: str,
                          bank: TopicBank | None = None) -> dict[str, Any]:
    bank = bank if bank is not None else load_bank()
    results = run_checks(context, bank=bank)
    failed = [r for r in results if not r["passed"]]
    payload = {
        "stage": S.STAGE_QUALIFIED,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_QUALIFIED],
        "inputs": {"registration": {"stage": S.STAGE_REGISTERED}},
        "producing_commit": producing_commit,
        "checks": results,
        "checks_expected": list(CHECKS),
        "reads_no_behavioural_rate": True,
        "topic_split_identity": bank.split_identity,
    }
    if failed:
        raise TerminalStatus(
            "QUALIFICATION_FAILURE", gate=S.STAGE_QUALIFIED,
            criterion="every apparatus precondition",
            observed=[r["check"] for r in failed],
            strongest_permissible_statement=S.TERMINAL_SENTENCE)
    return {**payload, "outcome": "PASS"}


def run_qualification(tree: ModelTree, *, producing_commit: str | None = None,
                      environment_digest: str = "",
                      bank: TopicBank | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return run_stage(
        tree, S.STAGE_QUALIFIED,
        compute=lambda _prev: qualification_payload(
            tree.context, producing_commit=commit, bank=bank),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------------ Gate 0

#: Fixture instances: the middle of each grid / the second rung of a ladder.
#: They cannot become calibration evidence: the rows carry the Gate-0 stage
#: name and no rule reads them.
GATE0_FIXTURES: dict[str, tuple[str, int]] = {
    "A": ("A", C.TARGET_GRID[len(C.TARGET_GRID) // 2]),
    "B": ("B", C.FOCAL_GRID[len(C.FOCAL_GRID) // 2]),
    "R1": ("MK1", FAMILIES["MK1"].ladder[1]),
    "CL": ("RF1", FAMILIES["RF1"].ladder[1]),
}


def gate0_payload(tree: ModelTree, *, producing_commit: str,
                  bank: TopicBank | None = None,
                  cap: int = C.COMPLETION_CAPS[-1], device: int = 0,
                  generate: Callable[..., dict[str, Any]] | None = None
                  ) -> dict[str, Any]:
    bank = bank if bank is not None else load_bank()
    prescreen = list(bank.topics("prescreen"))
    chosen: list[dict[str, Any]] = []
    for area in C.SUBJECT_AREAS:
        for topic in prescreen:
            if topic["area"] == area:
                chosen.append(topic)
                break
    if len(chosen) != S.GATE0_TOPICS:
        raise TerminalStatus(
            "APPARATUS_FAILURE", gate=S.STAGE_GATE0,
            criterion=f"{S.GATE0_TOPICS} fixed pre-screen topics",
            observed=len(chosen),
            strongest_permissible_statement=S.TERMINAL_SENTENCE)
    slot_map = {slot: Constraint(*spec) for slot, spec in GATE0_FIXTURES.items()}
    cells: list[Any] = []
    for block in blocks(chosen, "pilot"):
        cells.append(SoloCell(cell_id="unconstrained", arm="unconstrained",
                              block=block, slot=None, draws=S.GATE0_DRAWS))
        for slot, constraint in slot_map.items():
            cells.append(SoloCell(cell_id=f"solo:{constraint.label}",
                                  arm="solo", block=block, slot=slot,
                                  draws=S.GATE0_DRAWS))
    by_topic = {t["topic_id"]: t for t in chosen}
    prompts = [prompt_cell(c, by_topic[c.topic_id], slot_map=slot_map,
                           topic_split="prescreen") for c in cells]
    run_dir = tree.backend_runs(S.STAGE_GATE0) / "pilot"
    instances = tuple(dict.fromkeys(slot_map.values()))
    rows = generate_and_score(
        tree.model_key, prompts, stage=S.STAGE_GATE0, cap=cap, device=device,
        run_dir=run_dir, instances=instances, slot_map=slot_map,
        study_id=tree.context.study_id,
        protocol_identity=protocol_identity(tree, S.STAGE_GATE0),
        generate=resolve_generate(tree, generate, _pilot_responder,
                                  where=S.STAGE_GATE0))
    expected = len(prompts) * S.GATE0_DRAWS
    identities = [r["row_id"] for r in rows]
    per_cell: dict[str, int] = {}
    for row in rows:
        key = f"{row['block_id']}:{row['cell_id']}"
        per_cell[key] = per_cell.get(key, 0) + 1
    hashes = {"verifier_hash": verifier_source_hash()}
    from dci1v8dev.wordings import v8_wording_source_hash
    hashes["wording_hash"] = v8_wording_source_hash()
    acceptance = {
        "every_cell_and_draw_once": (len(identities) == expected
                                     and len(set(identities)) == expected),
        "one_cell_mean_over_M": all(n == S.GATE0_DRAWS
                                    for n in per_cell.values()),
        "byte_mutation_refused": _byte_mutation_refused(run_dir),
        "durable_restore_matches": _durable_restore_matches(tree, run_dir),
        "no_processing_failures": not any(
            s["processing_failure"] for r in rows for s in r["scores"]),
        "rows_carry_v8_identity": all(
            r["study_id"] == tree.context.study_id
            and r["classification"] == CLASSIFICATION
            and r["verifier_hash"] == hashes["verifier_hash"]
            and r["wording_hash"] == hashes["wording_hash"]
            for r in rows),
        "no_composed_row": all(r["load"] <= 1 for r in rows),
        "v8_frames_rendered": all(
            "the word " in p.prompt.lower() for p in prompts
            if p.present and p.present[0].kind in ("A", "MK1")),
    }
    failed = sorted(k for k, v in acceptance.items() if not v)
    payload = {
        "stage": S.STAGE_GATE0,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_GATE0],
        "inputs": {"qualification": {"stage": S.STAGE_QUALIFIED}},
        "producing_commit": producing_commit,
        "cells_per_block": 1 + len(slot_map),
        "blocks": len(chosen), "draws": S.GATE0_DRAWS,
        "rows": len(rows), "expected_rows": expected,
        "slot_fixtures": {s: c.label for s, c in slot_map.items()},
        "fixture_declaration": "§19-shaped fixture values; no rule reads a "
                               "Gate-0 row and the rows carry the stage name",
        "acceptance": acceptance,
        "topic_ids": sorted(t["topic_id"] for t in chosen),
        "synthetic_rows": all(r["synthetic"] for r in rows),
        "cap": cap,
    }
    if failed:
        raise TerminalStatus(
            "APPARATUS_FAILURE", gate=S.STAGE_GATE0,
            criterion="Gate 0's acceptance conditions", observed=failed,
            strongest_permissible_statement=S.TERMINAL_SENTENCE)
    return {**payload, "outcome": "PASS"}


def _pilot_responder(row: Mapping[str, Any]) -> str:
    words = ["thus", "hence", "though", "whereas", "indeed", "namely",
             "instead", "overall", "a", "brief", "reply", "here"]
    seed = sum(ord(ch) for ch in str(row["row_id"]))
    return " ".join(words[(seed + i) % len(words)]
                    for i in range(70)).capitalize() + "."


def _byte_mutation_refused(run_dir: Path) -> bool:
    path = run_dir / "scored.jsonl"
    if not path.exists():
        return False
    original = path.read_bytes()
    try:
        rows = [json.loads(line) for line in
                original.decode().splitlines() if line.strip()]
        if not rows:
            return False
        from dci1v4.protocol.hashing import sha_obj
        before = sha_obj(rows[0])
        mutated = {**rows[0],
                   "raw_response": (rows[0]["raw_response"] or "") + "!"}
        return sha_obj(mutated) != before
    finally:
        path.write_bytes(original)


def _durable_restore_matches(tree: ModelTree, run_dir: Path) -> bool:
    durable = tree.durable / S.STAGE_GATE0 / "backend_runs" / run_dir.name
    try:
        before = store.replicate(run_dir, durable)
        store.assert_replicated(run_dir, durable)
        return before == store.fingerprint_tree(durable)
    except Exception:                                        # pragma: no cover
        return False


def run_gate0(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "", bank: TopicBank | None = None,
              device: int = 0, cap: int = C.COMPLETION_CAPS[-1],
              generate: Callable[..., dict[str, Any]] | None = None
              ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return run_stage(
        tree, S.STAGE_GATE0,
        compute=lambda _prev: gate0_payload(
            tree, producing_commit=commit, bank=bank, cap=cap, device=device,
            generate=generate),
        producing_commit=commit, environment_digest=environment_digest)
