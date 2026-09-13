"""§18 stage 1, ``PROTOCOL_REGISTERED``: adoption, and why it refuses.

This is where v5 stops being a draft. The runner assembles the signed
registration manifest, binds §34's nineteen closures and their evidence into
it, and writes the stage record that every later stage's predecessor check
reads.

**It succeeds now**, and every refusal that used to stop it is still built:
``protocol/manifest.signing_blockers`` reports open decisions, unresolved
specification questions, missing topic-bank hashes, an unapproved candidate
population, an unconfirmed item, an unspecified floor, an unpinned model
revision and a non-derivable design --- each by name rather than collapsed
into one. §18 stage 1's registered failure status is
``REGISTRATION_INCOMPLETE``.

**The manifest is study-level and the record is per model.** §6.1 fixes every
study-wide rule before the first qualification, so the first replication signs
and the other three verify --- see ``manifest.ensure_registration``. Signing
on every call is what made three of the four registered models unregisterable.

``plan_registration`` produces the same report **without** attempting to sign,
so a researcher can see exactly what adoption binds without a call that could
write anything. ``supersede_registration`` is §32's path when a registration
has to be replaced before any observation exists; it retains everything.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError

from dci1v5 import STUDY_ID
from dci1v5.engine.paths import ModelTree
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions, manifest, open_items
from dci1v5.run.lifecycle import (StageOutcome, TerminalStatus, now,
                                  run_stage)
from dci1v5.topics.bank import TopicBank, load_bank

__all__ = ["plan_registration", "registration_payload",
           "supersede_registration", "run_registration"]


def plan_registration(*, repo_root: Path | str = ".",
                      bank: TopicBank | None = None) -> dict[str, Any]:
    """What adoption would bind, and everything that stops it. Writes nothing.

    Safe to call at any time, including today. It never signs, never creates
    a key and never touches an evidence root.
    """
    bank = bank if bank is not None else load_bank()
    blockers = manifest.signing_blockers(bank)
    return {
        "stage": C.STAGE_REGISTERED,
        "can_register": not blockers,
        "failure_status": (None if not blockers
                           else manifest.REGISTRATION_INCOMPLETE),
        "blockers": blockers,
        "n_blockers": len(blockers),
        "open_decisions": list(decisions.open_decisions()),
        "blocking_specification_questions": list(open_items.blocking_items()),
        "calibration_b_status": bank.calibration_b_status,
        "topic_hashes": bank.hashes,
        "what_adoption_binds": list(manifest.REQUIRED_BINDINGS),
        "note": "no manifest is built by this call; build_manifest(...) "
                "assembles the payload for inspection and sign_registration "
                "is the only path that writes one",
    }


def registration_payload(tree: ModelTree, *, producing_commit: str,
                         adoption: Mapping[str, Any],
                         repo_root: Path | str = ".",
                         bank: TopicBank | None = None,
                         supersedes: str | None = None) -> dict[str, Any]:
    """The stage record. Raises ``REGISTRATION_INCOMPLETE`` when not ready."""
    bank = bank if bank is not None else load_bank()
    plan = plan_registration(repo_root=repo_root, bank=bank)
    if not plan["can_register"]:
        raise TerminalStatus(
            manifest.REGISTRATION_INCOMPLETE,
            gate=C.STAGE_REGISTERED,
            criterion="§34: every open decision closed with its evidence, "
                      "every specification question resolved, the topic-bank "
                      "hashes present and the candidate population approved",
            observed=plan["blockers"],
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    signed = manifest.ensure_registration(
        tree.context, producing_commit=producing_commit, adoption=adoption,
        bank=bank, repo_root=repo_root, supersedes=supersedes)
    return {
        "stage": C.STAGE_REGISTERED,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_REGISTERED],
        "outcome": "PASS",
        "inputs": {},
        "manifest_hash": signed["manifest_hash"],
        "protocol_hash": signed["protocol_hash"],
        "reference_design_spec_hash": signed["reference_design_spec_hash"],
        "protocol_version": signed["protocol_version"],
        "decisions": signed["decisions"],
        "open_items": signed["open_items"],
        "topic_hashes": bank.hashes,
        "calibration_a_hash": bank.hashes[C.CALIBRATION_A],
        "calibration_b_hash": bank.hashes[C.CALIBRATION_B],
        "split_hash": bank.split_identity["split_hash"],
        "models": signed["models"],
        "measurement_basis": signed["measurement_basis"],
        "adoption": dict(adoption),
        "supersedes": signed.get("supersedes"),
    }


def supersede_registration(context: Any, *, reason: str,
                           model_keys: Sequence[str],
                           producing_commit: str,
                           amendment: Mapping[str, Any] | None = None,
                           invalidating: Mapping[str, str] | None = None
                           ) -> dict[str, Any]:
    """§32: retain a registration and everything signed under it, so a
    corrected one can be signed.

    Nothing is deleted. The manifest and every replication's stage-1 record
    move under ``superseded/<old manifest hash>/``, which
    ``engine/paths.is_superseded`` already excludes from every *current* pool
    while the durability audit still counts the files. A supersession record
    naming the old hash, the reason and the new producing commit is written
    beside them, and each replication's transition log gets a row --- an
    evidence tree that changed shape with nothing in the log saying why is the
    thing this exists to prevent.

    This is admissible **only before any observation exists**. A superseded
    registration with rows under it is not a re-registration, it is a
    discarded experiment, and §32 wants that said out loud rather than
    performed by a move.

    The line is drawn at ``GATE_0_APPARATUS``, the first stage that generates.
    ``PROTOCOL_REGISTERED`` and ``QUALIFIED`` produce no model response and no
    behavioural rate --- qualification reads none by construction (§19) --- so
    they are retained and re-run under the replacement rather than blocking
    it. Everything from Gate 0 on carries generated text, or a quantity
    derived from it, and refuses.

    ``invalidating`` is the researcher's explicit override, and the only way
    past that refusal: a mapping of model key to the reason its behavioural
    chain is being discarded. §32 calls this a discarded replication rather
    than a re-registration, and the difference has to be *said*, so an
    invalidated replication gets an ``invalidated.json`` naming every stage
    discarded and how many generated rows went with it. Its whole tree ---
    records and ``backend_runs`` alike --- moves under
    ``superseded/<manifest>/``, which is what makes the rows unreachable to
    ``run/execute._reusable_rows``: reuse reads ``tree.backend_runs(stage)``,
    the *current* path, so a retained run cannot be resumed into a later one
    by accident.

    §28.3's ``terminal_report.json`` moves too, and that is the repair for a
    defect this function had from the start: it retired every stage record and
    left the terminal verdict on the live path, where
    ``assert_predecessor_passed`` reads it. A replication that had terminated
    could therefore be superseded but never re-run --- the replacement
    registration's very first stage was disabled by a verdict about the
    registration it replaced. The verdict is retained, not deleted, beside the
    records it was reached on.
    """
    from dci1v4.engine import store
    from dci1v5.engine import transitions
    from dci1v5.engine.paths import model_tree
    from dci1v5.protocol import manifest as manifest_mod

    existing = manifest_mod.load_manifest(context)
    old_hash = existing["manifest_hash"]

    first_generating = C.STAGE_SEQUENCE.index(C.STAGE_GATE0)
    pre_observation = C.STAGE_SEQUENCE[:first_generating]
    invalidating = dict(invalidating or {})
    unknown = sorted(set(invalidating) - set(model_keys))
    if unknown:
        raise IntegrityError(
            f"cannot invalidate {unknown}: not among the replications being "
            "superseded")
    observed = []
    for key in model_keys:
        if key in invalidating:
            continue
        tree = model_tree(context, key)
        for stage in C.STAGE_SEQUENCE[first_generating:]:
            if tree.stage_record(stage).exists():
                observed.append(f"{key}:{stage}")
    if observed:
        raise IntegrityError(
            f"registration {old_hash} already has records for stages that "
            f"generate or read generated text ({observed}). Superseding it "
            "would orphan signed evidence; that is a discarded replication "
            "under §32 and must be recorded as one --- name the replication "
            "in `invalidating` with its reason, or do not supersede")

    discarded: dict[str, Any] = {}
    for key, why in invalidating.items():
        tree = model_tree(context, key)
        stages, rows = [], 0
        for stage in C.STAGE_SEQUENCE:
            if not tree.stage_dir(stage).exists():
                continue
            stages.append(stage)
            for produced in tree.stage_dir(stage).rglob("rows.jsonl"):
                rows += sum(1 for line in produced.open() if line.strip())
        record = {
            "model_key": key, "reason": why,
            "superseded_manifest": old_hash,
            "stages_discarded": stages,
            "behavioural_rows_discarded": rows,
            "reusable": False,
            "why_not_reusable":
                "retained under superseded/, which is not the path "
                "run/execute._reusable_rows reads; and §32 treats a "
                "discarded replication's rows as evidence of what was run, "
                "not as input to what replaces it",
            "discarded_at": now(),
        }
        discarded[key] = record
        tree.superseded_dir(old_hash).mkdir(parents=True, exist_ok=True)
        fs.write_json_once(
            tree.superseded_dir(old_hash) / "invalidated.json", record)

    retained: dict[str, list[str]] = {}
    for key in model_keys:
        tree = model_tree(context, key)
        stages = (C.STAGE_SEQUENCE if key in invalidating else pre_observation)
        for stage in stages:
            source = tree.stage_dir(stage)
            if not source.exists():
                continue
            target = tree.superseded_dir(old_hash) / stage
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            durable_source = tree.durable / stage
            if durable_source.exists():
                durable_target = (tree.durable / "superseded" / old_hash
                                  / stage)
                durable_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(durable_source), str(durable_target))
            retained.setdefault(key, []).append(str(target))
            transitions.log_transition(
                tree, stage=stage, outcome="SUPERSEDED",
                producing_commit=producing_commit, environment_digest="",
                detail={"superseded_manifest": old_hash, "reason": reason,
                        "retained_at": str(target)})
        # §28.3's terminal report belongs to the registration that produced
        # it, and it is `write_json_once` and read by
        # `assert_predecessor_passed`. Leaving it on the live path made a
        # supersession one-way for any replication that had terminated: the
        # stage records moved, the terminal status stayed, and every later
        # stage of the REPLACEMENT registration was mechanically disabled by
        # a verdict about the registration it replaced. It moves with the
        # rest, so what the replacement sees is the state it is entitled to
        # see, and the retired verdict stays readable where it was reached.
        if tree.terminal_report.exists():
            target = tree.superseded_dir(old_hash) / tree.terminal_report.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tree.terminal_report), str(target))
            durable_terminal = tree.durable / tree.terminal_report.name
            if durable_terminal.exists():
                durable_target = (tree.durable / "superseded" / old_hash
                                  / tree.terminal_report.name)
                durable_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(durable_terminal), str(durable_target))
            retained.setdefault(key, []).append(str(target))
            transitions.log_transition(
                tree, stage=C.STAGE_QUALIFIED, outcome="SUPERSEDED",
                producing_commit=producing_commit, environment_digest="",
                detail={"superseded_manifest": old_hash, "reason": reason,
                        "retained_at": str(target),
                        "terminal_report": True})

    keep = Path(context.registration_root) / "superseded" / old_hash
    keep.mkdir(parents=True, exist_ok=True)
    shutil.move(str(context.registration_manifest),
                str(keep / "registration_manifest.json"))
    record = {
        "superseded_manifest_hash": old_hash,
        "superseded_producing_commit": existing["producing_commit"],
        "superseded_protocol_version": existing["protocol_version"],
        "superseded_classification": existing["classification"],
        "reason": reason,
        "amendment": dict(amendment or {}),
        "new_producing_commit": producing_commit,
        "retained_stage_records": retained,
        "retained_stages": list(pre_observation),
        "invalidated": discarded,
        "observations_under_it": sum(
            d["behavioural_rows_discarded"] for d in discarded.values()),
        "superseded_at": now(),
    }
    fs.write_json_once(keep / "supersession.json", record)
    durable = (Path(context.durable_root) / STUDY_ID
               / context.registration_root.name)
    store.replicate(context.registration_root, durable)
    return record


def run_registration(tree: ModelTree, *, producing_commit: str | None = None,
                     adoption: Mapping[str, Any] | None = None,
                     repo_root: Path | str = ".",
                     environment_digest: str = "",
                     bank: TopicBank | None = None,
                     supersedes: str | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(repo_root))
    return run_stage(
        tree, C.STAGE_REGISTERED,
        compute=lambda _prev: registration_payload(
            tree, producing_commit=commit,
            adoption=dict(adoption or {"status": "DRAFT"}),
            repo_root=repo_root, bank=bank, supersedes=supersedes),
        producing_commit=commit, environment_digest=environment_digest)
