"""Append-only human records: hash-chained writes, prefix pinning, and a
schema that cannot express an operational failure as a semantic label.

Two independent integrity layers, because the two problems differ:

*chain*   Every record written from now on carries ``prev_sha256`` — the
          SHA-256 of the record file's bytes *before* that line was
          appended — and ``record_sha256`` over its own canonical JSON.
          Replaying the file recomputes both, so any edit to, deletion
          of, or reordering of an earlier line breaks every later link.
          The chain starts from whatever the file already contains, so it
          can be adopted mid-file without rewriting existing labels.

*pin*     ``records/digests.jsonl`` is an append-only log of
          ``{file, lines, sha256}`` prefix pins.  Verification requires
          the first ``lines`` lines of the file to still hash to
          ``sha256``; appends are allowed, edits are not.  This is the
          only mechanism available for records written before chaining
          existed (the initial 56): pinning cannot prove they were
          unedited *before* the pin, and says so.

Label vocabulary is fixed at SATISFIES / VIOLATES / UNSURE.  There is
deliberately no operational-failure label: judge statuses, truncation and
generation failures are evidence *about the instrument* and live in the
analysis' operational channel, never in a human record.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LABELS = ("SATISFIES", "VIOLATES", "UNSURE")
SEMANTIC_LABELS = ("SATISFIES", "VIOLATES")
ABSTENTION = "UNSURE"

#: Values a human record must never carry as a label: these are
#: operational states of the *judge* or the *generation*, not judgments.
OPERATIONAL_STATES = ("invalid_output", "refusal", "generation_failure",
                      "unscored", "truncated", "length", "error")

DIGESTS_NAME = "digests.jsonl"


class RecordError(Exception):
    """A record-integrity or schema rule was violated."""


def canonical(row: dict[str, Any]) -> str:
    return json.dumps({k: row[k] for k in sorted(row)
                       if k != "record_sha256"},
                      ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def validate_label(label: Any) -> str:
    if not isinstance(label, str):
        raise RecordError(f"label must be a string, got {type(label)}")
    if label in OPERATIONAL_STATES or label.lower() in OPERATIONAL_STATES:
        raise RecordError(
            f"{label!r} is an operational state, not a semantic judgment; "
            f"operational failures are never recorded as human labels")
    if label not in LABELS:
        raise RecordError(
            f"label {label!r} outside the fixed vocabulary {LABELS}")
    return label


def append_record(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    """Append one chained record.  Returns the row actually written."""
    validate_label(row.get("label"))
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_bytes() if path.exists() else b""
    if existing and not existing.endswith(b"\n"):
        raise RecordError(f"{path} does not end in a newline; refusing to "
                          f"append to a truncated record file")
    chained = dict(row)
    chained["prev_sha256"] = hashlib.sha256(existing).hexdigest()
    chained["record_sha256"] = hashlib.sha256(
        canonical(chained).encode()).hexdigest()
    with path.open("a") as fh:
        fh.write(json.dumps(chained, ensure_ascii=False) + "\n")
    return chained


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def verify_chain(path: Path) -> dict[str, Any]:
    """Replay a record file, verifying every chained link.

    Unchained legacy lines are reported, never rewritten.
    """
    if not path.exists():
        return {"file": path.name, "records": 0, "chained": 0,
                "unchained_legacy": 0}
    raw = [line for line in path.read_text().splitlines() if line.strip()]
    prefix = b""
    chained = unchained = 0
    for index, text in enumerate(raw):
        row = json.loads(text)
        line = (text + "\n").encode()
        if "record_sha256" in row or "prev_sha256" in row:
            expected_prev = hashlib.sha256(prefix).hexdigest()
            if row.get("prev_sha256") != expected_prev:
                raise RecordError(
                    f"{path.name} line {index + 1}: chain broken — "
                    f"earlier records were edited, removed or reordered")
            if row.get("record_sha256") != hashlib.sha256(
                    canonical(row).encode()).hexdigest():
                raise RecordError(
                    f"{path.name} line {index + 1}: record hash mismatch — "
                    f"this record was edited after it was written")
            chained += 1
        else:
            unchained += 1
        prefix += line
    return {"file": path.name, "records": len(raw), "chained": chained,
            "unchained_legacy": unchained}


# ------------------------------------------------------------- prefix pin
def _digests_path(records_dir: Path) -> Path:
    return Path(records_dir) / DIGESTS_NAME


def _prefix_hash(path: Path, lines: int) -> str:
    body = "".join(
        line + "\n" for line in path.read_text().splitlines()[:lines])
    return hashlib.sha256(body.encode()).hexdigest()


def pin_records(records_dir: Path) -> list[dict[str, Any]]:
    """Append a prefix pin for every record file whose current content
    extends (never contradicts) its previous pin."""
    records_dir = Path(records_dir)
    verify_pins(records_dir)                       # refuse to pin over a break
    pins = []
    log = _digests_path(records_dir)
    for path in sorted(records_dir.glob("*.jsonl")):
        if path.name == DIGESTS_NAME:
            continue
        lines = len(path.read_text().splitlines())
        if not lines:
            continue
        pin = {"file": path.name, "lines": lines,
               "sha256": _prefix_hash(path, lines)}
        pins.append(pin)
    with log.open("a") as fh:
        for pin in pins:
            fh.write(json.dumps(pin, sort_keys=True) + "\n")
    return pins


def verify_pins(records_dir: Path) -> dict[str, Any]:
    """Every recorded prefix pin must still hold; appends are allowed."""
    records_dir = Path(records_dir)
    log = _digests_path(records_dir)
    if not log.exists():
        return {"pins": 0, "files": 0}
    seen: set[str] = set()
    pins = [json.loads(line) for line in log.read_text().splitlines()
            if line.strip()]
    for pin in pins:
        path = records_dir / pin["file"]
        if not path.exists():
            raise RecordError(
                f"pinned record file {pin['file']} is missing")
        lines = path.read_text().splitlines()
        if len(lines) < pin["lines"]:
            raise RecordError(
                f"{pin['file']}: {len(lines)} lines but a pin covers "
                f"{pin['lines']} — records were deleted")
        if _prefix_hash(path, pin["lines"]) != pin["sha256"]:
            raise RecordError(
                f"{pin['file']}: pinned prefix of {pin['lines']} records "
                f"no longer matches — earlier labels were edited")
        seen.add(pin["file"])
    return {"pins": len(pins), "files": len(seen)}


def verify_all(records_dir: Path) -> dict[str, Any]:
    """Full integrity check used by the reviewer and the report."""
    records_dir = Path(records_dir)
    files = [p for p in sorted(records_dir.glob("*.jsonl"))
             if p.name != DIGESTS_NAME] if records_dir.exists() else []
    return {"pins": verify_pins(records_dir),
            "chains": [verify_chain(p) for p in files]}
