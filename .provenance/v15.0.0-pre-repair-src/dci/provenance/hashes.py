"""hashes — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
import dis
import hashlib
import json
from pathlib import Path
from typing import Any


def sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_int(text: str, modulus: int = 1_000_000_000) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16) % modulus


def referenced_names(*objects: Any) -> set[str]:
    """Global and attribute names a function's bytecode refers to.

    Used by Gate 0 to assert structural properties, for example that the
    caliper derivation never touches a pool-spread symbol. It works from the
    code object rather than from source text, so the same assertion runs
    identically in a notebook and in a headless harness where
    inspect.getsource has nothing to read.
    """
    names: set[str] = set()
    stack = [getattr(o, "__code__", None) for o in objects]
    while stack:
        code = stack.pop()
        if code is None:
            continue
        names.update(code.co_names)
        names.update(code.co_varnames)
        stack.extend(c for c in code.co_consts if hasattr(c, "co_names"))
    return names
