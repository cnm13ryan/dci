"""Shared synthetic fixtures: a structurally faithful fake confirmatory stage."""
from __future__ import annotations

from pathlib import Path

from dci1.design.blocks import Block, order_for_index
from dci1.design.prompts import prompt_for_cell
from dci1.evidence.store import AppendOnceJsonl
from dci1.generation.pools import Cell, pool_path
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import ARMS, StudyConfig
from dci1.protocol.hashing import sha_text
from dci1.protocol.seeds import generation_seed

N, M_PARAM = 2, 8
REFS = ("C1", "C3", "C10")

SPEC = ModelSpec(
    model_key="_test", model_id="synthetic/test", revision="test-rev-0",
    family="synthetic", chat_template_kwargs={}, switch_expectation="inert",
    leakage_markers=("<think>",))


def small_config(pool_size: int = 4, pseudo_runs: int = 20) -> StudyConfig:
    return StudyConfig(
        generation_pool_size=pool_size,
        primary_selection_rule="primary_pool_index=0",
        pool_to_cell_mapping="one cached response per (model, block, arm), "
                             "sampled with replacement, never aggregated",
        pseudo_run_count=pseudo_runs,
        generation_root_seed=111, resampling_root_seed=222,
        bootstrap_seed=333)


def make_blocks(count: int = 6) -> list[Block]:
    return [Block(index=i, block_id=f"T{i:02d}", topic_id=f"test-topic-{i}",
                  question=f"Why is test question number {i} interesting?",
                  order=order_for_index(i), wording_target=i % 4,
                  wording_added=(i // 4) % 4)
            for i in range(count)]


def make_cells(blocks: list[Block]) -> list[Cell]:
    return [Cell(block_id=b.block_id, arm=arm,
                 prompt=prompt_for_cell(b, arm, n=N, m=M_PARAM,
                                        references=REFS))
            for b in blocks for arm in ARMS]


def response_text(block_id: str, arm: str, index: int) -> str:
    weight = int(sha_text(f"{block_id}|{arm}|{index}")[:2], 16)
    count = weight % 4
    return " ".join(["The answer explains the point simply."]
                    + ["However, details matter."] * count)


def pool_row(config: StudyConfig, cell: Cell, index: int,
             text: str | None = None) -> dict:
    text = response_text(cell.block_id, cell.arm, index) \
        if text is None else text
    return {
        "row_id": f"_test:confirmatory:{cell.block_id}:{cell.arm}:{index}",
        "model_key": SPEC.model_key, "model_id": SPEC.model_id,
        "model_revision": SPEC.revision, "stream": "confirmatory",
        "block_id": cell.block_id, "arm": cell.arm,
        "prompt_hash": cell.prompt_sha, "pool_index": index,
        "generation_seed": generation_seed(
            config.generation_root_seed, "confirmatory", SPEC.model_id,
            cell.prompt_sha, index),
        "raw_response": text, "final_answer": text.strip(),
        "response_content_hash": sha_text(text),
        "token_count": len(text.split()), "finish_reason": "stop",
        "backend_config_hash": sha_text("test-backend-config"),
    }


def write_stage(tmp_path: Path, config: StudyConfig,
                blocks: list[Block] | None = None,
                ) -> tuple[Path, list[Block], list[Cell]]:
    blocks = blocks if blocks is not None else make_blocks()
    cells = make_cells(blocks)
    stage_dir = Path(tmp_path) / "confirmatory"
    store = AppendOnceJsonl(pool_path(stage_dir))
    store.append([pool_row(config, cell, index)
                  for cell in cells
                  for index in range(config.generation_pool_size)])
    return stage_dir, blocks, cells
