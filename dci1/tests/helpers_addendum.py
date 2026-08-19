"""Shared synthetic Addendum-A tree: a small but complete evidence flow."""
from __future__ import annotations

from pathlib import Path

from helpers import M_PARAM, REFS, SPEC, N, response_text, small_config

from dci1 import flow
from dci1.design.blocks import Block, order_for_index
from dci1.design.prompts import prompt_for_cell
from dci1.evidence.layout import StudyTree
from dci1.evidence.sealing import CacheWriter, replicate_raw_layers, seal_stage
from dci1.evidence.store import write_json
from dci1.generation.pools import Cell
from dci1.protocol.constants import ARMS
from dci1.protocol.hashing import sha, sha_text
from dci1.protocol.seeds import generation_seed

ENVIRONMENT = {"environment_digest": "synthetic-env", "gcn_archs": []}


def make_tree(tmp_path: Path, *, blocks_count: int = 6,
              config=None) -> tuple[StudyTree, list[Block], list[Cell]]:
    config = config or small_config()
    tree = StudyTree(model_slug=SPEC.model_key, freeze_id="testfreeze",
                     base=Path(tmp_path) / "evidence",
                     durable_base=Path(tmp_path) / "durable")
    blocks = [Block(index=i, block_id=f"T{i:02d}",
                    topic_id=f"test-topic-{i}",
                    question=f"Why is test question number {i} interesting?",
                    order=order_for_index(i), wording_target=i % 4,
                    wording_added=(i // 4) % 4)
              for i in range(blocks_count)]
    cells = [Cell(block_id=b.block_id, arm=arm,
                  prompt=prompt_for_cell(b, arm, n=N, m=M_PARAM,
                                         references=REFS))
             for b in blocks for arm in ARMS]
    return tree, blocks, cells


def fill_cache(tree: StudyTree, cells: list[Cell], config) -> None:
    writer = CacheWriter(tree.cache_file)
    rows = []
    for cell in cells:
        for index in range(config.generation_pool_size):
            text = response_text(cell.block_id, cell.arm, index)
            rows.append({
                "row_id": f"{SPEC.model_key}:confirmatory:{cell.block_id}:"
                          f"{cell.arm}:{index}",
                "model_key": SPEC.model_key, "model_id": SPEC.model_id,
                "model_revision": SPEC.revision, "stream": "confirmatory",
                "block_id": cell.block_id, "arm": cell.arm,
                "prompt_hash": cell.prompt_sha, "pool_index": index,
                "generation_seed": generation_seed(
                    config.generation_root_seed, "confirmatory",
                    SPEC.model_id, cell.prompt_sha, index),
                "raw_response": text, "final_answer": text.strip(),
                "response_content_hash": sha_text(text),
                "token_count": len(text.split()), "finish_reason": "stop",
                "backend_config_hash": sha_text("test-backend-config")})
    writer.append(rows)


def freeze_stub(tree: StudyTree, config) -> str:
    payload = {"TEST_RECORD": True, "model": {"model_id": SPEC.model_id},
               "resampling": config.to_dict()}
    write_json(tree.freeze_record, payload)
    return sha(payload)


def full_tree(tmp_path: Path, *, blocks_count: int = 6,
              config=None):
    """prompts + sealed cache + replication + freeze stub, ready to derive."""
    config = config or small_config()
    tree, blocks, cells = make_tree(tmp_path, blocks_count=blocks_count,
                                    config=config)
    flow.write_prompts(tree, cells)
    fill_cache(tree, cells, config)
    seal_stage(tree, "cache")
    replicate_raw_layers(tree)
    record_hash = freeze_stub(tree, config)
    return tree, blocks, cells, config, record_hash


def derive(tree, blocks, cells, config, record_hash, *, stage="final",
           drill=False):
    return flow.derive_primary(
        tree, SPEC, blocks, cells, stream="confirmatory", config=config,
        n=N, m=M_PARAM, references=REFS, freeze_record_hash=record_hash,
        bootstrap_seed_value=99, analysis_stage=stage,
        environment_record=ENVIRONMENT, n_resamples=200, allow_dirty=True,
        drill_rebuild=drill)
