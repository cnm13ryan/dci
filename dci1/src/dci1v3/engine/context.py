"""StudyContext: the single execution context every engine function receives.

Two namespaces exist and are structurally separate (item 10):

* ``registered`` — study_id ``dci1-v3``, evidence under the repository's
  ``dci1/evidence``, durable mirror under ``dci1/durable_root``. Only this
  namespace can hold accepted registered evidence.
* ``synthetic`` — study_id ``dci1-v3-synthetic``, roots supplied by the test
  harness and required to live OUTSIDE the registered roots. Synthetic
  artifacts can never enter the registered namespace: the constructor
  refuses mixed configurations and every record carries its namespace.

There is no allow_dirty flag, environment override, or bypass anywhere: the
same clean-worktree and provenance checks run in both namespaces against
``repo_root``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dci1v3 import STUDY_ID, SYNTHETIC_STUDY_ID
from dci1v3.errors import ProtocolError

#: dci1/ inside the repository (…/dci1/src/dci1v3/engine/context.py).
DCI1_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = DCI1_ROOT.parent

NAMESPACES = ("registered", "synthetic")


@dataclass(frozen=True)
class StudyContext:
    namespace: str
    study_id: str
    repo_root: Path
    evidence_root: Path
    durable_root: Path
    deps_lock_path: Path
    deps_export_path: Path

    def __post_init__(self):
        if self.namespace not in NAMESPACES:
            raise ProtocolError(f"unknown namespace {self.namespace!r}")
        expected = (STUDY_ID if self.namespace == "registered"
                    else SYNTHETIC_STUDY_ID)
        if self.study_id != expected:
            raise ProtocolError(
                f"namespace {self.namespace!r} requires study_id "
                f"{expected!r}, got {self.study_id!r}")
        if self.namespace == "synthetic":
            registered = registered_context()
            for root in (self.evidence_root, self.durable_root):
                if root.resolve().is_relative_to(
                        registered.evidence_root.resolve()) or \
                        root.resolve().is_relative_to(
                            registered.durable_root.resolve()):
                    raise ProtocolError(
                        "synthetic roots must live outside the registered "
                        "evidence and durable roots")

    @property
    def study_root(self) -> Path:
        return self.evidence_root / self.study_id

    @property
    def registration_dir(self) -> Path:
        return self.study_root / "registration"

    @property
    def registration_manifest(self) -> Path:
        return self.registration_dir / "manifest.json"

    @property
    def signing_key_path(self) -> Path:
        return self.registration_dir / "signing_key"

    @property
    def lock_dir(self) -> Path:
        return self.study_root / ".locks"

    @property
    def durable_study_root(self) -> Path:
        return self.durable_root / self.study_id


def registered_context() -> StudyContext:
    return StudyContext(
        namespace="registered",
        study_id=STUDY_ID,
        repo_root=REPO_ROOT,
        evidence_root=DCI1_ROOT / "evidence",
        durable_root=DCI1_ROOT / "durable_root",
        deps_lock_path=DCI1_ROOT / "uv.lock",
        deps_export_path=DCI1_ROOT / "requirements-frozen.txt",
    )


def synthetic_context(base: Path, repo_root: Path) -> StudyContext:
    """A synthetic-namespace context rooted at a harness directory."""
    base = Path(base)
    return StudyContext(
        namespace="synthetic",
        study_id=SYNTHETIC_STUDY_ID,
        repo_root=Path(repo_root),
        evidence_root=base / "evidence",
        durable_root=base / "durable",
        deps_lock_path=Path(repo_root) / "dci1" / "uv.lock",
        deps_export_path=Path(repo_root) / "dci1" / "requirements-frozen.txt",
    )
