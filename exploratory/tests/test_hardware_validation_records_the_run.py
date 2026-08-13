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


class TestTheEngineTokenizerCarriesItsProvenance:
    """Fixing the key alone left the value as "unknown", which the first
    regenerated artifact showed for all six executed cases.

    `build_engine` returns `llm.get_tokenizer()` and that object was never
    stamped — only `load_tokenizer` stamped the one IT fetched. So the run path,
    which validates against the engine's own tokenizer, had no provenance to
    record. The engine's tokenizer is the strongest provenance available, being
    the object that renders the prompts, and it was reported as unknown.
    """

    SOURCE = (Path(__file__).resolve().parent.parent / "vllm_backend"
              / "engine.py").read_text(encoding="utf-8")

    def test_build_engine_stamps_the_tokenizer_it_returns(self) -> None:
        import ast
        tree = ast.parse(self.SOURCE)
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "build_engine")
        body = ast.unparse(fn)
        assert "_dci_acquisition" in body, (
            "build_engine must stamp the tokenizer it returns; without it the "
            "switch evidence records 'unknown' for the run path")
        assert "_dci_revision" in body

    def test_it_stamps_the_revision_the_engine_was_pinned_to(self) -> None:
        """A revision recorded from anywhere else could disagree with the run."""
        assert "plan.model_revision" in self.SOURCE

    def test_the_three_acquisitions_are_distinct_and_unconfusable(self) -> None:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from vllm_backend.engine import (ACQUIRED_BY_FALLBACK, ACQUIRED_BY_VLLM,
                                         ACQUIRED_FROM_ENGINE)
        values = [ACQUIRED_FROM_ENGINE, ACQUIRED_BY_VLLM, ACQUIRED_BY_FALLBACK]
        assert len(set(values)) == 3
        for a in values:
            for b in values:
                assert a is b or a not in b, f"{a!r} is a substring of {b!r}"

    def test_unknown_is_not_a_declared_acquisition(self) -> None:
        """It is the absence of provenance, and must never look like a source."""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from vllm_backend import engine
        declared = {engine.ACQUIRED_FROM_ENGINE, engine.ACQUIRED_BY_VLLM,
                    engine.ACQUIRED_BY_FALLBACK}
        assert "unknown" not in declared
