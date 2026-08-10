def build_pseudo_focal_universe(source_name: str, source_ids: list[str],
                                sig: pd.DataFrame, sig_draws: np.ndarray,
                                calipers: pd.DataFrame,
                                valid_verifiers: set[str]) -> pd.DataFrame:
    """Hard eligibility over a source that is required to be B-independent.

    The check is on the ARGUMENT, at the call. Substituting a B-filtered object
    here raises even though this function and hard_eligible_universe() contain
    no B-relative symbol between them -- which is precisely the hole in v14's
    disassembly-based audit.
    """
    require_untainted(source_name, [TAINT_FOCAL_RELATIVE, TAINT_UVAL_OBSERVED,
                                    TAINT_CONFIRMATORY],
                      "the pseudo-focal universe")
    return hard_eligible_universe(
        source_ids, sig=sig, sig_draws=sig_draws, calipers=calipers,
        valid_verifiers=valid_verifiers)


with phase("pseudo_focal_cohort"):
    # Drawn from the DECLARED eligible universe, never from the prescreened
    # primary pool. The two dataflows meet nowhere before this point.
    HARD_ELIGIBILITY = build_pseudo_focal_universe(
        "DECLARED_ELIGIBLE", DECLARED_ELIGIBLE, SIGNATURE, SIG_DRAWS_RAW,
        CALIPERS, VALID_VERIFIERS)
    HARD_ELIGIBILITY.to_csv(GATE_DIR / "hard_eligibility_full.csv")
    PSEUDO_UNIVERSE = sorted(HARD_ELIGIBILITY.query("hard_eligible").index)
    declare_lineage("PF_UNIVERSE", parents=["DECLARED_ELIGIBLE"])

display(HARD_ELIGIBILITY[["hard_eligible", "agreement_with_A", "agreement_with_B",
                          "duplicate_of", "n_imprecise_components",
                          "rejection_reasons"]])
print(f"hard-eligible pseudo-focal universe: {len(PSEUDO_UNIVERSE)} constraints")
print(f"  {PSEUDO_UNIVERSE}")
print(f"pseudo-focal universe lineage: {sorted(lineage_of('PF_UNIVERSE')) or '(untainted)'}")
print(f"primary pool lineage         : {sorted(lineage_of('PRESCREEN_KEPT'))}")
display(lineage_table())


def donors_for(pseudo_focal: str, universe: list[str]) -> Optional[list[str]]:
    """Apply the frozen procedure to a pseudo-focal drawn from the universe."""
    gaps, gap_se = mismatch_table(SIGNATURE, SIG_DRAWS_RAW, MEASURED_IDS, U_BUILD,
                                  pseudo_focal, COUPLING_SE)
    pool = [c for c in universe if c != pseudo_focal]
    adm = admit_candidates(gaps, gap_se, CALIPERS,
                           CONSTRAINTS[pseudo_focal].generative_scope, pool)
    eligible = sorted(adm.query("eligible").index)
    if len(eligible) < CFG.reference_count:
        return None
    panel, _ = select_panel(eligible, SIGNATURE, pseudo_focal,
                            CFG.reference_count, CFG.mahalanobis_ridge)
    return panel


_cohort_rows, _donor_union = [], set()
for _q in PSEUDO_UNIVERSE:
    try:
        _panel = donors_for(_q, PSEUDO_UNIVERSE)
    except StudyStop:
        _panel = None
    _cohort_rows.append({"pseudo_focal": _q, "evaluable": _panel is not None,
                         "donors": ";".join(_panel or [])})
    if _panel:
        _donor_union.update(_panel)
# Explicit columns: an empty universe is a reportable state, not a KeyError.
PSEUDO_COHORT_TABLE = pd.DataFrame(
    _cohort_rows, columns=["pseudo_focal", "evaluable", "donors"]
).astype({"evaluable": bool}).set_index("pseudo_focal")
PSEUDO_COHORT_TABLE.to_csv(GATE_DIR / "pseudo_focal_cohort.csv")
display(PSEUDO_COHORT_TABLE)

PSEUDO_COHORT, _cohort_status = evaluate_pseudo_focal_cohort(
    PSEUDO_COHORT_TABLE.query("evaluable").index.tolist(), CFG.min_pseudo_focal)

# Why the universe is small decides the remedy, and the remedy is part of the
# status. Imprecision is a data problem that more calibration clusters fix.
# Duplication, scope and entailment are pool problems that only a different
# declared bank can fix. Reporting one as the other sends the reader to a
# remedy that cannot work.
_excluded = HARD_ELIGIBILITY.query("not hard_eligible")
_imprecise_only = [c for c in _excluded.index
                   if int(_excluded.at[c, "n_imprecise_components"]) > 0
                   and _excluded.at[c, "rejection_reasons"].startswith(
                       "own measurement too imprecise")]
_precision_bound = (len(PSEUDO_UNIVERSE) + len(_imprecise_only)
                    >= CFG.min_pseudo_focal + 1)

if _cohort_status != GateStatus.PASS:
    stop("3_validation", GateStatus.REFERENCE_VALIDATION_NOT_EVALUABLE,
         f"only {len(PSEUDO_COHORT)} constraints in the independent universe "
         f"could be given {CFG.reference_count} donors",
         quantities={"universe": PSEUDO_UNIVERSE, "evaluable": PSEUDO_COHORT,
                     "n_evaluable": len(PSEUDO_COHORT),
                     "excluded_for_imprecision_only": _imprecise_only,
                     "limiting_factor": ("calibration precision"
                                         if _precision_bound else "the declared pool")},
         thresholds={"min_pseudo_focal": CFG.min_pseudo_focal},
         more_data_could_resolve=_precision_bound,
         new_protocol_version_required=not _precision_bound,
         message=f"""
REFERENCE_VALIDATION_NOT_EVALUABLE.

Fewer than {CFG.min_pseudo_focal} constraints in the hard-eligible universe can themselves be
given {CFG.reference_count} donors, so the matching procedure cannot be validated at all. That
{CFG.focal_id} happens to have {CFG.reference_count} admissible references is not evidence that the
procedure works: it is the claim under test.

  limiting factor : {"calibration precision" if _precision_bound else "the declared pool"}
  universe        : {len(PSEUDO_UNIVERSE)} hard-eligible
  excluded solely for imprecision: {len(_imprecise_only)}

{"More calibration task clusters would enlarge this universe: the excluded constraints are measurable in principle and fail only the own-measurement precision rule." if _precision_bound else "More data will not help. The excluded constraints fail on duplication, scope or entailment, which are properties of the declared pool and change only with a new protocol version."}

Confirmation is NOT authorized. This is a distinct status from
REFERENCE_VALIDATION_FAILED, which would mean the procedure was evaluated and
did not work.
""")
    # Dry-run bypass only: a nominal cohort so the later cells can be exercised.
    PSEUDO_COHORT = (PSEUDO_COHORT_TABLE.index.tolist()
                     or sorted(DECLARED_ELIGIBLE))[:CFG.min_pseudo_focal]
    _donor_union.update(PSEUDO_COHORT)

# Frozen before U_val exists. Everything U_val will ever be measured against.
U_VAL_MEASURED_IDS = sorted(
    set(PSEUDO_COHORT) | set(_donor_union) | {CFG.focal_id} | set(SELECTED_REFERENCES))
PSEUDO_FOCAL_FREEZE = {
    "universe": PSEUDO_UNIVERSE, "cohort": PSEUDO_COHORT,
    "donor_union": sorted(_donor_union),
    "u_val_measured_ids": U_VAL_MEASURED_IDS,
    # Asserted only because the lineage says so, not because a function was
    # inspected. If any ancestor were B-relative the construction above would
    # have raised before reaching this line.
    "independent_of_focal": sorted(lineage_of("PF_UNIVERSE")) == [],
    "pf_universe_lineage": sorted(lineage_of("PF_UNIVERSE")),
    "primary_pool_lineage": sorted(lineage_of("PRESCREEN_KEPT")),
    "frozen_before_u_val_generation": True,
}
durable_write(GATE_DIR / "pseudo_focal_freeze.json",
              json.dumps(PSEUDO_FOCAL_FREEZE, indent=2))
print(f"\ncohort ({len(PSEUDO_COHORT)}): {PSEUDO_COHORT}")
print(f"donor union ({len(_donor_union)}): {sorted(_donor_union)}")
print(f"U_val will be measured for {len(U_VAL_MEASURED_IDS)} constraints.")
# ---------------------------------------------------------------- snapshot 4
# The exact frozen U_val design: the measured-id set, the cohort and the donor
# union are all known now, so this snapshot is the realised cost, not a guess.
record_budget(
    "4_after_pseudo_focal_freeze",
    f"frozen U_VAL_MEASURED_IDS ({len(U_VAL_MEASURED_IDS)}), cohort "
    f"({len(PSEUDO_COHORT)}), donor union ({len(_donor_union)})",
    realised=True,
    generations={
        "calibration_u_val": (
            len(CALIBRATION_TASKS) * len(CFG.calibration_seeds)
            * len(U_VAL_MEASURED_IDS) * (1 + 2 * len(U_VAL)) * 2 // 2),
        "wording_validation": (
            len(WORDING_TASKS) * len(CFG.wording_seeds)
            * len(CFG.paraphrase_holdout) * (1 + len(SELECTED_REFERENCES))
            * (1 + 2 * len(U_VAL))),
    },
    seconds_per_generation=SECONDS_PER_GENERATION,
    notes=("v14 assumed a fixed U_val measured set and a fixed donor union. "
           "Both follow from the data and are only knowable here."))
display(budget_frame().T)
checkpoint("pseudo_focal_cohort", PSEUDO_FOCAL_FREEZE)
