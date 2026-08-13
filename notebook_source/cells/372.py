with phase("analysis"):
    # ------------------------------------------------ order-averaged contrast
    _pooled_cols = [f"tau_pooled|{j}" for j in SELECTED_REFERENCES]
    POOLED = simultaneous_bounds(POINT[_pooled_cols], DRAWS[_pooled_cols],
                                 CFG.confidence_level).join(
        percentile_ci(DRAWS[_pooled_cols], CFG.confidence_level))
    POOLED["p_bootstrap"] = bootstrap_p(POINT[_pooled_cols], DRAWS[_pooled_cols],
                                        CFG.bootstrap_reps)
    POOLED["reference"] = [c.split("|")[1] for c in POOLED.index]
    POOLED.to_csv(SCORE_DIR / "secondary_order_average.csv")
    display(POOLED.round(4))
    print("SECONDARY. This is the effect under a 50/50 draw over presentation "
          "order. Where the two co-primary contrasts differ in sign, this "
          "number describes no condition that was run.")

    # ------------------------------------------------------- order contrast
    _order_cols = [f"order_effect|{c}" for c in [CFG.focal_id, *SELECTED_REFERENCES]]
    ORDER = percentile_ci(DRAWS[_order_cols], CFG.confidence_level)
    ORDER.insert(0, "estimate", POINT[_order_cols])
    ORDER["constraint"] = [c.split("|")[1] for c in ORDER.index]
    ORDER.to_csv(SCORE_DIR / "order_effects.csv")
    print(f"\nOrder contrast: {CFG.orders[0]} minus {CFG.orders[1]}, failure scale")
    display(ORDER.round(4))

    # -------------------------------------- stochastic reference intervention
    if STOCHASTIC_ESTIMAND_AVAILABLE:
        _st_cols = [f"tau_stoch|{o}" for o in CFG.orders] + ["tau_stoch_pooled"]
        STOCHASTIC = percentile_ci(DRAWS[_st_cols], CFG.confidence_level)
        STOCHASTIC.insert(0, "estimate", POINT[_st_cols])
        STOCHASTIC["p_bootstrap"] = bootstrap_p(POINT[_st_cols], DRAWS[_st_cols],
                                                CFG.bootstrap_reps)
        STOCHASTIC["j_effective"] = J_EFF
        STOCHASTIC.to_csv(SCORE_DIR / "secondary_stochastic_reference.csv")
        display(STOCHASTIC.round(4))
        print(f"""SECONDARY, and reported always. Read as: instead of adding {CFG.focal_id},
draw a reference constraint from the prespecified distribution over
{SELECTED_REFERENCES}
with weights {dict(WEIGHTS.round(3))}.
Heterogeneity does not make this quantity meaningless. It only forbids the
stronger statement that the six controls are interchangeable instances of one
comparator.""")
    else:
        STOCHASTIC = pd.DataFrame()
        print(f"\nStochastic reference intervention WITHHELD: J_eff = {J_EFF:.2f} "
              f"below the floor of {CFG.j_eff_floor:.1f}.")

    # -------------------------------------------- homogeneity, now secondary
    HOMOGENEITY = {}
    for o in CFG.orders:
        cols = [f"tau|{j}|{o}" for j in SELECTED_REFERENCES]
        point = POINT[cols].to_numpy()
        draws = DRAWS[cols].to_numpy()
        J = len(cols)
        C = (np.eye(J) - np.ones((J, J)) / J)[:-1]
        Sigma = np.cov(draws, rowvar=False)
        inv = np.linalg.pinv(C @ Sigma @ C.T)
        stat = float((C @ point) @ inv @ (C @ point))
        centred = draws - point
        null = np.array([float((C @ centred[i]) @ inv @ (C @ centred[i]))
                         for i in range(len(centred))])
        HOMOGENEITY[o] = {
            "wald_statistic": stat,
            "p_bootstrap": float(np.mean(null >= stat)),
            "p_chi2_reference": float(1 - stats.chi2.cdf(stat, J - 1)),
            "max_offdiag_correlation": float(np.max(np.abs(
                np.corrcoef(draws, rowvar=False) - np.eye(J)))),
            "homogeneous_at_0.10": bool(float(np.mean(null >= stat)) > 0.10)}
    display(pd.DataFrame(HOMOGENEITY).T.round(4))
    (SCORE_DIR / "homogeneity.json").write_text(
        json.dumps(HOMOGENEITY, indent=2, default=float), encoding="utf-8")
    print("SECONDARY. Every contrast shares the focal arm and the same blocks, "
          "so Cov(tau_j, tau_k) is not zero and Cochran's Q with independent "
          "inverse-variance weights would be invalid. The null distribution "
          "here is the centred bootstrap, not chi-square.")

# ---------------------------------------------------------------------- GEE
GEE_RESULT = None
with phase("gee"):
    try:
        import statsmodels.api as sm
        from statsmodels.genmod.cov_struct import Exchangeable
        from statsmodels.genmod.families import Binomial

        frame = confirmatory_scores.query(
            "constraint_id == @CFG.target_id and is_measured and "
            "condition_id != 'A_ONLY'").copy()
        frame["added_constraint"] = pd.Categorical(
            frame["added_constraint"], categories=[CFG.focal_id, *SELECTED_REFERENCES])
        frame["order"] = pd.Categorical(frame["order"], categories=list(CFG.orders))
        design_matrix = pd.get_dummies(
            frame[["added_constraint", "order", "paraphrase_id"]],
            drop_first=True).astype(float)
        interaction = pd.get_dummies(
            frame["added_constraint"].astype(str) + ":" + frame["order"].astype(str),
            drop_first=True).astype(float)
        interaction = interaction[[c for c in interaction.columns
                                   if CFG.orders[1] in c]]
        design_matrix = pd.concat([design_matrix, interaction.add_prefix("int_")], axis=1)
        design_matrix = sm.add_constant(design_matrix, has_constant="add")

        gee = sm.GEE(frame["fail"].astype(float), design_matrix,
                     groups=frame["task_id"], family=Binomial(),
                     cov_struct=Exchangeable()).fit()
        GEE_RESULT = pd.DataFrame({"coef": gee.params, "se": gee.bse,
                                   "z": gee.tvalues, "p": gee.pvalues,
                                   "odds_ratio": np.exp(gee.params)})
        n_clusters = frame["task_id"].nunique()
        if n_clusters < 15:
            GEE_RESULT = GEE_RESULT.drop(columns=["z", "p"])
            print(f"GEE fitted on {n_clusters} task clusters. Inferential "
                  "p-values suppressed: GEE needs a small-sample correction "
                  "below roughly 15 clusters and none is applied here.")
        # Review item 8: v12 displayed GEE_RESULT and never wrote it.
        GEE_RESULT.to_csv(SCORE_DIR / "gee_model.csv")
        display(GEE_RESULT.round(4))
        print("SECONDARY. Coefficients are log-odds; an odds ratio is not a "
              "risk difference. The task-clustered bootstrap contrasts remain "
              "primary.")
    except Exception as exc:
        log_departure("analysis", "GEE logistic model fitted",
                      f"GEE failed: {type(exc).__name__}: {exc}",
                      "reported; the bootstrap contrasts do not depend on it")
