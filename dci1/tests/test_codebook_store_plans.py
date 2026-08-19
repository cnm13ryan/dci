"""Codebook checks (§28), evidence store, model plans, seed levels, topics."""

import pytest

pytestmark = pytest.mark.cpu

from helpers import M_PARAM, REFS, SPEC, N, small_config, write_stage

from dci1.evidence.store import (
    AppendOnceJsonl,
    fingerprint_tree,
    mirror_to_durable,
    restore_from_durable,
)
from dci1.models.adapters import MODELS, backend_plan, get_model
from dci1.protocol.codebook import (
    CODEBOOKS,
    assert_constraining_checks_exist,
    assert_primary_fields,
    validate_rows,
)
from dci1.protocol.constants import DECODING, ProtocolError
from dci1.protocol.seeds import (
    bootstrap_seed,
    generation_seed,
    resampling_seed,
    select_pool_index,
)


# ------------------------------------------------------------------ codebook
def test_codebook_four_checks(tmp_path):
    assert_primary_fields()
    assert_constraining_checks_exist()
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    rows = AppendOnceJsonl(stage_dir / "pool" / "pool.jsonl").rows()
    validate_rows("pool", rows)
    bad = dict(rows[0], pool_index="zero")
    with pytest.raises(ProtocolError, match="declared type"):
        validate_rows("pool", [bad])
    with pytest.raises(ProtocolError, match="diverge"):
        validate_rows("pool", [{k: v for k, v in rows[0].items()
                                if k != "generation_seed"}])


def test_codebook_rows_have_six_fields():
    for table, columns in CODEBOOKS.items():
        for column in columns:
            assert set(column) == {"name", "type", "domain", "units",
                                   "causal_role", "definition"}


def test_scored_table_conforms_to_codebook(tmp_path):
    from dci1.analysis.tables import score_table
    from dci1.resampling.primary import build_primary, load_accepted

    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_primary(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                  config=config)
    accepted = load_accepted(stage_dir)
    validate_rows("accepted", accepted)
    scored = score_table(accepted, blocks, n=N, m=M_PARAM, references=REFS)
    validate_rows("scored", scored)


# ------------------------------------------------------------ evidence store
def test_append_once_and_hash_verification(tmp_path):
    store = AppendOnceJsonl(tmp_path / "rows.jsonl")
    store.append([{"row_id": "a", "x": 1}])
    with pytest.raises(ProtocolError):
        store.append([{"row_id": "a", "x": 2}])
    store.verify_hashes()
    text = (tmp_path / "rows.jsonl").read_text().replace('"x": 1', '"x": 9')
    (tmp_path / "rows.jsonl").write_text(text)
    with pytest.raises(ProtocolError, match="mutated"):
        store.verify_hashes()


def test_durable_mirror_restore_roundtrip(tmp_path):
    working = tmp_path / "working"
    durable = tmp_path / "durable"
    store = AppendOnceJsonl(working / "rows.jsonl")
    store.append([{"row_id": "a", "x": 1}, {"row_id": "b", "x": 2}])
    mirror_to_durable(working, durable)
    before = fingerprint_tree(working)
    import shutil

    shutil.rmtree(working)
    restore_from_durable(durable, working)
    assert fingerprint_tree(working) == before
    # a corrupted durable copy is refused
    payload = durable / "rows.jsonl"
    payload.write_text(payload.read_text() + "corrupt")
    with pytest.raises(ProtocolError, match="hash"):
        restore_from_durable(durable, working)


# --------------------------------------------------------------- model plans
def test_four_registered_models_with_pinned_revisions():
    assert len(MODELS) == 4
    for spec in MODELS:
        assert len(spec.revision) == 40          # a full commit hash
        plan = backend_plan(spec)
        assert plan["model_revision"] == spec.revision
        assert plan["reasoning_mode"] == "NO_THINKING"
        assert plan["temperature"] == DECODING["temperature"]
        assert plan["top_p"] == DECODING["top_p"]
        assert plan["top_k"] == DECODING["top_k"] == 50
        assert plan["generation_ceiling"] == DECODING["max_new_tokens"] == 400
        assert plan["dtype"] == "bfloat16"
        assert plan["tensor_parallel_size"] == 1


def test_no_thinking_configuration_per_model():
    assert get_model("qwen3-4b").chat_template_kwargs == \
        {"enable_thinking": False}
    assert get_model("qwen3-4b").switch_expectation == "live"
    for key in ("qwen3-4b-instruct-2507", "gemma-3n-e2b-it",
                "gemma-3n-e4b-it"):
        spec = get_model(key)
        assert spec.chat_template_kwargs == {}
        assert spec.switch_expectation == "inert"


def test_backend_config_hash_ignores_pacing_only():
    from dci1.generation.pools import backend_config_hash

    spec = get_model("qwen3-4b")
    a = backend_plan(spec, chunk_size=8)
    b = backend_plan(spec, chunk_size=64)
    assert backend_config_hash(a) == backend_config_hash(b)
    c = dict(a, temperature=0.0)
    assert backend_config_hash(c) != backend_config_hash(a)


def test_greedy_plan_differs_only_in_decoding():
    spec = get_model("qwen3-4b")
    stochastic = backend_plan(spec, decoding="stochastic")
    greedy = backend_plan(spec, decoding="greedy")
    assert greedy["temperature"] == 0.0 and greedy["top_k"] == 0
    assert greedy["model_revision"] == stochastic["model_revision"]


# ---------------------------------------------------------------- seed levels
def test_three_randomness_levels_are_disjoint():
    prompt_hash = "ab" * 32
    g = generation_seed(1, "confirmatory", "model", prompt_hash, 0)
    r = resampling_seed(1, "model", 0)
    b = bootstrap_seed(1, "model", "confirmatory")
    assert len({g, r, b}) == 3


def test_generation_seeds_distinct_per_pool_index():
    prompt_hash = "cd" * 32
    seeds = {generation_seed(7, "confirmatory", "m", prompt_hash, i)
             for i in range(16)}
    assert len(seeds) == 16


def test_generation_seed_rejects_unknown_stream():
    with pytest.raises(ValueError):
        generation_seed(1, "nonsense", "m", "ab" * 32, 0)


def test_select_pool_index_uniform_for_m16():
    seed = resampling_seed(9, "m", 4)
    counts = [0] * 16
    for i in range(1600):
        counts[select_pool_index(seed, f"B{i:03d}", "focal", 16)] += 1
    assert min(counts) > 40


# --------------------------------------------------------------------- topics
def test_topic_bank_and_split():
    from dci1.topics.bank import load_bank
    from dci1.topics.split import split_bank

    topics = load_bank()
    assert len(topics) == 576
    split = split_bank(topics)
    ids = set()
    for part in split.values():
        for topic in part:
            assert topic["topic_id"] not in ids
            ids.add(topic["topic_id"])


def test_topic_rules_reject_banned_vocabulary():
    from dci1.topics.bank import load_bank, validate_bank

    topics = [dict(t) for t in load_bank()]
    topics[0]["question"] = \
        "Why does this word matter to historians working today?"
    with pytest.raises(ProtocolError, match="letter/word-shape"):
        validate_bank(topics)
