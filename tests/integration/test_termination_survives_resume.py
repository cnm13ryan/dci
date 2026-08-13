"""Termination metadata must survive the cache boundary.

Pre-repair, the five termination fields lived only in the in-memory
`S.TERMINATION_RECORDS`, appended by the backends during generate(). A resumed
run generates nothing, so the list was empty, every field scored as None, and the
output-cap diagnostic evaluated an empty frame -- reporting no truncation because
it had no data, which is the worst possible way for a safeguard to pass.

These tests exercise the real journal: generate, then re-read through the cached
path and require identical termination summaries.
"""
import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]

FIELDS = ("generated_token_count", "ended_with_eos", "hit_max_new_tokens",
          "output_truncated", "stop_reason")


def _design(prefix: str, n: int, stage: str):
    import pandas as pd
    return pd.DataFrame([
        {"row_id": f"{prefix}{i:03d}", "repetition_seed": 1,
         "user_prompt": f"probe {i}", "stage": stage,
         "ordered_constraint_ids": '["A"]', "order": "isolated",
         "added_constraint": "", "measured_constraint": "A",
         "task_id": f"task{i % 3}", "paraphrase_id": 0,
         "condition_id": "A_ONLY"} for i in range(n)])


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    root = tmp_path_factory.mktemp("resume")
    cfg = loader.load_profile(Path("configs/profiles/dev_fast.toml"))
    cfg.data_root = str(root)
    loader.activate(cfg)
    assert run_pipeline(until="c192") == 0
    import sys
    import types
    handle = types.SimpleNamespace(S=S)
    for name, mod in list(sys.modules.items()):
        if name.startswith("dci.pipeline.stages.c192"):
            handle.generation = mod
    return handle


def test_committed_journal_records_carry_termination_fields(live):
    """The fields must be IN the payload, not merely in memory."""
    S = live.S
    stage = "termination_probe"
    design = _design("z", 8, stage)
    S.prerender_prompts(design)
    live.generation.run_generation_stage(design, stage)
    plan = live.generation.load_or_create_batch_plan(design, stage)

    committed = json.loads("[]")
    for path in sorted(Path(S.local_stage_dir(stage)).glob("batch-*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                committed.append(json.loads(line))
    assert committed, "nothing was committed"
    for record in committed:
        for field in FIELDS:
            assert field in record, f"{field} absent from the committed payload"
    assert any(r["generated_token_count"] is not None for r in committed)


def test_resumed_rows_score_identical_termination(live):
    """Re-reading through the cache must reproduce the termination summary."""
    S = live.S
    stage = "termination_resume"
    design = _design("y", 8, stage)
    S.prerender_prompts(design)
    live.generation.run_generation_stage(design, stage)
    plan = live.generation.load_or_create_batch_plan(design, stage)

    fresh = live.generation.rows_for_design(design, stage, plan)
    scored_fresh = S.score_responses(fresh)

    # Drop every live record: this is exactly the state a resumed process is in.
    S.TERMINATION_RECORDS.clear()
    S.TERMINATION_BY_ROW.clear()

    resumed = live.generation.rows_for_design(design, stage, plan)
    scored_resumed = S.score_responses(resumed)

    for field in FIELDS:
        assert field in scored_resumed.columns
        assert scored_resumed[field].notna().all(), (
            f"{field} was lost across the cache boundary")
    left = scored_fresh.set_index("row_id")[list(FIELDS)].sort_index()
    right = scored_resumed.set_index("row_id")[list(FIELDS)].sort_index()
    assert left.equals(right), "termination summary changed on resume"


def test_output_cap_report_is_non_empty_after_resume(live):
    """The diagnostic must have data to work with on a resumed run."""
    from dci.analysis.output_budget import termination_coverage, termination_report
    S = live.S
    stage = "termination_report_probe"
    design = _design("w", 8, stage)
    S.prerender_prompts(design)
    live.generation.run_generation_stage(design, stage)
    plan = live.generation.load_or_create_batch_plan(design, stage)

    S.TERMINATION_RECORDS.clear()
    S.TERMINATION_BY_ROW.clear()
    scored = S.score_responses(live.generation.rows_for_design(design, stage, plan))

    coverage = termination_coverage(scored)
    assert coverage["coverage"] == 1.0, coverage
    report = termination_report(scored, ["condition_id"])
    assert len(report) == 1
    assert int(report["n_with_metadata"].iloc[0]) == len(scored)


def test_termination_frame_includes_restored_rows(live):
    S = live.S
    stage = "termination_frame_probe"
    design = _design("v", 4, stage)
    S.prerender_prompts(design)
    live.generation.run_generation_stage(design, stage)
    plan = live.generation.load_or_create_batch_plan(design, stage)

    S.TERMINATION_RECORDS.clear()
    S.TERMINATION_BY_ROW.clear()
    live.generation.rows_for_design(design, stage, plan)

    frame = S.termination_frame()
    assert set(design["row_id"]) <= set(frame.index)
    assert list(frame.columns) == list(FIELDS)
