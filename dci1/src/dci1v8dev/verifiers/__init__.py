"""The v8 instrument layer (verifiers) and its canonical verifier hash.

Consolidated on 2026-08-29 from the ``dci1v8`` package (branch
``fix/v8-verifier-unification``, commit 5197c82) into the one v8 development
candidate, ``dci1v8dev``. One registered change against v7: **A and the eight
Tier-1 marker families are counted by one shared function**,
``words.count_marker(text, marker)``, under §9.2's lexical rule (segment the
response as written, fold each word, compare). v7 counted A with
``dci1v4.verifiers.target.s0_count`` (fold the whole response, then segment)
and the markers with the lexical rule; the two disagree on exactly one code
point, U+0130 ``İ``, when it is adjacent to the marker inside one alphabetic
run. The read-only rescore of every stored response
(``reports/dci1v8dev/verifier_unification/``) found no row containing it.

Nothing here reads or writes an evidence tree, and no v7 module imports it.
v7's rows keep v7's verdicts under v7's verifier hash.

The hash covers every source whose bytes decide what a v8 verifier computes:
the three v8 modules, the raw segmenter ``dci1v4/words.py`` they carry, and
the v7 modules v8 imports unchanged --- the family table (``constraints.py``),
the fourteen non-marker numerators (``statistics.py``), the five predicate
forms and the graded/vacuity rules (``compliance.py``) and the sentence rule
(``words.py``). Hashing the v7 files by path, rather than a v8 wrapper that
imports them, is what makes a drift underneath the import a v8 hash change.

The hash differs from v7's by construction: A's numerator moved. v7 rows stay
auditable under v7's recorded hash and are never re-labelled valid under this
one. (The hash also moved when the package moved from ``dci1v8`` to
``dci1v8dev.verifiers``: two import lines changed; the rescore report records
the value at the earlier path.)
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
        **{f"dci1v8dev/{n}": sha_file(here / n) for n in SEMANTIC_MODULES},
    }


def verifier_source_hash() -> str:
    """The one canonical v8 verifier hash."""
    return sha_obj(source_hashes())


__all__ = ["SEMANTIC_MODULES", "CARRIED_V4_MODULES", "CARRIED_V7_MODULES",
           "source_hashes", "verifier_source_hash"]
