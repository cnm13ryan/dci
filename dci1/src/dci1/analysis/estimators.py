"""Block-indexed estimators (prereg §11, §12).

The block is the only unit any primary estimator sees. `BlockTable` is the
sole accepted input type: it is indexed by block, carries all six arms of a
block together, and no function here accepts a response-level index — the
§12 function-signature check is enforced structurally and by test.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST
from dci1.protocol.constants import ARMS, ProtocolError


@dataclass(frozen=True)
class BlockTable:
    """All six arms of every block, indexed by block. The estimator input."""

    #: block_id → {"order": str, "f": {arm: 0/1}}
    blocks: Mapping[str, dict[str, Any]]

    def __post_init__(self):
        for block_id, entry in self.blocks.items():
            if set(entry["f"]) != set(ARMS):
                raise ProtocolError(
                    f"block {block_id} does not carry all six arms")
            if entry["order"] not in (TARGET_FIRST, ADDED_FIRST):
                raise ProtocolError(f"block {block_id}: bad order")

    def block_ids(self, order: str | None = None) -> list[str]:
        ids = sorted(self.blocks)
        if order is None:
            return ids
        return [b for b in ids if self.blocks[b]["order"] == order]


def build_block_table(scored_rows: list[dict[str, Any]],
                      failure_field: str = "f_s0") -> BlockTable:
    """Scored rows → BlockTable; asserts exactly one row per (block, arm)."""
    blocks: dict[str, dict[str, Any]] = {}
    for row in scored_rows:
        entry = blocks.setdefault(row["block_id"],
                                  {"order": row["order"], "f": {}})
        if row["arm"] in entry["f"]:
            raise ProtocolError(
                f"duplicate accepted response for cell "
                f"({row['block_id']}, {row['arm']})")
        entry["f"][row["arm"]] = int(row[failure_field])
    return BlockTable(blocks)


def block_contrast(table: BlockTable, block_id: str) -> float:
    """D_i = F_B − (F_R1 + F_R2 + F_R3)/3 (prereg §11)."""
    _require_table(table)
    f = table.blocks[block_id]["f"]
    return f["focal"] - (f["ref1"] + f["ref2"] + f["ref3"]) / 3.0


def tau_by_order(table: BlockTable, order: str) -> float:
    _require_table(table)
    ids = table.block_ids(order)
    if not ids:
        raise ProtocolError(f"no blocks with order {order!r}")
    return sum(block_contrast(table, b) for b in ids) / len(ids)


def delta(table: BlockTable, j: int, k: int) -> float:
    """δ_jk = E[F_Rj − F_Rk] over all blocks (prereg §11)."""
    _require_table(table)
    ids = table.block_ids()
    return sum(table.blocks[b]["f"][f"ref{j}"] -
               table.blocks[b]["f"][f"ref{k}"] for b in ids) / len(ids)


def per_reference_contrast(table: BlockTable, j: int, order: str) -> float:
    """E[F_B − F_Rj | order] — family F3 members."""
    _require_table(table)
    ids = table.block_ids(order)
    return sum(table.blocks[b]["f"]["focal"] -
               table.blocks[b]["f"][f"ref{j}"] for b in ids) / len(ids)


def _require_table(table: Any) -> None:
    if not isinstance(table, BlockTable):
        raise ProtocolError(
            "primary estimators accept a BlockTable only — a response-level "
            "input would resample the wrong unit (prereg §12)")


#: The estimator functions covered by the §12 signature check.
PRIMARY_ESTIMATORS = (block_contrast, tau_by_order, delta,
                      per_reference_contrast)

#: Parameter names that would indicate a response-level API; asserted absent.
FORBIDDEN_PARAMETERS = frozenset(
    {"response", "responses", "row", "rows", "replicate", "pool_index",
     "generation", "response_index", "row_index"})


def assert_block_indexed_signatures() -> None:
    import inspect

    for fn in PRIMARY_ESTIMATORS:
        parameters = set(inspect.signature(fn).parameters)
        clash = parameters & FORBIDDEN_PARAMETERS
        if clash:
            raise ProtocolError(
                f"{fn.__name__} accepts response-level parameter(s) {clash}")
        if "table" not in parameters:
            raise ProtocolError(f"{fn.__name__} does not take a BlockTable")
