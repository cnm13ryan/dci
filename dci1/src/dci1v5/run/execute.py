"""Plan -> generate -> score -> row, for one v5 stage on one model.

The generation seam is ``dci1v4.generation.backend``, carried unchanged: it
is protocol-neutral, every screen in this programme has used it, and a second
copy of the ROCm handling would buy nothing scientific.

Everything above the seam is v5's: §8.5's prompt template, §14.2's seeds,
§9.1's presence rule and §10.6's binding, which is **re-verified** here rather
than trusted --- a row is written with the verifier hash that scored it, and a
hash that moved while the stage was running fails the stage closed rather than
producing rows nobody can place.

**What differs from v4r4's execute, and why.**

* A cell is a **slot** plan, not a constraint list. v5's ``design/cells.py``
  builds cells over registered slots and the slot -> instance map lives on a
  per-model gate record, so the prompt is rendered here from the two together.
  That is what makes the arm-derived design executable: a cell type exists
  because an arm was admitted, and its constituents exist because a gate bound
  them.
* ``absent`` is computed **per cell** from §9.1's presence rule rather than
  passed only for load-0. v4r4 attached chance verdicts to the unconstrained
  cell alone, which is why kappa(R|B) --- a verdict for an absent R on a
  **B-solo** cell --- did not exist in its records and §13.6 had no input. In
  v5 every registered instance the replication uses is scored on every row
  where it was not stated.
* Every row carries its ``slot``, its ``configuration`` and its
  ``topic_split``, so nothing downstream has to re-derive which arm, which
  position or which calibration half produced it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import get_model

from dci1v5 import CLASSIFICATION, STUDY_ID
from dci1v5.design.prompts import assert_stem_present, prompt_hash, render
from dci1v5.protocol import constants as C
from dci1v5.protocol.seeds import generation_seed
from dci1v5.protocol.wordings import wording
from dci1v5.verifiers import verifier_source_hash
from dci1v5.verifiers.compliance import assert_presence_rule, score_generation
from dci1v5.verifiers.constraints import Constraint

__all__ = ["PromptCell", "prompt_cell", "absent_for", "design_rows",
           "generate_and_score", "cell_rates", "instance_rates",
           "per_topic_compliance", "fake_backend", "assert_no_outcome_read"]


@dataclass(frozen=True)
class PromptCell:
    """One prompt identity: a topic, an ordered constraint list, a wording."""

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

    @property
    def load(self) -> int:
        return len(self.present)

    def configuration_of(self, slot: str) -> str | None:
        if self.load != 2 or slot not in self.slots:
            return None
        return (C.OUTCOME_FIRST if self.slots[0] == slot
                else C.OUTCOME_SECOND)


def prompt_cell(cell: Any, topic: Mapping[str, Any], *,
                slot_map: Mapping[str, Constraint],
                topic_split: str) -> PromptCell:
    """Render one design cell into a prompt.

    ``cell`` is a ``design.cells.Cell``: it names slots, not instances.
    ``slot_map`` is the per-model binding a gate record wrote. A slot the map
    does not bind is a refusal here and not a silently dropped constituent ---
    a cell that quietly loses a constituent is a different experimental
    condition under the same label.
    """
    missing = [s for s in cell.slots if s not in slot_map]
    if missing:
        raise ProtocolError(
            f"{cell.cell_id}: slot(s) {missing} are not bound by this "
            "replication's slot map; a cell may not be rendered with a "
            "constituent the design did not admit")
    present = tuple(slot_map[s] for s in cell.slots)
    indices = tuple(cell.wording_by_slot[s] for s in cell.slots)
    lines = [wording(c.kind, i, c.severity)
             for c, i in zip(present, indices)]
    prompt = render(topic["question"], lines)
    assert_stem_present(prompt)
    return PromptCell(
        cell_id=cell.cell_id, arm=cell.arm, block_id=cell.block_id,
        topic_id=topic["topic_id"], area=topic["area"],
        topic_split=topic_split, prompt=prompt, prompt_hash=prompt_hash(prompt),
        slots=tuple(cell.slots), present=present, wording_indices=indices,
        draws=cell.draws)


def absent_for(cell: PromptCell, instances: Sequence[Constraint]
               ) -> tuple[Constraint, ...]:
    """§9.1: every registered instance this replication uses that this cell
    did **not** state.

    This is where kappa(R|B) comes from and it costs nothing: the B-solo cell
    already exists, its responses already exist, and scoring R on them is a
    verdict for an instance the prompt did not state. §13.6 registers that as
    its only use, and ``stages/interaction.assert_kappa_under_b_source``
    refuses every other reading of the same numbers.
    """
    stated = {c.label for c in cell.present}
    return tuple(c for c in instances if c.label not in stated)


def design_rows(cells: Sequence[PromptCell], *, stage: str, model_id: str
                ) -> list[dict[str, Any]]:
    """One row per (cell, draw). All draws are kept; none is selected."""
    rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(cell.draws):
            rows.append({
                "cell_id": cell.cell_id, "block_id": cell.block_id,
                "draw_index": draw,
                "row_id": f"{cell.block_id}:{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash,
                "scientific_seed": generation_seed(stage, model_id,
                                                   cell.prompt_hash, draw),
                "user_prompt": cell.prompt})
    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ProtocolError(
            f"{stage}: the row plan repeats a row identity; every "
            "(block, cell, draw) is generated exactly once (§14.2)")
    return rows


def _reusable_rows(run_dir: Path, wanted: Sequence[Mapping[str, Any]]
                   ) -> list[dict[str, Any]] | None:
    """The rows an interrupted run already produced, or None.

    §26 wants a restart to be cheap and a *silent* restart to be impossible.
    A previous run's rows are reused only when the design it was given is the
    one this call would give --- same row identities, same prompt hashes, same
    scientific seeds, same count, same order. Anything else and the generation
    is redone, because a partial match is how a study ends up with two
    experimental conditions under one label.

    Reuse is safe across a verifier change and unsafe across a prompt or seed
    change, which is exactly the distinction this draws: generation depends on
    the prompt and the seed, and scoring is redone here from the text every
    time.
    """
    design_path, rows_path = run_dir / "design.jsonl", run_dir / "rows.jsonl"
    if not (design_path.exists() and rows_path.exists()):
        return None
    previous = [json.loads(line) for line in
                design_path.read_text().splitlines() if line.strip()]
    if len(previous) != len(wanted):
        return None
    for old, new in zip(previous, wanted):
        if (old.get("row_id"), old.get("prompt_hash"),
                old.get("scientific_seed")) != (
                new["row_id"], new["prompt_hash"], new["scientific_seed"]):
            return None
    produced = [json.loads(line) for line in
                rows_path.read_text().splitlines() if line.strip()]
    by_id = {row.get("row_id"): row for row in produced}
    if set(by_id) != {row["row_id"] for row in wanted}:
        return None
    return [by_id[row["row_id"]] for row in wanted]


def fake_backend(responder: Callable[[Mapping[str, Any]], str]
                 ) -> Callable[..., dict[str, Any]]:
    """A deterministic stand-in for the GPU seam (§T14 / §19).

    The only substitution point in the generative path. Rows it produces carry
    ``synthetic: true`` and ``model_id`` from the registry, and **no v5
    analysis reads a synthetic row**: ``engine/guards.py`` admits positively
    and the synthetic study id is a different namespace with a different
    signing key and a different evidence root.
    """
    def _generate(run_dir: Path, plan: Mapping[str, Any],
                  rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        out = []
        for row in rows:
            text = responder(row)
            out.append({"row_id": row["row_id"], "final_answer": text,
                        "answer_truncated": False,
                        "finish_reason": "stop",
                        "total_generated_tokens": len(text.split())})
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "design.jsonl").write_text(
            "".join(json.dumps(dict(r), sort_keys=True) + "\n" for r in rows))
        (run_dir / "rows.jsonl").write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in out))
        return {"rows": out, "provenance": {"synthetic": True,
                                            "plan": dict(plan)}}
    return _generate


def generate_and_score(model_key: str, cells: Sequence[PromptCell], *,
                       stage: str, cap: int, device: int, run_dir: Path,
                       instances: Sequence[Constraint] = (),
                       slot_map: Mapping[str, Constraint] | None = None,
                       study_id: str = STUDY_ID,
                       limit: int | None = None,
                       generate: Callable[..., dict[str, Any]] | None = None
                       ) -> list[dict[str, Any]]:
    """Run one backend pass and score every row with the v5 primitive.

    ``instances`` is the replication's whole registered instance set. Every
    one of them is scored on every row: present where the prompt stated it,
    absent everywhere else. §9.1's rule is then *asserted* per row rather than
    assumed, so a row whose presence flags disagree with its prompt fails at
    the point of production.

    ``slot_map`` is the replication's slot binding, and it is what a score's
    ``slot`` is read from. **An absent verdict has a slot too**: the slot the
    instance occupies in this replication, which is exactly what §13.6 reads
    kappa(R|B) by. An earlier revision labelled a score from the *cell's*
    constituents alone, so every absent verdict was written ``slot: null`` ---
    and ``ObservationTable`` indexes absent verdicts by
    ``(block, cell, slot)``, so all of a cell's absent verdicts collapsed onto
    one key and the table refused the row set as duplicated. Nothing had built
    a table from scored rows before, so it had never been seen.
    """
    spec = get_model(model_key)
    frozen_hash = verifier_source_hash()
    rows = design_rows(cells, stage=stage, model_id=spec.model_id)
    if limit:
        rows = rows[:limit]
    plan = build_plan(spec, stage=stage, max_new_tokens=cap)
    plan["chunk_size"] = 64
    reused = _reusable_rows(run_dir, rows)
    if reused is not None:
        outcome: dict[str, Any] = {"rows": reused,
                                   "provenance": {"resumed": True}}
    elif generate is None:
        outcome = run_backend(run_dir, plan, rows, device=device,
                              timeout_seconds=60 * 60 * 12)
    else:
        outcome = generate(run_dir, plan, rows)
    if verifier_source_hash() != frozen_hash:
        raise ProtocolError(
            "§10.6: the canonical verifier hash moved while the stage was "
            "running; the rows just generated cannot be placed and the stage "
            "fails closed")

    by_cell = {c.cell_id + "|" + c.block_id: c for c in cells}
    # Every registered instance's slot, from the replication's binding. A
    # cell's own constituents agree with it by construction --- cells are
    # built *from* the slot map --- so this is the same label for a present
    # verdict and a defined one for an absent verdict.
    slot_of_instance = {c.label: slot for slot, c in (slot_map or {}).items()}
    scored_rows: list[dict[str, Any]] = []
    for raw, row in zip(outcome["rows"], rows):
        cell = by_cell[row["cell_id"] + "|" + row["block_id"]]
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
                             where=f"{stage}:{row['row_id']}")
        slot_of = dict(slot_of_instance)
        slot_of.update({c.label: s for s, c in zip(cell.slots, cell.present)})
        scored_rows.append({
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
            "model_key": model_key, "model_id": spec.model_id,
            "model_revision": spec.revision, "study_id": study_id,
            "classification": CLASSIFICATION, "stage": stage,
            "synthetic": generate is not None,
            "resumed": reused is not None,
            "verifier_hash": frozen_hash,
            "scores": [
                {"kind": s.kind, "severity": s.severity,
                 # Never null. A score with no slot cannot be indexed, and
                 # `ObservationTable` keys both the §25 chance cell and every
                 # §9.1 absent verdict by slot -- so a null collapsed all of
                 # a cell's verdicts onto one key. An instance the slot map
                 # does not bind falls back to its own label, which is unique
                 # among registered instances by construction.
                 "slot": slot_of.get(f"{s.kind}:{s.severity}",
                                     f"{s.kind}:{s.severity}"),
                 "statistic": s.statistic, "passed": s.passed,
                 "graded": s.graded, "non_vacuous": s.non_vacuous,
                 "vacuous_pass": s.vacuous_pass, "present": s.present,
                 "position": s.position,
                 "configuration": (
                     cell.configuration_of(
                         slot_of.get(f"{s.kind}:{s.severity}", ""))
                     if s.present else None),
                 "processing_failure": s.processing_failure}
                for s in scores.scores],
        })
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "scored.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in scored_rows))
    return scored_rows


def assert_no_outcome_read(rows: Iterable[Mapping[str, Any]], *,
                           where: str) -> None:
    """§13.11 at the generative boundary: a generation stage never inspects a
    composed outcome to decide what to generate next.

    The rule is enforced structurally --- the plan is built before the first
    row exists and is not rebuilt --- and this is the check that says so where
    a future edit would break it. It refuses a row set that carries a
    composed verdict *and* is being used to build a plan.
    """
    composed = [r for r in rows if r.get("load") == 2]
    if composed:
        raise ProtocolError(
            f"{where}: {len(composed)} composed row(s) reached a planning "
            "path. §13.11 forbids observe B+R -> choose R, and the plan for "
            "every stage is built from the design and the slot map alone")


def cell_rates(rows: Iterable[Mapping[str, Any]], *, kind: str, severity: int,
               present: bool, split: str | None = None) -> dict[str, float]:
    """Topic-mean compliance, vacuity and length for one constraint instance.

    The topic is the unit: draws average within a topic first, then topics
    average, so a topic contributes once however many draws it carry. ``split``
    restricts to one calibration half, which is what §13.7 needs and what
    v4r4 had no way to ask for.
    """
    per_topic: dict[str, list[dict[str, Any]]] = {}
    label = f"{kind}:{severity}"
    for row in rows:
        if split is not None and row.get("topic_split") != split:
            continue
        for score in row["scores"]:
            if (f"{score['kind']}:{score['severity']}" == label
                    and bool(score["present"]) == present):
                per_topic.setdefault(row["topic_id"], []).append(
                    {"passed": score["passed"],
                     "vacuous_pass": score["vacuous_pass"],
                     "graded": score["graded"],
                     "words": row["word_count"],
                     "truncated": row["truncated"]})
    if not per_topic:
        raise ProtocolError(
            f"no rows for {label} (present={present}, split={split})")

    def _mean(values):
        return sum(values) / len(values)

    topics = sorted(per_topic)
    compliance = _mean([_mean([float(o["passed"]) for o in per_topic[t]])
                        for t in topics])
    vacuity = _mean([_mean([float(o["vacuous_pass"]) for o in per_topic[t]])
                     for t in topics])
    graded = _mean([_mean([float(o["graded"]) for o in per_topic[t]])
                    for t in topics])
    truncation = _mean([_mean([float(o["truncated"]) for o in per_topic[t]])
                        for t in topics])
    words = sorted(o["words"] for t in topics for o in per_topic[t])
    return {"compliance": compliance, "vacuity": vacuity,
            "graded_mean": graded, "truncation": truncation,
            "median_words": float(words[len(words) // 2]),
            "n_topics": len(topics),
            "n_observations": sum(len(per_topic[t]) for t in topics)}


def per_topic_compliance(rows: Iterable[Mapping[str, Any]], *, kind: str,
                         severity: int, present: bool = True,
                         split: str | None = None) -> tuple[float, ...]:
    """One value per topic: the mean over that topic's draws, topics sorted.

    §13.7's equivalence test resamples **topics**, so it needs the per-topic
    vector and not the mean. ``CalibrationRow.per_topic_solo`` is where it
    reads it, and a row that carries an empty vector makes the test report
    that it could not be run --- which is not the same as passing it. This is
    the function that fills it.
    """
    per_topic: dict[str, list[float]] = {}
    label = f"{kind}:{severity}"
    for row in rows:
        if split is not None and row.get("topic_split") != split:
            continue
        for score in row["scores"]:
            if (f"{score['kind']}:{score['severity']}" == label
                    and bool(score["present"]) == present):
                per_topic.setdefault(row["topic_id"], []).append(
                    float(score["passed"]))
    return tuple(sum(v) / len(v)
                 for _, v in sorted(per_topic.items()))


def instance_rates(rows: Sequence[Mapping[str, Any]], *, kind: str,
                   severity: int, split: str | None = None) -> dict[str, float]:
    """Solo and chance for one instance, in §12.2's vocabulary."""
    rows = list(rows)
    solo = cell_rates(rows, kind=kind, severity=severity, present=True,
                      split=split)
    chance = cell_rates(rows, kind=kind, severity=severity, present=False,
                        split=split)
    return {"solo": solo["compliance"], "chance": chance["compliance"],
            "vacuity": solo["vacuity"], "chance_vacuity": chance["vacuity"],
            "graded_mean": solo["graded_mean"],
            "median_words": solo["median_words"],
            "truncation": solo["truncation"],
            "n_topics": solo["n_topics"],
            "split": split}
