"""E10 — pre-specified human-escalation triggers and automation
coverage. Triggers (fixed in PREREGISTERED.md before results): cap-stop;
unparseable output; any flip across the 3 identical repeat runs;
surviving configurations disagree; validated Scout pattern; response
length >= P95 of the population or n >= 7.

    .venv/bin/python experiments/escalation.py \
        --primary logs_exp/exp2/high/run1 \
        --repeats logs_exp/exp2/high \
        [--second logs_exp/exp2/medium/run1]

Coverage is reported on the evaluated sample AND re-weighted to the
full 983-item development population using each item's population
stratum share, because the diagnostic sets deliberately over-sample
contested items.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[1]
N_HIGH = 7


def run_meta(log_dir: Path):
    logs = list_eval_logs(str(log_dir))
    log = read_eval_log(sorted(logs, key=lambda l: l.name)[-1])
    out = {}
    for s in log.samples:
        m = s.scores["judge_parse"].metadata
        out[str(s.id)] = {"label": m.get("parsed_label"),
                          "status": m.get("status"),
                          "truncated": m.get("truncated")}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary", required=True)
    ap.add_argument("--repeats")
    ap.add_argument("--second")
    args = ap.parse_args()

    ds = {r["id"]: r for r in map(json.loads,
          (ROOT / "dataset" / "diagnostic.jsonl").read_text()
          .splitlines())}
    words = sorted(r["response_words"] for r in ds.values())
    p95 = words[int(0.95 * len(words))]

    primary = run_meta(Path(args.primary))
    repeats = None
    if args.repeats:
        runs = [run_meta(Path(args.repeats) / f"run{i}")
                for i in (1, 2, 3)
                if (Path(args.repeats) / f"run{i}").exists()]
        if len(runs) == 3:
            repeats = runs
    second = run_meta(Path(args.second)) if args.second else None

    per = {}
    for sid, p in primary.items():
        d = ds.get(sid)
        reasons = []
        if p["truncated"]:
            reasons.append("cap_stop")
        if p["status"] not in ("valid",):
            reasons.append("unparseable_or_failed")
        if repeats and len({(r[sid]["label"], r[sid]["status"])
                            for r in repeats if sid in r}) > 1:
            reasons.append("repeat_flip")
        if second and sid in second and second[sid]["status"] == "valid" \
                and p["status"] == "valid" \
                and second[sid]["label"] != p["label"]:
            reasons.append("configs_disagree")
        if d and (d["response_words"] >= p95 or d["target_n"] >= N_HIGH):
            reasons.append("difficult_range")
        # no Scout pattern is currently VALIDATED as high-risk (the
        # contradiction scanner found 0 hits) -> no scout trigger yet
        per[sid] = reasons
    n = len(per)
    esc = {s: r for s, r in per.items() if r}
    auto = n - len(esc)
    print(f"evaluated samples: {n}; escalated: {len(esc)} "
          f"({len(esc) / n:.1%}); automated: {auto} ({auto / n:.1%})")
    from collections import Counter
    c = Counter(r for rs in esc.values() for r in rs)
    for k, v in c.most_common():
        print(f"  trigger {k}: {v}")
    print("NOTE: this sample over-represents contested items; "
          "population-level coverage must be estimated on "
          "population-representative data (calibration sample or "
          "registered full-round statistics).")
    out = ROOT / "analysis" / "out" / "escalation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"p95_words": p95, "n_high": N_HIGH, "escalated": esc,
         "evaluated": n}, indent=1))


if __name__ == "__main__":
    main()
