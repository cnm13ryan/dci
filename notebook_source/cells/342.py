require_gate("0_implementation", "M_measurement", "1_u_bank", "2_feasibility",
             "3_validation", "3b_wording")

with phase("freeze"):
    WEIGHTS = fit_stochastic_weights(SIGNATURE, SELECTED_REFERENCES, CFG.focal_id,
                                     list(CALIPERS.index), MATCH_DISTANCE)
    J_EFF = j_effective(WEIGHTS)
    STOCHASTIC_ESTIMAND_AVAILABLE = bool(STOCHASTIC_AUTHORIZED
                                         and J_EFF >= CFG.j_eff_floor)
    display(WEIGHTS.round(4).to_frame("weight"))
    if not STOCHASTIC_ESTIMAND_AVAILABLE:
        log_departure("freeze", "stochastic reference intervention reported",
                      f"withheld (g2 authorized={STOCHASTIC_AUTHORIZED}, "
                      f"J_eff={J_EFF:.2f})",
                      "the per-reference matrix uses no weights and is unaffected")

    VERIFIER_SOURCE_SHA256 = source_fingerprint(
        [normalize_text, split_sentences, word_tokens, integer_tokens,
         count_status, fraction_status, _per_sentence]
        + [globals()[n] for n in sorted(globals()) if n.startswith("v_")])
    ANALYSIS_SOURCE_SHA256 = source_fingerprint(
        [bootstrap_functional, simultaneous_bounds, simultaneous_abs_upper,
         paired_advantage, holm, power_simulation, discrepancy_frames,
         panel_residual_frames, authorize_primary])
    SELECTION_SOURCE_SHA256 = source_fingerprint(
        [make_signature_fn, sensitivity_by_rotation, sensitivity_slopes,
         slope_jackknife, derive_calipers, mismatch_table, contender_set,
         precision_report, admit_candidates, select_panel,
         fit_stochastic_weights, hard_eligible_universe,
         evaluate_pseudo_focal_cohort])

    def _field(name: str, category: str, kind: str, value: Any,
               description: str) -> dict[str, Any]:
        return {"field": name, "category": category, "kind": kind,
                "value": value, "description": description}

    PROTOCOL_FIELDS: list[dict[str, Any]] = [
        _field("protocol_version", "identity", "value", CFG.protocol_version, "protocol version"),
        _field("model_profile", "model", "value", CFG.model_profile, "dev_fast, pilot or study"),
        _field("model_id", "model", "value", CFG.model_id, "Hugging Face model id"),
        _field("model_revision", "model", "value", CFG.model_revision,
               "immutable commit; never 'main'"),
        _field("tokenizer_sha256", "model", "hash", TOKENIZER_STATE["tokenizer_sha256"],
               "vocabulary, special tokens and class"),
        _field("chat_template_sha256", "model", "hash",
               TOKENIZER_STATE["chat_template_sha256"], "rendered chat template"),
        _field("transformers_version", "software", "value",
               PACKAGE_VERSIONS["transformers"], "inference library version"),
        _field("engine", "software", "value", CFG.engine, "inference engine"),
        _field("inference_dtype", "software", "value", CFG.inference_dtype, "numerical condition"),
        _field("attn_implementation", "software", "value", CFG.attn_implementation,
               "attention kernel"),
        _field("do_sample", "decoding", "value", CFG.do_sample, "sampling on or off"),
        _field("temperature", "decoding", "value", CFG.temperature, "sampling temperature"),
        _field("top_p", "decoding", "value", CFG.top_p, "nucleus sampling"),
        _field("max_new_tokens", "decoding", "value", CFG.max_new_tokens, "generation length"),
        _field("max_input_tokens", "decoding", "value", CFG.max_input_tokens, "truncation"),
        _field("initial_batch_size", "decoding", "value", CFG.initial_batch_size,
               "batch membership affects the sample"),
        _field("adaptive_batching", "decoding", "value", CFG.adaptive_batching,
               "off in a confirmatory run"),
        _field("base_seed", "seeds", "value", CFG.base_seed, "root seed"),
        _field("screening_seeds", "seeds", "value", list(CFG.screening_seeds), "stage seeds"),
        _field("calibration_seeds", "seeds", "value", list(CFG.calibration_seeds), "stage seeds"),
        _field("confirmatory_seeds", "seeds", "value", list(CFG.confirmatory_seeds), "stage seeds"),
        _field("wording_seeds", "seeds", "value", list(CFG.wording_seeds), "stage seeds"),
        _field("task_bank_sha256", "tasks", "hash",
               sha(TASKS.to_dict("records")), "every task id and its text"),
        _field("calibration_tasks", "tasks", "value",
               [t["task_id"] for t in CALIBRATION_TASKS], "calibration split"),
        _field("confirmatory_tasks", "tasks", "value",
               [t["task_id"] for t in CONFIRMATORY_TASKS], "confirmatory split"),
        _field("wording_tasks", "tasks", "value",
               [t["task_id"] for t in WORDING_TASKS], "Gate 3b split"),
        _field("instructions_sha256", "paraphrases", "hash",
               sha({k: list(v) for k, v in INSTRUCTIONS.items()}),
               "every rendered wording"),
        _field("paraphrases_primary", "paraphrases", "value", P_FINAL,
               "wordings in the primary estimand"),
        _field("paraphrases_held_out", "paraphrases", "value",
               list(CFG.paraphrase_holdout), "Gate 3b only"),
        _field("paraphrase_audit_sha256", "audits", "hash", PARAPHRASE_AUDIT_SHA256,
               "signed semantic audit"),
        _field("verifier_audit_sha256", "audits", "hash", VERIFIER_AUDIT_SHA256,
               "signed reliability audit"),
        _field("verifier_source_sha256", "verifiers", "hash", VERIFIER_SOURCE_SHA256,
               "verifier implementation"),
        _field("coupling_response_bank_sha256", "verifiers", "hash",
               RESPONSE_BANK_SHA256, "bank kappa is measured on"),
        _field("coupling_mutation_sha256", "verifiers", "hash", MUTATION_SPEC_SHA256,
               "mutation specification"),
        _field("coupling_edit_sha256", "verifiers", "hash", COUPLING_SPEC_SHA256,
               "coupling edit specification"),
        _field("u_split_sha256", "unrelated_targets", "hash", sha(U_SPLIT),
               "build, validation and test assignment"),
        _field("u_build", "unrelated_targets", "value", U_BUILD, "feature targets"),
        _field("u_val", "unrelated_targets", "value", U_VAL, "validation targets"),
        _field("u_test", "unrelated_targets", "value", U_TEST, "falsification targets"),
        _field("candidate_pool", "pool", "value", list(CANDIDATE_IDS), "declared pool"),
        _field("prescreen_retained", "pool", "value", PRESCREEN_KEPT, "narrowed pool"),
        _field("hard_eligible_universe", "pool", "value", PSEUDO_UNIVERSE,
               "B-independent universe"),
        _field("feature_roles_sha256", "features", "hash", FEATURE_ROLES_SHA256,
               "frozen causal role of every feature"),
        _field("calipers", "calipers", "value",
               {k: float(v) for k, v in CALIPERS["caliper"].items()},
               "SESOI divided by conservative upper sensitivity"),
        _field("caliper_rule_sha256", "calipers", "hash", SELECTION_SOURCE_SHA256,
               "selection and caliper implementation"),
        _field("sesoi", "calipers", "value", CFG.sesoi_risk_difference, "smallest effect of interest"),
        _field("selected_references", "selection", "value", SELECTED_REFERENCES,
               "the primary panel"),
        _field("pseudo_focal_cohort", "validation", "value", PSEUDO_COHORT,
               "Gate 3 cohort, frozen before U_val"),
        _field("stochastic_weights", "selection", "value",
               {k: float(v) for k, v in WEIGHTS.items()}, "secondary estimand weights"),
        _field("analysis_sha256", "analysis", "hash", ANALYSIS_SOURCE_SHA256,
               "estimator and inference implementation"),
        _field("confidence_level", "analysis", "value", CFG.confidence_level, "interval level"),
        _field("bootstrap_reps", "analysis", "value", CFG.bootstrap_reps, "resamples"),
        _field("cluster_level", "analysis", "value", CLUSTER_LEVEL, "resampling unit"),
    ]
    PROTOCOL_FIELDS_FRAME = pd.DataFrame(PROTOCOL_FIELDS)
    PROTOCOL_FIELDS_FRAME.to_csv(CONFIG_DIR / "protocol_fields.csv", index=False)
    durable_write(CONFIG_DIR / "protocol_fields.json",
                  json.dumps(PROTOCOL_FIELDS, indent=2, default=str))

    PLAN = {
        "protocol_version": CFG.protocol_version,
        "fields": PROTOCOL_FIELDS,
        "constraint_registry": {k: asdict(v) for k, v in CONSTRAINTS.items()},
        "rule_families": {k: {"invariants": list(v.invariants),
                              "templates": list(v.templates)}
                          for k, v in RULE_FAMILIES.items()},
        "system_message": SYSTEM_MESSAGE,
        "feature_roles": FEATURE_ROLES,
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
        "gates": {k: v.as_dict() for k, v in GATE_STATE.items()},
        "pool_dependence": POOL_AUDIT.to_dict("index"),
        "exclusions": "none; generation failures score as failures",
        "stopping_rule": "fixed N, no optional stopping, no interim looks",
        "n_blocks_per_contrast": (len(CONFIRMATORY_TASKS) * len(P_FINAL)
                                  * len(CFG.confirmatory_seeds)),
    }
    PLAN_SHA256 = sha_text(json.dumps(PLAN, sort_keys=True, default=str))

    PREREGISTRATION = {
        "protocol_sha256": PLAN_SHA256, "plan": PLAN,
        "metadata": {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "model_profile": CFG.model_profile,
            "produces_evidence": PROFILE["produces_evidence"],
            "stamp": PROFILE["stamp"],
            "execution_sha256": EXECUTION_SHA256,
            "execution_condition": EXECUTION_CONDITION,
            "hardware_recorded_separately": HARDWARE,
            "run_id": RESOLVED_RUN_ID,
        },
    }
    PREREG_PATH = CONFIG_DIR / "preregistration.json"
    if PREREG_PATH.exists():
        existing = json.loads(PREREG_PATH.read_text())
        if existing.get("protocol_sha256") != PLAN_SHA256:
            raise FrozenPlanMismatch(
                "the scientific protocol differs from the one frozen in this run "
                f"directory.\n  frozen:  {existing.get('protocol_sha256')}\n"
                f"  current: {PLAN_SHA256}\nA changed protocol is a new study. "
                "Start a new run id rather than overwriting a freeze that "
                "confirmatory data was generated under.")
    else:
        durable_write(PREREG_PATH, json.dumps(PREREGISTRATION, indent=2, default=str))

# The freeze is an object with a truth value, so export can ask whether the
# design was actually frozen rather than inferring it from the gates.
FREEZE = {
    "frozen": True,
    "plan_sha256": PLAN_SHA256,
    "execution_sha256": EXECUTION_SHA256,
    "hardware_class": HARDWARE_CLASS,
    "hardware_class_sha256": HARDWARE_CLASS_SHA256,
    "frozen_utc": PREREGISTRATION["metadata"]["created_utc"],
    "references": list(SELECTED_REFERENCES),
    "primary_estimand": CFG.primary_estimand,
}
durable_write(CONFIG_DIR / "freeze.json", json.dumps(FREEZE, indent=2, default=str))
# From here on, a scientific batch may not cross a hardware class boundary.
assert_hardware_class(FREEZE["hardware_class"])

print("Protocol hash :", PLAN_SHA256)
print("Execution hash:", EXECUTION_SHA256)
print("Hardware class:", HARDWARE_CLASS_SHA256[:16], HARDWARE_CLASS.get("gpu_name"))
print("Profile       :", CFG.model_profile, "|", PROFILE["stamp"])
print("References    :", SELECTED_REFERENCES)
print("Weights       :", {k: round(float(v), 3) for k, v in WEIGHTS.items()},
      f"J_eff={J_EFF:.2f}")
print(f"Protocol fields inventoried: {len(PROTOCOL_FIELDS)}")
if not PROFILE["produces_evidence"]:
    print(f"\n{PROFILE['stamp']}: this freeze is an engineering or feasibility "
          "artefact. It cannot authorize a scientific claim, and every empirical "
          "gate must be rerun from scratch on the study profile.")
checkpoint("freeze", {"protocol_sha256": PLAN_SHA256})
