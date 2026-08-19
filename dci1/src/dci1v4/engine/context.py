"""StudyContext: the single execution context every v4 engine function takes.

Two namespaces exist and are structurally separate:

* ``registered`` — study_id ``dci1-v4``, evidence under ``dci1/evidence``,
  durable mirror under ``dci1/durable_root``. Only this namespace can hold
  accepted registered v4 evidence.
* ``synthetic`` — study_id ``dci1-v4-synthetic``, roots supplied by the test
  harness and required to live outside the registered roots.

**Isolation from earlier studies is enforced here, not documented (§26).**
The constructor refuses any root that lies inside a v3, v2 or B+R pilot
evidence tree, so a v4 artifact cannot be written into ``evidence/dci1-v3``,
``durable_root/dci1-v3``, ``evidence/br-pilot-v4`` or ``reports/br_pilot_v4``
even by a caller that asks for it. There is no allow_dirty flag, environment
override, or bypass anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dci1v4 import STUDY_ID, SYNTHETIC_STUDY_ID
from dci1v4.errors import ProtocolError

#: dci1/ inside the repository (…/dci1/src/dci1v4/engine/context.py).
DCI1_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = DCI1_ROOT.parent

NAMESPACES = ("registered", "synthetic")

#: Study identifiers whose trees v4 may never write into (§26, brief §2).
FOREIGN_STUDY_IDS = ("dci1-v2", "dci1-v3", "dci1-v3-synthetic", "br-pilot-v4")


def foreign_roots() -> tuple[Path, ...]:
    """Every earlier study's evidence, durable and report tree."""
    roots = [DCI1_ROOT / "evidence" / sid for sid in FOREIGN_STUDY_IDS]
    roots += [DCI1_ROOT / "durable_root" / sid for sid in FOREIGN_STUDY_IDS]
    roots += [DCI1_ROOT / "reports" / "br_pilot_v4",
              DCI1_ROOT / "src" / "dci1v3", DCI1_ROOT / "src" / "dci1",
              DCI1_ROOT / "tests_v3"]
    return tuple(roots)


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
        for root in (self.evidence_root, self.durable_root):
            resolved = Path(root).resolve()
            for foreign in foreign_roots():
                if resolved.is_relative_to(foreign.resolve()) or \
                        foreign.resolve().is_relative_to(resolved):
                    raise ProtocolError(
                        f"v4 root {resolved} overlaps the historical tree "
                        f"{foreign}; v4 never writes into a v2, v3 or pilot "
                        f"tree and never adopts one as its own root (§26)")
        if self.namespace == "synthetic":
            registered = registered_context()
            for root in (self.evidence_root, self.durable_root):
                if Path(root).resolve().is_relative_to(
                        registered.study_root.resolve()) or \
                        Path(root).resolve().is_relative_to(
                            registered.durable_study_root.resolve()):
                    raise ProtocolError(
                        "synthetic roots must live outside the registered v4 "
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
    def amendment_register(self) -> Path:
        return self.registration_dir / "amendments.jsonl"

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


def synthetic_context(base: Path, repo_root: Path | None = None
                      ) -> StudyContext:
    """A synthetic-namespace context rooted at a harness directory."""
    base = Path(base)
    repo_root = Path(repo_root) if repo_root is not None else REPO_ROOT
    return StudyContext(
        namespace="synthetic",
        study_id=SYNTHETIC_STUDY_ID,
        repo_root=repo_root,
        evidence_root=base / "evidence",
        durable_root=base / "durable",
        deps_lock_path=DCI1_ROOT / "uv.lock",
        deps_export_path=DCI1_ROOT / "requirements-frozen.txt",
    )
