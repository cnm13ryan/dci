"""§10.4-R2's unit of validation: one instruction, one tiny answer.

**Why the unit changed.** §10.4-R asked an external judge to audit an
*operationalization card* --- the convention, the numerator, the denominator,
the arithmetic and the verdict --- on a real experimental response. It failed
four of five criteria, and the planted-defect arm showed why: the judge
recounted the response when the prompt told it not to (8 of 12 wrongly-failed
faithful cards were justified "wrong count of *however*"), and it was blind to
`vacuity_ignored`, 0 of 5, while catching `numerator_swap` and `off_by_one` 9
of 9 each. The diagnosis registered in amendment R1 --- that the task failed
because it was arithmetic --- was **wrong**: the repaired pathway reproduced
0.3125 truncation against §10.4's own 0.319. What binds is the reasoning
chain, not the enumeration.

So R2 removes the chain. A microcase is an instruction of five to eight words
and an answer of at most a dozen, small enough that no counting or extended
reasoning is required, and the validator returns one word. It never sees the
verifier's verdict, its derivation, or any label, so agreement cannot be
produced by agreeing.

**What makes the set informative.** Every case is placed at a boundary where a
*defective* reading of the same instruction gives a different verdict from the
registered one. The six defect kinds are §10.4's, and five of them are
implemented here as real alternative readings rather than as descriptions ---
`segmentation_drift` in particular is the actual composition error §10.2 found
in the carried helper, `alpha_runs(text.lower())`, and not a hypothetical one.
A validator that reads the instruction the way the verifier scores it agrees
with the registered verdict on those cases; a validator whose reading coincides
with a defect disagrees, and which cases it disagrees on says which defect.

**Two arms, because two of the six kinds are not determined by the
instruction.** A five-word wording says nothing about whether `well-known` is
one word or two, or about what a rate means when there are no words. Judging
`segmentation_drift` or `vacuity_ignored` on the wording alone would be asking
the validator to guess a convention and then scoring it for guessing wrong.

* the **instruction-only** arm shows the wording and the answer, and carries
  `inequality_flip`, `off_by_one`, `numerator_swap` and `denominator_swap` ---
  every kind the instruction alone determines;
* the **conventions** arm adds §7.3's registered lexical and rate rules,
  constant across every case and therefore incapable of leaking any case's
  verdict, and carries `segmentation_drift` and `vacuity_ignored`.

Both arms run the same cases, the same parser and the same thresholds, and both
are reported. A disagreement in the instruction-only arm that the conventions
arm resolves is a fact about the wording, not about the verifier, and §10.4-R2
records it as one.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import canonical_json, sha_text
from dci1v4.verifiers.target import s0_count
from dci1v4.verifiers.words import alpha_runs as _v4_alpha_runs

from dci1v6.protocol.wordings import N_WORDINGS, wording
from dci1v6.verifiers.compliance import passes
from dci1v6.verifiers.constraints import (MARKER_WORDS, 
    FAMILIES, FORM_COUNT, FORM_EXACT, FORM_LOWER_BOUND, FORM_RATE,
    FORM_RATE_LOWER_BOUND, Constraint, declared_range,
)
from dci1v6.verifiers.statistics import STATISTICS, focal_statistic, word_count
from dci1v6.verifiers.witnesses import FEATURE_WORD, FILLER, feature_free

__all__ = ["DEFECT_KINDS", "ARM_INSTRUCTION", "ARM_CONVENTIONS",
           "ARM_OF_DEFECT", "CONVENTIONS_TEXT", "NUMERATOR_SWAP",
           "TARGET_PER_DEFECT", "TARGET_TOTAL", "PHENOMENON_TEXTS",
           "MAX_ANSWER_WORDS",
           "Microcase", "defect_verdict", "build_cases", "split_cases",
           "generator_hash", "case_set_hash", "stratum_counts"]

#: §10.4's six defect kinds, unchanged. R2 changes the unit of validation, not
#: the taxonomy of what can go wrong with an operationalization.
DEFECT_KINDS = ("numerator_swap", "denominator_swap", "inequality_flip",
                "off_by_one", "segmentation_drift", "vacuity_ignored")

ARM_INSTRUCTION = "instruction_only"
ARM_CONVENTIONS = "with_conventions"

#: Which arm decides each kind. Registered before any case was judged.
ARM_OF_DEFECT = {
    "numerator_swap": ARM_INSTRUCTION,
    "denominator_swap": ARM_INSTRUCTION,
    "inequality_flip": ARM_INSTRUCTION,
    "off_by_one": ARM_INSTRUCTION,
    "segmentation_drift": ARM_CONVENTIONS,
    "vacuity_ignored": ARM_CONVENTIONS,
}

#: §7.3's registered conventions, stated once and identically for every case
#: of the conventions arm. Constant across cases, so it carries no information
#: about any case's verdict; it carries the protocol's own definitions, which
#: §10.2 already certifies the implementation against.
CONVENTIONS_TEXT = (
    "These definitions apply to the instruction below.\n"
    "- A word is a maximal run of letters. Digits, punctuation, spaces and "
    "symbols end a word, so a hyphenated form is two words and an "
    "apostrophised form is two words.\n"
    "- Letter tests read the word lower-cased, but a word's letters are the "
    "letters it is written with.\n"
    "- A percentage of words is that count divided by the number of words in "
    "the whole answer. An answer with no words has no percentage, and an "
    "instruction stated as a percentage is not satisfied by it.\n"
    "- Commas, semicolons and sentence-ending marks are counted as characters "
    "of the answer.\n"
    "- A sentence ends at a run of . ! or ?; text after the last such run is "
    "one more sentence."
)

#: The sibling numerator a `numerator_swap` reads instead. Chosen so the swap
#: is *plausible* --- a reader who mistook which feature was meant would
#: plausibly count this one --- and so that the two differ on the case texts.
NUMERATOR_SWAP = {
    "b_initial": "t_initial", "ing_final": "y_final",
    "one_letter": "doubled_letter", "doubled_letter": "one_letter",
    "comma": "semicolon", "capital_char": "capital_word",
    "capital_word": "capital_char", "letter_a": "vowel_initial",
    "y_final": "s_final", "t_initial": "b_initial", "s_final": "y_final",
    "vowel_initial": "letter_a", "sentence": "comma",
    "semicolon": "comma",
    # v5's eight markers swap for **each other**. That is the plausible
    # confusion in a same-form pool --- a reader who mistook which connective
    # was meant would count another connective, not a letter property --- and
    # it is the discrimination v5's Tier-1 design most needs to establish.
    # v4r4 swapped `marker_thus` for `t_initial`, which was the plausible
    # confusion when `thus` was the only marker in the library.
    "marker_thus": "marker_hence", "marker_hence": "marker_thus",
    "marker_though": "marker_whereas", "marker_whereas": "marker_though",
    "marker_indeed": "marker_namely", "marker_namely": "marker_indeed",
    "marker_instead": "marker_overall", "marker_overall": "marker_instead",
}
assert set(NUMERATOR_SWAP) == set(STATISTICS)


@dataclass(frozen=True)
class Microcase:
    """One (instruction, answer) pair and everything derivable from it."""

    case_id: str
    kind: str
    severity: int
    wording_index: int
    text: str
    covers: str
    #: The registered verdict: what the deterministic verifier records.
    correct: bool
    #: defect kind -> the verdict that reading would record.
    defect_verdicts: dict[str, bool] = field(default_factory=dict)

    @property
    def instruction(self) -> str:
        return wording(self.kind, self.wording_index, self.severity)

    @property
    def discriminates(self) -> tuple[str, ...]:
        """The kinds this case separates from the registered reading."""
        return tuple(d for d in DEFECT_KINDS
                     if d in self.defect_verdicts
                     and self.defect_verdicts[d] != self.correct)

    def as_dict(self) -> dict[str, Any]:
        return {"case_id": self.case_id, "kind": self.kind,
                "severity": self.severity, "wording_index": self.wording_index,
                "form": FAMILIES[self.kind].form,
                "statistic_id": FAMILIES[self.kind].statistic_id,
                "text": self.text, "covers": self.covers,
                "instruction": self.instruction,
                "correct": self.correct,
                "defect_verdicts": dict(self.defect_verdicts),
                "discriminates": list(self.discriminates)}


# ---------------------------------------------------------- defect readings

def _drift_words(text: str) -> list[str]:
    """v4r2's composition: fold the whole answer, *then* segment.

    Not a hypothetical defect. This is the carried helper §10.2's prose-only
    reimplementation disagreed with, and the disagreement is what made §7.3
    register the corrected order.
    """
    return _v4_alpha_runs(text.lower())


def _drift_statistic(statistic_id: str, text: str) -> int:
    """The same numerator read over the drifted word list."""
    words = _drift_words(text)
    if statistic_id == "b_initial":
        return sum(1 for w in words if w.startswith("b"))
    if statistic_id == "ing_final":
        return sum(1 for w in words if w.endswith("ing"))
    if statistic_id == "one_letter":
        return sum(1 for w in words if len(w) == 1)
    if statistic_id == "doubled_letter":
        return sum(1 for w in words if any(a == b for a, b in zip(w, w[1:])))
    if statistic_id == "letter_a":
        return sum(1 for w in words if "a" in w)
    if statistic_id == "y_final":
        return sum(1 for w in words if w.endswith("y"))
    if statistic_id == "t_initial":
        return sum(1 for w in words if w.startswith("t"))
    if statistic_id == "s_final":
        return sum(1 for w in words if w.endswith("s"))
    if statistic_id == "vowel_initial":
        return sum(1 for w in words if w[:1] in "aeiou")
    if statistic_id in MARKER_WORDS:
        # All eight markers, from the registered vocabulary rather than one
        # by one. v4r4 had a single marker family and this branch named its
        # word; with eight of them, seven fell through to the raw-character
        # return below and their drifted count came back **undrifted**, so no
        # constructed case could separate the reading and §10.7 A recorded
        # them ambiguous. Found by running the audit over v5's library.
        target = MARKER_WORDS[statistic_id]
        return sum(1 for w in words if w == target)
    if statistic_id == "capital_word":
        return sum(1 for w in words if any(c.isupper() for c in w))
    # comma, semicolon, capital_char and sentence read raw characters, which
    # the composition order cannot move.
    return STATISTICS[statistic_id](text)


def defect_verdict(constraint: Constraint, text: str, defect: str) -> bool:
    """The verdict a reading carrying ``defect`` would record.

    Every branch is a *reading of the same instruction*, not a corruption of
    the answer: the microcase is fixed and only the operationalization varies,
    which is what makes a disagreement attributable.
    """
    if defect not in DEFECT_KINDS:
        raise ProtocolError(f"{defect!r} is not a registered defect kind")
    kind, q = constraint.kind, constraint.severity
    family = FAMILIES[kind]
    form, statistic_id = family.form, family.statistic_id
    words = word_count(text)
    statistic = STATISTICS[statistic_id](text)
    is_rate = form in (FORM_RATE, FORM_RATE_LOWER_BOUND)
    is_lower = form in (FORM_LOWER_BOUND, FORM_RATE_LOWER_BOUND)

    if defect == "numerator_swap":
        statistic = STATISTICS[NUMERATOR_SWAP[statistic_id]](text)
    elif defect == "segmentation_drift":
        statistic = _drift_statistic(statistic_id, text)
        words = len(_drift_words(text))
    elif defect == "denominator_swap":
        if not is_rate:
            return passes(constraint, statistic, text)   # no denominator
        # Per hundred characters rather than per hundred words: the swap a
        # reader makes when the instruction says "percent" and the thing in
        # front of them is a string.
        words = len(text)
    elif defect == "off_by_one":
        q = q - 1 if not is_lower else q + 1
    elif defect == "vacuity_ignored":
        if words == 0 and is_rate:
            return True          # treats 0/0 as satisfying
        if not text.strip() and form in (FORM_LOWER_BOUND, FORM_EXACT):
            return True          # treats an empty answer as satisfying

    if form == FORM_COUNT:
        ok = statistic <= q
    elif form == FORM_EXACT:
        ok = statistic == q
    elif form == FORM_LOWER_BOUND:
        ok = statistic >= q
    else:
        if words == 0:
            ok = False
        else:
            rate = 100.0 * statistic / words
            ok = rate <= q if form == FORM_RATE else rate >= q
    if defect == "inequality_flip":
        if form == FORM_EXACT:
            # "at least q" instead of "exactly q": the flip an exact count
            # admits.
            ok = statistic >= q
        else:
            ok = not ok
    return ok


# ------------------------------------------------------- case construction

def _carrier(statistic_id: str) -> str:
    return FEATURE_WORD[statistic_id]


def _build_text(statistic_id: str, count: int, pad: int) -> str:
    """``count`` carriers and ``pad`` feature-free words, in that order."""
    carrier = _carrier(statistic_id)
    if statistic_id in ("comma", "semicolon", "sentence"):
        # Character numerators attach to words, so the answer stays an answer.
        head = [f"{FILLER[i % len(FILLER)]}{carrier}" for i in range(count)]
        return " ".join(head + [feature_free(pad)]).strip()
    return " ".join([carrier] * count + [feature_free(pad)]).strip()


#: Phenomena every family's candidate pool must reach, and the answer that
#: reaches them. Authored once; every verdict is computed, never asserted.
PHENOMENON_TEXTS: tuple[tuple[str, str], ...] = (
    ("case-folding-split", "İstanbul"),
    ("case-folding-split;longer", "İstanbul is one word"),
    ("case-folding-split;repeated", "İİ point"),
    ("case-folding-split;initial", "İce clue"),
    ("hyphenated-form", "well-known form"),
    ("hyphenated-form;two", "co-operate well-known"),
    ("apostrophised-form", "cats' toys"),
    ("apostrophised-form;single", "step's"),
    ("capitalisation", "Thus Point Clue"),
    ("capitalisation;shout", "THUS POINT"),
    ("adjacent-punctuation", "one,,two"),
    ("adjacent-punctuation;semicolon", "step;; clue"),
    ("empty-output", ""),
    ("empty-output;whitespace", "   "),
    ("wordless", ",,,"),
    ("wordless;semicolons", ";;;"),
    ("wordless;terminators", "..."),
    ("single-word-answer", "point"),
    ("single-word-answer;one-letter", "n"),
    ("terminator-run", "point... clue"),
    ("unterminated-tail", "point clue"),
    ("sentence-boundary;two", "point. clue"),
)

#: §10.4-R2's registered selection rule. The candidate pool is much larger than
#: any judge run can afford, so a rule decides which cases are judged --- and
#: it is fixed here, before any case was judged, and reads only properties of
#: the case: which defects it separates, what the registered verdict is, and
#: which family it belongs to. It never reads a validator's answer.
TARGET_PER_DEFECT = 20
TARGET_TOTAL = 160


def _case_id(kind: str, tag: str, index: int) -> str:
    digest = hashlib.sha256(f"{kind}|{tag}|{index}".encode()).hexdigest()[:8]
    return f"mc-{kind.lower()}-{index:02d}-{digest}"


#: No microcase answer may exceed this many words. §10.4-R2's whole premise is
#: that the validator does not have to count, and an answer of sixty words is
#: an answer it has to count. A case that would exceed it is dropped from the
#: pool rather than shortened, so no case is quietly a different case.
MAX_ANSWER_WORDS = 14


def _severity_for(kind: str) -> int:
    """The smallest declared severity that is at least one.

    Deterministic, family-local, and fixed before any case was judged --- so it
    is not a severity picked because the validator did better there. Smallest,
    because the answer that sits at severity q has about q carrier words in it
    and §10.4-R2 needs answers a reader takes in at a glance: `CL7`'s median
    rung is sixty, and a sixty-word answer is the counting task R2 exists to
    remove. At least one, so that the three-point sweep q-1, q, q+1 exists for
    every family.

    The cost is registered rather than hidden: every case audits the
    operationalization at the *bottom* of its family's declared range. What is
    being validated is the reading of the predicate, and both the predicate and
    the wording are severity-invariant by construction (§7.5), so the reading
    does not depend on where in the range the rung sits --- but the audit does
    not demonstrate that, it assumes it.
    """
    return min(q for q in declared_range(kind) if q >= 1)


def _pool(kinds: Sequence[str]) -> list[Microcase]:
    """Every candidate case, before selection."""
    cases: list[Microcase] = []
    for kind in kinds:
        family = FAMILIES[kind]
        q = _severity_for(kind)
        statistic_id = family.statistic_id
        index = 0
        specs: list[tuple[str, str]] = []
        for offset, tag in ((-1, "threshold-minus-one"),
                            (0, "exact-threshold"),
                            (1, "threshold-plus-one")):
            if family.form in (FORM_RATE, FORM_RATE_LOWER_BOUND):
                # Ten words, so a count of k reads as 10k percent and the
                # sweep lands on either side of q without arithmetic.
                count = max(0, round(q * 10 / 100.0) + offset)
                specs.append((f"{tag};rate",
                              _build_text(statistic_id, count,
                                          max(0, 10 - count))))
            else:
                target = q + offset
                if target < 0:
                    continue
                specs.append((tag, _build_text(statistic_id, target, 6)))
        specs.extend(PHENOMENON_TEXTS)
        for tag, text in specs:
            constraint = Constraint(kind, q, reserve=q not in family.ladder)
            statistic = STATISTICS[statistic_id](text)
            correct = passes(constraint, statistic, text)
            verdicts = {d: defect_verdict(constraint, text, d)
                        for d in DEFECT_KINDS}
            if word_count(text) > MAX_ANSWER_WORDS:
                index += 1
                continue
            cases.append(Microcase(
                case_id=_case_id(kind, tag, index), kind=kind, severity=q,
                wording_index=index % N_WORDINGS, text=text, covers=tag,
                correct=correct, defect_verdicts=verdicts))
            index += 1
    return cases


def _select(pool: Sequence[Microcase]) -> list[Microcase]:
    """The registered selection: scarce defects first, verdicts balanced.

    Scarcest kind first, because a kind with three discriminating cases in the
    pool cannot reach the four-item floor if the abundant kinds have already
    filled the budget. Verdicts alternate, because a validator that answers
    the same word to everything must not be able to pass: with the two halves
    balanced, always-yes scores one on specificity and zero on sensitivity.
    """
    scarcity = sorted(
        DEFECT_KINDS,
        key=lambda d: (sum(1 for c in pool if d in c.discriminates), d))
    chosen: dict[str, Microcase] = {}
    per_family: dict[str, int] = {}

    def admit(case: Microcase) -> None:
        chosen[case.case_id] = case
        per_family[case.kind] = per_family.get(case.kind, 0) + 1

    for defect in scarcity:
        sides = {
            want: sorted((c for c in pool
                          if c.case_id not in chosen
                          and defect in c.discriminates
                          and c.correct is want),
                         key=lambda c: (per_family.get(c.kind, 0), c.case_id))
            for want in (True, False)}
        have = sum(1 for c in chosen.values() if defect in c.discriminates)
        # Interleave the two verdict sides so the kind stays balanced, and
        # fall through to whichever side still has cases when one runs out ---
        # `vacuity_ignored` is nearly all violations, and a rule that insisted
        # on halves would have left it below the four-item floor.
        want = False
        while have < TARGET_PER_DEFECT and (sides[True] or sides[False]):
            queue = sides[want] or sides[not want]
            case = queue.pop(0)
            if case.case_id not in chosen:
                admit(case)
                have += 1
            want = not want

    # Fill to the total, alternating verdicts and spreading over families.
    while len(chosen) < TARGET_TOTAL:
        satisfied = sum(1 for c in chosen.values() if c.correct)
        want = satisfied <= (len(chosen) - satisfied)
        candidates = sorted(
            (c for c in pool
             if c.case_id not in chosen and c.correct is want),
            key=lambda c: (per_family.get(c.kind, 0), c.case_id))
        if not candidates:
            candidates = sorted((c for c in pool if c.case_id not in chosen),
                                key=lambda c: (per_family.get(c.kind, 0),
                                               c.case_id))
        if not candidates:
            break
        admit(candidates[0])
    return sorted(chosen.values(), key=lambda c: c.case_id)


def build_cases(kinds: Sequence[str] | None = None) -> list[Microcase]:
    """The frozen microcase set: a pool, then the registered selection.

    Deterministic. Every verdict --- registered and defective --- is computed
    from the text, so a case that fails to hit its intended statistic is a
    case with a different statistic and not a wrong expectation.
    """
    kinds = list(kinds) if kinds is not None else list(FAMILIES)
    return _select(_pool(kinds))


def split_cases(cases: Sequence[Microcase]) -> dict[str, list[Microcase]]:
    """§10.4's held-out discipline: a deterministic halving by case id.

    By hash of the case id and nothing else, so the split cannot depend on a
    case's difficulty, its family, its verdict or how any validator did on it.
    """
    development, calibration = [], []
    for case in cases:
        digit = int(hashlib.sha256(case.case_id.encode()).hexdigest()[:8], 16)
        (development if digit % 2 == 0 else calibration).append(case)
    return {"development": development, "calibration": calibration}


def case_set_hash(cases: Sequence[Microcase]) -> str:
    return sha_text(canonical_json([c.as_dict() for c in cases]))


def generator_hash() -> str:
    """One hash over everything that decides what a case is."""
    from pathlib import Path
    source = Path(__file__).read_bytes()
    return sha_text(canonical_json({
        "source": hashlib.sha256(source).hexdigest(),
        "defect_kinds": list(DEFECT_KINDS),
        "numerator_swap": NUMERATOR_SWAP,
        "conventions": CONVENTIONS_TEXT,
        "phenomena": [t for t, _ in PHENOMENON_TEXTS]}))


def stratum_counts(cases: Sequence[Microcase]) -> dict[str, Any]:
    """Family x form x defect coverage, and the verdict balance.

    The balance matters more than it looks. A validator that answers YES to
    everything scores perfectly on the satisfied half and zero on the other,
    so the two halves have to be comparable for the criteria to be
    informative at all.
    """
    by_form: dict[str, int] = {}
    by_defect: dict[str, int] = {}
    for case in cases:
        by_form[FAMILIES[case.kind].form] = \
            by_form.get(FAMILIES[case.kind].form, 0) + 1
        for defect in case.discriminates:
            by_defect[defect] = by_defect.get(defect, 0) + 1
    satisfied = sum(1 for c in cases if c.correct)
    return {"cases": len(cases), "families": len({c.kind for c in cases}),
            "by_form": by_form, "discriminating_by_defect": by_defect,
            "correct_satisfied": satisfied,
            "correct_not_satisfied": len(cases) - satisfied,
            "satisfied_share": satisfied / len(cases) if cases else 0.0}


def _unused() -> Callable:                              # pragma: no cover
    return focal_statistic or s0_count
