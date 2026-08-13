"""Machine-readable artifacts must be valid JSON.

Python's `json` emits bare `NaN`, `Infinity` and `-Infinity` by default, and
none of the three is valid JSON — RFC 8259 has no non-finite literals. The
consequences differ by consumer, which is what makes it insidious:

  * `node`'s JSON.parse rejects the whole file;
  * Python's loader rejects it under `parse_constant`, and silently returns
    float NaN without;
  * `jq` accepts it and rewrites NaN to `null`, so a reader gets a different
    value than the writer wrote, with no error anywhere.

Reported on PR #19 for the headline estimate. The audit found it wider: the
per-row JSONL had 480 invalid lines, and the generation-ceiling fields carried
it too — those NaNs came from the ceiling repair earlier in this same PR, which
correctly refused to coerce a missing ceiling to 0 and then serialized the
absence as an invalid token.

`null` is exactly how JSON expresses a missing value, so the conversion loses
nothing. `allow_nan=False` is the other half of the fix: it turns any future
non-finite into a loud failure at write time rather than an invalid artifact
found downstream.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xm_actual_results as R  # noqa: E402


def strict_loads(text: str):
    """Parse rejecting the non-finite tokens, as a conforming parser would."""
    def reject(token: str):
        raise ValueError(f"invalid JSON constant: {token}")
    return json.loads(text, parse_constant=reject)


class TestJsonSafe:
    def test_nan_becomes_none(self) -> None:
        assert R.json_safe(float("nan")) is None

    def test_infinities_become_none(self) -> None:
        assert R.json_safe(float("inf")) is None
        assert R.json_safe(float("-inf")) is None

    def test_finite_floats_survive_exactly(self) -> None:
        assert R.json_safe(0.031) == 0.031
        assert R.json_safe(0.0) == 0.0
        assert R.json_safe(-1.5) == -1.5

    def test_nested_structures_are_cleaned(self) -> None:
        payload = {"a": [1.0, float("nan"), {"b": float("inf")}],
                   "c": {"d": [float("nan")]}}
        assert R.json_safe(payload) == {"a": [1.0, None, {"b": None}],
                                        "c": {"d": [None]}}

    def test_numpy_scalars_are_converted(self) -> None:
        assert R.json_safe(np.float64("nan")) is None
        assert R.json_safe(np.float64(2.5)) == 2.5
        assert R.json_safe(np.int64(7)) == 7
        assert R.json_safe(np.bool_(True)) is True

    def test_non_numeric_values_pass_through(self) -> None:
        assert R.json_safe("IDENTIFIED") == "IDENTIFIED"
        assert R.json_safe(None) is None
        assert R.json_safe(True) is True


class TestSerialisedOutputIsStrictlyValid:
    @staticmethod
    def payload() -> dict:
        """The shape that broke: a model with no identified cells, and a run
        with no recorded ceiling."""
        return {
            "headline": [{"Model": "M", "Identified": 0,
                          "tau (identified only)": float("nan"),
                          "A-fail focal": float("nan")}],
            "executions": [{"model_id": "org/M",
                            "generation_ceiling": float("nan"),
                            "engineering_ceiling": float("nan")}],
        }

    def test_the_raw_payload_is_invalid_json(self) -> None:
        """Pins the defect, so a regression is detectable rather than absent."""
        text = json.dumps(self.payload())
        assert "NaN" in text
        with pytest.raises(ValueError):
            strict_loads(text)

    def test_json_safe_makes_it_valid(self) -> None:
        text = json.dumps(R.json_safe(self.payload()))
        assert "NaN" not in text
        parsed = strict_loads(text)
        assert parsed["headline"][0]["tau (identified only)"] is None
        assert parsed["executions"][0]["generation_ceiling"] is None

    def test_allow_nan_false_refuses_to_write_a_bad_artifact(self) -> None:
        """The guard: a future non-finite must fail loudly at write time."""
        with pytest.raises(ValueError):
            json.dumps(self.payload(), allow_nan=False)

    def test_allow_nan_false_accepts_the_cleaned_payload(self) -> None:
        json.dumps(R.json_safe(self.payload()), allow_nan=False)

    def test_a_missing_estimate_reads_as_absent_not_as_zero(self) -> None:
        """null must not be confused with a real 0.0 estimate."""
        cleaned = R.json_safe({"tau": float("nan"), "other": 0.0})
        assert cleaned["tau"] is None
        assert cleaned["other"] == 0.0
