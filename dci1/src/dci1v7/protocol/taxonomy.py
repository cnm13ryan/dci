"""The structural taxonomy: metadata vocabulary, tiers, slots (§7.3, §7.4).

v4r4 said what a control shared with A with one word --- its
``constraint_class``, ``budget`` or ``production`` --- and §2.3 F3 is the
measurement of how coarse that was: two companions in the *same* declared
class produced Delta_class of +0.011 and -0.511. This module is the
replacement. Thirteen declared fields, three tiers defined **relative to A's
own description and to nothing else**, and a slot table that an executable
check enforces rather than a paragraph asserts.

**A, in the vocabulary below**, is the reference point every tier is defined
against::

    operator              ==
    statistic_type        marker_occurrence
    count_or_rate         count
    denominator           none
    lexical_or_structural lexical
    length_dependence     none
    length_direction      neutral
    production_burden     moderate
    natural_frequency_band low
    constraint_class      production
    structural_tier       ---   (A is not a candidate)
    feature_group         marker_however
    discourse_role        contrastive

**Tier 1** matches every structural field of that record and differs only in
which marker word is counted and in the count. **Tier 2** keeps the operator,
the count-ness and the absent denominator and changes the statistic type.
**Tier 3** is everything else.

The tier of the *spectrum* slot is not a constant. §13.12 draws both spectrum
rungs from the same family as the core reference they belong to, so the
spectrum inherits that family's tier and no independent tier rule applies to
it. ``assert_tier_admits_slot`` therefore takes the core family's tier for
that slot rather than a literal, which is the §7.4 correction R3 found.
"""
from __future__ import annotations

from typing import Any, Mapping

from dci1v4.errors import InstrumentError

__all__ = ["METADATA_FIELDS", "OPERATORS", "STATISTIC_TYPES", "COUNT_OR_RATE",
           "DENOMINATORS", "LEXICAL_OR_STRUCTURAL", "LENGTH_DEPENDENCE",
           "LENGTH_DIRECTION", "PRODUCTION_BURDEN", "NATURAL_FREQUENCY_BAND",
           "CONSTRAINT_CLASSES", "DISCOURSE_ROLES", "TIERS", "TIER_1",
           "TIER_2", "TIER_3", "SLOTS", "SLOT_CORE", "SLOT_SPECTRUM",
           "SLOT_NEAR_FORM", "SLOT_BROAD_CLASS", "SLOT_ADMISSIBLE_TIERS",
           "A_STRUCTURAL_RECORD", "tier_of_metadata", "declared_roles",
           "assert_metadata_consistent", "assert_tier_admits_slot",
           "assert_core_set_structure", "VALUE_DOMAINS"]

# ------------------------------------------------------------ §7.3 vocabulary
OPERATORS = ("==", "<=", ">=")
STATISTIC_TYPES = ("marker_occurrence", "word_property",
                   "punctuation_character", "sentence_unit", "answer_length")
COUNT_OR_RATE = ("count", "rate")
DENOMINATORS = ("none", "word_count")
LEXICAL_OR_STRUCTURAL = ("lexical", "structural")
LENGTH_DEPENDENCE = ("none", "normalised", "proportional")
LENGTH_DIRECTION = ("neutral", "lengthens", "shortens")
PRODUCTION_BURDEN = ("low", "moderate", "high")
NATURAL_FREQUENCY_BAND = ("zero", "low", "moderate", "high")
CONSTRAINT_CLASSES = ("budget", "production")
#: §7.6. Declared, audited at qualification, never measured; §29 records what
#: that does and does not control.
DISCOURSE_ROLES = ("contrastive", "consecutive", "emphatic", "exemplifying",
                   "substitutive", "additive", "concessive", "summative",
                   "none")

TIER_1, TIER_2, TIER_3 = 1, 2, 3
TIERS = (TIER_1, TIER_2, TIER_3)

#: §7.3's thirteen fields, in the registered order. ``feature_group`` is a
#: free string checked against the registered partition by the library, not
#: by a closed domain here.
METADATA_FIELDS = ("operator", "statistic_type", "count_or_rate",
                   "denominator", "lexical_or_structural", "length_dependence",
                   "length_direction", "production_burden",
                   "natural_frequency_band", "constraint_class",
                   "structural_tier", "feature_group", "discourse_role")

VALUE_DOMAINS: dict[str, tuple[Any, ...]] = {
    "operator": OPERATORS, "statistic_type": STATISTIC_TYPES,
    "count_or_rate": COUNT_OR_RATE, "denominator": DENOMINATORS,
    "lexical_or_structural": LEXICAL_OR_STRUCTURAL,
    "length_dependence": LENGTH_DEPENDENCE,
    "length_direction": LENGTH_DIRECTION,
    "production_burden": PRODUCTION_BURDEN,
    "natural_frequency_band": NATURAL_FREQUENCY_BAND,
    "constraint_class": CONSTRAINT_CLASSES, "structural_tier": TIERS,
    "discourse_role": DISCOURSE_ROLES,
}

#: §7.4's reference point. Every tier is defined against this and nothing
#: else, so it is a value rather than a paragraph.
A_STRUCTURAL_RECORD: dict[str, Any] = {
    "operator": "==", "statistic_type": "marker_occurrence",
    "count_or_rate": "count", "denominator": "none",
    "lexical_or_structural": "lexical", "length_dependence": "none",
    "length_direction": "neutral", "production_burden": "moderate",
    "natural_frequency_band": "low", "constraint_class": "production",
    "feature_group": "marker_however", "discourse_role": "contrastive",
}

#: The fields Tier 1 must match A on. Deliberately *not* every field:
#: ``production_burden`` and ``natural_frequency_band`` are properties of the
#: particular marker and severity, and requiring identity on them would make
#: the tier a property of one word rather than of a form.
_TIER1_IDENTITY_FIELDS = ("operator", "statistic_type", "count_or_rate",
                          "denominator", "lexical_or_structural",
                          "length_dependence", "length_direction")

# ---------------------------------------------------------------- §7.4 slots
SLOT_CORE = "core_reference"
SLOT_SPECTRUM = "spectrum"
SLOT_NEAR_FORM = "near_form_control"
SLOT_BROAD_CLASS = "broad_class_control"
SLOTS = (SLOT_CORE, SLOT_SPECTRUM, SLOT_NEAR_FORM, SLOT_BROAD_CLASS)

#: §7.4's slot table. ``SLOT_SPECTRUM`` is absent by design: its admissible
#: tier is *the tier of its own core family*, which is not a constant, and
#: ``assert_tier_admits_slot`` requires the caller to supply it.
SLOT_ADMISSIBLE_TIERS: dict[str, tuple[int, ...]] = {
    SLOT_CORE: (TIER_1, TIER_2),
    SLOT_NEAR_FORM: (TIER_2,),
    SLOT_BROAD_CLASS: (TIER_3,),
}


def tier_of_metadata(meta: Mapping[str, Any]) -> int:
    """§7.4's tier rule, computed from the record rather than declared.

    ``assert_metadata_consistent`` compares this with the family's declared
    ``structural_tier``, so a family cannot claim a tier its own structure
    contradicts. That is the whole reason the rule is a function.
    """
    if meta.get("operator") == "==" and meta.get("count_or_rate") == "count" \
            and meta.get("denominator") == "none":
        if all(meta.get(f) == A_STRUCTURAL_RECORD[f]
               for f in _TIER1_IDENTITY_FIELDS):
            return TIER_1
        return TIER_2
    return TIER_3


def assert_metadata_consistent(kind: str, meta: Mapping[str, Any], *,
                               form_class: str, form_operator: str) -> None:
    """Every declared field in domain, and consistent with the predicate.

    ``form_class`` and ``form_operator`` come from the family's *predicate
    form*, so a declaration that disagrees with the predicate the verifier
    actually evaluates fails qualification (§7.3, §18 stage 2).
    """
    missing = [f for f in METADATA_FIELDS if f not in meta]
    if missing:
        raise InstrumentError(
            f"{kind}: §7.3 requires all thirteen structural-metadata fields; "
            f"missing {missing}")
    unknown = sorted(set(meta) - set(METADATA_FIELDS))
    if unknown:
        raise InstrumentError(
            f"{kind}: unknown structural-metadata field(s) {unknown}; the "
            "§7.3 record is closed so that a family cannot declare a "
            "property no rule reads")
    for field, domain in VALUE_DOMAINS.items():
        if meta[field] not in domain:
            raise InstrumentError(
                f"{kind}: {field}={meta[field]!r} is outside its registered "
                f"domain {domain}")
    if not isinstance(meta["feature_group"], str) or not meta["feature_group"]:
        raise InstrumentError(f"{kind}: feature_group must be a non-empty "
                              "registered group identifier")
    if meta["operator"] != form_operator:
        raise InstrumentError(
            f"{kind}: declares operator {meta['operator']!r} and its "
            f"predicate form evaluates {form_operator!r}")
    if meta["constraint_class"] != form_class:
        raise InstrumentError(
            f"{kind}: declares constraint_class {meta['constraint_class']!r} "
            f"and its predicate form is {form_class!r}; §7.3 asserts the "
            "class against the operator and a family may not declare a class "
            "its own form contradicts")
    if (meta["count_or_rate"] == "rate") != (meta["denominator"] ==
                                             "word_count"):
        raise InstrumentError(
            f"{kind}: a rate has the word count as denominator and a count "
            f"has none; got count_or_rate={meta['count_or_rate']!r} with "
            f"denominator={meta['denominator']!r}")
    if meta["count_or_rate"] == "rate" and \
            meta["length_dependence"] != "normalised":
        raise InstrumentError(
            f"{kind}: a rate normalises by the word count, so its "
            f"length_dependence is 'normalised', not "
            f"{meta['length_dependence']!r}")
    if meta["statistic_type"] == "marker_occurrence" and \
            meta["discourse_role"] == "none":
        raise InstrumentError(
            f"{kind}: §7.6 requires every marker family to declare a "
            "discourse role, because §13.8 selects on the spread of roles")
    if meta["statistic_type"] != "marker_occurrence" and \
            meta["discourse_role"] != "none":
        raise InstrumentError(
            f"{kind}: only a marker family carries a discourse role; "
            f"{meta['statistic_type']!r} declared "
            f"{meta['discourse_role']!r}")
    derived = tier_of_metadata(meta)
    if meta["structural_tier"] != derived:
        raise InstrumentError(
            f"{kind}: declares structural_tier {meta['structural_tier']} and "
            f"§7.4's rule derives {derived} from its own metadata")


def assert_tier_admits_slot(kind: str, tier: int, slot: str, *,
                            core_family_tier: int | None = None) -> None:
    """§7.4's slot table, on the mandatory path.

    ``core_family_tier`` is required for ``SLOT_SPECTRUM`` and forbidden
    elsewhere: §13.12 draws a spectrum rung from the *same family* as its core
    reference, so the only admissible tier for that slot is that family's own,
    and a call that cannot say which family it belongs to is a call that has
    lost the thing the rule is about.
    """
    if slot not in SLOTS:
        raise InstrumentError(f"{slot!r} is not a registered §7.4 slot; "
                              f"registered: {SLOTS}")
    if tier not in TIERS:
        raise InstrumentError(f"{kind}: {tier!r} is not a registered tier")
    if slot == SLOT_SPECTRUM:
        if core_family_tier is None:
            raise InstrumentError(
                f"{kind}: the spectrum slot admits the tier of its own core "
                "family (§7.4, §13.12); the caller must name it")
        if tier != core_family_tier:
            raise InstrumentError(
                f"{kind}: a spectrum rung is drawn from the same family as "
                f"its core reference, so its tier is {core_family_tier} and "
                f"this family is Tier {tier}")
        return
    if core_family_tier is not None:
        raise InstrumentError(
            f"{kind}: core_family_tier applies to the spectrum slot alone")
    admissible = SLOT_ADMISSIBLE_TIERS[slot]
    if tier not in admissible:
        raise InstrumentError(
            f"{kind}: Tier {tier} is not admissible to the {slot} slot; "
            f"§7.4 admits {admissible}")


def declared_roles(entries) -> set[str]:
    """The discourse roles an admitted set actually declares.

    ``none`` is **not** a role. §7.6 assigns a discourse role to marker
    families and to no others, so a Tier-2 member contributes no role and
    counting its ``none`` toward §13.8's "at least two declared discourse
    roles" would satisfy the requirement with one real role and one absence.

    **This is a reading of an under-specified rule and it is recorded as
    one.** §13.8 requires the three core references to span at least two
    declared roles and describes a substitution when *"the three
    otherwise-chosen references share one role"*; it does not say what a
    Tier-2 member --- which has no role at all --- contributes. §13.15
    guarantees at least two Tier-1 members, so at least two members always
    declare a role and the requirement is always well defined under this
    reading. The alternative reading, counting ``none``, would let a set of
    two same-role markers and one Tier-2 control satisfy a rule written to
    make the pool span discourse function.
    """
    return {e["discourse_role"] for e in entries
            if e["discourse_role"] != "none"}


def assert_core_set_structure(entries, *, min_tier1: int, n_groups: int,
                              min_roles: int, a_role: str) -> dict[str, Any]:
    """§7.4 and §13.8's structural conditions on the admitted core set.

    ``entries`` are mappings carrying ``family``, ``structural_tier``,
    ``feature_group`` and ``discourse_role``. Returns the realised counts and
    the identification statuses the set earns, so a caller records the
    verdict rather than recomputing it.
    """
    entries = list(entries)
    tiers = [e["structural_tier"] for e in entries]
    groups = {e["feature_group"] for e in entries}
    roles = declared_roles(entries)
    n_tier1 = sum(1 for t in tiers if t == TIER_1)
    if n_tier1 < min_tier1:
        raise InstrumentError(
            f"§13.15 requires at least {min_tier1} Tier-1 core references and "
            f"this set carries {n_tier1}: the primary local estimand is a "
            "same-form contrast")
    if len(groups) != n_groups:
        raise InstrumentError(
            f"§13.8 requires {n_groups} distinct feature groups among the "
            f"core references; got {sorted(groups)}")
    if len(roles) < min_roles:
        raise InstrumentError(
            f"§13.8 requires the core references to span at least "
            f"{min_roles} declared discourse roles; got {sorted(roles)}")
    statuses = []
    if a_role not in roles:
        statuses.append("REFERENCE_ROLE_NOT_MATCHED")
    return {"n_tier1": n_tier1, "feature_groups": sorted(groups),
            "discourse_roles": sorted(roles),
            "discourse_roles_as_declared":
                sorted({e["discourse_role"] for e in entries}),
            "roles_counted_excluding_none": True,
            "identification_statuses": statuses}
