"""The seeded five-way topic split (§6.2) and the confirmatory block plan.

Within each of the twelve strata the 52 authored questions are shuffled with
a fixed per-area seed and cut into 2 pre-screen, 8 solo calibration, 2
composed validation, 32 confirmatory and 8 sequestered topics — 24 / 96 / 24
/ 384 / 96 in total, all five disjoint. The cut is performed once by the
access-control tool, which writes the released four sets into the bank and
the sequestered eighth into the opaque manifest; this module re-derives the
released split from the recorded set labels and re-checks every count, so a
tampered bank cannot pass.

A **block** is a confirmatory topic together with the wording indices assigned
to it. Order is *not* a block property in v4: §8.4 makes it a cell-level
factor, so every block runs both order variants of every composed cell and
each configuration is estimated on all 384 blocks. The v3 block-level
``target_first`` / ``added_first`` strata do not exist here, and no block
carries an order field for a rule to key on.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.seeds import TOPIC_SPLIT_SEED, area_split_seed
from dci1v4.topics.bank import load_bank
from dci1v4.topics.sequestered import assert_no_materialisation

#: The order the per-area shuffle is cut into sets. Sequestered is last so the
#: released four can be re-derived without the sequestered texts.
CUT_ORDER = (("prescreen", C.PRESCREEN_PER_AREA), ("solo", C.SOLO_PER_AREA),
             ("composed", C.COMPOSED_PER_AREA),
             ("confirmatory", C.CONFIRMATORY_PER_AREA),
             ("sequestered", C.SEQUESTERED_PER_AREA))


@dataclass(frozen=True)
class Block:
    """One confirmatory or pilot block: a topic and its two wording indices.

    ``w1`` and ``w2`` are the §8.4 block-level wording indices for the first
    and second constituent of a composed cell in registered slot order, and
    ``w1`` is also the solo-cell wording index. There is no order field: order
    is decided per cell, not per block.
    """

    block_id: str
    index: int
    topic_id: str
    area: str
    question: str
    w1: int
    w2: int


def cut_area(questions: list[str], area: str,
             root: int = TOPIC_SPLIT_SEED) -> dict[str, list[str]]:
    """The seeded per-stratum cut. Used by the access-control tool and by the
    verification path; identical arithmetic in both."""
    if len(questions) != C.TOPICS_PER_AREA:
        raise ProtocolError(f"{area!r} carries {len(questions)} questions, "
                            f"not {C.TOPICS_PER_AREA}")
    ordered = sorted(questions)
    random.Random(area_split_seed(root, area)).shuffle(ordered)
    out: dict[str, list[str]] = {}
    start = 0
    for set_name, size in CUT_ORDER:
        out[set_name] = ordered[start:start + size]
        start += size
    if start != C.TOPICS_PER_AREA:
        raise ProtocolError("the five-way cut does not consume the stratum")
    return out


def split_topics(topics: list[dict[str, Any]] | None = None
                 ) -> dict[str, list[dict[str, Any]]]:
    """The four released sets, stratum-major in the frozen seeded order."""
    topics = topics if topics is not None else load_bank()
    assert_no_materialisation(topics)
    result: dict[str, list[dict[str, Any]]] = {
        "prescreen": [], "solo": [], "composed": [], "confirmatory": []}
    for area in C.SUBJECT_AREAS:
        in_area = sorted((t for t in topics if t["area"] == area),
                         key=lambda t: t["topic_id"])
        for set_name in result:
            members = [t for t in in_area if t["set"] == set_name]
            expected = dict(CUT_ORDER)[set_name]
            if len(members) != expected:
                raise ProtocolError(
                    f"{area!r} carries {len(members)} {set_name} topics, "
                    f"not {expected}")
            result[set_name].extend(members)
    counts = {k: len(v) for k, v in result.items()}
    expected = {"prescreen": C.N_PRESCREEN, "solo": C.N_SOLO,
                "composed": C.N_COMPOSED, "confirmatory": C.N_CONFIRMATORY}
    if counts != expected:
        raise ProtocolError(f"split counts {counts} != {expected}")
    ids = [t["topic_id"] for part in result.values() for t in part]
    if len(set(ids)) != len(ids):
        raise ProtocolError("the released splits are not disjoint")
    return result


def prescreen_cap_set(split: dict[str, list[dict[str, Any]]] | None = None
                      ) -> list[dict[str, Any]]:
    """The §12.1 cap-selection topics: the 24 pre-screen topics, each used at
    load zero, one and two, giving the subject-balanced 96-prompt set that
    §12.1 requires to contain all three loads (see design/cells.py)."""
    split = split or split_topics()
    return split["prescreen"]


def pilot_topics(split: dict[str, list[dict[str, Any]]] | None = None
                 ) -> list[dict[str, Any]]:
    """The twelve fixed procedural-pilot topics: the first pre-screen topic of
    each stratum, in stratum order (§19)."""
    split = split or split_topics()
    chosen = [next(t for t in split["prescreen"] if t["area"] == area)
              for area in C.SUBJECT_AREAS]
    if len(chosen) != C.PILOT_TOPICS:
        raise ProtocolError("pilot topic derivation failed")
    return chosen


def _block(index: int, topic: dict[str, Any]) -> Block:
    """§8.4: w(c1) = i mod 4 and w(c2) = (i + floor(i/4)) mod 4.

    The offset de-correlates the two wording indices. Under v4's cell-level
    order there is no collision with an order-by-parity rule to avoid, and the
    offset is still required so that the two constituents of a composed cell
    do not always carry the same wording.
    """
    return Block(block_id=f"b{index:03d}-{topic['topic_id']}", index=index,
                 topic_id=topic["topic_id"], area=topic["area"],
                 question=topic["question"],
                 w1=index % 4, w2=(index + index // 4) % 4)


def confirmatory_blocks(split: dict[str, list[dict[str, Any]]] | None = None
                        ) -> list[Block]:
    """The 384 frozen confirmatory blocks."""
    split = split or split_topics()
    blocks = [_block(i, topic)
              for i, topic in enumerate(split["confirmatory"])]
    assert_block_coverage(blocks, blocks_expected=C.N_BLOCKS)
    return blocks


def pilot_blocks(split: dict[str, list[dict[str, Any]]] | None = None
                 ) -> list[Block]:
    """The 12 procedural-pilot blocks under the same wording allocation."""
    blocks = [_block(i, topic) for i, topic in enumerate(pilot_topics(split))]
    if len(blocks) != C.PILOT_TOPICS:
        raise ProtocolError("pilot block derivation failed")
    return blocks


def assert_block_coverage(blocks: list[Block], *, blocks_expected: int) -> None:
    """§8.4: each wording index appears in a quarter of the blocks for each
    constituent slot. The cell-level order assertion lives in design/cells.py,
    where order actually exists."""
    if len(blocks) != blocks_expected:
        raise ProtocolError(f"{len(blocks)} blocks, expected "
                            f"{blocks_expected}")
    if len({b.index for b in blocks}) != blocks_expected:
        raise ProtocolError("duplicate block indices")
    if len({b.topic_id for b in blocks}) != blocks_expected:
        raise ProtocolError("duplicate topics across blocks")
    for attr in ("w1", "w2"):
        per = {w: sum(1 for b in blocks if getattr(b, attr) == w)
               for w in range(4)}
        if any(count != blocks_expected // 4 for count in per.values()):
            raise ProtocolError(f"{attr} allocation {per} is unbalanced; a "
                                f"structural zero or skew is refused")


def split_hash(split: dict[str, list[dict[str, Any]]] | None = None) -> str:
    """The recorded split hash for the registration manifest (check C17)."""
    from dci1v4.protocol.hashing import sha_obj

    split = split or split_topics()
    return sha_obj({name: [t["topic_id"] for t in members]
                    for name, members in sorted(split.items())})
