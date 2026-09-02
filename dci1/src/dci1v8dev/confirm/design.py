"""The frame-preserving confirmatory block (Approach A's §8.1 / §8.4).

v7's block is an admitted set of arms with derived cells (``dci1v7.design
.cells``). Two things change under Approach A and nothing else does:

1. **Every slot of a block is rendered under the block's frame.** v7's
   §8.4 gave the two constituents of a composed cell *different* wording
   indices (``i mod 4`` and ``(i + i//4) mod 4``) so that wording and order
   were orthogonal over the 384 blocks. Under Approach A the frame is a
   property of the block and of every constraint the block states
   (``dci1v8dev.run.execute.prompt_cell`` refuses anything else on a load-1
   cell); a composed cell whose two lines were under two frames would put
   one row in two conditions. Wording and order stay orthogonal: the frame
   is fixed within a block and both orders of every pair run in every block.

2. **Two arms are new, both linear with B.** ``backup`` carries the two
   frozen §13.15 backups R4, R5 beside B (their solo cells and B+R, R+B),
   so that the pre-registered reference-sensitivity contrast can be formed
   over every admissible triple of {R1..R5}; they never enter Delta_R,
   Rbar, Xi or the fit (``estimators.reference_slots`` filters on exact
   CORE_SLOTS membership). ``spectrum`` carries the frame's **selected**
   spectrum points S1..Sk (k <= 12, ``rules.SELECTION_MAX_FAMILIES`` x 3)
   beside B, in place of v7's six core-family companions: the v8 selection
   (``spectrum.selection``) is decoupled from the core families. A spectrum
   point that is the very rung of a core or backup reference is *aliased*
   to that slot rather than generated twice.

| arm | cells | what |
|---|---:|---|
| base | 5 | unconstrained; A solo; B solo; A+B; B+A |
| core | 21 | R1..R3 solo; every remaining unordered pair over {A,B,R1,R2,R3}, both orders |
| backup | 6 | R4, R5 solo; B+R4, R4+B, B+R5, R5+B |
| spectrum | 3k | S_j solo; B+S_j, S_j+B for each non-aliased selected point |

A LOCAL frame runs base + core + backup (32 cells); a SPECTRUM frame runs
base + spectrum; a frame in both runs all four. A block is one confirmatory
topic under one frame; ``FrameBlock.index`` is ``4 * position + frame`` so
that the pilot's invariant ``frame == block_index % N_WORDINGS`` holds on
every row (``execute.frame_of_block``), and the allocation is every
confirmatory topic under every entering frame (``rules``:
``CONFIRMATORY_BLOCKS_PER_FRAME``; ``confirm.precision`` chose it).
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v7.design.cells import CellType
from dci1v7.protocol import constants as C

__all__ = ["ARM_BASE", "ARM_CORE", "ARM_BACKUP", "ARM_SPECTRUM", "ARMS",
           "BACKUP_SLOTS", "MAX_SPECTRUM_POINTS", "spectrum_slot_names",
           "normalise_arms", "slot_order_key", "slots_for", "cell_types",
           "n_cells_for", "FrameBlock", "Cell", "block_cells", "design_cells",
           "assert_frame_allocation", "frame_blocks", "block_index_of"]

ARM_BASE, ARM_CORE, ARM_BACKUP, ARM_SPECTRUM = "base", "core", "backup", "spectrum"
ARMS = (ARM_BASE, ARM_CORE, ARM_BACKUP, ARM_SPECTRUM)
BACKUP_SLOTS = ("R4", "R5")
#: ``rules.SELECTION_MAX_FAMILIES`` families x (low, centre, high); a centre
#: that is a core or backup rung is aliased and not counted here.
MAX_SPECTRUM_POINTS = 12


def spectrum_slot_names(n: int) -> tuple[str, ...]:
    if not 0 <= n <= MAX_SPECTRUM_POINTS:
        raise ProtocolError(f"{n} spectrum points; at most {MAX_SPECTRUM_POINTS}")
    return tuple(f"S{i + 1}" for i in range(n))


SLOT_ORDER = C.BASE_SLOTS + C.CORE_SLOTS + BACKUP_SLOTS + \
    spectrum_slot_names(MAX_SPECTRUM_POINTS)


def slot_order_key(slot: str) -> int:
    try:
        return SLOT_ORDER.index(slot)
    except ValueError as exc:
        raise ProtocolError(f"{slot!r} is not a v8 confirmatory slot") from exc


def normalise_arms(arms: Iterable[str]) -> tuple[str, ...]:
    requested = set(arms) | {ARM_BASE}
    unknown = sorted(requested - set(ARMS))
    if unknown:
        raise ProtocolError(f"{unknown} are not v8 confirmatory arms; "
                            f"registered: {ARMS}")
    if ARM_BACKUP in requested and ARM_CORE not in requested:
        raise ProtocolError("the backup arm exists for the reference-"
                            "sensitivity contrast over {R1..R5} and needs "
                            "the core arm")
    return tuple(a for a in ARMS if a in requested)


def slots_for(arms: Sequence[str], *, n_spectrum: int) -> tuple[str, ...]:
    admitted = normalise_arms(arms)
    slots: list[str] = list(C.BASE_SLOTS)
    if ARM_CORE in admitted:
        slots += list(C.CORE_SLOTS)
    if ARM_BACKUP in admitted:
        slots += list(BACKUP_SLOTS)
    if ARM_SPECTRUM in admitted:
        slots += list(spectrum_slot_names(n_spectrum))
    return tuple(slots)


def cell_types(arms: Sequence[str], *, n_spectrum: int) -> list[CellType]:
    """Every logical cell of one block, in a stable order."""
    admitted = normalise_arms(arms)
    slots = slots_for(admitted, n_spectrum=n_spectrum)
    types = [CellType("unconstrained", ())]
    types += [CellType("solo", (s,)) for s in slots]
    core = [s for s in slots if s in C.BASE_SLOTS + C.CORE_SLOTS]
    pairs = [tuple(sorted(p, key=slot_order_key)) for p in combinations(core, 2)]
    linear = [s for s in slots if s in BACKUP_SLOTS
              or s in spectrum_slot_names(MAX_SPECTRUM_POINTS)]
    pairs += [("B", s) for s in linear]
    for first, second in pairs:
        types.append(CellType("composed", (first, second)))
        types.append(CellType("composed", (second, first)))
    expected = n_cells_for(admitted, n_spectrum=n_spectrum)
    if len(types) != expected:
        raise ProtocolError(f"derived {len(types)} cells; the arms "
                            f"{list(admitted)} imply {expected}")
    if len({(t.arm, t.slots) for t in types}) != len(types):
        raise ProtocolError("duplicate cell in the v8 cell set")
    return types


def n_cells_for(arms: Sequence[str], *, n_spectrum: int) -> int:
    admitted = normalise_arms(arms)
    n = 5
    if ARM_CORE in admitted:
        n += 21
    if ARM_BACKUP in admitted:
        n += 6
    if ARM_SPECTRUM in admitted:
        n += 3 * n_spectrum
    return n


def block_index_of(position: int, frame: int) -> int:
    if not 0 <= frame < C.N_WORDINGS:
        raise ProtocolError(f"frame {frame} outside 0..{C.N_WORDINGS - 1}")
    return position * C.N_WORDINGS + frame


class FrameBlock:
    """One confirmatory topic under one frame."""

    __slots__ = ("block_id", "index", "position", "frame", "topic_id", "area")

    def __init__(self, *, position: int, frame: int, topic_id: str, area: str):
        self.position, self.frame = int(position), int(frame)
        self.index = block_index_of(self.position, self.frame)
        self.block_id = f"conf-{self.index:04d}"
        self.topic_id, self.area = topic_id, area


def frame_blocks(topics: Sequence[Mapping[str, Any]], frame: int
                 ) -> list[FrameBlock]:
    """Every confirmatory topic, in released order, under ``frame``."""
    return [FrameBlock(position=i, frame=frame, topic_id=t["topic_id"],
                       area=t["area"]) for i, t in enumerate(topics)]


@dataclass(frozen=True)
class Cell:
    cell_id: str
    arm: str
    block_id: str
    block_index: int
    frame: int
    topic_id: str
    slots: tuple[str, ...]              # prompt order
    wording_by_slot: Mapping[str, int]
    draws: int

    @property
    def load(self) -> int:
        return len(self.slots)

    def configuration_of(self, slot: str) -> str:
        if slot not in self.slots:
            raise ProtocolError(f"{slot!r} is not in {self.cell_id}")
        return C.OUTCOME_FIRST if self.slots[0] == slot else C.OUTCOME_SECOND


def block_cells(block: FrameBlock, arms: Sequence[str], *, n_spectrum: int,
                draws: int = C.M_DRAWS) -> list[Cell]:
    out: list[Cell] = []
    for t in cell_types(arms, n_spectrum=n_spectrum):
        out.append(Cell(
            cell_id=t.cell_id, arm=t.arm, block_id=block.block_id,
            block_index=block.index, frame=block.frame,
            topic_id=block.topic_id, slots=t.slots,
            wording_by_slot={s: block.frame for s in t.slots}, draws=draws))
    return out


def design_cells(blocks: Sequence[FrameBlock], arms: Sequence[str], *,
                 n_spectrum: int, draws: int = C.M_DRAWS) -> list[Cell]:
    cells: list[Cell] = []
    for block in blocks:
        cells.extend(block_cells(block, arms, n_spectrum=n_spectrum,
                                 draws=draws))
    keys = {(c.block_id, c.cell_id) for c in cells}
    if len(keys) != len(cells):
        raise ProtocolError("a (block, cell) pair appears twice in the plan")
    return cells


def assert_frame_allocation(cells: Sequence[Cell], arms: Sequence[str], *,
                            n_spectrum: int, frame: int,
                            blocks_expected: int) -> dict[str, Any]:
    """Approach A's coverage assertion for one frame's plan: every block
    carries exactly the derived cell set, every stated slot is rendered
    under the block's frame (which is ``frame``), and both order variants
    of every composed cell are present in every block."""
    admitted = normalise_arms(arms)
    types = cell_types(admitted, n_spectrum=n_spectrum)
    by_block: dict[str, set[tuple[str, tuple[str, ...]]]] = {}
    for cell in cells:
        if cell.frame != frame or cell.block_index % C.N_WORDINGS != frame:
            raise ProtocolError(f"{cell.block_id}: frame {cell.frame} / index "
                                f"{cell.block_index} in a frame-{frame} plan")
        for slot, w in cell.wording_by_slot.items():
            if w != frame:
                raise ProtocolError(
                    f"{cell.cell_id}@{cell.block_id}: slot {slot} rendered "
                    f"under frame {w} in a block of frame {frame}")
        by_block.setdefault(cell.block_id, set()).add((cell.arm, cell.slots))
    if len(by_block) != blocks_expected:
        raise ProtocolError(f"{len(by_block)} blocks in the plan; expected "
                            f"{blocks_expected}")
    expected = {(t.arm, t.slots) for t in types}
    for block_id, present in sorted(by_block.items()):
        if present != expected:
            raise ProtocolError(
                f"{block_id}: cell set differs from the design's "
                f"({len(present)} vs {len(expected)} cells)")
    return {"frame": frame, "blocks": len(by_block),
            "cells_per_block": len(expected), "admitted_arms": list(admitted),
            "n_spectrum": n_spectrum, "both_orders_every_block": True,
            "every_slot_under_block_frame": True}
