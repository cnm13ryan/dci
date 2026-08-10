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
import dataclasses

import pytest

from dci.v19 import artifacts, pairs, reliability, stage2, verifiers
from dci.v19.parsing import INHERITED_MARKER_POLICY as P
from dci.v19.registry import REGISTRY, STAGE_GATE_BY_KEY
from dci.v19.resolution import Resolution, UnresolvedDependency
from dci.v19.verifiers import VerifierContractError

pytestmark = pytest.mark.cpu

STAGE = "stage_2_verifiers"
DECISIONS = ("verifiers.p1.list_policy", "verifiers.p1.ordering_depth",
             "verifiers.inherited_reuse_decision",
             "verifiers.binomial_interval_implementation")
FULL_MUTATIONS = {rule.constraint_id: stage2.MUTATIONS_PER_TEMPLATE
                  for rule in pairs.rules()}


def all_frozen():
    """A registry slot table with every Stage 2 decision recorded."""
    slots = REGISTRY.slots
    for name, value in [("verifiers.p1.list_policy", P),
                        ("verifiers.p1.ordering_depth",
                         {"domain": [2, 3, 4], "harder": "increasing"}),
                        ("verifiers.inherited_reuse_decision",
                         {"disposition": "reused_unchanged"}),
                        ("verifiers.binomial_interval_implementation",
                         "wilson_score")]:
        slots = slots.freeze(name, value, by="a signed Stage 2 decision")
    return slots


# ------------------------------------------------------------ the declarations
def test_the_four_open_decisions_are_declared_and_pending():
    for name in DECISIONS:
        slot = REGISTRY.slots[name]
        assert slot.resolution is Resolution.PENDING_DECISION, name
        assert slot.status == "BLOCKED_BY_PROSPECTIVE_DECISION", name
        assert slot.rule and slot.prereg


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
        "verifiers.binomial_interval_implementation", "verifiers.bundle_hash"}


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
def test_the_stage_two_gate_requires_all_four_decisions_and_the_mutations():
    gate = STAGE_GATE_BY_KEY[STAGE]
    assert set(gate.required_slots) == set(DECISIONS) | {
        "verifiers.boundary_mutations"}
    for slot in gate.required_slots:
        assert REGISTRY.citation_for(STAGE, slot)


def test_the_stage_two_gate_produces_the_three_artifacts_it_owns():
    assert set(STAGE_GATE_BY_KEY[STAGE].produces) == {
        "verifiers.specification_bundle", "verifiers.bundle_hash",
        "verifiers.tier1_reliability"}


def test_stage_two_is_blocked_and_the_root_cause_is_a_decision():
    row = REGISTRY.stage_status(STAGE)
    assert row["status"] == "BLOCKED_BY_PROSPECTIVE_DECISION"
    assert row["root_blocker"] == "BLOCKED_BY_PROSPECTIVE_DECISION"
    assert len(row["blockers"]) == row["n_required"] == 5


def test_require_stage_lists_every_blocker_at_once():
    with pytest.raises(UnresolvedDependency) as caught:
        REGISTRY.require_stage(STAGE)
    message = str(caught.value)
    for name in DECISIONS + ("verifiers.boundary_mutations",):
        assert name in message
    assert "5 unresolved" in message


def test_stage_two_is_not_ready_merely_because_the_pair_one_code_exists():
    """The whole point of the layer: implementation is not certification."""
    assert len(verifiers.assert_bundle_is_complete(P)) == 6
    assert REGISTRY.stage_status(STAGE)["status"] != "READY"


# ------------------------------------------------------------- certification
def test_certification_fails_closed_before_any_decision_is_made():
    report = stage2.certify_verifiers(REGISTRY.slots)
    assert not report.certified
    assert len(report.outstanding) == len(report.findings) == 6
    for finding in report.findings:
        assert finding.citation and finding.detail


def test_the_bundle_finding_explains_why_it_cannot_even_be_evaluated():
    report = stage2.certify_verifiers(REGISTRY.slots)
    bundle = next(f for f in report.findings if "bound to a hash" in f.requirement)
    assert not bundle.satisfied
    assert "no identity until the policy is frozen" in bundle.detail
    assert "implementation exists and is tested" in bundle.detail


def test_certification_passes_only_when_every_requirement_holds():
    report = stage2.certify_verifiers(all_frozen(), mutation_counts=FULL_MUTATIONS)
    assert report.certified
    assert not report.outstanding
    assert stage2.assert_verifiers_certified(
        all_frozen(), mutation_counts=FULL_MUTATIONS) is not None


@pytest.mark.parametrize("withheld", DECISIONS)
def test_withholding_any_one_decision_blocks_certification(withheld):
    """Six requirements, each individually load-bearing."""
    slots = REGISTRY.slots
    for name, value in [("verifiers.p1.list_policy", P),
                        ("verifiers.p1.ordering_depth", {"domain": [2]}),
                        ("verifiers.inherited_reuse_decision", "reused"),
                        ("verifiers.binomial_interval_implementation",
                         "wilson_score")]:
        if name != withheld:
            slots = slots.freeze(name, value, by="test")
    report = stage2.certify_verifiers(slots, mutation_counts=FULL_MUTATIONS)
    assert not report.certified
    assert any(withheld in f.detail for f in report.outstanding)


def test_absent_mutation_evidence_is_not_a_zero_defect_result():
    assert not stage2.certify_verifiers(all_frozen()).certified
    report = stage2.certify_verifiers(all_frozen(), mutation_counts=None)
    mutations = next(f for f in report.findings if "boundary mutations"
                     in f.requirement)
    assert "an absent count is not a zero-defect result" in mutations.detail


def test_an_empty_mutation_mapping_names_every_short_template():
    report = stage2.certify_verifiers(all_frozen(), mutation_counts={})
    mutations = next(f for f in report.findings if "boundary mutations"
                     in f.requirement)
    assert "6 template(s) below the floor" in mutations.detail
    for rule in pairs.rules():
        assert rule.constraint_id in mutations.detail


@pytest.mark.parametrize("shortfall", [1, 500, 999])
def test_one_mutation_below_the_floor_blocks_certification(shortfall):
    counts = dict(FULL_MUTATIONS)
    first = pairs.PAIR_1.target.constraint_id
    counts[first] = stage2.MUTATIONS_PER_TEMPLATE - shortfall
    assert not stage2.certify_verifiers(all_frozen(),
                                       mutation_counts=counts).certified


def test_the_mutation_floor_is_the_one_section_eight_seven_states():
    assert stage2.MUTATIONS_PER_TEMPLATE == 1_000


def test_a_frozen_policy_of_the_wrong_type_is_refused_not_coerced():
    slots = all_frozen().slots
    replaced = tuple(
        dataclasses.replace(s, value={"policy_id": "x"}) if
        s.name == "verifiers.p1.list_policy" else s for s in slots)
    from dci.v19.resolution import SlotTable
    report = stage2.certify_verifiers(SlotTable(slots=replaced),
                                      mutation_counts=FULL_MUTATIONS)
    bundle = next(f for f in report.findings if "bound to a hash" in f.requirement)
    assert not bundle.satisfied and "not a ListPolicy" in bundle.detail


def test_the_assertion_reports_every_outstanding_requirement_with_its_citation():
    with pytest.raises(VerifierContractError) as caught:
        stage2.assert_verifiers_certified(REGISTRY.slots)
    message = str(caught.value)
    assert "6 of 6 requirements are unmet" in message
    assert "section 10.4" in message and "section 8.7" in message


def test_the_certification_report_is_serialisable():
    import json
    described = stage2.certify_verifiers(REGISTRY.slots).describe()
    json.dumps(described)
    assert described["certified"] is False
    assert described["n_outstanding"] == len(described["findings"])


def test_a_certification_with_no_findings_is_not_certified():
    """Vacuous truth would make an empty check look like a passing one."""
    assert not stage2.Certification(findings=()).certified


# ------------------------------------------------------ the reported blockers
def test_the_open_decisions_are_reported_from_the_code_not_retyped():
    rows = stage2.open_scientific_decisions()
    assert {row["decision"] for row in rows} == set(DECISIONS)
    for row in rows:
        assert row["governing_text"] and row["minimum_decision"]
        assert row["open_questions"]


def test_the_list_policy_row_carries_all_eleven_open_questions():
    from dci.v19.parsing import UNDETERMINED_BY_PREREGISTRATION
    row = next(r for r in stage2.open_scientific_decisions()
               if r["decision"] == "verifiers.p1.list_policy")
    assert row["open_questions"] == dict(UNDETERMINED_BY_PREREGISTRATION)
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
def test_no_stage_two_decision_ships_with_a_value():
    for name in DECISIONS:
        slot = REGISTRY.slots[name]
        assert slot.pending
        with pytest.raises(UnresolvedDependency):
            slot.get()


def test_the_registry_still_reports_nothing_fabricated():
    from dci.v19 import registry
    registry.assert_nothing_fabricated()


def test_the_new_slots_did_not_disturb_the_other_stages():
    """Only Stage 2 gained requirements; every other gate is unchanged."""
    audit = {row["stage"]: row for row in REGISTRY.audit()}
    assert audit[STAGE]["n_required"] == 5
    assert audit["stage_1_definitions"]["status"] == "READY"
    ready = [row["stage"] for row in REGISTRY.audit()
             if row["status"] == "READY"]
    assert ready == ["stage_1_definitions"]
