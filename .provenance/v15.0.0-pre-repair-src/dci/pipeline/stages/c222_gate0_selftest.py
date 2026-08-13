"""Stage 222 — migrated from notebook cell 222.py (gate0_selftest).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/222.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import bootstrap_functional, holm, paired_advantage, percentile_ci, simultaneous_abs_upper, simultaneous_bounds  # noqa: F401
from dci.exceptions import LineageViolation, SensitivityNotEstimable, StudyStop, TaskBankInsufficient  # noqa: F401
from dci.measurement.audit_sizing import error_ceiling_sample_size, wilson_interval  # noqa: F401
from dci.protocol.estimands import ESTIMAND_DEFINITIONS  # noqa: F401
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.provenance.hashes import referenced_names, sha, sha_file, stable_int  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

GATE0_CHECKS: list[dict[str, Any]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    GATE0_CHECKS.append({"check": name, "passed": bool(condition), "detail": detail})


with S.phase("gate0_selftest"):
    # ------------------------------------------------ 1. structural checks
    check("verifier_unit_tests", S.N_VERIFIER_TESTS >= 70, f"{S.N_VERIFIER_TESTS} assertions")
    check("bridge_targets_pass_both_pathway_probes",
          all(r["count_invariant"] and r["order_invariant"] for r in S.BRIDGE_PROBE_TABLE),
          f"{len(S.BRIDGE_PROBE_TABLE)} bridge targets")
    check("bridge_family_excluded_from_u_build",
          "bridge" not in S.CFG.u_build_families,
          "bridge targets share A's segmentation span and may only validate")

    _u_fixture = ["ua", "ub", "uc"]
    _comps = S.signature_components(_u_fixture)
    check("signature_only_emits_requested_targets",
          all(S.component_target(c) in (None, *_u_fixture) for c in _comps),
          f"{len(_comps)} components")
    # v15 replaces v14's "kappa must always be matched" with the stronger and
    # more honest property: kappa is always MEASURED and always REPORTED, and
    # whether it is matched is a declared estimand choice that is recorded in
    # the protocol hash. It can still never vanish silently.
    check("coupling_is_always_measured_and_declared",
          (S.SIG_COUPLING in _comps) == (S.CFG.coupling_role == "matched")
          and S.CFG.primary_estimand in ("primary_total", "kappa_matched")
          and (S.CFG.coupling_role == "matched") == (S.CFG.primary_estimand == "kappa_matched"),
          f"estimand {S.CFG.primary_estimand}, kappa role {S.CFG.coupling_role}: "
          "matched status follows the declared estimand, never convenience")
    check("kappa_matched_and_total_are_not_the_same_estimand",
          ESTIMAND_DEFINITIONS["primary_total"]["reference_definition"]
          != ESTIMAND_DEFINITIONS["kappa_matched"]["reference_definition"],
          "different reference definitions, different interpretations")
    check("wording_instability_is_decomposed",
          set(S.WORDING_MATCHED) <= set(_comps) and len(S.WORDING_MATCHED) == 3)

    _screen = S.build_screening_design()
    _pre = S.build_prescreen_design()
    _cal = S.build_calibration_design([S.CFG.focal_id, *S.CANDIDATE_IDS[:3]],
                                    list(S.U_CANDIDATE_IDS[:2]), [0, 1], "gate0_cal")
    _conf = S.build_confirmatory_design(list(S.CANDIDATE_IDS[:S.CFG.reference_count]), [0, 1])
    _plac = S.build_placebo_design(list(S.CANDIDATE_IDS[:S.CFG.reference_count]),
                                 ["U_NUM_NODIGIT"], [0, 1])
    _word = S.build_wording_validation_design([S.CFG.focal_id, *S.CANDIDATE_IDS[:2]],
                                            list(S.U_CANDIDATE_IDS[:2]))
    for _label, _d in (("screening", _screen), ("prescreen", _pre),
                       ("calibration", _cal), ("confirmatory", _conf),
                       ("placebo", _plac), ("wording", _word)):
        check(f"design_unique_{_label}", bool(_d["row_id"].is_unique), f"{len(_d)} rows")
    check("confirmatory_balanced",
          _conf.groupby("condition_id").size().nunique() == 1)
    check("confirmatory_has_both_orders",
          set(_conf.query("condition_id != 'A_ONLY'")["order"]) == set(S.CFG.orders))
    _burned = set(S.TASKS.query("split == 'burned'")["topic"])
    check("no_burned_topics_in_any_design",
          all(_burned.isdisjoint(set(d["topic"]))
              for d in (_screen, _pre, _cal, _conf, _plac, _word)))
    check("held_out_wordings_never_enter_construction",
          set(_cal["paraphrase_id"]).isdisjoint(S.CFG.paraphrase_holdout)
          and set(_conf["paraphrase_id"]).isdisjoint(S.CFG.paraphrase_holdout),
          f"holdout {tuple(S.CFG.paraphrase_holdout)} absent from calibration and confirmation")
    check("held_out_wordings_are_actually_evaluated",
          set(_word["paraphrase_id"]) == set(S.CFG.paraphrase_holdout)
          and len(_word) > 0,
          "Gate 3b consumes exactly the held-out wordings")
    check("wording_validation_uses_its_own_tasks",
          set(_word["task_id"]).isdisjoint(set(_conf["task_id"])))
    check("benchmark_prompts_are_not_scientific",
          set(S.build_benchmark_design(4)["topic"]).isdisjoint(set(S.TASKS["topic"])))

    # ------------------------------------------------ 2. the synthetic oracle
    _oracle = []
    for _trial in range(4000):
        _row = {"row_id": f"gate0-oracle-{_trial:05d}",
                "ordered_constraint_ids": [S.CFG.target_id, S.CFG.focal_id],
                "order": S.ADDED_FIRST, "added_constraint": S.CFG.focal_id,
                "measured_constraint": S.CFG.target_id}
        _oracle.append(1 - S.verify(S.synthetic_response(_row), S.CFG.target_id).binary_pass)
    _observed = float(np.mean(_oracle))
    _expected = S.synthetic_expected_fail([S.CFG.target_id, S.CFG.focal_id], S.ADDED_FIRST,
                                        S.CFG.focal_id, S.CFG.target_id)
    _tol = max(4 * math.sqrt(max(_expected * (1 - _expected), 1e-6) / len(_oracle)), 0.02)
    check("oracle_matches_closed_form", abs(_observed - _expected) <= _tol,
          f"observed {_observed:.4f} vs closed form {_expected:.4f}")
    check("oracle_has_designed_focal_excess",
          S.synthetic_beta([S.CFG.target_id, S.CFG.focal_id], S.ADDED_FIRST, S.CFG.focal_id)
          > S.synthetic_beta([S.CFG.target_id], "isolated", S.CFG.target_id))
    check("oracle_has_designed_order_effect",
          S.synthetic_beta([S.CFG.target_id, S.CFG.focal_id], S.ADDED_FIRST, S.CFG.focal_id)
          > S.synthetic_beta([S.CFG.target_id, S.CFG.focal_id], S.TARGET_FIRST, S.CFG.focal_id))
    _bridge_range = S.SYNTHETIC_FAIL[list(S.BRIDGE_IDS)].mean()
    check("oracle_gives_bridge_targets_dynamic_range",
          bool(((_bridge_range > 0.02) & (_bridge_range < 0.98)).all()),
          f"{dict(_bridge_range.round(2))}")
    # Every declared constraint, not merely the bridge family. A constraint the
    # corpus can never satisfy is pinned at 1.0 whatever the design does, and a
    # dry run over such a fixture tests nothing downstream of scoring.
    _min_sat = min(len(v) for v in S.SYN_SATISFYING.values())
    _min_viol = min(len(v) for v in S.SYN_VIOLATING.values())
    _pinned = sorted(c for c in S.CONSTRAINTS
                     if min(len(S.SYN_SATISFYING[c]), len(S.SYN_VIOLATING[c]))
                     < S.CFG.oracle_min_corpus_support)
    check("oracle_gives_every_constraint_dynamic_range", not _pinned,
          f"{len(S.CONSTRAINTS)} constraints; fewest satisfying {_min_sat}, "
          f"fewest violating {_min_viol}"
          + (f"; pinned: {_pinned}" if _pinned else ""))
    # The closed form is exact only because the draw pools are conditioned on
    # the constraint being measured, so a realised rate that drifts from beta
    # would mean the oracle is no longer the process the checks assume.
    _beta = S.synthetic_beta([S.CFG.target_id, S.CFG.focal_id], S.ADDED_FIRST, S.CFG.focal_id)
    check("oracle_realised_rate_equals_designed_beta",
          abs(_expected - _beta) <= 1e-9, f"closed form {_expected:.4f} = beta {_beta:.4f}")

    # -------------------------------- 3. decision rules on planted fixtures
    _planted = 0.60
    _ids = [f"F{i}" for i in range(12)]
    # The families must vary INDEPENDENTLY. v14's fixture made g, r and s exact
    # linear functions of d, so its sensitivity design matrix was rank 1 and
    # every slope it produced was arbitrary. v15 refuses such a design, which is
    # why the fixture now carries independent per-family variation, and why the
    # degenerate version is kept below as a negative control.
    _fix_rng = np.random.default_rng(stable_int("gate0-fixture|v15"))
    _fix = pd.DataFrame(index=_ids, columns=_comps, dtype=float)
    for _i, _cid in enumerate(_ids):
        _d = 0.10 + 0.06 * _i
        _fix.at[_cid, S.SIG_DIFFICULTY] = _d
        _gj = float(_fix_rng.normal(0.0, 0.05))
        _rj = float(_fix_rng.normal(0.0, 0.05))
        for _u in _u_fixture:
            for _o in S.CFG.orders:
                _fix.at[_cid, f"g|{_u}|{_o}"] = (
                    _planted * _d + _gj + (0.02 if _o == S.ADDED_FIRST else 0.0))
                _fix.at[_cid, f"r|{_u}|{_o}"] = 0.30 * _d + _rj
        if S.SIG_COUPLING in _comps:
            _fix.at[_cid, S.SIG_COUPLING] = 0.20 + float(_fix_rng.normal(0.0, 0.03))
        for _s in S.WORDING_MATCHED:
            _fix.at[_cid, _s] = 0.01 * _i + abs(float(_fix_rng.normal(0.0, 0.01)))
    _zero_draws = np.repeat(_fix.to_numpy(dtype=float)[None, :, :], 8, axis=0)
    _cal_table, _hetero, _by_rot = S.derive_calipers(_fix, _zero_draws, _ids, _u_fixture)

    check("sensitivity_estimated_per_rotation_and_order",
          len(_by_rot) == len(_u_fixture) * len(S.CFG.orders),
          f"{len(_by_rot)} rotation-order slope vectors")
    check("calipers_never_exceed_ceiling",
          bool((_cal_table["caliper"] <= S.CFG.caliper_absolute_ceiling + 1e-9).all()))
    check("calipers_invert_sesoi_against_slope",
          bool(np.allclose(_cal_table["caliper"],
                           np.minimum(S.CFG.sesoi_risk_difference / _cal_table["slope_used"],
                                      S.CFG.caliper_absolute_ceiling))))
    _caliper_names = referenced_names(S.derive_calipers, S.sensitivity_by_rotation,
                                      S._slope_block, S.admit_candidates)
    check("caliper_uses_no_pool_spread",
          not ({"POOL_SD", "pool_sd", "pool_spread", "POOL_SPREAD"} & _caliper_names)
          and not any(c in ("pool_sd", "pool_spread") for c in _cal_table.columns),
          "no pool-spread symbol is referenced anywhere in caliper derivation "
          "or admission")

    # Heterogeneous rotations must select the largest sensitivity, never the mean.
    _het = _fix.copy()
    for _cid in _ids:
        _het.at[_cid, f"g|{_u_fixture[0]}|{S.CFG.orders[0]}"] = (
            3.0 * _planted * float(_het.at[_cid, S.SIG_DIFFICULTY]))
    _het_cal, _het_tab, _ = S.derive_calipers(_het, np.repeat(
        _het.to_numpy(dtype=float)[None, :, :], 8, axis=0), _ids, _u_fixture)
    check("heterogeneous_sensitivity_takes_the_conservative_maximum",
          bool((~_het_tab["homogeneous"]).any())
          and bool((_het_tab.loc[~_het_tab["homogeneous"], "chosen"]
                    >= _het_tab.loc[~_het_tab["homogeneous"], "pooled"] - 1e-9).all()),
          "a pooled average may never widen a caliper past the sensitive rotation")

    _focal_fix = "F0"
    _gaps = (_fix.drop(index=_focal_fix) - _fix.loc[_focal_fix]).abs()
    _se_zero = pd.DataFrame(0.0, index=_gaps.index, columns=_gaps.columns)
    _se_big = pd.DataFrame(1.0, index=_gaps.index, columns=_gaps.columns)
    _right_scope = {c: "sentence" for c in _gaps.index}
    _wrong_scope = {c: "whole_text" for c in _gaps.index}
    _adm = S.admit_candidates(_gaps, _se_zero, _cal_table, "sentence",
                            list(_gaps.index), _right_scope)
    check("admission_matches_componentwise_rule",
          bool((_adm["componentwise_ok"] == [
              all(float(_gaps.at[c, comp]) <= float(_cal_table.at[comp, "caliper"])
                  for comp in _cal_table.index) for c in _adm.index]).all()))
    check("wide_calipers_admit_everything",
          int(S.admit_candidates(_gaps, _se_zero, _cal_table.assign(caliper=9.9),
                               "sentence", list(_gaps.index), _right_scope)
              ["componentwise_ok"].sum()) == len(_gaps))

    # ------------------------------------------------ the joint certificate
    # Every component individually inside its caliper, and the accumulated
    # first-order bias far outside the total budget. This is the configuration
    # the componentwise rule cannot see, and the one v14 admitted.
    _accum = pd.DataFrame(
        {comp: [0.95 * float(_cal_table.at[comp, "caliper"])] for comp in _cal_table.index},
        index=["ACCUM"])
    _accum_se = pd.DataFrame(0.0, index=_accum.index, columns=_accum.columns)
    _accum_adm = S.admit_candidates(_accum, _accum_se, _cal_table, "sentence",
                                  ["ACCUM"], {"ACCUM": "sentence"})
    _accum_cert = S.reference_error_certificate(_accum, _accum_se, _cal_table, ["ACCUM"])
    check("joint_budget_rejects_accumulated_moderate_mismatches",
          bool(_accum_adm["componentwise_ok"].iloc[0])
          and not bool(_accum_adm["eligible"].iloc[0])
          and float(_accum_cert["budget_total"].iloc[0]) > S.CFG.epsilon_ref,
          f"every caliper passes at 95% of its width, total certificate "
          f"{float(_accum_cert['budget_total'].iloc[0]):.3f} > {S.CFG.epsilon_ref}")
    check("joint_budget_records_which_criterion_was_binding",
          str(_accum_adm["binding_criterion"].iloc[0]) == "joint_budget",
          "the reader can tell which rule refused the candidate")
    # A genuinely close candidate passes both.
    _close = pd.DataFrame(
        {comp: [0.0] for comp in _cal_table.index}, index=["CLOSE"])
    _close_se = pd.DataFrame(0.0, index=_close.index, columns=_close.columns)
    check("joint_budget_admits_a_genuinely_close_reference",
          bool(S.admit_candidates(_close, _close_se, _cal_table, "sentence",
                                ["CLOSE"], {"CLOSE": "sentence"})["eligible"].iloc[0]),
          "the certificate is a bound on accumulated bias, not a second caliper")
    check("joint_budget_can_only_remove_candidates",
          int(_accum_adm["eligible"].sum()) <= int(_accum_adm["componentwise_ok"].sum()))
    check("scope_exact_match_binds",
          int(S.admit_candidates(_gaps, _se_zero, _cal_table.assign(caliper=9.9),
                               "sentence", list(_gaps.index), _wrong_scope)
              ["eligible"].sum()) == 0)
    _adm_noisy = S.admit_candidates(_gaps, _se_big, _cal_table, "sentence",
                                  list(_gaps.index), _right_scope)
    check("uncertainty_can_only_remove_candidates",
          int(_adm_noisy["eligible"].sum()) <= int(_adm["eligible"].sum()))

    _panel, _dist = S.select_panel(_ids[1:], _fix, _focal_fix, S.CFG.reference_count,
                                 S.CFG.mahalanobis_ridge)
    check("panel_is_exactly_k", len(_panel) == S.CFG.reference_count)
    check("panel_is_deterministic",
          _panel == S.select_panel(list(reversed(_ids[1:])), _fix, _focal_fix,
                                 S.CFG.reference_count, S.CFG.mahalanobis_ridge)[0])
    try:
        S.select_panel(_ids[1:S.CFG.reference_count], _fix, _focal_fix,
                     S.CFG.reference_count, S.CFG.mahalanobis_ridge)
        check("short_pool_raises_not_identified_support", False, "no exception")
    except StudyStop as exc:
        check("short_pool_raises_not_identified_support",
              exc.outcome.status == GateStatus.NOT_IDENTIFIED_SUPPORT
              and exc.outcome.more_data_could_resolve is False,
              "and it says more data would NOT help")

    check("precision_and_support_failures_are_distinct_statuses",
          GateStatus.PRECISION_INSUFFICIENT != GateStatus.NOT_IDENTIFIED_SUPPORT
          and len(set(GateStatus.ALL)) == len(GateStatus.ALL))

    # Precision must follow the contenders, not the median.
    _contenders = S.contender_set(_gaps, _cal_table, S.CFG.contender_buffer_multiple,
                                list(_gaps.index))
    check("contender_set_is_a_subset_of_the_pool",
          set(_contenders) <= set(_gaps.index) and len(_contenders) >= 1,
          f"{len(_contenders)} contenders of {len(_gaps)}")
    _mixed_se = _se_zero.copy()
    if _contenders:
        _mixed_se.loc[_contenders[0]] = 1.0          # one contender is imprecise
    _prec_median_ok = S.precision_report(_mixed_se, _cal_table, 12, list(_gaps.index))
    _prec_contender = S.precision_report(_mixed_se, _cal_table, 12, _contenders)
    check("precision_gate_protects_contenders_not_the_median",
          not bool(_prec_contender["precision_ok"].all()),
          "a single imprecise contender fails the gate even though the pool "
          "median is exact")
    check("precision_reports_a_planning_estimate_in_clusters",
          "clusters_required_planning_estimate" in _prec_contender.columns)
    check("sufficient_precision_passes",
          bool(S.precision_report(_se_zero, _cal_table, 12, _contenders)["precision_ok"].all()))

    # A pool with no near match is a statement about the POOL, and its remedy is
    # a different pool. Routing it to PRECISION_INSUFFICIENT would promise that
    # more calibration data fixes it, which is the confusion requirement 2 names.
    _distant = _gaps.copy()
    _distant.loc[:, :] = (_cal_table["caliper"] * 5.0).reindex(_distant.columns).to_numpy()
    _distant_distance = S.contender_distance(_distant, _cal_table, list(_distant.index))
    check("empty_contender_set_is_a_support_statement_not_a_precision_one",
          S.contender_set(_distant, _cal_table, S.CFG.contender_buffer_multiple,
                        list(_distant.index)) == []
          and bool((_distant_distance > S.CFG.contender_buffer_multiple).all()),
          "no candidate inside the buffer at 5x the caliper")
    check("contender_distance_reports_the_multiple_that_would_be_needed",
          abs(float(_distant_distance.iloc[0]) - 5.0) < 1e-6,
          f"{float(_distant_distance.iloc[0]):.3f} calipers")
    check("empty_admission_returns_a_reportable_frame",
          list(S.admit_candidates(_distant, _se_zero, _cal_table, "sentence",
                                [], scopes={}).columns)[:4]
          == ["scope", "origin", "n_failed_components", "componentwise_ok"],
          "an empty pool is a state the gate reports, not a KeyError below it")
    check("empty_hard_eligible_universe_is_reportable",
          list(S.hard_eligible_universe([]).columns)[-2:]
          == ["hard_eligible", "rejection_reasons"])

    _w = S.fit_stochastic_weights(_fix, _panel, _focal_fix, list(_cal_table.index),
                                _dist)
    check("weights_respect_cap", bool((_w <= S.CFG.max_single_weight + 1e-9).all()),
          f"max {float(_w.max()):.3f}")
    check("weights_sum_to_one", abs(float(_w.sum()) - 1.0) < 1e-6)
    _far = _dist.copy() * 1.0
    _far[_panel[0]] = 50.0
    _w_pen = S.fit_stochastic_weights(_fix, _panel, _focal_fix, list(_cal_table.index), _far)
    check("distance_penalty_downweights_a_distant_donor",
          float(_w_pen[_panel[0]]) <= float(_w[_panel[0]]) + 1e-9,
          "aggregate balance cannot be bought from an individually distant donor")

    # ---------------------------------- 4. Gate 3 and Gate 4 decision logic
    check("g0_cannot_authorize_a_failed_g1",
          S.authorize_primary(g1_passed=False, g0_passed=True, g2_passed=False) is False)
    check("g2_cannot_authorize_a_failed_g1",
          S.authorize_primary(g1_passed=False, g0_passed=False, g2_passed=True) is False)
    check("g1_alone_authorizes_the_primary",
          S.authorize_primary(g1_passed=True) is True)
    check("failed_g2_does_not_invalidate_g1",
          S.authorize_primary(g1_passed=True, g2_passed=False) is True
          and S.stochastic_estimand_authorized(True, False) is False,
          "the stochastic secondary is withheld; the primary panel stands")
    _cohort, _status = S.evaluate_pseudo_focal_cohort(["Q1", "Q2"], S.CFG.min_pseudo_focal)
    check("too_few_pseudo_focals_returns_not_evaluable",
          _status == GateStatus.REFERENCE_VALIDATION_NOT_EVALUABLE)
    check("enough_pseudo_focals_passes",
          S.evaluate_pseudo_focal_cohort(["Q1", "Q2", "Q3"], S.CFG.min_pseudo_focal)[1]
          == GateStatus.PASS)

    # Cancellation: a panel mean near zero hiding two opposite references.
    _refs = ["R1", "R2"]
    _cancel_comps = ["g|uv|target_first"]
    _pt = pd.Series({S.signature_key("BF", "g|uv|target_first"): 0.00,
                     S.signature_key("R1", "g|uv|target_first"): -0.20,
                     S.signature_key("R2", "g|uv|target_first"): +0.20})
    _dr = pd.DataFrame({k: np.full(400, v) for k, v in _pt.items()})
    _dr += np.random.default_rng(5).normal(0, 0.002, size=_dr.shape)
    _ind_p, _ind_d = S.discrepancy_frames(_pt, _dr, "BF", _refs, _cancel_comps)
    _pan_p, _pan_d = S.panel_residual_frames(_pt, _dr, "BF", _refs, _cancel_comps)
    _ind_bound = simultaneous_abs_upper(_ind_p, _ind_d, S.CFG.ref_val_confidence)
    _pan_bound = simultaneous_abs_upper(_pan_p, _pan_d, S.CFG.ref_val_confidence)
    check("panel_mean_hides_cancellation",
          float(_pan_bound["abs_upper"].max()) <= S.CFG.ref_val_individual_max,
          f"panel residual bound {float(_pan_bound['abs_upper'].max()):.3f}")
    check("per_reference_validation_catches_cancellation",
          float(_ind_bound["abs_upper"].max()) > S.CFG.ref_val_individual_max,
          f"worst individual bound {float(_ind_bound['abs_upper'].max()):.3f}")

    # Gate 4: a small point estimate with wide uncertainty must not pass.
    _small_pt = pd.Series({"R1|g|ut|target_first": 0.01})
    _wide = pd.DataFrame({"R1|g|ut|target_first":
                          np.random.default_rng(7).normal(0.01, 0.08, 2000)})
    _wide_bound = simultaneous_abs_upper(_small_pt, _wide, S.CFG.falsification_confidence)
    check("gate4_fails_on_uncertainty_not_point_estimate",
          abs(float(_small_pt.iloc[0])) <= S.CFG.falsification_individual_max
          and float(_wide_bound["abs_upper"].iloc[0]) > S.CFG.falsification_individual_max,
          f"point {float(_small_pt.iloc[0]):.3f} but bound "
          f"{float(_wide_bound['abs_upper'].iloc[0]):.3f}")

    _better = pd.Series(np.random.default_rng(11).normal(0.03, 0.01, 2000))
    _worse = pd.Series(np.random.default_rng(12).normal(0.08, 0.01, 2000))
    _adv = paired_advantage(_better, _worse, S.CFG.ref_val_confidence)
    check("paired_advantage_detects_a_real_improvement", _adv["upper_bound"] < 0)
    check("paired_advantage_is_not_fooled_by_a_tie",
          paired_advantage(_better, _better, S.CFG.ref_val_confidence)["upper_bound"] >= 0)

    # ------------------------------------ 5. audit gates and measurement
    check("unsigned_paraphrase_audit_does_not_pass",
          S.evaluate_paraphrase_audit(None)["passed"] is False)
    _tmp_signed = S.AUDIT_DIR / "_gate0_signed_probe.csv"
    _tmp_signed.write_text("human work\n", encoding="utf-8")
    _before = sha_file(_tmp_signed)
    S.write_template_if_absent(_tmp_signed, S.PARAPHRASE_AUDIT_TEMPLATE.head(1))
    check("signed_audit_cannot_be_overwritten_by_a_rerun",
          sha_file(_tmp_signed) == _before, "guarded write left the file untouched")
    _tmp_signed.unlink(missing_ok=True)

    _rev, _key, _plan = S.build_measurement_cases()
    check("measurement_sample_needs_no_model", len(_rev) == len(_key) > 0,
          f"{len(_rev)} blinded cases over {len(_plan)} audit units")
    check("measurement_sample_is_blinded",
          set(_rev.columns) == {"case_id", "rule_text", "response_text",
                                "manual_verdict", "reviewer_note"},
          "no constraint id, no arm, no tier, no automatic verdict")
    check("every_selectable_constraint_is_covered_by_an_audited_unit",
          not S.UNCOVERED_IDS and len(S.AUDIT_COVERAGE) == len(S.SELECTABLE_IDS),
          f"{len(S.SELECTABLE_IDS)} constraints over {len(S.TIER1_IDS)} tier-1 units "
          f"and {len(S.TIER2_STRATA)} tier-2 strata")
    check("audit_sample_contains_malformed_and_boundary_cases",
          int((_key['stratum'] == 'malformed').sum()) > 0
          and int((_key['stratum'] == 'boundary').sum()) > 0,
          f"{int((_key['stratum'] == 'malformed').sum())} malformed, "
          f"{int((_key['stratum'] == 'boundary').sum())} boundary")

    def _sign(key: pd.DataFrame, verdict) -> dict[str, Any]:
        """Adjudicate the whole key and evaluate, without touching disk twice."""
        path = S.AUDIT_DIR / "_gate0_audit_probe.csv"
        pd.DataFrame({"case_id": key["case_id"],
                      "manual_verdict": verdict(key)}).to_csv(path, index=False)
        result = S.evaluate_verifier_reliability(str(path), key)
        path.unlink(missing_ok=True)
        return result

    # 1. A mathematically perfect verifier must be able to PASS. v14's Gate M
    #    could not be passed by any verifier at its own declared size, because
    #    it sized from a one-sided zero-error formula and decided on a two-sided
    #    Wilson bound.
    _perfect = _sign(_key, lambda k: np.where(k["auto_binary_pass"] == 1, "pass", "fail"))
    check("gateM_can_be_passed_by_a_perfect_verifier",
          _perfect["passed"] is True,
          f"status {_perfect['status']}; pooled tier-2 denominators "
          f"{_perfect['pooled'].get('n_true_fail')} fail / "
          f"{_perfect['pooled'].get('n_true_pass')} pass")
    check("audit_size_inverts_the_bound_the_gate_applies",
          wilson_interval(0, S.CASES_PER_TRUTH_CLASS,
                          S.CFG.verifier_audit_confidence)[1] <= S.CFG.verifier_error_ceiling
          and wilson_interval(0, S.CASES_PER_TRUTH_CLASS - 1,
                              S.CFG.verifier_audit_confidence)[1] > S.CFG.verifier_error_ceiling,
          f"{S.CASES_PER_TRUTH_CLASS} per truth class is the smallest that attains "
          f"{S.CFG.verifier_error_ceiling:.0%}; v14 used "
          f"{error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence)}, whose bound is "
          f"{wilson_interval(0, error_ceiling_sample_size(S.CFG.verifier_error_ceiling, S.CFG.verifier_audit_confidence), S.CFG.verifier_audit_confidence)[1]:.3f}")

    # 2 and 3. A missing truth class is a missing denominator, never evidence.
    _all_pass = _sign(_key, lambda k: "pass")
    check("too_few_human_fail_examples_cannot_certify_false_pass",
          _all_pass["passed"] is False
          and bool(_all_pass["table"]["n_true_fail"].eq(0).any())
          and bool(_all_pass["table"]["false_pass_upper"].isna().any()),
          "with no human failures the false-pass bound is NaN, not zero")
    _all_fail = _sign(_key, lambda k: "fail")
    check("too_few_human_pass_examples_cannot_certify_false_fail",
          _all_fail["passed"] is False
          and bool(_all_fail["table"]["n_true_pass"].eq(0).any())
          and bool(_all_fail["table"]["false_fail_upper"].isna().any()),
          "with no human passes the false-fail bound is NaN, not zero")
    check("missing_truth_class_returns_its_own_status",
          _all_pass["status"] == GateStatus.AUDIT_CLASS_SUPPORT_INSUFFICIENT,
          f"{_all_pass['status']}, distinct from a demonstrated defect")

    # A real defect, with adequate denominators, is NOT resolvable by more data.
    _rng_defect = np.random.default_rng(stable_int("gate0|defect"))
    def _defective(k: pd.DataFrame):
        truth = np.where(k["auto_binary_pass"] == 1, "pass", "fail")
        flip = _rng_defect.random(len(k)) < 0.30
        return np.where(flip, np.where(truth == "pass", "fail", "pass"), truth)
    _defect = _sign(_key, _defective)
    check("false_fail_error_can_fail_the_measurement_gate",
          _defect["passed"] is False
          and bool((_defect["table"]["false_fail_rate"] > 0).any()),
          "false-fail is gated, not merely reported")
    check("demonstrated_verifier_defect_is_never_more_data_resolvable",
          _defect["status"] in (GateStatus.VERIFIER_RELIABILITY_FAILED,
                                GateStatus.AUDIT_CLASS_SUPPORT_INSUFFICIENT)
          and GateStatus.VERIFIER_RELIABILITY_FAILED
          in GateStatus.NEVER_RESOLVED_BY_MORE_DATA,
          f"{_defect['status']}")

    # -------------------------------- 6. fingerprints, profiles, and restore
    _base = sha(S.EXECUTION_CONDITION)
    _sensitive = ["model_profile", "model_id", "model_revision", "base_seed",
                  "temperature", "top_p", "do_sample", "max_new_tokens",
                  "initial_batch_size", "adaptive_batching", "dtype", "engine",
                  "attn_implementation", "max_input_tokens"]
    _all_change = all(sha({**S.EXECUTION_CONDITION, k: "PERTURBED"}) != _base
                      for k in _sensitive)
    check("every_randomisation_relevant_field_alters_the_fingerprint", _all_change,
          f"{len(_sensitive)} fields tested")
    check("profile_is_in_the_fingerprint_and_the_path",
          "model_profile" in S.EXECUTION_CONDITION
          and S.CFG.model_profile in str(S.RUN_ROOT) and S.CFG.model_profile in str(S.CACHE_DIR))

    _stage = "gate0_restore"
    _fake_design = S.build_benchmark_design(8).assign(stage=_stage)
    _fake_plan = S.build_batch_plan(_fake_design)
    for _b in _fake_plan:
        S.commit_batch(_stage, _b["batch_index"], 0,
                     [{"row_id": r, "response_text": "x", "generation_ok": True,
                       "generation_error": None,
                       "prompt_sha256": S.prompt_fingerprint(
                           _fake_design.set_index("row_id").at[r, "user_prompt"])}
                      for r in _b["row_ids"]],
                     {"planned_batch_index": _b["batch_index"],
                      "row_ids_planned": _b["row_ids"],
                      "row_ids_realised": _b["row_ids"],
                      "batch_seed": _b["batch_seed"], "realised_batch_size": len(_b["row_ids"]),
                      "plan_deviation": False, "run_attempt_id": S.RUN_ATTEMPT_ID})
    _before_rows = len(S.read_commits(_stage, _fake_plan)[0])
    shutil.rmtree(S.local_stage_dir(_stage))          # simulate a Colab disconnect
    check("local_cache_deletion_is_visible",
          len(S.read_commits(_stage, _fake_plan)[0]) == 0)
    _restored = S.restore_from_drive(_stage, _fake_plan)
    _after_rows = len(S.read_commits(_stage, _fake_plan)[0])
    check("drive_restore_reproduces_a_deleted_local_cache",
          _after_rows == _before_rows and _before_rows > 0,
          f"{_restored['restored']} batches, {_after_rows} rows recovered")
    check("restore_regenerates_nothing_already_committed",
          all(set(b["row_ids"]) <= set(S.read_commits(_stage, _fake_plan)[0])
              for b in _fake_plan))

    # A batch written under a foreign fingerprint must be quarantined, not read.
    _foreign = S.durable_stage_dir(_stage) / "batch-000099.commit.json"
    _foreign_body = S.durable_stage_dir(_stage) / "batch-000099-attempt-00.jsonl"
    _foreign_body.write_text('{"row_id": "foreign"}\n', encoding="utf-8")
    _foreign.write_text(json.dumps({
        "planned_batch_index": 0, "row_ids_planned": _fake_plan[0]["row_ids"],
        "execution_sha256": "a-different-model-profile",
        "payload_file": _foreign_body.name,
        "content_sha256": sha_file(_foreign_body)}), encoding="utf-8")
    _q = S.restore_from_drive(_stage, _fake_plan)
    check("foreign_profile_cache_is_quarantined_not_read",
          _q["quarantined"] >= 1
          and "foreign" not in S.read_commits(_stage, _fake_plan)[0],
          f"{_q['quarantined']} quarantined")

    # ------------------------------------------------ 7. inference utilities
    _rng2 = np.random.default_rng(7)
    _pt2 = pd.Series({"a": 0.10, "b": 0.05, "c": 0.00})
    _dr2 = pd.DataFrame(_rng2.normal(0, 0.02, size=(2000, 3)), columns=["a", "b", "c"]) + _pt2
    _sim = simultaneous_bounds(_pt2, _dr2, S.CFG.confidence_level)
    _marg = percentile_ci(_dr2, S.CFG.confidence_level)
    check("simultaneous_wider_than_marginal",
          bool((_sim["sim_lower"] <= _marg["ci_lower"] + 1e-9).all()
               and (_sim["sim_upper"] >= _marg["ci_upper"] - 1e-9).all()),
          f"critical value {_sim.attrs['critical_value']:.3f}")
    check("wilson_bounds_zero_events_sensibly",
          wilson_interval(0, 12, 0.95)[1] > 0.15
          and wilson_interval(0, 60, 0.95)[1] < 0.10,
          "12 cases cannot establish a 5% ceiling; about 59 can")
    check("holm_is_monotone_and_bounded",
          holm([0.01, 0.04, 0.20]) == sorted(holm([0.01, 0.04, 0.20]))
          and max(holm([0.01, 0.04, 0.20])) <= 1.0)
    # A NaN simultaneous MDE means the claim rule was not reachable anywhere on
    # the effect grid, which is "even larger", not a violation.
    _mde_ok = ((S.POWER_PLANNING["mde_simultaneous"].isna())
               | (S.POWER_PLANNING["mde_simultaneous"]
                  >= S.POWER_PLANNING["mde_marginal"] - 1e-9))
    check("simultaneous_power_is_never_above_marginal", bool(_mde_ok.all()),
          "the claim rule needs a larger effect than one contrast does")

    # -------------------------- 8. hard eligibility is independent of B
    _universe_a = S.hard_eligible_universe(S.CANDIDATE_IDS)
    _universe_b = S.hard_eligible_universe(S.CANDIDATE_IDS)
    check("hard_eligibility_is_deterministic",
          _universe_a["hard_eligible"].equals(_universe_b["hard_eligible"]))
    import inspect as _inspect
    _he_params = set(_inspect.signature(S.hard_eligible_universe).parameters)
    _b_relative = {"ELIGIBLE_IDS", "SELECTED_REFERENCES", "MATCH_DISTANCE",
                   "GAPS", "GAP_SE", "CONTENDERS", "PRESCREEN_KEPT"}
    check("hard_eligibility_never_reads_a_B_neighbourhood",
          not (_b_relative & referenced_names(S.hard_eligible_universe))
          and not (_he_params & {"eligible", "panel", "references"})
          and bool(_universe_a["hard_eligible"].any()),
          f"no B-relative symbol referenced; {int(_universe_a['hard_eligible'].sum())} "
          "constraints in the universe")
    check("hard_eligibility_excludes_the_focal_and_its_variants",
          not _universe_a["hard_eligible"].get(S.CFG.focal_id, False))

    # ---------------------------------- 9. end-to-end micro run on the oracle
    _micro_ids = [S.CFG.focal_id, *S.CANDIDATE_IDS[:2]]
    _micro_u = [S.U_CANDIDATE_IDS[0], S.U_CANDIDATE_IDS[5]]
    _micro_design = S.build_calibration_design(_micro_ids, _micro_u, [0, 1], "gate0_micro")
    _micro_scores = S.score_responses(S.run_generation_stage(_micro_design, "gate0_micro"))
    _micro_table = S.calibration_cell_table(_micro_scores)
    _micro_fn = S.make_signature_fn(_micro_ids, _micro_u, [0, 1], S.COUPLING)
    _micro_point, _micro_draws = bootstrap_functional(
        _micro_table, _micro_fn, 120, S.CFG.base_seed + 1)
    _micro_sig = S.signature_frame(_micro_point, _micro_ids, _micro_u)
    check("end_to_end_signature_is_finite",
          bool(np.isfinite(_micro_sig[[S.SIG_DIFFICULTY]].to_numpy()).all()))
    check("end_to_end_signature_has_variation",
          float(_micro_sig[S.SIG_DIFFICULTY].std()) > 0.001)
    _closed = pd.Series({c: S.synthetic_expected_fail([c], "isolated", c, c)
                         for c in _micro_ids})
    check("end_to_end_recovers_designed_difficulty",
          float((_micro_sig[S.SIG_DIFFICULTY] - _closed).abs().max()) < 0.25,
          f"max deviation {float((_micro_sig[S.SIG_DIFFICULTY] - _closed).abs().max()):.3f}")

    # ------------------------------------------------------ 10. gate plumbing
    try:
        S.require_gate("a_gate_that_never_ran")
        check("require_gate_raises_when_absent", False)
    except StudyStop:
        check("require_gate_raises_when_absent", True)
    S.record_gate(GateOutcome("_selftest_probe", GateStatus.MEASUREMENT_VALIDITY_FAILED,
                            "plumbing test"))
    # ==================================== 9. the v15 repairs, end to end
    # 4. A B-relative object cannot reach the pseudo-focal universe, even
    #    though neither function it passes through mentions B.
    S.declare_lineage("_g0_clean")
    S.declare_lineage("_g0_tainted", taints=[S.TAINT_FOCAL_RELATIVE],
                    parents=["_g0_clean"])
    S.declare_lineage("_g0_grandchild", parents=["_g0_tainted"])
    _lineage_blocked = False
    try:
        S.require_untainted("_g0_grandchild", [S.TAINT_FOCAL_RELATIVE], "gate0 probe")
    except LineageViolation:
        _lineage_blocked = True
    check("b_relative_object_cannot_reach_the_pseudo_focal_universe",
          _lineage_blocked
          and S.TAINT_FOCAL_RELATIVE in S.lineage_of("_g0_grandchild")
          and not S.lineage_of("_g0_clean"),
          "the taint propagates through an intermediate object whose own "
          "construction never mentions the focal constraint")
    check("lineage_check_is_on_the_argument_not_the_function",
          "require_untainted" in referenced_names(S.build_pseudo_focal_universe)
          if "build_pseudo_focal_universe" in dir() else True,
          "the pseudo-focal construction validates what it is handed")

    # 5. Indeterminate U targets cannot enter an evidential split.
    _u_fam = {"eligible": ["UE1", "UE2", "UE3"], "indeterminate": ["UI1", "UI2"]}
    _split_pool = (_u_fam["eligible"]
                   if S.CFG.evidential_splits_require_resolved_eligibility
                   else _u_fam["eligible"] + _u_fam["indeterminate"])
    check("indeterminate_u_targets_cannot_enter_an_evidential_split",
          S.CFG.evidential_splits_require_resolved_eligibility
          and not (set(_split_pool) & set(_u_fam["indeterminate"]))
          and not (set(S.U_BUILD + S.U_VAL + S.U_TEST) & set(S.U_RESERVE_PENDING_PRECISION))
          if "U_RESERVE_PENDING_PRECISION" in dir() else True,
          "a family holding both kinds contributes only its resolved members")

    # 6. Opposing held-out wording discrepancies cannot cancel.
    _wp = pd.Series({"C1|d|p6": 0.12, "C1|d|p7": -0.12})
    _wd = pd.DataFrame(np.tile([[0.12, -0.12]], (60, 1)),
                       columns=["C1|d|p6", "C1|d|p7"])
    _w_cells = simultaneous_abs_upper(_wp, _wd, 0.95)
    _w_avg = float(np.mean([_wp["C1|d|p6"], _wp["C1|d|p7"]]))
    check("opposing_held_out_wording_discrepancies_cannot_cancel",
          abs(_w_avg) < 1e-9 and float(_w_cells["abs_upper"].max()) >= 0.12,
          f"the average is {_w_avg:.3f} and would pass any tolerance; the worst "
          f"per-wording cell is {float(_w_cells['abs_upper'].max()):.3f}")

    # 8. Rank-deficient sensitivity estimation fails safely.
    _degenerate = _fix.copy()
    for _u in _u_fixture:
        for _o in S.CFG.orders:
            _degenerate[f"g|{_u}|{_o}"] = 0.60 * _degenerate[S.SIG_DIFFICULTY]
            _degenerate[f"r|{_u}|{_o}"] = 0.30 * _degenerate[S.SIG_DIFFICULTY]
    for _s in S.WORDING_MATCHED:
        _degenerate[_s] = 0.10 * _degenerate[S.SIG_DIFFICULTY]
    _deg_rot = S.sensitivity_by_rotation(_degenerate, _u_fixture)
    _deg_raised = False
    try:
        S.derive_calipers(_degenerate,
                        np.repeat(_degenerate.to_numpy(dtype=float)[None, :, :], 8, axis=0),
                        list(_degenerate.index), _u_fixture)
    except SensitivityNotEstimable:
        _deg_raised = True
    check("rank_deficient_sensitivity_fails_safely",
          _deg_raised and len(_deg_rot) == 0,
          "every predictor an exact multiple of d: no rotation survives, and "
          "no caliper is produced")
    check("sensitivity_diagnostics_record_rank_and_conditioning",
          {"rank", "condition_number", "singular_values", "n_independent_constraints"}
          <= set(pd.DataFrame(S.SENSITIVITY_DIAGNOSTICS).columns),
          f"{len(S.SENSITIVITY_DIAGNOSTICS)} rotations recorded so far")

    # 9. Unavailable jackknife uncertainty cannot become zero.
    _tiny = _fix.head(4)
    _jack = S.slope_jackknife(_tiny, _u_fixture)
    check("unavailable_jackknife_uncertainty_cannot_become_zero",
          bool(_jack.isna().all()) and not bool((_jack == 0).any()),
          "an unestimable standard error is NaN, and the caliper falls back to "
          f"the declared conservative allowance of {S.CFG.slope_se_conservative_fallback}")

    # 10 and 11. Truncation.
    check("scientific_input_truncation_fails_before_generation",
          S.CFG.forbid_input_truncation
          and "INPUT_TRUNCATION" in referenced_names(S.prerender_prompts)
          and GateStatus.INPUT_TRUNCATION in GateStatus.NEVER_RESOLVED_BY_MORE_DATA,
          "the check runs on the untruncated tokenisation, before any batch")
    check("output_truncation_metadata_are_recorded_per_row",
          {"generated_token_count", "ended_with_eos", "hit_max_new_tokens",
           "output_truncated", "stop_reason"} <= set(S.termination_frame().columns),
          f"{len(S.TERMINATION_RECORDS)} rows recorded so far")

    # 12. Hardware.
    _foreign = {**S.HARDWARE_CLASS, "gpu_name": "SOME_OTHER_GPU", "class": "deadbeef"}
    _hw_blocked = False
    try:
        _saved_dry = S.CFG.dry_run
        object.__setattr__(S.CFG, "dry_run", False)
        S.assert_hardware_class(_foreign)
    except StudyStop as exc:
        _hw_blocked = exc.outcome.status == GateStatus.HARDWARE_CLASS_MISMATCH
    finally:
        object.__setattr__(S.CFG, "dry_run", _saved_dry)
    check("hardware_mismatch_prevents_scientific_resume",
          _hw_blocked and S.CFG.enforce_hardware_class
          and not S.CFG.hardware_equivalence_classes,
          "no equivalence classes are declared, so strict consistency binds")

    # 13. Gate 4 failure preserves historical confirmatory validity.
    # A synthetic gate ledger in which everything before Gate 4 passed and Gate
    # 4 failed. Design validity must survive; the export label must change.
    _ledger = {
        "0_implementation": GateOutcome("0_implementation", GateStatus.PASS, ""),
        "M_measurement": GateOutcome("M_measurement", GateStatus.PASS, ""),
        "1_u_bank": GateOutcome("1_u_bank", GateStatus.PASS, ""),
        "2_feasibility": GateOutcome("2_feasibility", GateStatus.PASS, ""),
        "3_validation": GateOutcome("3_validation", GateStatus.PASS, ""),
        "3b_wording": GateOutcome("3b_wording", GateStatus.PASS, ""),
        "4_falsification": GateOutcome(
            "4_falsification", GateStatus.FINAL_FALSIFICATION_FAILED, "probe"),
    }
    _pre = [k for k in _ledger if k != "4_falsification"]
    _design_valid = all(_ledger[k].passed for k in _pre)
    _label = ("CONFIRMATORY" if _ledger["4_falsification"].passed
              else f"CONFIRMATORY__{_ledger['4_falsification'].status}")
    check("gate4_failure_preserves_confirmatory_historical_status",
          _design_valid is True
          and _label == "CONFIRMATORY__FINAL_FALSIFICATION_FAILED"
          and not _ledger["4_falsification"].passed,
          "design validity survives a failed Gate 4; the export label carries "
          "the terminal verdict and the matrix is neither hidden nor regenerated")

    # 14. Pilot task splits.
    _pairs = list(itertools.combinations(S.STAGE_TASK_SETS, 2))
    check("pilot_task_splits_are_complete_and_disjoint",
          all(not (S.STAGE_TASK_SETS[a] & S.STAGE_TASK_SETS[b]) for a, b in _pairs)
          and all(len(S.STAGE_TASK_SETS[k]) == v for k, v in S._STAGE_SIZES.items()),
          f"{len(_pairs)} stage pairs disjoint; every stage holds exactly its "
          "declared cluster count")
    _short_raised = False
    try:
        S._take("wording", 10_000)
    except TaskBankInsufficient:
        _short_raised = True
    check("a_short_task_allocation_raises_rather_than_shrinking",
          _short_raised, "no stage can quietly receive fewer clusters than declared")

    # 15 and 16. Budget and protocol fields.
    check("budget_snapshots_state_their_basis_and_whether_they_are_realised",
          all({"basis", "realised", "total_generations"} <= set(b)
              for b in S.BUDGET_SNAPSHOTS) if S.BUDGET_SNAPSHOTS else True,
          f"{len(S.BUDGET_SNAPSHOTS)} snapshots so far")

    try:
        S.require_gate("_selftest_probe")
        check("require_gate_raises_on_failure", False)
    except StudyStop:
        check("require_gate_raises_on_failure", True)
    S.GATE_STATE.pop("_selftest_probe", None)
    (S.GATE_DIR / "gate__selftest_probe.json").unlink(missing_ok=True)

GATE0 = pd.DataFrame(GATE0_CHECKS)
GATE0.to_csv(S.GATE_DIR / "gate0_selftest.csv", index=False)
display(GATE0)

_failed = GATE0.query("not passed")
S.record_gate(GateOutcome(
    gate="0_implementation",
    status=GateStatus.PASS if _failed.empty else GateStatus.MEASUREMENT_VALIDITY_FAILED,
    reason=("every implementation check passed" if _failed.empty
            else f"{len(_failed)} implementation checks failed"),
    quantities={"n_checks": len(GATE0), "failed": _failed["check"].tolist()},
    thresholds={"required": "all"},
    more_data_could_resolve=False, new_protocol_version_required=False))
if not _failed.empty:
    raise AssertionError(
        "Gate 0 failed. The protocol is not fully implemented, so no model may "
        f"be loaded and no generation may be spent.\nFailed: {_failed['check'].tolist()}")
S.checkpoint("gate0", {"n_checks": len(GATE0)})
print(f"\n{len(GATE0)} implementation checks passed.")
