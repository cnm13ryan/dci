CLUSTER_LEVEL = "task_id"


def task_cell_table(scores: pd.DataFrame, value: str = "fail") -> pd.DataFrame:
    """One row per task, one column per (condition, constraint) cell."""
    return scores.pivot_table(index=CLUSTER_LEVEL,
                              columns=["condition_id", "constraint_id"],
                              values=value, aggfunc="mean").sort_index()


def calibration_cell_table(scores: pd.DataFrame) -> pd.DataFrame:
    """Task x (condition, constraint, paraphrase), so wording instability is
    computable from the same resample."""
    return scores.pivot_table(
        index=CLUSTER_LEVEL,
        columns=["condition_id", "constraint_id", "paraphrase_id"],
        values="fail", aggfunc="mean").sort_index()


def bootstrap_functional(table: pd.DataFrame,
                         fn: Callable[[pd.Series], dict[str, float]],
                         reps: int, seed: int) -> tuple[pd.Series, pd.DataFrame]:
    """Resample task rows, recompute `fn` on the column means.

    Every quantity `fn` produces comes from the SAME resample, so their joint
    covariance is preserved. Computing them from separate resamples would
    discard exactly the correlation induced by a shared arm.
    """
    observed = fn(table.mean(axis=0))
    keys = list(observed)
    values = table.to_numpy(dtype=float)
    index = list(table.columns)
    n = values.shape[0]
    rng = np.random.default_rng(seed)
    draws = np.empty((reps, len(keys)))
    for r in range(reps):
        idx = rng.integers(0, n, size=n)
        means = pd.Series(np.nanmean(values[idx], axis=0), index=index)
        result = fn(means)
        draws[r] = [result[k] for k in keys]
    return pd.Series(observed, dtype=float), pd.DataFrame(draws, columns=keys)


def bootstrap_se(draws: pd.DataFrame) -> pd.Series:
    return draws.std(axis=0, ddof=1).replace(0.0, np.nan)


def percentile_ci(draws: pd.DataFrame, level: float) -> pd.DataFrame:
    a = 1 - level
    return pd.DataFrame({"ci_lower": draws.quantile(a / 2),
                         "ci_upper": draws.quantile(1 - a / 2)})


def one_sided_upper(draws: pd.DataFrame, level: float) -> pd.Series:
    """Upper confidence bound. Used wherever the objective is 'small'."""
    return draws.quantile(level)


def abs_one_sided_upper(draws: pd.DataFrame, level: float) -> pd.Series:
    """Upper bound on the ABSOLUTE value, for two-sided equivalence claims."""
    return draws.abs().quantile(level)


def simultaneous_bounds(point: pd.Series, draws: pd.DataFrame,
                        level: float) -> pd.DataFrame:
    """Studentised max-T simultaneous intervals over every column at once."""
    se = bootstrap_se(draws)
    centred = draws.subtract(point, axis=1)
    studentised = centred.divide(se, axis=1).abs()
    critical = float(np.nanquantile(studentised.max(axis=1).to_numpy(), level))
    out = pd.DataFrame({"estimate": point, "se": se,
                        "sim_lower": point - critical * se,
                        "sim_upper": point + critical * se})
    out.attrs["critical_value"] = critical
    return out


def simultaneous_abs_upper(point: pd.Series, draws: pd.DataFrame,
                           level: float) -> pd.DataFrame:
    """Simultaneous upper bound on |quantity| for each component.

    This is what an equivalence gate needs: not "is the estimate small" but
    "allowing for uncertainty, and simultaneously across every component, is
    every one of them still small". Averaging cannot rescue a component here,
    because the bound is taken componentwise.
    """
    bounds = simultaneous_bounds(point, draws, level)
    bounds["abs_upper"] = np.maximum(bounds["sim_upper"].abs(),
                                     bounds["sim_lower"].abs())
    return bounds


def bootstrap_p(point: pd.Series, draws: pd.DataFrame, reps: int) -> pd.Series:
    centred = draws.subtract(point, axis=1).abs()
    return centred.ge(point.abs(), axis=1).mean(axis=0).clip(lower=1.0 / max(reps, 1))


def paired_advantage(draws_a: pd.Series, draws_b: pd.Series,
                     level: float) -> dict[str, float]:
    """Is A better (smaller) than B, on the same resample?

    Comparing two point estimates says nothing about whether the difference is
    real. Because both are computed from the same task resample, their paired
    difference has a bootstrap distribution and therefore a bound.
    """
    diff = np.asarray(draws_a, dtype=float) - np.asarray(draws_b, dtype=float)
    return {"mean_difference": float(np.mean(diff)),
            "upper_bound": float(np.quantile(diff, level)),
            "prob_a_not_better": float(np.mean(diff >= 0))}


# wilson_interval is defined in the configuration cell, because the audit
# sample size is obtained by inverting exactly this function.

def holm(pvalues: Iterable[float]) -> list[float]:
    values = list(pvalues)
    order = np.argsort(values)
    n, adjusted, running = len(values), [0.0] * len(values), 0.0
    for rank, idx in enumerate(order):
        running = max(running, (n - rank) * values[idx])
        adjusted[idx] = min(1.0, running)
    return adjusted


def within_sesoi(lower: float, upper: float, sesoi: float) -> bool:
    return bool(lower > -sesoi and upper < sesoi)


def cell_mean(means: pd.Series, condition: str, constraint: str,
              paraphrase: Optional[int] = None) -> float:
    key = (condition, constraint) if paraphrase is None else (condition, constraint, paraphrase)
    return float(means[key]) if key in means.index else float("nan")


# ============================================ sample-size planning by simulation
def power_simulation(n_tasks: int, n_refs: int, sd_task: float, rho: float,
                     effects: Iterable[float], reps: int, alpha: float,
                     seed: int = 1234) -> pd.DataFrame:
    """Simulate the estimator that is actually used.

    The primary bootstrap resamples task clusters, so the sampling distribution
    that matters is that of the vector of task-mean contrasts. Paraphrases and
    seeds inside a task reduce within-task noise; they do not add clusters, and
    treating them as independent observations would overstate precision.

    Returns marginal per-reference power and the power of the simultaneous
    reference-robust claim, which requires every one of the J lower bounds to
    exclude zero at once.
    """
    rng = np.random.default_rng(seed)
    cov = sd_task**2 * ((1 - rho) * np.eye(n_refs) + rho * np.ones((n_refs, n_refs)))
    chol = np.linalg.cholesky(cov / n_tasks)
    z_marginal = stats.norm.ppf(1 - alpha / 2)

    # Critical value for the max statistic under the same correlation.
    null = rng.standard_normal((reps, n_refs)) @ chol.T
    se = np.sqrt(np.diag(cov / n_tasks))
    crit_sim = float(np.quantile(np.max(np.abs(null / se), axis=1), 1 - alpha))

    rows = []
    for effect in effects:
        draws = effect + rng.standard_normal((reps, n_refs)) @ chol.T
        marginal = float(np.mean(np.abs(draws[:, 0] / se[0]) > z_marginal))
        lower = draws - crit_sim * se
        simultaneous = float(np.mean(np.all(lower > 0, axis=1)))
        rows.append({"true_tau": effect, "se_per_reference": float(se[0]),
                     "marginal_power": marginal,
                     "simultaneous_power": simultaneous})
    out = pd.DataFrame(rows)
    out.attrs["critical_marginal"] = z_marginal
    out.attrs["critical_simultaneous"] = crit_sim
    return out


def mde_from_simulation(table: pd.DataFrame, column: str, power: float) -> float:
    ok = table[table[column] >= power]
    return float(ok["true_tau"].min()) if len(ok) else float("nan")


N_CLUSTERS = len(CONFIRMATORY_TASKS)
_effects = np.round(np.arange(0.02, 0.42, 0.02), 3)
_planning = []
for _sd in (0.20, 0.30):
    for _rho in (0.3, 0.6):
        sim = power_simulation(N_CLUSTERS, CFG.reference_count, _sd, _rho,
                               _effects, CFG.power_sim_reps, CFG.alpha)
        _planning.append({
            "sd_task": _sd, "rho_between_refs": _rho, "n_clusters": N_CLUSTERS,
            "se_per_reference": float(sim["se_per_reference"].iloc[0]),
            "critical_marginal": sim.attrs["critical_marginal"],
            "critical_simultaneous": sim.attrs["critical_simultaneous"],
            "mde_marginal": mde_from_simulation(sim, "marginal_power", CFG.power),
            "mde_simultaneous": mde_from_simulation(sim, "simultaneous_power", CFG.power)})
POWER_PLANNING = pd.DataFrame(_planning)
POWER_PLANNING.to_csv(DESIGN_DIR / "power_planning.csv", index=False)
display(POWER_PLANNING.round(3))

print(f"""
Sample-size planning, simulated on the estimator that is used

  Clusters            : {N_CLUSTERS} tasks. Paraphrases and seeds are crossed WITHIN
                        tasks and do not add clusters.
  SESOI               : {CFG.sesoi_risk_difference:.2f} risk difference
  Marginal MDE        : {POWER_PLANNING['mde_marginal'].min():.3f} to {POWER_PLANNING['mde_marginal'].max():.3f} across the variance grid
  Simultaneous MDE    : {POWER_PLANNING['mde_simultaneous'].min():.3f} to {POWER_PLANNING['mde_simultaneous'].max():.3f}
  Stopping rule       : fixed N. No optional stopping, no interim looks.

The two MDE columns answer different questions and must not be conflated. The
marginal figure is the smallest effect detectable for ONE named reference. The
reference-robust claim requires every one of the {CFG.reference_count} lower bounds to exclude
zero simultaneously, and its MDE is the larger number. Adequate marginal power
is not adequate power for the claim rule.

sd_task and rho are a conservative grid here. The calibration stage measures
them, and the recorded values are reported at the freeze.
""")
