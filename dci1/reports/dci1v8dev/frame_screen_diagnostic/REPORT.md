# DCI-1 v8 — the frame-blind pre-screen, measured

**Verdict: PARTIALLY.** The candidate screen and retention rank and forward on a frame-pooled coordinate while every caliper from Gate 2 onward is frame-specific, and the cross-frame spread of a rung's iota at calibration has a median across families of 0.234 — 2.3x the 0.1 caliper. On 3 of 4 models a LOCAL-unsupported frame carries unforwarded Tier-1/2 candidates whose own frame-f screen iota sits inside that frame's caliper (qwen3-4b, gemma-3n-e2b-it, gemma-3n-e4b-it). But the screen's per-frame coordinate has a median SE(iota) of 0.168 on six topics at 1 draw — larger than the caliper itself — so the pooled screen could not reliably have steered around the loss it causes.

**This diagnostic changes no membership.** It opens no confirmatory stage, generates nothing, moves no threshold, caliper, operating point, forwarded set, validity component or verdict, and writes nothing into any evidence tree. Every rung it names as a "would-forward" candidate was never calibrated, so its downstream validity is NOT_IDENTIFIABLE from this study's data; only the size of the withheld set and the noise of the coordinate that withheld it are measured here.

Classification convention, fixed before the counts were read: CONFIRMED iff (i) the median per-family cross-frame spread of calibration iota exceeds the 0.10 caliper (the mechanism exists), (ii) on at least two of the four models some LOCAL-unsupported frame carries at least one unforwarded Tier-1/2 screen-near candidate family that is not already LOCAL-valid on that frame (the mechanism had something to bite on), and (iii) the screen's own median SE(iota) is at most the caliper, so the screen coordinate can in fact locate a rung inside a frame's caliper. PARTIALLY iff (i) and (ii) hold but (iii) does not: the loss is real but the pooled screen's per-frame coordinate is too noisy to have steered around it. NOT otherwise.

## (a) Ranking and retention were frame-pooled

| model | screen iota_A (one scalar) | Gate-2 iota_A per frame | forwarded rungs | pooled on both records |
|---|---:|---|---:|---|
| `qwen3-4b` | 0.708 (severity 7) | f0=0.671; f1=0.608; f2=0.672; f3=0.697 | 59 | True |
| `gemma-3n-e2b-it` | 0.625 (severity 7) | f0=0.680; f1=0.628; f2=0.794; f3=0.680 | 58 | True |
| `qwen3-4b-instruct-2507` | 0.542 (severity 5) | f0=—; f1=0.642; f2=—; f3=0.681 | 64 | True |
| `gemma-3n-e4b-it` | 0.708 (severity 6) | f0=0.724; f1=0.703; f2=0.659; f3=0.682 | 61 | True |

The proof fields, identical in kind on every model: `REGIME_SCREEN.prescreen_table` carries `['chance_k', 'chance_n', 'draws_per_topic', 'kind', 'n_topics', 'reserve', 'severity', 'solo_k', 'solo_n', 'vacuous_k']` — no frame column, and `PrescreenRung` rejects an unknown field; `REGIME_SCREEN.iota_a_prescreen` is a single scalar; `SECOND_PASS_SCREEN.retention.config` carries only budget sizes (`{'admissible_min': 0.5, 'class_arm_rungs': 2, 'generations_per_rung': 3072, 'local_rungs': 4, 'max_local_families': 12, 'max_spectrum_families': 8, 'near_form_rungs': 3, 'spectrum_rungs': 5, 'total_cap': None}`); and both stage records state the pooling themselves, e.g. `REGIME_SCREEN.frame_conditioning.at_this_stage` = "pooled over the four frames as a measurement budget: at 24 topics x 1 draw a frame holds six topics; the screen decides which rungs are measured at calibration and every measured rung is calibrated under every frame; no admission, matching or selection reads a screen quantity (§12.2; docs/V8_FRAME_CONDITIONING.md §5)". `SECOND_PASS_SCREEN.forwarded_set` and `GATE_2_CALIBRATION.calibration_population.forwarded` agree exactly on every model, so the pooled set is the set Gate 2 calibrated.

## (b) Cross-frame spread of candidate iota

Spread = max − min over frames, per rung; a family's value is the median over its measured rungs. Calibration uses each frame's own §13.11 table (supported frames only, pooled split); the screen uses `GATE_1_INSTRUMENT.frame_comparison_screen`.

| model | cal median/family | cal median/rung | cal q90 | families > caliper | screen median/family | screen median SE(iota) | topics per frame |
|---|---:|---:|---:|---|---:|---:|---:|
| `qwen3-4b` | 0.209 | 0.219 | 0.391 | 11/12 | 0.333 | 0.211 | [6] |
| `gemma-3n-e2b-it` | 0.260 | 0.268 | 0.792 | 13/13 | 0.400 | 0.167 | [6] |
| `qwen3-4b-instruct-2507` | 0.194 | 0.100 | 0.451 | 8/13 | 0.333 | 0.169 | [6] |
| `gemma-3n-e4b-it` | 0.266 | 0.193 | 0.549 | 12/13 | 0.333 | 0.167 | [6] |

The screen's noise is the point: at six topics and one draw a frame's screen iota moves in steps of about 1/6, its median SE is on the scale of the caliper or above it, and its own cross-frame spread is correspondingly inflated. The calibration column is the real spread; the screen column is that spread plus six-topic noise.

## (c) Screen-vs-calibration drift on the forwarded rungs

| model | rungs paired | mean abs drift | max abs | per-frame mean abs | pooled mean abs |
|---|---:|---:|---:|---|---:|
| `qwen3-4b` | 55 | 0.138 | 0.568 | f0=0.136; f1=0.166; f2=0.117; f3=0.135 | 0.070 |
| `gemma-3n-e2b-it` | 43 | 0.155 | 0.638 | f0=0.150; f1=0.139; f2=0.130; f3=0.201 | 0.080 |
| `qwen3-4b-instruct-2507` | 47 | 0.148 | 0.469 | f1=0.145; f3=0.150 | 0.099 |
| `gemma-3n-e4b-it` | 50 | 0.139 | 0.575 | f0=0.116; f1=0.175; f2=0.135; f3=0.130 | 0.067 |

Drift is `iota_screen(f) − iota_cal(f)`; the pooled column is the screen's own pooled `difficulty_table` iota against the mean of the frame-specific calibration iotas (no pooled calibration iota exists on the record — `descriptive_pooled` is `read_by: []` — so that comparator is computed here and is descriptive only).

## (d) and (e) Per frame: matched controls in hand, candidates withheld

| model | frame | LOCAL | iota_A(f) | families/backups (need ≥5/≥2) | calibrated inside caliper | screen-near unforwarded (T1/2) | of those, top-up subset |
|---|---:|---|---:|---|---:|---:|---:|
| `qwen3-4b` | f0 | SUPPORTED | 0.671 | 5/2 | 15 (9 fam) | 3 | 2 |
| `qwen3-4b` | f1 | LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.608 | 4/1 | 12 (8 fam) | 0 | 0 |
| `qwen3-4b` | f2 | LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.672 | 4/1 | 14 (6 fam) | 2 | 1 |
| `qwen3-4b` | f3 | SUPPORTED | 0.697 | 7/2 | 13 (8 fam) | 3 | 0 |
| `gemma-3n-e2b-it` | f0 | LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.680 | 4/1 | 23 (11 fam) | 3 | 1 |
| `gemma-3n-e2b-it` | f1 | SUPPORTED | 0.628 | 6/2 | 21 (9 fam) | 2 | 0 |
| `gemma-3n-e2b-it` | f2 | CORE_NOT_IDENTIFIED,LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.794 | 1/0 | 12 (9 fam) | 1 | 0 |
| `gemma-3n-e2b-it` | f3 | SUPPORTED | 0.680 | 6/2 | 20 (9 fam) | 4 | 2 |
| `qwen3-4b-instruct-2507` | f0 | UNSUPPORTED | — | —/— | — (— fam) | — | — |
| `qwen3-4b-instruct-2507` | f1 | SUPPORTED | 0.642 | 7/2 | 25 (9 fam) | 1 | 1 |
| `qwen3-4b-instruct-2507` | f2 | UNSUPPORTED | — | —/— | — (— fam) | — | — |
| `qwen3-4b-instruct-2507` | f3 | LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.681 | 3/0 | 16 (8 fam) | 0 | 0 |
| `gemma-3n-e4b-it` | f0 | LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.724 | 3/0 | 17 (9 fam) | 3 | 3 |
| `gemma-3n-e4b-it` | f1 | LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.703 | 4/1 | 13 (9 fam) | 5 | 1 |
| `gemma-3n-e4b-it` | f2 | LOCAL_FAMILIES_BELOW_MINIMUM,BACKUPS_BELOW_MINIMUM | 0.659 | 3/0 | 13 (6 fam) | 1 | 0 |
| `gemma-3n-e4b-it` | f3 | SUPPORTED | 0.682 | 6/2 | 20 (10 fam) | 2 | 2 |

"Calibrated inside caliper" counts forwarded rungs whose realised `|iota_R(f) − iota_A(f)|` is within 0.10 on that frame's own table: the matched controls the frozen pipeline delivered. "Screen-near unforwarded" counts Tier-1/2 rungs the first-pass screen measured under f whose frame-f screen iota is inside the same caliper and which the pooled forwarded set omitted; the top-up subset additionally drops families already LOCAL-valid on f, i.e. the `LOCAL_TOPUP` candidate set. A frame with no operating point has no iota_A(f) and no count.

The converse direction — rungs the pooled screen forwarded that sit outside the frame's caliper on the frame's own screen coordinate — is large everywhere, which is the same noise statement from the other side:

| model | f0 | f1 | f2 | f3 |
|---|---:|---:|---:|---:|
| `qwen3-4b` | 44 | 37 | 40 | 38 |
| `gemma-3n-e2b-it` | 23 | 30 | 27 | 26 |
| `qwen3-4b-instruct-2507` | — | 29 | — | 31 |
| `gemma-3n-e4b-it` | 28 | 26 | 30 | 28 |

## (f) Per-model summary

- **`qwen3-4b`** (`dci1v8-pilot-r9`): LOCAL-supported frames [0, 3]; unsupported f1 (0 top-up-eligible candidate rungs), f2 (1 top-up-eligible candidate rungs). Cross-frame calibration spread 0.209, screen median SE(iota) 0.211. LOCAL-eligible: True. Support read from `reports/dci1v8dev/local_eligibility.md`, not from any record's `state` field.
- **`gemma-3n-e2b-it`** (`dci1v8-pilot-r8`): LOCAL-supported frames [1, 3]; unsupported f0 (1 top-up-eligible candidate rungs), f2 (0 top-up-eligible candidate rungs). Cross-frame calibration spread 0.260, screen median SE(iota) 0.167. LOCAL-eligible: True. Support read from `reports/dci1v8dev/local_eligibility.md`, not from any record's `state` field.
- **`qwen3-4b-instruct-2507`** (`dci1v8-pilot-r10`): LOCAL-supported frames [1]; unsupported f0 (— top-up-eligible candidate rungs), f2 (— top-up-eligible candidate rungs), f3 (0 top-up-eligible candidate rungs). Cross-frame calibration spread 0.194, screen median SE(iota) 0.169. LOCAL-eligible: False. Support read from `reports/dci1v8dev/local_eligibility.md`, not from any record's `state` field.
- **`gemma-3n-e4b-it`** (`dci1v8-pilot-r11`): LOCAL-supported frames [3]; unsupported f0 (3 top-up-eligible candidate rungs), f1 (1 top-up-eligible candidate rungs), f2 (0 top-up-eligible candidate rungs). Cross-frame calibration spread 0.266, screen median SE(iota) 0.167. LOCAL-eligible: False. Support read from `reports/dci1v8dev/local_eligibility.md`, not from any record's `state` field.

## Cross-check against the production `LOCAL_TOPUP` rule

The top-up subset above is, by construction, the candidate set `dci1v8dev.confirm.topup.topup_plan` selects. Running that planner on the same signed records (it plans only; nothing is generated) reproduces this tool's subset exactly:

| model | identical on every frame | frames where the rule fires | rungs |
|---|---|---|---:|
| `qwen3-4b` | True | [2] | 1 |
| `gemma-3n-e2b-it` | True | [0] | 1 |
| `qwen3-4b-instruct-2507` | True | none | 0 |
| `gemma-3n-e4b-it` | True | [0, 1] | 4 |

Across the four models the rule fires on 4 frames and 6 rungs on the records as they stand. `docs/V8_CONFIRMATORY.md` §3a records the dry run as seven rungs on four frames; the frame and family sets agree, the rung count differs by one. That is a documentation-vs-record discrepancy noted here, not resolved here, and it moves nothing: the top-up is reported to have moved no verdict either way.

## Agreement with `tools/v8_screen_frame_audit.py`

- `qwen3-4b` (`dci1v8-pilot-r9`): prior verdict **MATERIAL_LOSS** with 12 lost (family, frame) cells over 7 families, and the frame label beat the pooled label in 0 of 8 comparisons. Against this tool's unforwarded near-families: 0 family-frame cells agree, 12 appear only in the prior audit, 8 only here.
- `gemma-3n-e2b-it` (`dci1v8-pilot-r8`): prior verdict **MATERIAL_LOSS** with 7 lost (family, frame) cells over 6 families, and the frame label beat the pooled label in 2 of 8 comparisons. Against this tool's unforwarded near-families: 1 family-frame cells agree, 6 appear only in the prior audit, 8 only here.
- `qwen3-4b-instruct-2507` (`dci1v8-pilot-r10`): no prior audit exists (the earlier tool covers r5, r6, r8, r9); nothing to compare.
- `gemma-3n-e4b-it` (`dci1v8-pilot-r11`): no prior audit exists (the earlier tool covers r5, r6, r8, r9); nothing to compare.

Where the two differ they are answering different questions on different units. The earlier audit re-runs the production screen family by family on each frame's own rows and asks whether the frame's *label* (ACCEPT / spectrum / local) would have promoted the family; this tool asks, rung by rung, whether the frame's own screen iota falls inside that frame's Gate-2 caliper. The earlier audit's load-bearing result — that on the forwarded set the frame-specific label never beat the pooled label on r9 — is not contradicted by anything here; it is the same six-topic imprecision that keeps this diagnostic's verdict at PARTIALLY.

## Scope

LOCAL Delta_R(f) is identified only for model x frame combinations where the frozen screening/calibration/reference pipeline yields adequate matched controls.
