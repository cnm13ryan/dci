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
into one. §18 stage 1's registered readiness status is
``REGISTRATION_INCOMPLETE``, and since amendment A15 it is a **refusal**:
every blocker names work a researcher has to do, so the verdict is logged,
writes no record and no terminal report, and the stage is attempted again
once the work is done.

**The manifest is study-level and the record is per model.** §6.1 fixes every
study-wide rule before the first qualification, so the first replication signs
and the other three verify --- see ``manifest.ensure_registration``. Signing
on every call is what made three of the four registered models unregisterable.

``plan_registration`` produces the same report **without** attempting to sign,
so a researcher can see exactly what adoption binds without a call that could
write anything. ``supersede_registration`` is §32's path when a registration
has to be replaced before any observation exists; it retains everything.
``retire_apparatus_fault`` is the same shape for the one case that predates a
manifest: a readiness verdict that a caller's own defect wrote as a §28.3
terminal report, retained under ``superseded/apparatus_fault/`` and named by
its own hash in every registration signed afterwards.
"""
from __future__ import annotations

import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError

from dci1v7 import STUDY_ID
from dci1v7.engine.paths import ModelTree
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions, manifest, open_items
from dci1v7.run.lifecycle import ReadinessRefusal, StageOutcome, now, run_stage
from dci1v7.topics.bank import TopicBank, load_bank

__all__ = [
    "amend_registration",
    "plan_registration",
    "registration_payload",
    "retire_apparatus_fault",
    "run_registration",
    "supersede_registration",
]


def plan_registration(*, repo_root: Path | str = ".",
                      bank: TopicBank | None = None) -> dict[str, Any]:
    """What adoption would bind, and everything that stops it. Writes nothing.

    Safe to call at any time, including today. It never signs, never creates
    a key and never touches an evidence root.
    """
    bank = bank if bank is not None else load_bank()
    blockers = manifest.signing_blockers(bank, repo_root=repo_root)
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
    """The stage record, or a ``ReadinessRefusal`` when the study is not ready.

    The criterion is ``signing_blockers`` and it is exactly the criterion it
    always was. What A15 changed is the *kind* of verdict: a study that is not
    yet ready is refused, logged and left where it was, rather than
    terminated. Every blocker names outstanding researcher work, so a
    terminating verdict made the whole vocabulary unreachable --- and made a
    caller's own configuration defect able to end a replication.
    """
    bank = bank if bank is not None else load_bank()
    plan = plan_registration(repo_root=repo_root, bank=bank)
    if not plan["can_register"]:
        raise ReadinessRefusal(
            manifest.REGISTRATION_INCOMPLETE,
            gate=C.STAGE_REGISTERED,
            criterion="§34: every open decision closed with its evidence, "
                      "every specification question resolved, the topic-bank "
                      "hashes present and the candidate population approved",
            observed=plan["blockers"],
            remedy="each blocker names work a researcher does --- close the "
                   "decision, resolve the question, build the calibration "
                   "set, approve the population, adopt the document --- and "
                   "then attempt PROTOCOL_REGISTERED again. Check the "
                   "`--repo-root` this ran against before acting on a "
                   "DRAFT_DOCUMENT finding: a document reported missing may "
                   "be a document looked for in the wrong repository")
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

    from dci1v7.engine import transitions
    from dci1v7.engine.paths import model_tree
    from dci1v7.protocol import manifest as manifest_mod

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


def amend_registration(context: Any, *, amendment_id: str, reason: str,
                       direction: str, sections: Sequence[str],
                       declaration: str, model_keys: Sequence[str],
                       producing_commit: str, repo_root: Path | str = ".",
                       decided_by: str, decided_on: str) -> dict[str, Any]:
    """§32 / v7 A4: bind an amendment adopted after the registration.

    v6 had two ways to change a registered document and neither covered the
    case that occurred. ``supersede_registration`` replaces a registration
    before any observation exists; ``retire_apparatus_fault`` retires one
    stage-1 verdict before any row. A16 and A17 were adopted with rows on the
    tree, the preregistration's bytes moved, and the pre-freeze audit's
    ``protocol_hashes_agree`` then refused the one replication that had
    passed every scientific gate --- correctly, under the rule it had, which
    was that the document must be the registered one.

    This is the third way, and it is the one §32 describes: an append-only
    register. The record carries the document hashes **before** (the chain
    head) and **after** (the files on disk now), the amendment's id, its
    reason, the sections it touches, the direction it declares relative to
    the criterion it touches, the §32.2 disclosure in the researcher's own
    words, and --- per replication --- the stage reached, the terminal status
    if any and the number of behavioural rows on the tree at adoption. It is
    signed with the study key, written once, mirrored, and logged on every
    replication's transition log. ``manifest.document_binding`` walks the
    chain and the pre-freeze audit reads its head, so an amended document is
    legal exactly when the chain says how it came to differ.

    **§32.3 is refused here, executably.** No component of §13 changes after
    Gate 2.5 begins on the first replication: an amendment naming a §13
    section is refused once any replication holds a Gate-2.5 record. What
    §32.1 asks --- that an amendment is never used to weaken a criterion so
    that a gate passes --- is not decidable by code; the record requires the
    direction to be declared and the disclosure to be written, so that a
    reader can judge it.
    """
    from dci1v4.engine import store
    from dci1v4.engine.signing import sign_payload
    from dci1v4.protocol.hashing import sha_obj

    from dci1v7.engine import transitions
    from dci1v7.engine.paths import model_tree
    from dci1v7.protocol import manifest as manifest_mod

    if direction not in manifest_mod.AMENDMENT_DIRECTIONS:
        raise IntegrityError(
            f"an amendment declares one of "
            f"{manifest_mod.AMENDMENT_DIRECTIONS}; got {direction!r}")
    touched = [str(x).strip() for x in sections if str(x).strip()]
    if not touched or not all(t.startswith("§") for t in touched):
        raise IntegrityError(
            "an amendment names the sections it touches, each as '§N...'; "
            f"got {list(sections)!r}")
    if not (amendment_id and reason and declaration and decided_by
            and decided_on):
        raise IntegrityError(
            "an amendment record carries its id, reason, §32.2 declaration, "
            "who adopted it and when; none may be blank")
    existing = manifest_mod.load_manifest(context)
    head = manifest_mod.document_binding(context, existing)
    before = {k: head[k] for k in ("protocol_hash",
                                   "reference_design_spec_hash")}
    after = manifest_mod.document_hashes(repo_root)
    if after == before:
        raise IntegrityError(
            "the governed documents on disk are the ones already bound; an "
            "amendment record with no change to bind would be a citation to "
            "nothing. Edit the document first, then bind the amendment")
    replications: dict[str, Any] = {}
    gate_2_5_exists = False
    for key in model_keys:
        tree = model_tree(context, key)
        reached = transitions.stage_reached(tree)
        if tree.stage_record(C.STAGE_GATE2_5).exists():
            gate_2_5_exists = True
        replications[key] = {
            "stage_reached": reached,
            "terminal_status": transitions.terminal_status(tree),
            "behavioural_rows": behavioural_rows_in(tree.root),
        }
    if gate_2_5_exists and any(t.startswith("§13") for t in touched):
        raise IntegrityError(
            f"§32.3: {touched} names §13, and a replication holds a "
            f"{C.STAGE_GATE2_5} record. No component of §13 changes after "
            "Gate 2.5 begins on the first replication; that change is a "
            "superseding protocol version, not an amendment")
    previous = manifest_mod.amendment_records(context)
    sequence = len(previous) + 1
    payload = {
        "amendment_id": amendment_id, "sequence": sequence,
        "study_id": context.study_id,
        "manifest_hash": existing["manifest_hash"],
        "before": before, "after": dict(after),
        "reason": reason, "direction": direction,
        "sections": touched, "declaration_32_2": declaration,
        "replications_at_adoption": replications,
        "any_behavioural_row_at_adoption": any(
            r["behavioural_rows"] > 0 for r in replications.values()),
        "producing_commit": producing_commit,
        "decided_by": decided_by, "decided_on": decided_on,
        "adopted_on": now(),
        "rule": "§32 / v7 A4: append-only; the chain head is what the "
                "pre-freeze audit and the freeze read",
    }
    payload["record_hash"] = sha_obj(payload)
    root = Path(context.registration_root) / manifest_mod.AMENDMENTS_DIRNAME
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{sequence:03d}_{amendment_id}.json"
    fs.write_json_once(path, sign_payload(payload,
                                          context.signing_key_path))
    durable = (Path(context.durable_root) / STUDY_ID
               / context.registration_root.name)
    store.replicate(context.registration_root, durable)
    for key in model_keys:
        tree = model_tree(context, key)
        if not tree.root.exists():
            continue
        transitions.log_transition(
            tree, stage=replications[key]["stage_reached"]
            or C.STAGE_REGISTERED,
            outcome="AMENDED", producing_commit=producing_commit,
            environment_digest="",
            detail={"amendment_id": amendment_id, "sequence": sequence,
                    "direction": direction, "sections": touched,
                    "record_hash": payload["record_hash"],
                    "record": str(path)})
    return payload


#: What a retirement record has to say about itself before it is written.
#: Named rather than inlined so that a caller cannot retire a record with a
#: blank reason and an unnamed amendment.
APPARATUS_FAULT_FIELDS = ("amendment", "reason", "defect")


def behavioural_rows_in(study_root: Path) -> int:
    """Every generated row under a study root, superseded ones included.

    The count is deliberately *total* rather than current. The question a
    retirement asks is "has this study observed anything yet", and a row that
    was retired under a supersession was still generated --- so counting only
    the live path would let a study that had produced data look untouched.
    """
    total = 0
    for produced in sorted(Path(study_root).rglob("rows.jsonl")):
        total += sum(1 for line in produced.open() if line.strip())
    return total


def retire_apparatus_fault(tree: ModelTree, *, record_hash: str, reason: str,
                           defect: str, amendment: Mapping[str, Any],
                           producing_commit: str,
                           decided_by: str, decided_on: str) -> dict[str, Any]:
    """§32/A15: retire a stage-1 readiness verdict an apparatus fault wrote.

    **This exists for one incident and its preconditions say so.** On
    2026-08-26 the v6 CLI did not forward ``--repo-root`` to
    ``run_registration``, whose default was ``"."``; invoked from ``dci1/``,
    ``assert_documents_adopted`` looked for the two governed documents one
    directory below where they are and reported both **missing**. Stage 1
    recorded ``REGISTRATION_INCOMPLETE`` against ``gemma-3n-e2b-it`` as a §28.3
    terminal report, naming two files that exist and declare ``ADOPTED`` at the
    very commit the record cites, and ``assert_predecessor_passed`` then
    disabled every later stage for that replication permanently. §6.1 registers
    four replications; a defect in the caller had reduced them to three.

    ``supersede_registration`` is §32's registered path for replacing a
    registration, and it does not reach this: it retires records under
    ``superseded/<old manifest hash>/`` and there was no manifest to name. So
    this borrows its shape --- retain, never delete; move under
    ``superseded/``; write a record saying what moved and why; log it on the
    replication's own transition log --- and names the retired **record** by
    its own hash where the other names a manifest by its.

    Six preconditions, every one of them a refusal:

    1. the terminal report exists and its file hash is the one the caller
       named, so a retirement cannot be aimed at a record nobody read;
    2. its signature verifies under this study's key;
    3. it is a ``PROTOCOL_REGISTERED`` verdict carrying a **readiness** status.
       A ``FOCAL_RANGE_EXHAUSTED`` at Gate 2, a
       ``REGIME_NOT_FOUND`` at Gate 2, a ``PREFREEZE_AUDIT_FAILURE`` --- every
       scientific terminal in §28 --- is refused here, and that is what stops
       this from being a general revival facility;
    4. **no registration manifest exists.** Once a study is registered this
       path is closed, because a stage-1 verdict after that is a verdict about
       a signed registration and not about an unready study;
    5. **no behavioural row exists anywhere in the study**, counted from the
       filesystem rather than believed;
    6. the replication has no stage record at all, so nothing downstream was
       ever computed from the verdict being retired.

    Nothing is deleted and nothing is rewritten. The signed report moves,
    byte-identical, to ``superseded/apparatus_fault/<record hash>/`` in the
    evidence tree and in the durable mirror; ``is_superseded`` already
    excludes that path from every current pool and the durability audit
    already counts it. The transition log is append-only and keeps every row
    the failed attempt wrote, including the ``TERMINAL`` one. The retirement
    record beside the report carries the retired payload verbatim, so reading
    the fault does not require reading the file it names.

    And it is bound into what follows: ``manifest.build_manifest`` reads these
    records and every registration signed afterwards carries them, so the
    incident is inside the signature of the study that replaced it rather
    than beside it.
    """
    from dci1v4.engine import store
    from dci1v4.engine.signing import verify_signed
    from dci1v4.protocol.hashing import sha_bytes

    from dci1v7.engine import paths as P
    from dci1v7.engine import transitions

    missing = [f for f in APPARATUS_FAULT_FIELDS
               if not (amendment if f == "amendment" else
                       {"reason": reason, "defect": defect}[f])]
    if missing:
        raise IntegrityError(
            f"a retirement states what it is and under which amendment; "
            f"missing {missing}")

    report = tree.terminal_report
    if not report.exists():
        raise IntegrityError(
            f"{tree.model_key}: there is no terminal report at {report} to "
            "retire")
    observed_hash = sha_bytes(report.read_bytes())
    if observed_hash != record_hash:
        raise IntegrityError(
            f"{tree.model_key}: the terminal report at {report} hashes to "
            f"{observed_hash} and the retirement names {record_hash}. A "
            "retirement identifies the exact record it retires; a mismatch "
            "means the record moved, or the caller is aiming at a different "
            "one, and either way this refuses")
    payload = verify_signed(fs.read_json(report),
                            tree.context.signing_key_path,
                            where=f"{tree.model_key}:terminal_report")
    if payload.get("gate") != C.STAGE_REGISTERED:
        raise IntegrityError(
            f"{tree.model_key}: this record is a verdict at "
            f"{payload.get('gate')!r}. Only a {C.STAGE_REGISTERED} readiness "
            "verdict may be retired as an apparatus fault; a scientific gate's "
            "outcome is a RESULT and §28 makes it irreversible")
    if payload.get("status") not in C.READINESS_REFUSAL_STATUSES:
        raise IntegrityError(
            f"{tree.model_key}: {payload.get('status')!r} is a §28 terminal "
            f"status, not a readiness status "
            f"({C.READINESS_REFUSAL_STATUSES}). It is not retirable")
    if Path(tree.context.registration_manifest).exists():
        raise IntegrityError(
            f"{tree.model_key}: this study has a signed registration at "
            f"{tree.context.registration_manifest}. A stage-1 verdict reached "
            "after a registration exists is not the pre-manifest apparatus "
            "fault this path recovers; §32's supersede_registration is the "
            "registered route once a manifest can be named")
    rows = behavioural_rows_in(tree.context.study_root)
    if rows:
        raise IntegrityError(
            f"this study holds {rows} generated row(s). A retirement is "
            "admissible only before any observation exists; past that, what "
            "happened is a discarded replication under §32 and has to be "
            "recorded as one")
    reached = [stage for stage in C.STAGE_SEQUENCE
               if tree.stage_record(stage).exists()]
    if reached:
        raise IntegrityError(
            f"{tree.model_key} holds stage records {reached}; a verdict that "
            "something downstream was computed from is not retirable")

    target = (tree.superseded_dir(P.APPARATUS_FAULT_DIRNAME) / record_hash)
    target.mkdir(parents=True, exist_ok=True)
    rows_before = transitions.transition_rows(tree)
    record = {
        "kind": "APPARATUS_FAULT",
        "study_id": tree.context.study_id,
        "model_key": tree.model_key,
        "retired_record": tree.terminal_report.name,
        "retired_record_hash": record_hash,
        "retired_status": payload.get("status"),
        "retired_gate": payload.get("gate"),
        "retired_producing_commit": payload.get("producing_commit"),
        "retired_payload": payload,
        "retired_transition_rows": [
            {"timestamp": row.get("timestamp"), "outcome": row.get("outcome"),
             "record_hash": row.get("record_hash")}
            for row in rows_before],
        "reason": reason,
        "defect": defect,
        "amendment": dict(amendment),
        "why_not_a_scientific_outcome":
            "§18 stage 1's readiness verdict is a statement about outstanding "
            "researcher work and about the apparatus. This one was reached "
            "with both governed documents present and ADOPTED at the commit "
            "the record itself names, with no manifest and no generated row "
            "in the study; it carries no evidence about the model it was "
            "recorded against",
        "preconditions_verified": {
            "record_hash_matches": True,
            "signature_verifies": True,
            "gate_is_stage_one": True,
            "status_is_a_readiness_status": True,
            "no_registration_manifest": True,
            "behavioural_rows_in_study": rows,
            "stage_records_for_this_replication": reached,
        },
        "retained_at": str(target),
        "nothing_deleted":
            "the signed report moves byte-identical into superseded/, in both "
            "roots; the transition log is append-only and keeps every row the "
            "failed attempt wrote",
        "producing_commit": producing_commit,
        "decided_by": decided_by,
        "decided_on": decided_on,
        "retired_at": now(),
    }
    shutil.move(str(report), str(target / tree.terminal_report.name))
    durable_report = tree.durable / tree.terminal_report.name
    durable_target = (tree.durable / P.SUPERSEDED_DIRNAME
                      / P.APPARATUS_FAULT_DIRNAME / record_hash)
    if durable_report.exists():
        durable_target.mkdir(parents=True, exist_ok=True)
        shutil.move(str(durable_report),
                    str(durable_target / tree.terminal_report.name))
    fs.write_json_once(target / P.APPARATUS_FAULT_RECORD, record)
    durable_target.mkdir(parents=True, exist_ok=True)
    store.replicate(target, durable_target)
    store.assert_replicated(target, durable_target)
    transitions.log_transition(
        tree, stage=C.STAGE_REGISTERED, outcome="RETIRED",
        producing_commit=producing_commit, environment_digest="",
        detail={"kind": "APPARATUS_FAULT",
                "retired_record_hash": record_hash,
                "retired_status": payload.get("status"),
                "amendment": dict(amendment),
                "retained_at": str(target)})
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
