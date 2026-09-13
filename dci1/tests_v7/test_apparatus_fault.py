"""Amendment A15: a stage-1 readiness verdict is a refusal, not a verdict.

On 2026-08-26 the v6 CLI was invoked for the first time and could not run a
single stage. Three defects, all of them in the documented entry point and
none in a scientific rule:

1. **no signing key.** Every record is signed at write and verified at read,
   and nothing in the v6 CLI created the study key. v4's runner created it
   explicitly; v6's had no equivalent.
2. **``--repo-root`` never reached the runner.** ``run_registration`` defaults
   it to ``"."``, so ``assert_documents_adopted`` read the *process's working
   directory*. Invoked from ``dci1/``, both governed documents are one level
   up, and the guard correctly reported them **missing**.
3. **stage 1 was not retryable.** ``REGISTRATION_INCOMPLETE`` was a §28
   terminal status, so that false readiness failure wrote §28.3's terminal
   report and ``assert_predecessor_passed`` disabled ``gemma-3n-e2b-it``
   permanently --- before any manifest existed and before a single row had
   been generated.

The third is the one that needed an amendment, and it was a real hole rather
than an inconvenience: every entry ``signing_blockers`` can report names work
a **researcher** has to do, and ``decisions.choice()`` had always said stage 1
returns the status *until then*. If the first invocation to find any of that
outstanding kills the replication, "until then" is false and the whole blocker
vocabulary is unreachable by construction.

So the criterion did not move --- ``signing_blockers`` decides readiness
exactly as it did --- and the handling did: a readiness verdict is refused,
logged and left retryable. Everything below is about keeping that narrow. A
scientific gate's verdict is a RESULT and stays irreversible, and the recovery
path for the one pre-manifest incident refuses six different ways.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.engine.signing import sign_payload
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import MODELS
from dci1v4.protocol.hashing import sha_bytes

from dci1v7.engine import transitions
from dci1v7.engine.context import synthetic_context
from dci1v7.engine.paths import (APPARATUS_FAULT_DIRNAME, is_superseded,
                                 model_tree)
from dci1v7.protocol import constants as C
from dci1v7.protocol import manifest
from dci1v7.run import cli, registration_run
from dci1v7.run.lifecycle import ReadinessRefusal, TerminalStatus

MODEL = "gemma-3n-e2b-it"
COMMIT = "0" * 40
AMENDMENT = {"id": "A15", "document": "user-notes/DCI1_preregistration_v7.md"}
REASON = "a caller's own configuration defect, not a verdict about this model"
DEFECT = "the CLI did not forward --repo-root to run_registration"


@pytest.fixture
def adopted_repo(v7_repo):
    """A root where both governed documents exist and declare ADOPTED."""
    return v7_repo


@pytest.fixture
def draft_repo(tmp_path_factory):
    """A root where they exist and declare themselves drafts.

    Not a git repository and it does not need to be: a readiness refusal
    happens before anything reads a commit, which is itself part of what is
    under test --- an unready study is refused without touching provenance.
    """
    root = tmp_path_factory.mktemp("draft-repo")
    prereg = root / "user-notes" / "DCI1_preregistration_v7.md"
    prereg.parent.mkdir(parents=True, exist_ok=True)
    prereg.write_text("# not the study's commitment\n\n"
                      f"status: {manifest.DRAFT_MARKER}\n")
    spec = root / "dci1" / "reports" / "dci1v7" / "reference_design_spec.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps({"_status": manifest.DRAFT_MARKER}) + "\n")
    return root


def _tree(tmp_path, model_key=MODEL):
    context = synthetic_context(tmp_path)
    tree = model_tree(context, model_key)
    tree.root.mkdir(parents=True, exist_ok=True)
    cli.ensure_signing_key(tree)
    return tree


def _register(tree, repo_root, **kwargs):
    return registration_run.run_registration(
        tree, producing_commit=COMMIT, adoption={"status": "SYNTHETIC"},
        repo_root=repo_root, environment_digest="test", **kwargs)


def _historical_terminal_report(tree) -> str:
    """The record the 2026-08-26 fault wrote, reproduced byte-for-byte-alike.

    It is signed directly rather than through ``write_terminal_report``
    because that function now **refuses** a readiness status --- which is the
    amendment. The record on the real evidence tree was written by code that
    no longer exists, so a test about recovering it has to be able to produce
    one the same way.
    """
    payload = {
        "status": "REGISTRATION_INCOMPLETE", "model_key": tree.model_key,
        "gate": C.STAGE_REGISTERED, "criterion": "§34",
        "observed": [{"kind": "DRAFT_DOCUMENT", "n": 2}],
        "producing_commit": COMMIT,
        "strongest_permissible_statement": C.TERMINAL_SENTENCE,
        "terminal_sentence": C.TERMINAL_SENTENCE}
    tree.terminal_report.parent.mkdir(parents=True, exist_ok=True)
    tree.terminal_report.write_text(json.dumps(
        sign_payload(payload, tree.context.signing_key_path),
        indent=2, sort_keys=True) + "\n")
    tree.durable.mkdir(parents=True, exist_ok=True)
    (tree.durable / tree.terminal_report.name).write_bytes(
        tree.terminal_report.read_bytes())
    return sha_bytes(tree.terminal_report.read_bytes())


def _retire(tree, record_hash, **kwargs):
    return registration_run.retire_apparatus_fault(
        tree, record_hash=record_hash, reason=REASON, defect=DEFECT,
        amendment=AMENDMENT, producing_commit=COMMIT,
        decided_by="researcher", decided_on="2026-08-26", **kwargs)


# ------------------------------------------------- the refusal, prospectively

def test_a_readiness_blocker_refuses_and_writes_no_scientific_outcome(
        tmp_path, draft_repo):
    """The whole amendment, in one call.

    It fails closed, it is logged, and the evidence tree is exactly where it
    was: no stage record, and --- the part that changed --- no terminal
    report and therefore no replication mechanically disabled.
    """
    tree = _tree(tmp_path)
    with pytest.raises(ReadinessRefusal) as refusal:
        _register(tree, draft_repo)
    assert refusal.value.status == "REGISTRATION_INCOMPLETE"
    assert refusal.value.gate == C.STAGE_REGISTERED
    assert [b["kind"] for b in refusal.value.observed] == ["DRAFT_DOCUMENT"]

    assert not tree.terminal_report.exists()
    assert not tree.stage_record(C.STAGE_REGISTERED).exists()
    assert transitions.terminal_status(tree) is None

    row = transitions.transition_rows(tree)[-1]
    assert row["outcome"] == "REFUSED"
    assert row["detail"]["kind"] == "READINESS_REFUSAL"
    assert row["detail"]["retryable"] is True
    assert row["detail"]["terminal"] is False
    assert row["detail"]["status"] == "REGISTRATION_INCOMPLETE"


def test_stage_one_can_be_attempted_again_once_the_blocker_is_gone(
        tmp_path, draft_repo, adopted_repo):
    """"Until then" is now true.

    The same replication, the same tree, the same command: the first attempt
    is refused because the documents declare themselves drafts and the second
    passes because they do not. Before A15 the first attempt ended it.
    """
    tree = _tree(tmp_path)
    with pytest.raises(ReadinessRefusal):
        _register(tree, draft_repo)
    outcome = _register(tree, adopted_repo)
    assert outcome.outcome == "PASS"
    assert tree.stage_record(C.STAGE_REGISTERED).exists()
    outcomes = [r["outcome"] for r in transitions.transition_rows(tree)]
    assert outcomes == ["REFUSED", "PASS"]


def test_stage_one_cannot_be_repeated_after_a_successful_registration(
        tmp_path, adopted_repo):
    """Retryable is not repeatable. §18's write-once rule is untouched."""
    tree = _tree(tmp_path)
    _register(tree, adopted_repo)
    with pytest.raises(IntegrityError, match="write-once"):
        _register(tree, adopted_repo)


def test_a_refusal_does_not_become_retryable_for_a_scientific_gate():
    """The narrowness, asserted at the constructor.

    A readiness refusal exists at stage 1 and carries stage 1's status. Give
    it any other gate, or any §28 status, and it refuses to be constructed ---
    so there is no way to spell "retry this terminal outcome" at all.
    """
    with pytest.raises(ProtocolError, match="nowhere else"):
        ReadinessRefusal("REGISTRATION_INCOMPLETE", gate=C.STAGE_GATE2_75,
                         criterion="x", observed=None, remedy="x")
    with pytest.raises(ProtocolError, match="not a registered readiness"):
        ReadinessRefusal("REGIME_NOT_FOUND",
                         gate=C.STAGE_REGISTERED, criterion="x",
                         observed=None, remedy="x")


def test_a_readiness_status_cannot_reach_the_terminal_report(tmp_path):
    """Two independent structural refusals, and they are the point.

    §28.3's record is what ``assert_predecessor_passed`` reads to disable a
    replication forever. A readiness status cannot be raised as a
    ``TerminalStatus`` and cannot be written as a terminal report, so the
    2026-08-26 record is not reproducible by any path in the current code.
    """
    with pytest.raises(ProtocolError, match="not a registered v7 terminal"):
        TerminalStatus("REGISTRATION_INCOMPLETE", gate=C.STAGE_REGISTERED,
                       criterion="x", observed=None,
                       strongest_permissible_statement="x")
    tree = _tree(tmp_path)
    with pytest.raises(ProtocolError, match="readiness refusal"):
        transitions.write_terminal_report(tree, {
            "status": "REGISTRATION_INCOMPLETE", "model_key": tree.model_key,
            "gate": C.STAGE_REGISTERED, "criterion": "x", "observed": None,
            "producing_commit": COMMIT,
            "strongest_permissible_statement": "x"})


def test_a_scientific_terminal_is_still_written_and_still_ends_it(tmp_path):
    """§28 is not weakened anywhere. A gate's verdict is a RESULT."""
    tree = _tree(tmp_path)
    transitions.write_terminal_report(tree, {
        "status": "REGIME_NOT_FOUND", "model_key": tree.model_key,
        "gate": C.STAGE_GATE2, "criterion": "§12.4", "observed": {},
        "producing_commit": COMMIT,
        "strongest_permissible_statement": C.TERMINAL_SENTENCE})
    assert transitions.terminal_status(tree) == "REGIME_NOT_FOUND"
    with pytest.raises(IntegrityError, match="mechanically disabled"):
        transitions.assert_predecessor_passed(tree, C.STAGE_GATE3A)


# ------------------------------------------------------------ the recovery

def test_the_bad_record_blocks_the_replication_until_it_is_retired(
        tmp_path, adopted_repo):
    """The state the incident left, and the only way out of it.

    The record was written by code that no longer exists, so it is
    reconstructed here; what matters is that the *current* code refuses the
    replication while it stands and admits it once the governed retirement
    has named it.
    """
    tree = _tree(tmp_path)
    record_hash = _historical_terminal_report(tree)
    with pytest.raises(IntegrityError, match="mechanically disabled"):
        _register(tree, adopted_repo)

    record = _retire(tree, record_hash)
    assert record["kind"] == "APPARATUS_FAULT"
    assert record["retired_record_hash"] == record_hash
    assert record["retired_status"] == "REGISTRATION_INCOMPLETE"
    assert record["amendment"] == AMENDMENT

    assert _register(tree, adopted_repo).outcome == "PASS"


def test_a_retirement_that_names_the_wrong_record_refuses(tmp_path):
    """Fails closed on the hash. A retirement identifies what it retires."""
    tree = _tree(tmp_path)
    _historical_terminal_report(tree)
    with pytest.raises(IntegrityError, match="retirement names"):
        _retire(tree, "f" * 64)
    assert tree.terminal_report.exists()


def test_a_retirement_refuses_once_a_manifest_exists(tmp_path, adopted_repo):
    """Pre-manifest only. After a registration is signed, a stage-1 verdict is
    a verdict about a signed registration and §32's supersession is the route.
    """
    tree = _tree(tmp_path)
    _register(tree, adopted_repo)
    other = model_tree(tree.context, "gemma-3n-e4b-it")
    other.root.mkdir(parents=True, exist_ok=True)
    record_hash = _historical_terminal_report(other)
    with pytest.raises(IntegrityError, match="signed registration"):
        _retire(other, record_hash)


def test_a_retirement_refuses_once_a_row_exists(tmp_path):
    """Pre-observation only, counted from the filesystem rather than believed.

    The row is put under a *different* replication on purpose: the question
    is whether the STUDY has observed anything, and §6.1's firewall does not
    make one replication's generation invisible to that question.
    """
    tree = _tree(tmp_path)
    record_hash = _historical_terminal_report(tree)
    other = model_tree(tree.context, "qwen3-4b")
    rows = other.backend_runs(C.STAGE_GATE0) / "run-0" / "rows.jsonl"
    rows.parent.mkdir(parents=True, exist_ok=True)
    rows.write_text(json.dumps({"row": 1}) + "\n")
    with pytest.raises(IntegrityError, match="generated row"):
        _retire(tree, record_hash)
    assert tree.terminal_report.exists()


def test_a_retirement_cannot_revive_a_scientific_terminal(tmp_path):
    """The refusal that keeps this from being a general retry facility.

    Both halves are checked, because either alone would leave a way through:
    a §28 status at stage 1, and a readiness status attributed to a gate.
    """
    tree = _tree(tmp_path)
    transitions.write_terminal_report(tree, {
        "status": "REGIME_NOT_FOUND", "model_key": tree.model_key,
        "gate": C.STAGE_GATE2, "criterion": "§12.4", "observed": {},
        "producing_commit": COMMIT,
        "strongest_permissible_statement": C.TERMINAL_SENTENCE})
    record_hash = sha_bytes(tree.terminal_report.read_bytes())
    with pytest.raises(IntegrityError, match="a verdict at"):
        _retire(tree, record_hash)
    assert tree.terminal_report.exists()

    forged = model_tree(tree.context, "qwen3-4b-instruct-2507")
    forged.root.mkdir(parents=True, exist_ok=True)
    payload = {"status": "PREFREEZE_AUDIT_FAILURE", "gate": C.STAGE_REGISTERED,
               "model_key": forged.model_key, "criterion": "x",
               "observed": {}, "producing_commit": COMMIT,
               "strongest_permissible_statement": C.TERMINAL_SENTENCE}
    forged.terminal_report.write_text(json.dumps(
        sign_payload(payload, forged.context.signing_key_path),
        indent=2, sort_keys=True) + "\n")
    with pytest.raises(IntegrityError, match="not retirable"):
        _retire(forged, sha_bytes(forged.terminal_report.read_bytes()))


def test_a_retirement_refuses_when_something_downstream_was_computed(
        tmp_path):
    """A verdict a later stage read is not a verdict nobody acted on."""
    tree = _tree(tmp_path)
    record_hash = _historical_terminal_report(tree)
    record = tree.stage_record(C.STAGE_REGISTERED)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("{}")
    with pytest.raises(IntegrityError, match="stage records"):
        _retire(tree, record_hash)


def test_a_retirement_states_what_it_is(tmp_path):
    """A blank reason and an unnamed amendment are refused."""
    tree = _tree(tmp_path)
    record_hash = _historical_terminal_report(tree)
    for kwargs in ({"reason": ""}, {"defect": ""}, {"amendment": {}}):
        with pytest.raises(IntegrityError, match="missing"):
            registration_run.retire_apparatus_fault(
                tree, record_hash=record_hash,
                **{"reason": REASON, "defect": DEFECT,
                   "amendment": AMENDMENT, **kwargs},
                producing_commit=COMMIT, decided_by="r",
                decided_on="2026-08-26")


def test_nothing_is_deleted_and_the_attempt_stays_visible(tmp_path):
    """§32's rule, applied to a record rather than to a manifest.

    The signed report survives byte-identical in both roots, under a path
    ``is_superseded`` already excludes from every current pool; the
    append-only transition log keeps the TERMINAL row the failed attempt
    wrote; and the retirement itself is logged. Nothing about the incident
    can be read as though it did not happen.
    """
    tree = _tree(tmp_path)
    before = tree.terminal_report.read_bytes() if \
        tree.terminal_report.exists() else None
    assert before is None
    record_hash = _historical_terminal_report(tree)
    original = tree.terminal_report.read_bytes()
    transitions.log_transition(
        tree, stage=C.STAGE_REGISTERED, outcome="TERMINAL",
        producing_commit=COMMIT, environment_digest="",
        detail={"status": "REGISTRATION_INCOMPLETE"})

    record = _retire(tree, record_hash)

    retained = Path(record["retained_at"])
    assert is_superseded(retained)
    assert retained.name == record_hash
    assert retained.parent.name == APPARATUS_FAULT_DIRNAME
    kept = retained / "terminal_report.json"
    assert kept.read_bytes() == original
    assert sha_bytes(kept.read_bytes()) == record_hash
    assert not tree.terminal_report.exists()

    durable = (tree.durable / "superseded" / APPARATUS_FAULT_DIRNAME
               / record_hash / "terminal_report.json")
    assert durable.read_bytes() == original
    assert not (tree.durable / "terminal_report.json").exists()

    # the retirement record carries the retired payload verbatim, so reading
    # the fault does not require reading the file it names
    body = json.loads((retained / "apparatus_fault.json").read_text())
    assert body["retired_payload"]["status"] == "REGISTRATION_INCOMPLETE"
    assert body["reason"] == REASON and body["defect"] == DEFECT

    outcomes = [r["outcome"] for r in transitions.transition_rows(tree)]
    assert outcomes == ["TERMINAL", "RETIRED"]


def test_the_registration_that_follows_binds_the_retirement(
        tmp_path, adopted_repo):
    """The incident is inside the signature, not beside it.

    A retirement recorded next to a registration would let the study's own
    signed provenance read as though the failed attempt never occurred. It is
    a bound field, so every replication registering under this manifest ---
    and every reader of it afterwards --- sees the retired record's hash.
    """
    tree = _tree(tmp_path)
    record_hash = _historical_terminal_report(tree)
    _retire(tree, record_hash)
    _register(tree, adopted_repo)

    bound = manifest.load_manifest(tree.context)["apparatus_faults"]
    assert [f["retired_record_hash"] for f in bound["retired"]] == [
        record_hash]
    assert bound["retired"][0]["model_key"] == MODEL
    assert bound["retired"][0]["retired_status"] == "REGISTRATION_INCOMPLETE"
    assert "apparatus_faults" in manifest.REQUIRED_BINDINGS


def test_the_manifest_carries_the_field_when_there_was_no_fault(
        tmp_path, adopted_repo):
    """An honest empty value, not an absent key. A binding that appears only
    when something went wrong is a binding a reader cannot rely on."""
    tree = _tree(tmp_path)
    _register(tree, adopted_repo)
    assert manifest.load_manifest(tree.context)["apparatus_faults"][
        "retired"] == []


def test_the_whole_registered_panel_still_registers(tmp_path, adopted_repo):
    """§6.1 registers four replications and the amendment keeps all four.

    The incident cost one of them under the old rule. This is the property
    that ruling was about, asserted against the four models the registry
    actually holds rather than a list written here.
    """
    tree = _tree(tmp_path)
    record_hash = _historical_terminal_report(tree)
    _retire(tree, record_hash)
    keys = [m.model_key for m in MODELS]
    assert len(keys) == 4
    for key in keys:
        replication = model_tree(tree.context, key)
        replication.root.mkdir(parents=True, exist_ok=True)
        assert _register(replication, adopted_repo).outcome == "PASS"
        assert replication.stage_record(C.STAGE_REGISTERED).exists()
        assert transitions.terminal_status(replication) is None
