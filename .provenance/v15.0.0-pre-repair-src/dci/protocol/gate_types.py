"""gate_types — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
from dci.statuses import GateStatus


@dataclass
class GateOutcome:
    gate: str
    status: str
    reason: str
    quantities: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    more_data_could_resolve: bool = False
    new_protocol_version_required: bool = False
    dry_run_bypassed: bool = False
    recorded_utc: str = ""

    @property
    def passed(self) -> bool:
        return self.status == GateStatus.PASS

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "passed": self.passed}
