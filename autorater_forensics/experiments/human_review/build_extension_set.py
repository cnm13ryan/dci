"""Build one human-calibration EXTENSION batch (PREREGISTERED.md E5).

    .venv/bin/python experiments/human_review/build_extension_set.py \
        --batch 1 --pass-target 52 --fail-target 52 --boundary 8

Writes ``experiments/human_review/extension_batch_<k>.json`` **once**:
a batch that already exists is never overwritten, because the design of a
batch must not change after a human has started labelling it.

READ-ONLY over registered evidence and over the SEALED reserved
final-check set (whose ids are used solely to subtract, and whose SHA-256
is recorded in the manifest and re-checked afterwards).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sampling                                    # noqa: E402

#: Cumulative per-class target: 52 clean labels per verifier class gives a
#: one-sided 95% Wilson upper bound of 4.95% (<= 5%); 25 gives 10.0%.
DEFAULT_CLASS_TARGET = 52
DEFAULT_BOUNDARY_PER_CLASS = 8


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--pass-target", type=int,
                    default=DEFAULT_CLASS_TARGET,
                    help="cumulative representative labels wanted in the "
                         "verifier-pass class")
    ap.add_argument("--fail-target", type=int,
                    default=DEFAULT_CLASS_TARGET,
                    help="cumulative representative labels wanted in the "
                         "verifier-fail class")
    ap.add_argument("--boundary", type=int,
                    default=DEFAULT_BOUNDARY_PER_CLASS,
                    help="purposive boundary items per class (0 disables "
                         "the stress component)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out = HERE / f"extension_batch_{args.batch}.json"
    if out.exists() and not args.dry_run:
        raise SystemExit(
            f"{out.name} already exists; a batch is write-once so its "
            f"design cannot change once labelling has begun")

    before = sampling.sealed_digest()
    manifest = sampling.build_extension(
        args.batch,
        class_targets={"pass": args.pass_target,
                       "fail": args.fail_target},
        boundary_per_class=args.boundary)
    if sampling.sealed_digest() != before:
        raise SystemExit("the sealed reserved set changed during the "
                         "build; refusing to write")

    text = json.dumps(manifest, indent=1) + "\n"
    if args.dry_run:
        print(text)
    else:
        out.write_text(text)

    rep = [s for s in manifest["samples"]
           if s["component"] == "representative"]
    bnd = [s for s in manifest["samples"] if s["component"] == "boundary"]
    print(f"{out.name}: {len(manifest['samples'])} new items "
          f"({len(rep)} representative, {len(bnd)} boundary)"
          + ("  [dry run, not written]" if args.dry_run else ""))
    print(f"  eligible pool          {manifest['eligible_size']} of "
          f"{manifest['population_size']}")
    print(f"  excluded               {manifest['excluded']} "
          f"(+{manifest['excluded_prior_batches']} prior batches)")
    print(f"  representative alloc   {manifest['representative_allocation']}")
    print(f"  boundary realised      {manifest['boundary_realised']}")
    print(f"  seed                   {manifest['seed']} "
          f"({manifest['seed_domain']})")


if __name__ == "__main__":
    main()
