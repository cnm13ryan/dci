"""Cached-generation pool construction (amendment §2.2–§2.5).

For every registered ``(model, block, arm)`` prompt of a stage, exactly
``M = generation_pool_size`` genuinely independent stochastic generations are
produced, each under its own deterministic seed (level-1 randomness), and
appended once to the immutable pool store. Missing members are
pipeline-integrity failures: they are surfaced in a machine-readable report,
repaired by regenerating ONLY the missing identities under their original
recorded seeds (existing members are never touched), and selection is blocked
until every pool is complete.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dci1.evidence.store import AppendOnceJsonl, append_run_record, write_json
from dci1.generation.backend import run_backend
from dci1.models.adapters import ModelSpec, backend_plan
from dci1.protocol.constants import ProtocolError, StudyConfig
from dci1.protocol.hashing import sha, sha_text
from dci1.protocol.seeds import generation_seed


@dataclass(frozen=True)
class Cell:
    """One registered (block, arm) prompt of a stage."""

    block_id: str
    arm: str
    prompt: str

    @property
    def prompt_sha(self) -> str:
        return sha_text(self.prompt)


def pool_row_id(model_key: str, stream: str, block_id: str, arm: str,
                pool_index: int) -> str:
    return f"{model_key}:{stream}:{block_id}:{arm}:{pool_index}"


#: Plan fields that are execution pacing, not configuration: excluded from the
#: backend configuration hash so a repair round hashes identically.
_NON_CONFIG_FIELDS = ("expected_rows", "chunk_size", "deadline_seconds")


def backend_config_hash(plan: dict[str, Any]) -> str:
    return sha({k: v for k, v in plan.items() if k not in _NON_CONFIG_FIELDS})


def pool_path(stage_dir: Path) -> Path:
    return Path(stage_dir) / "pool" / "pool.jsonl"


def expected_pool_size(stream: str, config: StudyConfig) -> int:
    """D09: the pooled stages carry exactly M members per cell; calibration,
    greedy and qualification are single-draw stages (pool_index 0 only).
    There is no other pool size, and no caller-chosen override."""
    if stream in ("confirmatory", "pilot"):
        return config.generation_pool_size
    if stream in ("calibration", "greedy", "qualification"):
        return 1
    raise ProtocolError(f"unknown generation stream {stream!r}")


def required_member_ids(spec: ModelSpec, stream: str, cells: list[Cell],
                        pool_size: int) -> dict[str, tuple[Cell, int]]:
    required: dict[str, tuple[Cell, int]] = {}
    for cell in cells:
        for index in range(pool_size):
            rid = pool_row_id(spec.model_key, stream, cell.block_id, cell.arm,
                              index)
            required[rid] = (cell, index)
    return required


def build_pools(spec: ModelSpec, cells: list[Cell], *, stream: str,
                stage_dir: Path, config: StudyConfig, model_dir: Path,
                device: int = 0, chunk_size: int = 32,
                max_repair_rounds: int = 3) -> dict[str, Any]:
    """Construct (or repair) the pools of a stage until complete; fail closed.

    Idempotent: existing members are never regenerated or modified; only
    missing identities are generated, each under its original deterministic
    seed (amendment §2.5).
    """
    if len({(c.block_id, c.arm) for c in cells}) != len(cells):
        raise ProtocolError("duplicate (block, arm) cells in stage plan")
    stage_dir = Path(stage_dir)
    store = AppendOnceJsonl(pool_path(stage_dir))
    plan = backend_plan(
        spec, decoding="greedy" if stream == "greedy" else "stochastic",
        chunk_size=chunk_size)
    config_hash = backend_config_hash(plan)
    required = required_member_ids(spec, stream, cells,
                                   expected_pool_size(stream, config))

    rounds = 0
    while True:
        have = store.existing_ids()
        missing = {rid: pair for rid, pair in required.items()
                   if rid not in have}
        if not missing:
            break
        if rounds > max_repair_rounds:
            report = {"status": "INCOMPLETE_POOL",
                      "missing_members": sorted(missing)[:200],
                      "missing_count": len(missing),
                      "rounds_attempted": rounds}
            write_json(stage_dir / "pool" / "integrity_failure.json", report)
            raise ProtocolError(
                f"pool construction failed closed after {rounds} rounds: "
                f"{len(missing)} members still missing (see "
                f"{stage_dir / 'pool' / 'integrity_failure.json'})")
        design_rows = []
        for rid, (cell, index) in sorted(missing.items()):
            seed = generation_seed(config.generation_root_seed, stream,
                                   spec.model_id, cell.prompt_sha, index)
            design_rows.append({
                "row_id": rid,
                "user_prompt": cell.prompt,
                "scientific_seed": seed,
                "block_id": cell.block_id,
                "arm": cell.arm,
                "pool_index": index,
                "prompt_hash": cell.prompt_sha,
                "stream": stream,
            })
        outcome = run_backend(stage_dir / "pool" / f"gen_round{rounds}",
                              plan, design_rows, device=device)
        accepted, failed = [], []
        for row in outcome["rows"]:
            if row.get("outcome") == "OK":
                accepted.append(_pool_row(spec, stream, row, config_hash))
            else:
                failed.append({"row_id": row.get("row_id"),
                               "outcome": row.get("outcome"),
                               "detail": row.get("outcome_detail", "")[:300]})
        if accepted:
            store.append(accepted)
        if failed:
            write_json(stage_dir / "pool" / f"failures_round{rounds}.json",
                       {"failed": failed})
        append_run_record(model_dir, {
            "event": "pool_generation_round", "stage": str(stage_dir.name),
            "stream": stream, "round": rounds, "requested": len(design_rows),
            "accepted": len(accepted), "failed": len(failed),
            "backend_config_hash": config_hash})
        rounds += 1

    from dci1.generation.validation import validate_pools

    report = validate_pools(spec, cells, stream=stream, stage_dir=stage_dir,
                            config=config)
    write_json(stage_dir / "pool" / "pool_integrity_report.json", report)
    return report


def _pool_row(spec: ModelSpec, stream: str, backend_row: dict[str, Any],
              config_hash: str) -> dict[str, Any]:
    """One immutable pool member from one OK backend row (amendment §2.4)."""
    raw = backend_row.get("raw_generation", "")
    return {
        "row_id": backend_row["row_id"],
        "model_key": spec.model_key,
        "model_id": spec.model_id,
        "model_revision": spec.revision,
        "stream": stream,
        "block_id": backend_row["block_id"],
        "arm": backend_row["arm"],
        "prompt_hash": backend_row["prompt_hash"],
        "pool_index": int(backend_row["pool_index"]),
        "generation_seed": int(backend_row.get("seed_reasoning", 0)),
        "raw_response": raw,
        "final_answer": backend_row.get("final_answer", ""),
        "response_content_hash": sha_text(raw),
        "token_count": int(backend_row.get("total_generated_tokens", 0)),
        "finish_reason": backend_row.get("finish_reason", ""),
        "backend_config_hash": config_hash,
    }
