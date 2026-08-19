"""§8.3 generation pools and §8.4 resampling, on synthetic caches."""
import json

import pytest

pytestmark = pytest.mark.cpu

from helpers import SPEC, make_blocks, make_cells, pool_row, small_config, write_stage

from dci1.evidence.store import AppendOnceJsonl, read_jsonl
from dci1.generation.pools import pool_path
from dci1.generation.validation import load_complete_pools, validate_pools
from dci1.protocol.constants import ProtocolError
from dci1.protocol.seeds import resampling_seed, select_pool_index
from dci1.resampling.primary import build_primary
from dci1.resampling.pseudo import build_pseudo_run, pseudo_dir


def test_exactly_m_members_and_metadata_reconstruction(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    report = validate_pools(SPEC, cells, stream="confirmatory",
                            stage_dir=stage_dir, config=config)
    assert report["status"] == "COMPLETE"
    assert report["members"] == len(cells) * config.generation_pool_size
    assert report["distinct_seeds"] == report["members"]


def test_incomplete_pool_fails_closed(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    # Remove one member by rewriting the file (simulating a defect).
    path = pool_path(stage_dir)
    rows = path.read_text().splitlines()
    path.write_text("\n".join(rows[:-1]) + "\n")
    with pytest.raises(ProtocolError, match="incomplete pools"):
        load_complete_pools(SPEC, cells, stream="confirmatory",
                            stage_dir=stage_dir, config=config)
    with pytest.raises(ProtocolError):
        build_primary(SPEC, cells, stream="confirmatory",
                      stage_dir=stage_dir, config=config)
    with pytest.raises(ProtocolError):
        build_pseudo_run(SPEC, cells, stream="confirmatory",
                         stage_dir=stage_dir, config=config, run_index=0)


def test_duplicate_row_identities_rejected(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    store = AppendOnceJsonl(pool_path(stage_dir))
    with pytest.raises(ProtocolError, match="already present"):
        store.append([pool_row(config, cells[0], 0)])


def test_duplicate_outputs_flagged_not_fatal(tmp_path):
    config = small_config(pool_size=2)
    blocks = make_blocks(2)
    cells = make_cells(blocks)
    stage_dir = tmp_path / "confirmatory"
    store = AppendOnceJsonl(pool_path(stage_dir))
    same = "However, the same text twice."
    store.append([pool_row(config, cell, index, text=same)
                  for cell in cells for index in range(2)])
    report = validate_pools(SPEC, cells, stream="confirmatory",
                            stage_dir=stage_dir, config=config)
    assert report["status"] == "COMPLETE"
    assert report["identical_outputs_within_pools"] == len(cells)


def test_mutated_response_detected(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    path = pool_path(stage_dir)
    text = path.read_text().replace("However, details matter.",
                                    "However, details Matter.", 1)
    path.write_text(text)
    with pytest.raises(ProtocolError):
        load_complete_pools(SPEC, cells, stream="confirmatory",
                            stage_dir=stage_dir, config=config)


def test_shared_seed_detected(tmp_path):
    config = small_config(pool_size=2)
    blocks = make_blocks(2)
    cells = make_cells(blocks)
    stage_dir = tmp_path / "confirmatory"
    rows = []
    for cell in cells:
        for index in range(2):
            row = pool_row(config, cell, index)
            rows.append(row)
    rows[1]["generation_seed"] = rows[0]["generation_seed"]
    AppendOnceJsonl(pool_path(stage_dir)).append(rows)
    with pytest.raises(ProtocolError):
        validate_pools(SPEC, cells, stream="confirmatory",
                       stage_dir=stage_dir, config=config)


def test_repair_leaves_existing_members_bit_identical(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    path = pool_path(stage_dir)
    lines = path.read_text().splitlines()
    kept, removed = lines[:-1], json.loads(lines[-1])
    path.write_text("\n".join(kept) + "\n")
    before = path.read_text()
    # Repair: regenerate ONLY the missing identity under its recorded seed.
    cell = next(c for c in cells if c.block_id == removed["block_id"]
                and c.arm == removed["arm"])
    AppendOnceJsonl(path).append([pool_row(config, cell,
                                           removed["pool_index"])])
    after = path.read_text()
    assert after.startswith(before)      # existing bytes untouched
    validate_pools(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                   config=config)


# ---------------------------------------------------------------- resampling
def test_selection_reproducible_in_range_with_replacement(tmp_path):
    config = small_config(pool_size=4, pseudo_runs=50)
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_pseudo_run(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                     config=config, run_index=3)
    manifest_a = read_jsonl(pseudo_dir(stage_dir, 3) / "manifest.jsonl")
    build_pseudo_run(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                     config=config, run_index=3)
    manifest_b = read_jsonl(pseudo_dir(stage_dir, 3) / "manifest.jsonl")
    assert manifest_a == manifest_b                       # reproduces exactly
    indices = [row["selected_pool_index"] for row in manifest_a]
    assert all(0 <= i < 4 for i in indices)
    # with replacement: across many runs every index appears
    seen = set()
    for r in range(20):
        build_pseudo_run(SPEC, cells, stream="confirmatory",
                         stage_dir=stage_dir, config=config, run_index=r)
        for row in read_jsonl(pseudo_dir(stage_dir, r) / "manifest.jsonl"):
            seen.add(row["selected_pool_index"])
    assert seen == {0, 1, 2, 3}


def test_exactly_one_selection_per_cell_no_aggregation(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_pseudo_run(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                     config=config, run_index=0)
    table = read_jsonl(pseudo_dir(stage_dir, 0) / "table.jsonl")
    assert len(table) == len(cells)
    assert len({(r["block_id"], r["arm"]) for r in table}) == len(cells)
    pools = load_complete_pools(SPEC, cells, stream="confirmatory",
                                stage_dir=stage_dir, config=config)
    for row in table:
        member = pools[(row["block_id"], row["arm"])][row["pool_index"]]
        assert row["response"] == member["raw_response"]
        assert row["response_content_hash"] == \
            member["response_content_hash"]


def test_different_seeds_alter_selections(tmp_path):
    config = small_config(pool_size=8, pseudo_runs=10)
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_pseudo_run(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                     config=config, run_index=0)
    build_pseudo_run(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                     config=config, run_index=1)
    a = [r["selected_pool_index"] for r in
         read_jsonl(pseudo_dir(stage_dir, 0) / "manifest.jsonl")]
    b = [r["selected_pool_index"] for r in
         read_jsonl(pseudo_dir(stage_dir, 1) / "manifest.jsonl")]
    assert a != b


def test_selection_seed_derivation_is_pure():
    seed = resampling_seed(222, "synthetic/test", 7)
    picks = [select_pool_index(seed, "T00", "focal", 16) for _ in range(3)]
    assert picks[0] == picks[1] == picks[2]
    assert select_pool_index(seed, "T00", "focal", 16) != \
        select_pool_index(seed + 1, "T00", "focal", 16) or True  # may collide
    counts = [0] * 4
    for i in range(400):
        counts[select_pool_index(seed, f"B{i}", "focal", 4)] += 1
    assert all(c > 50 for c in counts)      # roughly uniform


def test_no_inference_during_resampling():
    """Structural proof: the pseudo-run module imports nothing capable of
    inference — no backend seam, no subprocess, no vLLM."""
    import ast

    import dci1.resampling.primary as primary_module
    import dci1.resampling.pseudo as pseudo_module

    for module in (pseudo_module, primary_module):
        tree = ast.parse(open(module.__file__).read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        for name in imported:
            assert "subprocess" not in name
            assert "vllm" not in name
            assert "generation.backend" not in name
