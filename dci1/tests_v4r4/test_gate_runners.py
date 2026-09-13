"""Gate 2 and Gate 3 read solo cells, and the design variant is not an outcome.

Two things worth having on the execution path rather than in prose:

* §12.5 and §13.9 forbid a composed outcome reaching regime selection or
  reference selection. Here that is structural --- `calibration_cells` has no
  branch that builds a composed cell --- and the test parses the module to say
  so, because an assertion on generated cells only covers the arguments it was
  given;
* the §8.6 design variant is decided by reference admission and §12.6 coverage.
  Choosing between the full and no-spectrum designs from a composed effect
  would be selecting the analysis after seeing the answer.
"""
from __future__ import annotations

import ast
from pathlib import Path

from dci1v4r4.protocol import constants as C
from dci1v4r4.run import gates_run
from dci1v4r4.stages.selection import SelectionResult
from dci1v4r4.topics import split_topics

SRC = Path(__file__).resolve().parents[1] / "src" / "dci1v4r4"
SHORTLIST = {"RF1": [3, 4, 5], "CR3": [2, 4], "CL7": [30]}


def test_the_calibration_set_is_load_zero_and_load_one_only():
    topics = split_topics()["solo"][:4]
    cells = gates_run.calibration_cells(topics, SHORTLIST,
                                        focal_extension=False)
    assert {c.load for c in cells} == {0, 1}
    assert all("+" not in c.cell_id for c in cells)


def test_the_calibration_builder_cannot_construct_a_composed_cell():
    """Structural. The word does not appear in the module at all."""
    source = (SRC / "run" / "gates_run.py").read_text()
    tree = ast.parse(source)
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "composed_cell" not in called
    imported = {a.name for n in ast.walk(tree)
                if isinstance(n, ast.ImportFrom) for a in n.names}
    assert "composed_cell" not in imported


def test_the_calibration_set_covers_every_shortlisted_rung():
    topics = split_topics()["solo"][:1]
    cells = gates_run.calibration_cells(topics, SHORTLIST,
                                        focal_extension=False)
    labels = {c.present[0].label for c in cells if c.load == 1}
    for family, rungs in SHORTLIST.items():
        for q in rungs:
            assert f"{family}:{q}" in labels


def test_the_registered_calibration_size_is_the_ninety_six_topic_split():
    assert len(split_topics()["solo"]) == C.N_SOLO == 96
    assert C.M_CAL == 4


# ------------------------------------------------------- the design variant

def _selection(references: tuple, spectrum: tuple) -> SelectionResult:
    """The real Gate-3 result object, not a stand-in.

    These three tests used to build a `FakeSelection` dataclass carrying
    `core_references` as a plain attribute. `SelectionResult` has no such
    attribute --- the admitted references live at `core["core_references"]` ---
    so the fixture matched the `getattr(result, "core_references", ())` the
    production code was making, the default fired on every real call, and
    every replication was assigned the reduced design whatever Gate 3 had
    selected. The fixture had encoded the defect as the expected behaviour,
    and the tests could not have caught it. They use the certified object now.
    """
    return SelectionResult(
        core={"design": "full" if len(references) >= C.N_CORE_REFERENCES
              else "reduced",
              "identification_statuses": [],
              "core_references": [{"slot": slot, "family": "RF1",
                                   "severity": index}
                                  for index, slot in enumerate(references)]},
        spectrum=[{"slot": slot, "family": "RF1", "severity": index}
                  for index, slot in enumerate(spectrum)],
        klass={})


def test_three_references_and_a_spectrum_give_the_full_design():
    result = _selection(("R1", "R2", "R3"),
                        ("R1-", "R1+", "R2-", "R2+", "R3-", "R3+"))
    assert gates_run.design_variant_for(result) == "full"


def test_a_coverage_failure_keeps_the_core_matrix():
    """`Delta_R`, `Xi`, `Lambda` and the reciprocal matrix stay identified;
    only `delta_difficulty` does not."""
    result = _selection(("R1", "R2", "R3"), ())
    assert gates_run.design_variant_for(result) == "no_spectrum"


def test_fewer_than_three_references_gives_the_reduced_design():
    result = _selection(("R1", "R2"), ())
    assert gates_run.design_variant_for(result) == "reduced"


def test_the_variant_rule_reads_nothing_that_could_be_an_outcome():
    """The whole decision is a function of two fields, neither of them a
    composed quantity."""
    source = ast.parse((SRC / "run" / "gates_run.py").read_text())
    func = next(n for n in ast.walk(source)
                if isinstance(n, ast.FunctionDef)
                and n.name == "design_variant_for")
    # Attribute accesses, plus the constant of any subscript --- the admitted
    # references are reached as `result.core["core_references"]`, so a scan
    # that collected attributes alone would miss the field that matters. The
    # docstring is prose and says "composed" on purpose, so collecting every
    # string constant would test the comment instead of the code.
    read = {n.attr for n in ast.walk(func) if isinstance(n, ast.Attribute)}
    read |= {n.slice.value for n in ast.walk(func)
             if isinstance(n, ast.Subscript)
             and isinstance(n.slice, ast.Constant)
             and isinstance(n.slice.value, str)}
    assert "core_references" in read and "spectrum" in read
    for forbidden in ("b_with", "composed", "delta", "interference", "loss"):
        assert not any(forbidden in field for field in read), (forbidden, read)
