"""§18 stage 14, ``CONFIRMATORY_GENERATION``: the experiment the freeze
licensed, and nothing else.

**The design comes from the freeze record, not from the constants.** After
Gate 5 the record is the licence: the admitted arms, the derived cell count,
the block count, M, the completion cap, the slot map, the seeds and the
verifier hash are all read from it and asserted against what the runner is
about to use. A runner that re-derived them from ``protocol/constants.py``
would silently run a different experiment if a constant moved, and the whole
point of a freeze is that it cannot.

**Every expected row exactly once.** Row identity is
``(block, cell, draw)``; the plan is built whole before the first generation;
completeness is checked over the union of every batch against the freeze's
own arithmetic. A missing, duplicated or unexpected identity is a refusal.

**Resume does not change row identity.** A previous batch's rows are reused
only when the design this call would give is the one that produced them ---
same identities, same prompt hashes, same seeds, same order. A partial match
is how a study ends up with two experimental conditions under one label, so a
partial match regenerates.

**Nothing here reads an outcome.** No generation is discarded for what it
says, no draw is selected, all M are kept, and no estimate is computed. The
scoring is §9.1's: every registered instance the replication uses is scored
on every row, present where the prompt stated it and absent everywhere else,
so the confirmatory rows carry the chance and counterfactual-chance verdicts
the analysis will need without a second pass.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v4.models.registry import MODELS

from dci1v6.design.cells import design_cells, n_cells_for, normalise_arms
from dci1v6.engine.paths import ModelTree
from dci1v6.protocol import constants as C
from dci1v6.run.execute import generate_and_score, prompt_cell
from dci1v6.run.freeze_run import assert_matches_freeze, load_freeze
from dci1v6.run.lifecycle import (StageOutcome, confirmatory_licensed,
                                  frozen_identified_replications,
                                  protocol_identity, run_stage)
from dci1v6.topics.bank import TopicBank, load_bank
from dci1v6.verifiers import verifier_source_hash
from dci1v6.verifiers.constraints import Constraint

__all__ = ["BATCH_BLOCKS", "Block", "confirmatory_blocks", "batches",
           "licensed_design", "run_batch", "collect_rows", "completeness",
           "confirmatory_payload", "run_confirmatory"]

BATCH_BLOCKS = 32


class Block:
    """One confirmatory block: a topic and its position in the released order."""

    __slots__ = ("block_id", "index", "topic_id", "area")

    def __init__(self, block_id: str, index: int, topic_id: str, area: str):
        self.block_id, self.index = block_id, index
        self.topic_id, self.area = topic_id, area


def confirmatory_blocks(bank: TopicBank) -> list[Block]:
    """§14.1's blocks: the 384 confirmatory topics, in released order."""
    topics = list(bank.topics("confirmatory"))
    if len(topics) != C.N_BLOCKS:
        raise ProtocolError(
            f"§16.2 registers {C.N_BLOCKS} blocks and the confirmatory set "
            f"carries {len(topics)} topics")
    return [Block(f"block-{i:04d}", i, t["topic_id"], t["area"])
            for i, t in enumerate(topics)]


def batches(n_blocks: int | None = None, *, size: int = BATCH_BLOCKS
            ) -> list[tuple[int, int]]:
    total = n_blocks if n_blocks is not None else C.N_BLOCKS
    return [(start, min(start + size, total))
            for start in range(0, total, size)]


def licensed_design(tree: ModelTree, *, bank: TopicBank | None = None
                    ) -> dict[str, Any]:
    """What the freeze licensed, read from the freeze and asserted."""
    record = load_freeze(tree)
    freeze = record["freeze"]
    arms = normalise_arms(freeze["admitted_arms"])
    assert_matches_freeze(record, claimed={
        "admitted_arms": list(arms),
        "derived_cell_count": n_cells_for(arms),
        "m_draws": C.M_DRAWS, "n_blocks": C.N_BLOCKS,
        "canonical_verifier_hash": verifier_source_hash()},
        where="confirmatory:licensed_design")
    slot_map = {slot: Constraint(*value) if isinstance(value, (list, tuple))
                else Constraint(**value)
                for slot, value in (record.get("slot_map") or {}).items()}
    if not slot_map:
        raise ProtocolError(
            "the freeze record carries no slot map, so no cell can be "
            "rendered. §18.1 binds the exact wordings and the exact "
            "constituents; a confirmatory run may not choose them")
    bank = bank if bank is not None else load_bank()
    return {"freeze_record": record, "freeze": freeze, "arms": arms,
            "slot_map": slot_map, "blocks": confirmatory_blocks(bank),
            "cap": freeze["completion_cap"], "draws": freeze["m_draws"],
            "cells_per_block": freeze["derived_cell_count"],
            "freeze_hash": record["freeze_hash"], "bank": bank}


def run_batch(tree: ModelTree, design: Mapping[str, Any], *,
              start: int, stop: int, device: int = 0,
              generate: Callable[..., dict[str, Any]] | None = None
              ) -> list[dict[str, Any]]:
    """One contiguous batch of blocks, generated whole and scored."""
    blocks = design["blocks"][start:stop]
    cells = design_cells(blocks, design["arms"], draws=design["draws"])
    by_id = {t["topic_id"]: t for t in design["bank"].topics("confirmatory")}
    prompts = [prompt_cell(cell, by_id[cell.topic_id],
                           slot_map=design["slot_map"],
                           topic_split="confirmatory")
               for cell in cells]
    instances = tuple(dict.fromkeys(design["slot_map"].values()))
    return generate_and_score(
        tree.model_key, prompts, stage=C.STAGE_CONFIRMATORY,
        cap=design["cap"], device=device,
        run_dir=tree.backend_runs(C.STAGE_CONFIRMATORY)
        / f"blocks-{start:04d}-{stop:04d}",
        instances=instances, slot_map=design["slot_map"],
        study_id=tree.context.study_id,
        protocol_identity=protocol_identity(tree, C.STAGE_CONFIRMATORY),
        generate=generate)


def collect_rows(tree: ModelTree) -> list[dict[str, Any]]:
    """Every scored confirmatory row this replication has on disk."""
    root = tree.backend_runs(C.STAGE_CONFIRMATORY)
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    from dci1v6.engine.paths import current_files

    for path in current_files(root, "scored.jsonl"):
        rows.extend(json.loads(line) for line in
                    path.read_text().splitlines() if line.strip())
    return rows


def completeness(design: Mapping[str, Any],
                 rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """§14.2: complete means every registered identity, exactly once."""
    expected: set[str] = set()
    for block in design["blocks"]:
        for cell in design_cells([block], design["arms"],
                                 draws=design["draws"]):
            for draw in range(design["draws"]):
                expected.add(f"{block.block_id}:{cell.cell_id}:{draw}")
    seen: dict[str, int] = {}
    for row in rows:
        seen[row["row_id"]] = seen.get(row["row_id"], 0) + 1
    duplicates = sorted(k for k, n in seen.items() if n > 1)
    missing = sorted(expected - set(seen))
    unexpected = sorted(set(seen) - expected)
    return {
        "expected": len(expected), "produced": len(seen),
        "n_missing": len(missing), "n_duplicate": len(duplicates),
        "n_unexpected": len(unexpected),
        "missing": missing[:10], "duplicates": duplicates[:10],
        "unexpected": unexpected[:10],
        "complete": not (missing or duplicates or unexpected),
        "rule": "every (block, cell, draw) identity exactly once; all M "
                "draws kept and none selected (§14.2)",
    }


def confirmatory_payload(tree: ModelTree, *, producing_commit: str,
                         bank: TopicBank | None = None, device: int = 0,
                         generate: Callable[..., dict[str, Any]] | None = None,
                         block_limit: int | None = None) -> dict[str, Any]:
    # §34 D22: what licenses confirmatory generation at all. The check is
    # here, on the mandatory path, before a single row is generated --- a
    # licensing rule that lives in prose is a rule a run can walk past.
    licence = confirmatory_licensed(
        this_replication_frozen=True,
        survivors=frozen_identified_replications(
            tree.context, sorted(m.model_key for m in MODELS)))
    if not licence["licensed"]:
        raise ProtocolError(
            f"{C.STAGE_CONFIRMATORY} is not licensed for {tree.model_key}: "
            f"{licence['reason']}")
    design = licensed_design(tree, bank=bank)
    if block_limit is not None:
        from dci1v6.run.gates_run import assert_synthetic_only
        assert_synthetic_only(tree, "block_limit", block_limit)
        design = {**design, "blocks": design["blocks"][:block_limit]}
    produced = 0
    for start, stop in batches(len(design["blocks"])):
        produced += len(run_batch(tree, design, start=start, stop=stop,
                                  device=device, generate=generate))
    rows = collect_rows(tree)
    report = completeness(design, rows)
    if not report["complete"]:
        raise ProtocolError(
            f"§14.2: the confirmatory draw matrix is incomplete --- {report}")
    truncated = sum(1 for r in rows if r["truncated"])
    empty = sum(1 for r in rows if r["empty"])
    failures = sum(1 for r in rows for s in r["scores"]
                   if s["processing_failure"])
    return {
        "stage": C.STAGE_CONFIRMATORY,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_CONFIRMATORY],
        "outcome": "PASS",
        "inputs": {"freeze": {"stage": C.STAGE_GATE5,
                              "freeze_hash": design["freeze_hash"]}},
        "producing_commit": producing_commit,
        "freeze_hash": design["freeze_hash"],
        "confirmatory_licence": licence,
        "rows_path": str(tree.backend_runs(C.STAGE_CONFIRMATORY)),
        "n_rows": len(rows),
        "n_generated_this_call": produced,
        "completeness": report,
        "blocks": len(design["blocks"]),
        "cells_per_block": design["cells_per_block"],
        "draws": design["draws"],
        "admitted_arms": list(design["arms"]),
        "canonical_verifier_hash": verifier_source_hash(),
        "truncation": {"n_truncated": truncated, "n_empty": empty,
                       "n_processing_failures": failures,
                       "share_truncated": truncated / max(1, len(rows))},
        "no_outcome_read":
            "no generation is discarded for what it says, no draw is "
            "selected, all M are kept, and no estimate is computed here",
    }


def run_confirmatory(tree: ModelTree, *, producing_commit: str | None = None,
                     environment_digest: str = "",
                     bank: TopicBank | None = None, device: int = 0,
                     generate: Callable[..., dict[str, Any]] | None = None,
                     block_limit: int | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_CONFIRMATORY,
        compute=lambda _prev: confirmatory_payload(
            tree, producing_commit=commit, bank=bank, device=device,
            generate=generate, block_limit=block_limit),
        producing_commit=commit, environment_digest=environment_digest)
