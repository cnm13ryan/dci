"""The reporting pass must get its verdicts from the shared layer.

Before this, `xm_actual_results.py` carried a local `degeneracy()` helper that
emitted three labels — TARGET_CEILING, TARGET_FLOOR, estimable — and could see
only two failure modes. The identification layer distinguishes thirteen, and the
ones it adds are the ones this dataset actually hits: an undelivered focal
instruction is not a ceiling, and neither is a cap-truncated run.

Two properties are pinned here:

  * the reporting pass agrees with the layer, cell for cell, so the two cannot
    drift apart again;
  * a summary that requires estimability pools IDENTIFIED cells only.

The evidence mapping is tested directly, because it is where a wrong answer
would be silent. `channel_valid_rate` is NOT `scoreable`: a cap-truncated row
separated its channels perfectly and simply produced no answer, and reporting it
as a parser failure would be a false CHANNEL_INVALID.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xm_actual_results as R  # noqa: E402
from crossmodel import contract, identification, schema  # noqa: E402

FOCAL, REFERENCE = contract.FOCAL, contract.REFERENCE
SEMI = contract.SEMICOLON_BACKGROUND


def row(task: int, arm: str, *, answered: bool = True, cap_hit: bool = False,
        technical: bool = False, answer: str = "Alpha. Beta. Gamma. Delta.",
        replicate: int = 0, reasoning_text: str | None = "thinking",
        forced_close: bool = False) -> dict:
    status = (schema.TECHNICAL_FAILURE if technical
              else schema.FINAL_ANSWER if answered
              else schema.NO_FINAL_WITHIN_BUDGET)
    return {
        "row_id": f"r{task}-{arm}-{replicate}-{int(cap_hit)}",
        "task_id": f"PLT{task:02d}", "arm": arm, "background": SEMI,
        "model_id": "org/M", "model_revision": "0" * 40, "backend": "transformers",
        "backend_version": "1", "load": contract.LOAD, "replicate_id": replicate,
        "reasoning_mode": "NO_THINKING", "order": "QAC",
        "final_answer": answer if answered else "",
        "final_answer_status": status,
        "reasoning_cap_hit": cap_hit, "technical_failure": technical,
        "reasoning_text": reasoning_text or "",
        "reasoning_emitted": bool(reasoning_text),
        "forced_close_artefact": forced_close,
        "not_generated": False, "generation_ceiling": 8192,
        "engineering_ceiling": 8192, "answer_truncated": False,
    }


def scored(rows: list[dict]) -> pd.DataFrame:
    return R.score(pd.DataFrame(rows))


class TestEvidenceMapping:
    def test_a_cap_truncated_row_is_not_a_channel_failure(self) -> None:
        """The mapping error that would produce a false CHANNEL_INVALID.

        The channel fields are supplied here, because the rate is DERIVED from
        them rather than defaulted — see the no-evidence case below.
        """
        rows = []
        for task in range(10):
            rows.append(row(task, FOCAL, answered=False, cap_hit=True,
                            reasoning_text="thinking at length"))
            rows.append(row(task, REFERENCE, reasoning_text="thinking"))
        frame = scored(rows)
        evidence = R.cell_evidence(frame, R.tau_per_task(frame))
        assert evidence.channel_valid_rate == 1.0, (
            "a cap-truncated run was reported as a channel failure")
        assert evidence.cap_hit_rate == pytest.approx(0.5)

    def test_absent_channel_fields_yield_no_evidence_not_one(self) -> None:
        """The fail-open shape the self-audit found: absence became 1.0."""
        rows = [row(t, arm, reasoning_text=None)
                for t in range(10) for arm in (FOCAL, REFERENCE)]
        frame = scored(rows).drop(columns=["reasoning_text", "reasoning_emitted"])
        evidence = R.cell_evidence(frame, R.tau_per_task(frame))
        assert evidence.channel_valid_rate is None

    def test_raw_text_in_both_channels_is_a_channel_failure(self) -> None:
        """The X2 shape: the parser returned the generation as both channels."""
        rows = []
        for task in range(10):
            for arm in (FOCAL, REFERENCE):
                same = "Alpha. Beta. Gamma. Delta."
                rows.append(row(task, arm, answer=same, reasoning_text=same))
        frame = scored(rows)
        evidence = R.cell_evidence(frame, R.tau_per_task(frame))
        assert evidence.channel_valid_rate == 0.0

    def test_a_forced_close_artefact_is_a_channel_failure(self) -> None:
        rows = [row(t, arm, reasoning_text="x", forced_close=True)
                for t in range(10) for arm in (FOCAL, REFERENCE)]
        evidence = R.cell_evidence(scored(rows), R.tau_per_task(scored(rows)))
        assert evidence.channel_valid_rate == 0.0

    def test_channel_valid_column_is_used_when_present(self) -> None:
        rows = [row(t, arm) for t in range(6) for arm in (FOCAL, REFERENCE)]
        frame = scored(rows)
        frame["channel_valid"] = [False] * 4 + [True] * (len(frame) - 4)
        evidence = R.cell_evidence(frame, R.tau_per_task(frame))
        assert evidence.channel_valid_rate < 1.0

    def test_technical_failures_are_counted_as_apparatus(self) -> None:
        rows = [row(t, arm) for t in range(8) for arm in (FOCAL, REFERENCE)]
        rows.append(row(99, FOCAL, technical=True, answered=False))
        frame = scored(rows)
        evidence = R.cell_evidence(frame, R.tau_per_task(frame))
        assert evidence.technical_failure_rate > 0


class TestReportAgreesWithTheLayer:
    def test_per_cell_verdict_equals_a_direct_classify_call(self) -> None:
        # Whatever the verdict is, the report and the layer must agree on it.
        rows = [row(t, arm) for t in range(10) for arm in (FOCAL, REFERENCE)]
        frame = scored(rows)
        cells = R.per_cell(frame)
        assert len(cells) == 1
        direct = identification.classify(
            R.cell_evidence(frame, R.tau_per_task(frame)))
        assert cells.iloc[0]["identification"] == direct.status

    def test_every_cell_carries_a_verdict_and_its_reason(self) -> None:
        rows = [row(t, arm) for t in range(10) for arm in (FOCAL, REFERENCE)]
        cells = R.per_cell(scored(rows))
        assert cells["identification"].notna().all()
        assert (cells["identification_reason"].str.len() > 0).all()
        assert set(cells["identification"]) <= set(identification.ALL_VERDICTS)

    def test_the_constituents_are_published_beside_the_verdict(self) -> None:
        rows = [row(t, arm) for t in range(10) for arm in (FOCAL, REFERENCE)]
        cells = R.per_cell(scored(rows))
        for column in ("focal_uptake", "reference_uptake", "cap_hit_rate",
                       "A_fail_focal", "A_fail_reference", "n_tasks"):
            assert column in cells.columns, f"{column} not reported"

    def test_the_second_layer_is_published_as_a_conditional(self) -> None:
        """The column named what was assumed; it once read as an observation."""
        rows = [row(t, arm) for t in range(10) for arm in (FOCAL, REFERENCE)]
        frame = scored(rows)
        cells = R.per_cell(frame)
        assert "behavioural" not in cells.columns
        reading = identification.read(R.cell_evidence(frame, R.tau_per_task(frame)))
        cell = cells.iloc[0]
        assert cell["behavioural_if_prerequisites_pass"] == reading.behavioural.status
        assert cell["prerequisites_assumed"] == (
            ", ".join(reading.conditional_on) or "none")
        if reading.conditional_on:
            assert cell["behavioural_if_prerequisites_pass"] != identification.IDENTIFIED
            assert cell["behavioural_reason"].startswith("conditional on ")

    def test_the_narrow_local_helper_is_gone(self) -> None:
        assert not hasattr(R, "degeneracy"), (
            "the duplicate degeneracy() helper is still present")


class TestOnlyIdentifiedCellsPool:
    @staticmethod
    def _cells(*flags: bool) -> pd.DataFrame:
        return pd.DataFrame([{
            "model": "M", "model_id": "org/M", "backend": "transformers",
            "load": 3, "background": f"bg{i}", "variant": f"bg{i}",
            "requested": 80, "final_answers": 80,
            "final_answers_focal": 40, "final_answers_reference": 40,
            "no_final": 0, "technical_failures": 0, "not_generated": 0,
            "A_fail_focal": 0.5, "A_fail_reference": 0.1,
            "tau": 0.4 if ok else 0.0, "lo": 0.0, "hi": 0.0, "n_tasks": 20,
            "joint_focal": 0.0, "focal_uptake": 1.0, "reference_uptake": 1.0,
            "cap_hit_rate": 0.0,
            "identification": "IDENTIFIED" if ok else "TARGET_CEILING",
            "identification_reason": "", "estimable": ok,
        } for i, ok in enumerate(flags)])

    def test_unidentified_cells_do_not_dilute_pooled_tau(self) -> None:
        """A structural zero must not be averaged into a headline effect."""
        row_ = R.headline(self._cells(True, False)).iloc[0]
        assert row_["tau (identified only)"] == pytest.approx(0.4)
        assert row_["Cells"] == 2
        assert row_["Identified"] == 1

    def test_no_identified_cell_yields_no_pooled_tau(self) -> None:
        row_ = R.headline(self._cells(False, False)).iloc[0]
        assert np.isnan(row_["tau (identified only)"])
        assert row_["Identified"] == 0

    def test_all_identified_pools_everything(self) -> None:
        row_ = R.headline(self._cells(True, True)).iloc[0]
        assert row_["tau (identified only)"] == pytest.approx(0.4)
        assert row_["Identified"] == 2
