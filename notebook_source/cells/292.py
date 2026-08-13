with phase("pool_audit"):
    _natural = [c for c in PRESCREEN_KEPT if CONSTRAINTS[c].origin == "cse_pool"]
    _shadows = [c for c in PRESCREEN_KEPT if CONSTRAINTS[c].origin == "shadow"]
    _variants = [c for c in _shadows if CONSTRAINTS[c].rule_family
                 in {"min_words_per_sentence", "n_long_words_per_sentence"}]
    POOL_VARIANTS: dict[str, list[str]] = {
        "natural_only": _natural,
        "natural_plus_parameter_variants": sorted(set(_natural) | set(_variants)),
        "full_declared_pool": sorted(PRESCREEN_KEPT),
    }
    _families = sorted({CONSTRAINTS[c].rule_family for c in PRESCREEN_KEPT})
    for fam in _families:
        POOL_VARIANTS[f"leave_out_{fam}"] = sorted(
            c for c in PRESCREEN_KEPT if CONSTRAINTS[c].rule_family != fam)

    rows = []
    for name, pool in POOL_VARIANTS.items():
        if not pool:
            continue
        adm = admit_candidates(GAPS, GAP_SE, CALIPERS, FOCAL_SCOPE, pool)
        eligible = sorted(adm.query("eligible").index)
        rows.append({
            "pool": name, "n_in_pool": len(pool),
            "n_declared_eligible": len([c for c in pool if c in DECLARED_ELIGIBLE]),
            "n_passing_all_calipers": len(eligible),
            "six_control_identification": len(eligible) >= CFG.reference_count,
            "eligible": ";".join(eligible[:8])})
POOL_AUDIT = pd.DataFrame(rows).set_index("pool")
POOL_AUDIT.to_csv(GATE_DIR / "pool_dependence_audit.csv")
display(POOL_AUDIT)

_necessary = [r.replace("leave_out_", "") for r, row in POOL_AUDIT.iterrows()
              if r.startswith("leave_out_") and not row["six_control_identification"]]
print(f"""
Families whose removal destroys six-control identification: {_necessary or "none"}

Identification that rests on a single authored family is conditional on that
family. It is reported here and repeated at the freeze; it does not invalidate
purpose-built shadows and it does not change the declared primary pool, because
changing the pool after seeing this table would be exactly the specification
search the protocol forbids.
""")
checkpoint("pool_audit", {"necessary_families": _necessary})
