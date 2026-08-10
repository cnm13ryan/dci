"""exceptions — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
from dci.protocol.gate_types import GateOutcome  # noqa: F401


class StudyStop(RuntimeError):
    """A preregistered stopping condition. Carries the machine-readable outcome."""

    def __init__(self, outcome: GateOutcome, message: str = ""):
        self.outcome = outcome
        super().__init__(message or f"{outcome.gate}: {outcome.status} — {outcome.reason}")


class LineageViolation(RuntimeError):
    """A construction was handed an object carrying a forbidden taint."""


class CacheIntegrityError(RuntimeError):
    """Raised when the journal cannot be trusted to represent the design."""


class FrozenPlanMismatch(RuntimeError):
    """Raised when an existing frozen artefact disagrees with the current one."""


class TaskBankInsufficient(RuntimeError):
    """A stage asked for more task clusters than its bank can supply."""


class SensitivityNotEstimable(RuntimeError):
    """No caliper can be derived from outcome sensitivity at this size."""
