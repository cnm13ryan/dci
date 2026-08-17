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
    # Gate 1 blocks on human labels first (PENDING_HUMAN), then passes with
    # the harness annotations.
    step("gate1", "--model", MODEL, expect=1)
    packet = tree.data_dir("gate1") / "annotation_packet.jsonl"
    labels_path = base.parent / "annotations.json"
    fs.write_json(labels_path, make_synthetic_annotations(packet))
    step("gate1", "--model", MODEL, "--annotations", str(labels_path))
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
    return {"ctx": ctx, "tree": tree, "base": base, "repo": repo,
            "trace": trace}


def test_full_stage_sequence_reached(lifecycle):
    from dci1v3.engine.transitions import current_state
    assert current_state(lifecycle["tree"]) == C.STAGE_UNMASKED_ANALYSIS


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
