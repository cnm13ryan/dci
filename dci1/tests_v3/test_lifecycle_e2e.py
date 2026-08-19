"""The end-to-end synthetic lifecycle (items 63–64), through the actual
registered public entrypoints (dci1v3.cli), with real inference replaced by
the synthetic model adapter and nothing else.

The lifecycle: qualification → pilot → regime screen → Gate 1 → Gate 2A →
Gate 2B → freeze → synthetic confirmatory cache → primary selection →
confirmatory masking → masked analysis → single unmask → final analysis.
Afterwards, every prohibited attempt of item 64 must fail before prohibited
mutation or key access.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from dci1v3 import cli
from dci1v3.engine import fs
from dci1v3.engine.context import synthetic_context
from dci1v3.engine.paths import model_tree
from dci1v3.protocol import constants as C
from tests_v3.conftest import make_synthetic_annotations

MODEL = "gemma-3n-e2b-it"

pytestmark = pytest.mark.slow


def run_cli(base: Path, repo: Path, *args: str) -> int:
    return cli.main(["--synthetic-root", str(base),
                     "--repo-root", str(repo), *args])


@pytest.fixture(scope="module")
def lifecycle(synthetic_repo, tmp_path_factory):
    """Run the complete lifecycle once; tests then assert over its state."""
    base = tmp_path_factory.mktemp("lifecycle") / "study"
    repo = synthetic_repo
    ctx = synthetic_context(base, repo)
    tree = model_tree(ctx, MODEL)
    trace: list[tuple[str, int]] = []

    def step(*args: str, expect: int = 0) -> None:
        code = run_cli(base, repo, *args)
        trace.append((" ".join(args), code))
        assert code == expect, f"{args} exited {code}"

    step("register")
    step("qualify", "--model", MODEL)
    step("pilot", "--model", MODEL)
    step("prescreen", "--model", MODEL)
    # Amendment A2: the autorater-assisted verifier workflow (Gate 1 no
    # longer blocks on human labels; human-audit runs at the end).
    step("gate1-dev", "--model", MODEL)
    packet = tree.data_dir("gate1") / "annotation_packet.jsonl"
    packet_hash_before = fs.read_json(
        tree.root / "gate1_dev.json")["packet_hash"]
    step("gate1-calibrate", "--model", MODEL, expect=1)   # not frozen yet
    # A2.1: the study-level freeze refuses until every designated (non-
    # terminal) replication has completed its development run.
    step("verifier-freeze", expect=1)
    for other in ("qwen3-4b", "qwen3-4b-instruct-2507",
                  "gemma-3n-e4b-it"):
        step("qualify", "--model", other)
        step("pilot", "--model", other)
        step("prescreen", "--model", other)
        step("gate1-dev", "--model", other)
    step("verifier-freeze")
    step("gate1-calibrate", "--model", MODEL)
    step("gate1", "--model", MODEL, expect=1)   # approval flag required
    step("gate1", "--model", MODEL, "--approve-autorater-calibration")
    # Post-Gate-1 verifier binding, end-to-end through the dispatcher:
    # a signed freeze manifest whose verifier hashes differ from the
    # current sources blocks the next downstream stage before any
    # mutation; restoring the true manifest re-enables the pipeline.
    from dci1v3.engine.dispatch import dispatch
    from dci1v3.engine.signing import sign_payload, verify_signed
    from dci1v3.errors import IntegrityError
    manifest_file = ctx.study_root / "verifier_freeze.json"
    manifest_before = manifest_file.read_text()
    drifted = verify_signed(json.loads(manifest_before),
                            ctx.signing_key_path, where="verifier_freeze")
    drifted["verifier_sources"]["target.py"] = "0" * 64
    manifest_file.write_text(json.dumps(
        sign_payload(drifted, ctx.signing_key_path)))
    with pytest.raises(IntegrityError, match="verifier code changed"):
        dispatch(ctx, "gate2a", MODEL)
    assert not tree.stage_record(C.STAGE_GATE2A).exists()
    assert not (tree.data_dir("gate2a") / "cache.jsonl").exists()
    manifest_file.write_text(manifest_before)
    step("gate2a", "--model", MODEL)
    step("gate2b", "--model", MODEL)
    step("freeze", "--model", MODEL)
    step("generate", "--model", MODEL)
    step("select-primary", "--model", MODEL)
    step("mask", "--model", MODEL)
    step("masked-analysis", "--model", MODEL)
    step("unmask", "--model", MODEL)
    step("final-analysis", "--model", MODEL)
    step("pseudo-runs", "--model", MODEL, "--runs", "25")
    step("greedy", "--model", MODEL)
    step("verify-evidence", "--model", MODEL)

    # The preserved human pathway: reviewer GUI -> export -> human-audit.
    # Zero-label and multi-label files must be rejected by the real parser.
    from dci1v3.annotation.store import (
        AnnotatorSession,
        export_annotations,
    )
    truth = make_synthetic_annotations(packet)
    bad_zero = base.parent / "bad_zero.json"
    fs.write_json(bad_zero, {"face_validity": [True]})
    step("human-audit", "--model", MODEL, "--annotations", str(bad_zero),
         expect=1)
    bad_three = base.parent / "bad_three.json"
    fs.write_json(bad_three, {
        **{item_id: labels * 3 for item_id, labels in truth.items()
           if item_id != "face_validity"},
        "face_validity": [True, True, True]})
    step("human-audit", "--model", MODEL, "--annotations",
         str(bad_three), expect=1)
    annotation_workspace = base.parent / "annotation_work"
    reviewer = AnnotatorSession(
        packet_path=packet, workspace=annotation_workspace,
        model=MODEL, annotator="A1")
    for display in range(1, len(reviewer.packet) + 1):
        item_id = reviewer._item_id_for_display(display)
        reviewer.record(display, label=truth[item_id][0])
    reviewer.finalize(face_validity=True)
    labels_path = export_annotations(annotation_workspace, MODEL, packet)
    step("human-audit", "--model", MODEL, "--annotations",
         str(labels_path))
    return {"ctx": ctx, "tree": tree, "base": base, "repo": repo,
            "trace": trace, "labels_path": labels_path, "packet": packet,
            "packet_hash_before": packet_hash_before}


def test_full_stage_sequence_reached(lifecycle):
    from dci1v3.engine.transitions import current_state
    assert current_state(lifecycle["tree"]) == C.STAGE_UNMASKED_ANALYSIS


def test_gate1_record_states_claim_boundaries(lifecycle):
    """The Gate 1 record carries the autorater basis, the exact
    strongest-claim sentence, and HUMAN_VALIDATION_UNAVAILABLE — and no
    implication that human validation occurred."""
    from dci1v3.engine.signing import verify_signed
    from dci1v3.engine.transitions import load_stage_record

    tree, ctx = lifecycle["tree"], lifecycle["ctx"]
    body = verify_signed(load_stage_record(tree, C.STAGE_GATE1),
                         ctx.signing_key_path, where="gate1")["body"]
    assert body["human_validation"] == "HUMAN_VALIDATION_UNAVAILABLE"
    assert body["strongest_claim"] == C.STRONGEST_CLAIM
    assert body["calibration_report"]["not_human_validation"] is True
    assert "wilson" not in json.dumps(
        body["calibration_report"]).lower()      # no human threshold reuse
    assert body["development_report"]["contingency"]
    # Untouched-calibration guarantee: dev and calibration judgments are
    # disjoint item sets matching the recorded split.
    autorater_dir = tree.data_dir("gate1") / "autorater"
    dev_ids = {json.loads(l)["item_id"] for l in
               (autorater_dir / "dev" / "judgments.jsonl")
               .read_text().splitlines()}
    cal_ids = {json.loads(l)["item_id"] for l in
               (autorater_dir / "calibration" / "judgments.jsonl")
               .read_text().splitlines()}
    assert dev_ids and cal_ids and not (dev_ids & cal_ids)
    split = fs.read_json(autorater_dir / "split.json")
    assert dev_ids == set(split["development"])
    assert cal_ids == set(split["calibration"])
    # The frozen human packet is untouched by the autorater workflow.
    from dci1v3.protocol.hashing import sha_text
    assert sha_text(Path(lifecycle["packet"]).read_text()) == \
        lifecycle["packet_hash_before"]


def test_verifier_freeze_binds_realised_boundary(lifecycle):
    """A2.1: the manifest records every designated development run with
    the realised pool/split/dev-record hashes actually on disk."""
    from dci1v3.engine.signing import verify_signed
    from dci1v3.engine.paths import model_tree
    from dci1v3.protocol.hashing import sha_file

    ctx = lifecycle["ctx"]
    manifest = verify_signed(
        fs.read_json(ctx.study_root / "verifier_freeze.json"),
        ctx.signing_key_path, where="verifier_freeze")
    included = manifest["development_runs"]["included"]
    assert sorted(included) == ["gemma-3n-e2b-it", "gemma-3n-e4b-it",
                                "qwen3-4b", "qwen3-4b-instruct-2507"]
    assert manifest["development_runs"]["excluded"] == {}
    for model_key, entry in included.items():
        tree = model_tree(ctx, model_key)
        dev = fs.read_json(tree.root / "gate1_dev.json")
        split = fs.read_json(tree.data_dir("gate1") / "autorater"
                             / "split.json")
        assert entry["pool_hash"] == dev["pool_hash"]
        assert entry["split_hash"] == split["split_hash"]
        assert entry["dev_record_hash"] == sha_file(
            tree.root / "gate1_dev.json")


def test_gate1_basis_machine_distinguishable(lifecycle):
    """A2.1: PASSED never implies human validation — the basis marker and
    the effective human-validation status are machine-readable at every
    downstream reader."""
    from dci1v3.engine.signing import verify_signed
    from dci1v3.engine.transitions import load_stage_record
    from dci1v3.stages.gate1 import human_validation_status

    tree, ctx = lifecycle["tree"], lifecycle["ctx"]
    gate1 = verify_signed(load_stage_record(tree, C.STAGE_GATE1),
                          ctx.signing_key_path, where="gate1")["body"]
    assert gate1["measurement_basis"] == "autorater_calibration_approved"
    assert gate1["measurement_basis"] != "human_validated"
    freeze = verify_signed(load_stage_record(tree, C.STAGE_FREEZE),
                           ctx.signing_key_path, where="freeze")["body"]
    basis = freeze["measurement_basis"]
    assert basis["measurement_basis"] == "autorater_calibration_approved"
    # The freeze ran before the human audit: effective status at freeze
    # time was UNAVAILABLE, sourced from the gate record.
    assert basis["human_validation"]["human_validation"] == \
        "HUMAN_VALIDATION_UNAVAILABLE"
    # After the audit (end of lifecycle), the effective status flips —
    # sourced from the audit record, never from the PASSED state.
    effective = human_validation_status(tree)
    assert effective == {"human_validation": "HUMAN_VALIDATION_COMPLETE",
                         "source": "human_audit",
                         "outcome": "ESTABLISHED"}


def test_zz_exposed_calibration_cannot_rerun(lifecycle):
    """A2.1: calibration is one-shot through the ledger — deleting the
    record file cannot re-present the exposed holdout as fresh."""
    import shutil as _shutil
    tree = lifecycle["tree"]
    base, repo = lifecycle["base"], lifecycle["repo"]
    record = tree.root / "gate1_calibration.json"
    durable_copy = tree.durable / "gate1_calibration.json"
    record.unlink()
    try:
        assert run_cli(base, repo, "gate1-calibrate",
                       "--model", MODEL) == 1
        assert not record.exists()          # refused before any mutation
    finally:
        _shutil.copy2(durable_copy, record)


def test_human_audit_bounds_recompute_from_single_labels(lifecycle):
    """The preserved human pathway: audit bounds equal an independent
    recomputation from the single-annotator export."""
    from dci1v3.analysis.stats import wilson_upper_one_sided
    from dci1v3.verifiers.target import s0_count

    tree = lifecycle["tree"]
    annotations = fs.read_json(lifecycle["labels_path"])
    assert all(len(labels) == 1 for item_id, labels in annotations.items()
               if item_id != "face_validity")
    audit = fs.read_json(tree.root / "human_audit.json")
    assert audit["outcome"] == "ESTABLISHED"
    assert audit["human_validation"] == "HUMAN_VALIDATION_COMPLETE"
    recomputed: dict[str, dict[str, int]] = {
        "pass": {"cases": 0, "disagreements": 0},
        "fail": {"cases": 0, "disagreements": 0}}
    for line in Path(lifecycle["packet"]).read_text().splitlines():
        row = json.loads(line)
        verifier = ("pass" if s0_count(row["response_text"]) == row["n"]
                    else "fail")
        recomputed[verifier]["cases"] += 1
        if annotations[row["item_id"]][0] != verifier:
            recomputed[verifier]["disagreements"] += 1
    for cls, cell in recomputed.items():
        recorded = audit["class_bounds"][cls]
        assert recorded["cases"] == cell["cases"]
        assert recorded["disagreements"] == cell["disagreements"]
        assert recorded["wilson_upper"] == pytest.approx(
            wilson_upper_one_sided(cell["disagreements"], cell["cases"]))
    assert audit["face_validity"] == {"agreements": 1, "of": 1}


def test_confirmatory_matrix_counts(lifecycle):
    tree = lifecycle["tree"]
    cache = tree.data_dir("confirmatory") / "cache.jsonl"
    rows = cache.read_text().count("\n")
    assert rows == C.N_CACHED_DRAWS
    primaries = (tree.data_dir("confirmatory")
                 / "primary_rows.jsonl").read_text().count("\n")
    assert primaries == C.N_PRIMARY


def test_final_result_and_claims_exist(lifecycle):
    tree = lifecycle["tree"]
    result = fs.read_json(
        tree.data_dir("analysis") / "unmasked" / "result.json")
    assert set(result["families"]) == set(C.FAMILY_SIZES)
    for name, claim in result["primary_claims"].items():
        assert claim["direction"] is not None or claim["status"] != "OK"
    assert result["blocks"] == C.N_BLOCKS
    assert result["resamples"] == C.BOOTSTRAP_RESAMPLES


def test_rows_traceable_to_frozen_verifier(lifecycle):
    """Verifier-binding regression (E): every stored verdict row records
    the verifier_source_hash of the verifier that scored it, and that
    hash derives from the freeze manifest's verdict modules — stored
    evidence stays traceable to the Gate-1-frozen instrument."""
    from dci1v3.engine.signing import verify_signed
    from dci1v3.protocol.hashing import sha_obj
    from dci1v3.verifiers import verifier_source_hash

    tree, ctx = lifecycle["tree"], lifecycle["ctx"]
    manifest = verify_signed(
        fs.read_json(ctx.study_root / "verifier_freeze.json"),
        ctx.signing_key_path, where="verifier_freeze")
    frozen_hash = sha_obj({name: manifest["verifier_sources"][name]
                           for name in ("words.py", "target.py",
                                        "families.py", "boundary.py")})
    assert frozen_hash == verifier_source_hash()
    rows = fs.read_jsonl(tree.data_dir("confirmatory") / "cache.jsonl")
    assert rows and all(
        row["verdicts"]["verifier_source_hash"] == frozen_hash
        for row in rows)


def test_pilot_and_confirmatory_share_production_paths(lifecycle):
    """Item 64: identical production code for generation, caching, storage,
    selection, masking, verification, and analysis."""
    from dci1v3.stages import confirmatory as conf
    from dci1v3.stages import pilot as pil
    import dci1v3.generation.cache as cache_mod
    assert pil.fill_cache is cache_mod.fill_cache
    assert conf.fill_cache is cache_mod.fill_cache
    assert pil.select_primary is conf.select_primary
    assert pil.masking is conf.masking
    assert pil.analyse.__module__ == "dci1v3.analysis.run"
    assert conf.analyse.__module__ == "dci1v3.analysis.run"


def test_second_mask_and_unmask_fail_before_mutation(lifecycle):
    base, repo = lifecycle["base"], lifecycle["repo"]
    assert run_cli(base, repo, "mask", "--model", MODEL) == 1
    assert run_cli(base, repo, "unmask", "--model", MODEL) == 1
    tree = lifecycle["tree"]
    events = fs.read_jsonl(tree.mask_event_log("confirmatory_mask"))
    assert sum(1 for e in events if e["event"] == "mask_created") == 1
    assert sum(1 for e in events if e["event"] == "unmasked") == 1


def test_concurrent_duplicate_cache_write_fails(lifecycle):
    from dci1v3.engine.store import CacheWriter
    from dci1v3.errors import IntegrityError
    tree = lifecycle["tree"]
    writer = CacheWriter(tree.data_dir("confirmatory") / "cache.jsonl")
    first = fs.read_jsonl(writer.path)[0]
    size_before = writer.path.stat().st_size
    with pytest.raises(IntegrityError, match="duplicate cached-draw"):
        writer.append([{k: v for k, v in first.items()
                        if k != "record_hash"}])
    assert writer.path.stat().st_size == size_before


def test_dirty_worktree_blocks_artifact_production(lifecycle, synthetic_repo):
    marker = synthetic_repo / "drift.txt"
    marker.write_text("dirty")
    try:
        assert run_cli(lifecycle["base"], synthetic_repo,
                       "pseudo-runs", "--model", MODEL, "--runs", "2") == 1
    finally:
        marker.unlink()


def test_tampered_predecessor_record_and_signature_fail(lifecycle):
    tree = lifecycle["tree"]
    base, repo = lifecycle["base"], lifecycle["repo"]
    path = tree.stage_record(C.STAGE_FREEZE)
    original = path.read_text()
    try:
        record = json.loads(original)
        record["payload"]["body"]["n_star"] = 99
        path.write_text(json.dumps(record))
        assert run_cli(base, repo, "verify-evidence",
                       "--model", MODEL) == 1
        record = json.loads(original)
        record["signature"] = "e" * 64
        path.write_text(json.dumps(record))
        assert run_cli(base, repo, "verify-evidence",
                       "--model", MODEL) == 1
    finally:
        path.write_text(original)
    assert run_cli(base, repo, "verify-evidence", "--model", MODEL) == 0


def test_durable_mirror_complete(lifecycle):
    from dci1v3.engine.store import assert_replicated
    tree = lifecycle["tree"]
    assert_replicated(tree.root, tree.durable)


def test_masked_view_hides_arm_identifiers(lifecycle):
    from dci1v3.stages.masking import MASKED_VIEW_EXCLUDED, masked_rows
    rows = masked_rows(lifecycle["tree"], "confirmatory_mask")
    assert len(rows) == C.N_PRIMARY
    for row in rows[:50]:
        for hidden in MASKED_VIEW_EXCLUDED:
            assert hidden not in row


def test_pseudo_and_greedy_records_exist(lifecycle):
    tree = lifecycle["tree"]
    pseudo = fs.read_json(tree.root / "pseudo_runs.json")
    assert pseudo["summary"][C.TARGET_FIRST]["runs"] == 25
    assert pseudo["primary_selection_untouched"]
    greedy = fs.read_json(tree.root / "greedy_run.json")
    assert greedy["generations"] == C.GREEDY_GENERATIONS


def test_restore_drill_from_durable(lifecycle, tmp_path):
    """Deleting the local tree and restoring from durable storage
    reproduces every committed byte."""
    from dci1v3.engine.store import fingerprint_tree, restore
    tree = lifecycle["tree"]
    scratch = tmp_path / "restored"
    restore(tree.durable, scratch)
    durable_prints = fingerprint_tree(tree.durable)
    scratch_prints = fingerprint_tree(scratch)
    assert durable_prints == scratch_prints
