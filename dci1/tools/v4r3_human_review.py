"""Blind human review of the instruments §7.0-R3 added.

    python3 tools/v4r3_human_review.py build --items 25
    python3 tools/v4r3_human_review.py review --annotator <name>
    python3 tools/v4r3_human_review.py report  --annotator <name>

`build` writes two files. The **packet** carries an opaque id, an instruction
and an answer, and nothing else. The **key** carries the family, the severity,
the verifier's verdict and the defect each case separates, and `review` never
opens it.

`review` refuses to run unless it is talking to a terminal, so a piped stream
cannot answer for a person; it appends each judgment the moment it is given, so
a judgment cannot be revised once the next item is seen; and it reveals nothing
until every item is committed.

**What this can and cannot do.** The v3 record's 56-item blind review found the
deterministic verifier agreeing with a human on 56 of 56 while every autorater
configuration scored between 71 and 98 per cent --- and all 56 items were
`solo:A:n`. This packet points a human at the ten families the amendment added,
which have no human label anywhere. It is not §10.3: §10.3 wants an annotator
independent of the design and analysis team, marking features on natural
responses, at min(150, N_c) per verifier class, and says in terms that
author-performed labels are never described as independent validation. Nothing
here writes a measurement basis and nothing here offers a way to.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.protocol.hashing import canonical_json, sha_text        # noqa: E402
from dci1v4r3 import CLASSIFICATION                                 # noqa: E402
from dci1v4r3.stages.human_review import (                          # noqa: E402
    REVIEWER_BRIEF, agreement_report, assert_packet_blinded, build_packet,
)
from dci1v4r3.verifiers import verifier_source_hash                 # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r3" / "human_review"
PACKET = OUT / "packet.json"
KEY = OUT / "key.json"
BRIEF = OUT / "REVIEWER_BRIEF.md"

_CHOICES = {"s": "SATISFIES", "v": "VIOLATES", "u": "UNSURE"}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _records(annotator: str) -> Path:
    return OUT / "records" / f"{annotator}.jsonl"


def cmd_build(args) -> int:
    if PACKET.exists() and not args.replace:
        raise SystemExit(f"{PACKET.relative_to(DCI1)} already exists; a packet "
                         "is built once. Pass --replace only if no judgment "
                         "has been recorded against it.")
    if _records_exist():
        raise SystemExit("judgments already exist against a packet; building "
                         "another would make them unattributable")
    built = build_packet(args.items)
    OUT.mkdir(parents=True, exist_ok=True)
    PACKET.write_text(json.dumps({
        "artifact_type": "v4r3-human-review-packet",
        "classification": CLASSIFICATION,
        "verifier_hash": verifier_source_hash(),
        "built_at": _now(), "items": built["items"],
        "packet_hash": built["packet_hash"],
        "blinded": "the family, severity, verdict and defect live in key.json",
        "packet": built["packet"]}, indent=1) + "\n")
    KEY.write_text(json.dumps({
        "artifact_type": "v4r3-human-review-key",
        "classification": CLASSIFICATION,
        "verifier_hash": verifier_source_hash(),
        "packet_hash": built["packet_hash"], "key_hash": built["key_hash"],
        "key": built["key"]}, indent=1) + "\n")
    BRIEF.write_text(REVIEWER_BRIEF)
    print(json.dumps({k: v for k, v in built.items()
                      if k not in ("packet", "key")}, indent=1))
    print(f"\nwrote {PACKET.relative_to(DCI1)}"
          f"\n      {KEY.relative_to(DCI1)}   (do not open before reviewing)"
          f"\n      {BRIEF.relative_to(DCI1)}"
          f"\n\nreview with: python3 tools/v4r3_human_review.py review "
          f"--annotator <name>")
    return 0


def _records_exist() -> bool:
    directory = OUT / "records"
    return directory.exists() and any(directory.glob("*.jsonl"))


def _load_packet() -> list[dict[str, Any]]:
    if not PACKET.exists():
        raise SystemExit(f"no packet at {PACKET.relative_to(DCI1)}; build one")
    payload = json.loads(PACKET.read_text())
    packet = payload["packet"]
    assert_packet_blinded(packet)
    if sha_text(canonical_json(packet)) != payload["packet_hash"]:
        raise SystemExit("the packet's contents do not match its hash")
    return packet


def _done(annotator: str) -> dict[str, str]:
    path = _records(annotator)
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["item_id"]] = row["label"]
    return out


def cmd_review(args) -> int:
    if not sys.stdin.isatty():
        raise SystemExit("this command reads a person's judgment and refuses "
                         "a pipe; run it in a terminal")
    packet = _load_packet()
    already = _done(args.annotator)
    path = _records(args.annotator)
    path.parent.mkdir(parents=True, exist_ok=True)

    remaining = [i for i in packet if i["item_id"] not in already]
    print(BRIEF.read_text())
    print(f"{len(already)} of {len(packet)} already judged; "
          f"{len(remaining)} to go.\n")
    for position, item in enumerate(remaining, 1):
        print("=" * 68)
        print(f"[{position}/{len(remaining)}]  {item['item_id']}")
        print(f"\nINSTRUCTION: {item['instruction']}")
        print("\nANSWER, between the markers, and it may be empty:")
        print("[begin answer]")
        print(item["answer"])
        print("[end answer]\n")
        while True:
            choice = input("  (s)atisfies / (v)iolates / (u)nsure > ").strip().lower()
            if choice in _CHOICES:
                break
            print("  answer s, v or u")
        row = {"item_id": item["item_id"], "label": _CHOICES[choice],
               "annotator": args.annotator, "synthetic": False,
               "set": "r3_instruments", "recorded_at": _now(),
               "answer_sha256": hashlib.sha256(
                   item["answer"].encode()).hexdigest()}
        if row["answer_sha256"] != item["answer_sha256"]:
            raise SystemExit(f"{item['item_id']}: the answer does not match "
                             "its recorded hash; the packet has been edited")
        with path.open("a") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        print("  recorded.\n")
    print(f"all {len(packet)} items committed to "
          f"{path.relative_to(DCI1)}\n"
          f"report with: python3 tools/v4r3_human_review.py report "
          f"--annotator {args.annotator}")
    return 0


def cmd_report(args) -> int:
    if not KEY.exists():
        raise SystemExit("no key; build a packet first")
    packet = _load_packet()
    key_payload = json.loads(KEY.read_text())
    labels = _done(args.annotator)
    if len(labels) < len(packet) and not args.partial:
        raise SystemExit(
            f"{len(labels)} of {len(packet)} items judged. The key is revealed "
            "only after every item is committed; pass --partial if you have "
            "stopped deliberately and want the partial report.")
    report = agreement_report(key_payload["key"], labels)
    report.update({
        "artifact_type": "v4r3-human-review-report",
        "classification": CLASSIFICATION,
        "annotator": args.annotator,
        "independent_of_design_team": False,
        "verifier_hash": verifier_source_hash(),
        "packet_hash": key_payload["packet_hash"],
        "key_hash": key_payload["key_hash"],
        "items": len(packet), "partial": len(labels) < len(packet),
        "reported_at": _now(),
    })
    path = OUT / f"report_{args.annotator}.json"
    path.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in (
        "items", "compared", "unsure", "agreed", "disagreements", "agreement",
        "wilson_upper_on_disagreement", "section_10_3_threshold",
        "meets_threshold_numerically", "per_statistic")}, indent=1))
    if report["discordant"]:
        print("\ndiscordant items:")
        for row in report["discordant"]:
            print(f"  {row['item_id']}  {row['family']}:{row['severity']}  "
                  f"human {row['human']} / verifier {row['verifier']}  "
                  f"({row['covers']})")
    print(f"\nwrote {path.relative_to(DCI1)}")
    print(f"standing: {report['standing']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--items", type=int, default=25)
    build.add_argument("--replace", action="store_true")
    build.set_defaults(func=cmd_build)
    review = sub.add_parser("review")
    review.add_argument("--annotator", required=True)
    review.set_defaults(func=cmd_review)
    report = sub.add_parser("report")
    report.add_argument("--annotator", required=True)
    report.add_argument("--partial", action="store_true")
    report.set_defaults(func=cmd_report)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
