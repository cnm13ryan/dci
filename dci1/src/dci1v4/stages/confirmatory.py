"""Confirmatory generation and the greedy sensitivity run (§8.3, §21).

**Implemented and not executed.** The task that produced this implementation
stops before the freeze and before confirmatory generation, so this module
builds and validates the plan and refuses to generate unless the freeze record
exists and licenses it.

The greedy sensitivity run repeats the 20 composed cells on the first 96
confirmatory blocks at temperature 0 with one draw per cell — exactly
1,920 generations — in its own namespace, and is reported as a **different
generation population**. It never merges with the confirmatory cache.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.design.cells import Cell, SlotMap, design_cells, prompt_plan
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.topics.split import Block


def confirmatory_plan(blocks: Sequence[Block], slot_map: SlotMap, *,
                      m_draws: int = C.M_DRAWS) -> dict[str, Any]:
    """The frozen confirmatory plan, with the §8.4 allocation asserted."""
    cells = design_cells(C.STAGE_CONFIRMATORY, blocks, slot_map,
                         draws=m_draws, assert_allocation_over=len(blocks))
    total = sum(c.draws for c in cells)
    expected_cells = (C.N_CELLS_FULL if len(slot_map) == 5
                      else C.N_CELLS_REDUCED)
    if len(cells) != len(blocks) * expected_cells:
        raise ProtocolError(f"{len(cells)} cells for {len(blocks)} blocks at "
                            f"{expected_cells} per block")
    return {"cells": cells, "plan": prompt_plan(cells),
            "blocks": len(blocks), "cells_per_block": expected_cells,
            "draws_per_cell": m_draws, "cached_generations": total}


def assert_generation_licensed(freeze_record: Mapping[str, Any] | None
                               ) -> None:
    """Confirmatory generation runs only after Gate 5 (§18)."""
    if not freeze_record:
        raise IntegrityError(
            "confirmatory generation requires a Gate 5 freeze record; this "
            "implementation stops before the freeze and before confirmatory "
            "generation")
    if freeze_record.get("outcome") != "PASS":
        raise IntegrityError("the freeze record does not record PASS")


def greedy_plan(blocks: Sequence[Block], slot_map: SlotMap) -> dict[str, Any]:
    """§8.3: the 20 composed cells on the first 96 blocks at temperature 0."""
    subset = list(blocks)[:C.GREEDY_BLOCKS]
    if len(subset) != C.GREEDY_BLOCKS:
        raise ProtocolError(f"the greedy run needs the first "
                            f"{C.GREEDY_BLOCKS} confirmatory blocks")
    cells = [c for c in design_cells("greedy", subset, slot_map,
                                     draws=C.GREEDY_DRAWS)
             if c.load == 2]
    expected = C.GREEDY_BLOCKS * C.N_COMPOSED_CELLS
    if len(cells) != expected:
        raise ProtocolError(f"{len(cells)} greedy cells, expected {expected}")
    return {"cells": cells, "plan": prompt_plan(cells),
            "generations": sum(c.draws for c in cells),
            "temperature": C.GREEDY_TEMPERATURE,
            "namespace": "greedy",
            "population_note": ("reported as a different generation "
                                "population; never merged with the "
                                "confirmatory cache (§8.3)")}


def assert_separate_population(confirmatory_dir: Path, greedy_dir: Path
                               ) -> None:
    """The greedy run keeps its own namespace and its own cache file."""
    if Path(confirmatory_dir).resolve() == Path(greedy_dir).resolve():
        raise IntegrityError(
            "the greedy sensitivity run shares a directory with the "
            "confirmatory cache; it is a different generation population")
