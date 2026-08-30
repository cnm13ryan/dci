"""Plan -> generate -> score -> row, for one pilot stage on one model.

v7's ``run/execute`` with every identity replaced by v8's and nothing else
changed: the generative seam (``dci1v4.generation.backend``) and the reuse
rule are the same; the prompt is rendered from ``dci1v8dev.wordings`` (the
v8 instrument); the seed comes from ``dci1v8dev.run.seeds`` (the ``dci1v8``
domain); the rows are scored by ``dci1v8dev.verifiers.compliance`` and carry
the v8 verifier hash, the v8 wording hash, the v8 classification and the
tree's study id. The row-statistics kernels ``cell_rates``,
``instance_rates`` and ``per_topic_compliance`` are v7's, imported: they are
functions of scored rows and carry no identity.

**No composed cell.** ``prompt_cell`` refuses a cell with two slots. The
pilot has no stage that builds one, and this is the assertion that keeps a
future stage from doing so quietly (``stages.NO_COMPOSED_CELLS``).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import get_model
from dci1v4.protocol.hashing import sha_obj
from dci1v7.design.prompts import assert_stem_present, prompt_hash, render
from dci1v7.engine import parallel
from dci1v7.protocol import constants as C
from dci1v7.run.execute import (
    DECODING_IDENTITY_FIELDS, _reusable_rows, absent_for, cell_rates,
    decoding_identity, fake_backend, instance_rates, observation_identity,
    per_topic_compliance,
)
from dci1v7.verifiers.constraints import MARKER_WORDS, FAMILIES, Constraint
from dci1v7.verifiers.constraints import TIER1_FAMILY_IDS

from dci1v8dev.run import CLASSIFICATION
from dci1v8dev.run import stages as S
from dci1v8dev.run.seeds import generation_seed
from dci1v8dev.verifiers import verifier_source_hash
from dci1v8dev.verifiers.compliance import assert_presence_rule, score_generation
from dci1v8dev.wording_v8 import TARGET
from dci1v8dev.wordings import v8_wording, v8_wording_source_hash

__all__ = ["PromptCell", "Block", "SoloCell", "blocks", "prompt_cell",
           "design_rows", "generate_and_score", "resolve_generate",
           "fake_backend", "cell_rates", "instance_rates",
           "per_topic_compliance", "absent_for", "frame_of_row",
           "frame_of_block", "rows_of_frame",
           "marker_of", "assert_v8_prompt", "assert_no_composed_cell",
           "row_accounting", "UNCONSTRAINED_ARM",
           "DECODING_IDENTITY_FIELDS", "decoding_identity"]

UNCONSTRAINED_ARM = "unconstrained"


class Block:
    __slots__ = ("block_id", "index", "topic_id")

    def __init__(self, block_id: str, index: int, topic_id: str):
        self.block_id, self.index, self.topic_id = block_id, index, topic_id


class SoloCell:
    """A load-0 or load-1 cell over an explicit slot; the only cell shape the
    pilot renders. ``wording_index`` defaults to §8.4's allocation by block
    (``block.index % N_WORDINGS``), so every frame meets every topic
    position equally often across the twenty-four screen topics."""

    __slots__ = ("cell_id", "arm", "block_id", "block_index", "topic_id",
                 "slots", "wording_by_slot", "draws")

    def __init__(self, *, cell_id: str, arm: str, block: Block,
                 slot: str | None, draws: int,
                 wording_index: int | None = None):
        self.cell_id = cell_id
        self.arm = arm
        self.block_id = block.block_id
        self.block_index = block.index
        self.topic_id = block.topic_id
        self.slots = (slot,) if slot else ()
        index = (block.index % C.N_WORDINGS if wording_index is None
                 else wording_index)
        self.wording_by_slot = {slot: index} if slot else {}
        self.draws = draws


def blocks(topics: Sequence[Mapping[str, Any]], prefix: str, *,
           index_base: int = 0) -> list[Block]:
    """The blocks of one pass over ``topics``, numbered from ``index_base``.

    The block index is the *only* thing that decides the frame
    (``block.index % N_WORDINGS``, §8.4). ``index_base`` therefore does two
    things at once and both are load-bearing: it keeps a second pass over
    the same topics on block ids and row identities disjoint from the
    first's, and --- because the caller chooses a base congruent to the
    frame offset it wants --- it puts that pass's topics under a different
    frame. See ``calibration.calibration_blocks``.
    """
    return [Block(f"{prefix}-{index_base + i:03d}", index_base + i,
                  t["topic_id"])
            for i, t in enumerate(topics)]


@dataclass(frozen=True)
class PromptCell:
    cell_id: str
    arm: str
    block_id: str
    topic_id: str
    area: str
    topic_split: str
    prompt: str
    prompt_hash: str
    slots: tuple[str, ...]
    present: tuple[Constraint, ...]
    wording_indices: tuple[int, ...]
    draws: int
    #: The block's position, from which its frame follows
    #: (``block_index % N_WORDINGS``); carried on every row, load 0 included,
    #: so a frame's unconstrained cells can be read (§13.2 per frame).
    block_index: int = 0

    @property
    def load(self) -> int:
        return len(self.present)

    @property
    def block_frame(self) -> int:
        return self.block_index % C.N_WORDINGS

    def configuration_of(self, slot: str) -> str | None:
        return None                       # no composed cell, ever


def marker_of(kind: str) -> str | None:
    """The marker word an exact-count marker family (or A) names."""
    if kind == "A":
        return TARGET
    if kind in TIER1_FAMILY_IDS:
        return MARKER_WORDS[FAMILIES[kind].statistic_id]
    return None


def assert_v8_prompt(prompt: str, present: Sequence[Constraint]) -> None:
    """Every stated A/MK line names its target as ``the word X`` (the v8
    frames' one guarantee), asserted on the rendered bytes."""
    for c in present:
        marker = marker_of(c.kind)
        if marker is None:
            continue
        if f"the word {marker}" not in prompt.lower():
            raise ProtocolError(
                f"{c.label}: the rendered prompt does not name 'the word "
                f"{marker}'; the v8 instrument was not applied")


def assert_no_composed_cell(cells: Sequence[Any], *, where: str) -> None:
    """The hard block, at every seam a cell passes: a cell with two slots or
    two present constituents is refused before it is rendered, planned or
    generated. No stage of this layer builds one; a future one could not
    get it past here."""
    for cell in cells:
        slots = getattr(cell, "slots", ())
        present = getattr(cell, "present", ())
        if len(slots) > 1 or len(present) > 1:
            raise ProtocolError(
                f"{where}: a composed cell ({getattr(cell, 'cell_id', '?')}, "
                f"{len(slots)} slots) reached the pilot; the pilot generates "
                "load 0 and load 1 only and no composed cell exists before "
                "the v8 design and wording policy are frozen "
                "(stages.NO_COMPOSED_CELLS)")


def prompt_cell(cell: Any, topic: Mapping[str, Any], *,
                slot_map: Mapping[str, Constraint],
                topic_split: str) -> PromptCell:
    """Render one cell into a prompt under the v8 wording instrument."""
    assert_no_composed_cell([cell], where="prompt_cell")
    missing = [s for s in cell.slots if s not in slot_map]
    if missing:
        raise ProtocolError(
            f"{cell.cell_id}: slot(s) {missing} are not bound by this "
            "replication's slot map")
    present = tuple(slot_map[s] for s in cell.slots)
    indices = tuple(cell.wording_by_slot[s] for s in cell.slots)
    block_index = int(cell.block_index)
    # Approach A: the frame is the block's, on every constraint the block
    # states; a slot rendered under another frame would put a row in a
    # condition its block is not in.
    for slot, index in zip(cell.slots, indices):
        if index != block_index % C.N_WORDINGS:
            raise ProtocolError(
                f"{cell.cell_id}: slot {slot} is rendered under frame {index} "
                f"and its block {cell.block_id} carries frame "
                f"{block_index % C.N_WORDINGS}; the frame is a property of "
                "the block (docs/V8_FRAME_CONDITIONING.md)")
    lines = [v8_wording(c.kind, i, c.severity)
             for c, i in zip(present, indices)]
    prompt = render(topic["question"], lines)
    assert_stem_present(prompt)
    assert_v8_prompt(prompt, present)
    return PromptCell(
        cell_id=cell.cell_id, arm=cell.arm, block_id=cell.block_id,
        topic_id=topic["topic_id"], area=topic["area"],
        topic_split=topic_split, prompt=prompt,
        prompt_hash=prompt_hash(prompt), slots=tuple(cell.slots),
        present=present, wording_indices=indices, draws=cell.draws,
        block_index=block_index)


def generation_identity(cell: PromptCell, *, draw: int, stage: str,
                        study_id: str, protocol_identity: Mapping[str, Any],
                        decoding: Mapping[str, Any], seed: int,
                        wording_hash: str) -> str:
    """Everything that decides what text a row contains --- v7's key plus
    the v8 wording hash, so a row generated under a different instrument
    is never reused for this one."""
    return sha_obj({
        "study_id": study_id,
        "protocol_identity": dict(protocol_identity),
        "stage": stage,
        "decoding": dict(decoding),
        "wording_hash": wording_hash,
        "topic_id": cell.topic_id,
        "topic_split": cell.topic_split,
        "block_id": cell.block_id,
        "cell_id": cell.cell_id,
        "arm": cell.arm,
        "slots": list(cell.slots),
        "constituents": [[c.kind, c.severity] for c in cell.present],
        "wording_indices": list(cell.wording_indices),
        "prompt_hash": cell.prompt_hash,
        "draw_index": draw,
        "scientific_seed": seed,
    })


def design_rows(cells: Sequence[PromptCell], *, stage: str, model_id: str,
                study_id: str,
                protocol_identity: Mapping[str, Any] | None = None,
                decoding: Mapping[str, Any] | None = None
                ) -> list[dict[str, Any]]:
    """One row per (cell, draw). All draws are kept; none is selected."""
    assert_no_composed_cell(cells, where=f"design_rows:{stage}")
    wording_hash = v8_wording_source_hash()
    rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(cell.draws):
            seed = generation_seed(stage, model_id, cell.prompt_hash, draw)
            rows.append({
                "cell_id": cell.cell_id, "block_id": cell.block_id,
                "draw_index": draw,
                "row_id": f"{cell.block_id}:{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash,
                "topic_id": cell.topic_id,
                "topic_split": cell.topic_split,
                "scientific_seed": seed,
                "generation_identity": generation_identity(
                    cell, draw=draw, stage=stage, study_id=study_id,
                    protocol_identity=protocol_identity or {},
                    decoding=decoding or {}, seed=seed,
                    wording_hash=wording_hash),
                "user_prompt": cell.prompt})
    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ProtocolError(
            f"{stage}: the row plan repeats a row identity")
    keys = [r["generation_identity"] for r in rows]
    if len(set(keys)) != len(keys):
        raise ProtocolError(
            f"{stage}: two planned rows share a generation identity")
    return rows


def resolve_generate(tree: Any, generate: Callable[..., dict[str, Any]] | None,
                     responder: Callable[[Mapping[str, Any]], str], *,
                     where: str) -> Callable[..., dict[str, Any]] | None:
    """The pinned backend in the pilot namespace (a callable is refused);
    a stand-in in the synthetic namespace only."""
    namespace = getattr(getattr(tree, "context", None), "namespace", None)
    if namespace != "synthetic":
        if generate is not None:
            raise ProtocolError(
                f"{where}: a generation callable was passed in the "
                f"{namespace!r} namespace; the generative seam is the pinned "
                "backend and a stand-in is admissible only in the synthetic "
                "namespace")
        return None
    return generate if generate is not None else fake_backend(responder)


def generate_and_score(model_key: str, cells: Sequence[PromptCell], *,
                       stage: str, cap: int, device: int, run_dir: Path,
                       instances: Sequence[Constraint] = (),
                       slot_map: Mapping[str, Constraint] | None = None,
                       study_id: str,
                       protocol_identity: Mapping[str, Any] | None = None,
                       limit: int | None = None,
                       generate: Callable[..., dict[str, Any]] | None = None
                       ) -> list[dict[str, Any]]:
    """One backend pass; every row scored on every registered instance in
    use (present where stated, absent everywhere else --- §9.1)."""
    if stage not in S.GENERATION_STAGES:
        raise ProtocolError(f"{stage} is not a generating pilot stage")
    assert_no_composed_cell(cells, where=f"generate_and_score:{stage}")
    spec = get_model(model_key)
    frozen = {"verifier_hash": verifier_source_hash(),
              "wording_hash": v8_wording_source_hash()}
    plan = build_plan(spec, stage=stage, max_new_tokens=cap)
    plan["chunk_size"] = 64
    decoding = decoding_identity(plan)
    rows = design_rows(cells, stage=stage, model_id=spec.model_id,
                       study_id=study_id,
                       protocol_identity=protocol_identity or {},
                       decoding=decoding)
    if limit:
        rows = rows[:limit]
    reused, reuse = _reusable_rows(run_dir, rows)
    if reused is not None:
        outcome: dict[str, Any] = {"rows": reused,
                                   "provenance": {"resumed": True,
                                                  "reuse": dict(reuse)}}
    elif generate is None:
        outcome = run_backend(run_dir, plan, rows, device=device,
                              timeout_seconds=60 * 60 * 12)
    else:
        outcome = generate(run_dir, plan, rows)
    synthetic_run = bool(outcome.get("provenance", {}).get("synthetic"))
    if {"verifier_hash": verifier_source_hash(),
            "wording_hash": v8_wording_source_hash()} != frozen:
        raise ProtocolError(
            "the v8 verifier or wording hash moved while the stage was "
            "running; the rows just generated cannot be placed")
    by_cell = {c.cell_id + "|" + c.block_id: c for c in cells}
    slot_of_instance = {c.label: slot for slot, c in (slot_map or {}).items()}
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
    # Every planned row was generated and every generated row was scored,
    # compliant or not; asserted here, on the path, and recorded per run.
    accounting = row_accounting(run_dir)
    if not accounting["every_row_scored"]:
        raise ProtocolError(
            f"{stage}/{Path(run_dir).name}: {accounting['n_design']} rows "
            f"planned, {accounting['n_generated']} generated, "
            f"{accounting['n_scored']} scored; every generated row is data "
            "and reaches scoring")
    return scored_rows


def row_accounting(run_dir: Path) -> dict[str, Any]:
    """The audit that no generation was dropped: the planned rows
    (``design.jsonl``), the backend's rows (``rows.jsonl``) and the scored
    rows (``scored.jsonl``) carry the same row identities, and the scored
    rows hold both exact-compliant and non-compliant answers for the stated
    constraint --- the outcome is counted, never filtered on."""
    run_dir = Path(run_dir)

    def _ids(name: str, key: str = "row_id") -> list[str]:
        path = run_dir / name
        if not path.exists():
            return []
        return [json.loads(line)[key] for line in path.read_text().splitlines()
                if line.strip()]

    design = _ids("design.jsonl")
    generated = _ids("rows.jsonl")
    scored_rows = [json.loads(line) for line in
                   (run_dir / "scored.jsonl").read_text().splitlines()
                   if line.strip()] if (run_dir / "scored.jsonl").exists() else []
    scored = [r["row_id"] for r in scored_rows]
    present = [s for r in scored_rows for s in r["scores"] if s.get("present")]
    n_pass = sum(1 for s in present if s.get("passed"))
    return {"run": run_dir.name,
            "n_design": len(design), "n_generated": len(generated),
            "n_scored": len(scored),
            "every_row_scored": bool(design) and set(design) == set(scored)
            and len(set(scored)) == len(scored)
            and (not generated or set(generated) == set(design)),
            "n_present_verdicts": len(present),
            "n_present_exact_compliant": n_pass,
            "n_present_non_compliant": len(present) - n_pass,
            "rule": "every generated row is data; nothing downstream is "
                    "conditioned on exact compliance or uptake"}


def _score_row(task: tuple[Mapping[str, Any], Mapping[str, Any], PromptCell]
               ) -> dict[str, Any]:
    """Score one backend row with the v8 primitive. Pure in its task and the
    pool's shared state; the serial loop body."""
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
                         instances_in_use=list(instances) or
                         list(cell.present),
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
        "word_count": scores.word_count,
        "in_stem_band": scores.in_stem_band,
        "model_key": st["model_key"], "model_id": st["model_id"],
        "model_revision": st["model_revision"], "study_id": st["study_id"],
        "classification": CLASSIFICATION, "stage": st["stage"],
        "run": st["run"],
        "frame": (int(cell.wording_indices[0]) if len(cell.wording_indices) == 1
                  else None),
        "block_index": int(cell.block_index),
        "block_frame": int(cell.block_frame),
        "synthetic": bool(raw.get("synthetic")) or st["synthetic_run"],
        "resumed": st["resumed"],
        "verifier_hash": frozen_hash,
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


def frame_of_row(row: Mapping[str, Any]) -> int | None:
    """The wording index a load-1 row was rendered under."""
    indices = row.get("wording_indices") or []
    return int(indices[0]) if len(indices) == 1 else None


def frame_of_block(row: Mapping[str, Any]) -> int:
    """The frame of the row's block, defined on every load: ``block_frame``
    when the row carries it, else ``block_index % N_WORDINGS``, else the
    index parsed from a ``<prefix>-<index>`` block id (rows scored before
    the field existed). On a load-1 row it equals ``frame_of_row``; the
    two disagreeing is refused."""
    if row.get("block_frame") is not None:
        frame = int(row["block_frame"])
    elif row.get("block_index") is not None:
        frame = int(row["block_index"]) % C.N_WORDINGS
    else:
        block = str(row.get("block_id") or "")
        _, _, tail = block.rpartition("-")
        if not tail.isdigit():
            raise ProtocolError(f"row {row.get('row_id')!r}: no block frame "
                                f"and an unparseable block id {block!r}")
        frame = int(tail) % C.N_WORDINGS
    stated = frame_of_row(row)
    if stated is not None and stated != frame:
        raise ProtocolError(
            f"row {row.get('row_id')!r} was rendered under frame {stated} in "
            f"a block of frame {frame}")
    return frame


def rows_of_frame(rows: Sequence[Mapping[str, Any]], frame: int
                  ) -> list[dict[str, Any]]:
    """Every row --- load 0 and load 1 --- of the blocks rendered under
    ``frame``: the row set a frame-specific quantity is measured on."""
    return [dict(r) for r in rows if frame_of_block(r) == frame]
