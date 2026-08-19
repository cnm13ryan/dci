"""The append-only amendment register (§31).

One register carries each amendment's text, its timing relative to every
affected artifact, what it supersedes and what it leaves untouched. Before the
study-wide freeze a change is a revision of the preregistration and is
prospective by definition; after it, only operational settings that cannot
change a scientific quantity may move, with a recorded environment note, and
every other change creates v5.

**An amendment is never used to weaken a criterion so a gate passes.** That is
enforced here: an entry that weakens a registered threshold, region,
precondition or caliper and cites a gate outcome as its reason is refused.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Sequence

from dci1v4.engine import fs
from dci1v4.errors import ProtocolError

WEAKENING_MARKERS = ("so that the gate passes", "to make the gate pass",
                     "to admit", "to allow the replication to continue",
                     "because the gate failed")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def record_amendment(path: Path, *, text: str, kind: str,
                     supersedes: Sequence[str], leaves_untouched: Sequence[str],
                     affected_artifacts: Sequence[str],
                     before_study_freeze: bool,
                     weakens_criterion: bool = False,
                     environment_note: str | None = None) -> dict[str, Any]:
    """Append one amendment. Refuses a criterion-weakening amendment."""
    if kind not in ("revision", "operational", "protocol_version"):
        raise ProtocolError(f"unknown amendment kind {kind!r}")
    lowered = text.lower()
    if weakens_criterion or any(m in lowered for m in WEAKENING_MARKERS):
        raise ProtocolError(
            "an amendment is never used to weaken a criterion in order to "
            "make a gate pass (§31); this entry is refused")
    if not before_study_freeze and kind == "revision":
        raise ProtocolError(
            "after the study-wide freeze a scientific revision is not an "
            "amendment; it creates v5 (§31)")
    if kind == "operational" and not environment_note:
        raise ProtocolError(
            "an operational change after the freeze requires a recorded "
            "environment note (§31)")
    entry = fs.row_with_hash({
        "recorded_at": _now(), "kind": kind, "text": text,
        "supersedes": list(supersedes),
        "leaves_untouched": list(leaves_untouched),
        "affected_artifacts": list(affected_artifacts),
        "timing": ("before the study-wide freeze; prospective by definition"
                   if before_study_freeze else "after the study-wide freeze"),
        "environment_note": environment_note,
    })
    fs.append_jsonl(Path(path), entry)
    return entry


def read_register(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    rows = fs.read_jsonl(path)
    for row in rows:
        fs.verify_row_hash(row, where=f"amendment:{row.get('recorded_at')}")
    return rows
