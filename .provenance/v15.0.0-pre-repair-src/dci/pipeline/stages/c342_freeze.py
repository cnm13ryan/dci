"""Stage 342 — migrated from notebook cell 342.py (freeze).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/342.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import bootstrap_functional, holm, paired_advantage, simultaneous_abs_upper, simultaneous_bounds  # noqa: F401
from dci.exceptions import FrozenPlanMismatch  # noqa: F401
from dci.provenance.hashes import sha, sha_text  # noqa: F401
from dci.verifiers.rules import _per_sentence, count_status, fraction_status, integer_tokens, normalize_text, split_sentences, word_tokens  # noqa: F401

S.require_gate("0_implementation", "M_measurement", "1_u_bank", "2_feasibility",
             "3_validation", "3b_wording")

with S.phase("freeze"):
    S.WEIGHTS = S.fit_stochastic_weights(S.SIGNATURE, S.SELECTED_REFERENCES, S.CFG.focal_id,
                                     list(S.CALIPERS.index), S.MATCH_DISTANCE)
    S.J_EFF = S.j_effective(S.WEIGHTS)
    S.STOCHASTIC_ESTIMAND_AVAILABLE = bool(S.STOCHASTIC_AUTHORIZED
                                         and S.J_EFF >= S.CFG.j_eff_floor)
    display(S.WEIGHTS.round(4).to_frame("weight"))
    if not S.STOCHASTIC_ESTIMAND_AVAILABLE:
        S.log_departure("freeze", "stochastic reference intervention reported",
                      f"withheld (g2 authorized={S.STOCHASTIC_AUTHORIZED}, "
                      f"J_eff={S.J_EFF:.2f})",
                      "the per-reference matrix uses no weights and is unaffected")

    VERIFIER_SOURCE_SHA256 = S.source_fingerprint(
        [normalize_text, split_sentences, word_tokens, integer_tokens,
         count_status, fraction_status, _per_sentence]
        + [globals()[n] for n in sorted(globals()) if n.startswith("v_")])
    ANALYSIS_SOURCE_SHA256 = S.source_fingerprint(
        [bootstrap_functional, simultaneous_bounds, simultaneous_abs_upper,
         paired_advantage, holm, S.power_simulation, S.discrepancy_frames,
         S.panel_residual_frames, S.authorize_primary])
    SELECTION_SOURCE_SHA256 = S.source_fingerprint(
        [S.make_signature_fn, S.sensitivity_by_rotation, S.sensitivity_slopes,
         S.slope_jackknife, S.derive_calipers, S.mismatch_table, S.contender_set,
         S.precision_report, S.admit_candidates, S.select_panel,
         S.fit_stochastic_weights, S.hard_eligible_universe,
         S.evaluate_pseudo_focal_cohort])

    def _field(name: str, category: str, kind: str, value: Any,
               description: str) -> dict[str, Any]:
        return {"field": name, "category": category, "kind": kind,
                "value": value, "description": description}

    PROTOCOL_FIELDS: list[dict[str, Any]] = [
        _field("protocol_version", "identity", "value", S.CFG.protocol_version, "protocol version"),
        _field("model_profile", "model", "value", S.CFG.model_profile, "dev_fast, pilot or study"),
        _field("model_id", "model", "value", S.CFG.model_id, "Hugging Face model id"),
        _field("model_revision", "model", "value", S.CFG.model_revision,
               "immutable commit; never 'main'"),
        _field("tokenizer_sha256", "model", "hash", S.TOKENIZER_STATE["tokenizer_sha256"],
               "vocabulary, special tokens and class"),
        _field("chat_template_sha256", "model", "hash",
               S.TOKENIZER_STATE["chat_template_sha256"], "rendered chat template"),
        _field("transformers_version", "software", "value",
               S.PACKAGE_VERSIONS["transformers"], "inference library version"),
        _field("engine", "software", "value", S.CFG.engine, "inference engine"),
        _field("inference_dtype", "software", "value", S.CFG.inference_dtype, "numerical condition"),
        _field("attn_implementation", "software", "value", S.CFG.attn_implementation,
               "attention kernel"),
        _field("do_sample", "decoding", "value", S.CFG.do_sample, "sampling on or off"),
        _field("temperature", "decoding", "value", S.CFG.temperature, "sampling temperature"),
        _field("top_p", "decoding", "value", S.CFG.top_p, "nucleus sampling"),
        _field("max_new_tokens", "decoding", "value", S.CFG.max_new_tokens, "generation length"),
        _field("max_input_tokens", "decoding", "value", S.CFG.max_input_tokens, "truncation"),
        _field("initial_batch_size", "decoding", "value", S.CFG.initial_batch_size,
               "batch membership affects the sample"),
        _field("adaptive_batching", "decoding", "value", S.CFG.adaptive_batching,
               "off in a confirmatory run"),
        _field("base_seed", "seeds", "value", S.CFG.base_seed, "root seed"),
        _field("screening_seeds", "seeds", "value", list(S.CFG.screening_seeds), "stage seeds"),
        _field("calibration_seeds", "seeds", "value", list(S.CFG.calibration_seeds), "stage seeds"),
        _field("confirmatory_seeds", "seeds", "value", list(S.CFG.confirmatory_seeds), "stage seeds"),
        _field("wording_seeds", "seeds", "value", list(S.CFG.wording_seeds), "stage seeds"),
        _field("task_bank_sha256", "tasks", "hash",
               sha(S.TASKS.to_dict("records")), "every task id and its text"),
        _field("calibration_tasks", "tasks", "value",
               [t["task_id"] for t in S.CALIBRATION_TASKS], "calibration split"),
        _field("confirmatory_tasks", "tasks", "value",
               [t["task_id"] for t in S.CONFIRMATORY_TASKS], "confirmatory split"),
        _field("wording_tasks", "tasks", "value",
               [t["task_id"] for t in S.WORDING_TASKS], "Gate 3b split"),
        _field("instructions_sha256", "paraphrases", "hash",
               sha({k: list(v) for k, v in S.INSTRUCTIONS.items()}),
               "every rendered wording"),
        _field("paraphrases_primary", "paraphrases", "value", S.P_FINAL,
               "wordings in the primary estimand"),
        _field("paraphrases_held_out", "paraphrases", "value",
               list(S.CFG.paraphrase_holdout), "Gate 3b only"),
        _field("paraphrase_audit_sha256", "audits", "hash", S.PARAPHRASE_AUDIT_SHA256,
               "signed semantic audit"),
        _field("verifier_audit_sha256", "audits", "hash", S.VERIFIER_AUDIT_SHA256,
               "signed reliability audit"),
        _field("verifier_source_sha256", "verifiers", "hash", VERIFIER_SOURCE_SHA256,
               "verifier implementation"),
        _field("coupling_response_bank_sha256", "verifiers", "hash",
               S.RESPONSE_BANK_SHA256, "bank kappa is measured on"),
        _field("coupling_mutation_sha256", "verifiers", "hash", S.MUTATION_SPEC_SHA256,
               "mutation specification"),
        _field("coupling_edit_sha256", "verifiers", "hash", S.COUPLING_SPEC_SHA256,
               "coupling edit specification"),
        _field("u_split_sha256", "unrelated_targets", "hash", sha(S.U_SPLIT),
               "build, validation and test assignment"),
        _field("u_build", "unrelated_targets", "value", S.U_BUILD, "feature targets"),
        _field("u_val", "unrelated_targets", "value", S.U_VAL, "validation targets"),
        _field("u_test", "unrelated_targets", "value", S.U_TEST, "falsification targets"),
        _field("candidate_pool", "pool", "value", list(S.CANDIDATE_IDS), "declared pool"),
        _field("prescreen_retained", "pool", "value", S.PRESCREEN_KEPT, "narrowed pool"),
        _field("hard_eligible_universe", "pool", "value", S.PSEUDO_UNIVERSE,
               "B-independent universe"),
        _field("feature_roles_sha256", "features", "hash", S.FEATURE_ROLES_SHA256,
               "frozen causal role of every feature"),
        _field("calipers", "calipers", "value",
               {k: float(v) for k, v in S.CALIPERS["caliper"].items()},
               "SESOI divided by conservative upper sensitivity"),
        _field("caliper_rule_sha256", "calipers", "hash", SELECTION_SOURCE_SHA256,
               "selection and caliper implementation"),
        _field("sesoi", "calipers", "value", S.CFG.sesoi_risk_difference, "smallest effect of interest"),
        _field("selected_references", "selection", "value", S.SELECTED_REFERENCES,
               "the primary panel"),
        _field("pseudo_focal_cohort", "validation", "value", S.PSEUDO_COHORT,
               "Gate 3 cohort, frozen before U_val"),
        _field("stochastic_weights", "selection", "value",
               {k: float(v) for k, v in S.WEIGHTS.items()}, "secondary estimand weights"),
        _field("analysis_sha256", "analysis", "hash", ANALYSIS_SOURCE_SHA256,
               "estimator and inference implementation"),
        _field("confidence_level", "analysis", "value", S.CFG.confidence_level, "interval level"),
        _field("bootstrap_reps", "analysis", "value", S.CFG.bootstrap_reps, "resamples"),
        _field("cluster_level", "analysis", "value", S.CLUSTER_LEVEL, "resampling unit"),
    ]
    S.PROTOCOL_FIELDS_FRAME = pd.DataFrame(PROTOCOL_FIELDS)
    S.PROTOCOL_FIELDS_FRAME.to_csv(S.CONFIG_DIR / "protocol_fields.csv", index=False)
    S.durable_write(S.CONFIG_DIR / "protocol_fields.json",
                  json.dumps(PROTOCOL_FIELDS, indent=2, default=str))

    PLAN = {
        "protocol_version": S.CFG.protocol_version,
        "fields": PROTOCOL_FIELDS,
        "constraint_registry": {k: asdict(v) for k, v in S.CONSTRAINTS.items()},
        "rule_families": {k: {"invariants": list(v.invariants),
                              "templates": list(v.templates)}
                          for k, v in S.RULE_FAMILIES.items()},
        "system_message": S.SYSTEM_MESSAGE,
        "feature_roles": S.FEATURE_ROLES,
        "primary_estimand": (
            "the J x 2 matrix tau_{j,o} = E_X[mu_A(B,X,o) - mu_A(C_j,X,o)], "
            "co-primary at both presentation orders, over the g1 panel of "
            "individually admissible references"),
        "reference_robust_claim_rule": (
            "the simultaneous max-T lower bound on min_j tau_{j,o} must exceed "
            "zero at each order separately"),
        "secondary_estimands": [
            "50/50 order average, labelled as such",
            "stochastic reference intervention (only if g2 validated)",
            "order contrast", "GEE logistic model", "homogeneity",
            "g0 broad-eligible benchmark", "U_test falsification"],
        "gates": {k: v.as_dict() for k, v in S.GATE_STATE.items()},
        "pool_dependence": S.POOL_AUDIT.to_dict("index"),
        "exclusions": "none; generation failures score as failures",
        "stopping_rule": "fixed N, no optional stopping, no interim looks",
        "n_blocks_per_contrast": (len(S.CONFIRMATORY_TASKS) * len(S.P_FINAL)
                                  * len(S.CFG.confirmatory_seeds)),
    }
    S.PLAN_SHA256 = sha_text(json.dumps(PLAN, sort_keys=True, default=str))

    PREREGISTRATION = {
        "protocol_sha256": S.PLAN_SHA256, "plan": PLAN,
        "metadata": {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "model_profile": S.CFG.model_profile,
            "produces_evidence": S.PROFILE["produces_evidence"],
            "stamp": S.PROFILE["stamp"],
            "execution_sha256": S.EXECUTION_SHA256,
            "execution_condition": S.EXECUTION_CONDITION,
            "hardware_recorded_separately": S.HARDWARE,
            "run_id": S.RESOLVED_RUN_ID,
        },
    }
    PREREG_PATH = S.CONFIG_DIR / "preregistration.json"
    if PREREG_PATH.exists():
        existing = json.loads(PREREG_PATH.read_text())
        if existing.get("protocol_sha256") != S.PLAN_SHA256:
            raise FrozenPlanMismatch(
                "the scientific protocol differs from the one frozen in this run "
                f"directory.\n  frozen:  {existing.get('protocol_sha256')}\n"
                f"  current: {S.PLAN_SHA256}\nA changed protocol is a new study. "
                "Start a new run id rather than overwriting a freeze that "
                "confirmatory data was generated under.")
    else:
        S.durable_write(PREREG_PATH, json.dumps(PREREGISTRATION, indent=2, default=str))

# The freeze is an object with a truth value, so export can ask whether the
# design was actually frozen rather than inferring it from the gates.
S.FREEZE = {
    "frozen": True,
    "plan_sha256": S.PLAN_SHA256,
    "execution_sha256": S.EXECUTION_SHA256,
    "hardware_class": S.HARDWARE_CLASS,
    "hardware_class_sha256": S.HARDWARE_CLASS_SHA256,
    "frozen_utc": PREREGISTRATION["metadata"]["created_utc"],
    "references": list(S.SELECTED_REFERENCES),
    "primary_estimand": S.CFG.primary_estimand,
}
S.durable_write(S.CONFIG_DIR / "freeze.json", json.dumps(S.FREEZE, indent=2, default=str))
# From here on, a scientific batch may not cross a hardware class boundary.
S.assert_hardware_class(S.FREEZE["hardware_class"])

print("Protocol hash :", S.PLAN_SHA256)
print("Execution hash:", S.EXECUTION_SHA256)
print("Hardware class:", S.HARDWARE_CLASS_SHA256[:16], S.HARDWARE_CLASS.get("gpu_name"))
print("Profile       :", S.CFG.model_profile, "|", S.PROFILE["stamp"])
print("References    :", S.SELECTED_REFERENCES)
print("Weights       :", {k: round(float(v), 3) for k, v in S.WEIGHTS.items()},
      f"J_eff={S.J_EFF:.2f}")
print(f"Protocol fields inventoried: {len(PROTOCOL_FIELDS)}")
if not S.PROFILE["produces_evidence"]:
    print(f"\n{S.PROFILE['stamp']}: this freeze is an engineering or feasibility "
          "artefact. It cannot authorize a scientific claim, and every empirical "
          "gate must be rerun from scratch on the study profile.")
S.checkpoint("freeze", {"protocol_sha256": S.PLAN_SHA256})
