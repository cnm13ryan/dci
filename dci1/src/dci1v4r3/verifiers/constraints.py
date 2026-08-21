"""Registered constraints, grids, ladders, forms and classes (v4r3 §7).

Four things distinguish this module from ``dci1v4.verifiers.constraints``,
and each is a registered scientific change with an entry in the v4r2 -> v4r3
changelog:

1. **The focal grid escalates rather than widening** (§7.2). ``FOCAL_GRID``
   is the registered ``(7, 8, 9, 10)``; ``FOCAL_EXTENSION`` is ``(11, 12)``
   and is admissible only through ``focal_severities(extended=True)``, which
   §12.3 calls only when no registered severity is eligible. A flat six-rung
   grid would move ``m*`` on a model whose registered grid already works,
   because §12.3 selects the rung nearest 0.80 and a new rung can be nearer.

2. **The pool carries four predicate forms over eight counted statistics**
   (§7.3, §7.4). Count budgets ``S <= q`` are the v4r2 pool unchanged. Rate
   budgets ``100*S/W <= q`` exist because every count budget is prefix-closed
   and a prefix-closed constraint is satisfied for free by a short answer.
   Lower bounds ``S >= q`` and rate lower bounds ``100*S/W >= q`` are the two
   production forms, and §7.4 admits them to the class arm alone.

3. **The candidate library is a generative grammar, not a list** (§7.0).
   Every family is a (statistic, form) pair drawn from eight registered
   numerators and four registered forms, and every family carries **two**
   ladders: the ``ladder`` §12.2 measures at round 0, and the ``reserve``
   from which §12.6's expansion may draw when the identification-coverage
   criterion is short. Expansion picks the next rungs of a frozen enumeration;
   it never authors a constraint after seeing data. Wordings are
   severity-invariant, so a reserve rung needs no new wording and no new
   verifier -- only a boundary-suite case, and §10.2 freezes those over the
   whole declared range before qualification.

4. **Every family carries a declared class**, asserted against its predicate
   form, and the reference and spectrum slots refuse ``production``. A is a
   production constraint and the reference pool is budget throughout, which
   is the study's sharpest limitation (§29) and is stated rather than
   discovered.
"""
from __future__ import annotations

from dataclasses import dataclass

from dci1v4.errors import InstrumentError
from dci1v4.verifiers.target import TARGET_WORD

__all__ = ["TARGET_WORD", "TARGET_GRID", "FOCAL_GRID", "FOCAL_EXTENSION",
           "focal_severities", "FORM_COUNT", "FORM_RATE", "FORM_LOWER_BOUND",
           "FORM_RATE_LOWER_BOUND", "FORMS", "RATE_FORMS", "LOWER_BOUND_FORMS",
           "CLASS_BUDGET", "CLASS_PRODUCTION", "STATISTIC_IDS", "Family",
           "FAMILIES", "REFERENCE_FAMILY_IDS", "CLASS_FAMILY_IDS",
           "FAMILY_IDS", "REFERENCE_LADDERS", "CLASS_LADDERS", "LADDERS",
           "RESERVES", "declared_range", "N_REFERENCE_SEVERITIES",
           "N_CLASS_SEVERITIES", "N_SEVERITIES", "N_DECLARED_SEVERITIES",
           "KINDS", "Constraint", "registered_severities", "family_class",
           "family_form", "feature_group", "FEATURE_GROUPS",
           "FEATURE_GROUP_IDS", "assert_reference_slot_allowed",
           "assert_ladder_within_reserve", "assert_no_redundant_rate_rung"]

# ------------------------------------------------------------- §7.1 outcomes
TARGET_GRID = tuple(range(1, 9))            # A: n, unchanged from v4r2
FOCAL_GRID = (7, 8, 9, 10)                  # B: m, the registered grid
FOCAL_EXTENSION = (11, 12)                  # §7.2, measured only on escalation


def focal_severities(*, extended: bool = False) -> tuple[int, ...]:
    """B's admissible severities. ``extended`` is §12.3's escalation.

    The extension is *measured* in the §12.2 dense screen on every model,
    because that screen is one draw on 24 topics and §12.3's rule has to know
    whether the rungs exist before it can decide not to use them. Measuring
    them never makes them selectable: only this flag does, and only §12.3
    sets it, and only when the registered grid supplies no eligible severity.
    """
    return FOCAL_GRID + FOCAL_EXTENSION if extended else FOCAL_GRID


# ------------------------------------------------------- §7.0 the grammar
FORM_COUNT = "count_budget"                  # S <= q
FORM_RATE = "rate_budget"                    # 100 * S / W <= q
FORM_LOWER_BOUND = "count_lower_bound"       # S >= q
FORM_RATE_LOWER_BOUND = "rate_lower_bound"   # 100 * S / W >= q

FORMS = (FORM_COUNT, FORM_RATE, FORM_LOWER_BOUND, FORM_RATE_LOWER_BOUND)
RATE_FORMS = (FORM_RATE, FORM_RATE_LOWER_BOUND)
LOWER_BOUND_FORMS = (FORM_LOWER_BOUND, FORM_RATE_LOWER_BOUND)

CLASS_BUDGET = "budget"              # satisfied by doing less
CLASS_PRODUCTION = "production"      # satisfied by doing more of something

#: Predicate form -> constraint class. §7.5 asserts every family against it,
#: so a family cannot declare a class its own predicate contradicts.
#:
#: A rate lower bound is classed ``production`` because its registered
#: satisfaction route is to produce more of the counted feature. It also
#: admits a budget-like route -- deleting non-conforming words raises the
#: rate -- and §7.4 records that plainly rather than hiding it, because the
#: class arm exists to bound a class effect and an honest bound needs an
#: honest label.
_FORM_CLASS = {FORM_COUNT: CLASS_BUDGET,
               FORM_RATE: CLASS_BUDGET,
               FORM_LOWER_BOUND: CLASS_PRODUCTION,
               FORM_RATE_LOWER_BOUND: CLASS_PRODUCTION}

#: §7.0's nine registered counted statistics. A family is one of these under
#: one of the four forms; nothing else is a candidate family.
STATISTIC_IDS = ("b_initial", "ing_final", "one_letter", "doubled_letter",
                 "comma", "capital_char", "capital_word", "letter_a",
                 "y_final")

#: §7.0's **feature groups**: which statistics measure the same property of an
#: answer. Two families in the same group never co-occur in a cell and never
#: both enter the core reference set (§13.4).
#:
#: The grouping is not cosmetic. Two families of one group are related by
#: entailment at the edge of their ladders, so §7.5's non-entailment obligation
#: is *unsatisfiable* for such a pair rather than merely unmet: a count budget
#: at q = 0 forces its rate sibling's rate to zero, and ``capital_char = 0``
#: forces ``capital_word = 0``. It is also what structural diversity means for
#: the §11.7 fit -- three families from one group would give three intercepts
#: over one measurement and no cross-family variation at all.
FEATURE_GROUPS: dict[str, str] = {
    "b_initial": "b_initial", "ing_final": "ing_final",
    "one_letter": "one_letter", "doubled_letter": "doubled_letter",
    "comma": "comma", "capital_char": "capital", "capital_word": "capital",
    "letter_a": "letter_a", "y_final": "y_final",
}
assert set(FEATURE_GROUPS) == set(STATISTIC_IDS)
FEATURE_GROUP_IDS = tuple(sorted(set(FEATURE_GROUPS.values())))


@dataclass(frozen=True)
class Family:
    """One registered constraint family: a counted statistic under a form."""

    kind: str
    statistic_id: str
    form: str
    #: The rungs §12.2 measures at round 0.
    ladder: tuple[int, ...]
    #: §12.6's frozen expansion reserve. A superset of ``ladder``; expansion
    #: may admit rungs from it and from nowhere else.
    reserve: tuple[int, ...]
    #: ``reference`` families may fill a core reference or spectrum slot;
    #: ``class_control`` families may fill only the §13.7 class slot.
    role: str
    #: v4r2 §7.2's rule statement, or this document's, in full prose. The
    #: definition of what the family means; not a wording.
    rule: str
    #: The registered family whose counting statistic this one reuses, or
    #: ``"new"``. ``capital_word`` is the one new numerator in the pool and
    #: is flagged here rather than in prose, because §10.2's carry-over
    #: evidence turns on it.
    statistic_source: str

    def __post_init__(self):
        if self.form not in _FORM_CLASS:
            raise InstrumentError(f"unknown predicate form {self.form!r}")
        if self.statistic_id not in STATISTIC_IDS:
            raise InstrumentError(f"{self.kind}: {self.statistic_id!r} is not "
                                  "a registered counted statistic (§7.0)")
        if self.role not in ("reference", "class_control"):
            raise InstrumentError(f"unknown family role {self.role!r}")
        for name, rungs in (("ladder", self.ladder), ("reserve", self.reserve)):
            if not rungs or sorted(set(rungs)) != sorted(rungs):
                raise InstrumentError(f"{self.kind}: {name} must be strictly "
                                      "increasing with no repeats")
        if not set(self.ladder) <= set(self.reserve):
            raise InstrumentError(
                f"{self.kind}: §12.6 requires the round-0 ladder to be a "
                "subset of the frozen reserve, so that expansion is a "
                "restriction of an enumeration rather than new authoring")
        if self.form in RATE_FORMS and self.form == FORM_RATE \
                and min(self.reserve) < 1:
            raise InstrumentError(
                f"{self.kind}: a rate budget at q=0 is satisfied exactly when "
                "the count budget at q=0 is, so it would enter the pool as a "
                "second family with a first family's meaning (§7.3)")

    @property
    def constraint_class(self) -> str:
        return _FORM_CLASS[self.form]

    @property
    def feature_group(self) -> str:
        return FEATURE_GROUPS[self.statistic_id]

    @property
    def is_rate(self) -> bool:
        return self.form in RATE_FORMS


def _seq(lo: int, hi: int, step: int = 1) -> tuple[int, ...]:
    return tuple(range(lo, hi + 1, step))


#: The registered round-0 ladder shared by the five rate families whose
#: counted feature has a low natural rate.
_LOW_RATE_LADDER = (1, 2, 3, 4, 5, 6, 8, 10)
_LOW_RATE_RESERVE = _seq(1, 14)

FAMILIES: dict[str, Family] = {
    # ---- count budgets: the v4r2 pool, ladders complete, unchanged
    "RF1": Family("RF1", "b_initial", FORM_COUNT, _seq(0, 8), _seq(0, 8),
                  "reference",
                  "At most q words in the answer may begin with the letter b.",
                  "RF1"),
    "RF2": Family("RF2", "ing_final", FORM_COUNT, _seq(0, 8), _seq(0, 8),
                  "reference",
                  "At most q words in the answer may end with the letters ing.",
                  "RF2"),
    "RF3": Family("RF3", "one_letter", FORM_COUNT, _seq(0, 8), _seq(0, 8),
                  "reference",
                  "At most q words in the answer may have one letter.",
                  "RF3"),
    "RF4": Family("RF4", "doubled_letter", FORM_COUNT, _seq(0, 6), _seq(0, 6),
                  "reference",
                  "At most q words may contain two identical adjacent letters.",
                  "RF4"),
    "RF5": Family("RF5", "comma", FORM_COUNT, _seq(0, 12), _seq(0, 12),
                  "reference",
                  "The answer may contain at most q comma characters.",
                  "RF5"),
    "RF6": Family("RF6", "capital_char", FORM_COUNT, _seq(0, 12), _seq(0, 12),
                  "reference",
                  "The answer may contain at most q upper-case English "
                  "letters.",
                  "RF6"),
    "RF7": Family("RF7", "letter_a", FORM_COUNT, _seq(0, 24), _seq(0, 24),
                  "reference",
                  "At most q words in the answer may contain the letter a.",
                  "RF7"),
    "RF8": Family("RF8", "y_final", FORM_COUNT, _seq(0, 8), _seq(0, 8),
                  "reference",
                  "At most q words in the answer may end with the letter y.",
                  "RF8"),
    # ---- rate budgets: one per registered numerator (§7.3)
    "CR1": Family("CR1", "b_initial", FORM_RATE, _LOW_RATE_LADDER,
                  _LOW_RATE_RESERVE, "reference",
                  "At most q percent of words may begin with the letter b.",
                  "RF1"),
    "CR2": Family("CR2", "ing_final", FORM_RATE, _LOW_RATE_LADDER,
                  _LOW_RATE_RESERVE, "reference",
                  "At most q percent of words may end with the letters ing.",
                  "RF2"),
    "CR3": Family("CR3", "one_letter", FORM_RATE, _LOW_RATE_LADDER,
                  _LOW_RATE_RESERVE, "reference",
                  "At most q percent of words may have one letter.",
                  "RF3"),
    "CR4": Family("CR4", "doubled_letter", FORM_RATE,
                  (3, 5, 7, 9, 11, 13, 15, 18), _seq(2, 20), "reference",
                  "At most q percent of words may contain two identical "
                  "adjacent letters.",
                  "RF4"),
    "CR5": Family("CR5", "comma", FORM_RATE, _LOW_RATE_LADDER,
                  _LOW_RATE_RESERVE, "reference",
                  "The answer may contain at most q comma characters per "
                  "hundred words.",
                  "RF5"),
    "CR6": Family("CR6", "capital_word", FORM_RATE,
                  (3, 4, 5, 6, 7, 8, 10, 12), _seq(1, 16), "reference",
                  "At most q percent of words may use a capital letter.",
                  "new"),
    "CR7": Family("CR7", "letter_a", FORM_RATE,
                  (24, 28, 32, 36, 40, 44, 48, 52), _seq(20, 56, 2),
                  "reference",
                  "At most q percent of words may contain the letter a.",
                  "RF7"),
    "CR8": Family("CR8", "y_final", FORM_RATE, _LOW_RATE_LADDER,
                  _LOW_RATE_RESERVE, "reference",
                  "At most q percent of words may end with the letter y.",
                  "RF8"),
    # ---- lower bounds: production class, class arm only (§7.4, §13.7)
    "CL7": Family("CL7", "letter_a", FORM_LOWER_BOUND,
                  (10, 20, 30, 45, 60, 80, 100, 130), _seq(5, 140, 5),
                  "class_control",
                  "At least q words in the answer must contain the letter a.",
                  "RF7"),
    "CL8": Family("CL8", "y_final", FORM_LOWER_BOUND,
                  (2, 3, 5, 7, 10, 14, 19, 25), _seq(1, 28), "class_control",
                  "At least q words in the answer must end with the letter y.",
                  "RF8"),
    "CP4": Family("CP4", "doubled_letter", FORM_RATE_LOWER_BOUND,
                  (5, 8, 10, 12, 15, 18, 22, 28), _seq(2, 32), "class_control",
                  "At least q percent of words must contain two identical "
                  "adjacent letters.",
                  "RF4"),
    "CP7": Family("CP7", "letter_a", FORM_RATE_LOWER_BOUND,
                  (30, 34, 38, 42, 46, 50, 56, 64), _seq(20, 76, 2),
                  "class_control",
                  "At least q percent of words must contain the letter a.",
                  "RF7"),
}

REFERENCE_FAMILY_IDS = tuple(k for k, f in FAMILIES.items()
                             if f.role == "reference")
CLASS_FAMILY_IDS = tuple(k for k, f in FAMILIES.items()
                         if f.role == "class_control")
FAMILY_IDS = tuple(FAMILIES)

REFERENCE_LADDERS = {k: FAMILIES[k].ladder for k in REFERENCE_FAMILY_IDS}
CLASS_LADDERS = {k: FAMILIES[k].ladder for k in CLASS_FAMILY_IDS}
LADDERS = {k: f.ladder for k, f in FAMILIES.items()}
RESERVES = {k: f.reserve for k, f in FAMILIES.items()}

N_REFERENCE_SEVERITIES = sum(len(g) for g in REFERENCE_LADDERS.values())   # 158
N_CLASS_SEVERITIES = sum(len(g) for g in CLASS_LADDERS.values())           # 32
N_SEVERITIES = N_REFERENCE_SEVERITIES + N_CLASS_SEVERITIES                 # 190
N_DECLARED_SEVERITIES = sum(len(g) for g in RESERVES.values())             # 334

KINDS = ("A", "B") + FAMILY_IDS


def declared_range(kind: str) -> tuple[int, ...]:
    """Every severity of ``kind`` that can ever enter the study (§10.2).

    Gate 1's instrument population is this, not the round-0 ladder: §12.6's
    expansion may admit any reserve rung, so the boundary suites and the
    reimplementation evidence are frozen over the whole declared range before
    qualification. A rung that could enter without evidence is the failure
    this function exists to make impossible.
    """
    if kind == "A":
        return TARGET_GRID
    if kind == "B":
        return focal_severities(extended=True)
    if kind in RESERVES:
        return RESERVES[kind]
    raise InstrumentError(f"unknown constraint kind {kind!r}")


def family_class(kind: str) -> str:
    if kind == "A":
        return CLASS_PRODUCTION          # S == n: a production constraint
    if kind == "B":
        return CLASS_BUDGET              # max word length <= m
    if kind in FAMILIES:
        return FAMILIES[kind].constraint_class
    raise InstrumentError(f"unknown constraint kind {kind!r}")


def family_form(kind: str) -> str:
    if kind in FAMILIES:
        return FAMILIES[kind].form
    raise InstrumentError(f"{kind!r} is not a family")


def feature_group(kind: str) -> str:
    """§7.0: which property of an answer this family measures."""
    if kind in FAMILIES:
        return FAMILIES[kind].feature_group
    raise InstrumentError(f"{kind!r} is not a family")


def registered_severities(kind: str, *, extended: bool = False,
                          reserve: bool = False) -> tuple[int, ...]:
    """The round-0 ladder, or the declared range when ``reserve``."""
    if kind == "A":
        return TARGET_GRID
    if kind == "B":
        return focal_severities(extended=extended)
    if kind in LADDERS:
        return RESERVES[kind] if reserve else LADDERS[kind]
    raise InstrumentError(f"unknown constraint kind {kind!r}")


def assert_reference_slot_allowed(kind: str) -> None:
    """§7.5, §13.6, §13.7: a production family may not be a reference.

    On the mandatory path rather than in prose. The v4r2 rule admitted the
    three references with the smallest solo distance from A whatever their
    form, and on two of four models the third slot could only be filled by a
    lower-bound family -- so the class confound arrived *inside* the
    reference set, where no arm was watching for it.
    """
    if kind in ("A", "B"):
        raise InstrumentError(f"{kind} is an outcome constraint, not a "
                              "reference")
    family = FAMILIES.get(kind)
    if family is None:
        raise InstrumentError(f"unknown family {kind!r}")
    if family.role != "reference":
        raise InstrumentError(
            f"{kind} is a {family.constraint_class}-class {family.role} "
            "family: §13.7 admits it to the class arm only, never to a core "
            "reference or spectrum slot")


def assert_ladder_within_reserve() -> None:
    """§12.6: every round-0 rung is a reserve rung, on every family."""
    for kind, family in FAMILIES.items():
        if not set(family.ladder) <= set(family.reserve):
            raise InstrumentError(f"{kind}: ladder escapes its reserve")


def assert_no_redundant_rate_rung() -> None:
    """§7.3: no rate rung means what a count rung of the same numerator means.

    ``100 * S / W <= 0`` holds exactly when ``S <= 0`` for any answer with a
    word, so a rate family carrying q=0 would duplicate its count sibling and
    inflate the cross-family overlap the §12.6 coverage criterion counts.
    """
    for kind, family in FAMILIES.items():
        if family.form is FORM_RATE and 0 in family.reserve:
            raise InstrumentError(
                f"{kind}: q=0 duplicates the count budget of the same "
                "numerator and would be counted as an independent family")


assert_ladder_within_reserve()
assert_no_redundant_rate_rung()


@dataclass(frozen=True)
class Constraint:
    """One registered constraint instance: a kind and a severity.

    ``extended`` admits B's §7.2 escalation rungs. It defaults to False, so
    ``Constraint("B", 11)`` raises unless the caller has been through §12.3's
    escalation -- the registered grid cannot be widened by accident.

    ``reserve`` admits a §12.6 expansion rung. It likewise defaults to False,
    so a reserve severity cannot reach a cell plan except through the
    expansion record that admitted it.
    """

    kind: str
    severity: int
    extended: bool = False
    reserve: bool = False

    def __post_init__(self):
        allowed = registered_severities(self.kind, extended=self.extended,
                                        reserve=self.reserve)
        if self.severity not in allowed:
            raise InstrumentError(
                f"severity {self.severity} outside the "
                f"{'declared range' if self.reserve else 'registered grid'} "
                f"of {self.kind}: {allowed}")

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.severity}"

    @property
    def constraint_class(self) -> str:
        return family_class(self.kind)

    @property
    def form(self) -> str:
        if self.kind == "A":
            return "exact_count"
        if self.kind == "B":
            return "max_word_length"
        return family_form(self.kind)
