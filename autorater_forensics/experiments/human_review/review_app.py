"""Blind human-review CLI (PREREGISTERED.md E5/E6). Append-only records;
judge/verifier/effort/Scout fields are NEVER loaded into the display
path before a judgment is committed.

    # list the available sets:
    .venv/bin/python experiments/human_review/review_app.py sets
    # review (blind):
    .venv/bin/python experiments/human_review/review_app.py review \
        --set calibration --annotator NAME
    # reveal hidden fields AFTER a judgment exists (diagnosis only):
    .venv/bin/python experiments/human_review/review_app.py reveal \
        --set calibration --annotator NAME --id <sample_id>
    # pin the current records so later edits are detectable:
    .venv/bin/python experiments/human_review/review_app.py pin

Set files:
    calibration  -> experiments/human_review/calibration_sample.json
    diagnostic   -> experiments/human_review/diagnostic_set.json
    extension<k> -> experiments/human_review/extension_batch_<k>.json

Records: experiments/human_review/records/<set>_<annotator>.jsonl
(append-only and hash-chained; a sample already judged is never
re-presented, and an edited or reordered record breaks the chain).
Reveals:  experiments/human_review/records/reveals_<set>_<annotator>.jsonl

No model output is ever written into a human record. Piped/scripted
input is refused outside --selftest, so a model cannot silently stand
in for the reviewer. Ids belonging to the SEALED reserved final-check
set are refused everywhere in this app.
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
import records_io                                                 # noqa: E402
import sampling                                                   # noqa: E402

#: Display fields only. Anything outside this set is a blindness defect.
DISPLAY_FIELDS = {"id", "n", "constraint", "response"}


def available_sets() -> dict[str, Path]:
    sets = {"calibration": HERE / "calibration_sample.json",
            "diagnostic": HERE / "diagnostic_set.json"}
    for path in sorted(HERE.glob("extension_batch_*.json")):
        sets[f"extension{path.stem.rsplit('_', 1)[1]}"] = path
    return {name: path for name, path in sets.items() if path.exists()}


#: Kept for backwards compatibility with existing callers and tests.
SETS = available_sets()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _set_path(set_name: str) -> Path:
    sets = available_sets()
    if set_name not in sets:
        raise SystemExit(f"unknown set {set_name!r}; available: "
                         f"{', '.join(sorted(sets))}")
    return sets[set_name]


def load_items(set_name: str) -> list[dict]:
    """The blind display payload: instruction, response, id, n.

    Every response is checked against the registered content hash (and,
    where the sample manifest records one, against the hash the manifest
    fixed at sampling time), so a human never judges bytes that differ
    from registered evidence.
    """
    data = json.loads(_set_path(set_name).read_text())
    items = data["samples"] if "samples" in data else data["items"]
    sealed = sampling.sealed_ids()
    pools: dict[str, dict] = {}
    out = []
    for it in items:
        if it["id"] in sealed:
            raise SystemExit(
                f"{it['id']} belongs to the SEALED reserved final-check "
                f"set; it must never be presented for review")
        model, item_id = it["id"].split("::", 1)
        if model not in pools:
            pools[model] = dsmod.pool_items(model)
        p = pools[model][item_id]
        digest = hashlib.sha256(p["response_text"].encode()).hexdigest()
        if digest != p["response_hash"]:
            raise SystemExit(
                f"{it['id']}: response bytes do not match the registered "
                f"content hash")
        if it.get("response_sha256") and it["response_sha256"] != digest:
            raise SystemExit(
                f"{it['id']}: the sampled response hash does not match "
                f"registered evidence; the set is stale")
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


def judged_ids(annotator: str) -> set[str]:
    """Every id this annotator has judged in ANY set, so an item can never
    be presented twice under a different set name."""
    directory = HERE / "records"
    if not directory.exists():
        return set()
    ids: set[str] = set()
    for path in sorted(directory.glob(f"*_{annotator}.jsonl")):
        if path.name.startswith("reveals_"):
            continue
        ids |= existing_ids(path)
    return ids


def review(set_name: str, annotator: str, selftest_answers=None):
    items = load_items(set_name)
    rec = record_path(set_name, annotator)
    if rec.exists():
        records_io.verify_chain(rec)
    done = existing_ids(rec) | judged_ids(annotator)
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
                records_io.append_record(rec, {
                    "id": item["id"], "label": label,
                    "annotator": annotator,
                    "synthetic": selftest_answers is not None,
                    "set": set_name, "recorded_at": now(),
                    "response_sha256": hashlib.sha256(
                        item["response"].encode()).hexdigest(),
                })
                break
            if ans == "Q":
                print("stopped; progress saved")
                return
    print("set complete")


def reveal(set_name: str, annotator: str, sample_id: str):
    """Post-judgment diagnostics only: hidden fields for an item this
    annotator has already committed a blind judgment on."""
    if sample_id in sampling.sealed_ids():
        raise SystemExit(f"{sample_id} is in the SEALED reserved set")
    rec = record_path(set_name, annotator)
    if sample_id not in existing_ids(rec):
        raise SystemExit(
            f"no committed judgment for {sample_id!r} — hidden fields "
            f"stay hidden until the blind judgment is recorded")
    info = {"id": sample_id}
    population = {i["id"]: i for i in sampling.population()}
    item = population.get(sample_id)
    if item is not None:
        info.update({
            "deterministic_verifier_label": item["verifier_class"],
            "s0_count": item["s0_count"], "target_n": item["n"],
            "source_pool": item["source_pool"],
            "finish_reason": item["finish_reason"],
            "registered_round_labels": item["judge_round_labels"],
            "registered_round_statuses": item["judge_round_statuses"],
        })
    diag_path = ROOT / "dataset" / "diagnostic.jsonl"
    if diag_path.exists():
        diag = {r["id"]: r for r in map(
            json.loads, diag_path.read_text().splitlines())}
        d = diag.get(sample_id)
        if d:
            info["contested_reasons"] = d["contested_reasons"]
    if item is None:
        info["note"] = "not in the registered dev-half population"
    with (rec.parent / f"reveals_{set_name}_{annotator}.jsonl") \
            .open("a") as fh:
        fh.write(json.dumps({"id": sample_id, "revealed_at": now()})
                 + "\n")
    print(json.dumps(info, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["review", "reveal", "sets", "pin",
                                    "verify"])
    ap.add_argument("--set", choices=sorted(available_sets()))
    ap.add_argument("--annotator")
    ap.add_argument("--id")
    ap.add_argument("--selftest", action="store_true",
                    help="dry-run with synthetic answers; records are "
                         "marked synthetic and must be deleted before "
                         "real review")
    args = ap.parse_args()
    if args.cmd == "sets":
        for name, path in sorted(available_sets().items()):
            print(f"{name:14s} {len(load_items(name)):4d} items  "
                  f"{path.name}")
        return
    if args.cmd in ("pin", "verify"):
        directory = HERE / "records"
        if args.cmd == "pin":
            for pin in records_io.pin_records(directory):
                print(f"pinned {pin['file']} at {pin['lines']} records "
                      f"({pin['sha256'][:12]})")
        print(json.dumps(records_io.verify_all(directory), indent=1))
        return
    if not args.set or not args.annotator:
        raise SystemExit("--set and --annotator are required")
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
