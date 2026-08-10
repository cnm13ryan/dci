"""The assembled Stage 1 registry and its executable stage-dependency order.

Section 14.1 lists what Stage 1 freezes. Section 14 then makes the dependency
order mandatory: "A later stage may consume frozen outputs from earlier stages;
it may not retrospectively change them." STAGE_DEPENDENCIES is that ordering in
executable form, so `require_stage` refuses before a stage runs and the
completion audit reports blockers from the same declarations the gate reads
rather than from a hand-maintained list.
"""
import json

import pytest

from dci.v19 import PROTOCOL_VERSION, registry
from dci.v19.identity import ARMS, LOADS, ORDERS
from dci.v19.registry import (BLOCKER_PRECEDENCE, REGISTRY, STAGE_DEPENDENCIES,
                              Registry)
from dci.v19.resolution import SlotTable, UnresolvedDependency, fixed

pytestmark = pytest.mark.cpu


# ------------------------------------------------------------ the assembly
def test_stage_one_declares_everything_section_fourteen_one_lists():
    registry.assert_stage_one_complete()


def test_the_registry_assembles_every_declaring_module():
    from dci.v19 import pairs, pools, specs
    names = {s.name for s in REGISTRY.slots}
    assert {s.name for s in pairs.declared_slots()} <= names
    assert {s.name for s in pools.declared_slots()} <= names
    assert {s.name for s in specs.declared_slots()} <= names


def test_two_modules_cannot_claim_the_same_slot():
    """Merging refuses collisions, so one declaration cannot silently win."""
    with pytest.raises(ValueError, match="declared twice"):
        REGISTRY.slots.merged(SlotTable.of(fixed("exact_epsilon", "D27", 0.06)))


def test_the_fixed_design_matches_the_preregistration():
    assert REGISTRY.protocol == PROTOCOL_VERSION
    assert REGISTRY.slots.value("design.n_pairs") == 3
    assert REGISTRY.slots.value("design.n_references_per_pair") == 4
    assert REGISTRY.slots.value("design.loads") == LOADS == (2, 5)
    assert REGISTRY.slots.value("design.orders") == ORDERS
    assert REGISTRY.slots.value("design.arms") == ARMS
    assert REGISTRY.slots.value("design.primitive_support") == (-1.0, 1.0)
    assert REGISTRY.slots.value("design.secondary_support") == (-2.0, 2.0)
    assert REGISTRY.slots.value("design.alpha") == 0.05
    assert REGISTRY.slots.value("design.sesoi_floor") == 0.06


def test_the_excluded_severity_coordinate_is_recorded_as_excluded():
    """D7 is a fixed EXCLUSION, so its absence must itself be declared."""
    slot = REGISTRY.slots["design.severity_coordinate_excluded"]
    assert slot.get() is True
    assert "commensurable" in slot.note


def test_fixed_size_stopping_is_declared_with_its_prohibitions():
    slot = REGISTRY.slots["design.stopping_rule"]
    assert slot.get() == "fixed-size"
    for banned in ("effect size", "significance", "interval", "convenience"):
        assert banned in slot.note


def test_the_registry_exposes_the_design_axes():
    assert REGISTRY.pair_ids == ("p1", "p2", "p3")
    assert REGISTRY.loads == LOADS
    assert REGISTRY.orders == ORDERS
    assert REGISTRY.arms == ARMS


# ------------------------------------------------------ nothing is fabricated
def test_no_reserved_pre_freeze_output_carries_a_value():
    registry.assert_nothing_fabricated()


def test_the_check_covers_every_quantity_the_directive_reserves():
    """Exact epsilon, budgets, V, method, checkpoint, GPU class, caps, seed."""
    for name in ("exact_epsilon", "budget.retained_set",
                 "controller.final_answer_allowance_v",
                 "inference.selected_method", "runtime.checkpoint",
                 "runtime.selected_configuration",
                 "runtime.certified_gpu_class", "planning.h_max_caps",
                 "proposal.root_construction_seed", "falsification.battery"):
        assert not REGISTRY.slots[name].resolved, name


def test_a_fabricated_value_anywhere_in_the_registry_is_caught(monkeypatch):
    tampered = Registry(
        protocol=PROTOCOL_VERSION,
        slots=REGISTRY.slots.freeze("exact_epsilon", 0.06, by="a hunch"))
    monkeypatch.setattr(registry, "REGISTRY", tampered)
    with pytest.raises(AssertionError, match="confirm that procedure genuinely ran"):
        registry.assert_nothing_fabricated()


def test_admitted_reference_identities_are_still_absent():
    from dci.v19 import pairs
    for pair in pairs.PAIRS:
        assert not any(slot.admitted for slot in pair.references)


# ---------------------------------------------------------- the stage gate
def test_every_declared_stage_is_currently_blocked():
    """No pre-freeze output has legitimately been produced yet."""
    for stage in STAGE_DEPENDENCIES:
        assert REGISTRY.blockers_for(stage), stage


@pytest.mark.parametrize("stage", sorted(STAGE_DEPENDENCIES))
def test_requiring_any_stage_refuses_and_names_its_blockers(stage):
    with pytest.raises(UnresolvedDependency) as caught:
        REGISTRY.require_stage(stage)
    message = str(caught.value)
    assert stage in message
    assert "produced by:" in message


def test_the_stage_nine_gate_lists_the_preregistered_prerequisites():
    """Section 14.9: epsilon fixed, caps frozen, validity fixtures executed."""
    blockers = {s.name for s in REGISTRY.blockers_for("stage_9_method_selection")}
    assert {"exact_epsilon", "inference.validity_results", "planning.h_max_caps",
            "budget.retained_set", "runtime.selected_configuration"} == blockers


def test_stage_twelve_needs_every_numerical_output_it_freezes():
    blockers = {s.name for s in REGISTRY.blockers_for("stage_12_freeze")}
    for required in ("exact_epsilon", "budget.retained_set",
                     "controller.final_answer_allowance_v",
                     "inference.selected_method", "runtime.certified_gpu_class",
                     "falsification.battery"):
        assert required in blockers


def test_stage_ten_cannot_run_before_the_method_is_frozen():
    """Section 14.10: the bank is built after Stage 9, never before."""
    assert "inference.selected_method" in {
        s.name for s in REGISTRY.blockers_for("stage_10_attainable_bank")}


def test_an_unknown_stage_is_an_error_not_a_pass():
    with pytest.raises(KeyError, match="no declared slot-level prerequisites"):
        REGISTRY.blockers_for("stage_99_profit")
    with pytest.raises(KeyError, match="not a declared stage"):
        REGISTRY.require_stage("stage_99_profit")


def test_a_stage_becomes_ready_when_its_prerequisites_resolve():
    table = REGISTRY.slots
    table = table.freeze("runtime.checkpoint", "org/model@abc123",
                         by="Stage 3 checkpoint-selection record")
    advanced = Registry(protocol=PROTOCOL_VERSION, slots=table)
    assert advanced.stage_status("stage_3_runtime_freeze")["status"] == "READY"
    advanced.require_stage("stage_3_runtime_freeze")
    # And the original registry is untouched.
    assert REGISTRY.blockers_for("stage_3_runtime_freeze")


# --------------------------------------------------------- the root blocker
def test_the_reported_status_is_the_root_cause_not_the_first_alphabetically():
    """Stage 9 waits on hardware AND a prospective decision; the decision is root."""
    row = REGISTRY.stage_status("stage_9_method_selection")
    assert len(row["all_blocking_statuses"]) == 3
    assert row["root_blocker"] == "BLOCKED_BY_PROSPECTIVE_DECISION"
    assert row["status"] == row["root_blocker"]


def test_the_precedence_puts_human_supplied_inputs_furthest_upstream():
    assert BLOCKER_PRECEDENCE == ("BLOCKED_BY_PROSPECTIVE_DECISION",
                                  "BLOCKED_BY_CONTENT",
                                  "BLOCKED_BY_HARDWARE",
                                  "BLOCKED_BY_UPSTREAM_FREEZE")


def test_every_blocking_status_appears_in_the_precedence():
    seen = set()
    for stage in STAGE_DEPENDENCIES:
        seen |= set(REGISTRY.stage_status(stage)["all_blocking_statuses"])
    assert seen <= set(BLOCKER_PRECEDENCE)


# -------------------------------------------------------------- the report
def test_the_report_is_serialisable_and_complete():
    got = registry.report()
    json.dumps(got)
    assert got["protocol"] == PROTOCOL_VERSION
    assert got["n_slots"] == len(REGISTRY.slots)
    assert len(got["stages"]) == len(STAGE_DEPENDENCIES)
    assert set(got["statuses"]) <= {"IMPLEMENTED_AND_TESTED"} | set(
        BLOCKER_PRECEDENCE)


def test_the_report_names_the_two_unbuilt_pair_one_verifiers():
    assert registry.report()["unimplemented_verifiers"] == [
        "v19:verifier.exact_bullet_count", "v19:verifier.transitive_order"]


def test_the_status_census_accounts_for_every_slot():
    census = REGISTRY.statuses()
    assert sum(census.values()) == len(REGISTRY.slots)
    assert census["IMPLEMENTED_AND_TESTED"] == len(REGISTRY.slots.resolved())


def test_most_of_the_registry_is_still_pending():
    """An honest registry at Stage 1 is mostly unresolved."""
    assert len(REGISTRY.unresolved()) > len(REGISTRY.slots.resolved())


# ----------------------------------------------------------- the fingerprints
def test_the_declaration_fingerprint_is_deterministic():
    assert REGISTRY.fingerprint == registry.build().fingerprint
    assert len(REGISTRY.fingerprint) == 64


def test_the_declaration_fingerprint_survives_freezing_an_output():
    advanced = Registry(
        protocol=PROTOCOL_VERSION,
        slots=REGISTRY.slots.freeze("runtime.checkpoint", "org/model@abc",
                                    by="Stage 3"))
    assert advanced.fingerprint == REGISTRY.fingerprint
    assert advanced.state_fingerprint != REGISTRY.state_fingerprint


def test_the_state_fingerprint_records_the_current_freeze_position():
    assert REGISTRY.state_fingerprint == registry.build().state_fingerprint
    assert len(REGISTRY.state_fingerprint) == 64


def test_every_slot_cites_a_preregistration_location():
    for slot in REGISTRY.slots:
        assert slot.prereg, slot.name
