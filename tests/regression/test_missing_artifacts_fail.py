"""A gate record present on one side and missing on the other is a regression.

compare_runs skipped every GATE_JSONS entry unless BOTH sides had it. A run that
stopped early, or lost a gate record, therefore compared clean against a fixture
that has it - and the suite reported zero problems for a comparison that never
happened. The CSV and score loops already treated one-sided presence as a
problem; only the JSON loop did not.
"""
import json
import shutil
from pathlib import Path

import pytest

from tests.regression.compare import GATE_JSONS, compare_runs

pytestmark = pytest.mark.cpu

GATE = "gate_0_implementation.json"
PAYLOAD = {"gate": "0_implementation", "status": "PASS",
           "dry_run_bypassed": False, "quantities": {"checks": 114}}


@pytest.fixture
def pair(tmp_path):
    """Two identical minimal run trees."""
    for side in ("fixture", "run"):
        gates = tmp_path / side / "gates"
        gates.mkdir(parents=True)
        (gates / GATE).write_text(json.dumps(PAYLOAD))
    return tmp_path / "fixture", tmp_path / "run"


def test_identical_trees_compare_clean(pair):
    problems, compared = compare_runs(*pair)
    assert problems == []
    assert f"gates/{GATE}" in compared


def test_deleting_the_gate_from_the_run_is_a_problem(pair):
    fixture, run = pair
    (run / "gates" / GATE).unlink()
    problems, compared = compare_runs(fixture, run)
    assert problems, "a missing gate record must be reported"
    assert any(GATE in p for p in problems), problems
    assert f"gates/{GATE}" not in compared


def test_deleting_the_gate_from_the_fixture_is_also_a_problem(pair):
    fixture, run = pair
    (fixture / "gates" / GATE).unlink()
    problems, _ = compare_runs(fixture, run)
    assert any(GATE in p and "run" in p for p in problems), problems


def test_absent_on_both_sides_remains_acceptable(pair):
    """GATE_JSONS spans gates a legitimately shorter profile never reaches."""
    fixture, run = pair
    for side in (fixture, run):
        (side / "gates" / GATE).unlink()
    problems, compared = compare_runs(fixture, run)
    assert problems == []
    assert compared == []


@pytest.mark.parametrize("name", GATE_JSONS)
def test_every_declared_gate_json_is_checked_both_ways(pair, name):
    """The guard covers the whole list, not just the one gate above."""
    fixture, run = pair
    (fixture / "gates" / name).write_text(json.dumps(PAYLOAD))
    (run / "gates" / name).write_text(json.dumps(PAYLOAD))
    assert compare_runs(fixture, run)[0] == []
    (run / "gates" / name).unlink()
    assert any(name in p for p in compare_runs(fixture, run)[0])


def test_a_differing_gate_record_is_still_reported(pair):
    fixture, run = pair
    (run / "gates" / GATE).write_text(
        json.dumps({**PAYLOAD, "status": "NOT_IDENTIFIED_SUPPORT"}))
    assert compare_runs(fixture, run)[0]
