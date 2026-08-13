"""Missing or failed evidence must never reach IDENTIFIED.

A self-audit of PR #19 found four inputs to `CellEvidence` populated by
assertion rather than by measurement: `execution_validated=True`,
`verifier_certified=True`, `satisfiable=True`, and `channel_valid` absent
defaulting to `1.0`. All four defaults were unconditional, so a caller that
supplied no evidence at all received a cell certified on three preconditions it
had never established — and two cells did reach IDENTIFIED that way.

The fix is tri-state: `None` means never established, which is NOT `False`, and
a cell carrying any `None` fails closed to `EVIDENCE_INCOMPLETE`.

These tests are adversarial on purpose. Each one constructs a cell that is
perfect on every axis the layer CAN measure — good uptake, real headroom, clean
replicates, no cap — so that if a single evidence field were still fail-open the
cell would sail through to IDENTIFIED. Anything less than a full behavioural
alibi would let a bug hide behind an unrelated verdict.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel import identification as ident  # noqa: E402
from crossmodel.identification import CellEvidence, classify  # noqa: E402

#: Every axis the layer can measure, set to its healthiest value.
BEHAVIOURALLY_PERFECT = dict(
    technical_failure_rate=0.0, replicate_identical_rate=0.0, n_tasks=20,
    n_rows_focal=40, n_rows_reference=40,
    n_answered_focal=40, n_answered_reference=40,
    focal_uptake=0.95, reference_uptake=0.95,
    target_failure_focal=0.45, target_failure_reference=0.05,
    cap_hit_rate=0.0, tau=0.40, lo=0.22, hi=0.55)

#: The four evidence fields, all positively established.
ESTABLISHED = dict(execution_validated=True, channel_valid_rate=1.0,
                   verifier_certified=True, satisfiable=True)

EVIDENCE_FIELDS = tuple(ESTABLISHED)


def evidence(**overrides) -> CellEvidence:
    return CellEvidence(**{**BEHAVIOURALLY_PERFECT, **ESTABLISHED, **overrides})


class TestTheDefaultsAreNoLongerFailOpen:
    def test_a_bare_cell_supplies_no_evidence_and_is_not_identified(self) -> None:
        """The exact fail-open shape: construct with nothing established."""
        verdict = classify(CellEvidence(**BEHAVIOURALLY_PERFECT))
        assert verdict.status == ident.EVIDENCE_INCOMPLETE
        assert verdict.poolable is False

    @pytest.mark.parametrize("field", EVIDENCE_FIELDS)
    def test_no_evidence_field_defaults_to_established(self, field: str) -> None:
        assert getattr(CellEvidence(), field) is None, (
            f"{field} still carries a fail-open default")

    def test_the_bare_reason_names_every_missing_field(self) -> None:
        reason = classify(CellEvidence(**BEHAVIOURALLY_PERFECT)).reason
        for field in EVIDENCE_FIELDS:
            assert field in reason, f"{field} not named in the refusal"


class TestEachFieldIndependentlyBlocksIdentification:
    """One at a time, against an otherwise perfect cell."""

    @pytest.mark.parametrize("field", EVIDENCE_FIELDS)
    def test_missing_evidence_blocks(self, field: str) -> None:
        verdict = classify(evidence(**{field: None}))
        assert verdict.status == ident.EVIDENCE_INCOMPLETE, (
            f"a cell with {field}=None was classified {verdict.status}")
        assert verdict.poolable is False
        assert field in verdict.reason

    @pytest.mark.parametrize("field,expected", [
        ("execution_validated", ident.EXECUTION_INVALID),
        ("verifier_certified", ident.VERIFIER_UNCERTIFIED),
        ("satisfiable", ident.UNSATISFIABLE),
    ])
    def test_failed_evidence_blocks_with_its_own_verdict(
            self, field: str, expected: str) -> None:
        """False is a finding and gets its own status; None is a missing input."""
        verdict = classify(evidence(**{field: False}))
        assert verdict.status == expected
        assert verdict.poolable is False

    def test_a_degraded_channel_rate_blocks(self) -> None:
        verdict = classify(evidence(channel_valid_rate=0.4))
        assert verdict.status == ident.CHANNEL_INVALID
        assert verdict.poolable is False


class TestOnlyFullyEstablishedEvidenceIdentifies:
    def test_all_four_established_identifies(self) -> None:
        assert classify(evidence()).status == ident.IDENTIFIED

    def test_the_control_is_a_real_control(self) -> None:
        """If this ever stops passing, the tests above prove nothing."""
        assert classify(evidence()).poolable is True

    @pytest.mark.parametrize("field", EVIDENCE_FIELDS)
    def test_dropping_any_single_field_loses_identification(self, field) -> None:
        assert classify(evidence()).status == ident.IDENTIFIED
        assert classify(evidence(**{field: None})).status != ident.IDENTIFIED


class TestEvidenceGateRunsBeforeBehaviour:
    """Missing evidence must not be masked by a behavioural verdict, and must
    not mask one either — the reason has to say which input is absent."""

    def test_missing_evidence_wins_over_a_ceiling(self) -> None:
        verdict = classify(evidence(execution_validated=None,
                                    target_failure_focal=0.0,
                                    target_failure_reference=0.0))
        assert verdict.status == ident.EVIDENCE_INCOMPLETE

    def test_missing_evidence_wins_over_nonuptake(self) -> None:
        verdict = classify(evidence(satisfiable=None, focal_uptake=0.01))
        assert verdict.status == ident.EVIDENCE_INCOMPLETE

    def test_established_evidence_lets_behaviour_decide(self) -> None:
        assert classify(evidence(focal_uptake=0.01)).status == \
            ident.FOCAL_NONUPTAKE


class TestVerdictRegistry:
    def test_the_new_status_is_registered(self) -> None:
        assert ident.EVIDENCE_INCOMPLETE in ident.ALL_VERDICTS

    def test_it_is_not_poolable(self) -> None:
        assert ident.EVIDENCE_INCOMPLETE not in ident.POOLABLE

    def test_it_is_distinct_from_a_failed_check(self) -> None:
        assert ident.EVIDENCE_INCOMPLETE != ident.VERIFIER_UNCERTIFIED
        assert ident.EVIDENCE_INCOMPLETE != ident.EXECUTION_INVALID
