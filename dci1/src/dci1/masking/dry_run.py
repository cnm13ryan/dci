"""The blind dry run (Addendum A §4, R47).

Executes the entire masking and analysis pipeline on synthetic data with a
known injected structure — the synthetic focal arm fails the target far more
often than the reference arms — plus a known permutation record, and verifies
that (1) the full pipeline runs, (2) fail-closed branches fire where they
must, and (3) the injected structure is recovered after unmasking while the
masked-phase estimate is scrambled. No real study outcome is touched.
"""
from __future__ import annotations

import shutil
from typing import Any

from dci1 import flow
from dci1.analysis.entrypoint import run_masked_analysis
from dci1.design.blocks import Block, order_for_index
from dci1.design.prompts import prompt_for_cell
from dci1.evidence.layout import SYNTHETIC_SLUG, StudyTree
from dci1.evidence.sealing import CacheWriter, replicate_raw_layers, seal_stage
from dci1.evidence.store import write_json
from dci1.generation.pools import Cell
from dci1.masking import custody
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import ARMS, ProtocolError, study_config
from dci1.protocol.hashing import sha, sha_text
from dci1.protocol.seeds import generation_seed

_SPEC = ModelSpec(
    model_key="_dryrun", model_id="synthetic/dryrun", revision="dry-rev-0",
    family="synthetic", chat_template_kwargs={}, switch_expectation="inert",
    leakage_markers=("<think>",))
_N, _M = 2, 8
_REFS = ("C1", "C3", "C10")
#: The injected effect: the focal arm fails the target this often; every
#: reference arm always passes. True tau = _FOCAL_FAIL.
_FOCAL_FAIL_EVERY = 2          # every second focal response fails


def _blocks(count: int = 24) -> list[Block]:
    return [Block(index=i, block_id=f"D{i:02d}", topic_id=f"dry-topic-{i}",
                  question=f"Why is dry-run question number {i} asked?",
                  order=order_for_index(i), wording_target=i % 4,
                  wording_added=(i // 4) % 4)
            for i in range(count)]


def _response(block_id: str, arm: str, index: int) -> str:
    block_number = int(block_id[1:])
    fails = (arm == "focal" and
             (block_number + index) % _FOCAL_FAIL_EVERY == 0)
    count = 0 if fails else _N
    return " ".join(["A short dry-run answer sentence."]
                    + ["However, more detail follows."] * count)


def run_blind_dry_run() -> dict[str, Any]:
    config = study_config()
    tree = StudyTree(model_slug=SYNTHETIC_SLUG, freeze_id="dryrun")
    if tree.root.exists():
        shutil.rmtree(tree.root)
    if tree.durable_root.exists():
        shutil.rmtree(tree.durable_root)
    blocks = _blocks()
    cells = [Cell(block_id=b.block_id, arm=arm,
                  prompt=prompt_for_cell(b, arm, n=_N, m=_M,
                                         references=_REFS))
             for b in blocks for arm in ARMS]
    flow.write_prompts(tree, cells)
    writer = CacheWriter(tree.cache_file)
    rows = []
    for cell in cells:
        for index in range(config.generation_pool_size):
            text = _response(cell.block_id, cell.arm, index)
            rows.append({
                "row_id": f"_dryrun:confirmatory:{cell.block_id}:"
                          f"{cell.arm}:{index}",
                "model_key": "_dryrun", "model_id": _SPEC.model_id,
                "model_revision": _SPEC.revision, "stream": "confirmatory",
                "block_id": cell.block_id, "arm": cell.arm,
                "prompt_hash": cell.prompt_sha, "pool_index": index,
                "generation_seed": generation_seed(
                    config.generation_root_seed, "confirmatory",
                    _SPEC.model_id, cell.prompt_sha, index),
                "raw_response": text, "final_answer": text,
                "response_content_hash": sha_text(text),
                "token_count": len(text.split()), "finish_reason": "stop",
                "backend_config_hash": sha_text("dryrun-config")})
    writer.append(rows)
    seal_stage(tree, "cache")
    replicate_raw_layers(tree)

    checks: dict[str, Any] = {}
    mask_info = flow.construct_masked_view(
        tree, _SPEC, cells, stream="confirmatory", config=config,
        model_dir=tree.root)
    checks["mask_constructed"] = mask_info["changed"] >= len(blocks) / 2

    masked_result = run_masked_analysis(
        tree.masked_view, blocks, n=_N, m=_M, references=_REFS,
        bootstrap_seed_value=777, n_resamples=400)
    checks["masked_pipeline_ok"] = masked_result["status"] == "OK"

    # fail-closed branch: unmasking without a commitment must fail.
    try:
        custody.verify_commitment(tree, "whatever")
        checks["commitmentless_unmask_fails"] = False
    except ProtocolError:
        checks["commitmentless_unmask_fails"] = True

    masked_hash = sha(masked_result["estimates"])
    custody.write_commitment(
        tree, analysis_plan_hash="dryrun-plan",
        exclusion_decisions_hash="none", verifier_versions="1.0.0",
        failure_taxonomy_assignments_hash="dryrun",
        masked_analysis_result_hash=masked_hash,
        diagnostics_hash="dryrun", actor="dry-run", model_id=_SPEC.model_id,
        allow_dirty=True)
    custody.verify_commitment(tree, masked_hash)
    custody.write_unmasking_record(tree, actor="dry-run",
                                  model_id=_SPEC.model_id,
                                  reason="blind dry run (synthetic)")

    # fail-closed branch: a second unmasking attempt must fail.
    try:
        custody.write_unmasking_record(tree, actor="dry-run",
                                      model_id=_SPEC.model_id, reason="again")
        checks["second_unmask_fails"] = False
    except ProtocolError:
        checks["second_unmask_fails"] = True
    # fail-closed branch: a second mask key / re-mask must fail.
    try:
        custody.write_mask_key_sealed(tree, {})
        checks["second_key_fails"] = False
    except ProtocolError:
        checks["second_key_fails"] = True

    # final analysis on TRUE labels recovers the injected structure.
    from dci1.analysis.run import analyze

    selection = flow.select_primary(tree, _SPEC, cells,
                                    stream="confirmatory", config=config)
    wide = flow.wide_rows(tree, _SPEC, selection)
    final = analyze(wide, blocks, n=_N, m=_M, references=_REFS,
                    bootstrap_seed_value=777, n_resamples=400, masked=False)
    injected = 1.0 / _FOCAL_FAIL_EVERY
    recovered = (final["estimates"]["tau_target_first"]
                 + final["estimates"]["tau_added_first"]) / 2
    checks["structure_recovered_after_unmask"] = \
        abs(recovered - injected) < 0.15
    checks["masked_estimate_scrambled"] = abs(
        (masked_result["estimates"]["tau_target_first"]
         + masked_result["estimates"]["tau_added_first"]) / 2) < injected / 2

    report = {"passed": all(v is True for v in checks.values()),
              "checks": checks, "injected_tau": injected,
              "recovered_tau": recovered}
    write_json(tree.root / "dry_run_report.json", report)
    return report
