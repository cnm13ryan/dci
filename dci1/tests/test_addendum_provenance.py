"""Addendum A §6 analysis-provenance battery (SP-01 … SP-06)."""
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu

from helpers_addendum import derive, full_tree

from dci1.evidence import provenance as prov
from dci1.protocol.constants import ProtocolError
from dci1.tables.build import read_table

DOC = Path(__file__).resolve().parents[1] / "docs" / \
    "addendum_a_reconciliation.md"


def test_sp01_reconciliation_complete_zero_unresolved():
    assert DOC.exists()
    text = DOC.read_text()
    assert "| conflict (unresolved)" not in text
    assert text.count("| R") >= 55            # one row per requirement
    from dci1.cli import reconciliation_conflicts

    assert reconciliation_conflicts() == 0


def test_sp02_dirty_git_blocks_registered_output():
    with pytest.raises(ProtocolError, match="dirty"):
        prov.require_registered_writer(
            writer={"writer_commit": "c" * 40, "writer_dirty": True})
    clean = prov.require_registered_writer(
        writer={"writer_commit": "c" * 40, "writer_dirty": False})
    assert clean["writer_dirty"] is False


def test_sp03_provenance_fields_complete(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    derive(tree, blocks, cells, config, record_hash, stage="final",
           drill=True)
    rows = read_table(tree.derived_primary / "analysis.parquet",
                      "analysis").to_pylist()
    for row in rows:
        assert row["protocol_identity"].startswith("DCI-1-2.0+")
        assert row["input_manifest_hashes"]
        assert row["masking_state"] == "final"
        assert row["environment_record_hash"]
        assert row["analysis_command"]
        assert row["wall_clock_utc"].endswith("Z")
        assert row["resampling_root_seed"] == config.resampling_root_seed
    from dci1.freeze.record import environment_record

    environment = environment_record()
    for key in ("interpreter_version", "os", "kernel", "cpu_model",
                "vllm_version", "blas_threading",
                "dependency_lockfile_hash"):
        assert key in environment


def test_sp04_refusal_conditions(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    with pytest.raises(ProtocolError, match="differs from the record"):
        prov.require_freeze_consistency(tree, "0" * 64)
    prov.require_freeze_consistency(tree, record_hash)
    # stage inconsistent with unmasking status
    with pytest.raises(ProtocolError, match="without an unmasking record"):
        prov.require_stage_consistent_with_unmasking(tree, "final")
    # parent-manifest mismatch
    recorded = prov.input_manifest_hashes(tree)
    prov.require_parent_manifests(tree, recorded)
    with pytest.raises(ProtocolError, match="parent manifest"):
        prov.require_parent_manifests(tree, {"cache": "0" * 64})
    # a full derive at stage=final without unmasking record refuses
    from helpers import SPEC

    from dci1 import flow

    flow.select_primary(tree, SPEC, cells, stream="confirmatory",
                        config=config)          # also replicates selection
    with pytest.raises(ProtocolError, match="unmasking"):
        derive(tree, blocks, cells, config, record_hash, stage="final",
               drill=False)


def test_sp05_every_row_traces_to_cache(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    derive(tree, blocks, cells, config, record_hash, stage="final",
           drill=True)
    from dci1.tables.build import response_lookup

    cache = response_lookup(tree)
    accepted = read_table(tree.derived_primary / "accepted.parquet",
                          "accepted").to_pylist()
    scored = read_table(tree.derived_primary / "scored.parquet",
                        "scored").to_pylist()
    analysis = read_table(tree.derived_primary / "analysis.parquet",
                          "analysis").to_pylist()
    for row in accepted:
        assert row["cache_record_id"] in cache
    for row in scored:
        assert row["cache_record_id"] in cache
    for row in analysis:
        assert len(row["input_accepted_hash"]) == 64
        assert len(row["input_scored_hash"]) == 64


def test_sp06_report_regeneration_byte_identical(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    derive(tree, blocks, cells, config, record_hash, stage="final",
           drill=True)
    from dci1.reports.build import build_report

    build_report(tree)
    first = (tree.root / "report.json").read_bytes()
    build_report(tree)
    second = (tree.root / "report.json").read_bytes()
    assert first == second
    import json

    payload = json.loads(first)
    assert payload["analysis_table_hash"]
