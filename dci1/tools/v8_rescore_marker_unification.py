"""Offline rescoring: what the unified v8 marker counter says about every
stored response, against what v7's two rules said.

Reads every ``rows.jsonl`` under an evidence root **read-only**, scores each
row's ``final_answer`` under both rules for A (``however``) and the eight
Tier-1 markers, and records every row on which any count differs, every
verdict flip at every registered severity (A: n in 1..8; MK: q in 1..12),
and per-tree totals. Nothing under the evidence root is written, and the
report is written to ``dci1/reports/dci1v8dev/verifier_unification/``.

    dci1/.venv/bin/python dci1/tools/v8_rescore_marker_unification.py \
        --evidence-root /abs/path/to/dci1/evidence

The worker pool is small and niced so a live GPU run is not contended.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve()
SRC = HERE.parents[1] / "src"
sys.path.insert(0, str(SRC))

from dci1v4.verifiers.target import s0_count                     # noqa: E402
from dci1v7.verifiers.constraints import MARKER_WORDS, TARGET_WORD  # noqa: E402
from dci1v7.verifiers.statistics import marker_count as v7_marker_count  # noqa: E402
from dci1v8dev.verifiers.words import count_marker                  # noqa: E402

A_SEVERITIES = tuple(range(1, 9))
MK_SEVERITIES = tuple(range(1, 13))
I_DOT = "İ"


def _init_worker() -> None:
    try:
        os.nice(19)
    except OSError:                                   # pragma: no cover
        pass


def _score_file(path: str) -> dict:
    rows = bad = missing_text = with_i = differing = 0
    flips: Counter = Counter()
    diffs: list[dict] = []
    v7_a_total = v8_a_total = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                bad += 1                              # a partial trailing line
                continue
            rows += 1
            text = d.get("final_answer")
            if text is None:
                missing_text += 1
                text = d.get("raw_generation") or ""
            if I_DOT in text:
                with_i += 1
            v7 = {"A": s0_count(text)}
            v8 = {"A": count_marker(text, TARGET_WORD)}
            v7_a_total += v7["A"]
            v8_a_total += v8["A"]
            for sid, word in MARKER_WORDS.items():
                v7[sid] = v7_marker_count(text, word)
                v8[sid] = count_marker(text, word)
            if v7 != v8:
                differing += 1
                row_flips = []
                for n in A_SEVERITIES:
                    if (v7["A"] == n) != (v8["A"] == n):
                        flips[f"A:{n}"] += 1
                        row_flips.append(f"A:{n}")
                for sid in MARKER_WORDS:
                    for q in MK_SEVERITIES:
                        if (v7[sid] == q) != (v8[sid] == q):
                            flips[f"{sid}:{q}"] += 1
                            row_flips.append(f"{sid}:{q}")
                diffs.append({
                    "row_id": d.get("row_id"), "cell_id": d.get("cell_id"),
                    "block_id": d.get("block_id"), "topic_id": d.get("topic_id"),
                    "v7_counts": {k: v for k, v in v7.items() if v7[k] != v8[k]},
                    "v8_counts": {k: v for k, v in v8.items() if v7[k] != v8[k]},
                    "verdict_flips": row_flips,
                    "context": _context(text),
                })
    return {"path": path, "rows": rows, "undecodable_lines": bad,
            "missing_final_answer": missing_text, "rows_with_u0130": with_i,
            "rows_with_differing_counts": differing,
            "a_count_total_v7": v7_a_total, "a_count_total_v8": v8_a_total,
            "verdict_flips": dict(flips), "differing_rows": diffs}


def _context(text: str, width: int = 40) -> list[str]:
    out = []
    start = 0
    while True:
        i = text.find(I_DOT, start)
        if i < 0:
            return out
        out.append(text[max(0, i - width): i + width + 1])
        start = i + 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--out", type=Path,
                        default=HERE.parents[1] / "reports" / "dci1v8dev" / "verifier_unification"
                        / "verifier_unification_rescore.json")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)

    root = args.evidence_root.resolve()
    files = sorted(str(p) for p in root.rglob("rows.jsonl"))
    if not files:
        raise SystemExit(f"no rows.jsonl under {root}")
    started = time.time()
    with Pool(args.workers, initializer=_init_worker) as pool:
        results = pool.map(_score_file, files, chunksize=1)
    elapsed = time.time() - started

    per_tree: dict[str, dict] = {}
    total_flips: Counter = Counter()
    all_diffs: list[dict] = []
    for r in results:
        tree = Path(r["path"]).relative_to(root).parts[0]
        t = per_tree.setdefault(tree, {"files": 0, "rows": 0,
                                       "undecodable_lines": 0,
                                       "missing_final_answer": 0,
                                       "rows_with_u0130": 0,
                                       "rows_with_differing_counts": 0,
                                       "verdict_flips": Counter()})
        t["files"] += 1
        for k in ("rows", "undecodable_lines", "missing_final_answer",
                  "rows_with_u0130", "rows_with_differing_counts"):
            t[k] += r[k]
        t["verdict_flips"].update(r["verdict_flips"])
        total_flips.update(r["verdict_flips"])
        for d in r["differing_rows"]:
            all_diffs.append({"tree": tree,
                              "file": str(Path(r["path"]).relative_to(root)),
                              **d})
    for t in per_tree.values():
        t["verdict_flips"] = dict(t["verdict_flips"])

    report = {
        "tool": str(HERE.relative_to(HERE.parents[2])),
        "evidence_root": str(root),
        "read_only": True,
        "rule_v7_A": "dci1v4.verifiers.target.s0_count: lower-case whole "
                     "text, then alphabetic runs == 'however'",
        "rule_v7_MK": "dci1v7.verifiers.statistics.marker_count: alphabetic "
                      "runs of the text as written, each lower-cased, == marker",
        "rule_v8": "dci1v8dev.verifiers.words.count_marker(text, marker): the "
                   "v7 MK rule, for A and MK1-MK8 alike",
        "severities_checked": {"A": list(A_SEVERITIES),
                               "MK": list(MK_SEVERITIES)},
        "text_field": "final_answer (raw_generation only where absent)",
        "files": len(files),
        "rows": sum(r["rows"] for r in results),
        "undecodable_lines": sum(r["undecodable_lines"] for r in results),
        "missing_final_answer": sum(r["missing_final_answer"] for r in results),
        "rows_with_u0130": sum(r["rows_with_u0130"] for r in results),
        "rows_with_differing_counts": len(all_diffs),
        "verdict_flips_total": sum(total_flips.values()),
        "verdict_flips_by_instrument": dict(sorted(total_flips.items())),
        "per_tree": dict(sorted(per_tree.items())),
        "differing_rows": all_diffs,
        "elapsed_seconds": round(elapsed, 1),
        "workers": args.workers,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps({k: report[k] for k in (
        "files", "rows", "undecodable_lines", "rows_with_u0130",
        "rows_with_differing_counts", "verdict_flips_total",
        "verdict_flips_by_instrument", "elapsed_seconds")}, indent=1))
    print("written:", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
