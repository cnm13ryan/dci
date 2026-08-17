"""Gate 0: the procedural pilot (§17). Execution integrity only.

Twelve fixed pre-screen topics, six arms, both orders, fixtures n=3, m=9,
RF1@5, RF2@5, RF5@8, a 1,024-token cap: 72 logical cells and 1,152 cached
draws through the production cache, selection, masking, and analysis paths.
Only the five registered quantity classes are inspected; no target-failure
rate, uptake rate, or contrast is computed or viewed. Any failed acceptance
condition returns APPARATUS_FAILURE.
"""
from __future__ import annotations

import json
from typing import Any

from dci1v3.analysis.run import analyse, redact_structural
from dci1v3.engine import fs, store, transitions
from dci1v3.engine.dispatch import Job, operation
from dci1v3.engine.store import CacheWriter
from dci1v3.errors import TerminalStatus, V3Error
from dci1v3.generation.cache import cache_rows, fill_cache
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import arm_cells, prompt_plan
from dci1v3.protocol import constants as C
from dci1v3.protocol.codebook import validate_row
from dci1v3.protocol.hashing import sha_obj, sha_text
from dci1v3.stages import masking
from dci1v3.stages.select import select_primary
from dci1v3.topics.split import pilot_blocks


def _generate_fn(job: Job):
    from dci1v3.stages.inference import generate_fn
    return generate_fn(job)


def _tamper_probe(stage_dir) -> None:
    """Acceptance condition 6: a mutated stored byte changes the content
    hash and the reader refuses the row (demonstrated on a scratch copy)."""
    probe = stage_dir / "tamper_probe.jsonl"
    lines = (stage_dir / "cache.jsonl").read_text().splitlines(True)
    row = json.loads(lines[0])
    row["raw_response"] = row["raw_response"] + "X"   # hash now stale
    probe.write_text(json.dumps(row, sort_keys=True, ensure_ascii=False)
                     + "\n" + "".join(lines[1:]))
    try:
        CacheWriter(probe).rows()
    except V3Error:
        probe.unlink()
        return
    raise TerminalStatus("APPARATUS_FAILURE", {
        "criterion": "content-hash refusal",
        "observed": "a tampered row was accepted"})


def _restore_drill(job: Job, stage_dir) -> dict[str, Any]:
    """Acceptance condition 7: delete the local cache, restore from durable
    storage, reproduce every row with the same hashes."""
    durable = job.tree.durable / "pilot"
    store.replicate(stage_dir, durable)
    before = store.fingerprint_tree(stage_dir)
    (stage_dir / "cache.jsonl").unlink()
    store.restore(durable, stage_dir)
    after = store.fingerprint_tree(stage_dir)
    if before != after:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "criterion": "durable restoration",
            "observed": "restored bytes differ"})
    return {"files": len(after), "byte_identical": True}


@operation("pilot", stage=C.STAGE_GATE0)
def run_pilot(job: Job) -> dict[str, Any]:
    try:
        return _run(job)
    except TerminalStatus:
        raise
    except V3Error as error:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "criterion": "apparatus execution",
            "observed": str(error)}) from error


def _run(job: Job) -> dict[str, Any]:
    stage_dir = job.tree.data_dir("pilot")
    blocks = pilot_blocks()
    cells = arm_cells("pilot", blocks, n=C.PILOT_N, m=C.PILOT_M,
                      references=C.PILOT_REFERENCES, draws=C.M_DRAWS)
    if len(cells) != C.PILOT_CELLS:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "criterion": "cell count", "observed": len(cells)})
    plan_payload = prompt_plan(cells)
    stage_dir.mkdir(parents=True, exist_ok=True)
    if not (stage_dir / "prompt_plan.json").exists():
        fs.write_json_once(stage_dir / "prompt_plan.json", plan_payload)

    plan = backend_plan(job.spec, cap=C.PILOT_CAP)
    report = fill_cache(stage_dir, cells, spec=job.spec, stage="pilot",
                        generation_root=C.GENERATION_ROOT_SEED, plan=plan,
                        generate_fn=_generate_fn(job),
                        environment=job.environment)
    if report["cells"] != C.PILOT_CELLS or report["draws"] != C.PILOT_DRAWS:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "criterion": "committed counts", "observed": report})

    rows = cache_rows(stage_dir)
    for row in rows:
        validate_row(row)                      # acceptance condition 4

    primaries = select_primary(cells, rows, model_id=job.spec.model_id)
    if len(primaries) != C.PILOT_CELLS:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "criterion": "one primary row per cell",
            "observed": len(primaries)})

    _tamper_probe(stage_dir)
    restore_report = _restore_drill(job, stage_dir)

    # --------- acceptance condition 8: the separate pilot_mask cycle ------
    confirmatory_before = store.fingerprint_tree(
        job.tree.mask_dir("confirmatory_mask"))
    mask_report = masking.create_mask(job.tree, "pilot_mask", primaries)
    masked = masking.masked_rows(job.tree, "pilot_mask")
    structural = redact_structural(analyse(
        masked, model_id=job.spec.model_id, n=C.PILOT_N,
        resamples=200, expected_blocks=C.PILOT_TOPICS))
    fs.write_json(stage_dir / "structural_analysis.json", structural)
    unmask_report = masking.unmask(job.tree, "pilot_mask",
                                   timestamp=transitions.utc_now())
    confirmatory_after = store.fingerprint_tree(
        job.tree.mask_dir("confirmatory_mask"))
    masking.assert_namespace_untouched(confirmatory_before,
                                       confirmatory_after,
                                       "confirmatory_mask")

    body = {
        "hardware_class": report.get("provenance", {}).get("gpu_name"),
        "committed": {"cells": report["cells"], "draws": report["draws"]},
        "accepted": {"cells": report["cells"], "draws": report["draws"]},
        "technical_failures_after_retries": 0,
        "codebook_valid": True,
        "content_hash_refusal_demonstrated": True,
        "durable_restoration": restore_report,
        "pilot_mask": {"created": mask_report,
                       "unmask": unmask_report["record"],
                       "confirmatory_namespace_untouched": True},
        "structural_analysis_hash": sha_obj(structural),
        "fixtures": {"n": C.PILOT_N, "m": C.PILOT_M,
                     "references": [list(r) for r in C.PILOT_REFERENCES],
                     "cap": C.PILOT_CAP},
    }
    return {"status": "PASSED", "body": body,
            "input_hashes": {"prompt_plan": sha_obj(plan_payload)},
            "output_hashes": {"cache": sha_text(
                (stage_dir / "cache.jsonl").read_text())}}
