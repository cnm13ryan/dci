"""The Stage 1-17 dependency DAG: no stage may run ahead of its inputs.

Section 14 makes the ordering mandatory - "A later stage may consume frozen
outputs from earlier stages; it may not retrospectively change them" - so the
gate is the executable form of a protocol requirement, not a convenience.

The defect this file exists to prevent was concrete. Stage 15 declared four
configuration slots and nothing else, so freezing those four made confirmatory
generation report READY while every confirmation pool was unauthored, no
reference was admitted, and no generation manifest existed anywhere in the
registry. Section 14.15 permits execution of ONLY the frozen generation manifest,
so the gate authorised precisely what the protocol forbids.

Every test here therefore asks the same question in a different place: can this
stage become READY while something the preregistration requires is unresolved?
"""
import pytest
from v19_domain_values import for_domain

from dci.v19 import PROTOCOL_VERSION, artifacts, registry
from dci.v19.pairs import PAIR_IDS
from dci.v19.registry import (
    MANDATORY_STAGE_ORDINALS,
    REGISTRY,
    STAGE_GATES,
    Registry,
    Requirement,
)
from dci.v19.resolution import Resolution, UnresolvedDependency

pytestmark = pytest.mark.cpu


def advanced(*names, base=None):
    """A registry with the named slots frozen by a probe. Nothing else changes."""
    table = base if base is not None else REGISTRY.slots
    for name in names:
        table = table.freeze(name, f"probe:{name}", by="probe")
    return Registry(protocol=PROTOCOL_VERSION, slots=table)


def all_upstream_of(stage, table=None):
    """Transitively freeze everything `stage` needs, and everything they need."""
    table = table if table is not None else REGISTRY.slots
    frontier = list(REGISTRY.gate(stage).required_slots)
    seen = set()
    while frontier:
        name = frontier.pop()
        if name in seen:
            continue
        seen.add(name)
        slot = table[name]
        frontier.extend(slot.depends_on)
        if not slot.resolved:
            # A value its own domain admits. Slots are typed now, so "probe:<name>"
            # would be refused - which is the S11 repair working, not an obstacle.
            table = table.freeze(name, for_domain(slot.domain), by="probe")
    return Registry(protocol=PROTOCOL_VERSION, slots=table)


# --------------------------------------------------- every mandatory stage exists
def test_the_complete_preregistered_stage_sequence_has_a_gate():
    """The meta-test: 2A, 14, 16 and 17 were absent entirely before this."""
    assert tuple(g.ordinal for g in STAGE_GATES) == MANDATORY_STAGE_ORDINALS
    assert len(STAGE_GATES) == 18


@pytest.mark.parametrize("ordinal", MANDATORY_STAGE_ORDINALS)
def test_each_mandatory_stage_is_represented(ordinal):
    assert sum(1 for g in STAGE_GATES if g.ordinal == ordinal) == 1


def test_the_stages_are_declared_in_protocol_order():
    """Order carries meaning: section 14's sequence is the dependency order."""
    ordinals = [g.ordinal for g in STAGE_GATES]
    assert ordinals.index("2A") == ordinals.index("2") + 1
    assert ordinals.index("15") > ordinals.index("14") > ordinals.index("13")
    assert ordinals.index("17") > ordinals.index("16") > ordinals.index("15")


def test_every_stage_key_and_title_is_distinct():
    assert len({g.key for g in STAGE_GATES}) == len(STAGE_GATES)
    assert len({g.title for g in STAGE_GATES}) == len(STAGE_GATES)


# ------------------------------------------------------- every edge is auditable
def test_every_dependency_edge_carries_a_preregistration_citation():
    for gate in STAGE_GATES:
        for requirement in gate.requires:
            assert requirement.citation, f"{gate.key} -> {requirement.slot}"
            assert ("section" in requirement.citation
                    or requirement.citation.startswith("D")), requirement.citation


def test_an_uncited_dependency_cannot_be_constructed():
    with pytest.raises(ValueError, match="needs a preregistration citation"):
        Requirement(slot="exact_epsilon", citation="")


def test_every_stage_cites_its_own_definition():
    for gate in STAGE_GATES:
        assert gate.citation.startswith("section 14."), gate.key


def test_every_required_slot_is_actually_declared():
    """A gate naming a slot that does not exist would raise, not pass."""
    names = {s.name for s in REGISTRY.slots}
    for gate in STAGE_GATES:
        for slot in gate.required_slots:
            assert slot in names, f"{gate.key} requires undeclared {slot}"


def test_every_produced_slot_is_actually_declared():
    names = {s.name for s in REGISTRY.slots}
    for gate in STAGE_GATES:
        for slot in gate.produces:
            assert slot in names, f"{gate.key} claims to produce undeclared {slot}"


def test_a_slot_is_produced_by_at_most_one_stage():
    """Two stages producing one artifact would make its provenance ambiguous."""
    seen: dict[str, str] = {}
    for gate in STAGE_GATES:
        for slot in gate.produces:
            assert slot not in seen, f"{slot} produced by {seen.get(slot)} and {gate.key}"
            seen[slot] = gate.key


def test_the_citation_lookup_explains_why_a_stage_is_blocked():
    why = REGISTRY.citation_for("stage_15_confirmatory_generation",
                                "manifest.generation_manifest")
    assert "14.15" in why and "ONLY the frozen generation manifest" in why
    with pytest.raises(KeyError, match="does not declare a dependency"):
        REGISTRY.citation_for("stage_15_confirmatory_generation", "design.alpha")


def test_the_blocker_report_says_why_each_edge_exists():
    row = REGISTRY.stage_status("stage_15_confirmatory_generation")
    assert row["ordinal"] == "15"
    for blocker in row["blockers"]:
        assert blocker["why_required"]


# ------------------------------------------------ Stage 15: the reported defect
def test_stage_fifteen_is_not_ready_on_the_old_four_slots():
    """The exact reproduction: these four used to be the whole gate."""
    got = advanced("runtime.certified_gpu_class", "inference.selected_method",
                   "budget.retained_set", "controller.final_answer_allowance_v")
    assert got.stage_status("stage_15_confirmatory_generation")["status"] != "READY"
    with pytest.raises(UnresolvedDependency):
        got.require_stage("stage_15_confirmatory_generation")


def test_stage_fifteen_requires_the_generation_manifest():
    """Section 14.15: 'Execute only the frozen generation manifest.'"""
    assert "manifest.generation_manifest" in \
        REGISTRY.gate("stage_15_confirmatory_generation").required_slots


def test_stage_fifteen_requires_the_signed_final_freeze():
    """Section 14.14 records that no output predates the signed timestamp."""
    assert "freeze.root_signature" in \
        REGISTRY.gate("stage_15_confirmatory_generation").required_slots


def test_stage_fifteen_is_rejected_without_the_signature():
    got = advanced("manifest.generation_manifest", "runtime.certified_gpu_class")
    with pytest.raises(UnresolvedDependency, match="freeze.root_signature"):
        got.require_stage("stage_15_confirmatory_generation")


def test_stage_fifteen_is_rejected_without_the_manifest():
    got = advanced("freeze.root_signature", "runtime.certified_gpu_class")
    with pytest.raises(UnresolvedDependency, match="manifest.generation_manifest"):
        got.require_stage("stage_15_confirmatory_generation")


def test_the_signature_cannot_be_reached_without_unresolved_references():
    """The aggregate must be fail-closed on its primitives, or it is indirection.

    Freezing the signature directly is a probe, not a workflow; what matters is
    that its own declared dependency chain reaches the reference identities, the
    manifest and recertification.
    """
    chain = set()
    frontier = ["freeze.root_signature"]
    while frontier:
        name = frontier.pop()
        if name in chain:
            continue
        chain.add(name)
        frontier.extend(REGISTRY.slots[name].depends_on)
    for required in ("manifest.generation_manifest", "manifest.root_hash",
                     "recertification.stage13", "qualification.stage2a",
                     "design.final_h_p", "design.replicates_g",
                     "verifiers.bundle_hash", "falsification.battery"):
        assert required in chain, required
    for pair in PAIR_IDS:
        for i in range(1, 5):
            assert f"reference.{pair}.R{i}" in chain
        assert f"bank.{pair}.accepted_order" in chain
        assert f"parameters.{pair}.distribution" in chain


def test_stage_fifteen_becomes_ready_only_with_the_whole_chain():
    got = all_upstream_of("stage_15_confirmatory_generation")
    got.require_stage("stage_15_confirmatory_generation")
    assert got.stage_status("stage_15_confirmatory_generation")["status"] == "READY"
    # The unmodified registry is untouched.
    assert REGISTRY.blockers_for("stage_15_confirmatory_generation")


# ------------------------------------- the analogous omissions found by audit
@pytest.mark.parametrize("stage,slot,why", [
    ("stage_3_runtime_freeze", "qualification.stage2a",
     "section 9.4 precondition 2: the Stage 2A suite must pass before ranking"),
    ("stage_5_parameter_calibration", "budget.retained_set",
     "section 6.2: the screen applies under every retained budget"),
    ("stage_6_reference_eligibility", "verifiers.bundle_hash",
     "section 14.2: the verifier gates need the verifiers"),
    ("stage_6_reference_eligibility", "exact_epsilon",
     "section 14.6: epsilon/8 expansion needs exact epsilon frozen first"),
    ("stage_7_wording", "eligibility.p1.hard_gates",
     "section 14.7 certifies wordings for surviving candidates"),
    ("stage_8_reference_admission", "coupling.p1.audit",
     "section 14.8 ranks only already-eligible candidates"),
    ("stage_8_reference_admission", "wording.p1.instability",
     "section 14.8 consumes the wording outcome"),
    ("stage_9_method_selection", "reference.p1.R1",
     "section 13.1: comparison occurs after references are frozen"),
    ("stage_10_attainable_bank", "pool.p1.backgrounds.lexical_content",
     "section 8.3 step 2 draws one identity from each stratum"),
    ("stage_10_attainable_bank", "parameters.p1.distribution",
     "section 8.3 step 3 draws parameters from the frozen nu_Q"),
    ("stage_11_design_simulation", "bank.p1.attainable_count",
     "section 14.11 evaluates only attainable designs"),
    ("stage_11_design_simulation", "runtime.cost_model",
     "section 14.11 uses the measured runtime-cost model"),
    ("stage_12_freeze", "design.final_h_p",
     "section 14.12 freezes the final H_p"),
    ("stage_12_freeze", "matching.p1.constants",
     "section 14.12 freezes the matching constants"),
    ("stage_12_freeze", "bank.p1.accepted_order",
     "section 14.12 selects under the frozen bank order"),
    ("stage_13_recertification", "manifest.root_hash",
     "section 14.13 re-runs the manifest fail-closed tests"),
    ("stage_13_recertification", "qualification.stage2a",
     "section 14.13 compares all hashes to the Stage 2A baseline"),
    ("stage_14_freeze_signing", "recertification.stage13",
     "section 14.13: any failure blocks confirmation"),
    ("stage_16_locked_inference", "freeze.root_signature",
     "section 14.16 runs the preselected analysis after the freeze"),
    ("stage_17_terminal_falsification", "analysis.confirmatory_outputs",
     "section 14.17 opens the material only after outputs are locked"),
])
def test_each_audited_dependency_is_now_encoded(stage, slot, why):
    gate = REGISTRY.gate(stage)
    assert slot in gate.required_slots, f"{stage} must require {slot}: {why}"
    assert REGISTRY.citation_for(stage, slot)


@pytest.mark.parametrize("gate", [g.key for g in STAGE_GATES
                                  if g.key != "stage_1_definitions"])
def test_no_stage_is_ready_with_any_single_prerequisite_removed(gate):
    """Freeze everything the stage needs except one, and it must stay blocked."""
    required = REGISTRY.gate(gate).required_slots
    # Hold back the first prerequisite that is not ALREADY resolved: a slot a
    # recorded amendment fixes cannot be withheld, and asking the test to withhold
    # one would be asking it to unfreeze a frozen commitment.
    pending = [name for name in required if not REGISTRY.slots[name].resolved]
    if not pending:                                # pragma: no cover - all fixed
        pytest.skip(f"every prerequisite of {gate} is already fixed")
    held_back = pending[0]
    table = REGISTRY.slots
    for name in required:
        if name == held_back or table[name].resolved:
            continue
        table = table.freeze(name, for_domain(table[name].domain), by="probe")
    got = Registry(protocol=PROTOCOL_VERSION, slots=table)
    assert got.stage_status(gate)["status"] != "READY"
    with pytest.raises(UnresolvedDependency, match=held_back.replace(".", r"\.")):
        got.require_stage(gate)


# ------------------------------------------------- the newly declared artifacts
@pytest.mark.parametrize("name", [
    "qualification.stage2a", "verifiers.bundle_hash",
    "verifiers.tier1_reliability",
    "verifiers.boundary_mutations", "matching.p1.constants",
    "parameters.p1.admissible_set", "parameters.p1.distribution",
    "eligibility.p1.hard_gates", "coupling.p1.audit", "wording.p1.instability",
    "validation.p1.independent", "bank.p1.attainable_count",
    "bank.p1.accepted_order", "design.final_h_p", "design.replicates_g",
    "simulation.method_comparison", "simulation.authoritative_design",
    "simulation.counterfactual_diagnostic", "runtime.cost_model",
    "manifest.generation_manifest", "manifest.root_hash",
    "recertification.stage13", "freeze.root_signature",
    "ledger.terminal_states", "analysis.code_hash",
    "analysis.confirmatory_outputs", "falsification.result",
])
def test_every_new_artifact_is_declared_and_unresolved(name):
    slot = REGISTRY.slots[name]
    assert not slot.resolved, f"{name} must not ship with a value"
    assert slot.rule and slot.prereg


def test_the_new_artifacts_exist_for_every_pair():
    for pair in PAIR_IDS:
        for template in ("parameters.{p}.admissible_set",
                         "parameters.{p}.distribution",
                         "matching.{p}.constants", "bank.{p}.attainable_count",
                         "bank.{p}.accepted_order", "coupling.{p}.audit",
                         "wording.{p}.instability", "eligibility.{p}.hard_gates",
                         "validation.{p}.independent"):
            assert template.format(p=pair) in {s.name for s in REGISTRY.slots}


def test_the_artifact_module_declares_nothing_resolved():
    """Implemented is not accepted, and the declaration must not blur the two.

    Amendments A1-A4 are implemented, domain-validated and exhaustively tested,
    and the declaration still says PENDING_DECISION for every one of them. What
    makes a decision accepted is an acceptance RECORD naming who accepted it and
    when - never the presence of a candidate in the source, which would let the
    implementation treat a scientific decision as made before the investigator
    made it.
    """
    assert not artifacts.declared_slots().resolved()


def test_the_four_amendments_are_declared_as_decisions_with_domains():
    amended = {"verifiers.p1.list_policy", "verifiers.p1.ordering_depth",
               "verifiers.inherited_reuse_decision",
               "verifiers.binomial_interval_implementation",
               "verifiers.tier1_audit_design"}
    table = artifacts.declared_slots()
    for name in sorted(amended):
        slot = table[name]
        assert slot.resolution is Resolution.PENDING_DECISION, name
        assert slot.domain, name
        assert not slot.resolved, name


def test_acceptance_arrives_only_through_a_signed_record():
    """The same slots ARE resolved once the recorded acceptances are applied."""
    from dci.v19 import frozen
    accepted = {row["slot"] for row in frozen.audit()}
    declared = artifacts.declared_slots()
    for name in sorted(accepted):
        assert not declared[name].resolved, f"{name} was resolved before its record"
    applied = frozen.apply(registry.declared_table())
    for name in sorted(accepted):
        assert applied[name].resolved, name
        assert applied[name].frozen_by, name


def test_every_acceptance_record_names_who_accepted_it_and_on_what_evidence():
    from dci.v19 import frozen
    rows = frozen.audit()
    assert rows, "no acceptance has been recorded"
    for row in rows:
        assert row["frozen_by"].strip(), row["slot"]
        assert row["recorded_at"].strip(), row["slot"]
        assert len(row["evidence"]) > 200, (row["slot"], "evidence is a stub")

def test_the_counterfactual_diagnostic_is_disclosure_only():
    """Section 13.7: it cannot reopen Stage 9 or change the design."""
    note = REGISTRY.slots["simulation.counterfactual_diagnostic"].note
    assert "cannot reopen Stage 9" in note


def test_the_freeze_signature_is_a_prospective_decision():
    """Signing is an act, not a computation, so no procedure can produce it."""
    assert REGISTRY.slots["freeze.root_signature"].status == \
        "BLOCKED_BY_PROSPECTIVE_DECISION"


def test_recertification_records_that_failure_blocks_confirmation():
    note = REGISTRY.slots["recertification.stage13"].note
    assert "blocks confirmation" in note
    assert "does not license" in note


def test_the_registry_now_reports_every_stage():
    audit = REGISTRY.audit()
    assert len(audit) == 18
    assert [row["ordinal"] for row in audit] == list(MANDATORY_STAGE_ORDINALS)
    blocked = [row for row in audit if row["status"] != "READY"]
    assert len(blocked) == 17            # only Stage 1 has no prerequisite
