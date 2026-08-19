"""Gate 0, the procedural pilot (§19).

Twelve fixed pre-screen topics, all 25 cells, both orders, the registered
wording allocation, M = 4: **1,200 cached draws**. Fixture values for n, m and
the reference severities exercise the structure and **cannot become calibration
evidence**: nothing measured here is read by Gate 2, Gate 3 or Gate 4.

The pilot is technical only. It computes and exposes **no** compliance rate,
delivery loss, companion swap or contrast: its structurally complete analysis
is persisted fully redacted, with every numeric value replaced. ``redact``
is what makes that true rather than promised.

All eight §19 acceptance conditions are checked here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.errors import TerminalStatus
from dci1v4.protocol import constants as C

REDACTED = "REDACTED"

#: Fixture severities. Mid-grid values that exercise every code path and are
#: never read by a calibration or admission rule.
PILOT_FIXTURES = {"A": 3, "B": 8,
                  "R1": ("RF1", 2), "R2": ("RF5", 4), "R3": ("RF7", 6)}


def pilot_slot_map() -> dict[str, tuple[str, int]]:
    return {"A": ("A", PILOT_FIXTURES["A"]), "B": ("B", PILOT_FIXTURES["B"]),
            "R1": PILOT_FIXTURES["R1"], "R2": PILOT_FIXTURES["R2"],
            "R3": PILOT_FIXTURES["R3"]}


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
        raise AssertionError(f"the pilot analysis exposes a numeric value at "
                             f"{path or '<root>'}; §19 requires every numeric "
                             f"value to be redacted")
    if isinstance(payload, dict):
        for key, value in payload.items():
            assert_fully_redacted(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            assert_fully_redacted(value, f"{path}[{index}]")


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
            "criterion": "the eight §19 acceptance conditions",
            "threshold": "all eight", "observed": conditions,
            "artifact_hashes": {},
            "strongest_permissible_statement":
                f"the apparatus failed {len(failed)} of eight acceptance "
                f"conditions; a repair creates a new producing commit and "
                f"requires qualification and the pilot to run again",
            "estimands_unanswerable": "all"})
    return {"conditions": conditions, "passed": True}


def pilot_payload(*, draws: int, cells: int,
                  structural_result: Mapping[str, Any],
                  acceptance_report: Mapping[str, Any],
                  pilot_dir: Path) -> dict[str, Any]:
    redacted = redact(structural_result)
    assert_fully_redacted(redacted)
    return {
        "outcome": "PASS",
        "topics": C.PILOT_TOPICS,
        "cells": cells,
        "cached_draws": draws,
        "fixtures": {k: (v if isinstance(v, int) else list(v))
                     for k, v in PILOT_FIXTURES.items()},
        "fixtures_note": ("fixture values that exercise the structure and "
                          "cannot become calibration evidence (§19)"),
        "acceptance": dict(acceptance_report),
        "redacted_result": redacted,
        "exposes_no_rate": True,
        "pilot_dir": str(pilot_dir),
        "identification_statuses": [],
    }
