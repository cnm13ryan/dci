"""The signed study-wide registration manifest (§6.1).

**Every study-wide rule is fixed here before the first qualification.** The
manifest is written once, signed, and thereafter read-only; qualification
verifies its signature and refuses to run without it, so a replication cannot
be qualified against rules that were not registered first.

The §6.1 cross-replication firewall decides what belongs here and what does
not. Study-wide, and therefore in this manifest: the constraint families and
severity ladders, the graded-score definitions, the non-vacuity predicates, the
selection algorithms and tie-breakers, both calipers, the number and structural
diversity of references, the estimands, thresholds and regions, the precision
preconditions, the multiplicity families, the bootstrap, the decoding-policy
form, M, the block count, the masking rules, the gate rules, the artifact
semantics, the claim ladder and the codebook. Model-adaptive, and therefore
**not** here: n*, m*, the completion cap, the admitted reference severities and
identities, and whether the full or the reduced design runs. Those reach the
code only through the per-model gate records.

``assert_no_model_adaptive_values`` enforces that split executably, so a
per-model outcome cannot be written into a study-wide rule.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1v4.engine import fs, store
from dci1v4.engine.context import StudyContext
from dci1v4.engine.signing import create_signing_key, sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol import seeds, wordings
from dci1v4.protocol.codebook import CODEBOOK
from dci1v4.protocol.hashing import sha_obj
from dci1v4.stages.freeze import THRESHOLD_PROVENANCE
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.boundary import suite_hash

#: Keys that would be a model-adaptive value if they appeared in the manifest.
MODEL_ADAPTIVE_KEYS = ("n_star", "m_star", "completion_cap",
                       "admitted_references", "reference_severities",
                       "design_in_force", "selected_cap")


def build_manifest(context: StudyContext, *, producing_commit: str,
                   memo_provenance: dict[str, Any] | None = None
                   ) -> dict[str, Any]:
    """Every study-wide rule, as one signable payload."""
    from dci1v4.models.registry import registration_models
    from dci1v4.topics.bank import authoring_record
    from dci1v4.topics.split import split_hash, split_topics

    split = split_topics()
    manifest: dict[str, Any] = {
        "study_id": context.study_id,
        "protocol": "DCI-1",
        "protocol_version": "4.0 revision 2",
        "protocol_document": "user-notes/DCI1_preregistration_v4r2.md",
        "frozen": False,
        "status": ("registration manifest only; the protocol is NOT frozen "
                   "and no confirmatory data exist"),
        "producing_commit": producing_commit,

        "models": registration_models(),
        "judges": ["gpt-oss-20b"],

        "constraints": {
            "target_word": C.TARGET_WORD,
            "target_grid": list(C.TARGET_GRID),
            "focal_grid": list(C.FOCAL_GRID),
            "reference_ladders": {k: list(v)
                                  for k, v in C.REFERENCE_LADDERS.items()},
            "ladder_severities": C.N_LADDER_SEVERITIES,
            "family_rule_statements": dict(wordings.FAMILY_RULE_STATEMENTS),
            "wordings_per_constraint": C.N_WORDINGS,
            "wording_length_tolerance": C.WORDING_LENGTH_TOLERANCE,
            "wording_length_measured_against": "A",
        },
        "instruments": {
            "canonical_verifier_hash": verifier_source_hash(),
            "boundary_suite_hash": suite_hash(),
            "non_vacuity_min_words": C.NON_VACUITY_MIN_WORDS,
            "exact_count_rules": list(C.EXACT_COUNT_RULES),
            "primary_exact_count_rule": C.PRIMARY_EXACT_COUNT_RULE,
            "graded_score_definitions": {
                "A": "max(0, 1 - |s0 - n| / n)",
                "B": "1 - (words longer than m) / (total words); 0 if empty",
                "RF": "min(1, q / max(q, count)) for q > 0; 1[count = 0] for "
                      "q = 0",
            },
            "non_vacuity_predicates": {
                "A": "non-empty and not truncated",
                "B": f"non-empty, not truncated, at least "
                     f"{C.NON_VACUITY_MIN_WORDS} words",
                "RF": f"non-empty, not truncated, at least "
                      f"{C.NON_VACUITY_MIN_WORDS} words",
            },
            "determinism_processes": C.DETERMINISM_PROCESSES,
            "boundary_suite_min_cases": C.BOUNDARY_SUITE_MIN_CASES,
        },
        "design": {
            "registered_slots": list(C.REGISTERED_SLOTS),
            "reduced_slots": list(C.REDUCED_SLOTS),
            "cells_per_block_full": C.N_CELLS_FULL,
            "cells_per_block_reduced": C.N_CELLS_REDUCED,
            "orders": list(C.ORDERS),
            "order_is": "a cell-level factor (§8.4)",
            "wording_allocation": "w(c1) = i mod 4; w(c2) = (i + floor(i/4)) "
                                  "mod 4; solo uses i mod 4",
            "blocks": C.N_BLOCKS,
            "M": C.M_DRAWS,
            "M_cal": C.M_CAL,
            "ladder_screen_draws": C.LADDER_SCREEN_DRAWS,
            "prompt_template": {"zero": C.PROMPT_ZERO, "one": C.PROMPT_ONE,
                                "two": C.PROMPT_TWO},
            "greedy": {"blocks": C.GREEDY_BLOCKS, "draws": C.GREEDY_DRAWS,
                       "temperature": C.GREEDY_TEMPERATURE},
        },
        "topics": {**authoring_record(),
                   "split_hash": split_hash(split),
                   "split_counts": {k: len(v) for k, v in split.items()},
                   "sequestered": C.N_SEQUESTERED},
        "decoding_policy_form": {
            "backend": "vLLM", "dtype": "bfloat16", "temperature": 0.7,
            "top_p": 0.9, "top_k": 50,
            "completion_cap_grid": list(C.COMPLETION_CAPS),
            "zero_shot": True, "single_turn": True,
            "no_examples_tools_retrieval_self_consistency_best_of_n": True,
        },
        # The selection *rules* are study-wide; the values they select are
        # model-adaptive. The keys say "rule" so that the manifest itself
        # carries the distinction the §6.1 firewall draws, and so that the
        # guard's exact-name check cannot be satisfied by a rule that happens
        # to be named after its output.
        "selection_rules": {
            "n_star_selection_rule": {
                "band": list(C.TARGET_BAND), "aim": C.TARGET_AIM,
                "tie_break": "the smaller n"},
            "m_star_selection_rule": {
                "band": list(C.FOCAL_BAND), "aim": C.FOCAL_AIM,
                "tie_break": "the smaller m, meaning the more restrictive "
                             "severity"},
            "completion_cap_selection_rule": {"criterion": "smallest cap with truncation at most "
                                 f"{C.CAP_TRUNCATION_MAX} over the "
                                 "constrained prompts",
                    "zero_constraint_rate": "recorded separately"},
            "reference_admission_rule": {
                "matched_to": "A on solo compliance",
                "caliper": C.REFERENCE_CALIPER,
                "newcombe_region": C.REFERENCE_NEWCOMBE_REGION,
                "prescreen_caliper": C.REFERENCE_PRESCREEN_CALIPER,
                "vacuity_max": C.REFERENCE_VACUITY_MAX,
                "within_family_tie_break": "the less restrictive severity",
                "between_family_tie_break": "the family identifier",
                "final_references": C.N_FINAL_REFERENCES,
                "structural_diversity": "three distinct families",
                "not_a_criterion": "composed uptake (§13.3)",
            },
            "composed_headroom_band": list(C.COMPOSED_HEADROOM_BAND),
        },
        "estimands_and_families": {
            "families": {k: list(v) for k, v in C.FAMILY_MEMBERS.items()},
            "primary_family": C.PRIMARY_FAMILY,
            "configurations": ["outcome_first", "outcome_second"],
            "delta_r_form": "mean_j E[X_B | B+R_j] - E[X_B | A+B]",
            "rbar_rules": {
                "D(Rbar<-g)": "mean over the three admitted references",
                "D(Rbar<-Rbar')": "mean over the six ordered pairs of "
                                  "distinct admitted references",
            },
        },
        "thresholds_and_regions": {
            **{k: v["value"] for k, v in THRESHOLD_PROVENANCE.items()},
            "provenance": {k: v["provenance"]
                           for k, v in THRESHOLD_PROVENANCE.items()},
        },
        "precision_preconditions": dict(C.PRECISION_PRECONDITIONS),
        "variance_model": {
            "p_one_minus_p": C.P_ONE_MINUS_P,
            "phi": [C.PHI_PRIMARY, C.PHI_ALTERNATE],
            "rho": C.RHO, "menu": [dict(e) for e in C.ALLOCATION_MENU],
            "menu_rule": ("the smallest entry meeting every precision "
                          "precondition under the pre-freeze re-estimate"),
        },
        "bootstrap": {"resamples": C.BOOTSTRAP_RESAMPLES,
                      "unit": "block",
                      "construction": "studentised maximum modulus",
                      "root_seed": seeds.BOOTSTRAP_ROOT_SEED,
                      "domain": seeds.DOMAIN_BOOTSTRAP},
        "seeds": {
            "generation_root": seeds.GENERATION_ROOT_SEED,
            "topic_split": seeds.TOPIC_SPLIT_SEED,
            "gate1_sample": seeds.GATE1_SAMPLE_SEED,
            "autorater_split": seeds.AUTORATER_SPLIT_SEED,
            "adversarial": seeds.ADVERSARIAL_SEED,
            "domains": list(seeds.V4_DOMAINS),
            "generation_derivation": ("root, stage label, model identity, "
                                      "prompt hash, draw index"),
            "no_draw_selector": True,
        },
        "masking": {"namespaces": list(C.MASK_NAMESPACES),
                    "permuted": "the companion label within (outcome "
                                "constraint, order, block)",
                    "min_differing_fraction": C.MASK_MIN_DIFFERING_FRACTION},
        "gate_rules": {
            "sequence": list(C.STAGE_SEQUENCE),
            "terminal_statuses": list(C.TERMINAL_STATUSES),
            "identification_statuses": list(C.IDENTIFICATION_STATUSES),
            "result_markers": list(C.RESULT_MARKERS),
            "gate3_is_terminal": False,
            "early_stop_rule": "withdrawn (§6.1)",
        },
        "artifact_semantics": {"states": list(C.ARTIFACT_STATES),
                               "types": list(C.ARTIFACT_TYPES)},
        "claim_ladder": {"levels": list(C.CLAIM_LEVELS),
                         "withheld": list(C.WITHHELD_CLAIM_LEVELS),
                         "measurement_bases": list(C.MEASUREMENT_BASES),
                         "scope_sentence": C.SCOPE_SENTENCE},
        "codebook": [{"name": r["name"], "causal_role": r["causal_role"]}
                     for r in CODEBOOK],
        "qualification_limits": {
            "duplicate_rate_max": C.DUPLICATE_QUALIFICATION_MAX,
            "missingness_report_threshold": C.MISSINGNESS_REPORT_THRESHOLD,
            "truncation_bound_threshold": C.TRUNCATION_BOUND_THRESHOLD,
        },
        "open_decisions": ("V1 to V9 remain open; see "
                           "user-notes/DCI1_v4r2_unresolved_decisions.md"),
    }
    if memo_provenance:
        manifest["memo_provenance"] = dict(memo_provenance)
    assert_no_model_adaptive_values(manifest)
    manifest["manifest_hash"] = sha_obj(manifest)
    return manifest


def assert_no_model_adaptive_values(manifest: dict[str, Any]) -> None:
    """§6.1: a model-adaptive value never appears in a study-wide rule."""
    found: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in MODEL_ADAPTIVE_KEYS:
                    found.append(f"{path}.{key}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(manifest, "manifest")
    if found:
        raise ProtocolError(
            f"the registration manifest carries model-adaptive value(s) "
            f"{found}; those reach the code only through the per-model gate "
            f"records (§6.1)")


def register(context: StudyContext, *, producing_commit: str,
             memo_provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    """Write and sign the manifest, once, before the first qualification."""
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    manifest = build_manifest(context, producing_commit=producing_commit,
                              memo_provenance=memo_provenance)
    fs.write_json_once(context.registration_manifest,
                       sign_payload(manifest, context.signing_key_path))
    # The manifest is the study's root of trust; it gets a second copy on the
    # way out, like every stage record (see engine.dispatch._mirror).
    registration_root = context.registration_manifest.parent
    durable_root = (Path(context.durable_root) / context.study_id
                    / registration_root.name)
    store.replicate(registration_root, durable_root)
    store.assert_replicated(registration_root, durable_root)
    return manifest


def load_manifest(context: StudyContext) -> dict[str, Any]:
    """Read and verify the signed manifest. Fails closed when it is absent."""
    path = Path(context.registration_manifest)
    if not path.exists():
        raise IntegrityError(
            f"the signed registration manifest is missing at {path}. §6.1 "
            f"fixes every study-wide rule in it BEFORE the first "
            f"qualification, so no replication may be qualified without it")
    payload = verify_signed(fs.read_json(path), context.signing_key_path,
                            where="registration manifest")
    if payload.get("study_id") != context.study_id:
        raise IntegrityError("the registration manifest belongs to another "
                             "study")
    return payload


def assert_manifest_matches_code(context: StudyContext) -> dict[str, Any]:
    """The running code implements the rules the manifest registered.

    A study-wide rule that drifted after registration would make the manifest
    a description rather than a constraint, so the values the code would emit
    now are re-derived and compared.
    """
    registered = load_manifest(context)
    current = build_manifest(context,
                             producing_commit=registered["producing_commit"],
                             memo_provenance=registered.get("memo_provenance"))
    differing = [key for key in current
                 if key != "manifest_hash" and current[key] != registered.get(key)]
    if differing:
        raise IntegrityError(
            f"the running code no longer implements the registered study-wide "
            f"rules; differing sections: {differing}")
    return registered
