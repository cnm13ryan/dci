"""The committed review artifacts in docs/batch1 are what the code produces.

They are derived files: regenerate them with
``python -m dci.batch1 write-review-artifacts`` rather than editing them, and
this test fails until they are regenerated after any change that moves them.
"""
from __future__ import annotations

import pytest

from dci.batch1 import cli
from tests.batch1.conftest import REPO

pytestmark = pytest.mark.cpu

COMMITTED = REPO / "docs" / "batch1"
ARTIFACTS = ("library_manifest.json", "compatibility_matrix.json",
             "topic_split.json", "topic_overlap.json", "topic_hygiene.json",
             "estimate.json", "approvals_template.json",
             "freeze1_proposed.json", "library_review.md",
             "compatibility_review.md", "estimate.md", "decisions.md",
             "topic_screen_report.md")


def test_committed_review_artifacts_are_current(tmp_path, capsys):
    assert cli.main(["write-review-artifacts", "--out", str(tmp_path)]) == 0
    capsys.readouterr()
    stale = [name for name in ARTIFACTS
             if (COMMITTED / name).read_text() != (tmp_path / name).read_text()]
    assert not stale, (f"regenerate with `python -m dci.batch1 "
                       f"write-review-artifacts`: {stale}")
