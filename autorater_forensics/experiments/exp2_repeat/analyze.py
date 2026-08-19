"""E2 analysis: within-setting repeat instability vs between-setting
disagreement, against the PRE-REGISTERED thresholds (<= 2% within;
effect real only if between >= 3x within).

    .venv/bin/python experiments/exp2_repeat/analyze.py
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[2]
EFFORTS = ("low", "medium", "high")
THRESHOLD = 0.02          # pre-registered
EFFECT_RATIO = 3.0        # pre-registered


def run_labels(log_dir: Path):
    logs = list_eval_logs(str(log_dir))
    if not logs:
        return None
    log = read_eval_log(sorted(logs, key=lambda l: l.name)[-1])
    out = {}
    for s in log.samples:
        m = s.scores["judge_parse"].metadata
        out[str(s.id)] = (m.get("parsed_label"), m.get("status"))
    return out


def main():
    triples = {}
    for effort in EFFORTS:
        runs = []
        for i in (1, 2, 3):
            r = run_labels(ROOT / "logs_exp" / "exp2" / effort
                           / f"run{i}")
            if r:
                runs.append(r)
        if len(runs) == 3:
            triples[effort] = runs
    lines = ["# E2 — repeated-run stability\n",
             "Pre-registered: within-setting instability acceptable "
             f"iff <= {THRESHOLD:.0%}; a between-setting difference is "
             f"a real effect only where between >= {EFFECT_RATIO}x the "
             "larger within.\n"]
    within = {}
    details = {}
    for effort, runs in triples.items():
        ids = sorted(set(runs[0]) & set(runs[1]) & set(runs[2]))
        unstable = [i for i in ids
                    if len({r[i] for r in runs}) > 1]
        within[effort] = len(unstable) / len(ids)
        details[effort] = unstable
        lines.append(f"## {effort}: {len(unstable)}/{len(ids)} samples "
                     f"changed (label,status) across 3 identical runs "
                     f"= {within[effort]:.2%} -> "
                     f"{'PASS' if within[effort] <= THRESHOLD else 'FAIL'}"
                     f" (threshold {THRESHOLD:.0%})")
        for i in unstable:
            lines.append(f"  - {i}: " + " | ".join(
                f"run{k + 1}={r[i][0]}/{r[i][1]}"
                for k, r in enumerate(runs)))

    lines.append("\n## Between-setting disagreement "
                 "(majority label across the 3 runs)\n")

    def majority(runs, i):
        from collections import Counter
        c = Counter(r[i][0] for r in runs)
        return c.most_common(1)[0][0]
    for a, b in itertools.combinations(triples, 2):
        ids = sorted(set(triples[a][0]) & set(triples[b][0]))
        diff = [i for i in ids
                if majority(triples[a], i) != majority(triples[b], i)]
        rate = len(diff) / len(ids)
        floor = EFFECT_RATIO * max(within[a], within[b])
        lines.append(f"- {a} vs {b}: {len(diff)}/{len(ids)} = "
                     f"{rate:.2%}; noise floor {floor:.2%} -> "
                     f"{'REAL EFFECT' if rate >= floor else 'NOT DISTINGUISHABLE FROM NOISE'}")
    out = ROOT / "analysis" / "out" / "exp2_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
