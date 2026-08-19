"""The tiny synthetic end-to-end smoke run (task §9 step 16). CPU only.

Fabricates a small but structurally faithful confirmatory stage — synthetic
model, six blocks × six arms × M cached members with correctly derived seeds
and hashes — then exercises the complete downstream apparatus: pool
validation, primary selection, pseudo-runs with the bit-identity invariant,
§27 integrity validation, masking, and the full analysis. No GPU, no backend,
no real model; the point is that every seam downstream of generation runs end
to end and fails closed where it should.
"""
from __future__ import annotations

import shutil
from typing import Any

from dci1.analysis.run import analyze
from dci1.design.blocks import Block, order_for_index
from dci1.design.prompts import prompt_for_cell
from dci1.evidence.integrity import validate_accepted
from dci1.evidence.layout import synthetic_dir
from dci1.evidence.store import AppendOnceJsonl, write_json
from dci1.generation.pools import Cell, pool_path
from dci1.masking.mask import construct_mask, unmask
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import ARMS, study_config
from dci1.protocol.hashing import sha_text
from dci1.protocol.seeds import generation_seed
from dci1.resampling.primary import build_primary, load_accepted
from dci1.resampling.pseudo import (
    assert_primary_invariant,
    build_pseudo_run,
    primary_fingerprint,
)

_SMOKE_SPEC = ModelSpec(
    model_key="_smoke", model_id="synthetic/smoke", revision="smoke-rev-0",
    family="synthetic", chat_template_kwargs={}, switch_expectation="inert",
    leakage_markers=("<think>",))

_N, _M = 2, 8
_REFS = ("C1", "C3", "C10")


def _blocks() -> list[Block]:
    return [Block(index=i, block_id=f"S{i:02d}", topic_id=f"smoke-topic-{i}",
                  question=f"Why does smoke test number {i} rise?",
                  order=order_for_index(i), wording_target=i % 4,
                  wording_added=(i // 4) % 4)
            for i in range(6)]


def _synthetic_response(block_id: str, arm: str, index: int) -> str:
    weight = int(sha_text(f"{block_id}|{arm}|{index}")[:2], 16)
    count = weight % 4                       # 0..3 occurrences of the target
    sentences = ["The smoke rises because warm air is lighter."]
    sentences += ["However, cold air sinks below it."] * count
    if weight % 7 == 0:
        return ""                            # occasional empty response
    return " ".join(sentences)


def run_smoke() -> dict[str, Any]:
    config = study_config()
    root = synthetic_dir("smoke")
    if root.exists():
        shutil.rmtree(root)
    stage_dir = root / "confirmatory"
    blocks = _blocks()
    cells = [Cell(block_id=b.block_id, arm=arm,
                  prompt=prompt_for_cell(b, arm, n=_N, m=_M,
                                         references=_REFS))
             for b in blocks for arm in ARMS]

    store = AppendOnceJsonl(pool_path(stage_dir))
    rows = []
    for cell in cells:
        for index in range(config.generation_pool_size):
            text = _synthetic_response(cell.block_id, cell.arm, index)
            rows.append({
                "row_id": f"_smoke:confirmatory:{cell.block_id}:"
                          f"{cell.arm}:{index}",
                "model_key": "_smoke",
                "model_id": _SMOKE_SPEC.model_id,
                "model_revision": _SMOKE_SPEC.revision,
                "stream": "confirmatory",
                "block_id": cell.block_id, "arm": cell.arm,
                "prompt_hash": cell.prompt_sha, "pool_index": index,
                "generation_seed": generation_seed(
                    config.generation_root_seed, "confirmatory",
                    _SMOKE_SPEC.model_id, cell.prompt_sha, index),
                "raw_response": text, "final_answer": text.strip(),
                "response_content_hash": sha_text(text),
                "token_count": len(text.split()),
                "finish_reason": "stop" if text else "",
                "backend_config_hash": sha_text("smoke-backend-config"),
            })
    store.append(rows)

    checks: dict[str, Any] = {}
    build_primary(_SMOKE_SPEC, cells, stream="confirmatory",
                  stage_dir=stage_dir, config=config)
    accepted = load_accepted(stage_dir)
    checks["accepted_rows"] = len(accepted) == len(blocks) * 6
    validate_accepted(accepted, cells, _SMOKE_SPEC, stream="confirmatory",
                      config=config,
                      frozen_backend_config_hash=sha_text(
                          "smoke-backend-config"))
    checks["integrity_validated"] = True

    before = primary_fingerprint(stage_dir)
    for r in range(3):
        build_pseudo_run(_SMOKE_SPEC, cells, stream="confirmatory",
                         stage_dir=stage_dir, config=config, run_index=r)
    assert_primary_invariant(before, primary_fingerprint(stage_dir))
    checks["primary_invariant_under_pseudo_runs"] = True

    mask_info = construct_mask(accepted, root / "analysis", root)
    from dci1.evidence.store import read_jsonl

    masked_rows = read_jsonl(root / "analysis" / "masked_accepted.jsonl")
    masked_result = analyze(masked_rows, blocks, n=_N, m=_M,
                            references=_REFS, bootstrap_seed_value=1234,
                            n_resamples=400, masked=True)
    checks["masked_analysis_ok"] = masked_result["status"] == "OK"
    true_rows = unmask(masked_rows, root / "analysis" / "mask_key.json",
                       root)
    unmasked_result = analyze(true_rows, blocks, n=_N, m=_M,
                              references=_REFS, bootstrap_seed_value=1234,
                              n_resamples=400, masked=False)
    checks["unmasked_analysis_ok"] = unmasked_result["status"] == "OK"

    # fail-closed spot check: a missing cell must yield the named status.
    broken = analyze(accepted[:-1], blocks, n=_N, m=_M, references=_REFS,
                     bootstrap_seed_value=1, n_resamples=50, masked=True)
    checks["missing_cell_fails_closed"] = (
        broken["status"] == "INCONCLUSIVE_INCOMPLETE_MATRIX")

    report = {"passed": all(v is True for v in checks.values()),
              "checks": checks, "blocks": len(blocks),
              "pool_members": len(rows), "mask": mask_info}
    write_json(root / "smoke_report.json", report)
    return report
