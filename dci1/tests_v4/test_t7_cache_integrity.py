"""T7. Cached evidence integrity.

Exact cardinality 384 x cells x M; the greedy sensitivity run at exactly
20 x 96 x 1 generations at temperature 0, in its own namespace and reported as
a different generation population; deterministic unique seeds; immutable raw
writes; content hashes; exact-identity repair; duplicate rejection;
restoration from durable storage; refusal to form a cell mean from a partial
cell.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4 import SYNTHETIC_STUDY_ID
from dci1v4.design.cells import design_cells
from dci1v4.engine.store import CacheWriter, replicate, restore
from dci1v4.errors import IntegrityError
from dci1v4.generation.backend import build_plan
from dci1v4.generation.cache import (
    cache_rows,
    duplicate_report,
    fill_cache,
    validate_cache,
)
from dci1v4.generation.synthetic import synthetic_generate
from dci1v4.models.registry import get_model
from dci1v4.protocol import constants as C
from dci1v4.protocol.seeds import GENERATION_ROOT_SEED, generation_seed
from dci1v4.stages.confirmatory import (
    assert_separate_population,
    confirmatory_plan,
    greedy_plan,
)
from dci1v4.topics.split import confirmatory_blocks, split_topics

SLOT_MAP = {"A": ("A", 3), "B": ("B", 8), "R1": ("RF1", 2), "R2": ("RF5", 4),
            "R3": ("RF7", 6)}
SPEC = get_model("gemma-3n-e2b-it")
ENVIRONMENT = {"python_executable": "python", "dependency_digest": "d"}


@pytest.fixture(scope="module")
def blocks():
    return confirmatory_blocks(split_topics())


def _fill(tmp_path, cells, stage="confirmatory"):
    plan = build_plan(SPEC, stage=stage, max_new_tokens=768)
    return fill_cache(tmp_path / stage, cells, spec=SPEC, stage=stage,
                      slot_map=SLOT_MAP, study_id=SYNTHETIC_STUDY_ID,
                      plan=plan, generate_fn=synthetic_generate,
                      environment=ENVIRONMENT)


def test_the_confirmatory_cardinality_is_384_by_25_by_4(blocks):
    plan = confirmatory_plan(blocks, SLOT_MAP)
    assert plan["blocks"] == C.N_BLOCKS == 384
    assert plan["cells_per_block"] == C.N_CELLS_FULL == 25
    assert plan["draws_per_cell"] == C.M_DRAWS == 4
    assert plan["cached_generations"] == 384 * 25 * 4 == 38400


def test_the_reduced_design_cardinality(blocks):
    plan = confirmatory_plan(blocks, {"A": ("A", 3), "B": ("B", 8)})
    assert plan["cells_per_block"] == 4
    assert plan["cached_generations"] == 384 * 4 * 4 == 6144


def test_the_greedy_run_is_exactly_1920_generations_at_temperature_zero(blocks):
    plan = greedy_plan(blocks, SLOT_MAP)
    assert plan["generations"] == 20 * 96 * 1 == 1920
    assert plan["temperature"] == 0.0
    assert plan["namespace"] == "greedy"
    assert "different generation population" in plan["population_note"]
    assert all(cell.load == 2 for cell in plan["cells"])
    with pytest.raises(IntegrityError):
        assert_separate_population(Path("/a"), Path("/a"))


def test_confirmatory_generation_requires_a_freeze_record():
    from dci1v4.stages.confirmatory import assert_generation_licensed

    with pytest.raises(IntegrityError, match="stops before the freeze"):
        assert_generation_licensed(None)
    with pytest.raises(IntegrityError):
        assert_generation_licensed({"outcome": "FAIL"})


def test_every_seed_is_deterministic_and_unique(tmp_path, blocks):
    cells = design_cells("confirmatory", blocks[:4], SLOT_MAP, draws=4)
    _fill(tmp_path, cells)
    rows = cache_rows(tmp_path / "confirmatory")
    seeds = [row["seed"] for row in rows]
    assert len(set(seeds)) == len(seeds)
    for row in rows:
        assert row["seed"] == generation_seed(
            GENERATION_ROOT_SEED, "confirmatory", SPEC.model_id,
            row["prompt_hash"], row["draw_index"])


def test_the_seed_derives_from_experimental_identity_not_batch_position():
    a = generation_seed(GENERATION_ROOT_SEED, "confirmatory", "m", "h", 0)
    b = generation_seed(GENERATION_ROOT_SEED, "confirmatory", "m", "h", 1)
    c = generation_seed(GENERATION_ROOT_SEED, "gate2", "m", "h", 0)
    d = generation_seed(GENERATION_ROOT_SEED, "confirmatory", "m2", "h", 0)
    assert len({a, b, c, d}) == 4


def test_raw_writes_are_immutable_and_duplicates_are_refused(tmp_path):
    writer = CacheWriter(tmp_path / "cache.jsonl")
    writer.append([{"row_id": "x:0", "raw_response": "a"}])
    with pytest.raises(IntegrityError, match="duplicate cached-draw"):
        writer.append([{"row_id": "x:0", "raw_response": "b"}])
    assert len(writer.rows()) == 1


def test_a_mutated_byte_changes_the_hash_and_the_row_is_refused(tmp_path,
                                                                blocks):
    cells = design_cells("confirmatory", blocks[:2], SLOT_MAP, draws=4)
    _fill(tmp_path, cells)
    path = tmp_path / "confirmatory" / "cache.jsonl"
    lines = path.read_text().splitlines()
    row = json.loads(lines[0])
    row["raw_response"] = row["raw_response"] + "!"
    lines[0] = json.dumps(row, sort_keys=True, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(IntegrityError, match="row hash mismatch"):
        cache_rows(tmp_path / "confirmatory")


def test_a_partial_cell_never_forms_a_cell_mean(tmp_path, blocks):
    from dci1v4.analysis.observations import build_observations

    cells = design_cells("confirmatory", blocks[:2], SLOT_MAP, draws=4)
    _fill(tmp_path, cells)
    rows = cache_rows(tmp_path / "confirmatory")
    short = [r for r in rows if not (r["cell_id"] == rows[0]["cell_id"]
                                     and r["draw_index"] == 3)]
    with pytest.raises(IntegrityError, match="not exactly the"):
        build_observations(short, m_draws=4)


def test_validation_refuses_an_incomplete_draw_matrix(tmp_path, blocks):
    cells = design_cells("confirmatory", blocks[:2], SLOT_MAP, draws=4)
    _fill(tmp_path, cells)
    extra = design_cells("confirmatory", blocks[:3], SLOT_MAP, draws=4)
    with pytest.raises(IntegrityError, match="incomplete draw matrix"):
        validate_cache(tmp_path / "confirmatory", extra, spec=SPEC,
                       stage="confirmatory")


def test_repair_regenerates_only_the_predetermined_missing_identity(tmp_path,
                                                                    blocks):
    cells = design_cells("confirmatory", blocks[:2], SLOT_MAP, draws=4)
    _fill(tmp_path, cells)
    path = tmp_path / "confirmatory" / "cache.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    dropped = rows.pop(5)
    path.write_text("".join(json.dumps(r, sort_keys=True,
                                       ensure_ascii=False) + "\n"
                            for r in rows))
    _fill(tmp_path, cells)
    repaired = {r["row_id"]: r for r in cache_rows(tmp_path / "confirmatory")}
    assert dropped["row_id"] in repaired
    assert repaired[dropped["row_id"]]["seed"] == dropped["seed"]
    assert repaired[dropped["row_id"]]["raw_response"] == \
        dropped["raw_response"]


def test_durable_restore_reproduces_every_row_without_regenerating(tmp_path,
                                                                   blocks):
    cells = design_cells("confirmatory", blocks[:2], SLOT_MAP, draws=4)
    _fill(tmp_path, cells)
    source = tmp_path / "confirmatory"
    durable = tmp_path / "durable"
    hashes = replicate(source, durable)
    original = (source / "cache.jsonl").read_bytes()
    (source / "cache.jsonl").unlink()
    restored = restore(durable, source)
    assert set(restored) == set(hashes)
    assert (source / "cache.jsonl").read_bytes() == original


def test_the_duplicate_rate_is_measured_and_bounds_qualification():
    identical = [{"cell_id": "c", "response_content_hash": "h"}
                 for _ in range(4)]
    assert duplicate_report(identical)["overall_rate"] == 1.0
    distinct = [{"cell_id": "c", "response_content_hash": f"h{i}"}
                for i in range(4)]
    assert duplicate_report(distinct)["overall_rate"] == 0.0
    assert C.DUPLICATE_QUALIFICATION_MAX == 0.05
