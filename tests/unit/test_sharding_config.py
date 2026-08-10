"""A malformed shard configuration must fail before any batch is processed.

The previous reading treated any unusable field as "not sharded". A worker
launched with --shard-index 1 and no --shard-total therefore processed EVERY
batch: under a two-worker launch that is the whole plan generated twice, at
double the GPU cost, with the completeness barrier satisfied by one worker while
the operator believed the work had been split. Validation also happened lazily
inside the first shard_filter call, which is after the pipeline has built state
and reached a generation stage.
"""
import dataclasses

import pytest

from dci.config import loader
from dci.config.loader import activate
from dci.pipeline import runner
from dci.pipeline.sharding import (ShardConfigError, shard_config, shard_filter,
                                   validate_sharding)

pytestmark = pytest.mark.cpu


@pytest.fixture(autouse=True)
def restore_active():
    saved = dataclasses.replace(loader.ACTIVE)
    yield
    activate(saved)


def _shards(index, total):
    activate(dataclasses.replace(loader.ACTIVE, shard_index=index,
                                 shard_total=total))


PLAN = [{"batch_index": i} for i in range(6)]


# ------------------------------------------------------- incomplete pairs
@pytest.mark.parametrize("index,total", [(1, None), (0, None), (None, 4)])
def test_one_field_alone_is_refused_not_read_as_unsharded(index, total):
    _shards(index, total)
    with pytest.raises(ShardConfigError, match="incomplete shard configuration"):
        shard_config()
    with pytest.raises(ShardConfigError):
        validate_sharding()
    # And it cannot reach the assignment path at all.
    with pytest.raises(ShardConfigError):
        shard_filter("c292", PLAN, PLAN)


def test_neither_field_is_an_unsharded_worker():
    _shards(None, None)
    assert shard_config() is None
    assert shard_filter("c292", PLAN, PLAN) == PLAN
    validate_sharding()


# ---------------------------------------------------------- invalid values
@pytest.mark.parametrize("total", [0, -1, -4])
def test_a_total_below_one_is_refused(total):
    _shards(0, total)
    with pytest.raises(ShardConfigError, match="not a usable worker count"):
        validate_sharding()


@pytest.mark.parametrize("index", [-1, 4, 99])
def test_an_out_of_range_index_is_refused(index):
    _shards(index, 4)
    with pytest.raises(ShardConfigError, match="out of range"):
        validate_sharding()


def test_an_out_of_range_index_with_total_one_is_still_refused():
    """total=1 used to short-circuit before the index was ever looked at."""
    _shards(5, 1)
    with pytest.raises(ShardConfigError, match="out of range"):
        validate_sharding()


@pytest.mark.parametrize("index,total", [(True, 2), (0, True)])
def test_booleans_are_not_accepted_as_shard_integers(index, total):
    _shards(index, total)
    with pytest.raises(ShardConfigError):
        validate_sharding()


# ------------------------------------------------------------ valid configs
def test_a_declared_single_worker_owns_every_batch():
    _shards(0, 1)
    assert shard_config() is None
    assert shard_filter("c292", PLAN, PLAN) == PLAN


@pytest.mark.parametrize("index", [0, 1, 2])
def test_a_valid_pair_partitions_the_plan(index):
    _shards(index, 3)
    assert shard_config() == (index, 3)
    mine = shard_filter("c292", PLAN, PLAN)
    assert [b["batch_index"] for b in mine] == [index, index + 3]


def test_the_three_shards_partition_the_plan_exactly_once():
    seen = []
    for index in range(3):
        _shards(index, 3)
        seen += [b["batch_index"] for b in shard_filter("c292", PLAN, PLAN)]
    assert sorted(seen) == [b["batch_index"] for b in PLAN]


# ------------------------------------- the runner classifies it at startup
def test_the_runner_refuses_a_malformed_shard_before_running_a_stage(monkeypatch):
    _shards(3, None)
    called = []
    monkeypatch.setattr(runner, "_purge", lambda: called.append("purge"))
    monkeypatch.setattr(runner, "stage_order",
                        lambda: called.append("order") or ["c112"])
    assert runner.run_pipeline() == runner.EXIT_ENVIRONMENT
    assert called == []          # neither state reset nor stage discovery ran
