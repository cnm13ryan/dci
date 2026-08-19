"""The 576-topic bank (prereg §6) and its executable authoring rules.

Topics were drafted with model assistance and verified by the researcher
against the four §6 rules. The rules with programmatic content are enforced
here on every load, so a defective bank cannot silently enter the design:

* structure — 12 declared subject areas × 48 questions, unique identities;
* no wording mentions any letter, word length, or word-shape requirement
  (word-boundary match against a frozen banned vocabulary);
* single-sentence questions ending in a question mark, without digits or
  quotation marks (which keeps out date-recall and quoted reuse);
* no duplicated question text.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from dci1.protocol.constants import (
    N_TOPICS,
    SUBJECT_AREAS,
    TOPICS_PER_AREA,
    ProtocolError,
)

DATA_PATH = Path(__file__).resolve().parent / "data" / "topics.json"

#: Vocabulary that would collide with the study's lexical constraints (§6
#: rule four). Word-boundary matched, case-insensitive.
BANNED_PATTERN = re.compile(
    r"\b(letter|letters|word|words|wording|spell|spelling|spelled|spelt|"
    r"character|characters|syllable|syllables|vowel|vowels|consonant|"
    r"consonants|alphabet|alphabetic|alphabetical)\b", re.IGNORECASE)


def validate_bank(topics: list[dict[str, Any]]) -> None:
    if len(topics) != N_TOPICS:
        raise ProtocolError(f"topic bank has {len(topics)} entries, "
                            f"not {N_TOPICS}")
    per_area: dict[str, int] = {}
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    for topic in topics:
        area, question, topic_id = (topic["area"], topic["question"],
                                    topic["topic_id"])
        if area not in SUBJECT_AREAS:
            raise ProtocolError(f"{topic_id}: undeclared subject area {area!r}")
        per_area[area] = per_area.get(area, 0) + 1
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
                f"{topic_id}: question mentions letter/word-shape vocabulary: "
                f"{question!r}")
        if re.search(r"[\d\"“”‘’]", question):
            raise ProtocolError(
                f"{topic_id}: digits or quotation marks in question")
        # A straight apostrophe is fine after a letter (possessives,
        # contractions, plural possessives); an apostrophe opening a quotation
        # has a non-letter on its left and is refused.
        if re.search(r"(?<![A-Za-z])'", question):
            raise ProtocolError(f"{topic_id}: quotation-style apostrophe")
        words = question.split()
        if not 6 <= len(words) <= 30:
            raise ProtocolError(f"{topic_id}: question length {len(words)} "
                                f"outside 6..30 tokens")
    for area in SUBJECT_AREAS:
        if per_area.get(area, 0) != TOPICS_PER_AREA:
            raise ProtocolError(
                f"area {area!r} has {per_area.get(area, 0)} questions, "
                f"not {TOPICS_PER_AREA}")


def load_bank(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    if not Path(path).exists():
        raise ProtocolError(f"topic bank missing at {path}")
    topics = json.loads(Path(path).read_text())
    validate_bank(topics)
    return topics
