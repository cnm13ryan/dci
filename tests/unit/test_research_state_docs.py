"""The human-facing layer must keep pointing at things that exist.

`RESEARCH_STATE.md` is deliberately derivative: it holds almost no primary
numbers and instead links to the reports, matrices and generated artifacts that
do. That is what stops it becoming a thirty-fifth hand-maintained source of truth
— and it only works while the links resolve. A state document whose links rot is
worse than none, because it still reads as current.

These are cheap structural checks, not content review. Nothing here can tell
whether a claim is still true; that is what `CHANGES_SCIENTIFIC.md` is for.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu

REPO = Path(__file__).resolve().parents[2]

DOCS = (
    "RESEARCH_STATE.md",
    "docs/history/research_state_log.md",
    "CHANGES_SCIENTIFIC.md",
    "exploratory/EXPERIMENTS.md",
    "exploratory/evidence/README.md",
)

LINK = re.compile(r"\]\(([^)]+)\)")


@pytest.mark.parametrize("doc", DOCS)
def test_the_document_exists(doc: str):
    assert (REPO / doc).exists(), f"{doc} is referenced by the entry point and absent"


@pytest.mark.parametrize("doc", DOCS)
def test_every_relative_link_resolves(doc: str):
    path = REPO / doc
    broken = []
    for target in LINK.findall(path.read_text()):
        target = target.split("#")[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (path.parent / target).exists():
            broken.append(target)
    assert not broken, f"{doc} links to missing paths: {broken}"


def test_the_entry_point_reaches_the_index_and_the_change_log():
    """The three layers are only a hierarchy if the top one names the others."""
    text = (REPO / "RESEARCH_STATE.md").read_text()
    assert "exploratory/EXPERIMENTS.md" in text
    assert "CHANGES_SCIENTIFIC.md" in text


def test_the_experiment_index_names_every_script_prefix_in_use():
    """A family that exists in the tree but not in the index is undiscoverable."""
    index = (REPO / "exploratory" / "EXPERIMENTS.md").read_text()
    prefixes = {name.split("_")[0]
                for name in (p.name for p in (REPO / "exploratory").glob("*.py"))
                if "_" in name}
    # Prefixes that are single-purpose tooling rather than an experiment family
    # are named in the tooling table instead; both live in the same document.
    missing = [prefix for prefix in prefixes if f"{prefix}_" not in index]
    assert not missing, f"script families absent from EXPERIMENTS.md: {sorted(missing)}"


def test_the_change_log_is_prospective_not_a_commit_dump():
    """One entry per measurement change. If this ever holds hundreds of entries,
    the rule 'not a commit log' has quietly stopped being applied."""
    text = (REPO / "CHANGES_SCIENTIFIC.md").read_text()
    entries = [line for line in text.splitlines() if line.startswith("## ")]
    assert entries, "the change log has no entries"
    assert len(entries) < 200, (
        f"{len(entries)} entries — this has become a commit log")
    for entry in entries:
        assert re.match(r"## \d{4}-\d{2}-\d{2} — ", entry), (
            f"entry is not `## YYYY-MM-DD — what changed`: {entry!r}")
