"""Has any v4 generation touched a reserved topic set? (§6.2)

NOT a stage. §6.2 reserves three of the five v4 topic sets:

* **composed validation**, 24 topics --- Gate 4's own evidence set (§13.6);
* **confirmatory**, 384 topics --- the frozen experiment;
* **sequestered**, 96 topics --- a future uncontaminated rerun, and inaccessible
  to the design and execution team by construction.

Four non-confirmatory screens have run since the last audit, one of them
generating on 120 blocks. Reading their source shows they exclude the reserved
sets; this reads the generated rows instead, so the answer does not depend on
the screens being what they say they are.

Every row is attributed by the question text that reaches the prompt, which is
the only topic identifier a row carries.

Usage:
  PYTHONPATH=src python tools/topic_reservation_audit_v4.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.topics.split import split_topics                      # noqa: E402

OUT = DCI1 / "reports" / "section_13_2_v4"
RESERVED = ("composed", "confirmatory", "sequestered")


def audit() -> dict:
    split = split_topics()
    question_to_set = {t["question"]: name
                       for name, rows in split.items() for t in rows}
    # The sequestered 96 are hash-only by construction, so they cannot appear
    # in this map and cannot be matched by text. Their protection is that they
    # are not in the split at all; recorded rather than silently omitted.
    by_set: Counter[str] = Counter()
    files, rows_read = 0, 0
    offenders: list[str] = []
    for root in (DCI1 / "evidence", DCI1 / "durable_root"):
        for path in sorted(root.rglob("rows.jsonl")):
            if "v4" not in str(path):
                continue
            files += 1
            hit_here: set[str] = set()
            for line in path.open():
                if not line.strip():
                    continue
                try:
                    prompt = json.loads(line).get("rendered_prompt", "")
                except json.JSONDecodeError:
                    continue
                rows_read += 1
                name = None
                for chunk in prompt.split("\n"):
                    chunk = chunk.strip()
                    if chunk in question_to_set:
                        name = question_to_set[chunk]
                        break
                by_set[name or "no-v4-topic"] += 1
                if name in RESERVED:
                    hit_here.add(name)
            if hit_here:
                offenders.append(f"{path.relative_to(DCI1)}: {sorted(hit_here)}")
    return {
        "artifact": "§6.2 reserved-topic-set audit",
        "classification": ("integrity audit over generated rows. Reads only; "
                           "writes no evidence and approves nothing."),
        "files_scanned": files, "rows_read": rows_read,
        "rows_by_topic_set": dict(sorted(by_set.items())),
        "reserved_sets": {
            "composed": {"topics": len(split["composed"]),
                         "purpose": "Gate 4 composed-headroom validation (§13.6)",
                         "rows_generated": by_set.get("composed", 0)},
            "confirmatory": {"topics": len(split["confirmatory"]),
                             "purpose": "the frozen confirmatory experiment",
                             "rows_generated": by_set.get("confirmatory", 0)},
            "sequestered": {"topics": 96,
                            "purpose": "a future uncontaminated rerun (§6.2)",
                            "rows_generated": "not addressable: the sequestered "
                                              "text is hash-only and is absent "
                                              "from the split this audit reads"},
        },
        "offending_files": offenders,
        "unspent": not offenders,
        "note": ("rows attributed to 'no-v4-topic' are the Gate 0 procedural "
                 "pilot's fixed probes, which carry no v4 topic by design"),
    }


def main() -> int:
    payload = audit()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "topic_reservation_audit.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in
                      ("files_scanned", "rows_read", "rows_by_topic_set",
                       "unspent", "offending_files")}, indent=1))
    print(f"written: {path.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
