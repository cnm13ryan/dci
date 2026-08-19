"""Post-Gate-1 verifier-hash binding: the central fail-closed invariant
that every stage from Gate 2A onward (and the greedy replication, the
one non-stage command that scores newly generated rows) re-verifies the
current verifier sources against the signed verifier-freeze manifest
before any mutation. Drift never updates the manifest; reconciling it
is an audited supersession-and-recalibration decision.

Regression matrix: (A) unchanged verifier -> guarded operations pass
the binding; (B) a semantic verifier difference from the freeze fails
closed for every guarded operation; (C) reverting to the frozen
verifier restores operation; (D) the canonical hash scheme covers
exactly the behaviorally relevant verifier sources, so irrelevant
changes cannot produce a false mismatch; (E, in test_lifecycle_e2e)
stored verdict rows stay traceable to the verifier that scored them.
"""
from __future__ import annotations

import json

import pytest

import dci1v3.stages  # noqa: F401  — populates the operation registry
from dci1v3.engine import fs
from dci1v3.engine.dispatch import (
    REGISTRY,
    assert_verifier_binding,
    verifier_binding_required,
)
from dci1v3.engine.signing import sign_payload
from dci1v3.errors import IntegrityError
from dci1v3.protocol import constants as C
from dci1v3.stages.autorater import verifier_source_state

#: Exactly the operations whose validity depends on the Gate-1 freeze.
GUARDED = {"gate2a", "gate2b", "freeze", "generate", "select-primary",
           "mask", "masked-analysis", "unmask", "final-analysis",
           "greedy"}


def _write_freeze(ctx, sources: dict[str, str]) -> None:
    payload = {"kind": "verifier_freeze", "study_id": ctx.study_id,
               "verifier_sources": sources}
    fs.write_json(ctx.study_root / "verifier_freeze.json",
                  sign_payload(payload, ctx.signing_key_path))


def test_binding_required_exactly_for_post_gate1_operations():
    assert {name for name, op in REGISTRY.items()
            if verifier_binding_required(op)} == GUARDED
    gate1_index = C.STAGE_SEQUENCE.index(C.STAGE_GATE1)
    for name, op in REGISTRY.items():
        if op.stage is not None:
            assert verifier_binding_required(op) == \
                (C.STAGE_SEQUENCE.index(op.stage) > gate1_index)
    # GATE_1 keeps its own drift check (with calibration supersession);
    # the central guard must not pre-empt it.
    assert not verifier_binding_required(REGISTRY["gate1"])


def test_binding_passes_when_sources_match_freeze(registered_ctx):
    _write_freeze(registered_ctx, verifier_source_state())
    assert_verifier_binding(registered_ctx)      # must not raise


def test_binding_fails_closed_on_verifier_drift(registered_ctx):
    drifted = dict(verifier_source_state())
    drifted["target.py"] = "0" * 64
    _write_freeze(registered_ctx, drifted)
    with pytest.raises(IntegrityError, match="verifier code changed"):
        assert_verifier_binding(registered_ctx)


def test_binding_recovers_when_drift_reverted(registered_ctx):
    drifted = dict(verifier_source_state())
    drifted["words.py"] = "1" * 64
    _write_freeze(registered_ctx, drifted)
    with pytest.raises(IntegrityError, match="verifier code changed"):
        assert_verifier_binding(registered_ctx)
    _write_freeze(registered_ctx, verifier_source_state())
    assert_verifier_binding(registered_ctx)      # must not raise


def test_binding_fails_closed_without_manifest(registered_ctx):
    with pytest.raises(IntegrityError, match="verifier-freeze manifest"):
        assert_verifier_binding(registered_ctx)


def test_binding_rejects_unsigned_manifest_tampering(registered_ctx):
    _write_freeze(registered_ctx, verifier_source_state())
    path = registered_ctx.study_root / "verifier_freeze.json"
    record = json.loads(path.read_text())
    record["payload"]["verifier_sources"]["target.py"] = "2" * 64
    path.write_text(json.dumps(record))          # not re-signed
    with pytest.raises(IntegrityError, match="hash mismatch"):
        assert_verifier_binding(registered_ctx)


def test_hash_scheme_covers_exactly_the_verifier_sources():
    """(D) The canonical scheme hashes every behaviorally relevant
    verifier module and nothing else, so a change to unrelated code can
    never produce a false verifier mismatch."""
    assert set(verifier_source_state()) == {
        "words.py", "target.py", "families.py", "boundary.py",
        "reimplementation.py"}
