"""§13.11's chance column is §13.2's kappa_c (2026-08-29).

Regression tests for the defect `CHANGES_SCIENTIFIC.md` records on
2026-08-29: `gates_run._calibration_rows` obtained ``chance_compliance``
through `instance_rates`, whose solo scan finds no grid row that states a
non-outcome candidate, so the column was 0.0 for every candidate of every
replication of v5, v6 and v7. Each test here is one thing the correction has
to hold, and each would have failed on the previous implementation:

1. a non-zero chance is measured, on the unconstrained cells alone;
2. §13.4's ceiling excludes a candidate that exceeds it;
3. iota(R) is (solo - kappa)/(1 - kappa) on the corrected column;
4. a chance-free candidate's row and verdict are unchanged;
5. a qualification changes only where the corrected value requires it;
6. serial and pooled builders agree byte for byte on the corrected table;
7. a degenerate row is withheld, recorded, refused at the record seam, and
   still counted by §12.6's calibrated re-read (v6 A16).

The fixtures are `tests_v7/test_parallel.py`'s: pass-1 candidate solo cells,
and grid runs with an unconstrained cell whose verdict cycles so that each
topic's mean is exactly the rate asked for, beside B-solo cells that pass
every candidate on half the rows --- the value a denominator over every
absent verdict would have averaged in.
"""
from __future__ import annotations

import copy
import json

import pytest
from dci1v4.errors import ProtocolError
from dci1v7.engine import parallel
from dci1v7.protocol import constants as C
from dci1v7.run import gates_run
from dci1v7.stages import feasibility
from dci1v7.stages.calibration_table import (
    instructed_compliance,
    load_calibration_table,
)
from dci1v7.stages.qualification_gate import qualify_candidates

from tests_v7.test_parallel import (
    B_STAR,
    CANDIDATES,
    MODEL,
    _candidate_rows,
    _grid_rows,
)

CHANCE = {"MK1": 0.0, "MK2": 0.5, "MK6": 0.75}


def _tables(chance_by_kind=CHANCE, *, draws=4, grid_rows=None):
    solo_rows = _candidate_rows(draws=draws)
    grid = (_grid_rows(draws=draws, chance_by_kind=chance_by_kind)
            if grid_rows is None else grid_rows)
    b_solo = [r for r in grid if r["cell_id"] == f"solo:B:{B_STAR}"]
    return gates_run._calibration_rows(
        MODEL, CANDIDATES, m_star=B_STAR, solo_rows=solo_rows,
        chance_rows=grid, b_solo_rows=b_solo)


def _previous_semantics(tables):
    """What the previous implementation wrote: the same table with 0.0 in
    the chance column of every row."""
    old = copy.deepcopy(tables)
    for rows in old.values():
        for row in rows:
            row["chance_compliance"] = 0.0
    return old


def _qualified(table):
    rows = load_calibration_table(table, model_key=MODEL, m_star=B_STAR,
                                  split="pooled")
    return qualify_candidates(rows, model_key=MODEL, m_star=B_STAR)


def _verdict(qualification, label):
    return next(v for v in qualification["verdicts"]
                if v["candidate"] == label)


# ------------------------------------------------ 1. the measurement

def test_chance_is_measured_on_the_unconstrained_cells_alone():
    tables = _tables()
    for split, rows in tables.items():
        got = {r["kind"]: r["chance_compliance"] for r in rows}
        assert got == CHANCE, split
    # The B-solo cells pass every candidate on half the rows. A chance of
    # 0.75 for MK6 and 0.0 for MK1 on every split is possible only if those
    # rows were excluded from the denominator.
    assert all(r["chance_compliance"] != 0.5 for r in tables["pooled"]
               if r["kind"] != "MK2")


def test_a_split_with_no_unconstrained_cell_is_refused():
    grid = [r for r in _grid_rows(chance_by_kind=CHANCE)
            if not (r["arm"] == "unconstrained"
                    and r["topic_split"] == C.CALIBRATION_B)]
    with pytest.raises(ProtocolError, match="no unconstrained cell"):
        _tables(grid_rows=grid)


def test_a_chance_measured_on_another_topic_set_is_refused():
    grid = [r for r in _grid_rows(chance_by_kind=CHANCE)
            if not (r["arm"] == "unconstrained"
                    and r["topic_id"] == "fixture-topic-000")]
    with pytest.raises(ProtocolError, match="same topic set"):
        _tables(grid_rows=grid)


def test_the_gate2_record_names_the_basis():
    grid = _grid_rows(chance_by_kind=CHANCE)
    basis = gates_run._chance_basis(grid)
    assert basis["cell"] == "unconstrained"
    assert basis["per_split"]["pooled"] == {
        "n_topics": 12, "n_rows": 48, "draws_per_topic": 4.0}
    assert basis["per_split"][C.CALIBRATION_A]["n_topics"] == 6


# ------------------------------------------------- 2. the ceiling

def test_the_chance_ceiling_excludes_a_candidate_above_it():
    """A candidate at kappa = 0.875 fails V_chance on the corrected table and
    passed it, trivially, on the previous one."""
    rates = {"MK1": 0.0, "MK2": 0.5, "MK6": 0.875}
    tables = _tables(rates, draws=8)
    assert _verdict_row(tables, "MK6")["chance_compliance"] == 0.875
    now = _qualified(tables["pooled"])
    before = _qualified(_previous_semantics(tables)["pooled"])
    chance_now = _component(_verdict(now, "MK6:3"), "V_chance")
    chance_before = _component(_verdict(before, "MK6:3"), "V_chance")
    assert chance_now["passed"] is False
    assert f"above {C.CHANCE_MAX}" in chance_now["reason"]
    assert chance_before["passed"] is True
    assert "MK6:3" not in now["qualified_pool"]
    # The lift floor fires on the same values (H = solo - kappa), which is
    # why a candidate above the ceiling is rejected on §13.4 twice over.
    head_now = _component(_verdict(now, "MK6:3"), "V_head")
    assert head_now["passed"] is False and "lift" in head_now["reason"]


def _verdict_row(tables, kind):
    return next(r for r in tables["pooled"] if r["kind"] == kind)


def _component(verdict, name):
    return next(c for c in verdict["components"] if c["component"] == name)


# ----------------------------------------------- 3. the coordinate

def test_iota_uses_the_registered_formula_on_the_corrected_column():
    tables = _tables()
    rows = load_calibration_table(tables["pooled"], model_key=MODEL,
                                  m_star=B_STAR, split="pooled")
    for row in rows:
        kappa = CHANCE[row.kind]
        assert row.chance_compliance == kappa
        assert row.iota == (row.solo_compliance - kappa) / (1.0 - kappa)
        assert row.iota == instructed_compliance(row.solo_compliance, kappa)
        assert row.lift == row.solo_compliance - kappa
        if kappa > 0 and row.solo_compliance < 1.0:
            assert row.iota != row.solo_compliance


# ------------------------------------------- 4. chance-free unchanged

def test_a_chance_free_candidate_is_unchanged_in_every_column_and_verdict():
    tables = _tables()
    before = _previous_semantics(tables)
    for split in tables:
        now = next(r for r in tables[split] if r["kind"] == "MK1")
        old = next(r for r in before[split] if r["kind"] == "MK1")
        assert now == old
    assert _verdict(_qualified(tables["pooled"]), "MK1:1") == \
        _verdict(_qualified(before["pooled"]), "MK1:1")


# --------------------------------------- 5. changes only where required

def test_qualification_changes_only_where_the_corrected_value_requires_it():
    tables = _tables({"MK1": 0.0, "MK2": 0.0, "MK6": 0.5})
    now = _qualified(tables["pooled"])
    before = _qualified(_previous_semantics(tables)["pooled"])
    for label in ("MK1:1", "MK2:2"):
        assert _verdict(now, label) == _verdict(before, label)
    changed = _verdict(now, "MK6:3")
    unchanged = _verdict(before, "MK6:3")
    assert changed != unchanged
    assert changed["chance_compliance"] == 0.5 and \
        unchanged["chance_compliance"] == 0.0
    # Every other column of the row is the same.
    for key in ("solo_compliance", "kappa_under_b", "family", "severity"):
        assert changed[key] == unchanged[key]
    # And what moved is exactly the chance-derived quantities.
    assert changed["iota"] == pytest.approx(
        (changed["solo_compliance"] - 0.5) / 0.5)
    assert changed["instruction_lift"] == pytest.approx(
        changed["solo_compliance"] - 0.5)
    assert changed["displacement"] == pytest.approx(
        changed["kappa_under_b"] - 0.5)


# ------------------------------------------- 6. serial == pooled

def test_serial_and_pooled_builders_agree_on_the_corrected_table(monkeypatch):
    rates = {"MK1": 0.0, "MK2": 1.0, "MK6": 0.75}
    solo_rows = _candidate_rows()
    grid = _grid_rows(chance_by_kind=rates)
    b_solo = [r for r in grid if r["cell_id"] == f"solo:B:{B_STAR}"]
    monkeypatch.setattr(parallel, "MIN_ITEMS_FOR_A_POOL", 2)
    built = {}
    for workers in (1, 3):
        monkeypatch.setenv("DCI1_V7_CPU_WORKERS", str(workers))
        tables = gates_run._calibration_rows(
            MODEL, CANDIDATES, m_star=B_STAR, solo_rows=solo_rows,
            chance_rows=grid, b_solo_rows=b_solo)
        kept, withheld = gates_run._withhold_degenerate(tables)
        built[workers] = json.dumps([tables, kept, withheld], sort_keys=True)
    assert built[1] == built[3]
    assert '"chance_compliance": 1.0' in built[1]


# ------------------------------------------ 7. the degenerate row

def test_a_degenerate_row_is_withheld_recorded_and_refused_at_the_seam():
    tables = _tables({"MK1": 0.0, "MK2": 1.0, "MK6": 0.5})
    kept, withheld = gates_run._withhold_degenerate(tables)
    for split in tables:
        assert [r["kind"] for r in kept[split]] == ["MK1", "MK6"]
        assert [r["kind"] for r in withheld[split]] == ["MK2"]
        row = withheld[split][0]
        assert row["status"] == "DIFFICULTY_COORDINATE_DEGENERATE"
        assert row["chance_compliance"] == 1.0
        assert set(row["fails_registered_admission_on"]) == {"V_head",
                                                              "V_chance"}
        # Every measured value travels with it.
        for key in ("solo_compliance", "kappa_under_b", "per_topic_solo",
                    "solo_vacuity"):
            assert key in row
    # A withheld row cannot be loaded back through §13.11's closed schema.
    with pytest.raises(ProtocolError, match="unknown calibration fields"):
        load_calibration_table(withheld["pooled"], model_key=MODEL,
                               m_star=B_STAR, split="pooled")
    # The record seam refuses a table that carries one and reads the kept
    # table whole.
    with pytest.raises(ProtocolError, match="MK2:2"):
        feasibility.calibration_rows_at(
            {"m_star": B_STAR, "calibration_rows": tables},
            m_star=B_STAR, split="pooled")
    assert len(feasibility.calibration_rows_at(
        {"m_star": B_STAR, "calibration_rows": kept},
        m_star=B_STAR, split="pooled")) == 2
    # And every §13 reader downstream sees only rows with a coordinate.
    qualified = _qualified(kept["pooled"])
    assert {v["candidate"] for v in qualified["verdicts"]} == {"MK1:1",
                                                               "MK6:3"}


def test_withholding_is_per_table():
    """Degenerate on Calibration-A only: withheld there, kept on B and on
    the pooled table where its coordinate exists."""
    grid = _grid_rows(chance_by_kind={"MK1": 0.0, "MK2": 0.5, "MK6": 0.5})
    for row in grid:
        if row["arm"] == "unconstrained" and \
                row["topic_split"] == C.CALIBRATION_A:
            for score in row["scores"]:
                if score["kind"] == "MK2":
                    score["passed"] = True
                    score["graded"] = 1.0
    tables = _tables(grid_rows=grid)
    kept, withheld = gates_run._withhold_degenerate(tables)
    assert [r["kind"] for r in withheld[C.CALIBRATION_A]] == ["MK2"]
    assert withheld[C.CALIBRATION_B] == [] and withheld["pooled"] == []
    pooled_mk2 = next(r for r in kept["pooled"] if r["kind"] == "MK2")
    assert pooled_mk2["chance_compliance"] == 0.75


def test_the_calibrated_coverage_re_read_still_counts_a_withheld_row(
        harness_decisions):
    """v6 A16 on the calibrated basis: the row is dropped from every
    condition and recorded under `coordinate_undefined`."""
    tables = _tables({"MK1": 0.0, "MK2": 1.0, "MK6": 0.5})
    kept, withheld = gates_run._withhold_degenerate(tables)
    gate2 = {"iota_a": 0.5, "calibration_rows": kept,
             "calibration_rows_withheld": withheld}
    regime = {"coverage_eligibility_formulation": "E2",
              "iota_a_prescreen": None, "expansion": {}}
    out = feasibility.coverage_at_calibrated_iota_a(
        gate2_record=gate2, regime_record=regime)
    assert out["n_withheld_degenerate"] == 1
    assert out["n_rows"] == 3
    undefined = out["coordinate_undefined"]
    assert out["n_coordinate_undefined"] == 1
    assert [r["candidate"] for r in undefined] == ["MK2:2"]
    assert undefined[0]["status"] == "DIFFICULTY_COORDINATE_DEGENERATE"
    # Without the withheld block --- a record from before this change ---
    # the reading is the same on every condition and simply does not see it.
    older = feasibility.coverage_at_calibrated_iota_a(
        gate2_record={"iota_a": 0.5, "calibration_rows": kept},
        regime_record=regime)
    assert older["conditions"] == out["conditions"]
    assert older["n_withheld_degenerate"] == 0


def test_the_revision_change_is_registered_and_checked():
    from dci1v7.protocol import revision

    by_id = {c.id: c for c in revision.CHANGES}
    assert "§13.11" in by_id["V14"].section
    assert by_id["V14"].check()
    # V9 still holds: the §13 modules that read the column are untouched.
    assert by_id["V9"].check()
