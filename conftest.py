"""Shared collection rules for both test suites.

`pytest` resolves its configuration from the repository's `pyproject.toml` for
`tests/` and `exploratory/tests/` alike, so one conftest here covers both.

The only rule so far is the platform routing. Two tests used to fail on macOS for
reasons that had nothing to do with what they assert - a `/proc` read and a
`multiprocessing` start-method difference. A suite that is red for irrelevant
reasons teaches the reader to skip past the red, which is how a genuinely failing
verifier audit sat unnoticed on `main`. A Linux-only test is now skipped, not
failed, and a test that can be made portable is made portable instead of marked.
"""
from __future__ import annotations

import sys

import pytest


def pytest_collection_modifyitems(config, items):
    if sys.platform.startswith("linux"):
        return
    skip = pytest.mark.skip(reason="Linux-only interface; run on the workstation")
    for item in items:
        if "linux" in item.keywords:
            item.add_marker(skip)
