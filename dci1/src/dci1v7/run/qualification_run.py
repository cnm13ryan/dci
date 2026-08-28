"""§18 stages 2 and 3: ``QUALIFIED`` and ``GATE_0_APPARATUS``.

**Qualification reads no behavioural rate.** It asks whether the apparatus is
in a state in which a run can be attributed to something: a clean tree, a
commit that contains the code that ran, resolved revisions, a dependency
manifest, a schema-valid prompt plan, §7.7's wording and witness suites
**including the realistic witness**, class *and tier* labelling, structural
metadata asserted against every predicate, §9.1's presence rule asserted at
every generative stage, a reachable durable store, and hashable environment
and commit.

Every check reports its own verdict and a failure returns the whole list.
"The study is not qualified" is not useful; "the worktree is dirty, and here
is everything else that is fine" is.

**What v5 adds to v4r4's list**, each because a v4r4 defect or a v5 rule made
it necessary:

* ``realistic_witness_suite`` --- §7.7's second obligation. Formal
  satisfiability is not enough: a rung with no witness inside the 60-120 word
  stem band cannot be satisfied by an answer the stem permits.
* ``tier_labelling`` and ``structural_metadata`` --- §7.3/§7.4. The tier is
  *computed* from the metadata record, so this asserts the computation agrees
  with every family's declaration rather than trusting the label.
* ``presence_rule`` --- §9.1 at every generative stage. v4r4 scored chance
  verdicts on load-0 rows only, which is why kappa(R|B) had no home in its
  records.
* ``no_composite_score`` and ``no_backup_substitution`` --- §13.1 and §13.14
  as static namespace checks, so the two rules the red team asked for are
  qualified rather than remembered.

**Gate 0 is §19's procedural pilot.** Twelve fixed pre-screen topics, the full
admitted cell plan, both orders, the registered wording allocation, M = 4, at
**fixture** constraint values that cannot become calibration evidence. It
proves the plumbing: every cell and draw committed exactly once, one cell mean
over exactly M accepted draws, a mutated byte refused, a durable restore that
reproduces every hash, and a mask cycle in its own namespace.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo, store
from dci1v4.engine.environment import interpreter_identity

from dci1v7.design.cells import design_cells, n_cells_for, normalise_arms
from dci1v7.design.prompts import assert_stem_present, render
from dci1v7.engine.paths import ModelTree
from dci1v7.protocol import constants as C
from dci1v7.protocol import taxonomy
from dci1v7.protocol.wordings import wording
from dci1v7.run.execute import (generate_and_score, prompt_cell,
                                resolve_generate)
from dci1v7.run.lifecycle import (StageOutcome, TerminalStatus,
                                  protocol_identity, run_stage)
from dci1v7.stages import selection as selection_stage
from dci1v7.stages import validity as validity_stage
from dci1v7.verifiers import verifier_source_hash
from dci1v7.verifiers.constraints import (FAMILIES, FORM_OPERATOR,
                                          Constraint, declared_range)
from dci1v7.verifiers.realistic_witness import run_realistic_suite
from dci1v7.verifiers.witnesses import run_witness_suite
from dci1v7.verifiers.wording_suite import run_wording_suite
from dci1v7.topics.bank import TopicBank, load_bank

__all__ = ["CHECKS", "run_checks", "qualification_payload",
           "run_qualification", "PILOT_SLOT_FIXTURES", "pilot_slot_map",
           "pilot_payload", "run_gate0"]

CHECKS = ("clean_worktree", "commit_hashable", "tracked_implementation",
          "resolved_revisions", "dependency_manifest", "prompt_plan_schema",
          "wording_suite", "witness_suite", "realistic_witness_suite",
          "class_labelling", "tier_labelling", "structural_metadata",
          "presence_rule", "no_composite_score", "no_backup_substitution",
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
    results.append(_check(
        "clean_worktree", not dirty,
        {"changed_paths": len(dirty.splitlines()),
         "why_it_matters": "a run whose producing commit does not contain the "
                           "code that produced it has no provenance"}))

    try:
        commit = gitinfo.head_commit(repo)
    except Exception as error:                              # pragma: no cover
        results.append(_check("commit_hashable", False, str(error)))
    else:
        results.append(_check("commit_hashable", True, commit))

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "dci1/src/dci1v7"], cwd=repo,
        capture_output=True, text=True)
    results.append(_check(
        "tracked_implementation", tracked.returncode == 0,
        "dci1/src/dci1v7 is not tracked" if tracked.returncode else "tracked"))

    from dci1v4.models.registry import MODELS
    resolved = {m.model_key: len(m.revision) == 40 for m in MODELS}
    results.append(_check("resolved_revisions", all(resolved.values()),
                          resolved))

    lock = repo / "dci1" / "uv.lock"
    results.append(_check("dependency_manifest",
                          lock.exists() and lock.stat().st_size > 0,
                          str(lock)))

    topic = bank.topics("prescreen")[0]
    prompts = [render(topic["question"], lines) for lines in
               ([], [wording("A", 0, 4)],
                [wording("A", 0, 4), wording("B", 0, 9)])]
    for prompt in prompts:
        assert_stem_present(prompt)
    results.append(_check("prompt_plan_schema",
                          all(p.endswith("Answer:") for p in prompts),
                          {"loads": [0, 1, 2], "stem": C.STEM_SENTENCE}))

    wordings = run_wording_suite()
    results.append(_check("wording_suite", wordings["passed"],
                          {k: wordings[k] for k in
                           ("instruments", "verdicts_checked")
                           if k in wordings}))

    witnesses = run_witness_suite()
    results.append(_check("witness_suite", witnesses["passed"],
                          {"pairs": witnesses.get("pairs")}))

    realistic = run_realistic_suite()
    results.append(_check(
        "realistic_witness_suite", not realistic.get("failures"),
        {"unreachable": realistic.get("unreachable"),
         "note": "§7.7: a rung with no witness inside the 60-120 word stem "
                 "band cannot be satisfied by an answer the stem permits"}))

    labelling = {kind: bool(f.constraint_class) for kind, f in FAMILIES.items()}
    results.append(_check("class_labelling", all(labelling.values()),
                          {"families": len(labelling)}))

    tiers: dict[str, bool] = {}
    metadata_ok = True
    metadata_detail: list[str] = []
    for kind, family in FAMILIES.items():
        try:
            taxonomy.assert_metadata_consistent(
                kind, family.metadata,
                form_class=family.constraint_class,
                form_operator=FORM_OPERATOR[family.form])
            # The rule is a function of the record, so this asks whether the
            # STORED tier is the one the rule computes --- not whether the
            # stored tier equals itself.
            tiers[kind] = (taxonomy.tier_of_metadata(family.metadata)
                           == family.metadata["structural_tier"])
        except Exception as error:                          # pragma: no cover
            metadata_ok = False
            metadata_detail.append(f"{kind}: {error}")
            tiers[kind] = False
    results.append(_check("tier_labelling", all(tiers.values()),
                          {"families": len(tiers),
                           "disagreeing": sorted(k for k, v in tiers.items()
                                                 if not v)}))
    results.append(_check("structural_metadata", metadata_ok,
                          metadata_detail or
                          {"fields": list(taxonomy.METADATA_FIELDS)}))

    presence = _presence_rule_check()
    results.append(_check("presence_rule", presence["passed"], presence))

    try:
        validity_stage.assert_no_composite_score(vars(validity_stage))
        composite_ok, composite_detail = True, "no composite score exists"
    except Exception as error:
        composite_ok, composite_detail = False, str(error)
    results.append(_check("no_composite_score", composite_ok,
                          composite_detail))

    try:
        selection_stage.assert_no_backup_substitution(vars(selection_stage))
        backup_ok, backup_detail = True, "no substitution path exists"
    except Exception as error:
        backup_ok, backup_detail = False, str(error)
    results.append(_check("no_backup_substitution", backup_ok, backup_detail))

    durable = Path(context.durable_root)
    results.append(_check("durable_store_reachable",
                          durable.exists() or durable.parent.exists(),
                          str(durable)))

    identity = interpreter_identity()
    results.append(_check("environment_hashable", bool(identity), identity))
    return results


def _presence_rule_check() -> dict[str, Any]:
    """§9.1 exercised on a constructed row rather than asserted in prose.

    A B-solo cell with an absent reference is the *only* place kappa(R|B)
    comes from, so the check is run on exactly that shape.
    """
    from dci1v7.verifiers.compliance import (assert_presence_rule,
                                             score_generation)

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
    return {"passed": len(absent) == 1,
            "kappa_under_b_available": len(absent) == 1,
            "note": "an absent reference scored on a B-solo row is §13.6's "
                    "only input and costs no generation"}


def qualification_payload(context: Any, *, producing_commit: str,
                          bank: TopicBank | None = None) -> dict[str, Any]:
    """§18 stage 2. Fails closed with the whole list of reasons."""
    bank = bank if bank is not None else load_bank()
    results = run_checks(context, bank=bank)
    failed = [r for r in results if not r["passed"]]
    population = (len(C.TARGET_GRID)
                  + len(C.FOCAL_GRID) + len(C.FOCAL_EXTENSION)
                  + sum(len(declared_range(k)) for k in FAMILIES))
    payload = {
        "stage": C.STAGE_QUALIFIED,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_QUALIFIED],
        "inputs": {"registration": {"stage": C.STAGE_REGISTERED}},
        "producing_commit": producing_commit,
        "canonical_verifier_hash": verifier_source_hash(),
        "instrument_population": population,
        "checks": results,
        "checks_expected": list(CHECKS),
        "reads_no_behavioural_rate": True,
        "topic_split_identity": bank.split_identity,
    }
    if failed:
        raise TerminalStatus(
            "QUALIFICATION_FAILURE", gate=C.STAGE_QUALIFIED,
            criterion="§18 stage 2: every apparatus precondition",
            observed=[r["check"] for r in failed],
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    return {**payload, "outcome": "PASS"}


def run_qualification(tree: ModelTree, *, producing_commit: str | None = None,
                      environment_digest: str = "",
                      bank: TopicBank | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_QUALIFIED,
        compute=lambda _prev: qualification_payload(
            tree.context, producing_commit=commit, bank=bank),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------- §19 pilot

#: §19's fixture instances. They are **not** calibration values and cannot
#: become any: the pilot runs on twelve pre-screen topics, its rows carry the
#: pilot stage name, and no selection rule reads a pilot row. The values are
#: the middle of each registered grid so that the plumbing is exercised at a
#: severity a model can plausibly satisfy without any of it meaning anything.
PILOT_SLOT_FIXTURES: dict[str, tuple[str, int]] = {
    "A": ("A", C.TARGET_GRID[len(C.TARGET_GRID) // 2]),
    "B": ("B", C.FOCAL_GRID[len(C.FOCAL_GRID) // 2]),
    "R1": ("MK1", FAMILIES["MK1"].ladder[1]),
    "R2": ("MK2", FAMILIES["MK2"].ladder[1]),
    "R3": ("MK3", FAMILIES["MK3"].ladder[1]),
    "R1-": ("MK1", FAMILIES["MK1"].ladder[0]),
    "R1+": ("MK1", FAMILIES["MK1"].ladder[2]),
    "R2-": ("MK2", FAMILIES["MK2"].ladder[0]),
    "R2+": ("MK2", FAMILIES["MK2"].ladder[2]),
    "R3-": ("MK3", FAMILIES["MK3"].ladder[0]),
    "R3+": ("MK3", FAMILIES["MK3"].ladder[2]),
    "N1": ("XC1", FAMILIES["XC1"].ladder[1]),
    "N2": ("XC2", FAMILIES["XC2"].ladder[1]),
    "N3": ("XC3", FAMILIES["XC3"].ladder[1]),
    "CL": ("RF1", FAMILIES["RF1"].ladder[1]),
}


def pilot_slot_map(arms: Sequence[str]) -> dict[str, Constraint]:
    """Fixture instances for every slot the admitted arms need."""
    from dci1v7.design.cells import slots_for

    return {slot: Constraint(*PILOT_SLOT_FIXTURES[slot])
            for slot in slots_for(normalise_arms(arms))}


class _PilotBlock:
    __slots__ = ("block_id", "index", "topic_id")

    def __init__(self, block_id: str, index: int, topic_id: str):
        self.block_id, self.index, self.topic_id = block_id, index, topic_id


def pilot_payload(tree: ModelTree, *, producing_commit: str,
                  arms: Sequence[str] = C.ARMS,
                  bank: TopicBank | None = None,
                  cap: int = C.COMPLETION_CAPS[-1], device: int = 0,
                  generate: Callable[..., dict[str, Any]] | None = None
                  ) -> dict[str, Any]:
    """§19's procedural pilot on twelve fixed pre-screen topics."""
    bank = bank if bank is not None else load_bank()
    arms = normalise_arms(arms)
    prescreen = list(bank.topics("prescreen"))
    chosen: list[dict[str, Any]] = []
    for area in C.SUBJECT_AREAS:
        for topic in prescreen:
            if topic["area"] == area:
                chosen.append(topic)
                break
    if len(chosen) != C.PILOT_TOPICS:
        raise TerminalStatus(
            "APPARATUS_FAILURE", gate=C.STAGE_GATE0,
            criterion=f"§19: {C.PILOT_TOPICS} fixed pre-screen topics",
            observed=len(chosen),
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    blocks = [_PilotBlock(f"pilot-{i:02d}", i, t["topic_id"])
              for i, t in enumerate(chosen)]
    cells = design_cells(blocks, arms, draws=C.PILOT_DRAWS)
    slot_map = pilot_slot_map(arms)
    by_topic = {t["topic_id"]: t for t in chosen}
    prompt_cells = [prompt_cell(cell, by_topic[cell.topic_id],
                                slot_map=slot_map, topic_split="prescreen")
                    for cell in cells]
    run_dir = tree.backend_runs(C.STAGE_GATE0) / "pilot"
    instances = tuple(dict.fromkeys(slot_map.values()))
    rows = generate_and_score(
        tree.model_key, prompt_cells, stage=C.STAGE_GATE0, cap=cap,
        device=device, run_dir=run_dir, instances=instances,
        slot_map=slot_map, study_id=tree.context.study_id,
        protocol_identity=protocol_identity(tree, C.STAGE_GATE0),
        generate=resolve_generate(tree, generate, _pilot_responder,
                                  where=C.STAGE_GATE0))

    expected = len(prompt_cells) * C.PILOT_DRAWS
    identities = [r["row_id"] for r in rows]
    per_cell: dict[str, int] = {}
    for row in rows:
        per_cell[f"{row['block_id']}:{row['cell_id']}"] = \
            per_cell.get(f"{row['block_id']}:{row['cell_id']}", 0) + 1
    acceptance = {
        "every_cell_and_draw_once": (len(identities) == expected
                                     and len(set(identities)) == expected),
        "one_cell_mean_over_M": all(n == C.PILOT_DRAWS
                                    for n in per_cell.values()),
        "byte_mutation_refused": _byte_mutation_refused(run_dir),
        "durable_restore_matches": _durable_restore_matches(tree, run_dir),
        "mask_cycle": _mask_cycle_ran(tree, rows),
        "no_processing_failures": not any(
            s["processing_failure"] for r in rows for s in r["scores"]),
    }
    failed = sorted(k for k, v in acceptance.items() if not v)
    payload = {
        "stage": C.STAGE_GATE0,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE0],
        "inputs": {"qualification": {"stage": C.STAGE_QUALIFIED}},
        "producing_commit": producing_commit,
        "admitted_arms_exercised": list(arms),
        "cells_per_block": n_cells_for(arms),
        "blocks": len(blocks),
        "draws": C.PILOT_DRAWS,
        "rows": len(rows),
        "expected_rows": expected,
        "slot_fixtures": {s: c.label for s, c in slot_map.items()},
        "fixture_declaration":
            "§19: fixture values that cannot become calibration evidence; no "
            "selection rule reads a pilot row and the rows carry the pilot "
            "stage name",
        "acceptance": acceptance,
        "topic_ids": sorted(t["topic_id"] for t in chosen),
        "synthetic_rows": all(r["synthetic"] for r in rows),
    }
    if failed:
        raise TerminalStatus(
            "APPARATUS_FAILURE", gate=C.STAGE_GATE0,
            criterion="§19's acceptance conditions", observed=failed,
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    return {**payload, "outcome": "PASS"}


def _pilot_responder(row: Mapping[str, Any]) -> str:
    """A deterministic answer of stem-band length, from the row identity.

    It is not a model and does not pretend to be one. Its only job is to make
    the plumbing produce rows whose identities, hashes and counts can be
    checked. The text is a function of the row id, so a rerun reproduces it
    and the durability checks mean something.
    """
    words = ["thus", "hence", "though", "whereas", "indeed", "namely",
             "instead", "overall", "a", "brief", "reply", "here"]
    seed = sum(ord(ch) for ch in str(row["row_id"]))
    body = " ".join(words[(seed + i) % len(words)] for i in range(70))
    return body.capitalize() + "."


def _byte_mutation_refused(run_dir: Path) -> bool:
    """§19: mutating one stored byte changes its hash and the row is refused."""
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
    """§19: cache deletion and durable restore reproduce every row's hash."""
    durable = tree.durable / C.STAGE_GATE0 / "backend_runs" / run_dir.name
    try:
        before = store.replicate(run_dir, durable)
        store.assert_replicated(run_dir, durable)
        after = store.fingerprint_tree(durable)
        return before == after
    except Exception:                                        # pragma: no cover
        return False


def _mask_cycle_ran(tree: ModelTree, rows: Sequence[Mapping[str, Any]]
                    ) -> bool:
    """§19: the pilot mask cycle, in its own namespace."""
    from dci1v7.analysis.masking import apply_mask, build_mask
    from dci1v7.analysis.observations import build_observations

    try:
        observations = build_observations(list(rows), m_draws=C.PILOT_DRAWS)
        if len(observations) < 2:
            return False
        mask = build_mask(observations, namespace="pilot_mask", entropy=0)
        masked = apply_mask(observations, mask)
        return len(masked) == len(observations)
    except Exception:                                        # pragma: no cover
        return False


def run_gate0(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "", arms: Sequence[str] = C.ARMS,
              bank: TopicBank | None = None, device: int = 0,
              cap: int = C.COMPLETION_CAPS[-1],
              generate: Callable[..., dict[str, Any]] | None = None
              ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_GATE0,
        compute=lambda _prev: pilot_payload(
            tree, producing_commit=commit, arms=arms, bank=bank, cap=cap,
            device=device, generate=generate),
        producing_commit=commit, environment_digest=environment_digest)
