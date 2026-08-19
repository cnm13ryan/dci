"""Pool validation and the duplicate diagnostic (amendment §2.4–§2.5, §8.3).

Integrity failures (raise, fail closed):
* a pool with fewer or more than M members for any required cell;
* duplicated row identities;
* two pool members sharing a generation seed;
* a recorded seed differing from its deterministic derivation;
* a stored response failing its content hash;
* a prompt hash outside the stage's frozen cell plan.

Flagged but retained (legitimate model behaviour):
* identical outputs within or across pools — reported, never discarded.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from dci1.evidence.store import AppendOnceJsonl
from dci1.generation.pools import Cell, expected_pool_size, pool_path
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import ProtocolError, StudyConfig
from dci1.protocol.hashing import sha_text
from dci1.protocol.seeds import generation_seed


def load_complete_pools(spec: ModelSpec, cells: list[Cell], *, stream: str,
                        stage_dir: Path, config: StudyConfig,
                        ) -> dict[tuple[str, str], dict[int, dict[str, Any]]]:
    """The pools of a stage, verified complete; raises on any incomplete pool.

    Selection and pseudo-run construction call this and ONLY this — there is
    no code path that samples from a reduced pool (amendment §2.5).
    """
    store = AppendOnceJsonl(pool_path(stage_dir))
    store.verify_hashes()
    rows = store.rows()
    by_cell: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}
    for row in rows:
        key = (row["block_id"], row["arm"])
        members = by_cell.setdefault(key, {})
        index = int(row["pool_index"])
        if index in members:
            raise ProtocolError(
                f"duplicate pool identity {key}[{index}] — two writers")
        members[index] = row

    m = expected_pool_size(stream, config)
    incomplete = []
    for cell in cells:
        members = by_cell.get((cell.block_id, cell.arm), {})
        if set(members) != set(range(m)):
            incomplete.append({"block_id": cell.block_id, "arm": cell.arm,
                               "present": sorted(members), "required": m})
    if incomplete:
        raise ProtocolError(
            f"incomplete pools for {len(incomplete)} cell(s); selection is "
            f"blocked until every pool holds exactly M={m} members. First: "
            f"{incomplete[0]}")
    return {(c.block_id, c.arm): by_cell[(c.block_id, c.arm)] for c in cells}


def validate_pools(spec: ModelSpec, cells: list[Cell], *, stream: str,
                   stage_dir: Path, config: StudyConfig) -> dict[str, Any]:
    """Full §8.3 validation; returns the machine-readable integrity report."""
    pools = load_complete_pools(spec, cells, stream=stream,
                                stage_dir=stage_dir, config=config)
    cell_by_key = {(c.block_id, c.arm): c for c in cells}

    seeds_seen: dict[int, str] = {}
    output_hashes: Counter[str] = Counter()
    identical_within_pool = 0
    for key, members in pools.items():
        cell = cell_by_key[key]
        hashes_here: Counter[str] = Counter()
        for index, row in members.items():
            expected_seed = generation_seed(
                config.generation_root_seed, stream, spec.model_id,
                cell.prompt_sha, index)
            if int(row["generation_seed"]) != expected_seed:
                raise ProtocolError(
                    f"pool member {row['row_id']}: recorded seed "
                    f"{row['generation_seed']} != derived {expected_seed}")
            if row["prompt_hash"] != cell.prompt_sha:
                raise ProtocolError(
                    f"pool member {row['row_id']}: prompt hash outside the "
                    f"frozen cell plan")
            if sha_text(row["raw_response"]) != row["response_content_hash"]:
                raise ProtocolError(
                    f"pool member {row['row_id']}: response fails its "
                    f"content hash — stored evidence was mutated")
            seed = int(row["generation_seed"])
            if seed in seeds_seen:
                raise ProtocolError(
                    f"seed {seed} shared by {seeds_seen[seed]} and "
                    f"{row['row_id']} — pool members are not independent")
            seeds_seen[seed] = row["row_id"]
            if row["model_id"] != spec.model_id or \
                    row["model_revision"] != spec.revision:
                raise ProtocolError(
                    f"pool member {row['row_id']}: model identity mismatch")
            hashes_here[row["response_content_hash"]] += 1
            output_hashes[row["response_content_hash"]] += 1
        identical_within_pool += sum(c - 1 for c in hashes_here.values()
                                     if c > 1)

    total = sum(len(m) for m in pools.values())
    return {
        "status": "COMPLETE",
        "model_key": spec.model_key,
        "stream": stream,
        "cells": len(cells),
        "pool_size": expected_pool_size(stream, config),
        "members": total,
        "distinct_seeds": len(seeds_seen),
        # Diagnostic only: identical outputs may be legitimate behaviour and
        # are retained (amendment §2.4).
        "identical_outputs_within_pools": identical_within_pool,
        "identical_outputs_across_store": sum(
            c - 1 for c in output_hashes.values() if c > 1),
    }
