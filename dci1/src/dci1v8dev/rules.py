"""The v8 candidate's constants, in one place, each with its provenance.

Every rule module defaults to these values; nothing else defines a
threshold. A value's provenance is one of: a registered v7 constant
(``dci1v7.protocol.constants``, unchanged), a simulation report under
``reports/dci1v8dev/`` (prospective, synthetic), a derivation stated here,
or a budget choice stated here. Retrospective backtests never set a value
(the design note says which numbers were only *read* on stored evidence).
"""
from __future__ import annotations

from dci1v7.protocol import constants as C

__all__ = [name for name in dir() if name.isupper()]  # refreshed at the end

# ---------------------------------------------------------------- spectrum
#: The guard band on a spectrum point's raw solo rate: v5 registered it as
#: SPECTRUM_ELIGIBILITY_BAND = (0.10, 0.95) and applied it nowhere.
SPECTRUM_GUARD_BAND = C.SPECTRUM_ELIGIBILITY_BAND
#: A spectrum point must sit at least this far from ι_A (it is the core's
#: territory inside; a point there carries no leverage for the slope).
SPECTRUM_D_MIN = 0.05
#: Offsets the selected set must reach on each side of A, the minimum total
#: span, and the SE(ι) ceiling on a calibrated coordinate — chosen by
#: ``spectrum.coverage_simulation.threshold_choice`` (PPV ≥ 0.95 against
#: realised identifiability, maximum recall; reports/dci1v8dev/
#: coverage_simulation.md, 2026-08-29). The stricter 0.15/0.10/0.25 the
#: first candidate carried buys PPV 0.975 for recall 0.44 against 0.954/0.63.
SPECTRUM_OFFSET_BELOW = 0.10
SPECTRUM_OFFSET_ABOVE = 0.10
SPECTRUM_MIN_TOTAL_SPAN = 0.20
SPECTRUM_MAX_SE_IOTA = 0.05
#: Precision floor on §11.8's common slope: a 95 % half-width of ≈ 0.10 per
#: unit ι, i.e. the slope resolved to one SESOI (0.10 of compliance) per
#: unit of difficulty and to 0.01 over §13.8's 0.10 caliper. At the measured
#: per-point precision (spectrum.precision.MEASURED) it needs within-family
#: leverage ≥ 0.027: three families × two points at ±0.07.
SPECTRUM_MAX_SE_BETA = 0.05
#: The shape §13.13 already uses on the confirmatory data (registered).
SPECTRUM_MIN_POINTS_BELOW = C.SUPPORT_MIN_BELOW
SPECTRUM_MIN_POINTS_ABOVE = C.SUPPORT_MIN_ABOVE
SPECTRUM_MIN_FAMILIES_PER_SIDE = C.SUPPORT_MIN_FAMILIES_PER_SIDE
#: Where the selection *aims* per family (the gate requires only the offsets
#: above; farther points carry more leverage, spectrum_precision.md).
SELECTION_TARGET_BELOW = 0.20
SELECTION_TARGET_ABOVE = 0.15
SELECTION_MAX_FAMILIES = 4
#: Two points of one family must differ by at least this to count as a pair.
SELECTION_MIN_SEPARATION = 0.05

# ---------------------------------------------------------- frame conditioning
#: Approach A (docs/V8_FRAME_CONDITIONING.md, researcher decision of
#: 2026-08-30): the wording frame is part of the experimental condition, so
#: every difficulty, operating point, validity, selection and eventual
#: estimand is frame-specific. The registered confirmatory allocation
#: (N_BLOCKS × 8 draws, wording by block) puts one quarter of the blocks
#: under each frame; a frame-specific estimate is projected at that share.
#: Derived, not chosen: N_BLOCKS / N_WORDINGS.
CONFIRMATORY_BLOCKS_PER_FRAME = C.N_BLOCKS // C.N_WORDINGS
assert CONFIRMATORY_BLOCKS_PER_FRAME * C.N_WORDINGS == C.N_BLOCKS

# ---------------------------------------------------------------- pre-screen
#: Status thresholds on P(support both sides) and the posterior-majority
#: rule at the batch maximum — chosen by the synthetic operating
#: characteristics (tools/v8_prescreen_simulation.py → simulation.md).
#: tests_v8dev asserts these equal the report's recorded choice.
SCREEN_ACCEPT = 0.80
SCREEN_REJECT = 0.20
RESCREEN_FINAL_ACCEPT_AT = 0.50
#: Derived from the pre-screen's precision (screen.ScreenConfig.local_accept):
#: the posterior probability a rung on the caliper edge has of reading
#: inside it at 24 topics.
LOCAL_LABEL_MIN = 0.25
RESCREEN_MAX_BATCHES = 3
RESCREEN_BATCH_TOPICS = C.N_PRESCREEN
RESCREEN_RESERVE_PICKS_PER_BATCH = 2
#: Severity-range exploration: a side is reach-deficient below this
#: posterior probability; one calibration round of at most this many
#: reserve rungs per deficient side.
EXTENSION_P_REACH = 0.80
EXTENSION_CALIBRATION_PICKS = 2

# ---------------------------------------------------------------- retention
#: Budget choices (768 generations per rung at 192 × 4): a spectrum family
#: carries its five roles; a local family its four rungs most likely inside
#: the caliper (three lost the rung that calibrated inside the caliper on
#: 3/117 stored cases when ι_A moved between screen and calibration); up to
#: eight spectrum and twelve local families (§13.15 needs five families
#: passing the full V(R); the cap of ten lost five plausible ones on the
#: stored replications). Worst case 8×5 + 12×4 + 2 + 3 = 93 rungs, below
#: §12.7's 112–140; typical 35–50.
RETENTION_SPECTRUM_RUNGS = 5
RETENTION_LOCAL_RUNGS = 4
RETENTION_MAX_SPECTRUM_FAMILIES = 8
RETENTION_MAX_LOCAL_FAMILIES = 12
RETENTION_ADMISSIBLE_MIN = 0.50
RETENTION_CLASS_ARM_RUNGS = 2
RETENTION_NEAR_FORM_RUNGS = 3

__all__ = [name for name in list(globals()) if name.isupper()]
