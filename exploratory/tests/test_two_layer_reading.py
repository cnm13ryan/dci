"""Identification and behaviour are two questions, and both must be answerable.

`classify()` returns the FIRST verdict that applies. That is correct for
pooling — a cell missing a prerequisite must not enter a mean — but it destroys
information for reading: a checkpoint whose target never fails and whose
execution admission was never recorded reports `EVIDENCE_INCOMPLETE`, and the
ceiling, the floor and the undelivered focal instruction all vanish behind the
block.

`read()` answers both:

    identification  may this contrast be read causally?   (governs pooling)
    behavioural     what was observed?                    (governs reading)

The property these tests exist to pin is that the second layer is not a weaker
gate. It re-runs the same classifier on the same MEASURED constituents, filling
in only the absent prerequisite axes, so it can never excuse anything the model
actually did.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel import identification as ident  # noqa: E402
from crossmodel.identification import CellEvidence, read  # noqa: E402


def measured(**overrides) -> CellEvidence:
    """A cell whose BEHAVIOUR is fully measured and whose prerequisites are not.

    This is the shape every cross-model cell actually has: the model was run and
    scored, but `THINKING_ENABLED_BOUNDED` never went through Stage B/C
    admission and no verifier is certified for these output classes.
    """
    base = dict(
        technical_failure_rate=0.0, replicate_identical_rate=0.0, n_tasks=20,
        n_rows_focal=40, n_rows_reference=40,
        n_answered_focal=40, n_answered_reference=40,
        focal_uptake=0.95, reference_uptake=0.95,
        target_failure_focal=0.45, target_failure_reference=0.05,
        cap_hit_rate=0.0, tau=0.40, lo=0.22, hi=0.55)
    base.update(overrides)
    return CellEvidence(**base)


def established(**overrides) -> CellEvidence:
    return measured(execution_validated=True, channel_valid_rate=1.0,
                    verifier_certified=True, satisfiable=True, **overrides)


class TestTheBlockedCase:
    def test_identification_blocks_on_missing_evidence(self) -> None:
        assert read(measured()).identification.status == ident.EVIDENCE_INCOMPLETE

    def test_behaviour_is_still_reported_behind_the_block(self) -> None:
        """The whole point. A blocked cell still says what was observed."""
        assert read(measured()).behavioural.status == ident.IDENTIFIED

    def test_a_ceiling_is_visible_even_when_identification_blocks(self) -> None:
        cell = measured(target_failure_focal=0.0, target_failure_reference=0.0)
        reading = read(cell)
        assert reading.identification.status == ident.EVIDENCE_INCOMPLETE
        assert reading.behavioural.status == ident.TARGET_CEILING

    def test_an_undelivered_focal_is_visible_even_when_blocked(self) -> None:
        """The Kimi-VL shape: real headroom, treatment not delivered."""
        cell = measured(focal_uptake=0.088, reference_uptake=0.571,
                        target_failure_focal=0.559,
                        target_failure_reference=0.286)
        reading = read(cell)
        assert reading.identification.status == ident.EVIDENCE_INCOMPLETE
        assert reading.behavioural.status == ident.FOCAL_NONUPTAKE


class TestTheBehaviouralLayerIsNotAWeakerGate:
    """Everything the model did must survive into the behavioural reading."""

    def test_it_does_not_excuse_a_ceiling(self) -> None:
        cell = measured(target_failure_focal=0.0, target_failure_reference=0.0)
        assert read(cell).behavioural.status != ident.IDENTIFIED

    def test_it_does_not_excuse_a_floor(self) -> None:
        cell = measured(target_failure_focal=1.0, target_failure_reference=1.0)
        assert read(cell).behavioural.status == ident.TARGET_FLOOR

    def test_it_does_not_excuse_a_binding_cap(self) -> None:
        assert read(measured(cap_hit_rate=0.95)).behavioural.status == ident.CAP_BOUND

    def test_it_does_not_excuse_dependent_replicates(self) -> None:
        cell = measured(replicate_identical_rate=0.90)
        assert read(cell).behavioural.status == ident.REPLICATES_DEPENDENT

    def test_it_does_not_excuse_a_contaminated_reference(self) -> None:
        cell = measured(target_failure_focal=0.80, target_failure_reference=0.60)
        assert read(cell).behavioural.status == ident.REFERENCE_CONTAMINATED

    def test_it_does_not_invent_a_measurement(self) -> None:
        """Only the four prerequisite axes are supplied; nothing else moves."""
        cell = measured()
        reading = read(cell)
        for axis in ("focal_uptake", "reference_uptake", "cap_hit_rate",
                     "target_failure_focal", "target_failure_reference",
                     "replicate_identical_rate", "technical_failure_rate"):
            assert reading.behavioural.evidence[axis] == getattr(cell, axis)


class TestPoolingFollowsIdentificationAlone:
    def test_a_blocked_cell_is_not_poolable_however_it_behaves(self) -> None:
        reading = read(measured())
        assert reading.behavioural.status == ident.IDENTIFIED
        assert reading.poolable is False

    def test_poolable_helper_accepts_readings(self) -> None:
        assert ident.poolable([read(measured())]) == []
        assert len(ident.poolable([read(established())])) == 1

    def test_evidence_incomplete_is_never_poolable(self) -> None:
        assert ident.EVIDENCE_INCOMPLETE not in ident.POOLABLE


class TestTheUnblockedCase:
    def test_the_two_layers_coincide_when_nothing_was_missing(self) -> None:
        reading = read(established())
        assert reading.identification.status == reading.behavioural.status
        assert reading.behavioural.status == ident.IDENTIFIED

    def test_they_coincide_on_a_behavioural_failure_too(self) -> None:
        reading = read(established(target_failure_focal=0.0,
                                   target_failure_reference=0.0))
        assert reading.identification.status == ident.TARGET_CEILING
        assert reading.behavioural.status == ident.TARGET_CEILING

    def test_a_failed_prerequisite_is_not_a_missing_one(self) -> None:
        """`False` is an answer; `None` is the absence of one.

        A cell whose admission was refused stays EXECUTION_INVALID in both
        layers — `read()` fills in absent axes, never failed ones.
        """
        reading = read(measured(execution_validated=False,
                                channel_valid_rate=1.0,
                                verifier_certified=True, satisfiable=True))
        assert reading.identification.status == ident.EXECUTION_INVALID
        assert reading.behavioural.status == ident.EXECUTION_INVALID
        assert reading.blocked_on_evidence is False


class TestSerialisation:
    def test_both_layers_and_their_reasons_reach_the_row(self) -> None:
        row = read(measured()).to_dict()
        assert row["identification"] == ident.EVIDENCE_INCOMPLETE
        assert row["behavioural"] == ident.IDENTIFIED
        assert row["identification_reason"] and row["behavioural_reason"]

    def test_the_row_still_carries_the_constituents(self) -> None:
        row = read(measured()).to_dict()
        for key in ("target_failure_focal", "focal_uptake", "cap_hit_rate",
                    "n_tasks", "tau", "lo", "hi"):
            assert key in row, f"{key} missing from the serialised reading"
