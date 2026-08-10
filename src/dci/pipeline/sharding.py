"""Deterministic multi-worker generation over the frozen batch plan.

Assignment is `batch_index % shard_total == shard_index`, a pure function of
the frozen plan — never of queue timing — so worker count and launch order
cannot change batch membership, seeds, or which rows exist. Each worker runs
the FULL pipeline with a complementary shard: workers generate disjoint batch
sets, commit to the shared per-batch journal (disjoint filenames, atomic
writes), then wait at the completeness barrier until the union of commits
covers the stage, and continue into identical deterministic computation. The
journal's idempotence means interruption and restart can neither duplicate a
committed batch (it is skipped as already served) nor drop one (the barrier
refuses to proceed without it), and a batch generated under a different
execution fingerprint is quarantined, not consumed — those properties are the
notebook's and are regression-tested, not re-implemented here.
"""
from __future__ import annotations

import time


class ShardConfigError(ValueError):
    """The shard configuration is malformed, so no work may begin.

    Kept distinct from the batch-assignment logic because the failure is a
    configuration refusal at startup, not a scientific or invariant failure.
    """


def shard_config():
    """The validated (index, total) pair, or None when sharding is not requested.

    Strictness is the point. The previous reading treated a missing or
    unusable field as "not sharded", so a worker launched with --shard-index 1
    and no --shard-total silently processed EVERY batch. Under a two-worker
    launch that is the whole plan generated twice: harmless for scientific
    identity, which is a pure function of the frozen plan, but it doubles cost
    and destroys the barrier's meaning - and the operator believed they had
    split the work.
    """
    from dci.config.loader import ACTIVE
    idx, total = ACTIVE.shard_index, ACTIVE.shard_total
    if idx is None and total is None:
        return None
    if (idx is None) != (total is None):
        raise ShardConfigError(
            f"incomplete shard configuration: shard_index={idx!r}, "
            f"shard_total={total!r}. Both must be given together; one alone is "
            "not an unsharded worker.")
    if isinstance(total, bool) or not isinstance(total, int) or total < 1:
        raise ShardConfigError(
            f"shard_total={total!r} is not a usable worker count; it must be an "
            "integer of at least 1.")
    if isinstance(idx, bool) or not isinstance(idx, int) or not (0 <= idx < total):
        raise ShardConfigError(
            f"shard_index={idx!r} is out of range for shard_total={total}; it "
            f"must satisfy 0 <= index < {total}.")
    if total == 1:
        # A declared single worker owns every batch, which is what an unsharded
        # run already does. Accepted and validated rather than inferred.
        return None
    return idx, total


def validate_sharding() -> None:
    """Startup gate: refuse a malformed shard configuration before any work.

    Validation used to happen lazily inside the first shard_filter call, which
    is after the pipeline has built state and reached a generation stage.
    """
    shard_config()


def _cfg():
    """Backwards-compatible alias for the validated configuration."""
    return shard_config()


def shard_filter(stage: str, plan: list[dict], pending: list[dict]) -> list[dict]:
    cfg = _cfg()
    if cfg is None:
        return pending
    idx, total = cfg
    mine = [b for b in pending if b["batch_index"] % total == idx]
    print(f"[{stage}] shard {idx}/{total}: {len(mine)} of {len(pending)} "
          "pending batches assigned to this worker (deterministic: "
          "batch_index mod shard_total).")
    return mine


def wait_for_stage_complete(stage: str, design, plan: list[dict],
                            poll_seconds: float = 5.0,
                            timeout_seconds: float = 7200.0) -> None:
    """Barrier: block until every planned row of this stage is committed."""
    cfg = _cfg()
    if cfg is None:
        return
    from dci.pipeline import state as S
    deadline = time.monotonic() + timeout_seconds
    needed = set(design["row_id"])
    while True:
        payload, _ = S.read_commits(stage, plan)
        missing = needed - set(payload)
        if not missing:
            return
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"[{stage}] shard barrier: {len(missing)} rows still "
                "uncommitted after the timeout. Another worker died or was "
                "never started; its shard is idempotent to rerun.")
        print(f"[{stage}] shard barrier: waiting for {len(missing)} rows from "
              "other workers...", flush=True)
        time.sleep(poll_seconds)
