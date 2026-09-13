"""The v4 cell model: a pair of constraints with positions (v4r2 §8).

**This is not v3's arm model and the difference is load-bearing (T-1).** A v3
cell carried one target and one added constraint, and a row carried the target
verdict plus a companion manipulation check. A v4 composed cell is an
unordered pair of registered constraints together with an instruction order,
and each of its generations is scored on *both* constituents, so one composed
generation yields two (outcome, companion) observations. Nothing here
privileges one constituent over the other.

The registered cell set of a full replication (§8.1):

* 5 solo cells, one per registered slot in ``REGISTERED_SLOTS``;
* 20 composed cells: each of the ten unordered pairs in each of the two
  instruction orders.

**Order is a cell-level factor (§8.4, T-5).** Both order variants of every pair
are present in every block, so order is balanced by construction and each
configuration is estimated on all 384 blocks. The v3 names ``target_first`` and
``added_first`` are block-level strata and do not exist here; ``ORDER_C1_FIRST``
and ``ORDER_C2_FIRST`` name which constituent of the *registered slot order* is
stated first.

**Wording is a block-level factor (§8.4, T-6).** The block index fixes
``w(c1) = i mod 4`` and ``w(c2) = (i + floor(i/4)) mod 4``, applied identically
to both order variants of a cell, so wording and order are orthogonal by
construction. ``assert_allocation`` states the intended count for every wording
in every order of every cell type and refuses a plan containing a structural
zero; where a formula and an assertion disagree, qualification fails.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable, Sequence

from dci1v4.design.prompts import (
    assert_shared_constituent_identity,
    prompt_hash,
    render,
)
from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.wordings import wording
from dci1v4.topics.split import Block


@dataclass(frozen=True)
class Constituent:
    """One constraint as it appears in one prompt."""

    slot: str            # A | B | R1 | R2 | R3
    kind: str            # A | B | RF1..RF8
    severity: int
    position: int        # 1-based position in the numbered list
    wording_index: int
    text: str


@dataclass(frozen=True)
class Cell:
    """One logical prompt cell of one stage."""

    cell_id: str
    stage: str
    cell_type: str                 # solo:A | pair:A+B:c1_first | ...
    topic_id: str
    block_id: str | None
    block_index: int | None
    constituents: tuple[Constituent, ...]
    order: str | None              # None for solo cells
    prompt: str
    prompt_hash: str
    draws: int

    @property
    def load(self) -> int:
        return len(self.constituents)

    @property
    def slots(self) -> tuple[str, ...]:
        return tuple(c.slot for c in self.constituents)

    def constituent(self, slot: str) -> Constituent:
        for item in self.constituents:
            if item.slot == slot:
                return item
        raise ProtocolError(f"{self.cell_id} carries no slot {slot!r}")


#: A resolved slot assignment: the concrete constraint behind each registered
#: slot for one model. Produced by Gate 2 (n*, m*) and Gate 3 (references);
#: never by this module, which knows only the design.
SlotMap = dict[str, tuple[str, int]]


def full_slots(slot_map: SlotMap) -> tuple[str, ...]:
    """The registered slot order in force: five slots, or two under §8.6."""
    if set(slot_map) == set(C.REGISTERED_SLOTS):
        return C.REGISTERED_SLOTS
    if set(slot_map) == set(C.REDUCED_SLOTS):
        return C.REDUCED_SLOTS
    raise ProtocolError(
        f"slot map {sorted(slot_map)} is neither the full design "
        f"{C.REGISTERED_SLOTS} nor the reduced design {C.REDUCED_SLOTS}")


def unordered_pairs(slots: Sequence[str]) -> list[tuple[str, str]]:
    """Every unordered pair, in registered slot order."""
    return list(combinations(slots, 2))


def registered_cell_types(slot_map: SlotMap) -> list[str]:
    """The 25 cell types of the full design, or the 4 of the reduced one."""
    slots = full_slots(slot_map)
    types = [f"solo:{slot}" for slot in slots]
    for s1, s2 in unordered_pairs(slots):
        for order in C.ORDERS:
            types.append(f"pair:{s1}+{s2}:{order}")
    expected = (C.N_CELLS_FULL if len(slots) == len(C.REGISTERED_SLOTS)
                else C.N_CELLS_REDUCED)
    if len(types) != expected:
        raise ProtocolError(f"{len(types)} cell types, expected {expected}")
    return types


def _constituent(slot: str, slot_map: SlotMap, *, position: int,
                 wording_index: int) -> Constituent:
    kind, severity = slot_map[slot]
    return Constituent(slot=slot, kind=kind, severity=severity,
                       position=position, wording_index=wording_index,
                       text=wording(kind, wording_index, severity))


def block_cells(stage: str, block: Block, slot_map: SlotMap, *,
                draws: int) -> list[Cell]:
    """Every registered cell of one block (§8.1)."""
    slots = full_slots(slot_map)
    cells: list[Cell] = []

    for slot in slots:
        item = _constituent(slot, slot_map, position=1, wording_index=block.w1)
        prompt = render(block.question, [item.text])
        cells.append(Cell(
            cell_id=f"{stage}:{block.block_id}:solo:{slot}", stage=stage,
            cell_type=f"solo:{slot}", topic_id=block.topic_id,
            block_id=block.block_id, block_index=block.index,
            constituents=(item,), order=None, prompt=prompt,
            prompt_hash=prompt_hash(prompt), draws=draws))

    composed_prompts: dict[str, str] = {}
    composed_lines: dict[str, tuple[str, str]] = {}
    for s1, s2 in unordered_pairs(slots):
        for order in C.ORDERS:
            first_slot, second_slot = ((s1, s2) if order == C.ORDER_C1_FIRST
                                       else (s2, s1))
            # Wording follows the slot's place in the REGISTERED order and is
            # identical in both order variants (§8.4). It deliberately does
            # NOT follow the position in the prompt, which is what keeps
            # wording orthogonal to order.
            w = {s1: block.w1, s2: block.w2}
            first = _constituent(first_slot, slot_map, position=1,
                                 wording_index=w[first_slot])
            second = _constituent(second_slot, slot_map, position=2,
                                  wording_index=w[second_slot])
            prompt = render(block.question, [first.text, second.text])
            cell_type = f"pair:{s1}+{s2}:{order}"
            composed_prompts[cell_type] = prompt
            composed_lines[cell_type] = (first.text, second.text)
            cells.append(Cell(
                cell_id=f"{stage}:{block.block_id}:{cell_type}", stage=stage,
                cell_type=cell_type, topic_id=block.topic_id,
                block_id=block.block_id, block_index=block.index,
                constituents=(first, second), order=order, prompt=prompt,
                prompt_hash=prompt_hash(prompt), draws=draws))

    assert_shared_constituent_identity(composed_prompts, composed_lines)
    expected = (C.N_CELLS_FULL if len(slots) == len(C.REGISTERED_SLOTS)
                else C.N_CELLS_REDUCED)
    if len(cells) != expected:
        raise ProtocolError(f"block {block.block_id} produced {len(cells)} "
                            f"cells, expected {expected}")
    return cells


def design_cells(stage: str, blocks: Iterable[Block], slot_map: SlotMap, *,
                 draws: int, assert_allocation_over: int | None = None
                 ) -> list[Cell]:
    """The full cell set of a stage, with the §8.4 allocation assertion."""
    blocks = list(blocks)
    cells = [cell for block in blocks
             for cell in block_cells(stage, block, slot_map, draws=draws)]
    ids = [c.cell_id for c in cells]
    if len(set(ids)) != len(ids):
        raise ProtocolError("duplicate cell identities in the plan")
    if assert_allocation_over is not None:
        assert_allocation(cells, blocks_expected=assert_allocation_over,
                          slot_map=slot_map)
    return cells


def assert_allocation(cells: Sequence[Cell], *, blocks_expected: int,
                      slot_map: SlotMap) -> dict[str, Any]:
    """§8.4, the executable allocation assertion.

    States the intended count for every wording index of every constituent
    slot in every order of every cell type, refuses a plan containing a
    structural zero, and refuses any skew. Under the registered allocation of
    384 blocks each wording appears in 96 blocks in each order of each cell
    type; the assertion is written against ``blocks_expected // 4`` so it holds
    at the pilot and calibration sizes too.
    """
    slots = full_slots(slot_map)
    types = registered_cell_types(slot_map)
    if blocks_expected % 4:
        raise ProtocolError(
            f"the wording allocation requires a block count divisible by "
            f"four; got {blocks_expected}")
    per_wording = blocks_expected // 4

    counts: dict[tuple[str, str, int], int] = {}
    for cell in cells:
        for item in cell.constituents:
            key = (cell.cell_type, item.slot, item.wording_index)
            counts[key] = counts.get(key, 0) + 1

    structural_zeros: list[str] = []
    skew: list[str] = []
    for cell_type in types:
        involved = ([cell_type.split(":", 1)[1]] if cell_type.startswith("solo:")
                    else cell_type.split(":")[1].split("+"))
        for slot in involved:
            for index in range(4):
                got = counts.get((cell_type, slot, index), 0)
                if got == 0:
                    structural_zeros.append(f"{cell_type}/{slot}@w{index}")
                elif got != per_wording:
                    skew.append(f"{cell_type}/{slot}@w{index}={got} "
                                f"(expected {per_wording})")
    if structural_zeros:
        raise ProtocolError(
            f"the plan contains a structural zero: no block carries "
            f"{structural_zeros[:4]}")
    if skew:
        raise ProtocolError(
            f"wording allocation is unbalanced; the formula and the "
            f"assertion disagree, so qualification fails: {skew[:4]}")

    order_counts: dict[tuple[str, str], int] = {}
    for cell in cells:
        if cell.order is None:
            continue
        pair = cell.cell_type.rsplit(":", 1)[0]
        order_counts[(pair, cell.order)] = order_counts.get(
            (pair, cell.order), 0) + 1
    for (pair, order), count in sorted(order_counts.items()):
        if count != blocks_expected:
            raise ProtocolError(
                f"{pair} in order {order} appears in {count} blocks, not "
                f"{blocks_expected}; order is a cell-level factor and every "
                f"block carries both variants (§8.4)")

    return {"blocks": blocks_expected, "cell_types": len(types),
            "slots": list(slots), "wording_count_per_cell_type": per_wording,
            "orders_balanced": True,
            "wording_counts": {f"{k[0]}/{k[1]}@w{k[2]}": v
                               for k, v in sorted(counts.items())}}


def prompt_plan(cells: Sequence[Cell]) -> dict[str, Any]:
    """The frozen prompt plan of one stage: identities, hashes, draw counts."""
    return {"cells": [{
        "cell_id": c.cell_id, "stage": c.stage, "cell_type": c.cell_type,
        "topic_id": c.topic_id, "block_id": c.block_id,
        "block_index": c.block_index, "order": c.order,
        "prompt_hash": c.prompt_hash, "draws": c.draws,
        "constituents": [{"slot": x.slot, "kind": x.kind,
                          "severity": x.severity, "position": x.position,
                          "wording_index": x.wording_index}
                         for x in c.constituents]} for c in cells]}
