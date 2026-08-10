with phase("calibration"):
    _val_stage = "calibration_uval"
    _val_design = build_calibration_design(U_VAL_MEASURED_IDS, U_VAL, P_FINAL, _val_stage)
    _val_design.to_csv(DESIGN_DIR / f"{_val_stage}_design.csv", index=False)
    print(f"U_val calibration: {len(_val_design)} rows for "
          f"{len(U_VAL_MEASURED_IDS)} constraints x {len(U_VAL)} targets x "
          f"{len(CFG.orders)} orders x {len(P_FINAL)} wordings")
    _val_resp = run_generation_stage(_val_design, _val_stage)
    _err = 1.0 - _val_resp["generation_ok"].mean()
    if _err > 0.10:
        raise RuntimeError(f"{_err:.1%} of {_val_stage} generations failed.")
    val_calibration_scores = score_responses(_val_resp)
    CAL_TABLE_VAL = calibration_cell_table(val_calibration_scores)

calibration_scores = pd.concat([calibration_scores, val_calibration_scores],
                               ignore_index=True)
print(f"U_val burden is now measurable for {len(U_VAL_MEASURED_IDS)} constraints "
      "and has been read by nothing above this cell.")
