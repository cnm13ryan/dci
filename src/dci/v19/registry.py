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

from dci.v19 import (ALPHA, CANDIDATE_METHODS, PRIMITIVE_SUPPORT,
                     PROTOCOL_VERSION, SECONDARY_SUPPORT, SESOI_FLOOR)
from dci.v19 import field_roles, pairs, pools, specs
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


# Every stage that consumes a pre-freeze output, and what it needs first. Only
# the dependencies the preregistration states are listed; a stage absent from
# this map has no slot-level prerequisite rather than an unknown one.
STAGE_DEPENDENCIES: Mapping[str, tuple[str, ...]] = {
    # 14.3: outcome-independent checkpoint and accelerator/runtime freeze.
    "stage_3_runtime_freeze": ("runtime.checkpoint",),
    # 14.4: budget manipulation and the final-answer allowance.
    "stage_4_budget_manipulation": (
        "runtime.checkpoint", "runtime.selected_configuration",
        "budget.candidate_grid", "budget.separation_threshold",
        "pool.shared.manipulation_prompts"),
    # 14.5: exact SESOI if required, then boundary parameter calibration.
    "stage_5_parameter_calibration": (
        ("exact_epsilon",) + _per_pair("pool.{pair}.tasks.parameter_calibration")),
    # 14.6: candidate-reference hard eligibility and coupling.
    "stage_6_reference_eligibility": _per_pair(
        "pool.{pair}.candidate_references", "pool.{pair}.coupling_probes",
        "pool.{pair}.unrelated_targets"),
    # 14.7: paraphrases, wording instability, candidate-pool count.
    "stage_7_wording": _per_pair("pool.{pair}.wording_calibration"),
    # 14.8: matching calibration, simultaneous admission, validation.
    "stage_8_reference_admission": (
        ("exact_epsilon",)
        + _per_pair("pool.{pair}.candidate_references",
                    "pool.{pair}.tasks.independent_validation")),
    # 14.9: inference-method qualification and selection.
    "stage_9_method_selection": (
        "exact_epsilon", "inference.validity_results", "planning.h_max_caps",
        "budget.retained_set", "runtime.selected_configuration"),
    # 14.10: attainable superblock-bank construction.
    "stage_10_attainable_bank": (
        ("proposal.root_construction_seed", "proposal.construction_cap",
         "proposal.task_pmf", "inference.selected_method")
        + _per_pair("pool.{pair}.tasks.confirmation")
        + tuple(f"reference.{p}.R{i}" for p in pairs.PAIR_IDS
                for i in range(1, 5))),
    # 14.11: authoritative end-to-end (H, G) design simulation.
    "stage_11_design_simulation": (
        "inference.selected_method", "exact_epsilon",
        "controller.final_answer_allowance_v"),
    # 14.12: freeze numerical outputs and the scientific-draw manifest.
    "stage_12_freeze": (
        "exact_epsilon", "budget.retained_set",
        "controller.final_answer_allowance_v", "inference.selected_method",
        "runtime.certified_gpu_class", "falsification.battery"),
    # 14.13: final runtime re-certification.
    "stage_13_recertification": (
        "runtime.certified_gpu_class", "decoder.resolved_configuration_hash",
        "controller.identity_hash", "inference.production_code_hash"),
    # 14.15: confirmatory generation.
    "stage_15_confirmatory_generation": (
        "runtime.certified_gpu_class", "inference.selected_method",
        "budget.retained_set", "controller.final_answer_allowance_v"),
}


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
    def blockers_for(self, stage: str) -> tuple[Slot, ...]:
        """Which of a stage's declared prerequisites are still unresolved."""
        if stage not in STAGE_DEPENDENCIES:
            raise KeyError(
                f"{stage!r} has no declared slot-level prerequisites; known "
                f"stages: {', '.join(sorted(STAGE_DEPENDENCIES))}")
        return self.slots.blockers(*STAGE_DEPENDENCIES[stage])

    def require_stage(self, stage: str) -> None:
        """Fail closed unless every prerequisite of `stage` is resolved."""
        if stage not in STAGE_DEPENDENCIES:
            raise KeyError(f"{stage!r} is not a declared stage")
        self.slots.require(*STAGE_DEPENDENCIES[stage], what=stage)

    def stage_status(self, stage: str) -> dict[str, object]:
        """A completion-audit row for one stage, derived from the declarations.

        `status` is the ROOT blocker rather than the alphabetically first one:
        a prospective decision and unauthored content sit furthest upstream,
        hardware certification comes next, and a pending empirical output usually
        waits on one of those. Reporting the root is what tells an operator where
        to act; `all_blocking_statuses` keeps the rest visible.
        """
        blockers = self.blockers_for(stage)
        statuses = sorted({s.status for s in blockers})
        root = next((s for s in BLOCKER_PRECEDENCE if s in statuses), None)
        return {
            "stage": stage,
            "status": "READY" if not blockers else root,
            "root_blocker": root,
            "all_blocking_statuses": statuses,
            "blockers": [
                {"name": s.name, "prereg": s.prereg, "status": s.status,
                 "rule": s.rule} for s in blockers],
        }

    def audit(self) -> tuple[dict[str, object], ...]:
        """One row per stage with a declared prerequisite, in stage order."""
        return tuple(self.stage_status(stage) for stage in STAGE_DEPENDENCIES)

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
              tuple(sorted(field_roles.FIELD_ROLES))),
        fixed("design.material_splits", "section 11.1", pools.MATERIAL_SPLITS),
        fixed("design.background_strata", "section 8.2", pools.STRATA),
        fixed("design.candidate_methods", "D28 / section 12.4", CANDIDATE_METHODS),
        fixed("design.sesoi_floor", "D26 / section 11.9", SESOI_FLOOR),
        fixed("design.checkpoint_eligibility", "section 9.3",
              specs.CHECKPOINT_ELIGIBILITY),
        fixed("design.hardware_selection_rule", "section 9.4",
              HARDWARE_RULE_SUMMARY),
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


def build() -> Registry:
    """Assemble the Stage 1 registry from its declaring modules.

    Merging refuses overlapping slot names, so two modules cannot both claim to
    own the same pre-freeze output - the failure that would let one declaration
    silently win over another.
    """
    table = _fixed_commitments()
    for other in (pairs.declared_slots(), pools.declared_slots(),
                  pools.sufficiency_slots(), specs.declared_slots()):
        table = table.merged(other)
    return Registry(protocol=PROTOCOL_VERSION, slots=table)


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
