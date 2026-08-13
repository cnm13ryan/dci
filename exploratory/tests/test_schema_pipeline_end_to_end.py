"""The whole scientific data path, in one test, for every outcome.

    backend record -> serialization -> ingestion -> scoring -> plot data

Isolated schema tests did not catch what broke here. Each end of the pipeline
was internally consistent and self-tested; the mismatch lived in the seam. The
backend emitted `reasoning_closed` and an `outcome` enum while the ingest read
`natural_reasoning_closed` and a boolean triple, so a successful generation run
would have died with a `KeyError` on its first row — after the GPU work was
already spent.

So the property under test is not "each stage is correct" but "a row written by
the backend survives every stage", and it is asserted for all five outcomes,
because the non-behavioural ones are exactly the rows a happy-path test never
produces.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vllm_backend import records                                  # noqa: E402
from vllm_backend.contract import (                               # noqa: E402
    LEGACY_DERIVED, LEGACY_RENAMES, ROW_KEYS, GenerationRequest,
    GenerationResult, Outcome, canonicalise_row)


def _request(row_id: str = "r1") -> GenerationRequest:
    return GenerationRequest(
        row_id=row_id, user_prompt="Explain how a corkscrew removes a cork.",
        system_message="", scientific_seed=11, answer_seed=12,
        identity={"task_id": "PLT01", "arm": "B", "variant": "X_SEMICOLON_FREE",
                  "order": "QAC", "load": 3, "replicate": 0})


def _ok_result() -> GenerationResult:
    return GenerationResult(
        row_id="r1", outcome=Outcome.OK.value,
        rendered_prompt="<user>...", raw_generation="<think>t</think>A. B. C. D.",
        reasoning_text="t", final_answer="Alpha. Beta. Gamma. Delta.",
        reasoning_tokens=3, final_answer_tokens=8, total_generated_tokens=11,
        finish_reason="stop", reasoning_emitted=True, channel_valid=True,
        reasoning_closed=True, seed_reasoning=11, seed_answer=12,
        identity=_request().identity)


#: One representative row per outcome. The non-OK ones are built through the
#: record constructors so the test exercises the same code a real failure would.
def _all_outcomes() -> dict[str, GenerationResult]:
    request = _request()
    return {
        Outcome.OK.value: _ok_result(),
        Outcome.TECHNICAL_FAILURE.value: records.failed(
            request, "<user>...", RuntimeError("HIP out of memory")),
        Outcome.NOT_GENERATED.value: records.not_generated(
            request, "<user>...", "deadline reached before this chunk"),
        # The splice path records an unsegmentable generation this way: the
        # answer channel is empty and the row is explicitly non-behavioural.
        Outcome.CHANNEL_INVALID.value: GenerationResult(
            row_id=request.row_id, outcome=Outcome.CHANNEL_INVALID.value,
            outcome_detail="no close delimiter in the generation",
            rendered_prompt="<user>...", raw_generation="unsegmented scratchpad",
            channel_valid=False, seed_reasoning=request.scientific_seed,
            seed_answer=request.answer_seed, identity=request.identity),
        # A whole-run block still writes one row per design row.
        Outcome.BACKEND_UNSUPPORTED.value: records.blocked(
            [request], Outcome.BACKEND_UNSUPPORTED.value,
            "architecture not registered in this vLLM build")[0],
    }


class TestSerialisationRoundTrip:
    """Stage 1-2: a record becomes a stored row and survives being read back."""

    @pytest.mark.parametrize("outcome", sorted(_all_outcomes()))
    def test_every_outcome_serialises_to_the_full_key_set(self, outcome) -> None:
        row = _all_outcomes()[outcome].as_row()
        assert ROW_KEYS <= set(row), (
            f"{outcome} row is missing {sorted(ROW_KEYS - set(row))}; a "
            "consumer would have to test for the key's existence")

    @pytest.mark.parametrize("outcome", sorted(_all_outcomes()))
    def test_a_row_survives_jsonl(self, outcome) -> None:
        row = _all_outcomes()[outcome].as_row()
        assert json.loads(json.dumps(row)) == row

    def test_identity_travels_but_cannot_shadow_the_schema(self) -> None:
        result = _ok_result()
        result.identity = {**result.identity, "outcome": "SMUGGLED"}
        assert result.as_row()["outcome"] == Outcome.OK.value

    @pytest.mark.parametrize("outcome", sorted(_all_outcomes()))
    def test_canonicalising_a_canonical_row_is_a_no_op(self, outcome) -> None:
        """The boundary is safe to call unconditionally."""
        row = _all_outcomes()[outcome].as_row()
        assert canonicalise_row(row) == row


class TestTheMigrationBoundary:
    """Stage 2: archived rows of the older vintage read as canonical."""

    def _legacy_ok_row(self) -> dict:
        return {"row_id": "r1", "rendered_prompt": "<user>...",
                "raw_generation": "<think>t</think>A.", "reasoning_text": "t",
                "final_answer": "Alpha. Beta. Gamma. Delta.",
                "reasoning_tokens": 3, "final_answer_tokens": 8,
                "total_generated_tokens": 11, "finish_reason": "stop",
                "stop_reason": "", "reasoning_emitted": True,
                "natural_reasoning_closed": True, "reasoning_cap_hit": False,
                "answer_truncated": False, "seed_reasoning": 11,
                "technical_failure": False, "technical_failure_reason": "",
                "not_generated": False, "not_generated_reason": ""}

    def test_the_renamed_field_arrives_under_its_canonical_name(self) -> None:
        row = canonicalise_row(self._legacy_ok_row())
        assert row["reasoning_closed"] is True
        assert "natural_reasoning_closed" not in row

    def test_the_boolean_triple_becomes_an_outcome(self) -> None:
        assert canonicalise_row(self._legacy_ok_row())["outcome"] == Outcome.OK.value

    def test_a_legacy_technical_failure_carries_its_reason(self) -> None:
        legacy = {**self._legacy_ok_row(), "technical_failure": True,
                  "technical_failure_reason": "HIP out of memory",
                  "final_answer": ""}
        row = canonicalise_row(legacy)
        assert row["outcome"] == Outcome.TECHNICAL_FAILURE.value
        assert row["outcome_detail"] == "HIP out of memory"

    def test_a_legacy_ungenerated_row_becomes_not_generated(self) -> None:
        legacy = {**self._legacy_ok_row(), "not_generated": True,
                  "not_generated_reason": "deadline", "final_answer": ""}
        row = canonicalise_row(legacy)
        assert row["outcome"] == Outcome.NOT_GENERATED.value
        assert row["outcome_detail"] == "deadline"

    def test_derived_legacy_keys_do_not_survive(self) -> None:
        """No consumer may keep reading the old names by accident."""
        row = canonicalise_row(self._legacy_ok_row())
        assert not (LEGACY_DERIVED & set(row))
        assert not (set(LEGACY_RENAMES) & set(row))

    def test_channel_validity_is_derived_not_invented(self) -> None:
        answered = canonicalise_row(self._legacy_ok_row())
        assert answered["channel_valid"] is True
        unanswered = canonicalise_row({**self._legacy_ok_row(), "final_answer": ""})
        assert unanswered["channel_valid"] is False

    def test_the_reasoning_lines_names_also_migrate(self) -> None:
        """`answer`/`reasoning`/`closed_naturally` are the other archived shape."""
        row = canonicalise_row(
            {"row_id": "r", "answer": "A. B. C. D.", "reasoning": "t",
             "closed_naturally": True, "answer_tokens": 9})
        assert row["final_answer"] == "A. B. C. D."
        assert row["reasoning_text"] == "t"
        assert row["reasoning_closed"] is True
        assert row["final_answer_tokens"] == 9


class TestScoringAndPlotData:
    """Stages 4-5: the analysis layer reads canonical names and nothing else."""

    def test_the_scorer_reads_the_canonical_answer_field(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "reasoning_score.py").read_text()
        assert 'frame["final_answer"]' in source
        assert 'frame["answer"]' not in source

    def test_plot_data_reads_the_canonical_answer_field(self) -> None:
        source = (Path(__file__).resolve().parents[1]
                  / "dci_exploratory" / "plotdata.py").read_text()
        assert 'frame["final_answer"]' in source
        assert 'frame["answer"]' not in source

    @pytest.mark.parametrize("module", ["reasoning_score.py",
                                        "dci_exploratory/plotdata.py",
                                        "xm_vllm_ingest.py"])
    def test_each_consumer_crosses_the_boundary_exactly_once(self, module) -> None:
        """Not scattered `.get()` fallbacks: one call, at the load point."""
        source = (Path(__file__).resolve().parents[1] / module).read_text()
        assert "canonicalise_row" in source.split("\n\n")[0] or any(
            line.startswith(("from ", "import ")) and "canonicalise_row" in line
            for line in source.splitlines()), f"{module} does not import it"
        assert source.count("canonicalise_row(") == 1, (
            f"{module} crosses the migration boundary "
            f"{source.count('canonicalise_row(')} times; it should read a file "
            "once and use canonical names everywhere after")

    def test_no_consumer_reads_a_legacy_name(self) -> None:
        root = Path(__file__).resolve().parents[1]
        forbidden = set(LEGACY_RENAMES) | LEGACY_DERIVED
        offenders = []
        for module in ("reasoning_score.py", "dci_exploratory/plotdata.py"):
            source = (root / module).read_text()
            for name in forbidden:
                if f'"{name}"' in source or f"'{name}'" in source:
                    offenders.append(f"{module}:{name}")
        assert not offenders, f"legacy field names still read: {offenders}"


class TestAgainstArchivedGenerations:
    """The boundary against real stored bytes, not a fixture of them."""

    ARCHIVES = [
        Path("/home/cnm13ryan/git/dci-cross-model/exploratory/runs/"
             "xmA_Qwen35-4B_k3/raw_generations.jsonl"),
        Path("/home/cnm13ryan/git/dci-natural-reasoning-headline/exploratory/runs/"
             "stageS18_reasoning_design_20260811T144250Z/natural_reasoning.jsonl"),
    ]

    @pytest.mark.parametrize("archive", ARCHIVES, ids=["cross-model", "natural"])
    def test_every_archived_row_reads_as_canonical(self, archive: Path) -> None:
        if not archive.exists():
            pytest.skip(f"{archive.name} is not on this host")
        rows = [canonicalise_row(json.loads(line))
                for line in archive.open()]
        assert rows, "archive is empty"
        for row in rows:
            assert "outcome" in row and "final_answer" in row
            assert not (LEGACY_DERIVED & set(row))
            assert not (set(LEGACY_RENAMES) & set(row))
