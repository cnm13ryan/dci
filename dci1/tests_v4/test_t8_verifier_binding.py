"""T8. Verifier-hash binding (§10.6, check C5, trap T-12).

The five regression cases check C5 names:

1. an unchanged verifier after Gate 1 succeeds downstream;
2. a committed semantic verifier change fails **every** protected stage closed;
3. reverting succeeds again;
4. an irrelevant source change produces no false mismatch;
5. stored verdict provenance remains traceable to the verifier that produced
   it.

The protected set is the union §10.6 names and check C5 adds: eleven entry
points, not v3's single dispatcher.
"""
from __future__ import annotations

import pytest

from dci1v4.engine.binding import (
    current_verifier_hash,
    require_frozen_verifier,
    verifier_provenance,
)
from dci1v4.errors import ProtocolError, VerifierBindingError
from dci1v4.protocol import constants as C
from dci1v4.verifiers import SEMANTIC_MODULES, source_hashes


def test_the_protected_set_is_the_union_of_eleven_entry_points():
    assert len(C.VERIFIER_BOUND_ENTRY_POINTS) == 11
    assert set(C.VERIFIER_BOUND_ENTRY_POINTS) == {
        "ladder_screen", "solo_calibration", "reference_admission",
        "composed_headroom", "freeze", "confirmatory_generation", "scoring",
        "resume_restart", "analysis", "unmasking", "report_generation"}


def test_an_unregistered_entry_point_is_refused():
    with pytest.raises(ProtocolError, match="registered §10.6 entry point"):
        require_frozen_verifier("some_other_stage", current_verifier_hash())


def test_case_one_an_unchanged_verifier_succeeds_at_every_entry_point():
    frozen = current_verifier_hash()
    for entry_point in C.VERIFIER_BOUND_ENTRY_POINTS:
        assert require_frozen_verifier(entry_point, frozen) == frozen


def test_case_two_a_semantic_change_fails_every_protected_stage_closed(
        monkeypatch, tmp_path):
    """A changed semantic module changes the canonical hash, and every one of
    the eleven entry points refuses."""
    import dci1v4.verifiers as verifiers

    frozen = current_verifier_hash()
    original = verifiers.source_hashes

    def drifted():
        digests = dict(original())
        digests["compliance.py"] = "0" * 64      # a committed semantic change
        return digests

    monkeypatch.setattr(verifiers, "source_hashes", drifted)
    assert current_verifier_hash() != frozen
    for entry_point in C.VERIFIER_BOUND_ENTRY_POINTS:
        with pytest.raises(VerifierBindingError):
            require_frozen_verifier(entry_point, frozen)


def test_case_three_reverting_succeeds_again(monkeypatch):
    import dci1v4.verifiers as verifiers

    frozen = current_verifier_hash()
    original = verifiers.source_hashes
    monkeypatch.setattr(verifiers, "source_hashes",
                        lambda: {**original(), "words.py": "1" * 64})
    with pytest.raises(VerifierBindingError):
        require_frozen_verifier("analysis", frozen)
    monkeypatch.setattr(verifiers, "source_hashes", original)
    assert require_frozen_verifier("analysis", frozen) == frozen


def test_case_four_an_irrelevant_source_change_produces_no_false_mismatch(
        tmp_path):
    """The canonical hash covers verifier semantics only; a change to a module
    outside that set must not trip the binding."""
    from pathlib import Path

    import dci1v4
    from dci1v4.engine.context import DCI1_ROOT

    frozen = current_verifier_hash()
    irrelevant = DCI1_ROOT / "src" / "dci1v4" / "topics" / "bank.py"
    original = irrelevant.read_bytes()
    try:
        irrelevant.write_bytes(original + b"\n# an irrelevant comment\n")
        assert current_verifier_hash() == frozen
        assert require_frozen_verifier("scoring", frozen) == frozen
    finally:
        irrelevant.write_bytes(original)


def test_case_five_stored_verdict_provenance_stays_traceable():
    provenance = verifier_provenance()
    assert provenance["verifier_source_hash"] == current_verifier_hash()
    assert set(provenance["modules"]) == set(SEMANTIC_MODULES)
    # A stored row carries the hash it was produced under, so a later change
    # leaves historical rows auditable rather than newly valid.
    from dci1v4.design.cells import block_cells
    from dci1v4.generation.cache import compliance_row
    from dci1v4.topics.split import confirmatory_blocks, split_topics

    slot_map = {"A": ("A", 3), "B": ("B", 8)}
    block = confirmatory_blocks(split_topics())[0]
    cell = block_cells("confirmatory", block, slot_map, draws=4)[0]
    row = compliance_row(cell, "however", slot_map=slot_map,
                         finish_reason="stop")
    assert row["verifier_source_hash"] == current_verifier_hash()


def test_before_gate1_the_binding_records_rather_than_compares():
    """The ladder screen and solo calibration legitimately run before Gate 1;
    they still pass through the binding so the hash they ran under is on
    their own records."""
    for entry_point in ("ladder_screen", "solo_calibration"):
        assert require_frozen_verifier(entry_point, None) == \
            current_verifier_hash()


def test_the_semantic_module_set_covers_graded_scores_and_predicates():
    """§10.6: the hash covers every component that can change semantics for
    any registered instrument, including §7.4 and §9.3."""
    assert "compliance.py" in SEMANTIC_MODULES     # graded + non-vacuity
    assert "constraints.py" in SEMANTIC_MODULES    # the registered grids
    assert "statistics.py" in SEMANTIC_MODULES     # the counted statistics
    assert "words.py" in SEMANTIC_MODULES          # segmentation
    assert "target.py" in SEMANTIC_MODULES         # S0-S3
    digests = source_hashes()
    assert len(set(digests.values())) == len(SEMANTIC_MODULES)


def test_the_frozen_hash_is_never_silently_updated():
    """The error names invalidation and recalibration, not an update."""
    frozen = "f" * 64
    with pytest.raises(VerifierBindingError) as excinfo:
        require_frozen_verifier("freeze", frozen)
    message = str(excinfo.value)
    assert "invalidates every downstream stage" in message
    assert "never resolved by updating the frozen value" in message
