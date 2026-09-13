"""Audit the deterministic verifier by reading what it actually did.

The §10.3 workflow asks you to label a response blind, which means counting
qualifying words in a hundred-word answer by hand. This asks a different and
much faster question: **the derivation is shown, and you say whether it counted
the right things.** Each card gives the instruction as the model received it,
the answer, the word list §7.3 produced, the numerator with *the tokens it
matched listed out*, the denominator, the arithmetic, the predicate and the
verdict --- plus what each of the six registered misreadings would have
recorded instead.

The cards are chosen to be worth reading. Selection is coverage-greedy per
family: every numerator-and-form pair, every phenomenon the responses actually
exhibit, both margin classes, and every misreading that discriminates anywhere.
An item where all six readings agree cannot tell you whether the verifier is
right, and is not shown for its own sake.

**This is not §10.3 and its output is not an agreement rate.** You see the
verdict before you answer, so the numbers here measure nothing about
human-verifier agreement and must never be reported as if they did. What comes
out is a **defect worklist**: cards where a person read the derivation and said
it counted the wrong thing, grouped by which component was wrong. Acting on one
is a change to the verifier and carries everything §10.2 and
`CHANGES_SCIENTIFIC.md` require of one --- including that the verifier hash
moves and the evidence bound to the old hash has to be re-derived.

    python3 tools/v4r3_verifier_audit.py build
    python3 tools/v4r3_verifier_audit.py inspect --resume
    python3 tools/v4r3_verifier_audit.py report
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

from dci1v4.protocol.hashing import canonical_json, sha_text     # noqa: E402
from dci1v4r3 import CLASSIFICATION                              # noqa: E402
from dci1v4r3.stages.human_audit import natural_pool             # noqa: E402
from dci1v4r3.stages.verifier_audit import (                     # noqa: E402
    VERDICT_OF_KEY, card, select,
)
from dci1v4r3.verifiers import verifier_source_hash              # noqa: E402

ROOT = DCI1 / "reports" / "dci1v4r3" / "verifier_audit"
CARDS = ROOT / "cards.json"
WRAP = 78

#: When a derivation is wrong, *what* is wrong. The worklist is only useful if
#: it says which component to go and look at.
COMPONENTS = {
    "s": "segmentation --- the word list is not what §7.3 describes",
    "n": "numerator --- it counted the wrong things",
    "d": "denominator --- the rate is over the wrong base",
    "t": "threshold or direction --- the predicate is applied wrongly",
    "v": "vacuity or grading --- the pass/vacuity rule is wrong here",
    "w": "wording --- the instruction does not mean what the predicate does",
    "o": "other --- see the note",
}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=DCI1,
                          capture_output=True, text=True,
                          check=False).stdout.strip()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(DCI1))
    except ValueError:
        return str(path)


def _records(annotator: str) -> Path:
    return ROOT / "records" / f"{annotator}.jsonl"


def _read(annotator: str) -> list[dict[str, Any]]:
    path = _records(annotator)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def _append(annotator: str, record: dict[str, Any]) -> None:
    path = _records(annotator)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_cards() -> dict[str, Any]:
    if not CARDS.exists():
        raise SystemExit("no cards yet. Run:  python3 tools/"
                         "v4r3_verifier_audit.py build")
    return json.loads(CARDS.read_text())


# ------------------------------------------------------------------- build

def _section_10_3_rows() -> set[str]:
    """Rows the blinded §10.3 plan has already spoken for."""
    key = DCI1 / "reports" / "dci1v4r3" / "human_audit" / "key.json"
    if not key.exists():
        return set()
    return {row["row_id"]
            for row in json.loads(key.read_text())["key"]}


def cmd_build(args) -> int:
    if CARDS.exists() and not args.rebuild:
        existing = _load_cards()
        print(json.dumps({"already_built": True,
                          "cards": len(existing["cards"]),
                          "path": _rel(CARDS)}, indent=1))
        return 0
    pool = natural_pool()
    # Keep A9's frozen §10.3 sample clean. A card shows the verdict, so a row
    # seen here is a row that can no longer be labelled blind; 128 cards out of
    # thirty thousand rows lose nothing by avoiding the 300 that are spoken
    # for, and the alternative is a blind sample with a contaminated fraction.
    reserved = _section_10_3_rows()
    if reserved and not args.ignore_blind_sample:
        pool = [item for item in pool if item["row_id"] not in reserved]
    chosen = select(pool, per_family=args.per_family)
    cards = []
    for index, item in enumerate(chosen, start=1):
        body = card(item["kind"], item["severity"], item["response"],
                    wording_index=item["wording_index"])
        cards.append({
            "card_id": f"vc-{index:03d}-"
                       f"{sha_text(item['row_id'] + str(item['position']))[:8]}",
            "ordinal": index,
            "row_id": item["row_id"], "model_key": item["model_key"],
            "margin": item["margin"], "tags": item["tags"], **body})
    payload = {
        "artifact_type": "v4r3-verifier-audit-cards",
        "classification": CLASSIFICATION,
        "canonical_verifier_hash": verifier_source_hash(),
        "pool_size": len(pool),
        "per_family": args.per_family,
        "excluded_rows_reserved_by_the_blind_section_10_3_sample":
            len(reserved) if not args.ignore_blind_sample else 0,
        "cards": cards,
        "standing": "verifier audit. The verdict is shown, so nothing here is "
                    "a human-verifier agreement rate and none of it is §10.3.",
        "reads": "load 0 and load 1 rows only; no composed cell, no estimand",
        "producing_commit": _commit(),
        "built_at": _now(),
    }
    payload["cards_hash"] = sha_text(canonical_json(cards))
    ROOT.mkdir(parents=True, exist_ok=True)
    CARDS.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")

    covered: set[str] = set()
    for entry in cards:
        covered |= set(entry["tags"])
    print(json.dumps({
        "built": True, "cards": len(cards),
        "families": len({c["instrument"].split(":")[0] for c in cards}),
        "numerator_form_pairs": len([t for t in covered
                                     if t.startswith("numerator-form")]),
        "phenomena": sorted(t.split(":", 1)[1] for t in covered
                            if t.startswith("phenomenon")),
        "misreadings_exercised": sorted(t.split(":", 1)[1] for t in covered
                                        if t.startswith("discriminates")),
        "unfaithful_decompositions": [c["card_id"] for c in cards
                                      if not c["numerator"]["faithful"]],
        "cards_hash": payload["cards_hash"],
        "start_with": "python3 tools/v4r3_verifier_audit.py inspect --resume",
    }, indent=1))
    return 0


# ----------------------------------------------------------------- inspect

def _wrap(body: str, indent: str = "    ") -> None:
    for paragraph in body.split("\n"):
        if not paragraph.strip():
            print()
            continue
        for line in textwrap.wrap(paragraph, WRAP - len(indent)):
            print(f"{indent}{line}")


def _render(entry: dict[str, Any], seen: int, total: int) -> None:
    print()
    print("=" * WRAP)
    print(f"  card {seen} of {total}  ·  {entry['card_id']}  ·  "
          f"{entry['instrument']}")
    print("=" * WRAP)
    print("\n  INSTRUCTION AS THE MODEL RECEIVED IT\n")
    _wrap(entry["instruction"])
    print("\n  RESPONSE\n")
    _wrap(entry["response"] or "(empty)")

    numerator = entry["numerator"]
    print(f"\n  WHAT IT COUNTED  ·  {numerator['statistic']}  ·  "
          f"{numerator['count']} of {numerator['units']} "
          f"{numerator['granularity']}s")
    _wrap(numerator["counts"], "    ")
    if numerator["matched"]:
        shown = numerator["matched"][:60]
        _wrap("matched: " + ", ".join(repr(m) for m in shown)
              + (f"  ... and {len(numerator['matched']) - 60} more"
                 if len(numerator["matched"]) > 60 else ""), "    ")
    elif numerator["granularity"] in ("word", "character"):
        _wrap("matched: nothing", "    ")
    if not numerator["faithful"]:
        _wrap("!! the per-unit probes do not sum to the whole-text count, so "
              "this decomposition is NOT a faithful picture of what the "
              "verifier did. Treat the listing with suspicion and the count "
              "as authoritative.", "    ")

    print(f"\n  SEGMENTATION  ·  {entry['segmentation']['words']} words")
    _wrap(entry["segmentation"]["convention"], "    ")

    if entry["denominator"]["value"] is not None:
        print(f"\n  DENOMINATOR  ·  {entry['denominator']['value']}")
        _wrap(entry["denominator"]["is"], "    ")

    print("\n  ARITHMETIC\n")
    _wrap(entry["derived"]["arithmetic"])
    print("\n  PREDICATE\n")
    _wrap(f"{entry['predicate']['form']}: "
          f"{entry['predicate']['statement']}")
    print(f"\n  VERDICT  ·  {entry['verdict']}"
          f"   (graded {entry['graded']}, "
          f"non-vacuous {entry['non_vacuous']})")
    if entry["discriminates"]:
        print(f"\n  a different reading would flip this: "
              f"{', '.join(entry['discriminates'])}")
    print()


def cmd_inspect(args) -> int:
    payload = _load_cards()
    cards = payload["cards"]
    if sha_text(canonical_json(cards)) != payload["cards_hash"]:
        raise SystemExit("the card set's hash has moved since it was built")
    annotator = args.annotator
    done = {r["card_id"] for r in _read(annotator)}
    pending = [c for c in cards if c["card_id"] not in done]
    if args.only:
        pending = [c for c in cards if c["card_id"] in set(args.only)]
    if not pending:
        print("every card is answered. Run:  python3 tools/"
              "v4r3_verifier_audit.py report")
        return 0
    if not sys.stdin.isatty():                     # pragma: no cover
        raise SystemExit("inspect is interactive; run it in a terminal")

    print(__doc__.split("\n\n")[1])
    print(f"\n  {len(done)}/{len(cards)} answered  ·  {len(pending)} to go")
    print("\n  y = the derivation is correct    n = it is wrong"
          "    u = unsure    q = save and quit\n")

    for entry in pending:
        _render(entry, entry["ordinal"], len(cards))
        while True:
            try:
                answer = input("  is this derivation correct? "
                               "[y/n/u/q] > ").strip().lower()
            except EOFError:
                answer = "q"
            if answer == "q":
                print("\n  saved. Resume with:  python3 tools/"
                      "v4r3_verifier_audit.py inspect --resume\n")
                return 0
            if answer not in VERDICT_OF_KEY:
                print("  answer y, n, u or q.")
                continue
            component = None
            if answer == "n":
                print()
                for key, text in COMPONENTS.items():
                    print(f"    {key}  {text}")
                while component is None:
                    choice = input("\n  which component is wrong? > "
                                   ).strip().lower()
                    component = COMPONENTS.get(choice)
                    if component is None:
                        print(f"  choose one of "
                              f"{', '.join(COMPONENTS)}.")
            note = input("  note (optional) > ").strip()
            _append(annotator, {
                "card_id": entry["card_id"], "ordinal": entry["ordinal"],
                "instrument": entry["instrument"],
                "annotator": annotator,
                "assessment": VERDICT_OF_KEY[answer],
                "component": component,
                "note": note or None,
                "cards_hash": payload["cards_hash"],
                "verifier_hash": payload["canonical_verifier_hash"],
                "recorded_at": _now()})
            answered = len({r["card_id"] for r in _read(annotator)})
            print(f"  recorded.  {answered}/{len(cards)}.")
            break
    print(f"\n  all {len(cards)} cards answered. Run:  python3 tools/"
          f"v4r3_verifier_audit.py report\n")
    return 0


# ------------------------------------------------------------------ report

def cmd_report(args) -> int:
    payload = _load_cards()
    cards = {c["card_id"]: c for c in payload["cards"]}
    latest: dict[str, dict[str, Any]] = {}
    for record in _read(args.annotator):
        latest[record["card_id"]] = record

    wrong = [dict(r) for r in latest.values() if r["assessment"] == "wrong"]
    unsure = [dict(r) for r in latest.values() if r["assessment"] == "unsure"]
    for row in wrong + unsure:
        entry = cards[row["card_id"]]
        row.update({"statistic": entry["numerator"]["statistic"],
                    "form": entry["predicate"]["form"],
                    "instruction": entry["instruction"],
                    "verdict": entry["verdict"],
                    "matched": entry["numerator"]["matched"][:20],
                    "tags": entry["tags"]})

    def _by(rows, field):
        out: dict[str, int] = {}
        for row in rows:
            out[str(row.get(field))] = out.get(str(row.get(field)), 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    report = {
        "artifact_type": "v4r3-verifier-audit-report",
        "classification": CLASSIFICATION,
        "annotator": args.annotator,
        "canonical_verifier_hash": payload["canonical_verifier_hash"],
        "cards_hash": payload["cards_hash"],
        "cards": len(cards), "assessed": len(latest),
        "complete": len(latest) == len(cards),
        "correct": sum(1 for r in latest.values()
                       if r["assessment"] == "correct"),
        "wrong": len(wrong), "unsure": len(unsure),
        "worklist_by_component": _by(wrong, "component"),
        "worklist_by_numerator": _by(wrong, "statistic"),
        "worklist_by_form": _by(wrong, "form"),
        "wrong_cards": sorted(wrong, key=lambda r: r["ordinal"]),
        "unsure_cards": sorted(unsure, key=lambda r: r["ordinal"]),
        "standing": "a verifier audit, not §10.3. The verdict was visible "
                    "before each assessment, so no figure here is a "
                    "human-verifier agreement rate and none may be reported "
                    "as one.",
        "what_a_finding_costs": "changing a verifier changes the canonical "
                                "hash, which every §10.2 artifact, every "
                                "stage record and all 30,144 stored verdicts "
                                "are bound to. A confirmed defect is a "
                                "CHANGES_SCIENTIFIC.md entry, a re-run of "
                                "§10.2's evidence, and a re-derivation of "
                                "anything measured under the old hash.",
        "producing_commit": _commit(),
        "generated_at": _now(),
    }
    out = ROOT / f"report_{args.annotator}.json"
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("wrong_cards", "unsure_cards")}, indent=1))
    print(f"\nwrote {_rel(out)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="choose and freeze the cards")
    build.add_argument("--per-family", type=int, default=4)
    build.add_argument("--rebuild", action="store_true")
    build.add_argument("--ignore-blind-sample", action="store_true",
                       help="draw from rows the frozen §10.3 plan reserved; "
                            "doing so spoils those items for blind labelling")
    build.set_defaults(func=cmd_build)

    inspect = sub.add_parser("inspect", help="read derivations, mark them")
    inspect.add_argument("--annotator", default="Bryan")
    inspect.add_argument("--resume", action="store_true")
    inspect.add_argument("--only", nargs="*", metavar="CARD_ID")
    inspect.set_defaults(func=cmd_inspect)

    report = sub.add_parser("report", help="the defect worklist")
    report.add_argument("--annotator", default="Bryan")
    report.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
