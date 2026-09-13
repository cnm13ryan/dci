"""Sequestered-topic access control (§6.2, §25, §30).

The 96 sequestered v4 topic texts are inaccessible to the v4 package
throughout the study. This module holds only opaque identities, content
hashes and stratum metadata, produced once by the authorised access-control
process (``tools/build_topics_v4.py``). Missing access-control infrastructure
fails closed; nothing here can create, read, or reconstruct sequestered text,
and ``assert_no_materialisation`` proves that no released question collides
with a sequestered hash on every load of the released bank.

The sequestered *source* is retained by the researcher outside the repository
so a future uncontaminated rerun remains possible; the repository, and
therefore every execution path, holds identities only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v4.protocol.constants import SEQUESTERED_PER_AREA, SUBJECT_AREAS

MANIFEST_PATH = (Path(__file__).resolve().parent / "data"
                 / "sequestered_v4.json")

_OPAQUE_FIELDS = {"topic_id", "area", "sha256"}


def load_manifest(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or MANIFEST_PATH
    if not path.exists():
        raise ProtocolError(
            "sequestered access-control manifest is missing; v4 fails closed "
            "without it")
    entries = json.loads(path.read_text())
    per_area: dict[str, int] = {}
    seen: set[str] = set()
    for entry in entries:
        extra = sorted(set(entry) - _OPAQUE_FIELDS)
        if extra:
            raise ProtocolError(
                f"sequestered entry {entry.get('topic_id')!r} carries "
                f"non-opaque fields {extra}; sequestered text must never be "
                f"materialised")
        if entry["area"] not in SUBJECT_AREAS:
            raise ProtocolError(f"{entry['topic_id']}: undeclared stratum")
        if entry["topic_id"] in seen:
            raise ProtocolError(f"duplicate sequestered id "
                                f"{entry['topic_id']!r}")
        seen.add(entry["topic_id"])
        if not (isinstance(entry["sha256"], str)
                and len(entry["sha256"]) == 64):
            raise ProtocolError(f"{entry['topic_id']}: malformed content hash")
        per_area[entry["area"]] = per_area.get(entry["area"], 0) + 1
    for area in SUBJECT_AREAS:
        if per_area.get(area, 0) != SEQUESTERED_PER_AREA:
            raise ProtocolError(
                f"{area!r} has {per_area.get(area, 0)} sequestered entries, "
                f"not {SEQUESTERED_PER_AREA}")
    return entries


def sequestered_ids() -> set[str]:
    return {entry["topic_id"] for entry in load_manifest()}


def assert_no_materialisation(released: list[dict[str, Any]]) -> None:
    """No released topic identity or question text may coincide with a
    sequestered identity or content hash. Executed on every bank load."""
    manifest = load_manifest()
    ids = {e["topic_id"] for e in manifest}
    hashes = {e["sha256"] for e in manifest}
    for topic in released:
        if topic["topic_id"] in ids:
            raise ProtocolError(
                f"released topic {topic['topic_id']!r} collides with a "
                f"sequestered identity")
        digest = hashlib.sha256(topic["question"].encode("utf-8")).hexdigest()
        if digest in hashes:
            raise ProtocolError(
                f"released topic {topic['topic_id']!r} materialises "
                f"sequestered text; v4 fails closed")
