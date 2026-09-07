"""The topic-resampled methodology-validation replicate (2026-09-07).

Every v8 root of a model — the v8 roots, the v8.1 successor roots and their
re-executions — screens and calibrates the *same* topics: the bank's
pre-freeze sets are fixed (v4r2's split, carried unchanged, §6.2) and every
stage uses each set in full. The re-executions therefore measured decoding
nondeterminism only. A topic-resampled replicate must vary the topics, and
the pre-freeze pool is exactly the three sets the pilot spends —
``prescreen`` (24), ``calibration_a`` (96), ``calibration_b`` (96) — 216
topics, 18 per area. So a replicate is a fresh, area-stratified random
partition of those 216 topics into the same three roles under a new,
domain-separated seed. Every stage then sees a different sample: the screen
shares about 2.7 of its 24 topics with the pilot's screen, each calibration
grid about 43 of its 96 with the pilot's same-role grid, and the calibration
union about 171 of 192 — the pool bounds how different the union can be.

The reserved sets (``composed``, ``confirmatory``, ``sequestered``) are
carried untouched and never materialised for the replicate. The replicate
runs in its own namespace with its own study id, which ``confirm.pilot_import``
refuses, so nothing it produces can be bound by a freeze. It is
methodology-validation evidence only.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import domain_int
from dci1v5.topics.bank import (TopicBank, assert_calibration_sets_disjoint,
                                assert_per_area, assert_sets_disjoint,
                                load_bank)
from dci1v7.protocol import constants as C
from dci1v7.protocol import seeds as _v7
from dci1v8dev.run import stages as S

__all__ = ["DOMAIN_TOPIC_REPLICATE", "REPLICATE_INDEX", "RESAMPLED_SETS",
           "replicate_split_seed", "repartition", "ReplicateTopicBank",
           "bank_for", "overlap_with"]

#: Domain-separated from every v7 and v8 generation, bootstrap and screen
#: domain: a replicate partition can coincide with no other draw.
DOMAIN_TOPIC_REPLICATE = "dci1v8:topicrep:v1"
assert DOMAIN_TOPIC_REPLICATE not in _v7.V4R3_DOMAINS
#: The single registered replicate of 2026-09-07. A second replicate would be
#: a new index, never a re-draw of this one.
REPLICATE_INDEX = 1
#: The three pre-freeze roles the pilot spends, re-partitioned as one pool.
RESAMPLED_SETS = ("prescreen", C.CALIBRATION_A, C.CALIBRATION_B)


def replicate_split_seed(index: int = REPLICATE_INDEX) -> int:
    """Root: the carried topic-split seed; domain: the replicate's own."""
    if index is None or index < 1:
        raise ProtocolError("a replicate index is a positive integer")
    return domain_int(DOMAIN_TOPIC_REPLICATE, _v7.CARRIED_TOPIC_SPLIT_SEED,
                      "topic-replicate", index, bits=63)


@dataclass(frozen=True)
class ReplicateTopicBank(TopicBank):
    """A bank whose pre-freeze roles were re-drawn; says so in its identity."""
    replicate_index: int = REPLICATE_INDEX
    replicate_seed: int = 0
    carried_split_hash: str = ""

    @property
    def split_identity(self) -> dict[str, Any]:
        base = dict(TopicBank.split_identity.fget(self))
        base["split_seed"] = (f"topic-replicate {self.replicate_index}: "
                              f"{DOMAIN_TOPIC_REPLICATE} seed "
                              f"{self.replicate_seed} over the carried "
                              f"pre-freeze pool (carried split "
                              f"{self.carried_split_hash[:16]})")
        base["topic_replicate"] = {"index": self.replicate_index,
                                   "seed": self.replicate_seed,
                                   "domain": DOMAIN_TOPIC_REPLICATE,
                                   "resampled_sets": list(RESAMPLED_SETS),
                                   "carried_split_hash":
                                       self.carried_split_hash}
        return base


def repartition(bank: TopicBank, *, index: int = REPLICATE_INDEX
                ) -> ReplicateTopicBank:
    """A fresh area-stratified partition of the pre-freeze pool into the
    pilot's three roles, same sizes per area; reserved sets untouched."""
    seed = replicate_split_seed(index)
    rng = random.Random(seed)
    pool: dict[str, list[dict[str, Any]]] = {}
    for name in RESAMPLED_SETS:
        for topic in bank.topics(name):
            pool.setdefault(topic["area"], []).append(dict(topic))
    if len(pool) != C.N_AREAS:
        raise ProtocolError(f"the pre-freeze pool spans {len(pool)} areas; "
                            f"§6.2 registers {C.N_AREAS}")
    per_area = {name: C.SET_SIZES[name] // C.N_AREAS for name in RESAMPLED_SETS}
    new: dict[str, list[dict[str, Any]]] = {name: [] for name in RESAMPLED_SETS}
    for area in sorted(pool):
        topics = sorted(pool[area], key=lambda t: t["topic_id"])
        if len(topics) != sum(per_area.values()):
            raise ProtocolError(f"area {area!r} holds {len(topics)} pre-freeze "
                                f"topics; expected {sum(per_area.values())}")
        rng.shuffle(topics)
        start = 0
        for name in RESAMPLED_SETS:
            take = per_area[name]
            for topic in topics[start:start + take]:
                topic["set"] = name
                new[name].append(topic)
            start += take
    sets: dict[str, tuple[dict[str, Any], ...]] = {
        name: (tuple(sorted(new[name], key=lambda t: t["topic_id"]))
               if name in RESAMPLED_SETS else bank.sets[name])
        for name in C.TOPIC_SETS}
    for name in RESAMPLED_SETS:
        assert_per_area(sets[name], expected=per_area[name],
                        where=f"replicate:{name}")
    populated = {k: v for k, v in sets.items() if v}
    assert_sets_disjoint(populated)
    assert_calibration_sets_disjoint(populated)
    carried = {t["topic_id"] for n in RESAMPLED_SETS for t in bank.topics(n)}
    drawn = {t["topic_id"] for n in RESAMPLED_SETS for t in sets[n]}
    if carried != drawn:
        raise ProtocolError("the replicate partition spent a topic outside "
                            "the carried pre-freeze pool or lost one")
    return ReplicateTopicBank(sets=sets,
                              calibration_b_status=bank.calibration_b_status,
                              replicate_index=index, replicate_seed=seed,
                              carried_split_hash=bank.split_identity["split_hash"])


def bank_for(context: Any, *, bank: TopicBank | None = None) -> TopicBank:
    """The bank a stage runs on: the carried one in every namespace but the
    replicate's, where it is the re-partitioned one. A caller-supplied bank
    is honoured (the synthetic walk and the tests build their own)."""
    if bank is not None:
        return bank
    if getattr(context, "namespace", None) == S.TOPIC_REPLICATE_NAMESPACE:
        return repartition(load_bank(), index=REPLICATE_INDEX)
    return load_bank()


def overlap_with(bank: TopicBank, other: TopicBank) -> dict[str, dict[str, int]]:
    """How many topics each pre-freeze role shares between two banks."""
    out = {}
    for name in RESAMPLED_SETS:
        a = {t["topic_id"] for t in bank.topics(name)}
        b = {t["topic_id"] for t in other.topics(name)}
        out[name] = {"shared": len(a & b), "size": len(a)}
    ua = {t["topic_id"] for n in (C.CALIBRATION_A, C.CALIBRATION_B) for t in bank.topics(n)}
    ub = {t["topic_id"] for n in (C.CALIBRATION_A, C.CALIBRATION_B) for t in other.topics(n)}
    out["calibration_union"] = {"shared": len(ua & ub), "size": len(ua)}
    return out
