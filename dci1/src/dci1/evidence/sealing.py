"""Addendum-A storage invariants: append-only cache, stage locks, sealing,
manifests, the study manifest, and raw-layer replication (reconciliation
R09–R15, R22–R25).

* The raw cache is opened with ``O_APPEND`` and written one complete record
  per append; existing bytes are never rewritten. Each record carries a
  ``record_hash`` over its own payload.
* Writes to one (model, freeze_id, stage) are serialised through a
  non-blocking ``flock``; a second concurrent writer is refused.
* On acceptance a stage's ``MANIFEST.jsonl`` (sha256, byte_length,
  record_count per file) is written, its checksum recorded, and ``_SEALED``
  created; every subsequent write to a sealed stage is refused.
"""
from __future__ import annotations

import datetime
import fcntl
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from dci1.evidence.layout import RAW_LAYERS, StudyTree
from dci1.evidence.store import (
    atomic_write,
    read_json,
    verify_durable_copy,
    write_json,
)
from dci1.protocol.constants import ProtocolError
from dci1.protocol.hashing import sha_text

SEAL_MARKER = "_SEALED"
MANIFEST_NAME = "MANIFEST.jsonl"
#: A commit id as ``git rev-parse`` prints it (SHA-1 or SHA-256 repositories).
COMMIT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


def utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def writer_identity(repo_root: Path | None = None) -> dict[str, Any]:
    """The source revision an artifact is written from (R18, R20).

    Fail closed: unless both Git commands exit 0 and HEAD is a commit id, the
    identity is an empty commit with ``writer_dirty = True``, which
    ``provenance.require_registered_writer`` refuses. A failed command prints
    nothing, and reading that silence as a clean tree would let a registered
    artifact name no source revision.
    """
    root = repo_root or Path(__file__).resolve().parents[4]
    unknown = {"writer_commit": "", "writer_dirty": True}
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True, timeout=30)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                                capture_output=True, text=True, timeout=30)
    except Exception:                                    # noqa: BLE001
        return unknown
    commit = head.stdout.strip()
    if (head.returncode != 0 or status.returncode != 0
            or not COMMIT_ID.fullmatch(commit)):
        return unknown
    return {"writer_commit": commit,
            "writer_dirty": bool(status.stdout.strip())}


def artifact_header(tree: StudyTree, *, model_id: str, schema_name: str,
                    schema_version: str, freeze_record_hash: str,
                    writer: dict[str, Any] | None = None) -> dict[str, Any]:
    """The R18 metadata header carried by every artifact."""
    writer = writer if writer is not None else writer_identity()
    return {
        "study_id": tree.study_id,
        "model_id": model_id,
        "freeze_id": tree.freeze_id,
        "freeze_record_hash": freeze_record_hash,
        "schema_name": schema_name,
        "schema_version": schema_version,
        "addendum_version": "A-1.0",
        "writer_commit": writer["writer_commit"],
        "writer_dirty": writer["writer_dirty"],
        "created_at_utc": utc_now(),
    }


class StageLock:
    """Non-blocking exclusive lock on one (model, freeze_id, stage) (R13)."""

    def __init__(self, tree: StudyTree, stage: str):
        self.path = tree.root / f".lock_{stage}"
        self._handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w")
        try:
            fcntl.flock(self._handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self._handle.close()
            raise ProtocolError(
                f"stage lock {self.path} is held — concurrent writers to one "
                f"stage are refused (Addendum A)") from error
        self._handle.write(str(os.getpid()))
        self._handle.flush()
        return self

    def __exit__(self, *_exc):
        fcntl.flock(self._handle, fcntl.LOCK_UN)
        self._handle.close()


def is_sealed(stage_dir: Path) -> bool:
    return (Path(stage_dir) / SEAL_MARKER).exists()


def assert_stage_unsealed(stage_dir: Path) -> None:
    if is_sealed(stage_dir):
        raise ProtocolError(
            f"stage {stage_dir} is sealed; every subsequent write is refused")
    # Only `seal_stage` writes a manifest, so a manifest means the stage was
    # sealed, or a seal was interrupted. Removing the marker must not reopen it.
    if (Path(stage_dir) / MANIFEST_NAME).exists():
        raise ProtocolError(
            f"stage {stage_dir} has a {MANIFEST_NAME} but no {SEAL_MARKER} "
            "marker; a sealed stage is not reopened by removing its marker, "
            "and every write is refused")


class CacheWriter:
    """The append-only raw-generation cache (R10–R12).

    Opened ``O_APPEND``; one complete newline-terminated record per append;
    duplicate identities refused; each record stamped with ``record_hash``.
    """

    def __init__(self, path: Path, id_field: str = "row_id"):
        self.path = Path(path)
        self.id_field = id_field

    def existing_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        return {r[self.id_field] for r in self.rows()}

    def rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open() as handle:
            for line in handle:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def append(self, rows: list[dict[str, Any]]) -> int:
        assert_stage_unsealed(self.path.parent)
        rows = list(rows)
        fresh = [r[self.id_field] for r in rows]
        if len(set(fresh)) != len(fresh):
            raise ProtocolError(f"{self.path}: duplicate identities in batch")
        clash = set(fresh) & self.existing_ids()
        if clash:
            raise ProtocolError(
                f"{self.path}: identities already present "
                f"({sorted(clash)[:3]}…) — the cache is append-once")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            for row in rows:
                stamped = dict(row)
                stamped["record_hash"] = sha_text(
                    json.dumps(row, sort_keys=True))
                payload = (json.dumps(stamped, sort_keys=True) + "\n").encode()
                os.write(fd, payload)              # one complete record
            os.fsync(fd)
        finally:
            os.close(fd)
        return len(rows)

    def verify_hashes(self) -> None:
        for i, stamped in enumerate(self.rows()):
            row = {k: v for k, v in stamped.items() if k != "record_hash"}
            if sha_text(json.dumps(row, sort_keys=True)) != \
                    stamped.get("record_hash"):
                raise ProtocolError(
                    f"{self.path}: record {i} fails its record_hash — "
                    f"stored evidence was mutated")


def _file_entry(path: Path, base: Path) -> dict[str, Any]:
    from dci1.evidence.store import sha_bytes

    data = path.read_bytes()
    if path.suffix == ".jsonl":
        record_count = sum(1 for line in data.decode("utf-8").splitlines()
                           if line.strip())
    else:
        record_count = 1
    return {"path": str(path.relative_to(base)),
            "sha256": sha_bytes(data),
            "byte_length": len(data),
            "record_count": record_count}


def seal_stage(tree: StudyTree, stage: str) -> dict[str, Any]:
    """Write the stage manifest, record its checksum, create ``_SEALED``."""
    stage_dir = tree.stage_dir(stage)
    assert_stage_unsealed(stage_dir)
    entries = [
        _file_entry(p, stage_dir)
        for p in sorted(stage_dir.rglob("*"))
        if p.is_file() and p.name not in (MANIFEST_NAME, SEAL_MARKER)]
    manifest_path = stage_dir / MANIFEST_NAME
    text = "".join(json.dumps(e, sort_keys=True) + "\n" for e in entries)
    atomic_write(manifest_path, text)
    checksum = sha_text(text)
    atomic_write(stage_dir / SEAL_MARKER,
                 json.dumps({"sealed_at_utc": utc_now(),
                             "manifest_sha256": checksum,
                             "files": len(entries)}, indent=2,
                            sort_keys=True))
    return {"stage": stage, "files": len(entries),
            "manifest_sha256": checksum}


def verify_stage(tree: StudyTree, stage: str) -> dict[str, Any]:
    """Recompute every hash/count in a sealed stage; raise on mismatch.

    The seal marker is mandatory. It carries the manifest's checksum, so a
    manifest without one is unverified, and a stage whose marker was removed
    is refused rather than reported unsealed.
    """
    stage_dir = tree.stage_dir(stage)
    manifest_path = stage_dir / MANIFEST_NAME
    if not manifest_path.exists():
        raise ProtocolError(f"{stage_dir}: no stage manifest")
    if not is_sealed(stage_dir):
        raise ProtocolError(
            f"{stage_dir}: {MANIFEST_NAME} without its {SEAL_MARKER} marker; "
            "the seal was removed or never completed, and the stage is not "
            "verified")
    try:
        sealed_checksum = json.loads(
            (stage_dir / SEAL_MARKER).read_text())["manifest_sha256"]
    except (ValueError, KeyError, TypeError) as error:
        raise ProtocolError(
            f"{stage_dir}: unreadable {SEAL_MARKER} marker") from error
    text = manifest_path.read_text()
    if sha_text(text) != sealed_checksum:
        raise ProtocolError(f"{stage_dir}: manifest fails its sealed checksum")
    listed = {}
    for line in text.splitlines():
        if line.strip():
            entry = json.loads(line)
            listed[entry["path"]] = entry
    present = {str(p.relative_to(stage_dir)) for p in stage_dir.rglob("*")
               if p.is_file() and p.name not in (MANIFEST_NAME, SEAL_MARKER)}
    missing = set(listed) - present
    extra = present - set(listed)
    if missing or extra:
        raise ProtocolError(
            f"{stage_dir}: manifest/file divergence "
            f"(missing={sorted(missing)[:3]}, extra={sorted(extra)[:3]})")
    for rel, entry in listed.items():
        actual = _file_entry(stage_dir / rel, stage_dir)
        if actual != entry:
            raise ProtocolError(
                f"{stage_dir / rel}: differs from its manifest entry "
                f"(recorded {entry['sha256'][:10]}, "
                f"actual {actual['sha256'][:10]})")
    return {"stage": stage, "files": len(listed), "sealed": True}


def write_study_manifest(tree: StudyTree,
                         freeze_record_hash: str | None,
                         extra: dict[str, Any] | None = None) -> Path:
    """Hash every stage manifest into study_manifest.json (R23)."""
    stages = {}
    for stage in ("prompts", "cache", "selection", "masking"):
        manifest = tree.stage_dir(stage) / MANIFEST_NAME
        if manifest.exists():
            stages[stage] = sha_text(manifest.read_text())
    payload = {"study_id": tree.study_id, "model_slug": tree.model_slug,
               "freeze_id": tree.freeze_id,
               "freeze_record_hash": freeze_record_hash,
               "stage_manifest_sha256": stages,
               "written_at_utc": utc_now()}
    if extra:
        payload.update(extra)
    write_json(tree.study_manifest, payload)
    return tree.study_manifest


def replicate_raw_layers(tree: StudyTree) -> dict[str, Any]:
    """Replicate prompts/cache/selection to durable storage and record it
    (R25). Selection and scoring refuse to run without this record."""
    from dci1.evidence.store import mirror_to_durable

    replicated = {}
    for layer in RAW_LAYERS:
        src = tree.root / layer
        if src.exists():
            replicated[layer] = len(mirror_to_durable(
                src, tree.durable_root / layer))
    record = {"replicated_at_utc": utc_now(),
              "replication_target_id": "durable_root_local",
              "layers": replicated}
    write_json(tree.root / "integrity" / "replication.json", record)
    return record


def assert_replicated(tree: StudyTree, *layers: str) -> None:
    """Selection and scoring proceed only on raw layers whose durable copy
    exists, is intact and matches the working layer (R25).

    The receipt says a replication happened once. The copy is what makes the
    raw evidence recoverable, so every named layer's copy is checked on each
    call (``store.verify_durable_copy``). A receipt whose copy was deleted,
    corrupted or outgrown is refused.
    """
    path = tree.root / "integrity" / "replication.json"
    if not path.exists():
        raise ProtocolError(
            "raw layers are not replicated to durable storage; selection and "
            "scoring refuse to proceed (Addendum A R25)")
    record = read_json(path)
    for layer in layers:
        if layer not in record.get("layers", {}):
            raise ProtocolError(
                f"raw layer {layer!r} has no replication record (R25)")
        try:
            verify_durable_copy(tree.root / layer, tree.durable_root / layer)
        except ProtocolError as error:
            raise ProtocolError(
                f"raw layer {layer!r} has a replication record but no "
                f"current durable copy; selection and scoring refuse to "
                f"proceed (R25): {error}") from error
