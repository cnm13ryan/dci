"""The Gate-2 calibration screen: §12.3, §12.4 and §13.2 on the real set.

Every screen before this one measured on the 24 pre-screen topics at one draw.
Three separate artifacts say in terms that the pre-screen has never been shown
to predict the calibration set and may not:

* `user-notes/DCI1_v4_amendment_B_reference_pool.md` §9 — "The candidate
  families must clear the conjunction on the calibration set before they are
  adopted into the registered pool."
* `dci1/reports/fs_screen_v4/REPORT.md` §6 — "§12.3 re-measures on the disjoint
  96 solo-calibration topics at M = 4, and §13.2 admits against *that*."
* `dci1/reports/bgrid_screen_v4/REPORT.md` §1.4 — the extended focal grid is
  MARGINAL on qwen3-4b-instruct-2507 and "a fresh-topic confirmation is
  required before any grid amendment."

This module runs that measurement, once, for all three questions at the same
time, on the registered 96 solo-calibration topics at the registered
M_cal = 4, with the registered admission code doing the deciding.

**It is a screen, not a registered stage.** Gate 1 is not approved, the
canonical verifier hash is not frozen, and the candidate families are not in
the registered pool, so nothing generated here can be a §12.3 record. It
writes only under `evidence/cal-screen-v4/` and `reports/cal_screen_v4/`,
outside the v4 namespace, where the positive-admission guard refuses it.
"""
STUDY_ID = "dci1-cal-screen-v4"
CLASSIFICATION = "NON-CONFIRMATORY DESIGN SCREEN"

__all__ = ["STUDY_ID", "CLASSIFICATION"]
