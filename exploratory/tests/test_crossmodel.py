"""Tests for the cross-model adapter contract, seeds, design and schema.

The parser tests use SYNTHETIC fixtures rather than live generations, so they
run without a GPU and so a family's parser can be tested against outputs it has
not yet produced — including the malformed ones that matter most. The live
smoke artefacts under `runs/xm_validate_*` are the integration counterpart.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel import contract, seeds
from crossmodel.adapters import CHECKPOINTS, REGISTRY, get_adapter
from crossmodel.adapters.base import Generation, GenerationConfig
from crossmodel.adapters.gemma4 import Gemma4_12B, Gemma4_E4B
from crossmodel.adapters.kimivl import KimiVLThinkingAdapter
from crossmodel.adapters.qwen35 import Qwen35_4B, Qwen35_9B
from crossmodel.contract import ReasoningMode


# ------------------------------------------------------------------ registry
def test_registry_holds_the_five_checkpoints():
    assert set(CHECKPOINTS) == {
        "Qwen/Qwen3.5-4B", "Qwen/Qwen3.5-9B", "google/gemma-4-E4B-it",
        "google/gemma-4-12B-it", "moonshotai/Kimi-VL-A3B-Thinking-2506"}


def test_every_adapter_declares_its_execution_identity():
    for model_id, cls in REGISTRY.items():
        assert cls.MODEL_ID == model_id
        assert cls.FAMILY
        assert cls.SUPPORTED_MODES
        assert cls.THINK_OPEN and cls.THINK_CLOSE
        assert set(cls.SUPPORTED_MODES) <= set(ReasoningMode.ALL)


def test_unknown_checkpoint_is_refused():
    with pytest.raises(KeyError):
        get_adapter("Qwen/Qwen3-4B")


def test_kimi_offers_no_fabricated_non_thinking_mode():
    """The non-thinking sibling is a different checkpoint, not a mode."""
    assert KimiVLThinkingAdapter.SUPPORTED_MODES == (
        ReasoningMode.NATURAL_REASONING,)
    adapter = KimiVLThinkingAdapter()
    with pytest.raises(ValueError, match="does not natively support"):
        adapter.require_mode(ReasoningMode.NO_THINKING)


def test_families_do_not_share_delimiters():
    """A shared delimiter would mean one family's parser was copied blindly."""
    closes = {cls.FAMILY: cls.THINK_CLOSE for cls in REGISTRY.values()}
    assert closes["qwen3.5"] == "</think>"
    assert closes["gemma4"] == "<channel|>"
    assert closes["kimi-vl"] == "◁/think▷"
    assert len(set(closes.values())) == 3


# ------------------------------------------------------------------- parsing
QWEN_THINKING = (
    "The user wants four sentences.\nLet me count.\n</think>\n\n"
    "Alpha runs. Beta walks slowly. Gamma climbs the tall hill; it rains. "
    "Delta sleeps through the long and quiet afternoon.")

GEMMA_THINKING = (
    "<|channel>thought\nI must write exactly four sentences.\n<channel|>"
    "Alpha runs. Beta walks slowly. Gamma climbs; it rains. Delta sleeps.")

KIMI_THINKING = (
    "◁think▷Counting sentences: one, two, three, four.◁/think▷"
    "Alpha runs. Beta walks slowly. Gamma climbs; it rains. Delta sleeps.")


@pytest.mark.parametrize("cls,raw", [
    (Qwen35_4B, QWEN_THINKING),
    (Qwen35_9B, QWEN_THINKING),
    (Gemma4_E4B, GEMMA_THINKING),
    (Gemma4_12B, GEMMA_THINKING),
    (KimiVLThinkingAdapter, KIMI_THINKING),
])
def test_reasoning_and_answer_are_separated(cls, raw):
    adapter = cls()
    reasoning, answer = adapter.parse_output(
        raw, ReasoningMode.NATURAL_REASONING)

    assert answer.startswith("Alpha runs.")
    assert reasoning.strip()
    # The answer carries no reasoning markup...
    for marker in (cls.THINK_OPEN, cls.THINK_CLOSE):
        assert marker not in answer
    # ...and the reasoning does not swallow the answer.
    assert "Alpha runs." not in reasoning


@pytest.mark.parametrize("cls", [Qwen35_4B, Gemma4_E4B,
                                 KimiVLThinkingAdapter])
def test_unclosed_reasoning_yields_no_answer(cls):
    """A trace that never closed must NOT be scored as the answer."""
    adapter = cls()
    raw = f"{cls.THINK_OPEN}\nstill counting, wait, let me recount"
    reasoning, answer = adapter.parse_output(
        raw, ReasoningMode.NATURAL_REASONING)
    assert answer == ""
    assert "recount" in reasoning


@pytest.mark.parametrize("cls", [Qwen35_4B, Gemma4_E4B])
def test_non_thinking_output_is_all_answer(cls):
    adapter = cls()
    reasoning, answer = adapter.parse_output(
        "Alpha runs. Beta walks.", ReasoningMode.NO_THINKING)
    assert reasoning == ""
    assert answer == "Alpha runs. Beta walks."


def test_qwen_normalises_a_preopened_think_block():
    """Qwen3.5 pre-opens `<think>`; Qwen3 did not. Both normalise the same."""
    adapter = Qwen35_4B()
    assert adapter.normalise_reasoning("<think>\ncounting") == "counting"
    assert adapter.normalise_reasoning("counting") == "counting"


def test_gemma_channel_header_never_reaches_the_answer():
    adapter = Gemma4_E4B()
    assert adapter.clean_answer("<|channel>final\nAlpha runs.") == "Alpha runs."
    assert adapter.normalise_reasoning(
        "<|channel>thought\nI am counting") == "I am counting"


def test_final_answer_only_reaches_the_verifier():
    """The scoring path must be reachable from `final_answer` alone."""
    adapter = Gemma4_E4B()
    reasoning, answer = adapter.parse_output(
        GEMMA_THINKING, ReasoningMode.NATURAL_REASONING)
    scored = answer
    assert "I must write exactly four sentences" not in scored
    assert "<|channel>" not in scored and "<channel|>" not in scored
    assert reasoning != scored


# --------------------------------------------------------------------- seeds
def _cell(**overrides):
    base = dict(task_id="PLT01", replicate=0, arm="B",
                background="X_SEMICOLON_FREE", order="QAC", paraphrase_id=0,
                phase=seeds.REASONING_PHASE)
    base.update(overrides)
    return base


def test_seed_is_a_function_of_scientific_identity():
    first = seeds.scientific_seed(contract.MASTER_SEED, **_cell())
    again = seeds.scientific_seed(contract.MASTER_SEED, **_cell())
    assert first == again


@pytest.mark.parametrize("field,value", [
    ("task_id", "PLT02"), ("replicate", 1), ("arm", "C_L3"),
    ("background", "X_PAREN_FREE"), ("phase", seeds.ANSWER_PHASE),
])
def test_every_scientific_coordinate_moves_the_seed(field, value):
    base = seeds.scientific_seed(contract.MASTER_SEED, **_cell())
    moved = seeds.scientific_seed(contract.MASTER_SEED,
                                  **_cell(**{field: value}))
    assert base != moved


def test_replicates_never_share_a_seed():
    """The historical defect: one shared seed made 2 replicates 1 draw."""
    zero = seeds.scientific_seed(contract.MASTER_SEED, **_cell(replicate=0))
    one = seeds.scientific_seed(contract.MASTER_SEED, **_cell(replicate=1))
    assert zero != one


def test_seed_ignores_position_device_and_order():
    """Nothing outside scientific identity may enter the seed."""
    import inspect

    source = inspect.getsource(seeds.scientific_seed)
    for forbidden in ("index", "position", "device", "shard", "batch"):
        assert forbidden not in source.split('"""')[2]


def test_unknown_phase_is_refused():
    with pytest.raises(ValueError):
        seeds.scientific_seed(1, **_cell(phase="warmup"))


def test_replicate_duplication_flags_a_shared_seed():
    def record(task, answer, replicate):
        return {"model_id": "m", "reasoning_mode": "NATURAL_REASONING",
                "task_id": task, "arm": "B", "background": "S",
                "replicate_id": replicate, "final_answer": answer}

    identical = [record("T1", "same", 0), record("T1", "same", 1),
                 record("T2", "same", 0), record("T2", "same", 1)]
    audit = seeds.replicate_duplication(identical)
    assert audit["replicate_pairs"] == 2
    assert audit["identical_pairs"] == 2
    assert audit["implausible"] is True

    distinct = [record("T1", "a", 0), record("T1", "b", 1),
                record("T2", "c", 0), record("T2", "d", 1)]
    assert seeds.replicate_duplication(distinct)["implausible"] is False


# ------------------------------------------------------- engineering ceiling
def test_natural_reasoning_has_no_assigned_budget():
    """A ceiling is a safety bound; encoding it as `b` would fake a dose."""
    config = GenerationConfig(
        reasoning_mode=ReasoningMode.NATURAL_REASONING, max_answer_tokens=512,
        temperature=0.7, top_p=0.9, top_k=0, max_reasoning_tokens=39550)
    assert config.assigned_reasoning_budget is None
    assert config.engineering_ceiling == 39550


def test_limited_reasoning_has_a_budget_and_no_ceiling():
    config = GenerationConfig(
        reasoning_mode=ReasoningMode.LIMITED_REASONING, max_answer_tokens=512,
        temperature=0.7, top_p=0.9, top_k=0, max_reasoning_tokens=512)
    assert config.assigned_reasoning_budget == 512
    assert config.engineering_ceiling is None


def test_no_thinking_is_budget_zero_not_a_ceiling():
    config = GenerationConfig(
        reasoning_mode=ReasoningMode.NO_THINKING, max_answer_tokens=512,
        temperature=0.7, top_p=0.9, top_k=0)
    assert config.assigned_reasoning_budget == 0
    assert config.engineering_ceiling is None


# -------------------------------------------------------------------- design
@pytest.fixture(scope="module")
def state():
    from dci_exploratory import extensions, harvest

    extensions.register()
    return harvest.load()


def test_contract_matches_the_canonical_run(state):
    """The slice must still be the one the canonical config declares."""
    canonical = (Path(__file__).resolve().parents[2].parent
                 / "dci-natural-reasoning-headline" / "exploratory" / "runs"
                 / contract.CANONICAL_RUN)
    if not canonical.exists():
        pytest.skip("canonical run directory is not present on this machine")
    contract.assert_matches_canonical_run(canonical)


def test_design_is_the_expected_factorial(state):
    from crossmodel.runner import build_design

    rows = build_design(state, stage="XM_test")
    assert len(rows) == contract.EXPECTED_ROWS == 160
    assert len({r.row_id for r in rows}) == 160
    assert {r.arm for r in rows} == {contract.FOCAL, contract.REFERENCE}
    assert {r.variant for r in rows} == set(contract.BACKGROUNDS)
    assert {r.order for r in rows} == {contract.ORDER}
    assert {r.measured for r in rows} == {contract.TARGET}
    assert len({r.task_id for r in rows}) == contract.N_TASKS
    assert {r.replicate for r in rows} == {0, 1}


def test_focal_and_reference_differ_in_exactly_one_slot(state):
    from crossmodel.runner import build_design

    rows = build_design(state, stage="XM_test")
    groups: dict[str, list] = {}
    for row in rows:
        groups.setdefault(row.pair_key, []).append(row)
    assert groups
    for pair_key, group in groups.items():
        assert len(group) == 2, pair_key
        first, second = group
        assert first.task_id == second.task_id
        assert first.variant == second.variant
        assert len(first.ordered_ids) == len(second.ordered_ids)
        differing = [(a, b) for a, b in zip(first.ordered_ids,
                                            second.ordered_ids) if a != b]
        assert len(differing) == 1, f"{pair_key}: {differing}"


def test_seed_regime_holds_over_the_whole_design(state):
    from crossmodel.runner import build_design

    rows = build_design(state, stage="XM_test")
    audit = seeds.assert_seed_regime(rows, contract.MASTER_SEED)
    assert audit["unique_scientific_seeds"] == 160
    assert audit["unique_row_ids"] == 160
    assert audit["unique_scientific_cells"] == 160
    assert not audit["seed_collisions"]


# ------------------------------------------------------- deterministic shards
def test_sharding_preserves_batch_composition(state):
    """A row must land in the same batch whether one card runs it or two."""
    from crossmodel.runner import batches, build_design, shard_batches

    rows = build_design(state, stage="XM_test")
    single = batches(rows, 8)
    left = shard_batches(single, 0, 2)
    right = shard_batches(single, 1, 2)

    assert len(left) + len(right) == len(single)
    assert [b for pair in zip(left, right) for b in pair][:len(single)]
    # No row appears twice, and every row appears once.
    ids = [row.row_id for batch in left + right for row in batch]
    assert len(ids) == 160
    assert len(set(ids)) == 160
    # Batch membership is identical to the unsharded plan.
    assert {tuple(r.row_id for r in b) for b in left + right} == {
        tuple(r.row_id for r in b) for b in single}


def test_row_order_is_independent_of_input_order(state):
    from crossmodel.runner import build_design, order_rows

    rows = build_design(state, stage="XM_test")
    shuffled = list(reversed(rows))
    assert [r.row_id for r in order_rows(shuffled)] == [
        r.row_id for r in order_rows(rows)]


def test_merge_refuses_overlapping_shards(tmp_path):
    import json

    from crossmodel.runner import merge_shards

    def write(path, row_ids):
        with path.open("w") as handle:
            for row_id in row_ids:
                handle.write(json.dumps({
                    "row_id": row_id,
                    "reasoning_mode": "NATURAL_REASONING"}) + "\n")

    first, second = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    write(first, ["r1", "r2"])
    write(second, ["r2", "r3"])
    with pytest.raises(ValueError, match="overlap"):
        merge_shards([first, second])

    write(second, ["r3", "r4"])
    assert len(merge_shards([first, second], expected_rows=4)) == 4
    with pytest.raises(ValueError, match="expected"):
        merge_shards([first, second], expected_rows=5)


# -------------------------------------------------------------------- schema
def _generation(**overrides):
    base = dict(
        prompt="rendered", raw_generation="raw", reasoning_text="thinking",
        final_answer="Alpha runs.", reasoning_tokens=11,
        final_answer_tokens=3, finish_reason="stop",
        natural_reasoning_closed=True, reasoning_cap_hit=False,
        answer_truncated=False)
    base.update(overrides)
    return Generation(**base)


def _metadata(**overrides):
    base = {"model_id": "Qwen/Qwen3.5-4B", "model_revision": "a" * 40,
            "model_family": "qwen3.5", "backend": "transformers",
            "backend_version": "5.15.0", "dtype": "bfloat16",
            "quantization": "none", "device_configuration": "cuda:0",
            "chat_template_identifier": "tokenizer.chat_template",
            "chat_template_sha256": "deadbeef"}
    base.update(overrides)
    return base


def _design_row():
    return {"row_id": "abc", "task_id": "PLT01", "replicate": 0, "arm": "B",
            "variant": "X_SEMICOLON_FREE", "order": "QAC", "measured": "A",
            "load": 3, "paraphrase_id": 0, "pair_key": "PLT01|QAC|S|r0",
            "condition": "focal", "user_prompt": "topic ..."}


def test_row_carries_its_own_provenance():
    from crossmodel.schema import REQUIRED_FIELDS, build_row

    config = GenerationConfig(
        reasoning_mode=ReasoningMode.NATURAL_REASONING, max_answer_tokens=512,
        temperature=0.7, top_p=0.9, top_k=0, max_reasoning_tokens=39550)
    row = build_row(run_id="RUN", design_row=_design_row(),
                    generation=_generation(), adapter_metadata=_metadata(),
                    config=config, reasoning_control="chat_template(...)",
                    scientific_seed=1234)
    for field in REQUIRED_FIELDS:
        assert field in row
    assert row["model_id"] == "Qwen/Qwen3.5-4B"
    assert row["model_revision"] == "a" * 40
    assert row["assigned_reasoning_budget"] is None
    assert row["engineering_ceiling"] == 39550


def test_row_refuses_to_be_written_without_model_identity():
    from crossmodel.schema import build_row

    config = GenerationConfig(
        reasoning_mode=ReasoningMode.NO_THINKING, max_answer_tokens=512,
        temperature=0.7, top_p=0.9, top_k=0)
    metadata = _metadata()
    metadata["model_revision"] = ""
    with pytest.raises(ValueError, match="model_revision"):
        build_row(run_id="RUN", design_row=_design_row(),
                  generation=_generation(), adapter_metadata=metadata,
                  config=config, reasoning_control="c", scientific_seed=1)


def test_provenance_assertion_catches_a_mixed_file():
    from crossmodel.schema import assert_provenance

    rows = [{"model_id": "A", "model_revision": "a" * 40},
            {"model_id": "B", "model_revision": "b" * 40}]
    with pytest.raises(AssertionError, match="several model ids"):
        assert_provenance(rows)

    good = [{"model_id": "A", "model_revision": "a" * 40}] * 3
    assert assert_provenance(good, expected_model="A")["rows"] == 3
    with pytest.raises(AssertionError, match="expected model"):
        assert_provenance(good, expected_model="B")


def test_answer_empty_marks_the_row_not_ok():
    generation = _generation(final_answer="   ")
    assert generation.answer_empty
    assert not generation.generation_ok
