"""The v7 study context, and the isolation it enforces (§28).

Two namespaces, structurally separate:

* ``registered`` --- study id ``dci1v7``, evidence under ``dci1/evidence``,
  durable mirror under ``dci1/durable_root``;
* ``synthetic`` --- ``dci1v7-synthetic``, roots supplied by the harness and
  required to live outside the registered roots.

**Isolation runs in every direction and all of them are checked.** v5 may
never write into a v2, v3, v4r2, v4r3, **v4r4**, pilot or screen tree; and no
earlier revision may adopt a v5 record as a predecessor. Three independent
things stop the second: the v5 model tree is a different path, the v5 signing
key is a different key, and every record carries ``study_id``, which every
revision's ``read_stage_record`` tests against its own identifier by exact
equality. ``dci1v4``'s own admission guard admits a manifest whose study id
starts with ``dci1-v4``, and ``dci1v7`` does not, so a v5 artifact cannot
reach a v4r2 estimator either.

The ``dci1v6`` entry is the one this revision adds. v6 **closed** on
2026-08-27 with signed records through Gate 4 on two replications, four
terminal reports and 12,096 probe rows per replication; none of that may
satisfy a v7 stage or reach a v7 estimator. Its records are historical
outcomes and development evidence for v7's *design* and enter only through
``protocol/reuse_ledger.py``, never by a path that mistakes them for v7's own.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dci1v4.errors import ProtocolError

from dci1v7 import EVIDENCE_DIRNAME, FOREIGN_STUDY_PREFIXES, STUDY_ID

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
              DCI1_ROOT / "src" / "dci1v4r3", DCI1_ROOT / "src" / "dci1v4r4",
              DCI1_ROOT / "src" / "dci1v5", DCI1_ROOT / "src" / "dci1v6",
              DCI1_ROOT / "src" / "dci1",
              DCI1_ROOT / "tests_v3", DCI1_ROOT / "tests_v4",
              DCI1_ROOT / "tests_v4r3", DCI1_ROOT / "tests_v4r4",
              DCI1_ROOT / "tests_v5", DCI1_ROOT / "tests_v6"]
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
                        f"the v5 study root {resolved} overlaps the "
                        f"historical tree {foreign}; v5 never writes into "
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


def synthetic_context(root: Path, *,
                      repo_root: Path | str | None = None) -> StudyContext:
    """The synthetic namespace, rooted at ``root``.

    ``repo_root`` exists so an integration harness can point the production
    provenance rules --- clean worktree, resolvable head commit, protocol
    document hashes, the §30 ledger --- at an **isolated repository it built
    and committed**, rather than at the developer's dirty worktree. The rules
    then run unweakened: ``registered_context`` still names the real root and
    no production caller passes this.
    """
    root = Path(root)
    return StudyContext(namespace="synthetic", study_id=SYNTHETIC_STUDY_ID,
                        repo_root=Path(repo_root) if repo_root is not None
                        else REPO_ROOT,
                        evidence_root=root / "evidence",
                        durable_root=root / "durable")
