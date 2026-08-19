"""Sequestered-topic access control (§6, §19; implementation-prompt item 19).

The 96 sequestered topic texts are inaccessible throughout v3. This package
holds only opaque identities, pre-existing content hashes, and stratum
metadata, produced once by the authorised access-control process
(tools/build_topics_v3.py). Missing access-control infrastructure fails
closed; nothing here can create, read, or reconstruct sequestered text, and
``assert_no_materialisation`` proves no released text collides with a
sequestered hash.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import SEQUESTERED_PER_AREA, SUBJECT_AREAS

MANIFEST_PATH = (Path(__file__).resolve().parent / "data"
                 / "sequestered_v3.json")

_OPAQUE_FIELDS = {"topic_id", "area", "sha256"}


def load_manifest(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or MANIFEST_PATH
    if not path.exists():
        raise ProtocolError(
            "sequestered access-control manifest is missing; the v3 "
            "implementation fails closed without it")
    entries = json.loads(path.read_text())
    per_area: dict[str, int] = {}
    seen: set[str] = set()
    for entry in entries:
        if set(entry) != _OPAQUE_FIELDS:
            raise ProtocolError(
                f"sequestered entry {entry.get('topic_id')!r} carries "
                f"non-opaque fields {sorted(set(entry) - _OPAQUE_FIELDS)}; "
                f"sequestered text must never be materialised")
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
    """No released topic id or question text may coincide with a
    sequestered identity or content hash (executable §19 control)."""
    manifest = load_manifest()
    ids = {e["topic_id"] for e in manifest}
    hashes = {e["sha256"] for e in manifest}
    for topic in released:
        if topic["topic_id"] in ids:
            raise ProtocolError(
                f"released topic {topic['topic_id']!r} collides with a "
                f"sequestered identity")
        digest = hashlib.sha256(
            topic["question"].encode("utf-8")).hexdigest()
        if digest in hashes:
            raise ProtocolError(
                f"released topic {topic['topic_id']!r} materialises "
                f"sequestered text; v3 fails closed")
