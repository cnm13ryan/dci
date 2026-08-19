"""T2. Model execution.

Exact repository and revision, vLLM configuration, chat template, thinking
policy, hardware recording, decoding settings, answer extraction, seed
uniqueness and the duplicate-replicate rate.
"""
from __future__ import annotations

import pytest

from dci1v4.generation.backend import backend_env, build_plan
from dci1v4.models.registry import (
    JUDGE_BY_KEY,
    MODEL_BY_KEY,
    MODEL_KEYS,
    assert_disjoint_judges,
    get_judge,
    get_model,
    registration_models,
)
from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C


def test_the_four_registered_replications_and_their_execution_order():
    assert MODEL_KEYS == ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
                          "qwen3-4b-instruct-2507")
    manifest = registration_models()
    assert [m["execution_order"] for m in manifest] == [1, 2, 3, 4]
    assert [m["model_id"] for m in manifest] == [
        "google/gemma-3n-E2B-it", "google/gemma-3n-E4B-it", "Qwen/Qwen3-4B",
        "Qwen/Qwen3-4B-Instruct-2507"]


def test_every_revision_is_pinned_to_a_full_commit():
    for key in MODEL_KEYS:
        spec = get_model(key)
        assert len(spec.revision) == 40
        assert all(ch in "0123456789abcdef" for ch in spec.revision)


def test_an_unregistered_repository_blocks_rather_than_substituting():
    with pytest.raises(ProtocolError, match="not a registered v4 replication"):
        get_model("some/other-model")


def test_thinking_is_disabled_for_the_hybrid_qwen_through_its_own_mechanism():
    qwen = get_model("qwen3-4b")
    assert qwen.thinking_policy == "disabled"
    assert qwen.chat_template_kwargs == {"enable_thinking": False}
    assert qwen.switch_expectation == "live"
    for key in ("gemma-3n-e2b-it", "gemma-3n-e4b-it",
                "qwen3-4b-instruct-2507"):
        spec = get_model(key)
        assert spec.thinking_policy == "unavailable"
        assert spec.switch_expectation == "inert"


def test_the_judge_registry_is_disjoint_from_the_study_models():
    assert_disjoint_judges()
    assert not set(MODEL_BY_KEY) & set(JUDGE_BY_KEY)
    for key in MODEL_KEYS:
        with pytest.raises(ProtocolError, match="never be its own judge"):
            get_judge(key)


def test_the_registered_decoding_policy():
    spec = get_model("gemma-3n-e2b-it")
    plan = build_plan(spec, stage="confirmatory", max_new_tokens=768)
    assert plan["temperature"] == 0.7
    assert plan["top_p"] == 0.9
    assert plan["top_k"] == 50
    assert plan["dtype"] == "bfloat16"
    assert plan["tensor_parallel_size"] == 1
    assert plan["max_new_tokens"] in C.COMPLETION_CAPS
    assert plan["revision"] == spec.revision
    assert plan["thinking_policy"] == spec.thinking_policy


def test_the_greedy_sensitivity_plan_is_temperature_zero():
    spec = get_model("gemma-3n-e2b-it")
    plan = build_plan(spec, stage="greedy", max_new_tokens=768,
                      temperature=C.GREEDY_TEMPERATURE)
    assert plan["temperature"] == 0.0


def test_the_serialised_plan_pins_concurrency_at_one():
    spec = get_model("gemma-3n-e2b-it")
    plan = build_plan(spec, stage="gate1", max_new_tokens=512,
                      serialised=True)
    assert plan["max_concurrency"] == 1
    assert plan["chunk_size"] == 1


def test_gpu_hygiene_clears_inherited_visibility(monkeypatch):
    monkeypatch.setenv("ROCR_VISIBLE_DEVICES", "1,2")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "3")
    env = backend_env(0)
    assert env["HIP_VISIBLE_DEVICES"] == "0"
    assert "ROCR_VISIBLE_DEVICES" not in env
    assert "CUDA_VISIBLE_DEVICES" not in env
    assert env["HF_HUB_OFFLINE"] == "1"
    assert env["VLLM_WORKER_MULTIPROC_METHOD"] == "spawn"


def test_the_backend_seam_imports_no_dci_implementation():
    """The reused execution primitive is study-independent."""
    import ast
    from pathlib import Path

    from dci1v4.engine.context import REPO_ROOT

    contract = REPO_ROOT / "exploratory" / "vllm_backend" / "contract.py"
    if not contract.exists():
        pytest.skip("the shared backend is not present in this checkout")
    imported = set()
    for node in ast.walk(ast.parse(contract.read_text())):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not any(name.startswith(("dci1", "vllm", "torch"))
                   for name in imported), imported


def test_the_backend_adapter_is_the_only_v4_module_that_knows_the_seam():
    import ast

    from dci1v4.engine.context import DCI1_ROOT

    package = DCI1_ROOT / "src" / "dci1v4"
    naming = []
    for path in sorted(package.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if "vllm_backend" in path.read_text():
            naming.append(str(path.relative_to(package)))
    assert naming == ["generation/backend.py"]


def test_answer_extraction_prefers_the_final_answer_channel():
    import inspect

    from dci1v4.generation.cache import fill_cache

    source = inspect.getsource(fill_cache)
    assert 'row.get("final_answer") or row.get("raw_generation", "")' in source
    assert 'row.get("outcome") != "OK"' in source


def test_hardware_and_environment_are_recorded_on_every_row(tmp_path):
    from dci1v4 import SYNTHETIC_STUDY_ID
    from dci1v4.design.cells import design_cells
    from dci1v4.generation.cache import cache_rows, fill_cache
    from dci1v4.generation.synthetic import synthetic_generate
    from dci1v4.topics.split import confirmatory_blocks, split_topics

    slot_map = {"A": ("A", 3), "B": ("B", 8)}
    cells = design_cells("confirmatory", confirmatory_blocks(split_topics())[:1],
                         slot_map, draws=4)
    spec = get_model("gemma-3n-e2b-it")
    fill_cache(tmp_path / "c", cells, spec=spec, stage="confirmatory",
               slot_map=slot_map, study_id=SYNTHETIC_STUDY_ID,
               plan=build_plan(spec, stage="confirmatory", max_new_tokens=768),
               generate_fn=synthetic_generate,
               environment={"python_executable": "/usr/bin/python",
                            "dependency_digest": "abc"})
    for row in cache_rows(tmp_path / "c"):
        assert row["model_revision"] == spec.revision
        assert row["interpreter"] == "/usr/bin/python"
        assert row["dependency_digest"] == "abc"
        assert row["hardware_class"] == "none"
        assert row["backend_version"] == "synthetic"
