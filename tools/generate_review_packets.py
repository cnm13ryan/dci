#!/usr/bin/env python3
"""Regenerate `docs/v19_stage2_semantic_review_packets.json` from the code.

The packet bundle is the blinded material a human semantic reviewer reads. Its
packet ids are content hashes over the composition, the clause and the witness,
so anything that changes a verifier specification changes the bundle - which is
the point: a reviewer must not be shown packets built by a version of the parser
that is no longer running.

`tests/unit/test_v19_stage2_artifacts.py::test_the_generated_bundle_on_disk_matches_the_generator`
asserts the published file equals what this script writes. Until now nothing
wrote it, so the only way to satisfy that test after an amendment was to edit the
JSON by hand.

    python tools/generate_review_packets.py            # dry run, reports drift
    python tools/generate_review_packets.py --execute
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUBLISHED = REPO / "docs" / "v19_stage2_semantic_review_packets.json"

#: The only fields this tool owns. They are derived from the policy and the
#: compositions, so regenerating them is the whole point.
#:
#: Everything else in the file is prose the investigator wrote onto it and the
#: generator cannot reproduce — the published bundle carries a `stage` marker and
#: a `note` beginning "REHEARSAL, not Stage 2 evidence", which is precisely the
#: declaration that stops the file presenting as something it is not. A first
#: version of this tool wrote `bundle()` out wholesale and destroyed both. Fields
#: outside this set are carried forward from the existing file.
DERIVED_FIELDS = frozenset({
    "packets", "n_packets", "list_policy_hash", "text_policy_hash",
    "unblinding_index",
})


def merge(existing: dict | None, fresh: dict) -> dict:
    """Fresh derived content, with the file's own annotations preserved."""
    if not existing:
        return fresh
    merged = dict(existing)
    for field in DERIVED_FIELDS:
        if field in fresh:
            merged[field] = fresh[field]
        else:                                   # generator stopped producing it
            merged.pop(field, None)
    for field, value in fresh.items():          # new generator fields appear
        merged.setdefault(field, value)
    return merged


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--path", type=Path, default=PUBLISHED)
    args = parser.parse_args(argv)

    from dci.v19 import review_packets as RP
    from dci.v19.parsing import CANONICAL_LIST_POLICY as P

    fresh = RP.bundle(RP.canonical_review_compositions(P), P)
    current = json.loads(args.path.read_text()) if args.path.exists() else None
    target = merge(current, fresh)

    if current == target:
        print(f"{args.path} is current ({target['n_packets']} packets)")
        return 0

    old_ids = [p["packet_id"] for p in (current or {}).get("packets", ())]
    new_ids = [p["packet_id"] for p in target["packets"]]
    print(f"{args.path} is stale\n  packets: {len(old_ids)} -> {len(new_ids)}")
    for old, new in zip(old_ids, new_ids):
        if old != new:
            print(f"    {old} -> {new}")
    kept = sorted(set(target) - DERIVED_FIELDS)
    print(f"  preserved from the file: {kept}")

    if not args.execute:
        print("\ndry run; pass --execute to write")
        return 0
    args.path.write_text(json.dumps(target, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
