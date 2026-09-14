"""Append-once, content-hashed evidence storage with a durable mirror.

Raw generations are evidence (amendment §2.5): append-once during
construction, immutable after acceptance, content-hashed, recoverable from
durable storage, and separable from derived resampling outputs. This module
is the only writer of evidence files.

Layout (per model, under the working root)::

    <root>/<model_key>/qualification/...
    <root>/<model_key>/pilot/{pool,primary}/...
    <root>/<model_key>/calibration/...
    <root>/<model_key>/confirmatory/{pool,primary,pseudo}/...
    <root>/<model_key>/freeze/...
    <root>/<model_key>/runrecord.jsonl

The durable mirror at the durable root repeats the same relative layout; every
mirrored file carries a ``.sha256`` sidecar and is written payload-first,
sidecar-second, so a file is durably present only when its hash is. Restore
copies mirror → working and verifies every hash; verification failures raise.

The atomic-write pattern (temp sibling + fsync + os.replace) is copied from
the repository's audited storage stage; copied, not imported, to keep this
study free of the old pipeline's import-time state.
"""
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from dci1.protocol.constants import ProtocolError
from dci1.protocol.hashing import sha_text

#: Default roots. Overridable per call for tests; never via environment
#: variables (no hidden environment-dependent values, amendment §2.10).
#: All working evidence lives under one root, `dci1/evidence/`; the layout
#: inside it is `evidence/<study_id>/<model_slug>/<tree_id>/` (see
#: `evidence/layout.py` and README "Evidence layout").
EVIDENCE_ROOT = Path(__file__).resolve().parents[3] / "evidence"
DURABLE_ROOT = Path(__file__).resolve().parents[3] / "durable_root"


def atomic_write(path: Path, text: str) -> None:
    """Write whole-file atomically: temp sibling + fsync + os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Deterministic JSON: sorted keys, two-space indent (Addendum A R06)."""
    atomic_write(Path(path), json.dumps(payload, indent=2, sort_keys=True))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class AppendOnceJsonl:
    """A JSONL file whose rows are identities written exactly once.

    * a duplicate ``row_id`` is refused loudly (never silently replaced);
    * existing bytes are never rewritten — appends only;
    * every row is stamped with its own content hash at write time, so any
      later mutation of stored bytes is detectable row by row.
    """

    def __init__(self, path: Path, id_field: str = "row_id"):
        self.path = Path(path)
        self.id_field = id_field

    def existing_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        return {row[self.id_field] for row in read_jsonl(self.path)}

    def rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return read_jsonl(self.path)

    def append(self, rows: Iterable[dict[str, Any]]) -> int:
        rows = list(rows)
        seen = self.existing_ids()
        fresh_ids = [r[self.id_field] for r in rows]
        if len(set(fresh_ids)) != len(fresh_ids):
            raise ProtocolError(
                f"{self.path}: duplicate row identities within one append "
                f"batch — two writers or a bug; refusing")
        clash = set(fresh_ids) & seen
        if clash:
            raise ProtocolError(
                f"{self.path}: row identities already present: "
                f"{sorted(clash)[:5]}{'…' if len(clash) > 5 else ''} — "
                f"append-once storage never rewrites evidence")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as handle:
            for row in rows:
                stamped = dict(row)
                stamped["row_sha256"] = sha_text(
                    json.dumps(row, sort_keys=True))
                handle.write(json.dumps(stamped, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return len(rows)

    def verify_hashes(self) -> None:
        """Every stored row's bytes still match its recorded content hash."""
        for i, stamped in enumerate(self.rows()):
            row = {k: v for k, v in stamped.items() if k != "row_sha256"}
            expect = stamped.get("row_sha256")
            actual = sha_text(json.dumps(row, sort_keys=True))
            if expect != actual:
                raise ProtocolError(
                    f"{self.path}: row {i} ({row.get(self.id_field)!r}) fails "
                    f"its content hash — stored evidence was mutated")


def _iter_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.name.endswith(".sha256"):
            yield path


def sha_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def mirror_to_durable(working: Path, durable: Path) -> dict[str, str]:
    """Copy working → durable (payload first, hash sidecar second). Binary."""
    written = {}
    for src in _iter_files(Path(working)):
        rel = src.relative_to(working)
        dst = Path(durable) / rel
        data = src.read_bytes()
        digest = sha_bytes(data)
        atomic_write_bytes(dst, data)
        atomic_write(dst.with_suffix(dst.suffix + ".sha256"), digest)
        written[str(rel)] = digest
    return written


def restore_from_durable(durable: Path, working: Path) -> dict[str, str]:
    """Copy durable → working, verifying every recorded hash; fail closed."""
    restored = {}
    durable = Path(durable)
    if not durable.exists():
        raise ProtocolError(f"durable root {durable} does not exist")
    for src in _iter_files(durable):
        sidecar = src.with_suffix(src.suffix + ".sha256")
        if not sidecar.exists():
            raise ProtocolError(f"{src}: durable file has no hash sidecar")
        data = src.read_bytes()
        expect = sidecar.read_text().strip()
        actual = sha_bytes(data)
        if actual != expect:
            raise ProtocolError(
                f"{src}: durable bytes fail their recorded hash "
                f"({actual[:12]} != {expect[:12]})")
        rel = src.relative_to(durable)
        atomic_write_bytes(Path(working) / rel, data)
        restored[str(rel)] = actual
    return restored


def verify_working_matches_durable(working: Path, durable: Path) -> None:
    """Every durable file exists in working with identical hash."""
    for src in _iter_files(Path(durable)):
        rel = src.relative_to(durable)
        twin = Path(working) / rel
        if not twin.exists():
            raise ProtocolError(f"{twin}: present in durable, absent locally")
        if sha_bytes(twin.read_bytes()) != sha_bytes(src.read_bytes()):
            raise ProtocolError(f"{twin}: differs from durable copy")


def fingerprint_tree(root: Path) -> dict[str, str]:
    """path → sha256 for every file under root (bit-identity comparisons)."""
    return {str(p.relative_to(root)): sha_bytes(p.read_bytes())
            for p in _iter_files(Path(root))}


def append_run_record(model_dir: Path, event: dict[str, Any]) -> None:
    """The per-model append-only run record (§19, §27)."""
    import datetime

    path = Path(model_dir) / "runrecord.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    stamped = {"utc": datetime.datetime.now(datetime.UTC).isoformat(), **event}
    with path.open("a") as handle:
        handle.write(json.dumps(stamped, sort_keys=True) + "\n")
