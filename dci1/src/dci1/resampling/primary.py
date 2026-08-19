"""The registered primary realised dataset (amendment §2.7).

The primary selection rule is ``primary_pool_index = 0`` for every cell (D02):
fixed before any generation, identical across all four models, never revisited
after outcomes exist. The build reads ONLY complete pools, writes ONLY into
the ``primary/`` lineage, and is idempotent: a rebuild must reproduce the
existing artifacts byte-identically, and any divergence fails closed —
the primary dataset can never be silently replaced.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dci1.generation.pools import Cell
from dci1.generation.validation import load_complete_pools
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import PRIMARY_SELECTION_RULE, ProtocolError, StudyConfig

PRIMARY_POOL_INDEX = 0


def primary_dir(stage_dir: Path) -> Path:
    return Path(stage_dir) / "primary"


def build_primary(spec: ModelSpec, cells: list[Cell], *, stream: str,
                  stage_dir: Path, config: StudyConfig) -> dict[str, Any]:
    """Build (or verify) the primary-selection manifest and accepted table."""
    if config.primary_selection_rule != PRIMARY_SELECTION_RULE:
        raise ProtocolError(
            f"frozen primary_selection_rule "
            f"{config.primary_selection_rule!r} does not match the "
            f"registered rule {PRIMARY_SELECTION_RULE!r}")
    pools = load_complete_pools(spec, cells, stream=stream,
                                stage_dir=stage_dir, config=config)

    manifest_rows, accepted_rows = [], []
    for cell in cells:
        member = pools[(cell.block_id, cell.arm)][PRIMARY_POOL_INDEX]
        manifest_rows.append({
            "pseudo_run_id": "primary",
            "model_id": spec.model_id,
            "block_id": cell.block_id,
            "arm": cell.arm,
            "selected_pool_index": PRIMARY_POOL_INDEX,
            "selected_response_hash": member["response_content_hash"],
            "resampling_seed": None,
            "selection_rule": PRIMARY_SELECTION_RULE,
        })
        accepted_rows.append(_accepted_row(spec, cell, member))

    out = primary_dir(stage_dir)
    manifest_path = out / "primary_manifest.jsonl"
    accepted_path = out / "accepted.jsonl"
    manifest_text = "".join(json.dumps(r, sort_keys=True) + "\n"
                            for r in manifest_rows)
    accepted_text = "".join(json.dumps(r, sort_keys=True) + "\n"
                            for r in accepted_rows)
    for path, text in ((manifest_path, manifest_text),
                       (accepted_path, accepted_text)):
        if path.exists():
            if path.read_text() != text:
                raise ProtocolError(
                    f"{path}: rebuild diverges from the existing primary "
                    f"artifact — the registered primary dataset is immutable "
                    f"and is never replaced")
        else:
            from dci1.evidence.store import atomic_write

            atomic_write(path, text)
    return {"cells": len(cells), "manifest": str(manifest_path),
            "accepted": str(accepted_path)}


def _accepted_row(spec: ModelSpec, cell: Cell,
                  member: dict[str, Any]) -> dict[str, Any]:
    """One accepted observation for one (model, block, arm) cell (§2.9)."""
    return {
        "row_id": f"{spec.model_key}:{cell.block_id}:{cell.arm}",
        "model_key": spec.model_key,
        "model_id": spec.model_id,
        "model_revision": spec.revision,
        "block_id": cell.block_id,
        "arm": cell.arm,
        "prompt_hash": cell.prompt_sha,
        "pool_index": int(member["pool_index"]),
        "generation_seed": int(member["generation_seed"]),
        "response": member["raw_response"],
        "response_content_hash": member["response_content_hash"],
        "token_count": int(member["token_count"]),
        "finish_reason": member["finish_reason"],
        "backend_config_hash": member["backend_config_hash"],
    }


def load_accepted(stage_dir: Path) -> list[dict[str, Any]]:
    path = primary_dir(stage_dir) / "accepted.jsonl"
    if not path.exists():
        raise ProtocolError(f"no primary accepted table at {path}")
    return [json.loads(line) for line in path.read_text().splitlines() if line]
