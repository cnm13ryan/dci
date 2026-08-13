"""Storage, cache-integrity and provenance behaviors, exercised on the real
pipeline state (stages through the generation machinery), not on mocks."""
import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]


def _design(prefix: str, n: int, stage: str):
    import pandas as pd
    return pd.DataFrame([
        {"row_id": f"{prefix}{i:03d}", "repetition_seed": 1,
         "user_prompt": f"probe {i}", "stage": stage,
         "ordered_constraint_ids": '["A"]', "order": "isolated",
         "added_constraint": "", "measured_constraint": "A",
         "condition_id": "A_ONLY"} for i in range(n)])


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    """Run the pipeline through the oracle/generation stage once."""
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    root = tmp_path_factory.mktemp("shardless")
    cfg = loader.load_profile(Path("configs/profiles/dev_fast.toml"))
    cfg.data_root = str(root)
    loader.activate(cfg)
    assert run_pipeline(until="c192") == 0

    import sys
    import types
    handle = types.SimpleNamespace(S=S)
    for name, mod in list(sys.modules.items()):
        if name.startswith("dci.pipeline.stages.c126"):
            handle.storage = mod
        if name.startswith("dci.pipeline.stages.c192"):
            handle.generation = mod
    return handle


def test_frozen_plan_mismatch_refuses_a_changed_randomisation(live):
    S = live.S
    from dci.exceptions import FrozenPlanMismatch
    design = _design("t", 8, "probe_stage")
    plan = live.generation.load_or_create_batch_plan(design, "probe_stage")
    assert plan, "plan was not created"
    changed = design.copy()
    changed.loc[0, "row_id"] = "t999"
    with pytest.raises(FrozenPlanMismatch):
        live.generation.load_or_create_batch_plan(changed, "probe_stage")


def test_signed_artifact_survives_rerun(live):
    S = live.S
    import pandas as pd
    target = Path(S.AUDIT_DIR) / "_probe_signed.csv"
    target.write_text("human work\n", encoding="utf-8")
    before = target.read_text()
    S.write_template_if_absent(target, pd.DataFrame({"a": [1]}))
    assert target.read_text() == before
    target.unlink()


def test_foreign_fingerprint_batch_is_quarantined_not_read(live):
    S = live.S
    import pandas as pd
    design = _design("q", 4, "quarantine_probe")
    plan = live.generation.load_or_create_batch_plan(design, "quarantine_probe")
    # generate + commit honestly first
    resp = S.run_generation_stage(design, "quarantine_probe")
    assert len(resp) == 4
    # plant a FOREIGN batch in the durable mirror and delete the local cache
    stage_dir = live.storage.durable_stage_dir("quarantine_probe")
    victims = sorted(stage_dir.glob("batch-*.commit.json"))
    assert victims
    payload = json.loads(victims[0].read_text())
    payload["execution_sha256"] = "0" * 64
    victims[0].write_text(json.dumps(payload))
    for p in live.storage.local_stage_dir("quarantine_probe").glob("batch-*"):
        p.unlink()
    restored = S.restore_from_drive("quarantine_probe", plan)
    assert restored["quarantined"] >= 1
    q = list(Path(S.QUARANTINE_DIR).rglob("*.json"))
    assert q, "foreign batch did not land in quarantine/"


def test_restore_regenerates_nothing_already_committed(live):
    S = live.S
    import pandas as pd
    design = _design("r", 6, "restore_probe")
    S.run_generation_stage(design, "restore_probe")
    plan = live.generation.load_or_create_batch_plan(design, "restore_probe")
    for p in live.storage.local_stage_dir("restore_probe").glob("batch-*"):
        p.unlink()
    restored = S.restore_from_drive("restore_probe", plan)
    assert restored["restored"] >= 1 and restored["rows_restored"] == 6
    payload, _ = S.read_commits("restore_probe", plan)
    assert len(payload) == 6
