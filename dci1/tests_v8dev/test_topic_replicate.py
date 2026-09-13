"""The topic-resampled methodology-validation replicate.

`docs/V8_TOPIC_RESAMPLED_VALIDATION.md` prespecifies a fresh area-stratified
partition of the 216 pre-freeze topics into the pilot's three roles under a
domain-separated seed. These tests pin what the partition may and may not
do, and that a replicate root cannot enter a freeze.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.protocol import seeds as _v7
from dci1v7.topics.bank import load_bank
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import (STUDY_ID_OF_NAMESPACE,
                                   TOPIC_REPLICATE_STUDY_ID)
from dci1v8dev.run.topic_replicate import (DOMAIN_TOPIC_REPLICATE,
                                           RESAMPLED_SETS, bank_for,
                                           overlap_with, repartition,
                                           replicate_split_seed)

RESERVED = ("composed", "confirmatory", "sequestered")


@pytest.fixture(scope="module")
def carried():
    return load_bank()


@pytest.fixture(scope="module")
def replicate(carried):
    return repartition(carried)


def test_the_seed_is_domain_separated_and_deterministic():
    assert DOMAIN_TOPIC_REPLICATE.startswith("dci1v8:")
    assert DOMAIN_TOPIC_REPLICATE not in _v7.V4R3_DOMAINS
    assert replicate_split_seed(1) == replicate_split_seed(1)
    assert replicate_split_seed(1) != replicate_split_seed(2)
    with pytest.raises(ProtocolError):
        replicate_split_seed(0)


def test_the_partition_is_deterministic(carried):
    a, b = repartition(carried), repartition(load_bank())
    assert a.split_identity["split_hash"] == b.split_identity["split_hash"]


def test_the_roles_keep_their_registered_sizes_and_area_balance(replicate):
    for name in RESAMPLED_SETS:
        topics = replicate.topics(name)
        assert len(topics) == C.SET_SIZES[name]
        per_area = C.SET_SIZES[name] // C.N_AREAS
        counts = {}
        for t in topics:
            counts[t["area"]] = counts.get(t["area"], 0) + 1
        assert set(counts.values()) == {per_area}
        assert len(counts) == C.N_AREAS


def test_it_spends_the_pre_freeze_pool_exactly(carried, replicate):
    pool = {t["topic_id"] for n in RESAMPLED_SETS for t in carried.topics(n)}
    drawn = {t["topic_id"] for n in RESAMPLED_SETS for t in replicate.topics(n)}
    assert drawn == pool
    seen = [t["topic_id"] for n in RESAMPLED_SETS for t in replicate.topics(n)]
    assert len(seen) == len(set(seen)), "a topic was dealt into two roles"


def test_the_reserved_sets_are_untouched(carried, replicate):
    for name in RESERVED:
        assert replicate.topics(name) == carried.topics(name)
    conf = {t["topic_id"] for t in carried.topics("confirmatory")}
    drawn = {t["topic_id"] for n in RESAMPLED_SETS for t in replicate.topics(n)}
    assert not (conf & drawn), "a confirmatory topic entered the pre-freeze pool"


def test_the_sample_really_moved(carried, replicate):
    assert (replicate.split_identity["split_hash"]
            != carried.split_identity["split_hash"])
    overlap = overlap_with(replicate, carried)
    # A uniform re-deal shares 24*24/216 ≈ 2.7 prescreen and 96*96/216 ≈ 42.7
    # calibration topics with the carried split; the pool bounds the union.
    assert overlap["prescreen"]["shared"] <= 8, overlap
    assert overlap[C.CALIBRATION_A]["shared"] <= 64, overlap
    assert overlap["calibration_union"]["shared"] >= 150, overlap


def test_the_replicate_identity_is_recorded(replicate):
    ident = replicate.split_identity
    assert "topic-replicate" in ident["split_seed"]
    assert ident["topic_replicate"]["domain"] == DOMAIN_TOPIC_REPLICATE
    assert ident["topic_replicate"]["seed"] == replicate_split_seed()
    assert ident["topic_replicate"]["carried_split_hash"]


class _Ctx:
    def __init__(self, namespace):
        self.namespace = namespace


def test_only_the_replicate_namespace_gets_the_repartitioned_bank(carried):
    pilot = bank_for(_Ctx("pilot"))
    rep = bank_for(_Ctx(S.TOPIC_REPLICATE_NAMESPACE))
    assert pilot.split_identity["split_hash"] == carried.split_identity["split_hash"]
    assert rep.split_identity["split_hash"] != carried.split_identity["split_hash"]
    supplied = bank_for(_Ctx(S.TOPIC_REPLICATE_NAMESPACE), bank=carried)
    assert supplied is carried, "a supplied bank must be honoured"


def test_a_replicate_root_cannot_be_bound_by_a_freeze():
    from dci1v8dev.run import STUDY_ID

    assert STUDY_ID_OF_NAMESPACE[S.TOPIC_REPLICATE_NAMESPACE] == \
        TOPIC_REPLICATE_STUDY_ID
    assert TOPIC_REPLICATE_STUDY_ID != STUDY_ID
    import inspect

    from dci1v8dev.confirm import pilot_import

    src = inspect.getsource(pilot_import.open_pilot)
    assert "expected = SYNTHETIC_STUDY_ID if synthetic else STUDY_ID" in src
    assert "TOPIC_REPLICATE" not in src, \
        "the confirm layer must not learn about the replicate namespace"
