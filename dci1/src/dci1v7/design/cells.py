"""The arm-derived block, the §8.4 allocation, and the assertions (§8).

**v4r4's named design variants are gone.** It carried ``full``,
``no-spectrum`` and ``reduced`` as three enumerated shapes, a
``VARIANT_EXEMPTIONS`` table patching the freeze record for the fields a
variant legitimately left empty, and a cell count per variant. That is
brittle in a specific way: a variant the code does not name cannot be run, and
a field a variant leaves empty is explained by a lookup rather than by the
identification status that caused it.

v5's design is **an admitted set of arms**, and the cell count is derived:

| arm | cells | pairing rule |
|---|---:|---|
| base | 5 | unconstrained; A solo; B solo; A+B in each order |
| core | 21 | R_j solo; every remaining unordered pair over {A,B,R1,R2,R3}, both orders |
| spectrum | 18 | six spectrum solo; B + each, both orders |
| nearform | 9 | N_k solo; B + each, both orders |
| class | 3 | CL solo; B + CL, both orders |

56 with every arm; 38 without the spectrum; 29 with base, core and class; 17
with base, near-form and class; 8 with base and class; 5 with the base alone.
``cells_for`` derives the count from the admitted set and §18.1's freeze
records both, so a field a variant leaves empty is explained by the
identification status §13 wrote, which is the general form of what
``VARIANT_EXEMPTIONS`` did specially.

**Dropping an arm never drops another.** A replication that cannot identify
the spectrum still estimates Delta_R, Delta_j, Xi and the reciprocal matrix; a
replication that cannot identify the core arm still estimates D(B<-A),
D(A<-B), Lambda, the order contrasts and whichever of Delta_near and
Delta_broad its own arms support.

**The spectrum, near-form and class arms pair with B alone.** Crossing them
with each other and with A would add cells for quantities no registered
estimand reads; the full reciprocal matrix Xi needs is retained over the five
core constraints, and the three linear arms buy their quantities at linear
rather than quadratic cost.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions

__all__ = ["Cell", "CellType", "ARM_SLOTS", "normalise_arms", "slots_for",
           "cell_types", "cells_for", "n_cells_for", "block_cells",
           "design_cells", "assert_allocation", "wording_indices",
           "slot_order_key", "arms_from_identification",
           "admitted_arms_from_decision", "d1_scale", "D1_ARM_SETS",
           "D1_SCALE"]

#: Which slots each arm contributes. The base arm is always present.
ARM_SLOTS: dict[str, tuple[str, ...]] = {
    C.ARM_BASE: C.BASE_SLOTS,
    C.ARM_CORE: C.CORE_SLOTS,
    C.ARM_SPECTRUM: C.SPECTRUM_SLOTS,
    C.ARM_NEAR_FORM: C.NEAR_FORM_SLOTS,
    C.ARM_CLASS: (C.CLASS_SLOT,),
}


def normalise_arms(arms: Iterable[str]) -> tuple[str, ...]:
    """The admitted arm set, validated and in registered order.

    ``base`` is added if absent rather than refused, because it is not
    optional: §8.1 says it is always admitted. Every other name must be a
    registered arm, and the **spectrum requires the core arm**, because
    §13.12 draws every spectrum rung from an admitted core reference's own
    family --- a spectrum without a core arm would be six companions belonging
    to nothing.
    """
    requested = set(arms) | {C.ARM_BASE}
    unknown = sorted(requested - set(C.ARMS))
    if unknown:
        raise ProtocolError(
            f"{unknown} are not registered §8.1 arms; registered: {C.ARMS}")
    if C.ARM_SPECTRUM in requested and C.ARM_CORE not in requested:
        raise ProtocolError(
            "§13.12 draws both spectrum rungs from an admitted core "
            "reference's own family, so the spectrum arm cannot be admitted "
            "without the core arm")
    return tuple(a for a in C.ARMS if a in requested)


#: §34 D1's four registered compute options, as the arm set each one runs.
#: The near-form arm is **scientifically essential** under §34 D18's closure:
#: without it no replication can emit the strong L3c conclusion, so the option
#: that drops it is the option that gives up the study's refutation verdict.
#: `reports/dci1v5/d1_arm_compute_decision.md` derives the cost of each.
D1_ARM_SETS: dict[str, tuple[str, ...]] = {
    "four_models_56_cells": C.ARMS,
    # 47 = 56 - the 9 near-form cells. This is the option R1 names.
    "four_models_47_cells": tuple(a for a in C.ARMS
                                  if a != C.ARM_NEAR_FORM),
    "two_models_56_cells": C.ARMS,
    "384_blocks_m4": C.ARMS,
}
#: Per option, how many models and how many draws per cell. D1 selects a
#: budget, and a budget is arms x models x blocks x draws; naming only the
#: arms would leave three of the four factors to whoever wrote the runner.
D1_SCALE: dict[str, dict[str, int]] = {
    "four_models_56_cells": {"models": 4, "blocks": 384, "draws": 8},
    "four_models_47_cells": {"models": 4, "blocks": 384, "draws": 8},
    "two_models_56_cells": {"models": 2, "blocks": 384, "draws": 8},
    "384_blocks_m4": {"models": 4, "blocks": 384, "draws": 4},
}


def admitted_arms_from_decision() -> tuple[str, ...]:
    """§34 D1: the arm set the registered compute budget runs.

    The **design-time** arm set, which is not the same thing as
    ``arms_from_identification``: this is what the study registered it would
    attempt, and that is what a replication's Gate-3 verdicts then narrow. A
    replication cannot identify an arm the budget never ran, and it can fail
    to identify one the budget did.

    Every option exists here and none is reachable while D1 is open, so a
    runner cannot get a default arm set by asking for one.
    """
    return decisions.choice(
        "D1", {k: v for k, v in D1_ARM_SETS.items()},
        where="design.cells.admitted_arms_from_decision")


def d1_scale() -> dict[str, int]:
    """§34 D1's models, blocks and draws. Refuses while D1 is open."""
    return decisions.choice("D1", {k: dict(v) for k, v in D1_SCALE.items()},
                            where="design.cells.d1_scale")


def slots_for(arms: Sequence[str]) -> tuple[str, ...]:
    """The slots an admitted arm set runs, in §8.4's registered slot order."""
    admitted = normalise_arms(arms)
    slots = {s for arm in admitted for s in ARM_SLOTS[arm]}
    return tuple(s for s in C.REGISTERED_SLOT_ORDER if s in slots)


def slot_order_key(slot: str) -> int:
    """Position in §8.4's registered slot order."""
    try:
        return C.REGISTERED_SLOT_ORDER.index(slot)
    except ValueError as exc:
        raise ProtocolError(f"{slot!r} is not a registered slot") from exc


@dataclass(frozen=True)
class CellType:
    """One logical cell of a block, independent of topic."""

    arm: str                      # unconstrained | solo | composed
    slots: tuple[str, ...]        # () | (slot,) | (first, second) in PROMPT order

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
        """The §11.1 configuration this cell contributes for ``slot``.

        A configuration is the position of the **outcome**, so one composed
        generation serves ``outcome_first`` for the constituent stated first
        and ``outcome_second`` for the other.
        """
        if self.arm != "composed":
            raise ProtocolError("only a composed cell has a configuration")
        if slot not in self.slots:
            raise ProtocolError(f"{slot!r} is not in {self.cell_id}")
        return (C.OUTCOME_FIRST if self.slots[0] == slot
                else C.OUTCOME_SECOND)


def _composed_pairs(slots: Sequence[str]) -> list[tuple[str, str]]:
    """Unordered pairs, by arm (§8.1).

    Stated on the slot names rather than through a lookup, so that adding a
    slot to one arm cannot silently create pairs in another.
    """
    core = [s for s in slots if s in C.BASE_SLOTS + C.CORE_SLOTS]
    linear = [s for s in slots
              if s in C.SPECTRUM_SLOTS + C.NEAR_FORM_SLOTS + (C.CLASS_SLOT,)]
    pairs = [tuple(sorted(p, key=slot_order_key))
             for p in combinations(core, 2)]
    if linear:
        if "B" not in core:
            raise ProtocolError(
                "the spectrum, near-form and class arms pair with B and B is "
                "not active")
        pairs += [tuple(sorted(("B", s), key=slot_order_key)) for s in linear]
    return pairs


def cell_types(arms: Sequence[str]) -> list[CellType]:
    """Every logical cell of one block, in a stable order."""
    admitted = normalise_arms(arms)
    slots = slots_for(admitted)
    types = [CellType("unconstrained", ())]
    types += [CellType("solo", (s,)) for s in slots]
    for first, second in _composed_pairs(slots):
        types.append(CellType("composed", (first, second)))
        types.append(CellType("composed", (second, first)))

    expected = n_cells_for(admitted)
    if len(types) != expected:
        raise ProtocolError(
            f"the §8.1 cell set derived {len(types)} cells; the admitted arms "
            f"{list(admitted)} imply {expected}")
    if len({(t.arm, t.slots) for t in types}) != len(types):
        raise ProtocolError("duplicate cell in the §8.1 set")
    return types


def n_cells_for(arms: Sequence[str]) -> int:
    """§8.1's derived cell count for an admitted arm set.

    A sum over the per-arm counts of §8.1's table, which is the derivation the
    freeze record binds. ``cell_types`` builds the set independently and
    checks itself against this, so the two disagree loudly rather than one
    silently defining the other.
    """
    admitted = normalise_arms(arms)
    return sum(C.N_CELLS_BY_ARM[a] for a in admitted)


def cells_for(arms: Sequence[str]) -> tuple[CellType, ...]:
    """§8.1's cell set for an admitted arm set."""
    return tuple(cell_types(arms))


def arms_from_identification(*, core_identified: bool,
                             spectrum_identified: bool,
                             near_form_identified: bool,
                             class_identified: bool) -> tuple[str, ...]:
    """The arm set §13's identification verdicts admit (§18 stage 10).

    Every argument is a Gate-3 verdict and none is a preference. The spectrum
    cannot be admitted without the core arm, so a spectrum verdict of True
    with a core verdict of False is a defect in the caller and says so.
    """
    if spectrum_identified and not core_identified:
        raise ProtocolError(
            "§13.12: a spectrum triple is drawn from an admitted core "
            "reference's family, so the spectrum cannot be identified while "
            "the core arm is not")
    admitted = [C.ARM_BASE]
    if core_identified:
        admitted.append(C.ARM_CORE)
    if spectrum_identified:
        admitted.append(C.ARM_SPECTRUM)
    if near_form_identified:
        admitted.append(C.ARM_NEAR_FORM)
    if class_identified:
        admitted.append(C.ARM_CLASS)
    return normalise_arms(admitted)


def wording_indices(block_index: int, n_constituents: int) -> tuple[int, ...]:
    """§8.4 verbatim, carried unchanged.

    Solo cells use ``i mod 4``. A composed cell uses ``i mod 4`` for the
    constituent earlier in the REGISTERED slot order and
    ``(i + floor(i/4)) mod 4`` for the later one, applied identically to both
    order variants of that cell. The unconstrained cell has no wording index.
    Because order does not depend on the block index, wording and order are
    orthogonal by construction.
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


def block_cells(block: Any, arms: Sequence[str], *,
                draws: int = C.M_DRAWS) -> list[Cell]:
    """Materialise one block's cells. ``block`` needs ``block_id``, ``index``
    and ``topic_id``."""
    out: list[Cell] = []
    for t in cell_types(arms):
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


def design_cells(blocks: Sequence[Any], arms: Sequence[str], *,
                 draws: int = C.M_DRAWS,
                 assert_allocation_over: int | None = None) -> list[Cell]:
    cells: list[Cell] = []
    for block in blocks:
        cells.extend(block_cells(block, arms, draws=draws))
    keys = {(c.block_id, c.cell_id) for c in cells}
    if len(keys) != len(cells):
        raise ProtocolError("a (block, cell) pair appears twice in the plan")
    if assert_allocation_over is not None:
        assert_allocation(cells, arms, blocks_expected=assert_allocation_over)
    return cells


def assert_allocation(cells: Sequence[Cell], arms: Sequence[str], *,
                      blocks_expected: int) -> None:
    """§8.4's executable coverage assertion.

    Refuses a plan containing a structural zero (a (cell, slot, wording)
    combination that never occurs), a skew (one that occurs the wrong number
    of times), a composed cell type whose two order variants are not each
    present in every block, and --- last, because it is the only one the other
    three cannot catch --- a plan whose cell types are all present at the
    right counts but belong to a **different admitted arm set**.
    """
    admitted = normalise_arms(arms)
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

    types = cell_types(admitted)
    expected_keys = {(t.cell_id, slot, w) for t in types for slot in t.slots
                     for w in range(C.N_WORDINGS)}

    zeros = sorted(k for k in expected_keys if counts.get(k, 0) == 0)
    if zeros:
        raise ProtocolError(
            "§8.4 structural zero: these (cell, slot, wording) combinations "
            f"never occur: {zeros[:8]}{'...' if len(zeros) > 8 else ''}")
    skew = sorted(k for k in expected_keys if counts.get(k, 0) != per_wording)
    if skew:
        raise ProtocolError(
            f"§8.4 wording skew: expected {per_wording} blocks per wording; "
            f"got {[(k, counts[k]) for k in skew[:8]]}")

    for t in types:
        if t.arm != "composed":
            continue
        got = order_counts.get(t.slots, 0)
        if got != blocks_expected:
            raise ProtocolError(
                f"§8.4 requires both order variants of {t.cell_id} in every "
                f"block: {t.slots} appears in {got} of {blocks_expected}")

    expected = n_cells_for(admitted)
    per_block = len(cells) / blocks_expected if blocks_expected else 0
    if per_block != expected:
        raise ProtocolError(
            f"§8.4: the admitted arm set {list(admitted)} has {expected} "
            f"cells per block and the plan carries {per_block}; a plan with "
            "the wrong cell count is a plan for a different design")
