"""Fixtures for the v5 suite: synthetic observations and calibration rows.

Everything here is **fixture data**. No fixture value can become calibration
or confirmatory evidence: the topic identifiers are `fixture-*`, the model key
is `fixture-model`, and nothing in this file is written to an evidence tree.
"""
from __future__ import annotations

import random
from typing import Any, Sequence

import pytest

from dci1v5.analysis.observations import ObservationTable, build_observations
from dci1v5.design.cells import cell_types, normalise_arms
from dci1v5.protocol import constants as C
from dci1v5.stages.calibration_table import CalibrationRow
from dci1v5.stages.interaction import KappaUnderBSource

FIXTURE_MODEL = "fixture-model"
FIXTURE_M_STAR = 9


def _score(slot: str, passed: bool, *, position: int | None,
           present: bool = True) -> dict[str, Any]:
    return {"slot": slot, "kind": "A" if slot == "A" else
            "B" if slot == "B" else "MK1",
            "severity": 3, "passed": passed, "graded": 1.0 if passed else 0.0,
            "non_vacuous": True, "vacuous_pass": False, "position": position,
            "present": present, "processing_failure": False}


def synthetic_rows(arms: Sequence[str], *, blocks: int = 8,
                   m_draws: int = 4, seed: int = 11,
                   rates: dict[tuple[str, str | None, str | None], float]
                   | None = None) -> list[dict[str, Any]]:
    """Rows for ``build_observations`` over an admitted arm set.

    ``rates`` maps (outcome slot, companion slot or None, configuration or
    None) to a compliance probability, so a test can install a known
    order effect and read it back out of an estimator.
    """
    rng = random.Random(seed)
    rates = dict(rates or {})
    admitted = normalise_arms(arms)
    types = cell_types(admitted)
    rows: list[dict[str, Any]] = []
    for index in range(blocks):
        block_id = f"fixture-block-{index:03d}"
        for cell in types:
            for draw in range(m_draws):
                scores = []
                if cell.arm == "unconstrained":
                    slots = [s for s in
                             {sl for t in types for sl in t.slots}]
                    for slot in sorted(slots):
                        rate = rates.get((slot, None, None), 0.02)
                        # §9.1: the load-0 prompt states nothing, so every
                        # verdict on it is an ABSENT verdict. An earlier
                        # fixture marked them present, which is the one
                        # convention the production scorer cannot produce.
                        scores.append(_score(slot, rng.random() < rate,
                                             position=1, present=False))
                elif cell.arm == "solo":
                    slot = cell.slots[0]
                    rate = rates.get((slot, None, "solo"), 0.7)
                    scores.append(_score(slot, rng.random() < rate,
                                         position=1))
                else:
                    for position, slot in enumerate(cell.slots, start=1):
                        companion = cell.slots[1 - (position - 1)]
                        configuration = cell.configuration_of(slot)
                        rate = rates.get((slot, companion, configuration), 0.5)
                        scores.append(_score(slot, rng.random() < rate,
                                             position=position))
                rows.append({
                    "block_id": block_id, "cell_id": cell.cell_id,
                    "arm": cell.arm, "draw_index": draw, "scores": scores,
                    "truncated": False, "word_count": 80,
                    "exact_count_alternatives": {"s1": 3, "s2": 3, "s3": 3},
                })
    return rows


def observation_table(arms: Sequence[str], **kwargs: Any) -> ObservationTable:
    rows = synthetic_rows(arms, **kwargs)
    m_draws = kwargs.get("m_draws", 4)
    return ObservationTable(build_observations(rows, m_draws=m_draws))


def kappa_source(candidate: str, *, m_star: int = FIXTURE_M_STAR,
                 split: str = "pooled", load: int = 1,
                 present: tuple[str, ...] | None = None,
                 model_key: str = FIXTURE_MODEL,
                 n_topics: int = C.N_CALIBRATION) -> KappaUnderBSource:
    return KappaUnderBSource(
        load=load, present=present if present is not None
        else (f"B:{m_star}",), candidate=candidate, model_key=model_key,
        m_star=m_star, split=split, n_topics=n_topics, n_draws=C.M_CAL)


def calibration_row(kind: str, severity: int, *, solo: float,
                    chance: float = 0.01, split: str = "pooled",
                    kappa_b: float | None = 0.0, vacuity: float = 0.0,
                    n_topics: int = C.N_CALIBRATION,
                    per_topic: Sequence[float] = (),
                    **overrides: Any) -> CalibrationRow:
    label = f"{kind}:{severity}"
    source = (kappa_source(label, split=split, n_topics=n_topics)
              if kappa_b is not None else None)
    return CalibrationRow(
        kind=kind, severity=severity, split=split, model_key=FIXTURE_MODEL,
        solo_compliance=solo, chance_compliance=chance, solo_vacuity=vacuity,
        kappa_under_b=kappa_b, kappa_under_b_source=source,
        n_topics=n_topics, per_topic_solo=tuple(per_topic), **overrides)


@pytest.fixture
def restore_decisions():
    """Close decisions inside a test and restore the module afterwards."""
    from dci1v5.protocol import decisions

    yield decisions
    decisions.reopen_all_for_testing()


@pytest.fixture
def u4_named_for_testing():
    """Run U4 under a **named** §12.6 eligibility formulation, then restore.

    U4 is a researcher decision and no test takes it. What this supplies is
    the same thing `stages.regime.coverage_eligibility(formulation=...)`
    supplies: one of the two constructions, by name, so the machinery that
    depends on a resolved registry can be exercised. The registered namespace
    stays blocked --- `test_open_items` asserts that, and
    `test_the_plan_command_reports_the_one_open_question` asserts the CLI
    says so.
    """
    from dci1v5.protocol import open_items

    if "U4" in open_items.blocking_items():
        open_items.resolve("U4", "E1",
                           resolved_by="test harness; a named construction "
                                       "exercised, NOT an adoption",
                           resolved_on="test")
    yield open_items
    open_items.reopen_all_for_testing()


@pytest.fixture
def restore_open_items():
    """Resolve a specification question inside a test, then restore it."""
    from dci1v5.protocol import open_items

    yield open_items
    open_items.reopen_all_for_testing()
