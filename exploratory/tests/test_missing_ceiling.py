"""A run with no recorded generation ceiling must report the gap, not crash.

Defect (fixed in 0f117f7, previously without coverage): the reporting pass wrote
`int(value or 0)` for the generation ceiling. A column that is None in every row
arrives from pandas as float NaN, and **NaN is truthy in Python**, so `nan or 0`
evaluates to `nan` and `int(nan)` raises ValueError. Every one of the five
NO_THINKING/NATURAL runs stores a null ceiling, so the results document could
not be rebuilt from its own raw data — a reproducibility failure in a document
whose purpose is to assert provenance.

The audit that recovered this fix recorded it as the one repair with no
regression test. This is that test.

Three properties, because the obvious repair gets two of them wrong:

  * it must not raise;
  * it must not coerce a missing ceiling to 0 — absent is not a limit of zero,
    and a reader who saw "0" would conclude generation was impossible;
  * it must render the gap as a gap.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xm_actual_results as R  # noqa: E402
from crossmodel import contract, schema  # noqa: E402

FOCAL, REFERENCE = contract.FOCAL, contract.REFERENCE


def row(task: int, arm: str, ceiling, replicate: int = 0) -> dict:
    return {
        "row_id": f"r{task}-{arm}-{replicate}", "task_id": f"PLT{task:02d}",
        "arm": arm, "background": contract.SEMICOLON_BACKGROUND,
        "model_id": "org/M", "model_revision": "0" * 40,
        "backend": "transformers", "backend_version": "1",
        "load": contract.LOAD, "replicate_id": replicate,
        "reasoning_mode": "NO_THINKING", "order": "QAC",
        "final_answer": "Alpha. Beta. Gamma. Delta.",
        "final_answer_status": schema.FINAL_ANSWER,
        "reasoning_cap_hit": False, "technical_failure": False,
        "not_generated": False, "answer_truncated": False,
        "reasoning_tokens": 10, "final_answer_tokens": 8,
        "generation_ceiling": ceiling, "engineering_ceiling": ceiling,
        "natural_reasoning_closed": True, "latency_seconds": 1.0,
        # Provenance fields the manifest reprints verbatim.
        "model_family": "test", "dtype": "bfloat16", "quantization": "none",
        "device_configuration": "cuda:0", "thinking_implementation": "none",
        "reasoning_parser": "none", "reasoning_control": "none",
        "temperature": 0.7, "top_p": 0.9,
        "top_k": 0, "max_final_answer_tokens": 512, "seed_reasoning": 1,
        "chat_template_sha256": "0" * 64, "paraphrase_id": 0,
        "source_dir": "runs/fixture",
    }


def frame(ceiling) -> pd.DataFrame:
    rows = [row(t, arm, ceiling) for t in range(10)
            for arm in (FOCAL, REFERENCE)]
    return R.score(pd.DataFrame(rows))


def mixed_frame() -> pd.DataFrame:
    """One checkpoint that records a ceiling, one that does not.

    This is the shape that actually broke the reporting pass, and a single
    all-None run does NOT reproduce it. With every value None, pandas keeps the
    column as `object` holding real `None`, and `None or 0` is a harmless 0.
    Concatenating a run that stores 8192 with one that stores null coerces the
    column to float64, the nulls become **NaN**, and NaN is truthy — so
    `nan or 0` evaluates to nan and `int(nan)` raises. Reporting over several
    run directories at once is the normal way this script is invoked, so the
    mixed frame is the realistic case rather than the exotic one.
    """
    rows = [row(t, arm, 8192) for t in range(10) for arm in (FOCAL, REFERENCE)]
    for record in rows:
        record["model_id"] = "org/HasCeiling"
    absent = [row(t, arm, None) for t in range(10)
              for arm in (FOCAL, REFERENCE)]
    for record in absent:
        record["model_id"] = "org/NoCeiling"
        record["row_id"] += "-b"
    return R.score(pd.DataFrame(rows + absent))


class TestMixedCeilingIsTheRealFailureShape:
    """The reproduction that a single all-None run cannot provide."""

    def test_the_mixed_column_really_is_float_nan(self) -> None:
        column = mixed_frame()["generation_ceiling"]
        assert column.dtype.kind == "f", (
            "fixture no longer coerces to float; it would stop covering the bug")
        assert column.isna().any()

    def test_termination_survives_the_mixed_frame(self) -> None:
        table = R.termination(mixed_frame())
        assert len(table) == 2
        ceilings = sorted(table["ceiling"].tolist(), key=lambda v: (v != v, v))
        assert ceilings[0] == 8192.0
        assert math.isnan(ceilings[1])

    def test_manifest_survives_the_mixed_frame(self) -> None:
        entries = {e["model_id"]: e for e in R.manifest(mixed_frame())}
        assert entries["org/HasCeiling"]["generation_ceiling"] == 8192.0
        assert math.isnan(entries["org/NoCeiling"]["generation_ceiling"])

    def test_the_prefix_guard_would_raise_on_this_frame(self, monkeypatch) -> None:
        """Proves the coverage: restore `int(x or 0)` and the report dies."""
        monkeypatch.setattr(R, "_optional_float", lambda v: int(v or 0))
        with pytest.raises(ValueError):
            R.termination(mixed_frame())


class TestOptionalFloat:
    """The helper the repair turns on."""

    def test_none_becomes_nan_not_zero(self) -> None:
        assert math.isnan(R._optional_float(None))

    def test_nan_becomes_nan_not_zero(self) -> None:
        assert math.isnan(R._optional_float(float("nan")))

    def test_a_real_ceiling_survives(self) -> None:
        assert R._optional_float(8192) == 8192.0

    def test_zero_is_preserved_as_zero(self) -> None:
        """A recorded 0 is data; only an ABSENT value becomes NaN."""
        assert R._optional_float(0) == 0.0

    def test_the_naive_guard_would_have_raised(self) -> None:
        """Pins why `or 0` is wrong: NaN is truthy."""
        nan = float("nan")
        assert (nan or 0) is nan, "NaN stopped being truthy; revisit the repair"
        with pytest.raises(ValueError):
            int(nan or 0)


class TestReportingWithNoCeiling:
    @pytest.mark.parametrize("ceiling", [None, float("nan")])
    def test_termination_table_does_not_crash(self, ceiling) -> None:
        table = R.termination(frame(ceiling))
        assert len(table) == 1

    @pytest.mark.parametrize("ceiling", [None, float("nan")])
    def test_missing_ceiling_is_nan_not_zero(self, ceiling) -> None:
        table = R.termination(frame(ceiling))
        value = table.iloc[0]["ceiling"]
        assert math.isnan(value), f"absent ceiling became {value!r}"

    @pytest.mark.parametrize("ceiling", [None, float("nan")])
    def test_manifest_does_not_crash(self, ceiling) -> None:
        entries = R.manifest(frame(ceiling))
        assert entries
        assert math.isnan(entries[0]["generation_ceiling"])

    def test_a_recorded_ceiling_still_reports(self) -> None:
        table = R.termination(frame(8192))
        assert table.iloc[0]["ceiling"] == 8192.0


class TestRendering:
    def test_missing_ceiling_renders_as_a_gap_not_a_number(self) -> None:
        rendered = R.table(R.termination(frame(None)))
        header, _rule, data = rendered.strip().splitlines()[:3]
        columns = [c.strip() for c in header.strip("|").split("|")]
        values = [c.strip() for c in data.strip("|").split("|")]
        ceiling = values[columns.index("ceiling")]
        assert ceiling == "—", f"absent ceiling rendered as {ceiling!r}"

    def test_a_recorded_ceiling_renders_as_a_number(self) -> None:
        rendered = R.table(R.termination(frame(8192)))
        header, _rule, data = rendered.strip().splitlines()[:3]
        columns = [c.strip() for c in header.strip("|").split("|")]
        values = [c.strip() for c in data.strip("|").split("|")]
        assert values[columns.index("ceiling")] != "—"

    def test_prose_says_not_recorded(self) -> None:
        assert "NOT RECORDED" in R._ceiling_phrase(float("nan"))
        assert "NOT RECORDED" in R._ceiling_phrase(None)

    def test_prose_reports_a_real_ceiling(self) -> None:
        phrase = R._ceiling_phrase(8192)
        assert "8,192" in phrase and "NOT RECORDED" not in phrase
