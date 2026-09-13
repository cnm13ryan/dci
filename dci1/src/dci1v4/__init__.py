"""DCI-1 v4 (preregistration v4r2, NOT frozen).

A fresh, fully isolated implementation of the v4 revision 2 protocol. The
primitive observation is the per-constraint compliance vector (§9.1); the
primary estimand is reciprocal delivery loss (§11); five constraints are
registered per replication and every one of them is a primary instrument
(§10.2).

Isolation (§26). This package imports nothing from ``dci1v3``, from any v2
package, or from the B+R pilot tool, reads no v3 or pilot configuration at
runtime, and writes nothing inside a v3 or pilot evidence tree. The single
permitted carry-over — the exact-count segmentation and counting sources
and the forty v3 boundary cases (§10.2) — is performed as a byte-level
comparison against the v3 files read as data, never as an import, by
``dci1v4.verifiers.carryover``. ``tests_v4/test_isolation.py`` enforces all
of this executably.

Nothing here freezes the protocol. Gate 5 is implemented and is not run.
"""
from __future__ import annotations

#: The registered v4 study identifier and its synthetic twin. Structurally
#: distinct from ``dci1-v3`` and ``br-pilot-v4``: no v4 artifact can land in
#: an earlier study's tree (engine/context.py).
STUDY_ID = "dci1-v4"
SYNTHETIC_STUDY_ID = "dci1-v4-synthetic"

__all__ = ["STUDY_ID", "SYNTHETIC_STUDY_ID"]
