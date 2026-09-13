"""§26's durability gate, and the honesty of what it claims.

`evidence/` and `durable_root/` are gitignored by this repository's own design,
so a 411,648-generation confirmatory run would otherwise leave its whole
scientific chain outside version control. These tests pin two things: that the
gate fails closed when the chain is not verifiably duplicated, and that it
never claims off-machine durability it does not have.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import IntegrityError

from dci1v4r3.stages import durability as D


def _tree(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


CRITICAL = {"m/REGIME_SCREEN/records/regime_record.json": '{"a":1}',
            "m/REGIME_SCREEN/backend_runs/r/scored.jsonl": '{"x":1}\n',
            "m/REGIME_SCREEN/backend_runs/r/rows.jsonl": '{"y":2}\n',
            "notes.txt": "not critical"}


def test_a_matching_mirror_passes_and_states_its_limitation(tmp_path):
    evidence = _tree(tmp_path / "evidence", CRITICAL)
    durable = _tree(tmp_path / "durable", CRITICAL)
    record = D.report(evidence=evidence, durable=durable,
                      manifest=tmp_path / "manifest.json",
                      producing_commit="0" * 40, manifest_tracked=True)
    assert record["passed"]
    D.assert_durable_before_freeze(record)
    assert record["off_machine_copy"] is False
    assert "does NOT establish off-machine durability" \
        in record["stated_limitation"]


def test_a_record_mirror_is_not_an_evidence_mirror(tmp_path):
    """The defect the gate was written to catch.

    The mirror held six stage records while fifty-three critical artifacts --
    every raw and scored row among them -- existed in exactly one copy. A
    record mirror documents a result; only an evidence mirror can reproduce
    one.
    """
    evidence = _tree(tmp_path / "evidence", CRITICAL)
    durable = _tree(tmp_path / "durable",
                    {"m/REGIME_SCREEN/records/regime_record.json": '{"a":1}'})
    record = D.report(evidence=evidence, durable=durable,
                      manifest=tmp_path / "manifest.json",
                      producing_commit="0" * 40, manifest_tracked=True)
    assert not record["passed"]
    assert record["comparison"]["n_critical_missing"] == 2
    with pytest.raises(IntegrityError) as excinfo:
        D.assert_durable_before_freeze(record)
    assert "missing from the mirror" in str(excinfo.value)


def test_a_diverged_byte_fails_the_gate(tmp_path):
    evidence = _tree(tmp_path / "evidence", CRITICAL)
    durable = _tree(tmp_path / "durable",
                    {**CRITICAL,
                     "m/REGIME_SCREEN/backend_runs/r/scored.jsonl": '{"x":2}\n'})
    record = D.report(evidence=evidence, durable=durable,
                      manifest=tmp_path / "manifest.json",
                      producing_commit="0" * 40, manifest_tracked=True)
    assert record["comparison"]["n_critical_diverged"] == 1
    with pytest.raises(IntegrityError):
        D.assert_durable_before_freeze(record)


def test_an_untracked_manifest_fails_the_gate(tmp_path):
    """The artifact that makes loss detectable cannot itself be only in the
    cache."""
    evidence = _tree(tmp_path / "evidence", CRITICAL)
    durable = _tree(tmp_path / "durable", CRITICAL)
    record = D.report(evidence=evidence, durable=durable,
                      manifest=tmp_path / "manifest.json",
                      producing_commit="0" * 40, manifest_tracked=False)
    assert not record["passed"]
    with pytest.raises(IntegrityError) as excinfo:
        D.assert_durable_before_freeze(record)
    assert "not tracked in git" in str(excinfo.value)


def test_the_restore_rehearsal_actually_reads_the_mirror(tmp_path):
    durable = _tree(tmp_path / "durable", CRITICAL)
    assert D.restore_rehearsal(durable)["passed"]
    assert D.restore_rehearsal(tmp_path / "absent")["passed"] is False


def test_one_device_is_recorded_rather_than_glossed(tmp_path):
    evidence = _tree(tmp_path / "evidence", CRITICAL)
    durable = _tree(tmp_path / "durable", CRITICAL)
    record = D.report(evidence=evidence, durable=durable,
                      manifest=tmp_path / "m.json",
                      producing_commit="0" * 40, manifest_tracked=True)
    # tmp_path puts both roots on one filesystem, which is the situation on
    # the workstation too. Saying so is the point.
    assert record["roots_on_one_device"] is True
    assert "ONE device" in record["stated_limitation"]
