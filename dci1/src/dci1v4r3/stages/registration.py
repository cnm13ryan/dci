"""The signed v4r3 registration manifest (§6.1, §12.5, §26).

**Every study-wide rule is fixed here before the first qualification**, and the
manifest is written once, signed, and thereafter read-only.

The §6.1 cross-replication firewall decides what belongs in it. Study-wide, and
therefore here: the candidate grammar of §7.0 with every ladder *and every
reserve*, the expansion rule and coverage criterion of §12.6, the graded-score
definitions, the non-vacuity predicates, the lexical rule, every selection
algorithm and tie-breaker, the calipers, the estimands, thresholds and regions,
the precision preconditions, the multiplicity families, the bootstrap, the
decoding-policy form, M, the block count, the masking rules, the gate rules and
the claim ladder. Model-adaptive, and therefore **not** here: n*, m*, the
completion cap, the measured vocabulary §12.6 closes, the admitted references
and spectrum rungs, the class companion, and whether the full or the reduced
design runs. Those reach the code only through the per-model records.

``assert_no_model_adaptive_values`` enforces the split executably.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1v4.engine import fs, store
from dci1v4.engine.signing import create_signing_key, sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import registration_models
from dci1v4.protocol.hashing import sha_obj
from dci1v4.topics.bank import authoring_record
from dci1v4.topics.split import split_hash

from dci1v4r3 import CLASSIFICATION, STUDY_ID
from dci1v4r3.engine.context import StudyContext
from dci1v4r3.protocol import constants as C
from dci1v4r3.protocol import seeds, wordings
from dci1v4r3.stages.freeze import FREEZE_FIELDS, THRESHOLD_PROVENANCE
from dci1v4r3.topics import split_topics
from dci1v4r3.verifiers import verifier_source_hash
from dci1v4r3.verifiers.constraints import FAMILIES, RESERVES

PROTOCOL_VERSION = "4.0 revision 3"
PROTOCOL_DOCUMENT = "user-notes/DCI1_preregistration_v4r3.md"

#: Keys that would be a model-adaptive value if they appeared in the manifest.
MODEL_ADAPTIVE_KEYS = ("n_star", "m_star", "completion_cap", "selected_cap",
                       "admitted_references", "reference_severities",
                       "spectrum_severities", "class_companion",
                       "measured_vocabulary", "design_in_force",
                       "coverage_report")

__all__ = ["PROTOCOL_VERSION", "PROTOCOL_DOCUMENT", "MODEL_ADAPTIVE_KEYS",
           "build_manifest", "assert_no_model_adaptive_values", "register",
           "load_manifest"]


def build_manifest(context: StudyContext, *, producing_commit: str,
                   adoption: dict[str, Any]) -> dict[str, Any]:
    """Every study-wide rule, as one signable payload."""
    split = split_topics()
    manifest: dict[str, Any] = {
        "study_id": context.study_id,
        "protocol": "DCI-1",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_document": PROTOCOL_DOCUMENT,
        "classification": CLASSIFICATION,
        "frozen": False,
        "status": ("registration manifest only; the protocol is NOT frozen "
                   "and no confirmatory data exist"),
        "producing_commit": producing_commit,
        "adoption": dict(adoption),

        "models": registration_models(),
        "judges": ["gpt-oss-20b"],

        "candidate_library": {
            "grammar": "a registered counted statistic under a registered "
                       "predicate form; nothing else is a candidate family",
            "statistics": list(C.STATISTIC_IDS),
            "forms": {"count_budget": "S <= q",
                      "rate_budget": "100*S/W <= q; a wordless answer fails",
                      "count_lower_bound": "S >= q",
                      "rate_lower_bound":
                          "100*S/W >= q; a wordless answer fails"},
            "families": {
                kind: {"statistic": f.statistic_id, "form": f.form,
                       "class": f.constraint_class, "role": f.role,
                       "rule": f.rule, "statistic_source": f.statistic_source,
                       "ladder": list(f.ladder), "reserve": list(f.reserve)}
                for kind, f in FAMILIES.items()},
            "round_zero_severities": C.N_SEVERITIES,
            "declared_severities": sum(len(v) for v in RESERVES.values()),
            "no_rate_rung_at_zero":
                "100*S/W <= 0 holds exactly when S <= 0, so a rate rung at "
                "zero would duplicate its count sibling (§7.3)",
        },
        "constraints": {
            "target_word": C.TARGET_WORD,
            "target_grid": list(C.TARGET_GRID),
            "focal_grid": list(C.FOCAL_GRID),
            "focal_extension": list(C.FOCAL_EXTENSION),
            "focal_extension_rule":
                "measured only when §12.3 finds no eligible severity in the "
                "registered grid; a study-wide escalation, not a per-model "
                "grid",
            "family_rule_statements": dict(wordings.FAMILY_RULE_STATEMENTS),
            "wordings_per_constraint": C.N_WORDINGS,
            "wording_length_tolerance": C.WORDING_LENGTH_TOLERANCE,
            "wording_length_measured_against": "A",
            "wording_word_counts": wordings.assert_severity_invariance(),
        },
        "instruments": {
            "canonical_verifier_hash": verifier_source_hash(),
            "lexical_rule": {
                "word": "a maximal run of Unicode general-category-L "
                        "characters in the answer",
                "composition": "segment first, then lower-case each word for "
                               "the suffix and letter tests",
                "letters": "the characters of the word as written",
                "raw_character_counts": ["comma", "capital_char"],
                "A_exception":
                    "§9.2 registers S0 as lower-case-then-segment and A's "
                    "carried counting function implements exactly that",
                "correction_scope": "U+0130, the only character whose "
                                    "lower-case form is not alphabetic "
                                    "throughout; realised frequency 0 in "
                                    "285,936 v4-era generations",
            },
            "non_vacuity_min_words": C.NON_VACUITY_MIN_WORDS,
            "exact_count_rules": list(C.EXACT_COUNT_RULES),
            "primary_exact_count_rule": C.PRIMARY_EXACT_COUNT_RULE,
            "graded_score_definitions": {
                "A": "max(0, 1 - |s0 - n| / n)",
                "B": "1 - (words longer than m) / (total words); 0 if empty",
                "count_budget": "min(1, q / max(q, count)) for q > 0; "
                                "1[count = 0] for q = 0",
                "rate_budget": "min(1, q / max(q, rate)) for rate > 0; 1 for "
                               "rate = 0; 0 for a wordless answer",
                "count_lower_bound": "min(1, count / q) for q > 0",
                "rate_lower_bound": "min(1, rate / q) for q > 0; 0 for a "
                                    "wordless answer",
            },
            "non_vacuity_predicates": {
                "A": "non-empty and not truncated",
                "B_and_budget_families":
                    f"non-empty, not truncated, at least "
                    f"{C.NON_VACUITY_MIN_WORDS} words",
                "lower_bound_families":
                    "non-empty and not truncated; the rule already forces "
                    "length upward so a word-count clause would be "
                    "redundant rather than protective",
            },
            "determinism_processes": C.DETERMINISM_PROCESSES,
            "boundary_suite_min_cases": C.BOUNDARY_SUITE_MIN_CASES,
            "population": "the declared range of §7.0, not the round-0 ladder",
        },
        "design": {
            "core_slots": list(C.CORE_SLOTS),
            "spectrum_slots": list(C.SPECTRUM_SLOTS),
            "class_slot": C.CLASS_SLOT,
            "registered_slot_order": list(C.REGISTERED_SLOT_ORDER),
            "cells_per_block_full": C.N_CELLS_FULL,
            "cells_per_block_reduced": C.N_CELLS_REDUCED,
            "configurations": list(C.CONFIGURATIONS),
            "order_is": "a cell-level factor (§8.4)",
            "wording_allocation": "w(c1) = i mod 4; w(c2) = (i + floor(i/4)) "
                                  "mod 4; solo uses i mod 4",
            "blocks": C.N_BLOCKS,
            "M": C.M_DRAWS,
            "M_cal": C.M_CAL,
            "ladder_screen_draws": C.LADDER_SCREEN_DRAWS,
            "prompt_template": {"zero": C.PROMPT_ZERO, "one": C.PROMPT_ONE,
                                "two": C.PROMPT_TWO},
            "stem_sentence": C.STEM_SENTENCE,
            "stem_band": list(C.STEM_BAND),
            "greedy": {"blocks": C.GREEDY_BLOCKS, "draws": C.GREEDY_DRAWS,
                       "temperature": C.GREEDY_TEMPERATURE},
        },
        "topics": {**authoring_record(),
                   "split_hash": split_hash(split),
                   "split_counts": {k: len(v) for k, v in split.items()},
                   "split_seed": seeds.CARRIED_TOPIC_SPLIT_SEED,
                   "split_is": "v4r2's, carried unchanged",
                   "sequestered": C.N_SEQUESTERED},
        "decoding_policy_form": {
            "backend": "vLLM", "dtype": "bfloat16", "temperature": 0.7,
            "top_p": 0.9, "top_k": 50,
            "completion_cap_grid": list(C.COMPLETION_CAPS),
            "zero_shot": True, "single_turn": True,
            "no_examples_tools_retrieval_self_consistency_best_of_n": True,
        },
        "selection_rules": {
            "difficulty_coordinate": {
                "primary": C.DIFFICULTY_COORDINATE,
                "formula": "(solo - kappa) / (1 - kappa)",
                "kappa_measured_in": "the unconstrained cell of the same "
                                     "topic set at the same M",
                "secondary": C.SECONDARY_DIFFICULTY_COORDINATE,
                "degeneracy_ceiling": C.CHANCE_DEGENERACY_MAX,
            },
            "expansion_rule": {
                "source": "the frozen reserve of §7.0 and nowhere else",
                "max_rounds": C.EXPANSION_MAX_ROUNDS,
                "max_rungs_per_family_per_round":
                    C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND,
                "picks": "bisect between the adjacent measured severities "
                         "bracketing iota_A, or extend beyond the extreme "
                         "measured severity on the deficient side",
                "reads": "iota and severity, on development topics, and "
                         "nothing else",
            },
            "coverage_criterion": {
                "C1": "one eligible reference rung strictly below iota_A and "
                      "one strictly above",
                "C2": f"at least {C.COVERAGE_MIN_FAMILIES_PER_SIDE} eligible "
                      "reference families on each side",
                "C3": f"at least {C.COVERAGE_MIN_NEAR_RUNGS} eligible rungs "
                      f"within {C.COVERAGE_NEAR_CALIPER} of iota_A from at "
                      f"least {C.COVERAGE_MIN_NEAR_FAMILIES} families",
                "C4": f"at least {C.COVERAGE_MIN_STRADDLING_FAMILIES} "
                      "straddling families with at least "
                      f"{C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY} eligible "
                      f"rungs spanning {C.COVERAGE_MIN_WITHIN_FAMILY_SPAN}",
                "C5": f"at least {C.COVERAGE_MIN_ELIGIBLE_RUNGS} eligible "
                      "reference rungs in total",
                "C6": f"at least {C.SHORTLIST_REFERENCE_FAMILIES} eligible "
                      "reference families",
                "C7": f"an eligible class rung within "
                      f"{C.CLASS_MATCH_CALIPER} of iota_A; NOT decisive",
                "on_failure": "DIFFICULTY_SUPPORT_NOT_IDENTIFIED at design "
                              "time and the reduced spectrum arm",
            },
            "shortlist_rule": {
                "reference_families": C.SHORTLIST_REFERENCE_FAMILIES,
                "max_per_reference_family":
                    C.SHORTLIST_MAX_PER_REFERENCE_FAMILY,
                "class_families": C.N_CLASS_FAMILIES,
                "max_per_class_family": C.SHORTLIST_MAX_PER_CLASS_FAMILY,
                "ranking": "straddling feasibility first, then |iota_near - "
                           "iota_A|, then family identifier",
            },
            "n_star_selection_rule": {
                "band": list(C.TARGET_BAND), "aim": C.TARGET_AIM,
                "on": "raw solo compliance", "tie_break": "the smaller n"},
            "m_star_selection_rule": {
                "band": list(C.FOCAL_BAND), "aim": C.FOCAL_AIM,
                "on": "raw solo compliance",
                "tie_break": "the smaller m, the more restrictive severity"},
            "completion_cap_selection_rule": {
                "criterion": "smallest cap with truncation at most "
                             f"{C.CAP_TRUNCATION_MAX} over the constrained "
                             "prompts; every cap generated",
                "prompt_set": "four per pre-screen topic: load 0, A at the "
                              "largest n, B at the smallest m, and both"},
            "reference_admission_rule": {
                "matched_to": "A on instructed compliance",
                "caliper": C.REFERENCE_CALIPER,
                "newcombe_region": C.REFERENCE_NEWCOMBE_REGION,
                "prescreen_caliper": C.REFERENCE_PRESCREEN_CALIPER,
                "vacuity_max": C.REFERENCE_VACUITY_MAX,
                "within_family_tie_break": "the less restrictive severity",
                "between_family_tie_break": "the family identifier",
                "core_references": C.N_CORE_REFERENCES,
                "structural_diversity": "three distinct families",
                "class_requirement": "budget class only",
                "not_a_criterion": "any composed quantity (§13.9)",
            },
            "spectrum_selection_rule": {
                "offset": C.SPECTRUM_OFFSET,
                "eligibility_band": list(C.SPECTRUM_ELIGIBILITY_BAND),
                "straddling": "strictly below and strictly above iota_A, in "
                              "the same family as the core rung",
                "per_family": C.N_SPECTRUM_PER_FAMILY,
                "fit_points": C.N_FIT_POINTS,
            },
            "class_admission_rule": {
                "pool": "CL7, CL8, CP4, CP7 together",
                "criterion": "the eligible severity minimising "
                             "|iota_CL - iota_A|",
                "match_caliper": C.CLASS_MATCH_CALIPER,
                "never_enters": ["core references", "spectrum",
                                 "the difficulty fit", "Delta_R", "Rbar",
                                 "Xi"],
            },
            "support_rule": {
                "min_below": C.SUPPORT_MIN_BELOW,
                "min_above": C.SUPPORT_MIN_ABOVE,
                "min_families_per_side": C.SUPPORT_MIN_FAMILIES_PER_SIDE,
                "bootstrap_share_min": C.SUPPORT_BOOTSTRAP_SHARE_MIN,
            },
            "composed_headroom_band": list(C.COMPOSED_HEADROOM_BAND),
        },
        "estimands_and_families": {
            "families": {k: list(v) for k, v in C.FAMILY_MEMBERS.items()},
            "primary_family": C.PRIMARY_FAMILY,
            "difficulty_model_form":
                "Y_fs = alpha_f + beta * d_fs, ordinary least squares over "
                "the nine non-A companions, prediction at A using the mean "
                "intercept; A and the class companion are refused as inputs",
            "delta_difficulty_form":
                "D(B<-A) - (alphabar + beta * iota_A)",
            "delta_r_form": "E[X_B | A+B] against mean_j E[X_B | B+R_j], as "
                            "delivery losses",
        },
        "thresholds_and_regions": {
            "delta_r_generic": C.DELTA_R_GENERIC_THRESHOLD,
            "delta_r_pair_specific": C.DELTA_R_PAIR_SPECIFIC_THRESHOLD,
            "smallest_effect_of_interest": C.SMALLEST_EFFECT_OF_INTEREST,
            "equivalence_region": C.EQUIVALENCE_REGION,
            "delta_difficulty": dict(C.DELTA_DIFFICULTY_THRESHOLDS),
            "xi_has_magnitude_threshold": C.XI_HAS_MAGNITUDE_THRESHOLD,
            "provenance": dict(THRESHOLD_PROVENANCE),
        },
        "precision_preconditions": dict(C.PRECISION_PRECONDITIONS),
        "variance_model": {
            "p_one_minus_p": C.P_ONE_MINUS_P,
            "phi": [C.PHI_PRIMARY, C.PHI_ALTERNATE],
            "rho": C.RHO, "menu": [dict(e) for e in C.ALLOCATION_MENU],
            "beta_planning": C.BETA_PLANNING,
            "sum_w_squared_planning": C.SUM_W_SQUARED_PLANNING,
            "menu_rule": ("the smallest EXECUTABLE entry meeting every "
                          "precision precondition under the pre-freeze "
                          "re-estimate; entries needing more than 384 blocks "
                          "are not executable against a 528-question "
                          "released bank"),
        },
        "bootstrap": {"resamples": C.BOOTSTRAP_RESAMPLES, "unit": "block",
                      "construction": "studentised maximum modulus",
                      "refit_per_replicate": True,
                      "root_seed": seeds.BOOTSTRAP_ROOT_SEED,
                      "domain": seeds.DOMAIN_BOOTSTRAP},
        "seeds": {
            "generation_root": seeds.GENERATION_ROOT_SEED,
            "topic_split": seeds.CARRIED_TOPIC_SPLIT_SEED,
            "gate1_sample": seeds.GATE1_SAMPLE_SEED,
            "autorater_split": seeds.AUTORATER_SPLIT_SEED,
            "adversarial": seeds.ADVERSARIAL_SEED,
            "domains": list(seeds.V4R3_DOMAINS),
            "generation_derivation": ("root, stage label, model identity, "
                                      "prompt hash, draw index"),
            "no_draw_selector": True,
        },
        "masking": {"namespaces": list(C.MASK_NAMESPACES),
                    "min_differing_fraction": C.MASK_MIN_DIFFERING_FRACTION},
        "gate_rules": {
            "sequence": list(C.STAGE_SEQUENCE),
            "terminal_statuses": list(C.TERMINAL_STATUSES),
            "identification_statuses": list(C.IDENTIFICATION_STATUSES),
            "result_markers": list(C.RESULT_MARKERS),
            "verifier_bound_entry_points":
                list(C.VERIFIER_BOUND_ENTRY_POINTS),
            "gate3_is_terminal": False,
        },
        "artifact_semantics": {"states": list(C.ARTIFACT_STATES),
                               "types": list(C.ARTIFACT_TYPES)},
        "claim_ladder": {"levels": list(C.CLAIM_LEVELS),
                         "withheld": list(C.WITHHELD_CLAIM_LEVELS),
                         "measurement_bases": list(C.MEASUREMENT_BASES),
                         "scope_sentence": C.SCOPE_SENTENCE,
                         "class_sentence": C.CLASS_SENTENCE},
        "freeze_fields": list(FREEZE_FIELDS),
        "qualification_limits": {
            "duplicate_rate_max": C.DUPLICATE_QUALIFICATION_MAX,
            "missingness_report_threshold": C.MISSINGNESS_REPORT_THRESHOLD,
            "truncation_bound_threshold": C.TRUNCATION_BOUND_THRESHOLD,
        },
    }
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
            f"{found}; those reach the code only through the per-model "
            f"records (§6.1)")


def register(context: StudyContext, *, producing_commit: str,
             adoption: dict[str, Any], supersedes: str | None = None
             ) -> dict[str, Any]:
    """Write and sign the manifest, once, before the first qualification.

    ``supersedes`` names the manifest hash this one replaces. §26's artifact
    model carries a ``superseded`` state precisely so that a defective record
    is *retained and marked* rather than deleted or edited: the earlier file
    stays where it is, keeps its signature, and the new one names it. A
    manifest is never patched in place, and neither is one removed.
    """
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    manifest = build_manifest(context, producing_commit=producing_commit,
                              adoption=adoption)
    if supersedes:
        manifest["supersedes"] = supersedes
        manifest["manifest_hash"] = sha_obj(
            {k: v for k, v in manifest.items() if k != "manifest_hash"})
    context.registration_root.mkdir(parents=True, exist_ok=True)
    if supersedes and context.registration_manifest.exists():
        previous = fs.read_json(context.registration_manifest)
        archive = (context.registration_root
                   / f"registration_manifest_superseded_{supersedes[:12]}.json")
        fs.write_json_once(archive, previous)
        context.registration_manifest.unlink()
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
            f"the signed v4r3 registration manifest is missing at {path}. "
            "§6.1 fixes every study-wide rule in it BEFORE the first "
            "qualification, so no replication may be qualified without it")
    payload = verify_signed(fs.read_json(path), context.signing_key_path,
                            where="v4r3 registration manifest")
    if payload.get("study_id") != context.study_id:
        raise IntegrityError("the registration manifest belongs to another "
                             "study")
    return payload
