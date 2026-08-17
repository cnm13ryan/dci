"""The one canonical path function (§27, item 57).

Every registered location in a model evidence tree is derived here and
nowhere else. Missing required paths, stale paths, and unexpected registered
paths fail evidence verification (engine/verify.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dci1v3.engine.context import StudyContext
from dci1v3.models.registry import get_model
from dci1v3.protocol import constants as C

#: Stage -> its §27 record filename in the model tree root.
STAGE_RECORD_FILES = {
    C.STAGE_QUALIFIED: "qualification.json",
    C.STAGE_GATE0: "gate0_apparatus.json",
    C.STAGE_REGIME: "regime_screen.json",
    C.STAGE_GATE1: "gate1_measurement.json",
    C.STAGE_GATE2A: "gate2a_solo.json",
    C.STAGE_GATE2B: "gate2b_composed.json",
    C.STAGE_FREEZE: "gate3_freeze.json",
    C.STAGE_CONFIRMATORY: "confirmatory_manifest.json",
    C.STAGE_PRIMARY_SELECTION: "primary_selection.json",
    C.STAGE_MASK: "confirmatory_mask_record.json",
    C.STAGE_MASKED_ANALYSIS: "masked_result.json",
    C.STAGE_UNMASK: "unmask_record.json",
    C.STAGE_UNMASKED_ANALYSIS: "unmasked_result.json",
}

#: Non-stage registered records permitted in the tree root.
AUX_RECORD_FILES = ("transition_log.jsonl", "terminal_report.json",
                    "carry_over.json", "pseudo_runs.json", "greedy_run.json")

#: Data directories a model tree may contain.
STAGE_DATA_DIRS = ("qualification", "pilot", "prescreen", "gate1", "gate2a",
                   "gate2b", "confirmatory", "masking", "analysis",
                   "artifacts")


@dataclass(frozen=True)
class ModelTree:
    context: StudyContext
    model_key: str

    @property
    def root(self) -> Path:
        return self.context.study_root / self.model_key

    @property
    def durable(self) -> Path:
        return self.context.durable_study_root / self.model_key

    def stage_record(self, stage: str) -> Path:
        return self.root / STAGE_RECORD_FILES[stage]

    @property
    def transition_log(self) -> Path:
        return self.root / "transition_log.jsonl"

    @property
    def terminal_report(self) -> Path:
        return self.root / "terminal_report.json"

    @property
    def carry_over_record(self) -> Path:
        return self.root / "carry_over.json"

    @property
    def artifact_ledger(self) -> Path:
        return self.root / "artifacts" / "ledger.jsonl"

    def data_dir(self, stage_dir: str) -> Path:
        if stage_dir not in STAGE_DATA_DIRS:
            raise KeyError(stage_dir)
        return self.root / stage_dir

    # ---------------------------------------------------------- masking
    def mask_dir(self, mask_namespace: str) -> Path:
        assert mask_namespace in ("pilot_mask", "confirmatory_mask")
        return self.root / "masking" / mask_namespace

    def mask_key_path(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "mask_key.json"

    def mask_reservation(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "reservation.json"

    def unmask_reservation(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "unmask_reservation.json"

    def masked_view(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "masked_rows.jsonl"

    def mask_event_log(self, mask_namespace: str) -> Path:
        return self.mask_dir(mask_namespace) / "events.jsonl"


def model_tree(context: StudyContext, model_key: str) -> ModelTree:
    get_model(model_key)      # registered replications only
    return ModelTree(context=context, model_key=model_key)


def required_records(present_through: str) -> list[str]:
    """§27 record filenames required once the sequence reached a stage."""
    names = []
    for stage in C.STAGE_SEQUENCE:
        names.append(STAGE_RECORD_FILES[stage])
        if stage == present_through:
            break
    return names


def unexpected_root_files(tree: ModelTree) -> list[str]:
    """Registered-looking files in the tree root outside the closed list."""
    allowed = set(STAGE_RECORD_FILES.values()) | set(AUX_RECORD_FILES)
    if not tree.root.exists():
        return []
    return sorted(p.name for p in tree.root.iterdir()
                  if p.is_file() and p.name not in allowed)
