"""Build every pre-registered sample set (PREREGISTERED.md), READ-ONLY
over registered evidence. Deterministic: fixed seeds, sorted iteration.

    .venv/bin/python experiments/build_sets.py

Outputs:
    dataset/exp1_cap.jsonl                     E1 cap-search samples
    dataset/exp2_repeat.jsonl                  E2 repeat-stability subset
    experiments/human_review/calibration_sample.json
    experiments/reserved_final_check_ids.json  (sealed: never run or
                                                analyzed until freeze)
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from forensics import paths                      # noqa: E402
from forensics import dataset as dsmod           # noqa: E402

SEED = 20260818
CALIBRATION_N = 56
RESERVED_N = 40
EFFORTS = ("low", "medium", "high")


def load_diagnostic():
    recs = [json.loads(l) for l in
            (paths.DATASET / "diagnostic.jsonl").read_text().splitlines()]
    merged = {r["id"]: r for r in map(json.loads,
              (paths.ANALYSIS_OUT / "merged.jsonl").read_text().splitlines())}
    return recs, merged


def build_exp1(recs, merged) -> list[dict]:
    truncated = [r for r in recs if any(
        merged[r["id"]][f"{e}_truncated"] for e in EFFORTS)]
    trunc_ids = {r["id"] for r in truncated}
    # matched near-miss controls: per (model, n) of a truncated sample,
    # the non-truncated sample with the largest high completion tokens
    by_stratum = defaultdict(list)
    for r in recs:
        m = merged[r["id"]]
        if r["id"] in trunc_ids or m["high_truncated"]:
            continue
        by_stratum[(r["source_model"], r["target_n"])].append(
            (-(m["high_completion_tokens"] or 0), r["id"], r))
    controls, seen = [], set()
    for t in truncated:
        cands = sorted(by_stratum.get(
            (t["source_model"], t["target_n"]), []))
        for _, cid, c in cands:
            if cid not in seen:
                controls.append(c)
                seen.add(cid)
                break
    # top up to 30 with the globally longest non-truncated completions
    global_pool = sorted(
        ((-(merged[r["id"]]["high_completion_tokens"] or 0), r["id"], r)
         for r in recs
         if r["id"] not in trunc_ids and r["id"] not in seen
         and not merged[r["id"]]["high_truncated"]))
    for _, cid, c in global_pool:
        if len(controls) >= 30:
            break
        controls.append(c)
        seen.add(cid)
    out = sorted(truncated + controls, key=lambda r: r["id"])
    for r in out:
        r = dict(r)
    return out


def build_exp2(recs) -> list[dict]:
    controls = [r for r in recs if not r["contested"]]
    contested = [r for r in recs if r["contested"]]
    # stratified sorted-id-first: cycle strata, taking lowest unused id
    strata = defaultdict(list)
    for r in sorted(contested, key=lambda r: r["id"]):
        strata[(r["source_model"],
                r["deterministic_verifier_label"])].append(r)
    picked = []
    keys = sorted(strata)
    while len(picked) < 59:
        progressed = False
        for k in keys:
            if strata[k] and len(picked) < 59:
                picked.append(strata[k].pop(0))
                progressed = True
        if not progressed:
            break
    return sorted(controls + picked, key=lambda r: r["id"])


def full_population():
    """All 983 dev-half items with strata, sorted."""
    items = []
    for mk in paths.MODEL_KEYS:
        pool = dsmod.pool_items(mk)
        rounds = dsmod.round_judgments(mk)
        for iid in sorted(rounds["high"]):
            item = pool[iid]
            cls = "pass" if item["registered_s0"] == item["n"] else "fail"
            items.append({"id": f"{mk}::{iid}", "model": mk,
                          "item_id": iid, "n": item["n"],
                          "verifier_class": cls})
    return sorted(items, key=lambda r: r["id"])


def build_calibration(pop) -> dict:
    """Stratified proportional sample; per-item inclusion probability
    recorded (n_h / N_h within stratum h)."""
    rng = random.Random(SEED)
    strata = defaultdict(list)
    for it in pop:
        strata[(it["model"], it["verifier_class"])].append(it)
    keys = sorted(strata)
    total = len(pop)
    alloc = {k: max(1, round(CALIBRATION_N * len(strata[k]) / total))
             for k in keys}
    # fix rounding drift deterministically on the largest strata
    while sum(alloc.values()) != CALIBRATION_N:
        delta = 1 if sum(alloc.values()) < CALIBRATION_N else -1
        k = max(keys, key=lambda k: (len(strata[k]), k))
        alloc[k] += delta
    sample = []
    for k in keys:
        chosen = rng.sample(strata[k], alloc[k])
        p = alloc[k] / len(strata[k])
        for it in sorted(chosen, key=lambda r: r["id"]):
            sample.append({**it, "stratum": list(k),
                           "inclusion_probability": round(p, 6)})
    return {"seed": SEED, "population_size": total,
            "design": "stratified proportional, strata = source model "
                      "x deterministic verifier class, SRS within "
                      "stratum",
            "allocation": {"|".join(k): alloc[k] for k in keys},
            "samples": sample}


def build_reserved(pop, exposed_ids, calibration_ids) -> dict:
    rng = random.Random(SEED + 1)
    eligible = [it for it in pop if it["id"] not in exposed_ids
                and it["id"] not in calibration_ids]
    chosen = sorted(rng.sample(eligible, RESERVED_N),
                    key=lambda r: r["id"])
    return {"seed": SEED + 1, "eligible": len(eligible),
            "note": "SEALED. Do not run, inspect, or use until the "
                    "full configuration is frozen (PREREGISTERED.md "
                    "E11).",
            "ids": [it["id"] for it in chosen]}


def main():
    recs, merged = load_diagnostic()
    exp1 = build_exp1(recs, merged)
    exp2 = build_exp2(recs)
    for name, data in (("exp1_cap", exp1), ("exp2_repeat", exp2)):
        p = paths.DATASET / f"{name}.jsonl"
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                             for r in data))
        trunc = sum(1 for r in data if any(
            merged[r["id"]][f"{e}_truncated"] for e in EFFORTS))
        print(f"{p.name}: {len(data)} samples "
              f"({trunc} previously truncated, "
              f"{sum(1 for r in data if not r['contested'])} controls)")
    pop = full_population()
    cal = build_calibration(pop)
    hr = ROOT / "experiments" / "human_review"
    hr.mkdir(exist_ok=True)
    (hr / "calibration_sample.json").write_text(
        json.dumps(cal, indent=1))
    print(f"calibration_sample.json: {len(cal['samples'])} items, "
          f"allocation {cal['allocation']}")
    exposed = {r["id"] for r in recs}
    cal_ids = {s["id"] for s in cal["samples"]}
    reserved = build_reserved(pop, exposed, cal_ids)
    rp = ROOT / "experiments" / "reserved_final_check_ids.json"
    rp.write_text(json.dumps(reserved, indent=1))
    digest = hashlib.sha256(rp.read_bytes()).hexdigest()
    print(f"reserved_final_check_ids.json: {RESERVED_N} items "
          f"(eligible {reserved['eligible']}), sha256={digest}")


if __name__ == "__main__":
    main()
