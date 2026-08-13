"""The frozen specifications, and the pre-freeze outputs beside them.

Each specification here is a FIXED method whose numerical outputs arrive later.
The pairing is where mistakes live: the decoder specification is fixed, but "the
exact representation that disables top-k under the pinned Transformers version"
is not, and substituting a plausible default for that is indistinguishable from
having frozen it properly.

So the tests assert two things about every specification: the fixed part matches
the preregistration exactly, and the pending part has not quietly acquired a
value.
"""
import pytest

from dci.v19 import ALPHA, CANDIDATE_METHODS, SESOI_FLOOR, specs
from dci.v19.resolution import Resolution, UnresolvedDependency
from dci.v19.specs import (CHECKPOINT_ELIGIBILITY, CONTROLLER, DECODER,
                           HARDWARE_SELECTION, PROPOSAL_LAW,
                           SELECTION_TIE_BREAKS, SESOI_DECISION_STEPS,
                           VALIDITY_GATES)

pytestmark = pytest.mark.cpu


@pytest.fixture()
def table():
    return specs.declared_slots()


# ---------------------------------------------------------------- the decoder
def test_the_decoder_is_exactly_the_preregistered_configuration():
    """Section 9.6 and D23, field by field."""
    assert DECODER.temperature == 0.70
    assert DECODER.top_p == 0.95
    assert DECODER.top_k is None                     # disabled
    assert DECODER.do_sample is True                 # greedy is excluded
    assert DECODER.num_beams == 1
    assert DECODER.repetition_penalty == 1.0
    assert DECODER.no_repeat_ngram_size == 0


def test_top_k_is_disabled_rather_than_set_large():
    """A large top-k is still a top-k processor; section 9.6 disables it."""
    assert DECODER.sampling_fields["top_k"] is None


@pytest.mark.parametrize("control", [
    "min_p", "typical_p", "epsilon_cutoff", "eta_cutoff", "frequency_penalty",
    "presence_penalty", "best_of", "stop_strings"])
def test_every_forbidden_truncation_or_selection_control_is_named(control):
    assert control in DECODER.forbidden_controls


def test_the_decoder_specification_is_fixed_but_its_representation_is_not(table):
    assert table["decoder.specification"].resolution is Resolution.FIXED
    assert table["decoder.top_k_disabled_representation"].status == \
        "BLOCKED_BY_HARDWARE"
    with pytest.raises(UnresolvedDependency):
        table.value("decoder.top_k_disabled_representation")


def test_the_resolved_configuration_hash_awaits_the_actual_runtime(table):
    slot = table["decoder.resolved_configuration_hash"]
    assert not slot.resolved
    assert "after model defaults" in slot.rule
    assert "runtime.checkpoint" in slot.depends_on


def test_the_decoder_specification_is_immutable():
    with pytest.raises(Exception):
        DECODER.temperature = 1.0                       # type: ignore[misc]


# -------------------------------------------------------------- the controller
def test_the_controller_never_samples_beyond_the_allowance():
    """Section 9.7: "Do not sample token V+1" - not sample then discard."""
    assert CONTROLLER.sample_token_beyond_allowance is False


def test_cache_state_continues_within_a_generation_and_never_across():
    assert CONTROLLER.cache_continues_within_generation is True
    assert CONTROLLER.cache_crosses_generations is False


def test_the_two_controller_flags_are_the_preregistered_names():
    assert CONTROLLER.forced_transition_flag == "CAP_FORCED_TRANSITION"
    assert CONTROLLER.final_truncated_flag == "FINAL_TRUNCATED"


@pytest.mark.parametrize("banned", [
    "generic_textual_stop_strings", "best_of_n", "reranking",
    "self_consistency_selection", "critique_or_revision",
    "tool_mediated_replacement", "post_hoc_continuation"])
def test_every_section_nine_seven_prohibition_is_recorded(banned):
    assert banned in CONTROLLER.prohibited


@pytest.mark.parametrize("field", [
    "hard_budget", "realised_reasoning_use", "cap_hit",
    "reasoning_ended_naturally", "raw_reasoning_trace_hash", "final_answer_hash",
    "controller_hash", "finish_reason", "retry_lineage"])
def test_the_required_instrumentation_of_section_ten_two_is_listed(field):
    assert field in CONTROLLER.required_instrumentation


def test_the_final_answer_allowance_is_unresolved_and_budget_independent(table):
    slot = table["controller.final_answer_allowance_v"]
    assert slot.status == "BLOCKED_BY_UPSTREAM_FREEZE"
    assert "budget-dependent V is prohibited" in slot.rule
    with pytest.raises(UnresolvedDependency):
        table.value("controller.final_answer_allowance_v")


def test_the_reasoning_delimiter_is_a_property_of_the_checkpoint(table):
    slot = table["controller.reasoning_delimiter"]
    assert "runtime.checkpoint" in slot.depends_on
    assert "without consuming a draw" in slot.rule


# ------------------------------------------------------------- the budget grid
def test_three_retained_budgets_is_the_fixed_minimum(table):
    assert table.value("budget.minimum_retained") == 3
    assert "compute-treatment gate" in table["budget.minimum_retained"].note


def test_the_retained_budget_set_is_unresolved(table):
    with pytest.raises(UnresolvedDependency):
        table.value("budget.retained_set")
    assert table["budget.retained_set"].depends_on == (
        "budget.candidate_grid", "budget.separation_threshold")


# ------------------------------------------------------------ the proposal law
def test_the_proposal_law_is_with_replacement_and_rejects_whole_proposals():
    """D14: no round-robin without-replacement cycles, no component swap."""
    assert PROPOSAL_LAW.with_replacement is True
    assert PROPOSAL_LAW.whole_proposal_rejection is True
    assert PROPOSAL_LAW.repair_failed_proposal is False


def test_the_seed_stream_is_keyed_per_pair_index_attempt_and_field():
    assert PROPOSAL_LAW.seed_stream_key == ("pair", "draw_index",
                                            "proposal_attempt", "field")
    assert "SHA-256" in PROPOSAL_LAW.seed_derivation


def test_the_load_structure_matches_the_paired_design():
    assert PROPOSAL_LAW.backgrounds_at_max_load == 3
    assert PROPOSAL_LAW.lower_load_backgrounds == 0


def test_the_root_construction_seed_and_cap_are_unresolved(table):
    for name in ("proposal.root_construction_seed", "proposal.construction_cap"):
        assert not table[name].resolved
    assert "before any Stage 9 comparison output is viewed" in \
        table["proposal.construction_cap"].rule


# -------------------------------------------------------- inference candidates
def test_exactly_two_candidates_and_no_third(table):
    assert table.value("inference.candidate_set") == CANDIDATE_METHODS
    assert len(CANDIDATE_METHODS) == 2
    assert "new protocol version" in table["inference.candidate_set"].note


def test_the_discarded_bootstrap_is_recorded_as_discarded():
    assert specs.INFERENCE_CANDIDATES.discarded_as_claim_bearing == (
        "studentised max-T bootstrap",)
    assert "max-T" not in " ".join(CANDIDATE_METHODS)


@pytest.mark.parametrize("gate", VALIDITY_GATES)
def test_every_validity_gate_is_declared(gate):
    assert gate in VALIDITY_GATES


def test_the_nine_validity_gates_of_section_twelve_four_are_present():
    assert len(VALIDITY_GATES) == 9
    for phrase in ("theorem_assumption_mapping", "zero_variance",
                   "interval_missingness", "multiplicity", "max_min",
                   "null_coverage", "independent_reference"):
        assert any(phrase in g for g in VALIDITY_GATES), phrase


def test_the_tie_break_chain_is_in_the_preregistered_order():
    assert SELECTION_TIE_BREAKS == (
        "lowest_expected_compute_design_satisfying_all_acceptance_criteria",
        "smaller_sum_of_H_p",
        "smaller_median_primary_interval_width_at_theta_equals_epsilon",
        "lexicographic_frozen_method_id")


def test_ten_thousand_experiments_per_point_is_fixed(table):
    assert table.value("inference.experiments_per_point") == 10_000


def test_the_selected_method_is_unresolved_and_cannot_be_reopened(table):
    slot = table["inference.selected_method"]
    assert slot.status == "BLOCKED_BY_UPSTREAM_FREEZE"
    assert "exact_epsilon" in slot.depends_on
    assert "cannot reselect the method" in slot.note
    with pytest.raises(UnresolvedDependency):
        table.value("inference.selected_method")


def test_both_code_hashes_are_required_and_unresolved(table):
    for name in ("inference.production_code_hash", "inference.reference_code_hash"):
        assert not table[name].resolved


def test_the_planning_caps_are_frozen_before_any_comparison_output(table):
    assert "before any comparison output is viewed" in \
        table["planning.h_max_caps"].rule


# ----------------------------------------------------------------- multiplicity
def test_each_family_controls_its_own_five_percent(table):
    assert table.value("multiplicity.per_family_alpha") == ALPHA == 0.05


def test_there_is_no_joint_alpha_and_that_absence_is_explicit(table):
    """D34: the report must not state a single joint 5% rate."""
    slot = table["multiplicity.joint_alpha_across_families"]
    assert slot.resolved and slot.get() is None
    assert "must not state" in slot.note


def test_the_order_family_is_hierarchically_activated(table):
    note = table.value("multiplicity.order_family_activation")
    assert "L_Theta > 0" in note
    assert "restricts interpretation" in \
        table["multiplicity.order_family_activation"].note


# ---------------------------------------------------------------------- SESOI
def test_the_sesoi_floor_is_fixed_at_six_hundredths(table):
    assert table.value("sesoi_floor") == SESOI_FLOOR == 0.06


def test_the_two_construction_ceilings_resolve_under_the_floor(table):
    """min(0.015, eps/4) = 0.015 and min(0.02, eps/2) = 0.02 for every eps>=0.06."""
    assert table.value("coupling.kappa_ceiling") == 0.015
    assert table.value("wording.difference_ceiling") == 0.02
    for name in ("coupling.kappa_ceiling", "wording.difference_ceiling"):
        assert "every admissible exact epsilon" in table[name].note


def test_exact_epsilon_is_a_prospective_decision_not_an_empirical_output(table):
    slot = table["exact_epsilon"]
    assert slot.resolution is Resolution.PENDING_DECISION
    assert slot.status == "BLOCKED_BY_PROSPECTIVE_DECISION"
    with pytest.raises(UnresolvedDependency, match="signed prospective"):
        table.value("exact_epsilon")


def test_exact_epsilon_cannot_be_chosen_from_design_outputs(table):
    rule = table["exact_epsilon"].rule
    for forbidden in ("method-comparison results", "power curves",
                      "Stage 10 attainability", "confirmatory outcomes"):
        assert forbidden in rule


def test_the_epsilon_note_lists_every_first_dependency(table):
    note = table["exact_epsilon"].note
    for dependency in ("epsilon/8", "matching constant", "Theta = epsilon",
                       "design"):
        assert dependency in note


def test_the_six_steps_of_the_signed_procedure_are_recorded():
    assert len(SESOI_DECISION_STEPS) == 6
    for phrase in ("write_and_sign", "smallest_scientifically_meaningful",
                   "record_every_precedent", "why_smaller_effects",
                   "without_consulting", "signed_record"):
        assert any(phrase in s for s in SESOI_DECISION_STEPS), phrase


# --------------------------------------------------- checkpoint and hardware
def test_the_checkpoint_eligibility_conditions_are_the_preregistered_eight():
    assert len(CHECKPOINT_ELIGIBILITY) == 8
    for phrase in ("hashable", "revisions_pinned", "deterministically_separable",
                   "without_candidate_answer_selection", "v_independent",
                   "three_distinguishable_retained_budgets", "stage_2a",
                   "without_oom"):
        assert any(phrase in c for c in CHECKPOINT_ELIGIBILITY), phrase


def test_hardware_selection_ranks_by_cost_per_thousand_valid_generations():
    assert HARDWARE_SELECTION["primary_ranking_metric"] == (
        "monetary cost per 1,000 valid logical generations")
    assert HARDWARE_SELECTION["tie_breaks"] == (
        "lower_technical_failure_rate", "higher_valid_generations_per_hour",
        "lexicographic_frozen_configuration_id")


def test_no_gpu_sku_price_or_throughput_is_hard_coded():
    """Section 9.4 forbids preregistering a current SKU, price or throughput."""
    text = repr(HARDWARE_SELECTION) + repr(CHECKPOINT_ELIGIBILITY)
    for forbidden in ("H100", "A100", "B200", "H200", "$", "USD"):
        assert forbidden not in text


def test_no_dci_outcome_may_enter_hardware_selection():
    assert set(HARDWARE_SELECTION["forbidden_inputs"]) == {
        "dci_effect_estimate", "verifier_failure_magnitude",
        "behavioural_outcome"}


def test_the_scientific_architecture_is_fixed(table):
    assert table.value("runtime.architecture") == (
        "PyTorch + Hugging Face Transformers + frozen accelerator backend")


def test_one_process_and_one_active_sequence_per_gpu_is_the_default(table):
    slot = table["runtime.default_worker_topology"]
    assert "one active scientific sequence per GPU" in slot.get()
    assert "tensor parallelism is excluded by default" in slot.note


def test_vllm_is_recorded_as_optional_and_not_used(table):
    assert table.value("runtime.vllm_disposition") == "OPTIONAL_NOT_USED"
    assert "10,000 paired exact prompt-seed cases" in \
        table["runtime.vllm_disposition"].note
    assert "no scientific penalty" in table["runtime.vllm_disposition"].note


def test_the_checkpoint_and_certified_class_are_unresolved(table):
    for name in ("runtime.checkpoint", "runtime.selected_configuration",
                 "runtime.certified_gpu_class"):
        assert not table[name].resolved
    assert table["runtime.certified_gpu_class"].status == "BLOCKED_BY_HARDWARE"


def test_there_is_no_device_pinning_fallback(table):
    assert "no fallback" in table["runtime.certified_gpu_class"].note


# -------------------------------------------------------- terminal falsification
def test_terminal_falsification_is_sequestered_until_inference_is_locked(table):
    slot = table["falsification.sequencing"]
    assert "opened only after" in slot.get()
    assert "cannot trigger selective replacement" in slot.note


def test_the_falsification_battery_is_unauthored(table):
    assert table["falsification.battery"].status == "BLOCKED_BY_CONTENT"


# ------------------------------------------------------------------- the table
def test_no_reserved_pre_freeze_output_carries_a_value(table):
    from dci.v19.resolution import assert_no_fabricated_values
    assert_no_fabricated_values(table, {
        "exact_epsilon": "signed prospective scientific-decision procedure",
        "controller.final_answer_allowance_v": None,
        "budget.retained_set": None,
        "inference.selected_method": None,
        "runtime.checkpoint": None,
        "runtime.certified_gpu_class": None,
    })


def test_the_table_declares_no_duplicate_slots(table):
    names = [s.name for s in table]
    assert len(names) == len(set(names))


def test_the_fingerprint_is_deterministic(table):
    assert table.fingerprint == specs.declared_slots().fingerprint
    assert len(table.fingerprint) == 64


def test_every_slot_cites_a_preregistration_location(table):
    for slot in table:
        assert slot.prereg
        assert "section" in slot.prereg or slot.prereg.startswith("D")
