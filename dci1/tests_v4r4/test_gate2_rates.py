"""§12.3's difficulty coordinates, and the contract that had never been run.

`run_gate2` and `calibration_table` asked `cell_rates` for a
``{"solo", "chance", "vacuity"}`` mapping it has never returned, and omitted
its required keyword-only ``present``. Both raised on the first call. Neither
had ever executed: v4r2 stopped at Gate 2 under a different codebase and v4r3
stopped at Gate 1, so nothing in the study had reached the line.

`run/regime_screen.difficulty_table_from_rows` *has* run --- it produced the
§12.2 table that Gate 1's provenance and §12.6's coverage read --- so it is the
certified reading of solo and chance. `instance_rates` reproduces it, and these
tests hold the two together: if either changes, one definition of difficulty
would silently become two.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v4r4.run.execute import cell_rates, instance_rates
from dci1v4r4.run.regime_screen import difficulty_table_from_rows

#: (topic, present, passed, vacuous, graded, words, truncated) per row.
#: Deliberately unbalanced across topics: the topic is the averaging unit, so a
#: mean over rows and a mean over topics differ here, and a helper that
#: flattened them would fail.
CASES = [
    ("t1", True, True, False, 1.0, 100, False),
    ("t1", True, False, False, 0.4, 90, False),
    ("t1", True, True, True, 0.9, 80, False),
    ("t2", True, False, False, 0.2, 120, True),
    ("t3", True, True, False, 0.8, 110, False),
    ("t1", False, False, False, 0.1, 70, False),
    ("t2", False, True, True, 0.5, 95, False),
    ("t3", False, False, False, 0.0, 60, False),
]


def _rows(kind="RF1", severity=4):
    rows = []
    for index, (topic, present, passed, vacuous, graded, words, trunc) in \
            enumerate(CASES):
        rows.append({
            "row_id": f"r{index}", "topic_id": topic,
            "word_count": float(words), "truncated": trunc,
            "scores": [{"kind": kind, "severity": severity,
                        "present": present, "passed": passed,
                        "vacuous_pass": vacuous, "graded": graded}],
        })
    return rows


def test_instance_rates_reproduces_the_certified_difficulty_table():
    rows = _rows()
    measured = instance_rates(rows, kind="RF1", severity=4)
    certified = difficulty_table_from_rows(rows, [("RF1", 4)])["RF1:4"]
    for key in ("solo", "chance", "graded_mean", "median_words", "truncation",
                "n_topics"):
        assert measured[key] == certified[key], key
    assert measured["vacuity"] == certified["solo_vacuity"]
    assert measured["chance_vacuity"] == certified["chance_vacuity"]


def test_the_two_arms_are_the_present_and_absent_cells_and_not_each_other():
    rows = _rows()
    measured = instance_rates(rows, kind="RF1", severity=4)
    assert measured["solo"] == cell_rates(rows, kind="RF1", severity=4,
                                          present=True)["compliance"]
    assert measured["chance"] == cell_rates(rows, kind="RF1", severity=4,
                                            present=False)["compliance"]
    assert measured["solo"] != measured["chance"]


def test_the_topic_is_the_averaging_unit():
    """t1 carries three solo rows and t2 and t3 one each."""
    measured = instance_rates(_rows(), kind="RF1", severity=4)
    assert measured["n_topics"] == 3
    # t1 = 2/3, t2 = 0, t3 = 1  ->  5/9, not the 3/5 a row-mean would give.
    assert measured["solo"] == pytest.approx(5 / 9)
    assert measured["solo"] != pytest.approx(3 / 5)


def test_a_missing_arm_fails_closed_rather_than_reading_zero():
    """No load-0 row for this instance is a refusal, not a chance of 0."""
    rows = [row for row in _rows()
            if row["scores"][0]["present"]]
    with pytest.raises(ProtocolError):
        instance_rates(rows, kind="RF1", severity=4)


def test_instance_rates_accepts_a_sequence_it_must_scan_twice():
    """It reads the present and absent cells in turn; a generator would
    silently give the second read nothing."""
    measured = instance_rates(iter(_rows()), kind="RF1", severity=4)
    assert measured["chance"] > 0.0


def test_gate_2_asks_only_for_keys_this_helper_returns():
    """The defect in one line: the call sites read a contract that was not
    there, and nothing had ever executed to say so."""
    import ast
    import inspect

    from dci1v4r4.run import gates_run

    returned = set(instance_rates(_rows(), kind="RF1", severity=4))
    source = inspect.getsource(gates_run)
    read: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "instance_rates"
                and isinstance(node.slice, ast.Constant)):
            read.add(node.slice.value)
    assert read, "no instance_rates subscript found; the scan is stale"
    assert read <= returned, f"gates_run reads keys that do not exist: " \
                             f"{sorted(read - returned)}"


# ------------------------------------------- §7.2's escalation, as §12.3 runs it
def test_the_extension_design_matches_what_a_widened_design_would_build():
    """The 768 extension rows must have the identity they would have had
    inside `calibration_cells`, or the union is measured on a different
    instrument than the registered pass."""
    from dci1v4r4.run.gates_run import calibration_cells, focal_extension_cells
    from dci1v4r4.topics import split_topics
    from dci1v4r4.verifiers.constraints import FOCAL_EXTENSION

    topics = split_topics()["solo"]
    shortlist = {"RF1": (3,)}
    widened = {c.cell_id: c for c in
               calibration_cells(topics, shortlist, focal_extension=True)}
    registered = {c.cell_id for c in
                  calibration_cells(topics, shortlist, focal_extension=False)}
    extension = focal_extension_cells(topics)

    assert len(extension) == len(topics) * len(FOCAL_EXTENSION)
    assert {c.cell_id for c in extension} == set(widened) - registered
    for cell in extension:
        twin = widened[cell.cell_id]
        assert cell.prompt == twin.prompt          # same wording index
        assert cell.prompt_hash == twin.prompt_hash
        assert cell.arm == twin.arm
        assert cell.wording_indices == twin.wording_indices


def test_the_extension_carries_only_the_two_rungs_selection_may_use():
    """`select_focal_severity` refuses an extended curve holding a registered
    rung, so building it over all six would raise instead of escalating."""
    from dci1v4r4.stages.gates import select_focal_severity
    from dci1v4r4.verifiers.constraints import FOCAL_GRID, focal_severities

    exhausted = {m: 0.10 for m in FOCAL_GRID}
    assert select_focal_severity(exhausted)["m_star"] is None
    assert select_focal_severity(exhausted)["extension_required"] is True

    with pytest.raises(ProtocolError):
        select_focal_severity(exhausted,
                              {m: 0.8 for m in focal_severities(extended=True)})
    chosen = select_focal_severity(exhausted, {11: 0.70, 12: 0.90})
    assert chosen["m_star"] == 11
    assert chosen["extension_measured"] is True


def test_the_escalation_is_decided_by_gate_2_and_not_read_from_the_regime():
    """The regime record has never carried this flag: three readers, no
    producer. A replication whose registered grid was exhausted could only
    return PENDING_FOCAL_EXTENSION for ever."""
    import inspect

    from dci1v4r4.run import gates_run

    source = inspect.getsource(gates_run.run_gate2)
    assert 'regime_record.get("focal_extension_measured")' not in source
    assert "select_focal_severity(registered)" in source


def test_the_freeze_reads_the_escalation_from_the_record_that_decides_it():
    import inspect

    from dci1v4r4.run import freeze_run
    from dci1v4r4.stages.freeze import NEW_IN_V4R3

    assert "focal_extension_measured" in NEW_IN_V4R3
    source = inspect.getsource(freeze_run)
    assert 'gate2.get("focal", {}).get("extension_measured", False)' in source
    assert 'regime.get("focal_extension_measured"' not in source


# ---------------------------------------------- §8.6's variant, and the mask
def _selection(n_core: int, n_spectrum: int):
    from dci1v4r4.stages.selection import SelectionResult
    return SelectionResult(
        core={"design": "full" if n_core >= 3 else "reduced",
              "identification_statuses": [],
              "core_references": [{"slot": f"R{i}", "family": "RF1",
                                   "severity": i} for i in range(n_core)]},
        spectrum=[{"slot": f"S{i}", "family": "RF1", "severity": i}
                  for i in range(n_spectrum)],
        klass={})


def test_the_variant_never_contradicts_the_design_it_refines():
    """`design` is full/reduced and the variant refines it into three. A
    'full' design reported as a 'reduced' variant is the defect's signature."""
    from dci1v4r4.run.gates_run import design_variant_for

    for n_core, n_spectrum in ((0, 0), (2, 3), (3, 0), (3, 6), (4, 6)):
        result = _selection(n_core, n_spectrum)
        variant = design_variant_for(result)
        if result.design == "full":
            assert variant in ("full", "no_spectrum"), (n_core, n_spectrum)
        else:
            assert variant == "reduced", (n_core, n_spectrum)


def test_the_variant_helper_raises_rather_than_defaulting_on_a_rename():
    """The whole defect class in one assertion: no silent default.

    Checked over the body rather than the source, because the docstring names
    the call it replaced and would otherwise match itself.
    """
    import ast
    import inspect
    import textwrap

    from dci1v4r4.run import gates_run

    body = ast.parse(textwrap.dedent(
        inspect.getsource(gates_run.design_variant_for))).body[0]
    calls = [node.func.id for node in ast.walk(body)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert "getattr" not in calls
