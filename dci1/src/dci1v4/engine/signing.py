"""Signed records: content hash plus HMAC-SHA256 signature.

Every stage record is signed with the study-wide signing key created at
registration. Hash verification without signature verification is invalid, so
``verify_signed`` always checks both and there is no hash-only variant. §18
requires each command to verify its predecessor's content hash *and*
signature before any mutation; that is what this module exists for.
"""
from __future__ import annotations

import hmac
import os
import secrets
from hashlib import sha256
from pathlib import Path
from typing import Any

from dci1v4.errors import IntegrityError
from dci1v4.protocol.hashing import sha_obj


def create_signing_key(path: Path) -> str:
    """Write-once study signing key; returns its content hash."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32).hex()
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise IntegrityError(f"signing key already exists at {path}") from error
    with os.fdopen(fd, "w") as handle:
        handle.write(key)
    return sha256(key.encode()).hexdigest()


def _load_key(path: Path) -> bytes:
    path = Path(path)
    if not path.exists():
        raise IntegrityError(f"signing key missing at {path}; records cannot "
                             f"be authenticated")
    return path.read_text().strip().encode()


def sign_payload(payload: dict[str, Any], key_path: Path) -> dict[str, Any]:
    record_hash = sha_obj(payload)
    signature = hmac.new(_load_key(key_path), record_hash.encode(),
                         sha256).hexdigest()
    return {"payload": payload, "record_hash": record_hash,
            "signature": signature}


def verify_signed(record: dict[str, Any], key_path: Path,
                  where: str = "") -> dict[str, Any]:
    """Verify content hash AND signature; return the payload."""
    for field in ("payload", "record_hash", "signature"):
        if field not in record:
            raise IntegrityError(f"unsigned or malformed record {where}: "
                                 f"missing {field}")
    if sha_obj(record["payload"]) != record["record_hash"]:
        raise IntegrityError(f"record hash mismatch {where}")
    expected = hmac.new(_load_key(key_path), record["record_hash"].encode(),
                        sha256).hexdigest()
    if not hmac.compare_digest(expected, record["signature"]):
        raise IntegrityError(f"signature mismatch {where}")
    return record["payload"]
