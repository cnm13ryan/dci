"""Stage 312 — migrated from notebook cell 312.py (uval_measurement).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/312.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell


with S.phase("calibration"):
    _val_stage = "calibration_uval"
    _val_design = S.build_calibration_design(S.U_VAL_MEASURED_IDS, S.U_VAL, S.P_FINAL, _val_stage)
    _val_design.to_csv(S.DESIGN_DIR / f"{_val_stage}_design.csv", index=False)
    print(f"U_val calibration: {len(_val_design)} rows for "
          f"{len(S.U_VAL_MEASURED_IDS)} constraints x {len(S.U_VAL)} targets x "
          f"{len(S.CFG.orders)} orders x {len(S.P_FINAL)} wordings")
    _val_resp = S.run_generation_stage(_val_design, _val_stage)
    _err = 1.0 - _val_resp["generation_ok"].mean()
    if _err > 0.10:
        raise RuntimeError(f"{_err:.1%} of {_val_stage} generations failed.")
    val_calibration_scores = S.score_responses(_val_resp)
    S.CAL_TABLE_VAL = S.calibration_cell_table(val_calibration_scores)

S.calibration_scores = pd.concat([S.calibration_scores, val_calibration_scores],
                               ignore_index=True)
print(f"U_val burden is now measurable for {len(S.U_VAL_MEASURED_IDS)} constraints "
      "and has been read by nothing above this cell.")
