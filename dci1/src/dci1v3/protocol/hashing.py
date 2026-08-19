"""Canonical hashing for every v3 artifact and derivation.

The study-wide hash function H is SHA-256 (registered in the study manifest).
Domain-separated derivations join their inputs with the 0x1f unit separator,
so no concatenation of distinct inputs can collide with another.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SEP = "\x1f"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_text(text: str) -> str:
    return sha_bytes(text.encode("utf-8"))


def sha_file(path: Path) -> str:
    return sha_bytes(Path(path).read_bytes())


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no whitespace variance, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def sha_obj(obj: Any) -> str:
    return sha_text(canonical_json(obj))


def domain_digest(domain: str, *parts: Any) -> bytes:
    """SHA-256 over domain + parts, 0x1f-separated."""
    payload = SEP.join([domain, *[str(p) for p in parts]])
    return hashlib.sha256(payload.encode("utf-8")).digest()


def domain_int(domain: str, *parts: Any, bits: int = 63) -> int:
    """A non-negative integer of at most ``bits`` bits from the digest."""
    value = int.from_bytes(domain_digest(domain, *parts)[:8], "big")
    return value % (1 << bits)


def git_blob_sha(data: bytes) -> str:
    """The SHA-1 git assigns a blob with these bytes (for ls-tree matching)."""
    header = f"blob {len(data)}\x00".encode()
    return hashlib.sha1(header + data).hexdigest()
