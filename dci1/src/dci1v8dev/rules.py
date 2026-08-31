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

# ------------------------------------------------- calibration allocation
#: **The calibration passes** (researcher decision of 2026-08-30, after
#: pilot r5/r6; docs/V8_FRAME_CONDITIONING.md §10 item 1). Approach A gives
#: every frame its own difficulty coordinates, and §8.4's allocation --- one
#: frame per block --- gives each frame a quarter of the calibration
#: topics: 48, at which r5/r6 measured a median per-frame SE(iota) of 0.0497
#: against the 0.05 floor `SPECTRUM_MAX_SE_IOTA`, so `V_coord` refused most
#: rungs below A and no frame identified a spectrum (V8_PILOT.md §7b).
#:
#: A calibration *pass* renders every calibration topic under one frame;
#: pass p shifts the frame by ``CALIBRATION_FRAME_OFFSETS[p]``, so a topic
#: at position i is met under frame ``(i + offset_p) % N_WORDINGS``. Two
#: passes with distinct offsets put every topic under two frames and every
#: frame on ``N_CALIBRATION * 2 / N_WORDINGS`` = 96 topics --- half of each
#: §13.7 split --- at exactly 2x the Gate-2 generation.
#:
#: What it is and is not. It buys information *inside* each frame: the
#: offsets are distinct modulo N_WORDINGS, so no topic is ever measured
#: twice under one frame and the *topic*-level standard error falls by
#: sqrt(2) (the estimators average draws within a topic first, so extra
#: draws would not have done this). Frames are never pooled; every frame
#: still has its own curve, operating point, table, validity and selection.
#: No threshold moves: this changes how much is measured, not what admits.
CALIBRATION_FRAME_OFFSETS = (0, 2)

#: **The per-model allocation** (researcher decision of 2026-08-31, after
#: pilot r8; docs/V8_FRAME_CONDITIONING.md §4a). r8 measured what two passes
#: bought and what they did not: `SPECTRUM_MAX_SE_IOTA` is satisfied on the
#: *pooled* per-frame table (median SE(iota) 0.0356 against the 0.05 floor)
#: but §13.7 evaluates its condition 1 on **each split alone**, at half the
#: frame's topics, where the same coordinate carries SE(iota) ~ 0.05 --- so
#: 221 of 332 split-level `V_coord` refusals on `qwen3-4b` were the SE clause
#: and nothing else (reports/dci1v8dev/vstab.dci1v8-pilot-r8.qwen3-4b.md).
#: Four passes put every frame on all `N_CALIBRATION` topics, 96 per split,
#: which is the **ceiling**: the topic bank holds exactly N_CALIBRATION
#: calibration topics and every other topic set is reserved.
#:
#: The override is per model because the researcher approved the further 2x
#: for `qwen3-4b` alone --- it is the model whose frames r8 left short --- and
#: because an allocation is a property of a replication's measurement, not of
#: the admission rules, which are identical under either value. A model
#: absent from this table runs at `CALIBRATION_FRAME_OFFSETS`, so every
#: earlier run's meaning is untouched.
CALIBRATION_FRAME_OFFSETS_BY_MODEL: dict[str, tuple[int, ...]] = {
    "qwen3-4b": (0, 1, 2, 3),
}


def _assert_offsets(offsets: tuple[int, ...], where: str) -> tuple[int, ...]:
    """The passes' offsets must be distinct modulo the wordings.

    Two passes at the same offset would measure a topic twice under one
    frame and the per-topic vector would count the repeat as a second topic,
    inflating the very denominator every standard error is formed at.
    """
    assert offsets, f"{where}: at least one calibration pass"
    assert len({o % C.N_WORDINGS for o in offsets}) == len(offsets) \
        <= C.N_WORDINGS, (
            f"{where}: the passes' frame offsets must be distinct modulo "
            "N_WORDINGS, or a topic would be measured twice under one frame "
            "and its two measurements counted as two topics")
    return tuple(offsets)


_assert_offsets(CALIBRATION_FRAME_OFFSETS, "CALIBRATION_FRAME_OFFSETS")
for _model, _offsets in CALIBRATION_FRAME_OFFSETS_BY_MODEL.items():
    _assert_offsets(_offsets, f"CALIBRATION_FRAME_OFFSETS_BY_MODEL[{_model!r}]")


def calibration_frame_offsets(model_key: str | None = None) -> tuple[int, ...]:
    """The calibration passes this model runs. The default unless overridden."""
    if model_key is None:
        return CALIBRATION_FRAME_OFFSETS
    return CALIBRATION_FRAME_OFFSETS_BY_MODEL.get(model_key,
                                                  CALIBRATION_FRAME_OFFSETS)


def calibration_passes(model_key: str | None = None) -> int:
    return len(calibration_frame_offsets(model_key))


def calibration_topics_per_frame(model_key: str | None = None) -> int:
    """Distinct topics one frame's §13.11 table is measured on. Derived."""
    return C.N_CALIBRATION * calibration_passes(model_key) // C.N_WORDINGS


def calibration_topics_per_frame_per_split(model_key: str | None = None) -> int:
    """Distinct topics one frame carries in each §13.7 split. Derived."""
    return C.N_CALIBRATION_A * calibration_passes(model_key) // C.N_WORDINGS


def calibration_generations_per_rung(model_key: str | None = None) -> int:
    """What one calibrated rung costs across all frames. Derived."""
    return C.N_CALIBRATION * C.M_CAL * calibration_passes(model_key)


#: The default allocation's derived constants, for the paths that carry no
#: model in scope (the synthetic walk, the module-level design statements).
#: A model-scoped path calls the resolver above and never these.
CALIBRATION_FRAME_PASSES = calibration_passes()
CALIBRATION_TOPICS_PER_FRAME = calibration_topics_per_frame()
CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT = calibration_topics_per_frame_per_split()
CALIBRATION_GENERATIONS_PER_RUNG = calibration_generations_per_rung()
assert CALIBRATION_TOPICS_PER_FRAME * C.N_WORDINGS == \
    C.N_CALIBRATION * CALIBRATION_FRAME_PASSES
assert CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT * 2 == \
    CALIBRATION_TOPICS_PER_FRAME
#: The ceiling, stated once: four passes put every frame on every calibration
#: topic, and a fifth would repeat one inside a frame.
CALIBRATION_MAX_PASSES = C.N_WORDINGS
CALIBRATION_MAX_TOPICS_PER_FRAME = C.N_CALIBRATION
assert calibration_topics_per_frame_per_split("qwen3-4b") * 2 == C.N_CALIBRATION
for _model in CALIBRATION_FRAME_OFFSETS_BY_MODEL:
    assert calibration_topics_per_frame(_model) <= CALIBRATION_MAX_TOPICS_PER_FRAME

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
