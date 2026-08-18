"""Build the ~24-item DIAGNOSTIC human-review set with the
pre-registered composition (PREREGISTERED.md E5). Deterministic:
sorted-id-first within each category, deduplicated across categories.
Run only after E1/E2/E3 outputs exist.

    .venv/bin/python experiments/human_review/build_diagnostic_set.py
"""
from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

QUOTAS = (("medium_vs_high_disagree", 6), ("path_flip_control", 4),
          ("previously_truncated", 4), ("long_response", 4),
          ("high_n", 3), ("all_settings_vs_verifier", 3))


def run_labels(log_dir: Path):
    logs = list_eval_logs(str(log_dir))
    if not logs:
        return {}
    log = read_eval_log(sorted(logs, key=lambda l: l.name)[-1])
    return {str(s.id): {
        "label": s.scores["judge_parse"].metadata.get("parsed_label"),
        "status": s.scores["judge_parse"].metadata.get("status")}
        for s in log.samples}


def main():
    ds = {r["id"]: r for r in map(json.loads,
          (ROOT / "dataset" / "diagnostic.jsonl").read_text()
          .splitlines())}
    med = run_labels(ROOT / "logs_exp" / "exp2" / "medium" / "run1")
    high = run_labels(ROOT / "logs_exp" / "exp2" / "high" / "run1")
    exp1 = [json.loads(l) for l in
            (ROOT / "dataset" / "exp1_cap.jsonl").read_text()
            .splitlines()]
    merged = {r["id"]: r for r in map(json.loads,
              (ROOT / "analysis" / "out" / "merged.jsonl").read_text()
              .splitlines())}
    words = sorted(r["response_words"] for r in ds.values())
    p90 = words[int(0.90 * len(words))]

    cats: dict[str, list[str]] = {}
    cats["medium_vs_high_disagree"] = sorted(
        i for i in set(med) & set(high)
        if med[i]["status"] == "valid" and high[i]["status"] == "valid"
        and med[i]["label"] != high[i]["label"])
    cats["path_flip_control"] = sorted(
        i for i, r in ds.items() if not r["contested"] and any(
            merged[i][f"{e}_label"] != r[f"prior_{e}_label"]
            for e in ("low", "medium", "high")))
    cats["previously_truncated"] = sorted(
        r["id"] for r in exp1 if any(
            merged[r["id"]][f"{e}_truncated"]
            for e in ("low", "medium", "high")))
    cats["long_response"] = sorted(
        i for i, r in ds.items() if r["response_words"] >= p90)
    cats["high_n"] = sorted(
        i for i, r in ds.items() if r["target_n"] >= 7)
    # surviving settings = medium and high (E4); both disagree with the
    # deterministic verifier while valid
    cats["all_settings_vs_verifier"] = sorted(
        i for i in set(med) & set(high)
        if med[i]["status"] == "valid" and high[i]["status"] == "valid"
        and i in ds
        and med[i]["label"] != ds[i]["deterministic_verifier_label"]
        and high[i]["label"] != ds[i]["deterministic_verifier_label"])
    # no Scout-validated pattern currently exists (0 confirmed hits)

    chosen: list[dict] = []
    seen: set[str] = set()
    for cat, quota in QUOTAS:
        picked = []
        for i in cats[cat]:
            if i not in seen and len(picked) < quota:
                picked.append(i)
                seen.add(i)
        chosen += [{"id": i, "category": cat} for i in picked]
    out = {"design": "PREREGISTERED.md E5 diagnostic set — "
                     "deliberately unusual cases; NEVER used to "
                     "estimate overall accuracy",
           "quotas": dict(QUOTAS),
           "category_pool_sizes": {k: len(v) for k, v in cats.items()},
           "items": chosen}
    (HERE / "diagnostic_set.json").write_text(json.dumps(out, indent=1))
    print(f"diagnostic_set.json: {len(chosen)} items; pools "
          f"{out['category_pool_sizes']}")


if __name__ == "__main__":
    main()
