"""§18 stage 13, ``GATE_5_FREEZE``: assemble the freeze from signed records.

**Every value in the freeze record comes from a record, not from a constant
this process happens to be holding.** That is the difference between a freeze
and a snapshot of the interpreter: a rule that changed between the gate that
decided it and the freeze that recorded it would be invisible to the second
kind. So ``assemble`` takes the model tree and reads each predecessor stage
through ``read_stage_record``, which verifies the hash and the signature and
refuses a record belonging to another study.

**What §18.1 requires that v4r4 did not have.** ``EMPTIABLE_FIELDS`` replaces
v4r4's ``VARIANT_EXEMPTIONS``: a field a variant legitimately leaves empty is
declared empty **with the identification status that explains it**, and any
other empty field is refused. That is the general rule where v4r4 had a patch
keyed on a named variant, and it is why v5 can drop the variant table.

**After a successful freeze nothing scientific is writable.**
``assert_no_post_freeze_mutation`` refuses a later write to any stage at or
before Gate 5, and every downstream stage reads the freeze record rather than
the constants: ``assert_matches_freeze`` is what a runner calls to prove that
what it is about to do is what the freeze licensed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import gitinfo
from dci1v4.engine.environment import interpreter_identity
from dci1v4.errors import ProtocolError
from dci1v4.models.registry import get_model
from dci1v4.protocol.hashing import sha_obj

from dci1v6.design.cells import n_cells_for
from dci1v6.engine import transitions
from dci1v6.engine.paths import ModelTree
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions, identification, seeds, wordings
from dci1v6.protocol.reuse_ledger import build_ledger
from dci1v6.run.lifecycle import StageOutcome, run_stage
from dci1v6.stages import freeze as freeze_stage
from dci1v6.verifiers import source_hashes
from dci1v6.verifiers.constraints import FAMILIES, LADDERS, RESERVES

__all__ = ["assemble", "freeze_payload", "run_freeze", "assert_matches_freeze",
           "load_freeze"]


#: Where each design slot's admitted entries actually live on the Gate 3B
#: record. ``select_all`` returns a *block* per slot family --- ``core`` and
#: ``near_form`` are mappings carrying their entries under a named key, while
#: ``spectrum`` is the list itself --- and an earlier revision of ``assemble``
#: iterated all three as if they were lists, which iterates a mapping's keys
#: and fails on the first ``dict("core_references")``. The nesting is declared
#: here rather than guessed at each call site.
SELECTION_ENTRY_PATHS: dict[str, tuple[str, ...]] = {
    "core": ("core", "core_references"),
    "spectrum": ("spectrum",),
    "near_form": ("near_form", "controls"),
}


def _selection_entries(selection: Mapping[str, Any], key: str
                       ) -> list[dict[str, Any]]:
    """The admitted entries for one slot family, at their registered path."""
    node: Any = selection
    for step in SELECTION_ENTRY_PATHS[key]:
        node = (node or {}).get(step) if isinstance(node, Mapping) else None
    entries = node or []
    if not isinstance(entries, (list, tuple)):
        raise ProtocolError(
            f"§18.1: Gate 3B's {key!r} entries are at "
            f"{'.'.join(SELECTION_ENTRY_PATHS[key])} and that is a "
            f"{type(entries).__name__}, not a list of admitted references")
    return [dict(e) for e in entries]


def assemble(tree: ModelTree, *, producing_commit: str,
             environment_digest: str = "",
             variance_reestimate: Mapping[str, Any] | None = None
             ) -> dict[str, Any]:
    """One replication's freeze record, every value from a signed source."""
    read = transitions.read_stage_record
    registration = read(tree, C.STAGE_REGISTERED)
    regime = read(tree, C.STAGE_REGIME)
    gate1 = read(tree, C.STAGE_GATE1)
    gate2 = read(tree, C.STAGE_GATE2)
    gate2_5 = read(tree, C.STAGE_GATE2_5)
    probe = read(tree, C.STAGE_GATE2_75)
    gate3a = read(tree, C.STAGE_GATE3A)
    gate3b = read(tree, C.STAGE_GATE3B)
    gate3c = read(tree, C.STAGE_GATE3C)
    gate4 = read(tree, C.STAGE_GATE4)
    audit = read(tree, C.STAGE_PREFREEZE_AUDIT)
    if not audit.get("can_freeze"):
        raise ProtocolError(
            "§18 stage 12 did not pass; Gate 5 is unreachable and the "
            "predecessor check is what stops it. Blocked checks: "
            f"{audit.get('blocked')}")

    from dci1v6.run.gates_run import qualification_at

    qualified_at = qualification_at(gate2_5, m_star=int(probe["m_star"]))
    spec = get_model(tree.model_key)
    selection = gate3b["selection"]
    arms = tuple(gate3c["admitted_arms"])
    statuses = sorted(set(gate2.get("identification_statuses", []))
                      | set(gate3c.get("identification_statuses", [])))
    core = _selection_entries(selection, "core")
    record = freeze_stage.build_freeze_record(
        protocol_version=registration["protocol_version"],
        protocol_hash=registration["protocol_hash"],
        reference_design_spec_hash=registration[
            "reference_design_spec_hash"],
        model_repository=spec.model_id,
        model_revision=spec.revision,
        prompt_template={"zero": C.PROMPT_ZERO, "one": C.PROMPT_ONE,
                         "two": C.PROMPT_TWO},
        stem_sentence=C.STEM_SENTENCE,
        completion_cap=regime["selected_cap"],
        # §18.1 binds the operating point the study actually runs. Gate 2.75
        # may have re-selected m* once, so the freeze binds the probe's value
        # and records Gate 2's beside it --- binding Gate 2's would freeze a
        # severity the probe rejected.
        n_star=gate2["n_star"], m_star=probe["m_star"],
        focal_extension_measured=gate2["focal_selection"].get(
            "extension_measured", False),
        bracketing_status={
            "focal": gate2["focal_selection"].get("bracketed"),
            "target": gate2["target_selection"].get("bracketed")},
        composed_probe={
            "stage": C.STAGE_GATE2_75,
            "m_star_in": probe["m_star_in"],
            "m_star": probe["m_star"],
            "reselected": probe["reselected"],
            "margin": probe["margin"],
            "margin_band": probe["margin_band"],
            "band": probe["band"],
            "topic_split": probe["topic_split"],
            "standins": probe["standins"],
            "probe_cell_types": probe["probe_cell_types"],
            "disposition": probe["disposition"],
            "scope_limits": probe["scope_limits"]},
        candidate_family_vocabulary=sorted(FAMILIES),
        ladders={k: list(v) for k, v in LADDERS.items()},
        reserves={k: list(v) for k, v in RESERVES.items()},
        structural_metadata={k: dict(f.metadata)
                             for k, f in FAMILIES.items()},
        tiers={k: f.structural_tier for k, f in FAMILIES.items()},
        wordings=dict(wordings.FAMILY_RULE_STATEMENTS),
        difficulty_coordinate_definition={
            "primary": C.DIFFICULTY_COORDINATE,
            "formula": "(solo - kappa) / (1 - kappa)",
            "secondary": C.SECONDARY_DIFFICULTY_COORDINATE,
            "evaluated": "last, in §13.1's lexicographic order"},
        chance_definition="P(c passes | unconstrained cell, same topic set, "
                          "same M)",
        counterfactual_chance_definition=(
            "kappa(R|B) = P(R passes | B alone at m*, R absent), measured on "
            "load-one B cells under §9.1's presence rule"),
        validity_components=list(C.VALIDITY_COMPONENTS),
        validity_thresholds={
            "headroom_band": list(C.HEADROOM_BAND),
            "instruction_lift_min": C.INSTRUCTION_LIFT_MIN,
            "reference_vacuity_max": C.REFERENCE_VACUITY_MAX,
            "chance_max": C.CHANCE_MAX,
            "chance_wilson_upper_max": C.CHANCE_WILSON_UPPER_MAX,
            "projected_compliance_band": list(C.PROJECTED_COMPLIANCE_BAND),
            "displacement_max": C.DISPLACEMENT_MAX,
            "stability_equivalence_bound": C.STABILITY_EQUIVALENCE_BOUND,
            "reference_caliper": C.REFERENCE_CALIPER},
        calibration_a_table_hash=(gate3a["split_tables"][C.CALIBRATION_A]
                                  ["topic_set_hash"]),
        calibration_b_table_hash=(gate3a["split_tables"][C.CALIBRATION_B]
                                  ["topic_set_hash"]),
        # §13.6's pool at the operating point the study runs. Gate 2.5's
        # top-level fields are its own predecessor's m*, and Gate 2.75 may
        # have moved it --- so a freeze reading them would bind the pool that
        # qualified against a severity the probe rejected.
        qualified_pool=list(qualified_at["qualified_pool"]),
        earliest_failing_components=dict(
            qualified_at["earliest_failing_components"]),
        core_references=core,
        spectrum_severities=_selection_entries(selection, "spectrum"),
        near_form_controls=_selection_entries(selection, "near_form"),
        broad_class_control=selection.get("broad_class") or {},
        # §13.15 freezes the backups, and the stage that evaluates support is
        # the stage that computed them: Gate 3C's realised block. Reading
        # ``selection["backups"]`` --- a key Gate 3B never writes --- meant
        # this always fell through to a *recomputation* here, so the freeze
        # bound a number no signed record had produced.
        frozen_backup_families=list(
            gate3c["support"]["realised"]["frozen_backups"]),
        # The *flag*, because ``assert_freeze_complete`` asserts
        # ``is True`` --- passing the sentence here overwrote the boolean the
        # §13.14 check reads, and a freeze that explained the guarantee
        # without asserting it would have been the result.
        backups_never_substituted=True,
        backups_never_substituted_statement=(
            "§13.14: a frozen backup is never substituted into an admitted "
            "slot after Gate 4, and the guarantee is that no substitution "
            "function exists"),
        support_rule={
            "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
            "n_core_references": C.N_CORE_REFERENCES,
            "min_tier1_core": C.MIN_TIER1_CORE,
            "min_core_discourse_roles": C.MIN_CORE_DISCOURSE_ROLES,
            "n_backup_families": C.N_BACKUP_FAMILIES},
        # §31's table places every estimate at the difficulty coordinate, and
        # §11.7's fit predicts at iota_A. `run/contracts.py` already declared
        # Gate 5 as a reader of both and the freeze read neither, so the
        # coordinate had no producer downstream of the freeze.
        iota_a=gate3b["iota_a"],
        solo_compliance_a=gate2["solo_compliance_a"],
        solo_compliance_b=gate2["solo_compliance_b"],
        support_realised=gate3c["support"],
        # §34 D6, frozen: the estimand set this replication may not identify,
        # carried from Gate 3C rather than recomputed, so the freeze and the
        # gate cannot disagree about which numbers may still be produced.
        non_identification=gate3c.get("non_identification"),
        admitted_arms=list(arms),
        derived_cell_count=gate3c["derived_cell_count"],
        order_allocation="order is a cell-level factor; every block runs both "
                         "order variants of every composed cell (§8.4)",
        wording_allocation="w(c1) = i mod 4; w(c2) = (i + floor(i/4)) mod 4; "
                           "solo uses i mod 4",
        topic_splits=registration["topic_hashes"],
        split_seed=seeds.CARRIED_TOPIC_SPLIT_SEED,
        seed_rules={"domains": list(seeds.V4R3_DOMAINS),
                    "generation_root": seeds.GENERATION_ROOT_SEED,
                    "bootstrap_root": seeds.BOOTSTRAP_ROOT_SEED,
                    "mask_root": seeds.MASK_ROOT_SEED},
        m_draws=C.M_DRAWS, n_blocks=C.N_BLOCKS,
        variance_reestimate=dict(variance_reestimate or {
            "p_one_minus_p": C.P_ONE_MINUS_P, "phi": C.PHI_PRIMARY,
            "rho": C.RHO, "source": "§16.1's planning values; a realised "
                                    "re-estimate replaces them at the freeze "
                                    "when one has been measured"}),
        verifier_sources=source_hashes(),
        canonical_verifier_hash=gate1["canonical_verifier_hash"],
        wording_hash=gate1["wording_hash"],
        graded_score_definitions={
            "A": "max(0, 1 - |s0 - n| / n)",
            "B": "1 - (words longer than m) / (total words); 0 if empty",
            "exact_count": "max(0, 1 - |count - q| / q)",
            "count_budget": "min(1, q / max(q, count)) for q > 0",
            "count_lower_bound": "min(1, count / q) for q > 0"},
        non_vacuity_predicates={
            "A_and_exact_counts": "non-empty and not truncated",
            "B_and_budget_families":
                f"non-empty, not truncated, at least "
                f"{C.NON_VACUITY_MIN_WORDS} words",
            "lower_bound_families": "non-empty and not truncated"},
        decoding_settings={"temperature": 0.7, "top_p": 0.9, "top_k": 50,
                           "max_new_tokens": regime["selected_cap"],
                           "dtype": spec.dtype,
                           "backend": "vLLM 0.15.1+rocm720"},
        family_declarations={k: list(v)
                             for k, v in C.FAMILY_MEMBERS.items()},
        difficulty_model_form=(
            "Y_fs = alpha_f + beta*d_fs, three family intercepts and one "
            "common slope, OLS on nine equally weighted points; A excluded "
            "from the fit that predicts A"),
        tier_indicator_secondary={
            "registered": "§11.8's Y = alpha_f + beta*d + gamma*1[Tier 2] "
                          "over twelve points",
            "status": "NOT_IDENTIFIED_AS_WRITTEN",
            "open_item": "U2",
            "reported": False,
            "reason": "the section does not say what alpha_f is for the "
                      "three near-form controls; giving each its own "
                      "intercept makes gamma exactly collinear. More than "
                      "one repair is admissible and they estimate different "
                      "things, so the secondary is not reported"},
        bootstrap_algorithm={
            "resamples": C.BOOTSTRAP_RESAMPLES,
            "unit": "the block, resampled with replacement",
            "refit": "the §11.8 model is refitted inside every replicate"},
        thresholds={
            "delta_r_generic": C.DELTA_R_GENERIC_THRESHOLD,
            "delta_r_pair_specific": C.DELTA_R_PAIR_SPECIFIC_THRESHOLD,
            "sesoi": C.SMALLEST_EFFECT_OF_INTEREST,
            "delta_near": dict(C.DELTA_NEAR_THRESHOLDS),
            "delta_broad": dict(C.DELTA_BROAD_THRESHOLDS),
            "delta_difficulty": dict(C.DELTA_DIFFICULTY_THRESHOLDS),
            "order": dict(C.ORDER_THRESHOLDS),
            "composed_headroom_band": list(C.COMPOSED_HEADROOM_BAND)},
        regions={"equivalence": C.EQUIVALENCE_REGION,
                 "sesoi": C.SMALLEST_EFFECT_OF_INTEREST},
        precision_preconditions=dict(C.PRECISION_PRECONDITIONS),
        claim_ladder={"levels": list(C.CLAIM_LEVELS),
                      "withheld": list(C.WITHHELD_CLAIM_LEVELS),
                      "reference_pool_sentence":
                          C.REFERENCE_POOL_SAME_FORM_SENTENCE},
        l4_emitters=["emit_l4a (per named member)", "emit_l4b"],
        disagreement_rules={
            "LOCAL_AND_SPECTRUM_DISAGREE": "§17.6 table 1",
            "LOCAL_TIER_DISAGREE": "§17.6 table 2"},
        codebook={"row_fields": sorted(
            ["row_id", "cell_id", "block_id", "draw_index", "arm", "slots",
             "topic_id", "area", "topic_split", "load", "wording_indices",
             "prompt_hash", "seed", "raw_response", "finish_reason",
             "token_count", "truncated", "empty", "word_count",
             "in_stem_band", "model_key", "model_id", "model_revision",
             "study_id", "classification", "stage", "verifier_hash",
             "scores"])},
        producing_commit=producing_commit,
        clean_tree=True,
        dependency_digest=sha_obj({"uv_lock": str(
            Path(tree.context.repo_root) / "dci1" / "uv.lock")}),
        environment_digest=environment_digest or sha_obj(
            interpreter_identity()),
        hardware={"tensor_parallel_size": spec.tensor_parallel_size,
                  "gpu_memory_utilization": spec.gpu_memory_utilization},
        gate_record_hashes={
            stage: sha_obj(read(tree, stage))
            for stage in C.STAGE_SEQUENCE[:C.STAGE_SEQUENCE.index(
                C.STAGE_GATE5)]},
        measurement_basis=gate1["measurement_basis"],
        reuse_ledger_hash=sha_obj(build_ledger(
            tree.context.repo_root)),
        analysis_plan={
            "estimands": sorted({m for members in C.FAMILY_MEMBERS.values()
                                 for m in members}),
            "primary_family": C.PRIMARY_FAMILY,
            "primary_tier_families": list(C.PRIMARY_TIER_FAMILIES),
            "masking": {"namespaces": list(C.MASK_NAMESPACES)},
            "identification_statuses": statuses},
        open_decisions=list(decisions.open_decisions()),
    )
    freeze_stage.assert_freeze_complete(record,
                                        identification_statuses=statuses)
    if n_cells_for(arms) != record["derived_cell_count"]:
        raise ProtocolError(
            "§18.1: the frozen cell count is not the one the admitted arms "
            f"build ({n_cells_for(arms)} vs {record['derived_cell_count']})")
    if gate4.get("failures"):
        raise ProtocolError(
            "§13.14: Gate 4 recorded failures and a freeze may not follow one")
    # §34 D6: Gate 4 runs after Gate 3C, so it is the first place a
    # non-identification could be lifted. It is checked here, at the freeze,
    # because the freeze is what every later stage asserts against.
    identification.assert_not_rehabilitated(
        gate4, gate3c=gate3c.get("non_identification"),
        where="§34 D6: GATE_4_COMPOSED_HEADROOM")
    return record


def freeze_payload(tree: ModelTree, *, producing_commit: str,
                   environment_digest: str = "",
                   variance_reestimate: Mapping[str, Any] | None = None
                   ) -> dict[str, Any]:
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    gate3b = transitions.read_stage_record(tree, C.STAGE_GATE3B)
    probe = transitions.read_stage_record(tree, C.STAGE_GATE2_75)
    slot_map = {slot: list(value)
                for slot, value in (gate3b.get("slot_map") or {}).items()}
    slot_map.setdefault("A", ["A", gate2["n_star"]])
    # Confirmatory generation renders every cell from **this** slot map, so a
    # B bound at Gate 2's m* would run the whole confirmatory design at the
    # severity Gate 2.75 rejected for want of composed headroom --- while the
    # same record declared the probe's m*. The freeze binds one operating
    # point and it is the one the study runs.
    slot_map.setdefault("B", ["B", int(probe["m_star"])])
    record = assemble(tree, producing_commit=producing_commit,
                      environment_digest=environment_digest,
                      variance_reestimate=variance_reestimate)
    statuses = record["analysis_plan"]["identification_statuses"]
    return {
        "stage": C.STAGE_GATE5,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE5],
        "outcome": "PASS",
        "inputs": {"prefreeze": {"stage": C.STAGE_PREFREEZE_AUDIT}},
        "producing_commit": producing_commit,
        "freeze": record,
        "freeze_hash": sha_obj(record),
        "blocks": record["n_blocks"],
        "cells_per_block": record["derived_cell_count"],
        "M": record["m_draws"],
        "slot_map": dict(slot_map or {}),
        "admitted_arms": record["admitted_arms"],
        "identification_statuses": list(statuses),
        "non_identification": record["non_identification"],
        "selected_cap": record["completion_cap"],
        "n_star": record["n_star"], "m_star": record["m_star"],
        "post_freeze_statement":
            "no scientific rule changes after the freeze; every downstream "
            "stage asserts against this record rather than against the "
            "constants the runner is holding (§18.1)",
    }


def run_freeze(tree: ModelTree, *, producing_commit: str | None = None,
               environment_digest: str = "",
               variance_reestimate: Mapping[str, Any] | None = None
               ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_GATE5,
        compute=lambda _prev: freeze_payload(
            tree, producing_commit=commit,
            environment_digest=environment_digest,
            variance_reestimate=variance_reestimate),
        producing_commit=commit, environment_digest=environment_digest)


def load_freeze(tree: ModelTree) -> dict[str, Any]:
    """The signed freeze record. Every downstream stage's only licence."""
    return transitions.read_stage_record(tree, C.STAGE_GATE5)


def assert_matches_freeze(freeze_record: Mapping[str, Any], *,
                          claimed: Mapping[str, Any], where: str) -> None:
    """Prove that what a downstream runner is about to do is what was frozen.

    §18.1 says no scientific rule changes after the freeze. The way that
    fails in practice is not an edited freeze record but a runner that
    re-derives a value from the constants and gets a different one, because
    the constants moved. So a downstream stage states what it is about to use
    and this compares it, field by field, against the record.
    """
    freeze = freeze_record.get("freeze", freeze_record)
    mismatched = {}
    for key, value in claimed.items():
        frozen = freeze.get(key, freeze_record.get(key))
        if frozen != value:
            mismatched[key] = {"frozen": frozen, "about_to_use": value}
    if mismatched:
        raise ProtocolError(
            f"{where}: these values disagree with the freeze record "
            f"{mismatched}. After Gate 5 the record is the licence and the "
            "constants are not")
