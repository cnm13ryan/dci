"""Stage 352 — migrated from notebook cell 352.py (confirmatory_generation).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/352.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell


S.require_gate("0_implementation", "M_measurement", "1_u_bank", "2_feasibility",
             "3_validation", "3b_wording")
assert (S.GATE_DIR / "reference_validation.json").exists(), (
    "reference_validation.json is absent. Confirmatory generation is authorised "
    "by Gate 3 and Gate 3b and by nothing else.")

confirmatory_design = S.build_confirmatory_design(S.SELECTED_REFERENCES, S.P_FINAL)
confirmatory_design.to_csv(S.DESIGN_DIR / "confirmatory_design.csv", index=False)
print("confirmatory rows:", len(confirmatory_design),
      "| conditions:", confirmatory_design["condition_id"].nunique(),
      "| clusters:", confirmatory_design["task_id"].nunique())

confirmatory_responses = S.run_generation_stage(confirmatory_design, "confirmatory")
display(S.report_batch_composition(confirmatory_responses, "confirmatory"))
_err = 1.0 - confirmatory_responses["generation_ok"].mean()
print("confirmatory generation-error rate:", round(_err, 4))
if _err > 0.10:
    raise RuntimeError("More than 10% of confirmatory generations failed.")
if not S.CFG.dry_run and confirmatory_responses["is_synthetic"].any():
    raise AssertionError("Synthetic rows in an empirical run.")
S.confirmatory_scores = S.score_responses(confirmatory_responses)

S.placebo_scores = pd.DataFrame()
placebo_responses = pd.DataFrame()
if S.CFG.run_placebo:
    placebo_design = S.build_placebo_design(S.SELECTED_REFERENCES, S.U_TEST, S.P_FINAL)
    placebo_design.to_csv(S.DESIGN_DIR / "placebo_design.csv", index=False)
    placebo_responses = S.run_generation_stage(placebo_design, "placebo")
    S.placebo_scores = S.score_responses(placebo_responses)

if not S.CFG.dry_run:
    S.free_model()
display(S.batch_profile_summary("confirmatory").round(3))

all_scores = pd.concat(
    [S.calibration_scores, S.confirmatory_scores]
    + ([S.placebo_scores] if len(S.placebo_scores) else []), ignore_index=True)
ALL_RESPONSES = pd.concat(
    [confirmatory_responses] + ([placebo_responses] if len(placebo_responses) else []),
    ignore_index=True)
all_scores.to_csv(S.SCORE_DIR / "scores.csv", index=False)
ALL_RESPONSES.to_csv(S.SCORE_DIR / "responses.csv", index=False)
display(all_scores.groupby(["stage", "status"]).size().unstack(fill_value=0))

S.CONDITION_RATES = (S.confirmatory_scores.query("is_measured")
                   .groupby(["condition_id", "added_constraint", "order"])
                   .agg(n=("fail", "size"), fail_rate=("fail", "mean"),
                        unscorable=("status", lambda s: float((s == "unscorable").mean())),
                        mean_words=("response_words", "mean"))
                   .reset_index().sort_values(["added_constraint", "order"]))
S.CONDITION_RATES.to_csv(S.SCORE_DIR / "condition_failure_rates.csv", index=False)
display(S.CONDITION_RATES.round(4))
S.checkpoint("confirmatory", {"rows": len(confirmatory_design)})
