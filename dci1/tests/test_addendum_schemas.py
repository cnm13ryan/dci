"""Addendum A §6 schema battery (SC-01 … SC-09)."""
import pytest

pytestmark = pytest.mark.cpu

import pyarrow as pa
import pyarrow.parquet as pq
from helpers import SPEC
from helpers_addendum import derive, full_tree

from dci1 import flow
from dci1.protocol.constants import ProtocolError, study_config
from dci1.tables.build import read_table, write_parquet
from dci1.tables.schemas import PRIMARY_KEYS, SCHEMA_VERSIONS, validate_columns


@pytest.fixture(scope="module")
def derived(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("derived")
    tree, blocks, cells, config, record_hash = full_tree(tmp)
    result = derive(tree, blocks, cells, config, record_hash, stage="final",
                    drill=True)
    return tree, blocks, cells, config, record_hash, result


def test_sc01_accepted_blocks_times_six_no_nulls(derived):
    tree, blocks, *_ = derived
    table = read_table(tree.derived_primary / "accepted.parquet", "accepted")
    assert table.num_rows == len(blocks) * 6
    for column in table.column_names:
        assert table.column(column).null_count == 0
    assert "response" not in table.column_names       # R29: no raw text


def test_sc02_duplicate_primary_key_rejected(derived):
    tree, *_ = derived
    table = read_table(tree.derived_primary / "accepted.parquet", "accepted")
    rows = table.to_pylist()
    with pytest.raises(ProtocolError, match="duplicate primary key"):
        write_parquet(tree.root / "dup.parquet", "accepted",
                      rows + [rows[0]])


def test_sc03_response_retrieved_from_cache(derived):
    tree, *_ = derived
    from dci1.tables.build import response_lookup

    table = read_table(tree.derived_primary / "accepted.parquet", "accepted")
    cache = response_lookup(tree)
    for row in table.to_pylist():
        member = cache[row["cache_record_id"]]
        assert member["response_content_hash"] == row["response_content_hash"]


def test_sc04_scored_joins_accepted_one_to_one(derived):
    tree, blocks, *_ = derived
    accepted = read_table(tree.derived_primary / "accepted.parquet",
                          "accepted").to_pylist()
    scored = read_table(tree.derived_primary / "scored.parquet",
                        "scored").to_pylist()
    cells = {(r["block_id"], r["arm"]) for r in accepted}
    for row in scored:
        assert (row["block_id"], row["arm"]) in cells
        assert row["verifier_id"] in {"target_s0", "target_s1", "target_s2",
                                      "target_s3", "added"}
    target_rows = [r for r in scored if r["verifier_id"] == "target_s0"]
    assert len(target_rows) == len(accepted)          # one per observation


def test_sc05_analysis_n_observations_rule(derived):
    tree, blocks, *_ = derived
    analysis = read_table(tree.derived_primary / "analysis.parquet",
                          "analysis").to_pylist()
    assert analysis
    for row in analysis:
        assert row["n_observations"] == row["n_blocks"] * 6
        assert row["ci_method"] == "block_bootstrap"


def test_sc06_header_columns_present(derived):
    tree, *_ = derived
    for name in ("accepted", "scored", "analysis"):
        path = tree.derived_primary / f"{name}.parquet"
        table = read_table(path, name)
        for column in ("study_id", "freeze_id", "schema_name",
                       "schema_version", "addendum_version", "writer_commit",
                       "writer_dirty", "created_at_utc"):
            assert column in table.column_names
        assert set(table.column("schema_name").to_pylist()) == {name}


def test_sc07_unknown_columns_and_versions_rejected(derived, tmp_path):
    tree, *_ = derived
    with pytest.raises(ProtocolError, match="unknown columns"):
        validate_columns("accepted", ["study_id", "surprise_column"])
    # a parquet with a wrong schema_version is refused at read
    path = tree.derived_primary / "accepted.parquet"
    table = pq.read_table(path)
    bad = table.replace_schema_metadata({"schema_name": "accepted",
                                         "schema_version": "999.0.0"})
    bad_path = tmp_path / "bad.parquet"
    pq.write_table(bad, bad_path)
    with pytest.raises(ProtocolError, match="fail closed"):
        read_table(bad_path, "accepted")
    # a retyped column is refused (the typed schema rejects the conversion)
    with pytest.raises((ProtocolError, pa.lib.ArrowInvalid)):
        from dci1.tables.build import write_parquet as wp

        wp(tmp_path / "again.parquet", "accepted",
           [dict(r, token_count=str(r["token_count"]))
            for r in table.to_pylist()])


def test_sc08_freeze_record_addendum_fields(monkeypatch):
    from dci1.freeze import record as freeze_module
    from dci1.freeze.record import ADDENDUM_FIELDS

    gate2 = {"passed": True, "selected_n": 2, "selected_m": 8,
             "references": ["C1", "C3", "C10"], "certificates": []}
    record = freeze_module.build_freeze_record(
        SPEC, config=study_config(), gate0={"passed": True},
        gate1={"status": "PENDING_HUMAN", "passed": False}, gate2=gate2,
        qualification={"verdict": "QUALIFIED"},
        topic_split_ids={"calibration": [], "confirmatory": [],
                         "sequestered": []},
        block_plan_hash="h" * 64,
        environment={"environment_digest": "x", "gcn_archs": []})
    addendum = record["addendum"]
    for field in ADDENDUM_FIELDS:
        assert field in addendum
    assert addendum["storage_format_profile"] == "addendum-a-default-v1"
    assert addendum["manifest_hash_algorithm"] == "sha256"
    assert addendum["masking_scheme_id"] == \
        "v2-s19-block-primary-permutation"
    assert addendum["masking_root_seed"] is None      # R40: v2 precedence
    assert addendum["schema_versions"] == SCHEMA_VERSIONS
    # missing addendum block fails closed
    broken = {k: v for k, v in record.items()
              if k not in ("addendum", "freeze_hash")}
    with pytest.raises(ProtocolError, match="Addendum"):
        freeze_module.validate_freeze({**broken, "addendum": {}})


def test_sc09_pseudo_run_rows_marked_sensitivity(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    selection = flow.select_pseudo(tree, SPEC, cells, stream="confirmatory",
                                  config=config, run_index=2)
    assert tree.pseudo_selection(2).exists()
    assert all(r["pseudo_run_id"] == "pseudo_0002" for r in selection)
    assert all(r["resampling_seed"] is not None for r in selection)
    from dci1.evidence.sealing import writer_identity
    from dci1.tables.build import build_accepted, response_lookup

    rows = build_accepted(
        tree, spec=SPEC, blocks=blocks, selection_rows=selection,
        cache_by_id=response_lookup(tree), freeze_record_hash=record_hash,
        created_at="1970-01-01T00:00:00Z", writer=writer_identity(),
        selection_source="pseudo_run", pseudo_run_id="pseudo_0002")
    assert all(r["selection_source"] == "pseudo_run" for r in rows)
    assert all(r["resampling_seed"] >= 0 for r in rows)


def test_primary_keys_declared_for_all_tables():
    assert set(PRIMARY_KEYS) == {"accepted", "scored", "analysis"}


def test_codebook_name_mapping_complete():
    """Every addendum-renamed scientific column appears in the reconciliation
    mapping table, and the mapping hash is stable."""
    from pathlib import Path

    doc = (Path(__file__).resolve().parents[1] / "docs"
           / "addendum_a_reconciliation.md").read_text()
    marker = "## Codebook name mapping"
    section = doc[doc.index(marker):]
    for name in ("record_hash", "cache_record_id", "presentation_order",
                 "stratum_id", "wording_id", "selected_pool_index",
                 "verdict", "score_value", "manipulation_check_value",
                 "compliance_flag", "failure_taxonomy_code"):
        assert f"| {name} |" in section, name
    from dci1.freeze.record import _codebook_mapping_hash

    assert _codebook_mapping_hash() == _codebook_mapping_hash()
