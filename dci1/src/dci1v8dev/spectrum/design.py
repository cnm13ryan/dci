"""The confirmatory cells the frozen spectrum references need.

v7's §8.1 already generates, for every spectrum slot, its solo cell and the
composed pair with B **in both orders** (``design/cells.cell_types``:
"spectrum | 18 | six spectrum solo; B + each, both orders"); the spectrum
arm was never generated only because it was never identified. v8 decouples
the spectrum references from the core families, so the cell set is stated
here for an arbitrary list of frozen spectrum slots: per reference X the
cells ``solo:X``, ``pair:B+X`` and ``pair:X+B``; ``unconstrained`` and
``solo:B`` are shared with the base arm. The difficulty-response curve
needs exactly these: ``D(B <- X) = P(B | B solo) - P(B | B + X)`` per block
and configuration, and ``d_X = iota_X`` from ``solo:X`` and the
unconstrained cell on the same blocks.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dci1v7.design.cells import cell_types
from dci1v7.protocol import constants as C

__all__ = [
    "spectrum_cells",
    "spectrum_generation_cost",
    "v7_spectrum_orders_present",
]


def spectrum_cells(slots: Sequence[str]) -> list[dict[str, Any]]:
    cells = [{"cell_id": "unconstrained", "arm": "unconstrained",
              "slots": [], "shared": True},
             {"cell_id": "solo:B", "arm": "solo", "slots": ["B"],
              "shared": True}]
    for s in slots:
        cells.append({"cell_id": f"solo:{s}", "arm": "solo", "slots": [s],
                      "shared": False})
        cells.append({"cell_id": f"pair:B+{s}", "arm": "composed",
                      "slots": ["B", s], "shared": False,
                      "configuration_for_B": C.OUTCOME_FIRST})
        cells.append({"cell_id": f"pair:{s}+B", "arm": "composed",
                      "slots": [s, "B"], "shared": False,
                      "configuration_for_B": C.OUTCOME_SECOND})
    return cells


def spectrum_generation_cost(n_references: int, *,
                             blocks: int = C.N_BLOCKS,
                             draws: int = 8) -> dict[str, Any]:
    per_reference_cells = 3
    return {"references": n_references,
            "cells_per_reference": per_reference_cells,
            "blocks": blocks, "draws": draws,
            "generations": n_references * per_reference_cells * blocks * draws,
            "shared_cells_already_in_base_arm": ["unconstrained", "solo:B"]}


def v7_spectrum_orders_present() -> dict[str, Any]:
    """Registered fact, asserted: v7's cell set has both orders of B with
    every spectrum slot."""
    types = cell_types([C.ARM_BASE, C.ARM_CORE, C.ARM_SPECTRUM])
    ids = {t.cell_id for t in types}
    missing = [c for s in C.SPECTRUM_SLOTS
               for c in (f"solo:{s}", f"pair:B+{s}", f"pair:{s}+B")
               if c not in ids]
    return {"n_cells": len(types), "missing": missing, "ok": not missing}
