"""§6.2's topic bank: 720 questions, including the 96 authored for v5.

| Set | Per area | Total | Source | Permitted use |
|---|---:|---:|---|---|
| Pre-screen | 2 | 24 | v4 split, unchanged | cap selection, the high-recall screen, Gate-1 material |
| **Calibration-A** | 8 | 96 | v4 solo-calibration split, unchanged | solo, chance and counterfactual-chance quantities; one half of §13.7 |
| **Calibration-B** | 8 | 96 | **newly authored for v5** | the same quantities on disjoint topics; the other half |
| Composed validation | 2 | 24 | v4 split, unchanged | composed-headroom viability only |
| Confirmatory | 32 | 384 | v4 split, unchanged | the frozen confirmatory experiment |
| Sequestered | 8 | 96 | v4 split, unchanged | a future uncontaminated rerun only |

**Calibration-B now exists** (§34 D3, taken 2026-08-22 at
`author_before_adoption`; `topics/data/calibration_b_v6.json`). It was the
largest non-compute prerequisite in the protocol: §13.7's stability rule ---
v5's answer to the winner's curse §12.2 measures --- needs two disjoint
96-topic sets and v5 had one.

**Closing the decision did not do the work, and this module still says so.**
``calibration_b_bank`` refuses a bank that is not 96 questions verified
individually against §6.2's four authoring rules, whatever D3 says, and refuses
outright while D3 is open or closed at `author_after_adoption`. The one
mechanically checkable rule --- no form requirement in the question text --- is
run on every load.

**Calibration-A is not naive, and §6.2 says so.** Twenty-nine rungs per model
of v4r4's library were measured on those topics and the researcher has seen
the measurements. They are development data under §12.5's own definition, so
this is permitted; it is declared rather than left to be inferred, and §30's
ledger records per family whether a prior measurement exists.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions

__all__ = ["SET_SIZES", "AUTHORING_RULES", "assert_bank_shape",
           "assert_authoring_rules", "calibration_b_bank",
           "assert_sets_disjoint", "CALIBRATION_B_STATUS",
           "calibration_b_status"]

SET_SIZES = C.SET_SIZES
AUTHORING_RULES = C.AUTHORING_RULES

def calibration_b_status() -> str:
    """Derived, never asserted --- see ``topics.bank.calibration_b_status``."""
    from dci1v6.topics.bank import calibration_b_status as _status

    return _status()


#: The value at import. ``calibration_b_status()`` is the live one.
CALIBRATION_B_STATUS = "AUTHORED"

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
        # §6.2's schema field is `question`; `text` is accepted so a caller
        # holding a differently-shaped row is not silently exempted. Reading
        # `text` alone --- which is what this did --- meant the one
        # mechanically checkable rule scanned the empty string for every
        # topic in the bank, so it had never rejected anything.
        text = str(question.get("question") or question.get("text") or "")
        if not text.strip():
            offences.append({"topic_id": question.get("topic_id"),
                             "no_question_text": True})
            continue
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
    """§6.2's 96 newly authored questions. **Authored; §34 D3 closed.**

    One rule, in one place: this delegates to
    ``topics.bank.calibration_b_questions``, which is what ``load_bank``
    already used. Two copies of "what a Calibration-B bank must satisfy" is
    two places for the rule to drift, and this is the name §34 D3 registers
    as its blocked call, so it is kept as the name and not as a second
    implementation.

    With no argument the authored bank is loaded from disk. It still passes
    every check --- 96 questions, eight per area, all four authoring
    verifications recorded, no form requirement in the text --- because
    closing a decision is not the same as doing the work it names.
    """
    from dci1v6.topics.bank import calibration_b_questions
    from dci1v6.topics.calibration_b import DATA_PATH, load_calibration_b

    if questions is None and DATA_PATH.exists() and \
            decisions.value_of("D3") == "author_before_adoption":
        questions = load_calibration_b()
    return tuple(calibration_b_questions(questions))
