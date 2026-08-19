"""Raw evidence storage (§26, §27): write-once bytes, hashed rows, durable
replication and restoration.

Raw responses are write-once immutable bytes with content hashes recorded at
write time. The cache is an O_APPEND JSONL whose rows each carry a
``record_hash``; a duplicate cached-draw identity is refused at append, before
any byte is written. Durable replication copies raw layers byte-for-byte and
restoration reproduces every committed row with matching hashes, regenerating
no model output (§27).
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Iterable

from dci1v4.engine import fs
from dci1v4.errors import IntegrityError
from dci1v4.protocol.hashing import sha_bytes


class CacheWriter:
    """Append-only cached-draw store keyed by ``row_id``."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def existing_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        return {row["row_id"] for row in fs.read_jsonl(self.path)}

    def rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = fs.read_jsonl(self.path)
        for row in rows:
            fs.verify_row_hash(row, where=row.get("row_id", "?"))
        return rows

    def append(self, rows: Iterable[dict[str, Any]]) -> int:
        have = self.existing_ids()
        payload: list[str] = []
        for row in rows:
            if row["row_id"] in have:
                raise IntegrityError(
                    f"duplicate cached-draw identity {row['row_id']!r}; "
                    f"append refused before mutation")
            have.add(row["row_id"])
            payload.append(json.dumps(fs.row_with_hash(row), sort_keys=True,
                                      ensure_ascii=False))
        if not payload:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        with os.fdopen(fd, "w") as handle:
            handle.write("\n".join(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return len(payload)


def fingerprint_tree(root: Path) -> dict[str, str]:
    root = Path(root)
    if not root.exists():
        return {}
    return {str(p.relative_to(root)): sha_bytes(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}


def replicate(source: Path, durable: Path) -> dict[str, str]:
    """Copy a tree to durable storage; verify every byte; return hashes.

    Incremental: a durable file whose bytes already match is left alone, so
    replication never re-reads write-once artifacts it already holds.
    """
    source, durable = Path(source), Path(durable)
    hashes = fingerprint_tree(source)
    for rel in hashes:
        target = durable / rel
        if target.exists() and sha_bytes(target.read_bytes()) == hashes[rel]:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / rel, target)
        if sha_bytes(target.read_bytes()) != hashes[rel]:
            raise IntegrityError(f"durable replication corrupted {rel}")
    return hashes


def assert_replicated(source: Path, durable: Path) -> None:
    src, dur = fingerprint_tree(source), fingerprint_tree(durable)
    missing = [rel for rel in src if dur.get(rel) != src[rel]]
    if missing:
        raise IntegrityError(f"durable mirror out of date for {len(missing)} "
                             f"file(s), first: {missing[0]}")


def restore(durable: Path, target: Path) -> dict[str, str]:
    """Restore a tree from durable storage byte-for-byte; regenerate nothing."""
    durable, target = Path(durable), Path(target)
    hashes = fingerprint_tree(durable)
    if not hashes:
        raise IntegrityError(f"nothing to restore from {durable}")
    for rel, digest in hashes.items():
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(durable / rel, dest)
        if sha_bytes(dest.read_bytes()) != digest:
            raise IntegrityError(f"restoration corrupted {rel}")
    return hashes
