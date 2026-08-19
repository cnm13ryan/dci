"""The v4 canonical instrument-source hash (v4r2 §10.6).

Covers every dci1v4 source module that can change verifier semantics for a
registered instrument: segmentation, counting statistics, grids, and the
pass/graded/non-vacuity mappings. The hash is distinct from — and never
replaces — the frozen v3 ``verifier_source_hash``; v3 rows remain auditable
under their own recorded hash. Freezing this value in a Gate 1 record is a
separate, later act; nothing here freezes it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

INSTRUMENT_MODULES = ("words.py", "target.py", "statistics.py",
                      "constraints.py", "compliance.py")


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instrument_source_hash() -> str:
    """One hash over the registered instrument modules, order-independent."""
    here = Path(__file__).resolve().parent
    digests = {name: sha_file(here / name) for name in INSTRUMENT_MODULES}
    canonical = json.dumps(digests, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
