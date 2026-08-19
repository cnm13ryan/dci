"""Release assembly (prereg §31) and the machine-readable result table.

The release happens after unmasking; this module enumerates the §31 artifact
list against the evidence tree so nothing can be released incomplete, embeds
the canary string in the released topic file, and withholds the 96 sequestered
topics. The release-time exact-phrase web search of every confirmatory topic
(§24) is an operator step recorded here as pending until run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1.evidence.store import write_json
from dci1.protocol.constants import CANARY_STRING
from dci1.topics.split import split_bank

RELEASE_ARTIFACTS = (
    "topics_released.json", "constraint_wordings.json",
    "freeze/freeze_record.json", "pilot_report.json",
    "qualification_report.json", "calibration/gate2.json",
    "confirmatory/primary/accepted.jsonl",
    "confirmatory/primary/primary_manifest.jsonl",
    "analysis/masked_result.json", "analysis/unmasked_result.json",
    "runrecord.jsonl",
)


def released_topics() -> dict[str, Any]:
    """The 480 released topics with the canary; sequestered withheld (§24)."""
    split = split_bank()
    return {
        "canary": CANARY_STRING,
        "calibration": split["calibration"],
        "confirmatory": split["confirmatory"],
        "sequestered_withheld": len(split["sequestered"]),
    }


def release_manifest(model_dir: Path) -> dict[str, Any]:
    model_dir = Path(model_dir)
    write_json(model_dir / "topics_released.json", released_topics())
    status = {}
    for artifact in RELEASE_ARTIFACTS:
        status[artifact] = (model_dir / artifact).exists()
    manifest = {"artifacts": status,
                "complete": all(status.values()),
                "contamination_search": "PENDING_OPERATOR",
                "canary": CANARY_STRING}
    write_json(model_dir / "release_manifest.json", manifest)
    return manifest
