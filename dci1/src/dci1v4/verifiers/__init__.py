"""The v4 instrument layer and its canonical verifier hash (v4r2 §10.6).

The hash covers every source module that can change verifier semantics for
any registered instrument: segmentation, the exact-count rules, the counted
statistics, the registered grids, and the pass / graded-score / non-vacuity
mappings. Under v4 the word-length rule and every admitted family verifier
are primary instruments alongside the exact-count rule, so all five are
inside one hash and one freeze.

It is distinct from — and never replaces — the frozen v3
``verifier_source_hash``; v3 rows stay auditable under their own recorded
hash and are never treated as newly valid. The frozen boundary suites and
the frozen wordings are bound separately in the Gate 1 record, because they
are expectations and stimulus text rather than scoring semantics.
"""
from __future__ import annotations

from pathlib import Path

from dci1v4.protocol.hashing import sha_file, sha_obj

#: Modules whose bytes define what any registered verifier computes.
SEMANTIC_MODULES = ("words.py", "target.py", "statistics.py",
                    "constraints.py", "compliance.py")


def source_hashes() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    return {name: sha_file(here / name) for name in SEMANTIC_MODULES}


def verifier_source_hash() -> str:
    """The one canonical v4 verifier hash, recorded on every generation row
    and re-verified at every §10.6 entry point."""
    return sha_obj(source_hashes())
