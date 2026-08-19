"""Content hashing for protocol objects, files and text.

Copied from the repository's generic provenance primitive
(`src/dci/provenance/hashes.py`), which is study-independent by construction.
Copied rather than imported so this study has no import edge into the old
confirmatory package; the semantics are identical and pinned by
`tests/test_hashing.py`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePath
from typing import Any


class UnhashableProtocolValue(TypeError):
    """A value reached the protocol hash with no canonical serialization.

    Raised instead of guessing: `default=str` would silently hash an object's
    memory address, so the same logical protocol could hash differently in two
    processes, or two different protocols could collide.
    """


def canonicalize(obj: Any, path: str = "$") -> Any:
    """Reduce `obj` to JSON primitives, or refuse."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if isinstance(key, bool) or not isinstance(key, (str, int)):
                raise UnhashableProtocolValue(
                    f"{path}: dict key {key!r} of type {type(key).__name__} "
                    "has no canonical form; use string keys")
            out[str(key)] = canonicalize(value, f"{path}.{key}")
        return out
    if isinstance(obj, (list, tuple)):
        return [canonicalize(v, f"{path}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, (set, frozenset)):
        items = [canonicalize(v, f"{path}{{}}") for v in obj]
        return sorted(items, key=lambda v: json.dumps(v, sort_keys=True))
    if hasattr(obj, "item") and hasattr(obj, "dtype") and getattr(obj, "ndim", 1) == 0:
        return canonicalize(obj.item(), path)          # numpy scalar
    raise UnhashableProtocolValue(
        f"{path}: {type(obj).__name__} has no canonical serialization for the "
        "protocol hash. Convert it at the call site, or extend canonicalize().")


def sha(obj: Any) -> str:
    """Content hash of a protocol object, stable across processes."""
    return hashlib.sha256(
        json.dumps(canonicalize(obj), sort_keys=True).encode()).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
