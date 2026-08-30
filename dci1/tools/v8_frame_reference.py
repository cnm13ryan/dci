#!/usr/bin/env python3
"""Emit `reports/dci1v8dev/frame_reference.json`: the v7 frames' marker-absent
shares per model --- a **descriptive report** of the historical instrument.

Researcher decision (2026-08-30): no v8 pilot verdict reads this file. The
pilot's wording diagnostic is v8-internal (``dci1v8dev/run/wording.py``);
these numbers stay here as the historical context a reader may want beside
it, and nothing in ``dci1v8dev.run`` imports or binds them.

    python3 tools/v8_frame_reference.py            # write
    python3 tools/v8_frame_reference.py --check    # fail if it would change

Read from `reports/dci1v8dev/prescreen/wording_audit.json` (the stored-row
audit of the v7 frames on the signed v6/v7 trees and the rehearsals): per
model and per tree, over every A and MK solo row, the share of rows whose
marker statistic is 0 under each of the four frames. The pilot manifest binds
the reference tree is the registered v7 replication where one exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

AUDIT = HERE.parent / "reports" / "dci1v8dev" / "prescreen" / "wording_audit.json"
OUT = HERE.parent / "reports" / "dci1v8dev" / "frame_reference.json"
PREFERRED_TREES = ("v7", "v6", "r4", "r3", "dev")


def build() -> dict:
    audit = json.loads(AUDIT.read_text())
    per: dict[str, dict[str, dict[int, list[int]]]] = {}
    for result in audit["results"]:
        model, tree = result["model"], result["tree"]
        acc = per.setdefault(model, {}).setdefault(
            tree, {w: [0, 0] for w in range(4)})
        for entry in result["scan"].values():
            if entry["kind"] == "B":
                continue
            w = int(entry["wording"])
            acc[w][0] += int(entry["histogram"].get("0", 0))
            acc[w][1] += int(entry["n"])
    models = {}
    for model, trees in sorted(per.items()):
        by_tree = {}
        for tree, acc in sorted(trees.items()):
            shares = {str(w): (a / n if n else None) for w, (a, n) in acc.items()}
            n_rows = {str(w): n for w, (_, n) in acc.items()}
            best = min((s for s in shares.values() if s is not None), default=None)
            by_tree[tree] = {"marker_absent_share": shares, "n_rows": n_rows,
                             "best_share": best,
                             "best_frames": [w for w, s in shares.items()
                                             if s is not None and s == best]}
        reference_tree = next((t for t in PREFERRED_TREES if t in by_tree), None)
        models[model] = {"by_tree": by_tree, "reference_tree": reference_tree,
                         "best_v7_frame_share": (by_tree[reference_tree]["best_share"]
                                                 if reference_tree else None),
                         "best_v7_frames": (by_tree[reference_tree]["best_frames"]
                                            if reference_tree else [])}
    return {
        "generated_by": "dci1/tools/v8_frame_reference.py",
        "source": str(AUDIT.relative_to(HERE.parent.parent)),
        "source_sha256": hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
        "statistic": "share of A and MK1-8 solo rows (every severity, every "
                     "tree) whose marker statistic is 0, per wording index",
        "v7_frames": list(audit["frames"]),
        "models": models,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is stale", file=sys.stderr)
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
