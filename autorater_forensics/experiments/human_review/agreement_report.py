"""E8 — human-vs-model agreement report, per the pre-registered
measurement rules (PREREGISTERED.md E7/E8). Refuses synthetic records
unless --allow-synthetic (dry-run self-test only).

    .venv/bin/python experiments/human_review/agreement_report.py \
        --records experiments/human_review/records/calibration_X.jsonl \
        --config high=logs_exp/exp2/high/run1 \
        --config medium=logs_exp/exp2/medium/run1

Config sources: an Inspect log dir, or a JSONL with
{"sample_id"/"id", "label", "status"} rows (offline-path output).
Rules enforced here: UNSURE human judgments are abstentions (excluded
from agreement, counted and reported); non-valid judge statuses count
against coverage and are NEVER converted to VIOLATES; agreement is
computed only over (human in {SATISFIES,VIOLATES}) x (judge valid);
config pairs are compared ONLY on shared human-labelled items with
discordant counts.
"""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H2J = {"SATISFIES": "pass", "VIOLATES": "fail"}


def load_config_labels(source: str) -> dict[str, dict]:
    p = Path(source)
    if p.is_dir():
        from inspect_ai.log import list_eval_logs, read_eval_log
        logs = list_eval_logs(str(p))
        log = read_eval_log(sorted(logs, key=lambda l: l.name)[-1])
        return {str(s.id): {
            "label": s.scores["judge_parse"].metadata.get("parsed_label"),
            "status": s.scores["judge_parse"].metadata.get("status")}
            for s in log.samples}
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    return {r.get("sample_id", r.get("id")): {
        "label": r["label"], "status": r["status"]} for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--config", action="append", required=True,
                    metavar="NAME=SOURCE")
    ap.add_argument("--allow-synthetic", action="store_true")
    args = ap.parse_args()

    records = [json.loads(l) for l in
               Path(args.records).read_text().splitlines()]
    if any(r.get("synthetic") for r in records) \
            and not args.allow_synthetic:
        raise SystemExit("records contain synthetic (self-test) "
                         "judgments — not usable as human evidence")
    human = {r["id"]: r["label"] for r in records}
    labelled = {i: l for i, l in human.items() if l != "UNSURE"}
    unsure = sum(1 for l in human.values() if l == "UNSURE")

    configs = {}
    for spec in args.config:
        name, source = spec.split("=", 1)
        configs[name] = load_config_labels(source)

    lines = [f"# Human-agreement report",
             f"\n- human records: {len(human)} "
             f"({len(labelled)} labelled, {unsure} UNSURE abstentions)"]
    per_valid = {}
    for name, judge in configs.items():
        ids = sorted(set(labelled) & set(judge))
        valid = [i for i in ids if judge[i]["status"] == "valid"]
        correct = [i for i in valid
                   if judge[i]["label"] == H2J[labelled[i]]]
        by_class = {}
        for cls in ("SATISFIES", "VIOLATES"):
            cls_ids = [i for i in valid if labelled[i] == cls]
            cls_ok = [i for i in cls_ids
                      if judge[i]["label"] == H2J[cls]]
            by_class[cls] = (len(cls_ok), len(cls_ids))
        statuses = Counter(judge[i]["status"] for i in ids)
        table = Counter((labelled[i],
                         judge[i]["label"] if judge[i]["status"]
                         == "valid" else judge[i]["status"])
                        for i in ids)
        lines += [
            f"\n## {name}",
            f"- eligible human-labelled: {len(ids)}; valid judge "
            f"judgments: {len(valid)} (coverage "
            f"{len(valid) / len(ids):.1%})" if ids else "- no overlap",
            f"- correct among valid: {len(correct)}/{len(valid)}"
            + (f" = {len(correct) / len(valid):.1%}" if valid else ""),
            f"- when human SATISFIES: {by_class['SATISFIES'][0]}/"
            f"{by_class['SATISFIES'][1]}",
            f"- when human VIOLATES: {by_class['VIOLATES'][0]}/"
            f"{by_class['VIOLATES'][1]}",
            f"- human SATISFIES rate: "
            f"{sum(1 for i in ids if labelled[i] == 'SATISFIES')}"
            f"/{len(ids)}",
            f"- judge SATISFIES rate (valid): "
            f"{sum(1 for i in valid if judge[i]['label'] == 'pass')}"
            f"/{len(valid)}",
            f"- judge statuses: {dict(statuses)}",
            "- full table (human x judge):"]
        for k in sorted(table):
            lines.append(f"    - {k[0]} x {k[1]}: {table[k]}")
        per_valid[name] = {i: judge[i]["label"] for i in valid}

    for a, b in itertools.combinations(configs, 2):
        shared = sorted(set(per_valid[a]) & set(per_valid[b]))
        a_right_b_wrong = [i for i in shared
                           if per_valid[a][i] == H2J[labelled[i]]
                           != per_valid[b][i]]
        b_right_a_wrong = [i for i in shared
                           if per_valid[b][i] == H2J[labelled[i]]
                           != per_valid[a][i]]
        lines += [f"\n## Paired {a} vs {b} (same human-labelled items, "
                  f"n={len(shared)})",
                  f"- {a} right where {b} wrong: "
                  f"{len(a_right_b_wrong)} {a_right_b_wrong}",
                  f"- {b} right where {a} wrong: "
                  f"{len(b_right_a_wrong)} {b_right_a_wrong}"]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
