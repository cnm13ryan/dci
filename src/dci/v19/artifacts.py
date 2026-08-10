"""Pre-freeze artifacts produced by Stages 2 through 17.

The Stage 1 registry declares what the protocol fixes. This module declares what
the *later* stages will produce, because a gate cannot be fail-closed on an
artifact it has no name for. Before this existed, the Stage 15 gate could report
READY with no generation manifest in the registry at all - not because the
manifest was deemed unnecessary, but because nothing represented it.

Every slot here is pending. Its `rule` names the stage procedure that produces it
and its `depends_on` names what that procedure needs first, so the dependency
graph in `registry.py` can be checked against the preregistration rather than
trusted.

Two conventions matter:

  * an artifact is declared by the module, not by the stage that consumes it.
    Stage 15 does not own the generation manifest; Stage 12 produces it and
    Stage 15 requires it.
  * aggregate artifacts are declared alongside their primitives. Section 14.12
    computes a root manifest hash and section 14.14 signs a root SHA-256
    manifest, so downstream stages can depend on those single artifacts instead
    of re-enumerating everything upstream - provided the aggregate is itself
    fail-closed on its own prerequisites, which is what `depends_on` records.
"""
from __future__ import annotations

from dci.v19.pairs import PAIR_IDS
from dci.v19.resolution import Resolution, Slot, SlotTable, pending

# ------------------------------------------------- Stage 2: verifier infrastructure

VERIFIER_SLOTS = SlotTable.of(
    pending("verifiers.bundle_hash", "section 14.2 / Appendix I",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: implement and reconcile every deterministic verifier, then "
            "freeze the verifier bundle hash; Pair 1 bullet-count and "
            "transitive-order support must be built, and Pair 2/3 code may be "
            "reused only after a hash and semantic audit",
            note="Appendix I requires invariant verifier hashes across the run"),
    pending("verifiers.boundary_mutations", "section 8.7",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: at least 1,000 automated boundary mutations per constraint "
            "template covering off-by-one, duplication, omission, forbidden-item, "
            "ordering, formatting, Unicode and parser-edge cases",
            note="property-based testing is evidence about implementation "
                 "invariants, not a proof of natural-language semantics"),
    pending("verifiers.binomial_interval_implementation", "D9 / section 10.4",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: recover the exact two-sided binomial interval "
            "implementation used by the inherited reliability gate from the "
            "authoritative code or specification and freeze it; if it is not "
            "uniquely recoverable its choice is a pre-freeze output within D9, "
            "never an implementer decision"),
    pending("verifiers.tier1_reliability", "section 10.4",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: certify each target and focal verifier against the 5% "
            "Tier-1 conditional error ceiling using 73 human-adjudicated true "
            "failures and 73 true passes per verifier unit",
            depends_on=("verifiers.binomial_interval_implementation",),
            note="a missing truth class is missing evidence, not zero error, so "
                 "the corresponding bound is unavailable and the unit fails"),
)


# ------------------------------- Stage 2A: early runtime and inference qualification

QUALIFICATION_SLOTS = SlotTable.of(
    pending("qualification.stage2a", "section 14.2A / Appendix D",
            Resolution.PENDING_CERTIFICATION,
            "Stage 2A: run every test that could invalidate later calibration - "
            "tokenizer/template fixtures, reasoning-cap and final-answer "
            "boundaries, parser property tests, same- and cross-device replay, "
            "maximum-context and OOM, dtype and attention assertions, manifest "
            "fail-closed mutations, worker-death recovery, durable persistence, "
            "verifier replay, seed collisions, interval-missingness brute force, "
            "zero-variance fixtures, WSR truncation transitions, and max-min "
            "small-family fixtures",
            depends_on=("runtime.checkpoint",),
            note="Stage 13 compares all hashes back to this baseline, so it must "
                 "exist before recertification can mean anything"),
)


# ------------------------------------ Stages 5 to 8: construction outputs per pair

def _per_pair_slots() -> tuple[Slot, ...]:
    out: list[Slot] = []
    for pair in PAIR_IDS:
        out.append(pending(
            f"parameters.{pair}.admissible_set", "D6 / sections 6.2, 6.3, 14.5",
            Resolution.PENDING_EMPIRICAL,
            "Stage 5: the boundary-aware calibration of section 6.2 - an ordered "
            "grid of at most five admissible settings per family, n_cal = 100 "
            "observations, and the exact two-sided 95% Clopper-Pearson interval "
            "contained in [0.05, 0.95] - yielding a nonempty P_Q",
            depends_on=("exact_epsilon", "budget.retained_set",
                        f"pool.{pair}.tasks.parameter_calibration"),
            note="interpolation, manual tuning and post hoc choice are "
                 "prohibited; the first passing value is selected"))
        out.append(pending(
            f"parameters.{pair}.distribution", "D6 / sections 6.3, 8.3",
            Resolution.PENDING_EMPIRICAL,
            "Stage 5: the explicit sampling distribution nu_Q frozen with P_Q "
            "after the boundary gate and satisfiability requirements",
            depends_on=(f"parameters.{pair}.admissible_set",),
            note="section 8.3 step 3 draws each active constraint's parameter "
                 "from this distribution, so the proposal law cannot run without it"))
        out.append(pending(
            f"eligibility.{pair}.hard_gates", "section 14.6",
            Resolution.PENDING_EMPIRICAL,
            "Stage 6: apply the logical, schema, scope, satisfiability, boundary "
            "and verifier gates to the 24 authored candidates",
            depends_on=(f"pool.{pair}.candidate_references",
                        f"parameters.{pair}.admissible_set",
                        "verifiers.bundle_hash")))
        out.append(pending(
            f"coupling.{pair}.audit", "D10 / sections 7.7, 14.6",
            Resolution.PENDING_EMPIRICAL,
            "Stage 6: the fixed coupling probe - 2,000 base outputs balanced "
            "across the four (Y_A, Y_R) cells, eight frozen truth-preserving "
            "nuisance classes, and the simultaneous empirical-Bernstein system "
            "certifying max U_A <= 0.02, max U_R <= 0.02 and max U_kappa <= 0.015",
            depends_on=(f"pool.{pair}.coupling_probes", "verifiers.bundle_hash"),
            note="any expansion to the epsilon/8 precision target requires exact "
                 "epsilon to be frozen before the expansion data are generated"))
        out.append(pending(
            f"wording.{pair}.instability", "D11 / sections 7.8, 7.9, 14.7",
            Resolution.PENDING_EMPIRICAL,
            "Stage 7: certify one canonical wording plus 11 semantic paraphrases "
            "per relevant constraint, estimate wording instability with M = 12, "
            "N_W = 100, G_W = 2 and 10,000 task-cluster bootstraps, and require "
            "the simultaneous UCB for |W_R - W_A| to be at most 0.02",
            depends_on=(f"pool.{pair}.wording_calibration",
                        f"eligibility.{pair}.hard_gates")))
        out.append(pending(
            f"matching.{pair}.constants", "D12 / sections 7.6, 7.7, 14.8",
            Resolution.PENDING_EMPIRICAL,
            "Stage 8: the numerical calipers delta_r, the sensitivity "
            "coefficients s_f, and the joint reference-error allowance "
            "epsilon_ref, all linked to the SESOI and calibration evidence",
            depends_on=("exact_epsilon", f"coupling.{pair}.audit",
                        f"wording.{pair}.instability"),
            note="these are not fitted to force four candidates to pass"))
        out.append(pending(
            f"validation.{pair}.independent", "D12 / section 7.10",
            Resolution.PENDING_EMPIRICAL,
            "Stage 8: the disjoint validation split repeating logical "
            "eligibility, support, verifier/coupling, wording and "
            "matching-support checks under simultaneous uncertainty",
            depends_on=(f"pool.{pair}.tasks.independent_validation",)
            + tuple(f"reference.{pair}.R{i}" for i in range(1, 5)),
            note="one reference's excess error cannot be offset by another; "
                 "failure returns the pair to pre-freeze construction"))
        out.append(pending(
            f"bank.{pair}.attainable_count", "section 14.10",
            Resolution.PENDING_EMPIRICAL,
            "Stage 10: the realised attainable count H_p,max reached under the "
            "frozen with-replacement proposal law and the complete "
            "whole-composition acceptance gate, bounded by the predeclared "
            "construction cap",
            depends_on=("proposal.root_construction_seed",
                        "proposal.construction_cap",
                        f"parameters.{pair}.distribution"),
            note="proposal probabilities, pools, acceptance rules, the cap and "
                 "the Stage 9 method are never changed in response to this value"))
        out.append(pending(
            f"bank.{pair}.accepted_order", "sections 14.10, 14.12",
            Resolution.PENDING_EMPIRICAL,
            "Stage 10: the deterministic accepted-bank order, so Stage 12 can "
            "select exactly the first H_p eligible accepted superblocks",
            depends_on=(f"bank.{pair}.attainable_count",)))
    return tuple(out)


CONSTRUCTION_SLOTS = SlotTable(slots=_per_pair_slots())


# ------------------------------------- Stages 9 and 11: simulation and design output

SIMULATION_SLOTS = SlotTable.of(
    pending("simulation.method_comparison", "D35 / sections 13.1, 14.9",
            Resolution.PENDING_EMPIRICAL,
            "Stage 9: 10,000 simulated complete experiments per frozen "
            "scenario/design point for each valid candidate, through the actual "
            "production analysis path, within H_p <= the frozen planning caps",
            depends_on=("exact_epsilon", "planning.h_max_caps",
                        "inference.validity_results")),
    pending("runtime.cost_model", "section 13.3",
            Resolution.PENDING_EMPIRICAL,
            "measured valid logical generations per hour, empirical token counts "
            "from disjoint pre-confirmatory runtime material, retry and failure "
            "rates, and the contemporaneous selected-hardware cost",
            depends_on=("runtime.selected_configuration",)),
    pending("simulation.authoritative_design", "D36 / sections 13.7, 14.11",
            Resolution.PENDING_EMPIRICAL,
            "Stage 11: 10,000 simulated complete experiments per attainable "
            "candidate design through the single Stage 9 method and exact "
            "production analysis, with the runtime-cost model",
            depends_on=("inference.selected_method", "runtime.cost_model")
            + tuple(f"bank.{p}.attainable_count" for p in PAIR_IDS)),
    pending("simulation.counterfactual_diagnostic", "sections 13.7, 14.11",
            Resolution.PENDING_EMPIRICAL,
            "Stage 11: reapply the already frozen Stage 9 selection criterion to "
            "the archived Stage 9 curves restricted to H_p <= H_p,max, with no "
            "new simulation, interpolation, extrapolation or retuning",
            depends_on=("simulation.method_comparison",
                        "simulation.authoritative_design"),
            note="mandatory disclosure only: it cannot reopen Stage 9, change "
                 "claim-bearing inference, or modify the final design"),
    pending("design.final_h_p", "D36 / section 13.6",
            Resolution.PENDING_EMPIRICAL,
            "Stage 11: the pair-specific vector H = (H_1, H_2, H_3) of the "
            "lowest expected-compute valid design satisfying every prospective "
            "acceptance criterion",
            depends_on=("simulation.authoritative_design",
                        "simulation.counterfactual_diagnostic")),
    pending("design.replicates_g", "D36 / sections 11.6, 13.3",
            Resolution.PENDING_EMPIRICAL,
            "Stage 11: the common decoder replicate count G, from the same "
            "authoritative simulation",
            depends_on=("simulation.authoritative_design",),
            note="increasing G does not increase the number of independent "
                 "superblocks, and cannot reduce the MP-EB range term"),
)


# ------------------------------------ Stages 12 to 14: the manifest and the freeze

FREEZE_SLOTS = SlotTable.of(
    pending("manifest.generation_manifest", "D42 / section 14.12",
            Resolution.PENDING_EMPIRICAL,
            "Stage 12: expand the first H_p eligible accepted superblocks from "
            "each pair's bank, under the frozen bank order, into the complete "
            "generation manifest with immutable superblock, cell and generation "
            "ids, scientific seeds and condition metadata",
            depends_on=("design.final_h_p", "design.replicates_g",
                        "budget.retained_set",
                        "controller.final_answer_allowance_v")
            + tuple(f"bank.{p}.accepted_order" for p in PAIR_IDS)
            + tuple(f"reference.{p}.R{i}" for p in PAIR_IDS
                    for i in range(1, 5)),
            note="the completeness gate of Appendix I takes this as its expected "
                 "scientific population"),
    pending("manifest.root_hash", "D42 / section 14.12",
            Resolution.PENDING_EMPIRICAL,
            "Stage 12: the root manifest hash computed over the complete "
            "generation manifest",
            depends_on=("manifest.generation_manifest",)),
    pending("recertification.stage13", "D40 / section 14.13",
            Resolution.PENDING_CERTIFICATION,
            "Stage 13: re-run the complete mandatory runtime and "
            "inference-validation suite on the already frozen scientific "
            "configuration and intended confirmatory GPU pool, comparing every "
            "hash to the Stage 2A and Stage 3 baselines",
            depends_on=("qualification.stage2a", "manifest.root_hash",
                        "runtime.certified_gpu_class"),
            note="any failure blocks confirmation and invalidates the "
                 "dependency-scoped downstream artifacts; it does not license "
                 "silent repair after generation begins"),
    pending("freeze.root_signature", "section 14.14",
            Resolution.PENDING_DECISION,
            "Stage 14: sign the preregistration source and PDF, the complete "
            "decision register, the remaining-pre-freeze closure report, the "
            "construction artifacts, the runtime manifest, the inference code, "
            "the simulation outputs, the scientific-draw manifest, the "
            "terminal-falsification plan, and the root SHA-256 manifest",
            depends_on=("manifest.root_hash", "recertification.stage13",
                        "falsification.battery", "inference.production_code_hash",
                        "verifiers.bundle_hash"),
            note="records that no confirmatory output exists before the signed "
                 "freeze timestamp; this is the execution authority Stage 15 "
                 "requires, which is why it is a signed decision rather than a "
                 "computed artifact"),
)


# ------------------------------------ Stages 15 to 17: execution and falsification

EXECUTION_SLOTS = SlotTable.of(
    pending("ledger.terminal_states", "Appendix I / section 14.16",
            Resolution.PENDING_EMPIRICAL,
            "Stage 16: the frozen terminal observed/permanently-missing ledger, "
            "with exactly one terminal state per planned generation id",
            depends_on=("manifest.generation_manifest", "freeze.root_signature")),
    pending("analysis.code_hash", "section 14.16",
            Resolution.PENDING_EMPIRICAL,
            "Stage 16: the hash of the single preselected analysis code, run "
            "once as the authoritative confirmatory analysis",
            depends_on=("inference.production_code_hash",
                        "freeze.root_signature")),
    pending("analysis.confirmatory_outputs", "sections 14.16, 16.1",
            Resolution.PENDING_EMPIRICAL,
            "Stage 16: all primary and secondary family bounds, the full "
            "reference-specific surface, least-favourable bounds, L_Theta, the "
            "selected descriptive maximum, result and status codes, and the "
            "prespecified sensitivities",
            depends_on=("ledger.terminal_states", "analysis.code_hash"),
            note="the confirmatory analysis cannot trigger new generation, "
                 "method selection or sample-size extension"),
    pending("falsification.result", "D43 / section 14.17",
            Resolution.PENDING_EMPIRICAL,
            "Stage 17: execute the frozen terminal-falsification battery and "
            "decision rules, only after the confirmatory outputs and the "
            "analysis hash are locked",
            depends_on=("analysis.confirmatory_outputs", "analysis.code_hash",
                        "falsification.battery"),
            note="it cannot trigger selective replacement of confirmatory data "
                 "or retroactive redesign"),
)


def declared_slots() -> SlotTable:
    """Every artifact Stages 2 through 17 will produce, all pending."""
    table = VERIFIER_SLOTS
    for other in (QUALIFICATION_SLOTS, CONSTRUCTION_SLOTS, SIMULATION_SLOTS,
                  FREEZE_SLOTS, EXECUTION_SLOTS):
        table = table.merged(other)
    return table
