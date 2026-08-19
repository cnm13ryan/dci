"""Git provenance (§26, §27): clean worktree, producing commit, and
invoked-source membership.

There is no allow_dirty flag, environment override, or bypass: every namespace
runs the same checks against its context's ``repo_root``. The membership check
requires that the bytes of every loaded ``dci1v4`` source and data file exist
as a blob at the canonical repository path in the producing commit, so the
code that runs is exactly the code that is tracked.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import dci1v4
from dci1v4.errors import IntegrityError
from dci1v4.protocol.hashing import git_blob_sha

PACKAGE_DIR = Path(dci1v4.__file__).resolve().parent
PACKAGE_REPO_PREFIX = "dci1/src/dci1v4"


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo_root), *args],
                               capture_output=True, text=True)
    if completed.returncode != 0:
        raise IntegrityError(f"git {' '.join(args)} failed in {repo_root}: "
                             f"{completed.stderr.strip()}")
    return completed.stdout


def assert_clean_worktree(repo_root: Path) -> None:
    """Empty ``git status --porcelain``. Anything else is writer_dirty."""
    status = _git(repo_root, "status", "--porcelain")
    if status.strip():
        dirty = status.strip().splitlines()[:5]
        raise IntegrityError(
            f"dirty Git worktree in {repo_root}; no v4 artifact may be "
            f"produced (first entries: {dirty})")


def head_commit(repo_root: Path) -> str:
    return _git(repo_root, "rev-parse", "HEAD").strip()


def invoked_source_paths() -> list[Path]:
    """Every source and data file of the dci1v4 package."""
    files = [p for p in sorted(PACKAGE_DIR.rglob("*"))
             if p.is_file() and p.suffix in (".py", ".json")
             and "__pycache__" not in p.parts]
    if not files:
        raise IntegrityError("no dci1v4 source files found")
    return files


def assert_sources_in_commit(repo_root: Path, commit: str) -> dict:
    """Every invoked source path belongs, byte-for-byte, to the commit."""
    listing = _git(repo_root, "ls-tree", "-r", commit, "--",
                   PACKAGE_REPO_PREFIX)
    tree: dict[str, str] = {}
    for line in listing.strip().splitlines():
        meta, path = line.split("\t", 1)
        tree[path] = meta.split()[2]
    if not tree:
        raise IntegrityError(
            f"commit {commit[:12]} contains no {PACKAGE_REPO_PREFIX} tree; "
            f"the v4 implementation is not tracked")
    checked = 0
    for source in invoked_source_paths():
        rel = f"{PACKAGE_REPO_PREFIX}/{source.relative_to(PACKAGE_DIR)}"
        blob = tree.get(rel)
        if blob is None:
            raise IntegrityError(
                f"invoked source {rel} is absent from commit {commit[:12]}")
        if git_blob_sha(source.read_bytes()) != blob:
            raise IntegrityError(
                f"invoked source {rel} differs from commit {commit[:12]}")
        checked += 1
    return {"producing_commit": commit, "sources_verified": checked}
