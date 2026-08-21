"""Gate 0, the procedural pilot (§19).

Twelve fixed pre-screen topics, all 47 cells, both orders, the registered
wording allocation, M = 4: **2,256 cached draws**. Fixture values for every
slot exercise the structure and **cannot become calibration evidence** ---
nothing measured here is read by Gate 2, Gate 3 or Gate 4.

The pilot is technical only. It computes and exposes **no** compliance rate,
delivery loss, companion swap or contrast: its structurally complete analysis
is persisted fully redacted, with every numeric value replaced. `redact` and
`assert_fully_redacted` are what make that true rather than promised.

**What v4r3 adds to v4r2's Gate 0.** §19 now requires the redacted result to
carry *a fitted difficulty relation, a support diagnostic and a
delta_difficulty row*. That is the whole point of running the pilot at all in
a study whose headline estimand is a refit residual: if the spectrum machinery
cannot run end to end on fixtures, it will not run on 144,384 real
generations either, and finding that out afterwards would cost the run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.errors import TerminalStatus

from dci1v4r3.protocol import constants as C

__all__ = ["REDACTED", "PILOT_FIXTURES", "pilot_slot_map", "redact",
           "assert_fully_redacted", "assert_structural_completeness",
           "acceptance", "pilot_payload", "expected_draws"]

REDACTED = "REDACTED"

#: Fixture severities. Mid-grid values that exercise every code path and are
#: never read by a calibration or admission rule. The spectrum rungs bracket
#: their core reference so the fit has points on both sides of every
#: intercept, which is what makes the fixture run a real exercise of §11.7
#: rather than a shape check.
PILOT_FIXTURES: dict[str, tuple[str, int]] = {
    "A": ("A", 3), "B": ("B", 8),
    "R1": ("RF1", 3), "R1-": ("RF1", 1), "R1+": ("RF1", 5),
    "R2": ("RF5", 4), "R2-": ("RF5", 2), "R2+": ("RF5", 6),
    "R3": ("RF7", 6), "R3-": ("RF7", 4), "R3+": ("RF7", 8),
    C.CLASS_SLOT: ("CL7", 30),
}

#: slot -> the registered constraint family the fit groups it under (§11.7).
#: A and the class companion are deliberately absent: both are excluded from
#: the fit, and `spectrum.SpectrumInput` refuses them if they appear.
PILOT_FIT_FAMILIES = {"R1": "RF1", "R1-": "RF1", "R1+": "RF1",
                      "R2": "RF5", "R2-": "RF5", "R2+": "RF5",
                      "R3": "RF7", "R3-": "RF7", "R3+": "RF7"}


def pilot_slot_map() -> dict[str, tuple[str, int]]:
    return dict(PILOT_FIXTURES)


def expected_draws(*, cells: int = C.N_CELLS_FULL,
                   topics: int = C.PILOT_TOPICS,
                   draws: int = C.PILOT_DRAWS) -> int:
    """§19's 2,256: twelve topics x forty-seven cells x M = 4."""
    return topics * cells * draws


def redact(value: Any) -> Any:
    """Replace every numeric value, recursively, leaving structure intact."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return REDACTED
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


def assert_fully_redacted(payload: Any, path: str = "") -> None:
    """Refuse a pilot analysis that still carries a number."""
    if isinstance(payload, bool):
        return
    if isinstance(payload, (int, float)):
        raise AssertionError(
            f"the pilot analysis exposes a numeric value at "
            f"{path or '<root>'}; §19 requires every numeric value to be "
            f"redacted")
    if isinstance(payload, dict):
        for key, value in payload.items():
            assert_fully_redacted(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            assert_fully_redacted(value, f"{path}[{index}]")


#: §19's structural requirements on the redacted result. Presence of the KEY
#: is what is checked; the value is redacted by the time anyone sees it.
REQUIRED_RESULT_STRUCTURE = (
    ("F1", "D(B<-A)"), ("F1", "D(A<-B)"), ("F1", "Lambda"),
    ("F1", "Delta_R"), ("F1", "Xi"), ("F1", "delta_difficulty"),
    ("F8", "beta"), ("F9", "Delta_class"),
)


def assert_structural_completeness(result: Mapping[str, Any],
                                   support: Mapping[str, Any] | None) -> None:
    """§19: a fitted difficulty relation, a support diagnostic, a delta row.

    Checked on the structure the pipeline produced, before redaction, and
    stated as required (family, member) pairs so that a pipeline which
    silently dropped the spectrum arm cannot pass Gate 0.
    """
    missing = [f"{family}:{member}"
               for family, member in REQUIRED_RESULT_STRUCTURE
               if member not in (result.get(family, {}).get("members") or {})]
    if missing:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "status": "APPARATUS_FAILURE", "gate": C.STAGE_GATE0,
            "model_key": "-", "producing_commit": "-",
            "criterion": "§19's structurally complete result table",
            "observed": {"missing": missing},
            "strongest_permissible_statement":
                f"the pipeline produced a result table missing {missing}; §19 "
                f"requires a fitted difficulty relation, a support diagnostic "
                f"and a delta_difficulty row before any real generation",
            "estimands_unanswerable": "all"})
    if not support:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "status": "APPARATUS_FAILURE", "gate": C.STAGE_GATE0,
            "model_key": "-", "producing_commit": "-",
            "criterion": "§19's support diagnostic",
            "observed": {"support": support},
            "strongest_permissible_statement":
                "the pipeline produced no support diagnostic; §19 requires "
                "one before any real generation",
            "estimands_unanswerable": "all"})


def acceptance(*, committed_once: bool, cells_complete: bool,
               technical_failures: int, codebook_valid: bool,
               structural_result: Mapping[str, Any],
               byte_mutation_refused: bool, durable_restore_matches: bool,
               pilot_mask_isolated: bool) -> dict[str, Any]:
    """The eight §19 acceptance conditions, each named and each checked."""
    conditions = {
        "every logical cell and draw committed exactly once": committed_once,
        "every cell yielding one cell mean over exactly M accepted draws":
            cells_complete,
        "zero technical generation failures after retries":
            technical_failures == 0,
        "every codebook field present and in domain": codebook_valid,
        "the full pipeline running to a structurally complete redacted result":
            bool(structural_result),
        "mutating one stored byte changes its content hash and causes the "
        "analysis to refuse the row": byte_mutation_refused,
        "cache deletion and durable restore reproducing every row with "
        "matching hashes": durable_restore_matches,
        "the separate pilot mask cycle completing without touching the "
        "confirmatory mask namespace": pilot_mask_isolated,
    }
    failed = [name for name, ok in conditions.items() if not ok]
    if failed:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "status": "APPARATUS_FAILURE", "gate": C.STAGE_GATE0,
            "model_key": "-", "producing_commit": "-",
            "criterion": "the eight §19 acceptance conditions",
            "threshold": "all eight", "observed": conditions,
            "strongest_permissible_statement":
                f"the apparatus failed {len(failed)} of eight acceptance "
                f"conditions; a repair creates a new producing commit and "
                f"requires qualification and the pilot to run again",
            "estimands_unanswerable": "all"})
    return {"conditions": conditions, "passed": True}


def pilot_payload(*, draws: int, cells: int,
                  structural_result: Mapping[str, Any],
                  support: Mapping[str, Any] | None,
                  acceptance_report: Mapping[str, Any],
                  mask_report: Mapping[str, Any],
                  model_key: str, pilot_dir: Path) -> dict[str, Any]:
    assert_structural_completeness(structural_result, support)
    redacted = redact(structural_result)
    assert_fully_redacted(redacted)
    redacted_support = redact(support)
    assert_fully_redacted(redacted_support)
    expected = expected_draws(cells=cells)
    if draws != expected:
        raise TerminalStatus("APPARATUS_FAILURE", {
            "status": "APPARATUS_FAILURE", "gate": C.STAGE_GATE0,
            "model_key": model_key, "producing_commit": "-",
            "criterion": "§19's cached-draw count",
            "observed": {"draws": draws, "expected": expected},
            "strongest_permissible_statement":
                f"the pilot committed {draws} draws where §19 registers "
                f"{expected}",
            "estimands_unanswerable": "all"})
    return {
        "outcome": "PASS", "stage": C.STAGE_GATE0,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE0],
        "model_key": model_key,
        "topics": C.PILOT_TOPICS, "cells": cells, "cached_draws": draws,
        "fixtures": {k: list(v) for k, v in PILOT_FIXTURES.items()},
        "fixtures_note": ("fixture values that exercise the structure and "
                          "cannot become calibration evidence (§19); no "
                          "Gate 2, Gate 3 or Gate 4 rule reads them"),
        "acceptance": dict(acceptance_report),
        "redacted_result": redacted,
        "redacted_support": redacted_support,
        "mask_cycle": dict(mask_report),
        "exposes_no_rate": True,
        "pilot_dir": str(pilot_dir),
        "identification_statuses": [],
    }
