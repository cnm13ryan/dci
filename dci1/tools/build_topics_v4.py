"""Access-control build of the v4 topic bank (run once, by the researcher).

NOT part of the dci1v4 package. This tool is the authorised access-control
process of prereg v4r2 §6.2: it reads the authored 624-question source, runs
the seeded five-way per-stratum cut, and emits

  * src/dci1v4/topics/data/topics_v4.json      — 528 released topics with
    their set assignment (prescreen | solo | composed | confirmatory);
  * src/dci1v4/topics/data/sequestered_v4.json — 96 opaque identities with
    stratum and content hash only. No sequestered text is written anywhere
    inside the package.

It then moves the authoring source into the durable access-controlled store,
outside version control, so a future uncontaminated rerun remains possible
while no execution path can reach the sequestered text.

The tool also refuses any question that collides with a v3 topic identity,
a v3 question text, or a v3 sequestered content hash — the one corpus this
repository can check §6.2 rule three against. It reads the v3 data files as
data; it imports no v3 code.

Usage:  PYTHONPATH=src python tools/build_topics_v4.py --source <authored.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.protocol.constants import SUBJECT_AREAS, TOPICS_PER_AREA  # noqa: E402
from dci1v4.topics.bank import validate_question  # noqa: E402
from dci1v4.topics.split import cut_area  # noqa: E402

OUT_DIR = DCI1 / "src" / "dci1v4" / "topics" / "data"
V3_BANK = DCI1 / "src" / "dci1v3" / "topics" / "data" / "topics_v3.json"
V3_SEQUESTERED = (DCI1 / "src" / "dci1v3" / "topics" / "data"
                  / "sequestered_v3.json")
DURABLE_SOURCE = (DCI1 / "durable_root" / "dci1-v4" / "sequestered_source")


def slug(area: str) -> str:
    return area.replace(" ", "-")


def v3_exclusions() -> tuple[set[str], set[str]]:
    """v3 question texts and content hashes, read as data (§6.2 rule three)."""
    questions = {t["question"].strip().lower()
                 for t in json.loads(V3_BANK.read_text())}
    hashes = {hashlib.sha256(t["question"].encode()).hexdigest()
              for t in json.loads(V3_BANK.read_text())}
    hashes |= {e["sha256"]
               for e in json.loads(V3_SEQUESTERED.read_text())}
    return questions, hashes


def build(source: Path) -> dict:
    authored = json.loads(source.read_text())
    if sorted(authored) != sorted(SUBJECT_AREAS):
        raise SystemExit(f"authored source must carry exactly the twelve "
                         f"declared strata, got {sorted(authored)}")
    v3_questions, v3_hashes = v3_exclusions()

    released: list[dict] = []
    sequestered: list[dict] = []
    for area in SUBJECT_AREAS:
        questions = authored[area]
        if len(questions) != TOPICS_PER_AREA:
            raise SystemExit(f"{area!r} carries {len(questions)} questions")
        cut = cut_area(questions, area)
        index = {q: i for i, q in enumerate(sorted(questions))}
        for set_name, members in cut.items():
            for question in members:
                topic_id = f"{slug(area)}-{index[question]:02d}"
                validate_question(topic_id, question)
                digest = hashlib.sha256(question.encode()).hexdigest()
                if question.strip().lower() in v3_questions:
                    raise SystemExit(f"{topic_id}: reuses a v3 question")
                if digest in v3_hashes:
                    raise SystemExit(f"{topic_id}: collides with a v3 or v3 "
                                     f"sequestered content hash")
                if set_name == "sequestered":
                    sequestered.append({"topic_id": topic_id, "area": area,
                                        "sha256": digest})
                else:
                    released.append({"topic_id": topic_id, "area": area,
                                     "question": question, "set": set_name})

    released.sort(key=lambda t: t["topic_id"])
    sequestered.sort(key=lambda t: t["topic_id"])
    if len(released) != 528 or len(sequestered) != 96:
        raise SystemExit(f"cut produced {len(released)} released and "
                         f"{len(sequestered)} sequestered topics")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "topics_v4.json").write_text(
        json.dumps(released, indent=2, ensure_ascii=False) + "\n")
    (OUT_DIR / "sequestered_v4.json").write_text(
        json.dumps(sequestered, indent=2, ensure_ascii=False) + "\n")

    DURABLE_SOURCE.mkdir(parents=True, exist_ok=True)
    retained = DURABLE_SOURCE / "authored_624.json"
    shutil.copyfile(source, retained)
    return {"released": len(released), "sequestered": len(sequestered),
            "retained_source": str(retained)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True,
                        help="authored 624-question JSON, area -> [question]")
    args = parser.parse_args()
    report = build(Path(args.source))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
