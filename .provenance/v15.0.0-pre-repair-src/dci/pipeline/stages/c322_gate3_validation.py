"""Stage 322 — migrated from notebook cell 322.py (gate3_validation).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/322.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import bootstrap_functional, paired_advantage, simultaneous_abs_upper  # noqa: F401
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

VAL_COMPONENTS = S.burden_components(S.U_VAL)

with S.phase("gate3_validation"):
    _val_fn = S.make_signature_fn(S.U_VAL_MEASURED_IDS, S.U_VAL, S.P_FINAL, S.COUPLING)
    VAL_POINT, VAL_DRAWS = bootstrap_functional(
        S.CAL_TABLE_VAL, _val_fn, S.SIG_REPS, S.CFG.base_seed + 303)
    VAL_SIG = S.signature_frame(VAL_POINT, S.U_VAL_MEASURED_IDS, S.U_VAL)
    VAL_SIG.to_csv(S.SCORE_DIR / "u_val_burden.csv")


def _matrix(keys: list[str]) -> np.ndarray:
    return VAL_DRAWS[keys].to_numpy(dtype=float)


def architecture_errors(donor_map: dict[str, list[str]],
                        weight_map: Optional[dict[str, pd.Series]] = None
                        ) -> dict[str, Any]:
    """Held-out prediction error for every pseudo-focal, with bootstrap draws.

    Errors are a linear function of the signature draws, so the uncertainty is
    already joint and no second resample is needed.
    """
    point_errors, draw_blocks = [], []
    for q, donors in donor_map.items():
        if not donors:
            continue
        w = (np.array([float(weight_map[q][d]) for d in donors])
             if weight_map else np.full(len(donors), 1.0 / len(donors)))
        for comp in VAL_COMPONENTS:
            qk = S.signature_key(q, comp)
            dk = [S.signature_key(d, comp) for d in donors]
            if qk not in VAL_POINT.index or any(k not in VAL_POINT.index for k in dk):
                continue
            point_errors.append(float(np.dot(w, VAL_POINT[dk].to_numpy()) - VAL_POINT[qk]))
            draw_blocks.append(_matrix(dk) @ w - VAL_DRAWS[qk].to_numpy())
    if not point_errors:
        return {"n_errors": 0}
    errors = np.abs(np.asarray(point_errors))
    stacked = np.abs(np.column_stack(draw_blocks))
    return {"n_errors": len(point_errors), "n_pseudo_focal": len(donor_map),
            "mae": float(errors.mean()),
            "q90": float(np.quantile(errors, 0.90)),
            "bias": float(np.mean(point_errors)),
            "mae_draws": pd.Series(stacked.mean(axis=1)),
            "q90_draws": pd.Series(np.quantile(stacked, 0.90, axis=1))}


# ---------------------------------------------------------- the architectures
G1_DONORS = {q: S.donors_for(q, S.PSEUDO_UNIVERSE) for q in S.PSEUDO_COHORT}
G1_DONORS = {q: d for q, d in G1_DONORS.items() if d}
G0_DONORS = {q: [c for c in S.PSEUDO_UNIVERSE if c != q] for q in S.PSEUDO_COHORT}
G2_WEIGHTS = {}
for _q, _d in G1_DONORS.items():
    _dist = S.regularised_mahalanobis(S.SIGNATURE, _q, _d, S.CFG.mahalanobis_ridge)
    G2_WEIGHTS[_q] = S.fit_stochastic_weights(S.SIGNATURE, _d, _q, list(S.CALIPERS.index), _dist)

S.G0 = architecture_errors(G0_DONORS)
S.G1 = architecture_errors(G1_DONORS)
S.G2 = architecture_errors(G1_DONORS, G2_WEIGHTS)

# ------------------------------------------- random equal-sized eligible sets
_rng = np.random.default_rng(S.CFG.base_seed + 404)
_per_focal = max(1, S.CFG.ref_val_random_draws // max(len(G1_DONORS), 1))
RANDOM_SETS = {}
for _q in G1_DONORS:
    _pool = [c for c in S.PSEUDO_UNIVERSE if c != _q]
    RANDOM_SETS[_q] = [sorted(_rng.choice(_pool, size=min(S.CFG.reference_count, len(_pool)),
                                          replace=False).tolist())
                       for _ in range(_per_focal)] if len(_pool) >= S.CFG.reference_count else []
_random_points, _random_draw_sets = [], []
for _i in range(_per_focal):
    _dm = {q: sets[_i] for q, sets in RANDOM_SETS.items() if sets}
    if not _dm:
        continue
    _r = architecture_errors(_dm)
    if _r.get("n_errors"):
        _random_points.append(_r["mae"])
        _random_draw_sets.append(_r["mae_draws"].to_numpy())
S.RANDOM_MAE_DISTRIBUTION = pd.Series(_random_points, name="random_set_mae")
RANDOM_MAE_DRAWS = (pd.Series(np.mean(np.column_stack(_random_draw_sets), axis=1))
                    if _random_draw_sets else pd.Series(dtype=float))

ARCHITECTURES = pd.DataFrame([
    {"architecture": "g0_broad_eligible", "role": "benchmark only",
     "mae": S.G0.get("mae"), "q90": S.G0.get("q90"), "n_pseudo_focal": S.G0.get("n_pseudo_focal")},
    {"architecture": "g1_calipered_panel", "role": "PRIMARY, must pass alone",
     "mae": S.G1.get("mae"), "q90": S.G1.get("q90"), "n_pseudo_focal": S.G1.get("n_pseudo_focal")},
    {"architecture": "g2_synthetic_weighted", "role": "secondary, validated separately",
     "mae": S.G2.get("mae"), "q90": S.G2.get("q90"), "n_pseudo_focal": S.G2.get("n_pseudo_focal")},
    {"architecture": "random_eligible_sets", "role": "falsification comparator",
     "mae": float(S.RANDOM_MAE_DISTRIBUTION.mean()) if len(S.RANDOM_MAE_DISTRIBUTION) else np.nan,
     "q90": float(S.RANDOM_MAE_DISTRIBUTION.quantile(0.90)) if len(S.RANDOM_MAE_DISTRIBUTION) else np.nan,
     "n_pseudo_focal": len(RANDOM_SETS)},
])
ARCHITECTURES.to_csv(S.GATE_DIR / "architecture_comparison.csv", index=False)
display(ARCHITECTURES.round(4))
if len(S.RANDOM_MAE_DISTRIBUTION):
    S.RANDOM_MAE_DISTRIBUTION.to_csv(S.GATE_DIR / "random_reference_distribution.csv")
    display(S.RANDOM_MAE_DISTRIBUTION.describe().round(4).to_frame())

# ------------------------------------ per-reference validation for B (primary)
IND_POINT, IND_DRAWS = S.discrepancy_frames(VAL_POINT, VAL_DRAWS, S.CFG.focal_id,
                                          S.SELECTED_REFERENCES, VAL_COMPONENTS)
S.IND_BOUNDS = simultaneous_abs_upper(IND_POINT, IND_DRAWS, S.CFG.ref_val_confidence)
S.IND_BOUNDS["reference"] = [k.split("|")[0] for k in S.IND_BOUNDS.index]
S.IND_BOUNDS["within_tolerance"] = S.IND_BOUNDS["abs_upper"] <= S.CFG.ref_val_individual_max
S.IND_BOUNDS.to_csv(S.GATE_DIR / "individual_reference_validation.csv")
display(S.IND_BOUNDS.round(4))
_worst_ref = (S.IND_BOUNDS.groupby("reference")["abs_upper"].max()
              .sort_values(ascending=False))
display(_worst_ref.round(4).to_frame("worst_simultaneous_bound"))

PANEL_POINT, PANEL_DRAWS = S.panel_residual_frames(
    VAL_POINT, VAL_DRAWS, S.CFG.focal_id, S.SELECTED_REFERENCES, VAL_COMPONENTS)
S.PANEL_BOUNDS = simultaneous_abs_upper(PANEL_POINT, PANEL_DRAWS, S.CFG.ref_val_confidence)
S.PANEL_BOUNDS.to_csv(S.GATE_DIR / "panel_residual_validation.csv")

# --------------------------------------------- leave-one-reference-out stability
_loo = []
for j in S.SELECTED_REFERENCES:
    reduced = [c for c in S.SELECTED_REFERENCES if c != j]
    p_full, d_full = S.panel_residual_frames(VAL_POINT, VAL_DRAWS, S.CFG.focal_id,
                                           S.SELECTED_REFERENCES, VAL_COMPONENTS)
    p_red, d_red = S.panel_residual_frames(VAL_POINT, VAL_DRAWS, S.CFG.focal_id,
                                         reduced, VAL_COMPONENTS)
    shift_point = (p_red - p_full).abs()
    shift_draws = (d_red - d_full)
    bounds = simultaneous_abs_upper(p_red - p_full, shift_draws, S.CFG.ref_val_confidence)
    _loo.append({"dropped": j, "max_shift": float(shift_point.max()),
                 "max_shift_upper": float(bounds["abs_upper"].max())})
LOO = pd.DataFrame(_loo).set_index("dropped")
LOO["within_tolerance"] = LOO["max_shift_upper"] <= S.CFG.ref_val_loo_max
display(LOO.round(4))


def evaluate_architecture(name: str, result: dict[str, Any]) -> pd.DataFrame:
    """Every criterion on a bound. p > .05 is never validation."""
    if not result.get("n_errors"):
        return pd.DataFrame([{"criterion": "evaluable", "value": 0.0,
                              "threshold": 1.0, "passed": False}])
    mae_upper = float(result["mae_draws"].quantile(S.CFG.ref_val_confidence))
    q90_upper = float(result["q90_draws"].quantile(S.CFG.ref_val_confidence))
    rows = [
        {"criterion": "MAE upper bound on U_val", "value": mae_upper,
         "threshold": S.CFG.ref_val_mae_max, "passed": mae_upper <= S.CFG.ref_val_mae_max},
        {"criterion": "90th percentile |error| upper bound", "value": q90_upper,
         "threshold": S.CFG.ref_val_q90_max, "passed": q90_upper <= S.CFG.ref_val_q90_max},
    ]
    if len(RANDOM_MAE_DRAWS):
        adv = paired_advantage(result["mae_draws"],
                               RANDOM_MAE_DRAWS * S.CFG.ref_val_random_ratio_max,
                               S.CFG.ref_val_confidence)
        rows.append({"criterion": "paired advantage over random eligible sets",
                     "value": adv["upper_bound"], "threshold": 0.0,
                     "passed": adv["upper_bound"] < 0.0})
    return pd.DataFrame(rows)


G1_CRITERIA = evaluate_architecture("g1", S.G1)
G1_CRITERIA.loc[len(G1_CRITERIA)] = {
    "criterion": "worst individual reference bound on U_val",
    "value": float(S.IND_BOUNDS["abs_upper"].max()),
    "threshold": S.CFG.ref_val_individual_max,
    "passed": bool(S.IND_BOUNDS["within_tolerance"].all())}
G1_CRITERIA.loc[len(G1_CRITERIA)] = {
    "criterion": "leave-one-reference-out shift bound",
    "value": float(LOO["max_shift_upper"].max()),
    "threshold": S.CFG.ref_val_loo_max,
    "passed": bool(LOO["within_tolerance"].all())}
G1_CRITERIA["architecture"] = "g1_calipered_panel"

G2_CRITERIA = evaluate_architecture("g2", S.G2)
_w_b = S.fit_stochastic_weights(S.SIGNATURE, S.SELECTED_REFERENCES, S.CFG.focal_id,
                              list(S.CALIPERS.index), S.MATCH_DISTANCE)
G2_CRITERIA.loc[len(G2_CRITERIA)] = {
    "criterion": "max single weight", "value": float(_w_b.max()),
    "threshold": S.CFG.max_single_weight, "passed": float(_w_b.max()) <= S.CFG.max_single_weight + 1e-9}
G2_CRITERIA.loc[len(G2_CRITERIA)] = {
    "criterion": "effective panel size J_eff", "value": S.j_effective(_w_b),
    "threshold": S.CFG.j_eff_floor, "passed": S.j_effective(_w_b) >= S.CFG.j_eff_floor}
G2_CRITERIA["architecture"] = "g2_synthetic_weighted"

CRITERIA = pd.concat([G1_CRITERIA, G2_CRITERIA], ignore_index=True)
CRITERIA.to_csv(S.GATE_DIR / "reference_validation_criteria.csv", index=False)
display(CRITERIA.round(4))

G1_PASSED = bool(G1_CRITERIA["passed"].all())
G2_PASSED = bool(G2_CRITERIA["passed"].all())
PRIMARY_AUTHORIZED = S.authorize_primary(G1_PASSED, g0_passed=True, g2_passed=G2_PASSED)
S.STOCHASTIC_AUTHORIZED = S.stochastic_estimand_authorized(G1_PASSED, G2_PASSED)

REFERENCE_VALIDATION = {
    "g1_passed": G1_PASSED, "g2_passed": G2_PASSED,
    "primary_authorized": PRIMARY_AUTHORIZED,
    "stochastic_authorized": S.STOCHASTIC_AUTHORIZED,
    "g0_role": "benchmark and falsification comparator; authorizes nothing",
    "architectures": ARCHITECTURES.to_dict("records"),
    "criteria": CRITERIA.to_dict("records"),
    "pseudo_focal_cohort": S.PSEUDO_COHORT,
    "random_reference_mae_mean": float(S.RANDOM_MAE_DISTRIBUTION.mean())
    if len(S.RANDOM_MAE_DISTRIBUTION) else None,
    "u_build": S.U_BUILD, "u_val": S.U_VAL, "u_test": S.U_TEST,
    "selected_references": S.SELECTED_REFERENCES,
}
S.durable_write(S.GATE_DIR / "reference_validation.json",
              json.dumps(REFERENCE_VALIDATION, indent=2, default=str))

if not G2_PASSED:
    S.log_departure("validation", "stochastic reference estimand reported",
                  "withheld: g2 did not pass its own validation",
                  "the primary per-reference panel is unaffected, because g2 "
                  "never authorized it")

if PRIMARY_AUTHORIZED:
    S.record_gate(GateOutcome("3_validation", GateStatus.PASS,
                            "g1 passed every preregistered criterion on its own",
                            quantities=REFERENCE_VALIDATION,
                            thresholds={"mae": S.CFG.ref_val_mae_max,
                                        "q90": S.CFG.ref_val_q90_max,
                                        "individual": S.CFG.ref_val_individual_max,
                                        "loo": S.CFG.ref_val_loo_max}))
    print(f"""
Gate 3 passed on g1, the architecture that is actually reported.
  g1 MAE on U_val   : {S.G1.get('mae', float('nan')):.4f}
  g0 benchmark      : {S.G0.get('mae', float('nan')):.4f}   (comparator only)
  random sets       : {float(S.RANDOM_MAE_DISTRIBUTION.mean()) if len(S.RANDOM_MAE_DISTRIBUTION) else float('nan'):.4f}
  stochastic secondary authorized: {S.STOCHASTIC_AUTHORIZED}
""")
else:
    _failed = G1_CRITERIA.query("not passed")["criterion"].tolist()
    S.stop("3_validation", GateStatus.REFERENCE_VALIDATION_FAILED,
         f"g1 failed on {_failed}",
         quantities=REFERENCE_VALIDATION,
         thresholds={"mae": S.CFG.ref_val_mae_max, "q90": S.CFG.ref_val_q90_max,
                     "individual": S.CFG.ref_val_individual_max,
                     "loo": S.CFG.ref_val_loo_max},
         more_data_could_resolve=False, new_protocol_version_required=True,
         message=f"""
REFERENCE_VALIDATION_FAILED on g1: {_failed}

g1 is the declared primary estimand, so nothing substitutes for it. g2 passed:
{G2_PASSED}. That is irrelevant to this decision, and v13's habit of letting the
best-performing architecture authorize confirmation is exactly the defect this
gate now closes.

Failure here is a redesign under a NEW protocol version. Confirmatory A
outcomes may not be inspected first and then used to alter the reference
architecture.
""")
S.checkpoint("gate3", {"g1": G1_PASSED, "g2": G2_PASSED})
