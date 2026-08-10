#!/usr/bin/env python3
"""Blinded three-way audit of the sentence verifier.

Question: are the one-sentence clause-chain outputs GENUINE failures of "write
exactly four sentences", or parser artefacts?

Three counts per output, produced without reference to one another:
  1. the production verifier's count (stored in the raw artifact);
  2. an independently implemented counter (`reanalysis_standalone`);
  3. a human grammatical count, entered against a BLINDED export in which the
     arm, condition, order and every verifier verdict are withheld.

The export carries only an opaque case id and the raw response text. The key
mapping is written to a separate file that the reader does not open until the
counts are recorded, so a count cannot be nudged by knowing which arm it came
from.

    python verifier_audit.py export   # writes the blinded set + key
    python verifier_audit.py report   # joins counts and reports disagreements
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
OUT = HERE / "verifier_audit"

sys.path.insert(0, str(HERE))
from reanalysis_standalone import count_sentences_independent  # noqa: E402

RUN_SPECS = [
    ("stageB_20260810T183206Z", "B"),
    ("stageD2_anticollapse_20260810T192423Z", "D2"),
    ("stageD3_semicolon_20260810T192430Z", "D3"),
]


def _stratum(row: dict, n_target: int) -> str:
    observed = (row.get("verifier_detail") or {}).get("observed")
    failed = row.get("a_failure") == 1
    scaffolded = bool(row.get("scaffold"))
    arm = row["arm"]
    if scaffolded:
        return "scaffold_condition"
    if arm == "B" and failed:
        return "focal_B_failure"
    if arm == "S_SEMICOLON" and failed:
        return "semicolon_failure"
    if failed:
        return "ordinary_reference_failure"
    return "pass"


# Sample sizes per stratum. "all or a large sample" of the failure strata; a
# random sample of passes so the reader cannot infer a verdict from position.
QUOTA = {
    "focal_B_failure": 40,
    "semicolon_failure": 40,
    "ordinary_reference_failure": 25,
    "scaffold_condition": 30,
    "pass": 40,
}


def export(seed: int = 4242) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    pool: dict[str, list[dict]] = {}
    for run, tag in RUN_SPECS:
        directory = RUNS / run
        config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
        n_target = int(config["harvest_provenance"]["exact_sentence_count"])
        for row in (json.loads(l) for l in
                    (directory / "generations.jsonl").read_text(encoding="utf-8").splitlines()
                    if l.strip()):
            if row["condition"] not in ("focal", "reference") or not row["scorable"]:
                continue
            row["_run"] = run
            row["_tag"] = tag
            row["_n_target"] = n_target
            pool.setdefault(_stratum(row, n_target), []).append(row)

    picked: list[dict] = []
    for stratum, want in QUOTA.items():
        available = sorted(pool.get(stratum, []), key=lambda r: r["row_id"])
        take = available if len(available) <= want else rng.sample(available, want)
        picked.extend(take)
    rng.shuffle(picked)

    blinded, key = [], []
    for index, row in enumerate(picked):
        case_id = "C" + hashlib.sha256(
            f"{row['row_id']}|{seed}".encode()).hexdigest()[:8].upper()
        blinded.append({
            "case_id": case_id,
            "target_sentence_count": row["_n_target"],
            "response": row["response"],
            # to be filled by the reader:
            "human_sentence_count": "",
            "human_failure_mode": "",
            "human_note": "",
        })
        key.append({
            "case_id": case_id, "row_id": row["row_id"], "run": row["_run"],
            "arm": row["arm"], "order": row["order"],
            "scaffold": row.get("scaffold", ""),
            "stratum": _stratum(row, row["_n_target"]),
            "production_count": (row.get("verifier_detail") or {}).get("observed"),
            "production_a_failure": row["a_failure"],
            "independent_count": count_sentences_independent(row["response"]),
        })

    (OUT / "blinded_cases.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in blinded),
        encoding="utf-8")
    (OUT / "blinded_cases.md").write_text(_markdown(blinded), encoding="utf-8")
    (OUT / "KEY_DO_NOT_OPEN_FIRST.jsonl").write_text(
        "".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key),
        encoding="utf-8")
    return {"n_cases": len(blinded),
            "per_stratum": {s: sum(1 for k in key if k["stratum"] == s)
                            for s in QUOTA},
            "pool_sizes": {s: len(v) for s, v in sorted(pool.items())},
            "dir": str(OUT)}


def _markdown(cases: list[dict]) -> str:
    lines = ["# Blinded sentence-count audit", "",
             "For each case, count the **grammatical sentences** in the response, "
             "then record a failure-mode label. Arm, condition, order and every "
             "verifier verdict are deliberately withheld.", "",
             "Semicolon-joined independent clauses are ONE sentence in ordinary "
             "usage; that convention is the thing under test, so apply it "
             "consistently and note any case where it feels wrong.", ""]
    for case in cases:
        lines += ["---", "", f"## {case['case_id']}",
                  f"(target: exactly {case['target_sentence_count']} sentences)", "",
                  "```", case["response"] or "<none>", "```", "",
                  "- human_sentence_count: ", "- human_failure_mode: ", ""]
    return "\n".join(lines)


def report(counts_path: Path) -> int:
    key = {k["case_id"]: k for k in (json.loads(l) for l in
           (OUT / "KEY_DO_NOT_OPEN_FIRST.jsonl").read_text(encoding="utf-8").splitlines()
           if l.strip())}
    human = {}
    with counts_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("human_sentence_count", "").strip():
                human[row["case_id"]] = int(row["human_sentence_count"])

    rows, disagreements = [], []
    for case_id, entry in sorted(key.items()):
        h = human.get(case_id)
        record = {**entry, "human_count": h}
        rows.append(record)
        if h is not None and not (h == entry["production_count"] == entry["independent_count"]):
            disagreements.append(record)

    print(f"\ncases in key: {len(key)} | human counts entered: {len(human)}")
    prod_vs_indep = [e for e in key.values()
                     if e["production_count"] != e["independent_count"]]
    print(f"production vs independent disagreements: {len(prod_vs_indep)}")
    for e in prod_vs_indep[:10]:
        print(f"   {e['case_id']} {e['arm']:12s} production={e['production_count']} "
              f"independent={e['independent_count']}")

    if human:
        both = [e for e in rows if e["human_count"] is not None]
        agree_prod = sum(1 for e in both if e["human_count"] == e["production_count"])
        agree_indep = sum(1 for e in both if e["human_count"] == e["independent_count"])
        print(f"\nhuman vs production : {agree_prod}/{len(both)} agree "
              f"({agree_prod / len(both):.3f})")
        print(f"human vs independent: {agree_indep}/{len(both)} agree "
              f"({agree_indep / len(both):.3f})")
        print(f"\nthree-way disagreements: {len(disagreements)}")
        for e in disagreements[:20]:
            print(f"   {e['case_id']} {e['arm']:12s} stratum={e['stratum']:26s} "
                  f"production={e['production_count']} independent={e['independent_count']} "
                  f"human={e['human_count']}")
        by_stratum = Counter(e["stratum"] for e in disagreements)
        print(f"\ndisagreements by stratum: {dict(by_stratum)}")

    (OUT / "three_way_counts.json").write_text(json.dumps(rows, indent=2),
                                               encoding="utf-8")
    print(f"\nartifacts: {OUT}")
    return 1 if disagreements else 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "export":
        print(json.dumps(export(), indent=2))
        return 0
    if argv[0] == "report":
        path = Path(argv[1]) if len(argv) > 1 else OUT / "human_counts.csv"
        return report(path)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
