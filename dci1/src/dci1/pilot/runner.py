"""Gate 0 — the procedural pilot (prereg §17; D10/D15), on the Addendum-A
apparatus.

Exercises the exact evidence flow the confirmatory run will use, end to end,
on twelve calibration topics under the reserved non-registered tree id
``prefreeze-pilot``: prompts → append-only cache (M members per cell, sealed)
→ replication → primary selection → Parquet derived tables → v2 §19 masking
under addendum custody → commitment → unmasking → final analysis →
`verify-evidence` → restore drill. Exactly four quantities are inspected
(§17); no target failure rate, arm difference or contrast is computed or
viewed — analysis artifacts are written and only their completion recorded.

Pilot rows are discarded from every scientific quantity and retained as the
record of the pilot.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from dci1 import flow
from dci1.analysis.entrypoint import run_masked_analysis
from dci1.design.plan import pilot_blocks, pilot_cells
from dci1.evidence.layout import PREFREEZE_PILOT_ID, StudyTree
from dci1.evidence.sealing import CacheWriter
from dci1.evidence.store import read_json, write_json
from dci1.evidence.verify import restore_drill, verify_evidence
from dci1.freeze.record import environment_record
from dci1.masking import custody
from dci1.models.adapters import ModelSpec
from dci1.protocol.codebook import validate_rows
from dci1.protocol.constants import (
    PILOT_CELLS,
    PILOT_PROVISIONAL,
    PILOT_TRUNCATION_CEILING,
    ProtocolError,
    StudyConfig,
)
from dci1.protocol.hashing import sha
from dci1.protocol.seeds import bootstrap_seed
from dci1.tables.build import read_table


def pilot_tree(spec: ModelSpec) -> StudyTree:
    return StudyTree(model_slug=spec.model_key, freeze_id=PREFREEZE_PILOT_ID)


def write_pilot_record(tree: StudyTree, spec: ModelSpec,
                       config: StudyConfig) -> str:
    """The pilot's non-registered frozen plan: the fixed reference every
    §27-style check validates against during Gate 0."""
    payload = {
        "PREFREEZE_PILOT_NOT_A_FREEZE_RECORD": True,
        "model": {"model_key": spec.model_key, "model_id": spec.model_id,
                  "revision": spec.revision},
        "provisional": dict(PILOT_PROVISIONAL,
                            references=list(PILOT_PROVISIONAL["references"])),
        "resampling": config.to_dict(),
    }
    if not tree.freeze_record.exists():
        write_json(tree.freeze_record, payload)
    return _pilot_record_hash(tree)


def _pilot_record_hash(tree: StudyTree) -> str:
    record = read_json(tree.freeze_record)
    return sha({k: v for k, v in record.items() if k != "freeze_hash"})


def run_pilot(spec: ModelSpec, *, config: StudyConfig, model_dir: Path,
              durable_dir: Path, device: int = 0) -> dict[str, Any]:
    model_dir = Path(model_dir)
    tree = pilot_tree(spec)
    blocks = pilot_blocks()
    cells = pilot_cells()
    n = PILOT_PROVISIONAL["n"]
    m = PILOT_PROVISIONAL["m"]
    references = tuple(PILOT_PROVISIONAL["references"])
    write_pilot_record(tree, spec, config)
    record_hash = _pilot_record_hash(tree)
    environment = environment_record()
    seed = bootstrap_seed(config.bootstrap_seed, spec.model_id, "pilot")

    flow.write_prompts(tree, cells)
    cache_report = flow.generate_cache(tree, spec, cells, stream="pilot",
                                       config=config, model_dir=model_dir,
                                       device=device)

    cache_rows = CacheWriter(tree.cache_file).rows()
    failures = sorted(tree.integrity_dir.glob("failures_round*.json"))
    transient = sum(len(read_json(p).get("failed", [])) for p in failures)

    # ---- masking under custody, then the full analysis path ---------------
    if not tree.mask_key.exists():
        flow.construct_masked_view(tree, spec, cells, stream="pilot",
                                   config=config, model_dir=model_dir)
    masked_result = run_masked_analysis(
        tree.masked_view, blocks, n=n, m=m, references=references,
        bootstrap_seed_value=seed, n_resamples=2000)
    masked_ok = masked_result["status"] == "OK"
    masked_hash = sha(masked_result["estimates"])
    derive_masked = flow.derive_primary(
        tree, spec, blocks, cells, stream="pilot", config=config, n=n, m=m,
        references=references, freeze_record_hash=record_hash,
        bootstrap_seed_value=seed, analysis_stage="masked",
        environment_record=environment, n_resamples=2000, allow_dirty=True)
    if not tree.commitment.exists():
        custody.write_commitment(
            tree, analysis_plan_hash=record_hash,
            exclusion_decisions_hash="none",
            verifier_versions="1.0.0",
            failure_taxonomy_assignments_hash="deterministic-frozen-program",
            masked_analysis_result_hash=masked_hash,
            diagnostics_hash=sha(derive_masked["result"]["checks"]
                                 ["compliance"]),
            actor="gate0-pilot", model_id=spec.model_id, allow_dirty=True)
    if not tree.unmasking_record.exists():
        custody.verify_commitment(tree, masked_hash)
        custody.write_unmasking_record(
            tree, actor="gate0-pilot", model_id=spec.model_id,
            reason="Gate 0 procedural pilot (non-registered, §17)")
    derive_final = flow.derive_primary(
        tree, spec, blocks, cells, stream="pilot", config=config, n=n, m=m,
        references=references, freeze_record_hash=record_hash,
        bootstrap_seed_value=seed, analysis_stage="final",
        environment_record=environment, n_resamples=2000, allow_dirty=True)

    accepted = read_table(tree.derived_primary / "accepted.parquet",
                          "accepted")

    # ---- the four inspected quantities (§17), and nothing else ------------
    truncation_pool = (sum(1 for r in cache_rows
                           if r["finish_reason"] == "length")
                       / len(cache_rows)) if cache_rows else float("nan")
    truncated_column = accepted.column("finish_reason").to_pylist()
    truncation_accepted = (sum(1 for f in truncated_column if f == "length")
                           / len(truncated_column))
    codebook_ok, codebook_error = True, ""
    try:
        selection_rows = flow.select_primary(tree, spec, cells,
                                             stream="pilot", config=config)
        validate_rows("accepted", _codebook_view(tree, spec, selection_rows))
    except ProtocolError as error:
        codebook_ok, codebook_error = False, str(error)

    conditions: dict[str, Any] = {}
    conditions["c1_rows_committed_once"] = accepted.num_rows == PILOT_CELLS
    conditions["c2_zero_unresolved_technical_failures"] = \
        cache_report["status"] == "COMPLETE"
    conditions["c3_truncation_at_or_below_ceiling"] = \
        truncation_pool <= PILOT_TRUNCATION_CEILING
    conditions["c4_codebook_conformance"] = codebook_ok
    conditions["c5_analysis_completed"] = bool(
        masked_ok and derive_masked["result_status"] == "OK"
        and derive_final["result_status"] == "OK")

    # c6: mutation detection, demonstrated on a scratch copy.
    scratch = tree.root / "integrity" / "scratch_mutation"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    copy_path = scratch / "generations.jsonl"
    shutil.copyfile(tree.cache_file, copy_path)
    text = copy_path.read_text()
    mutated = text.replace('"raw_response": "', '"raw_response": "X', 1)
    copy_path.write_text(mutated if mutated != text else text + " ")
    try:
        CacheWriter(copy_path).verify_hashes()
        conditions["c6_mutation_detected"] = False
    except ProtocolError:
        conditions["c6_mutation_detected"] = True
    shutil.rmtree(scratch)

    # c7: durable restore + full byte-identity restore drill of derived/.
    workspace = tree.root / "integrity" / "restore_ws"
    if workspace.exists():
        shutil.rmtree(workspace)

    def rebuild(restored: StudyTree) -> None:
        flow.derive_primary(
            restored, spec, blocks, cells, stream="pilot", config=config,
            n=n, m=m, references=references, freeze_record_hash=record_hash,
            bootstrap_seed_value=seed, analysis_stage="final",
            environment_record=environment, n_resamples=2000,
            allow_dirty=True, drill_rebuild=True)

    try:
        drill = restore_drill(tree, rebuild, workspace)
        conditions["c7_restore_reproduces_rows"] = drill["byte_identical"]
    finally:
        if workspace.exists():
            shutil.rmtree(workspace)

    verify_report = verify_evidence(tree)
    conditions["c8_verify_evidence_passed"] = verify_report.get("ok", False)

    passed = all(v is True for v in conditions.values())
    report = {
        "model_key": spec.model_key,
        "tree": str(tree.root),
        "inspected_quantities": {
            "committed_rows": accepted.num_rows,
            "unresolved_technical_failure_share":
                0.0 if cache_report["status"] == "COMPLETE" else 1.0,
            "transient_failures_before_repair": transient,
            "truncation_share_pool": truncation_pool,
            "truncation_share_accepted": truncation_accepted,
            "codebook_conformance": codebook_ok,
            "codebook_error": codebook_error,
        },
        "cache_report": cache_report,
        "conditions": conditions,
        "passed": passed,
    }
    write_json(model_dir / "pilot_report.json", report)
    return report


def _codebook_view(tree: StudyTree, spec: ModelSpec,
                   selection_rows: list[dict[str, Any]]
                   ) -> list[dict[str, Any]]:
    """The wide accepted rows in the main-prompt codebook's shape."""
    rows = []
    for row in flow.wide_rows(tree, spec, selection_rows):
        rows.append({
            "row_id": row["row_id"], "model_key": row["model_key"],
            "model_id": row["model_id"],
            "model_revision": row["model_revision"],
            "block_id": row["block_id"], "arm": row["arm"],
            "prompt_hash": row["prompt_hash"],
            "pool_index": row["pool_index"],
            "generation_seed": row["generation_seed"],
            "response": row["response"],
            "response_content_hash": row["response_content_hash"],
            "token_count": row["token_count"],
            "finish_reason": row["finish_reason"],
            "backend_config_hash": row["backend_config_hash"],
        })
    return rows
