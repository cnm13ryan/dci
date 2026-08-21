"""§12.5's topic-reservation audit, run over rows rather than over source.

The claim "the reserved sets are unspent" is easy to make and easy to get
wrong, because it is a claim about what *ran*, not about what the code says.
This module answers it from the generated rows: every row any v4r3 process has
produced names its topic, the split says which set that topic belongs to, and
the audit reports the tally and refuses if a reserved set appears.

It is deliberately blind to intent. A row is evidence that a topic was used,
whatever the stage label says, and a stage that used a composed-validation
topic outside Gate 4 shows up here as a count rather than as an argument.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from dci1v4.errors import ProtocolError

from dci1v4r4.protocol import constants as C
from dci1v4r4.topics import split_topics

__all__ = ["topic_membership", "audit_rows", "audit_evidence_tree",
           "assert_reserved_sets_unspent", "resolve_stage",
           "STAGE_PERMISSIONS", "STAGE_LABEL_PREFIXES"]

def _stage_labels() -> tuple[str, str, str, str]:
    """The labels the runners actually emit, read from the runners."""
    from dci1v4r4.run.gates_run import STAGE_CALIBRATION
    from dci1v4r4.run.pilot_run import STAGE_PILOT
    from dci1v4r4.run.regime_screen import STAGE_CAP, STAGE_LADDER
    return STAGE_PILOT, STAGE_CAP, STAGE_LADDER, STAGE_CALIBRATION


_PILOT_LABEL, _CAP_LABEL, _LADDER_LABEL, _CALIBRATION_LABEL = _stage_labels()

#: Which registered stage may touch which sets.
STAGE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    C.STAGE_GATE0: ("prescreen",),
    C.STAGE_REGIME: ("prescreen",),
    C.STAGE_GATE1: ("prescreen", "solo"),
    C.STAGE_GATE2: ("solo",),
    C.STAGE_GATE3: ("solo",),
    C.STAGE_GATE4: ("composed",),
    C.STAGE_CONFIRMATORY: ("confirmatory",),
}

#: Row labels carry a run suffix -- the cap under test, the expansion round --
#: so the audit resolves a label to its registered stage by prefix rather than
#: by equality. An unresolved label is reported by name and held to the
#: development sets, so a mislabelled confirmatory run cannot pass by having a
#: name the table does not recognise.
#: The prefixes are **imported from the runners that emit them**, not restated.
#: `v4r3-pilot` was restated here and the runner emits `v4r3-gate0-pilot`, so
#: the first Gate 0 pilot this study ever ran produced 4,512 rows the audit
#: could not place --- and the audit did the right thing, holding an
#: unrecognised label to the development sets and refusing. It refused
#: correctly, but on a name rather than on a topic, and a guard that can be
#: defeated by renaming a stage is a guard about spelling.
STAGE_LABEL_PREFIXES: dict[str, str] = {
    _PILOT_LABEL: C.STAGE_GATE0,
    _CAP_LABEL: C.STAGE_REGIME,
    _LADDER_LABEL: C.STAGE_REGIME,
    _CALIBRATION_LABEL: C.STAGE_GATE2,
    "v4r3-composed-headroom": C.STAGE_GATE4,
    "v4r3-confirmatory": C.STAGE_CONFIRMATORY,
}


def resolve_stage(label: str) -> str | None:
    """The registered stage a row label belongs to, or None."""
    matches = [stage for prefix, stage in STAGE_LABEL_PREFIXES.items()
               if str(label).startswith(prefix)]
    return matches[0] if len(matches) == 1 else (
        max(matches, key=len) if matches else None)


def topic_membership() -> dict[str, str]:
    """topic_id -> the registered set it belongs to."""
    membership: dict[str, str] = {}
    for name, topics in split_topics().items():
        for topic in topics:
            membership[topic["topic_id"]] = name
    return membership


def audit_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Tally the topic set of every row, by stage."""
    membership = topic_membership()
    by_stage: dict[str, dict[str, int]] = {}
    unknown: set[str] = set()
    total = 0
    for row in rows:
        total += 1
        topic = row.get("topic_id")
        stage = row.get("stage", "unknown")
        where = membership.get(topic)
        if where is None:
            # A topic id absent from the released split is either sequestered
            # or not a v4 topic at all. Either way it is reported, never
            # silently bucketed.
            unknown.add(str(topic))
            where = "not_in_released_split"
        by_stage.setdefault(stage, {})
        by_stage[stage][where] = by_stage[stage].get(where, 0) + 1
    unresolved = sorted(label for label in by_stage
                        if resolve_stage(label) is None)
    return {"rows": total, "by_stage": by_stage,
            "resolved_stages": {label: resolve_stage(label)
                                for label in sorted(by_stage)},
            "unresolved_stage_labels": unresolved,
            "topics_not_in_released_split": sorted(unknown)}


def audit_evidence_tree(root: Path) -> dict[str, Any]:
    """Every scored row under ``root``, audited."""
    def _rows():
        for path in sorted(Path(root).rglob("scored.jsonl")):
            for line in path.read_text().splitlines():
                if line.strip():
                    yield json.loads(line)
    report = audit_rows(_rows())
    report["root"] = str(root)
    return report


def assert_reserved_sets_unspent(report: dict[str, Any]) -> dict[str, Any]:
    """§6.2: refuse if any stage used a set it may not use."""
    violations: list[str] = []
    for label, tally in sorted(report["by_stage"].items()):
        stage = resolve_stage(label)
        allowed = (STAGE_PERMISSIONS[stage] if stage in STAGE_PERMISSIONS
                   else C.DEVELOPMENT_TOPIC_SETS)
        for where, count in sorted(tally.items()):
            if where not in allowed:
                violations.append(f"{label} used {count} row(s) from "
                                  f"{where}, which it may not touch")
    if report["unresolved_stage_labels"]:
        violations.append(
            "rows carry stage labels §12.5 does not recognise: "
            f"{report['unresolved_stage_labels']}")
    if report["topics_not_in_released_split"]:
        violations.append(
            "rows name topics absent from the released split: "
            f"{report['topics_not_in_released_split'][:5]}")
    if violations:
        raise ProtocolError("§6.2's reserved sets are not unspent: "
                            + "; ".join(violations))
    return {**report, "reserved_sets_unspent": True,
            "reserved": list(C.RESERVED_TOPIC_SETS)}
