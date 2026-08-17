"""Gate 1 under amendment A2: the autorater-assisted verifier workflow,
plus the E2B carry-over and the preserved human-validation pathway.

    response pool (pre-screen + frozen validation responses)
    -> deterministic development/calibration split
    -> `gate1-dev`: verifier + configured autorater on the development
       half; disagreement listing for inspection; re-runnable while the
       verifier is under development (regression tests guard changes)
    -> `verifier-freeze` (study-level): manifest binding verifier sources,
       regression-test state, code revision, split, autorater config
    -> `gate1-calibrate`: the same autorater on the untouched calibration
       half; full report (coverage, marginals, 2x2 contingency,
       directional disagreement) with NO automatic acceptance threshold
    -> `gate1 --approve-autorater-calibration`: the explicit researcher
       approval that writes the GATE_1 stage record

The stage record states ``HUMAN_VALIDATION_UNAVAILABLE`` and the
registered strongest-claim sentence; autorater evidence is never
presented as human validation. The blinded annotation packet, reviewer
GUI, and parser are preserved unchanged; when an independent human
becomes available, `human-audit --annotations` attaches that evidence
(the original A1 criterion: one label per item, one-sided 95% Wilson
bound at most 0.10 per verifier class).

Boundary-suite and three-process determinism failures remain the
registered MEASUREMENT_NOT_ESTABLISHED terminal outcomes.
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
from dci1v3.engine.artifacts import record_state
from dci1v3.engine.dispatch import Job, operation
from dci1v3.errors import IntegrityError, ProtocolError, TerminalStatus
from dci1v3.generation.cache import cache_rows, fill_cache
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import Cell, prompt_plan, solo_cells
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_file, sha_obj, sha_text
from dci1v3.protocol.seeds import gate1_sample_seed
from dci1v3.protocol.wordings import target_wordings
from dci1v3.stages import autorater
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


# --------------------------------------------------------------- helpers
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
    """The response pool: naturally generated pre-screen target-solo rows
    plus the frozen measurement-validation rows."""
    items = []
    prescreen_cache = job.tree.data_dir("prescreen") / "full"
    if not (prescreen_cache / "cache.jsonl").exists():
        raise ProtocolError("Gate 1 requires the pre-screen cache")
    for row in cache_rows(prescreen_cache):
        if row["constraint_id"] is None:
            items.append(_item(row, source="prescreen"))
    validation_dir = job.tree.data_dir("gate1") / "validation"
    if (validation_dir / "cache.jsonl").exists():
        for row in cache_rows(validation_dir):
            items.append(_item(row, source="validation"))
    return items


def _item(row: dict[str, Any], *, source: str) -> dict[str, Any]:
    return {"item_id": row["row_id"],
            "response_text": row["raw_response"],
            "response_hash": row["response_content_hash"],
            "constraint_text": target_wordings(row["n"])[0],
            "n": row["n"],
            "source": source,          # descriptive provenance only
            "verifier_class": ("pass" if row["verdicts"]["s0"] == row["n"]
                               else "fail")}


def _validation_cells() -> list[Cell]:
    """The frozen additional measurement-validation set (DECISIONS V07)."""
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
    """The frozen human-annotation sample: min(150, N_c) per class."""
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
    """The carry-over comparison surfaces (§10)."""
    return {
        "construct": "Use the word however exactly {n} times.",
        "normalisation_source": inspect.getsource(words_mod.alpha_runs),
        "target_verifier_source": inspect.getsource(target_mod.s0_count),
        "boundary_specification_hash": boundary_specification_hash(),
    }


def _selected_cap(job: Job) -> int:
    from dci1v3.engine.signing import verify_signed
    from dci1v3.engine.transitions import load_stage_record
    record = load_stage_record(job.tree, C.STAGE_REGIME)
    if record is None:
        raise ProtocolError("Gate 1 requires the regime-screen record")
    payload = verify_signed(record, job.context.signing_key_path,
                            where="regime_screen")
    return int(payload["body"]["selected_cap"])


def _packet_rows(sampled: dict[str, list[dict[str, Any]]]
                 ) -> list[dict[str, Any]]:
    return [{"item_id": i["item_id"],
             "response_text": i["response_text"],
             "constraint_text": i["constraint_text"], "n": i["n"]}
            for cls in ("pass", "fail") for i in sampled[cls]]


def _pool_hash(reservoir: list[dict[str, Any]]) -> str:
    """The realised response-pool boundary: identities and response bytes."""
    return sha_obj(sorted((i["item_id"], i["response_hash"])
                          for i in reservoir))


def human_validation_status(tree) -> dict[str, Any]:
    """The effective human-validation status for downstream readers
    (A2.1): the human-audit record when one exists, else the Gate 1
    record's declaration, else unavailable. A generic PASSED stage state
    never implies human validation."""
    audit_path = tree.root / "human_audit.json"
    if audit_path.exists():
        audit = fs.read_json(audit_path)
        return {"human_validation": audit["human_validation"],
                "source": "human_audit", "outcome": audit["outcome"]}
    from dci1v3.engine.signing import verify_signed
    from dci1v3.engine.transitions import load_stage_record
    record = load_stage_record(tree, C.STAGE_GATE1)
    if record is not None:
        body = verify_signed(record, tree.context.signing_key_path,
                             where="gate1_measurement")["body"]
        return {"human_validation": body.get(
                    "human_validation", C.HUMAN_VALIDATION_UNAVAILABLE),
                "source": "gate1_record",
                "measurement_basis": body.get("measurement_basis")}
    return {"human_validation": C.HUMAN_VALIDATION_UNAVAILABLE,
            "source": "none"}


def assert_calibration_unexposed(tree) -> None:
    """One-shot calibration (A2.1), enforced through the append-only
    ledger BEFORE any mutation: once calibration evidence exists in any
    state, the held-out half is exposed and can never be re-presented as
    fresh; a contaminated (superseded) calibration additionally requires
    genuinely new untouched response data — not a reshuffle of the
    exposed pool — before independent calibration can be claimed again."""
    from dci1v3.engine.artifacts import artifact_states
    prior = artifact_states(tree).get("op:gate1-calibrate")
    if prior is None:
        return
    if prior["state"] == "superseded":
        raise ProtocolError(
            "calibration evidence is contaminated (verifier changed after "
            "inspection); recalibration requires genuinely new untouched "
            "response data — the existing pool is exposed and a reshuffle "
            "of it is not fresh held-out evidence")
    raise ProtocolError(
        f"calibration already ran (ledger state {prior['state']!r}); "
        f"calibration is one-shot and the held-out half is exposed")


def binding_mismatches(entry: dict[str, Any],
                       current: dict[str, Any]) -> list[str]:
    """Keys of the realised evidence boundary that differ from the frozen
    manifest entry."""
    return sorted(k for k in current if current[k] != entry.get(k))


def _assert_freeze_binding(job: Job, manifest: dict[str, Any]) -> None:
    """The freeze binds the realised evidence boundary (A2.1): the current
    pool, split, and development record must be byte-identical to what the
    manifest recorded for this model."""
    included = manifest.get("development_runs", {}).get("included", {})
    entry = included.get(job.spec.model_key)
    if entry is None:
        raise IntegrityError(
            f"{job.spec.model_key} was not a designated development run "
            f"in the verifier freeze; calibration refused")
    reservoir, split = _pool_and_split(job)
    dev_path = job.tree.root / "gate1_dev.json"
    current = {"pool_hash": _pool_hash(reservoir),
               "split_hash": split["split_hash"],
               "dev_record_hash": sha_file(dev_path)}
    mismatched = binding_mismatches(entry, current)
    if mismatched:
        raise IntegrityError(
            f"the realised evidence boundary differs from the verifier "
            f"freeze for {job.spec.model_key}: {mismatched}; the frozen "
            f"holdout is not the one on disk")


def _pool_and_split(job: Job) -> tuple[list[dict[str, Any]],
                                       dict[str, Any]]:
    reservoir = _reservoir(job)
    split_path = job.tree.data_dir("gate1") / "autorater" / "split.json"
    split = autorater.make_split(reservoir, model_id=job.spec.model_id)
    if split_path.exists():
        stored = fs.read_json(split_path)
        if stored["split_hash"] != split["split_hash"]:
            raise IntegrityError(
                "the stored development/calibration split differs from "
                "the deterministic derivation; the pool changed")
        split = stored
    else:
        split_path.parent.mkdir(parents=True, exist_ok=True)
        fs.write_json_once(split_path, split)
    return reservoir, split


def _half(reservoir: list[dict[str, Any]], split: dict[str, Any],
          half: str) -> list[dict[str, Any]]:
    wanted = set(split[half])
    items = [i for i in reservoir if i["item_id"] in wanted]
    if len(items) != len(wanted):
        raise IntegrityError(f"{half} half is missing pool items")
    return sorted(items, key=lambda i: i["item_id"])


# ------------------------------------------------------------ operations
@operation("gate1-dev", stage=None)
def gate1_dev(job: Job) -> dict[str, Any]:
    """Development phase: pool assembly, executable measurement checks,
    the frozen human packet, and autorater judging of the development
    half. Re-runnable while the verifier is under development."""
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
        if not (validation_dir / "prompt_plan.json").exists():
            fs.write_json_once(validation_dir / "prompt_plan.json",
                               prompt_plan(cells))
        fill_cache(validation_dir, cells, spec=job.spec,
                   stage="gate1_validation",
                   generation_root=C.GENERATION_ROOT_SEED,
                   plan=backend_plan(job.spec, cap=_selected_cap(job)),
                   generate_fn=_generate_fn(job),
                   environment=job.environment)
        reservoir = _reservoir(job)

    determinism = _determinism(
        [{"item_id": i["item_id"], "response_text": i["response_text"]}
         for i in reservoir], processes=C.DETERMINISM_PROCESSES)
    if determinism["agreement"] != C.DETERMINISM_REQUIRED:
        raise TerminalStatus("MEASUREMENT_NOT_ESTABLISHED", {
            "criterion": "verifier determinism 1.000",
            "observed": determinism})

    # The frozen future-human packet (unchanged A1 sampling).
    sampled = _sample(job, reservoir)
    packet = _packet_rows(sampled)
    packet_path = stage_dir / "annotation_packet.jsonl"
    packet_bytes = "".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
        for r in packet)
    if packet_path.exists():
        if sha_text(packet_path.read_text()) != sha_text(packet_bytes):
            raise IntegrityError(
                "the stored annotation packet differs from the frozen "
                "sampling derivation")
    else:
        packet_path.write_text(packet_bytes)

    # Autorater on the development half only.
    reservoir, split = _pool_and_split(job)
    config = autorater.load_config(job.options.get("autorater_config"))
    dev_items = _half(reservoir, split, "development")
    from dci1v3.stages.inference import judge_generate_fn
    judgments = autorater.run_autorater(
        stage_dir / "autorater" / "dev", dev_items, config=config,
        phase="development", generate_fn=judge_generate_fn(job),
        environment=job.environment)
    # Development-only stability check: the identical items judged a
    # second time under the identical configuration. Reported, never
    # averaged, never voted; the primary run stays the dev evidence.
    repeat = autorater.run_autorater(
        stage_dir / "autorater" / "dev_repeat", dev_items, config=config,
        phase="development-stability",
        generate_fn=judge_generate_fn(job), environment=job.environment)
    stability = autorater.stability_comparison(judgments, repeat)
    items_by_id = {i["item_id"]: i for i in dev_items}
    report = autorater.judgment_report(judgments)
    listing = autorater.disagreement_listing(items_by_id, judgments)
    breakdown = autorater.disagreement_breakdown(items_by_id, judgments)
    fs.write_json(stage_dir / "autorater" / "dev" / "report.json",
                  {"report": report, "disagreements": listing,
                   "disagreement_breakdown": breakdown,
                   "stability": stability})

    body = {
        "phase": "verifier-development",
        "boundary_suite": {"handled": boundary["handled_as_specified"]},
        "determinism": determinism,
        "reservoir": counts,
        "packet_hash": sha_text(packet_bytes),
        "pool_hash": _pool_hash(reservoir),
        "split_hash": split["split_hash"],
        "development_items": len(dev_items),
        "autorater_config_hash": config["config_hash"],
        "development_report": report,
        "disagreement_breakdown": breakdown,
        "stability": stability,
        "disagreements_to_inspect": len(listing),
        "verifier_sources": autorater.verifier_source_state(),
        "not_human_validation": True,
    }
    fs.write_json(job.tree.root / "gate1_dev.json", body)
    return {"status": "COMPLETED", "body": body,
            "input_hashes": {"autorater_config": config["config_hash"],
                             "split": split["split_hash"]},
            "output_hashes": {"development_report": sha_obj(report)}}


def verifier_freeze(context, *, autorater_config: str | None = None
                    ) -> dict[str, Any]:
    """Study-level, single-shot: the verifier-freeze manifest binding the
    verifier implementation, regression-test state, code revision, the
    designated development runs with their REALISED pool and split hashes,
    and the autorater configuration. Every registered, non-terminal model
    replication must have completed (and had inspectable) `gate1-dev`
    before the freeze; the manifest records exactly which runs were
    included. Runs the verifier regression suite and refuses on failure."""
    from dci1v3.engine import gitinfo, store
    from dci1v3.engine.paths import model_tree
    from dci1v3.engine.signing import sign_payload
    from dci1v3.engine.transitions import terminal_status
    from dci1v3.models.registry import MODEL_KEYS

    manifest_path = context.study_root / "verifier_freeze.json"
    if manifest_path.exists():
        raise ProtocolError("the verifier is already frozen; changing a "
                            "frozen instrument requires audited "
                            "supersession")

    included: dict[str, dict[str, str]] = {}
    excluded: dict[str, str] = {}
    missing: list[str] = []
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        status = terminal_status(tree)
        if status is not None:
            excluded[model_key] = f"terminal: {status}"
            continue
        dev_path = tree.root / "gate1_dev.json"
        split_path = tree.data_dir("gate1") / "autorater" / "split.json"
        if not dev_path.exists() or not split_path.exists():
            missing.append(model_key)
            continue
        dev = fs.read_json(dev_path)
        included[model_key] = {
            "dev_record_hash": sha_file(dev_path),
            "pool_hash": dev["pool_hash"],
            "split_hash": dev["split_hash"],
        }
    if missing:
        raise ProtocolError(
            f"verifier freeze requires every designated development run "
            f"first; missing gate1-dev for: {missing}")
    if not included:
        raise ProtocolError("no development runs available to freeze over")

    gitinfo.assert_clean_worktree(context.repo_root)
    commit = gitinfo.head_commit(context.repo_root)
    gitinfo.assert_sources_in_commit(context.repo_root, commit)

    test_path = (context.repo_root / "dci1" / "tests_v3"
                 / "test_verifiers.py")
    if not test_path.exists():
        raise ProtocolError(f"verifier regression tests missing at "
                            f"{test_path}")
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", str(test_path),
         "-p", "no:cacheprovider"],
        capture_output=True, text=True,
        cwd=str(context.repo_root / "dci1"),
        env={**__import__("os").environ,
             "PYTHONDONTWRITEBYTECODE": "1"})
    if completed.returncode != 0:
        raise ProtocolError(
            f"verifier regression suite failed; freeze refused:\n"
            f"{completed.stdout[-800:]}")

    config = autorater.load_config(
        Path(autorater_config) if autorater_config else None)
    payload = {
        "kind": "verifier_freeze",
        "study_id": context.study_id,
        "verifier_sources": autorater.verifier_source_state(),
        "regression_tests": {
            "path": "dci1/tests_v3/test_verifiers.py",
            "file_hash": sha_file(test_path),
            "result": completed.stdout.strip().splitlines()[-1]},
        "producing_commit": commit,
        "split_derivation": {"seed": C.AUTORATER_SPLIT_SEED,
                             "domain": C.DOMAIN_AUTORATER_SPLIT},
        "development_runs": {"included": included, "excluded": excluded},
        "autorater_config": {k: config[k] for k in
                             ("schema_version", "judge_model_key",
                              "judge_model_id", "judge_revision",
                              "backend", "prompt_version",
                              "parser_version", "label_mapping",
                              "decoding", "config_hash", "prompt_hash")},
    }
    record = sign_payload(payload, context.signing_key_path)
    fs.write_json_once(manifest_path, record)
    store.replicate(context.study_root, context.durable_study_root)
    return {"frozen": True, "record_hash": record["record_hash"],
            "producing_commit": commit}


def gate1_signoff(context, *, phase: str,
                  notes_path: str | None = None,
                  autorater_config: str | None = None) -> dict[str, Any]:
    """The cross-model inspection summary (study-level, re-runnable while
    inspection iterates).

    ``development``: produced BEFORE the verifier freeze — configuration
    and judge revision, realised pool/split hashes, coverage and
    invalid-output summaries, the four contingency tables, directional
    disagreement patterns, repeated-run stability, and the machine check
    that no calibration item has been exposed. ``calibration``: produced
    before approval — the four contingency tables, coverage and invalid
    rates, directional disagreements, identification intervals,
    descriptive concentrations, and the complete case appendix. The
    researcher's inspection record (disagreements inspected and
    classified, verifier changes with their regression tests, remaining
    known limitations) attaches through ``--notes``. Documentation for
    the approval decision — it decides nothing itself."""
    from dci1v3.engine import store
    from dci1v3.engine.artifacts import artifact_states
    from dci1v3.engine.paths import model_tree
    from dci1v3.engine.transitions import terminal_status
    from dci1v3.models.registry import MODEL_KEYS

    if phase not in ("development", "calibration"):
        raise ProtocolError(f"unknown sign-off phase {phase!r}")
    config = autorater.load_config(
        Path(autorater_config) if autorater_config else None)
    notes = fs.read_json(Path(notes_path)) if notes_path else None

    models: dict[str, dict[str, Any]] = {}
    excluded: dict[str, str] = {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        status = terminal_status(tree)
        if status is not None:
            excluded[model_key] = f"terminal: {status}"
            continue
        if phase == "development":
            dev_path = tree.root / "gate1_dev.json"
            if not dev_path.exists():
                raise ProtocolError(f"no gate1-dev record for {model_key}")
            dev = fs.read_json(dev_path)
            if dev["autorater_config_hash"] != config["config_hash"]:
                raise ProtocolError(
                    f"{model_key}'s development run used a different "
                    f"autorater configuration")
            calibration_rows = (tree.data_dir("gate1") / "autorater"
                                / "calibration" / "judgments.jsonl")
            models[model_key] = {
                "dev_record_hash": sha_file(dev_path),
                "pool_hash": dev["pool_hash"],
                "split_hash": dev["split_hash"],
                "development_items": dev["development_items"],
                "report": dev["development_report"],
                "disagreement_breakdown": dev["disagreement_breakdown"],
                "stability": dev["stability"],
                "disagreements_to_inspect": dev["disagreements_to_inspect"],
                "calibration_untouched": (
                    not calibration_rows.exists()
                    and artifact_states(tree).get("op:gate1-calibrate")
                    is None),
            }
        else:
            cal_path = tree.root / "gate1_calibration.json"
            if not cal_path.exists():
                raise ProtocolError(
                    f"no gate1-calibrate record for {model_key}")
            cal = fs.read_json(cal_path)
            if cal["autorater_config_hash"] != config["config_hash"]:
                raise ProtocolError(
                    f"{model_key}'s calibration used a different "
                    f"autorater configuration")
            models[model_key] = {
                "calibration_record_hash": sha_file(cal_path),
                "split_hash": cal["split_hash"],
                "calibration_items": cal["calibration_items"],
                "report": cal["report"],
                "disagreement_breakdown": cal["disagreement_breakdown"],
                "case_appendix": cal["disagreements"],
            }

    body = {
        "kind": f"gate1_{phase}_signoff",
        "study_id": context.study_id,
        "autorater_config": {k: config[k] for k in
                             ("schema_version", "judge_model_key",
                              "judge_model_id", "judge_revision",
                              "backend", "prompt_version",
                              "parser_version", "label_mapping",
                              "decoding", "config_hash", "prompt_hash")},
        "models": models,
        "excluded": excluded,
        "inspection_notes": notes,
        "not_human_validation": True,
        "measurement_scope": C.MEASUREMENT_SCOPE,
    }
    out_path = context.study_root / f"gate1_{phase}_signoff.json"
    fs.write_json(out_path, body)
    store.replicate(context.study_root, context.durable_study_root)
    return {"written": str(out_path), "models": sorted(models),
            "excluded": excluded}


def _load_verifier_freeze(job: Job) -> dict[str, Any]:
    from dci1v3.engine.signing import verify_signed
    manifest_path = job.context.study_root / "verifier_freeze.json"
    if not manifest_path.exists():
        raise ProtocolError(
            "the verifier is not frozen; run `verifier-freeze` after "
            "development-phase inspection")
    return verify_signed(fs.read_json(manifest_path),
                         job.context.signing_key_path,
                         where="verifier_freeze")


@operation("gate1-calibrate", stage=None)
def gate1_calibrate(job: Job) -> dict[str, Any]:
    """Held-out evaluation: the same configured autorater on the
    untouched calibration half of the pool. Reports everything, decides
    nothing: there is no automatic acceptance threshold."""
    dev_record = job.tree.root / "gate1_dev.json"
    if not dev_record.exists():
        raise ProtocolError("gate1-calibrate requires the development "
                            "phase (gate1-dev) first")
    assert_calibration_unexposed(job.tree)      # ledger-first, pre-mutation
    manifest = _load_verifier_freeze(job)
    autorater.assert_verifier_unchanged(manifest)
    _assert_freeze_binding(job, manifest)

    out_path = job.tree.root / "gate1_calibration.json"
    if out_path.exists():
        raise ProtocolError(
            "a calibration report already exists; calibration is one-shot "
            "and the held-out half is exposed")

    config = autorater.load_config(job.options.get("autorater_config"))
    if config["config_hash"] != \
            manifest["autorater_config"]["config_hash"]:
        raise IntegrityError(
            "autorater configuration differs from the verifier-freeze "
            "manifest; calibration must use the same configured autorater")

    reservoir, split = _pool_and_split(job)
    calibration_items = _half(reservoir, split, "calibration")
    from dci1v3.stages.inference import judge_generate_fn
    judgments = autorater.run_autorater(
        job.tree.data_dir("gate1") / "autorater" / "calibration",
        calibration_items, config=config, phase="calibration",
        generate_fn=judge_generate_fn(job),
        environment=job.environment)
    items_by_id = {i["item_id"]: i for i in calibration_items}
    report = autorater.judgment_report(judgments)
    listing = autorater.disagreement_listing(items_by_id, judgments)
    breakdown = autorater.disagreement_breakdown(items_by_id, judgments)

    body = {
        "phase": "autorater-calibration",
        "status": "REPORTED",
        "split_hash": split["split_hash"],
        "calibration_items": len(calibration_items),
        "autorater_config_hash": config["config_hash"],
        "verifier_freeze_hash": sha_obj(manifest),
        "report": report,
        "disagreements": listing,
        "disagreement_breakdown": breakdown,
        "approval": "pending explicit researcher approval "
                    "(`gate1 --approve-autorater-calibration`)",
        "not_human_validation": True,
    }
    fs.write_json_once(out_path, body)
    record_state(job.tree, artifact_id="op:gate1-calibrate",
                 path=out_path, artifact_type="gate_record",
                 state="generated", stage="gate1-calibrate",
                 producing_commit=job.producing_commit)
    record_state(job.tree, artifact_id="op:gate1-calibrate",
                 path=out_path, artifact_type="gate_record",
                 state="committed", stage="gate1-calibrate",
                 producing_commit=job.producing_commit)
    return {"status": "REPORTED", "body": body,
            "input_hashes": {"split": split["split_hash"],
                             "verifier_freeze": body[
                                 "verifier_freeze_hash"]},
            "output_hashes": {"calibration_report": sha_obj(report)}}


@operation("gate1", stage=C.STAGE_GATE1)
def run_gate1(job: Job) -> dict[str, Any]:
    """The explicit researcher approval that closes Gate 1 (A2)."""
    if not job.options.get("approve_autorater_calibration"):
        raise ProtocolError(
            "Gate 1 closes only on explicit researcher approval: inspect "
            "gate1_calibration.json and re-run with "
            "--approve-autorater-calibration")
    dev_path = job.tree.root / "gate1_dev.json"
    calibration_path = job.tree.root / "gate1_calibration.json"
    for path, hint in ((dev_path, "gate1-dev"),
                       (calibration_path, "gate1-calibrate")):
        if not path.exists():
            raise ProtocolError(f"approval requires {hint} first")
    manifest = _load_verifier_freeze(job)
    try:
        autorater.assert_verifier_unchanged(manifest)
        _assert_freeze_binding(job, manifest)
    except IntegrityError:
        record_state(job.tree, artifact_id="op:gate1-calibrate",
                     path=calibration_path,
                     artifact_type="superseded_non_evidence",
                     state="superseded", stage="gate1-calibrate",
                     producing_commit=job.producing_commit)
        raise
    dev = fs.read_json(dev_path)
    calibration = fs.read_json(calibration_path)
    record_state(job.tree, artifact_id="op:gate1-calibrate",
                 path=calibration_path, artifact_type="gate_record",
                 state="accepted", stage="gate1-calibrate",
                 producing_commit=job.producing_commit)

    body = {
        "measurement_basis": C.MEASUREMENT_BASIS_AUTORATER,
        "basis": "autorater-calibrated frozen verifier; explicit "
                 "researcher approval",
        "human_validation": C.HUMAN_VALIDATION_UNAVAILABLE,
        "strongest_claim": C.STRONGEST_CLAIM,
        "measurement_scope": C.MEASUREMENT_SCOPE,
        "boundary_suite": dev["boundary_suite"],
        "determinism": dev["determinism"],
        "reservoir": dev["reservoir"],
        "packet_hash": dev["packet_hash"],
        "split_hash": dev["split_hash"],
        "verifier_freeze_hash": calibration["verifier_freeze_hash"],
        "autorater_config_hash": calibration["autorater_config_hash"],
        "development_report": dev["development_report"],
        "calibration_report": calibration["report"],
        "approval": {"action": "--approve-autorater-calibration",
                     "recorded_by": "canonical dispatcher"},
        "human_pathway": "annotation packet + reviewer GUI preserved; "
                         "attach evidence later via `human-audit`",
        "instrument": {k: sha_text(v)
                       for k, v in instrument_identity().items()},
        "carry_over": (fs.read_json(job.tree.carry_over_record)
                       if job.tree.carry_over_record.exists() else None),
    }
    return {"status": "PASSED", "body": body,
            "input_hashes": {
                "development": sha_file(dev_path),
                "calibration": sha_file(calibration_path),
                "verifier_freeze": calibration["verifier_freeze_hash"]},
            "output_hashes": {"packet": dev["packet_hash"]}}


@operation("human-audit", stage=None)
def human_audit(job: Job) -> dict[str, Any]:
    """The preserved independent human validation (original A1 criterion),
    attachable whenever an independent annotator becomes available."""
    annotations_path = job.options.get("annotations")
    if not annotations_path:
        raise ProtocolError("human-audit requires --annotations (the "
                            "reviewer-GUI export)")
    out_path = job.tree.root / "human_audit.json"
    if out_path.exists():
        raise ProtocolError("a human audit is already recorded; "
                            "supersession requires an audited decision")
    packet_path = job.tree.data_dir("gate1") / "annotation_packet.jsonl"
    if not packet_path.exists():
        raise ProtocolError("no annotation packet exists for this model")
    annotations = fs.read_json(Path(annotations_path))

    by_class: dict[str, dict[str, int]] = {
        "pass": {"cases": 0, "disagreements": 0},
        "fail": {"cases": 0, "disagreements": 0}}
    for line in packet_path.read_text().splitlines():
        row = json.loads(line)
        labels = annotations.get(row["item_id"])
        if labels is None or len(labels) != C.GATE1_ANNOTATORS:
            raise ProtocolError(
                f"item {row['item_id']} lacks exactly "
                f"{C.GATE1_ANNOTATORS} human label(s)")
        if any(label not in ("pass", "fail") for label in labels):
            raise ProtocolError(
                f"item {row['item_id']} carries a label outside the "
                f"registered binary vocabulary")
        human = labels[0]
        verifier = ("pass" if target_mod.s0_count(
            row["response_text"]) == row["n"] else "fail")
        by_class[verifier]["cases"] += 1
        if human != verifier:
            by_class[verifier]["disagreements"] += 1
    face = annotations.get("face_validity")
    if not (isinstance(face, list) and len(face) == C.GATE1_ANNOTATORS):
        raise ProtocolError("face-validity judgement missing")

    outcome = "ESTABLISHED"
    for cls, cell in by_class.items():
        cell["wilson_upper"] = (
            wilson_upper_one_sided(cell["disagreements"], cell["cases"])
            if cell["cases"] else None)
        if cell["wilson_upper"] is None or \
                cell["wilson_upper"] > C.GATE1_DISAGREEMENT_MAX:
            outcome = ("BOUND_EXCEEDED"
                       if cell["cases"] >= C.GATE1_CLASS_TARGET
                       else "EVIDENCE_INSUFFICIENT")
    body = {
        "outcome": outcome,
        "human_validation": (C.HUMAN_VALIDATION_COMPLETE
                             if outcome == "ESTABLISHED"
                             else C.HUMAN_VALIDATION_UNAVAILABLE),
        "class_bounds": by_class,
        "threshold": C.GATE1_DISAGREEMENT_MAX,
        "face_validity": {"agreements": sum(1 for f in face if f),
                          "of": len(face)},
        "packet_hash": sha_text(packet_path.read_text()),
        "annotations_hash": sha_file(Path(annotations_path)),
        "interpretation": (
            "independent human validation established" if outcome ==
            "ESTABLISHED" else
            "human evidence does not certify the measurement; downstream "
            "results keep (or escalate) the unvalidated-measurement "
            "caveat"),
    }
    fs.write_json_once(out_path, body)
    return {"status": outcome, "body": body,
            "input_hashes": {"annotations": body["annotations_hash"],
                             "packet": body["packet_hash"]},
            "output_hashes": {"audit": sha_file(out_path)}}


# ------------------------------------------------------------ carry-over
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
