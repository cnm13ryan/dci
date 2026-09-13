"""The v4r4 study context, and the isolation it enforces (§26).

Two namespaces, structurally separate:

* ``registered`` -- study id ``dci1v4r4``, evidence under ``dci1/evidence``,
  durable mirror under ``dci1/durable_root``;
* ``synthetic`` -- ``dci1v4r4-synthetic``, roots supplied by the harness and
  required to live outside the registered roots.

**Isolation runs in every direction and all of them are checked.** v4r4 may
never write into a v2, v3, v4r2, **v4r3**, pilot or screen tree; and
``dci1v4``'s own admission guard admits a manifest whose study id starts with
``dci1-v4``, so v4r4's identifier is deliberately hyphen-free -- ``dci1-v4r4``
would have passed that guard and let v4r4 artifacts reach v4r2 estimators.

The v4r3 entry is the one this revision adds. v4r3 is closed at Gate 1 and its
evidence tree is preserved unchanged; a v4r4 run that could open it -- to write
into it, or to adopt it as its own study root -- would put the two revisions'
records in one namespace, where a v4r3 predecessor could satisfy a v4r4 stage
by accident. ``foreign_roots`` therefore names ``evidence/dci1v4r3``,
``durable_root/dci1v4r3``, ``src/dci1v4r3`` and ``tests_v4r3``, and
``stages/reuse.py`` is the only sanctioned way v4r3 evidence enters v4r4.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dci1v4.errors import ProtocolError

from dci1v4r4 import EVIDENCE_DIRNAME, FOREIGN_STUDY_PREFIXES, STUDY_ID

SYNTHETIC_STUDY_ID = f"{STUDY_ID}-synthetic"
NAMESPACES = ("registered", "synthetic")

DCI1_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = DCI1_ROOT.parent


def foreign_roots() -> tuple[Path, ...]:
    """Every earlier study's evidence, durable and source tree."""
    roots: list[Path] = []
    for parent in (DCI1_ROOT / "evidence", DCI1_ROOT / "durable_root"):
        if not parent.exists():
            continue
        for child in parent.iterdir():
            if any(child.name.startswith(p) for p in FOREIGN_STUDY_PREFIXES):
                roots.append(child)
    roots += [DCI1_ROOT / "src" / "dci1v3", DCI1_ROOT / "src" / "dci1v4",
              DCI1_ROOT / "src" / "dci1v4r3", DCI1_ROOT / "src" / "dci1",
              DCI1_ROOT / "tests_v3", DCI1_ROOT / "tests_v4",
              DCI1_ROOT / "tests_v4r3"]
    return tuple(roots)


@dataclass(frozen=True)
class StudyContext:
    namespace: str
    study_id: str
    repo_root: Path
    evidence_root: Path
    durable_root: Path

    def __post_init__(self):
        if self.namespace not in NAMESPACES:
            raise ProtocolError(f"unknown namespace {self.namespace!r}")
        expected = (STUDY_ID if self.namespace == "registered"
                    else SYNTHETIC_STUDY_ID)
        if self.study_id != expected:
            raise ProtocolError(
                f"namespace {self.namespace!r} requires study_id "
                f"{expected!r}, got {self.study_id!r}")
        for root in (Path(self.evidence_root) / EVIDENCE_DIRNAME,
                     Path(self.durable_root) / EVIDENCE_DIRNAME):
            resolved = root.resolve()
            for foreign in foreign_roots():
                other = foreign.resolve()
                if resolved.is_relative_to(other) or \
                        other.is_relative_to(resolved):
                    raise ProtocolError(
                        f"the v4r4 study root {resolved} overlaps the "
                        f"historical tree {foreign}; v4r4 never writes into "
                        "another study's tree and never adopts one as its own")

    @property
    def study_root(self) -> Path:
        return Path(self.evidence_root) / EVIDENCE_DIRNAME

    @property
    def registration_root(self) -> Path:
        return self.study_root / "registration"

    @property
    def registration_manifest(self) -> Path:
        return self.registration_root / "registration_manifest.json"

    @property
    def signing_key_path(self) -> Path:
        return self.study_root / "keys" / "signing.key"

    def model_root(self, model_key: str) -> Path:
        return self.study_root / model_key


def registered_context() -> StudyContext:
    return StudyContext(namespace="registered", study_id=STUDY_ID,
                        repo_root=REPO_ROOT,
                        evidence_root=DCI1_ROOT / "evidence",
                        durable_root=DCI1_ROOT / "durable_root")


def synthetic_context(root: Path) -> StudyContext:
    root = Path(root)
    return StudyContext(namespace="synthetic", study_id=SYNTHETIC_STUDY_ID,
                        repo_root=REPO_ROOT,
                        evidence_root=root / "evidence",
                        durable_root=root / "durable")
