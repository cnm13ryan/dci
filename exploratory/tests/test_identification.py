"""Identification is separate from estimation.

The central property: a cell can carry a perfectly ordinary-looking estimate and
still be unidentified, and the layer must say so. tau = 0.000 with a zero-width
interval is the exact shape of both "no interference" and "the target never
failed, so there was nothing to measure" — these tests pin that those two are
never given the same verdict.

Precedence is tested explicitly, because it encodes a scientific claim: an
undelivered treatment explains a null more simply than target difficulty does,
and a failed harness is not a measurement of the model at all.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel import identification as ident  # noqa: E402
from crossmodel.identification import CellEvidence, Thresholds, classify  # noqa: E402


def healthy(**overrides) -> CellEvidence:
    """A cell that should be IDENTIFIED unless an override breaks it."""
    # The four evidence fields are stated explicitly: they no longer default
    # to established, so a fixture that omitted them would test the
    # EVIDENCE_INCOMPLETE path instead of the behavioural one it means to.
    base = dict(
        execution_validated=True, channel_valid_rate=1.0,
        technical_failure_rate=0.0, verifier_certified=True,
        replicate_identical_rate=0.0, n_tasks=20,
        n_rows_focal=40, n_rows_reference=40,
        n_answered_focal=40, n_answered_reference=40,
        focal_uptake=0.95, reference_uptake=0.95,
        target_failure_focal=0.45, target_failure_reference=0.05,
        cap_hit_rate=0.0, satisfiable=True, tau=0.40, lo=0.22, hi=0.55)
    base.update(overrides)
    return CellEvidence(**base)


class TestBaseline:
    def test_a_healthy_cell_is_identified(self) -> None:
        assert classify(healthy()).status == ident.IDENTIFIED

    def test_identified_cells_are_poolable(self) -> None:
        assert classify(healthy()).poolable is True

    def test_the_verdict_carries_its_constituents(self) -> None:
        verdict = classify(healthy())
        for key in ("target_failure_focal", "target_failure_reference",
                    "focal_uptake", "reference_uptake", "n_tasks",
                    "cap_hit_rate", "tau", "lo", "hi"):
            assert key in verdict.evidence, f"{key} missing from the verdict"


class TestDegenerateTargets:
    def test_zero_in_both_arms_is_a_ceiling_not_a_null(self) -> None:
        verdict = classify(healthy(target_failure_focal=0.0,
                                   target_failure_reference=0.0,
                                   tau=0.0, lo=0.0, hi=0.0))
        assert verdict.status == ident.TARGET_CEILING
        assert verdict.poolable is False

    def test_saturation_in_both_arms_is_a_floor(self) -> None:
        verdict = classify(healthy(target_failure_focal=1.0,
                                   target_failure_reference=1.0,
                                   tau=0.0, lo=0.0, hi=0.0))
        assert verdict.status == ident.TARGET_FLOOR

    def test_a_real_null_with_headroom_is_still_identified(self) -> None:
        """tau = 0 where the target CAN fail is an identified null."""
        verdict = classify(healthy(target_failure_focal=0.30,
                                   target_failure_reference=0.30, tau=0.0))
        assert verdict.status == ident.IDENTIFIED

    def test_ceiling_and_identified_null_are_distinguished(self) -> None:
        ceiling = classify(healthy(target_failure_focal=0.0,
                                   target_failure_reference=0.0, tau=0.0))
        real = classify(healthy(target_failure_focal=0.30,
                                target_failure_reference=0.30, tau=0.0))
        assert ceiling.status != real.status, (
            "a structural zero and an identified null received the same verdict")


class TestTreatmentDelivery:
    def test_focal_nonuptake_is_not_a_null(self) -> None:
        verdict = classify(healthy(focal_uptake=0.10,
                                   target_failure_focal=0.05,
                                   target_failure_reference=0.05, tau=0.0))
        assert verdict.status == ident.FOCAL_NONUPTAKE

    def test_reference_nonuptake_breaks_load_matching(self) -> None:
        assert classify(healthy(reference_uptake=0.10)).status == \
            ident.REFERENCE_NONUPTAKE

    def test_uptake_is_checked_before_headroom(self) -> None:
        """Both would fire; the simpler explanation must win."""
        verdict = classify(healthy(focal_uptake=0.05,
                                   target_failure_focal=0.0,
                                   target_failure_reference=0.0))
        assert verdict.status == ident.FOCAL_NONUPTAKE


class TestReferenceIntegrity:
    def test_a_damaging_reference_is_contaminated(self) -> None:
        assert classify(healthy(target_failure_reference=0.80)).status == \
            ident.REFERENCE_CONTAMINATED

    def test_a_benign_reference_is_fine(self) -> None:
        assert classify(healthy(target_failure_reference=0.10)).status == \
            ident.IDENTIFIED


class TestExecutionAndChannel:
    def test_unvalidated_execution_wins_over_everything(self) -> None:
        verdict = classify(healthy(execution_validated=False,
                                   focal_uptake=0.0, cap_hit_rate=1.0))
        assert verdict.status == ident.EXECUTION_INVALID

    def test_material_apparatus_failure_voids_the_cell(self) -> None:
        assert classify(healthy(technical_failure_rate=0.5)).status == \
            ident.TECHNICAL_FAILURE

    def test_unsegmented_channels_void_the_cell(self) -> None:
        assert classify(healthy(channel_valid_rate=0.2)).status == \
            ident.CHANNEL_INVALID

    def test_uncertified_verifier_voids_the_cell(self) -> None:
        assert classify(healthy(verifier_certified=False)).status == \
            ident.VERIFIER_UNCERTIFIED


class TestSamplingIntegrity:
    def test_shared_seed_replicates_are_rejected(self) -> None:
        assert classify(healthy(replicate_identical_rate=0.97)).status == \
            ident.REPLICATES_DEPENDENT

    def test_a_thin_task_set_is_rejected(self) -> None:
        assert classify(healthy(n_tasks=2)).status == ident.EXECUTION_INVALID


class TestCapsAndSatisfiability:
    def test_a_binding_cap_makes_the_cap_the_treatment(self) -> None:
        assert classify(healthy(cap_hit_rate=0.86)).status == ident.CAP_BOUND

    def test_an_unsatisfiable_composition_is_rejected(self) -> None:
        assert classify(healthy(satisfiable=False)).status == ident.UNSATISFIABLE

    def test_cap_is_checked_before_uptake(self) -> None:
        verdict = classify(healthy(cap_hit_rate=0.9, focal_uptake=0.1))
        assert verdict.status == ident.CAP_BOUND


class TestPooling:
    def test_only_identified_cells_pool(self) -> None:
        cells = [classify(healthy()),
                 classify(healthy(target_failure_focal=0.0,
                                  target_failure_reference=0.0)),
                 classify(healthy(focal_uptake=0.0))]
        assert len(ident.poolable(cells)) == 1

    def test_every_verdict_name_is_registered(self) -> None:
        # 13 from the original framework list, plus EVIDENCE_INCOMPLETE, which
        # distinguishes "no evidence was recorded" from "a check was run and
        # failed". Collapsing those two is the fail-open shape the self-audit
        # of PR #19 found.
        assert len(set(ident.ALL_VERDICTS)) == 14
        assert ident.EVIDENCE_INCOMPLETE in ident.ALL_VERDICTS


class TestThresholdsAreDeclarations:
    def test_a_stricter_ceiling_changes_the_verdict(self) -> None:
        evidence = healthy(target_failure_focal=0.04,
                           target_failure_reference=0.03)
        assert classify(evidence).status == ident.IDENTIFIED
        strict = Thresholds(ceiling=0.05)
        assert classify(evidence, strict).status == ident.TARGET_CEILING
