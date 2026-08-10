packages = {}
for name in ["torch", "transformers", "accelerate", "numpy", "pandas",
             "matplotlib", "statsmodels", "scipy"]:
    try:
        packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        packages[name] = None

stop_telemetry()

TELEMETRY_SUMMARY: dict[str, Any] = {}
if TELEMETRY:
    tel = pd.DataFrame(TELEMETRY)
    tel.to_csv(RUN_ROOT / "telemetry.csv", index=False)
    for column in tel.columns:
        if column == "t" or column in CUMULATIVE_COUNTERS or not tel[column].notna().any():
            continue
        TELEMETRY_SUMMARY[column] = {"mean": float(tel[column].mean()),
                                     "max": float(tel[column].max())}
    TELEMETRY_SUMMARY["_note"] = (
        "disk and process I/O are reported as *_delta from the first sample of "
        "this run; the raw counters are monotonic since boot.")

RUN_METRICS = {
    "phases_seconds": {k: round(v, 3) for k, v in PHASES.items()},
    "cache_stats": CACHE_STATS, "telemetry_samples": len(TELEMETRY),
    "telemetry_summary": TELEMETRY_SUMMARY, "packages": PACKAGE_VERSIONS,
    "batch_profiles": {s: batch_profile_summary(s).to_dict("records")
                       for s in ("benchmark", "screening", "prescreen",
                                 "confirmatory", "placebo")},
}

(RUN_ROOT / "environment.json").write_text(json.dumps({
    "hardware": HARDWARE, "packages": packages, "run_mode": CFG.run_mode,
    "dry_run": CFG.dry_run, "model_profile": CFG.model_profile,
    "model_id": CFG.model_id, "model_revision": CFG.model_revision,
    "stamp": PROFILE["stamp"], "produces_evidence": PROFILE["produces_evidence"],
    "selected_references": SELECTED_REFERENCES,
    "u_build": U_BUILD, "u_val": U_VAL, "u_test": U_TEST,
    "paraphrases_primary": P_FINAL,
    "paraphrases_held_out": list(CFG.paraphrase_holdout),
    "protocol_sha256": PLAN_SHA256, "execution_sha256": EXECUTION_SHA256,
    "run_id": RESOLVED_RUN_ID, "run_attempt_id": RUN_ATTEMPT_ID,
    "gates": {k: v.status for k, v in GATE_STATE.items()},
}, indent=2, default=str), encoding="utf-8")

pd.DataFrame(DEPARTURES or [{"stage": "none", "planned": "-",
                             "actual": "no departures recorded", "reason": "-"}]
             ).to_csv(RUN_ROOT / "departures.csv", index=False)

for name, obj in [("gate_state", pd.DataFrame([v.as_dict() for v in GATE_STATE.values()])),
                  ("primary_effects", PRIMARY), ("claim_rule", CLAIM),
                  ("secondary_order_average", POOLED),
                  ("secondary_stochastic_reference", STOCHASTIC),
                  ("order_effects", ORDER), ("gee_model", GEE_RESULT),
                  ("robustness_grid", ROBUSTNESS),
                  ("falsification_individual", FALSIFICATION_INDIVIDUAL),
                  ("falsification_panel", FALSIFICATION_PANEL),
                  ("condition_failure_rates", CONDITION_RATES),
                  ("power_planning", POWER_PLANNING),
                  ("pool_dependence_audit", POOL_AUDIT),
                  ("protocol_fields", PROTOCOL_FIELDS_FRAME)]:
    if obj is not None and len(obj):
        obj.to_csv(SCORE_DIR / f"{name}.csv")

with phase("archiving"):
    # =================================================================
    # Two different questions, and v14 answered only one of them.
    #
    #   CONFIRMATORY_DESIGN_VALID   Was this dataset produced by a correctly
    #                               gated, correctly frozen, correctly executed
    #                               confirmatory design? This is a HISTORICAL
    #                               fact. Gate 4 is deliberately excluded from
    #                               it, because U_test is terminal: it runs
    #                               after the freeze and after confirmation, and
    #                               nothing it finds can travel back in time and
    #                               make a correctly executed design incorrect.
    #
    #   FINAL_FALSIFICATION_STATUS  Did the frozen reference architecture
    #                               generalise to the untouched targets? This
    #                               governs INTERPRETATION.
    #
    # v14 folded Gate 4 into the export label, so a Gate 4 failure relabelled a
    # valid confirmatory dataset as provisional -- which reads as though the
    # confirmation had not really happened, and invites regenerating it.
    # =================================================================
    _measurement_ok = PARAPHRASE_AUDIT_PASSED and VERIFIER_GATE_PASSED
    _pre_confirmatory = [k for k in GATE_STATE if k != "4_falsification"]
    _pre_gates_ok = all(GATE_STATE[k].passed for k in _pre_confirmatory)
    _bypassed = any(v.dry_run_bypassed for v in GATE_STATE.values())
    _gate4 = GATE_STATE.get("4_falsification")

    CONFIRMATORY_DESIGN_VALID = bool(
        _measurement_ok and _pre_gates_ok and not _bypassed
        and PROFILE["produces_evidence"] and not CFG.dry_run
        and bool(FREEZE.get("frozen")) and PLAN_SHA256 == FREEZE.get("plan_sha256"))
    FINAL_FALSIFICATION_STATUS = (
        _gate4.status if _gate4 is not None else "NOT_RUN")
    CONFIRMATORY_EXPORT_ALLOWED = CONFIRMATORY_DESIGN_VALID

    if not CONFIRMATORY_DESIGN_VALID:
        EXPORT_LABEL = "PROVISIONAL"
    elif FINAL_FALSIFICATION_STATUS == GateStatus.PASS:
        EXPORT_LABEL = "CONFIRMATORY"
    else:
        EXPORT_LABEL = f"CONFIRMATORY__{FINAL_FALSIFICATION_STATUS}"

    EXPORT_STATUS = {
        "confirmatory_design_valid": CONFIRMATORY_DESIGN_VALID,
        "final_falsification_status": FINAL_FALSIFICATION_STATUS,
        "export_label": EXPORT_LABEL,
        "measurement_valid": _measurement_ok,
        "pre_confirmatory_gates_passed": _pre_gates_ok,
        "any_gate_bypassed": _bypassed,
        "profile_produces_evidence": bool(PROFILE["produces_evidence"]),
        "frozen": bool(FREEZE.get("frozen")),
        "plan_sha256": PLAN_SHA256,
        "gate4_excluded_from_design_validity": True,
    }
    durable_write(GATE_DIR / "export_status.json",
                  json.dumps(EXPORT_STATUS, indent=2, default=str))

    EXPORT_DIR = EXPORT_ROOT / ("confirmatory" if CONFIRMATORY_DESIGN_VALID
                                else "provisional")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    _journal = sum(1 for p in RESPONSE_DIR.rglob("*") if p.is_file())

    status_lines = [
        EXPORT_LABEL, "",
        f"confirmatory design valid : {CONFIRMATORY_DESIGN_VALID}",
        f"final falsification       : {FINAL_FALSIFICATION_STATUS}",
        f"protocol      : {PLAN_SHA256}",
        f"model profile : {CFG.model_profile}  ({PROFILE['stamp']})",
        f"model         : {CFG.model_id} @ {CFG.model_revision}",
        f"run id        : {RESOLVED_RUN_ID}",
        f"references    : {SELECTED_REFERENCES}",
        f"wordings      : primary {P_FINAL}, held out {list(CFG.paraphrase_holdout)}",
        "", "Gates",
    ] + [f"  {k:20s} : {v.status}"
         + ("  [DRY-RUN BYPASS]" if v.dry_run_bypassed else "")
         for k, v in GATE_STATE.items()] + [
        "", "Measurement validity",
        f"  paraphrase audit signed off : {PARAPHRASE_AUDIT_PASSED}",
        f"  verifier reliability        : {VERIFIER_GATE_PASSED}", "",
        f"Per-batch journal: {_journal} files under responses/, not archived here; "
        "its content is in scores/responses.csv.", "",
    ]
    if not PROFILE["produces_evidence"]:
        status_lines.append(
            f"{PROFILE['stamp']}: this profile produces no scientific evidence. "
            "Every empirical gate must be rerun from scratch on the study profile.")
    if CFG.dry_run:
        status_lines.append("DRY RUN. Every response is synthetic. Not evidence.")
    if _bypassed:
        status_lines.append(
            "One or more gates were bypassed under dry run. See departures.csv.")
    if not CONFIRMATORY_DESIGN_VALID:
        status_lines.append(
            "These outputs must not be described as confirmatory.")
    elif FINAL_FALSIFICATION_STATUS != GateStatus.PASS:
        status_lines += [
            "",
            "REQUIRED INTERPRETATION",
            "",
            "  The confirmatory design is valid and its matrix stands as",
            "  generated. It is neither hidden nor regenerated.",
            "",
            "  The frozen reference architecture FAILED terminal generalisation",
            f"  on U_test ({FINAL_FALSIFICATION_STATUS}). Any manuscript reporting",
            "  this matrix must state that the reference architecture did not",
            "  generalise to the untouched targets, and must not present the",
            "  tau matrix as a reference-robust interference claim.",
            "",
            "  U_test is terminal. Repairing the architecture in response to",
            "  this result is a new protocol version and a new experiment.",
        ]
    (EXPORT_DIR / "STATUS.txt").write_text("\n".join(status_lines) + "\n", encoding="utf-8")

    _skip_dirs = {"exports", "responses", "quarantine"}
    files = [p for p in RUN_ROOT.rglob("*")
             if p.is_file() and p.suffix != ".zip"
             and p.name != "sha256_manifest.json"
             and not _skip_dirs & set(p.relative_to(RUN_ROOT).parts)]
    with phase("hashing"):
        manifest = {str(p.relative_to(RUN_ROOT)): sha_file(p) for p in files}
    manifest_path = EXPORT_DIR / "sha256_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    label = "confirmatory" if CONFIRMATORY_DESIGN_VALID else "provisional"
    archive = EXPORT_DIR / f"outputs_{label}_{CFG.model_profile}_{CFG.run_mode}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, arcname=p.relative_to(RUN_ROOT))
        zf.write(manifest_path, arcname="sha256_manifest.json")
        zf.write(EXPORT_DIR / "STATUS.txt", arcname="STATUS.txt")

PHASE_COVERAGE = {
    "timed": sorted(PHASES),
    "declared_but_untimed": sorted(set(PHASE_NAMES) - set(PHASES)),
    "timed_but_undeclared": sorted(n for n in PHASES if n not in PHASE_NAMES
                                   and not n.startswith("generate_")),
}
RUN_METRICS["phase_coverage"] = PHASE_COVERAGE
(RUN_ROOT / "run_metrics.json").write_text(
    json.dumps(RUN_METRICS, indent=2, default=str), encoding="utf-8")
display(pd.Series(PHASES).sort_values(ascending=False).round(2).to_frame("seconds"))
if PHASE_COVERAGE["declared_but_untimed"]:
    print("phases declared but not timed this run (skipped cells): "
          f"{PHASE_COVERAGE['declared_but_untimed']}")

print("archive :", archive)
print("entries :", len(manifest), f"(+ {_journal} journal files under responses/)")
print("status  :", label.upper())
print("durable :", RUN_ROOT)
print("departures recorded:", len(DEPARTURES))
checkpoint("export", {"status": label, "archive": str(archive)})
