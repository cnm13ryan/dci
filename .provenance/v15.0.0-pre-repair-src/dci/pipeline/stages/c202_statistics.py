"""Stage 202 — migrated from notebook cell 202.py (statistics).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/202.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell


S.CLUSTER_LEVEL = "task_id"


def task_cell_table(scores: pd.DataFrame, value: str = "fail") -> pd.DataFrame:
    """One row per task, one column per (condition, constraint) cell."""
    return scores.pivot_table(index=S.CLUSTER_LEVEL,
                              columns=["condition_id", "constraint_id"],
                              values=value, aggfunc="mean").sort_index()
S.task_cell_table = task_cell_table


def calibration_cell_table(scores: pd.DataFrame) -> pd.DataFrame:
    """Task x (condition, constraint, paraphrase), so wording instability is
    computable from the same resample."""
    return scores.pivot_table(
        index=S.CLUSTER_LEVEL,
        columns=["condition_id", "constraint_id", "paraphrase_id"],
        values="fail", aggfunc="mean").sort_index()
S.calibration_cell_table = calibration_cell_table








def one_sided_upper(draws: pd.DataFrame, level: float) -> pd.Series:
    """Upper confidence bound. Used wherever the objective is 'small'."""
    return draws.quantile(level)


def abs_one_sided_upper(draws: pd.DataFrame, level: float) -> pd.Series:
    """Upper bound on the ABSOLUTE value, for two-sided equivalence claims."""
    return draws.abs().quantile(level)










# wilson_interval is defined in the configuration cell, because the audit
# sample size is obtained by inverting exactly this function.





def cell_mean(means: pd.Series, condition: str, constraint: str,
              paraphrase: Optional[int] = None) -> float:
    key = (condition, constraint) if paraphrase is None else (condition, constraint, paraphrase)
    return float(means[key]) if key in means.index else float("nan")
S.cell_mean = cell_mean


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
S.power_simulation = power_simulation


def mde_from_simulation(table: pd.DataFrame, column: str, power: float) -> float:
    ok = table[table[column] >= power]
    return float(ok["true_tau"].min()) if len(ok) else float("nan")


N_CLUSTERS = len(S.CONFIRMATORY_TASKS)
_effects = np.round(np.arange(0.02, 0.42, 0.02), 3)
_planning = []
for _sd in (0.20, 0.30):
    for _rho in (0.3, 0.6):
        sim = S.power_simulation(N_CLUSTERS, S.CFG.reference_count, _sd, _rho,
                               _effects, S.CFG.power_sim_reps, S.CFG.alpha)
        _planning.append({
            "sd_task": _sd, "rho_between_refs": _rho, "n_clusters": N_CLUSTERS,
            "se_per_reference": float(sim["se_per_reference"].iloc[0]),
            "critical_marginal": sim.attrs["critical_marginal"],
            "critical_simultaneous": sim.attrs["critical_simultaneous"],
            "mde_marginal": mde_from_simulation(sim, "marginal_power", S.CFG.power),
            "mde_simultaneous": mde_from_simulation(sim, "simultaneous_power", S.CFG.power)})
S.POWER_PLANNING = pd.DataFrame(_planning)
S.POWER_PLANNING.to_csv(S.DESIGN_DIR / "power_planning.csv", index=False)
display(S.POWER_PLANNING.round(3))

print(f"""
Sample-size planning, simulated on the estimator that is used

  Clusters            : {N_CLUSTERS} tasks. Paraphrases and seeds are crossed WITHIN
                        tasks and do not add clusters.
  SESOI               : {S.CFG.sesoi_risk_difference:.2f} risk difference
  Marginal MDE        : {S.POWER_PLANNING['mde_marginal'].min():.3f} to {S.POWER_PLANNING['mde_marginal'].max():.3f} across the variance grid
  Simultaneous MDE    : {S.POWER_PLANNING['mde_simultaneous'].min():.3f} to {S.POWER_PLANNING['mde_simultaneous'].max():.3f}
  Stopping rule       : fixed N. No optional stopping, no interim looks.

The two MDE columns answer different questions and must not be conflated. The
marginal figure is the smallest effect detectable for ONE named reference. The
reference-robust claim requires every one of the {S.CFG.reference_count} lower bounds to exclude
zero simultaneously, and its MDE is the larger number. Adequate marginal power
is not adequate power for the claim rule.

sd_task and rho are a conservative grid here. The calibration stage measures
them, and the recorded values are reported at the freeze.
""")
