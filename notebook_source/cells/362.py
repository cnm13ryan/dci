target_rows = confirmatory_scores.query(
    "constraint_id == @CFG.target_id and is_measured").copy()
if target_rows["plan_deviation"].any():
    raise RuntimeError(
        f"{int(target_rows['plan_deviation'].sum())} confirmatory rows were "
        "generated outside the frozen batch plan. They belong to a different "
        "randomisation condition and cannot enter the primary estimator.")

CONF_TABLE = task_cell_table(target_rows, "fail")
_required = ["A_ONLY"] + [f"{c}|{o}" for c in [CFG.focal_id, *SELECTED_REFERENCES]
                          for o in CFG.orders]
_have = {c for c, _ in CONF_TABLE.columns}
_missing = sorted(set(_required) - _have)
if _missing:
    raise ValueError(f"Missing confirmatory conditions: {_missing}")
print(f"task clusters: {len(CONF_TABLE)}  conditions: {len(_have)}  "
      f"blocks per contrast: {len(CONFIRMATORY_TASKS) * len(P_FINAL) * len(CFG.confirmatory_seeds)}")

_w = {c: float(WEIGHTS[c]) for c in SELECTED_REFERENCES}


def confirmatory_fn(means: pd.Series) -> dict[str, float]:
    """Every estimand from one resample, so their joint covariance survives."""
    A = CFG.target_id

    def mu(condition: str) -> float:
        return cell_mean(means, condition, A)

    out: dict[str, float] = {}
    for o in CFG.orders:
        focal = mu(f"{CFG.focal_id}|{o}")
        for j in SELECTED_REFERENCES:
            out[f"tau|{j}|{o}"] = focal - mu(f"{j}|{o}")
        out[f"tau_stoch|{o}"] = focal - sum(
            _w[j] * mu(f"{j}|{o}") for j in SELECTED_REFERENCES)
        out[f"mu_focal|{o}"] = focal
    for j in SELECTED_REFERENCES:
        out[f"tau_pooled|{j}"] = float(np.mean(
            [out[f"tau|{j}|{o}"] for o in CFG.orders]))
    out["tau_stoch_pooled"] = float(np.mean(
        [out[f"tau_stoch|{o}"] for o in CFG.orders]))
    for c in [CFG.focal_id, *SELECTED_REFERENCES]:
        out[f"order_effect|{c}"] = mu(f"{c}|{CFG.orders[0]}") - mu(f"{c}|{CFG.orders[1]}")
    out["mu_A_only"] = mu("A_ONLY")
    return out


with phase("bootstrap"):
    POINT, DRAWS = bootstrap_functional(
        CONF_TABLE, confirmatory_fn, CFG.bootstrap_reps, CFG.base_seed + 4242)
np.save(SCORE_DIR / "bootstrap_draws.npy", DRAWS.to_numpy())

with phase("analysis"):
    TAU_COLS = [f"tau|{j}|{o}" for o in CFG.orders for j in SELECTED_REFERENCES]
    SIM = simultaneous_bounds(POINT[TAU_COLS], DRAWS[TAU_COLS], CFG.confidence_level)
    MARGINAL = percentile_ci(DRAWS[TAU_COLS], CFG.confidence_level)
    PVALUES = bootstrap_p(POINT[TAU_COLS], DRAWS[TAU_COLS], CFG.bootstrap_reps)

    PRIMARY = SIM.join(MARGINAL)
    PRIMARY["reference"] = [c.split("|")[1] for c in PRIMARY.index]
    PRIMARY["order"] = [c.split("|")[2] for c in PRIMARY.index]
    PRIMARY["p_bootstrap"] = PVALUES
    PRIMARY["p_holm"] = holm(list(PRIMARY["p_bootstrap"]))
    PRIMARY["equivalent_to_zero"] = [
        within_sesoi(r["ci_lower"], r["ci_upper"], CFG.sesoi_risk_difference)
        for _, r in PRIMARY.iterrows()]
    PRIMARY["excludes_zero_simultaneously"] = (
        (PRIMARY["sim_lower"] > 0) | (PRIMARY["sim_upper"] < 0))

PRIMARY = PRIMARY[["reference", "order", "estimate", "se", "ci_lower", "ci_upper",
                   "sim_lower", "sim_upper", "p_bootstrap", "p_holm",
                   "equivalent_to_zero", "excludes_zero_simultaneously"]]
PRIMARY.to_csv(SCORE_DIR / "primary_effects.csv")
display(PRIMARY.round(4))

TAU_MATRIX = PRIMARY.pivot(index="reference", columns="order", values="estimate")
TAU_MATRIX = TAU_MATRIX.reindex(SELECTED_REFERENCES)[list(CFG.orders)]
TAU_MATRIX.to_csv(SCORE_DIR / "tau_matrix.csv")
print("\nPrimary result: tau_{j,o}")
display(TAU_MATRIX.round(3))
print(f"simultaneous max-T critical value: {SIM.attrs['critical_value']:.3f} "
      f"(a per-contrast normal interval would use "
      f"{stats.norm.ppf(1 - (1 - CFG.confidence_level) / 2):.3f})")

# ------------------------------------------- the reference-robust claim rule
_claim_rows = []
for o in CFG.orders:
    sub = PRIMARY.query("order == @o")
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
CLAIM = pd.DataFrame(_claim_rows).set_index("order")
CLAIM["reference_robust_claim_supported"] = (
    CLAIM["robust_positive"] | CLAIM["robust_negative"])
CLAIM.to_csv(SCORE_DIR / "claim_rule.csv")
display(CLAIM.round(4))

for o in CFG.orders:
    row = CLAIM.loc[o]
    if row["reference_robust_claim_supported"]:
        direction = "raises" if row["robust_positive"] else "lowers"
        print(f"[{o}] Reference-robust claim SUPPORTED: adding {CFG.focal_id} {direction} "
              f"failure on {CFG.target_id} relative to every one of the "
              f"{CFG.reference_count} admitted references simultaneously.")
    else:
        print(f"[{o}] Reference-robust claim NOT supported. The least favourable "
              f"admitted reference is {row['least_favourable_reference']} at "
              f"tau = {row['tau_min']:+.3f}, simultaneous lower bound "
              f"{row['simultaneous_lower_bound_on_min']:+.3f}. Report this as "
              "reference-dependent heterogeneity, not as interference.")
