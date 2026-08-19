"""Engine integrity (item 62): signatures, cross-process writer
serialization, dirty-worktree refusal, invoked-source membership, uv
provenance, durable restoration, write-once storage, and artifact-state
monotonicity."""
from __future__ import annotations

import json
import multiprocessing
import subprocess
from pathlib import Path

import pytest

from dci1v3.engine import fs, gitinfo, store
from dci1v3.engine.artifacts import artifact_states, record_state
from dci1v3.engine.context import synthetic_context
from dci1v3.engine.environment import dependency_digest
from dci1v3.engine.locks import WriterLock
from dci1v3.engine.paths import model_tree
from dci1v3.engine.signing import (
    create_signing_key,
    sign_payload,
    verify_signed,
)
from dci1v3.errors import IntegrityError, ProtocolError, V3Error


def test_sign_and_verify_roundtrip(tmp_path):
    key = tmp_path / "key"
    create_signing_key(key)
    record = sign_payload({"a": 1}, key)
    assert verify_signed(record, key) == {"a": 1}


def test_tampered_payload_and_signature_fail(tmp_path):
    key = tmp_path / "key"
    create_signing_key(key)
    record = sign_payload({"a": 1}, key)
    tampered = {**record, "payload": {"a": 2}}
    with pytest.raises(IntegrityError, match="hash"):
        verify_signed(tampered, key)
    forged = {**record, "payload": {"a": 2},
              "record_hash": sign_payload({"a": 2}, key)["record_hash"]}
    forged["signature"] = "0" * 64
    with pytest.raises(IntegrityError, match="signature"):
        verify_signed(forged, key)


def test_signing_key_write_once(tmp_path):
    create_signing_key(tmp_path / "key")
    with pytest.raises(FileExistsError):
        create_signing_key(tmp_path / "key")


def _hold_lock(lock_dir, acquired, release):
    with WriterLock(Path(lock_dir), "s", "m", "op"):
        acquired.set()
        release.wait(timeout=30)


def test_writer_lock_cross_process(tmp_path):
    acquired = multiprocessing.Event()
    release = multiprocessing.Event()
    proc = multiprocessing.Process(
        target=_hold_lock, args=(str(tmp_path), acquired, release))
    proc.start()
    assert acquired.wait(timeout=10)
    with pytest.raises(IntegrityError, match="held by another process"):
        with WriterLock(tmp_path, "s", "m", "op"):
            pass
    release.set()
    proc.join(timeout=10)
    with WriterLock(tmp_path, "s", "m", "op"):
        pass


def test_dirty_worktree_refusal(synthetic_repo, tmp_path):
    gitinfo.assert_clean_worktree(synthetic_repo)
    marker = synthetic_repo / "untracked.txt"
    marker.write_text("dirty")
    try:
        with pytest.raises(IntegrityError, match="dirty"):
            gitinfo.assert_clean_worktree(synthetic_repo)
    finally:
        marker.unlink()


def test_invoked_sources_belong_to_commit(synthetic_repo):
    commit = gitinfo.head_commit(synthetic_repo)
    report = gitinfo.assert_sources_in_commit(synthetic_repo, commit)
    assert report["sources_verified"] > 40


def test_source_membership_detects_divergence(tmp_path, synthetic_repo):
    """A commit whose blob differs from the loaded bytes is refused."""
    from tests_v3.conftest import build_synthetic_repo
    repo = build_synthetic_repo(tmp_path)
    target = repo / "dci1" / "src" / "dci1v3" / "errors.py"
    target.write_text(target.read_text() + "\n# drift\n")
    subprocess.run(["git", "-C", str(repo), "commit", "-aqm", "drift"],
                   check=True)
    commit = gitinfo.head_commit(repo)
    with pytest.raises(IntegrityError, match="differs from commit"):
        gitinfo.assert_sources_in_commit(repo, commit)


def test_uv_provenance_fail_closed(synthetic_repo, tmp_path):
    ctx = synthetic_context(tmp_path / "study", synthetic_repo)
    digest = dependency_digest(ctx)
    assert digest["lockfile_hash"] and digest["export_hash"]

    empty = tmp_path / "empty-deps"
    empty.mkdir()
    (empty / "uv.lock").write_text("   ")
    (empty / "requirements-frozen.txt").write_text("numpy==2.5.2")
    bad = ctx.__class__(**{**ctx.__dict__,
                           "deps_lock_path": empty / "uv.lock"})
    with pytest.raises(IntegrityError, match="empty"):
        dependency_digest(bad)
    missing = ctx.__class__(**{**ctx.__dict__,
                               "deps_lock_path": empty / "absent"})
    with pytest.raises(IntegrityError, match="missing"):
        dependency_digest(missing)


def test_dependency_change_alters_digest(synthetic_repo, tmp_path):
    ctx = synthetic_context(tmp_path / "study", synthetic_repo)
    before = dependency_digest(ctx)["dependency_digest"]
    alt = tmp_path / "alt"
    alt.mkdir()
    alt_lock = alt / "uv.lock"
    alt_lock.write_text(ctx.deps_lock_path.read_text() + "\n# changed\n")
    changed = ctx.__class__(**{**ctx.__dict__, "deps_lock_path": alt_lock})
    assert dependency_digest(changed)["dependency_digest"] != before


def test_write_once_and_row_hashes(tmp_path):
    fs.write_json_once(tmp_path / "a.json", {"x": 1})
    with pytest.raises(IntegrityError, match="write-once"):
        fs.write_json_once(tmp_path / "a.json", {"x": 2})
    writer = store.CacheWriter(tmp_path / "cache.jsonl")
    writer.append([{"row_id": "r1", "raw_response": "hello"}])
    with pytest.raises(IntegrityError, match="duplicate cached-draw"):
        writer.append([{"row_id": "r1", "raw_response": "again"}])
    rows = writer.rows()
    assert rows[0]["record_hash"]
    tampered = dict(rows[0])
    tampered["raw_response"] = "changed"
    (tmp_path / "cache.jsonl").write_text(
        json.dumps(tampered, sort_keys=True) + "\n")
    with pytest.raises(IntegrityError, match="hash"):
        writer.rows()


def test_durable_replicate_and_restore(tmp_path):
    src = tmp_path / "src"
    (src / "sub").mkdir(parents=True)
    (src / "sub" / "f.txt").write_text("payload")
    durable = tmp_path / "durable"
    store.replicate(src, durable)
    store.assert_replicated(src, durable)
    (src / "sub" / "f.txt").unlink()
    store.restore(durable, src)
    assert (src / "sub" / "f.txt").read_text() == "payload"
    (durable / "sub" / "f.txt").write_text("drift")
    with pytest.raises(IntegrityError, match="out of date"):
        store.assert_replicated(src, durable)


def test_artifact_state_monotonicity(registered_ctx):
    tree = model_tree(registered_ctx, "gemma-3n-e2b-it")
    path = tree.root / "artifacts" / "blob.json"
    fs.write_json(path, {"v": 1})
    kwargs = dict(artifact_id="blob", path=path,
                  artifact_type="pilot_record", stage="GATE_0_APPARATUS_PASS",
                  producing_commit="c" * 40)
    record_state(tree, state="generated", **kwargs)
    with pytest.raises(IntegrityError, match="monotonic"):
        record_state(tree, state="accepted", **kwargs)
    record_state(tree, state="committed", **kwargs)
    record_state(tree, state="accepted", **kwargs)
    record_state(tree, state="superseded", **kwargs)
    with pytest.raises(IntegrityError, match="monotonic"):
        record_state(tree, state="accepted", **kwargs)
    assert artifact_states(tree)["blob"]["state"] == "superseded"


def test_synthetic_namespace_is_structurally_separate(synthetic_repo,
                                                     tmp_path):
    from dci1v3.engine.context import DCI1_ROOT

    with pytest.raises(ProtocolError, match="outside the registered"):
        synthetic_context(DCI1_ROOT / "evidence" / "nested", synthetic_repo)
    ctx = synthetic_context(tmp_path / "study", synthetic_repo)
    assert ctx.study_id == "dci1-v3-synthetic"
    with pytest.raises(V3Error):
        ctx.__class__(**{**ctx.__dict__, "study_id": "dci1-v3"})
