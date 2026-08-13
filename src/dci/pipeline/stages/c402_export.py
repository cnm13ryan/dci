"""Stage 402 — migrated from notebook cell 402.py (export).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/402.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.provenance.hashes import sha_file  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

packages = {}
for name in ["torch", "transformers", "accelerate", "numpy", "pandas",
             "matplotlib", "statsmodels", "scipy"]:
    try:
        packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        packages[name] = None

S.stop_telemetry()

TELEMETRY_SUMMARY: dict[str, Any] = {}
if S.TELEMETRY:
    tel = pd.DataFrame(S.TELEMETRY)
    tel.to_csv(S.RUN_ROOT / "telemetry.csv", index=False)
    for column in tel.columns:
        if column == "t" or column in S.CUMULATIVE_COUNTERS or not tel[column].notna().any():
            continue
        TELEMETRY_SUMMARY[column] = {"mean": float(tel[column].mean()),
                                     "max": float(tel[column].max())}
    TELEMETRY_SUMMARY["_note"] = (
        "disk and process I/O are reported as *_delta from the first sample of "
        "this run; the raw counters are monotonic since boot.")

RUN_METRICS = {
    "phases_seconds": {k: round(v, 3) for k, v in S.PHASES.items()},
    "cache_stats": S.CACHE_STATS, "telemetry_samples": len(S.TELEMETRY),
    "telemetry_summary": TELEMETRY_SUMMARY, "packages": S.PACKAGE_VERSIONS,
    "batch_profiles": {s: S.batch_profile_summary(s).to_dict("records")
                       for s in ("benchmark", "screening", "prescreen",
                                 "confirmatory", "placebo")},
}

(S.RUN_ROOT / "environment.json").write_text(json.dumps({
    "hardware": S.HARDWARE, "packages": packages, "run_mode": S.CFG.run_mode,
    "dry_run": S.CFG.dry_run, "model_profile": S.CFG.model_profile,
    "model_id": S.CFG.model_id, "model_revision": S.CFG.model_revision,
    "stamp": S.PROFILE["stamp"], "produces_evidence": S.PROFILE["produces_evidence"],
    "selected_references": S.SELECTED_REFERENCES,
    "u_build": S.U_BUILD, "u_val": S.U_VAL, "u_test": S.U_TEST,
    "paraphrases_primary": S.P_FINAL,
    "paraphrases_held_out": list(S.CFG.paraphrase_holdout),
    "protocol_sha256": S.PLAN_SHA256, "execution_sha256": S.EXECUTION_SHA256,
    "run_id": S.RESOLVED_RUN_ID, "run_attempt_id": S.RUN_ATTEMPT_ID,
    "gates": {k: v.status for k, v in S.GATE_STATE.items()},
}, indent=2, default=str), encoding="utf-8")

pd.DataFrame(S.DEPARTURES or [{"stage": "none", "planned": "-",
                             "actual": "no departures recorded", "reason": "-"}]
             ).to_csv(S.RUN_ROOT / "departures.csv", index=False)

for name, obj in [("gate_state", pd.DataFrame([v.as_dict() for v in S.GATE_STATE.values()])),
                  ("primary_effects", S.PRIMARY), ("claim_rule", S.CLAIM),
                  ("secondary_order_average", S.POOLED),
                  ("secondary_stochastic_reference", S.STOCHASTIC),
                  ("order_effects", S.ORDER), ("gee_model", S.GEE_RESULT),
                  ("robustness_grid", S.ROBUSTNESS),
                  ("falsification_individual", S.FALSIFICATION_INDIVIDUAL),
                  ("falsification_panel", S.FALSIFICATION_PANEL),
                  ("condition_failure_rates", S.CONDITION_RATES),
                  ("power_planning", S.POWER_PLANNING),
                  ("pool_dependence_audit", S.POOL_AUDIT),
                  ("protocol_fields", S.PROTOCOL_FIELDS_FRAME)]:
    if obj is not None and len(obj):
        obj.to_csv(S.SCORE_DIR / f"{name}.csv")

with S.phase("archiving"):
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
    _measurement_ok = S.PARAPHRASE_AUDIT_PASSED and S.VERIFIER_GATE_PASSED
    _pre_confirmatory = [k for k in S.GATE_STATE if k != "4_falsification"]
    _pre_gates_ok = all(S.GATE_STATE[k].passed for k in _pre_confirmatory)
    _bypassed = any(v.dry_run_bypassed for v in S.GATE_STATE.values())
    _gate4 = S.GATE_STATE.get("4_falsification")

    CONFIRMATORY_DESIGN_VALID = bool(
        _measurement_ok and _pre_gates_ok and not _bypassed
        and S.PROFILE["produces_evidence"] and not S.CFG.dry_run
        and bool(S.FREEZE.get("frozen")) and S.PLAN_SHA256 == S.FREEZE.get("plan_sha256"))
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
        "profile_produces_evidence": bool(S.PROFILE["produces_evidence"]),
        "frozen": bool(S.FREEZE.get("frozen")),
        "plan_sha256": S.PLAN_SHA256,
        "gate4_excluded_from_design_validity": True,
    }
    S.durable_write(S.GATE_DIR / "export_status.json",
                  json.dumps(EXPORT_STATUS, indent=2, default=str))

    EXPORT_DIR = S.EXPORT_ROOT / ("confirmatory" if CONFIRMATORY_DESIGN_VALID
                                else "provisional")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    _journal = sum(1 for p in S.RESPONSE_DIR.rglob("*") if p.is_file())

    status_lines = [
        EXPORT_LABEL, "",
        f"confirmatory design valid : {CONFIRMATORY_DESIGN_VALID}",
        f"final falsification       : {FINAL_FALSIFICATION_STATUS}",
        f"protocol      : {S.PLAN_SHA256}",
        f"model profile : {S.CFG.model_profile}  ({S.PROFILE['stamp']})",
        f"model         : {S.CFG.model_id} @ {S.CFG.model_revision}",
        f"run id        : {S.RESOLVED_RUN_ID}",
        f"references    : {S.SELECTED_REFERENCES}",
        f"wordings      : primary {S.P_FINAL}, held out {list(S.CFG.paraphrase_holdout)}",
        "", "Gates",
    ] + [f"  {k:20s} : {v.status}"
         + ("  [DRY-RUN BYPASS]" if v.dry_run_bypassed else "")
         for k, v in S.GATE_STATE.items()] + [
        "", "Measurement validity",
        f"  paraphrase audit signed off : {S.PARAPHRASE_AUDIT_PASSED}",
        f"  verifier reliability        : {S.VERIFIER_GATE_PASSED}", "",
        f"Per-batch journal: {_journal} files under responses/, not archived here; "
        "its content is in scores/responses.csv.", "",
    ]
    if not S.PROFILE["produces_evidence"]:
        status_lines.append(
            f"{S.PROFILE['stamp']}: this profile produces no scientific evidence. "
            "Every empirical gate must be rerun from scratch on the study profile.")
    if S.CFG.dry_run:
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
    files = [p for p in S.RUN_ROOT.rglob("*")
             if p.is_file() and p.suffix != ".zip"
             and p.name != "sha256_manifest.json"
             and not _skip_dirs & set(p.relative_to(S.RUN_ROOT).parts)]
    with S.phase("hashing"):
        manifest = {str(p.relative_to(S.RUN_ROOT)): sha_file(p) for p in files}
    manifest_path = EXPORT_DIR / "sha256_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    label = "confirmatory" if CONFIRMATORY_DESIGN_VALID else "provisional"
    archive = EXPORT_DIR / f"outputs_{label}_{S.CFG.model_profile}_{S.CFG.run_mode}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, arcname=p.relative_to(S.RUN_ROOT))
        zf.write(manifest_path, arcname="sha256_manifest.json")
        zf.write(EXPORT_DIR / "STATUS.txt", arcname="STATUS.txt")

PHASE_COVERAGE = {
    "timed": sorted(S.PHASES),
    "declared_but_untimed": sorted(set(S.PHASE_NAMES) - set(S.PHASES)),
    "timed_but_undeclared": sorted(n for n in S.PHASES if n not in S.PHASE_NAMES
                                   and not n.startswith("generate_")),
}
RUN_METRICS["phase_coverage"] = PHASE_COVERAGE
(S.RUN_ROOT / "run_metrics.json").write_text(
    json.dumps(RUN_METRICS, indent=2, default=str), encoding="utf-8")
display(pd.Series(S.PHASES).sort_values(ascending=False).round(2).to_frame("seconds"))
if PHASE_COVERAGE["declared_but_untimed"]:
    print("phases declared but not timed this run (skipped cells): "
          f"{PHASE_COVERAGE['declared_but_untimed']}")

print("archive :", archive)
print("entries :", len(manifest), f"(+ {_journal} journal files under responses/)")
print("status  :", label.upper())
print("durable :", S.RUN_ROOT)
print("departures recorded:", len(S.DEPARTURES))
S.checkpoint("export", {"status": label, "archive": str(archive)})
