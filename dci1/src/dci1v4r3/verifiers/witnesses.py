"""§7.5's joint-satisfiability and non-entailment witnesses.

Two obligations, both discharged by machine-verified construction rather than
by argument:

* **joint satisfiability** — for every realisable pair of registered
  constraint instances of distinct kinds, one response satisfies both;
* **non-entailment** — for the same pairs, one response satisfies the first and
  fails the second, and one does the reverse.

**Which pairs are realisable, and why the question has an answer.** §8.1's
composed cells put two constituents together, and only these combinations
occur: $A$ with anything, $B$ with anything, one core reference with another,
and the class companion with $A$ or $B$. Two core references co-occur, so the
obligation covers reference-with-reference; but §13.4 requires the three core
references to come from three different **counted statistics**, so two
instances of the same numerator never co-occur and the obligation does not
cover them.

That scoping is not a convenience. A count budget at $q = 0$ **entails** the
rate budget of the same numerator at every $q$: $S \\le 0$ forces the rate to
zero, so no response satisfies the count and fails the rate, and the
non-entailment obligation would be unsatisfiable rather than merely unmet.
§13.4's numerator-diversity rule is what makes the pair unrealisable, and this
module refuses such a pair rather than constructing a witness for it, so the
two rules are checked against each other rather than assumed compatible.

**The constructor envelope.** Every constructor asserts the form it was
written for and refuses outside it. This is registered because a v4r2-era
constructor used outside its envelope was found to report a construction
failure as an entailment claim -- the worst possible failure for this check,
because it turns a bug into a scientific finding.
"""
from __future__ import annotations

from typing import Any, Iterable

from dci1v4.errors import InstrumentError
from dci1v4.verifiers.target import s0_count

from dci1v4r3.verifiers.compliance import passes
from dci1v4r3.verifiers.constraints import (
    FAMILIES, FORM_COUNT, FORM_RATE, LOWER_BOUND_FORMS, Constraint,
    TARGET_GRID, declared_range, focal_severities,
)
from dci1v4r3.verifiers.statistics import STATISTICS, focal_statistic

__all__ = ["FILLER", "TARGET", "LONG_WORD", "FEATURE_WORD", "feature_free",
           "realisable_pairs", "assert_pair_realisable", "joint_witness",
           "separating_witnesses", "run_witness_suite"]

#: Words carrying **none** of the nine registered features: they do not begin
#: with b, do not end in ing or y, have more than one letter, contain no
#: doubled letter, no comma, no upper-case character and no letter a. Every
#: budget family reads zero on a text made of these, so a filler text is the
#: universal witness for the reference pool.
FILLER = ("point", "clue", "form", "step", "unit", "topic", "sound", "result")

#: The target word is itself feature-free, which is why $A$ composes with every
#: budget family without a construction: seven letters, no a, no doubling, no
#: b at the front, no ing or y at the end, no capital.
TARGET = "however"

#: Longer than the loosest admissible m (12) and still feature-free, so it can
#: break $B$ without moving any family statistic.
LONG_WORD = "counterproductive"

#: One word per numerator that carries that feature and, where possible, no
#: other. Used to push a statistic above a budget or up to a lower bound.
FEATURE_WORD = {
    "b_initial": "bold",          # b-initial; contains no a, no doubling
    "ing_final": "helping",       # ing-final
    "one_letter": "o",            # one letter
    "doubled_letter": "cell",     # doubled l
    "comma": ",",                 # a raw comma character
    "capital_char": "Point",      # one upper-case character
    "capital_word": "Point",      # a word containing an upper-case character
    "letter_a": "area",           # contains a
    "y_final": "duty",            # y-final
}


def feature_free(n_words: int) -> str:
    """A response of ``n_words`` filler words and nothing else."""
    if n_words <= 0:
        return ""
    return " ".join(FILLER[i % len(FILLER)] for i in range(n_words))


def _statistic(kind: str, text: str) -> int:
    if kind == "A":
        return s0_count(text)
    if kind == "B":
        return focal_statistic(text)
    return STATISTICS[FAMILIES[kind].statistic_id](text)


def _group(kind: str) -> str | None:
    return None if kind in ("A", "B") else FAMILIES[kind].feature_group


def assert_pair_realisable(first: Constraint, second: Constraint) -> None:
    """§8.1 plus §13.4: refuse a pair no cell of this design can contain."""
    kinds = {first.kind, second.kind}
    if first.kind == second.kind:
        raise InstrumentError("a cell never states one constraint twice")
    roles = {k: ("outcome" if k in ("A", "B") else FAMILIES[k].role)
             for k in kinds}
    values = sorted(roles.values())
    if values == ["class_control", "class_control"]:
        raise InstrumentError(
            "§13.7 admits exactly one class companion, so two class families "
            "never co-occur")
    if "class_control" in values and "reference" in values:
        raise InstrumentError(
            "§13.7 places the class companion beside B alone; it never shares "
            "a cell with a reference")
    if values == ["reference", "reference"]:
        if _group(first.kind) == _group(second.kind):
            raise InstrumentError(
                f"{first.kind} and {second.kind} measure the same feature "
                f"({_group(first.kind)}), and §13.4 admits three core "
                "references from three different feature groups, so they "
                "never co-occur. The obligation is not merely unmet for this "
                "pair -- it is unsatisfiable: a count budget at q=0 forces "
                "its rate sibling's rate to zero, and zero upper-case "
                "characters forces zero words carrying one")


def realisable_pairs() -> list[tuple[Constraint, Constraint]]:
    """Every pair §7.5 must discharge, in a fixed order."""
    outcomes = ([Constraint("A", n) for n in TARGET_GRID]
                + [Constraint("B", m, extended=True)
                   for m in focal_severities(extended=True)])
    references = [Constraint(k, q, reserve=True) for k in FAMILIES
                  if FAMILIES[k].role == "reference"
                  for q in declared_range(k)]
    classes = [Constraint(k, q, reserve=True) for k in FAMILIES
               if FAMILIES[k].role == "class_control"
               for q in declared_range(k)]
    pairs: list[tuple[Constraint, Constraint]] = []
    for i, a in enumerate(outcomes):
        for b in outcomes[i + 1:]:
            if a.kind != b.kind:
                pairs.append((a, b))
    for outcome in outcomes:
        for other in references + classes:
            pairs.append((outcome, other))
    for i, a in enumerate(references):
        for b in references[i + 1:]:
            if a.kind != b.kind and _group(a.kind) != _group(b.kind):
                pairs.append((a, b))
    return pairs


# ------------------------------------------------------------ constructors
def _satisfy_one(constraint: Constraint, *, base_words: int = 40) -> str:
    """A text satisfying ``constraint`` alone, by its declared form."""
    kind, q = constraint.kind, constraint.severity
    if kind == "A":
        return " ".join([TARGET] * q + [feature_free(base_words)])
    if kind == "B":
        return feature_free(base_words)          # every filler is <= 6 letters
    family = FAMILIES[kind]
    if family.form in (FORM_COUNT, FORM_RATE):
        return feature_free(base_words)          # every numerator reads zero
    if family.form not in LOWER_BOUND_FORMS:     # pragma: no cover
        raise InstrumentError(f"{kind}: unknown form {family.form!r}")
    word = FEATURE_WORD[family.statistic_id]
    if family.form == "count_lower_bound":
        return " ".join([word] * (q + 2))
    # A rate lower bound is scale-free: an all-feature text reads 100 percent.
    return " ".join([word] * max(q, 8))


def joint_witness(first: Constraint, second: Constraint) -> str:
    """One response satisfying both constraints of a realisable pair."""
    assert_pair_realisable(first, second)
    lower = [c for c in (first, second)
             if c.kind not in ("A", "B")
             and FAMILIES[c.kind].form in LOWER_BOUND_FORMS]
    target = next((c for c in (first, second) if c.kind == "A"), None)
    if lower:
        constraint = lower[0]
        family = FAMILIES[constraint.kind]
        word = FEATURE_WORD[family.statistic_id]
        n = target.severity if target else 0
        if family.form == "count_lower_bound":
            count = constraint.severity + 2
        else:
            # rate >= q with n target words present: k / (k + n) >= q/100.
            count = max(constraint.severity, 8)
            if n:
                count = max(count, int(4 * n) + count)
        words = [word] * count + [TARGET] * n
        return " ".join(words)
    n = target.severity if target else 0
    return " ".join([TARGET] * n + [feature_free(40)])


def _break(constraint: Constraint, *, alongside: Constraint) -> str:
    """A text that FAILS ``constraint`` while leaving ``alongside`` free.

    ``alongside`` is passed so the constructor can pick a breaking word that
    does not move the other constraint's statistic; where no such word exists
    the pair is not realisable and ``assert_pair_realisable`` has already said
    so.
    """
    kind, q = constraint.kind, constraint.severity
    if kind == "A":
        return feature_free(40)                  # zero occurrences, and n >= 1
    if kind == "B":
        return " ".join([LONG_WORD, feature_free(30)])
    family = FAMILIES[kind]
    word = FEATURE_WORD[family.statistic_id]
    if family.form == FORM_COUNT:
        return " ".join([word] * (q + 1) + [feature_free(30)])
    if family.form == FORM_RATE:
        # rate > q needs the feature share above q percent. For a word-shaped
        # numerator an all-feature text reads 100 and every registered q is
        # below it. The comma numerator is NOT word-shaped -- its feature is a
        # character, and a text of bare commas has no words at all, so its
        # rate is undefined and the constraint fails for the wrong reason.
        # Commas are therefore attached to filler words, which raises commas
        # per hundred words far above every registered q while leaving the
        # text a text.
        if family.statistic_id == "comma":
            return " ".join(f"{w}{',' * 5}" for w in FILLER[:4])
        return " ".join([word] * 12)
    # A lower bound is broken by producing none of the feature at all.
    return feature_free(40) if family.form == "count_lower_bound" \
        else feature_free(40)


def separating_witnesses(first: Constraint, second: Constraint
                         ) -> tuple[str, str]:
    """(satisfies first and fails second, satisfies second and fails first)."""
    assert_pair_realisable(first, second)

    def _one(keep: Constraint, drop: Constraint) -> str:
        base = _break(drop, alongside=keep)
        if keep.kind == "A":
            return " ".join([TARGET] * keep.severity + [base])
        family = FAMILIES.get(keep.kind)
        if family is not None and family.form in LOWER_BOUND_FORMS:
            word = FEATURE_WORD[family.statistic_id]
            count = (keep.severity + 2 if family.form == "count_lower_bound"
                     else max(keep.severity, 8) * 4)
            return " ".join([word] * count + [base])
        return base

    return _one(first, second), _one(second, first)


def run_witness_suite(pairs: Iterable[tuple[Constraint, Constraint]] | None
                      = None) -> dict[str, Any]:
    """Discharge §7.5 over every realisable pair, and report the failures."""
    pairs = list(pairs) if pairs is not None else realisable_pairs()
    joint_failures: list[str] = []
    entail_failures: list[str] = []
    for first, second in pairs:
        label = f"{first.label}+{second.label}"
        text = joint_witness(first, second)
        if not (passes(first, _statistic(first.kind, text), text)
                and passes(second, _statistic(second.kind, text), text)):
            joint_failures.append(label)
        one, two = separating_witnesses(first, second)
        ok_one = (passes(first, _statistic(first.kind, one), one)
                  and not passes(second, _statistic(second.kind, one), one))
        ok_two = (passes(second, _statistic(second.kind, two), two)
                  and not passes(first, _statistic(first.kind, two), two))
        if not (ok_one and ok_two):
            entail_failures.append(label)
    return {"pairs": len(pairs),
            "joint_satisfiability_failures": joint_failures,
            "non_entailment_failures": entail_failures,
            "passed": not (joint_failures or entail_failures)}
