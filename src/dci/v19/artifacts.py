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
from dci.v19.text import INTENTIONAL_CORRECTIONS

# The disposition amendment A2 records, DERIVED from the corrections the text layer
# declares rather than retyped beside them. Retyping would let the registry and the
# code drift: a correction added to one and not the other would still look complete
# from either side.
REUSE_DISPOSITION = {
    "disposition": "corrected",
    "rationale": ("section 14.2 permits reuse only after a hash and semantic audit; "
                  "the audit demonstrated three defects and section 10.6 requires "
                  "repair and re-audit before freeze, so the Pair 2 and Pair 3 "
                  "verifiers were moved onto the frozen v19 text policy with new "
                  "specification hashes"),
    "corrections": [dict(row) for row in INTENTIONAL_CORRECTIONS]}


# ------------------------------------------------- Stage 2: verifier infrastructure

VERIFIER_SLOTS = SlotTable.of(
    pending("verifiers.p1.list_policy", "sections 4.1, 4.2, 14.2",
            Resolution.PENDING_DECISION,
            "Stage 2: freeze the Pair 1 list-parsing semantics as one signed "
            "ListPolicy. The preregistration fixes the two statements and the "
            "coupling risk but no parsing rule: not the markers, not whether "
            "numbered lists are bullet-list items, not nesting, not continuation "
            "lines, not empty items, not Unicode normalisation, and not how an "
            "observed item is matched to a declared entity",
            note="amendment A1 answers every one of those questions and "
                 "dci.v19.parsing.RESOLVED_BY_AMENDMENT records the reason for each. "
                 "CANONICAL_LIST_POLICY is the IMPLEMENTED CANDIDATE; this slot "
                 "stays a decision until an acceptance record names the investigator "
                 "who accepted it, because implemented is not accepted",
            domain="list_policy"),
    pending("verifiers.p1.ordering_depth", "sections 4.1, 6.1, 14.5",
            Resolution.PENDING_DECISION,
            "Stage 2: define what the Pair 1 focal parameter `ordering_depth` "
            "declared in pairs.PAIR_1 ranges over, so Stage 5 has a grid to "
            "calibrate; section 6.1 names ordering depth as a family-specific "
            "quantity but never defines it",
            note="amendment A4 defines it as longest-chain cardinality and freezes "
                 "the generator with it, because a statistic alone does not fix what "
                 "the parameter manipulates. dci.v19.ordering.DECISION is the "
                 "implemented candidate. OrderingRelation.chain_depth counts EDGES "
                 "and is a diagnostic, not this parameter",
            domain="ordering_depth"),
    pending("verifiers.inherited_reuse_decision", "sections 4.3, 4.4, 10.6, 14.2",
            Resolution.PENDING_DECISION,
            "Stage 2: decide whether the audited Pair 2 and Pair 3 "
            "implementations are reused unchanged, corrected, or reimplemented. "
            "Section 14.2 permits reuse only after a hash and semantic audit; the "
            "audit has been performed and demonstrated defects, and section 10.6 "
            "requires that a demonstrated verifier defect be repaired and "
            "re-audited before freeze",
            note="the audit found that a zero-width space or homoglyph satisfies "
                 "the Pair 2 uniqueness rule while repeating a word, that a "
                 "non-ASCII mandatory word can never be matched, and that the "
                 "frozen sentence segmentation scores a bullet list as N "
                 "sentences; see docs/v19_stage2_gap_audit.md. Amendment A2 "
                 "dispositions this as 'corrected'; REUSE_DISPOSITION is the "
                 "implemented candidate",
            domain="reuse_disposition"),
    pending("verifiers.specification_bundle", "section 14.2 / Appendix I",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: the per-verifier table of declared-semantics and "
            "implementation hashes for all six target and focal verifiers, which "
            "dci.v19.verifiers.bundle_state computes once its inputs are frozen",
            depends_on=("verifiers.p1.list_policy", "verifiers.p1.ordering_depth",
                        "verifiers.inherited_reuse_decision"),
            note="the Pair 1 spec hashes contain the list-policy hash, so this "
                 "cannot be produced before that policy is a decision",
            domain="specification_bundle"),
    pending("verifiers.bundle_hash", "section 14.2 / Appendix I",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: implement and reconcile every deterministic verifier, then "
            "freeze the verifier bundle hash; Pair 1 bullet-count and "
            "transitive-order support must be built, and Pair 2/3 code may be "
            "reused only after a hash and semantic audit",
            depends_on=("verifiers.specification_bundle",
                        "verifiers.boundary_mutations"),
            note="Appendix I requires invariant verifier hashes across the run",
            domain="bundle_hash"),
    pending("verifiers.boundary_mutations", "section 8.7",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: at least 1,000 automated boundary mutations per constraint "
            "template covering off-by-one, duplication, omission, forbidden-item, "
            "ordering, formatting, Unicode and parser-edge cases",
            depends_on=("verifiers.specification_bundle",),
            note="property-based testing is evidence about implementation "
                 "invariants, not a proof of natural-language semantics. The domain "
                 "checks the record schema; whether the recorded hashes match a "
                 "battery the harness regenerates is checked at certification",
            domain="boundary_mutations"),
    pending("verifiers.binomial_interval_implementation", "section 10.4",
            Resolution.PENDING_DECISION,
            "Stage 2: recover the two-sided binomial interval implementation used "
            "by the inherited reliability gate and freeze it; section 10.4 makes "
            "the choice a pre-freeze decision rather than an implementer one if "
            "it is not uniquely recoverable",
            note="recovery succeeded and contradicts the request: the inherited "
                 "gate uses the Wilson score interval, which is not exact, and "
                 "only Wilson reproduces the 73-per-truth-class and 876-label "
                 "counts section 10.4 preserves (Clopper-Pearson gives 72 and "
                 "864). Both halves of that sentence cannot hold, so this is a "
                 "decision; see dci.v19.reliability.recover_inherited_interval. "
                 "Amendment A3 adopts 'clopper_pearson' and adds the register row "
                 "section 10.4 mis-cites as D9, which is the construction "
                 "bootstrap; dci.v19.reliability.REGISTER_ROW_D45 is that row",
            domain="binomial_interval"),
    pending("verifiers.tier1_audit_design",
            "section 10.4 + Stage 2 amendment A3, register row D45",
            Resolution.PENDING_DECISION,
            "Stage 2: fix the Tier-1 audit design prospectively - the per-truth-class "
            "sample size, the error budget, and whether the sample may be extended - "
            "because the interval alone does not determine a decision rule",
            depends_on=("verifiers.binomial_interval_implementation",),
            note="one error in 72 gives an exact upper bound of 0.0750 and fails; "
                 "the same error in 110 gives 0.0496 and would pass. 110 is the "
                 "SMALLEST sample at which one error clears the ceiling, so without "
                 "a fixed size the verdict would depend on an n chosen after the "
                 "errors were seen. dci.v19.reliability.AMENDED_TIER1_DESIGN is the "
                 "implemented candidate",
            domain="tier1_audit_design"),
    pending("verifiers.tier1_audit_protocol", "sections 10.4, 10.6",
            Resolution.PENDING_DECISION,
            "Stage 2: fix the Tier-1 audit's human procedure prospectively - how "
            "many reviewers judge each case independently, who adjudicates "
            "disagreement, and how exactly 72 adjudicated cases per truth class "
            "are reached given that the class is only known AFTER adjudication",
            depends_on=("verifiers.tier1_audit_design",),
            note="section 10.4 requires 'human-adjudicated' examples and never "
                 "says by how many reviewers or how disagreement resolves. Section "
                 "8.6's two-plus-adjudicator rule is scoped to SEMANTIC REVIEW of "
                 "compositions and does not extend here by itself, so reusing it "
                 "would be an implementer inventing a protocol detail. The "
                 "over-sampling question is real and unavoidable: a case's truth "
                 "class is established by the reviewers, so a manifest of exactly "
                 "72 per intended class reaches exactly 72 per ADJUDICATED class "
                 "only if every case lands where its author intended. See "
                 "docs/v19_tier1_audit_handoff.md",
            domain="tier1_audit_protocol"),
    pending("verifiers.tier1_reliability", "section 10.4",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: certify each target and focal verifier against the 5% "
            "Tier-1 conditional error ceiling using 72 human-adjudicated true "
            "failures and 72 true passes per verifier unit - 864 labels across the "
            "six units - with zero observed errors permitted",
            depends_on=("verifiers.binomial_interval_implementation",
                        "verifiers.tier1_audit_design",
                        "verifiers.tier1_audit_protocol",
                        "verifiers.bundle_hash")
            + tuple(f"pool.{pair}.audit" for pair in PAIR_IDS),
            note="72 rather than the inherited 73 because amendment A3 adopts the "
                 "exact interval, which reaches the 5% ceiling one label sooner. A "
                 "missing truth class is missing evidence, not zero error, so the "
                 "corresponding bound is unavailable and the unit fails. This is "
                 "human adjudication and cannot be produced by code. It depends "
                 "on pool.{p}.audit for all three pairs, because the 864 cases are "
                 "authored scientific content (section 11.1) and an audit with no "
                 "material is not an audit - an edge that was missing, so the "
                 "certificate could have been frozen with the pools still empty",
            domain="tier1_certificates"),
)


# --------------------------- Stage 2: whole-composition satisfiability certification

SATISFIABILITY_SLOTS = SlotTable.of(
    pending("satisfiability.review_trigger", "section 14.2 / section 8.6",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: the hash-frozen adversarial fixtures demonstrating that the "
            "semantic-review trigger fires when deterministic coverage is "
            "incomplete, stays silent when it is complete, rejects a review of the "
            "wrong witness, and requires adjudication of reviewer disagreement",
            depends_on=("satisfiability.encoding_map",
                        "satisfiability.witness_constructor"),
            note="section 14.2 assigns Stage 2 the review TRIGGERS; the reviews "
                 "themselves are per composition and are due at Stage 10, where "
                 "section 8.6 places SATCERT 'before entering a frozen "
                 "confirmatory bank'. Nothing escapes review: certify_composition "
                 "refuses any composition with an incompletely covered clause and "
                 "no passing review keyed to its own witness",
            domain="review_trigger"),
    pending("satisfiability.encoding_map", "D13 / sections 8.6, 14.2",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: freeze the canonical structured encoding of every constraint "
            "family and the abstract feature projection a solver sat result covers",
            depends_on=("verifiers.p1.list_policy",),
            note="the Pair 1 clauses embed the list-policy hash, because what "
                 "counts as a list item decides whether the encoding and the "
                 "verifier agree",
            domain="encoding_map"),
    pending("satisfiability.solver_identity", "D13 / section 8.6",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: record the frozen solver's name and exact version; section "
            "8.6 permits Z3 or an equivalently frozen solver, and a solver whose "
            "version is unrecorded is not frozen",
            note="unsat, unknown, timeout and missing solver output all fail "
                 "closed; only sat may support progression",
            domain="solver_identity"),
    pending("satisfiability.witness_constructor", "D13 / section 8.6",
            Resolution.PENDING_EMPIRICAL,
            "Stage 2: freeze the deterministic witness constructor, whose output is "
            "the stronger operational evidence a solver sat result cannot supply",
            depends_on=("satisfiability.encoding_map",),
            domain="witness_constructor"),
    pending("satisfiability.semantic_reviews", "D13 / sections 8.6, 14.10",
            Resolution.PENDING_DECISION,
            "Stage 10: two independent human reviews, with a third adjudicating "
            "disagreement, for every clause whose intended semantics the frozen "
            "encoding and deterministic verifier do not exhaust, for EVERY "
            "composition the bank accepts; unresolved disagreement fails "
            "certification",
            depends_on=("satisfiability.encoding_map",
                        "satisfiability.review_trigger"),
            note="due at Stage 10, not Stage 2. Section 14.2 assigns Stage 2 the "
                 "review TRIGGERS; section 8.6 places SATCERT 'before entering a "
                 "frozen confirmatory bank' and section 14.10 builds that bank. "
                 "Each pair has exactly one incompletely covered clause - Pair 1 "
                 "item identification, Pair 2 uniqueness under the frozen "
                 "tokenisation, Pair 3 sentence segmentation - so EVERY "
                 "composition needs a review. Granularity is per composition and "
                 "is not renegotiable against workload: two compositions differ "
                 "in their witness, and a review is a judgement about one "
                 "concrete text. Code must never stand in for the reviewer",
            domain="semantic_reviews"),
    pending("satisfiability.certified_compositions", "D13 / sections 8.6, 14.10",
            Resolution.PENDING_EMPIRICAL,
            "Stage 10: the SATCERT artifact per prospective A+B+S and "
            "A+R_j+S composition - encoding, solver input and output, witness and "
            "its construction procedure, the complete verifier vector, the semantic "
            "review where applicable, and the hashes tying them together",
            depends_on=("satisfiability.solver_identity",
                        "satisfiability.witness_constructor",
                        "satisfiability.semantic_reviews",
                        "verifiers.bundle_hash"),
            note="individual constraint validity and pairwise compatibility are "
                 "insufficient; the unit of certification is the whole arm",
            domain="certified_compositions"),
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
    pending("generation.confirmatory_outputs", "sections 14.15, 15.1",
            Resolution.PENDING_EMPIRICAL,
            "Stage 15: execute only the frozen generation manifest until every "
            "planned generation id has one durably persisted scientific output "
            "or a terminal permanent-technical-missingness record after the "
            "frozen retry policy",
            depends_on=("manifest.generation_manifest", "freeze.root_signature",
                        "runtime.certified_gpu_class"),
            note="section 15.1's fixed-size stopping rule is what makes it "
                 "complete; Stage 16 verifies that completeness and cannot "
                 "trigger new generation"),
    pending("ledger.terminal_states", "Appendix I / section 14.16",
            Resolution.PENDING_EMPIRICAL,
            "Stage 16: the frozen terminal observed/permanently-missing ledger, "
            "with exactly one terminal state per planned generation id",
            depends_on=("manifest.generation_manifest", "freeze.root_signature",
                        "generation.confirmatory_outputs")),
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
    for other in (SATISFIABILITY_SLOTS, QUALIFICATION_SLOTS, CONSTRUCTION_SLOTS, SIMULATION_SLOTS,
                  FREEZE_SLOTS, EXECUTION_SLOTS):
        table = table.merged(other)
    return table
