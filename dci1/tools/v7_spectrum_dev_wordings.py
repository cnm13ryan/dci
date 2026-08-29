#!/usr/bin/env python3
"""Exact-count compliance split by frozen wording index. DEVELOPMENT / DIAGNOSTIC.

    python tools/v7_spectrum_dev_wordings.py --tree /path/dci1/evidence/dci1v7 \
        --model gemma-3n-e2b-it --out reports/dci1v7/difficulty_spectrum_dev/counts

Read-only. §8.4 allocates one of the four frozen wordings per row. For every
solo cell of A and of each Tier-1 marker family this streams the Gate-2
``rows.jsonl``, identifies which of the four wordings the rendered prompt
carries (§7.8: the Tier-1 wordings are A's four templates with the marker
substituted), recomputes the count with the registered counter, and reports
P(S = q) and P(S = 0) per wording index. A large gap between wordings of one
family at one severity is a property of the *prose*, not of the count, and
is the hypothesis this script exists to test: templates 0–2 ("Use the word
instead exactly 1 time.") admit a parse in which the marker modifies the
instruction, template 3 ("The word instead must appear exactly 1 time.")
does not. Nothing under the tree is written.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.verifiers.target import s0_count  # noqa: E402
from dci1v7.protocol.wordings import wordings  # noqa: E402
from dci1v7.verifiers.constraints import FAMILIES  # noqa: E402
from dci1v7.verifiers.statistics import family_statistic  # noqa: E402

KINDS = ["A"] + [k for k, f in FAMILIES.items() if f.structural_tier == 1]


def run(tree: pathlib.Path, model: str) -> dict:
    g2 = tree / model / "GATE_2_FOCAL_CALIBRATION" / "backend_runs"
    hits: dict[tuple[str, int, int], list[int]] = collections.defaultdict(list)
    unmatched = collections.Counter()
    for run_dir in sorted(g2.iterdir()):
        path = run_dir / "rows.jsonl"
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                cell = r["cell_id"]
                if r.get("outcome") != "OK" or not cell.startswith("solo:"):
                    continue
                _, kind, sev = cell.split(":")
                if kind not in KINDS:
                    continue
                sev = int(sev)
                prompt = r["rendered_prompt"]
                idx = None
                for i, w in enumerate(wordings(kind, sev)):
                    if w in prompt:
                        idx = i
                        break
                if idx is None:
                    unmatched[f"{kind}:{sev}"] += 1
                    continue
                text = r.get("raw_generation") or ""
                s = s0_count(text) if kind == "A" else family_statistic(kind, text)
                hits[(kind, sev, idx)].append(s)
    out: dict = {"model_key": model, "unmatched": dict(unmatched), "cells": {}}
    for (kind, sev, idx), counts in sorted(hits.items()):
        n = len(counts)
        out["cells"].setdefault(f"{kind}:{sev}", {})[str(idx)] = {
            "n": n, "wording": wordings(kind, sev)[idx],
            "p_exact": sum(1 for c in counts if c == sev) / n,
            "p_zero": sum(1 for c in counts if c == 0) / n,
            "p_over": sum(1 for c in counts if c > sev) / n,
            "mean": sum(counts) / n,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = run(pathlib.Path(a.tree), a.model)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"wordings_{a.model}.json", "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(a.model, "unmatched:", res["unmatched"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
