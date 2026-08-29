"""The v8 instrument layer and its canonical verifier hash.

The hash covers every source whose bytes decide what a v8 verifier computes:
the three v8 modules, the raw segmenter ``dci1v4/words.py`` they carry, and
the v7 modules v8 imports unchanged --- the family table (``constraints.py``),
the fourteen non-marker numerators (``statistics.py``), the five predicate
forms and the graded/vacuity rules (``compliance.py``) and the sentence rule
(``words.py``). Hashing the v7 files by path, rather than a v8 wrapper that
imports them, is what makes a drift underneath the import a v8 hash change.

The hash differs from v7's by construction: A's numerator moved. v7 rows stay
auditable under v7's recorded hash and are never re-labelled valid under this
one.
"""
from __future__ import annotations

from pathlib import Path

import dci1v4.verifiers as _v4_verifiers
import dci1v7.verifiers as _v7_verifiers
from dci1v4.protocol.hashing import sha_file, sha_obj

SEMANTIC_MODULES = ("words.py", "statistics.py", "compliance.py")
CARRIED_V4_MODULES = ("words.py",)
CARRIED_V7_MODULES = ("constraints.py", "statistics.py", "compliance.py",
                      "words.py")


def source_hashes() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    v4 = Path(_v4_verifiers.__file__).resolve().parent
    v7 = Path(_v7_verifiers.__file__).resolve().parent
    return {
        **{f"dci1v4/{n}": sha_file(v4 / n) for n in CARRIED_V4_MODULES},
        **{f"dci1v7/{n}": sha_file(v7 / n) for n in CARRIED_V7_MODULES},
        **{f"dci1v8/{n}": sha_file(here / n) for n in SEMANTIC_MODULES},
    }


def verifier_source_hash() -> str:
    """The one canonical v8 verifier hash."""
    return sha_obj(source_hashes())


__all__ = ["SEMANTIC_MODULES", "CARRIED_V4_MODULES", "CARRIED_V7_MODULES",
           "source_hashes", "verifier_source_hash"]
