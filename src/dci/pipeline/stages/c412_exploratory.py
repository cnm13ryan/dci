"""Stage 412 — migrated from notebook cell 412.py (exploratory).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/412.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell

CFG = getattr(S, 'CFG', None)  # pandas @-resolution alias (read-only)

target_all = S.confirmatory_scores.query(
    "constraint_id == @CFG.target_id and is_measured")
print("EXPLORATORY. Descriptive only.\n")
display(target_all.groupby(["added_constraint", "order"])
        .agg(fail_rate=("fail", "mean"), mean_words=("response_words", "mean"),
             n=("fail", "size")).round(3))

_probe = pd.DataFrame({
    "reference": S.SELECTED_REFERENCES,
    "difficulty": [float(S.SIGNATURE.at[c, S.SIG_DIFFICULTY]) for c in S.SELECTED_REFERENCES],
    "wording_instability_max": [float(S.SIGNATURE_FULL.at[c, S.SIG_S_MAX])
                                for c in S.SELECTED_REFERENCES],
    "mahalanobis": [float(S.MATCH_DISTANCE[c]) for c in S.SELECTED_REFERENCES],
}).set_index("reference")
for o in S.CFG.orders:
    _probe[f"tau_{o}"] = [float(S.PRIMARY.loc[f"tau|{c}|{o}", "estimate"])
                          for c in S.SELECTED_REFERENCES]
display(_probe.round(3))
print("\nWith six references a correlation here has almost no power. It is "
      "recorded to motivate the next preregistration, not to support a claim.")

_lengths = (S.calibration_scores.query("order == 'isolated' and is_measured")
            .groupby("constraint_id")["response_words"].mean())
print(f"\nMediator watch: mean isolated response length, focal "
      f"{_lengths.get(S.CFG.focal_id, float('nan')):.1f} words versus panel mean "
      f"{_lengths.reindex(S.SELECTED_REFERENCES).mean():.1f}. This imbalance was "
      "accepted by the causal-variable audit and is reported, not corrected.")
