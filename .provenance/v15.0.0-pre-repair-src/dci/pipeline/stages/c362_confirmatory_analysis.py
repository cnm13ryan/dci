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
_claim_rows = []
for o in S.CFG.orders:
    sub = S.PRIMARY.query("order == @o")
    least = sub["estimate"].idxmin()
    _claim_rows.append({
        "order": o,
        "tau_min": float(sub["estimate"].min()),
        "least_favourable_reference": str(sub.loc[least, "reference"]),
        "simultaneous_lower_bound_on_min": float(sub["sim_lower"].min()),
        "simultaneous_upper_bound_on_max": float(sub["sim_upper"].max()),
        "all_same_sign": bool(np.sign(sub["estimate"]).nunique() == 1),
        "robust_positive": bool(sub["sim_lower"].min() > 0),
        "robust_negative": bool(sub["sim_upper"].max() < 0),
    })
S.CLAIM = pd.DataFrame(_claim_rows).set_index("order")
S.CLAIM["reference_robust_claim_supported"] = (
    S.CLAIM["robust_positive"] | S.CLAIM["robust_negative"])
S.CLAIM.to_csv(S.SCORE_DIR / "claim_rule.csv")
display(S.CLAIM.round(4))

for o in S.CFG.orders:
    row = S.CLAIM.loc[o]
    if row["reference_robust_claim_supported"]:
        direction = "raises" if row["robust_positive"] else "lowers"
        print(f"[{o}] Reference-robust claim SUPPORTED: adding {S.CFG.focal_id} {direction} "
              f"failure on {S.CFG.target_id} relative to every one of the "
              f"{S.CFG.reference_count} admitted references simultaneously.")
    else:
        print(f"[{o}] Reference-robust claim NOT supported. The least favourable "
              f"admitted reference is {row['least_favourable_reference']} at "
              f"tau = {row['tau_min']:+.3f}, simultaneous lower bound "
              f"{row['simultaneous_lower_bound_on_min']:+.3f}. Report this as "
              "reference-dependent heterogeneity, not as interference.")
