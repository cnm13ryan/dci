"""Pseudo-run resampling over the frozen cache (amendment §2.6, §2.8).

A pseudo-run reconstructs the experiment once, without any model inference:
for every registered cell it selects one cached response uniformly with
replacement, under level-2 randomness derived from the frozen resampling root
seed, the model identity and the pseudo-run index. Selections are
per-cell reconstructable from the manifest alone.

Structural separation (amendment §2.7): this module writes ONLY into the
``pseudo/`` lineage — the write guard refuses any path that resolves inside a
``primary/`` directory — and it imports nothing capable of inference (no
backend module, no subprocess). Executing any number of pseudo-runs leaves the
primary lineage bit-identical; `assert_primary_invariant` makes that an
executable check.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dci1.evidence.store import atomic_write, fingerprint_tree
from dci1.generation.pools import Cell
from dci1.generation.validation import load_complete_pools
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import ProtocolError, StudyConfig
from dci1.protocol.seeds import resampling_seed, select_pool_index


def pseudo_dir(stage_dir: Path, run_index: int) -> Path:
    return Path(stage_dir) / "pseudo" / f"run_{run_index:04d}"


def _guard_pseudo_path(path: Path) -> Path:
    parts = Path(path).parts
    if "pseudo" not in parts or "primary" in parts:
        raise ProtocolError(
            f"pseudo-run code may write only into the pseudo lineage; "
            f"refused {path}")
    return Path(path)


def build_pseudo_run(spec: ModelSpec, cells: list[Cell], *, stream: str,
                     stage_dir: Path, config: StudyConfig,
                     run_index: int) -> dict[str, Any]:
    """One pseudo-run: manifest + accepted-like table, no inference."""
    if stream != "confirmatory":
        raise ProtocolError(
            "pseudo-run resampling is registered for the confirmatory pools "
            f"only; refused for stream {stream!r}")
    if not 0 <= run_index < config.pseudo_run_count:
        raise ProtocolError(
            f"pseudo_run_index {run_index} outside the frozen pseudo_run_count "
            f"{config.pseudo_run_count}")
    pools = load_complete_pools(spec, cells, stream=stream,
                                stage_dir=stage_dir, config=config)
    seed_r = resampling_seed(config.resampling_root_seed, spec.model_id,
                             run_index)
    run_id = f"pseudo_{run_index:04d}"

    manifest_rows, table_rows = [], []
    for cell in cells:
        index = select_pool_index(seed_r, cell.block_id, cell.arm,
                                  config.generation_pool_size)
        member = pools[(cell.block_id, cell.arm)][index]
        manifest_rows.append({
            "pseudo_run_id": run_id,
            "model_id": spec.model_id,
            "block_id": cell.block_id,
            "arm": cell.arm,
            "selected_pool_index": index,
            "selected_response_hash": member["response_content_hash"],
            "resampling_seed": seed_r,
        })
        table_rows.append({
            "row_id": f"{spec.model_key}:{run_id}:{cell.block_id}:{cell.arm}",
            "pseudo_run_id": run_id,
            "model_key": spec.model_key,
            "block_id": cell.block_id,
            "arm": cell.arm,
            "prompt_hash": cell.prompt_sha,
            "pool_index": index,
            "response": member["raw_response"],
            "response_content_hash": member["response_content_hash"],
            "token_count": int(member["token_count"]),
            "finish_reason": member["finish_reason"],
        })

    out = _guard_pseudo_path(pseudo_dir(stage_dir, run_index))
    atomic_write(out / "manifest.jsonl",
                 "".join(json.dumps(r, sort_keys=True) + "\n"
                         for r in manifest_rows))
    atomic_write(out / "table.jsonl",
                 "".join(json.dumps(r, sort_keys=True) + "\n"
                         for r in table_rows))
    return {"pseudo_run_id": run_id, "resampling_seed": seed_r,
            "cells": len(cells), "dir": str(out)}


def primary_fingerprint(stage_dir: Path) -> dict[str, str]:
    """Bit-identity fingerprint of the primary lineage (amendment §2.7)."""
    root = Path(stage_dir) / "primary"
    if not root.exists():
        raise ProtocolError(f"no primary lineage under {stage_dir}")
    return fingerprint_tree(root)


def assert_primary_invariant(before: dict[str, str],
                             after: dict[str, str]) -> None:
    if before != after:
        changed = sorted(set(before.items()) ^ set(after.items()))
        raise ProtocolError(
            f"primary lineage changed across pseudo-run execution: "
            f"{changed[:6]} — the registered primary dataset must be "
            f"bit-identical before and after any number of pseudo-runs")
