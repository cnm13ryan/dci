"""DCI-1 v4 instrument layer (preregistration v4r2, NOT frozen).

Pre-freeze implementation of the v4r2 measurement seam: the per-constraint
compliance vector with graded scores (§7.4), non-vacuity predicates and
degeneracy flags (§9.3), over the registered constraint grids (§7.1–§7.2).
Design authority: user-notes/DCI1_preregistration_v4r2.md, a draft for
registration — nothing in this package freezes it, and no stage machinery,
generation path, or analysis pipeline lives here yet.

Per §26 the package is namespace-isolated: it imports nothing from any
earlier DCI implementation. The exact-count segmentation and counting
sources are carried byte-identically from the closed v3 instruments under
the §10.2 carry-over rule, verified by ``dci1v4.carryover``.
"""
from __future__ import annotations

from dci1v4.hashing import instrument_source_hash

__all__ = ["instrument_source_hash"]
