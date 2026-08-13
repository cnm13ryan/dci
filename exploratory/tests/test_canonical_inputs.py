"""A missing canonical input must stop the run, never degrade it.

Defect: `load_all_reasoning` preferred the re-seeded capped grid "when it
exists" and otherwise fell back to `s18_reasoning.jsonl`. That file was
deprecated because all 160 requests shared one seed, making replicate pairs
byte-identical — 390/400 pairs in the real file carry the same answer twice, so
two draws count once. `runs/` is gitignored, so a regenerated or partially
transferred run directory can easily hold the deprecated file without the
re-seeded one, at which point the fallback published two sampling regimes as a
single canonical curve.

Classification: canonical-data/provenance failure, plus replicate-independence
failure in the data it silently admits.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXPLORATORY))

from dci_exploratory import plotdata  # noqa: E402
from tests import gridfixtures  # noqa: E402


def test_missing_reseeded_grid_refuses_to_load(tmp_path: Path) -> None:
    gridfixtures.write_grid(tmp_path / "s18_reasoning.jsonl", shared_seed=True)
    gridfixtures.write_grid(tmp_path / "natural_reasoning.jsonl", shared_seed=False)
    # s18_reseeded.jsonl is deliberately absent.
    with pytest.raises(FileNotFoundError, match="s18_reseeded"):
        plotdata.load_all_reasoning(tmp_path)


def test_present_reseeded_grid_is_used(tmp_path: Path) -> None:
    gridfixtures.write_grid(tmp_path / "s18_reseeded.jsonl", shared_seed=False)
    gridfixtures.write_grid(tmp_path / "s18_reasoning.jsonl", shared_seed=True)
    gridfixtures.write_grid(tmp_path / "natural_reasoning.jsonl", shared_seed=False)
    frame = plotdata.load_all_reasoning(tmp_path)
    assert set(frame["capped_source"].dropna()) == {"s18_reseeded.jsonl"}


def test_deprecated_grid_is_never_the_capped_source(tmp_path: Path) -> None:
    """Even with both files present, the shared-seed file must not be read."""
    gridfixtures.write_grid(tmp_path / "s18_reseeded.jsonl", shared_seed=False)
    gridfixtures.write_grid(tmp_path / "s18_reasoning.jsonl", shared_seed=True)
    gridfixtures.write_grid(tmp_path / "natural_reasoning.jsonl", shared_seed=False)
    frame = plotdata.load_all_reasoning(tmp_path)
    assert "s18_reasoning.jsonl" not in set(frame["capped_source"].dropna())


def test_deprecated_grid_really_is_replicate_degenerate(tmp_path: Path) -> None:
    """The reason the fallback is refused, asserted rather than assumed."""
    path = tmp_path / "s18_reasoning.jsonl"
    gridfixtures.write_grid(path, shared_seed=True)
    frame = plotdata.load_reasoning(path)
    groups = frame.groupby(["task_id", "arm", "variant", "reasoning_budget"])
    identical = sum(1 for _, g in groups if g["final_answer"].nunique() == 1)
    assert identical == groups.ngroups, (
        "fixture no longer reproduces the shared-seed defect it guards against")
