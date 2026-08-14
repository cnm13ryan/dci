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

import ast
import sys
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXPLORATORY))

from dci_exploratory import plotdata  # noqa: E402
from tests import gridfixtures  # noqa: E402


def test_the_raw_loader_itself_refuses_non_admissible_evidence(tmp_path: Path) -> None:
    """The guard sits on `load_reasoning`, not only on the wrapper above it.

    Second defect, found after the first was fixed: `load_all_reasoning` refused
    the shared-seed grid, but `make_figures.py` never called it — it called
    `load_reasoning` on `s18_reasoning.jsonl` directly and concatenated the
    Round 10 `s18_transition.jsonl` budgets. So the tested invariant and the
    production figure path disagreed, and the committed row-level export came
    from the unguarded one. A guard beside the path is not a guard.
    """
    for name in ("s18_reasoning.jsonl", "s18_transition.jsonl",
                 "s18_reasoning.scored.jsonl"):
        path = tmp_path / name
        gridfixtures.write_grid(path, shared_seed=True)
        with pytest.raises(plotdata.NonAdmissibleEvidence, match=name):
            plotdata.load_reasoning(path)


def test_the_admissible_grid_still_loads(tmp_path: Path) -> None:
    path = tmp_path / "s18_reseeded.jsonl"
    gridfixtures.write_grid(path, shared_seed=False)
    assert len(plotdata.load_reasoning(path)) == 16


def test_demonstrating_the_defect_needs_an_explicit_opt_in(tmp_path: Path) -> None:
    """The escape hatch exists only so the deprecation can be evidenced."""
    path = tmp_path / "s18_reasoning.jsonl"
    gridfixtures.write_grid(path, shared_seed=True)
    frame = plotdata.load_reasoning(path, allow_non_admissible=True)
    assert len(frame) == 16


def test_the_figure_builder_uses_the_guarded_loader() -> None:
    """`make_figures.build` must route through `load_all_reasoning`.

    Asserted against the source because `build()` needs a real run directory to
    execute, and `runs/` is gitignored — so the property that actually regressed
    (which loader the production path calls) would otherwise be untested here.
    """
    source = (Path(__file__).resolve().parents[1] / "make_figures.py").read_text()
    build = source[source.index("def build("):]
    build = build[:build.index("\n# =====")]
    # Comments are stripped: the block explains which files it no longer reads,
    # and naming them in prose must not read as reading them.
    code = "\n".join(line for line in build.splitlines()
                     if not line.lstrip().startswith("#"))
    assert "load_all_reasoning(run)" in code
    for bypass in ("s18_reasoning.jsonl", "s18_transition.jsonl"):
        assert bypass not in code, (
            f"make_figures.build reaches past the guard to {bypass}")


def test_no_production_script_names_a_non_admissible_generation_file() -> None:
    """Generalises the check above to every script, not just `make_figures`.

    The narrow version missed `round10_analysis.py`, which carried the identical
    bypass — it loaded `s18_reasoning.jsonl` and appended `s18_transition.jsonl`
    onto one curve. A guard that is only asserted at the one call site someone
    remembered is how the second call site survives.

    The check is on USE, not mention: `natural_analysis.py` names the deprecated
    grid in order to print that it is refusing it, which is the opposite of a
    bypass. So a filename is an offence only when it reaches a loader.
    """
    root = Path(__file__).resolve().parents[1]
    loaders = {"load_reasoning", "load_all_reasoning", "load", "read_json",
               "read_csv", "load_jsonl"}
    offenders = []

    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts or ".venv" in str(path) or "tests" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(errors="ignore"))
        except SyntaxError:                       # not our problem here
            continue

        def literals(node: ast.AST) -> set[str]:
            return {n.value for n in ast.walk(node)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and n.value in plotdata.NON_ADMISSIBLE}

        # Variables bound to an expression naming a non-admissible file.
        tainted: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and literals(node.value):
                tainted.update(t.id for t in node.targets if isinstance(t, ast.Name))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name) else "")
            if name not in loaders:
                continue
            for arg in list(node.args) + [k.value for k in node.keywords]:
                used = literals(arg) | {n.id for n in ast.walk(arg)
                                        if isinstance(n, ast.Name) and n.id in tainted}
                if used:
                    offenders.append(
                        f"{path.relative_to(root)}:{node.lineno} {name}({sorted(used)})")

    assert not offenders, (
        "these call sites load evidence recorded non-admissible in "
        f"REASONING_DATA_PROVENANCE.md: {offenders}")


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
    # The one legitimate use of the escape hatch: evidencing the defect that put
    # this file on the non-admissible list in the first place.
    frame = plotdata.load_reasoning(path, allow_non_admissible=True)
    groups = frame.groupby(["task_id", "arm", "variant", "reasoning_budget"])
    identical = sum(1 for _, g in groups if g["final_answer"].nunique() == 1)
    assert identical == groups.ngroups, (
        "fixture no longer reproduces the shared-seed defect it guards against")
