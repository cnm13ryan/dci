"""The Addendum-A evidence tree (reconciliation R16).

    evidence/<study_id>/<model_slug>/<freeze_id>/
        freeze_record.json
        prompts/                 frozen cell plan (retained indefinitely)
        cache/                   raw generation cache (append-only, sealed)
        selection/primary/       primary_selection.jsonl
        selection/pseudo_runs/   pseudo_run_<r>.jsonl
        derived/primary/         accepted.parquet scored.parquet analysis.parquet
        derived/pseudo_runs/     accepted_<r>.parquet …
        masking/                 mask_key.sealed.json masked_view/ commitment.json
                                 unmasking_record.json
        integrity/               integrity_report.jsonl
        study_manifest.json

`freeze_id` is the first 12 hex digits of the model's `freeze_hash`. The
Gate-0 procedural pilot exercises the identical tree under the reserved,
non-registered id ``prefreeze-pilot`` (R16), because Gate 0 must certify the
apparatus the confirmatory run will actually use.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

STUDY_ID = "dci1-v2"
#: Reserved tree ids under a model slug. Every directory at that level is one
#: of: the pre-freeze apparatus results, the Gate-0 pilot tree, or a real
#: 12-hex freeze_id (confirmatory).
PREFREEZE_PILOT_ID = "prefreeze-pilot"
PREFREEZE_APPARATUS_ID = "prefreeze-apparatus"
#: Reserved model slug for non-model synthetic apparatus checks
#: (smoke, blind dry run). Reserved slugs start with an underscore.
SYNTHETIC_SLUG = "_synthetic"

EVIDENCE_BASE = Path(__file__).resolve().parents[3] / "evidence"
DURABLE_BASE = Path(__file__).resolve().parents[3] / "durable_root"

#: The raw layers retained indefinitely and replicated before selection (R25).
RAW_LAYERS = ("prompts", "cache", "selection")


def model_apparatus_dir(model_key: str) -> Path:
    """Working home of a model's pre-freeze apparatus results
    (qualification, calibration, gate records, run record, pilot report)."""
    return EVIDENCE_BASE / STUDY_ID / model_key / PREFREEZE_APPARATUS_ID


def durable_apparatus_dir(model_key: str) -> Path:
    return DURABLE_BASE / STUDY_ID / model_key / PREFREEZE_APPARATUS_ID


def synthetic_dir(name: str) -> Path:
    """Working home of one synthetic apparatus check ('smoke', 'dryrun')."""
    return EVIDENCE_BASE / STUDY_ID / SYNTHETIC_SLUG / name


@dataclass(frozen=True)
class StudyTree:
    """All addendum paths for one (study, model, freeze_id)."""

    model_slug: str
    freeze_id: str
    study_id: str = STUDY_ID
    base: Path = EVIDENCE_BASE
    #: Follows ``base`` overrides in tests so no test ever touches the real
    #: durable mirror.
    durable_base: Path = DURABLE_BASE

    @property
    def root(self) -> Path:
        return Path(self.base) / self.study_id / self.model_slug / self.freeze_id

    @property
    def freeze_record(self) -> Path:
        return self.root / "freeze_record.json"

    @property
    def prompts_dir(self) -> Path:
        return self.root / "prompts"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @property
    def cache_file(self) -> Path:
        return self.cache_dir / "generations.jsonl"

    @property
    def selection_dir(self) -> Path:
        return self.root / "selection"

    @property
    def primary_selection(self) -> Path:
        return self.selection_dir / "primary" / "primary_selection.jsonl"

    def pseudo_selection(self, run_index: int) -> Path:
        return (self.selection_dir / "pseudo_runs"
                / f"pseudo_run_{run_index:04d}.jsonl")

    @property
    def derived_primary(self) -> Path:
        return self.root / "derived" / "primary"

    def derived_pseudo(self, run_index: int) -> Path:
        return self.root / "derived" / "pseudo_runs"

    @property
    def masking_dir(self) -> Path:
        return self.root / "masking"

    @property
    def mask_key(self) -> Path:
        return self.masking_dir / "mask_key.sealed.json"

    @property
    def masked_view(self) -> Path:
        return self.masking_dir / "masked_view"

    @property
    def commitment(self) -> Path:
        return self.masking_dir / "commitment.json"

    @property
    def unmasking_record(self) -> Path:
        return self.masking_dir / "unmasking_record.json"

    @property
    def integrity_dir(self) -> Path:
        return self.root / "integrity"

    @property
    def study_manifest(self) -> Path:
        return self.root / "study_manifest.json"

    @property
    def durable_root(self) -> Path:
        return (Path(self.durable_base) / self.study_id / self.model_slug
                / self.freeze_id)

    def stage_dir(self, stage: str) -> Path:
        return {"prompts": self.prompts_dir, "cache": self.cache_dir,
                "selection": self.selection_dir,
                "masking": self.masking_dir}[stage]
