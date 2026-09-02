# DCI-1 protocol v8 — preregistration (standalone)

**Status: DRAFT under the pre-freeze audit of 2026-09-02.** This file is the
document the v8 confirmatory manifest and every `FROZEN` record bind by hash.
The rules it states are executable in `dci1/src/dci1v8dev/rules.py` and the
confirmatory layer `dci1/src/dci1v8dev/confirm/`; a test fails when a number
here and a number there disagree. Sections marked *pending* are completed
before any freeze; a freeze that binds a draft is refused (§19).

## 17. Confirmatory allocation (one value)

`CONFIRMATORY_BLOCKS_PER_FRAME = 384`: every entering frame of every study
model runs every registered confirmatory block (four passes at frame offsets
(0, 1, 2, 3); the ceiling). The 288 blocks per frame (2026-08-31) and the
{288, 384} menu rule (2026-09-02, morning) are superseded; both are recorded
in `rules.py` and in `CHANGES_SCIENTIFIC.md` as history.

## 9. Calibration allocation (universal)

`CALIBRATION_FRAME_OFFSETS = (0, 1, 2, 3)` for every study model: 192
calibration topics per frame, 96 per §13.7 split. No per-model override
exists (`rules.CALIBRATION_POLICY`).

*(remaining sections pending)*
