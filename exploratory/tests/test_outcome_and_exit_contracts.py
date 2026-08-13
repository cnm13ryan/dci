"""Consumers must read the backend's declared contracts, not re-derive them.

Two review findings shared one shape: a downstream consumer restated something
`vllm_backend` already declares, and drifted from it.

  * `xm_vllm_ingest` re-derived which outcomes are non-behavioural, though
    `contract.NON_BEHAVIOURAL` declares exactly that. It got three of five
    wrong, and an engine that could not serve a checkpoint was scored as the
    model failing the constraint.
  * `xm_vllm_run` collapsed every non-zero backend exit into "ceiling hits",
    though exit 2 means the run was BLOCKED and no row was generated.

The tests below assert the consumer agrees with the declaration, so the next
drift fails here rather than in an artifact nobody re-reads.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXPLORATORY))

from crossmodel.schema import (  # noqa: E402
    NO_FINAL_WITHIN_BUDGET,
    TECHNICAL_FAILURE,
    NOT_GENERATED,
    final_answer_status,
)
from vllm_backend.contract import NON_BEHAVIOURAL, Outcome  # noqa: E402

pytestmark = pytest.mark.cpu


class TestNoNonBehaviouralOutcomeIsScoredAsBehaviour:
    """`NO_FINAL_WITHIN_BUDGET` feeds target-failure scoring. Nothing that is
    not the model's behaviour may land there."""

    @staticmethod
    def _scored(outcome: Outcome) -> str:
        """Driven through the INGEST'S OWN classifier, not a copy of it.

        An earlier version of this test reimplemented the mapping inline and so
        passed against the buggy ingest — the same mistake the bug was. It now
        calls `scored_failure_flags`, which is the single boundary the ingest
        uses, so reverting the fix fails here.
        """
        from xm_vllm_ingest import scored_failure_flags
        not_generated, technical_failure = scored_failure_flags(outcome)
        return final_answer_status({
            "final_answer": "",                    # a blocked row carries none
            "not_generated": not_generated,
            "technical_failure": technical_failure,
        })

    def test_the_classifier_covers_the_declared_set_exactly(self) -> None:
        """No outcome may be silently unclassified, now or when one is added."""
        from xm_vllm_ingest import scored_failure_flags
        for outcome in Outcome:
            not_generated, technical = scored_failure_flags(outcome)
            flagged = not_generated or technical
            assert flagged == (outcome in NON_BEHAVIOURAL), (
                f"{outcome.value}: flagged={flagged} but "
                f"NON_BEHAVIOURAL membership is {outcome in NON_BEHAVIOURAL}")

    def test_the_two_flags_are_never_both_set(self) -> None:
        """`final_answer_status` checks not_generated first; both set would
        hide an apparatus failure behind an unattempted row."""
        from xm_vllm_ingest import scored_failure_flags
        for outcome in Outcome:
            not_generated, technical = scored_failure_flags(outcome)
            assert not (not_generated and technical), outcome.value

    @pytest.mark.parametrize("outcome", sorted(NON_BEHAVIOURAL, key=lambda o: o.value))
    def test_it_never_reads_as_a_behavioural_state(self, outcome) -> None:
        assert self._scored(outcome) != NO_FINAL_WITHIN_BUDGET, (
            f"{outcome.value} is declared NON_BEHAVIOURAL but scores as "
            f"{NO_FINAL_WITHIN_BUDGET}, which is read as the model failing")

    @pytest.mark.parametrize("outcome,expected", [
        (Outcome.BACKEND_UNSUPPORTED, TECHNICAL_FAILURE),
        (Outcome.CAPACITY_EXCEEDED, TECHNICAL_FAILURE),
        (Outcome.CHANNEL_INVALID, TECHNICAL_FAILURE),
        (Outcome.TECHNICAL_FAILURE, TECHNICAL_FAILURE),
        (Outcome.NOT_GENERATED, NOT_GENERATED),
    ])
    def test_each_lands_in_the_state_that_excludes_it(self, outcome,
                                                      expected) -> None:
        assert self._scored(outcome) == expected

    def test_an_ordinary_empty_answer_is_still_behavioural(self) -> None:
        """The fix must not swallow a real "model produced nothing" row."""
        assert final_answer_status({
            "final_answer": "", "not_generated": False,
            "technical_failure": False}) == NO_FINAL_WITHIN_BUDGET

    def test_a_normal_answer_is_untouched(self) -> None:
        assert final_answer_status({
            "final_answer": "an answer", "not_generated": False,
            "technical_failure": False}) == "FINAL_ANSWER"


class TestTheIngestConsumesTheDeclaration:
    SOURCE = (EXPLORATORY / "xm_vllm_ingest.py").read_text(encoding="utf-8")

    def test_it_imports_the_declared_set(self) -> None:
        assert "NON_BEHAVIOURAL" in self.SOURCE, (
            "the ingest must consume contract.NON_BEHAVIOURAL rather than "
            "restate which outcomes are apparatus failures")

    def test_it_retains_the_canonical_outcome_on_the_scored_row(self) -> None:
        """The booleans are a lossy projection; an audit needs the original."""
        assert "backend_outcome" in self.SOURCE


class TestTheDriverHonoursTheBackendExitCodes:
    SOURCE = (EXPLORATORY / "xm_vllm_run.py").read_text(encoding="utf-8")

    def test_the_backend_still_returns_two_when_blocked(self) -> None:
        """The value the driver keys on, read from the backend itself."""
        main = (EXPLORATORY / "vllm_backend" / "__main__.py").read_text()
        tree = ast.parse(main)
        blocked = [n for n in ast.walk(tree)
                   if isinstance(n, ast.If)
                   and "blocked" in ast.unparse(n.test)]
        assert blocked, "vllm_backend.__main__ no longer branches on `blocked`"
        assert "return 2" in ast.unparse(blocked[0])

    def test_the_driver_distinguishes_blocked_from_a_ceiling_hit(self) -> None:
        assert "BACKEND_BLOCKED" in self.SOURCE
        assert "BACKEND_BLOCKED = 2" in self.SOURCE

    def test_a_blocked_run_is_not_ingested(self) -> None:
        """A blocked run writes a FULL row set, so row counts cannot catch it."""
        blocked_index = self.SOURCE.index("BACKEND_BLOCKED")
        ingest_index = self.SOURCE.index("xm_vllm_ingest.py")
        assert blocked_index < ingest_index, (
            "the blocked check must precede ingest; a blocked run writes "
            "expected_rows rows and otherwise passes every count check")
