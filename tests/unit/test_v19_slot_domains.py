"""Populated is not validated: a slot's declared domain refuses a wrong value.

The adversarial audit's worst finding (S11) was that Stage 2 certified with every
registry value nonsense - `ordering_depth = None`, `inherited_reuse_decision = ""`,
an interval name the interval loader itself rejects - because the gate asked whether
a slot was RESOLVED and never whether its value was usable.

A domain is a named, auditable predicate. Its name is part of the slot's declaration
fingerprint, so widening one is a change to the registry rather than to a private
helper. These tests hold two properties: every value the code actually produces is
admissible, and the specific nonsense the audit froze is not.

BOUNDARY_MUTATIONS IS A RECORD SCHEMA, ON PURPOSE
-------------------------------------------------
It checks the SHAPE of section 8.7 evidence and says nothing about which templates
exist or what their hashes are. Whether the recorded hashes match a battery the
harness produces is a certification question, answered by regenerating the battery
where the harness lives. That division keeps the domain's meaning stable across the
stack: a slot whose declared domain silently tightened between two commits would
have a fingerprint that no longer described it.
"""
from __future__ import annotations

import pytest
import v19_domain_values as stand_in

from dci.v19 import artifacts, ordering
from dci.v19.parsing import CANONICAL_LIST_POLICY
from dci.v19.reliability import AMENDED_INTERVAL, AMENDED_TIER1_DESIGN
from dci.v19.resolution import Resolution, Slot, fixed, pending
from dci.v19.schemas import DOMAINS, DomainError, validate
from dci.v19.text import CANONICAL_TEXT_POLICY

pytestmark = pytest.mark.cpu


def a_slot(domain: str, value):
    return fixed("probe.slot", "a probe", value, rule="a probe", domain=domain)


# ------------------------------------------------------ the domain table itself
def test_an_undeclared_domain_is_refused_rather_than_ignored():
    with pytest.raises(DomainError, match="not a declared slot domain"):
        validate("no_such_domain", "anything")


@pytest.mark.parametrize("domain", sorted(DOMAINS))
def test_every_declared_domain_admits_the_value_the_code_produces(domain):
    validate(domain, stand_in.for_domain(domain))


@pytest.mark.parametrize("domain", sorted(DOMAINS))
def test_no_domain_admits_none_or_an_empty_string(domain):
    for nonsense in (None, "", 0):
        with pytest.raises(DomainError):
            validate(domain, nonsense)


# ------------------------------------------------------------- the audit's values
@pytest.mark.parametrize("domain,frozen_by_the_audit", [
    ("ordering_depth", None),
    ("ordering_depth", "a deep ordering"),
    ("reuse_disposition", ""),
    ("binomial_interval", "exact"),
    ("binomial_interval", "bootstrap_t"),
    ("boundary_mutations", {"not-a-real-template": {"n_mutations": 1000}}),
    ("bundle_hash", "0" * 64),
    ("specification_bundle", {"protocol": "v19"}),
    ("list_policy", 12345),
    ("tier1_audit_design", "clopper_pearson"),
])
def test_the_nonsense_the_audit_froze_is_refused(domain, frozen_by_the_audit):
    with pytest.raises(DomainError):
        validate(domain, frozen_by_the_audit)


def test_a_slot_refuses_an_inadmissible_value_at_declaration():
    with pytest.raises(ValueError, match="not admissible for domain"):
        a_slot("binomial_interval", "exact")


def test_a_slot_refuses_an_inadmissible_value_at_freeze():
    slot = pending("probe.slot", "a probe", Resolution.PENDING_DECISION,
                   "a probe", domain="binomial_interval")
    with pytest.raises(ValueError, match="not admissible for domain"):
        slot.freeze("exact", by="a probe")
    assert slot.freeze(AMENDED_INTERVAL, by="a probe").resolved


def test_a_slot_with_no_domain_still_accepts_anything():
    """Stated so the coverage requirement has something to be about."""
    assert fixed("probe.slot", "a probe", None, rule="r").get() is None


def test_the_domain_name_is_part_of_the_declaration_fingerprint():
    """Widening a domain must be a registry change, not a private edit.

    The declaration fingerprint is what two runs compare to show they are working
    from the same registry, so a domain that could be swapped without moving it
    would be a measurement rule nobody could detect a change to.
    """
    from dci.v19.resolution import SlotTable
    typed = SlotTable.of(
        Slot(name="probe.slot", prereg="a probe", resolution=Resolution.FIXED,
             rule="r", value=AMENDED_INTERVAL, domain="binomial_interval"))
    untyped = SlotTable.of(
        Slot(name="probe.slot", prereg="a probe", resolution=Resolution.FIXED,
             rule="r", value=AMENDED_INTERVAL, domain=""))
    assert typed.fingerprint != untyped.fingerprint
    assert typed["probe.slot"].describe()["domain"] == "binomial_interval"


# ----------------------------------------------------------------- list policy
def test_only_the_implemented_grammar_may_be_frozen():
    validate("list_policy", CANONICAL_LIST_POLICY.state())
    altered = dict(CANONICAL_LIST_POLICY.state())
    altered["numbered_max_digits"] = 2
    with pytest.raises(DomainError, match="does not match the implemented one"):
        validate("list_policy", altered)


def test_a_live_policy_object_is_not_a_registry_value():
    with pytest.raises(DomainError, match="expected a mapping"):
        validate("list_policy", CANONICAL_LIST_POLICY)


def test_the_text_policy_domain_is_the_implemented_one_too():
    validate("text_policy", CANONICAL_TEXT_POLICY.state())
    altered = dict(CANONICAL_TEXT_POLICY.state())
    altered["case_rule"] = "lower"
    with pytest.raises(DomainError):
        validate("text_policy", altered)


# -------------------------------------------------------------- ordering depth
def test_the_a4_decision_is_admissible():
    validate("ordering_depth", ordering.DECISION)


@pytest.mark.parametrize("field,value", [
    ("statistic", "v19:ordering-depth.edge-count"),
    ("generator", "v19:ordering-depth.something-else"),
    ("min_depth", 1),
    ("max_depth_rule", "unbounded"),
    ("harder_direction", "decreasing"),
    ("exposes", "transitive_closure"),
    ("definition", ""),
    ("generator_form", ""),
])
def test_a_decision_that_departs_from_the_implemented_construct_is_refused(field,
                                                                          value):
    offered = dict(ordering.DECISION)
    offered[field] = value
    with pytest.raises(DomainError):
        validate("ordering_depth", offered)


def test_a_stage_two_decision_carrying_a_grid_is_refused():
    """Section 6.2's grid is the Stage 5 output D6; carrying one pre-empts it."""
    offered = dict(ordering.DECISION)
    offered["grid"] = [2, 3, 4]
    with pytest.raises(DomainError, match="Stage 5 boundary-calibration output"):
        validate("ordering_depth", offered)


def test_dropping_the_reason_for_having_no_grid_is_refused():
    offered = dict(ordering.DECISION)
    offered["grid_rule"] = ""
    with pytest.raises(DomainError):
        validate("ordering_depth", offered)


# ---------------------------------------------------------- reuse disposition
def test_the_a2_disposition_is_admissible_and_says_corrected():
    validate("reuse_disposition", artifacts.REUSE_DISPOSITION)
    assert artifacts.REUSE_DISPOSITION["disposition"] == "corrected"


def test_a_correction_claim_with_no_corrections_is_refused():
    with pytest.raises(DomainError, match="names its corrections"):
        validate("reuse_disposition", {"disposition": "corrected",
                                       "rationale": "trust me", "corrections": []})


def test_reuse_unchanged_needs_no_corrections_but_still_needs_a_rationale():
    validate("reuse_disposition", {"disposition": "reused_unchanged",
                                   "rationale": "the audit found nothing"})
    with pytest.raises(DomainError, match="'rationale' is required"):
        validate("reuse_disposition", {"disposition": "reused_unchanged"})


def test_the_disposition_is_derived_from_the_text_corrections_not_retyped():
    from dci.v19.text import INTENTIONAL_CORRECTIONS
    recorded = {row["id"] for row in artifacts.REUSE_DISPOSITION["corrections"]}
    assert recorded == {row["id"] for row in INTENTIONAL_CORRECTIONS}


# ------------------------------------------------------------ interval, design
def test_the_interval_domain_and_its_consumer_agree():
    """S11c: the domain must not admit a name `frozen_interval` then rejects."""
    from dci.v19.reliability import INTERVAL_IMPLEMENTATIONS
    for name in INTERVAL_IMPLEMENTATIONS:
        validate("binomial_interval", name)
    with pytest.raises(DomainError):
        validate("binomial_interval", "clopper-pearson")


def test_the_audit_design_domain_is_the_implemented_design():
    validate("tier1_audit_design", AMENDED_TIER1_DESIGN.state())
    import dataclasses
    relaxed = dataclasses.replace(AMENDED_TIER1_DESIGN, errors_permitted=1)
    with pytest.raises(DomainError, match="does not match the implemented one"):
        validate("tier1_audit_design", relaxed.state())


# ------------------------------------------- boundary mutations: a record schema
def test_a_well_formed_battery_record_is_admissible():
    validate("boundary_mutations", stand_in.battery_evidence())


def test_a_template_that_is_not_a_constraint_id_is_refused():
    with pytest.raises(DomainError, match="not a v19 constraint id"):
        validate("boundary_mutations",
                 {"not-a-real-template": {"records_hash": "a" * 64,
                                          "n_mutations": 1000,
                                          "distinct_texts": 1000}})


def test_a_record_with_no_hash_cannot_be_re_derived_and_is_refused():
    with pytest.raises(DomainError, match="records_hash"):
        validate("boundary_mutations",
                 {"v19:p1.target.exact_bullet_count": {"n_mutations": 1000,
                                                       "distinct_texts": 1000}})


@pytest.mark.parametrize("count", [0, 1, 999, None, "1000", True])
def test_a_battery_below_the_section_eight_seven_floor_is_refused(count):
    with pytest.raises(DomainError):
        validate("boundary_mutations",
                 {"v19:p1.target.exact_bullet_count": {"records_hash": "a" * 64,
                                                       "n_mutations": count,
                                                       "distinct_texts": count}})


def test_a_floor_reached_by_repeating_one_edit_is_refused():
    """Section 8.7 wants coverage; 1,000 copies of one mutation is not coverage."""
    with pytest.raises(DomainError, match="not coverage"):
        validate("boundary_mutations",
                 {"v19:p1.target.exact_bullet_count": {"records_hash": "a" * 64,
                                                       "n_mutations": 1000,
                                                       "distinct_texts": 3}})


def test_the_record_schema_does_not_pin_which_templates_exist():
    """Stability across the stack: this is what PR #14 must NOT redefine.

    A single well-formed template validates. Which six templates are required, and
    whether their hashes match a regenerated battery, is a certification question
    answered where the harness lives.
    """
    validate("boundary_mutations",
             {"v19:p1.target.exact_bullet_count": {"records_hash": "a" * 64,
                                                   "n_mutations": 1000,
                                                   "distinct_texts": 1000}})


def test_an_empty_battery_is_not_evidence():
    with pytest.raises(DomainError, match="non-empty"):
        validate("boundary_mutations", {})


# ------------------------------------------------------------ tier 1 certificates
def test_a_certificate_set_missing_a_unit_is_refused():
    from dci.v19 import pairs
    complete = stand_in.tier1_certificates()
    validate("tier1_certificates", complete)
    partial = dict(complete)
    partial.pop(pairs.PAIR_1.target.constraint_id)
    with pytest.raises(DomainError, match="no Tier-1 certificate"):
        validate("tier1_certificates", partial)


def test_a_certificate_with_an_unavailable_truth_class_is_refused():
    from dci.v19 import pairs
    records = stand_in.tier1_certificates()
    records[pairs.PAIR_1.target.constraint_id] = {"passed": True,
                                                  "unavailable": ["true_passes"]}
    with pytest.raises(DomainError, match="missing denominator is missing evidence"):
        validate("tier1_certificates", records)


def test_a_failing_certificate_is_not_a_certificate():
    from dci.v19 import pairs
    records = stand_in.tier1_certificates()
    records[pairs.PAIR_1.target.constraint_id] = {"passed": False,
                                                  "unavailable": []}
    with pytest.raises(DomainError, match="does not record a pass"):
        validate("tier1_certificates", records)
