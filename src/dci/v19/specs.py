"""The frozen specifications: decoder, controller, proposal law, inference, SESOI.

Preregistration sections 8.3, 9.3-9.8, 11.9, 12.4 and 12.11, and register rows
D14, D16, D23, D24, D25, D26, D27, D28, D29, D34, D43.

Each dataclass here states a \\FIXED method and, alongside it, the pre-freeze
outputs that method will produce. Keeping the two in one place is deliberate: the
decoder specification is fixed but "the exact representation that disables top-k
under the pinned Transformers version" is not, and separating them is how a
plausible default gets substituted for a frozen value.

What this module does NOT do is enforce anything at generation time. Asserting
that the *resolved* generation configuration equals DECODER is a runtime concern
that has to read what the backend will actually execute after model defaults,
generation config, library defaults and backend arguments have all resolved
(section 9.6); the specification it will compare against lives here.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Optional

from dci.v19 import ALPHA, CANDIDATE_METHODS, SESOI_FLOOR
from dci.v19.resolution import Resolution, SlotTable, fixed, pending


def frozen_state(spec) -> dict:
    """The complete scientifically relevant state of a specification object.

    Hashing a hand-picked subset of a specification's fields is how a frozen
    commitment quietly stops being covered: the decoder's forbidden-control list
    is exactly what the runtime assertion checks, and the controller's
    prohibitions are exactly what distinguishes the frozen generator from a
    different one, yet neither was in its own hash. Serialising the whole
    dataclass means a field added later is covered by construction rather than by
    someone remembering to extend a literal.
    """
    if not dataclasses.is_dataclass(spec) or isinstance(spec, type):
        raise TypeError(f"{spec!r} is not a specification instance")
    return dataclasses.asdict(spec)

# --------------------------------------------------------------- the decoder


@dataclass(frozen=True)
class DecoderSpec:
    """Section 9.6 and D23. Every field is a fixed scientific commitment.

    Greedy decoding is excluded because it defines a different decoder kernel,
    which is why `do_sample` is part of the specification rather than an
    implementation detail. Hugging Face "may inherit values from a generation
    configuration", so the complete resolved configuration must be frozen
    explicitly and validated - the specification alone is not the guarantee.
    """
    temperature: float = 0.70
    top_p: float = 0.95
    top_k: Optional[int] = None            # disabled, not "set to a large value"
    do_sample: bool = True
    num_beams: int = 1
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0

    # Controls that must be absent, not merely set to a neutral value: section
    # 9.6 forbids "any other truncation/selection mechanism". A processor present
    # with a no-op setting still changes the kernel if a later default revives it.
    forbidden_controls: tuple[str, ...] = (
        "min_p", "typical_p", "epsilon_cutoff", "eta_cutoff",
        "frequency_penalty", "presence_penalty", "best_of",
        "num_return_sequences_above_one", "diversity_penalty",
        "length_penalty", "renormalize_logits_override", "guidance_scale",
        "sequence_bias", "bad_words_ids", "force_words_ids",
        "constraints", "prefix_allowed_tokens_fn", "stop_strings",
    )

    @property
    def sampling_fields(self) -> dict[str, object]:
        """The fields a resolved generation configuration must match exactly."""
        return {"temperature": self.temperature, "top_p": self.top_p,
                "top_k": self.top_k, "do_sample": self.do_sample,
                "num_beams": self.num_beams,
                "repetition_penalty": self.repetition_penalty,
                "no_repeat_ngram_size": self.no_repeat_ngram_size}


DECODER = DecoderSpec()

# The exact representation that disables top-k is version-dependent: some
# Transformers releases spell it None, others 0. Section 9.6 requires freezing
# the exact representation under the pinned version and validating that no top-k
# logits processor is active, so it cannot be guessed here.
DECODER_SLOTS = SlotTable.of(
    fixed("decoder.specification", "D23 / section 9.6", frozen_state(DECODER),
          note="the complete specification, including the forbidden-control "
               "list the resolved-configuration assertion will check"),
    pending("decoder.top_k_disabled_representation", "section 9.6",
            Resolution.PENDING_CERTIFICATION,
            "freeze the exact value that disables top-k under the pinned "
            "Transformers version, and validate that no top-k logits processor "
            "is active in the resolved configuration",
            depends_on=("runtime.transformers_version",)),
    pending("decoder.resolved_configuration_hash", "section 9.6 / D19",
            Resolution.PENDING_CERTIFICATION,
            "hash of the complete resolved generation configuration, captured "
            "after model defaults, generation config, library defaults and "
            "backend arguments have resolved",
            depends_on=("runtime.checkpoint", "runtime.transformers_version")),
)


# ------------------------------------------------- the hard reasoning controller


@dataclass(frozen=True)
class ControllerSpec:
    """Section 9.7 and D24: prompt -> reasoning content <= b -> final answer <= V.

    The transition is externally enforced. If reasoning content reaches exactly b
    first, sampling stops, the frozen native reasoning-end delimiter is appended
    deterministically *without consuming a random draw*, CAP_FORCED_TRANSITION is
    set, and final-answer generation continues without resetting KV/cache state or
    the pseudorandom stream. That "without consuming a random draw" clause is why
    this cannot be post-hoc truncation: appending through the sampler would
    advance the stream and change every subsequent token.
    """
    forced_transition_flag: str = "CAP_FORCED_TRANSITION"
    final_truncated_flag: str = "FINAL_TRUNCATED"

    # Token V+1 is never sampled, as opposed to sampled and discarded.
    sample_token_beyond_allowance: bool = False

    # KV/cache state may continue only across the two phases of one logical
    # generation; leakage across generation ids is prohibited.
    cache_continues_within_generation: bool = True
    cache_crosses_generations: bool = False

    # Section 9.7's prohibitions. Each would substitute a different generator for
    # the frozen one, so they are named rather than left implicit.
    prohibited: tuple[str, ...] = (
        "generic_textual_stop_strings", "best_of_n", "reranking",
        "self_consistency_selection", "critique_or_revision",
        "tool_mediated_replacement", "post_hoc_continuation",
    )

    # Section 10.2's required per-generation instrumentation.
    required_instrumentation: tuple[str, ...] = (
        "budget_id", "hard_budget", "realised_reasoning_use", "cap_hit",
        "reasoning_ended_naturally", "reasoning_parse_status",
        "final_answer_extraction_status", "raw_reasoning_trace_hash",
        "final_answer_hash", "checkpoint_hash", "tokenizer_hash",
        "chat_template_hash", "engine_hash", "dtype", "controller_hash",
        "final_answer_token_count", "finish_reason", "latency", "retry_lineage",
    )


CONTROLLER = ControllerSpec()

CONTROLLER_SLOTS = SlotTable.of(
    fixed("controller.specification", "D24 / section 9.7",
          frozen_state(CONTROLLER),
          note="the complete specification, including the seven section 9.7 "
               "prohibitions and the required per-generation instrumentation"),
    pending("controller.final_answer_allowance_v", "D24 / section 9.8",
            Resolution.PENDING_EMPIRICAL,
            "selected on disjoint pre-confirmatory material to give final-answer "
            "headroom for the most demanding admissible k=5 compositions; common "
            "across assigned budgets, since a budget-dependent V is prohibited",
            depends_on=("runtime.checkpoint",)),
    pending("controller.reasoning_delimiter", "section 9.7",
            Resolution.PENDING_CERTIFICATION,
            "the checkpoint's frozen native reasoning-end delimiter, appended "
            "deterministically at a forced transition without consuming a draw",
            depends_on=("runtime.checkpoint",)),
    pending("controller.identity_hash", "D19 / section 9.5",
            Resolution.PENDING_CERTIFICATION,
            "hash of the reasoning parser and controller implementation, frozen "
            "in the immutable implementation manifest"),
)


# ---------------------------------------------------------- the budget grid


BUDGET_SLOTS = SlotTable.of(
    fixed("budget.minimum_retained", "D25 / section 9.8", 3,
          note="fewer than three retained budgets fails the compute-treatment "
               "gate and makes the checkpoint/runtime ineligible"),
    pending("budget.candidate_grid", "section 9.8",
            Resolution.PENDING_EMPIRICAL,
            "a broad ordered candidate grid authored before manipulation "
            "outcomes are inspected, spanning a useful reasoning range within "
            "the validated context envelope",
            depends_on=("runtime.checkpoint",)),
    pending("budget.retained_set", "D25 / section 9.8",
            Resolution.PENDING_EMPIRICAL,
            "the largest ordered subset whose adjacent pairs all pass the frozen "
            "separation criterion, with at least three budgets",
            depends_on=("budget.candidate_grid",
                        "budget.separation_threshold")),
    pending("budget.separation_threshold", "section 9.8",
            Resolution.PENDING_EMPIRICAL,
            "prompt count M, repeat count, simultaneous confidence construction "
            "and lower-bound separation threshold, all frozen before "
            "manipulation outcomes are evaluated"),
)


# ------------------------------------------------------------- the proposal law


@dataclass(frozen=True)
class ProposalLawSpec:
    """Section 8.3, Appendix C and D14. Independent, with replacement.

    v19 replaced deterministic without-replacement background cycles because the
    claim-bearing confidence candidates require an explicitly stated probability
    model, and a round-robin cycle is not one. Two clauses are easy to lose in
    implementation and are therefore stated as data:

      * whole-proposal rejection. "No individual background identity is swapped
        in isolation" - a swap would define a different law under which accepted
        draws are no longer identically distributed.
      * per-index stream independence, by domain-separated counter-based SHA-256
        over (pair, index, proposal attempt, field), so retrying or parallelising
        one superblock cannot consume draws assigned to another.

    Reproducibility of the realised stream is explicitly *not* the argument for
    independence; the stated design law is.
    """
    with_replacement: bool = True
    whole_proposal_rejection: bool = True
    repair_failed_proposal: bool = False
    default_within_stratum_pmf: str = "uniform"
    seed_derivation: str = "domain-separated counter-based SHA-256"
    seed_stream_key: tuple[str, ...] = ("pair", "draw_index",
                                        "proposal_attempt", "field")
    backgrounds_at_max_load: int = 3
    lower_load_backgrounds: int = 0


PROPOSAL_LAW = ProposalLawSpec()

PROPOSAL_SLOTS = SlotTable.of(
    fixed("proposal.law", "D14 / section 8.3", frozen_state(PROPOSAL_LAW),
          note="the complete law, including the seed derivation and its "
               "domain-separation key, and the background structure at both loads"),
    pending("proposal.root_construction_seed", "section 8.3",
            Resolution.PENDING_EMPIRICAL,
            "frozen with the canonical sampler implementation before the first "
            "confirmatory superblock is realised"),
    pending("proposal.task_pmf", "section 8.3 step 1",
            Resolution.PENDING_CONTENT,
            "uniform with replacement over the frozen T_p unless Stage 1 freezes "
            "a different explicit pmf before any model-dependent calibration; "
            "the same pmf is used for every index",
            depends_on=("pool.p1.tasks.confirmation",)),
    pending("proposal.construction_cap", "section 13.3 / 14.10",
            Resolution.PENDING_EMPIRICAL,
            "the predeclared Stage 10 accepted-bank construction cap, frozen "
            "before any Stage 9 comparison output is viewed"),
)


# --------------------------------------------------------- inference candidates


# Section 12.4's validity-first gates, in the document's order. A method failing
# any one is ineligible "regardless of interval width or compute savings".
VALIDITY_GATES = (
    "theorem_assumption_mapping_to_the_dci_superblock_law",
    "exact_support_tests",
    "one_and_two_sided_coverage_derivations",
    "zero_variance_fixtures",
    "interval_missingness_proofs_and_brute_force_small_sample_checks",
    "complete_family_multiplicity_tests",
    "max_min_transformation_tests",
    "null_coverage_simulation",
    "production_versus_independent_reference_agreement_on_a_frozen_bank",
)

# Section 12.4's deterministic tie-break chain, applied in order after the
# validity-first filter.
SELECTION_TIE_BREAKS = (
    "lowest_expected_compute_design_satisfying_all_acceptance_criteria",
    "smaller_sum_of_H_p",
    "smaller_median_primary_interval_width_at_theta_equals_epsilon",
    "lexicographic_frozen_method_id",
)


@dataclass(frozen=True)
class InferenceCandidateSpec:
    """Section 12.4 and D28: exactly two candidates, and no third ever."""
    methods: tuple[str, ...] = CANDIDATE_METHODS
    validity_gates: tuple[str, ...] = VALIDITY_GATES
    tie_breaks: tuple[str, ...] = SELECTION_TIE_BREAKS
    experiments_per_scenario_design: int = 10_000
    fallback_if_betting_invalid: str = "MP-EB remains primary"
    fallback_if_neither_valid: str = "confirmation cannot begin"
    discarded_as_claim_bearing: tuple[str, ...] = ("studentised max-T bootstrap",)


INFERENCE_CANDIDATES = InferenceCandidateSpec()

INFERENCE_SLOTS = SlotTable.of(
    fixed("inference.candidate_set", "D28 / section 12.4",
          INFERENCE_CANDIDATES.methods,
          note="no third method may be introduced after comparison data are "
               "inspected; a new method requires a new protocol version"),
    fixed("inference.experiments_per_point", "D35 / section 13.1", 10_000),
    pending("inference.selected_method", "D29 / section 14.9",
            Resolution.PENDING_EMPIRICAL,
            "the validity-first deterministic rule of section 12.4, then the "
            "10,000-experiment comparison within the frozen pre-Stage-10 H caps",
            depends_on=("exact_epsilon", "inference.validity_results",
                        "planning.h_max_caps"),
            note="later realised attainability cannot reselect the method; the "
                 "post-Stage-10 restricted-region comparison is disclosure only"),
    pending("inference.validity_results", "section 12.4",
            Resolution.PENDING_EMPIRICAL,
            "every validity gate in VALIDITY_GATES, including the WSR-PP "
            "truncation-transition bank against an independent reference "
            "calculator (Appendix D item 16)"),
    pending("inference.production_code_hash", "section 12.4",
            Resolution.PENDING_EMPIRICAL,
            "frozen with the selected method, alongside the independent "
            "reference implementation hash and the validation report"),
    pending("inference.reference_code_hash", "section 12.4",
            Resolution.PENDING_EMPIRICAL,
            "hash of the independently implemented reference calculator"),
    pending("planning.h_max_caps", "section 13.3",
            Resolution.PENDING_EMPIRICAL,
            "per-pair min of the hard construction ceilings implied by "
            "pre-Stage-9 artifacts, frozen with each source ceiling before any "
            "comparison output is viewed"),
)


# ----------------------------------------------------------------- multiplicity


MULTIPLICITY_SLOTS = SlotTable.of(
    fixed("multiplicity.per_family_alpha", "D34 / section 12.11", ALPHA),
    fixed("multiplicity.joint_alpha_across_families", "D34 / section 12.11", None,
          note="explicitly absent: the report must not state a single 5% "
               "familywise rate jointly across every primary and secondary claim"),
    fixed("multiplicity.order_family_activation", "section 12.14",
          "hierarchically activated: confirmatory order-effect claims are "
          "interpreted only if the primary gate L_Theta > 0 is met",
          note="the hierarchy restricts interpretation and does not license a "
               "stronger across-all-families guarantee"),
)


# ------------------------------------------------------------------- the SESOI


# Section 11.9. The floor is a scientific commitment, and it is what makes the
# two construction ceilings resolve numerically for EVERY admissible exact
# epsilon - so those two ceilings are fixed even though exact epsilon is not.
SESOI_SLOTS = SlotTable.of(
    fixed("sesoi_floor", "D26 / section 11.9", SESOI_FLOOR),
    fixed("coupling.kappa_ceiling", "section 7.7", 0.015,
          note="min(0.015, epsilon/4) = 0.015 for every admissible exact epsilon "
               "under the Stage 1 floor"),
    fixed("wording.difference_ceiling", "section 7.9", 0.02,
          note="min(0.02, epsilon/2) = 0.02 for every admissible exact epsilon"),
    pending("exact_epsilon", "D27 / section 11.9",
            Resolution.PENDING_DECISION,
            "the signed prospective scientific-decision procedure of section "
            "11.9: a written and signed rationale, the smallest scientifically "
            "meaningful absolute increase in target-failure probability subject "
            "to the floor, every precedent used, why smaller effects would not "
            "support the claim, selected without consulting method-comparison "
            "results, power curves at alternative candidate values, Stage 10 "
            "attainability or confirmatory outcomes, then entered into the "
            "signed pre-freeze decision record",
            note="must be frozen before the first procedure that numerically "
                 "consumes it, including any epsilon/8 coupling-bank expansion, "
                 "any epsilon-dependent matching constant, scenarios at "
                 "Theta = epsilon or 2 epsilon, and authoritative design "
                 "selection"),
)

# The six steps of section 11.9's procedure, recorded so the decision-record
# machinery can require each one rather than accepting a bare number.
SESOI_DECISION_STEPS = (
    "write_and_sign_a_rationale_before_executing_the_dependent_procedure",
    "state_why_the_value_is_the_smallest_scientifically_meaningful_increase",
    "record_every_precedent_prior_result_domain_judgement_and_interpretation",
    "explain_why_smaller_effects_would_not_support_the_sesoi_claim",
    "select_without_consulting_comparison_power_attainability_or_outcomes",
    "enter_value_rationale_source_and_timestamp_into_the_signed_record",
)


# ------------------------------------------------- checkpoint and runtime choice


# Section 9.3. Every condition must hold "before model-dependent scientific
# calibration", and none of them may consult a DCI magnitude.
CHECKPOINT_ELIGIBILITY = (
    "weights_and_configuration_downloadable_and_hashable_under_the_licence",
    "exact_model_tokenizer_and_template_revisions_pinned",
    "reasoning_and_final_answer_segments_deterministically_separable",
    "hard_cap_enforceable_without_candidate_answer_selection",
    "v_independent_of_assigned_b",
    "at_least_three_distinguishable_retained_budgets_survive_the_gate",
    "complete_runtime_and_dtype_path_passes_stage_2a",
    "max_prompt_plus_control_tokens_plus_b_max_plus_v_fits_without_oom",
)

# Section 9.4. The candidate list is generated immediately before benchmarking
# from the provider's current instance-type API; no SKU, count, price, throughput
# or duration is hard-coded in the protocol.
HARDWARE_SELECTION = {
    "primary_ranking_metric": "monetary cost per 1,000 valid logical generations",
    "tie_breaks": ("lower_technical_failure_rate",
                   "higher_valid_generations_per_hour",
                   "lexicographic_frozen_configuration_id"),
    "eligibility_preconditions": (
        "envelope_fits_with_frozen_dtype_and_attention_backend",
        "complete_stage_2a_suite_passes",
        "no_silent_model_dtype_attention_generation_or_tokenizer_fallback",
        "runs_one_process_one_active_sequence_unless_tp_separately_justified"),
    "measured_quantities": (
        "valid_logical_generations_per_hour", "generated_token_throughput",
        "end_to_end_latency_distribution", "peak_allocated_device_memory",
        "peak_reserved_device_memory", "technical_failure_rate",
        "cost_per_1000_valid_logical_generations"),
    "forbidden_inputs": ("dci_effect_estimate", "verifier_failure_magnitude",
                         "behavioural_outcome"),
}

RUNTIME_SLOTS = SlotTable.of(
    fixed("runtime.architecture", "D17 / section 9.1",
          "PyTorch + Hugging Face Transformers + frozen accelerator backend"),
    fixed("runtime.default_worker_topology", "section 9.2",
          "one model process and one active scientific sequence per GPU",
          note="tensor parallelism is excluded by default and requires separate "
               "pre-freeze necessity justification plus the complete "
               "cross-device, seed, controller, recovery and equivalence suite"),
    fixed("runtime.vllm_disposition", "D22 / section 9.10", "OPTIONAL_NOT_USED",
          note="Transformers remains the scientific engine unless the full "
               "Stage 2A suite plus 10,000 paired exact prompt-seed cases pass; "
               "failure carries no scientific penalty"),
    pending("runtime.checkpoint", "D16 / section 14.3",
            Resolution.PENDING_EMPIRICAL,
            "selected only by the frozen non-DCI capability, architecture-"
            "diversity, single-device-fit, licensing, reproducibility and "
            "resource criteria of section 9.3"),
    pending("runtime.transformers_version", "D19 / section 9.5",
            Resolution.PENDING_CERTIFICATION,
            "frozen in the immutable implementation manifest before any "
            "model-dependent scientific calibration"),
    pending("runtime.selected_configuration", "D19 / section 9.4",
            Resolution.PENDING_CERTIFICATION,
            "the lowest-cost eligible configuration from the outcome-independent "
            "benchmark, ranked by cost per 1,000 valid logical generations",
            depends_on=("runtime.checkpoint",)),
    pending("runtime.certified_gpu_class", "D20 / section 9.9",
            Resolution.PENDING_CERTIFICATION,
            "one certified interchangeability class passing the cross-device "
            "replay corpus with exact agreement on token ids, persisted output "
            "bytes, controller flags, final-answer extraction and verifier "
            "outputs; one mismatch fails the class",
            depends_on=("runtime.selected_configuration",),
            note="there is no fallback that permanently pins scientific draws to "
                 "a non-interchangeable physical GPU"),
)


# ------------------------------------------------------- terminal falsification


TERMINAL_FALSIFICATION_SLOTS = SlotTable.of(
    fixed("falsification.sequencing", "D43 / section 14.17",
          "frozen and sequestered before confirmation; opened only after the "
          "confirmatory outputs and analysis hash are locked",
          note="terminal falsification can qualify, challenge or prevent "
               "interpretation, but cannot trigger selective replacement of "
               "confirmatory data or retroactive redesign"),
    pending("falsification.battery", "D43 / section 14.17",
            Resolution.PENDING_CONTENT,
            "the frozen terminal-falsification battery and decision rules, "
            "authored and sequestered before confirmation begins"),
)


def declared_slots() -> SlotTable:
    """Every specification-level slot, for the Stage 1 registry and the audit."""
    table = DECODER_SLOTS
    for other in (CONTROLLER_SLOTS, BUDGET_SLOTS, PROPOSAL_SLOTS,
                  INFERENCE_SLOTS, MULTIPLICITY_SLOTS, SESOI_SLOTS,
                  RUNTIME_SLOTS, TERMINAL_FALSIFICATION_SLOTS):
        table = table.merged(other)
    return table
