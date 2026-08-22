"""§6.2's topic bank: 720 questions, and the 96 that do not exist yet.

| Set | Per area | Total | Source | Permitted use |
|---|---:|---:|---|---|
| Pre-screen | 2 | 24 | v4 split, unchanged | cap selection, the high-recall screen, Gate-1 material |
| **Calibration-A** | 8 | 96 | v4 solo-calibration split, unchanged | solo, chance and counterfactual-chance quantities; one half of §13.7 |
| **Calibration-B** | 8 | 96 | **newly authored for v5** | the same quantities on disjoint topics; the other half |
| Composed validation | 2 | 24 | v4 split, unchanged | composed-headroom viability only |
| Confirmatory | 32 | 384 | v4 split, unchanged | the frozen confirmatory experiment |
| Sequestered | 8 | 96 | v4 split, unchanged | a future uncontaminated rerun only |

**Calibration-B does not exist.** §34 D3 is the decision and it is the largest
non-compute prerequisite in the whole protocol: §13.7's stability rule ---
v5's answer to the winner's curse §12.2 measures --- needs two disjoint
96-topic sets, and v5 has one. ``calibration_b_bank`` refuses while D3 is
open, and it refuses again if the bank it is handed is not 96 questions
verified individually against §6.2's four authoring rules.

**Calibration-A is not naive, and §6.2 says so.** Twenty-nine rungs per model
of v4r4's library were measured on those topics and the researcher has seen
the measurements. They are development data under §12.5's own definition, so
this is permitted; it is declared rather than left to be inferred, and §30's
ledger records per family whether a prior measurement exists.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions

__all__ = ["SET_SIZES", "AUTHORING_RULES", "assert_bank_shape",
           "assert_authoring_rules", "calibration_b_bank",
           "assert_sets_disjoint", "CALIBRATION_B_STATUS"]

SET_SIZES = C.SET_SIZES
AUTHORING_RULES = C.AUTHORING_RULES

#: The one honest thing this module can say about Calibration-B today.
CALIBRATION_B_STATUS = "NOT_AUTHORED"

#: §6.2 rule 4: no wording that itself mentions any letter, word length, word
#: shape, punctuation-count or capitalisation requirement. Fixed template text
#: identical in every cell --- including §8.5's answer-length sentence --- is
#: not question text and is not restricted by it.
_FORM_TOKENS = ("letter", "letters", "word length", "syllable", "capital",
                "capitalis", "capitaliz", "uppercase", "upper-case", "comma",
                "semicolon", "punctuation", "characters long", "sentence "
                "count", "how many words", "vowel", "consonant")


def assert_bank_shape(bank: Mapping[str, Sequence[Any]]) -> dict[str, Any]:
    """§6.2's six sets at their registered sizes, twelve areas each."""
    unknown = sorted(set(bank) - set(C.TOPIC_SETS))
    if unknown:
        raise ProtocolError(f"unknown topic set(s) {unknown}; §6.2 registers "
                            f"{C.TOPIC_SETS}")
    missing = [s for s in C.TOPIC_SETS if s not in bank]
    if missing:
        raise ProtocolError(f"§6.2's bank is missing {missing}")
    wrong = {s: len(bank[s]) for s in C.TOPIC_SETS
             if len(bank[s]) != SET_SIZES[s]}
    if wrong:
        raise ProtocolError(
            f"§6.2's registered set sizes are {SET_SIZES} and this bank "
            f"carries {wrong}")
    total = sum(len(bank[s]) for s in C.TOPIC_SETS)
    if total != C.N_TOPICS:
        raise ProtocolError(f"§6.2's bank is {C.N_TOPICS} questions; this one "
                            f"is {total}")
    return {"sets": {s: len(bank[s]) for s in C.TOPIC_SETS}, "total": total}


def assert_sets_disjoint(bank: Mapping[str, Sequence[Any]]) -> None:
    """No question appears in two sets, and no reserved question is spent."""
    seen: dict[Any, str] = {}
    for name in C.TOPIC_SETS:
        for question in bank.get(name, ()):
            key = question if isinstance(question, str) else \
                question.get("topic_id")
            if key in seen:
                raise ProtocolError(
                    f"{key!r} appears in both {seen[key]} and {name}; §6.2's "
                    "splits are disjoint and a topic a set spends is spent")
            seen[key] = name


def assert_authoring_rules(questions: Iterable[Mapping[str, Any]]
                           ) -> dict[str, Any]:
    """§6.2's four rules, verified per question.

    Only the fourth is mechanically checkable, and this checks it. The other
    three --- answerable from general knowledge, no single correct short
    answer, no reused public dataset or examination text --- are human
    verifications and are required to be **recorded per question**; a question
    that does not carry all four verifications is refused, so an unverified
    question cannot enter the bank by being silent about it.
    """
    questions = list(questions)
    offences: list[dict[str, Any]] = []
    for question in questions:
        text = str(question.get("text", ""))
        verified = question.get("authoring_rules_verified") or {}
        missing = [r for r in AUTHORING_RULES if not verified.get(r)]
        if missing:
            offences.append({"topic_id": question.get("topic_id"),
                             "unverified_rules": missing})
            continue
        lowered = text.lower()
        hits = [t for t in _FORM_TOKENS if t in lowered]
        if hits:
            offences.append({"topic_id": question.get("topic_id"),
                             "form_requirement_tokens": hits})
    if offences:
        raise ProtocolError(
            f"§6.2: {len(offences)} question(s) fail the authoring rules; "
            f"first {offences[0]}")
    return {"questions": len(questions), "rules": list(AUTHORING_RULES),
            "mechanically_checked": "no_form_requirement_in_the_question_text",
            "human_verified_per_question": [r for r in AUTHORING_RULES
                                            if r != "no_form_requirement_in_"
                                            "the_question_text"]}


def calibration_b_bank(questions: Sequence[Mapping[str, Any]] | None = None
                       ) -> tuple[Mapping[str, Any], ...]:
    """§6.2's 96 newly authored questions. **They do not exist yet.**

    §34 D3 gates adoption on them and this refuses while D3 is open. When D3
    is closed the bank must still be 96 questions passing §6.2's four rules,
    and this checks that too: closing a decision is not the same as doing the
    work it names.
    """
    def _author_before() -> tuple[Mapping[str, Any], ...]:
        if questions is None:
            raise ProtocolError(
                "§34 D3 was closed at 'author before adoption' and no bank "
                f"was supplied. §6.2 needs {C.N_CALIBRATION_B} newly authored "
                "questions, eight per subject area, each verified "
                "individually against the four authoring rules; §13.7's "
                "stability rule --- v5's answer to the winner's curse §12.2 "
                "measures --- does not work without them")
        if len(questions) != C.N_CALIBRATION_B:
            raise ProtocolError(
                f"§6.2: Calibration-B is {C.N_CALIBRATION_B} questions and "
                f"this bank is {len(questions)}")
        assert_authoring_rules(questions)
        return tuple(questions)

    def _author_after() -> tuple[Mapping[str, Any], ...]:
        raise ProtocolError(
            "§34 D3 was closed at 'author after adoption'. Nothing downstream "
            "of Gate 3A can run until the bank exists, and this function "
            "returns no questions rather than an empty split that would look "
            "like one")

    return decisions.choice("D3", {"author_before_adoption": _author_before,
                                   "author_after_adoption": _author_after},
                            where="topics.calibration_b_bank")()
