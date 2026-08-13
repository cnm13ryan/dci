"""Two concurrent shard workers over one run directory must produce exactly the
unsharded result: no duplicated batch, no omitted batch, membership unchanged.
Assignment comes from the frozen plan (batch_index mod N), so launch order and
timing cannot matter; the barrier makes each worker wait for the union."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]


def _worker(shard: str, root: Path) -> subprocess.Popen:
    # Workers share one run identity explicitly; the id is operator-chosen and
    # deterministic, so restarts land in the same journal.
    return subprocess.Popen(
        [sys.executable, "-m", "dci.cli", "run", "--profile",
         "configs/profiles/dev_fast.toml", "--data-root", str(root),
         "--shard", shard, "--run-id", "shardtest", "--until", "c232"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def test_two_workers_equal_one(tmp_path):
    root = tmp_path / "shared-artifacts"
    a = _worker("0/2", root)
    b = _worker("1/2", root)
    out_a, _ = a.communicate(timeout=900)
    out_b, _ = b.communicate(timeout=900)
    assert a.returncode == 0, out_a[-2000:]
    assert b.returncode == 0, out_b[-2000:]

    runs = sorted(root.rglob("*/gates/gate0_selftest.csv"))
    assert len(runs) == 1, "both workers must share one run directory"
    run_root = runs[0].parent.parent

    import pandas as pd
    from tests.regression.gate0_registry import assert_gate0_healthy
    # One authoritative expectation, not a copied total: this assertion used to
    # pin the v15.0 count of 110, so every repair that ADDED an invariant broke
    # an unrelated slow test.
    assert_gate0_healthy(pd.read_csv(runs[0]))

    # journal: every planned batch committed exactly once, split across workers
    stage_dir = run_root / "responses" / "gate0_micro"
    commits = sorted(stage_dir.glob("batch-*.commit.json"))
    plan = json.loads((run_root / "designs" /
                       "gate0_micro_batch_plan.json").read_text())
    assert len(commits) == plan["n_batches"], (
        f"{len(commits)} commits vs {plan['n_batches']} planned")
    indices = [json.loads(c.read_text())["planned_batch_index"] for c in commits]
    assert sorted(indices) == list(range(plan["n_batches"])), "dup or gap"
    # both workers actually contributed
    attempts = {json.loads(c.read_text())["run_attempt_id"] for c in commits}
    assert len(attempts) == 2, "one worker generated everything"
