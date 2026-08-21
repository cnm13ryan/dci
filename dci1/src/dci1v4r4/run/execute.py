"""Plan -> generate -> score -> record, for one v4r3 stage on one model.

The generation seam is ``dci1v4.generation.backend``, carried unchanged: it
is protocol-neutral, it is the seam every screen in this programme has used,
and re-implementing it would put a second copy of the ROCm handling in the
repository for no scientific gain.

Everything above the seam is v4r3's: the prompt template of §8.5, the seeds of
§14.2, the compliance primitive of §9.1, and the §10.6 binding, which is
re-verified here rather than trusted -- a row is written with the verifier
hash that scored it, and a hash that has moved since the stage began fails the
stage closed rather than producing rows nobody can place.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import get_model

from dci1v4r4 import CLASSIFICATION, EVIDENCE_DIRNAME, STUDY_ID
from dci1v4r4.design.prompts import assert_stem_present, prompt_hash, render
from dci1v4r4.protocol.seeds import generation_seed
from dci1v4r4.protocol.wordings import wording
from dci1v4r4.verifiers import verifier_source_hash
from dci1v4r4.verifiers.compliance import score_generation
from dci1v4r4.verifiers.constraints import Constraint

DCI1 = Path(__file__).resolve().parents[3]
EVIDENCE = DCI1 / "evidence" / EVIDENCE_DIRNAME

__all__ = ["Cell", "EVIDENCE", "solo_cell", "unconstrained_cell",
           "design_rows", "generate_and_score", "cell_rates"]


@dataclass(frozen=True)
class Cell:
    """One prompt identity: a topic, a constraint list, a wording allocation."""

    cell_id: str
    arm: str
    topic_id: str
    area: str
    prompt: str
    prompt_hash: str
    #: the constraints the prompt states, in prompt order
    present: tuple[Constraint, ...]
    wording_indices: tuple[int, ...]

    @property
    def load(self) -> int:
        return len(self.present)


def unconstrained_cell(topic: dict[str, Any], *, arm: str,
                       prefix: str) -> Cell:
    """§25's load-0 cell. It carries the stem and no numbered list."""
    prompt = render(topic["question"], [])
    assert_stem_present(prompt)
    return Cell(cell_id=f"{prefix}:{topic['topic_id']}:load0",
                arm=arm, topic_id=topic["topic_id"], area=topic["area"],
                prompt=prompt, prompt_hash=prompt_hash(prompt),
                present=(), wording_indices=())


def solo_cell(topic: dict[str, Any], constraint: Constraint, index: int, *,
              arm: str, prefix: str) -> Cell:
    """One solo cell at §8.4's block-level wording index."""
    line = wording(constraint.kind, index, constraint.severity)
    prompt = render(topic["question"], [line])
    assert_stem_present(prompt)
    return Cell(cell_id=f"{prefix}:{topic['topic_id']}:{constraint.label}",
                arm=arm, topic_id=topic["topic_id"], area=topic["area"],
                prompt=prompt, prompt_hash=prompt_hash(prompt),
                present=(constraint,), wording_indices=(index,))


def composed_cell(topic: dict[str, Any], first: Constraint, second: Constraint,
                  indices: tuple[int, int], *, arm: str, prefix: str) -> Cell:
    lines = [wording(first.kind, indices[0], first.severity),
             wording(second.kind, indices[1], second.severity)]
    prompt = render(topic["question"], lines)
    assert_stem_present(prompt)
    return Cell(
        cell_id=f"{prefix}:{topic['topic_id']}:{first.label}+{second.label}",
        arm=arm, topic_id=topic["topic_id"], area=topic["area"],
        prompt=prompt, prompt_hash=prompt_hash(prompt),
        present=(first, second), wording_indices=indices)


def _reusable_rows(run_dir: Path, wanted: Sequence[dict[str, Any]]
                   ) -> list[dict[str, Any]] | None:
    """The rows an interrupted run already produced, or None.

    §26 wants a restart to be cheap and a *silent* restart to be impossible.
    A previous run's rows are reused only when the design it was given is the
    one this call would give -- same row identities, same prompt hashes, same
    scientific seeds, same count, in the same order. Anything else and the
    generation is redone, because a partial match is how a study ends up with
    two experimental conditions under one label.

    Reuse is safe across a verifier change and unsafe across a prompt or seed
    change, which is exactly the distinction this check draws: generation
    depends on the prompt and the seed, and scoring is redone here from the
    text every time.
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
    if len(produced) != len(wanted):
        return None
    by_id = {row.get("row_id"): row for row in produced}
    if set(by_id) != {row["row_id"] for row in wanted}:
        return None
    return [by_id[row["row_id"]] for row in wanted]


def design_rows(cells: Sequence[Cell], *, stage: str, model_id: str,
                draws: int) -> list[dict[str, Any]]:
    """One row per (cell, draw). All draws are kept; none is selected."""
    rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(draws):
            rows.append({
                "cell_id": cell.cell_id, "draw_index": draw,
                "row_id": f"{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash,
                "scientific_seed": generation_seed(stage, model_id,
                                                   cell.prompt_hash, draw),
                "user_prompt": cell.prompt})
    return rows


def generate_and_score(model_key: str, cells: Sequence[Cell], *, stage: str,
                       cap: int, draws: int, device: int, run_dir: Path,
                       absent: Sequence[Constraint] = (),
                       limit: int | None = None,
                       carried=None,
                       generate=None) -> list[dict[str, Any]]:
    """Run one backend pass and score every row with the v4r3 primitive.

    ``absent`` are the registered instances scored on the **load-0 rows**
    without having been stated: §25's chance verdicts, which §13.3's
    difficulty coordinate divides by. §25 defines kappa in the unconstrained
    cell, so attaching the chance vector anywhere else would both inflate the
    record and invite a reading the protocol does not license. They are marked
    ``present: false`` and no estimand may read them as treated (§9.1).
    """
    spec = get_model(model_key)
    frozen_hash = verifier_source_hash()
    rows = design_rows(cells, stage=stage, model_id=spec.model_id, draws=draws)
    if limit:
        rows = rows[:limit]
    plan = build_plan(spec, stage=stage, max_new_tokens=cap)
    plan["chunk_size"] = 64
    reused = _reusable_rows(run_dir, rows)
    if reused is not None:
        outcome = {"rows": reused, "provenance": {"resumed": True}}
    elif carried is not None:
        # §10.7 E: generations carried from the superseded revision, admitted
        # only when every row this plan wants exists there under a
        # byte-identical model-facing prompt. Verdicts are recomputed below,
        # from the text, by this study's verifier -- the rows are evidence of
        # what the model said and of nothing else.
        from dci1v4r4.run.carried_run import carried_rows
        outcome = carried_rows(carried, rows)
    elif generate is None:
        outcome = run_backend(run_dir, plan, rows, device=device,
                              timeout_seconds=60 * 60 * 12)
    else:
        # The one substitution seam (§T14): a synthetic generator for the
        # CPU-only walk of this path. Rows it produces carry
        # ``synthetic: true`` and no analysis reads them.
        outcome = generate(run_dir, plan, rows)
    if verifier_source_hash() != frozen_hash:
        raise ProtocolError(
            "§10.6: the canonical verifier hash moved while the stage was "
            "running; the rows just generated cannot be placed and the stage "
            "fails closed")

    provenance = outcome.get("provenance") or {}
    carried_study = (provenance.get("source", {}).get("study")
                     if provenance.get("carried") else None)
    by_cell = {c.cell_id: c for c in cells}
    scored_rows: list[dict[str, Any]] = []
    for raw, row in zip(outcome["rows"], rows):
        cell = by_cell[row["cell_id"]]
        text = raw.get("final_answer") or ""
        truncated = bool(raw.get("answer_truncated"))
        # A constraint the prompt stated is never also scored as absent.
        chance = tuple(absent) if cell.load == 0 else ()
        scores = score_generation(
            text, present=cell.present, absent=chance, truncated=truncated,
            finish_reason=raw.get("finish_reason"),
            token_count=raw.get("total_generated_tokens"))
        scored_rows.append({
            "row_id": row["row_id"], "cell_id": cell.cell_id,
            "draw_index": row["draw_index"], "arm": cell.arm,
            "topic_id": cell.topic_id, "area": cell.area, "load": cell.load,
            "wording_indices": list(cell.wording_indices),
            "prompt_hash": cell.prompt_hash, "seed": row["scientific_seed"],
            "raw_response": text, "finish_reason": raw.get("finish_reason"),
            "token_count": raw.get("total_generated_tokens"),
            "truncated": truncated, "empty": scores.empty,
            "word_count": scores.word_count,
            "in_stem_band": scores.in_stem_band,
            "model_key": model_key, "model_id": spec.model_id,
            "model_revision": spec.revision, "study_id": STUDY_ID,
            "classification": CLASSIFICATION, "stage": stage,
            "synthetic": generate is not None,
            "resumed": reused is not None,
            "carried_from": carried_study,
            "verifier_hash": frozen_hash,
            "scores": [
                {"kind": s.kind, "severity": s.severity,
                 "statistic": s.statistic, "passed": s.passed,
                 "graded": s.graded, "non_vacuous": s.non_vacuous,
                 "vacuous_pass": s.vacuous_pass, "present": s.present,
                 "position": s.position,
                 "processing_failure": s.processing_failure}
                for s in scores.scores],
        })
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "scored.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in scored_rows))
    return scored_rows


def cell_rates(rows: Iterable[dict[str, Any]], *, kind: str, severity: int,
               present: bool) -> dict[str, float]:
    """Topic-mean compliance, vacuity and length for one constraint instance.

    The topic is the unit: draws average within a topic first, then topics
    average, so a topic contributes once however many draws it carries.
    """
    per_topic: dict[str, list[dict[str, Any]]] = {}
    label = f"{kind}:{severity}"
    for row in rows:
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
        raise ProtocolError(f"no rows for {label} (present={present})")
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
