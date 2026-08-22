"""§18 stage 1's signed registration manifest, and the five things that stop
it being signed.

The manifest is where every study-wide rule stops being a draft. §6.1's
cross-replication firewall decides what belongs in it: study-wide values are
bound here once, before the first qualification, and model-adaptive values ---
n*, m*, the completion cap, the closed vocabulary, the admitted references,
the arm set --- never appear, because they reach the code only through
per-model gate records. ``assert_no_model_adaptive_values`` enforces that
split executably rather than by convention.

**It refuses to be signed today, for five separate reasons, and each one is a
different kind of not-ready:**

1. a §34 decision is open --- ``protocol/decisions.py``;
2. a specification question the documents do not settle is unresolved ---
   ``protocol/open_items.py``;
3. a required topic-bank hash is missing --- Calibration-B does not exist;
4. the candidate population is unapproved --- §34 D4;
5. a red-team finding whose registered mitigation *is* a decision is still
   open --- R1, R11, R14, R16.

They are checked separately and reported separately, because "we have not
decided" and "the work has not been done" are different facts and collapsing
them into one refusal loses which one a researcher has to act on. §18 stage
1's failure status is ``REGISTRATION_INCOMPLETE`` for all five.

``build_manifest`` assembles the payload **whether or not it can be signed**,
so that a researcher can see exactly what adoption would bind before adopting
anything. ``assert_signable`` is what refuses, and ``sign_registration`` calls
it first.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, store
from dci1v4.engine.signing import create_signing_key, sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import registration_models
from dci1v4.protocol.hashing import sha_obj

from dci1v5 import (CLASSIFICATION, PREREGISTRATION, REFERENCE_DESIGN_SPEC,
                    STUDY_ID)
from dci1v5.engine.context import StudyContext
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions, open_items, revision, seeds, taxonomy
from dci1v5.protocol import wordings
from dci1v5.protocol.wordings import wording_source_hash
from dci1v5.stages.audit_prefreeze import UNRESOLVED_REDTEAM_FINDINGS
from dci1v5.topics.bank import TopicBank, load_bank
from dci1v5.verifiers import verifier_source_hash
from dci1v5.verifiers.constraints import FAMILIES, RESERVES

__all__ = ["PROTOCOL_VERSION", "PROTOCOL_DOCUMENT", "MODEL_ADAPTIVE_KEYS",
           "REQUIRED_BINDINGS", "REGISTRATION_INCOMPLETE", "Blocker",
           "signing_blockers", "assert_signable", "build_manifest",
           "assert_no_model_adaptive_values", "document_hashes",
           "sign_registration", "load_manifest"]

PROTOCOL_VERSION = "5.0 DRAFT"
PROTOCOL_DOCUMENT = PREREGISTRATION
REGISTRATION_INCOMPLETE = decisions.REGISTRATION_INCOMPLETE

#: Keys that would be a model-adaptive value if they appeared (§6.1).
MODEL_ADAPTIVE_KEYS = (
    "n_star", "m_star", "completion_cap", "selected_cap", "carried_set",
    "admitted_references", "reference_severities", "spectrum_severities",
    "near_form_controls", "broad_class_control", "admitted_arms",
    "measured_vocabulary", "coverage_report", "qualified_pool",
    "identification_statuses", "derived_cell_count")

#: Every top-level binding §34 and §18.1 require the manifest to carry. The
#: tuple is asserted against the built payload, so a binding that is dropped
#: from the builder fails a test rather than going missing from a signature.
REQUIRED_BINDINGS = (
    "study_id", "protocol", "protocol_version", "protocol_document",
    "protocol_hash", "reference_design_spec", "reference_design_spec_hash",
    "classification", "producing_commit", "decisions", "open_items",
    "models", "backend", "topics", "candidate_library", "marker_population",
    "structural_taxonomy", "severity_ladders", "focal_grid", "constraints",
    "instruments", "design", "decoding_policy_form", "seeds",
    "selection_rules", "validity_rule", "interaction_rule", "stability_rule",
    "support_requirements", "lifecycle", "estimands", "order_estimands",
    "multiplicity_families", "claim_ladder", "masking", "freeze_requirements",
    "measurement_basis", "thresholds", "precision_preconditions",
    "reuse_ledger", "revision_changes", "red_team",
)


class Blocker(ProtocolError):
    """A named reason the registration manifest may not be signed."""


def document_hashes(repo_root: Path | str = ".") -> dict[str, Any]:
    """The two documents the manifest binds, by content.

    §18 stage 1 binds *this document's* hash and the spec file's hash, so a
    later reader can prove which text the study registered. A missing file is
    a refusal and not an empty string: an unbound protocol hash is exactly the
    hole this field exists to close.
    """
    out: dict[str, Any] = {}
    for name, rel in (("protocol_hash", PROTOCOL_DOCUMENT),
                      ("reference_design_spec_hash", REFERENCE_DESIGN_SPEC)):
        path = Path(repo_root) / rel
        if not path.exists():
            raise Blocker(
                f"§18 stage 1 binds the hash of {rel} and the file is not at "
                f"{path}; a registration that cannot name its own protocol "
                "text binds nothing")
        out[name] = sha_obj({"path": rel, "bytes": path.read_bytes().hex()})
    return out


# ------------------------------------------------------------- refusals

def signing_blockers(bank: TopicBank | None = None) -> list[dict[str, Any]]:
    """The five refusals, each reported separately and by kind."""
    bank = bank if bank is not None else load_bank()
    blockers: list[dict[str, Any]] = []

    still_open = list(decisions.open_decisions())
    if still_open:
        blockers.append({
            "kind": "OPEN_DECISION", "section": "§34",
            "detail": still_open,
            "n": len(still_open),
            "why": "§34 requires every decision closed, with its evidence, in "
                   "this manifest before stage 1 can pass"})

    blocking_items = list(open_items.blocking_items())
    if blocking_items:
        blockers.append({
            "kind": "UNRESOLVED_SPECIFICATION", "section": "§33",
            "detail": [{"id": i, "title": open_items.OPEN_ITEMS[i].title,
                        "alternatives":
                            [a.id for a in open_items.OPEN_ITEMS[i]
                             .alternatives]}
                       for i in blocking_items],
            "n": len(blocking_items),
            "why": "the preregistration, the spec and the implementation do "
                   "not determine the rule, and the admissible formulations "
                   "estimate different things"})

    missing_hashes = [name for name, value in bank.hashes.items()
                      if value is None and name != "sequestered"]
    if missing_hashes:
        blockers.append({
            "kind": "MISSING_TOPIC_HASH", "section": "§6.2",
            "detail": missing_hashes,
            "calibration_b_status": bank.calibration_b_status,
            "n": len(missing_hashes),
            "why": "§18 stage 1 binds the topic-bank hash and §13.7 needs two "
                   "disjoint 96-topic calibration sets; Calibration-B is "
                   f"{bank.calibration_b_status}"})

    if not decisions.is_closed("D4"):
        blockers.append({
            "kind": "CANDIDATE_POPULATION_UNAPPROVED", "section": "§7.10",
            "detail": {"decision": "D4",
                       "markers": list(C.MARKER_WORDS),
                       "families": C.N_FAMILIES,
                       "instruments": C.N_INSTRUMENTS},
            "n": 1,
            "why": "the manifest binds the marker population and the "
                   "candidate library; §34 D4 is the approval and it is open"})

    open_findings = {k: v for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()
                     if v["decision"] and
                     not decisions.is_closed(v["decision"])}
    if open_findings:
        blockers.append({
            "kind": "OPEN_RED_TEAM_FINDING", "section": "§33",
            "detail": {k: {"decision": v["decision"],
                           "finding": v["finding"]}
                       for k, v in open_findings.items()},
            "n": len(open_findings),
            "why": "each of these findings' registered mitigation IS a §34 "
                   "decision; closing the decision is what resolves it"})
    return blockers


def assert_signable(bank: TopicBank | None = None, *,
                    where: str = "registration") -> None:
    """§18 stage 1: refuse, by name, everything that is not ready."""
    blockers = signing_blockers(bank)
    if blockers:
        summary = ", ".join(f"{b['kind']}({b['n']})" for b in blockers)
        raise Blocker(
            f"{where}: the v5 registration manifest may not be signed --- "
            f"{summary}. §18 stage 1 records {REGISTRATION_INCOMPLETE}. "
            f"Detail: {blockers}")


# ------------------------------------------------------------- the payload

def _candidate_library() -> dict[str, Any]:
    return {
        "grammar": "a registered counted statistic under a registered "
                   "predicate form; nothing else is a candidate family",
        "statistics": list(C.STATISTIC_IDS),
        "forms": list(C.FORMS),
        "families": {
            kind: {"statistic": f.statistic_id, "form": f.form,
                   "class": f.constraint_class,
                   "tier": f.structural_tier, "rule": f.rule,
                   "statistic_source": f.statistic_source,
                   "metadata": dict(f.metadata),
                   "ladder": list(f.ladder), "reserve": list(f.reserve)}
            for kind, f in FAMILIES.items()},
        "n_families": C.N_FAMILIES,
        "round_zero_severities": C.N_SEVERITIES,
        "declared_severities": sum(len(v) for v in RESERVES.values()),
        "instruments": C.N_INSTRUMENTS,
        "verifiers": C.N_VERIFIERS,
        "population": "the declared range of §7, not the round-0 ladder",
        "frozen_by": "§7.10; §12.6's expansion picks from the reserve and "
                     "never authors a family",
    }


def build_manifest(context: StudyContext, *, producing_commit: str,
                   adoption: Mapping[str, Any],
                   bank: TopicBank | None = None,
                   repo_root: Path | str = ".") -> dict[str, Any]:
    """Every study-wide rule, as one signable payload.

    Assembled whether or not it is signable. A researcher deciding whether to
    adopt v5 needs to see what adoption would bind, and a builder that
    refused before assembling would make that impossible.
    """
    bank = bank if bank is not None else load_bank()
    manifest: dict[str, Any] = {
        "study_id": context.study_id,
        "protocol": "DCI-1",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_document": PROTOCOL_DOCUMENT,
        "reference_design_spec": REFERENCE_DESIGN_SPEC,
        "classification": CLASSIFICATION,
        "frozen": False,
        "status": ("registration manifest only; the protocol is NOT frozen "
                   "and no confirmatory data exist"),
        "producing_commit": producing_commit,
        "adoption": dict(adoption),
        **document_hashes(repo_root),

        # ------------------------------------------------ §34 and §33
        "decisions": decisions.registration_payload(),
        "open_items": open_items.manifest_payload(),
        "red_team": {
            "source": "dci1/reports/dci1v5/v5_prereg_redteam.md",
            "unresolved": {k: dict(v)
                           for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()},
            "not_closeable_by_rule":
                [k for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()
                 if not v["closeable_by_rule"]],
        },
        "revision_changes": revision.revision_record(),

        # ------------------------------------------------------ apparatus
        "models": registration_models(),
        "judges": ["gpt-oss-20b"],
        "backend": {
            "backend": "vLLM", "pinned": "0.15.1+rocm720",
            "dtype": "bfloat16", "tensor_parallel_size": 1,
            "chat_template": "each model's own, from its pinned revision",
            "reasoning_mode": "disabled where the model offers one; "
                              "unavailable otherwise (§6.1)",
        },
        "decoding_policy_form": {
            "temperature": 0.7, "top_p": 0.9, "top_k": 50,
            "completion_cap_grid": list(C.COMPLETION_CAPS),
            "zero_shot": True, "single_turn": True,
            "no_examples_tools_retrieval_self_consistency_best_of_n": True,
        },
        "seeds": {
            "domain_strings": list(seeds.V4R3_DOMAINS),
            "generation_root": seeds.GENERATION_ROOT_SEED,
            "bootstrap_root": seeds.BOOTSTRAP_ROOT_SEED,
            "mask_root": seeds.MASK_ROOT_SEED,
            "topic_split_seed": "v4r2's, carried unchanged (§6.2)",
        },

        # --------------------------------------------------------- §6.2
        "topics": {
            **bank.split_identity,
            "sets": {name: {"n": len(bank.sets[name]),
                            "hash": bank.hashes[name]}
                     for name in C.TOPIC_SETS},
            "calibration_a_hash": bank.hashes[C.CALIBRATION_A],
            "calibration_b_hash": bank.hashes[C.CALIBRATION_B],
            "authoring_rules": list(C.AUTHORING_RULES),
            "development_sets": list(C.DEVELOPMENT_TOPIC_SETS),
            "reserved_sets": list(C.RESERVED_TOPIC_SETS),
        },

        # ------------------------------------------------------ §7, §10
        "candidate_library": _candidate_library(),
        "marker_population": {
            "words": list(C.MARKER_WORDS),
            "max_letters": C.MARKER_MAX_LETTERS,
            "natural_frequency_max": C.MARKER_NATURAL_FREQUENCY_MAX,
            "benchmark": "A's own `however` frequency (§7.6 rule 3)",
            "evidence_class": "DEVELOPMENT_EVIDENCE",
            "approved_by": "§34 D4",
            "approval_status": decisions.value_of("D4"),
        },
        "structural_taxonomy": {
            "fields": list(taxonomy.METADATA_FIELDS),
            "tiers": list(taxonomy.TIERS),
            "slots": list(taxonomy.SLOTS),
            "tier_rule": "computed from the metadata record, never declared",
            "a_record": dict(taxonomy.A_STRUCTURAL_RECORD),
        },
        "severity_ladders": {kind: {"ladder": list(f.ladder),
                                    "reserve": list(f.reserve)}
                             for kind, f in FAMILIES.items()},
        "focal_grid": {"grid": list(C.FOCAL_GRID),
                       "extension": list(C.FOCAL_EXTENSION),
                       "target_grid": list(C.TARGET_GRID),
                       "target_word": C.TARGET_WORD},
        "constraints": {
            "family_rule_statements":
                dict(wordings.FAMILY_RULE_STATEMENTS),
            "wordings_per_constraint": C.N_WORDINGS,
            "wording_length_tolerance": C.WORDING_LENGTH_TOLERANCE,
            "wording_length_measured_against": "A",
            "wording_hash": wording_source_hash(),
        },
        "instruments": {
            "canonical_verifier_hash": verifier_source_hash(),
            "non_vacuity_min_words": C.NON_VACUITY_MIN_WORDS,
            "stem_band": list(C.STEM_BAND),
            "exact_count_rules": list(C.EXACT_COUNT_RULES),
            "primary_exact_count_rule": C.PRIMARY_EXACT_COUNT_RULE,
            "presence_rule": "§9.1: an instance is scored present only where "
                             "the prompt stated it; absent verdicts are "
                             "chance verdicts and no estimand reads them as "
                             "treated",
            "determinism_processes": C.DETERMINISM_PROCESSES,
            "boundary_suite_min_cases": C.BOUNDARY_SUITE_MIN_CASES,
        },

        # ------------------------------------------------------------ §8
        "design": {
            "arms": list(C.ARMS),
            "optional_arms": list(C.OPTIONAL_ARMS),
            "cells_by_arm": dict(C.N_CELLS_BY_ARM),
            "cells_full": C.N_CELLS_FULL,
            "cell_set_is": "derived from the admitted arm set; there is no "
                           "named variant table (§8.1)",
            "registered_slot_order": list(C.REGISTERED_SLOT_ORDER),
            "configurations": list(C.CONFIGURATIONS),
            "order_is": "a cell-level factor (§8.4)",
            "wording_allocation": "w(c1) = i mod 4; w(c2) = (i + floor(i/4)) "
                                  "mod 4; solo uses i mod 4",
            "blocks": C.N_BLOCKS, "M": C.M_DRAWS, "M_cal": C.M_CAL,
            "prompt_template": {"zero": C.PROMPT_ZERO, "one": C.PROMPT_ONE,
                                "two": C.PROMPT_TWO},
            "stem_sentence": C.STEM_SENTENCE,
        },

        # ----------------------------------------------------------- §13
        "selection_rules": {
            "difficulty_coordinate": {
                "primary": C.DIFFICULTY_COORDINATE,
                "formula": "(solo - kappa) / (1 - kappa)",
                "secondary": C.SECONDARY_DIFFICULTY_COORDINATE,
                "degeneracy_ceiling": C.CHANCE_DEGENERACY_MAX,
                "evaluated": "last, in §13.1's lexicographic order",
            },
            "prescreen_retention_band": list(C.PRESCREEN_RETENTION_BAND),
            "prescreen_caliper": None,
            "prescreen_caliper_note":
                "§12.2 deletes v4r4's pre-screen distance caliper: the two "
                "stages' iota estimates disagree by a median of 0.071",
            "expansion": {"max_rounds": C.EXPANSION_MAX_ROUNDS,
                          "max_rungs_per_family_per_round":
                              C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND,
                          "source": "the frozen reserve of §7.10"},
            "coverage_conditions": list(C.COVERAGE_CONDITIONS),
            "coverage_decisive": list(C.COVERAGE_DECISIVE),
            "reference_caliper": C.REFERENCE_CALIPER,
            "secondary_coordinate_caliper": C.SECONDARY_COORDINATE_CALIPER,
            "spectrum": {"band": list(C.SPECTRUM_ELIGIBILITY_BAND),
                         "offset": C.SPECTRUM_OFFSET,
                         "per_family": C.N_SPECTRUM_PER_FAMILY,
                         "drawn_from": "the admitted core reference's own "
                                       "family (§13.12)"},
            "near_form": {"n": C.N_NEAR_FORM_CONTROLS, "tier": 2},
            "broad_class": {"caliper": C.CLASS_MATCH_CALIPER,
                            "class": "budget", "tier": 3},
            "backups": {"n_families": C.N_BACKUP_FAMILIES,
                        "may_substitute_after_gate_4":
                            C.BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4},
        },
        "validity_rule": {
            "components": list(C.VALIDITY_COMPONENTS),
            "combination": "conjunction; the order decides the recorded "
                           "reason and never the verdict",
            "composite_score": False,
            "headroom_band": list(C.HEADROOM_BAND),
            "instruction_lift_min": C.INSTRUCTION_LIFT_MIN,
            "reference_vacuity_max": C.REFERENCE_VACUITY_MAX,
            "chance_max": C.CHANCE_MAX,
            "chance_wilson_upper_max": C.CHANCE_WILSON_UPPER_MAX,
        },
        "interaction_rule": {
            "quantity": "kappa(R|B): P(R passes | B alone at m*, R absent)",
            "measured_on": "load-one B cells; R must be absent (§9.1)",
            "projected_compliance_band": list(C.PROJECTED_COMPLIANCE_BAND),
            "projection_error_allowance": C.PROJECTION_ERROR_ALLOWANCE,
            "displacement_max": C.DISPLACEMENT_MAX,
            "costs": "no additional generation",
        },
        "stability_rule": {
            "splits": list(C.TOPIC_SETS[1:3]),
            "equivalence_bound": C.STABILITY_EQUIVALENCE_BOUND,
            "bootstrap_resamples": C.STABILITY_BOOTSTRAP_RESAMPLES,
            "form": "an equivalence bound on the interval, not a threshold "
                    "on the point difference",
            "population": "§34 D16",
            "population_value": decisions.value_of("D16"),
        },
        "support_requirements": {
            "min_below": C.SUPPORT_MIN_BELOW, "min_above": C.SUPPORT_MIN_ABOVE,
            "min_families_per_side": C.SUPPORT_MIN_FAMILIES_PER_SIDE,
            "bootstrap_share_min": C.SUPPORT_BOOTSTRAP_SHARE_MIN,
            "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
            "min_structurally_eligible_tier12_families":
                C.MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES,
            "n_core_references": C.N_CORE_REFERENCES,
            "min_tier1_core": C.MIN_TIER1_CORE,
            "n_core_feature_groups": C.N_CORE_FEATURE_GROUPS,
            "min_core_discourse_roles": C.MIN_CORE_DISCOURSE_ROLES,
            "status_when_unmet": "REFERENCE_SUPPORT_NOT_IDENTIFIED",
            "status_when_unmet_is_terminal": "§34 D6",
            "status_when_unmet_is_terminal_value": decisions.value_of("D6"),
        },

        # ----------------------------------------------------------- §18
        "lifecycle": {
            "stages": list(C.STAGE_SEQUENCE),
            "generation_stages": list(C.GENERATION_STAGES),
            "terminal_statuses": list(C.TERMINAL_STATUSES),
            # The registered *vocabulary*. Which statuses a replication
            # realises is model-adaptive and lives on its Gate 3C record;
            # the key is named so the two can never be confused.
            "identification_status_vocabulary":
                list(C.IDENTIFICATION_STATUSES),
            "verifier_bound_entry_points":
                list(C.VERIFIER_BOUND_ENTRY_POINTS),
            "artifact_types": list(C.ARTIFACT_TYPES),
            "stage_artifact_type": dict(C.STAGE_ARTIFACT_TYPE),
            "interpretation": "interaction-aware during development, "
                              "interaction-blind during confirmatory "
                              "selection",
        },

        # ------------------------------------------------------ §11, §15
        "estimands": {
            "D": "P(c passes alone) - P(c passes composed with g)",
            "Delta_j": "D(B<-A) - D(B<-R_j)",
            "Delta_R": "D(B<-A) - mean_j D(B<-R_j)",
            "Lambda": "D(B<-A) - D(A<-B)",
            "Xi": "§11.7's reciprocal gate",
            "delta_difficulty": "D(B<-A) minus the §11.8 prediction at iota_A",
            "Delta_near": "D(B<-A) - mean_k D(B<-N_k)",
            "Delta_broad": "D(B<-A) - D(B<-CL)",
            "difficulty_relation":
                "Y_fs = alpha_f + beta*d_fs, three family intercepts and one "
                "common slope, OLS on nine equally weighted points",
            "tier_indicator_secondary":
                "§11.8's secondary; NOT identified as written and blocked by "
                "open_items.U2",
        },
        "order_estimands": {
            "family": "F11",
            "members": list(C.FAMILY_MEMBERS["F11"]),
            "cross_configuration": True,
            "dependence": "Ord_Lambda = Ord_B - Ord_A exactly, declared "
                          "rather than hidden (§11.7)",
        },
        "multiplicity_families": {
            name: {"members": list(members), "n": len(members),
                   "tier": ("primary" if name in C.PRIMARY_TIER_FAMILIES
                            else "secondary")}
            for name, members in C.FAMILY_MEMBERS.items()},
        "claim_ladder": {
            "levels": list(C.CLAIM_LEVELS),
            "withheld": list(C.WITHHELD_CLAIM_LEVELS),
            "l4a": "per named member (§17.7)",
            "l3c_near_form_precondition": "§34 D18",
            "l3c_near_form_precondition_value": decisions.value_of("D18"),
            "reference_pool_sentence": C.REFERENCE_POOL_SAME_FORM_SENTENCE,
            "class_sentence": C.CLASS_SENTENCE,
            "l3c_without_near_form_sentence":
                C.L3C_WITHOUT_NEAR_FORM_SENTENCE,
        },
        "masking": {
            "namespaces": list(C.MASK_NAMESPACES),
            "min_differing_fraction": C.MASK_MIN_DIFFERING_FRACTION,
            "unmask": "once, bound to the sealed masked artifact and to the "
                      "analysis code hash (§20)",
        },
        "freeze_requirements": {
            "section": "§18.1",
            "empty_field_rule": "a field a variant legitimately leaves empty "
                                "is declared empty with the identification "
                                "status that explains it",
            "post_freeze": "no scientific rule changes after the freeze",
        },
        "measurement_basis": {
            "value": C.MEASUREMENT_BASIS,
            "refused": list(C.MEASUREMENT_BASES_REFUSED),
            "scope_sentence": C.SCOPE_SENTENCE,
            "permanent": True,
        },
        "thresholds": {
            "delta_r_generic": C.DELTA_R_GENERIC_THRESHOLD,
            "delta_r_pair_specific": C.DELTA_R_PAIR_SPECIFIC_THRESHOLD,
            "sesoi": C.SMALLEST_EFFECT_OF_INTEREST,
            "equivalence_region": C.EQUIVALENCE_REGION,
            "delta_near": dict(C.DELTA_NEAR_THRESHOLDS),
            "delta_broad": dict(C.DELTA_BROAD_THRESHOLDS),
            "delta_difficulty": dict(C.DELTA_DIFFICULTY_THRESHOLDS),
            "order": dict(C.ORDER_THRESHOLDS),
            "composed_headroom_band": list(C.COMPOSED_HEADROOM_BAND),
            "construct_floor": "§34 D17",
            "construct_floor_value": decisions.value_of("D17"),
        },
        "precision_preconditions": dict(C.PRECISION_PRECONDITIONS),
        "reuse_ledger": {
            "classifications": list(C.REUSE_CLASSIFICATIONS),
            "declaration": "historical v4r4 outcomes informed the DESIGN of "
                           "v5's matching rules; no v5 B+R outcome selects, "
                           "replaces, widens, adds, repairs or alters "
                           "anything (§30)",
        },
    }
    missing = [k for k in REQUIRED_BINDINGS if k not in manifest]
    if missing:
        raise ProtocolError(
            f"the registration manifest is missing required binding(s) "
            f"{missing}; REQUIRED_BINDINGS is what §34 and §18.1 ask it to "
            "carry and the builder must produce every one")
    assert_no_model_adaptive_values(manifest)
    manifest["manifest_hash"] = sha_obj(manifest)
    return manifest


def assert_no_model_adaptive_values(manifest: Mapping[str, Any]) -> None:
    """§6.1: a model-adaptive value never appears in a study-wide rule."""
    found: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if key in MODEL_ADAPTIVE_KEYS:
                    found.append(f"{path}.{key}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(manifest, "manifest")
    if found:
        raise ProtocolError(
            f"the registration manifest carries model-adaptive value(s) "
            f"{found}; those reach the code only through the per-model "
            "records (§6.1)")


def sign_registration(context: StudyContext, *, producing_commit: str,
                      adoption: Mapping[str, Any],
                      bank: TopicBank | None = None,
                      repo_root: Path | str = ".",
                      supersedes: str | None = None) -> dict[str, Any]:
    """Write and sign the manifest, once. **Refuses today, by design.**

    ``assert_signable`` runs first and before any file is created, so a
    refused registration leaves no directory, no key and no partial artifact
    behind that a later run could mistake for a registration.
    """
    bank = bank if bank is not None else load_bank()
    assert_signable(bank, where="sign_registration")
    manifest = build_manifest(context, producing_commit=producing_commit,
                              adoption=adoption, bank=bank,
                              repo_root=repo_root)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    if supersedes:
        manifest["supersedes"] = supersedes
        manifest["manifest_hash"] = sha_obj(
            {k: v for k, v in manifest.items() if k != "manifest_hash"})
    context.registration_root.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(context.registration_manifest,
                       sign_payload(manifest, context.signing_key_path))
    durable = (Path(context.durable_root) / STUDY_ID
               / context.registration_root.name)
    store.replicate(context.registration_root, durable)
    store.assert_replicated(context.registration_root, durable)
    return manifest


def load_manifest(context: StudyContext) -> dict[str, Any]:
    """Read and verify the signed manifest. Fails closed when it is absent."""
    path = Path(context.registration_manifest)
    if not path.exists():
        raise IntegrityError(
            f"the signed v5 registration manifest is missing at {path}. §6.1 "
            "fixes every study-wide rule in it BEFORE the first "
            "qualification, so no replication may be qualified without it")
    payload = verify_signed(fs.read_json(path), context.signing_key_path,
                            where="v5 registration manifest")
    if payload.get("study_id") != context.study_id:
        raise IntegrityError(
            "the registration manifest belongs to another study")
    return payload
