"""Repository paths named in v7 source, tests and reports resolve.

A docstring that points at a report is a citation, and a citation of a path
that does not exist is a broken one (``CLAUDE.md``, *Evidence*). Historical
paths are welcome --- v5's decision packets are cited from v7 code because
that is where they live --- but they must exist where they say they are.
Evidence trees are gitignored and are not checked.
"""
from __future__ import annotations

import re
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent

#: ``docs/VERSION_DRIFT.md`` is not scanned: its stale-reference table
#: quotes the broken paths it records, on purpose.
SCANNED = ("src/dci1v7/**/*.py", "tests_v7/*.py", "reports/dci1v7/*.md",
           "reports/dci1v7/development_rehearsal/*.md", "README.md")
#: Runtime trees and environments: gitignored, absent from a fresh clone.
RUNTIME_PREFIXES = ("dci1/evidence", "evidence/", "dci1/durable_root",
                    "dci1/.venv", "dci1/annotations")
PATTERN = re.compile(
    r"(?<![\w/])((?:dci1|user-notes|exploratory|docs|tools|reports)"
    r"/[A-Za-z0-9_./\-]+)")
#: Symbol references written path-first, and names that are not files.
ALLOWED_MISSING = frozenset((
    "dci1/src/dci1v7/protocol/manifest.assert_documents_adopted",
))


def _candidates(token: str) -> tuple[Path, ...]:
    """Repository-relative first; ``tools/``, ``docs/`` and ``reports/``
    are also written relative to ``dci1/`` in this package."""
    return (REPO / token, DCI1 / token)


def referenced_paths() -> dict[str, set[str]]:
    seen: dict[str, set[str]] = {}
    for pattern in SCANNED:
        for path in sorted(DCI1.glob(pattern)):
            if path == Path(__file__):
                continue            # names the stale paths it guards against
            for match in PATTERN.finditer(path.read_text()):
                token = match.group(1).rstrip(".,;:)'\"`")
                if "*" in token or token.endswith(("_", "-", "/")):
                    continue
                if token.startswith(RUNTIME_PREFIXES):
                    continue
                seen.setdefault(token, set()).add(
                    str(path.relative_to(DCI1)))
    return seen


def test_every_repository_path_named_in_v7_resolves():
    missing = {token: files for token, files in referenced_paths().items()
               if token not in ALLOWED_MISSING
               and not any(p.exists() for p in _candidates(token))}
    assert not missing, "\n".join(
        f"{token}  <- {sorted(files)}" for token, files in sorted(
            missing.items()))


def test_the_v5_design_evidence_is_cited_at_v5_s_path():
    """The two pointers that were stale until 2026-08-29: the marker
    frequency measurement and the D4 audit packet are v5 artifacts and are
    cited from v5's tree, not from a v7 path that never existed."""
    source = (DCI1 / "src/dci1v7/verifiers/constraints.py").read_text()
    assert "dci1/reports/dci1v5/development/d6_marker_frequency.json" in source
    assert "dci1/reports/dci1v5/d4_marker_audit.md" in source
    assert "dci1/reports/dci1v7/development/d6_marker_frequency.json" \
        not in source
    assert "dci1/reports/dci1v7/d4_marker_audit.md" not in source
    for token in ("dci1/reports/dci1v5/development/d6_marker_frequency.json",
                  "dci1/reports/dci1v5/d4_marker_audit.md"):
        assert (REPO / token).exists()
