require_gate("0_implementation", "M_measurement", "1_u_bank", "2_feasibility",
             "3_validation", "3b_wording")
assert (GATE_DIR / "reference_validation.json").exists(), (
    "reference_validation.json is absent. Confirmatory generation is authorised "
    "by Gate 3 and Gate 3b and by nothing else.")

confirmatory_design = build_confirmatory_design(SELECTED_REFERENCES, P_FINAL)
confirmatory_design.to_csv(DESIGN_DIR / "confirmatory_design.csv", index=False)
print("confirmatory rows:", len(confirmatory_design),
      "| conditions:", confirmatory_design["condition_id"].nunique(),
      "| clusters:", confirmatory_design["task_id"].nunique())

confirmatory_responses = run_generation_stage(confirmatory_design, "confirmatory")
display(report_batch_composition(confirmatory_responses, "confirmatory"))
_err = 1.0 - confirmatory_responses["generation_ok"].mean()
print("confirmatory generation-error rate:", round(_err, 4))
if _err > 0.10:
    raise RuntimeError("More than 10% of confirmatory generations failed.")
if not CFG.dry_run and confirmatory_responses["is_synthetic"].any():
    raise AssertionError("Synthetic rows in an empirical run.")
confirmatory_scores = score_responses(confirmatory_responses)

placebo_scores = pd.DataFrame()
placebo_responses = pd.DataFrame()
if CFG.run_placebo:
    placebo_design = build_placebo_design(SELECTED_REFERENCES, U_TEST, P_FINAL)
    placebo_design.to_csv(DESIGN_DIR / "placebo_design.csv", index=False)
    placebo_responses = run_generation_stage(placebo_design, "placebo")
    placebo_scores = score_responses(placebo_responses)

if not CFG.dry_run:
    free_model()
display(batch_profile_summary("confirmatory").round(3))

all_scores = pd.concat(
    [calibration_scores, confirmatory_scores]
    + ([placebo_scores] if len(placebo_scores) else []), ignore_index=True)
ALL_RESPONSES = pd.concat(
    [confirmatory_responses] + ([placebo_responses] if len(placebo_responses) else []),
    ignore_index=True)
all_scores.to_csv(SCORE_DIR / "scores.csv", index=False)
ALL_RESPONSES.to_csv(SCORE_DIR / "responses.csv", index=False)
display(all_scores.groupby(["stage", "status"]).size().unstack(fill_value=0))

CONDITION_RATES = (confirmatory_scores.query("is_measured")
                   .groupby(["condition_id", "added_constraint", "order"])
                   .agg(n=("fail", "size"), fail_rate=("fail", "mean"),
                        unscorable=("status", lambda s: float((s == "unscorable").mean())),
                        mean_words=("response_words", "mean"))
                   .reset_index().sort_values(["added_constraint", "order"]))
CONDITION_RATES.to_csv(SCORE_DIR / "condition_failure_rates.csv", index=False)
display(CONDITION_RATES.round(4))
checkpoint("confirmatory", {"rows": len(confirmatory_design)})
