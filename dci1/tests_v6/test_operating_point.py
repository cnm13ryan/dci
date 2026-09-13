"""The operating point, from Gate 2 to the freeze.

**m\\* is selected once and never moves.** §12.3 chooses it at Gate 2;
``GATE_2_75_COMPOSED_PROBE`` measures composed headroom at it and either
passes or terminates the replication. What these pin is that every quantity
which is a *property of the operating point* is read at the one the study
runs, **by name**, and that a read at any other is refused rather than
silently satisfied:

* §13.6's kappa(R|B) column, which ``assert_kappa_under_b_source`` refuses
  under a different m*. Gate 2 records the column at every admissible
  severity, so the refusal is a real check against a real alternative rather
  than a check that cannot fail for want of a second column;
* §13.1's qualified pool, computed from that column and selected by name from
  Gate 2.5's by-severity map;
* the freeze's slot map, whose ``B`` is bound at the operating point the study
  runs.

And one thing that would otherwise not be checked at all: an *eligible*
severity has passed §12.3's band test only, so P3.1 requires the probed m* to
be in ``focal_admissible`` --- eligible **and** adequate under §12.4 **and**
past §34 D17's construct floor at that severity.

The end-to-end branches live in
``scenarios.scenario_probe_passes_at_the_frozen_m_star`` and
``scenarios.scenario_probe_terminates_at_the_frozen_m_star``. These are the
cheap unit-level pins on the same four things.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.run.gates_run import _kappa_columns, _kappa_under_b
from dci1v6.stages.feasibility import calibration_rows_at, qualification_at
from dci1v6.stages.calibration_table import load_calibration_table
from dci1v6.verifiers.constraints import Constraint

from tests_v6.conftest import FIXTURE_MODEL

CANDIDATES = (Constraint("MK1", 1), Constraint("MK2", 2))


def _score(kind: str, severity: int, passed: bool, *, present: bool
           ) -> dict:
    return {"slot": "S0", "kind": kind, "severity": severity,
            "passed": passed, "graded": 1.0 if passed else 0.0,
            "non_vacuous": True, "vacuous_pass": False, "position": 1,
            "present": present, "processing_failure": False}


def _b_solo_rows(severity: int, *, rate_by_kind: dict[str, float]) -> list:
    """B-solo rows at one severity, every candidate scored as **absent**."""
    rows = []
    for index in range(8):
        split = C.CALIBRATION_A if index % 2 == 0 else C.CALIBRATION_B
        for draw in range(4):
            scores = [_score("B", severity, True, present=True)]
            for candidate in CANDIDATES:
                hit = ((index + draw) / 4.0) < rate_by_kind[candidate.kind]
                scores.append(_score(candidate.kind, candidate.severity, hit,
                                     present=False))
            rows.append({
                "cell_id": f"solo:B:{severity}", "arm": "solo",
                "topic_id": f"fixture-topic-{index:03d}", "draw_index": draw,
                "topic_split": split, "scores": scores, "truncated": False,
                "word_count": 80})
    return rows


def test_the_one_pass_kappa_column_equals_the_per_candidate_reference():
    """``_kappa_columns`` is an optimisation of ``_kappa_under_b``, not a rule.

    Gate 2 builds the column for every admissible severity, so the
    per-candidate form it replaces is quadratic in the pool. The two must
    agree exactly, on every split, or the optimisation has changed §13.6's
    quantity.
    """
    rows = _b_solo_rows(9, rate_by_kind={"MK1": 0.30, "MK2": 0.75})
    columns = _kappa_columns(rows, CANDIDATES, severities=[9],
                             model_key=FIXTURE_MODEL)["9"]
    for split in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled"):
        restrict = None if split == "pooled" else split
        for candidate in CANDIDATES:
            value, n_topics, n_draws = _kappa_under_b(rows, candidate,
                                                      split=restrict)
            entry = columns[split][candidate.label]
            assert entry["kappa_under_b"] == pytest.approx(value, abs=1e-12)
            source = entry["kappa_under_b_source"]
            assert source["n_topics"] == n_topics
            assert source["n_draws"] == n_draws
            assert source["present"] == ["B:9"]
            assert source["m_star"] == 9


def test_a_table_reads_the_kappa_column_measured_at_its_own_severity():
    """§13.11's table at m* = 11, from a Gate 2 that selected m* = 9.

    The refusal this exercises is real and stays: reading Gate 2's m*-column
    under another m* must fail. Gate 2 records a column at every admissible
    severity, so a read at the wrong one is a refusal rather than a missing
    column --- which is what makes it a check and not an absence.
    """
    at_9 = _kappa_columns(_b_solo_rows(9, rate_by_kind={"MK1": 0.30,
                                                        "MK2": 0.75}),
                          CANDIDATES, severities=[9],
                          model_key=FIXTURE_MODEL)
    at_11 = _kappa_columns(_b_solo_rows(11, rate_by_kind={"MK1": 0.55,
                                                          "MK2": 0.20}),
                           CANDIDATES, severities=[11],
                           model_key=FIXTURE_MODEL)
    base_rows = []
    for candidate in CANDIDATES:
        entry = at_9["9"]["pooled"][candidate.label]
        base_rows.append({
            "kind": candidate.kind, "severity": candidate.severity,
            "split": "pooled", "model_key": FIXTURE_MODEL,
            "solo_compliance": 0.5, "chance_compliance": 0.01,
            "solo_vacuity": 0.0, "n_topics": 8, "n_draws": C.M_CAL,
            "per_topic_solo": [0.5] * 8,
            "kappa_under_b": entry["kappa_under_b"],
            "kappa_under_b_source": dict(entry["kappa_under_b_source"])})
    gate2 = {"m_star": 9, "calibration_rows": {"pooled": base_rows},
             "focal_admissible": [9, 11],
             "kappa_under_b_by_severity": {"9": at_9["9"], "11": at_11["11"]}}

    # Gate 2's own m*: the table comes back untouched and loads.
    same = calibration_rows_at(gate2, m_star=9, split="pooled")
    assert load_calibration_table(same, model_key=FIXTURE_MODEL, m_star=9,
                                  split="pooled")

    # The re-selected m*: the column is swapped and the table loads at 11.
    moved = calibration_rows_at(gate2, m_star=11, split="pooled")
    loaded = load_calibration_table(moved, model_key=FIXTURE_MODEL,
                                    m_star=11, split="pooled")
    assert [r.kappa_under_b_source.m_star for r in loaded] == [11, 11]
    assert [r.kappa_under_b for r in loaded] == [
        at_11["11"]["pooled"][c.label]["kappa_under_b"] for c in CANDIDATES]

    # And the guard that made the branch unexecutable still fires when the
    # table and the operating point genuinely disagree.
    with pytest.raises(ProtocolError) as excinfo:
        load_calibration_table(same, model_key=FIXTURE_MODEL, m_star=11,
                               split="pooled")
    assert "B:9" in str(excinfo.value)


def test_a_severity_gate_2_recorded_no_column_for_is_refused():
    """Falling back to Gate 2's column is the defect; absence must refuse."""
    gate2 = {"m_star": 9, "calibration_rows": {"pooled": []},
             "kappa_under_b_by_severity": {"9": {"pooled": {}}}}
    with pytest.raises(ProtocolError) as excinfo:
        calibration_rows_at(gate2, m_star=12, split="pooled")
    assert "focal_admissible" in str(excinfo.value)


def test_the_qualified_pool_is_read_at_the_operating_point():
    record = {"qualification_by_severity": {
        "9": {"m_star": 9, "qualified_pool": ["MK1:1"],
              "qualified_families": ["MK1"], "n_qualified": 1},
        "11": {"m_star": 11, "qualified_pool": ["MK1:1", "MK2:2"],
               "qualified_families": ["MK1", "MK2"], "n_qualified": 2}}}
    assert qualification_at(record, m_star=11)["n_qualified"] == 2
    assert qualification_at(record, m_star=9)["qualified_pool"] == ["MK1:1"]
    with pytest.raises(ProtocolError) as excinfo:
        qualification_at(record, m_star=12)
    assert "12" in str(excinfo.value)


def test_the_freeze_binds_b_at_the_probes_operating_point_not_gate_2s():
    """§18.1 binds one operating point and it is the one the study runs.

    Read off the source rather than off a run, because the run that would
    show it costs a full walk and lives in ``scenarios``. What is pinned here
    is that the default comes from the probe record: the field this replaces
    read ``gate2["m_star"]``, and confirmatory generation renders every cell
    from this slot map.
    """
    import inspect

    from dci1v6.run import freeze_run

    source = inspect.getsource(freeze_run.freeze_payload)
    assert 'slot_map.setdefault("B", ["B", int(probe["m_star"])])' in source
    assert 'gate2["m_star"]' not in source


def test_confirmatory_rebuilds_b_through_the_focal_constructor():
    """§7.2's extension survives the freeze -> confirmatory boundary.

    ``Constraint("B", 15)`` is refused by the instrument layer unless the
    caller states the extension, and the freeze stores a bare ``["B", m]``.
    A replication that escalated at §12.3 would have been refused by its own
    verifiers at the one stage that spends the confirmatory budget.
    """
    from dci1v6.run.confirmatory_run import licensed_design      # noqa: F401
    from dci1v6.run.gates_run import focal_constraint

    assert focal_constraint(15).extended is True
    assert focal_constraint(15).severity == 15
    with pytest.raises(ProtocolError):
        Constraint("B", 15)
