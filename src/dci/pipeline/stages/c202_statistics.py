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
from dci.analysis.power import plan_primary_power  # noqa: F401


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

# --------------------------------------------------------------- LEGACY planner
# Retained, clearly labelled, for provenance only: it models `reference_count`
# contrasts and OMITS the order dimension, so its critical value controls a
# 6-contrast family while the confirmatory analysis calibrates over 12. It is no
# longer the planning basis. See dci.analysis.power for why substituting J=12
# into an equicorrelation model is not the fix either.
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
S.POWER_PLANNING_LEGACY = pd.DataFrame(_planning)
S.POWER_PLANNING_LEGACY.to_csv(
    S.DESIGN_DIR / "power_planning_legacy_six_reference_family.csv", index=False)

# ------------------------------------------------- the ACTUAL primary family
# refs x orders, with an arm-level covariance so that shared-focal-arm coupling,
# order-pair coupling and reference-to-reference coupling are consequences of one
# consistent model rather than three independently settable numbers.
S.POWER_PLANNING = plan_primary_power(
    n_clusters=N_CLUSTERS, n_refs=S.CFG.reference_count,
    n_orders=len(S.CFG.orders), effects=_effects,
    reps=S.CFG.power_sim_reps, alpha=S.CFG.alpha, power=S.CFG.power,
    sesoi=S.CFG.sesoi_risk_difference)
S.POWER_PLANNING.to_csv(S.DESIGN_DIR / "power_planning.csv", index=False)
display(S.POWER_PLANNING.round(3))

S.PRIMARY_FAMILY_SIZE = int(S.CFG.reference_count * len(S.CFG.orders))
S.POWERED_AT_SESOI = bool(S.POWER_PLANNING["powered_at_sesoi"].all())
_worst = S.POWER_PLANNING.loc[S.POWER_PLANNING["power_at_sesoi_per_order"].idxmin()]
_best = S.POWER_PLANNING.loc[S.POWER_PLANNING["power_at_sesoi_per_order"].idxmax()]

print(f"""
Sample-size planning, simulated on the claim rule that is used

  Clusters            : {N_CLUSTERS} tasks. Paraphrases and seeds are crossed WITHIN
                        tasks and do not add clusters.
  Primary family      : {S.PRIMARY_FAMILY_SIZE} contrasts = {S.CFG.reference_count} references x {len(S.CFG.orders)} orders.
                        This is the family simultaneous_bounds() calibrates.
  SESOI               : {S.CFG.sesoi_risk_difference:.2f} risk difference
  Marginal MDE        : {S.POWER_PLANNING['mde_marginal'].min():.3f} to {S.POWER_PLANNING['mde_marginal'].max():.3f} across the scenario grid
  Simultaneous MDE
    one order         : {S.POWER_PLANNING['mde_simultaneous_per_order'].min():.3f} to {S.POWER_PLANNING['mde_simultaneous_per_order'].max():.3f}
    both orders       : {S.POWER_PLANNING['mde_simultaneous_both_orders'].min():.3f} to {S.POWER_PLANNING['mde_simultaneous_both_orders'].max():.3f}
  Power at the SESOI  : {_worst['power_at_sesoi_per_order']:.2f} ({_worst['scenario']}) to {_best['power_at_sesoi_per_order']:.2f} ({_best['scenario']})
  Powered at SESOI    : {S.POWERED_AT_SESOI}   (target {S.CFG.power:.2f})
  Stopping rule       : fixed N. No optional stopping, no interim looks.

The MDE columns answer different questions and must not be conflated. The
marginal figure is the smallest effect detectable for ONE named reference at ONE
order. The reference-robust claim requires every one of the {S.CFG.reference_count} lower bounds at
an order to exclude zero simultaneously, while the critical value controls all
{S.PRIMARY_FAMILY_SIZE}. Adequate marginal power is not adequate power for the claim rule.

The correlations are ASSUMED, not measured: `scenario` labels a sensitivity grid
and the MDE is reported as a range over it. `sd_task` here is the ARM standard
deviation; `implied_contrast_sd` is the comparable quantity to the legacy
planner's `sd_task`. Calibration measures these, and the recorded values are
reported at the freeze.
""")
if not S.POWERED_AT_SESOI:
    print(f"""POWER NOTICE: at {N_CLUSTERS} clusters no scenario in the grid reaches
{S.CFG.power:.0%} power for the reference-robust claim at the SESOI of
{S.CFG.sesoi_risk_difference:.2f}. A non-significant primary result is therefore
NOT evidence of absence, and must be reported as inconclusive at the SESOI unless
the interval itself establishes equivalence. This is a preregistration-relevant
fact, not a result.""")
