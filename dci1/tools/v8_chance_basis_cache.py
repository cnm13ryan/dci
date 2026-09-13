#!/usr/bin/env python3
"""Build the §13.2 chance-basis cache for the twelve stored replications
(read-only over the evidence root; writes only under reports/dci1v8dev/).

    python3 tools/v8_chance_basis_cache.py --evidence /path/to/dci1/evidence \
        [--workers 4] [--verify]

One pass per replication over the grid runs' unconstrained rows; the cache
is what every v8 backtest reads instead of the recorded (zero) column.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v8dev import chance_basis as CB          # noqa: E402
from dci1v8dev.backtest import REPLICATIONS       # noqa: E402

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v8dev" / CB.CACHE_DIRNAME


def _one(job):
    tree, model, rel, evidence, out, verify = job
    t0 = time.time()
    model_dir = Path(evidence) / rel
    if not (model_dir / "GATE_2_FOCAL_CALIBRATION" / "gate2_focal_calibration.json").exists():
        return {"tree": tree, "model": model, "skipped": "no Gate-2 record"}
    cache = CB.build_cache(model_dir, tree=tree, model=model)
    path = CB.write_cache(cache, Path(out))
    result = {"tree": tree, "model": model, "path": str(path),
              "n_labels": len(cache["chance"]),
              "n_unconstrained_rows": cache["n_unconstrained_rows"],
              "seconds": round(time.time() - t0, 1)}
    if verify:
        labels = sorted(cache["chance"])
        sample = [labels[0], labels[len(labels) // 3], labels[2 * len(labels) // 3],
                  labels[-1]] + [f"A:{q}" for q in (1, 8) if f"A:{q}" in cache["chance"]]
        result["verified"] = CB.verify_against_cell_rates(
            model_dir / "GATE_2_FOCAL_CALIBRATION", cache, sorted(set(sample)))["n"]
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    jobs = [(t, m, rel, args.evidence, args.out, args.verify)
            for t, m, rel in REPLICATIONS]
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for r in ex.map(_one, jobs):
            results.append(r)
            print(json.dumps(r), flush=True)
    summary = {"generated_by": "tools/v8_chance_basis_cache.py", "read_only": True,
               "evidence_root": args.evidence, "results": results,
               "seconds": round(time.time() - t0, 1)}
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "INDEX.json").write_text(json.dumps(summary, indent=1))
    print("written", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
