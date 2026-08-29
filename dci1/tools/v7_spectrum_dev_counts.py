#!/usr/bin/env python3
"""Count distributions behind every exact-count ladder. DEVELOPMENT / DIAGNOSTIC.

    python tools/v7_spectrum_dev_counts.py --tree /path/dci1/evidence/dci1v7 \
        --model qwen3-4b --out reports/dci1v7/difficulty_spectrum_dev/counts

Read-only over the tree it is given. For one replication it streams the
Gate-2 backend runs' ``rows.jsonl`` (the raw generations; scoring is redone
from text as §26 says it may be) and, for every **solo** cell of a Tier-1 or
Tier-2 family and of A, recomputes the family's counted statistic with the
registered counter (``verifiers.statistics.family_statistic``; A's own
``s0_count``) and records the distribution of the count S against the stated
severity q: P(S = q), P(S < q), P(S > q), the mean and the histogram. The
grid runs' unconstrained rows give the natural (load-zero) count distribution
of every statistic on the same topics.

Why this exists: §12.6's ladders are read only as a compliance rate per rung.
Whether a rung fails because the model *undershoots* (writes the word fewer
times than asked), *overshoots* (writes it more often) or ignores the
instruction is invisible in that rate and is exactly what decides whether
nominal severity can move difficulty (Phase 5 of the 2026-08-29
difficulty-spectrum investigation). Nothing under the tree is written.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics as st
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.verifiers.target import s0_count  # noqa: E402
from dci1v7.verifiers.constraints import FAMILIES  # noqa: E402
from dci1v7.verifiers.statistics import (  # noqa: E402
    STATISTICS, family_statistic, word_count,
)

TIER12 = [k for k, f in FAMILIES.items() if f.structural_tier in (1, 2)
          and not f.probe_only]
NATURAL_STATS = sorted({FAMILIES[k].statistic_id for k in TIER12})


def _summ(counts: list[int], q: int | None, words: list[int]) -> dict:
    n = len(counts)
    hist = collections.Counter(counts)
    out = {
        "n": n,
        "mean": (sum(counts) / n) if n else None,
        "sd": (st.pstdev(counts) if n > 1 else None),
        "histogram": {str(k): v for k, v in sorted(hist.items())},
        "median_words": (st.median(words) if words else None),
    }
    if q is not None and n:
        out.update({
            "q": q,
            "p_exact": hist.get(q, 0) / n,
            "p_under": sum(v for k, v in hist.items() if k < q) / n,
            "p_over": sum(v for k, v in hist.items() if k > q) / n,
            "p_zero": hist.get(0, 0) / n,
            "p_within_1": sum(v for k, v in hist.items()
                              if abs(k - q) <= 1) / n,
            "mean_minus_q": (sum(counts) / n) - q,
        })
    return out


def run(tree: pathlib.Path, model: str) -> dict:
    g2 = tree / model / "GATE_2_FOCAL_CALIBRATION" / "backend_runs"
    t0 = time.time()
    solo: dict[tuple[str, int], list[int]] = collections.defaultdict(list)
    solo_words: dict[tuple[str, int], list[int]] = collections.defaultdict(list)
    solo_split: dict[tuple[str, int, str], list[int]] = collections.defaultdict(list)
    natural: dict[str, list[int]] = collections.defaultdict(list)
    natural_words: list[int] = []
    n_rows = 0
    for run_dir in sorted(g2.iterdir()):
        path = run_dir / "rows.jsonl"
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if r.get("outcome") != "OK":
                    continue
                n_rows += 1
                text = r.get("raw_generation") or ""
                cell = r["cell_id"]
                if cell == "unconstrained":
                    for sid in NATURAL_STATS:
                        natural[sid].append(STATISTICS[sid](text))
                    natural["marker_however"].append(s0_count(text))
                    natural_words.append(word_count(text))
                    continue
                if not cell.startswith("solo:"):
                    continue
                _, kind, sev = cell.split(":")
                sev = int(sev)
                if kind == "A":
                    s = s0_count(text)
                elif kind in TIER12:
                    s = family_statistic(kind, text)
                else:
                    continue
                solo[(kind, sev)].append(s)
                solo_words[(kind, sev)].append(word_count(text))
                solo_split[(kind, sev, r.get("topic_split"))].append(s)
    out = {
        "model_key": model, "tree": str(tree), "n_rows_read": n_rows,
        "seconds": round(time.time() - t0, 1),
        "natural": {sid: _summ(v, None, natural_words)
                    for sid, v in natural.items()},
        "solo": {},
    }
    for (kind, sev), counts in sorted(solo.items()):
        entry = _summ(counts, sev, solo_words[(kind, sev)])
        entry["by_split"] = {
            sp: _summ(solo_split[(kind, sev, sp)], sev, [])
            for sp in ("calibration_a", "calibration_b")
            if (kind, sev, sp) in solo_split}
        out["solo"][f"{kind}:{sev}"] = entry
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out_dir = pathlib.Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    res = run(pathlib.Path(a.tree), a.model)
    path = out_dir / f"counts_{a.model}.json"
    with open(path, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(f"{a.model}: {res['n_rows_read']} rows in {res['seconds']} s -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
