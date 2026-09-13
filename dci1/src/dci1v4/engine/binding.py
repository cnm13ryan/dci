"""Verifier-hash binding at every v4 entry point (§10.6, check C5, trap T-12).

v3 enforced the binding at its dispatcher, and only after a specific commit.
v4r2 §10.6 names nine entry points and check C5 adds the ladder screen and
solo calibration, so eleven are protected here. Every one of them calls
``require_frozen_verifier`` **before any mutation**, and the call fails closed
on mismatch.

A frozen hash is never silently updated. A semantic verifier change requires
explicit invalidation and recalibration; historical rows stay auditable under
the hash recorded on them and are never treated as newly valid.
"""
from __future__ import annotations

from typing import Any

from dci1v4.errors import ProtocolError, VerifierBindingError
from dci1v4.protocol.constants import VERIFIER_BOUND_ENTRY_POINTS
from dci1v4.verifiers import source_hashes, verifier_source_hash


def current_verifier_hash() -> str:
    return verifier_source_hash()


def require_frozen_verifier(entry_point: str, frozen_hash: str | None) -> str:
    """Re-verify the canonical verifier hash before an entry point mutates.

    ``frozen_hash`` comes from the Gate 1 record. It is ``None`` only before
    Gate 1 exists, and the two entry points that legitimately run then — the
    ladder screen and solo calibration — still pass through here so the hash
    they ran under is recorded on their own records.
    """
    if entry_point not in VERIFIER_BOUND_ENTRY_POINTS:
        raise ProtocolError(
            f"{entry_point!r} is not a registered §10.6 entry point; the "
            f"protected set is {VERIFIER_BOUND_ENTRY_POINTS}")
    current = current_verifier_hash()
    if frozen_hash is None:
        return current
    if current != frozen_hash:
        raise VerifierBindingError(
            f"{entry_point}: the canonical verifier hash is {current} and the "
            f"Gate 1 record froze {frozen_hash}. A semantic verifier change "
            f"invalidates every downstream stage; it is never resolved by "
            f"updating the frozen value.")
    return current


def verifier_provenance() -> dict[str, Any]:
    """The per-module hashes recorded beside the canonical hash, so a stored
    verdict stays traceable to the verifier that produced it (check C5)."""
    return {"verifier_source_hash": current_verifier_hash(),
            "modules": source_hashes()}
