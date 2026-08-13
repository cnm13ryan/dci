"""The retained validation artifact must describe the run that produced it.

Two review findings, both making `HARDWARE_VALIDATION.json` misdescribe what
executed — which matters more than an ordinary bug because that file IS the
evidence. It was committed to close the gap left when the consolidation was
reported hardware-validated without an artifact.

  * the validator read `provenance["switch_evidence"]`, a key `engine.run` does
    not emit, so every committed case recorded a null tokenizer acquisition and
    revision while the engine had in fact performed the validation;
  * it wrote `case.max_tokens` as the sampling ceiling, but a two_phase_splice
    case caps the reasoning phase at `reasoning_budget`. The 256-token limited
    probe claimed a 512-token ceiling.

Neither could be caught by the artifact passing 7/7: both are fields ABOUT the
run, not the run's result.
"""
from __future__ import annotations

from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.cpu


class TestTheHardwareValidationRecordsWhatItRan:
    SOURCE = (EXPLORATORY / "vllm_backend" / "hardware_validation.py").read_text(
        encoding="utf-8")

    def test_it_reads_the_provenance_key_the_engine_emits(self) -> None:
        engine = (EXPLORATORY / "vllm_backend" / "engine.py").read_text()
        assert '"template_switch_evidence"' in engine
        assert '"template_switch_evidence"' in self.SOURCE, (
            "the validator read `switch_evidence`, which the engine never "
            "emits, so every case recorded null template evidence")
        assert 'provenance.get("switch_evidence"' not in self.SOURCE

    def test_it_records_the_reasoning_phase_cap_not_the_answer_allowance(self) -> None:
        """For two_phase_splice the two differ: 256 budget vs 512 answer."""
        assert '"max_tokens": sampling.max_tokens' in self.SOURCE
        assert '"max_tokens": case.max_tokens' not in self.SOURCE

    def test_it_records_the_answer_allowance_separately(self) -> None:
        assert '"answer_tokens": case.max_tokens' in self.SOURCE
        assert '"reasoning_budget": case.reasoning_budget' in self.SOURCE
