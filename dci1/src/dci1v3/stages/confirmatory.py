"""The confirmatory chain (items 39–52, §19–§20): generation, response-blind
primary selection, single-shot confirmatory masking, masked analysis,
single-shot unmasking, and the final analysis on true labels.

Every operation here dispatches through the canonical production path; the
freeze must exist and verify before generation, and canonical evidence
verification runs immediately before every irreversible transition (in the
dispatcher).
"""
from __future__ import annotations

import json
from typing import Any

from dci1v3.analysis.run import analyse
from dci1v3.engine import fs, transitions
from dci1v3.engine.dispatch import Job, operation
from dci1v3.engine.signing import verify_signed
from dci1v3.engine.transitions import load_stage_record
from dci1v3.errors import IntegrityError, ProtocolError
from dci1v3.generation.cache import cache_rows, fill_cache
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import arm_cells, prompt_plan
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_file, sha_obj, sha_text
from dci1v3.stages import masking
from dci1v3.stages.select import select_primary
from dci1v3.topics.split import confirmatory_blocks


def frozen_body(job: Job) -> dict[str, Any]:
    record = load_stage_record(job.tree, C.STAGE_FREEZE)
    if record is None:
        raise ProtocolError("confirmatory operations require the freeze")
    return verify_signed(record, job.context.signing_key_path,
                         where="gate3_freeze")["body"]


def confirmatory_cells(job: Job):
    frozen = frozen_body(job)
    blocks = confirmatory_blocks()
    cells = arm_cells(
        "confirmatory", blocks, n=int(frozen["n_star"]),
        m=int(frozen["m_star"]),
        references=tuple((f, int(q))
                         for f, q in frozen["final_references"]),
        draws=C.M_DRAWS)
    plan = prompt_plan(cells)
    if sha_obj(plan) != frozen["block_plan_hash"]:
        raise IntegrityError("the derived confirmatory plan differs from "
                             "the frozen block plan; generation refused")
    return frozen, cells, plan


def _generate_fn(job: Job):
    from dci1v3.stages.inference import generate_fn
    return generate_fn(job)


@operation("generate", stage=C.STAGE_CONFIRMATORY)
def run_confirmatory(job: Job) -> dict[str, Any]:
    frozen, cells, plan = confirmatory_cells(job)
    stage_dir = job.tree.data_dir("confirmatory")
    stage_dir.mkdir(parents=True, exist_ok=True)
    if not (stage_dir / "prompt_plan.json").exists():
        fs.write_json_once(stage_dir / "prompt_plan.json", plan)
    report = fill_cache(stage_dir, cells, spec=job.spec,
                        stage="confirmatory",
                        generation_root=C.GENERATION_ROOT_SEED,
                        plan=backend_plan(job.spec,
                                          cap=int(frozen["completion_cap"])),
                        generate_fn=_generate_fn(job),
                        environment=job.environment)
    if report["cells"] != C.N_CELLS or report["draws"] != C.N_CACHED_DRAWS:
        raise IntegrityError(f"confirmatory matrix incomplete: {report}")
    body = {"matrix": {"blocks": C.N_BLOCKS, "arms": len(C.ARMS),
                       "draws_per_cell": C.M_DRAWS},
            "cells": report["cells"], "draws": report["draws"],
            "hardware_class": report.get("provenance", {}).get("gpu_name")}
    return {"status": "PASSED", "body": body,
            "input_hashes": {"block_plan": frozen["block_plan_hash"]},
            "output_hashes": {"cache": sha_file(stage_dir / "cache.jsonl")}}


@operation("select-primary", stage=C.STAGE_PRIMARY_SELECTION)
def run_selection(job: Job) -> dict[str, Any]:
    frozen, cells, _plan = confirmatory_cells(job)
    stage_dir = job.tree.data_dir("confirmatory")
    rows = cache_rows(stage_dir)
    primaries = select_primary(cells, rows, model_id=job.spec.model_id)
    if len(primaries) != C.N_PRIMARY:
        raise IntegrityError(f"{len(primaries)} primaries, expected "
                             f"{C.N_PRIMARY}")
    path = stage_dir / "primary_rows.jsonl"
    if path.exists():
        raise IntegrityError("primary selection already exists; selection "
                             "is single-shot")
    path.write_text("".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
        for r in primaries))
    body = {"primaries": len(primaries),
            "selector": frozen["seed_rules"]["primary_draw_rule"],
            "selector_inputs": ["model-id", "prompt-hash"]}
    return {"status": "PASSED", "body": body,
            "input_hashes": {"cache": sha_file(stage_dir / "cache.jsonl")},
            "output_hashes": {"primary_rows": sha_file(path)}}


@operation("mask", stage=C.STAGE_MASK)
def run_mask(job: Job) -> dict[str, Any]:
    stage_dir = job.tree.data_dir("confirmatory")
    primaries = fs.read_jsonl(stage_dir / "primary_rows.jsonl")
    report = masking.create_mask(job.tree, "confirmatory_mask", primaries)
    return {"status": "PASSED", "body": report,
            "input_hashes": {"primary_rows": sha_file(
                stage_dir / "primary_rows.jsonl")},
            "output_hashes": {"masked_view": report["masked_view_hash"],
                              "mask_key_hash": report["mask_key_hash"]}}


@operation("masked-analysis", stage=C.STAGE_MASKED_ANALYSIS)
def run_masked_analysis(job: Job) -> dict[str, Any]:
    frozen = frozen_body(job)
    rows = masking.masked_rows(job.tree, "confirmatory_mask")
    result = analyse(rows, model_id=job.spec.model_id,
                     n=int(frozen["n_star"]),
                     resamples=int(frozen["analysis_plan"]["resamples"]),
                     matrix={"blocks": C.N_BLOCKS, "arms": len(C.ARMS),
                             "draws_per_cell": C.M_DRAWS},
                     expected_blocks=C.N_BLOCKS)
    out_dir = job.tree.data_dir("analysis") / "masked"
    out_dir.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(out_dir / "result.json", result)
    body = {"result_hash": sha_file(out_dir / "result.json"),
            "analysis_code_hash": masking.analysis_code_hash(),
            "phase": "masked"}
    return {"status": "PASSED", "body": body,
            "input_hashes": {"masked_view": sha_file(
                job.tree.masked_view("confirmatory_mask"))},
            "output_hashes": {"masked_result": body["result_hash"]}}


@operation("unmask", stage=C.STAGE_UNMASK)
def run_unmask(job: Job) -> dict[str, Any]:
    masked_record = load_stage_record(job.tree, C.STAGE_MASKED_ANALYSIS)
    masked_body = verify_signed(masked_record,
                                job.context.signing_key_path,
                                where="masked_result")["body"]
    code_hash = masking.analysis_code_hash()
    if code_hash != masked_body["analysis_code_hash"]:
        raise IntegrityError(
            "analysis code changed since the masked phase; unmasking "
            "refused before key access")
    outcome = masking.unmask(job.tree, "confirmatory_mask",
                             timestamp=transitions.utc_now())
    rows = masking.masked_rows(job.tree, "confirmatory_mask")
    unmasked = masking.apply_key(rows, outcome["key"])
    out_dir = job.tree.data_dir("analysis") / "unmasked"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "unmasked_rows.jsonl"
    path.write_text("".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
        for r in unmasked))
    body = {**outcome["record"],
            "unmasked_rows_hash": sha_file(path)}
    return {"status": "PASSED", "body": body,
            "input_hashes": {"masked_result_hash":
                             masked_body["result_hash"]},
            "output_hashes": {"unmasked_rows": body["unmasked_rows_hash"]}}


@operation("final-analysis", stage=C.STAGE_UNMASKED_ANALYSIS)
def run_final(job: Job) -> dict[str, Any]:
    frozen = frozen_body(job)
    unmask_body = verify_signed(
        load_stage_record(job.tree, C.STAGE_UNMASK),
        job.context.signing_key_path, where="unmask_record")["body"]

    # §19 executable check 3: the masked phase reproduces byte-for-byte
    # from the code whose hash was recorded at unmasking.
    code_hash = masking.analysis_code_hash()
    if code_hash != unmask_body["analysis_code_hash"]:
        raise IntegrityError("analysis code changed after unmasking; the "
                            "final analysis supports no primary claim")
    masked_view = masking.masked_rows(job.tree, "confirmatory_mask")
    rerun = analyse(masked_view, model_id=job.spec.model_id,
                    n=int(frozen["n_star"]),
                    resamples=int(frozen["analysis_plan"]["resamples"]),
                    expected_blocks=C.N_BLOCKS)
    masked_result = fs.read_json(
        job.tree.data_dir("analysis") / "masked" / "result.json")
    if sha_obj(rerun) != sha_obj(masked_result):
        raise IntegrityError("masked-phase outputs do not reproduce "
                             "byte-for-byte; final analysis refused")

    unmasked_rows = fs.read_jsonl(
        job.tree.data_dir("analysis") / "unmasked" / "unmasked_rows.jsonl")
    result = analyse(unmasked_rows, model_id=job.spec.model_id,
                     n=int(frozen["n_star"]),
                     resamples=int(frozen["analysis_plan"]["resamples"]),
                     matrix={"blocks": C.N_BLOCKS, "arms": len(C.ARMS),
                             "draws_per_cell": C.M_DRAWS},
                     expected_blocks=C.N_BLOCKS)
    out_dir = job.tree.data_dir("analysis") / "unmasked"
    fs.write_json_once(out_dir / "result.json", result)
    body = {"result_hash": sha_file(out_dir / "result.json"),
            "masked_reproduced": True,
            "analysis_code_hash": code_hash,
            "primary_claims": result["primary_claims"],
            "exchangeability_holds": result["exchangeability_holds"],
            "phase": "unmasked"}
    return {"status": "PASSED", "body": body,
            "input_hashes": {"unmasked_rows":
                             unmask_body["unmasked_rows_hash"]},
            "output_hashes": {"unmasked_result": body["result_hash"]}}


def _sha_line_rows(rows: list[dict[str, Any]]) -> str:
    return sha_text("".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
        for r in rows))
