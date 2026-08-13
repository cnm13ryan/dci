"""Stage 292 — migrated from notebook cell 292.py (pool_dependence).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/292.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell


with S.phase("pool_audit"):
    _natural = [c for c in S.PRESCREEN_KEPT if S.CONSTRAINTS[c].origin == "cse_pool"]
    _shadows = [c for c in S.PRESCREEN_KEPT if S.CONSTRAINTS[c].origin == "shadow"]
    _variants = [c for c in _shadows if S.CONSTRAINTS[c].rule_family
                 in {"min_words_per_sentence", "n_long_words_per_sentence"}]
    POOL_VARIANTS: dict[str, list[str]] = {
        "natural_only": _natural,
        "natural_plus_parameter_variants": sorted(set(_natural) | set(_variants)),
        "full_declared_pool": sorted(S.PRESCREEN_KEPT),
    }
    _families = sorted({S.CONSTRAINTS[c].rule_family for c in S.PRESCREEN_KEPT})
    for fam in _families:
        POOL_VARIANTS[f"leave_out_{fam}"] = sorted(
            c for c in S.PRESCREEN_KEPT if S.CONSTRAINTS[c].rule_family != fam)

    rows = []
    for name, pool in POOL_VARIANTS.items():
        if not pool:
            continue
        adm = S.admit_candidates(S.GAPS, S.GAP_SE, S.CALIPERS, S.FOCAL_SCOPE, pool)
        eligible = sorted(adm.query("eligible").index)
        rows.append({
            "pool": name, "n_in_pool": len(pool),
            "n_declared_eligible": len([c for c in pool if c in S.DECLARED_ELIGIBLE]),
            "n_passing_all_calipers": len(eligible),
            "six_control_identification": len(eligible) >= S.CFG.reference_count,
            "eligible": ";".join(eligible[:8])})
S.POOL_AUDIT = pd.DataFrame(rows).set_index("pool")
S.POOL_AUDIT.to_csv(S.GATE_DIR / "pool_dependence_audit.csv")
display(S.POOL_AUDIT)

_necessary = [r.replace("leave_out_", "") for r, row in S.POOL_AUDIT.iterrows()
              if r.startswith("leave_out_") and not row["six_control_identification"]]
print(f"""
Families whose removal destroys six-control identification: {_necessary or "none"}

Identification that rests on a single authored family is conditional on that
family. It is reported here and repeated at the freeze; it does not invalidate
purpose-built shadows and it does not change the declared primary pool, because
changing the pool after seeing this table would be exactly the specification
search the protocol forbids.
""")
S.checkpoint("pool_audit", {"necessary_families": _necessary})
