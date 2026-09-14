"""The committed evidence subset is what it says it is.

``fixtures/evidence_subset`` carries the signed records two evidence checks
need, so they run in CI and a fresh clone instead of skipping
(``tools/v8_ci_evidence_fixture.py``). A fixture standing in for evidence is
only as good as the proof that it is that evidence, so:

* in CI, every committed record matches its manifest entry, and its content
  is the signed payload the manifest names (``sha_obj`` of the record equals
  its ``record_hash``, the hash the signature covers);
* the Gate-2 record is the one the committed chance cache was built from, so
  the corrected-basis replay pairs a record with its own cache;
* the backtest subset is every record ``load_replication`` opens, and the
  eligibility extract is every field ``local_eligibility`` reads, so neither
  test can quietly read a default where the tree had a value;
* where the stored tree is on disk, the subset equals it. Those two checks
  skip without it, and they are the only ones here that do.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from dci1v4.protocol.hashing import sha_obj
from dci1v8dev import backtest as B
from dci1v8dev.run import eligibility as EL
from dci1v8dev.run import stages as S

from tests_v8dev.conftest import (EVIDENCE, SUBSET, pilot_eligibility_inputs,
                                  subset_manifest)

DCI1 = Path(__file__).resolve().parents[1]


def _records():
    for rel, entry in subset_manifest()["backtest"]["files"].items():
        yield rel, entry, gzip.decompress((SUBSET / entry["fixture"]).read_bytes())


def test_the_backtest_subset_is_every_record_the_loader_opens():
    backtest = subset_manifest()["backtest"]
    expected = {f"{backtest['rel']}/{stage}/{name}": key
                for key, (stage, name) in B.STAGE_FILES.items()}
    assert {rel: e["stage_key"] for rel, e in backtest["files"].items()} == expected


def test_every_committed_record_is_its_manifest_entry_and_a_signed_payload():
    n = 0
    for rel, entry, data in _records():
        assert len(data) == entry["bytes"], rel
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], rel
        assert sha_obj(json.loads(data)) == entry["record_hash"], rel
        n += 1
    assert n == len(B.STAGE_FILES)


def test_the_gate2_record_is_the_one_the_chance_cache_was_built_from():
    backtest = subset_manifest()["backtest"]
    cache = json.loads((DCI1 / backtest["chance_cache"]).read_text())
    gate2 = next(e for e in backtest["files"].values() if e["stage_key"] == "gate2")
    assert (cache["tree"], cache["model"]) == (backtest["tree"], backtest["model"])
    assert gate2["sha256"] == cache["gate2_record_sha256"]


class _Reads(dict):
    """A frame entry that records which of its keys a reader asks for."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read: set[str] = set()

    def get(self, key, default=None):
        self.read.add(key)
        return super().get(key, default)

    def __getitem__(self, key):
        self.read.add(key)
        return super().__getitem__(key)


def test_the_eligibility_extract_is_the_manifested_extract_of_every_field_read():
    spec = subset_manifest()["local_eligibility"]
    lanes = pilot_eligibility_inputs()
    assert set(lanes) == set(spec["lanes"])
    assert spec["frames"] == list(S.FRAMES)
    for lane, block in lanes.items():
        assert sha_obj(block) == spec["lanes"][lane]["extract_sha"], lane
        entries = {w: _Reads(v) for w, v in block["by_frame"].items()}
        assert all(set(e) == set(spec["fields"]) for e in entries.values()), lane
        EL.local_eligibility(entries, frames=S.FRAMES)
        read = set().union(*(e.read for e in entries.values()))
        assert read <= set(spec["fields"]), (lane, read - set(spec["fields"]))


# ------------------------------------------------ against the stored tree

def test_the_backtest_records_equal_the_stored_tree():
    checked = 0
    for rel, entry, data in _records():
        path = EVIDENCE / rel
        if not path.exists():
            continue
        assert path.read_bytes() == data, rel
        checked += 1
    if not checked:
        pytest.skip(f"no stored v7 records under {EVIDENCE} (gitignored)")


def test_the_eligibility_extract_equals_the_stored_pilot_records():
    spec = subset_manifest()["local_eligibility"]
    lanes = pilot_eligibility_inputs()
    checked = 0
    for lane, source in spec["lanes"].items():
        path = EVIDENCE / source["source"]
        if not path.exists():
            continue
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == source["sha256"], lane
        by_frame = json.loads(data)["by_frame"]
        assert lanes[lane]["by_frame"] == {
            str(w): {f: by_frame[str(w)].get(f) for f in spec["fields"]}
            for w in S.FRAMES}, lane
        checked += 1
    if not checked:
        pytest.skip(f"no stored pilot roots under {EVIDENCE} (gitignored); "
                    "set DCI1_EVIDENCE_ROOT to the tree holding them")
