"""Four frozen wordings per registered constraint (§7.5).

The v4r3 module, carried through v4r4, v5 and v6; the Tier-1, Tier-2 and
probe-only templates below were added by v5 and v6 and every one of them
renders through the same function to the same caliper.

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

The eight ``RF`` wordings are **carried** from ``dci1v4.protocol.wordings``,
byte-identically at every severity but ``q = 1``, and
``assert_rf_wordings_are_carried`` measures both halves of that statement
rather than trusting either. The twelve wordings new in v4r3 are authored
here in the same lexical vocabulary and to the same caliper.

**Grammatical number (2026-08-29, prospective).** Every template is a
``str.format`` string over ``{q}`` and two number placeholders: ``{s}`` is the
plural ``s`` on a noun the numeral governs (``word{s}``, ``comma{s}``,
``character{s}``, ``sentence{s}``) and ``{v}`` the singular ``s`` on a verb
whose subject that noun is (``contain{v}``). At ``q = 1`` they render *word*
and *contains*; at every other severity, including 0, *words* and *contain*.
Until this date every non-marker template hard-coded the plural, so
``q = 1`` rendered *exactly 1 semicolons*, *at most 1 words* and *at least 1
words*; A's and the Tier-1 templates already carried ``time{s}``. A numeral
is not an alphabetic run and the placeholders add none, so no wording's word
count moves and ``assert_severity_invariance`` holds as before, which is what
keeps §7.5's caliper and §12.6's expansion exactly where they were. The
change is to text the model is shown and is entered in
``CHANGES_SCIENTIFIC.md``: rows generated under the plural rendering at
``q = 1`` carry a different constraint sentence from the one this module now
renders, and ``carryover.assert_wordings_match_stored`` says so rather than
admitting them.
"""
from __future__ import annotations

from typing import Any

from dci1v4.errors import ProtocolError
from dci1v4.protocol.wordings import (
    _FAMILY_TEMPLATES as _V4_FAMILY_TEMPLATES,
)
from dci1v4.protocol.wordings import focal_wordings as _v4_focal_wordings
from dci1v4.protocol.wordings import target_wordings as _v4_target_wordings

from dci1v7.verifiers.constraints import (
    FAMILIES, MARKER_WORDS, TARGET_GRID, TARGET_WORD, declared_range,
    focal_severities,
)

__all__ = ["N_WORDINGS", "WORDING_LENGTH_TOLERANCE", "FAMILY_RULE_STATEMENTS",
           "number_fields", "NUMBER_PLACEHOLDERS",
           "target_wordings", "focal_wordings", "family_wordings", "wordings",
           "wording", "wording_word_count", "length_caliper_ok",
           "caliper_table", "assert_severity_invariance",
           "assert_rule_vocabulary", "assert_caliper_feasible",
           "assert_rf_wordings_are_carried", "wording_source_hash",
           "grammatical_number_defects", "assert_grammatical_number"]

N_WORDINGS = 4
WORDING_LENGTH_TOLERANCE = 0.20

#: The two grammatical-number placeholders every template may carry, and the
#: one rule that fills them. ``s`` is a noun's plural ending, ``v`` a verb's
#: singular ending; one is empty exactly when the other is not.
NUMBER_PLACEHOLDERS = ("s", "v")


def number_fields(q: int) -> dict[str, str]:
    """``{s}`` and ``{v}`` for severity ``q``: singular at 1, plural otherwise
    (0 takes the plural in English: *0 words*)."""
    return {"s": "" if q == 1 else "s", "v": "s" if q == 1 else ""}


#: The carried RF templates are v4r2's, which render a plural noun at every
#: severity. They are made number-aware by a fixed rewrite rather than by
#: retyping: each rule maps the plural phrase the numeral governs to its
#: placeholder form, and ``_number_aware`` refuses a template it cannot make
#: render byte-identically to v4's at every severity but 1 --- so the
#: derivation can change nothing except the grammatical number at ``q = 1``.
#: Ordered: a longer phrase before the phrase it contains.
_NUMBER_REWRITES: tuple[tuple[str, str], ...] = (
    ("{q} words contain ", "{q} word{s} contain{v} "),
    ("{q} words", "{q} word{s}"),
    ("{q} comma characters", "{q} comma character{s}"),
    ("{q} commas", "{q} comma{s}"),
    ("{q} upper-case English letters", "{q} upper-case English letter{s}"),
)


def _number_aware(templates: tuple[str, ...]) -> tuple[str, ...]:
    out = []
    for template in templates:
        aware = template
        for plural, placeholder in _NUMBER_REWRITES:
            aware = aware.replace(plural, placeholder)
        for q in (0, 2, 3, 12):
            if aware.format(q=q, **number_fields(q)) != template.format(q=q):
                raise ProtocolError(
                    f"the number-aware form of {template!r} does not render "
                    f"v4's text at q={q}; the carry-over is refused")
        out.append(aware)
    return tuple(out)

#: §7.3 and §7.4, verbatim. The definition of each family's rule; not a
#: wording. Sourced from the registered ``Family.rule`` so the two cannot
#: drift apart.
FAMILY_RULE_STATEMENTS: dict[str, str] = {k: f.rule for k, f in FAMILIES.items()}


def target_wordings(n: int) -> tuple[str, str, str, str]:
    """A: carried byte-identically from v4r2 (§10.2 carry-over)."""
    return _v4_target_wordings(n)


def _focal_templates() -> tuple[str, str, str, str]:
    """B's four wordings as ``{m}`` templates, derived from v4's renderings.

    v4's grid stopped at m = 10 and v5's runs to 16 (§7.1, §7.2), so the
    strings are re-derived rather than re-typed: two renderings that differ
    only in the numeral give the template, and a difference anywhere else is
    refused. §7.2 requires the four wordings to be parameterised on m and to
    render at every severity of the declared range from the same four strings.
    """
    a, b = _v4_focal_wordings(8), _v4_focal_wordings(9)
    out = []
    for one, two in zip(a, b):
        template = one.replace("8", "{m}")
        if two.replace("9", "{m}") != template:
            raise ProtocolError(
                "B's wordings differ by more than the numeral between two "
                "severities; §7.2's severity-invariance premise fails")
        out.append(template)
    return tuple(out)


_FOCAL_TEMPLATES = _focal_templates()


def focal_wordings(m: int) -> tuple[str, str, str, str]:
    """B: four strings parameterised on m, over §7.1's grid and §7.2's extension.

    v4r2's function refuses a severity outside its own ``(7, 8, 9, 10)``.
    §7.1 registers ``{7,...,14}`` and §7.2 a conditional extension to
    ``{15, 16}``, so this one accepts the union and produces the same four
    strings from the same four templates --- which is what §7.2 says it does.
    """
    if m not in focal_severities(extended=True):
        raise ProtocolError(f"m={m} outside the registered focal grid and "
                            "its §7.2 extension")
    return tuple(t.format(m=m) for t in _FOCAL_TEMPLATES)


#: The twelve families new in v4r3 and the ten added by §7.0-R3. The eight
#: carried ``RF`` families are spliced in below rather than restated, so a
#: divergence is impossible rather than merely tested for.
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
        "Use at most {q} comma{s} per hundred words.",
        "At most {q} comma{s} per hundred words.",
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
        "At least {q} word{s} must contain letter a.",
        "Include at least {q} word{s} with letter a.",
        "Use {q} or more words containing letter a.",
        "Your answer needs {q} word{s} with letter a.",
    ),
    "CL8": (
        "At least {q} word{s} must end with y.",
        "Include at least {q} word{s} ending with y.",
        "Use {q} or more words ending with y.",
        "Your answer needs {q} word{s} ending with y.",
    ),
    # CP4 and CP7 stood here in v4r3. Their third and fourth wordings state
    # the severity as a target and name no bound, which does not pin down the
    # registered lower bound; §7.0-R4 removed both families and
    # ``verifiers.constraints.REMOVED_IN_V4R4`` carries the finding.
    # ---- §7.0-R3. The four budget families take RF1's and RF8's templates
    # over a different letter, which is what makes them controls for those
    # families rather than merely additional constraints: a wording difference
    # cannot explain a difficulty difference when the wording is the same
    # sentence with one letter changed.
    "RF9": (
        "At most {q} word{s} may begin with t.",
        "Use at most {q} word{s} beginning with t.",
        "No more than {q} word{s} may start with t.",
        "Limit words beginning with t to {q}.",
    ),
    "RF10": (
        "At most {q} word{s} may end with s.",
        "Use at most {q} word{s} ending with s.",
        "No more than {q} word{s} may end in s.",
        "Limit words ending with s to {q}.",
    ),
    "RF11": (
        "Words beginning with vowels: at most {q}.",
        "At most {q} word{s} may begin with vowels.",
        "No more than {q} word{s} may start with vowels.",
        "Limit words beginning with vowels to {q}.",
    ),
    "RF12": (
        "Your answer may use at most {q} sentence{s}.",
        "Your answer must have at most {q} sentence{s}.",
        "No more than {q} sentence{s} may appear.",
        "Do not write more than {q} sentence{s}.",
    ),
    "CR9": (
        "Words beginning with t: at most {q} percent.",
        "At most {q} percent of words begin with t.",
        "Keep words beginning with t to {q} percent.",
        "Limit words beginning with t to {q} percent.",
    ),
    "CR10": (
        "Words ending with s: at most {q} percent.",
        "At most {q} percent of words end with s.",
        "Keep words ending with s to {q} percent.",
        "Limit words ending with s to {q} percent.",
    ),
    "CR11": (
        "Words beginning with vowels: at most {q} percent.",
        "At most {q} percent of words begin with vowels.",
        "Keep words beginning with vowels to {q} percent.",
        "Limit words beginning with vowels to {q} percent.",
    ),
    "CR12": (
        "Use at most {q} sentence{s} per hundred words.",
        "At most {q} sentence{s} per hundred words.",
        "Keep sentences to {q} per hundred words.",
        "Limit sentences to {q} per hundred words.",
    ),
    # ---- §7.8. Every Tier-1 marker family carries A's four templates with
    # the marker word substituted, which makes the same-form claim a property
    # of the INSTRUMENT rather than of the prose describing it. The templates
    # are generated from A's rather than retyped, so the parallel cannot drift.
}

def _marker_templates(marker: str) -> tuple[str, str, str, str]:
    """A's four templates with A's marker replaced (§7.8).

    Derived from ``target_wordings`` at import rather than retyped, so the
    Tier-1 wordings cannot drift from A's and the §7.7 length caliper holds by
    construction: the substitution changes one word for one word.
    """
    singular = _v4_target_wordings(1)
    plural = _v4_target_wordings(2)
    out = []
    for one, many in zip(singular, plural):
        template = many.replace(" 2 ", " {q} ").replace("times", "time{s}")
        if one.replace(" 1 ", " {q} ").replace("time.", "time{s}.") \
                .replace("time ", "time{s} ") != template:
            raise ProtocolError(
                "A's singular and plural wordings differ by more than the "
                "plural suffix; the Tier-1 substitution is defined as "
                "replacing one word with one word (§7.8) and cannot be "
                "derived here")
        out.append(template.replace(TARGET_WORD, marker))
    return tuple(out)


_TIER1_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    kind: _marker_templates(MARKER_WORDS[FAMILIES[kind].statistic_id])
    for kind in FAMILIES if FAMILIES[kind].structural_tier == 1
}

#: §7.10's Tier-2 families. XC1 carries v4r4's CX2 templates, byte-identical
#: at every severity but q = 1; XC2 and XC3 are authored in the same lexical
#: vocabulary and to the same caliper against A.
_TIER2_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "XC1": (
        "Your answer must use exactly {q} semicolon{s}.",
        "Use exactly {q} semicolon character{s} in your answer.",
        "Exactly {q} semicolon{s} must appear in your answer.",
        "Include exactly {q} semicolon character{s} in your answer.",
    ),
    "XC2": (
        "Your answer must use exactly {q} comma{s}.",
        "Use exactly {q} comma character{s} in your answer.",
        "Exactly {q} comma{s} must appear in your answer.",
        "Include exactly {q} comma character{s} in your answer.",
    ),
    "XC3": (
        "Your answer must have exactly {q} sentence{s}.",
        "Use exactly {q} sentence{s} in your whole answer.",
        "Exactly {q} sentence{s} must appear in your answer.",
        "Include exactly {q} sentence{s} in your whole answer.",
    ),
}

#: §34 D24's three ``probe_only`` stand-ins. Authored in the same lexical
#: vocabulary and to the same caliper as every other family, because a
#: stand-in is prompted, generated and scored through exactly the same path
#: as a candidate --- the only thing that differs about it is that no
#: selection rule may see it. Wordings that were "good enough for a probe"
#: would make the probe's composed cells a different kind of measurement from
#: the ones §13.14 audits, which is the one thing the stage cannot afford.
_PROBE_ONLY_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "PS1": (
        "Use exactly {q} capitalised word{s} in your answer.",
        "Exactly {q} capitalised word{s} must appear in your answer.",
        "Your answer must use exactly {q} capitalised word{s}.",
        "Include exactly {q} capitalised word{s} in your whole answer.",
    ),
    "PS2": (
        "Use at least {q} semicolon{s} in your answer.",
        "At least {q} semicolon{s} must appear in your answer.",
        "Your answer must use at least {q} semicolon{s}.",
        "Include at least {q} semicolon character{s} in your answer.",
    ),
    "PS3": (
        "Words ending with y: {q} percent at least.",
        "Words ending with y: at least {q} percent.",
        "At least {q} percent of words end in y.",
        "Use {q} percent or more words ending with y.",
    ),
}


_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    **{k: _number_aware(v) for k, v in _V4_FAMILY_TEMPLATES.items()
       if k in FAMILIES},
    **{k: v for k, v in _NEW_TEMPLATES.items() if k in FAMILIES},
    **_TIER1_TEMPLATES,
    **_TIER2_TEMPLATES,
    **_PROBE_ONLY_TEMPLATES,
}
assert set(_TEMPLATES) == set(FAMILIES), (
    "every registered family needs exactly four frozen wordings")


def family_wordings(family: str, q: int) -> tuple[str, str, str, str]:
    if family not in _TEMPLATES:
        raise ProtocolError(f"unknown family {family!r}")
    if q not in declared_range(family):
        raise ProtocolError(f"severity q={q} outside the declared range of "
                            f"{family}")
    return tuple(t.format(q=q, **number_fields(q))
                 for t in _TEMPLATES[family])


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
    # §7.0-R3. Each names the letter or the unit its verifier counts, and the
    # two exact families additionally have to say "exactly", because that word
    # is the whole difference between their rule and a budget's.
    "RF9": (("t",), ("begin", "beginning", "start")),
    "RF10": (("s",), ("end", "ending")),
    "RF11": (("vowels",), ("begin", "beginning", "start")),
    "RF12": (("sentences", "sentence"),),
    "CR9": (("t",), ("begin", "beginning"), ("percent",)),
    "CR10": (("s",), ("end", "ending"), ("percent",)),
    "CR11": (("vowels",), ("begin", "beginning"), ("percent",)),
    "CR12": (("sentences", "sentence"), ("hundred",), ("words",)),
    **{kind: ((MARKER_WORDS[FAMILIES[kind].statistic_id],), ("exactly",))
       for kind in FAMILIES if FAMILIES[kind].structural_tier == 1},
    "XC1": (("semicolons", "semicolon"), ("exactly",)),
    "XC2": (("commas", "comma"), ("exactly",)),
    "XC3": (("sentences", "sentence"), ("exactly",)),
    # §34 D24's stand-ins. The same obligation as any other family: name the
    # feature the verifier counts, and name the operator that distinguishes
    # the form. PS2 and PS3 are the library's only lower-bound families whose
    # wordings had to be authored, so "least"/"more" carries the `>=` the way
    # "exactly" carries `==`.
    "PS1": (("capital", "capitalised"), ("exactly",)),
    "PS2": (("semicolons", "semicolon"), ("least", "more")),
    "PS3": (("y",), ("percent",), ("least", "more")),
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


def _differs_only_in_number(carried: str, rendered: str) -> bool:
    """Token by token, every difference is a plural ending: the carried
    token is the rendered one plus ``s`` (words/word, commas/comma,
    characters/character, letters/letter) or the rendered token is the
    carried one plus ``s`` (contain/contains). Nothing else may differ."""
    a = [t.strip(".,:;") for t in carried.split()]
    b = [t.strip(".,:;") for t in rendered.split()]
    if len(a) != len(b):
        return False
    return all(x == y or x == y + "s" or y == x + "s" for x, y in zip(a, b))


#: Tokens that end the noun phrase a numeral governs, for the grammatical-
#: number check: modals, prepositions and the words that follow a phrase.
_NUMBER_PHRASE_STOPS = frozenset((
    "may", "must", "will", "can", "of", "per", "percent", "or", "and", "in",
    "to", "with", "at", "is", "are", "containing", "beginning", "ending",
))
#: Verbs a noun phrase governs without a modal, in their plural (bare) and
#: singular forms. After ``1 word`` the singular form is required; after
#: ``2 words`` the bare form. Either ends the noun phrase.
_NUMBER_BARE_VERBS = frozenset((
    "contain", "have", "begin", "end", "start", "appear", "use",
))
_NUMBER_SINGULAR_VERBS = frozenset((
    "contains", "has", "begins", "ends", "starts", "appears", "uses",
))


def _number_phrase(tokens: list[str], start: int) -> tuple[list[str], str]:
    """The noun phrase after a numeral and the token that follows it."""
    phrase: list[str] = []
    for token in tokens[start:]:
        if token in _NUMBER_PHRASE_STOPS or token in _NUMBER_BARE_VERBS \
                or token in _NUMBER_SINGULAR_VERBS:
            return phrase, token
        phrase.append(token)
    return phrase, ""


def grammatical_number_defects(text: str, q: int) -> list[str]:
    """Every place a rendered wording pairs a numeral with the wrong number.

    Mechanical rather than linguistic: after the numeral ``q`` the noun phrase
    up to the next modal, preposition or bare verb must end in ``s`` exactly
    when ``q != 1`` (*1 word*, *0 words*, *2 words*; *percent* is invariant),
    and a bare verb that follows it must carry ``s`` exactly when ``q == 1``
    (*1 word contains*, *2 words contain*). *1 or more words* stops at
    *or* and is plural, as it should be.
    """
    defects: list[str] = []
    tokens = [t.strip(".,:;") for t in text.lower().split()]
    for index, token in enumerate(tokens):
        if token != str(q):
            continue
        phrase, following = _number_phrase(tokens, index + 1)
        if not phrase:
            continue
        head = phrase[-1]
        if head in ("percent",):
            continue
        if q == 1 and head.endswith("s"):
            defects.append(f"'1 {' '.join(phrase)}': plural noun after 1")
        if q != 1 and not head.endswith("s"):
            defects.append(f"'{q} {' '.join(phrase)}': singular noun after "
                           f"{q}")
        if following in _NUMBER_BARE_VERBS and q == 1:
            defects.append(f"'1 {' '.join(phrase)} {following}': bare verb "
                           "after a singular noun")
        if following in _NUMBER_SINGULAR_VERBS and q != 1:
            defects.append(f"'{q} {' '.join(phrase)} {following}': singular "
                           "verb after a plural noun")
    return defects


def assert_grammatical_number() -> dict[str, int]:
    """Every wording of every registered constraint, at every severity of
    its declared range (B: the grid and its extension), pairs its numeral
    with the right grammatical number. Returns the count of renderings
    checked per kind."""
    checked: dict[str, int] = {}
    kinds = [("A", TARGET_GRID), ("B", focal_severities(extended=True))] + \
        [(family, declared_range(family)) for family in FAMILIES]
    for kind, severities in kinds:
        for q in severities:
            for index, text in enumerate(wordings(kind, q)):
                defects = grammatical_number_defects(text, q)
                if defects:
                    raise ProtocolError(
                        f"{kind} wording {index} at q={q} renders "
                        f"{text!r}: {defects}")
                checked[kind] = checked.get(kind, 0) + 1
    return checked


def assert_rf_wordings_are_carried() -> dict[str, list[dict[str, Any]]]:
    """§10.2 carry-over: the eight RF wordings are v4r2's.

    Byte for byte at every severity but ``q = 1``, where v4r2's template
    rendered a plural noun after the numeral and this revision renders the
    singular (2026-08-29, prospective). Both halves are measured: every
    rendering at ``q != 1`` must equal v4r2's exactly, and at ``q = 1`` the
    two may differ only in grammatical number, token by token. Returns the
    ``q = 1`` differences so a record can show them rather than summarise.
    """
    differences: dict[str, list[dict[str, Any]]] = {}
    for family, templates in _V4_FAMILY_TEMPLATES.items():
        if family not in FAMILIES:
            continue
        for q in declared_range(family):
            carried = tuple(t.format(q=q) for t in templates)
            rendered = family_wordings(family, q)
            if q != 1:
                if rendered != carried:
                    raise ProtocolError(
                        f"{family}'s wordings at q={q} are not v4r2's")
                continue
            for index, (old, new) in enumerate(zip(carried, rendered)):
                if old == new:
                    continue
                if not _differs_only_in_number(old, new):
                    raise ProtocolError(
                        f"{family} wording {index} at q=1 differs from v4r2's "
                        f"in more than grammatical number: {old!r} vs {new!r}")
                differences.setdefault(family, []).append(
                    {"index": index, "v4r2": old, "rendered": new})
    return differences


def wording_source_hash() -> str:
    """The canonical v5 **wording** hash (§18 stage 5).

    §18 freezes the verifier hash *and the wording hash* at Gate 1, and v4r4
    froze only the first. The two are separate bindings because they can move
    independently: a verifier change alters what a response is scored as, and
    a wording change alters what the model was asked, and either one on its
    own makes an earlier row incomparable. This covers the module that renders
    every constraint line and the rule statements the manifest quotes, so a
    silently edited template is a hash change at the next entry point rather
    than a difference nobody can see in a row.
    """
    from pathlib import Path

    from dci1v4.protocol.hashing import sha_file, sha_obj

    here = Path(__file__).resolve().parent
    return sha_obj({"dci1v7/protocol/wordings.py": sha_file(here /
                                                            "wordings.py"),
                    "family_rule_statements": sha_obj(
                        dict(FAMILY_RULE_STATEMENTS))})
