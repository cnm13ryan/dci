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


def _cfg():
    from dci.config.loader import ACTIVE
    if ACTIVE.shard_index is None or not ACTIVE.shard_total or ACTIVE.shard_total <= 1:
        return None
    if not (0 <= ACTIVE.shard_index < ACTIVE.shard_total):
        raise ValueError(f"shard {ACTIVE.shard_index}/{ACTIVE.shard_total} is invalid")
    return ACTIVE.shard_index, ACTIVE.shard_total


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
