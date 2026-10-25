"""Pilot design: counts, topic allocation, identities, seeds, the refusal of
composed conditions, carried configuration, and the estimate."""
from __future__ import annotations

import ast

import pytest

from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import library as L
from dci.batch1 import topics as TOP
from tests.batch1.conftest import historical_source

pytestmark = pytest.mark.cpu


@pytest.fixture(scope="module")
def split():
    return TOP.split_bank(TOP.load_bank(), pilot_topics=96, stage1_topics=32)


@pytest.fixture(scope="module")
def rows(split):
    return D.rows_for_cells(D.stage1_cells(), split)


def test_stage1_cell_and_row_counts(rows):
    cells = D.stage1_cells()
    assert len(cells) == 4 + 4 * 2 * (3 + 6 + 51) == 484
    assert len(rows) == 15_616
    refs = [r for r in rows if r["condition"] in
            {c.cid for c in L.reference_library()}]
    assert len(refs) == 51 * 4 * 2 * 32 == 13_056


def test_every_stand_alone_cell_uses_the_same_stage1_topics(rows, split):
    stage1 = {t.topic_id for t in split.stage1}
    by_cell: dict = {}
    for r in rows:
        by_cell.setdefault(r["cell_id"], set()).add(r["topic_id"])
    assert all(topics == stage1 for topics in by_cell.values())
    confirmatory = {t.topic_id for t in split.confirmatory}
    assert not confirmatory & {r["topic_id"] for r in rows}


def test_task_only_is_frame_invariant_with_two_draws(rows):
    task = [r for r in rows if r["condition"] == D.TASK_ONLY]
    assert len(task) == 4 * 32 * 2
    assert all(r["frame"] is None and r["load"] == 0 for r in task)
    assert all("1. " not in r["user_prompt"] for r in task)


def test_ids_and_seeds_are_stable_unique_and_identity_bound(rows, split):
    again = D.rows_for_cells(list(reversed(D.stage1_cells())), split)
    assert [(r["row_id"], r["scientific_seed"]) for r in rows] == \
        [(r["row_id"], r["scientific_seed"]) for r in again]
    assert len({r["row_id"] for r in rows}) == len(rows)
    seeds = {}
    for r in rows:
        seeds.setdefault(r["scientific_seed"], []).append(r["row_id"])
    assert max(len(v) for v in seeds.values()) == 1
    model = CFG.MODEL_BY_KEY["qwen3-4b"]
    base = dict(stage="stage1", model=model, prompt_hash="abc")
    s0 = D.generation_seed(CFG.DEFAULT_CONFIG, draw=0, **base)
    assert s0 == D.generation_seed(CFG.DEFAULT_CONFIG, draw=0, **base)
    assert s0 != D.generation_seed(CFG.DEFAULT_CONFIG, draw=1, **base)
    with pytest.raises(D.DesignError):
        D.generation_seed(CFG.DEFAULT_CONFIG, draw=0, stage="stage1",
                          model=model, prompt_hash="")


def test_model_and_frame_conditions_are_independent(rows):
    keys = {(r["model"], r["frame"], r["condition"], r["topic_id"], r["draw"])
            for r in rows}
    assert len(keys) == len(rows)
    a = [r for r in rows if r["condition"] == "A.however.4"
         and r["topic_id"] == rows[0]["topic_id"]]
    assert len({r["user_prompt"] for r in a}) == 2          # two frames
    assert len({r["scientific_seed"] for r in a}) == len(a)


def test_composed_conditions_cannot_be_built():
    by_id = L.constraint_by_id()
    with pytest.raises(D.DesignError):
        D.render_prompt("Q?", (by_id["A.however.4"], by_id["B.max9"]), "F0")
    with pytest.raises(D.DesignError):
        D.Cell("stage1", "qwen3-4b", "F0", "A.however.4+B.max9")
    with pytest.raises(D.DesignError):
        D.Cell("stage1", "qwen3-4b", "F0", D.TASK_ONLY)
    with pytest.raises(D.DesignError):
        D.Cell("stage3", "qwen3-4b", "F0", "B.max9")
    assert "2. " not in CFG.PROMPT_ONE and not hasattr(CFG, "PROMPT_TWO")


def test_prompts_render_the_carried_template(split):
    q = split.stage1[0].question
    c = L.constraint_by_id()["B.max9"]
    assert D.render_prompt(q, c, "F1") == (
        f"{q}\n\nAnswer in 60 to 120 words.\n\n1. Every word in the answer "
        "must have at most 9 letters.\n\nAnswer:")


def test_model_panel_is_carried_from_the_dci1_registry():
    tree = ast.parse(historical_source("dci1/src/dci1v4/models/registry.py"))
    carried = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == \
                "ModelSpec":
            kw = {k.arg: ast.literal_eval(k.value) for k in node.keywords}
            carried[kw["model_key"]] = kw
    for m in CFG.MODELS:
        h = carried[m.key]
        assert (h["model_id"], h["revision"], h["family"], h["thinking_policy"],
                h["chat_template_kwargs"]) == (
            m.model_id, m.revision, m.family, m.thinking_policy,
            m.chat_template_kwargs)
        assert h.get("gpu_memory_utilization", 0.85) == m.gpu_memory_utilization


def test_decoding_is_the_registered_v81_policy():
    src = historical_source("dci1/src/dci1v4/generation/backend.py")
    assert "temperature: float = 0.7, top_p: float = 0.9" in src
    assert "top_k: int = 50" in src
    assert (CFG.DECODING["temperature"], CFG.DECODING["top_p"],
            CFG.DECODING["top_k"]) == (0.7, 0.9, 50)


def test_estimate_counts(split):
    est = D.estimate(split=split)
    assert est["stage1_rows"] == 15_616
    assert est["stage2_max_rows"] == 240 * 64 == 15_360
    assert est["total_max_rows"] == 30_976
    assert 20_000 <= est["total_max_rows"] <= 35_000
    assert sum(v["stage1_rows"] for v in est["per_model"].values()) == 15_616
    assert est["stage2_hours_worst_case"] >= est["stage2_hours_if_even"]


def test_config_rejects_inconsistent_topic_counts():
    with pytest.raises(ValueError):
        CFG.PilotConfig(pilot_topics=90)
    with pytest.raises(ValueError):
        CFG.PilotConfig(models=("gpt-unknown",))
