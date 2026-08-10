"""Stage 272 — migrated from notebook cell 272.py (calibration_and_calipers).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/272.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import bootstrap_functional  # noqa: F401
from dci.exceptions import SensitivityNotEstimable  # noqa: F401
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

# Both dataflows must be measured on the same calibration data: the primary
# pool because it may enter the panel, and the whole declared-eligible universe
# because the pseudo-focal validation is drawn from it and may not inherit a
# B-relative filter. The prescreen therefore narrows ADMISSION, not calibration,
# and the compute it saves is smaller than v14 assumed. The budget cell reports
# the difference rather than hiding it.
S.MEASURED_IDS = [S.CFG.focal_id, *sorted(set(S.PRESCREEN_KEPT) | set(S.DECLARED_ELIGIBLE))]
S.declare_lineage("MEASURED_IDS", parents=["DECLARED_ELIGIBLE"])
S.SIG_REPS = min(S.CFG.bootstrap_reps, 800)

_calibration_frames: list[pd.DataFrame] = []
_paraphrases_used: list[int] = []
_escalation_log: list[dict[str, Any]] = []
S.SIGNATURE = S.SIG_DRAWS_RAW = S.CALIPERS = PRECISION = None
SLOPE_HETEROGENEITY = SLOPES_BY_ROTATION = None
S.GAPS = S.GAP_SE = CONTENDERS = None
PRECISION_OK = False

with S.phase("calibration"):
    for _target_p in S.CFG.paraphrase_schedule:
        _wanted = list(S.PARAPHRASE_POOL[:_target_p])
        _new = [p for p in _wanted if p not in _paraphrases_used]
        if _new:
            _stage = "calibration_p" + "-".join(str(p) for p in _new)
            _design = S.build_calibration_design(S.MEASURED_IDS, S.U_BUILD, _new, _stage)
            _design.to_csv(S.DESIGN_DIR / f"{_stage}_design.csv", index=False)
            print(f"\n=== calibration at P={_target_p}: wordings {_new} "
                  f"({len(_design)} rows) ===")
            _resp = S.run_generation_stage(_design, _stage)
            _err = 1.0 - _resp["generation_ok"].mean()
            if _err > 0.10:
                raise RuntimeError(f"{_err:.1%} of {_stage} generations failed.")
            _calibration_frames.append(S.score_responses(_resp))
            _paraphrases_used.extend(_new)

        S.calibration_scores = pd.concat(_calibration_frames, ignore_index=True)
        _table = S.calibration_cell_table(S.calibration_scores)

        with S.phase("feature_build"):
            _fn = S.make_signature_fn(S.MEASURED_IDS, S.U_BUILD,
                                    sorted(_paraphrases_used), S.COUPLING)
            _point, _draws = bootstrap_functional(
                _table, _fn, S.SIG_REPS, S.CFG.base_seed + 202 + len(_paraphrases_used))
            _sig = S.signature_frame(_point, S.MEASURED_IDS, S.U_BUILD)
            _sig_full = S.signature_frame(_point, S.MEASURED_IDS, S.U_BUILD, include_diagnostic=True)
            _sig_draws = S.draws_to_frames(_draws, S.MEASURED_IDS, S.U_BUILD)

        with S.phase("caliper_derivation"):
            # The focal constraint is excluded from the sensitivity regression:
            # calipers describe how mismatch moves generic burden in general.
            try:
                _cal, _hetero, _by_rot = S.derive_calipers(
                    _sig, _sig_draws, S.MEASURED_IDS, S.U_BUILD, exclude=[S.CFG.focal_id])
            except SensitivityNotEstimable as exc:
                _complete = S.complete_pool(_sig, [S.CFG.focal_id])
                S.stop("2_feasibility", GateStatus.PRECISION_INSUFFICIENT, str(exc),
                     quantities={"constraints_with_complete_signature": _complete,
                                 "n_complete": len(_complete),
                                 "measured": S.MEASURED_IDS,
                                 "coupling_role": S.CFG.coupling_role},
                     thresholds={"minimum_complete_pool": 3},
                     more_data_could_resolve=True,
                     new_protocol_version_required=False,
                     message=f"""
PRECISION_INSUFFICIENT: no caliper can be derived from outcome sensitivity.

Only {len(_complete)} constraints have a complete calibration signature, so the
held-one-target-out sensitivity regression has too few rows. The usual cause is
a component that is undefined for most candidates, and with
coupling_role='{S.CFG.coupling_role}' the usual such component is kappa.

  1. Enlarge the coupling response bank so more responses satisfy both A and a
     candidate at baseline, which is what makes kappa estimable.
  2. Or set coupling_role='audit', which removes kappa from the quantitative
     signature and enforces it as a hard measurement-coupling audit instead.
     That is a declared protocol choice recorded in the hash, and it is the
     documented alternative to silently dropping a matching dimension.
  3. Or collect more calibration data.

Pool spread remains unacceptable as a substitute.
""")
                # Dry-run bypass only: a permissive table so the remaining cells
                # can be exercised. Nothing computed from it is evidence.
                _floor_slope = S.CFG.caliper_slope_floor
                _cal = pd.DataFrame(
                    [{"component": c, "family": S.component_family(c),
                      "slope_pooled": np.nan, "slope_max_rotation": np.nan,
                      "slope_relative_spread": np.nan, "pooling_justified": False,
                      "slope_se": np.nan, "slope_used": _floor_slope,
                      "caliper": min(S.CFG.sesoi_risk_difference / _floor_slope,
                                     S.CFG.caliper_absolute_ceiling),
                      "bound_by": "dry-run bypass", "capped": True}
                     for c in S.signature_components(S.U_BUILD)]).set_index("component")
                _hetero = pd.DataFrame()
                _by_rot = pd.DataFrame()
            _gaps, _gap_se = S.mismatch_table(_sig, _sig_draws, S.MEASURED_IDS, S.U_BUILD,
                                            S.CFG.focal_id, S.COUPLING_SE)
            _distance = S.contender_distance(_gaps, _cal, S.PRESCREEN_KEPT)
            _contenders = S.contender_set(_gaps, _cal, S.CFG.contender_buffer_multiple,
                                        S.PRESCREEN_KEPT)
            _prec = S.precision_report(_gap_se, _cal, len(S.CALIBRATION_TASKS), _contenders)

        _ok = bool(_prec["precision_ok"].all()) and len(_contenders) > 0
        _escalation_log.append({
            "paraphrases": len(_paraphrases_used),
            "contenders": len(_contenders),
            "components_failing_precision": int((~_prec["precision_ok"]).sum()),
            "max_clusters_required": float(_prec["clusters_required_planning_estimate"].max()),
            "precision_ok": _ok})
        print(f"P={len(_paraphrases_used)}: {len(_contenders)} contenders; "
              f"{int((~_prec['precision_ok']).sum())} of {len(_prec)} components fail "
              f"the contender precision rule")

        CONTENDER_DISTANCE = _distance
        S.SIGNATURE, S.SIG_DRAWS_RAW = _sig, _sig_draws
        S.SIGNATURE_FULL = _sig_full
        S.CALIPERS, PRECISION = _cal, _prec
        SLOPE_HETEROGENEITY, SLOPES_BY_ROTATION = _hetero, _by_rot
        S.GAPS, S.GAP_SE, CONTENDERS = _gaps, _gap_se, _contenders
        PRECISION_OK = _ok
        if _ok:
            break

S.P_FINAL = sorted(_paraphrases_used)
CAL_TABLE = _table
ESCALATION = pd.DataFrame(_escalation_log)

SENSITIVITY_DIAGNOSTICS_FRAME = pd.DataFrame(S.SENSITIVITY_DIAGNOSTICS)
if len(SENSITIVITY_DIAGNOSTICS_FRAME):
    SENSITIVITY_DIAGNOSTICS_FRAME.to_csv(
        S.SCORE_DIR / "sensitivity_diagnostics.csv", index=False)
    _usable = SENSITIVITY_DIAGNOSTICS_FRAME.query("usable")
    display(SENSITIVITY_DIAGNOSTICS_FRAME[
        ["held_out", "order", "n_pairs", "n_independent_constraints",
         "n_predictors", "rank", "full_rank", "condition_number",
         "well_conditioned", "usable", "excluded_reason"]].round(3))
    print(f"""
Sensitivity estimation quality
  rotations attempted      : {len(SENSITIVITY_DIAGNOSTICS_FRAME)}
  usable                   : {len(_usable)}
  minimum independent constraints required : {S.CFG.min_constraints_for_sensitivity}
  maximum condition number permitted       : {S.CFG.max_condition_number:.0e}
  worst condition number observed          : {SENSITIVITY_DIAGNOSTICS_FRAME['condition_number'].replace(np.inf, np.nan).max():.3g}

A rotation that is rank deficient or worse conditioned than the declared limit
is excluded and named, not silently averaged in. v14 read a slope from every
rotation it could invert, including its own Gate 0 fixture, whose design matrix
was rank 1.""")
    if len(_usable) == 0:
        S.stop("2_feasibility", GateStatus.SENSITIVITY_NOT_ESTIMABLE,
             "no sensitivity rotation is both full rank and well conditioned",
             quantities={"rotations": len(SENSITIVITY_DIAGNOSTICS_FRAME),
                         "reasons": SENSITIVITY_DIAGNOSTICS_FRAME[
                             "excluded_reason"].value_counts().to_dict()},
             thresholds={"min_constraints": S.CFG.min_constraints_for_sensitivity,
                         "max_condition_number": S.CFG.max_condition_number},
             more_data_could_resolve=True, new_protocol_version_required=False,
             message="SENSITIVITY_NOT_ESTIMABLE: every rotation was excluded.")

for _name, _obj in (("paraphrase_escalation", ESCALATION),
                    ("calibration_signature", S.SIGNATURE_FULL),
                    ("calipers", S.CALIPERS), ("caliper_precision", PRECISION),
                    ("slope_heterogeneity", SLOPE_HETEROGENEITY),
                    ("slopes_by_rotation", SLOPES_BY_ROTATION),
                    ("signature_gaps", S.GAPS), ("signature_gap_se", S.GAP_SE)):
    _obj.to_csv(S.SCORE_DIR / f"{_name}.csv")
np.save(S.SCORE_DIR / "signature_draws.npy", S.SIG_DRAWS_RAW)

display(ESCALATION)
display(S.SIGNATURE_FULL.round(3))
display(S.CALIPERS.round(4))
display(SLOPE_HETEROGENEITY.round(4))
print(f"frozen calibration wordings: {S.P_FINAL}  "
      f"(held out, evaluated at Gate 3b: {tuple(S.CFG.paraphrase_holdout)})")
print(f"contenders under the {S.CFG.contender_buffer_multiple}x caliper buffer: {CONTENDERS}")

_pool_sd = float(S.SIGNATURE.loc[[c for c in S.MEASURED_IDS if c != S.CFG.focal_id],
                               S.SIG_DIFFICULTY].std())
print(f"""
Caliper provenance
  Every caliper is SESOI / (conservative upper sensitivity), floored at a slope
  of {S.CFG.caliper_slope_floor} and capped at {S.CFG.caliper_absolute_ceiling}. Sensitivity is estimated separately for
  each held-out target and order; where those disagree by more than
  {S.CFG.slope_pooling_max_relative_spread:.0%} the largest is used, so pooling can never widen a caliper.

  For comparison only, and used for nothing: the pool SD of isolated difficulty
  is {_pool_sd:.3f}, so a v12-style 0.50-SD caliper would have been {0.5 * _pool_sd:.3f} against
  the {float(S.CALIPERS.at[S.SIG_DIFFICULTY, 'caliper']):.3f} derived here.
""")

if not S.COUPLING_USABLE:
    S.stop("2_feasibility", GateStatus.PRECISION_INSUFFICIENT,
         "verifier coupling with the target is undefined or too imprecise for "
         "the focal constraint",
         quantities={"kappa": S.FOCAL_COUPLING, "se": S.FOCAL_COUPLING_SE,
                     "informative_responses": S.FOCAL_COUPLING_N},
         thresholds={"min_informative": S.CFG.min_informative_coupling_probes,
                     "max_se": S.CFG.max_coupling_se},
         more_data_could_resolve=True, new_protocol_version_required=False,
         message=f"""
PRECISION_INSUFFICIENT on the coupling component.

kappa for {S.CFG.focal_id} against {S.CFG.target_id} rests on {S.FOCAL_COUPLING_N} informative bank
responses with SE {S.FOCAL_COUPLING_SE:.4f}. v13 would have dropped this matching dimension
because it was undefined for B, silently changing the estimand.

Enlarge the coupling response bank so that more responses satisfy both A and B
at baseline, or demote coupling to an explicit hard measurement audit and
declare that as a new protocol version. Do not simply remove it.
""")

if not CONTENDERS:
    # No candidate lies within even the generous buffer, so there is nothing for
    # precision to protect. This is a statement about the POOL, not about the
    # calibration: more calibration data would sharpen gaps that already sit far
    # outside the caliper. Routing it to PRECISION_INSUFFICIENT would promise a
    # remedy that cannot work, which is exactly the confusion these separate
    # statuses exist to prevent.
    _nearest = CONTENDER_DISTANCE.dropna()
    display(_nearest.head(10).to_frame("max_gap_over_caliper").round(3))
    _closest = float(_nearest.iloc[0]) if len(_nearest) else float("nan")
    S.stop("2_feasibility", GateStatus.NOT_IDENTIFIED_SUPPORT,
         "no candidate is within the contender buffer of the focal constraint "
         "on every signature component",
         quantities={"contender_buffer_multiple": S.CFG.contender_buffer_multiple,
                     "nearest_candidates": _nearest.head(5).round(4).to_dict(),
                     "pool_size": len(S.PRESCREEN_KEPT),
                     "components": list(S.CALIPERS.index),
                     "paraphrases": S.P_FINAL},
         thresholds={"buffer_multiple": S.CFG.contender_buffer_multiple},
         more_data_could_resolve=False, new_protocol_version_required=True,
         message=f"""
NOT_IDENTIFIED_SUPPORT at the contender stage.

The nearest candidate sits {_closest:.2f} calipers away on its worst component, against a
buffer of {S.CFG.contender_buffer_multiple}. Calibration is not the limiting factor: these gaps are
measured, and shrinking their uncertainty would not move the point estimates
inside the caliper.

  1. Author further candidate constraints that resemble the focal constraint on
     the components listed above. That is a change to the declared pool and
     therefore a new protocol version.
  2. Or accept that the focal constraint has no comparable reference in this
     family, and report that as the finding it is.

Widening the caliper is not on this list. The caliper is SESOI / sensitivity;
widening it to admit a distant reference redefines what comparable means and
silently changes the estimand the panel is supposed to identify.
""")

elif not PRECISION_OK:
    # Reached only when contenders exist, so every quantity below is defined.
    _failing = PRECISION.query("not precision_ok")
    display(_failing.round(4))
    _required = float(_failing["clusters_required_planning_estimate"].max())
    _have = float(len(S.CALIBRATION_TASKS))
    S.stop("2_feasibility", GateStatus.PRECISION_INSUFFICIENT,
         f"{len(_failing)} of {len(PRECISION)} components cannot be resolved for "
         "the contending candidates",
         quantities={"components_failing": _failing.index.tolist(),
                     "binding_component": str(_failing["clusters_required_planning_estimate"].idxmax()),
                     "worst_contender": str(_failing["worst_contender"].iloc[0]),
                     "clusters_now": _have,
                     "clusters_required_planning_estimate": _required,
                     "contenders": CONTENDERS, "paraphrases": S.P_FINAL},
         thresholds={"precision_fraction": S.CFG.caliper_precision_fraction,
                     "uncertainty_q": S.CFG.caliper_uncertainty_q},
         more_data_could_resolve=True, new_protocol_version_required=False,
         message=f"""
PRECISION_INSUFFICIENT.

The paraphrase schedule is exhausted at P={len(S.P_FINAL)} and calibration still cannot
resolve the caliper for the candidates that could actually enter the panel.
This is NOT the same as NOT_IDENTIFIED_SUPPORT: the references may well exist,
and we cannot yet tell.

  binding component     : {str(_failing['clusters_required_planning_estimate'].idxmax())}
  worst contender       : {str(_failing['worst_contender'].iloc[0])}
  calibration clusters  : {_have:.0f} tasks
  clusters required     : {_required:.0f} tasks (planning estimate under 1/sqrt(n) scaling)

Uncertainty here is a task-cluster bootstrap, so it falls with the number of
calibration TASKS. Adding wordings or seeds inside the same tasks reduces
within-task noise and will not close this gap.

  1. Author further calibration topics and rerun.
  2. Reconsider the SESOI. A caliper is SESOI / sensitivity, so a smaller
     interesting effect demands proportionally more calibration.
  3. Accept that comparability cannot be measured at this scale.

Dropping a component would also make this pass. That is a change of estimand
and therefore a new protocol version, not a patch.
""")
else:
    S.record_gate(GateOutcome("2a_precision", GateStatus.PASS,
                            "every caliper is resolvable for every contender",
                            quantities={"clusters": len(S.CALIBRATION_TASKS),
                                        "paraphrases": S.P_FINAL,
                                        "contenders": CONTENDERS}))
S.checkpoint("calibration", {"paraphrases": S.P_FINAL, "contenders": CONTENDERS})
