"""The Stage 1 registry: one place that knows what is settled and what is not.

Preregistration section 14.1 lists what Stage 1 freezes - the three rule
definitions, the exactly-four-reference requirement, family registries and schema
mappings where already known, candidate and reserve authoring rubrics, background
strata, material splits, the field-role registry, proposal distributions, the
decoder specification, the SESOI floor, checkpoint eligibility criteria, the
hardware benchmark rule, the inference-candidate specifications, and the
terminal-falsification design template.

This module assembles those pieces and answers two questions that are otherwise
scattered: *what does the protocol currently know*, and *what is a given stage
still waiting for*. Both matter because section 14 makes the dependency order
mandatory rather than advisory - "a later stage may consume frozen outputs from
earlier stages; it may not retrospectively change them" - and a stage that cannot
enumerate its own blockers will discover them one exception at a time.

The stage dependency map below is the executable form of that ordering. It is
deliberately expressed as "which declared slots must be resolved before this stage
runs", so `blockers_for()` produces the BLOCKED_BY_* report the completion audit
needs from the same declarations the runtime gate reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from dci.v19 import (
    ALPHA,
    CANDIDATE_METHODS,
    PRIMITIVE_SUPPORT,
    PROTOCOL_VERSION,
    SECONDARY_SUPPORT,
    SESOI_FLOOR,
    artifacts,
    field_roles,
    frozen,
    pairs,
    pools,
    specs,
)
from dci.v19.identity import ARMS, LOADS, ORDERS
from dci.v19.resolution import Slot, SlotTable

# Which blocking status to report as a stage's ROOT cause, most upstream first.
# A prospective scientific judgement and unauthored content are things only
# people can supply; hardware certification needs hardware; a pending empirical
# output usually waits on one of those. Reporting the root is what tells an
# operator where to act, which alphabetical order would not.
BLOCKER_PRECEDENCE = ("BLOCKED_BY_PROSPECTIVE_DECISION", "BLOCKED_BY_CONTENT",
                      "BLOCKED_BY_HARDWARE", "BLOCKED_BY_UPSTREAM_FREEZE")

def _per_pair(*templates: str) -> tuple[str, ...]:
    """Expand a slot-name template across all three pairs.

    The construction stages apply to every pair, so naming only one would give a
    gate that passes while two pairs are still unbuilt.
    """
    return tuple(t.format(pair=p) for t in templates for p in pairs.PAIR_IDS)


def _all_references() -> tuple[str, ...]:
    return tuple(f"reference.{p}.R{i}" for p in pairs.PAIR_IDS
                 for i in range(1, 5))


@dataclass(frozen=True)
class Requirement:
    """One dependency edge, with the text that makes it a requirement.

    The citation is not decoration. A gate whose edges cannot be traced to the
    preregistration is a gate someone can quietly widen, and the whole point of
    section 14's mandatory ordering is that widening it is a protocol change.
    """
    slot: str
    citation: str

    def __post_init__(self):
        if not self.slot or not self.citation:
            raise ValueError(
                f"dependency {self.slot!r} needs a preregistration citation; an "
                "uncited edge cannot be audited against the protocol")


def _req(citation: str, *slots: str) -> tuple[Requirement, ...]:
    return tuple(Requirement(slot=s, citation=citation) for s in slots)


@dataclass(frozen=True)
class StageGate:
    """One preregistered stage: what it needs, and what it produces."""
    key: str
    ordinal: str
    title: str
    citation: str
    requires: tuple[Requirement, ...] = ()
    produces: tuple[str, ...] = ()

    @property
    def required_slots(self) -> tuple[str, ...]:
        return tuple(r.slot for r in self.requires)


# The complete stage sequence of section 14, including the ones that were absent
# before: 2A, 14, 16 and 17. Stage 1 has no slot-level prerequisite because it is
# the first; that is a fact about the protocol, not an omission.
#
# Downstream stages depend on AGGREGATE freeze artifacts where the protocol
# provides one - section 14.12's root manifest hash and section 14.14's signed
# root manifest - rather than re-enumerating every primitive.
#
# That shortening loses no strictness only because the gate is transitive over
# STAGES, not just over `depends_on`: a stage is blocked by its own requirements
# and, recursively, by the requirements of every stage that produces one of them
# (`Registry.upstream_requirements`). Review found the `depends_on` chains alone
# did not carry this - Stage 15 could report READY with every confirmation pool
# unauthored and the Stage 10, 12 and 14 gates still blocked, because no
# aggregate's `depends_on` reached them. Section 14's ordering says a later stage
# consumes what an earlier stage produced, so an earlier stage's unmet
# requirement blocks everything downstream of it, and a requirement added to an
# upstream gate later propagates without editing any slot.
#
# Transitivity only follows `produces`, so a stage that declares no output cannot
# be reached by it. Stage 15 was such a stage, and Stage 16 could report READY
# before any confirmatory generation had run; it now produces
# `generation.confirmatory_outputs`, which Stage 16 requires.
STAGE_GATES: tuple[StageGate, ...] = (
    StageGate(
        key="stage_1_definitions", ordinal="1",
        title="scientific definitions, registries, splits, SESOI floor",
        citation="section 14.1",
        produces=("design.n_pairs", "design.loads", "design.orders",
                  "design.sesoi_floor", "decoder.specification",
                  "controller.specification", "proposal.law")),
    StageGate(
        key="stage_2_verifiers", ordinal="2",
        title="satisfiability and verifier infrastructure",
        citation="section 14.2",
        requires=(
            _req("section 14.2: Pair 1 support must be built and Pair 2/3 "
                 "code reused only after a hash and semantic audit",
                 "verifiers.boundary_mutations")
            + _req("sections 4.1 and 4.2 fix the two Pair 1 statements and name "
                   "the shared-parser coupling risk but fix no list-parsing "
                   "semantics, so the policy is a signed decision",
                   "verifiers.p1.list_policy")
            + _req("section 6.1 names ordering depth as a family-specific "
                   "parameter without defining what it ranges over, and Stage 5 "
                   "cannot calibrate a grid that does not exist",
                   "verifiers.p1.ordering_depth")
            + _req("section 14.2 permits Pair 2/3 reuse only after a hash and "
                   "semantic audit, and section 10.6 requires a demonstrated "
                   "verifier defect to be repaired and re-audited before freeze",
                   "verifiers.inherited_reuse_decision")
            + _req("section 10.4 freezes the two-sided binomial interval at "
                   "Stage 2, before dependent reliability audits",
                   "verifiers.binomial_interval_implementation")
            + _req("section 10.4 fixes the Tier-1 planning count prospectively, "
                   "and the interval alone does not determine a decision rule: "
                   "one error fails at 72 and passes at 110, so the sample size "
                   "and error budget must be fixed before the audit runs",
                   "verifiers.tier1_audit_design")
            + _req("section 14.2 assigns Stage 2 the semantic-review TRIGGERS. "
                   "The reviews themselves are per composition, and compositions "
                   "are Stage 8 and Stage 10 outputs, so requiring them here "
                   "would block Stage 2 on material later stages produce",
                   "satisfiability.review_trigger")),
        produces=("verifiers.specification_bundle", "verifiers.bundle_hash",
                  "verifiers.tier1_reliability", "satisfiability.encoding_map",
                  "satisfiability.solver_identity",
                  "satisfiability.witness_constructor",
                  "satisfiability.review_trigger")),
    StageGate(
        key="stage_2a_qualification", ordinal="2A",
        title="early scientific-runtime and inference qualification",
        citation="section 14.2A",
        requires=_req("section 14.2A qualifies candidate checkpoints before "
                      "expensive model-dependent construction",
                      "runtime.checkpoint"),
        produces=("qualification.stage2a",)),
    StageGate(
        key="stage_3_runtime_freeze", ordinal="3",
        title="outcome-independent checkpoint and accelerator/runtime freeze",
        citation="section 14.3",
        requires=(
            _req("section 14.3 selects the checkpoint by the frozen non-DCI "
                 "criteria", "runtime.checkpoint")
            + _req("section 9.4 precondition 2: the complete Stage 2A "
                   "correctness, determinism, replay, persistence and recovery "
                   "suite must pass before cost ranking",
                   "qualification.stage2a")),
        produces=("runtime.selected_configuration", "runtime.certified_gpu_class",
                  "runtime.transformers_version")),
    StageGate(
        key="stage_4_budget_manipulation", ordinal="4",
        title="budget manipulation and final-answer allowance",
        citation="section 14.4",
        requires=(
            _req("section 14.4 runs on the frozen checkpoint and runtime",
                 "runtime.checkpoint", "runtime.selected_configuration")
            + _req("section 9.8 authors the candidate grid and freezes the "
                   "separation criterion before manipulation outcomes are "
                   "evaluated",
                   "budget.candidate_grid", "budget.separation_threshold")
            + _req("section 11.1 permits an adapter/manipulation bank only when "
                   "demonstrably disjoint from all DCI content pools",
                   "pool.shared.manipulation_prompts")),
        produces=("budget.retained_set", "controller.final_answer_allowance_v")),
    StageGate(
        key="stage_5_parameter_calibration", ordinal="5",
        title="exact SESOI if required, then boundary parameter calibration",
        citation="section 14.5",
        requires=(
            _req("section 14.5 freezes exact epsilon before the first procedure "
                 "that numerically consumes it", "exact_epsilon")
            + _req("section 6.2: the screen applies under every budget, load and "
                   "order capable of entering the search set",
                   "budget.retained_set")
            + _req("section 14.5 uses the dedicated calibration split",
                   *_per_pair("pool.{pair}.tasks.parameter_calibration"))),
        produces=_per_pair("parameters.{pair}.admissible_set",
                           "parameters.{pair}.distribution")),
    StageGate(
        key="stage_6_reference_eligibility", ordinal="6",
        title="candidate-reference hard eligibility and coupling",
        citation="section 14.6",
        requires=(
            _req("section 14.6 starts from the 24 authored candidates and runs "
                 "the fixed coupling probe on unrelated targets",
                 *_per_pair("pool.{pair}.candidate_references",
                            "pool.{pair}.coupling_probes",
                            "pool.{pair}.unrelated_targets"))
            + _req("section 14.6 applies the boundary gate, which consumes the "
                   "calibrated admissible parameter sets",
                   *_per_pair("parameters.{pair}.admissible_set"))
            + _req("section 14.2 requires the deterministic verifiers before any "
                   "verifier gate can be applied", "verifiers.bundle_hash")
            + _req("section 14.6: if the probe-expansion branch requires the "
                   "epsilon/8 precision target, exact epsilon must be frozen "
                   "before any expansion data are generated", "exact_epsilon")),
        produces=_per_pair("eligibility.{pair}.hard_gates",
                           "coupling.{pair}.audit")),
    StageGate(
        key="stage_7_wording", ordinal="7",
        title="semantic paraphrases, wording instability, candidate-pool count",
        citation="section 14.7",
        requires=(
            _req("section 14.7 certifies wordings on the dedicated calibration "
                 "material", *_per_pair("pool.{pair}.wording_calibration"))
            + _req("section 14.7 certifies wordings for the surviving relevant "
                   "constraints, so hard eligibility comes first",
                   *_per_pair("eligibility.{pair}.hard_gates"))),
        produces=_per_pair("wording.{pair}.instability")),
    StageGate(
        key="stage_8_reference_admission", ordinal="8",
        title="reference-matching calibration, admission, independent validation",
        citation="section 14.8",
        requires=(
            _req("section 14.8 freezes exact epsilon before any matching "
                 "caliper, sensitivity coefficient or allowance that depends on "
                 "it", "exact_epsilon")
            + _req("section 14.8 ranks only already-eligible candidates, using "
                   "the coupling and wording outcomes",
                   *_per_pair("coupling.{pair}.audit",
                              "wording.{pair}.instability"))
            + _req("section 7.10 runs the complete disjoint independent-"
                   "validation procedure",
                   *_per_pair("pool.{pair}.tasks.independent_validation"))),
        produces=_per_pair("matching.{pair}.constants",
                           "validation.{pair}.independent") + _all_references()),
    StageGate(
        key="stage_9_method_selection", ordinal="9",
        title="inference-method qualification and selection",
        citation="section 14.9",
        requires=(
            _req("section 14.9: exact epsilon must already have been fixed",
                 "exact_epsilon")
            + _req("section 14.9 executes all validity fixtures, including the "
                   "validity-critical WSR truncation-transition bank",
                   "inference.validity_results")
            + _req("section 13.3 freezes the pair-specific planning caps before "
                   "any comparison output is viewed", "planning.h_max_caps")
            + _req("section 14.9 maps the theorems under the now-frozen "
                   "superblock law, decoder and runtime",
                   "budget.retained_set", "runtime.selected_configuration")
            + _req("section 13.1: method comparison occurs after the "
                   "checkpoint/runtime AND references are frozen",
                   *_all_references())),
        produces=("inference.selected_method", "simulation.method_comparison",
                  "inference.production_code_hash",
                  "inference.reference_code_hash")),
    StageGate(
        key="stage_10_attainable_bank", ordinal="10",
        title="attainable superblock-bank construction",
        citation="section 14.10",
        requires=(
            _req("section 8.3 freezes the root construction seed and canonical "
                 "sampler before the first confirmatory superblock is realised",
                 "proposal.root_construction_seed", "proposal.task_pmf")
            + _req("section 13.3 predeclares the construction cap",
                   "proposal.construction_cap")
            + _req("section 14.10 builds the bank after the Stage 9 method is "
                   "frozen", "inference.selected_method")
            + _req("section 8.3 step 1 draws the task from the frozen "
                   "confirmation population",
                   *_per_pair("pool.{pair}.tasks.confirmation"))
            + _req("section 8.3 step 2 draws exactly one background identity "
                   "from each of the three frozen strata",
                   *_per_pair("pool.{pair}.backgrounds.lexical_content",
                              "pool.{pair}.backgrounds.structural_format",
                              "pool.{pair}.backgrounds.relational_order"))
            + _req("section 8.3 step 3 draws each active constraint's parameter "
                   "from its own frozen distribution",
                   *_per_pair("parameters.{pair}.distribution"))
            + _req("section 8.3 step 5 evaluates the proposal in the focal arm "
                   "and all four reference arms", *_all_references())
            + _req("section 8.7 requires whole-composition certification, which "
                   "needs the deterministic verifier conjunction",
                   "verifiers.bundle_hash")
            + _req("section 8.6 requires human semantic review for every clause "
                   "the frozen encoding and deterministic verifier do not "
                   "exhaust, and unresolved disagreement fails certification. "
                   "Section 8.6 places SATCERT 'before entering a frozen "
                   "confirmatory bank', and section 14.10 builds that bank here, "
                   "so this is where the reviews are due",
                   "satisfiability.semantic_reviews")),
        produces=_per_pair("bank.{pair}.attainable_count",
                           "bank.{pair}.accepted_order")
        + ("satisfiability.certified_compositions",)),
    StageGate(
        key="stage_11_design_simulation", ordinal="11",
        title="authoritative end-to-end (H, G) design simulation",
        citation="section 14.11",
        requires=(
            _req("section 14.11 runs through the single method frozen at Stage 9",
                 "inference.selected_method")
            + _req("section 13.2 simulates scenarios at Theta = 0, epsilon and "
                   "2 epsilon", "exact_epsilon")
            + _req("section 14.11 evaluates only attainable designs, so the "
                   "realised counts come first",
                   *_per_pair("bank.{pair}.attainable_count"))
            + _req("section 14.11 uses the measured runtime-cost model",
                   "runtime.cost_model")
            + _req("section 13.3 accounts for the complete generation envelope",
                   "controller.final_answer_allowance_v")),
        produces=("simulation.authoritative_design",
                  "simulation.counterfactual_diagnostic", "design.final_h_p",
                  "design.replicates_g")),
    StageGate(
        key="stage_12_freeze", ordinal="12",
        title="freeze numerical pre-confirmatory outputs and the draw manifest",
        citation="section 14.12",
        requires=(
            _req("section 14.12 freezes exact epsilon, retained budgets, V and "
                 "the selected inference method",
                 "exact_epsilon", "budget.retained_set",
                 "controller.final_answer_allowance_v",
                 "inference.selected_method")
            + _req("section 14.12 freezes P_Q and nu_Q",
                   *_per_pair("parameters.{pair}.admissible_set",
                              "parameters.{pair}.distribution"))
            + _req("section 14.12 freezes the four reference identities per pair "
                   "and the matching constants",
                   *(_all_references()
                     + _per_pair("matching.{pair}.constants",
                                 "validation.{pair}.independent")))
            + _req("section 14.12 freezes the final H_p and G",
                   "design.final_h_p", "design.replicates_g")
            + _req("section 14.12 selects the first H_p accepted superblocks "
                   "under the frozen bank order",
                   *_per_pair("bank.{pair}.accepted_order"))
            + _req("section 14.12 freezes the runtime/hardware identities",
                   "runtime.certified_gpu_class")
            + _req("section 14.12 freezes the terminal-falsification fixtures "
                   "and rules", "falsification.battery")),
        produces=("manifest.generation_manifest", "manifest.root_hash")),
    StageGate(
        key="stage_13_recertification", ordinal="13",
        title="final runtime re-certification",
        citation="section 14.13",
        requires=(
            _req("section 14.13 re-certifies the already qualified frozen "
                 "configuration and intended confirmatory GPU pool",
                 "runtime.certified_gpu_class",
                 "decoder.resolved_configuration_hash",
                 "controller.identity_hash", "inference.production_code_hash")
            + _req("section 14.13 compares all hashes to the Stage 2A and "
                   "Stage 3 baselines", "qualification.stage2a")
            + _req("section 14.13 re-runs the manifest fail-closed tests, which "
                   "requires the frozen scientific manifest",
                   "manifest.root_hash")),
        produces=("recertification.stage13",)),
    StageGate(
        key="stage_14_freeze_signing", ordinal="14",
        title="immutable protocol and analysis freeze",
        citation="section 14.14",
        requires=(
            _req("section 14.14 signs the scientific-draw manifest and the root "
                 "SHA-256 manifest", "manifest.root_hash")
            + _req("section 14.13: any recertification failure blocks "
                   "confirmation", "recertification.stage13")
            + _req("section 14.14 signs the construction artifacts, inference "
                   "code, simulation outputs and terminal-falsification plan",
                   "verifiers.bundle_hash", "inference.production_code_hash",
                   "inference.reference_code_hash",
                   "simulation.authoritative_design",
                   "simulation.counterfactual_diagnostic",
                   "falsification.battery")),
        produces=("freeze.root_signature",)),
    StageGate(
        key="stage_15_confirmatory_generation", ordinal="15",
        title="confirmatory generation",
        citation="section 14.15",
        requires=(
            _req("section 14.15: execute ONLY the frozen generation manifest",
                 "manifest.generation_manifest")
            + _req("section 14.14 records that no confirmatory output exists "
                   "before the signed freeze timestamp, so the signature is the "
                   "execution authority", "freeze.root_signature")
            + _req("section 14.15 replays failures only within the certified "
                   "interchangeability class", "runtime.certified_gpu_class")),
        produces=("generation.confirmatory_outputs",)),
    StageGate(
        key="stage_16_locked_inference", ordinal="16",
        title="locked confirmatory inference",
        citation="section 14.16",
        requires=(
            _req("section 14.16 verifies completeness and integrity against the "
                 "frozen manifest", "manifest.generation_manifest",
                 "manifest.root_hash")
            + _req("section 14.16 verifies the completeness of the confirmatory "
                   "generation, which ends under section 15.1's fixed-size "
                   "stopping rule", "generation.confirmatory_outputs")
            + _req("section 14.16 runs the single preselected analysis code once",
                   "freeze.root_signature")),
        produces=("ledger.terminal_states", "analysis.code_hash",
                  "analysis.confirmatory_outputs")),
    StageGate(
        key="stage_17_terminal_falsification", ordinal="17",
        title="sequestered terminal falsification",
        citation="section 14.17",
        requires=_req(
            "section 14.17: only after the confirmatory outputs and the analysis "
            "hash are locked may the terminal-falsification material be opened",
            "analysis.confirmatory_outputs", "analysis.code_hash",
            "falsification.battery"),
        produces=("falsification.result",)),
)

# The complete preregistered stage sequence. A meta-test asserts that STAGE_GATES
# covers exactly this, so a stage cannot be forgotten again.
MANDATORY_STAGE_ORDINALS = ("1", "2", "2A", "3", "4", "5", "6", "7", "8", "9",
                            "10", "11", "12", "13", "14", "15", "16", "17")

STAGE_GATE_BY_KEY: Mapping[str, StageGate] = {g.key: g for g in STAGE_GATES}

# Derived view, kept because it is the simplest thing to read and to assert on.
STAGE_DEPENDENCIES: Mapping[str, tuple[str, ...]] = {
    g.key: g.required_slots for g in STAGE_GATES}

# Which stage produces each output. An output has at most one producer.
PRODUCING_STAGE: Mapping[str, StageGate] = {
    slot: g for g in STAGE_GATES for slot in g.produces}


@dataclass(frozen=True)
class Registry:
    """Everything Stage 1 declares, with the pending outputs it does not have."""
    protocol: str
    slots: SlotTable

    # ------------------------------------------------------------- accessors
    @property
    def pair_ids(self) -> tuple[str, ...]:
        return pairs.PAIR_IDS

    @property
    def loads(self) -> tuple[int, ...]:
        return LOADS

    @property
    def orders(self) -> tuple[str, ...]:
        return ORDERS

    @property
    def arms(self) -> tuple[str, ...]:
        return ARMS

    @property
    def fingerprint(self) -> str:
        """The declaration identity, stable as pre-freeze outputs arrive."""
        return self.slots.fingerprint

    @property
    def state_fingerprint(self) -> str:
        """The freeze-state identity, which changes as outputs are produced."""
        return self.slots.state_fingerprint

    # ---------------------------------------------------------- the stage gate
    def gate(self, stage: str) -> StageGate:
        if stage not in STAGE_GATE_BY_KEY:
            raise KeyError(
                f"{stage!r} is not a declared stage; known stages: "
                f"{', '.join(g.key for g in STAGE_GATES)}")
        return STAGE_GATE_BY_KEY[stage]

    def requirement_sources(self, stage: str) -> dict[str, StageGate]:
        """Every slot `stage` needs, mapped to the stage that declares the need.

        A stage's own requirements come first. Then, for each required slot that an
        earlier stage produces, that stage's requirements are needed too, and so on
        upstream: the producing stage could not legitimately have produced its
        output while one of its own prerequisites was unmet. A stage that requires
        one of its own outputs (Stage 2 and `satisfiability.review_trigger`) is not
        re-entered.
        """
        root = self.gate(stage)
        sources: dict[str, StageGate] = {}
        visited = {root.key}
        queue: list[tuple[str, StageGate]] = [(slot, root) for slot in root.required_slots]
        while queue:
            slot, declared_by = queue.pop(0)
            if slot in sources:
                continue
            sources[slot] = declared_by
            producer = PRODUCING_STAGE.get(slot)
            if producer is not None and producer.key not in visited:
                visited.add(producer.key)
                queue.extend((s, producer) for s in producer.required_slots)
        return sources

    def upstream_requirements(self, stage: str) -> tuple[str, ...]:
        """`requirement_sources` as names, own requirements first."""
        return tuple(self.requirement_sources(stage))

    def blockers_for(self, stage: str) -> tuple[Slot, ...]:
        """Which prerequisites of `stage`, its own or inherited from the stages that
        produce its inputs, are still unresolved."""
        return self.slots.blockers(*self.upstream_requirements(stage))

    def require_stage(self, stage: str) -> None:
        """Fail closed unless every prerequisite of `stage`, including those of the
        stages that produce its inputs, is resolved."""
        gate = self.gate(stage)
        self.slots.require(*self.upstream_requirements(stage),
                           what=f"Stage {gate.ordinal} ({gate.title})")

    def citation_for(self, stage: str, slot: str) -> str:
        """Why a stage depends on a slot, in the preregistration's own words."""
        for requirement in self.gate(stage).requires:
            if requirement.slot == slot:
                return requirement.citation
        raise KeyError(f"Stage {stage} does not declare a dependency on {slot!r}")

    def stage_status(self, stage: str) -> dict[str, object]:
        """A completion-audit row for one stage, derived from the declarations.

        `status` is the ROOT blocker rather than the alphabetically first one:
        a prospective decision and unauthored content sit furthest upstream,
        hardware certification comes next, and a pending empirical output usually
        waits on one of those. Reporting the root is what tells an operator where
        to act; `all_blocking_statuses` keeps the rest visible.
        """
        gate = self.gate(stage)
        blockers = self.blockers_for(stage)
        sources = self.requirement_sources(stage)
        statuses = sorted({s.status for s in blockers})
        root = next((s for s in BLOCKER_PRECEDENCE if s in statuses), None)
        return {
            "stage": stage,
            "ordinal": gate.ordinal,
            "title": gate.title,
            "citation": gate.citation,
            "status": "READY" if not blockers else root,
            "root_blocker": root,
            "all_blocking_statuses": statuses,
            "n_required": len(gate.required_slots),
            "n_required_including_upstream": len(sources),
            "produces": list(gate.produces),
            "blockers": [
                {"name": s.name, "prereg": s.prereg, "status": s.status,
                 "rule": s.rule,
                 "required_by": sources[s.name].key,
                 "why_required": self.citation_for(sources[s.name].key, s.name)}
                for s in blockers],
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        """One row per stage with a declared prerequisite, in stage order."""
        return tuple(self.stage_status(g.key) for g in STAGE_GATES)

    def statuses(self) -> dict[str, int]:
        return self.slots.statuses()

    def unresolved(self) -> tuple[Slot, ...]:
        return self.slots.unresolved()


# Fixed scientific commitments that are not produced by any procedure. Declared
# here rather than scattered so the registry can be asked what the protocol
# states without consulting five modules.
def _fixed_commitments() -> SlotTable:
    from dci.v19.resolution import fixed
    return SlotTable.of(
        fixed("design.protocol_version", "section 1.2", PROTOCOL_VERSION),
        fixed("design.n_pairs", "D2 / section 5.1", len(pairs.PAIRS)),
        fixed("design.n_references_per_pair", "D3 / section 5.1",
              len(pairs.PAIR_1.references),
              note="exactly four independently admitted references; primitive "
                   "effects stay reference-specific with no primary averaging"),
        fixed("design.loads", "D5 / section 8.1", LOADS,
              note="maximum-load feasibility is established first; k=2 is the "
                   "paired restriction obtained by removing the backgrounds"),
        fixed("design.orders", "D5 / section 4.2", ORDERS,
              note="a crossed primary moderator; no primary analysis averages "
                   "o_A and o_Q before inference"),
        fixed("design.arms", "section 11.3", ARMS),
        fixed("design.primitive_support", "D32 / section 12.3", PRIMITIVE_SUPPORT),
        fixed("design.secondary_support", "D33 / section 12.3", SECONDARY_SUPPORT),
        fixed("design.alpha", "D34 / section 12.11", ALPHA),
        fixed("design.stopping_rule", "section 15.1", "fixed-size",
              note="no optional stopping on effect size, significance, interval "
                   "width, favourable reference, runtime convenience, or "
                   "apparent stability"),
        fixed("design.severity_coordinate_excluded", "D7 / section 6.5", True,
              note="no scalar severity coordinate is constructed to make "
                   "heterogeneous parameter quantities commensurable"),
        fixed("design.field_roles", "section 11.8",
              {role: list(fields)
               for role, fields in sorted(field_roles.FIELD_ROLES.items())},
              note="the field-to-role ASSIGNMENT, not just the role names: "
                   "moving a field between roles changes what primary analysis "
                   "may consume, so it must change the fingerprint"),
        fixed("design.material_splits", "section 11.1", pools.MATERIAL_SPLITS),
        fixed("design.background_strata", "section 8.2", pools.STRATA),
        fixed("design.candidate_methods", "D28 / section 12.4", CANDIDATE_METHODS),
        fixed("design.sesoi_floor", "D26 / section 11.9", SESOI_FLOOR),
        fixed("design.checkpoint_eligibility", "section 9.3",
              specs.CHECKPOINT_ELIGIBILITY),
        fixed("design.hardware_selection_rule", "section 9.4",
              {"summary": HARDWARE_RULE_SUMMARY, **specs.HARDWARE_SELECTION},
              note="the structured rule, so the measured quantities, the "
                   "tie-break chain and the forbidden inputs are all covered"),
        fixed("design.pair_definitions", "D2 / section 5.1",
              pairs.rule_definitions(),
              note="the complete fixed rule semantics, verifier bindings and "
                   "parameter names for all three pairs"),
        fixed("design.candidate_pool_rule", "D8 / section 7.2",
              "24 authored candidates plus at most one blind tranche of 12; at "
              "least 12 hard-eligible survivors required before matching"),
        fixed("design.construction_bootstrap", "D9 / section 7.5",
              "complete construction clusters U_i, exactly 10,000 replicates"),
    )


HARDWARE_RULE_SUMMARY = (
    "benchmark every eligible configuration from the provider's current "
    "instance-type API, rank by cost per 1,000 valid logical generations, break "
    "ties by failure rate then throughput then configuration id, and admit no "
    "DCI outcome as an input")


def declared_table() -> SlotTable:
    """Every slot the protocol declares, with all pre-freeze outputs still pending.

    Merging refuses overlapping slot names, so two modules cannot both claim to
    own the same pre-freeze output - the failure that would let one declaration
    silently win over another.

    Kept separate from `build` so a test can ask what the protocol DECLARES
    without the recorded outputs applied. That is also what the declaration
    fingerprint is a hash of.
    """
    table = _fixed_commitments()
    for other in (pairs.declared_slots(), pools.declared_slots(),
                  pools.sufficiency_slots(), specs.declared_slots(),
                  artifacts.declared_slots()):
        table = table.merged(other)
    return table


def build() -> Registry:
    """The declared registry with every recorded Stage 2 output applied.

    `frozen.apply` refuses a record whose own prerequisites are still unresolved,
    so a hand-edited file cannot bypass the ordering section 14 makes mandatory,
    and every value passes through `Slot.freeze` and its typed domain on the way
    in. A recorded output the code can no longer reproduce therefore fails at
    IMPORT rather than at whatever later stage happens to read it.
    """
    return Registry(protocol=PROTOCOL_VERSION,
                    slots=frozen.apply(declared_table()))


REGISTRY = build()


def assert_stage_one_complete() -> None:
    """Everything section 14.1 says Stage 1 freezes is actually declared.

    A structural check, not a scientific one: it establishes that the registry
    covers the required ground, and says nothing about whether the material
    behind the pending entries has been authored.
    """
    pairs.assert_pair_structure()
    field_roles.assert_roles_well_formed()
    required = (
        "design.n_pairs", "design.n_references_per_pair", "design.loads",
        "design.orders", "design.primitive_support", "design.secondary_support",
        "design.alpha", "design.sesoi_floor", "design.material_splits",
        "design.background_strata", "design.candidate_methods",
        "design.field_roles", "design.checkpoint_eligibility",
        "design.hardware_selection_rule", "design.candidate_pool_rule",
        "design.severity_coordinate_excluded", "design.stopping_rule",
        "decoder.specification", "controller.specification", "proposal.law",
        "multiplicity.per_family_alpha", "falsification.sequencing",
    )
    REGISTRY.slots.require(*required, what="Stage 1 (section 14.1)")


def assert_nothing_fabricated() -> None:
    """The quantities the protocol reserves for later procedures are unresolved.

    Section 16 of the implementation directive names these explicitly. Keeping the
    list here means the prohibition is checked against the assembled registry
    rather than module by module, so a value appearing anywhere is caught.
    """
    from dci.v19.resolution import assert_no_fabricated_values
    assert_no_fabricated_values(REGISTRY.slots, {
        "exact_epsilon": "signed prospective",
        "budget.retained_set": "separation criterion",
        "controller.final_answer_allowance_v": "disjoint pre-confirmatory",
        "inference.selected_method": "validity-first",
        "runtime.checkpoint": "non-DCI",
        "runtime.selected_configuration": "outcome-independent",
        "runtime.certified_gpu_class": "cross-device replay",
        "planning.h_max_caps": "before any comparison output",
        "proposal.root_construction_seed": "before the first confirmatory",
        "falsification.battery": "sequestered",
    })
    for pair in pairs.PAIRS:
        for slot in pair.references:
            if slot.admitted:
                raise AssertionError(
                    f"{slot.identity.name} carries a reference identity; the "
                    "four admitted references are a Stage 8 output")


def report() -> dict[str, object]:
    """A compact machine-readable summary for the completion audit."""
    return {
        "protocol": REGISTRY.protocol,
        "declaration_fingerprint": REGISTRY.fingerprint,
        "state_fingerprint": REGISTRY.state_fingerprint,
        "n_slots": len(REGISTRY.slots),
        "statuses": REGISTRY.statuses(),
        "stages": REGISTRY.audit(),
        "unimplemented_verifiers": [
            v.verifier_id for v in pairs.unimplemented_verifiers()],
    }
