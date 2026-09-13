# Finding 11 — adaptive design history (reconstructed 2026-09-02 from git, pilot records, confirm records)

Protected-outcome boundary: the earliest file under any CONFIRMATORY_GENERATION directory is
`dci1/evidence/dci1v8-confirm/logs/qwen3-4b.CONFIRMATORY_GENERATION.20260902T101144Z.out`
(2026-09-02 10:11:44Z; first evidence file 10:11:44Z; last written 13:09Z when the operator stopped generation).
Every design commit below precedes it; the only later commit, `11697e9` (10:28:59Z), is docs-only.
Membership lock `5870ddf` landed 10:11:28Z, 16 s before the first composed row.

## Dated decisions (times +0100 local as in the git log)

| # | when | commit | decision | evidence visible before it | composed outcomes existed? | scope | changed which cells could enter? |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-29 22:14 | 5635b9a | LOCAL/SPECTRUM validity separated; selected-coverage gate; admissible backups; v8 wording frames; reserve extension | v7 replays only | no | universal | defines the arms |
| 2 | 2026-08-29 22:18 | 19576b9 | verifier unification (dci1v8dev.verifiers) | none | no | universal | no |
| 3 | 2026-08-29 22:52 | 7196123 | corrected chance basis in every replay; coverage thresholds by simulation (0.10/0.10, span 0.20, SE(ι) ≤ 0.05) | reports/dci1v8dev/coverage_simulation.json 22:30 | no | universal | sets the SPECTRUM gate |
| 4 | 2026-08-30 07:22 | 190e660 | second-pass batch index fix after r2 | r2 REGIME_SCREEN record 06:57 | no | universal | no |
| 5 | 2026-08-30 10:01 | ebf757d | Approach A: frame is part of the condition (n*(f), m*(f), ι_A(f), per-frame Gate 3, Δ_R(f)); wording policy model_frame_variation | r3 terminal GRID_RESOLUTION_INSUFFICIENT (A:5 = 0.22/0.68/0.42/0.52) 07:57–08:11 | no | universal | yes: creates model×frame cells |
| 6 | 2026-08-30 11:34 | 2145277 | extension reserve rungs declared as grid instances (r4 found the round inert) | r4 stopped after GATE_1 | no | universal | no |
| 7 | 2026-08-30 17:01 | c8b70d3 | 2× calibration: CALIBRATION_FRAME_OFFSETS (0,2), 96 topics/frame | r5 (both Qwens) 12:58/13:38, r6 (e2b) 15:55: median per-frame SE(ι) 0.0497 vs 0.05 floor | no | universal | yes: first roots to clear REFERENCE_SURVIVAL (r8) |
| 8 | 2026-08-31 07:40 | bf136bb | qwen3-4b → 4 passes / 192 topics (ceiling) via CALIBRATION_FRAME_OFFSETS_BY_MODEL | r8 three lanes (19:40, 21:02, 23:03 on 08-30); vstab.dci1v8-pilot-r8.qwen3-4b.json 07:32 | no | MODEL-SPECIFIC | yes: r8 qwen3-4b 0 supported frames → r9 f0+f3 supported; model becomes eligible |
| 9 | 2026-08-31 14:39 | 7dc26d1 | manifest rule table binds dict-valued constants | r9 PASS 12:21 | no | universal | no |
| 10 | 2026-08-31 16:31 | 5e4791e (a) | LOCAL_ELIGIBILITY_MIN_FRAMES = 2; run/eligibility.py | r5–r9 Gate-3 records; local_eligibility.{json,md} | no | universal | yes: 2507 (1 frame) and later e4b (1 frame) ineligible |
| 11 | 2026-08-31 16:31 | 5e4791e (b) | confirmatory allocation 96 → 288 (CONFIRMATORY_FRAME_OFFSETS (0,1,2)) | tools/v8_local_precision.py: 1 pass half-width 0.078 vs 0.05 | no | universal | coverage condition 4 projects at 288 (1 of 16 recorded frame verdicts would differ: r8 qwen3-4b f3, superseded) |
| 12 | 2026-08-31 16:31 | 5e4791e (c) | qwen3-4b-instruct-2507 → ceiling | r8 2507 lane (f1 supported; f3 4 families/1 backup) | no | MODEL-SPECIFIC | yes, negatively: r10 f3 fell 4→3 families, f0 lost its operating point; still ineligible |
| 13 | 2026-08-31 17:46 → 09-01 01:50 | run at 5e4791e | gemma-3n-e4b-it measured (r11) at the default 2 passes | r10 in flight | no | default (not raised) | yes: adds 4 SPECTRUM frames; f3 only LOCAL-supported |
| 14 | 2026-09-02 10:29 | cd61e72 | confirmatory layer; allocation 288 → 384 by confirm/precision.py; joint cross-frame family; frame-aware LOCAL top-up; backups R4/R5 generated | r8–r11 records; coverage_at_288.json, local_precision.json (09-01) | no (42 min before the first composed file) | universal | sets what is generated |
| 15 | 2026-09-02 10:41 | fbf00c8 | top-up equality check derives LOCAL support by rule on both sides | e4b/2507 top-ups already written | no | universal | no |
| 16 | 2026-09-02 10:38–10:47 | records | LOCAL_TOPUP outcome: 6 rungs on 4 frames of 3 models (1536+384+768 rows); eligibility unchanged on every model | — | no | per model | no |
| 17 | 2026-09-02 11:11 | 5870ddf | membership locked + four freezes (LOCAL: qwen3-4b f0+f3, e2b f1+f3; SPECTRUM 14 frames; 384 blocks/frame) | MEMBERSHIP records 10:43–11:10 | no (14–46 s before the first composed row) | universal | final (superseded 2026-09-02 by this audit) |

## LOCAL_TOPUP detail (signed records)

| model | frames run | rungs | rows | change | eligibility before → after |
|---|---|---|---|---|---|
| gemma-3n-e4b-it | f0, f1 | XC1:2, XC3:3, XC3:9 (f0); MK3:7 (f1) | 1536 | f0 gained backup XC1 (3→4 families, 0→1 backup); still short | [3], false → [3], false |
| qwen3-4b-instruct-2507 | none | — | 0 | — | [1], false → [1], false |
| gemma-3n-e2b-it | f0 | MK1:8 | 384 | none | [1,3], true → unchanged |
| qwen3-4b | f2 | XC3:5 | 768 | none | [0,3], true → unchanged |

Discrepancies found: signed records show six topped-up rungs; CHANGES_SCIENTIFIC.md and commits 5870ddf/11697e9 say seven (row count 2,688 matches). V8_CONFIRMATORY.md said spectrum k ≤ 8 while design.py carries MAX_SPECTRUM_POINTS = 12 and freezes carry 9–10 slots. MEMBERSHIP records projected 288 for the two SPECTRUM-only models while all four FROZEN records bound 384.

## Pilot roots

| root | dates | models | calibration | endpoint | LOCAL-supported frames |
|---|---|---|---|---|---|
| dci1v8-pilot | 08-30 06:36 | 2507 | 1 pass (48/frame) | TERMINAL QUALIFICATION_FAILURE | — |
| r2 | 08-30 06:38–06:57 | 2507 | 1 pass | stopped at REGIME_SCREEN (index defect) | — |
| r3 | 08-30 07:22–08:11 | 2507 | 1 pass | TERMINAL Gate 2 GRID_RESOLUTION_INSUFFICIENT | — |
| r4 | 08-30 10:01–11:24 | qwen3-4b, 2507 | 1 pass (first Approach-A root) | stopped after GATE_1 (reserve-rung defect) | — |
| r5 | 08-30 11:34–13:38 | qwen3-4b, 2507 | 1 pass | 9 stages PASS | none |
| r6 | 08-30 13:29–15:55 | e2b | 1 pass | 9 stages PASS | none |
| r7 | 08-30 17:01 | e2b | 2 passes | TERMINAL QUALIFICATION_FAILURE | — |
| r8 | 08-30 17:02–23:03 | e2b, qwen3-4b, 2507 | 2 passes / 96 | PASS ×3 | e2b f1,f3; 2507 f1; qwen3-4b none |
| r9 | 08-31 07:41–12:21 | qwen3-4b | 4 passes / 192 | PASS | f0, f3 |
| r10 | 08-31 16:31–22:19 | 2507 | 4 passes / 192 | PASS | f1 |
| r11 | 08-31 17:46 – 09-01 01:50 | e4b | 2 passes / 96 | PASS | f3 |

Verdict: **CONFIRMED** — three model-specific measurement decisions (rows 8, 12, 13) and three universal rule decisions (rows 10, 11, 14) were taken after seeing calibration/reference-survival behaviour on the study checkpoints; none used a composed outcome.
