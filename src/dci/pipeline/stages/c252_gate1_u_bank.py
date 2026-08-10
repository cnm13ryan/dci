"""Stage 252 — migrated from notebook cell 252.py (gate1_u_bank).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/252.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.stats import bootstrap_functional, percentile_ci  # noqa: F401
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.provenance.hashes import stable_int  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

S.require_gate("0_implementation", "M_measurement")

with S.phase("screen_u"):
    screening_design = S.build_screening_design()
    screening_design.to_csv(S.DESIGN_DIR / "screening_design.csv", index=False)
    screening_responses = S.run_generation_stage(screening_design, "screening")
    screening_scores = S.score_responses(screening_responses)
    _err = 1.0 - screening_responses["generation_ok"].mean()
    if _err > 0.10:
        raise RuntimeError(f"{_err:.1%} of screening generations failed.")

    _screen_table = S.task_cell_table(screening_scores.query("is_measured"), "fail")
    partner = S.CFG.u_screen_partner_id

    def _screen_fn(means: pd.Series) -> dict[str, float]:
        out = {}
        for u in S.U_CANDIDATE_IDS:
            out[f"{u}::isolated"] = S.cell_mean(means, S.iso_condition(u), u)
            out[f"{u}::composed"] = S.cell_mean(means, S.pair_condition(u, partner, u), u)
        return out

    _screen_point, _screen_draws = bootstrap_functional(
        _screen_table, _screen_fn, S.CFG.bootstrap_reps, S.CFG.base_seed + 101)
    _screen_ci = percentile_ci(_screen_draws, S.CFG.u_screen_confidence)


def _classify(lo: float, hi: float, low: float, high: float) -> str:
    """Wholly inside, wholly outside, or unresolved against the band."""
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "unmeasurable"
    if lo >= low and hi <= high:
        return "inside"
    if hi < low or lo > high:
        return "outside"
    return "indeterminate"


rows = []
for u in S.U_CANDIDATE_IDS:
    iso, comp = float(_screen_point[f"{u}::isolated"]), float(_screen_point[f"{u}::composed"])
    iso_lo, iso_hi = _screen_ci.loc[f"{u}::isolated", ["ci_lower", "ci_upper"]]
    cmp_lo, cmp_hi = _screen_ci.loc[f"{u}::composed", ["ci_lower", "ci_upper"]]
    iso_class = _classify(iso_lo, iso_hi, S.CFG.u_screen_isolated_low, S.CFG.u_screen_isolated_high)
    cmp_class = _classify(cmp_lo, cmp_hi, S.CFG.u_screen_composed_low, S.CFG.u_screen_composed_high)
    if iso_class == "inside" and cmp_class == "inside":
        verdict = "eligible"
    elif "indeterminate" in (iso_class, cmp_class) or "unmeasurable" in (iso_class, cmp_class):
        verdict = "indeterminate"
    else:
        verdict = "ineligible"
    rows.append({
        "constraint_id": u, "family": S.CONSTRAINTS[u].u_family,
        "isolated_fail": iso, "isolated_lo": float(iso_lo), "isolated_hi": float(iso_hi),
        "isolated_class": iso_class,
        "composed_fail": comp, "composed_lo": float(cmp_lo), "composed_hi": float(cmp_hi),
        "composed_class": cmp_class,
        "composition_shift": comp - iso, "verdict": verdict})

U_SCREEN = pd.DataFrame(rows).set_index("constraint_id")
U_SCREEN.to_csv(S.GATE_DIR / "u_screening.csv")
display(U_SCREEN.round(3))

_eligible_by_family = {f: sorted(U_SCREEN.query("verdict == 'eligible' and family == @f").index)
                       for f in S.CFG.u_families}
_indet_by_family = {f: sorted(U_SCREEN.query("verdict == 'indeterminate' and family == @f").index)
                    for f in S.CFG.u_families}
_need = {f: (S.CFG.u_min_eligible_per_family if f in S.CFG.u_build_families else 2)
         for f in S.CFG.u_families}
_short = [f for f in S.CFG.u_families if len(_eligible_by_family[f]) < _need[f]]
_rescuable = [f for f in _short
              if len(_eligible_by_family[f]) + len(_indet_by_family[f]) >= _need[f]]

print("\neligible per family    :", {f: len(v) for f, v in _eligible_by_family.items()})
print("indeterminate per family:", {f: len(v) for f, v in _indet_by_family.items()})
print("required per family     :", _need)

_quant = {"eligible": {f: len(v) for f, v in _eligible_by_family.items()},
          "indeterminate": {f: len(v) for f, v in _indet_by_family.items()},
          "screening_clusters": len(S.SCREENING_TASKS)}

if not _short:
    S.record_gate(GateOutcome("1_u_bank", GateStatus.PASS,
                            "every family has enough targets with resolved dynamic range",
                            quantities=_quant, thresholds=_need))
elif _rescuable:
    S.stop("1_u_bank", GateStatus.U_PRECISION_INSUFFICIENT,
         f"families {_rescuable} would have enough targets if the indeterminate "
         "candidates were resolved",
         quantities=_quant, thresholds=_need,
         more_data_could_resolve=True, new_protocol_version_required=False,
         message=f"""
U_PRECISION_INSUFFICIENT for families {_rescuable}.

Their candidates are not at ceiling or floor; the screening interval simply
straddles a band edge, so they cannot be classified either way at
{len(S.SCREENING_TASKS)} screening task clusters.

Collect more screening clusters and rerun. Do NOT widen the dynamic-range band
to obtain three eligible targets: a target that cannot register burden is
useless however the band is drawn, and this status exists precisely so that the
two situations are not confused.
""")
else:
    S.stop("1_u_bank", GateStatus.U_BANK_NOT_IDENTIFIED,
         f"families {_short} have too few targets with usable dynamic range, "
         "and the classification is resolved",
         quantities=_quant, thresholds=_need,
         more_data_could_resolve=False, new_protocol_version_required=True,
         message=f"""
U_BANK_NOT_IDENTIFIED for families {_short}.

Measurement is adequate; the targets themselves lack dynamic range. Author
further candidates in the short families with parameters aimed at mid
difficulty and rerun screening. That is a change to the declared bank and
therefore a new protocol version.
""")

# ------------------------------- frozen stratified split, one per build family
#
# Only targets whose dynamic range is RESOLVED may enter an evidential split.
# v14 passed Gate 1 on the eligible count and then drew split members from
# eligible + indeterminate, so a target the screen could not classify could sit
# in U_build, U_val or U_test and carry weight in the result. Indeterminate
# targets wait in U_RESERVE_PENDING_PRECISION until more screening resolves them.
_split_rng = np.random.default_rng(stable_int("u_split|v15") + S.CFG.base_seed)
S.U_BUILD, S.U_VAL, S.U_TEST, U_RESERVE = [], [], [], []
S.U_RESERVE_PENDING_PRECISION = sorted(
    {c for members in _indet_by_family.values() for c in members})
_split_source = (dict(_eligible_by_family) if S.CFG.evidential_splits_require_resolved_eligibility
                 else {f: _eligible_by_family[f] + _indet_by_family[f]
                       for f in _eligible_by_family})
for fam in S.CFG.u_build_families:
    members = list(dict.fromkeys(_split_source.get(fam, [])))
    if len(members) < 3:
        # Only reachable under a dry-run bypass, where the gate above already
        # recorded that the bank is not usable. Members stay distinct so the
        # disjointness assertion still means something, and each one is marked
        # so that no downstream reader mistakes it for a resolved target.
        members += [c for c in U_SCREEN.query("family == @fam").index
                    if c not in members]
        S.log_departure(
            "screening", f"family {fam} supplies 3 RESOLVED-eligible targets",
            f"padded to 3 from unresolved candidates",
            "DRY RUN ONLY. Unreachable when dry_run is False, because Gate 1 "
            "halts first. Nothing computed from these targets is evidence.")
    shuffled = [members[i] for i in _split_rng.permutation(len(members))]
    S.U_BUILD.append(shuffled[0])
    S.U_VAL.append(shuffled[1])
    S.U_TEST.append(shuffled[2])
    U_RESERVE.extend(shuffled[3:])

# Bridge targets go to validation and test only: they share A's segmentation
# span, so using them to build the features that define comparability would be
# defining the focal pathway away rather than probing transport to it.
# The same rule binds the bridge family: an unresolved bridge target may not
# validate or falsify anything.
_bridge_pool = list(dict.fromkeys(
    _split_source.get("bridge", _eligible_by_family.get("bridge", []))))
_bridge_shuffled = [_bridge_pool[i] for i in _split_rng.permutation(len(_bridge_pool))]
if len(_bridge_shuffled) >= 2:
    S.U_VAL.append(_bridge_shuffled[0])
    S.U_TEST.append(_bridge_shuffled[1])
    U_RESERVE.extend(_bridge_shuffled[2:])
    S.BRIDGE_AVAILABLE = True
else:
    S.BRIDGE_AVAILABLE = False
    S.log_departure(
        "screening", "one bridge target in each of U_val and U_test",
        f"only {len(_bridge_shuffled)} bridge targets survived screening",
        "the transport limitation is reported rather than invented: without a "
        "sentence-scoped validation target, nothing tests generalisation into "
        "A's own scope, and every validation result is conditional on "
        "whole-answer targets.")

S.U_BUILD, S.U_VAL, S.U_TEST = sorted(S.U_BUILD), sorted(S.U_VAL), sorted(S.U_TEST)
assert len({*S.U_BUILD, *S.U_VAL, *S.U_TEST}) == len(S.U_BUILD) + len(S.U_VAL) + len(S.U_TEST), \
    "the three splits must be disjoint"

_indeterminate_in_splits = sorted(
    set(S.U_BUILD + S.U_VAL + S.U_TEST) & set(S.U_RESERVE_PENDING_PRECISION))
if _indeterminate_in_splits and S.CFG.evidential_splits_require_resolved_eligibility:
    if S.CFG.dry_run:
        S.log_departure(
            "screening", "no unresolved target in any evidential split",
            f"{_indeterminate_in_splits} were padded in",
            "DRY RUN ONLY. Gate 1 halts before this point when dry_run is False.")
    else:
        raise AssertionError(
            f"{_indeterminate_in_splits} have unresolved dynamic range and "
            "cannot enter an evidential split. This is unreachable: Gate 1 "
            "stops first.")
S.declare_lineage("U_BUILD")
S.declare_lineage("U_VAL")
S.declare_lineage("U_TEST")

S.U_SPLIT = {
    "u_build": S.U_BUILD, "u_val": S.U_VAL, "u_test": S.U_TEST,
    "u_reserve": sorted(set(U_RESERVE)),
    "u_reserve_pending_precision": S.U_RESERVE_PENDING_PRECISION,
    "architecture": S.CFG.u_split_architecture,
    "evidential_splits_resolved_only": S.CFG.evidential_splits_require_resolved_eligibility,
    "bridge_available": S.BRIDGE_AVAILABLE,
    "rule": ("frozen stratified randomisation, one eligible candidate per build "
             "family per split, plus one bridge target in validation and test"),
    "roles": {"u_build": "designs features and calipers",
              "u_val": "one-shot validation at Gate 3; may veto the design",
              "u_test": "falsification after the freeze; may alter nothing"},
}
S.durable_write(S.GATE_DIR / "u_split.json", json.dumps(S.U_SPLIT, indent=2))
print(f"\nU_build : {S.U_BUILD}\nU_val   : {S.U_VAL}\nU_test  : {S.U_TEST}")
print(f"reserve : {sorted(set(U_RESERVE))}   bridge available: {S.BRIDGE_AVAILABLE}")
# ---------------------------------------------------------------- snapshot 2
S.record_budget(
    "2_after_gate1_u_split",
    f"realised U split: |U_build|={len(S.U_BUILD)}, |U_val|={len(S.U_VAL)}, "
    f"|U_test|={len(S.U_TEST)}",
    realised=True,
    generations={
        "screening": len(screening_design),
        "calibration_u_build_per_wording": (
            len(S.CALIBRATION_TASKS) * len(S.CFG.calibration_seeds)
            * (1 + 2 * len(S.U_BUILD)) * 2),
    },
    seconds_per_generation=S.SECONDS_PER_GENERATION,
    notes=("calibration scales with |U_build| and with the number of measured "
           "constraints, which is now the whole declared-eligible universe "
           "rather than the prescreened pool, because the pseudo-focal "
           "validation may not inherit a B-relative filter."))
display(S.budget_frame().T)
S.checkpoint("gate1", S.U_SPLIT)
