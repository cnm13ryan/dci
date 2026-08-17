"""Gate 1: measurement (§10, §18.3, items 31–34) and the E2B carry-over.

Boundary suite, three-process determinism at agreement 1.000, the closed
natural-response reservoir with the frozen additional validation set, the
seeded min(150, N_c) sample per verifier class, and the one-sided 95%
Wilson disagreement bound at most 0.10 in both classes. Human labels are
external input; without them the gate does not pass and reports
PENDING_HUMAN (not a terminal status). A bound above 0.10 with 150 cases
is MEASUREMENT_NOT_ESTABLISHED; an exhausted natural class below 150 is
MEASUREMENT_EVIDENCE_INSUFFICIENT.
"""
from __future__ import annotations

import inspect
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

from dci1v3.analysis.stats import wilson_upper_one_sided
from dci1v3.engine import fs
from dci1v3.engine.dispatch import Job, operation
from dci1v3.errors import ProtocolError, TerminalStatus
from dci1v3.generation.cache import cache_rows, fill_cache
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import Cell, prompt_plan, solo_cells
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_obj, sha_text
from dci1v3.protocol.seeds import gate1_sample_seed
from dci1v3.protocol.wordings import target_wordings
from dci1v3.stages.determinism_worker import verdict_digest
from dci1v3.topics.split import split_topics
from dci1v3.verifiers import target as target_mod
from dci1v3.verifiers import words as words_mod
from dci1v3.verifiers.boundary import (
    boundary_specification_hash,
    evaluate_suite,
)

#: The v2 artifacts the authorised E2B carry-over reads (item 2). These are
#: historical evidence and instrument files, read as bytes only.
V2_E2B_PACKET = ("evidence/dci1-v2/gemma-3n-e2b-it/prefreeze-apparatus/"
                 "calibration/gate1/annotation_packet.jsonl")
V2_TARGET_SOURCE = "src/dci1/verifiers/target.py"
V2_WORDS_SOURCE = "src/dci1/verifiers/words.py"


def _determinism(items: list[dict[str, Any]], *, processes: int
                 ) -> dict[str, Any]:
    """Run every verifier over every item in three separate processes."""
    payload = json.dumps(items)
    digests = []
    package_src = str(Path(__file__).resolve().parents[2])
    for _ in range(processes):
        completed = subprocess.run(
            [sys.executable, "-m", "dci1v3.stages.determinism_worker"],
            input=payload, capture_output=True, text=True,
            env={"PYTHONPATH": package_src, "PATH": "/usr/bin:/bin"})
        if completed.returncode != 0:
            raise ProtocolError(f"determinism worker failed: "
                                f"{completed.stderr.strip()}")
        digests.append(completed.stdout.strip())
    agreement = 1.0 if len(set(digests)) == 1 else 0.0
    return {"processes": processes, "agreement": agreement,
            "digest": digests[0] if len(set(digests)) == 1 else None}


def _reservoir(job: Job) -> list[dict[str, Any]]:
    """Naturally generated target-solo responses: pre-screen rows plus any
    dedicated validation rows already generated."""
    items = []
    prescreen_cache = job.tree.data_dir("prescreen") / "full"
    if not (prescreen_cache / "cache.jsonl").exists():
        raise ProtocolError("Gate 1 requires the pre-screen cache")
    for row in cache_rows(prescreen_cache):
        if row["constraint_id"] is None:
            items.append(_item(row))
    validation_dir = job.tree.data_dir("gate1") / "validation"
    if (validation_dir / "cache.jsonl").exists():
        for row in cache_rows(validation_dir):
            items.append(_item(row))
    return items


def _item(row: dict[str, Any]) -> dict[str, Any]:
    return {"item_id": row["row_id"],
            "response_text": row["raw_response"],
            "response_hash": row["response_content_hash"],
            "constraint_text": target_wordings(row["n"])[0],
            "n": row["n"],
            "verifier_class": ("pass" if row["verdicts"]["s0"] == row["n"]
                               else "fail")}


def _validation_cells() -> list[Cell]:
    """The frozen additional measurement-validation set: pre-screen topics
    across the full target grid, enumerated topic-major and truncated to
    300 draws (DECISIONS_V3 V07)."""
    split = split_topics()
    base = solo_cells("gate1_validation", split["prescreen"],
                      [("A", n) for n in C.TARGET_GRID], draws=1)
    total = len(base)                       # 192
    extra = C.GATE1_EXTRA_RESPONSES_MAX - total   # 108 second draws
    cells = []
    for index, cell in enumerate(base):
        draws = 2 if index < extra else 1
        cells.append(Cell(**{**cell.__dict__, "draws": draws}))
    assert sum(c.draws for c in cells) == C.GATE1_EXTRA_RESPONSES_MAX
    return cells


def _generate_fn(job: Job):
    from dci1v3.stages.inference import generate_fn
    return generate_fn(job)


def _sample(job: Job, reservoir: list[dict[str, Any]]
            ) -> dict[str, list[dict[str, Any]]]:
    sampled = {}
    for cls in ("pass", "fail"):
        members = sorted([i for i in reservoir
                          if i["verifier_class"] == cls],
                         key=lambda i: i["item_id"])
        rng = random.Random(gate1_sample_seed(
            C.GATE1_SAMPLE_SEED, job.spec.model_id, cls))
        rng.shuffle(members)
        sampled[cls] = members[:C.GATE1_CLASS_TARGET]
    return sampled


def instrument_identity() -> dict[str, str]:
    """The carry-over comparison surfaces (§10): construct, normalisation,
    target-verifier source, boundary specification."""
    return {
        "construct": "Use the word however exactly {n} times.",
        "normalisation_source": inspect.getsource(words_mod.alpha_runs),
        "target_verifier_source": inspect.getsource(target_mod.s0_count),
        "boundary_specification_hash": boundary_specification_hash(),
    }


@operation("carry-over", stage=None)
def carry_over(job: Job) -> dict[str, Any]:
    """The authorised E2B v2 Gate 1 packet carry-over (item 2)."""
    if job.spec.model_key != "gemma-3n-e2b-it":
        raise ProtocolError("the carry-over is authorised for the E2B "
                            "replication only")
    repo = job.context.repo_root
    packet_path = repo / "dci1" / V2_E2B_PACKET
    if not packet_path.exists():
        raise ProtocolError(f"v2 packet not found at {packet_path}")
    identity = instrument_identity()
    v2_target = (repo / "dci1" / V2_TARGET_SOURCE).read_text()
    v2_words = (repo / "dci1" / V2_WORDS_SOURCE).read_text()
    mismatches = []
    if identity["target_verifier_source"] not in v2_target:
        mismatches.append("target-verifier source")
    if identity["normalisation_source"] not in v2_words:
        mismatches.append("normalisation")
    packet_rows = fs.read_jsonl(packet_path)
    for row in packet_rows:
        # The registered wording renderer handles the n=1 singular exactly
        # as the v2 instrument did.
        if row["constraint_text"] != target_wordings(row["n"])[0]:
            mismatches.append("construct definition")
            break
    body = {
        "source_packet": str(packet_path),
        "source_packet_hash": sha_text(packet_path.read_text()),
        "items": len(packet_rows),
        "instrument_hashes": {k: sha_text(v) for k, v in identity.items()},
        "mismatches": mismatches,
        "accepted": not mismatches,
        "v2_provenance": {
            "target_source_hash": sha_text(v2_target),
            "words_source_hash": sha_text(v2_words)},
    }
    existing = job.tree.carry_over_record
    if existing.exists():
        prior = fs.read_json(existing)
        if prior.get("accepted"):
            raise ProtocolError("an accepted carry-over record already "
                                "exists; carry-over is single-shot")
        # A refused carry-over is not accepted evidence: preserve it for
        # audit as superseded_non_evidence and record the supersession.
        from dci1v3.engine.artifacts import record_state
        from dci1v3.protocol.hashing import sha_obj
        parked = (job.tree.data_dir("artifacts") / "superseded"
                  / f"carry_over.{sha_obj(prior)[:12]}.json")
        parked.parent.mkdir(parents=True, exist_ok=True)
        existing.rename(parked)
        for state in ("generated", "committed", "superseded"):
            record_state(job.tree,
                         artifact_id=f"carry_over:{sha_obj(prior)[:12]}",
                         path=parked,
                         artifact_type="superseded_non_evidence",
                         state=state, stage="carry-over",
                         producing_commit=job.producing_commit)
    fs.write_json_once(job.tree.carry_over_record, body)
    if mismatches:
        return {"status": "REFUSED", "body": body, "input_hashes": {},
                "output_hashes": {}}
    return {"status": "COMPLETED", "body": body,
            "input_hashes": {"packet": body["source_packet_hash"]},
            "output_hashes": {}}


@operation("gate1", stage=C.STAGE_GATE1)
def run_gate1(job: Job) -> dict[str, Any]:
    stage_dir = job.tree.data_dir("gate1")
    stage_dir.mkdir(parents=True, exist_ok=True)

    boundary = evaluate_suite()
    if boundary["handled_as_specified"] != C.BOUNDARY_CASES_REQUIRED:
        raise TerminalStatus("MEASUREMENT_NOT_ESTABLISHED", {
            "criterion": "forty-case boundary suite",
            "observed": boundary})

    reservoir = _reservoir(job)
    counts = {cls: sum(1 for i in reservoir
                       if i["verifier_class"] == cls)
              for cls in ("pass", "fail")}
    if min(counts.values()) < C.GATE1_CLASS_TARGET and \
            not (stage_dir / "validation" / "cache.jsonl").exists():
        cells = _validation_cells()
        validation_dir = stage_dir / "validation"
        validation_dir.mkdir(parents=True, exist_ok=True)
        fs.write_json_once(validation_dir / "prompt_plan.json",
                           prompt_plan(cells))
        cap = _selected_cap(job)
        fill_cache(validation_dir, cells, spec=job.spec,
                   stage="gate1_validation",
                   generation_root=C.GENERATION_ROOT_SEED,
                   plan=backend_plan(job.spec, cap=cap),
                   generate_fn=_generate_fn(job),
                   environment=job.environment)
        reservoir = _reservoir(job)          # reservoir now closes
        counts = {cls: sum(1 for i in reservoir
                           if i["verifier_class"] == cls)
                  for cls in ("pass", "fail")}

    determinism = _determinism(
        [{"item_id": i["item_id"], "response_text": i["response_text"]}
         for i in reservoir], processes=C.DETERMINISM_PROCESSES)
    if determinism["agreement"] != C.DETERMINISM_REQUIRED:
        raise TerminalStatus("MEASUREMENT_NOT_ESTABLISHED", {
            "criterion": "verifier determinism 1.000",
            "observed": determinism})

    sampled = _sample(job, reservoir)
    packet = [{"item_id": i["item_id"],
               "response_text": i["response_text"],
               "constraint_text": i["constraint_text"], "n": i["n"]}
              for cls in ("pass", "fail") for i in sampled[cls]]
    packet_path = stage_dir / "annotation_packet.jsonl"
    if not packet_path.exists():
        packet_path.write_text("".join(
            json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
            for r in packet))

    annotations = _load_annotations(job)
    if annotations is None:
        raise ProtocolError(
            f"PENDING_HUMAN: {len(packet)} sampled responses await three "
            f"annotators; packet at {packet_path}")
    stored = stage_dir / "annotations.json"
    if not stored.exists():
        fs.write_json_once(stored, annotations)

    class_bounds: dict[str, Any] = {}
    for cls in ("pass", "fail"):
        items = sampled[cls]
        disagreements = 0
        for item in items:
            labels = annotations.get(item["item_id"])
            if labels is None:
                labels = annotations.get(item["response_hash"])
            if labels is None or len(labels) != C.GATE1_ANNOTATORS:
                raise ProtocolError(
                    f"PENDING_HUMAN: item {item['item_id']} lacks "
                    f"{C.GATE1_ANNOTATORS} labels")
            majority = ("pass" if sum(1 for l in labels if l == "pass") >= 2
                        else "fail")
            verifier = ("pass" if target_mod.s0_count(
                item["response_text"]) == item["n"] else "fail")
            if majority != verifier:
                disagreements += 1
        bound = wilson_upper_one_sided(disagreements, len(items)) \
            if items else 1.0
        class_bounds[cls] = {"cases": len(items),
                             "disagreements": disagreements,
                             "wilson_upper": bound}
        if bound > C.GATE1_DISAGREEMENT_MAX:
            if len(items) >= C.GATE1_CLASS_TARGET:
                raise TerminalStatus("MEASUREMENT_NOT_ESTABLISHED", {
                    "criterion": f"one-sided 95% Wilson upper bound at "
                                 f"most {C.GATE1_DISAGREEMENT_MAX}",
                    "class": cls, "bounds": class_bounds})
            raise TerminalStatus("MEASUREMENT_EVIDENCE_INSUFFICIENT", {
                "criterion": "natural class exhausted below 150 cases",
                "class": cls, "bounds": class_bounds,
                "reservoir": counts})

    face = annotations.get("face_validity")
    if not (isinstance(face, list) and len(face) == C.GATE1_ANNOTATORS):
        raise ProtocolError("PENDING_HUMAN: face-validity judgements "
                            "missing")

    body = {
        "boundary_suite": {"handled": boundary["handled_as_specified"]},
        "determinism": determinism,
        "reservoir": counts,
        "sampled": {cls: len(sampled[cls]) for cls in sampled},
        "class_bounds": class_bounds,
        "face_validity": {"agreements": sum(1 for f in face if f),
                          "of": len(face)},
        "discriminant_validity": {
            "verifier_inputs": ["response text", "target identity", "n"],
            "parse_independent": True},
        "carry_over": (fs.read_json(job.tree.carry_over_record)
                       if job.tree.carry_over_record.exists() else None),
        "instrument": {k: sha_text(v)
                       for k, v in instrument_identity().items()},
    }
    return {"status": "PASSED", "body": body,
            "input_hashes": {"packet": sha_text(packet_path.read_text())},
            "output_hashes": {"bounds": sha_obj(class_bounds)}}


def _selected_cap(job: Job) -> int:
    from dci1v3.engine.signing import verify_signed
    from dci1v3.engine.transitions import load_stage_record
    record = load_stage_record(job.tree, C.STAGE_REGIME)
    if record is None:
        raise ProtocolError("Gate 1 requires the regime-screen record")
    payload = verify_signed(record, job.context.signing_key_path,
                            where="regime_screen")
    return int(payload["body"]["selected_cap"])


def _load_annotations(job: Job) -> dict[str, Any] | None:
    path = job.options.get("annotations")
    if path:
        return fs.read_json(Path(path))
    default = job.tree.data_dir("gate1") / "annotations.json"
    if default.exists():
        return fs.read_json(default)
    carried = job.tree.carry_over_record
    if carried.exists():
        record = fs.read_json(carried)
        if record.get("accepted") and record.get("annotations"):
            return record["annotations"]
    return None
