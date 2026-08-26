"""Fixtures for the v6 suite: synthetic observations and calibration rows.

Everything here is **fixture data**. No fixture value can become calibration
or confirmatory evidence: the topic identifiers are `fixture-*`, the model key
is `fixture-model`, and nothing in this file is written to an evidence tree.

**One fixture is autouse and it needs its reason stated.** v5's suite ran
against ``reports/dci1v5/researcher_decisions.json``, a committed record of
closures the researcher had actually taken, so a test that walked a stage
found the decisions closed. **v6 has no such record and must not have one:**
v6 is not adopted, not registered, and all twenty-seven of D0 to D26 are
UNRESOLVED at import --- which is the correct state and is asserted by
``test_lifecycle.py``. Without a fixture, every test that runs a stage would
fail at stage 1 on ``REGISTRATION_INCOMPLETE`` and say nothing about the code
under test.

``harness_decisions`` therefore closes them **in process, per test, and never
durably**, and reopens the registry afterwards. It does it two ways, and the
difference matters:

* **D0-D18** come from ``fixture_v5_carried_decisions.json``, which is v5's
  own record copied into this directory as a fixture. Reading a *record* is
  how §34 D17's ``floor`` reaches the code at all --- the quantity, the value,
  the semantics and the derivation deliberately live in a record and not in
  the source --- so a harness that only supplied bare values could not
  exercise that path. ``decisions.RECORD_PATH`` is monkeypatched to the
  fixture for the duration of a test.
* **D19-D26**, v6's own, are supplied as bare harness values from
  ``synthetic_lifecycle.TEST_CLOSURES``. They are deliberately **absent** from
  the fixture: v6 has taken nothing and no file in this repository says
  otherwise.

A harness value is not a decision: it is what lets the suite reach the thing
it is testing. ``test_lifecycle.py`` asserts the committed state --- twenty-seven
open, no record on the real path --- from a fresh read that this fixture
cannot reach.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Sequence

import pytest

from dci1v6.analysis.observations import ObservationTable, build_observations
from dci1v6.design.cells import cell_types, normalise_arms
from dci1v6.protocol import constants as C
from dci1v6.stages.calibration_table import CalibrationRow
from dci1v6.stages.interaction import KappaUnderBSource

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
    from dci1v6.protocol import decisions

    yield decisions
    decisions.reopen_all_for_testing()


@pytest.fixture
def restore_open_items():
    """Resolve a specification question inside a test, then restore it."""
    from dci1v6.protocol import open_items

    yield open_items
    open_items.reopen_all_for_testing()


#: v5's researcher-decision record, as a **fixture**. See the module note.
FIXTURE_RECORD = Path(__file__).resolve().parent / \
    "fixture_v5_carried_decisions.json"


@pytest.fixture(autouse=True)
def harness_decisions(monkeypatch):
    """Close §34 in process for one test, then reopen. See the module note.

    Not durable, not a recommendation, and not evidence that any decision has
    been taken for v6.
    """
    from dci1v6.protocol import decisions, open_items

    from tests_v6 import synthetic_lifecycle

    monkeypatch.setattr(decisions, "RECORD_PATH", FIXTURE_RECORD)
    synthetic_lifecycle.use_fixture_record()
    for decision_id, value in synthetic_lifecycle.TEST_CLOSURES.items():
        if not decisions.is_closed(decision_id):
            decisions.close(
                decision_id, value,
                evidence="tests_v6 harness; not a researcher decision and "
                         "never durable",
                decided_by="tests_v6 harness", decided_on="synthetic")
    for item_id, resolution in (("U2", "A2"), ("U4", "E2"),
                                ("P1", "confirmed")):
        if open_items.get_item(item_id).resolution is None:
            open_items.resolve(item_id, resolution,
                               resolved_by="tests_v6 harness; not a "
                                           "researcher resolution",
                               resolved_on="synthetic")
    yield
    decisions.reopen_all_for_testing()
    open_items.reopen_all_for_testing()


@pytest.fixture(scope="session")
def v6_repo(tmp_path_factory):
    """A repository root where v6's two governed documents exist.

    **They do not exist in this repository and must not be created here.**
    §18 stage 1 binds the hash of ``user-notes/DCI1_preregistration_v6.md``
    and of ``dci1/reports/dci1v6/reference_design_spec.json``, neither of
    which is written --- so ``manifest.document_hashes`` raises ``Blocker``
    against the real root. That refusal is correct, it is blocker 3 of
    ``dci1/reports/dci1v6/READINESS.md``, and
    ``test_lifecycle.test_no_v6_registration_is_possible_yet`` asserts it.

    A test that is about something *else* --- supersession, invalidation,
    manifest binding, the amendment rules --- still has to get past stage 1.
    This builds the isolated, committed repository ``synthetic_lifecycle``
    already builds for the lifecycle walk, in which the two documents are
    labelled placeholders living in a pytest tmpdir.
    """
    from tests_v6.synthetic_lifecycle import synthetic_repo

    repo, _commit = synthetic_repo(tmp_path_factory.mktemp("v6-repo"))
    return repo
