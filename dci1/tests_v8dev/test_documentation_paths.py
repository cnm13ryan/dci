"""Repository paths named in the v8 candidate's source, tests, tools and
reports resolve (CLAUDE.md, *Evidence*: a cited path that does not exist is
a broken citation). ``docs/VERSION_DRIFT.md`` is not scanned: its table
quotes the stale paths it records, on purpose. Evidence trees are gitignored
and are not checked."""
from __future__ import annotations

import re
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
SCANNED = ("src/dci1v8dev/**/*.py", "tests_v8dev/*.py", "tools/v8_*.py",
           "reports/dci1v8dev/*.md", "reports/dci1v8dev/prescreen/README.md",
           "docs/V8_CANDIDATE.md", "README.md")
RUNTIME_PREFIXES = ("dci1/evidence", "evidence/", "dci1/durable_root", "dci1/.venv")
PATTERN = re.compile(r"(?<![\w/`])((?:dci1|user-notes|exploratory|docs|tools|reports)"
                     r"/[A-Za-z0-9_./\-]+[A-Za-z0-9_/\-])")
ALLOWED_MISSING = frozenset((
    "reports/dci1v8dev/chance_basis/<tree>__<model>.json",
    "tools/v8_*.py", "reports/dci1v8dev/prescreen/*.json",
))


def _exists(token: str) -> bool:
    """Exact, or a prefix of existing files (``reports/x/coverage_simulation``
    cites ``coverage_simulation.{json,md}``)."""
    for base in (REPO, DCI1):
        if (base / token).exists():
            return True
        parent, stem = (base / token).parent, (base / token).name
        if parent.exists() and any(p.name.startswith(stem) for p in parent.iterdir()):
            return True
    return False


def test_every_cited_path_exists():
    missing = {}
    for pattern in SCANNED:
        for path in DCI1.glob(pattern):
            for token in PATTERN.findall(path.read_text(errors="replace")):
                token = token.rstrip(".,;:)")
                if token.startswith(RUNTIME_PREFIXES) or token in ALLOWED_MISSING:
                    continue
                if "*" in token or "<" in token:
                    continue
                if not _exists(token):
                    missing.setdefault(token, []).append(str(path.relative_to(DCI1)))
    assert not missing, missing
