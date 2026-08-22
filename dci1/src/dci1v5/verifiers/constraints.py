"""The v5 candidate library: grammar, tiers, ladders and metadata (§7).

Three things distinguish this module from v4r4's, and each is a registered
scientific change with an entry in the v4r4 -> v5 changelog.

1. **The core reference pool is same-form with A** (§7.5). v4r3 §13.1 says a
   reference occupies A's slot and therefore has to resemble A; v4r3 §7.3 then
   forbade production families from that pool. Applied to v4r4's own
   measurements, v5's validity gates leave **3, 0, 0 and 0** qualifying
   families in the budget-class pool on the four replications and **4, 4, 2
   and 3** in the production-class pool v4r3 excluded. v5 resolves the
   contradiction in favour of §13.1: eight Tier-1 marker families, exact
   counts of a short word, differing from A only in which word and how many.

2. **Every family carries thirteen declared structural-metadata fields and a
   tier** (§7.3, §7.4), asserted against its own predicate at import.
   ``protocol/taxonomy.py`` holds the vocabulary and the rule; nothing here
   restates either.

3. **The focal grid runs 7 to 14 with an extension to 15 and 16** (§7.1,
   §7.2). v4r4 registered {7,8,9,10} extending to {11,12} and selected the
   **last measured rung on all four replications**; §12.3 additionally
   requires the operating point to be bracketed.

**The library is a grammar, not a list.** A candidate family is a counted
statistic under a predicate form and nothing else is one. ``rate_lower_bound``
stays in the grammar and in the verifier and **no v5 family instantiates it**,
for the reason v4r4 removed CP4 and CP7: two of each such family's four
model-facing wordings stated the severity as a target and named no bound,
which fails §10.7 A'.

**Sizes, asserted rather than described.** 37 families; 326 round-0
severities; 632 severities in the declared range; with A's eight and B's ten,
650 constraint instances in 39 verifiers. v4r4's constants carried comments
that disagreed with its computed values --- ``N_SEVERITIES`` documented 190
against a computed 254, ``N_DECLARED_SEVERITIES`` 334 against 510. The
computed values are what that code used and what its records carry, so nothing
scientific moved; the comments were wrong. Here the numbers are assertions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dci1v4.errors import InstrumentError

from dci1v5.protocol.taxonomy import (
    SLOT_BROAD_CLASS, SLOT_CORE, SLOT_NEAR_FORM, SLOT_SPECTRUM, TIER_1, TIER_2,
    TIER_3, assert_metadata_consistent, assert_tier_admits_slot,
    tier_of_metadata,
)

__all__ = [
    "TARGET_GRID", "TARGET_WORD", "FOCAL_GRID", "FOCAL_EXTENSION",
    "focal_severities", "FORM_COUNT", "FORM_RATE", "FORM_LOWER_BOUND",
    "FORM_RATE_LOWER_BOUND", "FORM_EXACT", "FORMS", "RATE_FORMS",
    "LOWER_BOUND_FORMS", "FORM_OPERATOR", "CLASS_BUDGET", "CLASS_PRODUCTION",
    "STATISTIC_IDS", "MARKER_STATISTIC_IDS", "NEW_STATISTIC_IDS",
    "MARKER_WORDS",
    "RESERVE_MARKER_WORDS", "REJECTED_MARKERS", "MARKER_MAX_LETTERS",
    "MARKER_NATURAL_FREQUENCY_MAX", "FEATURE_GROUPS", "FEATURE_GROUP_IDS",
    "Family", "FAMILIES", "FAMILY_IDS", "TIER1_FAMILY_IDS",
    "TIER2_FAMILY_IDS", "TIER3_FAMILY_IDS", "LADDERS", "RESERVES",
    "declared_range", "registered_severities", "family_class", "family_form",
    "family_tier", "feature_group", "discourse_role", "structural_metadata",
    "N_FAMILIES", "N_SEVERITIES", "N_DECLARED_SEVERITIES", "N_INSTRUMENTS",
    "N_VERIFIERS", "KINDS", "Constraint", "CARRIED_FROM_V4R4",
    "assert_slot_allowed", "assert_ladder_within_reserve",
    "assert_no_zero_rung", "assert_marker_vocabulary", "assert_library_sizes",
]

# ------------------------------------------------------------- §7.1 outcomes
#: A: use the word `however` exactly n times.
TARGET_WORD = "however"
TARGET_GRID = tuple(range(1, 9))              # n in 1..8

#: B: every word at most m letters. §7.1's registered grid, and §7.2's
#: conditional extension. `however` has seven letters, so m >= 7 is required
#: for A+B to be jointly satisfiable at all.
FOCAL_GRID = (7, 8, 9, 10, 11, 12, 13, 14)
FOCAL_EXTENSION = (15, 16)


def focal_severities(*, extended: bool = False) -> tuple[int, ...]:
    """B's admissible severities. ``extended`` is §12.3's escalation.

    The extension is measured in the §12.2 dense screen on every model,
    because §12.3's bracketing rule has to know whether the rungs exist before
    it can decide not to use them. Measuring them never makes them selectable:
    only this flag does, and only §12.3 sets it.
    """
    return FOCAL_GRID + FOCAL_EXTENSION if extended else FOCAL_GRID


# ------------------------------------------------------- §7.3 the grammar
FORM_COUNT = "count_budget"                   # S <= q
FORM_RATE = "rate_budget"                     # 100 * S / W <= q
FORM_LOWER_BOUND = "count_lower_bound"        # S >= q
FORM_RATE_LOWER_BOUND = "rate_lower_bound"    # 100 * S / W >= q, unused
FORM_EXACT = "exact_count"                    # S == q

FORMS = (FORM_EXACT, FORM_COUNT, FORM_RATE, FORM_LOWER_BOUND,
         FORM_RATE_LOWER_BOUND)
RATE_FORMS = (FORM_RATE, FORM_RATE_LOWER_BOUND)
LOWER_BOUND_FORMS = (FORM_LOWER_BOUND, FORM_RATE_LOWER_BOUND)

CLASS_BUDGET = "budget"
CLASS_PRODUCTION = "production"

#: §7.3: the class is asserted against the operator, so a family cannot
#: declare a class its own predicate contradicts.
_FORM_CLASS = {FORM_COUNT: CLASS_BUDGET, FORM_RATE: CLASS_BUDGET,
               FORM_LOWER_BOUND: CLASS_PRODUCTION,
               FORM_RATE_LOWER_BOUND: CLASS_PRODUCTION,
               FORM_EXACT: CLASS_PRODUCTION}

FORM_OPERATOR = {FORM_COUNT: "<=", FORM_RATE: "<=", FORM_LOWER_BOUND: ">=",
                 FORM_RATE_LOWER_BOUND: ">=", FORM_EXACT: "=="}

# ---------------------------------------------------- §7.6 counted statistics
#: The eight registered marker words of §7.10, chosen on three rules: not A's
#: own word; at most seven letters, so the marker is jointly satisfiable with
#: B at every admissible severity; and a natural occurrence rate at or near
#: A's own. `however` itself appears in 1.3% to 10.4% of unconstrained v4r4
#: development responses, so the ceiling is benchmarked against A rather than
#: against zero.
MARKER_WORDS: dict[str, str] = {
    "marker_thus": "thus", "marker_hence": "hence", "marker_though": "though",
    "marker_whereas": "whereas", "marker_indeed": "indeed",
    "marker_namely": "namely", "marker_instead": "instead",
    "marker_overall": "overall",
}

#: §7.10's three reserve markers. Admissible **only by a registered
#: amendment** and only when a registered marker fails Gate 1. They are not
#: families here: a family for one of them is what the amendment would add.
RESERVE_MARKER_WORDS: dict[str, dict[str, Any]] = {
    "notably": {"letters": 7, "discourse_role": "emphatic",
                "development_frequency_max": 0.000},
    "albeit": {"letters": 6, "discourse_role": "contrastive",
               "development_frequency_max": 0.013},
    "besides": {"letters": 7, "discourse_role": "additive",
                "development_frequency_max": 0.000},
}

#: §7.6's structural rule and its measured rule, with the reason each word
#: fails. Recorded because §7.10 says the rejections are stated rather than
#: left implicit, and because an earlier draft of the preregistration rejected
#: five of these on an assertion the measurement contradicted.
REJECTED_MARKERS: dict[str, str] = {
    "however": "A's own marker; a companion counting A's word would be A "
               "under another name",
    "moreover": "8 letters, above the 7-letter structural ceiling",
    "likewise": "8 letters", "therefore": "9 letters",
    "meanwhile": "9 letters", "otherwise": "9 letters",
    "conversely": "10 letters", "nonetheless": "11 letters",
    "also": "P(>=1 | unconstrained) = 0.419, above the 0.15 ceiling",
    "finally": "P(>=1 | unconstrained) = 0.185, above the 0.15 ceiling",
    "yet": "admissible on both measured rules; not registered because the "
           "vocabulary is capped at eight and `yet` carries a common "
           "non-connective sense (`not yet`)",
    "still": "admissible; not registered, common non-connective sense "
             "(`still water`)",
    "then": "admissible; not registered, duplicates the consecutive role",
    "next": "admissible; not registered, duplicates the consecutive role",
    "rather": "admissible; not registered, duplicates the substitutive role",
    "further": "admissible; not registered, duplicates the additive role",
    "equally": "admissible; not registered, duplicates the additive role",
    "granted": "admissible; not registered, vocabulary capped at eight",
}

#: §7.6 rule 2. Structural, not measured: B's severities begin at m = 7
#: *because* `however` has seven letters, and a longer marker would not be
#: jointly satisfiable with B at every admissible severity.
MARKER_MAX_LETTERS = 7
#: §7.6 rule 3. About 1.5 times A's own measured maximum of 0.104.
MARKER_NATURAL_FREQUENCY_MAX = 0.15

MARKER_STATISTIC_IDS = tuple(MARKER_WORDS)

#: The numerators **new in v5**, which must earn their own §10.2 evidence.
#: Seven of the eight markers; `marker_thus` is v4r4's `CX1` numerator carried.
NEW_STATISTIC_IDS = tuple(s for s in MARKER_STATISTIC_IDS
                          if s != "marker_thus")

#: The fifteen statistics carried from v4r4, `marker_thus` among them: v4r4
#: already carried it as CX1's numerator, so §7.6's "twenty-two in all" is
#: eight markers plus fourteen non-marker numerators.
_CARRIED_STATISTIC_IDS = ("b_initial", "ing_final", "one_letter",
                          "doubled_letter", "comma", "capital_char",
                          "capital_word", "letter_a", "y_final", "t_initial",
                          "s_final", "vowel_initial", "sentence", "semicolon")

STATISTIC_IDS = MARKER_STATISTIC_IDS + _CARRIED_STATISTIC_IDS

#: Per statistic: its §7.3 ``statistic_type``, whether it is lexical or
#: structural, and its declared natural-frequency band.
#:
#: ``punctuation_character`` is the registered vocabulary's value for a
#: **raw-character numerator**; ``capital_char`` counts upper-case letters and
#: takes it, which is a property of the vocabulary's naming and not a claim
#: that a capital is punctuation. §7.3's five values are closed and this is
#: the honest placement.
_STATISTIC_META: dict[str, tuple[str, str, str]] = {
    **{s: ("marker_occurrence", "lexical", "low") for s in MARKER_WORDS},
    "b_initial": ("word_property", "lexical", "moderate"),
    "ing_final": ("word_property", "lexical", "low"),
    "one_letter": ("word_property", "lexical", "moderate"),
    "doubled_letter": ("word_property", "lexical", "moderate"),
    "comma": ("punctuation_character", "structural", "high"),
    "capital_char": ("punctuation_character", "structural", "high"),
    "capital_word": ("word_property", "lexical", "high"),
    "letter_a": ("word_property", "lexical", "high"),
    "y_final": ("word_property", "lexical", "moderate"),
    "t_initial": ("word_property", "lexical", "high"),
    "s_final": ("word_property", "lexical", "high"),
    "vowel_initial": ("word_property", "lexical", "high"),
    "sentence": ("sentence_unit", "structural", "high"),
    "semicolon": ("punctuation_character", "structural", "low"),
}
assert set(_STATISTIC_META) == set(STATISTIC_IDS)

#: §7.6's feature groups: which statistics measure the same property.
#: **Each marker is its own group.** The criterion is entailment, not
#: resemblance: two families of one group are related by entailment at the
#: edge of their ladders, so §7.7's non-entailment obligation is
#: *unsatisfiable* for such a pair rather than merely unmet. No answer's
#: `thus` count constrains its `hence` count at any severity.
FEATURE_GROUPS: dict[str, str] = {
    **{s: s.replace("marker_", "marker_") for s in MARKER_WORDS},
    "b_initial": "b_initial", "ing_final": "ing_final",
    "one_letter": "one_letter", "doubled_letter": "doubled_letter",
    "comma": "comma", "capital_char": "capital", "capital_word": "capital",
    "letter_a": "letter_a", "y_final": "y_final", "t_initial": "t_initial",
    "s_final": "s_final", "vowel_initial": "vowel_initial",
    "sentence": "sentence", "semicolon": "semicolon",
}
assert set(FEATURE_GROUPS) == set(STATISTIC_IDS)
FEATURE_GROUP_IDS = tuple(sorted(set(FEATURE_GROUPS.values())))


def _seq(lo: int, hi: int, step: int = 1) -> tuple[int, ...]:
    return tuple(range(lo, hi + 1, step))


@dataclass(frozen=True)
class Family:
    """One registered constraint family: a counted statistic under a form.

    ``metadata`` is §7.3's thirteen-field record and is validated against the
    family's own predicate in ``__post_init__``, so a family whose declared
    structure contradicts what its verifier evaluates cannot be constructed.
    """

    kind: str
    statistic_id: str
    form: str
    ladder: tuple[int, ...]
    reserve: tuple[int, ...]
    rule: str
    #: The registered family whose counting statistic this one reuses, or
    #: ``"new"``. §10.2's carry-over evidence turns on it.
    statistic_source: str
    #: §7.3's declared record. Built by ``_metadata`` below rather than typed
    #: out per family, so a field cannot be silently omitted from one entry.
    metadata: dict[str, Any]
    #: §27: the marker's measured occurrence rate on the **predecessor
    #: study's** unconstrained development responses. Historical design
    #: evidence, kept separate from every v5 measurement, and read by no rule.
    development_frequency_max: float | None = None

    def __post_init__(self):
        if self.form not in _FORM_CLASS:
            raise InstrumentError(f"unknown predicate form {self.form!r}")
        if self.statistic_id not in STATISTIC_IDS:
            raise InstrumentError(
                f"{self.kind}: {self.statistic_id!r} is not a registered "
                "counted statistic (§7.6)")
        for name, rungs in (("ladder", self.ladder),
                            ("reserve", self.reserve)):
            if not rungs or sorted(set(rungs)) != sorted(rungs):
                raise InstrumentError(f"{self.kind}: {name} must be strictly "
                                      "increasing with no repeats")
        if not set(self.ladder) <= set(self.reserve):
            raise InstrumentError(
                f"{self.kind}: §12.6 requires the round-0 ladder to be a "
                "subset of the frozen reserve, so that expansion is a "
                "restriction of an enumeration rather than new authoring")
        assert_metadata_consistent(self.kind, self.metadata,
                                   form_class=_FORM_CLASS[self.form],
                                   form_operator=FORM_OPERATOR[self.form])
        if self.metadata["feature_group"] != FEATURE_GROUPS[self.statistic_id]:
            raise InstrumentError(
                f"{self.kind}: declares feature group "
                f"{self.metadata['feature_group']!r} and §7.6 puts "
                f"{self.statistic_id!r} in "
                f"{FEATURE_GROUPS[self.statistic_id]!r}")
        if (self.statistic_id in MARKER_WORDS) != \
                (self.development_frequency_max is not None):
            raise InstrumentError(
                f"{self.kind}: §7.6's measured natural-occurrence rule "
                "applies to marker families and only to them")
        if self.development_frequency_max is not None:
            word = MARKER_WORDS[self.statistic_id]
            if len(word) > MARKER_MAX_LETTERS:
                raise InstrumentError(
                    f"{self.kind}: marker {word!r} has {len(word)} letters, "
                    f"above §7.6's structural ceiling of "
                    f"{MARKER_MAX_LETTERS}; it would not be jointly "
                    "satisfiable with B at every admissible severity")
            if word == TARGET_WORD:
                raise InstrumentError(
                    f"{self.kind}: {TARGET_WORD!r} is A's marker (§7.6 rule 1)")
            if self.development_frequency_max > MARKER_NATURAL_FREQUENCY_MAX:
                raise InstrumentError(
                    f"{self.kind}: marker {word!r} occurs in "
                    f"{self.development_frequency_max} of unconstrained "
                    f"development responses, above §7.6's ceiling of "
                    f"{MARKER_NATURAL_FREQUENCY_MAX}")
        if self.form is FORM_RATE and min(self.reserve) < 1:
            raise InstrumentError(
                f"{self.kind}: a rate budget at q=0 is satisfied exactly when "
                "the count budget at q=0 is, so it would enter the pool as a "
                "second family with a first family's meaning (§7.10)")
        if self.form is FORM_EXACT and 0 in self.reserve:
            raise InstrumentError(
                f"{self.kind}: an exact count at q=0 is a prohibition whose "
                "chance compliance is near one, which §13.4 would reject "
                "(§7.10)")

    @property
    def constraint_class(self) -> str:
        return _FORM_CLASS[self.form]

    @property
    def structural_tier(self) -> int:
        return self.metadata["structural_tier"]

    @property
    def feature_group(self) -> str:
        return self.metadata["feature_group"]

    @property
    def discourse_role(self) -> str:
        return self.metadata["discourse_role"]

    @property
    def is_rate(self) -> bool:
        return self.form in RATE_FORMS

    @property
    def marker(self) -> str | None:
        return MARKER_WORDS.get(self.statistic_id)


def _metadata(statistic_id: str, form: str, *, length_direction: str,
              production_burden: str, discourse_role: str = "none",
              natural_frequency_band: str | None = None) -> dict[str, Any]:
    """Build §7.3's thirteen-field record from the parts that vary.

    Six of the thirteen are *derived* from the statistic and the form ---
    operator, count-or-rate, denominator, length dependence, class and tier ---
    so a family cannot declare them inconsistently in the first place, and
    ``assert_metadata_consistent`` still re-derives them independently.
    """
    statistic_type, lexical, default_band = _STATISTIC_META[statistic_id]
    is_rate = form in RATE_FORMS
    record = {
        "operator": FORM_OPERATOR[form],
        "statistic_type": statistic_type,
        "count_or_rate": "rate" if is_rate else "count",
        "denominator": "word_count" if is_rate else "none",
        "lexical_or_structural": lexical,
        "length_dependence": ("normalised" if is_rate else
                              ("none" if statistic_type == "marker_occurrence"
                               else "proportional")),
        "length_direction": length_direction,
        "production_burden": production_burden,
        "natural_frequency_band": natural_frequency_band or default_band,
        "constraint_class": _FORM_CLASS[form],
        "feature_group": FEATURE_GROUPS[statistic_id],
        "discourse_role": discourse_role,
    }
    record["structural_tier"] = tier_of_metadata(record)
    return record


#: §7.10's Tier-1 table: marker, letters, discourse role, and the measured
#: maximum P(at least one occurrence | unconstrained) over the four v4r4
#: replications. The measurement is
#: ``dci1/reports/dci1v5/development/d6_marker_frequency.json``; it is
#: **development evidence**, it justified the vocabulary, and it is not a v5
#: measurement of anything.
_TIER1: tuple[tuple[str, str, str, float], ...] = (
    ("MK1", "marker_thus", "consecutive", 0.057),
    ("MK2", "marker_hence", "consecutive", 0.000),
    ("MK3", "marker_though", "contrastive", 0.013),
    ("MK4", "marker_whereas", "contrastive", 0.013),
    ("MK5", "marker_indeed", "emphatic", 0.000),
    ("MK6", "marker_namely", "exemplifying", 0.000),
    ("MK7", "marker_instead", "substitutive", 0.021),
    ("MK8", "marker_overall", "summative", 0.112),
)

#: §7.10: round-0 ladder 1..8, frozen reserve 1..12. The reserve runs to 12
#: and not to 10 on a measurement: §12.6's condition C4 requires a straddling
#: family to carry three eligible rungs spanning at least 0.40 in iota, and
#: the one marker family v4r4 measured spanned **0.375 on three of four**
#: replications. Higher q is harder, so extending the reserve extends the
#: span downward, which is the deficient side.
_TIER1_LADDER = _seq(1, 8)
_TIER1_RESERVE = _seq(1, 12)

_LOW_RATE_LADDER = (1, 2, 3, 4, 5, 6, 8, 10)
_LOW_RATE_RESERVE = _seq(1, 14)


def _tier1_families() -> dict[str, Family]:
    out: dict[str, Family] = {}
    for kind, statistic_id, role, frequency in _TIER1:
        word = MARKER_WORDS[statistic_id]
        out[kind] = Family(
            kind=kind, statistic_id=statistic_id, form=FORM_EXACT,
            ladder=_TIER1_LADDER, reserve=_TIER1_RESERVE,
            rule=f"The answer must use the word {word} exactly q times.",
            statistic_source=("CX1" if kind == "MK1" else "new"),
            metadata=_metadata(statistic_id, FORM_EXACT,
                               length_direction="neutral",
                               production_burden="moderate",
                               discourse_role=role),
            development_frequency_max=frequency)
    return out


#: §7.10's Tier-2 table. XC1 is v4r4's CX2 carried; XC2 and XC3 are new
#: **predicate forms** over v4r4's `comma` and `sentence` counting functions,
#: so §10.2's carry-over evidence covers the numerators and only the form is
#: new.
_TIER2: dict[str, Family] = {
    "XC1": Family(
        "XC1", "semicolon", FORM_EXACT, _seq(1, 8), _seq(1, 10),
        "The answer must contain exactly q semicolon characters.", "CX2",
        _metadata("semicolon", FORM_EXACT, length_direction="neutral",
                  production_burden="moderate")),
    "XC2": Family(
        "XC2", "comma", FORM_EXACT, (2, 4, 6, 8, 10, 12, 14, 16), _seq(1, 20),
        "The answer must contain exactly q comma characters.", "RF5",
        _metadata("comma", FORM_EXACT, length_direction="neutral",
                  production_burden="moderate")),
    "XC3": Family(
        "XC3", "sentence", FORM_EXACT, _seq(3, 10), _seq(1, 14),
        "The answer must contain exactly q sentences.", "RF12",
        _metadata("sentence", FORM_EXACT, length_direction="neutral",
                  production_burden="moderate")),
}

#: §7.10's Tier-3 pool: v4r4's twenty-six broad families, carried unchanged
#: with their ladders and reserves. Admissible to the broad-class slot, and to
#: a spectrum slot only through a core family of their own tier --- which
#: §7.4 admits none of, so in practice they are broad-class families and the
#: check is executable rather than argued.
_TIER3_SPEC: tuple[tuple[str, str, str, tuple[int, ...], tuple[int, ...],
                         str, str], ...] = (
    ("RF1", "b_initial", FORM_COUNT, _seq(0, 8), _seq(0, 8),
     "At most q words in the answer may begin with the letter b.", "RF1"),
    ("RF2", "ing_final", FORM_COUNT, _seq(0, 8), _seq(0, 8),
     "At most q words in the answer may end with the letters ing.", "RF2"),
    ("RF3", "one_letter", FORM_COUNT, _seq(0, 8), _seq(0, 8),
     "At most q words in the answer may have one letter.", "RF3"),
    ("RF4", "doubled_letter", FORM_COUNT, _seq(0, 6), _seq(0, 6),
     "At most q words may contain two identical adjacent letters.", "RF4"),
    ("RF5", "comma", FORM_COUNT, _seq(0, 12), _seq(0, 12),
     "The answer may contain at most q comma characters.", "RF5"),
    ("RF6", "capital_char", FORM_COUNT, _seq(0, 12), _seq(0, 12),
     "The answer may contain at most q upper-case English letters.", "RF6"),
    ("RF7", "letter_a", FORM_COUNT, _seq(0, 24), _seq(0, 24),
     "At most q words in the answer may contain the letter a.", "RF7"),
    ("RF8", "y_final", FORM_COUNT, _seq(0, 8), _seq(0, 8),
     "At most q words in the answer may end with the letter y.", "RF8"),
    ("RF9", "t_initial", FORM_COUNT, (0, 2, 4, 6, 8, 10, 13, 16), _seq(0, 26),
     "At most q words in the answer may begin with the letter t.", "RF9"),
    ("RF10", "s_final", FORM_COUNT, (0, 2, 4, 6, 9, 12, 15, 19), _seq(0, 30),
     "At most q words in the answer may end with the letter s.", "RF10"),
    ("RF11", "vowel_initial", FORM_COUNT, (0, 4, 8, 12, 16, 21, 26, 32),
     _seq(0, 48),
     "At most q words in the answer may begin with a vowel.", "RF11"),
    ("RF12", "sentence", FORM_COUNT, _seq(1, 8), _seq(1, 12),
     "The answer may contain at most q sentences.", "RF12"),
    ("CR1", "b_initial", FORM_RATE, _LOW_RATE_LADDER, _LOW_RATE_RESERVE,
     "At most q percent of words may begin with the letter b.", "RF1"),
    ("CR2", "ing_final", FORM_RATE, _LOW_RATE_LADDER, _LOW_RATE_RESERVE,
     "At most q percent of words may end with the letters ing.", "RF2"),
    ("CR3", "one_letter", FORM_RATE, _LOW_RATE_LADDER, _LOW_RATE_RESERVE,
     "At most q percent of words may have one letter.", "RF3"),
    ("CR4", "doubled_letter", FORM_RATE, (3, 5, 7, 9, 11, 13, 15, 18),
     _seq(2, 20),
     "At most q percent of words may contain two identical adjacent letters.",
     "RF4"),
    ("CR5", "comma", FORM_RATE, _LOW_RATE_LADDER, _LOW_RATE_RESERVE,
     "The answer may contain at most q comma characters per hundred words.",
     "RF5"),
    ("CR6", "capital_word", FORM_RATE, (3, 4, 5, 6, 7, 8, 10, 12), _seq(1, 16),
     "At most q percent of words may use a capital letter.", "CR6"),
    ("CR7", "letter_a", FORM_RATE, (24, 28, 32, 36, 40, 44, 48, 52),
     _seq(20, 56, 2),
     "At most q percent of words may contain the letter a.", "RF7"),
    ("CR8", "y_final", FORM_RATE, _LOW_RATE_LADDER, _LOW_RATE_RESERVE,
     "At most q percent of words may end with the letter y.", "RF8"),
    ("CR9", "t_initial", FORM_RATE, (1, 2, 4, 6, 8, 10, 12, 15), _seq(1, 20),
     "At most q percent of words may begin with the letter t.", "RF9"),
    ("CR10", "s_final", FORM_RATE, (2, 4, 6, 8, 11, 14, 17, 21), _seq(1, 26),
     "At most q percent of words may end with the letter s.", "RF10"),
    ("CR11", "vowel_initial", FORM_RATE, (4, 8, 12, 16, 20, 24, 28, 33),
     _seq(2, 40),
     "At most q percent of words may begin with a vowel.", "RF11"),
    ("CR12", "sentence", FORM_RATE, (1, 2, 3, 4, 5, 6, 8, 10), _seq(1, 14),
     "The answer may contain at most q sentences per hundred words.", "RF12"),
    ("CL7", "letter_a", FORM_LOWER_BOUND, (10, 20, 30, 45, 60, 80, 100, 130),
     _seq(5, 140, 5),
     "At least q words in the answer must contain the letter a.", "RF7"),
    ("CL8", "y_final", FORM_LOWER_BOUND, (2, 3, 5, 7, 10, 14, 19, 25),
     _seq(1, 28),
     "At least q words in the answer must end with the letter y.", "RF8"),
)


def _tier3_families() -> dict[str, Family]:
    out: dict[str, Family] = {}
    for kind, statistic_id, form, ladder, reserve, rule, source in _TIER3_SPEC:
        if form in RATE_FORMS:
            direction, burden = "neutral", "low"
        elif form in LOWER_BOUND_FORMS:
            direction, burden = "lengthens", "high"
        else:
            direction, burden = "shortens", "low"
        out[kind] = Family(
            kind=kind, statistic_id=statistic_id, form=form, ladder=ladder,
            reserve=reserve, rule=rule, statistic_source=source,
            metadata=_metadata(statistic_id, form, length_direction=direction,
                               production_burden=burden))
    return out


FAMILIES: dict[str, Family] = {**_tier1_families(), **_TIER2,
                               **_tier3_families()}
FAMILY_IDS = tuple(FAMILIES)
TIER1_FAMILY_IDS = tuple(k for k, f in FAMILIES.items()
                         if f.structural_tier == TIER_1)
TIER2_FAMILY_IDS = tuple(k for k, f in FAMILIES.items()
                         if f.structural_tier == TIER_2)
TIER3_FAMILY_IDS = tuple(k for k, f in FAMILIES.items()
                         if f.structural_tier == TIER_3)

LADDERS = {k: f.ladder for k, f in FAMILIES.items()}
RESERVES = {k: f.reserve for k, f in FAMILIES.items()}
KINDS = ("A", "B") + FAMILY_IDS

#: §30's ledger, in the source rather than only in a report. An instrument is
#: carried only when its construct string, segmentation source, counting
#: source and frozen case texts are byte-identical to the source artifact;
#: ``verifiers/carryover.py`` refuses on any mismatch and **measures** the
#: predicate agreement rather than asserting it.
CARRIED_FROM_V4R4: dict[str, dict[str, str]] = {
    "MK1": {"from": "CX1", "what": "the exact-count predicate over the "
                                   "marker `thus`, ladder and reserve widened",
            "class": "REUSED_IMPLEMENTATION"},
    "XC1": {"from": "CX2", "what": "the exact-count predicate over semicolon "
                                   "characters, reserve unchanged",
            "class": "REUSED_IMPLEMENTATION"},
    "XC2": {"from": "RF5", "what": "the `comma` counting function; the "
                                   "exact-count form is new",
            "class": "REUSED_IMPLEMENTATION"},
    "XC3": {"from": "RF12", "what": "the `sentence` counting function; the "
                                    "exact-count form is new",
            "class": "REUSED_IMPLEMENTATION"},
}

N_FAMILIES = len(FAMILIES)
N_SEVERITIES = sum(len(v) for v in LADDERS.values())
N_DECLARED_SEVERITIES = sum(len(v) for v in RESERVES.values())
#: §10.2's instrument population: the declared range of every family, plus A's
#: eight severities and B's eight registered plus two extension rungs.
N_INSTRUMENTS = (N_DECLARED_SEVERITIES + len(TARGET_GRID)
                 + len(focal_severities(extended=True)))
N_VERIFIERS = N_FAMILIES + 2


def assert_library_sizes() -> dict[str, int]:
    """§7.10's four counts, asserted rather than described.

    v4r4's constants carried comments that disagreed with its computed values.
    Nothing scientific moved --- the code used the computed values --- but a
    number a reader can check against the source is the only kind worth
    printing, so these are assertions and the report reads them from here.
    """
    expected = {"families": 37, "round_0_severities": 326,
                "declared_severities": 632, "instruments": 650,
                "verifiers": 39}
    got = {"families": N_FAMILIES, "round_0_severities": N_SEVERITIES,
           "declared_severities": N_DECLARED_SEVERITIES,
           "instruments": N_INSTRUMENTS, "verifiers": N_VERIFIERS}
    if got != expected:
        raise InstrumentError(
            f"§7.10's registered library sizes are {expected} and this "
            f"library computes {got}")
    return got


def assert_ladder_within_reserve() -> None:
    for kind, family in FAMILIES.items():
        if not set(family.ladder) <= set(family.reserve):
            raise InstrumentError(f"{kind}: ladder escapes its reserve")


def assert_no_zero_rung() -> None:
    """§7.10: no rate ladder and no exact-count ladder contains q = 0."""
    for kind, family in FAMILIES.items():
        if family.form is FORM_RATE and 0 in family.reserve:
            raise InstrumentError(
                f"{kind}: q=0 duplicates the count budget of the same "
                "numerator")
        if family.form is FORM_EXACT and 0 in family.reserve:
            raise InstrumentError(
                f"{kind}: an exact count at q=0 is a prohibition whose chance "
                "compliance is near one")


def assert_marker_vocabulary() -> None:
    """§7.6's three rules over the registered vocabulary.

    The rule is stated over the **population** and not over a list of words
    that happened to work: every registered marker is tested, and a word is
    rejected by the rule rather than by being absent from an allow-list.
    """
    seen: set[str] = set()
    for kind in TIER1_FAMILY_IDS:
        family = FAMILIES[kind]
        word = family.marker
        if word is None:
            raise InstrumentError(f"{kind}: a Tier-1 family names a marker")
        if word == TARGET_WORD:
            raise InstrumentError(f"{kind}: {TARGET_WORD!r} is A's marker")
        if len(word) > MARKER_MAX_LETTERS:
            raise InstrumentError(f"{kind}: {word!r} exceeds "
                                  f"{MARKER_MAX_LETTERS} letters")
        if family.development_frequency_max > MARKER_NATURAL_FREQUENCY_MAX:
            raise InstrumentError(
                f"{kind}: {word!r} above the natural-frequency ceiling")
        if word in seen:
            raise InstrumentError(f"{word!r} is registered twice")
        seen.add(word)
    if len(seen) != 8:
        raise InstrumentError(
            f"§7.10 registers eight Tier-1 marker families; found {len(seen)}")


assert_ladder_within_reserve()
assert_no_zero_rung()
assert_marker_vocabulary()
assert_library_sizes()


def declared_range(kind: str) -> tuple[int, ...]:
    """Every severity of ``kind`` that can ever enter the study (§10.2).

    Gate 1's instrument population is this and not the round-0 ladder: §12.6's
    expansion may admit any reserve rung, so the boundary suites and the
    reimplementation evidence are frozen over the whole declared range before
    qualification.
    """
    if kind == "A":
        return TARGET_GRID
    if kind == "B":
        return focal_severities(extended=True)
    if kind in RESERVES:
        return RESERVES[kind]
    raise InstrumentError(f"unknown constraint kind {kind!r}")


def registered_severities(kind: str, *, extended: bool = False,
                          reserve: bool = False) -> tuple[int, ...]:
    if kind == "A":
        return TARGET_GRID
    if kind == "B":
        return focal_severities(extended=extended)
    if kind in LADDERS:
        return RESERVES[kind] if reserve else LADDERS[kind]
    raise InstrumentError(f"unknown constraint kind {kind!r}")


def family_class(kind: str) -> str:
    if kind == "A":
        return CLASS_PRODUCTION          # S == n
    if kind == "B":
        return CLASS_BUDGET              # longest word <= m
    if kind in FAMILIES:
        return FAMILIES[kind].constraint_class
    raise InstrumentError(f"unknown constraint kind {kind!r}")


def family_form(kind: str) -> str:
    if kind in FAMILIES:
        return FAMILIES[kind].form
    raise InstrumentError(f"{kind!r} is not a family")


def family_tier(kind: str) -> int:
    if kind in FAMILIES:
        return FAMILIES[kind].structural_tier
    raise InstrumentError(f"{kind!r} is not a family")


def feature_group(kind: str) -> str:
    if kind in FAMILIES:
        return FAMILIES[kind].feature_group
    raise InstrumentError(f"{kind!r} is not a family")


def discourse_role(kind: str) -> str:
    if kind in FAMILIES:
        return FAMILIES[kind].discourse_role
    raise InstrumentError(f"{kind!r} is not a family")


def structural_metadata(kind: str) -> dict[str, Any]:
    if kind in FAMILIES:
        return dict(FAMILIES[kind].metadata)
    raise InstrumentError(f"{kind!r} is not a family")


def assert_slot_allowed(kind: str, slot: str, *,
                        core_family_tier: int | None = None) -> None:
    """§7.4's slot table, and §13.10's budget-class rule for the broad slot.

    On the mandatory path rather than in prose, and with the **broad-class
    slot's extra condition** enforced here: §13.10 admits Tier-3 *budget*
    families only, so `CL7` and `CL8` --- the two count lower bounds --- are
    Tier 3 and broad-class-ineligible, and the check says so by name.
    """
    if kind in ("A", "B"):
        raise InstrumentError(
            f"{kind} is an outcome constraint, not a companion candidate")
    family = FAMILIES.get(kind)
    if family is None:
        raise InstrumentError(f"unknown family {kind!r}")
    assert_tier_admits_slot(kind, family.structural_tier, slot,
                            core_family_tier=core_family_tier)
    if slot == SLOT_BROAD_CLASS and \
            family.constraint_class != CLASS_BUDGET:
        raise InstrumentError(
            f"{kind} is {family.constraint_class} class; §13.10 admits a "
            "budget-class companion to the broad-class slot only")


@dataclass(frozen=True)
class Constraint:
    """One registered constraint instance: a kind and a severity.

    ``extended`` admits B's §7.2 escalation rungs and ``reserve`` a §12.6
    expansion rung. Both default to False, so neither can reach a cell plan
    except through the record that admitted it.
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
    def structural_tier(self) -> int | None:
        return None if self.kind in ("A", "B") else family_tier(self.kind)

    @property
    def form(self) -> str:
        if self.kind == "A":
            return FORM_EXACT
        if self.kind == "B":
            return "max_word_length"
        return family_form(self.kind)


#: Re-exported so a caller need not reach into the taxonomy for a slot name.
SLOT_CORE = SLOT_CORE
SLOT_SPECTRUM = SLOT_SPECTRUM
SLOT_NEAR_FORM = SLOT_NEAR_FORM
SLOT_BROAD_CLASS = SLOT_BROAD_CLASS


def assert_marker_vocabulary_approved() -> tuple[str, ...]:
    """§34 D4: the marker vocabulary is a **researcher decision**.

    ``assert_marker_vocabulary`` checks that the eight registered markers
    satisfy §7.6's three rules. That is a different question from whether the
    researcher has approved them: a reader may hold that `namely`, `notably`
    or `overall` is not semantically neutral in an informational answer, or
    that eight is too many or too few. This refuses until D4 is closed, and
    §18 stage 4 calls it before the regime screen measures a marker rung.
    """
    from dci1v5.protocol import decisions

    assert_marker_vocabulary()
    return decisions.choice(
        "D4",
        {"approve_eight": tuple(MARKER_WORDS.values()),
         "approve_with_substitution": tuple(MARKER_WORDS.values()),
         "reject": ()},
        where="verifiers.constraints.assert_marker_vocabulary_approved")
