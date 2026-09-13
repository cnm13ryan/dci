"""Cached-draw generation and the v4 row schema (§8.2, §9, §14.2, §26).

Every cell has predetermined cached-draw identities ``cell_id:draw`` with
predetermined seeds. A missing draw is repaired only by regenerating that exact
identity with its exact seed; pool shrinking, replacement seeds and averaging
around a gap are structurally impossible, because the writer refuses duplicates
and validation requires the exact draw matrix (§14.2).

**All M draws enter the cell mean and there is no selector (§8.2, T-10).** v3
derived one draw of sixteen from a hash; nothing here selects, discards or
replaces a draw, and no function in this package returns a chosen draw index.

**The row is a compliance vector, not a verdict (§9.1, T-1).** Each row carries,
for every constraint *present* in its prompt, the identity, severity, position,
wording index, boolean verdict, graded score, non-vacuity flag and processing
state; and, for every registered constraint *absent* from that prompt, the same
verifier evaluated and marked as an accidental-compliance diagnostic (§25).
Nothing is marginalised at record time and the exact-count verdict has no
privileged status.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

from dci1v4.design.cells import Cell, SlotMap
from dci1v4.engine import fs
from dci1v4.engine.store import CacheWriter
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.generation.backend import GenerateFn
from dci1v4.protocol.hashing import sha_text
from dci1v4.protocol.seeds import GENERATION_ROOT_SEED, generation_seed
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.compliance import score_constraint
from dci1v4.verifiers.constraints import Constraint
from dci1v4.verifiers.target import s0_count, s1_count, s2_count, s3_count
from dci1v4.verifiers.words import alpha_runs

#: Finish reasons that mean the completion cap stopped the response (§9.3).
TRUNCATION_FINISH_REASONS = ("length", "max_tokens")


def is_truncated(finish_reason: str | None) -> bool:
    return (finish_reason or "").lower() in TRUNCATION_FINISH_REASONS


def _score_entry(constraint: Constraint, text: str, *, truncated: bool,
                 slot: str, position: int | None, wording_index: int | None,
                 role: str) -> dict[str, Any]:
    score = score_constraint(constraint, text, truncated=truncated)
    return {"slot": slot, "kind": score.kind, "severity": score.severity,
            "position": position, "wording_index": wording_index,
            "statistic": score.statistic, "passed": score.passed,
            "graded": score.graded, "non_vacuous": score.non_vacuous,
            "vacuous_pass": score.vacuous_pass,
            "processing_failure": score.processing_failure, "role": role}


def compliance_row(cell: Cell, text: str, *, slot_map: SlotMap,
                   finish_reason: str | None) -> dict[str, Any]:
    """The §9.1 compliance vector plus the §9.3 degeneracy record."""
    truncated = is_truncated(finish_reason)
    word_count = len(alpha_runs(text))
    present = {c.slot for c in cell.constituents}

    scores = [_score_entry(Constraint(item.kind, item.severity), text,
                           truncated=truncated, slot=item.slot,
                           position=item.position,
                           wording_index=item.wording_index, role="outcome")
              for item in cell.constituents]

    # §25: every registered constraint absent from this prompt is still
    # scored, giving the base rate at which an unconstrained or
    # differently-constrained answer satisfies it by chance. These are
    # diagnostics and never outcomes.
    accidental = [_score_entry(Constraint(kind, severity), text,
                               truncated=truncated, slot=slot, position=None,
                               wording_index=None,
                               role="accidental_compliance_diagnostic")
                  for slot, (kind, severity) in sorted(slot_map.items())
                  if slot not in present]

    a_present = any(item.kind == "A" for item in cell.constituents)
    active_wordings = tuple(item.text for item in cell.constituents)
    return {
        "scores": scores,
        "accidental": accidental,
        "empty": word_count == 0,
        "word_count": word_count,
        "truncated": truncated,
        "finish_reason": finish_reason,
        "verifier_processing_failure": any(s["processing_failure"]
                                           for s in scores + accidental),
        # §25: the accidental-occurrence count of the exact-count target word
        # in every cell where A is absent.
        "accidental_s0": None if a_present else s0_count(text),
        # §9.2: the three registered alternatives, recorded for the robustness
        # family and never redefining X_A.
        "exact_count_alternatives": {
            "s0": s0_count(text), "s1": s1_count(text), "s2": s2_count(text),
            "s3": s3_count(text, active_wordings)},
        "verifier_source_hash": verifier_source_hash(),
    }


def build_row(cell: Cell, *, draw_index: int, spec, stage: str,
              slot_map: SlotMap, study_id: str, raw: str,
              finish_reason: str | None, seed: int,
              prompt_tokens: int, token_count: int,
              provenance: dict[str, Any], environment: dict[str, Any]
              ) -> dict[str, Any]:
    """One committed row, carrying every §26 provenance field."""
    return {
        "row_id": f"{cell.cell_id}:{draw_index}",
        "study_id": study_id,
        "stage": stage,
        "artifact_state": "committed",
        "model_key": spec.model_key,
        "model_id": spec.model_id,
        "model_revision": spec.revision,
        "cell_id": cell.cell_id,
        "cell_type": cell.cell_type,
        "topic_id": cell.topic_id,
        "block_id": cell.block_id,
        "block_index": cell.block_index,
        "order": cell.order,
        "load": cell.load,
        "constituents": [{"slot": x.slot, "kind": x.kind,
                          "severity": x.severity, "position": x.position,
                          "wording_index": x.wording_index}
                         for x in cell.constituents],
        "draw_index": draw_index,
        "prompt_hash": cell.prompt_hash,
        "backend_version": provenance.get(
            "vllm_version", provenance.get("backend", "unknown")),
        "interpreter": environment.get("python_executable"),
        "dependency_digest": environment.get("dependency_digest"),
        "hardware_class": provenance.get("gpu_name", "unknown"),
        "seed": seed,
        "raw_response": raw,
        "response_content_hash": sha_text(raw),
        "prompt_tokens": prompt_tokens,
        "token_count": token_count,
        **compliance_row(cell, raw, slot_map=slot_map,
                         finish_reason=finish_reason),
    }


def fill_cache(stage_dir: Path, cells: Sequence[Cell], *, spec, stage: str,
               slot_map: SlotMap, study_id: str, plan: dict[str, Any],
               generate_fn: GenerateFn, environment: dict[str, Any],
               generation_root: int = GENERATION_ROOT_SEED,
               max_repair_rounds: int = 3) -> dict[str, Any]:
    """Fill the append-only cache to exactly ``cell.draws`` per cell; validate;
    fail closed on exhausted repairs (§14.2)."""
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
                f"{stage}: {len(missing)} cached draws missing after {rounds} "
                f"repair rounds; the run fails closed for those cells and no "
                f"draw is imputed or substituted (§14.2)")
        design_rows = []
        for rid, (cell, index) in sorted(missing.items()):
            design_rows.append({
                "row_id": rid, "user_prompt": cell.prompt,
                "scientific_seed": generation_seed(
                    generation_root, stage, spec.model_id, cell.prompt_hash,
                    index),
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
            raw = row.get("final_answer") or row.get("raw_generation", "")
            accepted.append(build_row(
                cell, draw_index=index, spec=spec, stage=stage,
                slot_map=slot_map, study_id=study_id, raw=raw,
                finish_reason=row.get("finish_reason", ""),
                seed=int(row.get("seed_reasoning",
                                 row.get("scientific_seed", 0))),
                prompt_tokens=int(row.get("prompt_tokens", 0)),
                token_count=int(row.get("total_generated_tokens", 0)),
                provenance=provenance, environment=environment))
        if accepted:
            writer.append(accepted)
        rounds += 1

    report = validate_cache(stage_dir, cells, spec=spec, stage=stage,
                            generation_root=generation_root)
    fs.write_json(stage_dir / "cache_report.json", report)
    return {**report, "provenance": provenance}


def validate_cache(stage_dir: Path, cells: Sequence[Cell], *, spec,
                   stage: str, generation_root: int = GENERATION_ROOT_SEED
                   ) -> dict[str, Any]:
    """The exact draw matrix, seed derivations, content hashes, duplicates."""
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
        expected_seed = generation_seed(generation_root, stage, spec.model_id,
                                        row["prompt_hash"], row["draw_index"])
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
        raise IntegrityError(
            f"incomplete draw matrix for {len(incomplete)} cell(s), first: "
            f"{incomplete[0]}; a cell mean is never formed from a partial cell")
    extras = set(by_cell) - {c.cell_id for c in cells}
    if extras:
        raise IntegrityError(f"cache contains cells outside the plan: "
                             f"{sorted(extras)[:3]}")
    return {"status": "COMPLETE", "cells": len(cells), "draws": len(rows),
            "duplicates": duplicate_report(rows)}


def duplicate_report(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """§14.2 / check C14: byte-identical replicate pairs within a cell.

    A rate above 0.05 in any cell fails qualification, because duplicate rows
    cannot count as independent replicates.
    """
    by_cell: dict[str, list[str]] = {}
    for row in rows:
        by_cell.setdefault(row["cell_id"], []).append(
            row["response_content_hash"])
    worst_cell, worst_rate, pairs_total, pairs_dup = None, 0.0, 0, 0
    for cell_id, hashes in by_cell.items():
        n = len(hashes)
        if n < 2:
            continue
        pairs = n * (n - 1) // 2
        counts: dict[str, int] = {}
        for digest in hashes:
            counts[digest] = counts.get(digest, 0) + 1
        duplicates = sum(c * (c - 1) // 2 for c in counts.values())
        pairs_total += pairs
        pairs_dup += duplicates
        rate = duplicates / pairs
        if rate > worst_rate:
            worst_cell, worst_rate = cell_id, rate
    return {"cells": len(by_cell), "pairs": pairs_total,
            "duplicate_pairs": pairs_dup,
            "overall_rate": (pairs_dup / pairs_total) if pairs_total else 0.0,
            "worst_cell": worst_cell, "worst_cell_rate": worst_rate}


def cache_rows(stage_dir: Path) -> list[dict[str, Any]]:
    return CacheWriter(Path(stage_dir) / "cache.jsonl").rows()


def rows_by_cell(rows: Iterable[dict[str, Any]]
                 ) -> dict[str, dict[int, dict[str, Any]]]:
    grouped: dict[str, dict[int, dict[str, Any]]] = {}
    for row in rows:
        members = grouped.setdefault(row["cell_id"], {})
        if row["draw_index"] in members:
            raise ProtocolError(f"duplicate draw {row['row_id']}")
        members[row["draw_index"]] = row
    return grouped
