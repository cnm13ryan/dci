"""Verifier package: registered source hashes for §27 instrument checks."""
from __future__ import annotations

from pathlib import Path

from dci1v3.protocol.hashing import sha_file, sha_obj

_MODULES = ("words.py", "target.py", "families.py", "boundary.py")


def source_hashes() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    return {name: sha_file(here / name) for name in _MODULES}


def verifier_source_hash() -> str:
    """The single frozen instrument hash recorded on every generation row."""
    return sha_obj(source_hashes())
