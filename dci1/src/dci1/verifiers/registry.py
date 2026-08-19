"""Verifier identities and source hashes (prereg §10, §27).

The verifier source hash covers every module that decides a verdict: the word
segmentation, the target scoring rules, the pool verifiers and the constraint
dispatch. It is frozen at Gate 3 and asserted on every analysis load; any
drift aborts (§27).

Discriminant validity, structural half (§10): every verifier callable takes
the response text and its own fixed parameter only. `assert_blindness` checks
the signatures for treatment-shaped parameters.
"""
from __future__ import annotations

import inspect
from pathlib import Path

from dci1.protocol.constants import ProtocolError
from dci1.protocol.hashing import sha_file, sha_text

_SOURCES = (
    Path(__file__).resolve().parent / "words.py",
    Path(__file__).resolve().parent / "target.py",
    Path(__file__).resolve().parent / "pool.py",
    Path(__file__).resolve().parents[1] / "constraints" / "definitions.py",
)

_FORBIDDEN = {"arm", "arm_label", "condition", "treatment", "added_id",
              "other_verdict", "uptake"}


def verifier_source_hash() -> str:
    parts = [f"{p.name}\x1f{sha_file(p)}" for p in _SOURCES]
    return sha_text("\n".join(parts))


def assert_blindness() -> None:
    from dci1.verifiers import pool, target

    functions = [target.s0_count, target.s1_count, target.s2_count,
                 target.s3_count, pool.focal_max_letters, pool.min_letters,
                 pool.no_initial, pool.no_suffix, pool.no_doubled_letter]
    for fn in functions:
        parameters = set(inspect.signature(fn).parameters)
        clash = parameters & _FORBIDDEN
        if clash:
            raise ProtocolError(
                f"verifier {fn.__name__} accepts treatment-shaped "
                f"parameter(s) {clash} — verifiers must be blind (§10)")
