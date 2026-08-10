"""hashes — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
import dis
import hashlib
import json
from pathlib import Path, PurePath
from typing import Any


class UnhashableProtocolValue(TypeError):
    """A value reached the protocol hash with no canonical serialization.

    Raised instead of guessing. `default=str` used to absorb these, which is
    silently wrong for any object whose repr embeds its memory address: the
    same logical protocol would then hash differently in two processes, and a
    resume would be refused - or, worse, two genuinely different protocols
    would collide onto the same "<object at 0x...>" text.
    """


def canonicalize(obj: Any, path: str = "$") -> Any:
    """Reduce `obj` to JSON primitives, or refuse.

    Supported beyond JSON's own types: tuples (as lists, which is what JSON
    already does), `PurePath` (as its string form), sets and frozensets (as
    lists sorted by their own canonical text, since set iteration order is not
    a protocol fact), and numpy scalars (as the Python scalar they wrap).
    Anything else raises, because a hash nobody can reproduce is worse than a
    loud failure at freeze time.
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        # str/int subclasses include the str-valued enums used for statuses;
        # json.dumps writes the underlying value, which is what we want.
        return obj
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if isinstance(key, bool) or not isinstance(key, (str, int)):
                raise UnhashableProtocolValue(
                    f"{path}: dict key {key!r} of type {type(key).__name__} has "
                    "no canonical form; use string keys")
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
    """Content hash of a protocol object.

    Deterministic across processes and PYTHONHASHSEED values: key order is
    fixed by sort_keys, set order by canonicalize, and there is no fallback
    that could serialize an object's identity instead of its value.
    """
    return hashlib.sha256(
        json.dumps(canonicalize(obj), sort_keys=True).encode()).hexdigest()


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
