"""The pre-freeze resolution model: pending cannot become a default.

Section 1.3 warns that "a row marked PFD is not permission for implementer
discretion: its value is produced only by the rule cited in that row". The two
invariants that enforce it mechanically are tested here:

  * a pending slot cannot carry a value, so no placeholder can later be mistaken
    for a legitimately produced output;
  * a resolved slot cannot be re-frozen, so a later stage can consume a frozen
    output but never retrospectively change it (section 14).

The third thing under test is that the audit statuses used by the completion
report are *derived* from the same declarations the runtime gate reads, rather
than maintained by hand alongside them.
"""
import pytest

from dci.v19.resolution import (MISSING, PENDING, RESOLVED, AlreadyFrozen,
                                Resolution, Slot, SlotTable,
                                UnresolvedDependency, assert_no_fabricated_values,
                                blocking_status, fixed, pending)

pytestmark = pytest.mark.cpu


def a_pending(name="exact_epsilon", resolution=Resolution.PENDING_DECISION,
              **kw):
    return pending(name, "D27", resolution,
                   "the signed prospective SESOI decision procedure "
                   "(section 11.9)", **kw)


# ------------------------------------------------------------- the vocabulary
def test_every_resolution_is_either_resolved_or_pending():
    assert set(RESOLVED) | set(PENDING) == set(Resolution)
    assert not set(RESOLVED) & set(PENDING)


@pytest.mark.parametrize("resolution,expected", [
    (Resolution.FIXED, "IMPLEMENTED_AND_TESTED"),
    (Resolution.FROZEN, "IMPLEMENTED_AND_TESTED"),
    (Resolution.PENDING_EMPIRICAL, "BLOCKED_BY_UPSTREAM_FREEZE"),
    (Resolution.PENDING_DECISION, "BLOCKED_BY_PROSPECTIVE_DECISION"),
    (Resolution.PENDING_CERTIFICATION, "BLOCKED_BY_HARDWARE"),
    (Resolution.PENDING_CONTENT, "BLOCKED_BY_CONTENT"),
])
def test_each_reason_implies_one_audit_status(resolution, expected):
    """The audit vocabulary is derived, not maintained separately."""
    slot = (fixed("x", "S1", 1) if resolution is Resolution.FIXED else
            Slot(name="x", prereg="S1", resolution=resolution, rule="a rule",
                 frozen_by="proc" if resolution is Resolution.FROZEN else "",
                 value=1 if resolution is Resolution.FROZEN else MISSING))
    assert blocking_status(slot) == slot.status == expected


# -------------------------------------------------- a pending slot has no value
def test_a_pending_slot_cannot_carry_a_value():
    """The core prohibition: a placeholder is indistinguishable from an output."""
    with pytest.raises(ValueError, match="fabricated pre-freeze output"):
        Slot(name="exact_epsilon", prereg="D27",
             resolution=Resolution.PENDING_DECISION, rule="signed procedure",
             value=0.06)


def test_a_pending_slot_cannot_carry_none_either():
    """None is a value; the sentinel is deliberately distinct from it."""
    with pytest.raises(ValueError, match="fabricated pre-freeze output"):
        Slot(name="v", prereg="D24", resolution=Resolution.PENDING_EMPIRICAL,
             rule="Stage 4", value=None)


def test_reading_a_pending_slot_refuses_rather_than_defaulting():
    slot = a_pending()
    assert slot.pending and not slot.resolved
    with pytest.raises(UnresolvedDependency) as caught:
        slot.get()
    assert "exact_epsilon" in str(caught.value)
    assert "signed prospective SESOI decision" in str(caught.value)
    assert caught.value.statuses == ("BLOCKED_BY_PROSPECTIVE_DECISION",)


def test_get_has_no_default_parameter():
    """A default would defeat the whole point, so the signature has none."""
    import inspect
    assert list(inspect.signature(Slot.get).parameters) == ["self"]


def test_a_pending_slot_must_name_its_production_rule():
    with pytest.raises(ValueError, match="no stated production rule"):
        Slot(name="v", prereg="D24", resolution=Resolution.PENDING_EMPIRICAL,
             rule="")


def test_the_error_lists_what_it_is_waiting_on():
    slot = a_pending(depends_on=("checkpoint", "retained_budgets"))
    with pytest.raises(UnresolvedDependency, match="retained_budgets"):
        slot.get()


# ------------------------------------------------------- a resolved slot is firm
def test_a_fixed_slot_returns_its_value():
    assert fixed("sesoi_floor", "D26", 0.06).get() == 0.06


def test_a_resolved_slot_must_carry_a_value():
    with pytest.raises(ValueError, match="carries no value"):
        Slot(name="x", prereg="S1", resolution=Resolution.FIXED, rule="r")


def test_freezing_records_the_value_and_its_provenance():
    frozen = a_pending().freeze(0.08, by="signed SESOI record 2026-08-11")
    assert frozen.resolution is Resolution.FROZEN
    assert frozen.get() == 0.08
    assert frozen.frozen_by == "signed SESOI record 2026-08-11"
    assert frozen.status == "IMPLEMENTED_AND_TESTED"


def test_freezing_leaves_the_original_slot_pending():
    slot = a_pending()
    slot.freeze(0.08, by="record")
    assert slot.pending                        # frozen dataclass, new instance


def test_a_frozen_slot_cannot_be_refrozen():
    frozen = a_pending().freeze(0.08, by="record")
    with pytest.raises(AlreadyFrozen, match="cannot be changed by a later stage"):
        frozen.freeze(0.10, by="second thoughts")


def test_a_fixed_slot_cannot_be_overwritten():
    with pytest.raises(AlreadyFrozen):
        fixed("sesoi_floor", "D26", 0.06).freeze(0.04, by="convenience")


def test_freezing_requires_naming_the_producing_procedure():
    with pytest.raises(ValueError, match="provenance is recorded"):
        a_pending().freeze(0.08, by="")


def test_a_frozen_slot_must_name_what_froze_it():
    with pytest.raises(ValueError, match="provenance cannot be audited"):
        Slot(name="x", prereg="S1", resolution=Resolution.FROZEN, rule="r",
             value=1)


def test_a_slot_cannot_be_mutated_in_place():
    slot = fixed("sesoi_floor", "D26", 0.06)
    with pytest.raises(Exception):
        slot.value = 0.04                                   # type: ignore[misc]


# ----------------------------------------------------------------- the gate
def table():
    return SlotTable.of(
        fixed("sesoi_floor", "D26", 0.06),
        a_pending(),
        a_pending("retained_budgets", Resolution.PENDING_EMPIRICAL),
        a_pending("certified_gpu_class", Resolution.PENDING_CERTIFICATION),
        a_pending("confirmation_task_pool", Resolution.PENDING_CONTENT),
    )


def test_a_gate_over_resolved_slots_passes():
    table().require("sesoi_floor", what="the coupling ceiling")


def test_a_gate_reports_every_blocker_at_once():
    """One exception naming the whole dependency set, not one per attempt."""
    with pytest.raises(UnresolvedDependency) as caught:
        table().require("sesoi_floor", "exact_epsilon", "retained_budgets",
                        "certified_gpu_class", what="Stage 9")
    message = str(caught.value)
    assert "Stage 9 needs 3 unresolved pre-freeze outputs" in message
    for name in ("exact_epsilon", "retained_budgets", "certified_gpu_class"):
        assert name in message
    assert "BLOCKED_BY_PROSPECTIVE_DECISION" in message
    assert "BLOCKED_BY_HARDWARE" in message
    assert set(caught.value.statuses) == {"BLOCKED_BY_PROSPECTIVE_DECISION",
                                          "BLOCKED_BY_UPSTREAM_FREEZE",
                                          "BLOCKED_BY_HARDWARE"}


def test_a_gate_on_an_undeclared_slot_is_an_error_not_a_pass():
    """Requiring something that does not exist must never look satisfied."""
    with pytest.raises(KeyError, match="not a declared slot"):
        table().require("exact_epsilon_v2")


def test_the_singular_message_reads_correctly():
    with pytest.raises(UnresolvedDependency, match="1 unresolved pre-freeze output:"):
        table().require("exact_epsilon", what="Stage 5")


def test_blockers_are_reported_in_declaration_order():
    got = table().blockers("certified_gpu_class", "exact_epsilon")
    assert [s.name for s in got] == ["exact_epsilon", "certified_gpu_class"]


# --------------------------------------------------------------- the table
def test_duplicate_slot_names_are_refused():
    with pytest.raises(ValueError, match="duplicate slot name"):
        SlotTable.of(fixed("x", "S1", 1), fixed("x", "S1", 2))


def test_merging_refuses_overlapping_names():
    with pytest.raises(ValueError, match="declared twice"):
        table().merged(SlotTable.of(fixed("sesoi_floor", "D26", 0.06)))


def test_merging_disjoint_tables_unions_them():
    got = table().merged(SlotTable.of(fixed("alpha", "D34", 0.05)))
    assert len(got) == len(table()) + 1
    assert got.value("alpha") == 0.05


def test_freezing_returns_a_new_table_and_leaves_the_old_one_pending():
    before = table()
    after = before.freeze("retained_budgets", (512, 1024, 2048), by="Stage 4")
    assert after.value("retained_budgets") == (512, 1024, 2048)
    assert before["retained_budgets"].pending
    assert len(before) == len(after)


def test_an_unknown_slot_name_lists_the_known_ones():
    with pytest.raises(KeyError, match="sesoi_floor"):
        table()["sesoi_flor"]


def test_resolved_and_unresolved_partition_the_table():
    got = table()
    assert len(got.resolved()) + len(got.unresolved()) == len(got)
    assert [s.name for s in got.resolved()] == ["sesoi_floor"]


def test_the_status_census_matches_the_declarations():
    assert table().statuses() == {"IMPLEMENTED_AND_TESTED": 1,
                                  "BLOCKED_BY_PROSPECTIVE_DECISION": 1,
                                  "BLOCKED_BY_UPSTREAM_FREEZE": 1,
                                  "BLOCKED_BY_HARDWARE": 1,
                                  "BLOCKED_BY_CONTENT": 1}


def test_the_audit_rows_are_serialisable_and_complete():
    import json
    rows = table().audit()
    assert len(rows) == len(table())
    json.dumps(rows)                                     # must not raise
    assert {r["name"] for r in rows} >= {"exact_epsilon", "sesoi_floor"}
    assert all(r["prereg"] and r["rule"] for r in rows)


# ------------------------------------------------------------- the fingerprint
def test_the_fingerprint_is_deterministic_and_order_independent():
    a = SlotTable.of(fixed("x", "S1", 1), a_pending())
    b = SlotTable.of(a_pending(), fixed("x", "S1", 1))
    assert a.fingerprint == b.fingerprint
    assert len(a.fingerprint) == 64


def test_the_declaration_fingerprint_survives_freezing():
    """Same registry, further along the stage sequence: same declaration."""
    before = table()
    after = before.freeze("retained_budgets", (1, 2, 3), by="Stage 4")
    assert after.fingerprint == before.fingerprint

    renamed = SlotTable.of(*[s for s in before if s.name != "sesoi_floor"],
                           fixed("sesoi_bound", "D26", 0.06))
    assert renamed.fingerprint != before.fingerprint


def test_changing_a_citation_or_rule_changes_the_fingerprint():
    base = SlotTable.of(a_pending())
    other_rule = SlotTable.of(pending("exact_epsilon", "D27",
                                      Resolution.PENDING_DECISION, "guesswork"))
    assert base.fingerprint != other_rule.fingerprint


def test_the_state_fingerprint_records_what_has_been_produced():
    before = table()
    after = before.freeze("retained_budgets", (1, 2, 3), by="Stage 4")
    assert after.state_fingerprint != before.state_fingerprint
    assert len(after.state_fingerprint) == 64
    # Freezing the same value under the same provenance is reproducible.
    assert after.state_fingerprint == before.freeze(
        "retained_budgets", (1, 2, 3), by="Stage 4").state_fingerprint
    # A different value, or different provenance, is a different state.
    assert after.state_fingerprint != before.freeze(
        "retained_budgets", (1, 2, 4), by="Stage 4").state_fingerprint
    assert after.state_fingerprint != before.freeze(
        "retained_budgets", (1, 2, 3), by="Stage 4 rerun").state_fingerprint


def test_relabelling_a_pending_output_as_fixed_changes_the_state_fingerprint():
    """The two fingerprints together separate progress from alteration."""
    before = table()
    tampered = SlotTable.of(*[s for s in before if s.name != "exact_epsilon"],
                            fixed("exact_epsilon", "D27", 0.06,
                                  rule="the signed prospective SESOI decision "
                                       "procedure (section 11.9)"))
    assert tampered.fingerprint == before.fingerprint     # declaration unchanged
    assert tampered.state_fingerprint != before.state_fingerprint


def test_the_state_fingerprint_refuses_a_value_with_no_reproducible_form():
    from dci.provenance.hashes import UnhashableProtocolValue
    frozen = table().freeze("retained_budgets", object(), by="Stage 4")
    with pytest.raises(UnhashableProtocolValue):
        frozen.state_fingerprint


# ------------------------------------------------- the anti-fabrication check
def test_reserved_outputs_must_stay_unresolved():
    assert_no_fabricated_values(table(), {
        "exact_epsilon": "signed prospective SESOI",
        "retained_budgets": None,
        "certified_gpu_class": None})


def test_a_reserved_output_marked_fixed_is_caught():
    bad = SlotTable.of(fixed("exact_epsilon", "D27", 0.06))
    with pytest.raises(AssertionError, match="marked FIXED"):
        assert_no_fabricated_values(bad, {"exact_epsilon": None})


def test_a_reserved_output_that_acquired_a_value_is_caught():
    frozen = table().freeze("exact_epsilon", 0.06, by="a hunch")
    with pytest.raises(AssertionError, match="confirm that procedure genuinely ran"):
        assert_no_fabricated_values(frozen, {"exact_epsilon": None})


def test_a_reserved_output_citing_the_wrong_rule_is_caught():
    with pytest.raises(AssertionError, match="does not mention"):
        assert_no_fabricated_values(table(), {"exact_epsilon": "Stage 9 power"})
