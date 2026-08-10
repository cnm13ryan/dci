"""Deterministic batch-to-worker assignment from the frozen plan."""
import pytest

from dci.config import loader
from dci.pipeline.sharding import shard_filter

pytestmark = pytest.mark.cpu
PLAN = [{"batch_index": i, "row_ids": [f"r{i}"]} for i in range(11)]


def _with(idx, total):
    loader.activate(loader.ActiveConfig(shard_index=idx, shard_total=total))


def teardown_function(_):
    loader.activate(loader.ActiveConfig())


def test_partition_is_exact_and_disjoint():
    _with(0, 3); a = shard_filter("s", PLAN, PLAN)
    _with(1, 3); b = shard_filter("s", PLAN, PLAN)
    _with(2, 3); c = shard_filter("s", PLAN, PLAN)
    ids = [x["batch_index"] for x in a + b + c]
    assert sorted(ids) == list(range(11))
    assert len(set(ids)) == 11


def test_assignment_ignores_pending_order():
    _with(1, 2)
    fwd = shard_filter("s", PLAN, PLAN)
    rev = shard_filter("s", PLAN, list(reversed(PLAN)))
    assert {x["batch_index"] for x in fwd} == {x["batch_index"] for x in rev}


def test_unsharded_is_identity():
    loader.activate(loader.ActiveConfig())
    assert shard_filter("s", PLAN, PLAN) is PLAN or shard_filter("s", PLAN, PLAN) == PLAN


def test_invalid_shard_rejected():
    _with(3, 2)
    with pytest.raises(ValueError):
        shard_filter("s", PLAN, PLAN)
