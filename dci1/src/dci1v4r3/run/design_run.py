"""Materialising the registered design for a model whose slots are fixed.

Gate 0's pilot builds its cells from a fixture slot map; Gate 4 and the
confirmatory run build theirs from the slot map Gate 2 and Gate 3 *decided*.
The construction is otherwise identical, and it is here once so that the
headroom check and the confirmatory generation cannot drift apart --- a
headroom result about a cell the confirmatory run does not generate would be
a check of something the study never does.

Three things this module refuses:

* a slot the design needs and the map does not bind;
* a scored constraint instance that is not in the map, which is how a row from
  a different severity would enter an analysis indexed by slot;
* two slots bound to the same (family, severity), which would make the slot of
  a scored verdict ambiguous and silently merge two companions.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v4r3.design.cells import cell_types, wording_indices
from dci1v4r3.protocol import constants as C
from dci1v4r3.run.execute import (
    Cell, composed_cell, solo_cell, unconstrained_cell,
)
from dci1v4r3.stages.confirmatory import DESIGN_VARIANTS
from dci1v4r3.verifiers.constraints import Constraint

__all__ = ["slot_constraints", "assert_slot_map_usable", "design_cells_for",
           "attach_slots", "absent_instances"]


def slot_constraints(slot_map: Mapping[str, Any]) -> dict[str, Constraint]:
    """slot -> Constraint, over the whole registered slot order."""
    out: dict[str, Constraint] = {}
    for slot, entry in slot_map.items():
        kind, severity = (entry["family"], entry["severity"]) \
            if isinstance(entry, Mapping) else tuple(entry)
        out[slot] = Constraint(kind, int(severity), extended=True,
                               reserve=True)
    return out


def assert_slot_map_usable(slot_map: Mapping[str, Any], variant: str) -> None:
    """Every slot the variant needs is bound, and no two slots share an
    instance."""
    if variant not in DESIGN_VARIANTS:
        raise ProtocolError(f"{variant!r} is not a registered design variant")
    reduced, class_arm, spectrum = DESIGN_VARIANTS[variant]
    needed = {s for t in cell_types(reduced=reduced, class_arm=class_arm,
                                    spectrum=spectrum) for s in t.slots}
    missing = sorted(needed - set(slot_map))
    if missing:
        raise IntegrityError(
            f"the {variant} design needs slots the map does not bind: "
            f"{missing}")
    constraints = slot_constraints(slot_map)
    seen: dict[tuple[str, int], str] = {}
    for slot in sorted(needed):
        key = (constraints[slot].kind, constraints[slot].severity)
        if key in seen:
            raise IntegrityError(
                f"slots {seen[key]} and {slot} are both bound to "
                f"{key[0]}:{key[1]}; a scored verdict could not be attributed "
                "to one of them and the two companions would merge")
        seen[key] = slot


def design_cells_for(topics: Sequence[Mapping[str, Any]],
                     slot_map: Mapping[str, Any], *, variant: str,
                     prefix: str, block_prefix: str,
                     block_index_of: Mapping[str, int] | None = None
                     ) -> list[tuple[Cell, str]]:
    """Every cell of the variant, on every topic, with its block id.

    ``block_index_of`` supplies §8.4's block index when the caller has a
    registered block numbering; otherwise the position in ``topics`` is used,
    which is what a validation stage wants and what the confirmatory run must
    not use.
    """
    assert_slot_map_usable(slot_map, variant)
    reduced, class_arm, spectrum = DESIGN_VARIANTS[variant]
    constraints = slot_constraints(slot_map)
    out: list[tuple[Cell, str]] = []
    for position, topic in enumerate(topics):
        block = f"{block_prefix}-{topic['topic_id']}"
        index = (block_index_of[topic["topic_id"]]
                 if block_index_of is not None else position)
        for cell_type in cell_types(reduced=reduced, class_arm=class_arm,
                                    spectrum=spectrum):
            if cell_type.arm == "unconstrained":
                out.append((unconstrained_cell(topic, arm="unconstrained",
                                               prefix=prefix), block))
            elif cell_type.arm == "solo":
                slot = cell_type.slots[0]
                w = wording_indices(index, 1)[0]
                out.append((solo_cell(topic, constraints[slot], w,
                                      arm="solo", prefix=prefix), block))
            else:
                first, second = cell_type.slots
                # §8.4: the wording index follows the REGISTERED slot order,
                # not the prompt order, so both order variants of a pair carry
                # the same two wordings.
                ordered = sorted(cell_type.slots,
                                 key=C.REGISTERED_SLOT_ORDER.index)
                pair = dict(zip(ordered, wording_indices(index, 2)))
                out.append((composed_cell(
                    topic, constraints[first], constraints[second],
                    (pair[first], pair[second]), arm="composed",
                    prefix=prefix), block))
    return out


def attach_slots(rows: Sequence[Mapping[str, Any]],
                 block_of: Mapping[str, str],
                 slot_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Give every scored constraint its design slot, and every row its block.

    The verifier records a constraint by kind and severity, which is what it
    scores. The analysis indexes by slot, because two slots may share a family
    --- `R1` and `R1+` are both one family at different severities --- and a
    contrast over kinds would silently merge them.
    """
    constraints = slot_constraints(slot_map)
    by_instance = {(c.kind, c.severity): slot
                   for slot, c in constraints.items()}
    out: list[dict[str, Any]] = []
    for row in rows:
        scores = []
        for entry in row["scores"]:
            slot = by_instance.get((entry["kind"], entry["severity"]))
            if slot is None:
                raise IntegrityError(
                    f"scored instance {entry['kind']}:{entry['severity']} is "
                    "not bound to any slot of this model's frozen slot map; "
                    "a verdict the design does not name cannot enter an "
                    "analysis indexed by slot")
            scores.append({**entry, "slot": slot})
        block = block_of.get(row["cell_id"])
        if block is None:
            raise IntegrityError(f"no block for cell {row['cell_id']}")
        out.append({**row, "scores": scores, "block_id": block})
    return out


def absent_instances(slot_map: Mapping[str, Any]) -> tuple[Constraint, ...]:
    """§25's chance set: every bound instance, scored on every row.

    The unconstrained cell is where the difficulty coordinate's denominator
    comes from, and it can only supply one for an instance it was scored
    against.
    """
    return tuple(slot_constraints(slot_map).values())
