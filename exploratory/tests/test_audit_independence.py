"""The audit controls must stay independent of the thing they audit.

COUNTERWEIGHT TO THE SEGMENTATION UNIFICATION
---------------------------------------------
The Pair 3 segmentation was just unified: `dci.v19.text` stopped carrying its own
boundary regex and abbreviation tables and now calls the one certified
implementation, because two copies had silently drifted and reinstated a repaired
defect.

That is right for two layers of the SAME measurement. It is exactly wrong for the
checks that exist to catch such a defect. This repository has three deliberate
re-implementations, and their scientific value is precisely that they do not
share code:

  * `independent_segmenter.segment` — a different algorithm class (a character
    scanner, not a regex split) with a mechanically derived abbreviation set;
  * `reanalysis_standalone` — a from-scratch recomputation of every headline that
    imports nothing from the project at all;
  * `dci_exploratory.mechanism.legacy_split_sentences` — a verbatim
    reconstruction of the PRE-repair segmenter, which powers the
    `n_sentences_legacy` sensitivity column and must never be improved.

The history is explicit about why: the first "independent" checker reproduced the
production defect because it was written the same way, and two implementations
that share an author's blind spot agree without that agreement meaning anything.

So these tests assert non-sharing. Anyone applying "one implementation" uniformly
across the repository will fail here, and should read this docstring rather than
delete the assertion. `test_round5_machinery` separately pins that the legacy
segmenter still DISAGREES with the certified one; this module pins the imports.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parents[1]

PRODUCTION_PACKAGES = ("dci", "dci_exploratory", "crossmodel")


def module_level_imports(path: Path) -> set[str]:
    """Top-level imported module names only.

    Scope matters. A comparison driver MUST import production to compare against
    it — `independent_segmenter.main` does, inside the function. What would
    destroy the control is the segmenter itself depending on production, and that
    dependency would be a module-level import.
    """
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in tree.body:                       # module level only, not nested
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def all_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_the_independent_segmenter_does_not_import_production_to_segment():
    """Its algorithm must owe nothing to `dci.verifiers.rules`."""
    path = EXPLORATORY / "independent_segmenter.py"
    shared = module_level_imports(path) & set(PRODUCTION_PACKAGES)
    assert not shared, (
        f"independent_segmenter imports {shared} at module scope; its value is "
        "that it shares no code with the segmenter it audits")


def test_the_independent_segmenter_may_still_compare_against_production():
    """The driver imports production deliberately — that IS the comparison.

    Asserted so the previous test is not "fixed" by deleting the comparison.
    """
    source = (EXPLORATORY / "independent_segmenter.py").read_text()
    assert "from dci.verifiers.rules import split_sentences" in source
    assert "def main(" in source


def test_the_standalone_reanalysis_imports_nothing_from_the_project():
    """Agreement is evidence only where it could have failed."""
    path = EXPLORATORY / "reanalysis_standalone.py"
    shared = all_imports(path) & set(PRODUCTION_PACKAGES)
    assert not shared, (
        f"reanalysis_standalone imports {shared}; it re-implements the analysis "
        "from scratch so that agreeing with production is a result, not a tautology")


def test_the_legacy_segmenter_keeps_its_own_frozen_boundary_rule():
    """The pre-repair pattern is reconstructed on purpose and must not be
    redirected at the certified one — that would silently turn the sensitivity
    column into a copy of the primary."""
    source = (EXPLORATORY / "dci_exploratory" / "mechanism.py").read_text()
    assert "_LEGACY_BOUNDARY = re.compile(r'(?<=[.!?])[\"”’]?\\s+')" in source, (
        "the frozen pre-repair boundary rule has been altered; it is a verbatim "
        "reconstruction of a defect and must never be improved")
    assert "ends_sentence" not in source, (
        "the legacy segmenter has been given the abbreviation guard, which is "
        "the repair it exists to measure the absence of")


@pytest.mark.parametrize("text,legacy_n,certified_n", [
    ("Dr. Ellis spoke to Mr. Hall about the survey.", 3, 1),
    ("Sales spike at 6 a.m. when others sleep.", 2, 1),
])
def test_the_two_segmenters_still_disagree_where_the_repair_applies(
        text, legacy_n, certified_n):
    """Behavioural counterpart to the import checks: if these ever agree, the
    sensitivity column has stopped measuring anything."""
    import sys
    sys.path.insert(0, str(EXPLORATORY))
    from dci_exploratory import mechanism

    from dci.verifiers.rules import split_sentences

    assert len(mechanism.legacy_split_sentences(text)) == legacy_n
    assert len(split_sentences(text)) == certified_n
