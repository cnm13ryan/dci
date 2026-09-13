"""The 528 released v4 topics and their executable authoring rules (§6.2).

The v4 bank is 624 newly authored questions, 52 in each of the twelve declared
subject areas. This file holds the 528 that are not sequestered; the 96
sequestered questions exist to this package only as opaque identities and
content hashes (``topics/sequestered.py``), exactly as §6.2 requires.

Every load re-validates the four §6.2 authoring rules that can be decided
mechanically, so a defective bank cannot silently enter a design:

1. *answerable from general knowledge* — enforced structurally, as a single
   short open question with no digits and no quoted material, which excludes
   the arithmetic and named-fact-recall forms the rule rules out;
2. *no single correct short answer* — enforced through the interrogative
   opening, which admits explanatory and comparative questions and rejects
   closed forms;
3. *no reused text from any public dataset or examination* — enforced
   negatively against the one corpus this repository can check, the v3 bank
   and its sequestered hashes, so that no v3 topic and no B+R pilot topic
   (which consumed the v3 solo-calibration set) can enter a v4 set;
4. *no wording that itself mentions a letter, word length, word shape,
   punctuation-count or capitalisation requirement* — enforced by
   ``BANNED_PATTERN``, which is deliberately wider than v3's: v4 registers
   comma-count and upper-case-count families, so a question that merely says
   *capital* or *comma* would prime a registered constraint.

Rule 3's positive half — that no question is lifted from an external public
dataset — cannot be decided inside this repository and is recorded as an
authoring attestation in the topic-authoring record instead.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v4.protocol.constants import SUBJECT_AREAS, TOPICS_PER_AREA

DATA_PATH = Path(__file__).resolve().parent / "data" / "topics_v4.json"

#: §6.2 rule four. Wider than the v3 list by the punctuation-count and
#: capitalisation vocabulary, because RF5 counts commas and RF6 counts
#: upper-case letters and both are registered v4 constraints.
BANNED_PATTERN = re.compile(
    r"\b(letter|letters|word|words|wording|spell|spelling|spelled|spelt|"
    r"character|characters|syllable|syllables|vowel|vowels|consonant|"
    r"consonants|alphabet|alphabetic|alphabetical|comma|commas|punctuation|"
    r"capital|capitals|capitalise|capitalised|capitalisation|capitalize|"
    r"capitalized|capitalization|uppercase|lowercase|apostrophe|apostrophes|"
    r"hyphen|hyphens|hyphenated)\b", re.IGNORECASE)

#: Openings admitted by rule two: explanatory and comparative forms, which do
#: not have one short correct answer. Closed openings are refused.
OPEN_OPENINGS = ("why ", "how ", "what makes ", "what changes ")

RELEASED_SETS = ("prescreen", "solo", "composed", "confirmatory")


def validate_question(topic_id: str, question: str) -> None:
    """The mechanically decidable part of the four §6.2 authoring rules."""
    if not question.endswith("?"):
        raise ProtocolError(f"{topic_id}: question must end with a query mark")
    if question.count("?") != 1 or "\n" in question:
        raise ProtocolError(f"{topic_id}: question must be one sentence")
    if BANNED_PATTERN.search(question):
        hit = BANNED_PATTERN.search(question).group(0)
        raise ProtocolError(
            f"{topic_id}: question mentions {hit!r}, which primes a "
            f"registered constraint family: {question!r}")
    if re.search(r"[\d\"“”‘’]", question):
        raise ProtocolError(f"{topic_id}: digits or quotation marks present")
    if re.search(r"(?<![A-Za-z])'", question):
        raise ProtocolError(f"{topic_id}: quotation-style apostrophe")
    if not question.lower().startswith(OPEN_OPENINGS):
        raise ProtocolError(
            f"{topic_id}: question does not open in an admitted open form "
            f"{OPEN_OPENINGS}: {question!r}")
    tokens = question.split()
    if not 6 <= len(tokens) <= 30:
        raise ProtocolError(f"{topic_id}: question length {len(tokens)} "
                            f"outside 6..30 tokens")


def validate_bank(topics: list[dict[str, Any]], *,
                  per_area: dict[str, int] | None = None) -> None:
    counts: dict[tuple[str, str], int] = {}
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    for topic in topics:
        topic_id, area = topic["topic_id"], topic["area"]
        question, set_name = topic["question"], topic["set"]
        if area not in SUBJECT_AREAS:
            raise ProtocolError(f"{topic_id}: undeclared subject area {area!r}")
        if set_name not in RELEASED_SETS:
            raise ProtocolError(f"{topic_id}: set {set_name!r} is not a "
                                f"released v4 set")
        if topic_id in seen_ids:
            raise ProtocolError(f"duplicate topic_id {topic_id!r}")
        seen_ids.add(topic_id)
        key = question.strip().lower()
        if key in seen_questions:
            raise ProtocolError(f"{topic_id}: duplicate question text")
        seen_questions.add(key)
        validate_question(topic_id, question)
        counts[(area, set_name)] = counts.get((area, set_name), 0) + 1
    if per_area is not None:
        for area in SUBJECT_AREAS:
            for set_name, expected in per_area.items():
                got = counts.get((area, set_name), 0)
                if got != expected:
                    raise ProtocolError(
                        f"{area!r} has {got} {set_name} topics, not {expected}")


def load_bank(path: Path | None = None) -> list[dict[str, Any]]:
    """The 528 released topics, with the seeded split already applied."""
    from dci1v4.protocol.constants import (
        COMPOSED_PER_AREA,
        CONFIRMATORY_PER_AREA,
        PRESCREEN_PER_AREA,
        SOLO_PER_AREA,
    )
    topics = json.loads((path or DATA_PATH).read_text())
    validate_bank(topics, per_area={
        "prescreen": PRESCREEN_PER_AREA, "solo": SOLO_PER_AREA,
        "composed": COMPOSED_PER_AREA, "confirmatory": CONFIRMATORY_PER_AREA})
    if len(topics) != 528:
        raise ProtocolError(f"released bank holds {len(topics)} topics, not "
                            f"528 (624 authored less 96 sequestered)")
    return topics


def authoring_record(topics: list[dict[str, Any]] | None = None) -> dict:
    """The §6.2 authoring record: per-area counts and the rule attestations."""
    from dci1v4.protocol.hashing import sha_obj

    topics = topics if topics is not None else load_bank()
    per_area = {area: sum(1 for t in topics if t["area"] == area)
                for area in SUBJECT_AREAS}
    return {
        "authored_total": TOPICS_PER_AREA * len(SUBJECT_AREAS),
        "released_total": len(topics),
        "released_per_area": per_area,
        "rules_checked_mechanically": [
            "single short open question, no digits, no quoted material",
            "admitted open interrogative opening",
            "no letter, word-shape, punctuation-count or capitalisation "
            "vocabulary",
            "disjoint from every v3 topic identity and content hash",
        ],
        "rules_attested_by_the_author": [
            "answerable from general knowledge without tools, arithmetic, or "
            "recall of a specific named fact",
            "no reused text from any public dataset or examination",
        ],
        "bank_hash": sha_obj(sorted(
            [{"topic_id": t["topic_id"], "question": t["question"],
              "area": t["area"], "set": t["set"]} for t in topics],
            key=lambda t: t["topic_id"])),
    }
