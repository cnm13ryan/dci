"""Builders and readers for the registered Parquet tables (Addendum A §3).

Accepted rows never duplicate raw response text; the text is retrieved from
the immutable cache via ``cache_record_id`` (R29). Scored rows are long
format: one row per accepted observation per verifier (R30). Analysis rows
serialise the §20 result with full provenance (§5).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from dci1.evidence.layout import StudyTree
from dci1.evidence.sealing import artifact_header
from dci1.protocol.constants import (
    ARMS,
    PRIMARY_ARMS,
    SMALLEST_EFFECT_OF_INTEREST,
    ProtocolError,
)
from dci1.tables.schemas import SCHEMA_VERSIONS, arrow_schema, validate_table
from dci1.verifiers.registry import verifier_source_hash

ESTIMATOR_ID = "block-mean-contrast-v1"


def write_parquet(path: Path, name: str, rows: list[dict[str, Any]], *,
                  expect_rows: int | None = None,
                  forbid_nulls: bool = False) -> Path:
    """Deterministic Parquet write: fixed schema/column order, PK-sorted rows,
    schema metadata, temp file + fsync + atomic rename (R09)."""
    from dci1.tables.schemas import PRIMARY_KEYS

    schema = arrow_schema(name).with_metadata(
        {"schema_name": name, "schema_version": SCHEMA_VERSIONS[name],
         "addendum_version": "A-1.0"})
    rows = sorted(rows, key=lambda r: tuple(r[k] for k in PRIMARY_KEYS[name]))
    arrays = {field.name: [row[field.name] for row in rows]
              for field in schema}
    table = pa.Table.from_pydict(arrays, schema=schema)
    validate_table(name, table, expect_rows=expect_rows,
                   forbid_nulls=forbid_nulls)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    os.close(fd)
    try:
        pq.write_table(table, tmp)
        with open(tmp, "rb") as handle:
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path


def read_table(path: Path, name: str) -> pa.Table:
    """Read with schema-name/version validation before use (R21)."""
    table = pq.read_table(path)
    validate_table(name, table)
    return table


def response_lookup(tree: StudyTree) -> dict[str, dict[str, Any]]:
    """cache_record_id → cache record (the only source of response text)."""
    from dci1.evidence.sealing import CacheWriter

    return {r["row_id"]: r for r in CacheWriter(tree.cache_file).rows()}


def build_accepted(tree: StudyTree, *, spec, blocks, selection_rows,
                   cache_by_id, freeze_record_hash: str, created_at: str,
                   writer: dict[str, Any], selection_source: str = "primary",
                   pseudo_run_id: str = "primary") -> list[dict[str, Any]]:
    """Accepted rows (no response text) from a selection manifest + cache."""
    block_by_id = {b.block_id: b for b in blocks}
    rows = []
    for sel in selection_rows:
        block = block_by_id[sel["block_id"]]
        member = cache_by_id[sel["cache_record_id"]] \
            if "cache_record_id" in sel else cache_by_id[
                f"{spec.model_key}:{sel['stream']}:{sel['block_id']}:"
                f"{sel['arm']}:{sel['selected_pool_index']}"]
        header = artifact_header(
            tree, model_id=spec.model_id, schema_name="accepted",
            schema_version=SCHEMA_VERSIONS["accepted"],
            freeze_record_hash=freeze_record_hash, writer=writer)
        header["created_at_utc"] = created_at
        rows.append({
            **header,
            "model_revision": spec.revision,
            "block_id": block.block_id,
            "topic_id": block.topic_id,
            "stratum_id": block.topic_id.rsplit("-", 1)[0],
            "arm": sel["arm"],
            "presentation_order": block.order,
            "wording_id": f"t{block.wording_target}a{block.wording_added}",
            "prompt_hash": member["prompt_hash"],
            "selection_source": selection_source,
            "pseudo_run_id": pseudo_run_id,
            "selected_pool_index": int(member["pool_index"]),
            "response_content_hash": member["response_content_hash"],
            "cache_record_id": member["row_id"],
            "token_count": int(member["token_count"]),
            "finish_reason": member["finish_reason"],
            "generation_seed": int(member["generation_seed"]),
            "resampling_seed": int(sel.get("resampling_seed") or -1),
        })
    return rows


def build_scored(tree: StudyTree, *, spec, scored_wide: list[dict[str, Any]],
                 accepted_by_cell: dict[tuple[str, str], dict[str, Any]],
                 references: tuple[str, str, str],
                 freeze_record_hash: str, created_at: str,
                 writer: dict[str, Any]) -> list[dict[str, Any]]:
    """Long-format scored rows from the wide §9 scoring output (R30).

    verifier_id ∈ {target_s0..target_s3, added}; the added-constraint row's
    ``scoring_rule`` is the codebook-registered value "ADDED" and its uptake
    verdict also fills ``manipulation_check_value``.
    """
    from dci1.design.prompts import added_constraint_id

    v_hash = verifier_source_hash()
    rows = []
    for wide in scored_wide:
        cell = (wide["block_id"], wide["arm"])
        accepted = accepted_by_cell[cell]
        header = artifact_header(
            tree, model_id=spec.model_id, schema_name="scored",
            schema_version=SCHEMA_VERSIONS["scored"],
            freeze_record_hash=freeze_record_hash, writer=writer)
        header["created_at_utc"] = created_at
        base = {
            **header,
            "block_id": wide["block_id"], "arm": wide["arm"],
            "response_content_hash": wide["response_content_hash"],
            "verifier_version": "1.0.0",
            "verifier_source_hash": v_hash,
            "wording_id": f"t{wide['wording_target']}a{wide['wording_added']}",
            "parse_status": "ok",
            "compliance_flag": bool(wide["short_flag"] or wide["truncated"]
                                    or wide["empty"]),
            "failure_taxonomy_code": wide["failure_category"] or "",
            "cache_record_id": accepted["cache_record_id"],
        }
        for k in range(4):
            rows.append({
                **base,
                "verifier_id": f"target_s{k}",
                "constraint_id": "A", "constraint_role": "target",
                "verdict": wide[f"f_s{k}"] == 0,
                "verdict_reason_code": "" if wide[f"f_s{k}"] == 0
                                       else "count_mismatch",
                "scoring_rule": f"S{k}",
                "score_value": float(wide[f"s{k}_count"]),
                "manipulation_check_value": float("nan"),
            })
        if wide["arm"] in PRIMARY_ARMS:
            added_id = added_constraint_id(wide["arm"], references)
            rows.append({
                **base,
                "verifier_id": "added",
                "constraint_id": added_id, "constraint_role": "added",
                "verdict": wide["uptake"] == 1,
                "verdict_reason_code": "" if wide["uptake"] == 1
                                       else "constraint_violated",
                "scoring_rule": "ADDED",
                "score_value": float(wide["uptake"]),
                "manipulation_check_value": float(wide["uptake"]),
            })
    return rows


def build_analysis(tree: StudyTree, *, spec, result: dict[str, Any],
                   provenance: dict[str, Any], freeze_record_hash: str,
                   created_at: str, writer: dict[str, Any],
                   analysis_stage: str, n_blocks_by_scope: dict[str, int],
                   input_accepted_hash: str,
                   input_scored_hash: str) -> list[dict[str, Any]]:
    """Analysis rows from the §20 result dict, with §5 provenance columns.

    Every estimand row enforces ``n_observations == n_blocks × 6`` over its
    scope (R33; full-design scope = all blocks, per-order scope = that
    stratum's blocks).
    """
    if analysis_stage not in ("masked", "final", "sensitivity"):
        raise ProtocolError(f"unknown analysis_stage {analysis_stage!r}")
    header = artifact_header(
        tree, model_id=spec.model_id, schema_name="analysis",
        schema_version=SCHEMA_VERSIONS["analysis"],
        freeze_record_hash=freeze_record_hash, writer=writer)
    header["created_at_utc"] = created_at
    shared = {
        **header,
        "model_revision": spec.revision,
        "estimator_id": ESTIMATOR_ID,
        "ci_method": "block_bootstrap",
        "n_bootstrap": int(result["bootstrap"]["resamples"]),
        "bootstrap_seed": int(result["bootstrap"]["seed"]),
        "analysis_stage": analysis_stage,
        "masked": bool(result.get("masked")),
        "input_accepted_hash": input_accepted_hash,
        "input_scored_hash": input_scored_hash,
        "protocol_identity": provenance["protocol_identity"],
        "input_manifest_hashes": json.dumps(
            provenance["input_manifest_hashes"], sort_keys=True),
        "resampling_root_seed": int(provenance["resampling_root_seed"]),
        "masking_state": provenance["masking_state"],
        "environment_record_hash": provenance["environment_record_hash"],
        "analysis_command": provenance["analysis_command"],
        "wall_clock_utc": created_at,
    }

    def scope_blocks(member: str) -> int:
        for scope, count in n_blocks_by_scope.items():
            if scope != "all" and scope in member:
                return count
        return n_blocks_by_scope["all"]

    rows = []
    equivalence = {"F1": (-SMALLEST_EFFECT_OF_INTEREST,
                          SMALLEST_EFFECT_OF_INTEREST),
                   "F2": (-0.05, 0.05)}
    outcomes = result.get("outcomes") or {}
    for family_id, family in (result.get("families") or {}).items():
        eq = equivalence.get(family_id, (float("nan"), float("nan")))
        for member, entry in (family.get("members") or {}).items():
            n_blocks = scope_blocks(member)
            simultaneous = entry.get("simultaneous")
            outcome = outcomes.get(member, {})
            rows.append({
                **shared,
                "family_id": family_id,
                "estimand_id": member,
                "contrast_id": member,
                "point_estimate": float(entry.get("estimate", float("nan"))),
                "ci_lower": float(simultaneous[0]) if simultaneous
                            else float("nan"),
                "ci_upper": float(simultaneous[1]) if simultaneous
                            else float("nan"),
                "simultaneous": True,
                "multiplicity_adjustment": "studentised-max-t",
                "equivalence_lower": eq[0], "equivalence_upper": eq[1],
                "smallest_effect_of_interest": SMALLEST_EFFECT_OF_INTEREST,
                "claim_rule_id": ("v2-s15-primary" if family_id == "F1"
                                  else "v2-s15-exchangeability"
                                  if family_id == "F2" else ""),
                "claim_outcome": (outcome.get("terminal", "")
                                  if analysis_stage != "sensitivity" else ""),
                "n_blocks": n_blocks,
                "n_observations": n_blocks * len(ARMS),
            })
    for row in rows:
        if row["n_observations"] != row["n_blocks"] * 6:
            raise ProtocolError("n_observations != n_blocks × 6 (R33)")
    return rows
