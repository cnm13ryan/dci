"""Stage 5, ``CONFIRMATORY_GENERATION``: the protected composed cells.

The design comes from the signed freeze and nowhere else: the entering
frames, their arms, slot maps and spectrum slots, the blocks per frame,
the draws and the cap are read from it and asserted against what this
runner is about to use. Every expected (block, cell, draw) identity is
generated exactly once per frame; resume reuses a stored batch only under
an identical generation identity; nothing here reads an outcome, drops a
draw or computes an estimate.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.topics.bank import TopicBank, load_bank
from dci1v7.verifiers.constraints import Constraint

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.design import (FrameBlock, assert_frame_allocation,
                                      design_cells, frame_blocks)
from dci1v8dev.confirm.execute import (generate_and_score, prompt_cell,
                                       resolve_generate)
from dci1v8dev.confirm.freeze import load_freeze
from dci1v8dev.confirm.membership import constraint_of
from dci1v8dev.run.context import current_files

__all__ = ["BATCH_BLOCKS", "frame_topics", "licensed_design", "run_batch",
           "collect_rows", "completeness", "generation_payload",
           "run_generation"]

BATCH_BLOCKS = 32


def frame_topics(topics: Sequence[Mapping[str, Any]], frame: int, *,
                 blocks_per_frame: int) -> list[Mapping[str, Any]]:
    """The topics frame ``frame`` holds under the allocation: at the ceiling
    every topic; below it, the pass-offset scheme (position i under frame f
    iff (f - i) mod N_WORDINGS < passes)."""
    n = len(topics)
    if blocks_per_frame == n:
        return list(topics)
    if blocks_per_frame % (n // C.N_WORDINGS):
        raise ProtocolError(f"{blocks_per_frame} blocks per frame is not a "
                            "whole number of passes")
    passes = blocks_per_frame // (n // C.N_WORDINGS)
    return [t for i, t in enumerate(topics)
            if (frame - i) % C.N_WORDINGS < passes]


def licensed_design(tree: L.ConfirmTree, *, bank: TopicBank | None = None,
                    block_limit: int | None = None) -> dict[str, Any]:
    freeze, freeze_hash = load_freeze(tree)
    design = freeze["design"]
    bank = bank if bank is not None else load_bank()
    topics = list(bank.topics("confirmatory"))
    if block_limit is not None:
        if not tree.synthetic:
            raise ProtocolError("block_limit is a synthetic-namespace knob")
        topics = topics[:block_limit]
    frames: dict[int, dict[str, Any]] = {}
    for w, e in design["frames"].items():
        slot_map = {slot: constraint_of(v) for slot, v in e["slot_map"].items()}
        per_frame = (min(int(design["blocks_per_frame"]), len(topics))
                     if block_limit is not None else int(design["blocks_per_frame"]))
        held = frame_topics(topics, int(w), blocks_per_frame=per_frame)
        blocks = [FrameBlock(position=i, frame=int(w), topic_id=t["topic_id"],
                             area=t["area"]) for i, t in enumerate(held)]
        frames[int(w)] = {"arms": list(e["arms"]),
                          "n_spectrum": int(e["n_spectrum_slots"]),
                          "runner_up": tuple(e.get("runner_up_slots") or ()),
                          "cells_per_block": int(e["cells_per_block"]),
                          "slot_map": slot_map, "blocks": blocks}
    return {"freeze": freeze, "freeze_hash": freeze_hash, "frames": frames,
            "draws": int(design["draws"]), "cap": int(design["completion_cap"]),
            "blocks_per_frame": int(design["blocks_per_frame"]),
            "topics": {t["topic_id"]: t for t in topics}, "bank": bank}


def run_batch(tree: L.ConfirmTree, design: Mapping[str, Any], *, frame: int,
              start: int, stop: int, device: int,
              generate: Callable[..., dict[str, Any]] | None
              ) -> list[dict[str, Any]]:
    fr = design["frames"][frame]
    blocks = fr["blocks"][start:stop]
    cells = design_cells(blocks, fr["arms"], n_spectrum=fr["n_spectrum"], runner_up=fr["runner_up"],
                         draws=design["draws"])
    prompts = [prompt_cell(c, design["topics"][c.topic_id],
                           slot_map=fr["slot_map"]) for c in cells]
    instances = tuple(dict.fromkeys(fr["slot_map"].values()))
    return generate_and_score(
        tree.model_key, prompts, stage=L.STAGE_GENERATION, cap=design["cap"],
        device=device,
        run_dir=tree.backend_runs(L.STAGE_GENERATION)
        / f"frame-{frame}-blocks-{start:04d}-{stop:04d}",
        instances=instances, slot_map=fr["slot_map"],
        study_id=tree.context.study_id,
        protocol_identity=L.protocol_identity(tree, L.STAGE_GENERATION),
        generate=generate, composed_licensed=True)


def collect_rows(tree: L.ConfirmTree) -> list[dict[str, Any]]:
    root = tree.backend_runs(L.STAGE_GENERATION)
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in current_files(root, "scored.jsonl"):
        rows.extend(json.loads(line) for line in path.read_text().splitlines()
                    if line.strip())
    return rows


def completeness(design: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
                 ) -> dict[str, Any]:
    expected: set[str] = set()
    for frame, fr in design["frames"].items():
        for cell in design_cells(fr["blocks"], fr["arms"], n_spectrum=fr["n_spectrum"], runner_up=fr["runner_up"],
                                 draws=design["draws"]):
            for draw in range(design["draws"]):
                expected.add(f"{cell.block_id}:{cell.cell_id}:{draw}")
    seen: dict[str, int] = {}
    for row in rows:
        seen[row["row_id"]] = seen.get(row["row_id"], 0) + 1
    duplicates = sorted(k for k, n in seen.items() if n > 1)
    missing = sorted(expected - set(seen))
    unexpected = sorted(set(seen) - expected)
    return {"expected": len(expected), "produced": len(seen),
            "n_missing": len(missing), "n_duplicate": len(duplicates),
            "n_unexpected": len(unexpected), "missing": missing[:10],
            "duplicates": duplicates[:10], "unexpected": unexpected[:10],
            "complete": not (missing or duplicates or unexpected),
            "rule": "every (block, cell, draw) identity exactly once per "
                    "frame; all M draws kept and none selected"}


def generation_payload(tree: L.ConfirmTree, *, producing_commit: str,
                       device: int = 0,
                       generate: Callable[..., dict[str, Any]] | None = None,
                       block_limit: int | None = None,
                       frames_only: Sequence[int] | None = None
                       ) -> dict[str, Any]:
    design = licensed_design(tree, block_limit=block_limit)
    generate = resolve_generate(tree, generate, where=L.STAGE_GENERATION)
    allocation: dict[str, Any] = {}
    produced = 0
    for frame, fr in sorted(design["frames"].items()):
        if frames_only is not None and frame not in frames_only:
            continue
        cells = design_cells(fr["blocks"], fr["arms"], n_spectrum=fr["n_spectrum"], runner_up=fr["runner_up"], draws=design["draws"])
        allocation[str(frame)] = assert_frame_allocation(
            cells, fr["arms"], n_spectrum=fr["n_spectrum"], frame=frame,
            blocks_expected=len(fr["blocks"]), runner_up=fr["runner_up"])
        if fr["cells_per_block"] != allocation[str(frame)]["cells_per_block"]:
            raise ProtocolError(f"frame {frame}: the plan derives "
                                f"{allocation[str(frame)]['cells_per_block']} "
                                f"cells and the freeze bound "
                                f"{fr['cells_per_block']}")
        n = len(fr["blocks"])
        for start in range(0, n, BATCH_BLOCKS):
            stop = min(start + BATCH_BLOCKS, n)
            produced += len(run_batch(tree, design, frame=frame, start=start,
                                      stop=stop, device=device,
                                      generate=generate))
    rows = collect_rows(tree)
    report = completeness(design, rows)
    if not report["complete"]:
        raise L.TerminalStatus(
            "GENERATION_INCOMPLETE", gate=L.STAGE_GENERATION,
            criterion="every registered identity exactly once",
            observed={k: report[k] for k in ("expected", "produced",
                                             "n_missing", "n_duplicate",
                                             "n_unexpected")},
            strongest_permissible_statement="the confirmatory draw matrix "
                                            "is incomplete; no estimate is "
                                            "formed")
    truncated = sum(1 for r in rows if r["truncated"])
    return {
        "stage": L.STAGE_GENERATION,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_GENERATION],
        "outcome": "PASS", "producing_commit": producing_commit,
        "inputs": {"freeze_hash": design["freeze_hash"]},
        "freeze_hash": design["freeze_hash"],
        "rows_path": str(tree.backend_runs(L.STAGE_GENERATION)),
        "n_rows": len(rows), "n_generated_this_call": produced,
        "completeness": report, "allocation_realised": allocation,
        "frames": {str(f): {"blocks": len(fr["blocks"]),
                            "cells_per_block": fr["cells_per_block"],
                            "arms": fr["arms"]}
                   for f, fr in design["frames"].items()},
        "draws": design["draws"], "cap": design["cap"],
        "truncation": {"n_truncated": truncated,
                       "share_truncated": truncated / max(1, len(rows))},
        "protected": True,
        "no_outcome_read": "no generation is discarded for what it says, no "
                           "draw is selected, all M are kept, and no "
                           "estimate is computed here",
    }


def run_generation(tree: L.ConfirmTree, *, producing_commit: str | None = None,
                   environment_digest: str = "", device: int = 0,
                   generate: Callable[..., dict[str, Any]] | None = None,
                   block_limit: int | None = None) -> L.StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return L.run_stage(
        tree, L.STAGE_GENERATION,
        compute=lambda _prev: generation_payload(
            tree, producing_commit=commit, device=device, generate=generate,
            block_limit=block_limit),
        producing_commit=commit, environment_digest=environment_digest)
