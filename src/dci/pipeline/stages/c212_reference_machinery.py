"""Stage 212 — migrated from notebook cell 212.py (reference_machinery).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/212.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import indexed_frame  # noqa: F401
from dci.analysis.reference_error import reference_error_certificate as family_level_certificate  # noqa: F401
from dci.analysis.coupling_audit import audit_summary, coupling_audit, kappa_is_degenerate  # noqa: F401
from dci.exceptions import SensitivityNotEstimable, StudyStop  # noqa: F401
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.provenance.hashes import sha  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

# ===================================================== signature definition
S.SIG_DIFFICULTY = "d"
S.SIG_COUPLING = "kappa"
SIG_S_D, SIG_S_G, SIG_S_R, S.SIG_S_MAX = "s_d", "s_g", "s_r", "s_max"
# s_max is computed and reported but is a summary of the three family-specific
# instabilities, so matching on it as well would double count.
S.WORDING_MATCHED = (SIG_S_D, SIG_S_G, SIG_S_R)
WORDING_DIAGNOSTIC = (S.SIG_S_MAX,)


def signature_components(u_build: Iterable[str]) -> list[str]:
    comps = [S.SIG_DIFFICULTY]
    for u in u_build:
        for o in S.CFG.orders:
            comps.append(f"g|{u}|{o}")
    for u in u_build:
        for o in S.CFG.orders:
            comps.append(f"r|{u}|{o}")
    if S.CFG.coupling_role == "matched":
        comps.append(S.SIG_COUPLING)
    comps.extend(S.WORDING_MATCHED)
    return comps
S.signature_components = signature_components


def component_family(component: str) -> str:
    if component.startswith("g|"):
        return "g"
    if component.startswith("r|"):
        return "r"
    if component in S.WORDING_MATCHED or component in WORDING_DIAGNOSTIC:
        return "s"
    return component
S.component_family = component_family


def component_target(component: str) -> Optional[str]:
    return component.split("|")[1] if "|" in component else None
S.component_target = component_target


def component_order(component: str) -> Optional[str]:
    return component.split("|")[2] if component.count("|") == 2 else None
S.component_order = component_order


def signature_key(cid: str, component: str) -> str:
    return f"{cid}::{component}"
S.signature_key = signature_key


# Every feature carries a frozen causal role. A feature may only be used in the
# way its role permits; the role table is hashed into the protocol.
S.FEATURE_ROLES: dict[str, str] = {
    "generative_scope": "exact_eligibility",
    "logical_compatibility": "eligibility",
    "entailment_duplication": "eligibility",
    "verifier_validity": "eligibility",
    S.SIG_DIFFICULTY: "caliper",
    "g": "caliper",
    "r": "caliper",
    S.SIG_COUPLING: "caliper",
    SIG_S_D: "caliper", SIG_S_G: "caliper", SIG_S_R: "caliper",
    S.SIG_S_MAX: "diagnostic",
    "mahalanobis_distance": "ranking_after_eligibility",
    "stochastic_weights": "weighting_after_admissibility",
    "mutation_flip_rate": "diagnostic",
    "response_words": "post_treatment_reported_never_matched",
    "cross_sentence_planning_demand": "mechanism_never_matched",
}
S.FEATURE_ROLES_SHA256 = sha(S.FEATURE_ROLES)


def make_signature_fn(constraint_ids: list[str], u_build: list[str],
                      paraphrase_ids: list[int],
                      coupling: pd.Series) -> Callable[[pd.Series], dict[str, float]]:
    """Turn task-mean cells into a full signature for every constraint at once."""
    comps = S.signature_components(u_build)
    measured = [c for c in comps
                if c not in (S.SIG_COUPLING, *S.WORDING_MATCHED)]
    emit_coupling = True   # always emitted; matched only when the role says so

    def fn(means: pd.Series) -> dict[str, float]:
        out: dict[str, float] = {}
        for cid in constraint_ids:
            per_p: dict[int, dict[str, float]] = {}
            for p in paraphrase_ids:
                vals: dict[str, float] = {}
                iso_q = S.cell_mean(means, S.iso_condition(cid), cid, p)
                vals[S.SIG_DIFFICULTY] = iso_q
                for u in u_build:
                    iso_u = S.cell_mean(means, S.iso_condition(u), u, p)
                    vals[f"g|{u}|{S.TARGET_FIRST}"] = (
                        S.cell_mean(means, S.pair_condition(u, cid, u), u, p) - iso_u)
                    vals[f"g|{u}|{S.ADDED_FIRST}"] = (
                        S.cell_mean(means, S.pair_condition(u, cid, cid), u, p) - iso_u)
                    vals[f"r|{u}|{S.TARGET_FIRST}"] = (
                        S.cell_mean(means, S.pair_condition(u, cid, cid), cid, p) - iso_q)
                    vals[f"r|{u}|{S.ADDED_FIRST}"] = (
                        S.cell_mean(means, S.pair_condition(u, cid, u), cid, p) - iso_q)
                per_p[p] = vals

            stacked = np.array([[per_p[p][c] for c in measured]
                                for p in paraphrase_ids], dtype=float)
            for j, c in enumerate(measured):
                out[S.signature_key(cid, c)] = float(np.nanmean(stacked[:, j]))
            out[S.signature_key(cid, S.SIG_COUPLING)] = float(coupling.get(cid, np.nan))

            # Decomposed wording instability. A single wording cannot express
            # instability, so it is 0 by definition at P=1 and the escalation
            # rule handles the rest.
            if stacked.shape[0] > 1:
                sds = np.nanstd(stacked, axis=0, ddof=1)
                by_family: dict[str, list[float]] = {"d": [], "g": [], "r": []}
                for j, c in enumerate(measured):
                    by_family[S.component_family(c)].append(float(sds[j]))
                s_d = float(np.nanmax(by_family["d"])) if by_family["d"] else 0.0
                s_g = float(np.nanmax(by_family["g"])) if by_family["g"] else 0.0
                s_r = float(np.nanmax(by_family["r"])) if by_family["r"] else 0.0
            else:
                s_d = s_g = s_r = 0.0
            out[S.signature_key(cid, SIG_S_D)] = s_d
            out[S.signature_key(cid, SIG_S_G)] = s_g
            out[S.signature_key(cid, SIG_S_R)] = s_r
            out[S.signature_key(cid, S.SIG_S_MAX)] = float(max(s_d, s_g, s_r))
        return out

    return fn
S.make_signature_fn = make_signature_fn


def signature_frame(point: pd.Series, constraint_ids: list[str],
                    u_build: list[str], include_diagnostic: bool = False) -> pd.DataFrame:
    comps = list(S.signature_components(u_build))
    if include_diagnostic:
        comps += list(WORDING_DIAGNOSTIC)
    return pd.DataFrame(
        [[point.get(S.signature_key(c, k), np.nan) for k in comps]
         for c in constraint_ids], index=constraint_ids, columns=comps)
S.signature_frame = signature_frame


def draws_to_frames(draws: pd.DataFrame, constraint_ids: list[str],
                    u_build: list[str]) -> np.ndarray:
    comps = S.signature_components(u_build)
    cols = [S.signature_key(c, k) for c in constraint_ids for k in comps]
    return draws[cols].to_numpy(dtype=float).reshape(
        len(draws), len(constraint_ids), len(comps))
S.draws_to_frames = draws_to_frames


# =============================== sensitivity: per rotation, per order, pooled
def _ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta






def slope_families() -> tuple[str, ...]:
    """Predictor families, which follow the signature actually in use.

    kappa is a predictor only when it is a matched signature component. Under
    the primary_total estimand it is audited rather than matched, so it is not
    a column here and the design matrix has one fewer coordinate. v14 hard-coded
    the tuple, which silently mismatched the matrix when the role changed.
    """
    fams = ["d", "g", "r"]
    if S.CFG.coupling_role == "matched":
        fams.append("kappa")
    fams.append("s")
    return tuple(fams)


SLOPE_FAMILIES = slope_families()

# Every rotation's design diagnostics, used or not, land here and are
# written to sensitivity_diagnostics.csv.
S.SENSITIVITY_DIAGNOSTICS: list[dict[str, Any]] = []


def _slope_block(sig: pd.DataFrame, pool: list[str], held_out: str,
                 others: list[str], order: str) -> tuple[np.ndarray, np.ndarray]:
    col = {c: j for j, c in enumerate(sig.columns)}
    M = sig.loc[pool].to_numpy(dtype=float)
    pairs = np.array(list(itertools.combinations(range(len(pool)), 2)))
    if len(pairs) == 0:
        return np.zeros((0, len(SLOPE_FAMILIES))), np.zeros(0)
    a, b = pairs[:, 0], pairs[:, 1]
    y = M[a, col[f"g|{held_out}|{order}"]] - M[b, col[f"g|{held_out}|{order}"]]
    g_cols = [col[f"g|{u}|{order}"] for u in others]
    r_cols = [col[f"r|{u}|{order}"] for u in others]
    s_cols = [col[c] for c in S.WORDING_MATCHED]
    with np.errstate(invalid="ignore"):
        columns = [
            M[a, col[S.SIG_DIFFICULTY]] - M[b, col[S.SIG_DIFFICULTY]],
            np.nanmean(M[np.ix_(a, g_cols)] - M[np.ix_(b, g_cols)], axis=1),
            np.nanmean(M[np.ix_(a, r_cols)] - M[np.ix_(b, r_cols)], axis=1)]
        if "kappa" in SLOPE_FAMILIES:
            columns.append(M[a, col[S.SIG_COUPLING]] - M[b, col[S.SIG_COUPLING]])
        # Wording instability, SIGNED (v15.1). Pre-repair this column was
        # nanmax(|Δs|), a non-negative predictor regressed on a signed outcome y.
        # That destroyed the design's antisymmetry: swapping the two constraints
        # in a pair flips y and every other predictor, but left this one
        # unchanged, so the fitted slope depended on an arbitrary ordering of
        # itertools.combinations. The repair keeps the same MAGNITUDE -- the
        # largest coordinate difference -- and restores its sign, so swapping a
        # and b negates the whole row and the slope is invariant.
        _s_diff = M[np.ix_(a, s_cols)] - M[np.ix_(b, s_cols)]
        _dominant = np.nanargmax(np.abs(np.nan_to_num(_s_diff, nan=-np.inf)), axis=1)
        columns.append(_s_diff[np.arange(_s_diff.shape[0]), _dominant])
        X = np.column_stack(columns)
    keep = np.isfinite(y) & np.isfinite(X).all(axis=1)
    return X[keep], y[keep]
S._slope_block = _slope_block


def design_diagnostics(X: np.ndarray, y: np.ndarray, n_constraints: int
                       ) -> dict[str, Any]:
    """Rank, conditioning and singular values of a sensitivity design matrix.

    A slope read off a rank-deficient or severely ill-conditioned design is not
    a measurement, and v14 read one without looking. Everything here is
    recorded whether or not the regression is used.
    """
    if X.size == 0:
        return {"n_pairs": 0, "n_independent_constraints": n_constraints,
                "n_predictors": X.shape[1] if X.ndim == 2 else 0,
                "rank": 0, "full_rank": False, "condition_number": float("inf"),
                "singular_values": [], "well_conditioned": False}
    design = np.column_stack([X, np.ones(len(X))])
    singular = np.linalg.svd(design, compute_uv=False)
    rank = int((singular > singular.max() * 1e-10).sum()) if singular.size else 0
    smallest = float(singular.min()) if singular.size else 0.0
    condition = float(singular.max() / smallest) if smallest > 0 else float("inf")
    return {"n_pairs": int(len(y)),
            "n_independent_constraints": int(n_constraints),
            "n_predictors": int(design.shape[1]),
            "rank": rank, "full_rank": bool(rank == design.shape[1]),
            "condition_number": condition,
            "singular_values": [round(float(v), 6) for v in singular],
            "well_conditioned": bool(condition <= S.CFG.max_condition_number)}


def complete_pool(sig: pd.DataFrame, exclude: Iterable[str] = ()) -> list[str]:
    """Constraints whose every signature component is measured.

    A slope cannot be estimated from a constraint with a missing predictor, and
    letting one undefined component empty the regression would turn a
    measurement gap into "no caliper can be derived".
    """
    excluded = set(exclude)
    return [c for c in sig.index
            if c not in excluded and np.isfinite(sig.loc[c].to_numpy(dtype=float)).all()]
S.complete_pool = complete_pool


def sensitivity_by_rotation(sig: pd.DataFrame, u_build: list[str],
                            exclude: Iterable[str] = ()) -> pd.DataFrame:
    """One slope vector per (held-out target, order).

    The pseudo-contrast predicted is a difference in outgoing burden on the
    held-out target, so the predictors must exclude anything measured on that
    same target: otherwise the coefficient on it is 1 by construction.
    """
    pool = S.complete_pool(sig, exclude)
    if len(pool) < S.CFG.min_constraints_for_sensitivity or len(u_build) < 2:
        return pd.DataFrame()
    rows = []
    for held_out in u_build:
        others = [u for u in u_build if u != held_out]
        for order in S.CFG.orders:
            X, y = S._slope_block(sig, pool, held_out, others, order)
            diag = design_diagnostics(X, y, len(pool))
            usable = bool(len(y) >= len(SLOPE_FAMILIES) + 2
                          and diag["full_rank"] and diag["well_conditioned"])
            row = {"held_out": held_out, "order": order, "n_pairs": len(y),
                   "usable": usable,
                   "excluded_reason": ("" if usable else
                                       "too few pairs" if len(y) < len(SLOPE_FAMILIES) + 2
                                       else "rank deficient" if not diag["full_rank"]
                                       else "ill conditioned"),
                   **{k: v for k, v in diag.items() if k != "singular_values"},
                   "singular_values": ";".join(
                       f"{v:.4g}" for v in diag["singular_values"])}
            if usable:
                beta = _ols(np.column_stack([X, np.ones(len(y))]), y)
                row.update({fam: float(beta[i]) for i, fam in enumerate(SLOPE_FAMILIES)})
            else:
                row.update({fam: float("nan") for fam in SLOPE_FAMILIES})
            rows.append(row)
    S.SENSITIVITY_DIAGNOSTICS.extend(rows)
    frame = pd.DataFrame(rows)
    return frame.query("usable") if len(frame) else frame
S.sensitivity_by_rotation = sensitivity_by_rotation


def sensitivity_slopes(sig: pd.DataFrame, u_build: list[str],
                       exclude: Iterable[str] = ()) -> dict[str, float]:
    """Pooled slopes with rotation intercepts. Retained as a comparison."""
    pool = S.complete_pool(sig, exclude)
    if len(pool) < S.CFG.min_constraints_for_sensitivity or len(u_build) < 2:
        return {}
    blocks_X, blocks_y, blocks_rot = [], [], []
    for rotation, held_out in enumerate(u_build):
        others = [u for u in u_build if u != held_out]
        for order in S.CFG.orders:
            X, y = S._slope_block(sig, pool, held_out, others, order)
            blocks_X.append(X)
            blocks_y.append(y)
            blocks_rot.append(np.full(len(y), rotation))
    X = np.vstack(blocks_X) if blocks_X else np.zeros((0, len(SLOPE_FAMILIES)))
    y = np.concatenate(blocks_y) if blocks_y else np.zeros(0)
    rot = np.concatenate(blocks_rot) if blocks_rot else np.zeros(0, dtype=int)
    if len(y) < len(SLOPE_FAMILIES) + len(u_build) + 2:
        return {}
    dummies = np.zeros((len(rot), len(u_build)))
    dummies[np.arange(len(rot)), rot] = 1.0
    design = np.hstack([X, dummies])
    singular = np.linalg.svd(design, compute_uv=False)
    if singular.size == 0 or singular.min() <= 0:
        return {}
    if int((singular > singular.max() * 1e-10).sum()) < design.shape[1]:
        return {}                      # rank deficient: not a measurement
    if float(singular.max() / singular.min()) > S.CFG.max_condition_number:
        return {}                      # ill conditioned: not a measurement
    beta = _ols(design, y)
    return {fam: float(beta[i]) for i, fam in enumerate(SLOPE_FAMILIES)}
S.sensitivity_slopes = sensitivity_slopes


def slope_jackknife(sig: pd.DataFrame, u_build: list[str],
                    exclude: Iterable[str] = ()) -> pd.Series:
    """Leave-one-constraint-out standard error for the pooled slopes.

    Pairwise differences that share a constraint are not independent, so a
    naive standard error over pairs understates uncertainty. Dropping one
    constraint at a time removes every pair it appears in at once.
    """
    pool = S.complete_pool(sig, exclude)
    full = S.sensitivity_slopes(sig, u_build, exclude)
    # NaN, not zero. v14 returned 0.0 when the jackknife could not be computed,
    # which is the most dangerous possible answer: it says the slope is known
    # exactly, and a slope known exactly produces the widest caliper the point
    # estimate allows. Unavailable uncertainty is unavailable.
    if not full or len(pool) < S.CFG.min_constraints_for_jackknife:
        return pd.Series(float("nan"), index=list(SLOPE_FAMILIES))
    estimates = []
    for dropped in pool:
        partial = S.sensitivity_slopes(sig, u_build, list(exclude) + [dropped])
        if partial:
            estimates.append([partial[f] for f in SLOPE_FAMILIES])
    if len(estimates) < 3:
        return pd.Series(float("nan"), index=list(SLOPE_FAMILIES))
    arr = np.asarray(estimates, dtype=float)
    n = len(arr)
    se = np.sqrt((n - 1) / n * np.sum((arr - arr.mean(axis=0)) ** 2, axis=0))
    return pd.Series(se, index=list(SLOPE_FAMILIES))
S.slope_jackknife = slope_jackknife


def derive_calipers(sig: pd.DataFrame, sig_draws: np.ndarray,
                    constraint_ids: list[str], u_build: list[str],
                    exclude: Iterable[str] = ()
                    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """delta_r = SESOI / conservative upper sensitivity, per family.

    The upper sensitivity is the largest across rotations and orders unless the
    spread is demonstrably small, plus a one-sided allowance for slope
    uncertainty taken as the larger of the task bootstrap and the
    leave-one-constraint-out jackknife. Pool spread is not an input anywhere.
    """
    by_rotation = S.sensitivity_by_rotation(sig, u_build, exclude)
    pooled = S.sensitivity_slopes(sig, u_build, exclude)
    if by_rotation.empty or not pooled:
        raise SensitivityNotEstimable(
            f"the sensitivity regression is not estimable: "
            f"{len(S.complete_pool(sig, exclude))} constraints have a complete "
            "signature, against the minimum of 3. Pool spread is not an "
            "acceptable substitute.")

    reps = min(len(sig_draws), 200)
    comps = S.signature_components(u_build)
    boot = []
    for i in range(reps):
        frame = pd.DataFrame(sig_draws[i], index=constraint_ids, columns=comps)
        slopes = S.sensitivity_slopes(frame, u_build, exclude)
        if slopes:
            boot.append([slopes[f] for f in SLOPE_FAMILIES])
    boot_se = (pd.DataFrame(boot, columns=list(SLOPE_FAMILIES)).std(ddof=1)
               if len(boot) > 2 else pd.Series(float("nan"), index=list(SLOPE_FAMILIES)))
    jack_se = S.slope_jackknife(sig, u_build, exclude)
    slope_se = pd.concat([boot_se, jack_se], axis=1).max(axis=1)
    # Where neither estimator produced a standard error, the fallback is the
    # prespecified conservative allowance, which is larger than any slope SE the
    # design has ever produced. It is recorded as a fallback, never as a
    # measurement, and it can only narrow a caliper.
    slope_se_source = pd.Series(
        np.where(slope_se.notna(), "estimated", "conservative_fallback"),
        index=slope_se.index)
    slope_se = slope_se.fillna(S.CFG.slope_se_conservative_fallback)

    rows, hetero_rows = [], []
    family_slope: dict[str, dict[str, float]] = {}
    for fam in SLOPE_FAMILIES:
        values = by_rotation[fam].abs()
        largest = float(values.max())
        smallest = float(values.min())
        spread = (largest - smallest) / largest if largest > 0 else 0.0
        pooled_abs = abs(pooled.get(fam, 0.0))
        homogeneous = spread <= S.CFG.slope_pooling_max_relative_spread
        # Conservative: pooling is used only when the rotations agree. When they
        # do not, the largest sensitivity governs, so a pooled average can never
        # produce a caliper wider than the one a clearly more sensitive
        # component implies.
        chosen = pooled_abs if homogeneous else max(largest, pooled_abs)
        family_slope[fam] = {"pooled": pooled_abs, "max_rotation": largest,
                             "min_rotation": smallest, "relative_spread": spread,
                             "homogeneous": homogeneous, "chosen": chosen,
                             "se": float(slope_se.get(fam, S.CFG.slope_se_conservative_fallback)),
                             "se_source": str(slope_se_source.get(fam, "unknown"))}
        hetero_rows.append({"family": fam, **family_slope[fam]})

    for comp in comps:
        fam = S.component_family(comp)
        info = family_slope[fam]
        effective = max(info["chosen"] + S.CFG.caliper_slope_q * info["se"],
                        S.CFG.caliper_slope_floor)
        delta = min(S.CFG.sesoi_risk_difference / effective, S.CFG.caliper_absolute_ceiling)
        rows.append({"component": comp, "family": fam,
                     "slope_pooled": info["pooled"],
                     "slope_max_rotation": info["max_rotation"],
                     "slope_relative_spread": info["relative_spread"],
                     "pooling_justified": info["homogeneous"],
                     "slope_se": info["se"], "slope_used": effective,
                     "caliper": float(delta),
                     "bound_by": ("slope floor" if effective == S.CFG.caliper_slope_floor
                                  else "sensitivity"),
                     "capped": bool(S.CFG.sesoi_risk_difference / effective
                                    > S.CFG.caliper_absolute_ceiling)})
    return (indexed_frame(rows, "component"),
            pd.DataFrame(hetero_rows).set_index("family"),
            by_rotation)
S.derive_calipers = derive_calipers


# ================================================ uncertainty-aware admission
def mismatch_table(sig: pd.DataFrame, draws: np.ndarray, constraint_ids: list[str],
                   u_build: list[str], focal: str,
                   coupling_se: Optional[pd.Series] = None
                   ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """|z_focal - z_C| and its standard error, for every candidate.

    Coupling is measured on the response bank rather than on tasks, so its
    uncertainty does not appear in the task bootstrap and is combined in
    explicitly. v13 treated it as exact, which made an unmeasurable coupling
    look like a perfect match.
    """
    comps = S.signature_components(u_build)
    f = constraint_ids.index(focal)
    gaps, ses = {}, {}
    for i, cid in enumerate(constraint_ids):
        if cid == focal:
            continue
        diff = sig.loc[focal] - sig.loc[cid]
        gaps[cid] = diff.abs()
        se = pd.Series(np.nanstd(draws[:, f, :] - draws[:, i, :], axis=0, ddof=1),
                       index=comps)
        if coupling_se is not None and S.SIG_COUPLING in se.index:
            a = float(coupling_se.get(focal, np.nan))
            b = float(coupling_se.get(cid, np.nan))
            combined = math.sqrt(np.nansum([a**2, b**2])) if np.isfinite([a, b]).any() else np.nan
            se[S.SIG_COUPLING] = combined
        ses[cid] = se
    return pd.DataFrame(gaps).T, pd.DataFrame(ses).T
S.mismatch_table = mismatch_table


def contender_distance(gaps: pd.DataFrame, calipers: pd.DataFrame,
                       candidate_ids: Iterable[str]) -> pd.Series:
    """Largest gap/caliper ratio over components, per candidate.

    The buffer multiple a candidate would need before it counted as a contender.
    Reported when the contender set is empty so that "no near match exists" is
    an inspectable quantity rather than a bare verdict.
    """
    out = {}
    for cid in candidate_ids:
        if cid not in gaps.index:
            continue
        ratios = [float(gaps.at[cid, c]) / float(calipers.at[c, "caliper"])
                  for c in calipers.index
                  if np.isfinite(gaps.at[cid, c]) and float(calipers.at[c, "caliper"]) > 0]
        out[cid] = float(max(ratios)) if ratios else float("nan")
    return pd.Series(out, dtype=float).sort_values()
S.contender_distance = contender_distance


def contender_set(gaps: pd.DataFrame, calipers: pd.DataFrame,
                  buffer_multiple: float, candidate_ids: Iterable[str]) -> list[str]:
    """Candidates that could plausibly enter the final panel.

    Precision must protect these, not the pool median: a precise median can sit
    beside a highly uncertain candidate that the selection would then admit.
    """
    distance = S.contender_distance(gaps, calipers, candidate_ids)
    return sorted(distance.index[distance <= buffer_multiple].tolist())
S.contender_set = contender_set


def precision_report(gap_se: pd.DataFrame, calipers: pd.DataFrame, n_clusters: int,
                     contenders: Iterable[str]) -> pd.DataFrame:
    """Is calibration precise enough to resolve the caliper for the contenders?

    Never widens anything. The requirement is stated in task CLUSTERS, because
    uncertainty comes from a cluster bootstrap: adding wordings or seeds inside
    the same tasks leaves the between-task component untouched. The cluster
    count is a PLANNING ESTIMATE under 1/sqrt(n) scaling, not a guarantee.
    """
    contenders = [c for c in contenders if c in gap_se.index]
    rows = []
    for comp in calipers.index:
        delta = float(calipers.at[comp, "caliper"])
        budget = S.CFG.caliper_precision_fraction * delta
        if contenders and comp in gap_se.columns:
            se_values = gap_se.loc[contenders, comp].astype(float)
            worst = float(np.nanmax(se_values)) if len(se_values) else np.nan
            worst_id = (str(se_values.idxmax()) if len(se_values.dropna()) else "")
        else:
            worst, worst_id = np.nan, ""
        consumed = S.CFG.caliper_uncertainty_q * worst
        ok = bool(np.isfinite(consumed) and consumed <= budget)
        required = (n_clusters * (consumed / budget) ** 2
                    if np.isfinite(consumed) and budget > 0 else np.nan)
        rows.append({"component": comp, "caliper": delta,
                     "worst_contender": worst_id, "worst_gap_se": worst,
                     "q_times_se": consumed, "permitted": budget,
                     "precision_ok": ok, "clusters_now": n_clusters,
                     "clusters_required_planning_estimate":
                         float(np.ceil(required)) if np.isfinite(required) else np.nan})
    return indexed_frame(rows, "component")
S.precision_report = precision_report


def reference_error_certificate(gaps: pd.DataFrame, gap_se: pd.DataFrame,
                                calipers: pd.DataFrame,
                                candidate_ids: Iterable[str]) -> pd.DataFrame:
    """A conservative upper bound on the ACCUMULATED reference mismatch.

    Componentwise calipers bound each coordinate separately. They do not bound
    the total, so the certificate bounds the accumulation:

        B_C = sum_families  s_family^U * ( aggregated |mismatch| + q * SE )
              <=  epsilon_ref

    v15.1 CORRECTED THE UNIT. Pre-repair this summed one contribution per
    COMPONENT while reusing the FAMILY slope for each, but `_slope_block` fits the
    g and r slopes against the MEAN across those families. A slope fitted on a
    mean and charged once per member over-counts by about the family size: six g
    components each off by 0.02 with s_g = 0.5 predicts 0.01 of burden difference
    and was charged 0.06, against a 0.05 budget. The effect was an over-strict
    rule that rejects defensible references and drives the panel toward
    near-twins -- not a lax one. See dci.analysis.reference_error.

    Three things remain assumptions rather than measurements:

      1. ADDITIVITY. Families are summed. The sensitivity regression estimates
         them jointly, so this is a first-order approximation whose error is not
         measured.
      2. NO CANCELLATION. Absolute magnitudes are aggregated, so mismatches that
         would partly offset are counted as though they compound. This is
         deliberately conservative and cannot be relaxed using candidate-pool
         covariance, which would let the pool decide the scientific budget.
         `reference_budget_aggregation="rss"` is a separate declared choice about
         CROSS-FAMILY accumulation and was never a fix for the unit error.
      3. THE NUMBER. epsilon_ref = 0.05 against a 0.10 SESOI. The source
         methodology states exactly that reservation -- half the SESOI -- but
         for the pseudo-focal held-out prediction error, a different quantity.
         Reusing it here is a v15 decision, unchanged in v15.1.
    """
    return family_level_certificate(
        gaps, gap_se, calipers, candidate_ids,
        uncertainty_q=S.CFG.caliper_uncertainty_q,
        epsilon_ref=S.CFG.epsilon_ref,
        aggregation_mode=S.CFG.reference_budget_aggregation,
        indexed_frame=indexed_frame)
S.reference_error_certificate = reference_error_certificate


def coupling_audit_table(candidate_ids: Iterable[str]) -> pd.DataFrame:
    """The declared |kappa_C - kappa_B| audit, with candidate-level support.

    Support is demanded of candidates on exactly the terms that decide whether
    the FOCAL estimate is usable (`min_informative_coupling_probes`,
    `max_coupling_se`). An unmeasurable candidate has not passed the audit; it has
    failed to take it, and those are not the same thing.
    """
    return coupling_audit(
        S.COUPLING, S.COUPLING_SE, S.COUPLING_N_INFORMATIVE, S.CFG.focal_id,
        candidate_ids, max_gap=S.CFG.coupling_audit_max,
        min_probes=S.CFG.min_informative_coupling_probes,
        max_se=S.CFG.max_coupling_se,
        uncertainty_q=S.CFG.caliper_uncertainty_q,
        indexed_frame=indexed_frame)
S.coupling_audit_table = coupling_audit_table


def admit_candidates(gaps: pd.DataFrame, gap_se: pd.DataFrame,
                     calipers: pd.DataFrame, focal_scope: str,
                     candidate_ids: Iterable[str],
                     scopes: Optional[dict[str, str]] = None,
                     coupling_audit_frame: Optional[pd.DataFrame] = None
                     ) -> pd.DataFrame:
    """|z_focal - z_C| + q*SE <= delta, componentwise, plus the exact scope match.

    Both orders are covered automatically, because the order-specific g and r
    components are separate rows of the caliper table.
    """
    scope_of = scopes if scopes is not None else {
        c: s.generative_scope for c, s in S.CONSTRAINTS.items()}
    rows = []
    for cid in candidate_ids:
        if cid not in gaps.index:
            continue
        reasons = []
        if scope_of[cid] != focal_scope:
            reasons.append("scope mismatch (exact-match restriction)")
        detail = {}
        for comp in calipers.index:
            delta = float(calipers.at[comp, "caliper"])
            gap = float(gaps.at[cid, comp])
            se = float(gap_se.at[cid, comp]) if comp in gap_se.columns else 0.0
            se = 0.0 if not np.isfinite(se) else se
            adjusted = gap + S.CFG.caliper_uncertainty_q * se
            detail[f"adj_{comp}"] = adjusted
            if not np.isfinite(gap):
                reasons.append(f"{comp} undefined")
            elif adjusted > delta:
                reasons.append(f"{comp} {adjusted:.3f} > {delta:.3f}")
        componentwise_failed = len([r for r in reasons if not r.startswith("scope")])
        rows.append({"constraint_id": cid, "scope": scope_of[cid],
                     "origin": (S.CONSTRAINTS[cid].origin if cid in S.CONSTRAINTS else "fixture"),
                     "n_failed_components": componentwise_failed,
                     "componentwise_ok": not reasons,
                     "rejection_reasons": "; ".join(reasons[:6]), **detail})

    frame = indexed_frame(rows, "constraint_id",
                          ["constraint_id", "scope", "origin",
                           "n_failed_components", "componentwise_ok",
                           "rejection_reasons",
                           *[f"adj_{c}" for c in calipers.index]])
    if not len(frame):
        frame["budget_total"] = pd.Series(dtype=float)
        frame["budget_ok"] = pd.Series(dtype=bool)
        frame["binding_criterion"] = pd.Series(dtype=object)
        frame["eligible"] = pd.Series(dtype=bool)
        return frame

    # The joint certificate is an ADDITIONAL requirement. It can only remove
    # candidates, never admit one the componentwise rule rejected.
    if S.CFG.enforce_reference_budget and "slope_used" in calipers.columns:
        cert = S.reference_error_certificate(gaps, gap_se, calipers, frame.index)
        frame["budget_total"] = cert["budget_total"].reindex(frame.index)
        frame["budget_ok"] = cert["budget_ok"].reindex(frame.index).fillna(False)
        # v15.1: the binding unit is a FAMILY, not a component.
        frame["largest_family"] = cert["largest_family"].reindex(frame.index)
    else:
        frame["budget_total"] = np.nan
        frame["budget_ok"] = True
        frame["largest_family"] = ""

    # ------------------------------------------- the declared coupling audit
    # v15.1. Under `primary_total`, kappa is NOT a matched coordinate -- it is an
    # ELIGIBILITY AUDIT, exactly as ESTIMAND_DEFINITIONS says. Pre-repair the
    # tolerance was declared, printed to the operator as "a hard
    # measurement-coupling audit", and consumed by nothing, so the executed
    # reference definition differed from the declared one. Under `kappa_matched`
    # kappa is a caliper component instead and the audit does not apply, because
    # applying both would impose the narrower rule twice.
    if S.CFG.coupling_role == "audit" and S.COUPLING is not None:
        audit = (coupling_audit_frame if coupling_audit_frame is not None
                 else S.coupling_audit_table(frame.index))
        frame["kappa"] = audit["kappa"].reindex(frame.index)
        frame["coupling_gap_adjusted"] = audit["adjusted_gap"].reindex(frame.index)
        # Absent coupling data fails the audit: unmeasurable is not matched. The
        # sole exception is an explicitly marked FIXTURE frame (see
        # coupling_audit.passthrough_audit), which Gate 0 uses for synthetic ids.
        _fill = bool(audit.attrs.get("passthrough_fixture", False))
        frame["coupling_audit_ok"] = (
            audit["coupling_audit_ok"].reindex(frame.index).fillna(_fill))
        _why = audit["coupling_audit_reason"].reindex(frame.index).fillna("")
        _add = frame["coupling_audit_ok"].astype(bool).eq(False) & _why.ne("")
        frame.loc[_add, "rejection_reasons"] = (
            frame.loc[_add, "rejection_reasons"].where(
                frame.loc[_add, "rejection_reasons"].eq(""),
                frame.loc[_add, "rejection_reasons"] + "; ") + _why[_add])
    else:
        frame["kappa"] = np.nan
        frame["coupling_gap_adjusted"] = np.nan
        frame["coupling_audit_ok"] = True

    frame["eligible"] = (frame["componentwise_ok"] & frame["budget_ok"]
                         & frame["coupling_audit_ok"].astype(bool))
    frame["binding_criterion"] = np.where(
        frame["eligible"], "none",
        np.where(~frame["componentwise_ok"],
                 np.where(~frame["budget_ok"], "both", "componentwise"),
                 "joint_budget"))
    frame.loc[~frame["budget_ok"] & frame["componentwise_ok"], "rejection_reasons"] = (
        "joint reference-error certificate "
        + frame.loc[~frame["budget_ok"] & frame["componentwise_ok"],
                    "budget_total"].round(4).astype(str)
        + f" > {S.CFG.epsilon_ref}")
    return frame
S.admit_candidates = admit_candidates


# ==================================================== deterministic selection
def regularised_mahalanobis(sig: pd.DataFrame, focal: str, pool: list[str],
                            ridge: float) -> pd.Series:
    """Ranking only, after every hard caliper has already been applied."""
    block = sig.loc[pool + [focal]].astype(float)
    block = block.loc[:, block.notna().all(axis=0)]
    if block.shape[1] == 0 or len(pool) < 2:
        return pd.Series(np.nan, index=pool)
    cov = np.atleast_2d(np.cov(block.to_numpy(), rowvar=False))
    reg = cov + ridge * np.diag(np.maximum(np.diag(cov), 1e-8)) + 1e-9 * np.eye(len(cov))
    inv = np.linalg.pinv(reg)
    target = block.loc[focal].to_numpy()
    return pd.Series({cid: float(np.sqrt(max(
        (block.loc[cid].to_numpy() - target) @ inv @ (block.loc[cid].to_numpy() - target),
        0.0))) for cid in pool})
S.regularised_mahalanobis = regularised_mahalanobis


def select_panel(eligible: list[str], sig: pd.DataFrame, focal: str, k: int,
                 ridge: float) -> tuple[list[str], pd.Series]:
    """Exactly k, chosen deterministically. Fewer than k is not identified."""
    if len(eligible) < k:
        raise StudyStop(
            GateOutcome("2_feasibility", GateStatus.NOT_IDENTIFIED_SUPPORT,
                        f"{len(eligible)} candidates passed every caliper in "
                        f"both orders; the estimand named exactly {k}",
                        quantities={"n_eligible": len(eligible)},
                        thresholds={"required": k},
                        more_data_could_resolve=False,
                        new_protocol_version_required=True),
            f"{len(eligible)} admissible references; exactly {k} are required.")
    distances = S.regularised_mahalanobis(sig, focal, eligible, ridge)
    ranked = sorted(eligible, key=lambda c: (float(distances[c]), c))
    return ranked[:k], distances
S.select_panel = select_panel


# ============================================ reference prediction and weights
def predict_burden(sig: pd.DataFrame, donors: list[str], targets: list[str],
                   weights: Optional[pd.Series] = None) -> dict[str, float]:
    out = {}
    for u in targets:
        for o in S.CFG.orders:
            comp = f"g|{u}|{o}"
            if comp not in sig.columns:
                continue
            values = np.array([sig.at[c, comp] for c in donors], dtype=float)
            if weights is None:
                out[comp] = float(np.nanmean(values))
            else:
                w = np.array([float(weights[c]) for c in donors])
                out[comp] = float(np.nansum(w * values) / max(np.nansum(w), 1e-12))
    return out


def fit_stochastic_weights(sig: pd.DataFrame, donors: list[str], focal: str,
                           components: list[str],
                           distances: Optional[pd.Series] = None) -> pd.Series:
    """Weights on the concatenated signature across BOTH orders at once.

    A penalty on individual donor distance is included, because aggregate
    balance can otherwise be bought from individually distant donors: a
    half-and-half mixture of (0,100) and (100,0) matches (50,50) exactly while
    neither donor resembles the focal constraint at all.
    """
    from scipy.optimize import minimize

    Z = sig.loc[donors, components].to_numpy(dtype=float)
    target = sig.loc[focal, components].to_numpy(dtype=float)
    good = np.all(np.isfinite(Z), axis=0) & np.isfinite(target)
    Z, target = Z[:, good], target[good]
    n = len(donors)
    d2 = (np.array([float(distances.get(c, 0.0)) for c in donors]) ** 2
          if distances is not None else np.zeros(n))
    x0 = np.full(n, 1.0 / n)

    def objective(w):
        return float(np.sum((w @ Z - target) ** 2)
                     + S.CFG.synthetic_distance_penalty * float(np.dot(w, d2)))

    result = minimize(objective, x0, method="SLSQP",
                      bounds=[(0.0, S.CFG.max_single_weight)] * n,
                      constraints=[{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}],
                      options={"maxiter": 500, "ftol": 1e-12})
    w = np.clip(result.x, 0.0, S.CFG.max_single_weight)
    w = w / w.sum() if w.sum() > 0 else x0
    return pd.Series(w, index=donors)
S.fit_stochastic_weights = fit_stochastic_weights


def j_effective(weights: pd.Series) -> float:
    return float(1.0 / np.sum(np.asarray(weights, dtype=float) ** 2))
S.j_effective = j_effective


# ============================================ hard eligibility, B-independent
def verifier_agreement(a: str, b: str,
                       corpus: Optional[list[str]] = None) -> tuple[float, int]:
    """Agreement between two verifiers over INFORMATIVE probe responses.

    Restricted to responses that at least one of the two accepts. Two hard
    constraints that both reject every probe agree on 100% of it and are not
    thereby duplicates; scoring them as such would delete most of the candidate
    pool for a reason that has nothing to do with duplication.

    Returns the agreement and the number of informative responses, so an
    undetermined comparison is visible rather than silently counted as zero.
    """
    corpus = S.SYNTHETIC_CORPUS if corpus is None else corpus
    va = np.array([S.verify(t, a).binary_pass for t in corpus])
    vb = np.array([S.verify(t, b).binary_pass for t in corpus])
    informative = (va == 1) | (vb == 1)
    n = int(informative.sum())
    if n < 5:
        return float("nan"), n
    return float(np.mean(va[informative] == vb[informative])), n


def hard_eligible_universe(candidate_ids: Iterable[str],
                           sig: Optional[pd.DataFrame] = None,
                           sig_draws: Optional[np.ndarray] = None,
                           calipers: Optional[pd.DataFrame] = None,
                           valid_verifiers: Optional[set[str]] = None,
                           scope: Optional[str] = None) -> pd.DataFrame:
    """Eligibility criteria that never mention resemblance to the focal constraint.

    This is the universe the pseudo-focal cohort and its donors are drawn from.
    v13 drew both from B's own eligible neighbourhood, which asked whether
    constraints resembling B predict one another.
    """
    scope = scope or S.CONSTRAINTS[S.CFG.target_id].generative_scope
    valid_verifiers = valid_verifiers if valid_verifiers is not None else set(S.CONSTRAINTS)
    protected = {S.CFG.target_id, S.CFG.focal_id, "B_SOFT"}
    kept: list[str] = []
    rows = []
    for cid in sorted(candidate_ids):
        s = S.CONSTRAINTS[cid]
        reasons = []
        if cid in protected:
            reasons.append("is the target or the focal constraint")
        if S.CFG.target_id in s.incompatible_with or S.CFG.focal_id in s.incompatible_with:
            reasons.append("declared logically incompatible with A or B")
        if set(s.entails) & {S.CFG.target_id, S.CFG.focal_id}:
            reasons.append("declared to entail A or B")
        if S.CONSTRAINTS[S.CFG.target_id].entails and cid in S.CONSTRAINTS[S.CFG.target_id].entails:
            reasons.append("entailed by A")
        if s.generative_scope != scope:
            reasons.append(f"generative scope is {s.generative_scope}, not {scope}")
        if cid not in valid_verifiers:
            reasons.append("verifier validity not established at Gate M")
        dup_a, n_a = verifier_agreement(cid, S.CFG.target_id)
        dup_b, n_b = verifier_agreement(cid, S.CFG.focal_id)
        if np.isfinite(dup_a) and dup_a >= S.CFG.duplicate_agreement_threshold:
            reasons.append(f"verifier agrees with A on {dup_a:.3f} of {n_a} "
                           "informative probes")
        if np.isfinite(dup_b) and dup_b >= S.CFG.duplicate_agreement_threshold:
            reasons.append(f"verifier agrees with B on {dup_b:.3f} of {n_b} "
                           "informative probes")
        dup_peer = ""
        for other in kept:
            agreement, n_peer = verifier_agreement(cid, other)
            if np.isfinite(agreement) and agreement >= S.CFG.duplicate_agreement_threshold:
                dup_peer = other
                reasons.append(f"duplicates {other} on {agreement:.3f} of "
                               f"{n_peer} informative probes")
                break
        measurable = True
        imprecise = []
        if sig is not None and cid in sig.index:
            measurable = bool(np.isfinite(sig.loc[cid].to_numpy(dtype=float)).all())
            if not measurable:
                reasons.append("calibration signature has undefined components")
        if (sig_draws is not None and calipers is not None and sig is not None
                and cid in sig.index):
            i = list(sig.index).index(cid)
            own_se = pd.Series(np.nanstd(sig_draws[:, i, :], axis=0, ddof=1),
                               index=list(sig.columns))
            for comp in calipers.index:
                budget = S.CFG.caliper_precision_fraction * float(calipers.at[comp, "caliper"])
                if np.isfinite(own_se.get(comp, np.nan)) and \
                        S.CFG.caliper_uncertainty_q * float(own_se[comp]) > budget:
                    imprecise.append(comp)
            if imprecise:
                reasons.append(f"own measurement too imprecise on {len(imprecise)} components")
        if not reasons:
            kept.append(cid)
        rows.append({"constraint_id": cid, "agreement_with_A": dup_a,
                     "informative_probes_vs_A": n_a,
                     "agreement_with_B": dup_b, "duplicate_of": dup_peer,
                     "measurable": measurable, "n_imprecise_components": len(imprecise),
                     "hard_eligible": not reasons,
                     "rejection_reasons": "; ".join(reasons[:5])})
    return indexed_frame(rows, "constraint_id",
                         ["constraint_id", "agreement_with_A",
                          "informative_probes_vs_A", "agreement_with_B",
                          "duplicate_of", "measurable", "n_imprecise_components",
                          "hard_eligible", "rejection_reasons"])
S.hard_eligible_universe = hard_eligible_universe


print("Reference-model machinery defined.")
print(f"signature components at |U_build| = {S.CFG.u_per_split}: "
      f"{len(S.signature_components(['u1', 'u2', 'u3']))}  "
      f"(wording matched on {S.WORDING_MATCHED}, {WORDING_DIAGNOSTIC} reported)")
print(f"feature roles hash: {S.FEATURE_ROLES_SHA256[:16]}")


# ======================================= authorization and discrepancy helpers
def authorize_primary(g1_passed: bool, g0_passed: bool = False,
                      g2_passed: bool = False) -> bool:
    """Only g1 authorizes the primary confirmatory experiment.

    The declared primary estimand uses the six individually admissible g1
    references, so nothing else can stand in for them. g0 is a benchmark and
    falsification comparator; g2 is a separate secondary estimand. v13 tuned
    across all three and let the winner authorize, which is how a notebook
    validates an estimand it is not going to report.
    """
    return bool(g1_passed)
S.authorize_primary = authorize_primary


def stochastic_estimand_authorized(g1_passed: bool, g2_passed: bool) -> bool:
    """The stochastic secondary needs its own validation AND a valid primary."""
    return bool(g1_passed and g2_passed)
S.stochastic_estimand_authorized = stochastic_estimand_authorized


def burden_components(u_targets: Iterable[str]) -> list[str]:
    return [f"g|{u}|{o}" for u in u_targets for o in S.CFG.orders]
S.burden_components = burden_components


def discrepancy_frames(point: pd.Series, draws: pd.DataFrame, focal: str,
                       references: Iterable[str], components: Iterable[str]
                       ) -> tuple[pd.Series, pd.DataFrame]:
    """Per-reference held-out discrepancies, one column per (reference, component).

    A linear function of the signature draws, so the joint uncertainty is
    already correct and no second bootstrap is needed. Keeping the reference
    index means a panel average can never conceal two references cancelling.
    """
    p: dict[str, float] = {}
    d: dict[str, np.ndarray] = {}
    for j in references:
        for c in components:
            fk, jk = S.signature_key(focal, c), S.signature_key(j, c)
            if fk not in point.index or jk not in point.index:
                continue
            key = f"{j}|{c}"
            p[key] = float(point[fk] - point[jk])
            d[key] = (draws[fk] - draws[jk]).to_numpy()
    return pd.Series(p, dtype=float), pd.DataFrame(d)
S.discrepancy_frames = discrepancy_frames


def panel_residual_frames(point: pd.Series, draws: pd.DataFrame, focal: str,
                          references: list[str], components: Iterable[str],
                          weights: Optional[pd.Series] = None
                          ) -> tuple[pd.Series, pd.DataFrame]:
    """The pooled panel residual. A secondary diagnostic, never the gate."""
    w = (np.full(len(references), 1.0 / len(references)) if weights is None
         else np.array([float(weights[j]) for j in references]))
    p: dict[str, float] = {}
    d: dict[str, np.ndarray] = {}
    for c in components:
        fk = S.signature_key(focal, c)
        if fk not in point.index:
            continue
        ref_point = sum(wi * float(point[S.signature_key(j, c)])
                        for wi, j in zip(w, references))
        ref_draws = sum(wi * draws[S.signature_key(j, c)].to_numpy()
                        for wi, j in zip(w, references))
        p[c] = float(point[fk]) - ref_point
        d[c] = draws[fk].to_numpy() - ref_draws
    return pd.Series(p, dtype=float), pd.DataFrame(d)
S.panel_residual_frames = panel_residual_frames


def evaluate_pseudo_focal_cohort(evaluable: Iterable[str],
                                 minimum: int) -> tuple[list[str], str]:
    """Too few evaluable pseudo-focals is NOT_EVALUABLE, never a quiet pass.

    A panel of exactly six for B says nothing about how many constraints can
    themselves be given six donors from the independent universe, so the two
    must not be confused: this returns its own status.
    """
    cohort = sorted(evaluable)
    if len(cohort) < minimum:
        return cohort, GateStatus.REFERENCE_VALIDATION_NOT_EVALUABLE
    return cohort, GateStatus.PASS
S.evaluate_pseudo_focal_cohort = evaluate_pseudo_focal_cohort
