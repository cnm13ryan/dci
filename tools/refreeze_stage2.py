#!/usr/bin/env python3
"""Recompute the derivable records in `src/dci/v19/stage2_frozen.json`.

WHY THIS EXISTS
---------------
`stage2_frozen.json` is the artifact trail for Stage 2. Most of its records are
not opinions: each names, in `frozen_by`, the procedure that produced its value,
and the slot's typed domain re-checks that value against the running code at
import. So when an accepted amendment legitimately changes the implementation,
every derived record is stale and the package refuses to import until they are
brought forward.

Until now the only way to do that was to hand-edit JSON. That is the same
hand-transcription path that put a pre-repair sentence-boundary regex into
`v19/text.py` in the first place: a value that claims to have been produced by a
procedure, typed in by a person. This tool runs the procedures instead.

WHAT IT WILL NOT DO
-------------------
Investigator decisions have no producer and are never touched: their value IS the
decision, and regenerating one would mean inventing a decision nobody made. They
are listed as `held` so the operator can see what was left alone.

`verifiers.p1.list_policy` sits in between. Amendment A1 is a decision, but the
recorded value is the *implemented* policy state, and the domain enforces exactly
that. So it is derivable, and it is the one record where the operator should read
the diff rather than trust it.

USE
---
    python tools/refreeze_stage2.py                       # dry run, prints a diff
    python tools/refreeze_stage2.py --amendment "..." --execute

`--amendment` is required to write: a changed frozen value is a measurement
amendment, and the note is appended to each affected record's `evidence` so the
file keeps saying why it holds what it holds.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
FROZEN = REPO / "src" / "dci" / "v19" / "stage2_frozen.json"


def producers() -> dict[str, Callable[[], Any]]:
    """Slot -> the procedure its `frozen_by` names.

    Imported lazily and inside the function so that this module can be read, and
    its --help printed, even while the package refuses to import because the very
    records it repairs are stale.
    """
    from dci.v19 import encoding, mutation, review_trigger, solver, verifiers, witness
    from dci.v19.parsing import CANONICAL_LIST_POLICY as P

    def solver_state() -> dict[str, str]:
        # `solver_identity()` returns a bare (name, version) tuple while the slot's
        # domain requires a mapping with those keys. The gap used to be closed by
        # whoever typed the record; closing it here is the point of the tool.
        name, version = solver.solver_identity()
        return {"name": name, "version": version}

    return {
        "verifiers.p1.list_policy": P.state,
        "satisfiability.solver_identity": solver_state,
        "satisfiability.encoding_map": lambda: encoding.encoding_map_state(P),
        "satisfiability.witness_constructor": lambda: witness.CONSTRUCTOR_ID,
        "satisfiability.review_trigger": review_trigger.frozen_trigger_evidence,
        "verifiers.specification_bundle": lambda: verifiers.bundle_state(P),
        "verifiers.boundary_mutations": mutation.frozen_battery_evidence,
        "verifiers.bundle_hash": lambda: verifiers.bundle_hash(P),
    }


def _summarise(value: Any, width: int = 88) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return text if len(text) <= width else text[: width - 3] + "..."


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--amendment", default="",
                        help="why the implementation changed; appended to evidence")
    parser.add_argument("--execute", action="store_true",
                        help="write the file (default is a dry run)")
    parser.add_argument("--path", type=Path, default=FROZEN)
    args = parser.parse_args(argv)

    payload = json.loads(args.path.read_text())
    known = producers()

    changed, held, unchanged = [], [], []
    for record in payload["records"]:
        slot = record["slot"]
        if slot not in known:
            held.append(slot)
            continue
        fresh = known[slot]()
        # Round-trip through JSON so tuples/sets compare the way they will be
        # stored, not the way Python happens to hold them.
        fresh = json.loads(json.dumps(fresh, sort_keys=True, default=str))
        if fresh == record["value"]:
            unchanged.append(slot)
            continue
        changed.append((slot, record["value"], fresh))

    print(f"{len(unchanged)} already current, {len(held)} investigator decisions "
          f"held, {len(changed)} to regenerate\n")
    for slot in held:
        print(f"  held      {slot}")
    for slot in unchanged:
        print(f"  current   {slot}")
    for slot, old, new in changed:
        print(f"  REGEN     {slot}\n"
              f"      was   {_summarise(old)}\n"
              f"      now   {_summarise(new)}")

    if not changed:
        print("\nnothing to do")
        return 0
    if not args.execute:
        print("\ndry run; pass --amendment \"...\" --execute to write")
        return 0
    if not args.amendment.strip():
        print("\nrefusing to write without --amendment: a changed frozen value is a "
              "measurement amendment and the file records why", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    fresh_by_slot = {slot: new for slot, _, new in changed}
    for record in payload["records"]:
        if record["slot"] not in fresh_by_slot:
            continue
        record["value"] = fresh_by_slot[record["slot"]]
        record["recorded_at"] = stamp
        record["evidence"] = (
            f"{record['evidence']} REGENERATED {stamp} by tools/refreeze_stage2.py "
            f"after: {args.amendment.strip()}")
    args.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {args.path} ({len(changed)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
