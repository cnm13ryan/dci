"""Stage cell plans: which (block, arm) prompts each stage generates.

Every plan is a pure function of frozen design facts (topic split, block
rules, calibrated parameters); prompts are exact bytes from
`design.prompts.compose`, so the same plan always yields the same prompt
hashes — the frozen prompt plan of the evidence hierarchy (task §7).
"""
from __future__ import annotations

from dci1.constraints.wordings import wording
from dci1.design.blocks import Block, build_blocks, order_for_index
from dci1.design.prompts import compose, prompt_for_cell
from dci1.generation.pools import Cell
from dci1.protocol.constants import (
    ARMS,
    GREEDY_BLOCKS,
    M_GRID,
    N_GRID,
    PILOT_PROVISIONAL,
    PILOT_TOPICS,
    PRIMARY_ARMS,
    SUBJECT_AREAS,
    ProtocolError,
)
from dci1.topics.split import split_bank


def confirmatory_blocks() -> list[Block]:
    return build_blocks(split_bank()["confirmatory"])


def confirmatory_cells(n: int, m: int,
                       references: tuple[str, str, str]) -> list[Cell]:
    """The 384 × 6 registered confirmatory cells."""
    cells = []
    for block in confirmatory_blocks():
        for arm in ARMS:
            cells.append(Cell(
                block_id=block.block_id, arm=arm,
                prompt=prompt_for_cell(block, arm, n=n, m=m,
                                       references=references)))
    return cells


def greedy_cells(n: int, m: int,
                 references: tuple[str, str, str]) -> list[Cell]:
    """The §8 greedy sensitivity replication: first 96 blocks × 4 primary arms."""
    cells = []
    for block in confirmatory_blocks()[:GREEDY_BLOCKS]:
        for arm in PRIMARY_ARMS:
            cells.append(Cell(
                block_id=block.block_id, arm=arm,
                prompt=prompt_for_cell(block, arm, n=n, m=m,
                                       references=references)))
    return cells


# ---------------------------------------------------------------- pilot (D15)
def pilot_blocks() -> list[Block]:
    """Twelve pilot blocks: the first calibration topic of each stratum.

    Order and target wording follow the confirmatory formulas; the added
    wording uses ``j // 3`` so all four wordings of both constraints are
    represented across twelve blocks (§17; D15).
    """
    calibration = split_bank()["calibration"]
    picks = []
    for stratum_index, area in enumerate(SUBJECT_AREAS):
        area_topics = [t for t in calibration if t["area"] == area]
        picks.append(area_topics[0])
    if len(picks) != PILOT_TOPICS:
        raise ProtocolError("pilot topic selection failed")
    blocks = []
    for j, topic in enumerate(picks):
        blocks.append(Block(
            index=j, block_id=f"P{j:02d}", topic_id=topic["topic_id"],
            question=topic["question"], order=order_for_index(j),
            wording_target=j % 4, wording_added=j // 3))
    return blocks


def pilot_cells() -> list[Cell]:
    """The 72 pilot cells under the provisional, discarded parameters."""
    n = PILOT_PROVISIONAL["n"]
    m = PILOT_PROVISIONAL["m"]
    references = tuple(PILOT_PROVISIONAL["references"])
    cells = []
    for block in pilot_blocks():
        for arm in ARMS:
            cells.append(Cell(
                block_id=block.block_id, arm=arm,
                prompt=prompt_for_cell(block, arm, n=n, m=m,
                                       references=references)))
    return cells


# -------------------------------------------------------- calibration (D14)
def calibration_conditions() -> list[dict]:
    """The 19 solo conditions of Gate 2: A over the n grid, B over the m
    grid, and each pool candidate."""
    conditions = [{"solo_id": f"A:n={n}", "constraint_id": "A", "n": n,
                   "m": None} for n in N_GRID]
    conditions += [{"solo_id": f"B:m={m}", "constraint_id": "B", "n": None,
                    "m": m} for m in M_GRID]
    from dci1.constraints.definitions import CANDIDATE_IDS

    conditions += [{"solo_id": cid, "constraint_id": cid, "n": None,
                    "m": None} for cid in CANDIDATE_IDS]
    return conditions


def calibration_cells() -> list[Cell]:
    """96 calibration topics × 19 solo prompts, wording rotated by topic
    position (p mod 4, decision D14)."""
    calibration = split_bank()["calibration"]
    cells = []
    for position, topic in enumerate(calibration):
        wording_index = position % 4
        for condition in calibration_conditions():
            text = wording(condition["constraint_id"], wording_index,
                           n=condition["n"], m=condition["m"])
            cells.append(Cell(
                block_id=topic["topic_id"],
                arm=f"solo:{condition['solo_id']}",
                prompt=compose(topic["question"], (text,))))
    return cells
