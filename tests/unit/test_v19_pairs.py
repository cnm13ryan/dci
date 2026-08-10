"""The three fixed pairs, four reference slots each, and nothing invented.

Section 5 and register rows D2, D3, D5 fix the scientific spine: three
target-focal pairs, exactly four independently admitted references per pair,
paired loads k in {2,5}, both presentation orders. What the registry must *not*
do is supply the things later stages produce - the four reference identities
(Stage 8), the canonical wordings (Stage 7), the parameter populations (Stage 5),
the retained budget set (Stage 4).

So the tests come in two halves: the fixed structure is present and immutable,
and every unresolved output refuses to yield a placeholder.
"""
import pytest

from dci.v19 import pairs
from dci.v19.families import N_PAIRS, N_REFERENCES
from dci.v19.identity import ARMS, LOADS, ORDERS
from dci.v19.pairs import (PAIRS, ConstraintRule, Pair, ReferenceSlot,
                           VerifierBinding)
from dci.v19.resolution import Resolution, UnresolvedDependency, fixed, pending

pytestmark = pytest.mark.cpu


# ------------------------------------------------------------ fixed structure
def test_the_declared_structure_satisfies_the_fixed_commitments():
    pairs.assert_pair_structure()


def test_exactly_three_pairs_exist():
    assert len(PAIRS) == N_PAIRS == 3
    assert pairs.PAIR_IDS == ("p1", "p2", "p3")


def test_each_pair_matches_the_preregistered_rule_table():
    """Section 5.1's table, checked by substance rather than by id."""
    expected = {
        "p1": ("exactly N bullet-list items", "correct transitive order"),
        "p2": ("all specified mandatory words", "unique"),
        "p3": ("exactly N sentences", "increase monotonically"),
    }
    for pair_id, (target_text, focal_text) in expected.items():
        got = pairs.pair(pair_id)
        assert target_text in got.target.statement
        assert focal_text in got.focal.statement


def test_every_pair_has_exactly_four_reference_slots():
    for p in PAIRS:
        assert len(p.references) == N_REFERENCES == 4
        assert [r.arm for r in p.references] == ["R1", "R2", "R3", "R4"]
        assert [r.index for r in p.references] == [1, 2, 3, 4]


def test_the_arms_are_the_focal_plus_four_references():
    for p in PAIRS:
        assert p.arms == ARMS == ("B", "R1", "R2", "R3", "R4")


def test_reference_slots_are_distinguishable_positions_not_a_set():
    """Section 3.3: the comparison with R1 is not interchangeable with R2."""
    slots = pairs.PAIR_1.references
    assert len({r.arm for r in slots}) == 4
    assert len({r.identity.name for r in slots}) == 4


def test_constraint_identifiers_are_v19_native_and_unique():
    """Section 5.1 requires v19 ids rather than the colliding inherited ones."""
    ids = [rule.constraint_id for rule in pairs.rules()]
    assert len(ids) == 6 and len(set(ids)) == 6
    assert all(i.startswith("v19:") for i in ids)


def test_an_inherited_identifier_is_refused():
    with pytest.raises(ValueError, match="not a v19-native identifier"):
        ConstraintRule(constraint_id="A", role="target", name="n",
                       statement="s", family="f", generative_scope="sentence",
                       verifier=VerifierBinding(verifier_id="v"))


def test_the_v15_lineage_is_recorded_where_a_rule_descends_from_one():
    """Provenance only: reuse is permitted after audit, not assumed by it."""
    p3 = pairs.pair("p3")
    assert p3.target.v15_lineage and p3.focal.v15_lineage
    # Pair 1 is new in v19, so it must not claim a lineage it does not have.
    p1 = pairs.pair("p1")
    assert p1.target.v15_lineage == "" and p1.focal.v15_lineage == ""


def test_the_pair_registry_is_immutable():
    with pytest.raises(Exception):
        pairs.PAIR_1.pair_id = "p9"                     # type: ignore[misc]
    with pytest.raises(Exception):
        pairs.PAIR_1.target.statement = "something else"  # type: ignore[misc]


def test_family_labels_are_descriptive_metadata():
    """Section 5.5: one pair per family combination, so no family inference."""
    combos = {p.family_combination for p in PAIRS}
    assert len(combos) == 3
    for p in PAIRS:
        assert "->" in p.family_combination


def test_every_pair_records_its_principal_measurement_risk():
    for p in PAIRS:
        assert len(p.measurement_risk) > 40
        assert "section 5." in p.measurement_risk


# -------------------------------------------------------- loads, orders, arms
@pytest.mark.parametrize("load", LOADS)
def test_the_preregistered_loads_are_accepted(load):
    assert pairs.assert_load(load) == load


@pytest.mark.parametrize("load", [0, 1, 3, 4, 6, -2, None, "2", True])
def test_any_other_load_is_refused(load):
    with pytest.raises(ValueError, match=r"load .* is not one of \(2, 5\)"):
        pairs.assert_load(load)


def test_an_integer_valued_float_load_is_refused():
    """2.0 == 2 but hashes differently, so it would give one cell two ids."""
    with pytest.raises(ValueError, match="types are part of the hashed identity"):
        pairs.assert_load(2.0)


@pytest.mark.parametrize("order", ORDERS)
def test_the_preregistered_orders_are_accepted(order):
    assert pairs.assert_order(order) == order


@pytest.mark.parametrize("order", ["o_B", "A", "", None, "o_a", "average", 0])
def test_any_other_order_is_refused(order):
    with pytest.raises(ValueError, match="presentation order"):
        pairs.assert_order(order)


@pytest.mark.parametrize("arm", ARMS)
def test_the_preregistered_arms_are_accepted(arm):
    assert pairs.assert_arm(arm) == arm


@pytest.mark.parametrize("arm", ["R5", "R0", "b", "", None, "synthetic_control", 1])
def test_any_other_arm_is_refused(arm):
    with pytest.raises(ValueError, match="arm"):
        pairs.assert_arm(arm)


# ------------------------------------------------- nothing acquires a default
def test_reference_identities_are_unresolved():
    for p in PAIRS:
        for slot in p.references:
            assert not slot.admitted
            assert slot.identity.resolution is Resolution.PENDING_EMPIRICAL
            assert slot.identity.status == "BLOCKED_BY_UPSTREAM_FREEZE"


def test_asking_for_reference_identities_refuses_with_the_full_blocker_set():
    with pytest.raises(UnresolvedDependency) as caught:
        pairs.PAIR_2.require_admitted_references()
    message = str(caught.value)
    assert "4 unresolved pre-freeze outputs" in message
    for i in range(1, 5):
        assert f"p2.reference.R{i}" in message
    assert "Stage 8 simultaneous admission" in message


def test_the_reference_production_rule_is_the_preregistered_one():
    rule = pairs.PAIR_1.references[0].identity.rule
    for phrase in ("Stage 8", "joint reference-error certificate",
                   "exactly four admitted", "independent validation"):
        assert phrase in rule


def test_reference_admission_depends_on_exact_epsilon():
    """Stage 8 freezes epsilon before any epsilon-dependent matching constant."""
    assert "exact_epsilon" in pairs.PAIR_3.references[0].identity.depends_on


def test_a_slot_shipped_with_an_identity_is_refused():
    """A registry that ships reference identities has pre-empted Stage 8."""
    with pytest.raises(ValueError, match="pre-empted the construction procedure"):
        ReferenceSlot(pair="p1", index=1, arm="R1",
                      identity=fixed("p1.reference.R1", "D12", "some_constraint"))


def test_a_fifth_reference_slot_is_refused():
    with pytest.raises(ValueError, match="exactly four references"):
        ReferenceSlot(pair="p1", index=5, arm="R5",
                      identity=pending("x", "D12", Resolution.PENDING_EMPIRICAL,
                                       "Stage 8"))


def test_a_slot_whose_arm_disagrees_with_its_index_is_refused():
    with pytest.raises(ValueError, match="must occupy arm R2"):
        ReferenceSlot(pair="p1", index=2, arm="R3",
                      identity=pending("x", "D12", Resolution.PENDING_EMPIRICAL,
                                       "Stage 8"))


def test_a_pair_with_the_wrong_number_of_slots_is_refused():
    p = pairs.PAIR_1
    with pytest.raises(ValueError, match="exactly 4 is fixed"):
        Pair(pair_id="p1", ordinal=1, target=p.target, focal=p.focal,
             family_combination=p.family_combination,
             measurement_risk=p.measurement_risk,
             references=p.references[:3], candidate_pool=p.candidate_pool,
             reserve_pool=p.reserve_pool)


def test_candidate_and_reserve_pools_are_unresolved_content():
    for p in PAIRS:
        assert p.candidate_pool.status == "BLOCKED_BY_CONTENT"
        assert p.reserve_pool.status == "BLOCKED_BY_CONTENT"
        assert "24 authored candidates" in p.candidate_pool.rule
        assert "blind tranche of 12" in p.candidate_pool.rule


def test_the_candidate_pool_records_the_refpool_failure_mode():
    assert "REFPOOL" in pairs.PAIR_1.candidate_pool.note


def test_the_declared_slot_table_covers_every_pending_pair_output():
    table = pairs.declared_slots()
    assert len(table) == N_PAIRS * (N_REFERENCES + 2) == 18
    assert not table.resolved()
    assert table.statuses() == {"BLOCKED_BY_UPSTREAM_FREEZE": 12,
                                "BLOCKED_BY_CONTENT": 6}


def test_the_declaration_fingerprint_is_deterministic():
    assert pairs.declared_slots().fingerprint == \
        pairs.declared_slots().fingerprint
    assert len(pairs.declared_slots().fingerprint) == 64


# ------------------------------------------------------------ the budget grid
def test_cells_cannot_be_enumerated_against_an_assumed_budget_grid():
    """B_ret is a Stage 4 output, so there is no default to enumerate over."""
    with pytest.raises(ValueError, match="Stage 4 output"):
        list(pairs.cells())


def test_cells_cross_the_full_design_when_budgets_are_supplied():
    got = list(pairs.cells(["b_lo", "b_mid", "b_hi"]))
    assert len(got) == 3 * 3 * len(LOADS) * len(ORDERS) * len(ARMS) == 180
    assert len(set(got)) == len(got)
    # Every pair contributes every arm at every load and order.
    for pair_id in pairs.PAIR_IDS:
        arms = {c[4] for c in got if c[0] == pair_id}
        assert arms == set(ARMS)


# --------------------------------------------------------------- verifiers
def test_pair_one_verifiers_are_declared_but_not_yet_built():
    """Section 10.9: Pair 1 bullet-count and transitive-order support is new."""
    missing = {v.verifier_id for v in pairs.unimplemented_verifiers()}
    assert missing == {"v19:verifier.exact_bullet_count",
                       "v19:verifier.transitive_order"}


def test_an_unbuilt_verifier_refuses_to_resolve():
    binding = pairs.PAIR_1.target.verifier
    assert not binding.implemented
    with pytest.raises(NotImplementedError, match="Stage 2 must build it"):
        binding.resolve()


def test_the_reused_pair_two_and_three_verifiers_resolve_today():
    for pair_id in ("p2", "p3"):
        p = pairs.pair(pair_id)
        for rule in (p.target, p.focal):
            assert rule.verifier.implemented, rule.constraint_id
            assert callable(rule.verifier.resolve())


def test_a_verifier_naming_a_missing_callable_refuses_clearly():
    binding = VerifierBinding(verifier_id="v19:verifier.ghost",
                              callable_name="v_does_not_exist")
    assert not binding.implemented
    with pytest.raises(NotImplementedError, match="which does not exist"):
        binding.resolve()


def test_every_verifier_declares_the_span_it_parses():
    """Coupling risk is a property of the shared parse, so the span is recorded."""
    for rule in pairs.rules():
        assert rule.verifier.span, rule.constraint_id


def test_pair_one_verifiers_share_a_parse_span_which_is_the_coupling_risk():
    p1 = pairs.pair("p1")
    assert "list_segmentation" in p1.target.verifier.span
    assert "list_segmentation" in p1.focal.verifier.span


# --------------------------------------------------------------- parameters
def test_parameterised_rules_name_their_parameters_without_values():
    """Section 6: P_Q and nu_Q are Stage 5 outputs; only the names are fixed."""
    assert pairs.pair("p1").target.parameters == ("n_items",)
    assert pairs.pair("p1").focal.parameters == ("ordering_depth",)
    assert pairs.pair("p3").target.parameters == ("n_sentences",)
    assert "mandatory_word_count" in pairs.pair("p2").target.parameters


def test_the_unparameterised_focal_rules_say_why():
    """Section 6.1 forbids a scalar severity coordinate across families."""
    for pair_id in ("p2", "p3"):
        focal = pairs.pair(pair_id).focal
        assert not focal.parameterised
        assert "unparameterised" in focal.note


def test_no_rule_declares_a_severity_coordinate():
    """D7: the universal cross-family severity coordinate is fixed EXCLUDED."""
    for rule in pairs.rules():
        assert not any("severity" in p for p in rule.parameters)


# ------------------------------------------------------- generative scope
def test_every_rule_declares_a_legal_generative_scope():
    for rule in pairs.rules():
        assert rule.generative_scope in ("sentence", "whole_text")


def test_an_illegal_generative_scope_is_refused():
    with pytest.raises(ValueError, match="generative scope"):
        ConstraintRule(constraint_id="v19:x", role="target", name="n",
                       statement="s", family="f", generative_scope="paragraph",
                       verifier=VerifierBinding(verifier_id="v"))


def test_an_illegal_role_is_refused():
    with pytest.raises(ValueError, match="role"):
        ConstraintRule(constraint_id="v19:x", role="synthetic_control", name="n",
                       statement="s", family="f", generative_scope="sentence",
                       verifier=VerifierBinding(verifier_id="v"))


def test_an_unknown_pair_id_lists_the_three_that_exist():
    with pytest.raises(KeyError, match=r"\('p1', 'p2', 'p3'\)"):
        pairs.pair("p4")
