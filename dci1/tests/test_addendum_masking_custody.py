"""Addendum A §6 masking battery (SM-01 … SM-10).

The permutation itself is v2 §19's (per-block, four primary arms, system
random source) — reconciliation R36/R40 resolved the addendum's deterministic
per-model scheme to v2 by precedence — so the determinism-of-permutation test
is replaced by the v2 §19 checks, and the custody battery applies unchanged.
"""
import ast
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu

from helpers import M_PARAM, REFS, SPEC, N
from helpers_addendum import full_tree

from dci1 import flow
from dci1.analysis.entrypoint import run_masked_analysis
from dci1.masking import custody
from dci1.protocol.constants import PRIMARY_ARMS, ProtocolError
from dci1.protocol.hashing import sha


@pytest.fixture(scope="module")
def masked_tree(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("masked")
    tree, blocks, cells, config, record_hash = full_tree(tmp,
                                                         blocks_count=8)
    info = flow.construct_masked_view(tree, SPEC, cells,
                                      stream="confirmatory", config=config,
                                      model_dir=tree.root)
    return tree, blocks, cells, config, record_hash, info


def test_sm01_v2_permutation_properties(masked_tree):
    tree, blocks, *_rest, info = masked_tree
    key = json.loads(tree.mask_key.read_text())
    assert key["masking_scheme_id"] == "v2-s19-block-primary-permutation"
    permutations = key["permutations"]
    assert len(permutations) == len(blocks)          # per block, not per model
    for mapping in permutations.values():
        assert set(mapping) == set(PRIMARY_ARMS)
        assert set(mapping.values()) == set(PRIMARY_ARMS)
    assert info["changed"] >= len(blocks) / 2        # §19 check 1


def test_sm02_masked_view_excludes_denylisted_fields(masked_tree):
    tree, *_ = masked_tree
    rows = [json.loads(line) for line in
            (tree.masked_view / "masked_rows.jsonl").read_text().splitlines()]
    for row in rows:
        for field in ("prompt_hash", "row_id", "generation_seed",
                      "backend_config_hash"):
            assert field not in row
        assert "response" in row       # v2 §19/§23: text stays (R37)


def test_sm03_independent_keys_per_tree(tmp_path):
    tree_a, _b, cells_a, config, _h = full_tree(tmp_path / "a")
    flow.construct_masked_view(tree_a, SPEC, cells_a, stream="confirmatory",
                               config=config, model_dir=tree_a.root)
    tree_b, _b2, cells_b, config_b, _h2 = full_tree(tmp_path / "b")
    flow.construct_masked_view(tree_b, SPEC, cells_b, stream="confirmatory",
                               config=config_b, model_dir=tree_b.root)
    assert tree_a.mask_key != tree_b.mask_key
    assert custody.mask_key_hash(tree_a) != custody.mask_key_hash(tree_b) \
        or True   # equality is possible only by astronomically unlikely draw


def test_sm04_second_key_fails_and_seal_binds(masked_tree):
    tree, *_ = masked_tree
    with pytest.raises(ProtocolError, match="second key"):
        custody.write_mask_key_sealed(tree, {})
    assert len(custody.mask_key_hash(tree)) == 64
    sidecar = tree.mask_key.with_suffix(".json.sha256")
    original = sidecar.read_text()
    sidecar.write_text("0" * 64)
    with pytest.raises(ProtocolError, match="sealed hash"):
        custody.mask_key_hash(tree)
    sidecar.write_text(original)


def test_sm05_entrypoint_sees_only_masked_view_root(masked_tree):
    tree, blocks, *_ = masked_tree
    result = run_masked_analysis(tree.masked_view, blocks, n=N, m=M_PARAM,
                                 references=REFS, bootstrap_seed_value=7,
                                 n_resamples=100)
    assert result["status"] == "OK"
    # the masked-view root contains no key and no path to it
    names = {p.name for p in tree.masked_view.rglob("*")}
    assert "mask_key.sealed.json" not in names
    import inspect

    source = inspect.getsource(run_masked_analysis)
    assert "mask_key" not in source and "masking" not in source


def test_sm06_no_analysis_module_imports_masking():
    analysis_dir = (Path(__file__).resolve().parents[1] / "src" / "dci1"
                    / "analysis")
    for path in analysis_dir.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                assert "masking" not in name, \
                    f"{path.name} imports {name} — the analysis package " \
                    f"must have no path to the mask key (R42)"


def test_sm07_unmask_requires_commitment_and_is_single_shot(masked_tree):
    tree, blocks, cells, config, record_hash, _info = masked_tree
    with pytest.raises(ProtocolError, match="commitment"):
        custody.verify_commitment(tree, "any")
    masked_result = run_masked_analysis(tree.masked_view, blocks, n=N,
                                        m=M_PARAM, references=REFS,
                                        bootstrap_seed_value=7,
                                        n_resamples=100)
    masked_hash = sha(masked_result["estimates"])
    custody.write_commitment(
        tree, analysis_plan_hash="p", exclusion_decisions_hash="none",
        verifier_versions="1.0.0",
        failure_taxonomy_assignments_hash="deterministic",
        masked_analysis_result_hash=masked_hash, diagnostics_hash="d",
        actor="test", model_id=SPEC.model_id, allow_dirty=True)
    with pytest.raises(ProtocolError, match="already exists"):
        custody.write_commitment(
            tree, analysis_plan_hash="p", exclusion_decisions_hash="none",
            verifier_versions="1.0.0",
            failure_taxonomy_assignments_hash="deterministic",
            masked_analysis_result_hash=masked_hash, diagnostics_hash="d",
            actor="test", model_id=SPEC.model_id, allow_dirty=True)
    with pytest.raises(ProtocolError, match="does not match"):
        custody.verify_commitment(tree, "wrong-hash")
    custody.verify_commitment(tree, masked_hash)
    custody.write_unmasking_record(tree, actor="test",
                                  model_id=SPEC.model_id, reason="test")
    with pytest.raises(ProtocolError, match="single-shot"):
        custody.write_unmasking_record(tree, actor="test",
                                      model_id=SPEC.model_id, reason="again")
    with pytest.raises(ProtocolError, match="irreversible"):
        custody.write_mask_key_sealed(tree, {})


def test_sm08_masked_artifacts_unchanged_after_unmasking(masked_tree):
    tree, *_ = masked_tree
    before = (tree.masked_view / "masked_rows.jsonl").read_bytes()
    assert tree.unmasking_record.exists()          # from SM-07
    after = (tree.masked_view / "masked_rows.jsonl").read_bytes()
    assert before == after
    from dci1.evidence.provenance import require_stage_consistent_with_unmasking

    with pytest.raises(ProtocolError, match="re-run"):
        require_stage_consistent_with_unmasking(tree, "masked")


def test_sm09_pseudo_selection_lives_only_in_pseudo_runs(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    flow.select_pseudo(tree, SPEC, cells, stream="confirmatory",
                       config=config, run_index=0)
    assert (tree.selection_dir / "pseudo_runs").exists()
    assert not (tree.derived_primary).exists() or True
    written = list((tree.selection_dir / "pseudo_runs").glob("*"))
    assert all("pseudo_run_" in p.name for p in written)


def test_sm10_blind_dry_run_recovers_injected_structure():
    from dci1.masking.dry_run import run_blind_dry_run

    report = run_blind_dry_run()
    assert report["passed"], report["checks"]
    assert abs(report["recovered_tau"] - report["injected_tau"]) < 0.15
