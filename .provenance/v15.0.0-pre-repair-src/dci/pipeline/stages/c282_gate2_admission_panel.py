"""Stage 282 — migrated from notebook cell 282.py (gate2_admission_panel).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/282.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

S.FOCAL_SCOPE = S.CONSTRAINTS[S.CFG.focal_id].generative_scope

with S.phase("gate2_feasibility"):
    ELIGIBILITY = S.admit_candidates(S.GAPS, S.GAP_SE, S.CALIPERS, S.FOCAL_SCOPE, S.PRESCREEN_KEPT)
ELIGIBILITY.to_csv(S.GATE_DIR / "eligibility_log.csv")
display(ELIGIBILITY[["scope", "origin", "n_failed_components", "eligible",
                     "rejection_reasons"]])

_blocking = []
for comp in S.CALIPERS.index:
    col = f"adj_{comp}"
    if col not in ELIGIBILITY:
        continue
    delta = float(S.CALIPERS.at[comp, "caliper"])
    _blocking.append({"component": comp, "family": S.component_family(comp),
                      "order": S.component_order(comp) or "-", "caliper": delta,
                      "candidates_blocked": int((ELIGIBILITY[col] > delta).sum()),
                      "median_adjusted_gap": float(ELIGIBILITY[col].median())})
BLOCKING = pd.DataFrame(_blocking).set_index("component").sort_values(
    "candidates_blocked", ascending=False)
BLOCKING.to_csv(S.GATE_DIR / "blocking_components.csv")
display(BLOCKING.round(4))

_order_only = {}
for o in S.CFG.orders:
    comps = [c for c in S.CALIPERS.index if S.component_order(c) in (None, o)]
    _order_only[o] = int(S.admit_candidates(S.GAPS, S.GAP_SE, S.CALIPERS.loc[comps],
                                          S.FOCAL_SCOPE, S.PRESCREEN_KEPT)["eligible"].sum())
display(pd.Series(_order_only, name="n_eligible_using_only_this_order").to_frame())
print("The eligible set used below is the intersection: a candidate must clear "
      "the calipers at BOTH positions.")

_pool = [c for c in S.PRESCREEN_KEPT if c != S.CFG.focal_id]
SUPPORT = pd.DataFrame([{
    "component": comp, "focal": float(S.SIGNATURE.at[S.CFG.focal_id, comp]),
    "pool_min": float(S.SIGNATURE.loc[_pool, comp].min()),
    "pool_max": float(S.SIGNATURE.loc[_pool, comp].max()),
    "focal_inside": bool(S.SIGNATURE.loc[_pool, comp].min()
                         <= S.SIGNATURE.at[S.CFG.focal_id, comp]
                         <= S.SIGNATURE.loc[_pool, comp].max()),
} for comp in S.CALIPERS.index]).set_index("component")
SUPPORT.to_csv(S.GATE_DIR / "common_support.csv")
display(SUPPORT.round(3))
_unsupported = SUPPORT.query("not focal_inside").index.tolist()

ELIGIBLE_IDS = sorted(ELIGIBILITY.query("eligible").index)
print(f"\ncandidates clearing every caliper in both orders: {len(ELIGIBLE_IDS)} "
      f"(need exactly {S.CFG.reference_count})")

_detail = {"n_eligible": len(ELIGIBLE_IDS), "eligible": ELIGIBLE_IDS,
           "unsupported_components": _unsupported, "paraphrases_used": S.P_FINAL,
           "top_blocking": BLOCKING.head(5)["candidates_blocked"].to_dict()}

if len(ELIGIBLE_IDS) < S.CFG.reference_count or _unsupported:
    print("\nleave-one-component-out: how many would qualify without that rule")
    for comp in BLOCKING.head(10).index:
        keep = [c for c in S.CALIPERS.index if c != comp]
        print(f"  without {comp:28s} -> "
              f"{int(S.admit_candidates(S.GAPS, S.GAP_SE, S.CALIPERS.loc[keep], S.FOCAL_SCOPE, S.PRESCREEN_KEPT)['eligible'].sum())}")
    S.stop("2_feasibility", GateStatus.NOT_IDENTIFIED_SUPPORT,
         f"{len(ELIGIBLE_IDS)} admissible references and "
         f"{len(_unsupported)} components without common support",
         quantities=_detail, thresholds={"required": S.CFG.reference_count},
         more_data_could_resolve=False, new_protocol_version_required=True,
         message=f"""
NOT_IDENTIFIED_SUPPORT.

Precision was already sufficient at Gate 2a, so this is not a measurement
problem: under the prespecified definition of a comparable added constraint,
the current constraint universe does not contain six admissible references for
{S.CFG.focal_id} against {S.CFG.target_id}, and no amount of further data will create them.

  admissible references : {len(ELIGIBLE_IDS)} (exactly {S.CFG.reference_count} required)
  without common support: {_unsupported or "none"}

The leave-one-component-out table says which requirement binds. The legitimate
responses are to build additional constraints on that dimension and recalibrate
under a new protocol version, or to report non-identification. Widening a
caliper is not among them.
""")
    ELIGIBLE_IDS = sorted(S.PRESCREEN_KEPT)      # dry-run bypass only
    _detail["dry_run_bypass"] = True

S.SELECTED_REFERENCES, S.MATCH_DISTANCE = S.select_panel(
    ELIGIBLE_IDS, S.SIGNATURE, S.CFG.focal_id, S.CFG.reference_count, S.CFG.mahalanobis_ridge)
SELECTION = pd.DataFrame({"mahalanobis_to_focal": S.MATCH_DISTANCE,
                          "selected": [c in S.SELECTED_REFERENCES
                                       for c in S.MATCH_DISTANCE.index]}
                         ).sort_values("mahalanobis_to_focal")
SELECTION.to_csv(S.GATE_DIR / "reference_selection.csv")
display(SELECTION.round(3))
S.record_gate(GateOutcome("2_feasibility", GateStatus.PASS,
                        f"exactly {S.CFG.reference_count} individually admissible "
                        "references in both orders",
                        quantities={**_detail, "selected": S.SELECTED_REFERENCES},
                        thresholds={"required": S.CFG.reference_count}))
print(f"\nSelected panel (common to both orders): {S.SELECTED_REFERENCES}")

_iso = S.calibration_scores.query("order == 'isolated' and is_measured")
_length = _iso.groupby("constraint_id")["response_words"].mean()
BALANCE = pd.DataFrame([{
    "component": comp, "focal": float(S.SIGNATURE.at[S.CFG.focal_id, comp]),
    "panel_mean": float(S.SIGNATURE.loc[S.SELECTED_REFERENCES, comp].mean()),
    "caliper": float(S.CALIPERS.at[comp, "caliper"]), "matched_on": True,
} for comp in S.CALIPERS.index])
for feature in S.CFG.mediator_features:
    BALANCE.loc[len(BALANCE)] = {
        "component": feature, "focal": float(_length.get(S.CFG.focal_id, np.nan)),
        "panel_mean": float(_length.reindex(S.SELECTED_REFERENCES).mean()),
        "caliper": np.nan, "matched_on": False}
BALANCE["gap"] = BALANCE["focal"] - BALANCE["panel_mean"]
BALANCE.to_csv(S.SCORE_DIR / "balance_table.csv", index=False)
display(BALANCE.round(3))
print("Rows with matched_on = False were excluded by causal-variable audit. "
      "Realised response length lies downstream of the focal mechanism, so "
      "matching on it would condition on a mediator. Its imbalance is reported.")
S.checkpoint("gate2", {"selected": S.SELECTED_REFERENCES})

# ---------------------------------------------------------------- snapshot 3
S.record_budget(
    "3_after_prescreen_and_panel",
    f"retained primary pool ({len(S.PRESCREEN_KEPT)}), B-independent pseudo-focal "
    f"source ({len(S.DECLARED_ELIGIBLE)}), panel ({len(S.SELECTED_REFERENCES)})",
    realised=True,
    generations={
        "confirmatory": len(S.CONFIRMATORY_TASKS) * len(S.CFG.confirmatory_seeds)
                        * (1 + 2 * len(S.SELECTED_REFERENCES)),
        "placebo_u_test": len(S.PLACEBO_TASKS) * (1 + len(S.SELECTED_REFERENCES))
                          * len(S.U_TEST) * 2,
    },
    seconds_per_generation=S.SECONDS_PER_GENERATION,
    notes=("the prescreen narrows admission only. Calibration measures the "
           "whole declared-eligible universe, so the funnel saves less compute "
           "than v14 claimed and the difference is stated here."))
display(S.budget_frame().T)
