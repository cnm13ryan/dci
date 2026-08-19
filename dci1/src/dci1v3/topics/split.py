"""Seeded topic split and block plan (§6, §7).

Within each stratum the 12 calibration topics are shuffled with the fixed
per-area seed and cut into 2 pre-screen / 8 final-solo / 2 composed-validation
topics; the 32 confirmatory topics are shuffled with the same seed scheme
into their frozen block order. Confirmatory block index i (stratum-major)
fixes presentation order i mod 2 (even = target first), target wording
i mod 4, and added wording floor(i/4) mod 4. The twelve procedural-pilot
topics are the first pre-screen topic of each stratum.

Every generative stage has an executable allocation assertion; a formula is
secondary to its coverage assertion (§7).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from dci1v3.errors import ProtocolError
from dci1v3.protocol import constants as C
from dci1v3.protocol.seeds import area_split_seed
from dci1v3.topics.bank import load_bank
from dci1v3.topics.sequestered import assert_no_materialisation


@dataclass(frozen=True)
class Block:
    """One confirmatory or pilot block: topic + frozen order and wordings."""

    block_id: str
    index: int
    topic_id: str
    area: str
    question: str
    order: str
    target_wording: int
    added_wording: int


def split_topics(topics: list[dict[str, Any]] | None = None
                 ) -> dict[str, list[dict[str, Any]]]:
    """{"prescreen": 24, "solo": 96, "composed": 24, "confirmatory": 384},
    each stratum-major in the frozen seeded order."""
    topics = topics if topics is not None else load_bank()
    assert_no_materialisation(topics)
    result: dict[str, list[dict[str, Any]]] = {
        "prescreen": [], "solo": [], "composed": [], "confirmatory": []}
    for area in C.SUBJECT_AREAS:
        rng = random.Random(area_split_seed(C.TOPIC_SPLIT_SEED, area))
        calibration = [t for t in topics
                       if t["area"] == area and t["set"] == "calibration"]
        confirmatory = [t for t in topics
                        if t["area"] == area and t["set"] == "confirmatory"]
        if (len(calibration) != C.CALIBRATION_PER_AREA
                or len(confirmatory) != C.CONFIRMATORY_PER_AREA):
            raise ProtocolError(f"stratum {area!r} has the wrong topic counts")
        calibration = sorted(calibration, key=lambda t: t["topic_id"])
        confirmatory = sorted(confirmatory, key=lambda t: t["topic_id"])
        rng.shuffle(calibration)
        rng.shuffle(confirmatory)
        result["prescreen"].extend(calibration[:C.PRESCREEN_PER_AREA])
        result["solo"].extend(
            calibration[C.PRESCREEN_PER_AREA:
                        C.PRESCREEN_PER_AREA + C.SOLO_PER_AREA])
        result["composed"].extend(
            calibration[C.PRESCREEN_PER_AREA + C.SOLO_PER_AREA:])
        result["confirmatory"].extend(confirmatory)
    counts = {k: len(v) for k, v in result.items()}
    expected = {"prescreen": C.N_PRESCREEN, "solo": C.N_SOLO,
                "composed": C.N_COMPOSED, "confirmatory": C.N_CONFIRMATORY}
    if counts != expected:
        raise ProtocolError(f"split counts {counts} != {expected}")
    ids = [t["topic_id"] for part in result.values() for t in part]
    if len(set(ids)) != len(ids):
        raise ProtocolError("splits are not disjoint")
    return result


def pilot_topics(split: dict[str, list[dict[str, Any]]] | None = None
                 ) -> list[dict[str, Any]]:
    """The twelve fixed pilot topics: the first pre-screen topic of each
    stratum, in stratum order (§6)."""
    split = split or split_topics()
    chosen = []
    for area in C.SUBJECT_AREAS:
        chosen.append(next(t for t in split["prescreen"]
                           if t["area"] == area))
    if len(chosen) != C.PILOT_TOPICS:
        raise ProtocolError("pilot topic derivation failed")
    return chosen


def _block(index: int, topic: dict[str, Any], *, order: str,
           target_wording: int, added_wording: int) -> Block:
    return Block(block_id=f"b{index:03d}-{topic['topic_id']}", index=index,
                 topic_id=topic["topic_id"], area=topic["area"],
                 question=topic["question"], order=order,
                 target_wording=target_wording, added_wording=added_wording)


def confirmatory_blocks(split: dict[str, list[dict[str, Any]]] | None = None
                        ) -> list[Block]:
    """The 384 frozen confirmatory blocks (§7 allocation)."""
    split = split or split_topics()
    blocks = [
        _block(i, topic,
               order=C.TARGET_FIRST if i % 2 == 0 else C.ADDED_FIRST,
               target_wording=i % 4, added_wording=(i // 4) % 4)
        for i, topic in enumerate(split["confirmatory"])]
    assert_coverage(blocks, blocks_expected=C.N_BLOCKS)
    return blocks


def pilot_blocks(split: dict[str, list[dict[str, Any]]] | None = None
                 ) -> list[Block]:
    """The 12 pilot blocks under the stage-specific §7 allocation."""
    topics = pilot_topics(split)
    blocks = [
        _block(i, topic,
               order=C.TARGET_FIRST if i % 2 == 0 else C.ADDED_FIRST,
               target_wording=i % 4, added_wording=(i + i // 4) % 4)
        for i, topic in enumerate(topics)]
    assert_coverage(blocks, blocks_expected=C.PILOT_TOPICS)
    return blocks


def assert_coverage(blocks: list[Block], *, blocks_expected: int) -> None:
    """§7: the executable allocation assertion. Each order must cover half
    the blocks and each wording index a quarter, exactly."""
    if len(blocks) != blocks_expected:
        raise ProtocolError(f"{len(blocks)} blocks, expected "
                            f"{blocks_expected}")
    if len({b.index for b in blocks}) != blocks_expected:
        raise ProtocolError("duplicate block indices")
    per_order = {order: sum(1 for b in blocks if b.order == order)
                 for order in C.ORDERS}
    if any(count != blocks_expected // 2 for count in per_order.values()):
        raise ProtocolError(f"order allocation {per_order} is unbalanced")
    for attr in ("target_wording", "added_wording"):
        per_wording = {w: sum(1 for b in blocks if getattr(b, attr) == w)
                       for w in range(4)}
        if any(count != blocks_expected // 4
               for count in per_wording.values()):
            raise ProtocolError(f"{attr} allocation {per_wording} "
                                f"is unbalanced")
