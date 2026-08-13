"""Every repository path a document points at must exist in that snapshot.

The migration report described `scripts/` and `notebook_source/` before either
was committed, so a reviewer following the README on a clean checkout of that
commit found neither - and the runbook's commands could not be run at all. The
rule is simple enough to enforce mechanically: a path named in a document is a
claim about the tree the document ships in.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu

DOCS = [Path("README.md"), Path("docs/MIGRATION.md")]

# Paths that look like references but are not committed repository paths.
# `build/` is generated output: tools/migrate_v15.py writes its reconstruction
# there on demand, so its absence from a clean checkout is correct and a
# document may name it as a destination.
IGNORE = re.compile(r"^(src/dci/|stages/|cells/|build/|https?:|~|/|\.{1,2}/|S\.)")

# A repository path in backticks or a fenced command: conservative on purpose,
# since a false positive here would be a nuisance and a false negative only
# leaves the reviewer where they already were.
CANDIDATE = re.compile(
    r"(?<![\w/.])((?:configs|docs|environments|scripts|tests|tools|"
    r"notebook_source|build)/[\w./*|-]*)")

# Prose that NAMES a path in order to say it is not here yet would trip the
# scanner, so those sentences use plain words instead of path syntax. That keeps
# this check strict rather than teaching it an exemption a future edit could
# lean on.


def _referenced(text: str) -> set[str]:
    found = set()
    for raw in CANDIDATE.findall(text):
        path = raw.rstrip(".,;:)`").rstrip("/")
        if IGNORE.match(path) or "*" in path or "|" in path:
            continue
        found.add(path)
    return found


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p))
def test_every_referenced_path_exists(doc):
    missing = sorted(p for p in _referenced(doc.read_text())
                     if not Path(p).exists())
    assert not missing, (
        f"{doc} names paths that do not exist in this snapshot: {missing}. "
        "Either commit them here or document them where they land.")


def test_the_scanner_would_catch_a_missing_path(tmp_path):
    """Guard against the check silently matching nothing."""
    assert "scripts/lambda_collect.sh" in _referenced(
        "run `bash scripts/lambda_collect.sh --host $IP` to collect")
    assert _referenced("see docs/MIGRATION.md") == {"docs/MIGRATION.md"}


def test_the_scanner_finds_something_in_the_real_docs():
    assert _referenced(Path("README.md").read_text())
