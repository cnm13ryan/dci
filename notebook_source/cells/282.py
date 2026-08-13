FOCAL_SCOPE = CONSTRAINTS[CFG.focal_id].generative_scope

with phase("gate2_feasibility"):
    ELIGIBILITY = admit_candidates(GAPS, GAP_SE, CALIPERS, FOCAL_SCOPE, PRESCREEN_KEPT)
ELIGIBILITY.to_csv(GATE_DIR / "eligibility_log.csv")
display(ELIGIBILITY[["scope", "origin", "n_failed_components", "eligible",
                     "rejection_reasons"]])

_blocking = []
for comp in CALIPERS.index:
    col = f"adj_{comp}"
    if col not in ELIGIBILITY:
        continue
    delta = float(CALIPERS.at[comp, "caliper"])
    _blocking.append({"component": comp, "family": component_family(comp),
                      "order": component_order(comp) or "-", "caliper": delta,
                      "candidates_blocked": int((ELIGIBILITY[col] > delta).sum()),
                      "median_adjusted_gap": float(ELIGIBILITY[col].median())})
BLOCKING = pd.DataFrame(_blocking).set_index("component").sort_values(
    "candidates_blocked", ascending=False)
BLOCKING.to_csv(GATE_DIR / "blocking_components.csv")
display(BLOCKING.round(4))

_order_only = {}
for o in CFG.orders:
    comps = [c for c in CALIPERS.index if component_order(c) in (None, o)]
    _order_only[o] = int(admit_candidates(GAPS, GAP_SE, CALIPERS.loc[comps],
                                          FOCAL_SCOPE, PRESCREEN_KEPT)["eligible"].sum())
display(pd.Series(_order_only, name="n_eligible_using_only_this_order").to_frame())
print("The eligible set used below is the intersection: a candidate must clear "
      "the calipers at BOTH positions.")

_pool = [c for c in PRESCREEN_KEPT if c != CFG.focal_id]
SUPPORT = pd.DataFrame([{
    "component": comp, "focal": float(SIGNATURE.at[CFG.focal_id, comp]),
    "pool_min": float(SIGNATURE.loc[_pool, comp].min()),
    "pool_max": float(SIGNATURE.loc[_pool, comp].max()),
    "focal_inside": bool(SIGNATURE.loc[_pool, comp].min()
                         <= SIGNATURE.at[CFG.focal_id, comp]
                         <= SIGNATURE.loc[_pool, comp].max()),
} for comp in CALIPERS.index]).set_index("component")
SUPPORT.to_csv(GATE_DIR / "common_support.csv")
display(SUPPORT.round(3))
_unsupported = SUPPORT.query("not focal_inside").index.tolist()

ELIGIBLE_IDS = sorted(ELIGIBILITY.query("eligible").index)
print(f"\ncandidates clearing every caliper in both orders: {len(ELIGIBLE_IDS)} "
      f"(need exactly {CFG.reference_count})")

_detail = {"n_eligible": len(ELIGIBLE_IDS), "eligible": ELIGIBLE_IDS,
           "unsupported_components": _unsupported, "paraphrases_used": P_FINAL,
           "top_blocking": BLOCKING.head(5)["candidates_blocked"].to_dict()}

if len(ELIGIBLE_IDS) < CFG.reference_count or _unsupported:
    print("\nleave-one-component-out: how many would qualify without that rule")
    for comp in BLOCKING.head(10).index:
        keep = [c for c in CALIPERS.index if c != comp]
        print(f"  without {comp:28s} -> "
              f"{int(admit_candidates(GAPS, GAP_SE, CALIPERS.loc[keep], FOCAL_SCOPE, PRESCREEN_KEPT)['eligible'].sum())}")
    stop("2_feasibility", GateStatus.NOT_IDENTIFIED_SUPPORT,
         f"{len(ELIGIBLE_IDS)} admissible references and "
         f"{len(_unsupported)} components without common support",
         quantities=_detail, thresholds={"required": CFG.reference_count},
         more_data_could_resolve=False, new_protocol_version_required=True,
         message=f"""
NOT_IDENTIFIED_SUPPORT.

Precision was already sufficient at Gate 2a, so this is not a measurement
problem: under the prespecified definition of a comparable added constraint,
the current constraint universe does not contain six admissible references for
{CFG.focal_id} against {CFG.target_id}, and no amount of further data will create them.

  admissible references : {len(ELIGIBLE_IDS)} (exactly {CFG.reference_count} required)
  without common support: {_unsupported or "none"}

The leave-one-component-out table says which requirement binds. The legitimate
responses are to build additional constraints on that dimension and recalibrate
under a new protocol version, or to report non-identification. Widening a
caliper is not among them.
""")
    ELIGIBLE_IDS = sorted(PRESCREEN_KEPT)      # dry-run bypass only
    _detail["dry_run_bypass"] = True

SELECTED_REFERENCES, MATCH_DISTANCE = select_panel(
    ELIGIBLE_IDS, SIGNATURE, CFG.focal_id, CFG.reference_count, CFG.mahalanobis_ridge)
SELECTION = pd.DataFrame({"mahalanobis_to_focal": MATCH_DISTANCE,
                          "selected": [c in SELECTED_REFERENCES
                                       for c in MATCH_DISTANCE.index]}
                         ).sort_values("mahalanobis_to_focal")
SELECTION.to_csv(GATE_DIR / "reference_selection.csv")
display(SELECTION.round(3))
record_gate(GateOutcome("2_feasibility", GateStatus.PASS,
                        f"exactly {CFG.reference_count} individually admissible "
                        "references in both orders",
                        quantities={**_detail, "selected": SELECTED_REFERENCES},
                        thresholds={"required": CFG.reference_count}))
print(f"\nSelected panel (common to both orders): {SELECTED_REFERENCES}")

_iso = calibration_scores.query("order == 'isolated' and is_measured")
_length = _iso.groupby("constraint_id")["response_words"].mean()
BALANCE = pd.DataFrame([{
    "component": comp, "focal": float(SIGNATURE.at[CFG.focal_id, comp]),
    "panel_mean": float(SIGNATURE.loc[SELECTED_REFERENCES, comp].mean()),
    "caliper": float(CALIPERS.at[comp, "caliper"]), "matched_on": True,
} for comp in CALIPERS.index])
for feature in CFG.mediator_features:
    BALANCE.loc[len(BALANCE)] = {
        "component": feature, "focal": float(_length.get(CFG.focal_id, np.nan)),
        "panel_mean": float(_length.reindex(SELECTED_REFERENCES).mean()),
        "caliper": np.nan, "matched_on": False}
BALANCE["gap"] = BALANCE["focal"] - BALANCE["panel_mean"]
BALANCE.to_csv(SCORE_DIR / "balance_table.csv", index=False)
display(BALANCE.round(3))
print("Rows with matched_on = False were excluded by causal-variable audit. "
      "Realised response length lies downstream of the focal mechanism, so "
      "matching on it would condition on a mediator. Its imbalance is reported.")
checkpoint("gate2", {"selected": SELECTED_REFERENCES})

# ---------------------------------------------------------------- snapshot 3
record_budget(
    "3_after_prescreen_and_panel",
    f"retained primary pool ({len(PRESCREEN_KEPT)}), B-independent pseudo-focal "
    f"source ({len(DECLARED_ELIGIBLE)}), panel ({len(SELECTED_REFERENCES)})",
    realised=True,
    generations={
        "confirmatory": len(CONFIRMATORY_TASKS) * len(CFG.confirmatory_seeds)
                        * (1 + 2 * len(SELECTED_REFERENCES)),
        "placebo_u_test": len(PLACEBO_TASKS) * (1 + len(SELECTED_REFERENCES))
                          * len(U_TEST) * 2,
    },
    seconds_per_generation=SECONDS_PER_GENERATION,
    notes=("the prescreen narrows admission only. Calibration measures the "
           "whole declared-eligible universe, so the funnel saves less compute "
           "than v14 claimed and the difference is stated here."))
display(budget_frame().T)
