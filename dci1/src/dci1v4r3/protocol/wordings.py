"""Four frozen wordings per registered constraint (v4r3 §7.5).

One verifier decides all four wordings of a constraint; the twenty-response
suite of ``verifiers.wording_suite`` asserts identical verdicts at every
severity of the **declared range**, not only of the round-0 ladder. Severity
parameters render as numerals, which are not alphabetic runs, so every word
count here is severity-invariant -- a property ``assert_severity_invariance``
proves rather than assumes. That invariance is what lets §12.6's expansion
admit a reserve rung without authoring anything: the wording of CR4 at q=17
is the wording of CR4 at q=18 with a different numeral in it.

**The length caliper is measured against A, not against B** (§7.5, §13.4
condition 3). A's canonical wording is six words and its other three are
seven, so a companion wording must land within 20% of the A wording carrying
the same index: index 0 in {5,6,7} and indices 1-3 in {6,7,8}. The full-prose
rule statements of §7.3 and §7.4 are eleven and twelve words and could never
meet that caliper, which is why they are the *definition* of each family and
never a wording; ``FAMILY_RULE_STATEMENTS`` keeps them, and
``assert_rule_vocabulary`` checks that every compact wording still names the
feature its verifier counts.

The eight ``RF`` wordings are **carried byte-identically** from
``dci1v4.protocol.wordings``; a test asserts the carry rather than trusting
it. The twelve wordings new in v4r3 are authored here in the same lexical
vocabulary and to the same caliper.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.protocol.wordings import (
    _FAMILY_TEMPLATES as _V4_FAMILY_TEMPLATES,
)
from dci1v4.protocol.wordings import focal_wordings as _v4_focal_wordings
from dci1v4.protocol.wordings import target_wordings as _v4_target_wordings

from dci1v4r3.verifiers.constraints import (
    FAMILIES, TARGET_GRID, declared_range, focal_severities,
)

__all__ = ["N_WORDINGS", "WORDING_LENGTH_TOLERANCE", "FAMILY_RULE_STATEMENTS",
           "target_wordings", "focal_wordings", "family_wordings", "wordings",
           "wording", "wording_word_count", "length_caliper_ok",
           "caliper_table", "assert_severity_invariance",
           "assert_rule_vocabulary", "assert_caliper_feasible",
           "assert_rf_wordings_are_carried"]

N_WORDINGS = 4
WORDING_LENGTH_TOLERANCE = 0.20

#: §7.3 and §7.4, verbatim. The definition of each family's rule; not a
#: wording. Sourced from the registered ``Family.rule`` so the two cannot
#: drift apart.
FAMILY_RULE_STATEMENTS: dict[str, str] = {k: f.rule for k, f in FAMILIES.items()}


def target_wordings(n: int) -> tuple[str, str, str, str]:
    """A: carried byte-identically from v4r2 (§10.2 carry-over)."""
    return _v4_target_wordings(n)


def focal_wordings(m: int) -> tuple[str, str, str, str]:
    """B: v4r2's four strings, parameterised on m, rendering at 11 and 12 too.

    v4r2's function refuses a severity outside ``FOCAL_GRID``. §7.2 registers
    the conditional extension, so this one accepts the union and produces the
    same four strings from the same four templates -- which is what §7.2 says
    it does.
    """
    if m not in focal_severities(extended=True):
        raise ProtocolError(f"m={m} outside the registered focal grid and "
                            "its conditional extension")
    if m in focal_severities():
        return _v4_focal_wordings(m)
    return (
        f"Every word in the answer must have at most {m} letters.",
        f"Use only words of {m} letters or fewer.",
        f"Do not use any word longer than {m} letters.",
        f"No word in your answer may exceed {m} letters.",
    )


#: The twelve families new in v4r3. The eight ``RF`` families are carried and
#: are spliced in below rather than restated, so a divergence is impossible
#: rather than merely tested for.
_NEW_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "CR1": (
        "Words beginning with b: at most {q} percent.",
        "At most {q} percent of words begin with b.",
        "Keep words beginning with b to {q} percent.",
        "Limit words beginning with b to {q} percent.",
    ),
    "CR2": (
        "Words ending with ing: at most {q} percent.",
        "At most {q} percent of words end with ing.",
        "Keep words ending with ing to {q} percent.",
        "Limit words ending with ing to {q} percent.",
    ),
    "CR3": (
        "Words of one letter: at most {q} percent.",
        "At most {q} percent of words have one letter.",
        "Keep words of one letter to {q} percent.",
        "Limit words of one letter to {q} percent.",
    ),
    "CR4": (
        "Words with doubled letters: at most {q} percent.",
        "At most {q} percent of words have doubled letters.",
        "Keep words with doubled letters to {q} percent.",
        "Limit words with doubled letters to {q} percent.",
    ),
    "CR5": (
        "Use at most {q} commas per hundred words.",
        "At most {q} commas per hundred words.",
        "Keep commas to {q} per hundred words.",
        "Limit commas to {q} per hundred words.",
    ),
    "CR6": (
        "Words with capitals: at most {q} percent.",
        "At most {q} percent of words use capitals.",
        "Keep words with capitals to {q} percent.",
        "Limit words with capitals to {q} percent.",
    ),
    "CR7": (
        "Words with letter a: at most {q} percent.",
        "At most {q} percent of words have letter a.",
        "Keep words with letter a to {q} percent.",
        "Limit words with letter a to {q} percent.",
    ),
    "CR8": (
        "Words ending with y: at most {q} percent.",
        "At most {q} percent of words end with y.",
        "Keep words ending with y to {q} percent.",
        "Limit words ending with y to {q} percent.",
    ),
    "CL7": (
        "At least {q} words must contain letter a.",
        "Include at least {q} words with letter a.",
        "Use {q} or more words containing letter a.",
        "Your answer needs {q} words with letter a.",
    ),
    "CL8": (
        "At least {q} words must end with y.",
        "Include at least {q} words ending with y.",
        "Use {q} or more words ending with y.",
        "Your answer needs {q} words ending with y.",
    ),
    "CP4": (
        "Words with doubled letters: at least {q} percent.",
        "At least {q} percent of words have doubled letters.",
        "Give {q} percent of words doubled letters.",
        "Make {q} percent of words carry doubled letters.",
    ),
    "CP7": (
        "Words with letter a: at least {q} percent.",
        "At least {q} percent of words have letter a.",
        "Give {q} percent of words letter a.",
        "Make {q} percent of words carry letter a.",
    ),
}

_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    **{k: _V4_FAMILY_TEMPLATES[k] for k in _V4_FAMILY_TEMPLATES},
    **_NEW_TEMPLATES,
}
assert set(_TEMPLATES) == set(FAMILIES), (
    "every registered family needs exactly four frozen wordings")


def family_wordings(family: str, q: int) -> tuple[str, str, str, str]:
    if family not in _TEMPLATES:
        raise ProtocolError(f"unknown family {family!r}")
    if q not in declared_range(family):
        raise ProtocolError(f"severity q={q} outside the declared range of "
                            f"{family}")
    return tuple(t.format(q=q) for t in _TEMPLATES[family])


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
    (§7.3). Numerals are not alphabetic and contribute nothing."""
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
    """§7.5 / §13.4 condition 3: every frozen wording of the family at ``q``
    is within 20% of the A wording of the same index at ``n``."""
    a_counts = [wording_word_count(w) for w in target_wordings(n)]
    r_counts = [wording_word_count(w) for w in family_wordings(family, q)]
    return all(abs(r - a) <= WORDING_LENGTH_TOLERANCE * a
               for r, a in zip(r_counts, a_counts))


def caliper_table(n: int) -> dict[str, dict]:
    """Per family: the four A counts, the four companion counts, and the
    verdict. Written into the Gate 3 record so admission is auditable."""
    a_counts = [wording_word_count(w) for w in target_wordings(n)]
    table: dict[str, dict] = {}
    for family in FAMILIES:
        per_severity = {}
        for q in declared_range(family):
            counts = [wording_word_count(w) for w in family_wordings(family, q)]
            per_severity[q] = {"counts": counts,
                               "ok": length_caliper_ok(family, q, n)}
        table[family] = {"a_counts": a_counts, "severities": per_severity}
    return table


def assert_severity_invariance() -> dict[str, int]:
    """§7.5: prove that no wording's word count depends on its severity.

    The caliper is stated per severity; if word counts moved with severity a
    family could pass the caliper at one severity and fail at another for a
    purely typographic reason. They do not, because numerals are not
    alphabetic runs -- asserted here rather than assumed. §12.6's expansion
    rests on the same property: a reserve rung inherits its family's wording
    lengths exactly.
    """
    counts: dict[str, int] = {}
    for index in range(N_WORDINGS):
        seen = {wording_word_count(wording("A", index, n)) for n in TARGET_GRID}
        if len(seen) != 1:
            raise ProtocolError(f"A wording {index} word count varies with n: "
                                f"{sorted(seen)}")
        counts[f"A:{index}"] = seen.pop()
        seen = {wording_word_count(wording("B", index, m))
                for m in focal_severities(extended=True)}
        if len(seen) != 1:
            raise ProtocolError(f"B wording {index} word count varies with m: "
                                f"{sorted(seen)}")
        counts[f"B:{index}"] = seen.pop()
        for family in FAMILIES:
            seen = {wording_word_count(wording(family, index, q))
                    for q in declared_range(family)}
            if len(seen) != 1:
                raise ProtocolError(
                    f"{family} wording {index} word count varies with q: "
                    f"{sorted(seen)}")
            counts[f"{family}:{index}"] = seen.pop()
    return counts


#: Vocabulary each family's wordings must use, drawn from its §7.3/§7.4 rule
#: statement: a tuple of alternative sets, at least one member of each of
#: which must appear. ``assert_rule_vocabulary`` checks that every authored
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
    "CR1": (("b",), ("percent",)),
    "CR2": (("ing",), ("percent",)),
    "CR3": (("one",), ("letter", "letters"), ("percent",)),
    "CR4": (("doubled",), ("letter", "letters"), ("percent",)),
    "CR5": (("comma", "commas"), ("hundred",), ("words",)),
    "CR6": (("capitals",), ("percent",)),
    "CR7": (("letter", "letters"), ("a",), ("percent",)),
    "CR8": (("y",), ("percent",)),
    "CL7": (("letter", "letters"), ("a",), ("least", "more", "needs")),
    "CL8": (("y",), ("least", "more", "needs")),
    "CP4": (("doubled",), ("letter", "letters"), ("percent",),
            ("least", "give", "make")),
    "CP7": (("letter", "letters"), ("a",), ("percent",),
            ("least", "give", "make")),
}


def assert_rule_vocabulary() -> None:
    """Every authored wording names the counted feature (§7.3, §7.4)."""
    if set(_REQUIRED_TOKENS) != set(FAMILIES):
        raise ProtocolError("every family needs a registered required-token "
                            "set; missing "
                            f"{sorted(set(FAMILIES) - set(_REQUIRED_TOKENS))}")
    for family, alternatives in _REQUIRED_TOKENS.items():
        for q in declared_range(family):
            for index, text in enumerate(family_wordings(family, q)):
                raw = text.replace("-", " ").lower().split()
                words = {w.strip(".,:;") for w in raw}
                missing = [alt for alt in alternatives if not words & set(alt)]
                if missing:
                    raise ProtocolError(
                        f"{family} wording {index} at q={q} names none of "
                        f"{missing}; it must state the rule "
                        f"{FAMILY_RULE_STATEMENTS[family]!r}")


def assert_caliper_feasible() -> dict[str, list[int]]:
    """Every family meets the §7.5 caliper at every severity of its declared
    range and at every registered n.

    v4r2 asserted only that *some* severity was feasible. v4r3 asserts *all*,
    because §12.6's expansion may admit any reserve rung and a rung that
    could never be admitted for a typographic reason would silently shrink
    the coverage the expansion exists to deliver.
    """
    assert_severity_invariance()
    assert_rule_vocabulary()
    feasible: dict[str, list[int]] = {}
    for family in FAMILIES:
        ok = [q for q in declared_range(family)
              if all(length_caliper_ok(family, q, n) for n in TARGET_GRID)]
        if len(ok) != len(declared_range(family)):
            bad = sorted(set(declared_range(family)) - set(ok))
            raise ProtocolError(
                f"{family} misses the §7.5 length caliper against A at "
                f"severities {bad}")
        feasible[family] = ok
    return feasible


def assert_rf_wordings_are_carried() -> None:
    """§10.2 carry-over: the eight RF wordings are v4r2's, byte for byte."""
    for family, templates in _V4_FAMILY_TEMPLATES.items():
        if _TEMPLATES[family] != templates:
            raise ProtocolError(f"{family}'s wordings are not v4r2's")
