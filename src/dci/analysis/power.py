"""Power for the claim rule that is actually used.

WHAT WAS WRONG
--------------
The pre-repair planner simulated `n_refs = CFG.reference_count` = 6 correlated
contrasts. The confirmatory analysis passes `refs x orders` = 12 contrasts into
`simultaneous_bounds`. A max-T critical value grows with the dimension of the
family it controls (2.60 -> 2.82 at these settings), so the planner was reporting
the MDE of a claim rule the study does not use.

Substituting J=12 into the old equicorrelation model is not the fix either: it
asserts that every pair of the 12 contrasts is equally correlated, which is false
by construction. tau_{j,o} and tau_{k,o} SHARE THE FOCAL ARM mu_focal|o, so they
are strongly correlated; tau_{j,target_first} and tau_{j,added_first} share only
the task cluster. Those are different numbers and they pull the critical value in
different directions.

HOW THIS MODELS IT
------------------
Parameters live at the ARM level, where they are interpretable and where the
resulting contrast covariance is automatically a valid one:

    tau_{j,o} = mu_{focal,o} - mu_{j,o}                      (the estimator)
    Cov(tau) = L Sigma_arm L' / n_clusters                   (L = contrast matrix)

`Sigma_arm` is exchangeable in three blocks:

    same arm                                 -> 1
    same order, different constraint         -> rho_same_order
    different order, same constraint         -> rho_cross_order_same_constraint
    different order, different constraint    -> rho_cross_order_diff_constraint

Shared-focal-arm dependence across references, order-pair dependence, and
reference-to-reference dependence are then CONSEQUENCES of the arm model rather
than three free parameters that could be set to an impossible combination. The
builder checks positive semidefiniteness and refuses an inconsistent grid.

None of these correlations is measured yet. `SCENARIOS` is an explicit, labelled
sensitivity grid, and the reported MDE is a range over it -- not a point claim.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from typing import Iterable, Optional


def arm_covariance(n_refs: int, n_orders: int, sd_task: float,
                   rho_same_order: float,
                   rho_cross_order_same_constraint: float,
                   rho_cross_order_diff_constraint: float) -> np.ndarray:
    """Task-level covariance of the arm means, arms ordered focal-first per order.

    Arm index layout, for `n_orders` orders and `n_refs` references:
        o=0: [focal, ref_0, ..., ref_{J-1}], o=1: [focal, ref_0, ...], ...
    """
    per_order = n_refs + 1
    n = per_order * n_orders
    constraint = np.tile(np.arange(per_order), n_orders)
    order = np.repeat(np.arange(n_orders), per_order)

    same_order = order[:, None] == order[None, :]
    same_constraint = constraint[:, None] == constraint[None, :]
    corr = np.where(
        same_order,
        np.where(same_constraint, 1.0, rho_same_order),
        np.where(same_constraint, rho_cross_order_same_constraint,
                 rho_cross_order_diff_constraint))
    np.fill_diagonal(corr, 1.0)
    cov = corr * (sd_task ** 2)
    eig = float(np.min(np.linalg.eigvalsh(cov)))
    if eig < -1e-10:
        raise ValueError(
            f"the arm correlation grid is not positive semidefinite "
            f"(min eigenvalue {eig:.3e}): rho_same_order="
            f"{rho_same_order}, rho_cross_order_same_constraint="
            f"{rho_cross_order_same_constraint}, "
            f"rho_cross_order_diff_constraint={rho_cross_order_diff_constraint}")
    return cov


def contrast_matrix(n_refs: int, n_orders: int) -> np.ndarray:
    """L such that L @ arm_means gives tau_{j,o}, ordered o-major then j."""
    per_order = n_refs + 1
    rows = []
    for o in range(n_orders):
        for j in range(n_refs):
            row = np.zeros(per_order * n_orders)
            row[o * per_order] = 1.0                 # + focal|o
            row[o * per_order + 1 + j] = -1.0        # - ref_j|o
            rows.append(row)
    return np.vstack(rows)


def contrast_labels(references: Iterable[str], orders: Iterable[str]) -> list[str]:
    return [f"tau|{j}|{o}" for o in orders for j in references]


def primary_family_covariance(n_refs: int, n_orders: int, n_clusters: int,
                              sd_task: float, rho_same_order: float,
                              rho_cross_order_same_constraint: float,
                              rho_cross_order_diff_constraint: float
                              ) -> np.ndarray:
    """Sampling covariance of the 12 primary contrasts' task-mean estimator."""
    sigma = arm_covariance(n_refs, n_orders, sd_task, rho_same_order,
                           rho_cross_order_same_constraint,
                           rho_cross_order_diff_constraint)
    L = contrast_matrix(n_refs, n_orders)
    return L @ sigma @ L.T / float(n_clusters)


def simulate_claim_power(cov: np.ndarray, n_refs: int, n_orders: int,
                         effects: Iterable[float], reps: int, alpha: float,
                         seed: int = 20260809) -> pd.DataFrame:
    """Power of the max-T intersection claim on the real family.

    Reports three quantities that the pre-repair planner conflated:
      * marginal_power        one named reference, one order;
      * simultaneous_power_per_order
                              every reference positive at ONE order, with the
                              critical value controlling the whole 12-contrast
                              family (which is what the analysis calibrates);
      * simultaneous_power_both_orders
                              the co-primary reading: both orders at once.
    """
    cov = np.asarray(cov, dtype=float)
    k = cov.shape[0]
    if k != n_refs * n_orders:
        raise ValueError(f"covariance is {k}x{k}, expected {n_refs * n_orders}")
    rng = np.random.default_rng(seed)
    # Jitter only if needed: the arm model is PSD but can be singular.
    chol = np.linalg.cholesky(cov + np.eye(k) * 1e-12)
    se = np.sqrt(np.diag(cov))
    z_marginal = float(stats.norm.ppf(1 - alpha / 2))

    null = rng.standard_normal((reps, k)) @ chol.T
    crit_sim = float(np.quantile(np.max(np.abs(null / se), axis=1), 1 - alpha))

    order_blocks = [slice(o * n_refs, (o + 1) * n_refs) for o in range(n_orders)]
    rows = []
    for effect in effects:
        draws = effect + rng.standard_normal((reps, k)) @ chol.T
        lower = draws - crit_sim * se
        per_order = np.column_stack([np.all(lower[:, b] > 0, axis=1)
                                     for b in order_blocks])
        rows.append({
            "true_tau": float(effect),
            "se_per_contrast": float(se[0]),
            "marginal_power": float(np.mean(np.abs(draws[:, 0] / se[0]) > z_marginal)),
            "simultaneous_power_per_order": float(np.mean(per_order.any(axis=1))),
            "simultaneous_power_both_orders": float(np.mean(per_order.all(axis=1))),
        })
    out = pd.DataFrame(rows)
    out.attrs["critical_marginal"] = z_marginal
    out.attrs["critical_simultaneous"] = crit_sim
    out.attrs["n_family"] = k
    return out


def mde(table: pd.DataFrame, column: str, power: float) -> float:
    ok = table[table[column] >= power]
    return float(ok["true_tau"].min()) if len(ok) else float("nan")


# Labelled sensitivity scenarios. `rho_same_order` is the correlation between two
# constraint arms measured on the same task and order; it is the dominant driver
# of how much the shared focal arm couples the references.
SCENARIOS: tuple[dict, ...] = (
    {"label": "weak_task_coupling", "sd_task": 0.20,
     "rho_same_order": 0.30, "rho_cross_order_same_constraint": 0.50,
     "rho_cross_order_diff_constraint": 0.20},
    {"label": "moderate_task_coupling", "sd_task": 0.20,
     "rho_same_order": 0.60, "rho_cross_order_same_constraint": 0.70,
     "rho_cross_order_diff_constraint": 0.45},
    {"label": "weak_task_coupling_high_variance", "sd_task": 0.30,
     "rho_same_order": 0.30, "rho_cross_order_same_constraint": 0.50,
     "rho_cross_order_diff_constraint": 0.20},
    {"label": "moderate_task_coupling_high_variance", "sd_task": 0.30,
     "rho_same_order": 0.60, "rho_cross_order_same_constraint": 0.70,
     "rho_cross_order_diff_constraint": 0.45},
)


# Effect multiples of the SESOI that every design simulation must contain
# outright: the null, the SESOI itself, and twice the SESOI. These are the points
# the acceptance rule is stated at, so they are simulated rather than interpolated.
REQUIRED_SESOI_MULTIPLES: tuple[float, ...] = (0.0, 1.0, 2.0)


def scenario_effects(effects: Iterable[float], sesoi: float,
                     multiples: Iterable[float] = REQUIRED_SESOI_MULTIPLES
                     ) -> list[float]:
    """The simulated grid, guaranteed to contain the exact required effects.

    The exact SESOI is inserted rather than approached. A planner that reports
    the nearest grid point as `power_at_sesoi` answers a question nobody asked:
    with a grid of 0.05 and 0.10 and a SESOI of 0.06, the reported number was
    power at 0.05 - overstating it, because power rises with the effect.
    """
    grid = [float(e) for e in effects]
    for multiple in multiples:
        required = float(multiple) * float(sesoi)
        if not any(g == required for g in grid):
            grid.append(required)
    return sorted(set(grid))


def power_at_exact_effect(sim: pd.DataFrame, effect: float,
                          column: str) -> float:
    """Read one simulated effect by exact equality, or refuse.

    The lookup cannot silently degrade into a nearest-neighbour search: the
    grid is built to contain this value, so its absence is a configuration
    error rather than something to approximate around.
    """
    hit = sim[sim["true_tau"] == float(effect)]
    if len(hit) != 1:
        raise ValueError(
            f"the simulated effect grid does not contain exactly one row at "
            f"{effect!r}; it holds {sorted(sim['true_tau'].unique())}. Insert "
            "the required effect with scenario_effects() instead of reporting a "
            "neighbouring grid point.")
    return float(hit.iloc[0][column])


def plan_primary_power(n_clusters: int, n_refs: int, n_orders: int,
                       effects: Iterable[float], reps: int, alpha: float,
                       power: float, sesoi: float,
                       scenarios: Iterable[dict] = SCENARIOS,
                       seed: int = 20260809) -> pd.DataFrame:
    """One row per sensitivity scenario, for the real primary family."""
    effects = scenario_effects(effects, sesoi)
    rows = []
    for i, sc in enumerate(scenarios):
        cov = primary_family_covariance(
            n_refs, n_orders, n_clusters, sc["sd_task"], sc["rho_same_order"],
            sc["rho_cross_order_same_constraint"],
            sc["rho_cross_order_diff_constraint"])
        sim = simulate_claim_power(cov, n_refs, n_orders, effects, reps, alpha,
                                   seed=seed + i)
        rows.append({
            "scenario": sc["label"], "n_clusters": n_clusters,
            "n_family": int(n_refs * n_orders),
            "sd_task": sc["sd_task"], "rho_same_order": sc["rho_same_order"],
            "rho_cross_order_same_constraint": sc["rho_cross_order_same_constraint"],
            "rho_cross_order_diff_constraint": sc["rho_cross_order_diff_constraint"],
            # NOT the legacy `sd_task`. Legacy parameterised the CONTRAST sd
            # directly; this model parameterises the ARM sd, and the contrast sd
            # follows as sqrt(2 * sd^2 * (1 - rho_same_order)). Reported so the
            # two planners' grids can be compared on the same footing.
            "implied_contrast_sd": float(np.sqrt(
                2.0 * sc["sd_task"] ** 2 * (1.0 - sc["rho_same_order"]))),
            "se_per_contrast": float(sim["se_per_contrast"].iloc[0]),
            "critical_marginal": sim.attrs["critical_marginal"],
            "critical_simultaneous": sim.attrs["critical_simultaneous"],
            "mde_marginal": mde(sim, "marginal_power", power),
            "mde_simultaneous_per_order": mde(sim, "simultaneous_power_per_order", power),
            "mde_simultaneous_both_orders": mde(sim, "simultaneous_power_both_orders", power),
            "sesoi": sesoi,
            "power_at_sesoi_marginal":
                power_at_exact_effect(sim, sesoi, "marginal_power"),
            "power_at_sesoi_per_order":
                power_at_exact_effect(sim, sesoi, "simultaneous_power_per_order"),
            "power_at_sesoi_both_orders":
                power_at_exact_effect(sim, sesoi, "simultaneous_power_both_orders"),
            # The other two points the acceptance rule is stated at, also exact.
            "false_positive_at_zero":
                power_at_exact_effect(sim, 0.0, "simultaneous_power_per_order"),
            "power_at_two_sesoi_per_order":
                power_at_exact_effect(sim, 2.0 * sesoi,
                                      "simultaneous_power_per_order"),
        })
    out = pd.DataFrame(rows)
    out["powered_at_sesoi"] = out["power_at_sesoi_per_order"] >= power
    return out


def required_clusters(n_refs: int, n_orders: int, scenario: dict,
                      effect: float, reps: int, alpha: float, power: float,
                      candidates: Iterable[int], seed: int = 20260809
                      ) -> Optional[int]:
    """Smallest cluster count in `candidates` reaching `power` at `effect`."""
    for n in sorted(candidates):
        cov = primary_family_covariance(
            n_refs, n_orders, n, scenario["sd_task"], scenario["rho_same_order"],
            scenario["rho_cross_order_same_constraint"],
            scenario["rho_cross_order_diff_constraint"])
        sim = simulate_claim_power(cov, n_refs, n_orders, [effect], reps, alpha,
                                   seed=seed)
        if float(sim["simultaneous_power_per_order"].iloc[0]) >= power:
            return int(n)
    return None
