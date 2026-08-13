"""A failed guard must leave the previous canonical artifacts untouched.

Defect: `guard()` only appended to `_FAILURES`, and `main()` consulted that list
in its final line — after every canonical CSV had already been written. A run
whose data failed a hard guard (duplicate replicates, a ceiling hit, a mismatched
model revision) therefore exited nonzero but had already overwritten the
canonical outputs the figure scripts read. The nonzero status is only seen by an
operator; the corrupted CSV is seen by every downstream script.

Classification: validity-gate failure. The gate existed and computed the right
verdict, but it was advisory at the point where it needed to be blocking.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXPLORATORY))

from tests import gridfixtures  # noqa: E402

CANONICAL_OUTPUTS = (
    "natural_question1_interference.csv",
    "natural_question2_reasoning_use.csv",
    "natural_question3_outcomes.csv",
    "natural_task_heterogeneity.csv",
    "natural_leave_one_task_out.csv",
    "natural_long_trace_sensitivity.csv",
    "natural_leakage_audit.csv",
    "canonical_capped_and_natural_curve.csv",
)


@pytest.fixture()
def analysis(monkeypatch, tmp_path):
    """natural_analysis with a stubbed loader and an isolated output dir."""
    import natural_analysis

    out = tmp_path / "data"
    out.mkdir()
    monkeypatch.setattr(natural_analysis, "OUT", out)
    monkeypatch.setattr(natural_analysis, "_FAILURES", [])

    frame = gridfixtures.natural_frame()
    monkeypatch.setattr(natural_analysis, "load_canonical",
                        lambda _run: (frame, frame))
    # `main()` resolves the run directory before it loads anything, and that
    # directory lives under the gitignored `runs/`. Stubbing only the loader
    # left the test depending on whichever raw data happened to be on the
    # machine: it passed in the worktree that still held the S18 run and failed
    # everywhere else, including in any fresh clone. The lookup is stubbed too,
    # so what the test asserts is guard ORDERING and nothing else.
    from dci_exploratory import plotdata
    monkeypatch.setattr(plotdata, "latest", lambda _pattern: tmp_path)
    return natural_analysis, out


def test_failed_guard_writes_nothing(analysis, monkeypatch) -> None:
    natural_analysis, out = analysis
    sentinel = out / CANONICAL_OUTPUTS[0]
    sentinel.write_text("PREVIOUS,CANONICAL,CONTENT\n")
    monkeypatch.setattr(natural_analysis, "_FAILURES", ["synthetic guard"])

    status = natural_analysis.main()

    assert status != 0, "a failed guard must produce a nonzero exit status"
    assert sentinel.read_text() == "PREVIOUS,CANONICAL,CONTENT\n", (
        "canonical artifact was overwritten despite a failed guard")


def test_failed_guard_creates_no_new_files(analysis, monkeypatch) -> None:
    natural_analysis, out = analysis
    monkeypatch.setattr(natural_analysis, "_FAILURES", ["synthetic guard"])

    status = natural_analysis.main()

    assert status != 0
    assert list(out.iterdir()) == [], (
        f"a failed guard still created {[p.name for p in out.iterdir()]}")


def test_passing_guards_write_every_canonical_output(analysis) -> None:
    """The gate must not be so eager that a clean run produces nothing."""
    natural_analysis, out = analysis

    status = natural_analysis.main()

    assert status == 0
    written = {p.name for p in out.iterdir()}
    assert set(CANONICAL_OUTPUTS) <= written, (
        f"clean run missing {set(CANONICAL_OUTPUTS) - written}")
