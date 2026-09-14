"""Fail-closed regressions for the recovered v2 evidence package (PR #41).

`src/dci1/evidence` was never committed until PR #41, so it was reviewed late.
The review found four checks that trusted a stand-in for the invariant they
guard: a replication receipt instead of the durable copy, an optional seal
marker, a freeze binding skipped when its record was missing, and a failed Git
command read as a clean tree. Each test builds a tree with the production
helpers, tampers with it, and asserts the refusal. These are not part of the
Addendum A §6 battery (SA-, SP-, SM- ids), which is unchanged.
"""
import json
import subprocess

import pytest

pytestmark = pytest.mark.cpu

from helpers import SPEC
from helpers_addendum import full_tree

from dci1 import flow
from dci1.evidence import provenance as prov
from dci1.evidence import sealing
from dci1.evidence.sealing import (
    CacheWriter,
    assert_replicated,
    replicate_raw_layers,
    seal_stage,
    verify_stage,
    write_study_manifest,
    writer_identity,
)
from dci1.evidence.store import sha_bytes
from dci1.evidence.verify import verify_evidence
from dci1.protocol.constants import ProtocolError

RAW = ("prompts", "cache")
UNKNOWN_WRITER = {"writer_commit": "", "writer_dirty": True}


# ------------------------------------- 1. a receipt needs its durable copy
def _replicated(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    assert_replicated(tree, *RAW)
    receipt = json.loads((tree.root / "integrity" / "replication.json")
                         .read_text())
    assert set(RAW) <= set(receipt["layers"])
    return tree, cells, config


def test_a_deleted_durable_layer_is_refused_despite_its_receipt(tmp_path):
    tree, _cells, _config = _replicated(tmp_path)
    for path in sorted((tree.durable_root / "cache").iterdir()):
        path.unlink()
    (tree.durable_root / "cache").rmdir()
    with pytest.raises(ProtocolError, match="does not exist"):
        assert_replicated(tree, *RAW)


def test_a_deleted_durable_file_is_refused(tmp_path):
    tree, _cells, _config = _replicated(tmp_path)
    (tree.durable_root / "prompts" / "cells.jsonl").unlink()
    with pytest.raises(ProtocolError, match="stale"):
        assert_replicated(tree, *RAW)


def test_corrupted_durable_bytes_are_refused(tmp_path):
    tree, _cells, _config = _replicated(tmp_path)
    copy = tree.durable_root / "cache" / "generations.jsonl"
    copy.write_bytes(copy.read_bytes().replace(b"However", b"Xowever", 1))
    with pytest.raises(ProtocolError, match="fail their recorded hash"):
        assert_replicated(tree, *RAW)


def test_a_corrupted_copy_with_a_rewritten_sidecar_is_still_refused(tmp_path):
    """A matching sidecar hides corruption from a restore, not from the
    comparison with the working layer."""
    tree, _cells, _config = _replicated(tmp_path)
    copy = tree.durable_root / "cache" / "generations.jsonl"
    data = copy.read_bytes().replace(b"However", b"Xowever", 1)
    copy.write_bytes(data)
    copy.with_suffix(".jsonl.sha256").write_text(sha_bytes(data))
    with pytest.raises(ProtocolError, match="differs from durable copy"):
        assert_replicated(tree, *RAW)


def test_a_durable_file_without_its_sidecar_is_refused(tmp_path):
    tree, _cells, _config = _replicated(tmp_path)
    (tree.durable_root / "cache" / "generations.jsonl.sha256").unlink()
    with pytest.raises(ProtocolError, match="no hash sidecar"):
        assert_replicated(tree, *RAW)


def test_a_stale_copy_is_refused_until_the_layer_is_replicated_again(tmp_path):
    tree, cells, config = _replicated(tmp_path)
    late = tree.prompts_dir / "late.jsonl"
    late.write_text('{"written": "after replication"}\n')
    with pytest.raises(ProtocolError, match="stale"):
        assert_replicated(tree, *RAW)
    # and the gates that depend on it refuse too
    with pytest.raises(ProtocolError, match="no current durable copy"):
        flow.select_primary(tree, SPEC, cells, stream="confirmatory",
                            config=config)
    replicate_raw_layers(tree)
    assert_replicated(tree, *RAW)


# --------------------------------------------- 2. the seal is mandatory
def test_a_removed_seal_marker_fails_verification(tmp_path):
    tree, *_ = full_tree(tmp_path)
    assert verify_stage(tree, "cache")["sealed"] is True
    (tree.cache_dir / "_SEALED").unlink()
    with pytest.raises(ProtocolError, match="without its _SEALED marker"):
        verify_stage(tree, "cache")
    with pytest.raises(ProtocolError, match="without its _SEALED marker"):
        verify_evidence(tree)


def test_a_removed_seal_marker_does_not_reopen_the_stage(tmp_path):
    tree, *_ = full_tree(tmp_path)
    before = tree.cache_file.read_bytes()
    (tree.cache_dir / "_SEALED").unlink()
    with pytest.raises(ProtocolError, match="no _SEALED marker"):
        CacheWriter(tree.cache_file).append([{"row_id": "reopened"}])
    with pytest.raises(ProtocolError, match="no _SEALED marker"):
        seal_stage(tree, "cache")
    assert tree.cache_file.read_bytes() == before
    assert not (tree.cache_dir / "_SEALED").exists()


def test_an_unreadable_seal_marker_fails_verification(tmp_path):
    tree, *_ = full_tree(tmp_path)
    (tree.cache_dir / "_SEALED").write_text("not json")
    with pytest.raises(ProtocolError, match="unreadable _SEALED marker"):
        verify_stage(tree, "cache")


# ------------------------------- 3. a bound freeze record is mandatory
def _bound(tmp_path):
    tree, _blocks, _cells, _config, record_hash = full_tree(tmp_path)
    write_study_manifest(tree, record_hash)
    assert verify_evidence(tree)["study_manifest_verified"]
    return tree


def test_a_missing_bound_freeze_record_fails_verification(tmp_path):
    tree = _bound(tmp_path)
    tree.freeze_record.unlink()
    with pytest.raises(ProtocolError, match="no freeze record"):
        verify_evidence(tree)


@pytest.mark.parametrize("content", ["", "{not json", "[1, 2]", "\xff\xfe"])
def test_an_unreadable_bound_freeze_record_fails_verification(tmp_path,
                                                             content):
    tree = _bound(tmp_path)
    tree.freeze_record.write_bytes(content.encode("latin-1"))
    with pytest.raises(ProtocolError, match="unreadable"):
        verify_evidence(tree)


def test_a_changed_bound_freeze_record_fails_verification(tmp_path):
    tree = _bound(tmp_path)
    record = json.loads(tree.freeze_record.read_text())
    record["TEST_RECORD"] = False
    tree.freeze_record.write_text(json.dumps(record))
    with pytest.raises(ProtocolError, match="differs from the record"):
        verify_evidence(tree)


def test_a_manifest_that_binds_no_freeze_record_needs_none(tmp_path):
    tree, *_ = full_tree(tmp_path)
    write_study_manifest(tree, None)
    tree.freeze_record.unlink()
    assert verify_evidence(tree)["ok"]


# ------------------------------- 4. an unknown writer is a dirty writer
def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _committed_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "a.txt").write_text("a")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-q", "-m", "one")
    return repo, _git(repo, "rev-parse", "HEAD")


def test_a_committed_clean_repository_is_a_clean_writer(tmp_path):
    repo, head = _committed_repo(tmp_path)
    assert writer_identity(repo) == {"writer_commit": head,
                                     "writer_dirty": False}
    (repo / "b.txt").write_text("b")
    assert writer_identity(repo) == {"writer_commit": head,
                                     "writer_dirty": True}


def test_a_directory_outside_any_repository_is_an_unknown_writer(
        tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    outside = tmp_path / "not-a-repository"
    outside.mkdir()
    assert writer_identity(outside) == UNKNOWN_WRITER
    with pytest.raises(ProtocolError, match="dirty"):
        prov.require_registered_writer(writer=writer_identity(outside))


def test_a_repository_without_a_commit_is_an_unknown_writer(tmp_path):
    repo = tmp_path / "empty"
    repo.mkdir()
    _git(repo, "init", "-q")
    assert writer_identity(repo) == UNKNOWN_WRITER


@pytest.mark.parametrize("failing", ["rev-parse", "status"])
def test_a_nonzero_git_exit_is_an_unknown_writer(tmp_path, monkeypatch,
                                                 failing):
    """Both commands print nothing on this failure, which the old code read
    as a clean tree."""
    repo, _head = _committed_repo(tmp_path)
    real = subprocess.run

    def run(cmd, *args, **kwargs):
        if cmd[:2] == ["git", failing]:
            return subprocess.CompletedProcess(cmd, 128, stdout="",
                                               stderr="fatal: refused")
        return real(cmd, *args, **kwargs)

    monkeypatch.setattr(sealing.subprocess, "run", run)
    assert writer_identity(repo) == UNKNOWN_WRITER


@pytest.mark.parametrize("outcome", [
    subprocess.CompletedProcess(["git"], 0, stdout="HEAD\n", stderr=""),
    subprocess.CompletedProcess(["git"], 0, stdout="", stderr=""),
    subprocess.TimeoutExpired(["git"], 30),
    FileNotFoundError("git"),
])
def test_an_invalid_commit_a_timeout_or_no_git_is_an_unknown_writer(
        tmp_path, monkeypatch, outcome):
    repo, _head = _committed_repo(tmp_path)

    def run(cmd, *args, **kwargs):
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(sealing.subprocess, "run", run)
    assert writer_identity(repo) == UNKNOWN_WRITER
