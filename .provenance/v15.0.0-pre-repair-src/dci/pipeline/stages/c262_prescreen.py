"""Stage 262 — migrated from notebook cell 262.py (prescreen).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/262.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell

CFG = getattr(S, 'CFG', None)  # pandas @-resolution alias (read-only)

with S.phase("hard_eligibility"):
    DECLARED_ELIGIBILITY = S.hard_eligible_universe(
        S.CANDIDATE_IDS, valid_verifiers=S.VALID_VERIFIERS)
DECLARED_ELIGIBILITY.to_csv(S.GATE_DIR / "hard_eligibility_declared.csv")
display(DECLARED_ELIGIBILITY.round(3))

S.DECLARED_ELIGIBLE = sorted(DECLARED_ELIGIBILITY.query("hard_eligible").index)
S.declare_lineage("CANDIDATE_IDS")
S.declare_lineage("DECLARED_ELIGIBLE", parents=["CANDIDATE_IDS"])
print(f"declared-eligible candidates: {len(S.DECLARED_ELIGIBLE)} of {len(S.CANDIDATE_IDS)}")
print(f"rejected: {sorted(set(S.CANDIDATE_IDS) - set(S.DECLARED_ELIGIBLE))}")
print("""
Two candidate dataflows, kept apart on purpose.

  primary pool        DECLARED_ELIGIBLE -> prescreen (B-relative, a compute
                      funnel only) -> PRESCREEN_KEPT -> full uncertainty-aware
                      admission. Carries the focal_relative taint from the
                      prescreen onward.
  pseudo-focal        DECLARED_ELIGIBLE -> PF_UNIVERSE, with no B-relative
                      step anywhere in its ancestry. Untainted.

v14 built the pseudo-focal universe from PRESCREEN_KEPT, so it was downstream of
a B-relative filter while being reported as independent of B.""")

with S.phase("prescreen"):
    prescreen_design = S.build_prescreen_design()
    prescreen_scores = S.score_responses(
        S.run_generation_stage(prescreen_design, "prescreen"))
    _pre_rates = prescreen_scores.query("is_measured").groupby("constraint_id")["fail"].mean()

_focal_pre = float(_pre_rates.get(S.CFG.focal_id, np.nan))
PRESCREEN = pd.DataFrame({"isolated_fail_canonical": _pre_rates.reindex(S.DECLARED_ELIGIBLE)})
PRESCREEN["distance_to_focal"] = (PRESCREEN["isolated_fail_canonical"] - _focal_pre).abs()
PRESCREEN = PRESCREEN.sort_values("distance_to_focal")

_within = PRESCREEN.query("distance_to_focal <= @CFG.prescreen_difficulty_margin")
_floor = 2 * S.CFG.reference_count
if len(_within) < _floor:
    _within = PRESCREEN.head(min(_floor, len(PRESCREEN)))
    S.log_departure("prescreen",
                  f"retain candidates within {S.CFG.prescreen_difficulty_margin:.2f} of focal",
                  f"retained the {len(_within)} nearest instead",
                  "the margin would have cut the pool below twice the panel size, "
                  "and a loose pre-screen must not decide eligibility")

S.PRESCREEN_KEPT = sorted(_within.index)
# The prescreen ranks by distance to the focal constraint. Everything derived
# from it is B-relative from here on, and the pseudo-focal dataflow refuses it.
S.declare_lineage("PRESCREEN_KEPT", taints=[S.TAINT_FOCAL_RELATIVE],
                parents=["DECLARED_ELIGIBLE"])
PRESCREEN["retained"] = PRESCREEN.index.isin(S.PRESCREEN_KEPT)
PRESCREEN.to_csv(S.GATE_DIR / "prescreen.csv")
display(PRESCREEN.round(3))
print(f"""
focal isolated failure at the canonical wording: {_focal_pre:.3f}
retained {len(S.PRESCREEN_KEPT)} of {len(S.DECLARED_ELIGIBLE)} declared-eligible candidates
This is pool narrowing, not eligibility. Every retained candidate still faces
the full uncertainty-aware caliper test on the multi-paraphrase calibration.
""")
if _focal_pre >= 0.90 or _focal_pre <= 0.10:
    print(f"WARNING: the focal constraint sits at a "
          f"{'ceiling' if _focal_pre > 0.5 else 'floor'} ({_focal_pre:.3f}). No "
          "caliper width can match a constraint outside the pool's range.")
S.checkpoint("prescreen", {"declared_eligible": S.DECLARED_ELIGIBLE,
                         "retained": S.PRESCREEN_KEPT})
