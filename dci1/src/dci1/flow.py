"""The Addendum-A evidence flow over one StudyTree.

    prompts  →  cache (append-only, sealed)  →  replication
             →  selection (primary / pseudo-runs)
             →  derived Parquet tables (accepted / scored / analysis)
             →  masking (v2 §19 permutation; addendum custody)

The scientific content — prompts, seeds, verifiers, estimators, claim rules —
is exactly the main implementation's; this module only routes it through the
addendum storage invariants.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dci1.design.blocks import Block
from dci1.evidence import provenance as prov
from dci1.evidence.layout import StudyTree
from dci1.evidence.sealing import (
    CacheWriter,
    StageLock,
    assert_replicated,
    assert_stage_unsealed,
    is_sealed,
    replicate_raw_layers,
    seal_stage,
)
from dci1.evidence.store import append_run_record, atomic_write, write_json
from dci1.generation.pools import Cell, backend_config_hash
from dci1.models.adapters import ModelSpec, backend_plan
from dci1.protocol.constants import ProtocolError, StudyConfig
from dci1.protocol.hashing import sha_text
from dci1.protocol.seeds import generation_seed, resampling_seed, select_pool_index
from dci1.tables.build import (
    build_accepted,
    build_analysis,
    build_scored,
    response_lookup,
    write_parquet,
)


# ------------------------------------------------------------------- prompts
def write_prompts(tree: StudyTree, cells: list[Cell]) -> None:
    if (tree.prompts_dir / "cells.jsonl").exists():
        return
    with StageLock(tree, "prompts"):
        assert_stage_unsealed(tree.prompts_dir)
        rows = [{"block_id": c.block_id, "arm": c.arm, "prompt": c.prompt,
                 "prompt_hash": c.prompt_sha} for c in cells]
        atomic_write(tree.prompts_dir / "cells.jsonl",
                     "".join(json.dumps(r, sort_keys=True) + "\n"
                             for r in rows))
        seal_stage(tree, "prompts")


# --------------------------------------------------------------------- cache
def generate_cache(tree: StudyTree, spec: ModelSpec, cells: list[Cell], *,
                   stream: str, config: StudyConfig, model_dir: Path,
                   device: int = 0, chunk_size: int = 32,
                   max_repair_rounds: int = 3) -> dict[str, Any]:
    """Fill the append-only cache to exactly M members per cell; validate;
    seal; replicate the raw layers (R10–R12, R25)."""
    from dci1.generation.backend import run_backend
    from dci1.generation.pools import expected_pool_size

    writer = CacheWriter(tree.cache_file)
    plan = backend_plan(
        spec, decoding="greedy" if stream == "greedy" else "stochastic",
        chunk_size=chunk_size)
    config_hash = backend_config_hash(plan)
    m = expected_pool_size(stream, config)
    required: dict[str, tuple[Cell, int]] = {}
    for cell in cells:
        for index in range(m):
            rid = (f"{spec.model_key}:{stream}:{cell.block_id}:"
                   f"{cell.arm}:{index}")
            required[rid] = (cell, index)

    with StageLock(tree, "cache"):
        rounds = 0
        while True:
            have = writer.existing_ids()
            missing = {rid: pair for rid, pair in required.items()
                       if rid not in have}
            if not missing:
                break
            if rounds > max_repair_rounds:
                write_json(tree.integrity_dir / "integrity_failure.json",
                           {"status": "INCOMPLETE_POOL",
                            "missing_count": len(missing)})
                raise ProtocolError(
                    f"cache construction failed closed: {len(missing)} "
                    f"members missing after {rounds} rounds")
            design_rows = []
            for rid, (cell, index) in sorted(missing.items()):
                design_rows.append({
                    "row_id": rid, "user_prompt": cell.prompt,
                    "scientific_seed": generation_seed(
                        config.generation_root_seed, stream, spec.model_id,
                        cell.prompt_sha, index),
                    "block_id": cell.block_id, "arm": cell.arm,
                    "pool_index": index, "prompt_hash": cell.prompt_sha,
                    "stream": stream})
            outcome = run_backend(
                tree.cache_dir / "backend_runs" / f"round{rounds}",
                plan, design_rows, device=device)
            accepted, failed = [], []
            for row in outcome["rows"]:
                if row.get("outcome") == "OK":
                    raw = row.get("raw_generation", "")
                    accepted.append({
                        "row_id": row["row_id"],
                        "model_key": spec.model_key,
                        "model_id": spec.model_id,
                        "model_revision": spec.revision,
                        "stream": stream,
                        "block_id": row["block_id"], "arm": row["arm"],
                        "prompt_hash": row["prompt_hash"],
                        "pool_index": int(row["pool_index"]),
                        "generation_seed": int(row.get("seed_reasoning", 0)),
                        "raw_response": raw,
                        "final_answer": row.get("final_answer", ""),
                        "response_content_hash": sha_text(raw),
                        "token_count": int(
                            row.get("total_generated_tokens", 0)),
                        "finish_reason": row.get("finish_reason", ""),
                        "backend_config_hash": config_hash,
                    })
                else:
                    failed.append({"row_id": row.get("row_id"),
                                   "outcome": row.get("outcome")})
            if accepted:
                writer.append(accepted)
            if failed:
                write_json(tree.integrity_dir / f"failures_round{rounds}.json",
                           {"failed": failed})
            append_run_record(model_dir, {
                "event": "cache_generation_round", "tree": str(tree.root),
                "round": rounds, "requested": len(design_rows),
                "accepted": len(accepted), "failed": len(failed)})
            rounds += 1

        report = validate_cache(tree, spec, cells, stream=stream,
                                config=config)
        if not is_sealed(tree.cache_dir):
            seal_stage(tree, "cache")
    replicate_raw_layers(tree)
    write_json(tree.integrity_dir / "cache_report.json", report)
    return report


def validate_cache(tree: StudyTree, spec: ModelSpec, cells: list[Cell], *,
                   stream: str, config: StudyConfig) -> dict[str, Any]:
    """The §8.3 pool checks over the addendum cache."""
    from dci1.generation.pools import expected_pool_size

    writer = CacheWriter(tree.cache_file)
    writer.verify_hashes()
    pools = group_complete_pools(writer.rows(), spec, cells, stream=stream,
                                 config=config)
    seeds: dict[int, str] = {}
    identical = 0
    for (block_id, arm), members in pools.items():
        cell = next(c for c in cells if c.block_id == block_id
                    and c.arm == arm)
        hashes: dict[str, int] = {}
        for index, row in members.items():
            expected = generation_seed(config.generation_root_seed, stream,
                                       spec.model_id, cell.prompt_sha, index)
            if int(row["generation_seed"]) != expected:
                raise ProtocolError(f"{row['row_id']}: seed differs from "
                                    f"derivation")
            if sha_text(row["raw_response"]) != row["response_content_hash"]:
                raise ProtocolError(f"{row['row_id']}: response fails hash")
            seed = int(row["generation_seed"])
            if seed in seeds:
                raise ProtocolError(f"seed shared by {seeds[seed]} and "
                                    f"{row['row_id']}")
            seeds[seed] = row["row_id"]
            hashes[row["response_content_hash"]] = \
                hashes.get(row["response_content_hash"], 0) + 1
        identical += sum(c - 1 for c in hashes.values() if c > 1)
    total = sum(len(m) for m in pools.values())
    return {"status": "COMPLETE", "cells": len(cells), "members": total,
            "pool_size": expected_pool_size(stream, config),
            "distinct_seeds": len(seeds),
            "identical_outputs_within_pools": identical}


def group_complete_pools(rows: list[dict[str, Any]], spec: ModelSpec,
                         cells: list[Cell], *, stream: str,
                         config: StudyConfig
                         ) -> dict[tuple[str, str], dict[int, dict]]:
    from dci1.generation.pools import expected_pool_size

    m = expected_pool_size(stream, config)
    by_cell: dict[tuple[str, str], dict[int, dict]] = {}
    for row in rows:
        if row.get("model_id") != spec.model_id or \
                row.get("model_revision") != spec.revision:
            raise ProtocolError(f"{row.get('row_id')}: model identity "
                                f"mismatch")
        members = by_cell.setdefault((row["block_id"], row["arm"]), {})
        if int(row["pool_index"]) in members:
            raise ProtocolError(f"duplicate pool identity "
                                f"{row.get('row_id')}")
        members[int(row["pool_index"])] = row
    incomplete = [
        (c.block_id, c.arm) for c in cells
        if set(by_cell.get((c.block_id, c.arm), {})) != set(range(m))]
    if incomplete:
        raise ProtocolError(
            f"incomplete pools for {len(incomplete)} cell(s); selection is "
            f"blocked (first: {incomplete[0]})")
    return {(c.block_id, c.arm): by_cell[(c.block_id, c.arm)]
            for c in cells}


# ----------------------------------------------------------------- selection
def select_primary(tree: StudyTree, spec: ModelSpec, cells: list[Cell], *,
                   stream: str, config: StudyConfig,
                   require_replication: bool = True) -> list[dict[str, Any]]:
    if require_replication:
        assert_replicated(tree, "prompts", "cache")
    pools = group_complete_pools(CacheWriter(tree.cache_file).rows(), spec,
                                 cells, stream=stream, config=config)
    rows = []
    for cell in cells:
        member = pools[(cell.block_id, cell.arm)][0]
        rows.append({
            "pseudo_run_id": "primary", "model_id": spec.model_id,
            "block_id": cell.block_id, "arm": cell.arm,
            "selected_pool_index": 0,
            "selected_response_hash": member["response_content_hash"],
            "cache_record_id": member["row_id"],
            "resampling_seed": None,
            "selection_rule": config.primary_selection_rule})
    text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    path = tree.primary_selection
    if path.exists():
        if path.read_text() != text:
            raise ProtocolError(f"{path}: rebuild diverges — the primary "
                                f"selection is immutable")
    else:
        with StageLock(tree, "selection"):
            assert_stage_unsealed(tree.selection_dir)
            atomic_write(path, text)
        replicate_raw_layers(tree)
    return rows


def select_pseudo(tree: StudyTree, spec: ModelSpec, cells: list[Cell], *,
                  stream: str, config: StudyConfig,
                  run_index: int) -> list[dict[str, Any]]:
    if stream != "confirmatory" and tree.freeze_id != "prefreeze-pilot":
        raise ProtocolError("pseudo-runs are registered for the confirmatory "
                            "stage only")
    if not 0 <= run_index < config.pseudo_run_count:
        raise ProtocolError("pseudo_run_index outside the frozen count")
    assert_replicated(tree, "prompts", "cache")
    pools = group_complete_pools(CacheWriter(tree.cache_file).rows(), spec,
                                 cells, stream=stream, config=config)
    seed_r = resampling_seed(config.resampling_root_seed, spec.model_id,
                             run_index)
    rows = []
    for cell in cells:
        index = select_pool_index(seed_r, cell.block_id, cell.arm,
                                  config.generation_pool_size)
        member = pools[(cell.block_id, cell.arm)][index]
        rows.append({
            "pseudo_run_id": f"pseudo_{run_index:04d}",
            "model_id": spec.model_id,
            "block_id": cell.block_id, "arm": cell.arm,
            "selected_pool_index": index,
            "selected_response_hash": member["response_content_hash"],
            "cache_record_id": member["row_id"],
            "resampling_seed": seed_r})
    atomic_write(tree.pseudo_selection(run_index),
                 "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    return rows


# ------------------------------------------------------------ derived tables
def _created_at(tree: StudyTree) -> str:
    """Input-derived timestamp for byte-identical regeneration (R26)."""
    seal = tree.cache_dir / "_SEALED"
    if seal.exists():
        return json.loads(seal.read_text())["sealed_at_utc"]
    return "1970-01-01T00:00:00Z"


def wide_rows(tree: StudyTree, spec: ModelSpec,
              selection_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Accepted rows WITH response text, in memory only (the Parquet
    accepted table never duplicates text, R29)."""
    cache = response_lookup(tree)
    rows = []
    for sel in selection_rows:
        member = cache[sel["cache_record_id"]]
        rows.append({
            "row_id": f"{spec.model_key}:{sel['block_id']}:{sel['arm']}",
            "model_key": spec.model_key, "model_id": spec.model_id,
            "model_revision": spec.revision,
            "block_id": sel["block_id"], "arm": sel["arm"],
            "prompt_hash": member["prompt_hash"],
            "pool_index": int(member["pool_index"]),
            "generation_seed": int(member["generation_seed"]),
            "response": member["raw_response"],
            "response_content_hash": member["response_content_hash"],
            "token_count": int(member["token_count"]),
            "finish_reason": member["finish_reason"],
            "backend_config_hash": member["backend_config_hash"],
        })
    return rows


def derive_primary(tree: StudyTree, spec: ModelSpec, blocks: list[Block],
                   cells: list[Cell], *, stream: str, config: StudyConfig,
                   n: int, m: int, references: tuple[str, str, str],
                   freeze_record_hash: str, bootstrap_seed_value: int,
                   analysis_stage: str, environment_record: dict[str, Any],
                   n_resamples: int = 10_000, allow_dirty: bool = False,
                   drill_rebuild: bool = False) -> dict[str, Any]:
    """Accepted + scored Parquet from the primary selection, plus the
    analysis Parquet for one stage. The masked-stage analysis is written into
    the masking lineage (it depends on the mask key); ``derived/`` holds only
    artifacts reproducible from the raw layers alone (R26).
    ``drill_rebuild`` bypasses only the unmasking-status gate, for the
    byte-identity restore drill — never for a registered emission."""
    from dci1.analysis.run import analyze
    from dci1.analysis.tables import score_table

    if not drill_rebuild:
        assert_replicated(tree, "prompts", "cache", "selection")
    writer = prov.require_registered_writer(allow_dirty=allow_dirty)
    prov.require_freeze_consistency(tree, freeze_record_hash)
    if not drill_rebuild:
        prov.require_stage_consistent_with_unmasking(tree, analysis_stage)
    created = _created_at(tree)
    selection_rows = select_primary(tree, spec, cells, stream=stream,
                                    config=config,
                                    require_replication=not drill_rebuild)
    cache = response_lookup(tree)
    accepted_rows = build_accepted(
        tree, spec=spec, blocks=blocks, selection_rows=selection_rows,
        cache_by_id=cache, freeze_record_hash=freeze_record_hash,
        created_at=created, writer=writer)
    accepted_path = write_parquet(
        tree.derived_primary / "accepted.parquet", "accepted", accepted_rows,
        expect_rows=len(blocks) * 6, forbid_nulls=True)

    wide = wide_rows(tree, spec, selection_rows)
    scored_wide = score_table(wide, blocks, n=n, m=m, references=references)
    accepted_by_cell = {(r["block_id"], r["arm"]): r for r in accepted_rows}
    scored_rows = build_scored(
        tree, spec=spec, scored_wide=scored_wide,
        accepted_by_cell=accepted_by_cell, references=references,
        freeze_record_hash=freeze_record_hash, created_at=created,
        writer=writer)
    scored_path = write_parquet(
        tree.derived_primary / "scored.parquet", "scored", scored_rows)

    if analysis_stage == "masked":
        analysis_input = _masked_wide(tree, spec)
    else:
        analysis_input = wide
    result = analyze(analysis_input, blocks, n=n, m=m,
                     references=references,
                     bootstrap_seed_value=bootstrap_seed_value,
                     n_resamples=n_resamples,
                     masked=analysis_stage == "masked")
    if result["status"] != "OK":
        raise ProtocolError(f"analysis failed closed: {result['status']} "
                            f"({result.get('detail')})")
    provenance = prov.analysis_provenance(
        tree, analysis_command=f"dci1 derive --stage {analysis_stage}",
        masking_state=analysis_stage,
        environment_record=environment_record,
        resampling_root_seed=config.resampling_root_seed)
    analysis_rows = build_analysis(
        tree, spec=spec, result=result, provenance=provenance,
        freeze_record_hash=freeze_record_hash, created_at=created,
        writer=writer, analysis_stage=analysis_stage,
        n_blocks_by_scope=_scopes(blocks),
        input_accepted_hash=sha_text(
            accepted_path.read_bytes().hex()),
        input_scored_hash=sha_text(scored_path.read_bytes().hex()))
    if analysis_stage == "masked":
        analysis_path = write_parquet(
            tree.masked_view / "analysis_masked.parquet", "analysis",
            analysis_rows)
    else:
        analysis_path = write_parquet(
            tree.derived_primary / "analysis.parquet", "analysis",
            analysis_rows)
    return {"accepted": str(accepted_path), "scored": str(scored_path),
            "analysis": str(analysis_path), "result_status": result["status"],
            "result": result}


def _scopes(blocks: list[Block]) -> dict[str, int]:
    from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST

    return {"all": len(blocks),
            TARGET_FIRST: sum(1 for b in blocks if b.order == TARGET_FIRST),
            ADDED_FIRST: sum(1 for b in blocks if b.order == ADDED_FIRST)}


# ------------------------------------------------------------------- masking
#: Columns removed from the masked view (R38; response text retained per v2).
MASKED_VIEW_EXCLUDED = ("prompt_hash", "row_id", "generation_seed",
                        "backend_config_hash")


def construct_masked_view(tree: StudyTree, spec: ModelSpec,
                          cells: list[Cell], *, stream: str,
                          config: StudyConfig,
                          model_dir: Path) -> dict[str, Any]:
    """v2 §19 mask over the primary selection, under addendum custody."""
    from dci1.masking.custody import write_mask_key_sealed
    from dci1.masking.mask import build_permutations

    selection_rows = select_primary(tree, spec, cells, stream=stream,
                                    config=config)
    wide = wide_rows(tree, spec, selection_rows)
    permutations, changed = build_permutations(
        sorted({r["block_id"] for r in wide}))
    if changed < len(permutations) / 2:
        raise ProtocolError("mask permutations differ in fewer than half of "
                            "the blocks (§19 check 1)")
    key_hash = write_mask_key_sealed(tree, permutations)
    masked = []
    for row in wide:
        out = {k: v for k, v in row.items()
               if k not in MASKED_VIEW_EXCLUDED}
        mapping = permutations[row["block_id"]]
        if row["arm"] in mapping:
            out["arm"] = mapping[row["arm"]]
        masked.append(out)
    atomic_write(tree.masked_view / "masked_rows.jsonl",
                 "".join(json.dumps(r, sort_keys=True) + "\n"
                         for r in masked))
    from dci1.evidence.sealing import write_study_manifest

    append_run_record(model_dir, {
        "event": "mask_constructed", "tree": str(tree.root),
        "mask_key_hash": key_hash,
        "blocks_with_changed_labels": changed,
        "blocks": len(permutations)})
    write_study_manifest(tree, None, extra={"mask_key_hash": key_hash})
    return {"mask_key_hash": key_hash, "blocks": len(permutations),
            "changed": changed}


def _masked_wide(tree: StudyTree, spec: ModelSpec) -> list[dict[str, Any]]:
    path = tree.masked_view / "masked_rows.jsonl"
    if not path.exists():
        raise ProtocolError("no masked view; construct the mask first (§19)")
    rows = [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]
    # score_table needs these provenance fields; they are design/apparatus
    # facts, not outcome-bearing.
    for row in rows:
        row.setdefault("pool_index", 0)
    return rows
