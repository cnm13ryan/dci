"""The 47-cell block, the §8.4 allocation, and the assertions that guard them.

v4r2's block was a single arm -- five constraints, every unordered pair, both
orders, 25 cells -- and its cell count was a literal. v4r3's block is four
arms with different pairing rules, so the count is *derived* from the arms and
the literal is an assertion about the derivation rather than the definition of
it. That distinction matters: the number 47 appears in this module exactly
once, in a check.

| arm | cells | pairing rule |
|---|---:|---|
| unconstrained | 1 | none: load zero, §25's chance baseline |
| core solo | 5 | one per core constraint |
| core composed | 20 | every unordered pair, both orders |
| spectrum solo | 6 | one per spectrum companion |
| spectrum composed | 12 | B + companion only, both orders |
| class solo | 1 | the production-class control |
| class composed | 2 | B + CL only, both orders |

The spectrum and class arms pair with **B alone**. Crossing them with each
other and with A would add ninety composed cells per block for quantities no
registered estimand reads; the full reciprocal matrix that Xi needs is
retained over the five core constraints, exactly as v4r2 registered it.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r3.protocol import constants as C

__all__ = ["Cell", "CellType", "cell_types", "block_cells", "design_cells",
           "assert_allocation", "wording_indices", "slot_order_key",
           "active_slots"]


def active_slots(*, reduced: bool, class_arm: bool,
                 spectrum: bool = True) -> tuple[str, ...]:
    """The slots a replication runs, in registered slot order (§8.4).

    Three variants, not two, and the third is the one §12.6 usually produces:

    * **full** -- five core slots, six spectrum rungs, the class companion;
    * **no-spectrum** (``spectrum=False``) -- the core matrix intact and the
      spectrum arm dropped. This is what a model runs when §13.4 admits three
      core references but §12.6's coverage criterion fails: `Delta_R`, `Xi`,
      `Lambda` and the reciprocal matrix are all still identified, and only
      `delta_difficulty` is not. Dropping the core matrix too would discard
      identified estimands because an unidentified one is unavailable;
    * **reduced** (``reduced=True``) -- §8.6, for a model where §13.4 cannot
      admit three core references at all.
    """
    core = C.REDUCED_SLOTS if reduced else C.CORE_SLOTS
    tail = (C.CLASS_SLOT,) if class_arm else ()
    if reduced or not spectrum:
        return tuple(core) + tail
    return tuple(core) + tuple(C.SPECTRUM_SLOTS) + tail


def slot_order_key(slot: str) -> int:
    """Position in §8.4's registered slot order."""
    try:
        return C.REGISTERED_SLOT_ORDER.index(slot)
    except ValueError as exc:                       # pragma: no cover
        raise ProtocolError(f"{slot!r} is not a registered slot") from exc


@dataclass(frozen=True)
class CellType:
    """One logical cell of a block, independent of topic."""

    arm: str                      # unconstrained | solo | composed
    slots: tuple[str, ...]        # () | (slot,) | (first, second) in PROMPT order
    #: For a composed cell, which configuration this variant belongs to *for
    #: each* of its two constituents. §11.1: a configuration is the position
    #: of the OUTCOME, so one generation serves outcome_first for the
    #: constituent stated first and outcome_second for the other.
    @property
    def cell_id(self) -> str:
        if self.arm == "unconstrained":
            return "unconstrained"
        if self.arm == "solo":
            return f"solo:{self.slots[0]}"
        return f"pair:{self.slots[0]}+{self.slots[1]}"

    @property
    def load(self) -> int:
        return len(self.slots)

    def configuration_of(self, slot: str) -> str:
        """The §11.1 configuration this cell contributes for ``slot``."""
        if self.arm != "composed":
            raise ProtocolError("only a composed cell has a configuration")
        return (C.OUTCOME_FIRST if self.slots[0] == slot
                else C.OUTCOME_SECOND)


def _composed_pairs(slots: Sequence[str]) -> list[tuple[str, str]]:
    """Unordered pairs, by arm. §8.1.

    Core pairs with core; spectrum pairs with B alone; class pairs with B
    alone. The rule is stated on the slot names rather than on a lookup so
    that adding a slot to one arm cannot silently create pairs in another.
    """
    core = [s for s in slots if s in C.CORE_SLOTS]
    spectrum = [s for s in slots if s in C.SPECTRUM_SLOTS]
    klass = [s for s in slots if s == C.CLASS_SLOT]
    pairs = [tuple(sorted(p, key=slot_order_key))
             for p in combinations(core, 2)]
    if "B" in core:
        pairs += [tuple(sorted(("B", s), key=slot_order_key))
                  for s in spectrum + klass]
    elif spectrum or klass:
        raise ProtocolError(
            "the spectrum and class arms pair with B and B is not active")
    return pairs


def cell_types(*, reduced: bool = False, class_arm: bool = True,
               spectrum: bool = True) -> list[CellType]:
    """Every logical cell of one block, in a stable order."""
    slots = active_slots(reduced=reduced, class_arm=class_arm,
                         spectrum=spectrum)
    types = [CellType("unconstrained", ())]
    types += [CellType("solo", (s,)) for s in slots]
    for first, second in _composed_pairs(slots):
        types.append(CellType("composed", (first, second)))
        types.append(CellType("composed", (second, first)))

    expected = _expected_cell_count(reduced=reduced, class_arm=class_arm,
                                    spectrum=spectrum)
    if len(types) != expected:
        raise ProtocolError(
            f"the §8.1 cell set derived {len(types)} cells; the arms it is "
            f"built from imply {expected}")
    if len({t.cell_id + str(t.slots) for t in types}) != len(types):
        raise ProtocolError("duplicate cell in the §8.1 set")
    return types


def _expected_cell_count(*, reduced: bool, class_arm: bool,
                         spectrum: bool = True) -> int:
    if reduced:
        return (C.N_CELLS_REDUCED_WITH_CLASS if class_arm
                else C.N_CELLS_REDUCED)
    if not spectrum:
        return (C.N_CELLS_NO_SPECTRUM if class_arm
                else C.N_CELLS_NO_SPECTRUM_NO_CLASS)
    return C.N_CELLS_FULL if class_arm else C.N_CELLS_FULL_NO_CLASS


def wording_indices(block_index: int, n_constituents: int) -> tuple[int, ...]:
    """§8.4 verbatim, carried unchanged from v4r2.

    Solo cells use ``i mod 4``. A composed cell uses ``i mod 4`` for the
    constituent earlier in the REGISTERED slot order and
    ``(i + floor(i/4)) mod 4`` for the later one, applied identically to both
    order variants of that cell. The unconstrained cell has no wording index.
    """
    if n_constituents == 0:
        return ()
    first = block_index % C.N_WORDINGS
    if n_constituents == 1:
        return (first,)
    second = (block_index + block_index // C.N_WORDINGS) % C.N_WORDINGS
    return (first, second)


@dataclass(frozen=True)
class Cell:
    """One materialised cell of one block."""

    cell_id: str
    arm: str
    block_id: str
    block_index: int
    topic_id: str
    slots: tuple[str, ...]              # PROMPT order
    wording_by_slot: Mapping[str, int]
    draws: int

    @property
    def load(self) -> int:
        return len(self.slots)

    def position_of(self, slot: str) -> int:
        return self.slots.index(slot) + 1

    def configuration_of(self, slot: str) -> str:
        return (C.OUTCOME_FIRST if self.slots[0] == slot
                else C.OUTCOME_SECOND)


def block_cells(block: Any, *, reduced: bool = False, class_arm: bool = True,
                draws: int = C.M_DRAWS) -> list[Cell]:
    """Materialise one block's cells.

    ``block`` needs ``block_id``, ``index`` and ``topic_id``.
    """
    out: list[Cell] = []
    for t in cell_types(reduced=reduced, class_arm=class_arm):
        if t.arm == "composed":
            ordered = tuple(sorted(t.slots, key=slot_order_key))
            w = dict(zip(ordered, wording_indices(block.index, 2)))
        elif t.arm == "solo":
            w = {t.slots[0]: wording_indices(block.index, 1)[0]}
        else:
            w = {}
        out.append(Cell(
            cell_id=t.cell_id, arm=t.arm, block_id=block.block_id,
            block_index=block.index, topic_id=block.topic_id,
            slots=t.slots, wording_by_slot=w, draws=draws))
    return out


def design_cells(blocks: Sequence[Any], *, reduced: bool = False,
                 class_arm: bool = True, draws: int = C.M_DRAWS,
                 assert_allocation_over: int | None = None) -> list[Cell]:
    cells: list[Cell] = []
    for block in blocks:
        cells.extend(block_cells(block, reduced=reduced, class_arm=class_arm,
                                 draws=draws))
    keys = {(c.block_id, c.cell_id) for c in cells}
    if len(keys) != len(cells):
        raise ProtocolError("a (block, cell) pair appears twice in the plan")
    if assert_allocation_over is not None:
        assert_allocation(cells, blocks_expected=assert_allocation_over,
                          reduced=reduced, class_arm=class_arm)
    return cells


def assert_allocation(cells: Sequence[Cell], *, blocks_expected: int,
                      reduced: bool = False, class_arm: bool = True) -> None:
    """§8.4's executable coverage assertion.

    Refuses a plan containing a structural zero (a (cell, slot, wording)
    combination that never occurs) or a skew (one that occurs the wrong number
    of times), and refuses a composed cell type whose two order variants are
    not each present in every block.
    """
    if blocks_expected % C.N_WORDINGS:
        raise ProtocolError(
            f"{blocks_expected} blocks is not a whole number of wording "
            f"cycles of {C.N_WORDINGS}")
    per_wording = blocks_expected // C.N_WORDINGS

    counts: dict[tuple[str, str, int], int] = {}
    order_counts: dict[tuple[str, ...], int] = {}
    for cell in cells:
        if cell.arm == "composed":
            order_counts[cell.slots] = order_counts.get(cell.slots, 0) + 1
        for slot, w in cell.wording_by_slot.items():
            key = (cell.cell_id, slot, w)
            counts[key] = counts.get(key, 0) + 1

    expected_keys = set()
    for t in cell_types(reduced=reduced, class_arm=class_arm):
        for slot in t.slots:
            for w in range(C.N_WORDINGS):
                expected_keys.add((t.cell_id, slot, w))

    zeros = sorted(k for k in expected_keys if counts.get(k, 0) == 0)
    if zeros:
        raise ProtocolError(
            f"§8.4 structural zero: these (cell, slot, wording) combinations "
            f"never occur: {zeros[:8]}{'...' if len(zeros) > 8 else ''}")
    skew = sorted(k for k in expected_keys if counts.get(k, 0) != per_wording)
    if skew:
        raise ProtocolError(
            f"§8.4 wording skew: expected {per_wording} blocks per wording; "
            f"got {[(k, counts[k]) for k in skew[:8]]}")

    for t in cell_types(reduced=reduced, class_arm=class_arm):
        if t.arm != "composed":
            continue
        got = order_counts.get(t.slots, 0)
        if got != blocks_expected:
            raise ProtocolError(
                f"§8.4 requires both order variants of {t.cell_id} in every "
                f"block: {t.slots} appears in {got} of {blocks_expected}")
