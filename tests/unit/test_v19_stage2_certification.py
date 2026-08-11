"""Stage 2 certification: code existing is not the same as a stage being ready.

Four things stay distinct, and section 14.2 needs all four:

    code exists  !=  artifact certified  !=  slot frozen  !=  stage READY

The Pair 1 verifiers exist, are hashed and are exhaustively tested. Stage 2 is
still blocked, because the *measurement decision* underneath them - which list
policy is frozen - is one the preregistration does not make and code must not.

Every check below is written so that removing any single requirement makes
certification pass when it should not, which is the only way to know the gate is
load-bearing rather than decorative.
"""

import pytest
import v19_domain_values as stand_in

from dci.v19 import artifacts, reliability, stage2, verifiers
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.registry import REGISTRY, STAGE_GATE_BY_KEY
from dci.v19.resolution import Resolution, UnresolvedDependency
from dci.v19.verifiers import VerifierContractError

pytestmark = pytest.mark.cpu

STAGE = "stage_2_verifiers"

# What Stage 2 amendments A1-A3 fix, and what they deliberately do not.
# Amendments A1-A4, each accepted by a recorded acceptance rather than declared.
ACCEPTED = ("verifiers.p1.list_policy", "verifiers.p1.ordering_depth",
            "verifiers.inherited_reuse_decision",
            "verifiers.binomial_interval_implementation",
            "verifiers.tier1_audit_design")
# The verifier half is now blocked only on the section 8.7 battery, whose harness
# lands with the satisfiability layer.
# Stage 2's gate is now fully satisfied: every decision is accepted and every
# artifact it owns has been produced. What remains outstanding at CERTIFICATION is
# the Tier-1 reliability audit, which is 864 human-adjudicated labels and cannot be
# produced by code.
STILL_OPEN = ()
GATE_BLOCKERS = STILL_OPEN
TRIGGER = "satisfiability.review_trigger"


def all_frozen():
    """A slot table with every Stage 2 prerequisite recorded, values and all.

    Each value comes from `v19_domain_values`, which supplies something the slot's own
    typed domain admits. Freezing the string "probe" everywhere - what this helper used
    to do - is exactly what the S11 repair now refuses.
    """
    watched = [s.name for s in REGISTRY.slots
               if s.name.startswith("verifiers.")]
    return stand_in.resolve(REGISTRY.slots, *watched)


# ------------------------------------------------------------ the declarations
def test_the_amendments_are_accepted_by_record_not_by_declaration():
    """FROZEN, not FIXED, and that difference is the whole point.

    FIXED means the preregistration fixes it directly. These five are decisions
    the protocol leaves open or answers inconsistently; each is FROZEN by an
    acceptance record naming who accepted it and on what evidence. Declaring them
    FIXED would have the implementation treating a scientific decision as made
    before the investigator made it.
    """
    for name in ACCEPTED:
        slot = REGISTRY.slots[name]
        assert slot.resolution is Resolution.FROZEN, name
        assert slot.frozen_by, name
        assert slot.domain, name


def test_the_declaration_alone_still_leaves_every_amendment_open():
    from dci.v19 import registry
    declared = registry.declared_table()
    for name in ACCEPTED:
        slot = declared[name]
        assert slot.resolution is Resolution.PENDING_DECISION, name
        assert not slot.resolved, name
        assert slot.status == "BLOCKED_BY_PROSPECTIVE_DECISION", name


def test_ordering_depth_carries_the_construct_and_not_a_grid():
    """A4 decides what the parameter IS; section 6.2's grid stays a Stage 5 output."""
    from dci.v19 import ordering
    slot = REGISTRY.slots["verifiers.p1.ordering_depth"]
    assert slot.domain == "ordering_depth"
    value = slot.get()
    assert value["statistic"] == ordering.STATISTIC_ID
    assert value["generator"] == ordering.GENERATOR_ID
    assert value["grid"] is None and "D6" in value["grid_rule"]


def test_the_specification_bundle_waits_on_the_three_verifier_decisions():
    slot = REGISTRY.slots["verifiers.specification_bundle"]
    assert set(slot.depends_on) == {"verifiers.p1.list_policy",
                                    "verifiers.p1.ordering_depth",
                                    "verifiers.inherited_reuse_decision"}


def test_the_bundle_hash_waits_on_the_specifications_and_the_mutations():
    slot = REGISTRY.slots["verifiers.bundle_hash"]
    assert set(slot.depends_on) == {"verifiers.specification_bundle",
                                    "verifiers.boundary_mutations"}


def test_the_reliability_certificate_waits_on_the_interval_and_the_bundle():
    slot = REGISTRY.slots["verifiers.tier1_reliability"]
    assert set(slot.depends_on) == {
        "verifiers.binomial_interval_implementation",
        "verifiers.tier1_audit_design", "verifiers.tier1_audit_protocol",
        "verifiers.bundle_hash",
        "pool.p1.audit", "pool.p2.audit", "pool.p3.audit"}


def test_every_stage_two_slot_names_a_production_rule_and_a_citation():
    for slot in artifacts.VERIFIER_SLOTS:
        assert slot.rule and slot.prereg, slot.name
        assert slot.name.startswith("verifiers.")


def test_the_dependency_edges_all_name_declared_slots():
    """A depends_on pointing at nothing is a gate that cannot fail closed."""
    known = {slot.name for slot in REGISTRY.slots}
    for slot in artifacts.VERIFIER_SLOTS:
        for dependency in slot.depends_on:
            assert dependency in known, f"{slot.name} -> {dependency}"


# --------------------------------------------------------------- the stage gate
def test_the_stage_two_gate_requires_every_decision_and_the_mutations():
    gate = STAGE_GATE_BY_KEY[STAGE]
    assert set(gate.required_slots) == set(ACCEPTED) | {
        "verifiers.boundary_mutations", TRIGGER}
    for slot in gate.required_slots:
        assert REGISTRY.citation_for(STAGE, slot)


def test_the_stage_two_gate_produces_the_artifacts_it_owns():
    assert set(STAGE_GATE_BY_KEY[STAGE].produces) == {
        "verifiers.specification_bundle", "verifiers.bundle_hash",
        "verifiers.tier1_reliability", "satisfiability.encoding_map",
        "satisfiability.solver_identity", "satisfiability.witness_constructor",
        "satisfiability.review_trigger"}
    # The per-composition certificates are a Stage 10 product, not a Stage 2 one.
    assert "satisfiability.certified_compositions" in STAGE_GATE_BY_KEY[
        "stage_10_attainable_bank"].produces


def test_the_stage_two_gate_is_now_satisfied():
    """Every decision accepted, every artifact the gate requires produced."""
    row = REGISTRY.stage_status(STAGE)
    assert row["status"] == "READY"
    assert not row["blockers"]


def test_require_stage_no_longer_raises_for_stage_two():
    REGISTRY.require_stage(STAGE)


def test_require_stage_still_lists_every_blocker_at_once():
    """The fail-closed path stays live, checked on a stage that is still blocked."""
    with pytest.raises(UnresolvedDependency) as caught:
        REGISTRY.require_stage("stage_10_attainable_bank")
    message = str(caught.value)
    assert "satisfiability.semantic_reviews" in message
    assert "unresolved" in message


def test_the_gate_being_ready_is_not_the_same_as_stage_two_being_certified():
    """The distinction the whole layer exists for.

    The GATE is ready: every prerequisite slot is resolved. Stage 2 is still not
    CERTIFIED, because certification also requires the Tier-1 reliability audit -
    864 human-adjudicated labels that no amount of code can produce.
    """
    assert len(verifiers.assert_bundle_is_complete(P)) == 6
    assert REGISTRY.stage_status(STAGE)["status"] == "READY"
    assert not stage2.certify_stage2(REGISTRY.slots).certified


# ------------------------------------------------------------- certification
def test_certification_still_fails_closed_after_the_amendments():
    report = stage2.certify_stage2(REGISTRY.slots)
    assert not report.certified
    # The single outstanding requirement is human adjudication.
    assert len(report.outstanding) == 1
    assert "human-adjudicated" in report.outstanding[0].requirement
    for finding in report.findings:
        assert finding.citation and finding.detail


def test_the_bundle_finding_is_now_satisfied_under_the_frozen_grammar():
    report = stage2.certify_verifiers(REGISTRY.slots)
    bundle = next(f for f in report.findings if "bound to a hash" in f.requirement)
    assert bundle.satisfied
    assert "6 verifiers" in bundle.detail


def test_the_bundle_finding_refuses_a_grammar_the_parser_does_not_implement():
    """A registry and a parser that disagree is the one case a complete bundle is
    still the wrong evidence."""
    import dataclasses as dc

    from dci.v19.resolution import Resolution, Slot
    wrong = dc.replace(REGISTRY.slots["verifiers.p1.list_policy"],
                       domain="", value={"policy_id": "something else"})
    assert isinstance(wrong, Slot) and wrong.resolution is Resolution.FROZEN
    from dci.v19.resolution import SlotTable
    table = SlotTable(slots=tuple(
        wrong if s.name == "verifiers.p1.list_policy" else s
        for s in REGISTRY.slots))
    finding = next(f for f in stage2.certify_verifiers(table).findings
                   if "bound to a hash" in f.requirement)
    assert not finding.satisfied
    assert "does not match the implemented one" in finding.detail


def test_certification_passes_only_when_every_requirement_holds():
    report = stage2.certify_verifiers(all_frozen())
    assert report.certified, [f.detail for f in report.outstanding]
    assert not report.outstanding
    assert stage2.assert_verifiers_certified(all_frozen()) is not None


@pytest.mark.parametrize("withheld", STAGE_GATE_BY_KEY[STAGE].required_slots)
def test_withholding_any_one_requirement_blocks_certification(withheld):
    """Every requirement is individually load-bearing - the gate is not decorative.

    Rebuilt from the DECLARATION with one acceptance record left out, because the
    live registry now resolves all seven and a frozen commitment cannot be
    unfrozen. An earlier version of this test parametrised over the outstanding
    blockers, which became the empty set once Stage 2's gate was satisfied - so it
    silently stopped testing anything at all.
    """
    report = stage2.certify_stage2(stand_in.table_without(withheld))
    assert not report.certified
    assert any(withheld in f.detail or withheld in f.requirement
               for f in report.outstanding), [f.detail for f in report.outstanding]


def test_the_withholding_test_is_not_vacuous():
    """A guard on the guard: the parameter set must be non-empty."""
    assert len(STAGE_GATE_BY_KEY[STAGE].required_slots) == 7


def test_unfrozen_battery_evidence_does_not_satisfy_the_gate():
    """The harness producing enough is not the same as the record existing.

    Checked against the DECLARED table, where the battery is not yet recorded: on
    the live registry it now is, which is what makes the finding satisfied there.
    """
    from dci.v19 import registry
    finding = next(f for f in stage2.certify_verifiers(
        registry.declared_table()).findings
        if "boundary mutations" in f.requirement)
    assert not finding.satisfied
    assert "not part of the artifact trail" in finding.detail


def test_a_caller_can_no_longer_assert_the_battery():
    """`certify_verifiers` and `certify_satisfiability` take no mutation argument.

    The audit passed a hand-written summary and the gate accepted it. Both halves now
    read the same regenerated battery, so there is nothing to pass.
    """
    import inspect
    for function in (stage2.certify_verifiers, stage2.assert_verifiers_certified):
        parameters = set(inspect.signature(function).parameters) - {"slots"}
        assert not parameters, (function.__name__, parameters)


def test_the_mutation_floor_is_the_one_section_eight_seven_states():
    assert stage2.MUTATIONS_PER_TEMPLATE == 1_000


@pytest.mark.parametrize("name,bad", [
    ("verifiers.p1.ordering_depth", None),
    ("verifiers.p1.ordering_depth", {"grid": [2, 3], "harder_direction": "increasing",
                                     "definition": "x"}),
    ("verifiers.p1.ordering_depth", {"statistic": "v19:ordering-depth.edge-count"}),
    ("verifiers.bundle_hash", "0" * 64),
    ("verifiers.specification_bundle", {"protocol": "v19"}),
    ("verifiers.tier1_reliability", {"unit": {"passed": False}}),
    ("verifiers.tier1_audit_design", {"n_per_truth_class": 110}),
    ("verifiers.boundary_mutations", {"not-a-real-template": {"n_mutations": 1000}}),
])
def test_a_nonsense_value_is_refused_where_it_is_recorded(name, bad):
    """S11: populated is not validated. Every one of these froze silently before.

    Applied to the DECLARED table, because an accepted slot refuses to be
    re-frozen at all - which is a different guarantee, checked separately.
    """
    from dci.v19 import registry
    with pytest.raises(ValueError, match="not admissible for domain"):
        registry.declared_table().freeze(name, bad, by="an adversarial probe")


@pytest.mark.parametrize("name", ACCEPTED)
def test_an_accepted_decision_cannot_be_re_frozen_at_all(name):
    """Section 14: a later stage may consume a frozen output, not change it."""
    from dci.v19.resolution import AlreadyFrozen
    with pytest.raises(AlreadyFrozen):
        REGISTRY.slots.freeze(name, stand_in.for_domain(REGISTRY.slots[name].domain),
                              by="an adversarial probe")


def test_the_assertion_reports_every_outstanding_requirement_with_its_citation():
    with pytest.raises(VerifierContractError) as caught:
        stage2.assert_verifiers_certified(REGISTRY.slots)
    message = str(caught.value)
    assert "1 of " in message and "requirements are unmet" in message
    assert "section 10.4" in message   # the one outstanding requirement
    assert "Stage 2 certification is incomplete" in message


def test_the_certification_report_is_serialisable():
    import json
    described = stage2.certify_verifiers(REGISTRY.slots).describe()
    json.dumps(described)
    assert described["certified"] is False
    assert 0 < described["n_outstanding"] < len(described["findings"])


def test_a_certification_with_no_findings_is_not_certified():
    """Vacuous truth would make an empty check look like a passing one."""
    assert not stage2.Certification(findings=()).certified


# ------------------------------------------------------ the reported blockers
def test_the_open_decisions_are_reported_from_the_code_not_retyped():
    rows = stage2.open_scientific_decisions()
    assert {row["decision"] for row in rows} == set(ACCEPTED) - {"verifiers.tier1_audit_design"}
    for row in rows:
        assert row["governing_text"] and row["minimum_decision"]


def test_the_list_policy_row_now_records_answers_rather_than_questions():
    from dci.v19.parsing import RESOLVED_BY_AMENDMENT
    row = next(r for r in stage2.open_scientific_decisions()
               if r["decision"] == "verifiers.p1.list_policy")
    assert row["open_questions"] == {}
    assert row["resolved_by_amendment"] == dict(RESOLVED_BY_AMENDMENT)
    assert "LIST_MARKER" in row["what_is_recoverable"]


def test_the_interval_row_carries_the_recovered_conflict():
    row = next(r for r in stage2.open_scientific_decisions()
               if r["decision"] == "verifiers.binomial_interval_implementation")
    assert row["what_is_recoverable"] == "wilson_score"
    assert row["open_questions"]["conflict"] == (
        reliability.recover_inherited_interval()["conflict"])
    assert "D9" in row["open_questions"]["register_row"]


def test_the_reuse_row_names_the_three_demonstrated_defects():
    row = next(r for r in stage2.open_scientific_decisions()
               if r["decision"] == "verifiers.inherited_reuse_decision")
    assert set(row["open_questions"]) == {"pair_2_uniqueness",
                                          "pair_2_mandatory_words",
                                          "pair_3_segmentation"}


def test_the_open_decisions_are_serialisable():
    import json
    json.dumps(stage2.open_scientific_decisions())


# ----------------------------------------------------- nothing was fabricated
def test_no_unresolved_stage_two_decision_ships_with_a_value():
    for name in STILL_OPEN:
        slot = REGISTRY.slots[name]
        assert slot.pending
        with pytest.raises(UnresolvedDependency):
            slot.get()


def test_the_registry_still_reports_nothing_fabricated():
    from dci.v19 import registry
    registry.assert_nothing_fabricated()


def test_the_new_slots_did_not_disturb_the_other_stages():
    """Stages 1 and 2 are ready; every later gate is still blocked."""
    audit = {row["stage"]: row for row in REGISTRY.audit()}
    assert audit[STAGE]["n_required"] == 7
    assert audit["stage_1_definitions"]["status"] == "READY"
    ready = [row["stage"] for row in REGISTRY.audit()
             if row["status"] == "READY"]
    assert ready == ["stage_1_definitions", "stage_2_verifiers"]


def test_stage_ten_gained_the_review_requirement_stage_two_gave_up():
    """The boundary correction, seen from the gate that received it."""
    row = {r["stage"]: r for r in REGISTRY.audit()}["stage_10_attainable_bank"]
    assert row["status"] != "READY"
    assert "satisfiability.semantic_reviews" in {
        b["name"] for b in row["blockers"]}
