GATE4_RESULT: dict[str, Any] = {"run": False}
FALSIFICATION_INDIVIDUAL = pd.DataFrame()
FALSIFICATION_PANEL = pd.DataFrame()

if CFG.run_placebo and len(placebo_scores):
    with phase("gate4_falsification"):
        _plac_table = task_cell_table(placebo_scores.query("is_measured"), "fail")
        _w = {c: float(WEIGHTS[c]) for c in SELECTED_REFERENCES}

        def _falsification_fn(means: pd.Series) -> dict[str, float]:
            """Per-reference and weighted discrepancies on U_test.

            g_{Q,u,o} shares the u-alone baseline, so it cancels in the
            difference and the discrepancy is read directly from the two paired
            cells.
            """
            out: dict[str, float] = {}
            for u in U_TEST:
                for o in CFG.orders:
                    focal = cell_mean(means, f"{u}|{CFG.focal_id}|{o}", u)
                    refs = {j: cell_mean(means, f"{u}|{j}|{o}", u)
                            for j in SELECTED_REFERENCES}
                    for j, value in refs.items():
                        out[f"{j}|g|{u}|{o}"] = focal - value
                    out[f"panel|g|{u}|{o}"] = focal - float(
                        np.nanmean(list(refs.values())))
                    out[f"weighted|g|{u}|{o}"] = focal - float(
                        np.nansum([_w[j] * refs[j] for j in SELECTED_REFERENCES]))
            return out

        _p_point, _p_draws = bootstrap_functional(
            _plac_table, _falsification_fn, CFG.bootstrap_reps, CFG.base_seed + 505)

    _ind_keys = [k for k in _p_point.index
                 if not k.startswith(("panel|", "weighted|"))]
    _panel_keys = [k for k in _p_point.index if k.startswith("panel|")]
    _weighted_keys = [k for k in _p_point.index if k.startswith("weighted|")]

    # ---------------------------------------- primary g1 falsification
    FALSIFICATION_INDIVIDUAL = simultaneous_abs_upper(
        _p_point[_ind_keys], _p_draws[_ind_keys], CFG.falsification_confidence)
    FALSIFICATION_INDIVIDUAL["reference"] = [k.split("|")[0]
                                             for k in FALSIFICATION_INDIVIDUAL.index]
    FALSIFICATION_INDIVIDUAL["within_tolerance"] = (
        FALSIFICATION_INDIVIDUAL["abs_upper"] <= CFG.falsification_individual_max)
    FALSIFICATION_INDIVIDUAL.to_csv(GATE_DIR / "falsification_individual.csv")
    display(FALSIFICATION_INDIVIDUAL.round(4))
    display(FALSIFICATION_INDIVIDUAL.groupby("reference")["abs_upper"].max()
            .round(4).to_frame("worst_simultaneous_bound"))

    FALSIFICATION_PANEL = simultaneous_abs_upper(
        _p_point[_panel_keys], _p_draws[_panel_keys], CFG.falsification_confidence)
    FALSIFICATION_PANEL["within_tolerance"] = (
        FALSIFICATION_PANEL["abs_upper"] <= CFG.falsification_panel_max)
    FALSIFICATION_PANEL.to_csv(GATE_DIR / "falsification_panel.csv")

    _g1_pass = bool(FALSIFICATION_INDIVIDUAL["within_tolerance"].all())
    _worst = float(FALSIFICATION_INDIVIDUAL["abs_upper"].max())
    _worst_point = float(FALSIFICATION_INDIVIDUAL["estimate"].abs().max())

    # ---------------------------------------- secondary g2 falsification
    _g2_pass = None
    if STOCHASTIC_ESTIMAND_AVAILABLE and _weighted_keys:
        FALSIFICATION_WEIGHTED = simultaneous_abs_upper(
            _p_point[_weighted_keys], _p_draws[_weighted_keys],
            CFG.falsification_confidence)
        FALSIFICATION_WEIGHTED["within_tolerance"] = (
            FALSIFICATION_WEIGHTED["abs_upper"] <= CFG.falsification_panel_max)
        FALSIFICATION_WEIGHTED.to_csv(GATE_DIR / "falsification_weighted.csv")
        display(FALSIFICATION_WEIGHTED.round(4))
        _g2_pass = bool(FALSIFICATION_WEIGHTED["within_tolerance"].all())

    GATE4_RESULT = {
        "run": True, "u_test": U_TEST,
        "g1_individual_passed": _g1_pass,
        "worst_individual_bound": _worst,
        "worst_individual_point": _worst_point,
        "panel_residual_bound": float(FALSIFICATION_PANEL["abs_upper"].max()),
        "panel_passed": bool(FALSIFICATION_PANEL["within_tolerance"].all()),
        "g2_weighted_passed": _g2_pass,
        "bridge_target_in_u_test": bool(BRIDGE_AVAILABLE),
    }
    if _g1_pass:
        record_gate(GateOutcome("4_falsification", GateStatus.PASS,
                                "every individual reference reproduced B's generic "
                                "burden on targets that influenced nothing",
                                quantities=GATE4_RESULT,
                                thresholds={"individual": CFG.falsification_individual_max,
                                            "panel": CFG.falsification_panel_max}))
        print(f"""
Gate 4 passed on the primary g1 architecture. The worst simultaneous bound over
{len(FALSIFICATION_INDIVIDUAL)} reference x target x order cells is {_worst:.4f}, inside {CFG.falsification_individual_max}.
Secondary g2 falsification: {_g2_pass}.
""")
    else:
        _bad = sorted(FALSIFICATION_INDIVIDUAL.query("not within_tolerance")
                      ["reference"].unique())
        stop("4_falsification", GateStatus.FINAL_FALSIFICATION_FAILED,
             f"references {_bad} exceeded the equivalence tolerance on U_test",
             quantities=GATE4_RESULT,
             thresholds={"individual": CFG.falsification_individual_max},
             more_data_could_resolve=False, new_protocol_version_required=True,
             message=f"""
FINAL_FALSIFICATION_FAILED for {_bad}.

Worst individual simultaneous bound {_worst:.4f} against a tolerance of
{CFG.falsification_individual_max}; the largest point estimate was only {_worst_point:.4f}, which is why this gate
decides on bounds. The equal-weight panel residual bound was
{float(FALSIFICATION_PANEL['abs_upper'].max()):.4f}: averaging looked acceptable while an individual
reference did not.

This is reported, not repaired. Do not adjust the reference set, the calipers
or the panel and rerun: a redesign is a new protocol version. The confirmatory
matrix above stands as computed and must be read alongside this failure.
""")
else:
    record_gate(GateOutcome("4_falsification", GateStatus.FINAL_FALSIFICATION_FAILED,
                            "the placebo stage was not run, so the frozen "
                            "architecture is unfalsified",
                            quantities={"run": False},
                            more_data_could_resolve=True))

if not BRIDGE_AVAILABLE:
    print("""
TRANSPORT LIMITATION: no sentence-scoped bridge target survived screening, so
U_test contains only whole-answer targets. Nothing here tests generalisation
into A's own scope, and the falsification result is conditional on that.
""")

# ---------------------------- robustness over preregistered analytic choices
with phase("robustness"):
    grid = []
    for scope_choice in ("both_orders", *CFG.orders):
        for endpoint in ("strict", "strict_or_unscorable"):
            source = confirmatory_scores.query(
                "constraint_id == @CFG.target_id and is_measured").copy()
            source["outcome"] = (
                source["fail"] if endpoint == "strict"
                else source["status"].isin(["violation", "unscorable"]).astype(int))
            if scope_choice in CFG.orders:
                source = source.query("order in (@scope_choice, 'none')")
            piv = source.pivot_table(
                index=["task_id", "paraphrase_id", "repetition_seed"],
                columns="added_constraint", values="outcome", aggfunc="mean")
            if CFG.focal_id not in piv.columns or not set(SELECTED_REFERENCES) <= set(piv.columns):
                continue
            row = {"order_scope": scope_choice, "endpoint": endpoint,
                   "tau_min": float(min((piv[CFG.focal_id] - piv[j]).mean()
                                        for j in SELECTED_REFERENCES))}
            row.update({f"tau_{j}": float((piv[CFG.focal_id] - piv[j]).mean())
                        for j in SELECTED_REFERENCES})
            grid.append(row)
    ROBUSTNESS = pd.DataFrame(grid)
ROBUSTNESS.to_csv(SCORE_DIR / "robustness_grid.csv", index=False)
display(ROBUSTNESS.round(4))

_by_wording = []
for p in P_FINAL:
    sub = confirmatory_scores.query(
        "constraint_id == @CFG.target_id and is_measured and paraphrase_id == @p")
    piv = sub.pivot_table(index="task_id", columns="condition_id",
                          values="fail", aggfunc="mean")
    for o in CFG.orders:
        for j in SELECTED_REFERENCES:
            a, b = f"{CFG.focal_id}|{o}", f"{j}|{o}"
            if {a, b} <= set(piv.columns):
                _by_wording.append({"paraphrase_id": p, "order": o, "reference": j,
                                    "tau": float((piv[a] - piv[b]).mean())})
BY_WORDING = pd.DataFrame(_by_wording)
BY_WORDING.to_csv(SCORE_DIR / "tau_by_paraphrase.csv", index=False)
if not BY_WORDING.empty:
    _spread = BY_WORDING.groupby(["order", "reference"])["tau"].agg(["min", "max", "std"])
    _spread["sign_flips"] = BY_WORDING.groupby(["order", "reference"])["tau"].apply(
        lambda s: bool(np.sign(s).nunique() > 1))
    display(_spread.round(4))
    if bool(_spread["sign_flips"].any()):
        print("At least one contrast changes sign across primary wordings. The "
              "cluster bootstrap resamples tasks and does not cover paraphrase, "
              "so report this table with every tau.")
checkpoint("gate4", GATE4_RESULT)
