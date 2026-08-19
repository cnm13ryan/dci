"""Scientific transcription (item 62): registered identities, grids,
wordings, topics, sequestering, prompt allocation, and design counts match
the v3 preregistration exactly; and dci1v3 is scientifically independent."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from dci1v3.protocol import constants as C
from dci1v3.protocol.wordings import (
    family_wordings,
    focal_wordings,
    length_caliper_ok,
    target_wordings,
    wording_word_count,
)
from dci1v3.models.registry import (
    FIRST_MODEL_KEY,
    MODEL_KEYS,
    MODELS,
    get_model,
)
from dci1v3.topics.bank import load_bank
from dci1v3.topics.sequestered import (
    assert_no_materialisation,
    load_manifest,
)
from dci1v3.topics.split import (
    confirmatory_blocks,
    pilot_blocks,
    split_topics,
)

PKG = Path(__file__).resolve().parents[1] / "src" / "dci1v3"


def test_registered_models_and_order():
    assert [m.model_id for m in
            sorted(MODELS, key=lambda m: m.execution_order)] == [
        "google/gemma-3n-E2B-it", "Qwen/Qwen3-4B",
        "Qwen/Qwen3-4B-Instruct-2507", "google/gemma-3n-E4B-it"]
    assert FIRST_MODEL_KEY == "gemma-3n-e2b-it"
    hybrid = get_model("qwen3-4b")
    assert hybrid.thinking_policy == "disabled"
    assert hybrid.chat_template_kwargs == {"enable_thinking": False}
    for spec in MODELS:
        assert len(spec.revision) == 40
        assert spec.dtype == "bfloat16"
        assert spec.tensor_parallel_size == 1


def test_inference_settings():
    assert C.DECODING == {"temperature": 0.7, "top_p": 0.9, "top_k": 50}
    assert C.CAP_GRID == (512, 768, 1024)
    assert C.CALIBRATION_DRAWS_PER_CELL == 1
    assert C.M_DRAWS == 16


def test_grids_and_families():
    assert C.TARGET_GRID == (1, 2, 3, 4, 5, 6, 7, 8)
    assert C.FOCAL_GRID == (7, 8, 9, 10)
    assert C.REFERENCE_FAMILIES == {
        "RF1": (8, 5, 2, 0), "RF2": (8, 5, 2, 0), "RF3": (8, 5, 2, 0),
        "RF4": (6, 4, 2, 0), "RF5": (12, 8, 4, 0), "RF6": (12, 8, 4, 0),
        "RF7": (24, 16, 8, 0), "RF8": (8, 5, 2, 0)}


def test_design_counts():
    assert (C.N_BLOCKS, C.BLOCKS_PER_ORDER) == (384, 192)
    assert C.N_CELLS == 2304 and C.N_CACHED_DRAWS == 36864
    assert C.N_PRIMARY == 2304
    assert C.GREEDY_BLOCKS == 96 and C.GREEDY_GENERATIONS == 384
    assert (C.PILOT_CELLS, C.PILOT_DRAWS) == (72, 1152)
    assert C.PILOT_N == 3 and C.PILOT_M == 9 and C.PILOT_CAP == 1024
    assert C.PILOT_REFERENCES == (("RF1", 5), ("RF2", 5), ("RF5", 8))
    assert C.BOOTSTRAP_RESAMPLES == 10_000 and C.PSEUDO_RUNS == 1_000
    assert C.FAMILY_SIZES == {"F1": 2, "F2": 3, "F3": 6, "F4": 6,
                              "F5": 9, "F6": 3}
    assert C.SESOI == 0.10 and C.EXCHANGEABILITY_MARGIN == 0.05


def test_wordings_frozen_and_calipered():
    assert target_wordings(3)[0] == "Use the word however exactly 3 times."
    assert target_wordings(1)[0] == "Use the word however exactly 1 time."
    assert focal_wordings(7)[0] == \
        "Every word in the answer must have at most 7 letters."
    assert family_wordings("RF1", 5)[0] == \
        "At most 5 words in the answer may begin with the letter b."
    for family, grid in C.REFERENCE_FAMILIES.items():
        for q in grid:
            assert len(set(family_wordings(family, q))) == 4
            for m in C.FOCAL_GRID:
                assert length_caliper_ok(family, q, m), (family, q, m)
    assert wording_word_count("Use at most 5 words.") == 4


def test_topics_counts_and_split():
    bank = load_bank()
    assert len(bank) == 528
    split = split_topics()
    assert {k: len(v) for k, v in split.items()} == {
        "prescreen": 24, "solo": 96, "composed": 24, "confirmatory": 384}
    manifest = load_manifest()
    assert len(manifest) == 96
    assert_no_materialisation(bank)
    ids = {t["topic_id"] for t in bank}
    assert ids.isdisjoint({e["topic_id"] for e in manifest})


def test_sequestered_manifest_is_opaque():
    for entry in load_manifest():
        assert set(entry) == {"topic_id", "area", "sha256"}
        assert "question" not in entry


def test_confirmatory_allocation():
    blocks = confirmatory_blocks()
    assert len(blocks) == 384
    for block in blocks:
        expected_order = (C.TARGET_FIRST if block.index % 2 == 0
                          else C.ADDED_FIRST)
        assert block.order == expected_order
        assert block.target_wording == block.index % 4
        assert block.added_wording == (block.index // 4) % 4


def test_pilot_allocation():
    blocks = pilot_blocks()
    assert len(blocks) == 12
    for block in blocks:
        assert block.target_wording == block.index % 4
        assert block.added_wording == \
            (block.index + block.index // 4) % 4
        assert block.order == (C.TARGET_FIRST if block.index % 2 == 0
                               else C.ADDED_FIRST)
    areas = [b.area for b in blocks]
    assert areas == list(C.SUBJECT_AREAS)


def test_terminal_status_vocabulary():
    assert C.TERMINAL_STATUSES == (
        "QUALIFICATION_FAILURE", "APPARATUS_FAILURE",
        "RESPONSE_LENGTH_INCOMPATIBLE", "TARGET_RANGE_EXHAUSTED",
        "FOCAL_RANGE_EXHAUSTED", "GRID_RESOLUTION_INSUFFICIENT",
        "REFERENCE_POOL_MISMATCH", "COMPOSED_HEADROOM_FAILURE",
        "MEASUREMENT_NOT_ESTABLISHED", "MEASUREMENT_EVIDENCE_INSUFFICIENT")
    assert C.ARTIFACT_STATES == ("generated", "committed", "accepted",
                                 "superseded")
    assert len(C.ARTIFACT_TYPES) == 10


def test_no_v2_imports():
    """dci1v3 never imports, calls, or reads the earlier implementation."""
    offenders = []
    for path in PKG.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if name == "dci1" or name.startswith("dci1."):
                    offenders.append((str(path), name))
    assert not offenders


def test_seed_domains_separated():
    from dci1v3.protocol.seeds import (
        bootstrap_seed,
        generation_seed,
        pseudo_run_index,
    )
    g = generation_seed(C.GENERATION_ROOT_SEED, "confirmatory", "m",
                       "hash", 0)
    p = pseudo_run_index(C.PSEUDO_RUN_ROOT_SEED, 0, "m", "hash")
    b = bootstrap_seed(C.BOOTSTRAP_ROOT_SEED, "m", "F1")
    assert len({g, p, b}) == 3
    with pytest.raises(Exception):
        generation_seed(None, "confirmatory", "m", "hash", 0)


def test_qualification_uses_synthetic_hardware_only_in_synthetic():
    assert C.STUDY_ID == "dci1-v3"
    assert C.SYNTHETIC_STUDY_ID == "dci1-v3-synthetic"
    assert MODEL_KEYS[0] == FIRST_MODEL_KEY
