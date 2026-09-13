"""The one canonical v4r3 path function (§26).

Every registered location in a model evidence tree is derived here and nowhere
else, so that a stage cannot invent a place to put a record and a verifier
cannot miss one.

**The layout differs from v4r2's on purpose.** v4r2 puts each stage record in
the model tree root under its own filename; v4r3 gives every stage a directory,
because a v4r3 stage owns generated rows as well as a record and the two belong
together::

    evidence/dci1v4r4/<model>/<STAGE>/records/<record>.json   <- the record
    evidence/dci1v4r4/<model>/<STAGE>/backend_runs/<run>/      <- its rows
    evidence/dci1v4r4/<model>/<STAGE>/<record>.json            <- reader copy

The reader copy at the stage-directory root is what the §12.2 screen already
wrote and what `tools/v4r3_regime_report.py` reads; it is a convenience, and
``records/`` is canonical. Both are covered by the evidence manifest.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dci1v4.errors import ProtocolError

from dci1v4r4.engine.context import StudyContext
from dci1v4r4.protocol import constants as C

__all__ = ["SUPERSEDED_DIRNAME", "is_superseded", "current_files","STAGE_RECORD_FILES", "AUX_RECORD_FILES", "ModelTree",
           "model_tree", "required_records", "unexpected_stage_files"]

#: Stage -> its §26 record filename inside ``<model>/<STAGE>/records/``.
STAGE_RECORD_FILES = {
    C.STAGE_QUALIFIED: "qualification_record.json",
    C.STAGE_GATE0: "gate0_apparatus.json",
    C.STAGE_REGIME: "regime_record.json",
    C.STAGE_GATE1: "gate1_measurement.json",
    C.STAGE_GATE2: "gate2_regime.json",
    C.STAGE_GATE3: "gate3_references.json",
    C.STAGE_GATE4: "gate4_composed.json",
    C.STAGE_GATE5: "gate5_freeze.json",
    C.STAGE_CONFIRMATORY: "confirmatory_manifest.json",
    C.STAGE_MASKED_ANALYSIS: "masked_result.json",
    C.STAGE_UNMASKING: "unmask_record.json",
    C.STAGE_UNMASKED_ANALYSIS: "unmasked_result.json",
}

#: Non-stage registered records permitted in the model tree root.
AUX_RECORD_FILES = ("transition_log.jsonl", "terminal_report.json",
                    "cap_probe_truncation.json")


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
        from dci1v4r4 import EVIDENCE_DIRNAME
        return (Path(self.context.durable_root) / EVIDENCE_DIRNAME
                / self.model_key)

    def stage_dir(self, stage: str) -> Path:
        if stage not in STAGE_RECORD_FILES:
            raise ProtocolError(f"{stage!r} is not a registered v4r3 stage")
        return self.root / stage

    def stage_record(self, stage: str) -> Path:
        """The canonical record. ``records/`` is the one a guard reads."""
        return self.stage_dir(stage) / "records" / STAGE_RECORD_FILES[stage]

    def stage_record_reader_copy(self, stage: str) -> Path:
        return self.stage_dir(stage) / STAGE_RECORD_FILES[stage]

    def backend_runs(self, stage: str) -> Path:
        return self.stage_dir(stage) / "backend_runs"

    @property
    def transition_log(self) -> Path:
        return self.root / "transition_log.jsonl"

    @property
    def terminal_report(self) -> Path:
        return self.root / "terminal_report.json"

    def superseded_dir(self, marker: str) -> Path:
        """Where a superseded stage's whole directory is retained.

        §26's artifact model carries a `superseded` state so that a record the
        study no longer stands behind is *retained and marked* rather than
        deleted or edited. `marker` identifies the supersession --- in
        practice the first twelve characters of the commit that supersedes it
        --- so two supersessions of the same stage never collide.
        """
        return self.root / "superseded" / marker

    @property
    def cap_probe_truncation(self) -> Path:
        """§12.1's restricted derived artifact. See ``stages/cap_probe.py``."""
        return self.root / "cap_probe_truncation.json"

    # ---------------------------------------------------------- masking
    def mask_dir(self, mask_namespace: str) -> Path:
        if mask_namespace not in C.MASK_NAMESPACES:
            raise ProtocolError(
                f"{mask_namespace!r} is not a registered v4r3 mask namespace; "
                f"registered: {C.MASK_NAMESPACES}")
        return self.root / "masking" / mask_namespace

    def mask_key_path(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "mask_key.json"

    def masked_view(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "masked_rows.jsonl"

    def mask_event_log(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "events.jsonl"


#: The directory name a superseded stage is retained under.
SUPERSEDED_DIRNAME = "superseded"


def is_superseded(path: Path) -> bool:
    """True for a file retained under a supersession.

    Superseded rows are real generations and remain evidence --- the §6.2
    topic-spend audit and the durability manifest both count them, because a
    topic a retired run spent is still spent and a file the study holds is
    still a file it must be able to restore. What they must never do is enter
    a *current* pool: after a stage is re-run, a glob that reaches both copies
    puts every response in twice, and a pool with duplicate identities has no
    disjoint split.
    """
    return SUPERSEDED_DIRNAME in Path(path).parts


def current_files(root: Path, pattern: str) -> list[Path]:
    """Files matching ``pattern`` under ``root``, superseded ones excluded."""
    return sorted(p for p in Path(root).rglob(pattern) if not is_superseded(p))


def model_tree(context: StudyContext, model_key: str) -> ModelTree:
    from dci1v4.models.registry import get_model

    get_model(model_key)          # registered replications only
    return ModelTree(context=context, model_key=model_key)


def required_records(present_through: str) -> list[str]:
    """§26 record paths required once the sequence has reached a stage."""
    names: list[str] = []
    for stage in C.STAGE_SEQUENCE:
        names.append(f"{stage}/records/{STAGE_RECORD_FILES[stage]}")
        if stage == present_through:
            break
    return names


def unexpected_stage_files(tree: ModelTree, stage: str) -> list[str]:
    """Registered-looking record files outside the closed list for a stage."""
    records = tree.stage_dir(stage) / "records"
    if not records.exists():
        return []
    allowed = {STAGE_RECORD_FILES[stage]}
    return sorted(p.name for p in records.iterdir()
                  if p.is_file() and p.name not in allowed)
