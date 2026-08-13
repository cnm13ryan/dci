"""Stage 2 outputs that have actually been produced, and nothing else.

The registry declares what each stage will produce; this is where a produced value
is recorded so it survives the process that produced it. Without it a Stage 2
artifact could be computed, verified, and then lost - `SlotTable.freeze` returns a
new table, so a freeze that is never written down is a freeze that never happened.

Three properties make the file safe to trust:

  * every record is applied through `Slot.freeze`, so its typed domain runs. A wrong
    value in the file is refused at IMPORT, not at the point some later stage happens
    to read it;
  * a record may only be applied when the slot's own `depends_on` are already
    resolved. Section 14 makes the stage ordering mandatory, and a hand-edited file
    is exactly how an out-of-order freeze would otherwise get in;
  * every record names the procedure that produced it and the evidence that makes it
    valid. `frozen_by` is required by `Slot.freeze`; `evidence` is required here.

What must NOT go in this file: anything a procedure has not actually run. The file is
the artifact trail Appendix J archives, and a value written here is indistinguishable
from a legitimately produced one to everything downstream - which is the whole reason
the domains exist.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from dci.v19.resolution import SlotTable

FROZEN_PATH = Path(__file__).with_name("stage2_frozen.json")

REQUIRED_FIELDS = ("slot", "value", "frozen_by", "recorded_at", "evidence")


class FrozenRecordError(ValueError):
    """A recorded Stage 2 output that cannot be applied as written."""


def records(path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    """The recorded outputs, in the order they were produced."""
    source = path or FROZEN_PATH
    if not source.exists():
        return ()
    payload = json.loads(source.read_text())
    if not isinstance(payload, Mapping) or "records" not in payload:
        raise FrozenRecordError(
            f"{source} must be an object with a 'records' array")
    found = payload["records"]
    if not isinstance(found, Sequence) or isinstance(found, str):
        raise FrozenRecordError(f"{source}: 'records' must be an array")
    for index, record in enumerate(found):
        if not isinstance(record, Mapping):
            raise FrozenRecordError(f"{source}: record {index} is not an object")
        missing = [field for field in REQUIRED_FIELDS if not record.get(field)]
        if missing:
            raise FrozenRecordError(
                f"{source}: record {index} ({record.get('slot', '?')}) is missing "
                f"{missing}. A recorded output states which procedure produced it, "
                "when, and what evidence makes it valid")
    return tuple(found)


def apply(table: SlotTable, path: Path | None = None) -> SlotTable:
    """Freeze every recorded output onto `table`, in dependency order.

    Refuses a record whose slot still has an unresolved prerequisite, so the file
    cannot bypass the ordering section 14 makes mandatory. The domain check happens
    inside `Slot.freeze`, so a value the code cannot reproduce is refused here too.
    """
    for record in records(path):
        name = record["slot"]
        slot = table[name]                       # KeyError if undeclared
        if slot.resolved:
            raise FrozenRecordError(
                f"{name} is already {slot.resolution.value}; a recorded output "
                "cannot re-freeze a value the registry already carries")
        waiting = [dependency for dependency in slot.depends_on
                   if not table[dependency].resolved]
        if waiting:
            raise FrozenRecordError(
                f"{name} is recorded as produced while {waiting} are still "
                "unresolved. Section 14 permits a later stage to consume a frozen "
                "output and not to precede it, so this record is out of order")
        table = table.freeze(name, record["value"], by=record["frozen_by"])
    return table


def audit(path: Path | None = None) -> tuple[dict[str, Any], ...]:
    """One row per recorded output, without its value, for a completion report."""
    return tuple({"slot": record["slot"], "frozen_by": record["frozen_by"],
                  "recorded_at": record["recorded_at"],
                  "evidence": record["evidence"]}
                 for record in records(path))
