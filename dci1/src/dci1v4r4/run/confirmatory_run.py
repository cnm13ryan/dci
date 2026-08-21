"""The confirmatory generation, in registered block batches (§21, §14.2).

Generation is licensed by the freeze and by nothing else, and the plan is
derived from the freeze record, so this module decides nothing scientific. What
it adds is the one operational thing 144,384 generations per model need: the
work is cut into contiguous **block batches**, each its own backend run
directory, so an interruption costs one batch rather than the study.

Batching is not selection. The batches are a partition of the registered block
list in registered order, every batch is generated whole, and completeness is
checked against `expected_row_ids` over the union at the end. Nothing here can
choose a draw, drop a generation, or re-run a cell: `assert_no_selective_rerun`
sees the union and refuses a row set that is not the plan's own.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from dci1v4.engine import fs
from dci1v4.errors import IntegrityError

from dci1v4r4.engine.paths import ModelTree
from dci1v4r4.protocol import constants as C
from dci1v4r4.run.design_run import (
    absent_instances, attach_slots, design_cells_for,
)
from dci1v4r4.run.execute import generate_and_score
from dci1v4r4.stages import confirmatory as CF
from dci1v4r4.topics import split_topics

__all__ = ["STAGE_CONFIRMATORY", "BATCH_BLOCKS", "batches", "run_batch",
           "collect_rows", "completeness", "run_confirmatory"]

STAGE_CONFIRMATORY = "v4r3-confirmatory"

#: Blocks per backend run. 16 blocks is about 6,000 generations at the full
#: design, which is a batch a machine finishes in minutes and an interruption
#: can afford to lose.
BATCH_BLOCKS = 16


def _confirmatory_blocks() -> list[dict[str, Any]]:
    """§14.1's blocks: the 384 confirmatory topics, in released order.

    The index is the position in that order, and §8.4's wording allocation
    reads it. Re-ordering the list would re-allocate every wording, which is
    why the order is taken from the released split and never sorted here.
    """
    return list(split_topics()["confirmatory"])


def batches(n_blocks: int | None = None, *, size: int = BATCH_BLOCKS
            ) -> list[tuple[int, int]]:
    total = n_blocks if n_blocks is not None else len(_confirmatory_blocks())
    return [(start, min(start + size, total))
            for start in range(0, total, size)]


def run_batch(model_key: str, tree: ModelTree, *, freeze_record: Mapping,
              start: int, stop: int, device: int = 0, generate=None
              ) -> list[dict[str, Any]]:
    """One contiguous batch of blocks, generated whole and scored."""
    CF.assert_generation_licensed(freeze_record)
    blocks = _confirmatory_blocks()[start:stop]
    slot_map = dict(freeze_record["slot_map"])
    variant = freeze_record["design_variant"]
    index_of = {t["topic_id"]: i
                for i, t in enumerate(_confirmatory_blocks())}
    pairs = design_cells_for(blocks, slot_map, variant=variant,
                             prefix="conf", block_prefix="block",
                             block_index_of=index_of)
    cells = [c for c, _, _ in pairs]
    block_of = {c.cell_id: b for c, b, _ in pairs}
    design_cell_of = {c.cell_id: d for c, _, d in pairs}
    run_dir = (tree.backend_runs(C.STAGE_CONFIRMATORY)
               / f"blocks-{start:04d}-{stop:04d}")
    rows = generate_and_score(
        model_key, cells, stage=STAGE_CONFIRMATORY,
        cap=freeze_record["completion_cap"], draws=int(freeze_record["m_draws"]),
        device=device, run_dir=run_dir, absent=absent_instances(slot_map),
        generate=generate)
    resolved = attach_slots(rows, block_of, slot_map, design_cell_of)
    # The scored rows the backend seam writes carry neither the block nor the
    # design cell type: both are attached here, above that seam. §14.2's
    # completeness rule is stated over (block, cell type, draw), so a resume
    # that re-read `scored.jsonl` would be reading rows the rule cannot see.
    fs.atomic_write_text(
        run_dir / "resolved.jsonl",
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in resolved))
    return resolved


def collect_rows(tree: ModelTree) -> list[dict[str, Any]]:
    """Every scored confirmatory row this replication has on disk."""
    root = tree.backend_runs(C.STAGE_CONFIRMATORY)
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.glob("blocks-*/resolved.jsonl")):
        rows.extend(fs.read_jsonl(path))
    return rows


def completeness(freeze_record: Mapping[str, Any],
                 rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """§14.2: complete means every registered identity, exactly once.

    The identity is (block, **design cell type**, draw). The execution cell id
    carries the topic and the constraint labels and is a different string; a
    completeness rule stated over it would be comparing the plan against
    names the plan does not use.
    """
    plan_rows = [{"block_id": _block_key(r["block_id"]),
                  "cell_id": r["design_cell_id"],
                  "draw_index": r["draw_index"]} for r in rows]
    return CF.missing_rows(freeze_record, plan_rows)


def _block_key(block_id: str) -> str:
    """The freeze names blocks by topic id; the runner prefixes them."""
    return block_id[len("block-"):] if block_id.startswith("block-") \
        else block_id


def run_confirmatory(model_key: str, tree: ModelTree, *,
                     freeze_record: Mapping, device: int = 0,
                     batch_size: int = BATCH_BLOCKS,
                     generate=None) -> dict[str, Any]:
    """Every batch, then the completeness rule over the union."""
    plan = CF.confirmatory_plan(freeze_record)
    CF.assert_plan_matches_freeze({**plan, **{
        k: freeze_record[k] for k in
        ("design_variant", "m_draws", "completion_cap", "model_revision",
         "verifier_source_hash", "producing_commit")}}, freeze_record)
    total = len(_confirmatory_blocks())
    done = 0
    for start, stop in batches(total, size=batch_size):
        run_batch(model_key, tree, freeze_record=freeze_record, start=start,
                  stop=stop, device=device, generate=generate)
        done += stop - start
    rows = collect_rows(tree)
    report = completeness(freeze_record, rows)
    if not report["complete"]:
        raise IntegrityError(
            f"the confirmatory row set is not complete: {report['missing']} "
            f"missing, {report['duplicated']} duplicated, "
            f"{report['unexpected']} unexpected. §14.2 forms a cell mean over "
            f"exactly M accepted draws or not at all")
    return {"outcome": "PASS", "stage": C.STAGE_CONFIRMATORY,
            "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_CONFIRMATORY],
            "model_key": model_key, "plan": plan, "blocks_generated": done,
            "rows": len(rows), "completeness": report,
            "batch_blocks": batch_size,
            "batching_is_not_selection": (
                "the batches partition the registered block list in "
                "registered order, every batch is generated whole, and "
                "completeness is evaluated over the union")}
