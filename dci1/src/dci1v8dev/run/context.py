"""The v8 pilot's study context, evidence layout and the isolation it enforces.

Two namespaces, both rooted where the caller says and nowhere by default:

* ``pilot`` --- study id ``dci1v8``; the pinned backend, the real model,
  every rule. ``<root>/evidence/dci1v8/<model>/...`` and
  ``<root>/durable/dci1v8/<model>/...``.
* ``synthetic`` --- ``dci1v8-synthetic``; a stand-in generator and scale
  knobs are admissible; the lifecycle test and the audits live here.

**Isolation, checked in every direction.** A v8 study root may neither lie
inside nor contain any other study's evidence or durable tree: every child
of ``dci1/evidence`` and ``dci1/durable_root`` whose name does not begin
with ``dci1v8`` is foreign (the registered ``dci1v7``, its development roots
``dci1v7-development*``, every earlier revision, every screen), and so is
every other package's source tree. The v7 rehearsal roots ``r3/r4/r5`` are
refused by that rule, not by a list that could go stale. A v8 record carries
a study id no v7 reader accepts, and the v8 signing key is its own.

The layout is v7's (``engine/paths``), carried because every audit tool in
this repository already understands it::

    <root>/evidence/dci1v8/<model>/<STAGE>/records/<record>.json   canonical
    <root>/evidence/dci1v8/<model>/<STAGE>/backend_runs/<run>/      rows
    <root>/evidence/dci1v8/<model>/<STAGE>/<record>.json            reader copy
    <root>/evidence/dci1v8/<model>/transition_log.jsonl
    <root>/evidence/dci1v8/<model>/terminal_report.json
    <root>/evidence/dci1v8/registration/pilot_manifest.json
    <root>/evidence/dci1v8/keys/signing.key
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dci1v4.errors import ProtocolError

from dci1v8dev.run import EVIDENCE_DIRNAME, STUDY_ID
from dci1v8dev.run import stages as S

__all__ = ["DCI1_ROOT", "REPO_ROOT", "SYNTHETIC_STUDY_ID",
           "STUDY_ID_OF_NAMESPACE", "StudyContext", "ModelTree",
           "pilot_context", "synthetic_context", "model_tree",
           "foreign_roots", "assert_isolated_root", "is_superseded",
           "current_files", "MANIFEST_FILENAME"]

SYNTHETIC_STUDY_ID = f"{STUDY_ID}-synthetic"
STUDY_ID_OF_NAMESPACE = {"pilot": STUDY_ID, "synthetic": SYNTHETIC_STUDY_ID,
                         "confirm": STUDY_ID,
                         "confirm-synthetic": SYNTHETIC_STUDY_ID}
MANIFEST_FILENAME = "pilot_manifest.json"

DCI1_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = DCI1_ROOT.parent

#: Source and test trees of every other revision: a v8 root inside one of
#: these would be a record beside another study's code.
_OTHER_SOURCE_TREES = ("dci1", "dci1v3", "dci1v4", "dci1v4r3", "dci1v4r4",
                       "dci1v5", "dci1v6", "dci1v7")


def foreign_roots() -> tuple[Path, ...]:
    """Every tree a v8 root must not touch."""
    roots: list[Path] = []
    for parent in (DCI1_ROOT / "evidence", DCI1_ROOT / "durable_root"):
        if not parent.exists():
            continue
        for child in sorted(parent.iterdir()):
            if child.name.startswith(".") or not child.is_dir():
                continue
            if not child.name.startswith(STUDY_ID):
                roots.append(child)
    roots += [DCI1_ROOT / "src" / name for name in _OTHER_SOURCE_TREES]
    roots += sorted(p for p in DCI1_ROOT.glob("tests*") if p.is_dir())
    return tuple(roots)


STUDY_TREE_DIRNAMES = ("evidence", "durable_root")


def assert_isolated_root(path: Path, *, what: str) -> None:
    resolved = Path(path).resolve()
    # Structural rule, independent of which checkout this package runs
    # from: on the path's ancestry, every study container --- a child of a
    # ``dci1/evidence`` or ``dci1/durable_root`` directory --- must be named
    # ``dci1v8*``. The v7 rehearsal roots (``dci1/evidence/dci1v7-development-r5``)
    # and the registered tree are refused by name wherever they live, and
    # so is a v8 root placed under any other checkout's v7 tree.
    parts = resolved.parts
    for i in range(1, len(parts) - 1):
        if parts[i] in STUDY_TREE_DIRNAMES and parts[i - 1] == "dci1":
            container = parts[i + 1]
            if not container.startswith(STUDY_ID):
                raise ProtocolError(
                    f"the v8 {what} {resolved} lies under the study "
                    f"container {Path(*parts[:i + 2])}, which is not a "
                    f"{STUDY_ID}* tree; a v8 root never lies inside another "
                    "study's evidence or durable tree (r3/r4/r5 and the "
                    "registered dci1v7 tree included)")
    for foreign in foreign_roots():
        other = foreign.resolve()
        if resolved.is_relative_to(other) or other.is_relative_to(resolved):
            raise ProtocolError(
                f"the v8 {what} {resolved} overlaps {other}; a v8 root lies "
                "outside every other study's evidence, durable and source "
                "tree in every direction (r3/r4/r5 and the registered "
                "dci1v7 tree included)")


@dataclass(frozen=True)
class StudyContext:
    namespace: str
    study_id: str
    repo_root: Path
    evidence_root: Path
    durable_root: Path

    def __post_init__(self):
        if self.namespace not in S.NAMESPACES:
            raise ProtocolError(f"unknown v8 namespace {self.namespace!r}; "
                                f"registered: {S.NAMESPACES}")
        expected = STUDY_ID_OF_NAMESPACE[self.namespace]
        if self.study_id != expected:
            raise ProtocolError(
                f"namespace {self.namespace!r} requires study_id "
                f"{expected!r}, got {self.study_id!r}")
        assert_isolated_root(Path(self.evidence_root) / EVIDENCE_DIRNAME,
                             what="study root")
        assert_isolated_root(Path(self.durable_root) / EVIDENCE_DIRNAME,
                             what="durable root")
        if Path(self.evidence_root).resolve() == \
                Path(self.durable_root).resolve():
            raise ProtocolError("the evidence root and the durable root are "
                                "the same directory; §26's mirror needs two")

    @property
    def study_root(self) -> Path:
        return Path(self.evidence_root) / EVIDENCE_DIRNAME

    @property
    def registration_root(self) -> Path:
        return self.study_root / "registration"

    @property
    def registration_manifest(self) -> Path:
        return self.registration_root / MANIFEST_FILENAME

    @property
    def signing_key_path(self) -> Path:
        return self.study_root / "keys" / "signing.key"

    def model_root(self, model_key: str) -> Path:
        return self.study_root / model_key


def pilot_context(root: Path, *, repo_root: Path | str | None = None
                  ) -> StudyContext:
    root = Path(root)
    return StudyContext(namespace="pilot", study_id=STUDY_ID,
                        repo_root=Path(repo_root) if repo_root is not None
                        else REPO_ROOT,
                        evidence_root=root / "evidence",
                        durable_root=root / "durable")


def synthetic_context(root: Path, *, repo_root: Path | str | None = None
                      ) -> StudyContext:
    root = Path(root)
    return StudyContext(namespace="synthetic", study_id=SYNTHETIC_STUDY_ID,
                        repo_root=Path(repo_root) if repo_root is not None
                        else REPO_ROOT,
                        evidence_root=root / "evidence",
                        durable_root=root / "durable")


SUPERSEDED_DIRNAME = "superseded"


def is_superseded(path: Path) -> bool:
    return SUPERSEDED_DIRNAME in Path(path).parts


def current_files(root: Path, pattern: str) -> list[Path]:
    return sorted(p for p in Path(root).rglob(pattern) if not is_superseded(p))


@dataclass(frozen=True)
class ModelTree:
    """One replication's evidence tree, in both roots."""

    context: StudyContext
    model_key: str

    @property
    def root(self) -> Path:
        return self.context.model_root(self.model_key)

    @property
    def durable(self) -> Path:
        return Path(self.context.durable_root) / EVIDENCE_DIRNAME / self.model_key

    def stage_dir(self, stage: str) -> Path:
        if stage not in S.STAGE_RECORD_FILES:
            raise ProtocolError(f"{stage!r} is not a v8 pilot stage")
        return self.root / stage

    def stage_record(self, stage: str) -> Path:
        return self.stage_dir(stage) / "records" / S.STAGE_RECORD_FILES[stage]

    def stage_record_reader_copy(self, stage: str) -> Path:
        return self.stage_dir(stage) / S.STAGE_RECORD_FILES[stage]

    def backend_runs(self, stage: str) -> Path:
        return self.stage_dir(stage) / "backend_runs"

    @property
    def transition_log(self) -> Path:
        return self.root / "transition_log.jsonl"

    @property
    def terminal_report(self) -> Path:
        return self.root / "terminal_report.json"


def model_tree(context: StudyContext, model_key: str) -> ModelTree:
    from dci1v4.models.registry import get_model

    get_model(model_key)          # registered replications only
    return ModelTree(context=context, model_key=model_key)
