"""Filesystem primitives: atomic, write-once, append-only, deterministic.

Derived artifacts must be byte-identical on regeneration (§27), so JSON is
always written with sorted keys and a fixed layout, and no writer here injects
wall-clock state. Timestamps enter records only where the protocol asks for
one (the transition log, the unmask record), and never inside a hashed
payload that has to reproduce.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dci1v4.errors import IntegrityError
from dci1v4.protocol.hashing import sha_obj


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def write_json(path: Path, obj: Any) -> None:
    atomic_write_text(path, dumps(obj))


def write_json_once(path: Path, obj: Any) -> None:
    """Write-once: refuses to replace an existing artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dumps(obj).encode("utf-8")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as error:
        raise IntegrityError(f"{path} already exists; v4 artifacts are "
                             f"write-once") from error
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    """Append-only single-row append with O_APPEND."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    with os.fdopen(fd, "w") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def row_with_hash(row: dict[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in row.items() if k != "record_hash"}
    return {**body, "record_hash": sha_obj(body)}


def verify_row_hash(row: dict[str, Any], where: str = "") -> None:
    body = {k: v for k, v in row.items() if k != "record_hash"}
    if row.get("record_hash") != sha_obj(body):
        raise IntegrityError(f"row hash mismatch {where}")
