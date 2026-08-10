#!/usr/bin/env python3
"""Print raw generations for a human to read. No classifier, no judge.

Every round of this study has found something in the raw text that no summary
column showed: the 180-token cap, the content-dictating background, the fact
that `S_SEMICOLON`'s passing answers carry MORE semicolons than its failing
ones. A table cannot surface a failure mode nobody thought to count, so each new
run gets read.

The sample is deterministic (fixed seed, sorted row ids) so that "I looked at
these" is a reproducible claim, and it is stratified by cell so that a rare arm
is not crowded out by a common one.

    python inspect_raw.py runs/<dir> --per-cell 2
    python inspect_raw.py runs/<dir> --arm X_COLON_EACH --only-failures
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))


def main(argv: list[str] | None = None) -> int:
    from dci_exploratory.mechanism import load, legacy_split_sentences
    from dci.verifiers.rules import split_sentences

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--per-cell", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260811)
    parser.add_argument("--arm", default=None, help="restrict to one arm")
    parser.add_argument("--scaffold", default=None)
    parser.add_argument("--order", default=None)
    parser.add_argument("--only-failures", action="store_true")
    parser.add_argument("--only-passes", action="store_true")
    parser.add_argument("--condition", default="focal,reference")
    args = parser.parse_args(argv)

    frame, config = load(args.run_dir)
    n_target = frame.attrs["n_target"]
    frame = frame[frame["condition"].isin(args.condition.split(","))]
    for column, value in (("arm", args.arm), ("scaffold", args.scaffold),
                          ("order", args.order)):
        if value is not None:
            frame = frame[frame[column] == value]
    if args.only_failures:
        frame = frame[frame["a_failure"] == 1]
    if args.only_passes:
        frame = frame[frame["a_failure"] == 0]

    rng = random.Random(args.seed)
    print(f"# raw sample — {Path(args.run_dir).name}")
    print(f"# target={config['selection']['target']} n_target={n_target} "
          f"rows_in_scope={len(frame)} per_cell={args.per_cell} seed={args.seed}\n")

    for key, group in frame.groupby(["scaffold", "order", "arm"], dropna=False):
        rows = group.sort_values("row_id")
        picked = rng.sample(range(len(rows)), min(args.per_cell, len(rows)))
        for index in sorted(picked):
            row = rows.iloc[index]
            print("=" * 78)
            print(f"{key}  task={row['task_id']}  rep={row['replicate']}  "
                  f"row={row['row_id']}")
            print(f"  a_failure={row['a_failure']} status={row['verifier_status']} "
                  f"arm_pass={row.get('arm_binary_pass')} "
                  f"n_sentences={row.get('n_sentences')} "
                  f"(legacy {row.get('n_sentences_legacy')}) "
                  f"periods={row.get('n_periods')} semis={row.get('n_semicolons')} "
                  f"colons={row.get('n_colons')} dashes={row.get('n_dashes')} "
                  f"commas={row.get('n_commas')} newlines={row.get('n_newlines')} "
                  f"words={row.get('n_words')} trunc={row.get('output_truncated')}")
            print("-" * 78)
            print(row["response"])
            print("-" * 78)
            segments = split_sentences(row["response"] or "")
            for i, segment in enumerate(segments, 1):
                print(f"  [{i}] {segment[:150]}")
            legacy = legacy_split_sentences(row["response"] or "")
            if len(legacy) != len(segments):
                print(f"  !! legacy segmenter would say {len(legacy)}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
