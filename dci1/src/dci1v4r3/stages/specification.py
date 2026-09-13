"""§10.7-R5 component A: does the prose pin down the predicate?

**The question §10.2 cannot ask.** §10.2 proves that the program computes what
the program computes, three times, in two implementations, on 164 frozen cases
and 16,604 responses. What it never asks is whether the sentence the model was
shown *determines* that program rather than a neighbouring one. That is a
question about the specification, and the honest way to answer it is not to
poll reviewers -- reviewers miscount, which is the failure §10.4 and §10.4-R2
both ran into -- but to write the predicate down in a form a machine can
execute and then hand it cases built to separate it from every plausible
misreading.

**So the specification record is itself under test.** `specification(kind)`
records the instruction templates, the rule statement, the counted statistic,
the segmentation convention, the numerator, the denominator, the operator, the
threshold reading, the vacuity rule, the Unicode and case-folding behaviour,
and the formal predicate as **structured data**. `evaluate_specification` then
decides a verdict reading *only that record*, and A.2 requires it to reproduce
the primary verifier on every constructed case and on the whole frozen boundary
corpus, at every severity of every declared range. A specification that is
merely described cannot pass this; only one that can be executed from what is
written down.

What that check does **not** cover is the counting functions: the evaluator
calls the same registered statistic the verifier calls, so it tests the mapping
from prose to predicate and not the numerator itself. The numerator is what
§10.2's independent reimplementation covers, over every response, and the two
halves are kept separate deliberately rather than blurred into one number.

**Alternative readings are named, not assumed away.** For each of the six
registered defective readings, a family records whether the reading is
*meaningful* for its form, which reading is registered, and a constructed case
that separates them. A reading that cannot be meaningful -- a denominator swap
in a form with no denominator -- is recorded as not applicable **with its
reason**, and `stages.mutation` then checks that claim against the corpus
rather than believing it. Silence is accepted for neither.

`A` and `B` are audited here too. `microcase.defect_verdict` covers the twenty
families only, and it is frozen by §10.4-R2's generator hash and is not
touched; the two outcome constraints get their alternative readings defined in
this module, under R5, and that provenance is recorded on the card.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import canonical_json, sha_text
from dci1v4.verifiers.target import s0_count
from dci1v4.verifiers.words import alpha_runs as _v4_alpha_runs

from dci1v4r3.protocol.wordings import FAMILY_RULE_STATEMENTS, wordings
from dci1v4r3.stages.microcase import DEFECT_KINDS, defect_verdict
from dci1v4r3.verifiers.boundary import ALL_CASES, instrument_population
from dci1v4r3.verifiers.compliance import (
    NON_VACUITY_MIN_WORDS, non_vacuous, passes,
)
from dci1v4r3.verifiers.constraints import (
    FAMILIES, FORM_COUNT, FORM_EXACT, FORM_LOWER_BOUND, FORM_RATE,
    FORM_RATE_LOWER_BOUND, Constraint, declared_range,
)
from dci1v4r3.verifiers.statistics import (
    STATISTICS, focal_statistic, word_count,
)
from dci1v4r3.verifiers.witnesses import FEATURE_WORD, FILLER, feature_free

__all__ = [
    "SPEC_CASE_KINDS", "SPEC_FIELDS", "WORD_GRAIN", "CHARACTER_GRAIN",
    "SUFFIX_TESTS", "separating_case",
    "audit_severity", "specification", "evaluate_specification",
    "spec_cases", "reading_verdict", "applicability", "audit_family",
    "run_specification_audit", "specification_hash", "wording_review",
]

#: The constructed cases every family carries. Deliberate, not sampled: each
#: one exists to separate the registered reading from a specific neighbour.
SPEC_CASE_KINDS = (
    "threshold_below", "threshold_at", "threshold_above",
    "zero_statistic", "empty_answer", "wordless_answer",
    "punctuation_boundary", "unicode_boundary", "case_folding_boundary",
    "malformed_delimiter",
)

#: Every field A.1 requires. Completeness is checked against this tuple, so a
#: field that is added to the requirement and not to a record fails the audit
#: rather than being quietly absent.
SPEC_FIELDS = (
    "instruction_templates", "rule_statement", "counted_statistic",
    "segmentation_convention", "numerator", "denominator",
    "comparison_operator", "threshold_interpretation", "vacuity_rule",
    "case_folding_and_unicode", "formal_predicate",
)

#: Which statistics read a word list, and which read raw characters. A
#: composition-order drift can only move a word-grain numerator directly --- it
#: moves a character-grain one only through a rate denominator.
WORD_GRAIN = ("b_initial", "ing_final", "one_letter", "doubled_letter",
              "capital_word", "letter_a", "y_final", "t_initial", "s_final",
              "vowel_initial", "marker_thus")
CHARACTER_GRAIN = ("comma", "semicolon", "capital_char", "sentence")

#: Numerators that read the **end** of a word. The audit finds these to be
#: invariant under the composition order, and the finding is registered here
#: with its argument rather than discovered per family: see `applicability`.
SUFFIX_TESTS = ("ing_final", "y_final", "s_final")

_RATE_FORMS = (FORM_RATE, FORM_RATE_LOWER_BOUND)

#: A and B are not families. Their forms are registered in §7.1, and the
#: audit needs them named the same way a family's form is.
FORM_FOCAL = "focal_budget"


def form_of(kind: str) -> str:
    if kind == "A":
        return FORM_EXACT
    if kind == "B":
        return FORM_FOCAL
    return FAMILIES[kind].form


def statistic_id_of(kind: str) -> str:
    if kind == "A":
        return "s0"
    if kind == "B":
        return "focal"
    return FAMILIES[kind].statistic_id


def _count(statistic_id: str, text: str) -> int:
    if statistic_id == "s0":
        return s0_count(text)
    if statistic_id == "focal":
        return focal_statistic(text)
    return STATISTICS[statistic_id](text)


def constraint(kind: str, severity: int) -> Constraint:
    return (Constraint(kind, severity) if kind == "A"
            else Constraint(kind, severity, extended=True, reserve=True))


def audit_severity(kind: str) -> int:
    """The rung the constructed cases are built at: smallest declared >= 1.

    The same rule §10.4-R2 registered, and for the same reason: an answer that
    sits at severity q carries about q carrier words, and the cases exist to be
    read. At least one, so the sweep q-1, q, q+1 exists everywhere.

    The cost this rule carries in §10.4-R2 -- that the audit runs at the bottom
    of the range and *assumes* severity-invariance rather than showing it -- is
    not carried here. A.2 re-runs the prose-to-predicate check at **every**
    severity of every declared range, so the invariance is measured.
    """
    return min(q for q in declared_range(kind) if q >= 1)


# ------------------------------------------------------- the record itself

_NUMERATOR_PROSE = {
    "b_initial": "words beginning with the letter b",
    "ing_final": "words ending with the letters ing",
    "one_letter": "words of exactly one letter",
    "doubled_letter": "words containing two identical adjacent letters",
    "comma": "comma characters in the raw answer",
    "capital_char": "upper-case characters in the raw answer",
    "capital_word": "words containing at least one upper-case character",
    "letter_a": "words containing the letter a",
    "y_final": "words ending with the letter y",
    "t_initial": "words beginning with the letter t",
    "s_final": "words ending with the letter s",
    "vowel_initial": "words beginning with a, e, i, o or u; y is not a vowel "
                     "here (§7.3-R3)",
    "sentence": "sentence units: maximal runs of . ! or ?, plus one for an "
                "unterminated tail",
    "marker_thus": "occurrences of the word thus",
    "semicolon": "semicolon characters in the raw answer",
    "s0": "occurrences of the target word however as a word",
    "focal": "the letter count of the longest word",
}

_SEGMENTATION_73 = (
    "§7.3: a word is a maximal run of characters of Unicode general category "
    "L. The answer is segmented first and each word is lower-cased for the "
    "suffix and letter tests. Digits, punctuation, spaces and symbols end a "
    "word, so a hyphenated form is two words and an apostrophised form is two "
    "words."
)
_SEGMENTATION_92 = (
    "§9.2: A's counter lower-cases the whole answer and segments after. The "
    "two orders differ on exactly one character of Unicode, U+0130 LATIN "
    "CAPITAL LETTER I WITH DOT ABOVE, whose lower-case form is two "
    "codepoints; §10.2's segmenter differential measures that over the whole "
    "range rather than asserting it."
)

_OPERATOR = {FORM_COUNT: "<=", FORM_RATE: "<=", FORM_LOWER_BOUND: ">=",
             FORM_RATE_LOWER_BOUND: ">=", FORM_EXACT: "==",
             FORM_FOCAL: "<="}

#: A' -- the phrases by which a wording *names its own direction*. Registered
#: per form, and derived by reading all 128 templates rather than by guessing
#: a vocabulary: `assert_direction_lexicon_is_exhaustive` re-derives the
#: unmatched set, so a future wording that names its direction some other way
#: is reported as a finding instead of silently passing.
BOUNDING_PHRASES = {
    FORM_COUNT: ("at most", "no more than", "not more than", "more than",
                 "do not exceed", "exceed", "limit ", "keep ", "or fewer"),
    FORM_RATE: ("at most", "no more than", "more than", "limit ", "keep ",
                "or fewer"),
    FORM_FOCAL: ("at most", "or fewer", "longer than", "exceed"),
    FORM_LOWER_BOUND: ("at least", "or more", "minimum"),
    FORM_RATE_LOWER_BOUND: ("at least", "or more", "minimum"),
    FORM_EXACT: ("exactly",),
}

#: Phrases that state a *requirement* without stating a bound. On a lower-bound
#: form a requirement of q is met by q or more, so such a wording is awkward
#: rather than ambiguous. On a budget form it would name the wrong direction
#: entirely, which is why the rescue below is restricted to lower bounds.
REQUIRING_PHRASES = ("needs", "must contain", "must appear", "must have",
                     "must use", "must end", "must begin", "include ")

_LOWER_BOUND_FORMS_A = (FORM_LOWER_BOUND, FORM_RATE_LOWER_BOUND)


def specification(kind: str) -> dict[str, Any]:
    """A.1: every field the amendment requires, for one family or outcome.

    ``formal_predicate`` is structured rather than prose precisely so that
    ``evaluate_specification`` can execute it without reading anything else.
    """
    form = form_of(kind)
    statistic_id = statistic_id_of(kind)
    is_rate = form in _RATE_FORMS
    q = audit_severity(kind)
    return {
        "kind": kind,
        "form": form,
        "instruction_templates": list(wordings(kind, q)),
        "rule_statement": (FAMILY_RULE_STATEMENTS[kind] if kind in FAMILIES
                           else ("§7.1: the answer must contain the target "
                                 "word however exactly n times"
                                 if kind == "A" else
                                 "§7.1: no word of the answer may be longer "
                                 "than m letters")),
        "counted_statistic": statistic_id,
        "segmentation_convention": (_SEGMENTATION_92 if kind == "A"
                                    else _SEGMENTATION_73),
        "numerator": {
            "statistic_id": statistic_id,
            "counts": _NUMERATOR_PROSE[statistic_id],
            "grain": ("word" if statistic_id in WORD_GRAIN else
                      "character" if statistic_id in CHARACTER_GRAIN else
                      "word" if statistic_id == "s0" else "derived"),
        },
        "denominator": ({"kind": "word_count",
                         "counts": "every word of the whole answer under "
                                   "§7.3, not only the qualifying ones"}
                        if is_rate else
                        {"kind": "none",
                         "counts": "this form compares a count, so it has no "
                                   "denominator"}),
        "comparison_operator": _OPERATOR[form],
        "threshold_interpretation": (
            f"the severity q is the bound itself; the predicate is "
            f"{'rate' if is_rate else 'statistic'} {_OPERATOR[form]} q, with q "
            f"in {'percent' if is_rate else 'units of the count'}. The "
            f"declared range is {list(declared_range(kind))}."),
        "vacuity_rule": (
            "a wordless answer has no rate. The rate predicate is not "
            "satisfied by it and returns False, in both directions (§7.3, "
            "§9.3)." if is_rate else
            f"the pass predicate has no word-count clause. §9.3's non-vacuity "
            f"flag is recorded beside the verdict and is not part of it: a "
            f"budget pass under {NON_VACUITY_MIN_WORDS} words is recorded as "
            f"a vacuous pass, and the pass itself is unchanged."),
        "case_folding_and_unicode": (
            "letter tests read the word lower-cased; the word's own letters "
            "are the letters it is written with. Segmentation is over Unicode "
            "general category L, so non-Latin letters are word characters and "
            "digits are not."
            + (" A folds before segmenting (§9.2), which is why U+0130 is the "
               "one character on which A and the family word list differ."
               if kind == "A" else "")),
        "formal_predicate": {
            "statistic_id": statistic_id,
            "denominator": "word_count" if is_rate else "none",
            "scale": 100 if is_rate else 1,
            "operator": _OPERATOR[form],
            "threshold": "severity",
            "zero_denominator": "fails" if is_rate else "not_applicable",
            "reads": (("100 * S(text) / W(text) " + _OPERATOR[form] + " q, "
                       "and False when W(text) = 0")
                      if is_rate else
                      "S(text) " + _OPERATOR[form] + " q"),
        },
    }


def evaluate_specification(spec: Mapping[str, Any], severity: int,
                           text: str) -> bool:
    """A.2's evaluator. It reads the specification record and nothing else.

    No family identity, no form name, no constraint object: the only inputs
    are the recorded predicate's four fields and the registered counting
    function it names. If the record under-determines the verdict, this
    disagrees with the verifier and the audit fails, which is the point.
    """
    predicate = spec["formal_predicate"]
    value: float = _count(predicate["statistic_id"], text)
    if predicate["denominator"] == "word_count":
        words = word_count(text)
        if words == 0:
            return predicate["zero_denominator"] == "satisfies"
        value = predicate["scale"] * value / words
    elif predicate["denominator"] != "none":
        raise ProtocolError(
            f"unknown recorded denominator {predicate['denominator']!r}")
    operator = predicate["operator"]
    if operator == "<=":
        return value <= severity
    if operator == ">=":
        return value >= severity
    if operator == "==":
        return value == severity
    raise ProtocolError(f"unknown recorded operator {operator!r}")


# --------------------------------------------- the constructed case bodies

_UNICODE_TEXT = "İstanbul is one word here"
_ZERO_WIDTH = "point​clue north"


def _carrier(statistic_id: str) -> str:
    return FEATURE_WORD[statistic_id] if statistic_id in FEATURE_WORD else (
        "however" if statistic_id == "s0" else "counterproductive")


def _compose(statistic_id: str, carriers: int, fillers: int) -> str:
    """``carriers`` feature words then ``fillers`` feature-free words.

    Character numerators attach to a filler word so the answer stays an
    answer: a text of bare commas has no words and would exercise the wordless
    rule instead of the threshold it was built for.
    """
    carrier = _carrier(statistic_id)
    if statistic_id in ("comma", "semicolon", "sentence"):
        head = [f"{FILLER[i % len(FILLER)]}{carrier}" for i in range(carriers)]
    else:
        head = [carrier] * carriers
    return " ".join(head + ([feature_free(fillers)] if fillers else [])).strip()


def _search(statistic_id: str, want: Callable[[str], bool], *,
            width: int = 130) -> str | None:
    """The smallest composed text meeting ``want``, or None if none does.

    A search rather than an arithmetic construction because several numerators
    are not linear in the carrier count -- `sentence` reads one on any
    unterminated text, `focal` reads a maximum -- and a constructed text that
    silently misses its target would make the audit report a case it does not
    have.
    """
    for total in range(0, width):
        for carriers in range(0, total + 1):
            text = _compose(statistic_id, carriers, total - carriers)
            if want(text):
                return text
    return None


def _value(spec: Mapping[str, Any], text: str) -> float | None:
    """The derived quantity the predicate compares: a count, or a rate."""
    predicate = spec["formal_predicate"]
    count = _count(predicate["statistic_id"], text)
    if predicate["denominator"] == "none":
        return float(count)
    words = word_count(text)
    return None if words == 0 else predicate["scale"] * count / words


def _splitter_candidates(statistic_id: str, q: int) -> list[str]:
    """Texts built around U+0130, the one character folding order splits.

    `verifiers.words.case_folding_splitters` returns exactly the characters
    whose lower-case form leaves general category L, and it returns one. A
    family's segmentation drift can therefore only be exhibited by a text
    containing it, and the shape that exhibits it depends on the numerator ---
    so the candidates are generated and the separating one is *found*, not
    guessed.
    """
    carrier = _carrier(statistic_id)
    splitter = "İ"
    pieces = [splitter, splitter + carrier, carrier + splitter,
              carrier + splitter + carrier, splitter + splitter,
              splitter + "a", "a" + splitter, splitter + "s",
              splitter + "ing", "ing" + splitter, splitter + "thus",
              "thus" + splitter, splitter + "n",
              # A doubling on each side of the split: one word carrying one
              # doubling becomes two words each carrying one.
              "aa" + splitter + "bb", "cell" + splitter + "cell",
              "ll" + splitter + "mm", carrier + splitter + "aa",
              # A word whose split leaves a one-letter piece.
              "n" + splitter + "n", splitter + "n " + splitter + "n",
              # Prefix shapes: the second piece starts with the feature.
              "x" + splitter + carrier, "x" + splitter + "under",
              # Length shapes, for B.
              "counterproductive" + splitter + "counterproductive"]
    texts: list[str] = []
    for piece in pieces:
        for carriers in range(0, q + 3):
            for pad in (0, 1, 2, q + 1):
                texts.append(_compose_around(piece, statistic_id, carriers,
                                             pad))
                texts.append(_compose_around(piece + " " + piece,
                                             statistic_id, carriers, pad))
    return texts


def _compose_around(head: str, statistic_id: str, carriers: int,
                    fillers: int) -> str:
    """``carriers`` plain carrier words, then the splitter shape, then filler.

    The carrier prefix is what lets a *threshold* be reached with a splitter
    shape in the answer: a lower bound of five cannot be separated by a single
    two-piece word, only by four ordinary matches plus one that splits.
    """
    head_words = _compose(statistic_id, carriers, 0)
    tail = feature_free(fillers)
    return " ".join(part for part in (head_words, head, tail) if part).strip()


def _candidates(kind: str, q: int) -> list[str]:
    """The constructed pool a separating case is searched in.

    Every member is authored: composed carrier/filler texts across the
    threshold, the degenerate answers, the punctuation and folding boundaries,
    the U+0130 shapes above, and --- for rate forms --- texts whose character
    length and word count diverge far enough for a denominator swap to show.
    """
    statistic_id = statistic_id_of(kind)
    texts: list[str] = []
    for carriers in range(0, q + 4):
        for fillers in range(0, q + 4):
            texts.append(_compose(statistic_id, carriers, fillers))
    for total in (10, 20, 100):
        for carriers in range(0, min(total, q + 4) + 1):
            texts.append(_compose(statistic_id, carriers, total - carriers))
    texts += ["", "   ", ",,,", ";;;", "...", ",;.", "a", "n", "point",
              "well-known cats' one,,two step;; clue",
              "Thus THUS thus Point POINT", _UNICODE_TEXT, _ZERO_WIDTH,
              "one,,two step;; clue point... clue"]
    # Long words move the character count without moving the word count, which
    # is the whole difference a denominator swap makes.
    carrier = _carrier(statistic_id)
    for repeat in (1, 2, 3):
        texts.append(" ".join([carrier] * repeat
                              + ["counterproductive"] * (repeat * 4)))
        texts.append(" ".join([carrier + "," * 30] * repeat))
    texts += _splitter_candidates(statistic_id, q)
    if kind == "A":
        # The target word's own neighbourhood: the substring reading and the
        # folding order are both about what counts as an occurrence of it.
        texts += ["however", "howevers", "however however", "Howevers",
                  "However", "however, however", "whichever however",
                  "İhowever", "however İ", "İhowever however",
                  "howeverİ", "İhowevers"]
    if kind == "B":
        # A length ladder, because B compares a length and the filler pool
        # tops out at five letters: without it no constructed answer sits at
        # the threshold and the off-by-one reading cannot be separated.
        ladder = "counterproductive"
        texts += [ladder[:n] for n in range(1, len(ladder) + 1)]
        texts += [f"point {ladder[:n]} clue" for n in range(1, 18)]
        texts += [f"İ{ladder[:n]}" for n in range(1, 18)]
        texts += [f"{ladder[:n]}İ{ladder[:n]}" for n in range(1, 12)]

    # The dense sweep goes last, and the search returns on its first hit, so
    # only a reading that the cheap pool cannot separate pays for it. It
    # exists for `segmentation_drift` on a rate form, where the drift moves
    # the *denominator* by one word and the rate has to cross q to show:
    # that needs a specific answer length, not a boundary shape.
    dense: list[str] = []
    for total in range(0, 122):
        for carriers in range(0, min(total, q + 6) + 1):
            base = _compose(statistic_id, carriers, total - carriers)
            dense.append(base)
            # A *standalone* U+0130 is one word under both orders, because
            # folding it and segmenting gives one run. Only an **embedded**
            # one splits, so the denominator shifts by one word per appended
            # token and by two per pair. `pointİclue` reads zero on every
            # registered numerator except the two capital ones, so it moves
            # the denominator without moving the numerator.
            dense.append((base + " pointİclue").strip())
            dense.append((base + " pointİclue formİstep").strip())
    texts += dense

    seen: set[str] = set()
    out: list[str] = []
    for text in texts:
        if text not in seen:
            seen.add(text)
            out.append(text)
    return out


def separating_case(kind: str, severity: int, defect: str,
                    pool: Sequence[str]) -> str | None:
    """The first constructed text on which ``defect`` records a different
    verdict from the registered reading."""
    statistic_id = statistic_id_of(kind)
    rule = constraint(kind, severity)
    for text in pool:
        registered = passes(rule, _count(statistic_id, text), text)
        if reading_verdict(kind, severity, text, defect) != registered:
            return text
    return None


def spec_cases(kind: str) -> list[dict[str, Any]]:
    """The constructed discriminating cases for one family, at its rung.

    Two groups. The ten registered case kinds -- the threshold sweep, the
    degenerate answers, the boundaries -- are built for every family whether
    or not they happen to separate anything: they are what the amendment asks
    a reader to be shown. The **separators** are then searched for, one per
    alternative reading the applicability rule calls meaningful, so that A.3
    is answered by an exhibited case rather than by an expectation.
    """
    spec = specification(kind)
    statistic_id = spec["counted_statistic"]
    q = audit_severity(kind)
    is_rate = spec["formal_predicate"]["denominator"] == "word_count"

    def at(target: float) -> str | None:
        if is_rate:
            # An exact percentage needs an exact denominator, so ask for a
            # hundred-word answer and let the search find the carrier count.
            return _search(statistic_id,
                           lambda t: (word_count(t) == 100
                                      and _value(spec, t) == target))
        # With words, so that the sweep does not collapse onto the empty
        # answer at q = 1 and audit the vacuity rule by accident.
        found = _search(statistic_id,
                        lambda t: (word_count(t) > 0
                                   and _value(spec, t) == target))
        return found if found is not None else _search(
            statistic_id, lambda t: _value(spec, t) == target)

    built: list[tuple[str, str | None, str]] = [
        ("threshold_below", at(q - 1) if q >= 1 else None,
         f"the derived quantity is exactly q-1 = {q - 1}"),
        ("threshold_at", at(q), f"the derived quantity is exactly q = {q}"),
        ("threshold_above", at(q + 1),
         f"the derived quantity is exactly q+1 = {q + 1}"),
        ("zero_statistic", _search(statistic_id,
                                   lambda t: (_count(statistic_id, t) == 0
                                              and word_count(t) > 0)),
         "the numerator reads zero on an answer that has words"),
        ("empty_answer", "", "the empty string"),
        ("wordless_answer", ",,, ;;; ...",
         "punctuation only: the answer has no words at all, so a rate has no "
         "denominator"),
        ("punctuation_boundary", "well-known cats' one,,two step;; clue",
         "hyphen, apostrophe and adjacent punctuation: each breaks a word "
         "under §7.3 and each is a place a reader would not"),
        ("unicode_boundary", _UNICODE_TEXT,
         "U+0130, the one character on which §7.3's segment-then-fold and "
         "§9.2's fold-then-segment disagree"),
        ("case_folding_boundary", "Thus THUS thus Point POINT",
         "the same words in three cases: letter tests fold, and a word's own "
         "letters do not"),
        ("malformed_delimiter",
         "one,,two step;; clue point... clue"
         if statistic_id in ("comma", "semicolon", "sentence") else None,
         "runs of the counted character with nothing between them"
         if statistic_id in ("comma", "semicolon", "sentence") else
         "not applicable: this numerator counts no delimiter, and the answer "
         "format has none"),
    ]

    applies = applicability(kind)
    pool = _candidates(kind, q)
    for defect in DEFECT_KINDS:
        if not applies[defect]["meaningful"]:
            continue
        found = separating_case(kind, q, defect, pool)
        built.append((
            f"separator:{defect}", found,
            f"constructed to separate the registered reading from "
            f"{defect}: on this answer the two record different verdicts"
            if found is not None else
            f"no constructed answer separates {defect} here, although the "
            f"applicability rule calls it meaningful"))

    cases: list[dict[str, Any]] = []
    for case_kind, text, why in built:
        if text is None:
            cases.append({"kind": kind, "severity": q, "case_kind": case_kind,
                          "text": None, "why": why, "constructed": False})
            continue
        registered = passes(constraint(kind, q), _count(statistic_id, text),
                            text)
        cases.append({
            "kind": kind, "severity": q, "case_kind": case_kind,
            "text": text, "why": why, "constructed": True,
            "words": word_count(text),
            "statistic": _count(statistic_id, text),
            "derived": _value(spec, text),
            "registered_verdict": registered,
            "non_vacuous": non_vacuous(constraint(kind, q), text,
                                       truncated=False),
            "alternative_readings": {
                defect: reading_verdict(kind, q, text, defect)
                for defect in DEFECT_KINDS},
        })
        cases[-1]["separates"] = sorted(
            d for d, v in cases[-1]["alternative_readings"].items()
            if v != registered)
    return cases


# ------------------------------------------- alternative readings for A and B

def _drift_words(text: str) -> list[str]:
    """v4r2's composition: fold the whole answer, then segment.

    The same helper `microcase._drift_words` uses, restated here so that A and
    B's readings do not depend on a private name in a module §10.4-R2 froze.
    """
    return _v4_alpha_runs(text.lower())


def _outcome_reading(kind: str, severity: int, text: str,
                     defect: str) -> bool:
    """R5's registered alternative readings for the two outcome constraints.

    §10.4-R2's `defect_verdict` covers the twenty families only. These are
    defined here, under R5, and are recorded as R5-defined on every card so
    that no reader takes them for R2 evidence.
    """
    q = severity
    if kind == "A":
        statistic = s0_count(text)
        if defect == "numerator_swap":
            # The substring reading: "howevers" and "however" both count.
            statistic = text.lower().count("however")
        elif defect == "segmentation_drift":
            # A's registered counter already folds and then segments (§9.2).
            # Its drift is therefore §7.3's order -- segment, then fold --
            # which is the family word list. The direction matters: reading it
            # the other way would call A's own registered rule the defect.
            statistic = sum(1 for w in alpha_runs_of(text)
                            if w.lower() == "however")
        elif defect == "off_by_one":
            q = q - 1
        elif defect == "vacuity_ignored":
            if not text.strip():
                return True
        elif defect == "denominator_swap":
            return s0_count(text) == q          # no denominator to swap
        if defect == "inequality_flip":
            return statistic >= q               # "at least n", not "exactly n"
        return statistic == q
    if kind == "B":
        runs = alpha_runs_of(text)
        statistic = max((len(w) for w in runs), default=0)
        if defect == "numerator_swap":
            # The mean reading: "no word longer than m" read as an average.
            statistic = (sum(len(w) for w in runs) / len(runs)) if runs else 0
        elif defect == "segmentation_drift":
            drifted = _drift_words(text)
            statistic = max((len(w) for w in drifted), default=0)
        elif defect == "off_by_one":
            q = q - 1
        elif defect == "denominator_swap":
            return focal_statistic(text) <= q   # no denominator to swap
        elif defect == "vacuity_ignored":
            return focal_statistic(text) <= q   # a budget already passes it
        if defect == "inequality_flip":
            return statistic >= q
        return statistic <= q
    raise ProtocolError(f"{kind!r} is not an outcome constraint")


def alpha_runs_of(text: str) -> list[str]:
    from dci1v4r3.verifiers.words import alpha_runs
    return alpha_runs(text)


def reading_verdict(kind: str, severity: int, text: str,
                    defect: str) -> bool:
    """The verdict a reading carrying ``defect`` would record, for any kind."""
    if defect not in DEFECT_KINDS:
        raise ProtocolError(f"{defect!r} is not a registered defect kind")
    if kind in ("A", "B"):
        return _outcome_reading(kind, severity, text, defect)
    return defect_verdict(constraint(kind, severity), text, defect)


def reading_source(kind: str) -> str:
    return ("§10.7-R5, this module (§10.4-R2's defect_verdict covers families "
            "only)" if kind in ("A", "B") else
            "§10.4-R2 microcase.defect_verdict, unchanged")


# ------------------------------------------------------------ applicability

def applicability(kind: str) -> dict[str, dict[str, Any]]:
    """A.3: for each reading, is it meaningful here, and why or why not.

    A registered rule, stated once. `stages.mutation` then checks every
    ``meaningful: False`` against the corpus instead of believing it, so a
    reason recorded here that turns out to be wrong fails the gate.
    """
    form = form_of(kind)
    statistic_id = statistic_id_of(kind)
    is_rate = form in _RATE_FORMS
    out: dict[str, dict[str, Any]] = {}

    out["numerator_swap"] = {
        "meaningful": True,
        "reason": "every form reads a numerator, so a reader can read the "
                  "wrong one"}
    out["inequality_flip"] = {
        "meaningful": True,
        "reason": "every form carries a direction, so a reader can take the "
                  "other one"}
    out["off_by_one"] = {
        "meaningful": True,
        "reason": "every form carries a threshold, so a reader can put the "
                  "boundary on the wrong side of it"}
    out["denominator_swap"] = (
        {"meaningful": True,
         "reason": "the form divides by a word count, and a reader looking at "
                   "a string can divide by its characters instead"}
        if is_rate else
        {"meaningful": False,
         "reason": f"{form} compares a count and has no denominator, so there "
                   "is nothing to swap"})
    if is_rate:
        out["segmentation_drift"] = {
            "meaningful": True,
            "reason": "the rate denominator is a word count, and folding "
                      "before segmenting splits a word that carries U+0130, "
                      "so the denominator moves whatever the numerator reads"}
    elif statistic_id in CHARACTER_GRAIN:
        out["segmentation_drift"] = {
            "meaningful": False,
            "reason": f"{statistic_id} counts raw characters of the answer "
                      f"and {form} has no word denominator, so no composition "
                      "order can move either side of the comparison"}
    elif statistic_id in SUFFIX_TESTS:
        out["segmentation_drift"] = {
            "meaningful": False,
            "reason": "folding before segmenting splits a word carrying "
                      "U+0130 into a first piece ending in the folded i and a "
                      "final piece carrying the original word's ending. A "
                      "suffix test therefore matches the same words under "
                      "either order: the extra piece can never end in "
                      f"{statistic_id.split('_')[0]!r}, and the piece that "
                      "does keeps the ending it had. Registered as a "
                      "non-separable reading and checked against the whole "
                      "corpus rather than asserted"}
    else:
        out["segmentation_drift"] = {
            "meaningful": True,
            "reason": "the numerator reads a word list, and folding before "
                      "segmenting changes which words are in it"}
    out["vacuity_ignored"] = (
        {"meaningful": True,
         "reason": ("a wordless answer has no rate, and treating 0/0 as "
                    "satisfying is the reading the rule exists to exclude"
                    if is_rate else
                    "an empty answer reaches the threshold from below, and "
                    "treating it as satisfying is the reading the rule "
                    "excludes")}
        if is_rate or form in (FORM_LOWER_BOUND, FORM_EXACT) else
        {"meaningful": False,
         "reason": f"{form} is satisfied by an empty answer under the "
                   "registered reading as well, so no verdict moves. §9.3's "
                   "non-vacuity flag records that pass separately and is not "
                   "part of the predicate"})
    return out


# ------------------------------------------------------------- the audit

def _corpus() -> list[str]:
    """The frozen boundary corpus. A.2 runs on all of it, not a sample."""
    return [case["text"] for case in ALL_CASES]


def audit_family(kind: str, *, corpus: Sequence[str] | None = None
                 ) -> dict[str, Any]:
    """A.1, A.2 and A.3 for one family or outcome constraint."""
    spec = specification(kind)
    cases = spec_cases(kind)
    texts = list(corpus if corpus is not None else _corpus())
    texts += [c["text"] for c in cases if c["text"] is not None]

    missing = [f for f in SPEC_FIELDS if not spec.get(f)]

    # A.2: the recorded predicate against the verifier, at EVERY severity of
    # the declared range, on the whole corpus. Severity-invariance measured,
    # not assumed.
    disagreements: list[dict[str, Any]] = []
    checked = 0
    for severity in declared_range(kind):
        rule = constraint(kind, severity)
        statistic_id = spec["counted_statistic"]
        for text in texts:
            checked += 1
            if (evaluate_specification(spec, severity, text)
                    != passes(rule, _count(statistic_id, text), text)):
                disagreements.append({"severity": severity,
                                      "text": text[:60]})
    applies = applicability(kind)
    separated: dict[str, list[str]] = {d: [] for d in DEFECT_KINDS}
    for case in cases:
        for defect in case.get("separates", ()):
            separated[defect].append(case["case_kind"])

    unresolved = [d for d in DEFECT_KINDS
                  if applies[d]["meaningful"] and not separated[d]]
    return {
        "kind": kind,
        "form": spec["form"],
        "audit_severity": audit_severity(kind),
        "declared_range": list(declared_range(kind)),
        "specification": spec,
        "specification_complete": not missing,
        "missing_fields": missing,
        "cases": cases,
        "cases_constructed": sum(1 for c in cases if c["constructed"]),
        "cases_not_applicable": [c["case_kind"] for c in cases
                                 if not c["constructed"]],
        "predicate_check": {
            "severities": len(declared_range(kind)),
            "texts": len(texts),
            "comparisons": checked,
            "disagreements": disagreements[:10],
            "agreement": 1.0 if not disagreements else 0.0,
        },
        "alternative_readings": {
            "source": reading_source(kind),
            "applicability": applies,
            "separated_by": separated,
        },
        "unresolved_readings": unresolved,
        "ambiguous": bool(missing or disagreements or unresolved),
    }


def run_specification_audit(kinds: Iterable[str] | None = None
                            ) -> dict[str, Any]:
    """A, over every family and form in the final instrument population."""
    population = sorted({k for k, _ in instrument_population()})
    audited = sorted(kinds) if kinds is not None else population
    corpus = _corpus()
    families = {kind: audit_family(kind, corpus=corpus) for kind in audited}
    ambiguous = sorted(k for k, a in families.items() if a["ambiguous"])
    forms = sorted({a["form"] for a in families.values()})
    return {
        "population_kinds": population,
        "audited_kinds": audited,
        "covered": sorted(set(population) - set(audited)) == [],
        "uncovered_kinds": sorted(set(population) - set(audited)),
        "forms": forms,
        "boundary_corpus": len(corpus),
        "families": families,
        "ambiguous_kinds": ambiguous,
        "passed": not ambiguous and not (set(population) - set(audited)),
        "criterion": "A.1 completeness, A.2 the recorded predicate reproduces "
                     "the verifier at every declared severity on the whole "
                     "boundary corpus and every constructed case, A.3 every "
                     "meaningful alternative reading is separated by a "
                     "constructed case",
    }


def specification_hash(audit: Mapping[str, Any] | None = None) -> str:
    """A content hash over the audit, for the §10.7-R5 E binding."""
    audit = audit if audit is not None else run_specification_audit()
    return sha_text(canonical_json(audit))


# ------------------------------------------------------ A': wording review

#: The three classes §10.7-R5 A' registers. A wording in the third class
#: blocks Gate 1 until it is corrected and its dependent evidence invalidated.
WORDING_CLASSES = ("awkward_unambiguous", "genuinely_ambiguous",
                   "requires_correction")


def _number_agrees(wording: str, severity: int) -> bool:
    """Does the wording's grammatical number match its numeral?

    Only q = 1 can disagree, and it disagrees when the noun the numeral
    governs is plural. Checked by looking for `1 <word>s` rather than by
    parsing: the wordings are five to eight words long and the numeral always
    governs the token after it.
    """
    tokens = wording.replace(".", "").split()
    for index, token in enumerate(tokens[:-1]):
        if token == str(severity) and severity == 1:
            return not tokens[index + 1].endswith("s")
    return True


def wording_review() -> dict[str, Any]:
    """A': every wording of every instrument, classified.

    The direction check is what makes this more than a plural audit: a wording
    that named the wrong direction would be a treatment that does not describe
    the predicate scoring it, and no amount of verifier evidence would show it.
    """
    findings: list[dict[str, Any]] = []
    checked = 0
    for kind, severity in instrument_population():
        form = form_of(kind)
        for index, text in enumerate(wordings(kind, severity)):
            checked += 1
            lowered = text.lower()
            bounds = any(phrase in lowered
                         for phrase in BOUNDING_PHRASES[form])
            requires = any(phrase in lowered
                           for phrase in REQUIRING_PHRASES)
            if not bounds and requires and form in _LOWER_BOUND_FORMS_A:
                findings.append({
                    "kind": kind, "severity": severity, "wording_index": index,
                    "wording": text, "finding": "direction_implicit",
                    "classification": "awkward_unambiguous",
                    "why": "the wording states a requirement of q rather than "
                           "a bound. On a lower-bound form the two agree: an "
                           "answer that needs q of something has q of it when "
                           "it has more, so every reading of the wording "
                           "selects the registered predicate"})
            elif not bounds:
                findings.append({
                    "kind": kind, "severity": severity, "wording_index": index,
                    "wording": text, "finding": "direction_not_named",
                    "classification": "genuinely_ambiguous",
                    "why": f"the wording states q as a target and names no "
                           f"bound, so it does not distinguish the registered "
                           f"predicate ({_OPERATOR[form]} q) from the reading "
                           f"that takes q as exact. Both readings call the "
                           f"same answers at q compliant, and they disagree "
                           f"on every answer past it -- which the verifier "
                           f"scores as a pass"})
            if not _number_agrees(text, severity):
                findings.append({
                    "kind": kind, "severity": severity, "wording_index": index,
                    "wording": text, "finding": "plural_noun_at_q_equals_one",
                    "classification": "awkward_unambiguous",
                    "why": "the numeral is 1 and the noun it governs is "
                           "plural. The numeral is unambiguous and is what "
                           "the verifier reads; the mismatch is a register "
                           "artefact of rendering severity as a numeral in a "
                           "frozen template, which §7.5's severity-invariance "
                           "requires"})
    by_class = {name: [f for f in findings if f["classification"] == name]
                for name in WORDING_CLASSES}
    return {
        "wordings_checked": checked,
        "instruments": len(instrument_population()),
        "findings": findings,
        "counts": {name: len(rows) for name, rows in by_class.items()},
        "requires_correction": by_class["requires_correction"],
        "genuinely_ambiguous": by_class["genuinely_ambiguous"],
        "passed": not by_class["requires_correction"]
                  and not by_class["genuinely_ambiguous"],
        "criterion": "no wording is classified genuinely_ambiguous or "
                     "requires_correction. An awkward-but-unambiguous wording "
                     "does not block, and is recorded rather than fixed: "
                     "changing a live wording invalidates every measurement "
                     "taken under it (§10.7-R5 A')",
    }


def wordings_hash() -> str:
    """E: every model-facing wording in the final population, hashed.

    §10.6 binds the verifier hash and not this one, because a wording cannot
    change what a verifier computes. It can change what the model was asked,
    which is why R5 binds it separately: a silent wording edit is otherwise
    invisible to every downstream check.
    """
    table = {f"{kind}:{severity}": list(wordings(kind, severity))
             for kind, severity in instrument_population()}
    return sha_text(canonical_json(table))
