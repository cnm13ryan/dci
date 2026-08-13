"""Stage 362 — migrated from notebook cell 362.py (confirmatory_analysis).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/362.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import bootstrap_functional, bootstrap_p, holm, percentile_ci, simultaneous_bounds, within_sesoi  # noqa: F401
from dci.analysis.claim import REQUIRED_FINITE, claim_blockers, reference_robust_claim  # noqa: F401
from dci.analysis.completeness import assert_primary_table_complete  # noqa: F401
from dci.analysis.output_budget import arm_gap, cap_verdict, termination_coverage, termination_report  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401
CFG = getattr(S, 'CFG', None)  # pandas @-resolution alias (read-only)

target_rows = S.confirmatory_scores.query(
    "constraint_id == @CFG.target_id and is_measured").copy()
if target_rows["plan_deviation"].any():
    raise RuntimeError(
        f"{int(target_rows['plan_deviation'].sum())} confirmatory rows were "
        "generated outside the frozen batch plan. They belong to a different "
        "randomisation condition and cannot enter the primary estimator.")

CONF_TABLE = S.task_cell_table(target_rows, "fail")
_required = ["A_ONLY"] + [f"{c}|{o}" for c in [S.CFG.focal_id, *S.SELECTED_REFERENCES]
                          for o in S.CFG.orders]
_have = {c for c, _ in CONF_TABLE.columns}
_missing = sorted(set(_required) - _have)
if _missing:
    raise ValueError(f"Missing confirmatory conditions: {_missing}")

# Condition presence (above) is necessary but not sufficient: the CELLS must be
# populated too, or bootstrap_functional's np.nanmean would average the focal and
# reference arms over different task subsets and call the difference a contrast.
S.CONF_SUPPORT = assert_primary_table_complete(
    CONF_TABLE,
    required_columns=[(c, S.CFG.target_id) for c in _required],
    label="confirmatory")
S.CONF_SUPPORT.to_csv(S.SCORE_DIR / "primary_table_support.csv")

# ------------------------------------------------- the output-budget artefact
# Required response length differs sharply across the panel: B is satisfiable in
# about ten words, while a 15-word-per-sentence reference needs at least sixty,
# against a 180-TOKEN ceiling that belongs to the apparatus rather than the
# science. Truncation is post-treatment, so it is measured and reported and may
# block interpretation -- it never edits an outcome and never filters a row.
_cap_rows = S.confirmatory_scores.query("is_measured").copy()
S.OUTPUT_CAP_COVERAGE = termination_coverage(_cap_rows)
S.OUTPUT_CAP_BY_ARM = termination_report(
    _cap_rows, ["added_constraint", "order", "paraphrase_id"])
S.OUTPUT_CAP_BY_CONSTRAINT = termination_report(_cap_rows, ["added_constraint"])
S.OUTPUT_CAP_GAPS = arm_gap(
    termination_report(_cap_rows, ["added_constraint", "order"]),
    "added_constraint", S.CFG.focal_id, S.SELECTED_REFERENCES)
for _name, _frame in (("output_cap_by_arm", S.OUTPUT_CAP_BY_ARM),
                      ("output_cap_by_constraint", S.OUTPUT_CAP_BY_CONSTRAINT),
                      ("output_cap_arm_gaps", S.OUTPUT_CAP_GAPS)):
    if len(_frame):
        _frame.to_csv(S.SCORE_DIR / f"{_name}.csv", index=False)

S.OUTPUT_CAP_VERDICT = cap_verdict(
    S.OUTPUT_CAP_BY_ARM, S.OUTPUT_CAP_GAPS,
    warn_share=S.CFG.output_truncation_warn_share,
    stop_share=S.CFG.output_truncation_stop_share,
    max_arm_gap=S.CFG.output_truncation_max_arm_gap,
    coverage=S.OUTPUT_CAP_COVERAGE,
    min_coverage=S.CFG.output_termination_min_coverage)

print(f"\noutput budget: cap {S.CFG.max_new_tokens} new tokens | "
      f"metadata coverage {S.OUTPUT_CAP_COVERAGE['coverage']:.3f} | "
      f"{S.OUTPUT_CAP_VERDICT['n_cells']} reported cells | worst truncated share "
      f"{S.OUTPUT_CAP_VERDICT['worst_truncated_share']:.3f} | worst focal-vs-reference "
      f"gap {S.OUTPUT_CAP_VERDICT['worst_abs_arm_gap']:.3f}")
if len(S.OUTPUT_CAP_BY_CONSTRAINT):
    display(S.OUTPUT_CAP_BY_CONSTRAINT.round(3))
for _w in S.OUTPUT_CAP_VERDICT["warnings"]:
    print(f"  output-budget WARNING: {_w}")

if not S.OUTPUT_CAP_VERDICT["ok"]:
    S.stop("5_output_budget", GateStatus.OUTPUT_CAP_DOMINATES,
           "the declared output cap is plausibly dominating measured compliance",
           quantities={k: S.OUTPUT_CAP_VERDICT[k] for k in
                       ("reasons", "coverage", "worst_truncated_share",
                        "worst_abs_arm_gap", "n_cells")},
           thresholds=S.OUTPUT_CAP_VERDICT["thresholds"],
           more_data_could_resolve=False, new_protocol_version_required=True,
           message="OUTPUT CAP DOMINATES:\n  "
                   + "\n  ".join(S.OUTPUT_CAP_VERDICT["reasons"])
                   + "\n\nTruncated rows are NOT dropped and tau is NOT "
                     "conditioned on clean termination: that would condition on "
                     "a post-treatment outcome. Raise max_new_tokens under a new "
                     "protocol identity, or preregister a high-cap sensitivity "
                     "condition, and regenerate.")
print(f"task clusters: {len(CONF_TABLE)}  conditions: {len(_have)}  "
      f"blocks per contrast: {len(S.CONFIRMATORY_TASKS) * len(S.P_FINAL) * len(S.CFG.confirmatory_seeds)}")

_w = {c: float(S.WEIGHTS[c]) for c in S.SELECTED_REFERENCES}


def confirmatory_fn(means: pd.Series) -> dict[str, float]:
    """Every estimand from one resample, so their joint covariance survives."""
    A = S.CFG.target_id

    def mu(condition: str) -> float:
        return S.cell_mean(means, condition, A)

    out: dict[str, float] = {}
    for o in S.CFG.orders:
        focal = mu(f"{S.CFG.focal_id}|{o}")
        for j in S.SELECTED_REFERENCES:
            out[f"tau|{j}|{o}"] = focal - mu(f"{j}|{o}")
        out[f"tau_stoch|{o}"] = focal - sum(
            _w[j] * mu(f"{j}|{o}") for j in S.SELECTED_REFERENCES)
        out[f"mu_focal|{o}"] = focal
    for j in S.SELECTED_REFERENCES:
        out[f"tau_pooled|{j}"] = float(np.mean(
            [out[f"tau|{j}|{o}"] for o in S.CFG.orders]))
    out["tau_stoch_pooled"] = float(np.mean(
        [out[f"tau_stoch|{o}"] for o in S.CFG.orders]))
    for c in [S.CFG.focal_id, *S.SELECTED_REFERENCES]:
        out[f"order_effect|{c}"] = mu(f"{c}|{S.CFG.orders[0]}") - mu(f"{c}|{S.CFG.orders[1]}")
    out["mu_A_only"] = mu("A_ONLY")
    return out


with S.phase("bootstrap"):
    S.POINT, S.DRAWS = bootstrap_functional(
        CONF_TABLE, confirmatory_fn, S.CFG.bootstrap_reps, S.CFG.base_seed + 4242)
np.save(S.SCORE_DIR / "bootstrap_draws.npy", S.DRAWS.to_numpy())

with S.phase("analysis"):
    TAU_COLS = [f"tau|{j}|{o}" for o in S.CFG.orders for j in S.SELECTED_REFERENCES]
    SIM = simultaneous_bounds(S.POINT[TAU_COLS], S.DRAWS[TAU_COLS], S.CFG.confidence_level)
    MARGINAL = percentile_ci(S.DRAWS[TAU_COLS], S.CFG.confidence_level)
    PVALUES = bootstrap_p(S.POINT[TAU_COLS], S.DRAWS[TAU_COLS], S.CFG.bootstrap_reps)

    S.PRIMARY = SIM.join(MARGINAL)
    S.PRIMARY["reference"] = [c.split("|")[1] for c in S.PRIMARY.index]
    S.PRIMARY["order"] = [c.split("|")[2] for c in S.PRIMARY.index]
    S.PRIMARY["p_bootstrap"] = PVALUES
    S.PRIMARY["p_holm"] = holm(list(S.PRIMARY["p_bootstrap"]))
    S.PRIMARY["equivalent_to_zero"] = [
        within_sesoi(r["ci_lower"], r["ci_upper"], S.CFG.sesoi_risk_difference)
        for _, r in S.PRIMARY.iterrows()]
    S.PRIMARY["excludes_zero_simultaneously"] = (
        (S.PRIMARY["sim_lower"] > 0) | (S.PRIMARY["sim_upper"] < 0))

S.PRIMARY = S.PRIMARY[["reference", "order", "estimate", "se", "ci_lower", "ci_upper",
                   "sim_lower", "sim_upper", "p_bootstrap", "p_holm",
                   "equivalent_to_zero", "excludes_zero_simultaneously"]]
S.PRIMARY.to_csv(S.SCORE_DIR / "primary_effects.csv")
display(S.PRIMARY.round(4))

TAU_MATRIX = S.PRIMARY.pivot(index="reference", columns="order", values="estimate")
TAU_MATRIX = TAU_MATRIX.reindex(S.SELECTED_REFERENCES)[list(S.CFG.orders)]
TAU_MATRIX.to_csv(S.SCORE_DIR / "tau_matrix.csv")
print("\nPrimary result: tau_{j,o}")
display(TAU_MATRIX.round(3))
print(f"simultaneous max-T critical value: {SIM.attrs['critical_value']:.3f} "
      f"(a per-contrast normal interval would use "
      f"{stats.norm.ppf(1 - (1 - S.CFG.confidence_level) / 2):.3f})")

# ------------------------------------------- the reference-robust claim rule
# Delegated to dci.analysis.claim, which fails closed: a degenerate or non-finite
# contrast makes the order INCONCLUSIVE_PRECISION instead of dropping a reference
# out of the intersection. See that module's docstring for the defect this
# replaces. The claim is evaluated over the SELECTED references and BOTH orders,
# and the table records how many references actually entered inference.
S.CLAIM = reference_robust_claim(S.PRIMARY, S.SELECTED_REFERENCES, S.CFG.orders,
                                 sim_attrs=dict(SIM.attrs))
S.CLAIM.to_csv(S.SCORE_DIR / "claim_rule.csv")
display(S.CLAIM.round(4))

S.CLAIM_BLOCKERS = claim_blockers(S.CLAIM)
for o in S.CFG.orders:
    row = S.CLAIM.loc[o]
    n_used = int(row["n_references_in_inference"])
    if row["inference_status"] != GateStatus.PASS:
        print(f"[{o}] Reference-robust claim INCONCLUSIVE ({row['inference_status']}): "
              f"only {n_used} of {int(row['n_references_declared'])} declared "
              f"references produced usable simultaneous inference. "
              f"Degenerate: {row['degenerate_references'] or 'none'}. "
              f"{row['family_problems']}\n"
              "     No directional claim is made. The remedy is precision, not "
              "omission: a contrast with zero resampling variance is an "
              "unanswered hypothesis, not an absent one.")
    elif row["reference_robust_claim_supported"]:
        direction = "raises" if row["robust_positive"] else "lowers"
        print(f"[{o}] Reference-robust claim SUPPORTED: adding {S.CFG.focal_id} {direction} "
              f"failure on {S.CFG.target_id} relative to every one of the "
              f"{n_used} admitted references simultaneously.")
    else:
        print(f"[{o}] Reference-robust claim NOT supported. The least favourable "
              f"admitted reference is {row['least_favourable_reference']} at "
              f"tau = {row['tau_min']:+.3f}, simultaneous lower bound "
              f"{row['simultaneous_lower_bound_on_min']:+.3f}. Report this as "
              "reference-dependent heterogeneity, not as interference.")

# The claim rule is a scientific gate, not a print statement. An order whose
# inference is degenerate may not be interpreted, and dev-run bypass is the only
# path that continues past it.
if S.CLAIM_BLOCKERS:
    S.stop("5_primary_inference", GateStatus.INCONCLUSIVE_PRECISION,
           "the primary max-T family is incomplete or degenerate, so the "
           "reference-robust claim cannot be evaluated",
           quantities={"blockers": S.CLAIM_BLOCKERS,
                       "n_family_requested": SIM.attrs["n_family_requested"],
                       "n_family_calibrated": SIM.attrs["n_family_calibrated"],
                       "degenerate_contrasts": SIM.attrs["degenerate"]},
           thresholds={"required_contrasts": len(S.SELECTED_REFERENCES) * len(S.CFG.orders),
                       "required_finite": list(REQUIRED_FINITE)},
           more_data_could_resolve=True, new_protocol_version_required=False,
           message="PRIMARY INFERENCE INCONCLUSIVE:\n  " + "\n  ".join(S.CLAIM_BLOCKERS))
