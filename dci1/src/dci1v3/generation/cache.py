"""Cached-draw generation (§4, §27 item 56, item 39).

Every cell has predetermined cached-draw identities ``cell_id:draw`` with
predetermined seeds; a missing draw is repaired only by regenerating that
exact identity with its exact seed. Pool shrinking, replacement seeds, and
averaging around missing cells are structurally impossible: the writer
refuses duplicates and validation requires the exact draw matrix.

Each committed row carries every field of implementation-prompt item 56,
including every verifier verdict with the frozen instrument hash.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1v3.engine import fs
from dci1v3.engine.store import CacheWriter
from dci1v3.errors import IntegrityError, ProtocolError
from dci1v3.generation.backend import GenerateFn
from dci1v3.generation.prompts import Cell
from dci1v3.protocol.hashing import sha_text
from dci1v3.protocol.seeds import generation_seed
from dci1v3.verifiers import verifier_source_hash
from dci1v3.verifiers.families import added_verifier
from dci1v3.verifiers.target import (
    s0_count,
    s1_count,
    s2_count,
    s3_count,
)


def _verdicts(cell: Cell, text: str) -> dict[str, Any]:
    verdicts: dict[str, Any] = {
        "s0": s0_count(text), "s1": s1_count(text), "s2": s2_count(text),
        "s3": s3_count(text, cell.active_wordings),
        "verifier_source_hash": verifier_source_hash(),
    }
    if cell.n is not None:
        verdicts["target_pass"] = verdicts["s0"] == cell.n
    if cell.constraint_id is not None and cell.severity is not None:
        verdicts["added_pass"] = added_verifier(
            cell.constraint_id, cell.severity)(text)
    return verdicts


def fill_cache(stage_dir: Path, cells: list[Cell], *, spec, stage: str,
               generation_root: int, plan: dict[str, Any],
               generate_fn: GenerateFn, environment: dict[str, Any],
               max_repair_rounds: int = 3) -> dict[str, Any]:
    """Fill the append-only cache to exactly ``cell.draws`` members per
    cell; validate; fail closed on exhausted repairs."""
    stage_dir = Path(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)
    writer = CacheWriter(stage_dir / "cache.jsonl")

    required: dict[str, tuple[Cell, int]] = {}
    for cell in cells:
        for index in range(cell.draws):
            required[f"{cell.cell_id}:{index}"] = (cell, index)

    rounds = 0
    provenance: dict[str, Any] = {}
    while True:
        have = writer.existing_ids()
        missing = {rid: pair for rid, pair in required.items()
                   if rid not in have}
        if not missing:
            break
        if rounds > max_repair_rounds:
            raise IntegrityError(
                f"{stage}: {len(missing)} cached draws missing after "
                f"{rounds} repair rounds; generation fails closed")
        design_rows = []
        for rid, (cell, index) in sorted(missing.items()):
            design_rows.append({
                "row_id": rid, "user_prompt": cell.prompt,
                "scientific_seed": generation_seed(
                    generation_root, stage, spec.model_id,
                    cell.prompt_hash, index),
                "prompt_hash": cell.prompt_hash, "cell_id": cell.cell_id,
                "draw_index": index})
        outcome = generate_fn(stage_dir / "backend_runs" / f"round{rounds}",
                              plan, design_rows)
        provenance = outcome.get("provenance", provenance)
        accepted = []
        for row in outcome["rows"]:
            if row.get("outcome") != "OK":
                continue
            cell, index = required[row["row_id"]]
            raw = row.get("raw_generation", "")
            accepted.append({
                "row_id": row["row_id"],
                "stage": stage,
                "artifact_state": "committed",
                "model_key": spec.model_key,
                "model_id": spec.model_id,
                "model_revision": spec.revision,
                "cell_id": cell.cell_id,
                "topic_id": cell.topic_id,
                "block_id": cell.block_id,
                "arm": cell.arm,
                "kind": cell.kind,
                "draw_index": index,
                "order": cell.order,
                "target_wording": cell.target_wording,
                "added_wording": cell.added_wording,
                "n": cell.n,
                "constraint_id": cell.constraint_id,
                "severity": cell.severity,
                "prompt_hash": cell.prompt_hash,
                "backend_version": provenance.get("vllm_version",
                                                  provenance.get("backend",
                                                                 "unknown")),
                "interpreter": environment.get("python_executable"),
                "dependency_digest": environment.get("dependency_digest"),
                "hardware_class": provenance.get("gpu_name", "unknown"),
                "seed": int(row.get("seed_reasoning",
                                    row.get("scientific_seed", 0))),
                "raw_response": raw,
                "response_content_hash": sha_text(raw),
                "prompt_tokens": int(row.get("prompt_tokens", 0)),
                "token_count": int(row.get("total_generated_tokens", 0)),
                "finish_reason": row.get("finish_reason", ""),
                "verdicts": _verdicts(cell, raw),
            })
        if accepted:
            writer.append(accepted)
        rounds += 1

    report = validate_cache(stage_dir, cells, spec=spec, stage=stage,
                            generation_root=generation_root)
    fs.write_json(stage_dir / "cache_report.json", report)
    return {**report, "provenance": provenance}


def validate_cache(stage_dir: Path, cells: list[Cell], *, spec, stage: str,
                   generation_root: int) -> dict[str, Any]:
    """The exact draw matrix, seed derivations, and content hashes."""
    writer = CacheWriter(Path(stage_dir) / "cache.jsonl")
    rows = writer.rows()
    by_cell: dict[str, dict[int, dict]] = {}
    seeds: dict[int, str] = {}
    for row in rows:
        if row["model_id"] != spec.model_id or \
                row["model_revision"] != spec.revision:
            raise IntegrityError(f"{row['row_id']}: model identity mismatch")
        members = by_cell.setdefault(row["cell_id"], {})
        if row["draw_index"] in members:
            raise IntegrityError(f"duplicate cached-draw identity "
                                 f"{row['row_id']}")
        members[row["draw_index"]] = row
        expected_seed = generation_seed(generation_root, stage,
                                        spec.model_id, row["prompt_hash"],
                                        row["draw_index"])
        if int(row["seed"]) != expected_seed:
            raise IntegrityError(f"{row['row_id']}: seed differs from the "
                                 f"frozen derivation")
        if row["seed"] in seeds:
            raise IntegrityError(f"seed shared by {seeds[row['seed']]} and "
                                 f"{row['row_id']}")
        seeds[row["seed"]] = row["row_id"]
        if sha_text(row["raw_response"]) != row["response_content_hash"]:
            raise IntegrityError(f"{row['row_id']}: response fails its "
                                 f"content hash")
    incomplete = [c.cell_id for c in cells
                  if set(by_cell.get(c.cell_id, {})) != set(range(c.draws))]
    if incomplete:
        raise IntegrityError(f"incomplete draw matrix for "
                             f"{len(incomplete)} cell(s), first: "
                             f"{incomplete[0]}")
    extras = set(by_cell) - {c.cell_id for c in cells}
    if extras:
        raise IntegrityError(f"cache contains cells outside the plan: "
                             f"{sorted(extras)[:3]}")
    return {"status": "COMPLETE", "cells": len(cells), "draws": len(rows)}


def cache_rows(stage_dir: Path) -> list[dict[str, Any]]:
    return CacheWriter(Path(stage_dir) / "cache.jsonl").rows()


def rows_by_cell(rows: list[dict[str, Any]]
                 ) -> dict[str, dict[int, dict[str, Any]]]:
    grouped: dict[str, dict[int, dict[str, Any]]] = {}
    for row in rows:
        members = grouped.setdefault(row["cell_id"], {})
        if row["draw_index"] in members:
            raise ProtocolError(f"duplicate draw {row['row_id']}")
        members[row["draw_index"]] = row
    return grouped
