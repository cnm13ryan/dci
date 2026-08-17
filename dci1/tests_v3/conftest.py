"""Fixtures for the v3 canonical test suite.

Synthetic-namespace tests run the production engine against a scratch git
repository containing a committed copy of the dci1v3 sources, so the
clean-worktree and invoked-source-membership checks run for real, with no
bypass anywhere.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

DCI1 = Path(__file__).resolve().parents[1]
SRC = DCI1 / "src"
sys.path.insert(0, str(SRC))

from dci1v3.engine.context import StudyContext, synthetic_context  # noqa: E402
from dci1v3.stages.registration import register_study  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo), *args],
                               capture_output=True, text=True, check=True)
    return completed.stdout


def build_synthetic_repo(root: Path) -> Path:
    repo = root / "repo"
    (repo / "dci1" / "src").mkdir(parents=True)
    shutil.copytree(SRC / "dci1v3", repo / "dci1" / "src" / "dci1v3",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(DCI1 / "uv.lock", repo / "dci1" / "uv.lock")
    shutil.copy(DCI1 / "requirements-frozen.txt",
                repo / "dci1" / "requirements-frozen.txt")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "v3@test")
    _git(repo, "config", "user.name", "v3 test harness")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "synthetic v3 fixture")
    return repo


@pytest.fixture(scope="session")
def synthetic_repo(tmp_path_factory) -> Path:
    return build_synthetic_repo(tmp_path_factory.mktemp("v3"))


@pytest.fixture()
def ctx(synthetic_repo, tmp_path) -> StudyContext:
    return synthetic_context(tmp_path / "study", synthetic_repo)


@pytest.fixture()
def registered_ctx(ctx) -> StudyContext:
    register_study(ctx)
    return ctx


def make_synthetic_annotations(packet_path: Path) -> dict:
    """Synthetic annotators: three labels per item agreeing with S0."""
    import json

    from dci1v3.verifiers.target import s0_count

    annotations: dict = {"face_validity": [True, True, True]}
    for line in packet_path.read_text().splitlines():
        item = json.loads(line)
        label = "pass" if s0_count(item["response_text"]) == item["n"] \
            else "fail"
        annotations[item["item_id"]] = [label] * 3
    return annotations
