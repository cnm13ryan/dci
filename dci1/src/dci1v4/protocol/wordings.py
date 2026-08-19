"""Four frozen wordings per registered constraint (v4r2 §7.3).

One verifier decides all four wordings of a constraint; the twenty-response
suite of ``verifiers.wording_suite`` asserts identical verdicts at every
registered severity. Severity parameters render as numerals, which are not
alphabetic runs, so every word count here is severity-invariant — a property
``assert_severity_invariance`` proves rather than assumes (§7.3).

**The length caliper is measured against A, not against B (T-8, §7.3,
§13.2 condition 3).** That inverts v3 and it binds the authoring, not just
the admission: A's canonical wording is six words, so a reference wording
must land within 20% of the A wording carrying the same index. The eleven-
and twelve-word family templates printed in the v4r2 §7.2 table cannot meet
that caliper against any A wording, so no family stated in the table's own
words could ever be admitted. The four frozen wordings authored here state
each family's registered rule in the registered lexical vocabulary and are
compact enough for the caliper to be satisfiable; the §7.2 table text is
retained verbatim in ``FAMILY_RULE_STATEMENTS`` as the definition of what
each family means, and ``assert_rule_vocabulary`` checks every authored
wording against it. This authoring decision is recorded in
``docs/v4_traceability.md`` and reported for the researcher, because index 0
is not the §7.2 table string for the eight families.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.verifiers.constraints import (
    FOCAL_GRID,
    REFERENCE_LADDERS,
    TARGET_GRID,
)

N_WORDINGS = 4
WORDING_LENGTH_TOLERANCE = 0.20

#: v4r2 §7.2, verbatim. The definition of each family's rule; not a wording.
FAMILY_RULE_STATEMENTS: dict[str, str] = {
    "RF1": "At most q words in the answer may begin with the letter b.",
    "RF2": "At most q words in the answer may end with the letters ing.",
    "RF3": "At most q words in the answer may have one letter.",
    "RF4": "At most q words may contain two identical adjacent letters.",
    "RF5": "The answer may contain at most q comma characters.",
    "RF6": "The answer may contain at most q upper-case English letters.",
    "RF7": "At most q words in the answer may contain the letter a.",
    "RF8": "At most q words in the answer may end with the letter y.",
}


def target_wordings(n: int) -> tuple[str, str, str, str]:
    """A: index 0 is the v4r2 §7.1 canonical text."""
    if n not in TARGET_GRID:
        raise ProtocolError(f"n={n} outside the registered target grid")
    t = "time" if n == 1 else "times"
    return (
        f"Use the word however exactly {n} {t}.",
        f"Your answer must contain however exactly {n} {t}.",
        f"Include however exactly {n} {t} in your answer.",
        f"The word however must appear exactly {n} {t}.",
    )


def focal_wordings(m: int) -> tuple[str, str, str, str]:
    """B: index 0 is the v4r2 §7.1 canonical text. B is not calipered."""
    if m not in FOCAL_GRID:
        raise ProtocolError(f"m={m} outside the registered focal grid")
    return (
        f"Every word in the answer must have at most {m} letters.",
        f"Use only words of {m} letters or fewer.",
        f"Do not use any word longer than {m} letters.",
        f"No word in your answer may exceed {m} letters.",
    )


_FAMILY_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "RF1": (
        "At most {q} words may begin with b.",
        "Use at most {q} words beginning with b.",
        "No more than {q} words may start with b.",
        "Limit words beginning with b to {q}.",
    ),
    "RF2": (
        "At most {q} words may end with ing.",
        "Use at most {q} words ending with ing.",
        "No more than {q} words may end in ing.",
        "Limit words ending with ing to {q}.",
    ),
    "RF3": (
        "At most {q} words may have one letter.",
        "Use at most {q} words of one letter.",
        "No more than {q} words may have one letter.",
        "Limit words of one letter to {q}.",
    ),
    "RF4": (
        "At most {q} words contain a doubled letter.",
        "Use at most {q} words with a doubled letter.",
        "No more than {q} words contain a doubled letter.",
        "Limit words with a doubled letter to {q}.",
    ),
    "RF5": (
        "Use at most {q} comma characters.",
        "Your answer may contain at most {q} commas.",
        "No more than {q} commas may appear.",
        "Do not use more than {q} comma characters.",
    ),
    "RF6": (
        "Use at most {q} upper-case English letters.",
        "Include at most {q} upper-case English letters.",
        "No more than {q} upper-case English letters.",
        "Do not exceed {q} upper-case English letters.",
    ),
    "RF7": (
        "At most {q} words contain the letter a.",
        "Use at most {q} words containing the letter a.",
        "No more than {q} words contain the letter a.",
        "Limit words containing the letter a to {q}.",
    ),
    "RF8": (
        "At most {q} words may end with y.",
        "Use at most {q} words ending with y.",
        "No more than {q} words may end in y.",
        "Limit words ending with y to {q}.",
    ),
}
assert set(_FAMILY_TEMPLATES) == set(REFERENCE_LADDERS)


def family_wordings(family: str, q: int) -> tuple[str, str, str, str]:
    if family not in REFERENCE_LADDERS:
        raise ProtocolError(f"unknown reference family {family!r}")
    if q not in REFERENCE_LADDERS[family]:
        raise ProtocolError(f"severity q={q} outside the registered "
                            f"{family} ladder")
    return tuple(t.format(q=q) for t in _FAMILY_TEMPLATES[family])


def wordings(kind: str, severity: int) -> tuple[str, str, str, str]:
    """The four frozen wordings of one registered constraint at one severity."""
    if kind == "A":
        return target_wordings(severity)
    if kind == "B":
        return focal_wordings(severity)
    return family_wordings(kind, severity)


def wording(kind: str, index: int, severity: int) -> str:
    if not 0 <= index < N_WORDINGS:
        raise ProtocolError(f"wording index {index} outside 0..3")
    return wordings(kind, severity)[index]


def wording_word_count(text: str) -> int:
    """Word count under the registered lexical rule: maximal alphabetic runs
    (§7.2). Numerals are not alphabetic and contribute nothing."""
    count, in_run = 0, False
    for ch in text:
        if ch.isalpha():
            if not in_run:
                count += 1
                in_run = True
        else:
            in_run = False
    return count


def length_caliper_ok(family: str, q: int, n: int) -> bool:
    """§7.3 / §13.2 condition 3: every frozen wording of the family at ``q``
    is within 20% of the A wording of the same index at ``n``."""
    a_counts = [wording_word_count(w) for w in target_wordings(n)]
    r_counts = [wording_word_count(w) for w in family_wordings(family, q)]
    return all(abs(r - a) <= WORDING_LENGTH_TOLERANCE * a
               for r, a in zip(r_counts, a_counts))


def caliper_table(n: int) -> dict[str, dict]:
    """Per family: the four A counts, the four reference counts, and the
    verdict. Written into the Gate 3 record so admission is auditable."""
    a_counts = [wording_word_count(w) for w in target_wordings(n)]
    table: dict[str, dict] = {}
    for family, ladder in REFERENCE_LADDERS.items():
        per_severity = {}
        for q in ladder:
            counts = [wording_word_count(w) for w in family_wordings(family, q)]
            per_severity[q] = {"counts": counts,
                               "ok": length_caliper_ok(family, q, n)}
        table[family] = {"a_counts": a_counts, "severities": per_severity}
    return table


def assert_severity_invariance() -> dict[str, int]:
    """§7.3: prove that no wording's word count depends on its severity.

    The caliper is stated per severity; if word counts moved with severity a
    family could pass the caliper at one severity and fail at another for a
    purely typographic reason. They do not, because numerals are not
    alphabetic runs — asserted here rather than assumed.
    """
    counts: dict[str, int] = {}
    for index in range(N_WORDINGS):
        seen = {wording_word_count(wording("A", index, n)) for n in TARGET_GRID}
        if len(seen) != 1:
            raise ProtocolError(f"A wording {index} word count varies with n: "
                                f"{sorted(seen)}")
        counts[f"A:{index}"] = seen.pop()
        seen = {wording_word_count(wording("B", index, m)) for m in FOCAL_GRID}
        if len(seen) != 1:
            raise ProtocolError(f"B wording {index} word count varies with m: "
                                f"{sorted(seen)}")
        counts[f"B:{index}"] = seen.pop()
        for family, ladder in REFERENCE_LADDERS.items():
            seen = {wording_word_count(wording(family, index, q))
                    for q in ladder}
            if len(seen) != 1:
                raise ProtocolError(
                    f"{family} wording {index} word count varies with q: "
                    f"{sorted(seen)}")
            counts[f"{family}:{index}"] = seen.pop()
    return counts


#: Vocabulary each family's wordings must use, drawn from its §7.2 rule
#: statement: a tuple of alternative sets, each of which at least one member
#: of must appear. ``assert_rule_vocabulary`` checks that every authored
#: wording names the feature the verifier actually counts, so a compact
#: wording cannot quietly stop stating its own rule.
_REQUIRED_TOKENS: dict[str, tuple[tuple[str, ...], ...]] = {
    "RF1": (("b",),),
    "RF2": (("ing",),),
    "RF3": (("one",), ("letter", "letters")),
    "RF4": (("doubled",), ("letter", "letters")),
    "RF5": (("comma", "commas"),),
    "RF6": (("upper",), ("case",), ("english",)),
    "RF7": (("letter", "letters"), ("a",)),
    "RF8": (("y",),),
}


def assert_rule_vocabulary() -> None:
    """Every authored family wording names the counted feature (§7.2)."""
    for family, alternatives in _REQUIRED_TOKENS.items():
        for q in REFERENCE_LADDERS[family]:
            for index, text in enumerate(family_wordings(family, q)):
                raw = text.replace("-", " ").lower().split()
                words = {w.strip(".,") for w in raw}
                missing = [alt for alt in alternatives
                           if not words & set(alt)]
                if missing:
                    raise ProtocolError(
                        f"{family} wording {index} at q={q} names none of "
                        f"{missing}; it must state the rule "
                        f"{FAMILY_RULE_STATEMENTS[family]!r}")


def assert_caliper_feasible() -> dict[str, list[int]]:
    """Every family has at least one severity meeting the caliper at every
    registered n. A family that could never be admitted for a length reason
    is an authoring defect, not an empirical outcome."""
    assert_severity_invariance()
    assert_rule_vocabulary()
    feasible: dict[str, list[int]] = {}
    for family, ladder in REFERENCE_LADDERS.items():
        ok = [q for q in ladder
              if all(length_caliper_ok(family, q, n) for n in TARGET_GRID)]
        if not ok:
            raise ProtocolError(
                f"{family} meets the §7.3 length caliper against A at no "
                f"registered severity; it could never be admitted")
        feasible[family] = ok
    return feasible
