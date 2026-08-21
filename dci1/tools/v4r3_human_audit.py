"""§10.3's human agreement audit: plan it, label it blind, seal it, score it.

The scientific rule lives in `dci1v4r3.stages.human_audit`; this file is the
workflow around it. Four properties are the point, and each is enforced rather
than documented:

* **Frozen first.** `plan` draws every batch before a single item is shown and
  writes a hash per batch. `review` refuses to run against a plan whose hash
  has moved. No item is ever replaced, re-drawn or dropped, least of all one
  the annotator disagreed with.
* **Blind.** `review` never opens `key.json`. That is asserted by a test that
  parses this file and looks for the name, because a comment saying so is not
  evidence. The annotator sees a constraint, a response and an ordinal --- no
  verdict, no model, no family, no severity, no earlier answer of their own,
  and no agreement figure at any point.
* **Append-only.** Every answer is appended and fsynced the moment it is
  given, so an interrupted session loses nothing. An edit appends a correction
  rather than rewriting a line; the last row for an item is the effective one
  and the earlier one stays visible.
* **Sealed once.** `seal-batch` is irreversible and refuses a batch that is
  not complete. After it, that batch takes no further rows.

`report` refuses to print agreement until every batch is sealed, because a
partial agreement figure is exactly the thing that would bias the rest of the
labelling. It can be forced, deliberately and explicitly, by a researcher who
wants it anyway.

    python3 tools/v4r3_human_audit.py plan --annotator Bryan
    python3 tools/v4r3_human_audit.py review --batch 1
    python3 tools/v4r3_human_audit.py status
    python3 tools/v4r3_human_audit.py seal-batch 1
    python3 tools/v4r3_human_audit.py report
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.errors import ProtocolError                          # noqa: E402
from dci1v4.protocol.hashing import canonical_json, sha_text     # noqa: E402
from dci1v4r3 import CLASSIFICATION                              # noqa: E402
from dci1v4r3.stages.human_audit import (                        # noqa: E402
    BATCH_SIZE, EVAL_STRATA, LABEL_OF_KEY, REVIEWER_BRIEF, SAMPLING_RULES,
    agreement_report, assert_plan_blinded, build_plan, natural_pool,
    plan_hash, reachability,
)
from dci1v4r3.verifiers import verifier_source_hash              # noqa: E402

ROOT = DCI1 / "reports" / "dci1v4r3" / "human_audit"
PLAN = ROOT / "plan.json"
KEY = ROOT / "key.json"
BRIEF = ROOT / "REVIEWER_BRIEF.md"
WRAP = 78


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=DCI1,
                          capture_output=True, text=True,
                          check=False).stdout.strip()


def _rel(path: Path) -> str:
    """Repo-relative when it can be, absolute when it cannot."""
    try:
        return str(path.relative_to(DCI1))
    except ValueError:
        return str(path)


def _records_dir(annotator: str) -> Path:
    return ROOT / "records" / annotator


def _batch_file(annotator: str, batch: int) -> Path:
    return _records_dir(annotator) / f"batch-{batch:02d}.jsonl"


def _seal_file(annotator: str, batch: int) -> Path:
    return ROOT / "seals" / annotator / f"batch-{batch:02d}.json"


def _load_plan() -> dict[str, Any]:
    if not PLAN.exists():
        raise SystemExit("no plan yet. Run:  python3 tools/"
                         "v4r3_human_audit.py plan --annotator <name>")
    plan = json.loads(PLAN.read_text())
    if plan_hash(plan) != plan["plan_hash"]:
        raise SystemExit("the plan's hash does not recompute: its membership "
                         "has changed since it was frozen. Refusing.")
    return plan


def _batch_rows(plan: dict[str, Any], batch: int) -> list[dict[str, Any]]:
    rows = [row for row in plan["packet"] if row["batch"] == batch]
    if not rows:
        raise SystemExit(f"batch {batch} is not in the plan "
                         f"(batches {plan['batches'][0]}"
                         f"-{plan['batches'][-1]})")
    frozen = plan["batch_hashes"][str(batch)]
    if sha_text(canonical_json(rows)) != frozen:
        raise SystemExit(f"batch {batch}'s membership hash has moved. "
                         f"Refusing to show it.")
    return rows


def _read_records(annotator: str, batch: int) -> list[dict[str, Any]]:
    path = _batch_file(annotator, batch)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def _append(annotator: str, batch: int, record: dict[str, Any]) -> None:
    """Append and fsync, so an interruption after this line loses nothing."""
    path = _batch_file(annotator, batch)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _sealed(annotator: str, batch: int) -> bool:
    return _seal_file(annotator, batch).exists()


# ------------------------------------------------------------------- plan

def cmd_plan(args) -> int:
    if PLAN.exists() and not args.replan:
        plan = _load_plan()
        print(json.dumps({"already_planned": True, "items": plan["items"],
                          "batches": plan["batches"][-1],
                          "plan_hash": plan["plan_hash"],
                          "path": _rel(PLAN)}, indent=1))
        return 0
    if args.replan:
        existing = sorted(ROOT.glob("records/*/batch-*.jsonl"))
        if existing:
            raise SystemExit(
                "labels already exist, so the sample is fixed. Replacing a "
                "frozen sample after labelling has begun is precisely what "
                "§10.3's seeded sample exists to prevent. Refusing:\n  "
                + "\n  ".join(_rel(p) for p in existing))

    pool = natural_pool()
    plan, key = build_plan(pool, rule=args.rule, batch_size=args.batch_size,
                           annotator=args.annotator)
    assert_plan_blinded(plan["packet"])
    plan.update({
        "classification": CLASSIFICATION,
        "canonical_verifier_hash": verifier_source_hash(),
        "pool_size": len(pool),
        "producing_commit": _commit(),
        "planned_at": _now(),
        "reachability": reachability(key["key"]),
    })
    plan["plan_hash"] = plan_hash(plan)
    key["plan_hash"] = plan["plan_hash"]

    ROOT.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(plan, indent=1, sort_keys=True) + "\n")
    KEY.write_text(json.dumps(key, indent=1, sort_keys=True) + "\n")
    BRIEF.write_text(REVIEWER_BRIEF)
    print(json.dumps({
        "planned": True, "annotator": args.annotator, "rule": args.rule,
        "items": plan["items"], "batches": plan["batches"][-1],
        "batch_size": plan["batch_size"],
        "quota": plan["sampling"]["quota"],
        "population": plan["sampling"]["population"],
        "reachability": {k: v["reachable"]
                         for k, v in plan["reachability"].items()},
        "plan_hash": plan["plan_hash"],
        "standing": plan["standing"],
        "start_with": "python3 tools/v4r3_human_audit.py review --batch 1",
    }, indent=1))
    return 0


# ----------------------------------------------------------------- review

def _show(row: dict[str, Any], seen: int, total: int, batch: int) -> None:
    print()
    print("=" * WRAP)
    print(f"  batch {batch}  ·  item {seen} of {total}  ·  {row['item_id']}")
    print("=" * WRAP)
    print("\n  CONSTRAINT\n")
    for line in textwrap.wrap(row["constraint"], WRAP - 6):
        print(f"    {line}")
    print("\n  RESPONSE\n")
    body = row["response"]
    if not body.strip():
        print("    (the response is empty)")
    for paragraph in body.split("\n"):
        if not paragraph.strip():
            print()
            continue
        for line in textwrap.wrap(paragraph, WRAP - 6):
            print(f"    {line}")
    print()


def _mark(item_id: str) -> dict[str, Any]:
    """§10.3's tool-assisted protocol: the annotator marks, the tool tallies.

    Nothing is detected, highlighted, counted or normalised on the
    annotator's behalf. The only arithmetic is over marks they typed.
    """
    print("\n  Type one qualifying feature per line, blank line to finish.")
    print("  The tool counts what you type and nothing else.\n")
    marks: list[str] = []
    while True:
        try:
            entry = input(f"    mark {len(marks) + 1}> ").strip()
        except EOFError:
            break
        if not entry:
            break
        marks.append(entry)
    print(f"\n  You marked {len(marks)} feature"
          f"{'' if len(marks) == 1 else 's'}.\n")
    return {"marks": marks, "count": len(marks)}


def cmd_review(args) -> int:
    plan = _load_plan()
    annotator = args.annotator or plan["annotator"]
    batch = args.batch
    if batch is None:
        if not args.resume:
            raise SystemExit("pass --batch N, or --resume to continue the "
                             "first unfinished batch")
        sizes = {b: sum(1 for r in plan["packet"] if r["batch"] == b)
                 for b in plan["batches"]}
        batch = next((b for b in plan["batches"]
                      if not _sealed(annotator, b)
                      and len({r["item_id"]
                               for r in _read_records(annotator, b)})
                      < sizes[b]), None)
        if batch is None:
            print("every batch is answered. Seal them, then run report.")
            return 0
    if _sealed(annotator, batch):
        raise SystemExit(f"batch {batch} is sealed. Sealed batches take no "
                         f"further rows.")

    rows = _batch_rows(plan, batch)
    if not sys.stdin.isatty():                     # pragma: no cover
        raise SystemExit("review is interactive; run it in a terminal so the "
                         "labels are a person's and are known to be")
    records = _read_records(annotator, batch)
    answered = {r["item_id"] for r in records}
    pending = [row for row in rows if row["item_id"] not in answered]
    if args.edit:
        pending = rows                              # revisit the whole batch

    print(REVIEWER_BRIEF)
    print(f"  batch {batch} of {plan['batches'][-1]}  ·  "
          f"{len(answered)}/{len(rows)} already answered  ·  "
          f"{len(pending)} to go")

    index = 0
    while index < len(pending):
        row = pending[index]
        _show(row, rows.index(row) + 1, len(rows), batch)
        marks: dict[str, Any] | None = None
        while True:
            try:
                answer = input("  [y]es / [n]o / [u]nsure / "
                               "[m]ark / [r]eshow / [b]ack / [q]uit > "
                               ).strip().lower()
            except EOFError:
                answer = "q"
            if answer == "q":
                print(f"\n  saved. Resume with:  python3 tools/"
                      f"v4r3_human_audit.py review --batch {batch}\n")
                return 0
            if answer == "r":
                _show(row, rows.index(row) + 1, len(rows), batch)
                continue
            if answer == "m":
                marks = _mark(row["item_id"])
                continue
            if answer == "b":
                if index == 0:
                    print("  this is the first item of the batch.")
                    continue
                index -= 1
                break
            if answer in LABEL_OF_KEY:
                note = input("  note (optional) > ").strip()
                _append(annotator, batch, {
                    "item_id": row["item_id"], "batch": batch,
                    "position": row["position"], "annotator": annotator,
                    "label": LABEL_OF_KEY[answer],
                    "note": note or None,
                    "marks_used": marks is not None,
                    "marks": marks["marks"] if marks else None,
                    "mark_count": marks["count"] if marks else None,
                    "response_sha256": row["response_sha256"],
                    "recorded_at": _now(),
                    "plan_hash": plan["plan_hash"]})
                index += 1
                done = len({r["item_id"]
                            for r in _read_records(annotator, batch)})
                print(f"  recorded.  {done}/{len(rows)} in this batch.")
                break
            print("  answer y, n, u, m, r, b or q.")

    done = len({r["item_id"] for r in _read_records(annotator, batch)})
    print(f"\n  batch {batch}: {done}/{len(rows)} answered.")
    if done == len(rows):
        print(f"  seal it with:  python3 tools/v4r3_human_audit.py "
              f"seal-batch {batch}\n")
    return 0


# ----------------------------------------------------------------- status

def cmd_status(args) -> int:
    plan = _load_plan()
    annotator = args.annotator or plan["annotator"]
    batches = []
    for batch in plan["batches"]:
        rows = [r for r in plan["packet"] if r["batch"] == batch]
        answered = len({r["item_id"] for r in _read_records(annotator, batch)})
        batches.append({"batch": batch, "items": len(rows),
                        "answered": answered,
                        "complete": answered == len(rows),
                        "sealed": _sealed(annotator, batch)})
    sealed = sum(1 for b in batches if b["sealed"])
    print(json.dumps({
        "annotator": annotator,
        "items": plan["items"], "batches": len(batches),
        "answered": sum(b["answered"] for b in batches),
        "sealed_batches": sealed,
        "all_sealed": sealed == len(batches),
        "per_batch": batches,
        "agreement": "withheld until every batch is sealed (§10.3 blinding)",
    }, indent=1))
    return 0


# ------------------------------------------------------------- seal-batch

def cmd_seal(args) -> int:
    plan = _load_plan()
    annotator = args.annotator or plan["annotator"]
    batch = args.batch
    if _sealed(annotator, batch):
        raise SystemExit(f"batch {batch} is already sealed. Sealing is "
                         f"irreversible.")
    rows = _batch_rows(plan, batch)
    records = _read_records(annotator, batch)
    answered = {r["item_id"] for r in records}
    missing = [row["item_id"] for row in rows if row["item_id"] not in answered]
    if missing:
        raise SystemExit(f"batch {batch} has {len(missing)} unanswered items. "
                         f"Refusing to seal an incomplete batch.")
    path = _seal_file(annotator, batch)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_type": "v4r3-human-audit-seal",
        "annotator": annotator, "batch": batch,
        "items": len(rows),
        "rows_recorded": len(records),
        "membership_hash": plan["batch_hashes"][str(batch)],
        "records_hash": sha_text(canonical_json(records)),
        "plan_hash": plan["plan_hash"],
        "producing_commit": _commit(),
        "sealed_at": _now(),
        "irreversible": "this batch accepts no further rows, and its "
                        "membership can no longer change",
    }
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    remaining = [b for b in plan["batches"] if not _sealed(annotator, b)]
    print(json.dumps({"sealed": batch, "items": len(rows),
                      "batches_remaining": len(remaining),
                      "next": (f"python3 tools/v4r3_human_audit.py review "
                               f"--batch {remaining[0]}" if remaining else
                               "python3 tools/v4r3_human_audit.py report"),
                      "agreement": "not computed; see report once every "
                                   "batch is sealed"}, indent=1))
    return 0


# ----------------------------------------------------------------- report

def cmd_report(args) -> int:
    plan = _load_plan()
    annotator = args.annotator or plan["annotator"]
    unsealed = [b for b in plan["batches"] if not _sealed(annotator, b)]
    if unsealed and not args.reveal_early:
        raise SystemExit(
            f"{len(unsealed)} of {len(plan['batches'])} batches are not "
            f"sealed. Agreement is withheld until the registered set is "
            f"finished, because a partial figure biases the labelling that "
            f"is left. Pass --reveal-early to override deliberately.")

    key = json.loads(KEY.read_text())
    if key["plan_hash"] != plan["plan_hash"]:
        raise SystemExit("the key does not belong to this plan")
    records = [record for batch in plan["batches"]
               for record in _read_records(annotator, batch)]
    report = agreement_report(key["key"], records)
    report.update({
        "classification": CLASSIFICATION,
        "annotator": annotator,
        "independent_of_design_team": False,
        "canonical_verifier_hash": plan["canonical_verifier_hash"],
        "plan_hash": plan["plan_hash"],
        "sampling": plan["sampling"],
        "revealed_early": bool(unsealed),
        "unsealed_batches": unsealed,
        "protocol_conformance": {
            "items_where_the_annotator_used_the_marking_protocol":
                len({r["item_id"] for r in records if r.get("marks_used")}),
            "of": len({r["item_id"] for r in records}),
            "meaning": "§10.3's tool-assisted protocol has the annotator "
                       "mark each qualifying feature and the interface tally "
                       "their own marks. The affordance is offered on every "
                       "item and its use is recorded, so conformance is a "
                       "measured quantity rather than an assumed one."},
        "producing_commit": _commit(),
        "generated_at": _now(),
    })
    out = ROOT / f"report_{annotator}.json"
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "compared": report["compared"], "planned": report["planned"],
        "complete": report["complete"],
        "agreement_overall": report["agreement_overall"],
        "criterion": report["criterion"],
        "by_stratum": {s: {k: report["by_stratum"][s][k] for k in
                           ("n", "disagreements",
                            "wilson_upper_on_disagreement",
                            "meets_criterion")}
                       for s in EVAL_STRATA},
        "all_strata_meet_the_criterion":
            report["all_strata_meet_the_criterion"],
        "standing": report["standing"],
        "satisfies_section_10_3": report["satisfies_section_10_3"],
        "why_not": report["why_not"],
        "report": _rel(out),
    }, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="freeze every batch, before labelling")
    plan.add_argument("--annotator", required=True)
    plan.add_argument("--rule", default="per_class", choices=SAMPLING_RULES)
    plan.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    plan.add_argument("--replan", action="store_true",
                      help="rebuild; refused once any label exists")
    plan.set_defaults(func=cmd_plan)

    review = sub.add_parser("review", help="label one batch, blind")
    review.add_argument("--batch", type=int)
    review.add_argument("--resume", action="store_true")
    review.add_argument("--edit", action="store_true",
                        help="revisit every item in the batch; a changed "
                             "answer is appended, not overwritten")
    review.add_argument("--annotator")
    review.set_defaults(func=cmd_review)

    status = sub.add_parser("status", help="progress only, never agreement")
    status.add_argument("--annotator")
    status.set_defaults(func=cmd_status)

    seal = sub.add_parser("seal-batch", help="irreversible")
    seal.add_argument("batch", type=int)
    seal.add_argument("--annotator")
    seal.set_defaults(func=cmd_seal)

    report = sub.add_parser("report", help="§10.3's criterion, once sealed")
    report.add_argument("--annotator")
    report.add_argument("--reveal-early", action="store_true")
    report.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ProtocolError as error:
        raise SystemExit(str(error))


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
