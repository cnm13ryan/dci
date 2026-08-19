"""Block construction (prereg §7, §8, §12; decision D13).

A block is one confirmatory topic together with its fixed presentation order
and fixed wording indices. Block index i over the stratum-major confirmatory
topic order determines, identically for all six arms of the block:

* presentation order — even i: target first; odd i: added first;
* wording index for A — ``i mod 4``;
* wording index for the added constraint — ``(i // 4) mod 4``.
"""
from __future__ import annotations

from dataclasses import dataclass

from dci1.protocol.constants import (
    ARMS,
    N_BLOCKS,
    N_WORDINGS,
    PRIMARY_ARMS,
    ProtocolError,
)

TARGET_FIRST = "target_first"
ADDED_FIRST = "added_first"


@dataclass(frozen=True)
class Block:
    index: int
    block_id: str
    topic_id: str
    question: str
    order: str
    wording_target: int
    wording_added: int


def order_for_index(index: int) -> str:
    return TARGET_FIRST if index % 2 == 0 else ADDED_FIRST


def wording_target_for_index(index: int) -> int:
    return index % N_WORDINGS


def wording_added_for_index(index: int) -> int:
    return (index // N_WORDINGS) % N_WORDINGS


def build_blocks(confirmatory_topics: list[dict]) -> list[Block]:
    """The 384 confirmatory blocks, in frozen stratum-major topic order (D13).

    ``confirmatory_topics`` must already be in the split's frozen order; each
    entry carries ``topic_id`` and ``question``.
    """
    if len(confirmatory_topics) != N_BLOCKS:
        raise ProtocolError(
            f"expected {N_BLOCKS} confirmatory topics, got "
            f"{len(confirmatory_topics)}")
    blocks = []
    for i, topic in enumerate(confirmatory_topics):
        blocks.append(Block(
            index=i,
            block_id=f"B{i:03d}",
            topic_id=topic["topic_id"],
            question=topic["question"],
            order=order_for_index(i),
            wording_target=wording_target_for_index(i),
            wording_added=wording_added_for_index(i),
        ))
    return blocks


def assert_block_plan(blocks: list[Block]) -> dict:
    """Executable §7/§8 structure checks: order balance, wording coverage."""
    if len(blocks) != N_BLOCKS:
        raise ProtocolError("wrong block count")
    per_order = {TARGET_FIRST: 0, ADDED_FIRST: 0}
    for block in blocks:
        per_order[block.order] += 1
    if per_order[TARGET_FIRST] != per_order[ADDED_FIRST]:
        raise ProtocolError(f"presentation order unbalanced: {per_order}")
    if len({b.block_id for b in blocks}) != N_BLOCKS:
        raise ProtocolError("duplicate block ids")
    if len({b.topic_id for b in blocks}) != N_BLOCKS:
        raise ProtocolError("duplicate topics across blocks")
    return {"blocks": len(blocks), "per_order": per_order,
            "arms": list(ARMS), "primary_arms": list(PRIMARY_ARMS)}
