"""Addendum A §6 storage-integrity battery (SA-01 … SA-12)."""
import json
import os
import shutil

import pytest

pytestmark = pytest.mark.cpu

from helpers import SPEC, small_config
from helpers_addendum import derive, fill_cache, full_tree, make_tree

from dci1 import flow
from dci1.evidence import store
from dci1.evidence.layout import StudyTree
from dci1.evidence.sealing import (
    CacheWriter,
    StageLock,
    artifact_header,
    replicate_raw_layers,
    seal_stage,
    utc_now,
    verify_stage,
)
from dci1.evidence.store import atomic_write, write_json
from dci1.evidence.verify import restore_drill, verify_evidence
from dci1.protocol.constants import ProtocolError


def test_sa01_interrupted_write_leaves_no_final_artifact(tmp_path,
                                                         monkeypatch):
    target = tmp_path / "out.json"

    def failing_replace(src, dst):
        raise OSError("interrupted")

    monkeypatch.setattr(os, "replace", failing_replace)
    with pytest.raises(OSError):
        atomic_write(target, "payload")
    monkeypatch.undo()
    assert not target.exists()
    assert not list(tmp_path.glob("*.json"))       # no partial artifact


def test_sa02_concurrent_stage_writers_rejected(tmp_path):
    tree, _b, _c = make_tree(tmp_path)
    tree.root.mkdir(parents=True, exist_ok=True)
    with StageLock(tree, "cache"), pytest.raises(ProtocolError, match="concurrent"):
        StageLock(tree, "cache").__enter__()


def test_sa03_cache_appends_preserve_every_previous_byte(tmp_path):
    config = small_config(pool_size=2)
    tree, blocks, cells = make_tree(tmp_path, config=config)
    writer = CacheWriter(tree.cache_file)
    writer.append([{"row_id": "a", "payload": "x"}])
    before = tree.cache_file.read_bytes()
    writer.append([{"row_id": "b", "payload": "y"}])
    after = tree.cache_file.read_bytes()
    assert after.startswith(before)
    assert after.count(b"\n") == 2                 # one record per line
    with pytest.raises(ProtocolError, match="append-once"):
        writer.append([{"row_id": "a", "payload": "z"}])


def test_sa04_record_hash_present_and_verified(tmp_path):
    tree, _b, _c = make_tree(tmp_path)
    writer = CacheWriter(tree.cache_file)
    writer.append([{"row_id": "a", "payload": "x"}])
    row = writer.rows()[0]
    assert "record_hash" in row and len(row["record_hash"]) == 64
    writer.verify_hashes()
    mutated = tree.cache_file.read_text().replace('"x"', '"y"')
    tree.cache_file.write_text(mutated)
    with pytest.raises(ProtocolError, match="mutated"):
        writer.verify_hashes()


def test_sa05_seal_manifest_and_flipped_byte_detected(tmp_path):
    config = small_config()
    tree, blocks, cells = make_tree(tmp_path, config=config)
    fill_cache(tree, cells, config)
    report = seal_stage(tree, "cache")
    assert report["files"] >= 1
    manifest = [json.loads(line) for line in
                (tree.cache_dir / "MANIFEST.jsonl").read_text().splitlines()]
    for entry in manifest:
        assert set(entry) == {"path", "sha256", "byte_length",
                              "record_count"}
    verify_stage(tree, "cache")
    text = tree.cache_file.read_text()
    tree.cache_file.write_text(text.replace("However", "Xowever", 1))
    with pytest.raises(ProtocolError, match="manifest entry"):
        verify_stage(tree, "cache")


def test_sa06_sealed_stage_rejects_writes(tmp_path):
    config = small_config(pool_size=1)
    tree, blocks, cells = make_tree(tmp_path, config=config)
    fill_cache(tree, cells, config)
    seal_stage(tree, "cache")
    with pytest.raises(ProtocolError, match="sealed"):
        CacheWriter(tree.cache_file).append([{"row_id": "new"}])
    with pytest.raises(ProtocolError, match="sealed"):
        seal_stage(tree, "cache")


def test_sa07_deterministic_json_and_timestamps(tmp_path):
    path = tmp_path / "record.json"
    write_json(path, {"b": 2, "a": 1})
    assert path.read_text() == '{\n  "a": 1,\n  "b": 2\n}'
    stamp = utc_now()
    assert stamp.endswith("Z") and "T" in stamp


def test_sa08_artifact_header_complete(tmp_path):
    tree, _b, _c = make_tree(tmp_path)
    header = artifact_header(tree, model_id=SPEC.model_id,
                             schema_name="accepted", schema_version="1.0.0",
                             freeze_record_hash="h" * 64,
                             writer={"writer_commit": "c" * 40,
                                     "writer_dirty": False})
    assert set(header) == {"study_id", "model_id", "freeze_id",
                           "freeze_record_hash", "schema_name",
                           "schema_version", "addendum_version",
                           "writer_commit", "writer_dirty",
                           "created_at_utc"}


def test_sa09_layout_paths(tmp_path):
    tree = StudyTree(model_slug="m", freeze_id="f", base=tmp_path)
    assert tree.cache_file == \
        tmp_path / "dci1-v2" / "m" / "f" / "cache" / "generations.jsonl"
    assert tree.pseudo_selection(3).name == "pseudo_run_0003.jsonl"
    assert tree.mask_key.name == "mask_key.sealed.json"
    assert "primary" in str(tree.primary_selection)


def test_sa10_verify_evidence_end_to_end(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    report = verify_evidence(tree)
    assert report["ok"]
    text = tree.cache_file.read_text()
    tree.cache_file.write_text(text.replace("However", "Xowever", 1))
    with pytest.raises(ProtocolError):
        verify_evidence(tree)


def test_sa11_selection_refuses_without_replication(tmp_path):
    config = small_config()
    tree, blocks, cells = make_tree(tmp_path, config=config)
    flow.write_prompts(tree, cells)
    fill_cache(tree, cells, config)
    seal_stage(tree, "cache")
    with pytest.raises(ProtocolError, match="replicat"):
        flow.select_primary(tree, SPEC, cells, stream="confirmatory",
                            config=config)
    replicate_raw_layers(tree)
    assert flow.select_primary(tree, SPEC, cells, stream="confirmatory",
                               config=config)


def test_sa12_restore_drill_byte_identical(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    derive(tree, blocks, cells, config, record_hash, stage="final",
           drill=True)
    replicate_raw_layers(tree)

    def rebuild(restored):
        derive(restored, blocks, cells, config, record_hash, stage="final",
               drill=True)

    drill = restore_drill(tree, rebuild, tmp_path / "clean_ws")
    assert drill["byte_identical"]


def test_deterministic_runs_produce_byte_identical_artifacts(tmp_path):
    tree, blocks, cells, config, record_hash = full_tree(tmp_path)
    derive(tree, blocks, cells, config, record_hash, stage="final",
           drill=True)
    first = store.fingerprint_tree(tree.root / "derived")
    shutil.rmtree(tree.root / "derived")
    derive(tree, blocks, cells, config, record_hash, stage="final",
           drill=True)
    second = store.fingerprint_tree(tree.root / "derived")
    assert first == second
