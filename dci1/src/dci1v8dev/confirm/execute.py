"""Plan -> generate -> score -> row for a confirmatory stage.

``dci1v8dev.run.execute`` with the composed-cell refusal replaced by the
freeze check: the v8 instrument (``dci1v8dev.wordings``), the v8 seeds,
the v8 verifier and the same generative seam and reuse rule. A composed
cell is rendered here and nowhere else in v8, and ``prompt_cell`` asserts
that both of its lines are under the block's frame (Approach A).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import get_model
from dci1v4.protocol.hashing import sha_obj
from dci1v7.design.prompts import assert_stem_present, prompt_hash, render
from dci1v7.engine import parallel
from dci1v7.protocol import constants as C
from dci1v7.run.execute import (_reusable_rows, absent_for, decoding_identity,
                                fake_backend, observation_identity)
from dci1v7.verifiers.constraints import Constraint

from dci1v8dev.confirm import CLASSIFICATION
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.design import Cell
from dci1v8dev.run.execute import (PromptCell, assert_v8_prompt,
                                   reusable_rows_checked,
                                   row_accounting)
from dci1v8dev.run.seeds import generation_seed
from dci1v8dev.verifiers import verifier_source_hash
from dci1v8dev.verifiers.compliance import assert_presence_rule, score_generation
from dci1v8dev.wordings import v8_wording, v8_wording_source_hash

__all__ = ["prompt_cell", "design_rows", "generate_and_score",
           "resolve_generate", "row_accounting", "fake_backend"]


def prompt_cell(cell: Cell, topic: Mapping[str, Any], *,
                slot_map: Mapping[str, Constraint],
                topic_split: str = "confirmatory") -> PromptCell:
    """Render one cell (load 0, 1 or 2) under the block's frame."""
    missing = [s for s in cell.slots if s not in slot_map]
    if missing:
        raise ProtocolError(f"{cell.cell_id}: slot(s) {missing} are not bound "
                            "by the frozen slot map")
    present = tuple(slot_map[s] for s in cell.slots)
    indices = tuple(cell.wording_by_slot[s] for s in cell.slots)
    frame = cell.block_index % C.N_WORDINGS
    if cell.frame != frame or any(i != frame for i in indices):
        raise ProtocolError(
            f"{cell.cell_id}@{cell.block_id}: every stated line is rendered "
            f"under the block's frame {frame} (Approach A); got "
            f"{indices} / cell frame {cell.frame}")
    lines = [v8_wording(c.kind, i, c.severity) for c, i in zip(present, indices)]
    prompt = render(topic["question"], lines)
    assert_stem_present(prompt)
    assert_v8_prompt(prompt, present)
    return PromptCell(
        cell_id=cell.cell_id, arm=cell.arm, block_id=cell.block_id,
        topic_id=topic["topic_id"], area=topic["area"],
        topic_split=topic_split, prompt=prompt, prompt_hash=prompt_hash(prompt),
        slots=tuple(cell.slots), present=present, wording_indices=indices,
        draws=cell.draws, block_index=cell.block_index)


def _generation_identity(cell: PromptCell, *, draw: int, stage: str,
                         study_id: str, protocol_identity: Mapping[str, Any],
                         decoding: Mapping[str, Any], seed: int,
                         wording_hash: str) -> str:
    return sha_obj({
        "study_id": study_id, "layer": "confirm",
        "protocol_identity": dict(protocol_identity), "stage": stage,
        "decoding": dict(decoding), "wording_hash": wording_hash,
        "topic_id": cell.topic_id, "topic_split": cell.topic_split,
        "block_id": cell.block_id, "cell_id": cell.cell_id, "arm": cell.arm,
        "slots": list(cell.slots),
        "constituents": [[c.kind, c.severity] for c in cell.present],
        "wording_indices": list(cell.wording_indices),
        "prompt_hash": cell.prompt_hash, "draw_index": draw,
        "scientific_seed": seed})


def design_rows(cells: Sequence[PromptCell], *, stage: str, model_id: str,
                study_id: str, protocol_identity: Mapping[str, Any],
                decoding: Mapping[str, Any]) -> list[dict[str, Any]]:
    wording_hash = v8_wording_source_hash()
    rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(cell.draws):
            seed = generation_seed(stage, model_id, cell.prompt_hash, draw)
            rows.append({
                "cell_id": cell.cell_id, "block_id": cell.block_id,
                "draw_index": draw,
                "row_id": f"{cell.block_id}:{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash, "topic_id": cell.topic_id,
                "topic_split": cell.topic_split, "scientific_seed": seed,
                "generation_identity": _generation_identity(
                    cell, draw=draw, stage=stage, study_id=study_id,
                    protocol_identity=protocol_identity, decoding=decoding,
                    seed=seed, wording_hash=wording_hash),
                "user_prompt": cell.prompt})
    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ProtocolError(f"{stage}: the row plan repeats a row identity")
    return rows


def resolve_generate(tree: L.ConfirmTree,
                     generate: Callable[..., dict[str, Any]] | None, *,
                     where: str) -> Callable[..., dict[str, Any]] | None:
    if not tree.synthetic:
        if generate is not None:
            raise ProtocolError(
                f"{where}: a generation callable was passed in the "
                f"{tree.context.namespace!r} namespace; the seam is the "
                "pinned backend")
        return None
    if generate is None:
        raise ProtocolError(f"{where}: the confirm-synthetic namespace needs "
                            "a stand-in generator")
    return generate


def generate_and_score(model_key: str, cells: Sequence[PromptCell], *,
                       stage: str, cap: int, device: int, run_dir: Path,
                       instances: Sequence[Constraint],
                       slot_map: Mapping[str, Constraint], study_id: str,
                       protocol_identity: Mapping[str, Any],
                       generate: Callable[..., dict[str, Any]] | None = None,
                       composed_licensed: bool = False) -> list[dict[str, Any]]:
    """One backend pass; every row scored on every instance in use."""
    if stage not in L.GENERATION_STAGES:
        raise ProtocolError(f"{stage} is not a generating confirmatory stage")
    if any(c.load > 1 for c in cells) and not composed_licensed:
        raise ProtocolError(
            f"{stage}: a composed cell reached the generator without a "
            "verified freeze licence (confirm.generation licenses it)")
    if stage != L.STAGE_GENERATION and any(c.load > 1 for c in cells):
        raise ProtocolError(f"{stage} renders load-0 and load-1 cells only")
    spec = get_model(model_key)
    frozen = {"verifier_hash": verifier_source_hash(),
              "wording_hash": v8_wording_source_hash()}
    plan = build_plan(spec, stage=stage, max_new_tokens=cap)
    plan["chunk_size"] = 64
    decoding = decoding_identity(plan)
    rows = design_rows(cells, stage=stage, model_id=spec.model_id,
                       study_id=study_id, protocol_identity=protocol_identity,
                       decoding=decoding)
    reused, reuse = reusable_rows_checked(run_dir, rows)
    if reused is not None:
        outcome: dict[str, Any] = {"rows": reused,
                                   "provenance": {"resumed": True,
                                                  "reuse": dict(reuse)}}
    elif generate is None:
        outcome = run_backend(run_dir, plan, rows, device=device,
                              timeout_seconds=60 * 60 * 12)
    else:
        outcome = generate(run_dir, plan, rows)
    if {"verifier_hash": verifier_source_hash(),
            "wording_hash": v8_wording_source_hash()} != frozen:
        raise ProtocolError("the v8 verifier or wording hash moved while the "
                            "stage was running")
    synthetic_run = bool(outcome.get("provenance", {}).get("synthetic"))
    by_cell = {c.cell_id + "|" + c.block_id: c for c in cells}
    slot_of_instance = {c.label: slot for slot, c in slot_map.items()}
    n_rows = min(len(outcome["rows"]), len(rows))
    tasks = [(outcome["rows"][i], rows[i],
              by_cell[rows[i]["cell_id"] + "|" + rows[i]["block_id"]])
             for i in range(n_rows)]
    scored_rows: list[dict[str, Any]] = parallel.pool_map(
        _score_row, tasks,
        shared={"instances": tuple(instances),
                "slot_of_instance": slot_of_instance,
                "model_key": model_key, "model_id": spec.model_id,
                "model_revision": spec.revision, "study_id": study_id,
                "stage": stage, "synthetic_run": synthetic_run,
                "resumed": reused is not None, "run": Path(run_dir).name,
                **frozen})
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "scored.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in scored_rows))
    accounting = row_accounting(run_dir)
    if not accounting["every_row_scored"]:
        raise ProtocolError(
            f"{stage}/{Path(run_dir).name}: {accounting['n_design']} planned, "
            f"{accounting['n_generated']} generated, "
            f"{accounting['n_scored']} scored; every generated row is data")
    return scored_rows


def _score_row(task: tuple[Mapping[str, Any], Mapping[str, Any], PromptCell]
               ) -> dict[str, Any]:
    raw, row, cell = task
    st = parallel.shared()
    instances, frozen_hash = st["instances"], st["verifier_hash"]
    text = raw.get("final_answer") or ""
    truncated = bool(raw.get("answer_truncated"))
    absent = absent_for(cell, instances)
    scores = score_generation(
        text, present=cell.present, absent=absent, truncated=truncated,
        finish_reason=raw.get("finish_reason"),
        token_count=raw.get("total_generated_tokens"))
    assert_presence_rule(scores, stated=cell.present,
                         instances_in_use=list(instances) or list(cell.present),
                         where=f"{st['stage']}:{row['row_id']}")
    slot_of = dict(st["slot_of_instance"])
    slot_of.update({c.label: s for s, c in zip(cell.slots, cell.present)})
    return {
        "row_id": row["row_id"], "cell_id": cell.cell_id,
        "block_id": cell.block_id, "draw_index": row["draw_index"],
        "arm": cell.arm, "slots": list(cell.slots),
        "topic_id": cell.topic_id, "area": cell.area,
        "topic_split": cell.topic_split, "load": cell.load,
        "wording_indices": list(cell.wording_indices),
        "prompt_hash": cell.prompt_hash, "seed": row["scientific_seed"],
        "raw_response": text, "finish_reason": raw.get("finish_reason"),
        "token_count": raw.get("total_generated_tokens"),
        "truncated": truncated, "empty": scores.empty,
        "word_count": scores.word_count, "in_stem_band": scores.in_stem_band,
        "model_key": st["model_key"], "model_id": st["model_id"],
        "model_revision": st["model_revision"], "study_id": st["study_id"],
        "classification": CLASSIFICATION, "layer": "confirm",
        "stage": st["stage"], "run": st["run"],
        "frame": int(cell.block_frame), "block_index": int(cell.block_index),
        "block_frame": int(cell.block_frame),
        "synthetic": bool(raw.get("synthetic")) or st["synthetic_run"],
        "resumed": st["resumed"], "verifier_hash": frozen_hash,
        "wording_hash": st["wording_hash"],
        "generation_identity": row["generation_identity"],
        "observation_identity": observation_identity(
            row["generation_identity"], verifier_hash=frozen_hash,
            instances=list(instances) or list(cell.present)),
        "scores": [
            {"kind": s.kind, "severity": s.severity,
             "slot": slot_of.get(f"{s.kind}:{s.severity}",
                                 f"{s.kind}:{s.severity}"),
             "statistic": s.statistic, "passed": s.passed,
             "graded": s.graded, "non_vacuous": s.non_vacuous,
             "vacuous_pass": s.vacuous_pass, "present": s.present,
             "position": s.position, "configuration": None,
             "processing_failure": s.processing_failure}
            for s in scores.scores],
    }
