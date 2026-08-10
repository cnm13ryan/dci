WORDING_PANEL = [CFG.focal_id, *SELECTED_REFERENCES]
WORDING_COMPONENTS = ([SIG_DIFFICULTY]
                      + [f"g|{u}|{o}" for u in U_VAL for o in CFG.orders]
                      + [f"r|{u}|{o}" for u in U_VAL for o in CFG.orders])

with phase("gate3b_wording"):
    _w_design = build_wording_validation_design(WORDING_PANEL, U_VAL)
    _w_design.to_csv(DESIGN_DIR / "wording_validation_design.csv", index=False)
    print(f"wording validation: {len(_w_design)} rows, wordings "
          f"{tuple(CFG.paraphrase_holdout)}, {len(WORDING_TASKS)} dedicated tasks")
    _w_resp = run_generation_stage(_w_design, "wording_validation")
    _err = 1.0 - _w_resp["generation_ok"].mean()
    if _err > 0.10:
        raise RuntimeError(f"{_err:.1%} of wording-validation generations failed.")
    wording_scores = score_responses(_w_resp)
    _w_table = calibration_cell_table(wording_scores)

    # ------------------------------------------------------------------ v15
    # One discrepancy per (reference, held-out wording, component, order).
    #
    # v14 handed BOTH held-out wordings to make_signature_fn together, which
    # averages over them inside the signature before any discrepancy is formed.
    # A reference that is +0.12 too easy under one wording and -0.12 too hard
    # under the other then presents as perfectly comparable. Comparability that
    # only holds on average across wordings is not comparability: the
    # confirmatory design renders ONE wording at a time.
    def _per_wording_gap_fn(means: pd.Series) -> dict[str, float]:
        out: dict[str, float] = {}
        for p_id in CFG.paraphrase_holdout:
            sig = make_signature_fn(WORDING_PANEL, U_VAL, [p_id], COUPLING)(means)
            for ref in SELECTED_REFERENCES:
                for comp in WORDING_COMPONENTS:
                    fk, jk = signature_key(CFG.focal_id, comp), signature_key(ref, comp)
                    if fk in sig and jk in sig:
                        out[f"{ref}|{comp}|p{p_id}"] = float(sig[fk]) - float(sig[jk])
        return out

    W_GAP_POINT, W_GAP_DRAWS = bootstrap_functional(
        _w_table, _per_wording_gap_fn, SIG_REPS, CFG.base_seed + 606)

    # The averaged view is retained as a DIAGNOSTIC only, so the report can show
    # exactly how much cancellation the v14 rule would have absorbed.
    _w_fn = make_signature_fn(WORDING_PANEL, U_VAL, list(CFG.paraphrase_holdout), COUPLING)
    W_POINT, W_DRAWS = bootstrap_functional(
        _w_table, _w_fn, SIG_REPS, CFG.base_seed + 607)
    W_SIG = signature_frame(W_POINT, WORDING_PANEL, U_VAL)
    W_SIG.to_csv(SCORE_DIR / "wording_validation_signature.csv")
    W_AVG_POINT, W_AVG_DRAWS = discrepancy_frames(
        W_POINT, W_DRAWS, CFG.focal_id, SELECTED_REFERENCES, WORDING_COMPONENTS)
    W_AVERAGED = simultaneous_abs_upper(W_AVG_POINT, W_AVG_DRAWS,
                                        CFG.wording_val_confidence)
    W_AVERAGED.to_csv(GATE_DIR / "wording_validation_averaged_diagnostic.csv")

# Family calipers. derive_calipers assigns one delta per family, so any member
# of the family carries it.
_family_caliper = {}
for comp in CALIPERS.index:
    _family_caliper.setdefault(component_family(comp), float(CALIPERS.at[comp, "caliper"]))

# Simultaneous across the WHOLE held-out family: every reference, every held-out
# wording, every component, every order, at once.
W_BOUNDS = simultaneous_abs_upper(W_GAP_POINT, W_GAP_DRAWS, CFG.wording_val_confidence)
W_BOUNDS["reference"] = [k.split("|")[0] for k in W_BOUNDS.index]
W_BOUNDS["wording"] = [int(k.rsplit("|p", 1)[1]) for k in W_BOUNDS.index]
W_BOUNDS["component"] = ["|".join(k.rsplit("|p", 1)[0].split("|")[1:])
                         for k in W_BOUNDS.index]
W_BOUNDS["order"] = [component_order(c) or "" for c in W_BOUNDS["component"]]
W_BOUNDS["family"] = [component_family(c) for c in W_BOUNDS["component"]]
W_BOUNDS["caliper"] = [_family_caliper.get(f, np.nan) for f in W_BOUNDS["family"]]
W_BOUNDS["tolerance"] = W_BOUNDS["caliper"] * CFG.wording_val_caliper_multiple
W_BOUNDS["within_tolerance"] = W_BOUNDS["abs_upper"] <= W_BOUNDS["tolerance"]
W_BOUNDS.to_csv(GATE_DIR / "wording_validation.csv")
display(W_BOUNDS.round(4))

_per_ref = W_BOUNDS.groupby(["reference", "wording"]).agg(
    worst_bound=("abs_upper", "max"), worst_tolerance=("tolerance", "min"),
    n_failing=("within_tolerance", lambda s: int((~s).sum())))
display(_per_ref.round(4))

# How much cancellation the averaged rule would have absorbed, reported so the
# difference between the two rules is visible rather than asserted.
_avg_worst = float(W_AVERAGED["abs_upper"].max())
_cell_worst = float(W_BOUNDS["abs_upper"].max())
print(f"""
Per-wording versus averaged
  worst per-cell bound (the gate)        : {_cell_worst:.4f}
  worst averaged bound (diagnostic only) : {_avg_worst:.4f}
  cancellation absorbed by averaging     : {_cell_worst - _avg_worst:+.4f}

Gate 3b decides on the per-cell bound. The averaged figure is reported so the
size of the cancellation is visible; it authorizes nothing.""")

WORDING_VALIDATION = {
    "rule": "every (reference, held-out wording, component, order) cell",
    "n_cells": int(len(W_BOUNDS)),
    "worst_cell_bound": _cell_worst,
    "worst_averaged_bound_diagnostic": _avg_worst,
    "held_out_wordings": list(CFG.paraphrase_holdout),
    "tasks": [t["task_id"] for t in WORDING_TASKS],
    "components": WORDING_COMPONENTS,
    "caliper_multiple": CFG.wording_val_caliper_multiple,
    "worst_bound": float(W_BOUNDS["abs_upper"].max()),
    "n_failing_cells": int((~W_BOUNDS["within_tolerance"]).sum()),
    "per_reference_wording": {f"{r}|p{w}": v for (r, w), v
                              in _per_ref.to_dict("index").items()},
    "passed": bool(W_BOUNDS["within_tolerance"].all()),
}
durable_write(GATE_DIR / "wording_validation.json",
              json.dumps(WORDING_VALIDATION, indent=2, default=str))

if WORDING_VALIDATION["passed"]:
    record_gate(GateOutcome("3b_wording", GateStatus.PASS,
                            "comparability survives wordings never used to build it",
                            quantities=WORDING_VALIDATION,
                            thresholds={"caliper_multiple": CFG.wording_val_caliper_multiple}))
    print(f"""
Gate 3b passed. Under the two held-out wordings the worst simultaneous bound on
|z_B - z_Cj| is {WORDING_VALIDATION['worst_bound']:.4f}, inside {CFG.wording_val_caliper_multiple}x the caliper everywhere.

The primary estimand still averages only over the prespecified primary
wordings. This result says the comparability transports; it does not enlarge
the wording set the claim is about.
""")
else:
    _bad = _per_ref.query("n_failing > 0").index.tolist()
    stop("3b_wording", GateStatus.WORDING_VALIDATION_FAILED,
         f"comparability does not transport for {_bad}",
         quantities=WORDING_VALIDATION,
         thresholds={"caliper_multiple": CFG.wording_val_caliper_multiple},
         more_data_could_resolve=False, new_protocol_version_required=True,
         message=f"""
WORDING_VALIDATION_FAILED for {_bad}.

Under wordings that never contributed to the calibration signature or to
reference selection, {WORDING_VALIDATION['n_failing_cells']} comparability cells exceed {CFG.wording_val_caliper_multiple}x their caliper.
The panel is matched to B in the wordings used to build it and not otherwise.

Confirmation is not authorized. The legitimate responses are to author further
audited wordings and recalibrate under a new protocol version, or to report
that comparability is wording-specific. Adding the held-out wordings to the
calibration set is NOT one of them: it would destroy the only held-out wording
evidence the design has.
""")
checkpoint("gate3b", WORDING_VALIDATION)
