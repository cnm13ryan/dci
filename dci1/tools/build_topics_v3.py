"""Access-control build of the v3 topic bank (run once, by the researcher).

NOT part of the dci1v3 package. This tool is the authorised access-control
process of prereg v3 §6/§19: it reads the v2 bank and its frozen split,
carries the 384 confirmatory and 96 calibration topics forward (changelog:
"Preserved 384 confirmatory and 96 sequestered topics"; "Expanded calibration
from 96 to 144"), merges the 48 newly authored calibration topics, and emits

  * src/dci1v3/topics/data/topics_v3.json   — 528 released topics with their
    set assignment (calibration | confirmatory);
  * src/dci1v3/topics/data/sequestered_v3.json — 96 opaque identities with
    stratum and content hash only. No sequestered text is written anywhere.

The dci1v3 package never imports v2 code and never sees sequestered text;
only this tool touches both, exactly once, before any v3 artifact exists.

Usage:  PYTHONPATH=src .venv/bin/python tools/build_topics_v3.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1.topics.split import split_bank  # v2 — permitted here only  # noqa: E402

OUT_DIR = DCI1 / "src" / "dci1v3" / "topics" / "data"
NEW_TOPICS = DCI1 / "tools" / "new_topics_v3.json"

BANNED = re.compile(
    r"\b(letter|letters|word|words|wording|spell|spelling|spelled|spelt|"
    r"character|characters|syllable|syllables|vowel|vowels|consonant|"
    r"consonants|alphabet|alphabetic|alphabetical)\b", re.IGNORECASE)


def check_question(topic_id: str, question: str) -> None:
    assert question.endswith("?"), topic_id
    assert question.count("?") == 1 and "\n" not in question, topic_id
    assert not BANNED.search(question), (topic_id, question)
    assert not re.search(r"[\d\"“”‘’]", question), topic_id
    assert not re.search(r"(?<![A-Za-z])'", question), topic_id
    assert 6 <= len(question.split()) <= 30, topic_id


def main() -> None:
    split = split_bank()
    new = json.loads(NEW_TOPICS.read_text())

    released: list[dict] = []
    seen_questions: set[str] = set()
    for topic in split["calibration"]:
        released.append({**topic, "set": "calibration"})
    for topic in split["confirmatory"]:
        released.append({**topic, "set": "confirmatory"})
    for row in released:
        seen_questions.add(row["question"].strip().lower())

    sequestered = []
    for topic in split["sequestered"]:
        sequestered.append({
            "topic_id": topic["topic_id"], "area": topic["area"],
            "sha256": hashlib.sha256(
                topic["question"].encode("utf-8")).hexdigest()})

    for area, questions in new.items():
        assert len(questions) == 4, area
        slug = area.replace(" ", "-")
        for offset, question in enumerate(questions):
            topic_id = f"{slug}-{48 + offset:02d}"
            check_question(topic_id, question)
            key = question.strip().lower()
            assert key not in seen_questions, (topic_id, "duplicate")
            seen_questions.add(key)
            released.append({"topic_id": topic_id, "area": area,
                             "question": question, "set": "calibration"})

    assert len(released) == 528 and len(sequestered) == 96
    for row in released:  # no released text may equal a sequestered text
        digest = hashlib.sha256(row["question"].encode("utf-8")).hexdigest()
        assert digest not in {s["sha256"] for s in sequestered}, row["topic_id"]

    released.sort(key=lambda r: r["topic_id"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "topics_v3.json").write_text(
        json.dumps(released, indent=2, ensure_ascii=False) + "\n")
    (OUT_DIR / "sequestered_v3.json").write_text(
        json.dumps(sorted(sequestered, key=lambda s: s["topic_id"]),
                   indent=2, ensure_ascii=False) + "\n")
    print(f"released={len(released)} sequestered={len(sequestered)}")


if __name__ == "__main__":
    main()
