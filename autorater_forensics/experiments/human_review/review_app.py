"""Blind human-review CLI (PREREGISTERED.md E5/E6). Append-only records;
judge/verifier/effort/Scout fields are NEVER loaded into the display
path before a judgment is committed.

    # review (blind):
    .venv/bin/python experiments/human_review/review_app.py review \
        --set calibration --annotator NAME
    # reveal hidden fields AFTER a judgment exists (diagnosis only):
    .venv/bin/python experiments/human_review/review_app.py reveal \
        --set calibration --annotator NAME --id <sample_id>

Set files:
    calibration -> experiments/human_review/calibration_sample.json
    diagnostic  -> experiments/human_review/diagnostic_set.json

Records: experiments/human_review/records/<set>_<annotator>.jsonl
(append-only; a sample already judged is never re-presented).
Reveals:  experiments/human_review/records/reveals_<set>_<annotator>.jsonl

No model output is ever written into a human record. Piped/scripted
input is refused outside --selftest, so a model cannot silently stand
in for the reviewer.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from definitions import EDGE_RULES, SATISFIES_DEF, VIOLATES_DEF  # noqa: E402
from forensics import dataset as dsmod                            # noqa: E402

SETS = {"calibration": HERE / "calibration_sample.json",
        "diagnostic": HERE / "diagnostic_set.json"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_items(set_name: str) -> list[dict]:
    data = json.loads(SETS[set_name].read_text())
    items = data["samples"] if "samples" in data else data["items"]
    pools: dict[str, dict] = {}
    out = []
    for it in items:
        model, item_id = it["id"].split("::", 1)
        if model not in pools:
            pools[model] = dsmod.pool_items(model)
        p = pools[model][item_id]
        out.append({"id": it["id"], "n": p["n"],
                    "constraint": dsmod.wording(p["n"]),
                    "response": p["response_text"]})
    return out


def record_path(set_name: str, annotator: str) -> Path:
    d = HERE / "records"
    d.mkdir(exist_ok=True)
    return d / f"{set_name}_{annotator}.jsonl"


def existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(l)["id"] for l in path.read_text().splitlines()
            if l.strip()}


def review(set_name: str, annotator: str, selftest_answers=None):
    items = load_items(set_name)
    rec = record_path(set_name, annotator)
    done = existing_ids(rec)
    todo = [i for i in items if i["id"] not in done]
    if not todo:
        print("nothing left to review")
        return
    if selftest_answers is None and not sys.stdin.isatty():
        raise SystemExit(
            "refusing non-interactive review: human judgments must be "
            "typed by a human (use --selftest only for the dry-run "
            "self-test, whose records are marked synthetic)")
    print(f"{len(todo)} of {len(items)} items to review "
          f"(set={set_name}, annotator={annotator})\n")
    for k, item in enumerate(todo):
        print("=" * 72)
        print(f"[{k + 1}/{len(todo)}]  id: {item['id']}")
        print(f"\nINSTRUCTION:\n  {item['constraint']}\n")
        print(f"RESPONSE:\n{item['response']}\n")
        print(SATISFIES_DEF)
        print(VIOLATES_DEF)
        print(EDGE_RULES)
        while True:
            if selftest_answers is not None:
                ans = selftest_answers.pop(0)
                print(f"[selftest] answer: {ans}")
            else:
                ans = input("\nJudgment [S=satisfies / V=violates / "
                            "U=unsure / Q=quit]: ").strip().upper()
            if ans in ("S", "V", "U"):
                label = {"S": "SATISFIES", "V": "VIOLATES",
                         "U": "UNSURE"}[ans]
                with rec.open("a") as fh:
                    fh.write(json.dumps({
                        "id": item["id"], "label": label,
                        "annotator": annotator,
                        "synthetic": selftest_answers is not None,
                        "set": set_name, "recorded_at": now(),
                        "response_sha256": hashlib.sha256(
                            item["response"].encode()).hexdigest(),
                    }, ensure_ascii=False) + "\n")
                break
            if ans == "Q":
                print("stopped; progress saved")
                return
    print("set complete")


def reveal(set_name: str, annotator: str, sample_id: str):
    rec = record_path(set_name, annotator)
    if sample_id not in existing_ids(rec):
        raise SystemExit(
            f"no committed judgment for {sample_id!r} — hidden fields "
            f"stay hidden until the blind judgment is recorded")
    diag = {r["id"]: r for r in map(json.loads,
            (ROOT / "dataset" / "diagnostic.jsonl").read_text()
            .splitlines())} if (ROOT / "dataset"
                               / "diagnostic.jsonl").exists() else {}
    d = diag.get(sample_id)
    info = {"id": sample_id}
    if d:
        info.update({
            "deterministic_verifier_label":
                d["deterministic_verifier_label"],
            "s0_count": d["s0_count"], "target_n": d["target_n"],
            "registered_round_labels": {
                e: d[f"prior_{e}_label"]
                for e in ("low", "medium", "high")},
            "contested_reasons": d["contested_reasons"]})
    else:
        info["note"] = ("not in the diagnostic dataset; judge labels "
                        "for calibration items come from the frozen "
                        "configuration's run at comparison time")
    with (rec.parent / f"reveals_{set_name}_{annotator}.jsonl") \
            .open("a") as fh:
        fh.write(json.dumps({"id": sample_id, "revealed_at": now()})
                 + "\n")
    print(json.dumps(info, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["review", "reveal"])
    ap.add_argument("--set", required=True, choices=sorted(SETS))
    ap.add_argument("--annotator", required=True)
    ap.add_argument("--id")
    ap.add_argument("--selftest", action="store_true",
                    help="dry-run with synthetic answers; records are "
                         "marked synthetic and must be deleted before "
                         "real review")
    args = ap.parse_args()
    if args.cmd == "review":
        answers = None
        if args.selftest:
            n = len(load_items(args.set))
            answers = (["S", "V", "U"] * (n // 3 + 1))[:n]
        review(args.set, args.annotator, answers)
    else:
        if not args.id:
            raise SystemExit("--id required for reveal")
        reveal(args.set, args.annotator, args.id)


if __name__ == "__main__":
    main()
