"""The 528 released v3 topics and their executable authoring rules (§6).

The bank file carries each topic's set assignment: 144 calibration and 384
confirmatory topics, 12 and 32 per subject stratum. The 96 sequestered
topics are NOT here — only their opaque identities exist to this package
(topics/sequestered.py). Every load re-validates structure and the §6
authoring rules, so a defective bank cannot silently enter the design.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import (
    CALIBRATION_PER_AREA,
    CONFIRMATORY_PER_AREA,
    SUBJECT_AREAS,
)

DATA_PATH = Path(__file__).resolve().parent / "data" / "topics_v3.json"

#: Vocabulary that would collide with the study's lexical constraints
#: (§6 rule four). Word-boundary matched, case-insensitive.
BANNED_PATTERN = re.compile(
    r"\b(letter|letters|word|words|wording|spell|spelling|spelled|spelt|"
    r"character|characters|syllable|syllables|vowel|vowels|consonant|"
    r"consonants|alphabet|alphabetic|alphabetical)\b", re.IGNORECASE)

SETS = ("calibration", "confirmatory")


def validate_bank(topics: list[dict[str, Any]]) -> None:
    expected = {("calibration",): CALIBRATION_PER_AREA,
                ("confirmatory",): CONFIRMATORY_PER_AREA}
    counts: dict[tuple[str, str], int] = {}
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    for topic in topics:
        area, question, topic_id, set_name = (
            topic["area"], topic["question"], topic["topic_id"], topic["set"])
        if area not in SUBJECT_AREAS:
            raise ProtocolError(f"{topic_id}: undeclared subject area {area!r}")
        if set_name not in SETS:
            raise ProtocolError(f"{topic_id}: undeclared set {set_name!r}")
        counts[(area, set_name)] = counts.get((area, set_name), 0) + 1
        if topic_id in seen_ids:
            raise ProtocolError(f"duplicate topic_id {topic_id!r}")
        seen_ids.add(topic_id)
        key = question.strip().lower()
        if key in seen_questions:
            raise ProtocolError(f"{topic_id}: duplicate question text")
        seen_questions.add(key)
        if not question.endswith("?"):
            raise ProtocolError(f"{topic_id}: question must end with '?'")
        if question.count("?") != 1 or "\n" in question:
            raise ProtocolError(f"{topic_id}: question must be one sentence")
        if BANNED_PATTERN.search(question):
            raise ProtocolError(
                f"{topic_id}: question mentions letter/word-shape "
                f"vocabulary: {question!r}")
        if re.search(r"[\d\"“”‘’]", question):
            raise ProtocolError(
                f"{topic_id}: digits or quotation marks in question")
        if re.search(r"(?<![A-Za-z])'", question):
            raise ProtocolError(f"{topic_id}: quotation-style apostrophe")
        words = question.split()
        if not 6 <= len(words) <= 30:
            raise ProtocolError(f"{topic_id}: question length {len(words)} "
                                f"outside 6..30 tokens")
    for area in SUBJECT_AREAS:
        for set_name, per_area in (("calibration", CALIBRATION_PER_AREA),
                                   ("confirmatory", CONFIRMATORY_PER_AREA)):
            if counts.get((area, set_name), 0) != per_area:
                raise ProtocolError(
                    f"{area!r} has {counts.get((area, set_name), 0)} "
                    f"{set_name} topics, not {per_area}")


def load_bank(path: Path | None = None) -> list[dict[str, Any]]:
    topics = json.loads((path or DATA_PATH).read_text())
    validate_bank(topics)
    return topics
