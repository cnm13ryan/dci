# Track 1 — the B-grid screen

**NON-CONFIRMATORY DESIGN SCREEN.** Same standing as the FORM × STEM screen.
Not a registered v4 stage. Nothing here may enter a v4 estimator, no registered
constant, verifier, threshold, grid, ladder or wording was changed, and
`m = 11` and `m = 12` are **not registered** by anything in this work.

Gate 1 is not approved. The protocol is not frozen. No confirmatory data was
generated. V1–V9 remain open. Amendment C is drafted, not adopted.

---

## 1. Provenance

| item | value |
|---|---|
| screen protocol hash | `6a63ba782db0de6e1c4d80763065dda7ced1279e3c8ddcc097c7119087f4fff2` |
| frozen at commit | `9523917347dcafb1fec3a8263c4b441f0244456a` (contains the apparatus) |
| frozen | before the first generation; the §1.4 decision rule is inside the frozen payload |
| canonical verifier hash | `f5d4f7e74e757769…` — unchanged, still equal to the signed registration manifest |
| evidence root | `dci1/evidence/bgrid-screen-v4/` |
| reports | `dci1/reports/bgrid_screen_v4/` |
| seed root / domain | `202608210` / `bgrid:gen:v1`, distinct from every v3 root (202608170–175), every v4 root (202608190–195) and the FORM × STEM root (202608200) |
| topics | the 24 registered pre-screen topics; the 96 solo-calibration, 24 composed-validation, 384 confirmatory and 96 sequestered sets were not touched |
| generations | 528 per model, 2,112 total, one draw per cell, cap 512, `tensor_parallel_size` 1 |
| truncation / empty | **0 / 0** on all four models |
| analysis seed | `20260821`, 2000 topic-clustered bootstrap resamples |

**Topic dependency, recorded.** This screen re-spends the pre-screen development
sample. It measures the B-solo curve and selects no reference family, so it adds
no new §13.2 condition 2 contamination beyond what the FORM × STEM screen
already created.

**The extension is B, not a new constraint.** The registered grid still refuses
`m = 11`: `Constraint("B", 11)` raises and `focal_wordings(11)` raises, and a
test pins both. The screen carries its own renderer and scorer for the two
extension rungs and proves they are the registered ones by two equalities the
suite enforces — byte-identical wordings on all four registered rungs, and 160
verdicts at exactly 1.000 agreement with the registered verifier.

---

## 2. What was generated

| cell | rungs | per model |
|---|---|---|
| B solo, floored | m ∈ {7,8,9,10,11,12} | 144 |
| B solo, current | m ∈ {11,12} | 48 |
| A solo, floored | the full n grid | 192 |
| A+B fixture, floored (A = 3) | m ∈ {7,…,12} | 144 |

B solo under the current stem at m = 7…10 is the registered §12.2 ladder screen,
read from `evidence/dci1-v4` without regeneration; its values reproduce the
registered record exactly.

**One deviation from the brief, stated.** §1.2 asks for the A+B fixture "at each
in-band m". Which m is in band is not known until the B-solo curve exists, and a
two-phase run costs a second engine load per model for no scientific gain, so the
fixture was generated at *every* screen rung. The out-of-band fixture rows are
reported and carry no weight in the §1.4 verdict.

---

## 3. §1.3 readouts

### B-solo compliance under the floored stem (raw)

| model | m=7 | m=8 | m=9 | m=10 | m=11 | m=12 |
|---|---|---|---|---|---|---|
| E2B | 0.417 | 0.417 | 0.417 | 0.917 | 0.833 | 1.000 |
| E4B | 0.500 | 0.625 | 0.667 | 0.750 | 1.000 | 0.958 |
| Qwen3-4B | 0.042 | 0.125 | 0.167 | 0.375 | 0.625 | 0.875 |
| Qwen3-4B-Inst | 0.125 | 0.417 | 0.375 | 0.667 | 0.667 | 0.958 |

Every model's floored curve is monotone in m up to sampling noise; the two
inversions (E2B m = 10→11, E4B m = 11→12) are 0.084 and 0.042, both inside one
standard error of the difference.

### Topic-clustered standard errors

| model | m=7 | m=8 | m=9 | m=10 | m=11 | m=12 |
|---|---|---|---|---|---|---|
| E2B | 0.097 | 0.101 | 0.098 | 0.057 | 0.077 | 0.000 |
| E4B | 0.102 | 0.097 | 0.094 | 0.089 | 0.000 | 0.041 |
| Qwen3-4B | 0.042 | 0.068 | 0.076 | 0.098 | 0.101 | 0.068 |
| Qwen3-4B-Inst | 0.067 | 0.103 | 0.101 | 0.094 | 0.097 | 0.041 |

At 24 topics and one draw the standard error near p = 0.5 is about 0.10, which is
29% of the width of the focal band. That is the resolution this screen has, and it
is why §1.4 has a MARGINAL branch.

### Non-vacuous compliance at ≥ 20 words

| model | m=7 | m=8 | m=9 | m=10 | m=11 | m=12 |
|---|---|---|---|---|---|---|
| E2B | 0.417 | 0.417 | 0.417 | 0.917 | 0.833 | 1.000 |
| E4B | 0.500 | 0.625 | 0.667 | 0.750 | 1.000 | 0.958 |
| Qwen3-4B | 0.042 | 0.125 | 0.167 | 0.375 | 0.625 | 0.875 |
| Qwen3-4B-Inst | 0.125 | 0.375 | 0.375 | 0.625 | 0.667 | 0.958 |

### Realised max word length (median) and word count (median)

| model | m=7 | m=8 | m=9 | m=10 | m=11 | m=12 |
|---|---|---|---|---|---|---|
| E2B maxlen | 8.0 | 9.0 | 10.0 | 9.0 | 10.0 | 9.5 |
| E2B words | 84 | 84 | 85 | 84 | 86 | 86 |
| E4B maxlen | 7.5 | 8.0 | 8.5 | 9.0 | 9.0 | 9.5 |
| E4B words | 80 | 80 | 83 | 84 | 82 | 82 |
| Qwen3-4B maxlen | 10.0 | 10.0 | 10.5 | 11.0 | 11.0 | 11.0 |
| Qwen3-4B words | 50 | 56 | 55 | 56 | 61 | 58 |
| Qwen3-4B-Inst maxlen | 10.0 | 9.0 | 10.0 | 10.0 | 11.0 | 11.0 |
| Qwen3-4B-Inst words | 42 | 51 | 44 | 48 | 52 | 56 |

### Vacuity, truncation and stem satisfaction, floored

| model | max vacuous share of passes | max truncation | stem satisfied | median words | 10th pct words |
|---|---|---|---|---|---|
| E2B | 0.000 | 0.000 | 1.000 | 85 | 70 |
| E4B | 0.000 | 0.000 | 0.993 | 82 | 67 |
| Qwen3-4B | 0.000 | 0.000 | 0.382 | 56 | 34 |
| Qwen3-4B-Inst | 0.100 | 0.000 | 0.292 | 49 | 27 |

**The floored stem removes B-side vacuity on all four models.** The maximum
vacuous share of passes across all six rungs is 0.000 on three models and 0.100
on one. Truncation is zero everywhere.

**It does not do so by being obeyed.** The Gemmas obey the 60–120 word instruction
essentially always (0.99–1.00); the Qwens obey it 29–38% of the time. What removes
the vacuity is not compliance with the stem but the floor it puts under response
length even when the instruction is only partly followed: the Qwens' median
floored answer is 49–56 words against 4–11 words under the current stem, and their
lowest 10th percentile across rungs is 27 words, still above the 20-word threshold.

### What the current stem was actually measuring

| model | m | raw | non-vacuous | vacuous share of passes | median words |
|---|---|---|---|---|---|
| E2B | 7 | 0.833 | 0.333 | 0.600 | 19 |
| E2B | 8 | 0.875 | 0.500 | 0.429 | 22 |
| E2B | 9 | 0.833 | 0.667 | 0.200 | 26 |
| E2B | 10 | 0.958 | 0.625 | 0.348 | 21 |
| E2B | 11 | 1.000 | 0.792 | 0.208 | 32 |
| E2B | 12 | 1.000 | 0.625 | 0.375 | 22 |
| E4B | 7 | 0.667 | 0.375 | 0.438 | 29 |
| E4B | 8 | 0.833 | 0.583 | 0.300 | 30 |
| E4B | 9 | 0.833 | 0.708 | 0.150 | 34 |
| E4B | 10 | 0.917 | 0.583 | 0.364 | 30 |
| E4B | 11 | 1.000 | 0.750 | 0.250 | 32 |
| E4B | 12 | 1.000 | 0.750 | 0.250 | 26 |
| Qwen3-4B | 7 | 0.250 | 0.000 | 1.000 | 7 |
| Qwen3-4B | 8 | 0.583 | 0.208 | 0.643 | 9 |
| Qwen3-4B | 9 | 0.542 | 0.083 | 0.846 | 8 |
| Qwen3-4B | 10 | 0.750 | 0.125 | 0.833 | 10 |
| Qwen3-4B | 11 | 0.833 | 0.250 | 0.700 | 11 |
| Qwen3-4B | 12 | 0.958 | 0.333 | 0.652 | 11 |
| Qwen3-4B-Inst | 7 | 0.708 | 0.042 | 0.941 | 7 |
| Qwen3-4B-Inst | 8 | 0.792 | 0.125 | 0.842 | 8 |
| Qwen3-4B-Inst | 9 | 0.917 | 0.042 | 0.955 | 4 |
| Qwen3-4B-Inst | 10 | 0.875 | 0.042 | 0.952 | 10 |
| Qwen3-4B-Inst | 11 | 1.000 | 0.042 | 0.958 | 5 |
| Qwen3-4B-Inst | 12 | 1.000 | 0.125 | 0.875 | 6 |

Under the current stem B's apparent compliance is substantially vacuous on **all
four** models, not only on the Qwens: the vacuous share of passes runs 0.15–0.60
on the Gemmas and 0.64–1.00 on the Qwens. Honest compliance on
qwen3-4b-instruct-2507 is 0.042 at m = 9, 10 and 11 — one topic in twenty-four —
against an apparent 0.88–1.00. The median current-stem answer is 4 to 11 words on
the Qwens. This is the finding that motivates the exercise, and it replicates here
on a fresh draw.

---

## 4. The §1.4 verdict

The rule was frozen before the first generation. Its sentence — "at least one m …
inside the band, **and that rung** sits more than one standard error from both band
edges" — admits two readings of *that rung*: any in-band rung, or the smallest
in-band rung of §1.3. Both are reported. **They give the same study verdict.**

| model | in-band m | smallest | clear of both edges | permissive | strict |
|---|---|---|---|---|---|
| E2B | [10, 11] | 10 | [11] | PASS | MARGINAL |
| E4B | [8, 9, 10] | 8 | [10] | PASS | MARGINAL |
| Qwen3-4B | [11, 12] | 11 | [12] | PASS | MARGINAL |
| Qwen3-4B-Inst | [10, 11] | 10 | -- | MARGINAL | MARGINAL |

### Verdict: MARGINAL

Every model has at least one m in {7,…,12} whose floored B-solo compliance is
inside the registered focal band [0.60, 0.95]. **An honest focal severity exists at
m ≤ 12 on all four models.** But qwen3-4b-instruct-2507 has no in-band rung more
than one standard error from both edges: its two in-band rungs are both at 0.667,
which is 0.71 and 0.69 standard errors above the band floor.

Per §1.4, MARGINAL means **a fresh-topic confirmation is required before any grid
amendment**. The grid was not extended past m = 12, and no rung was chosen to
obtain a result.

Under the stricter reading every model is MARGINAL, because the *smallest* in-band
rung is by construction the one nearest a band edge.

---

## 5. The finding that changes the previous conclusion

The FORM × STEM screen concluded that the floored stem drives **both** Qwens to
`FOCAL_RANGE_EXHAUSTED` on the registered grid. On a fresh, independently seeded
draw of the same cells that is half right.

| model | registered grid {7, 8, 9, 10} under floored | Gate 2 outcome |
|---|---|---|
| E2B | 0.417 0.417 0.417 **0.917** | m\* = 10 |
| E4B | 0.500 **0.625** **0.667** **0.750** | m\* = 10 |
| Qwen3-4B | 0.042 0.125 0.167 0.375 | **FOCAL_RANGE_EXHAUSTED** |
| Qwen3-4B-Inst | 0.125 0.417 0.375 **0.667** | m\* = 10 |

**qwen3-4b-instruct-2507 does not terminate in this draw.** The FORM × STEM screen
measured 0.542 at m = 10, below the 0.60 floor; this screen measures 0.667, above
it. The terminal-status call flipped between two independent single draws on the
same 24 topics. The FORM × STEM report flagged that call as marginal — 0.54 against
a 0.60 floor, about 1.5 topics — and it was.

**qwen3-4b replicates decisively**: 0.375 against a 0.60 floor is 2.3 standard
errors, and the two screens agree to within 0.042 at every registered rung.

The correction matters for Amendment A. The honest statement is now: *the floored
stem terminates qwen3-4b on the registered grid, and its effect on
qwen3-4b-instruct-2507 is not resolved at 24 topics.* It is not "the stem
terminates both Qwens".

### The replication gap, measured

| model | m=7 | m=8 | m=9 | m=10 | mean abs gap |
|---|---|---|---|---|---|
| E2B | 0.500 → 0.417 | 0.458 → 0.417 | 0.625 → 0.417 | 0.750 → 0.917 | 0.125 |
| E4B | 0.417 → 0.500 | 0.667 → 0.625 | 0.708 → 0.667 | 0.875 → 0.750 | 0.073 |
| Qwen3-4B | 0.042 → 0.042 | 0.167 → 0.125 | 0.208 → 0.167 | 0.333 → 0.375 | 0.031 |
| Qwen3-4B-Inst | 0.167 → 0.125 | 0.250 → 0.417 | 0.417 → 0.375 | 0.542 → 0.667 | 0.094 |

Two independent single draws per topic under different seed roots. The mean
absolute gap is 0.031–0.125 and the largest single-rung gap is 0.208 (E2B, m = 9).
At 24 topics this is sampling noise of the size the standard errors predict, not
disagreement between the screens — but it is large relative to the 0.35-wide focal
band, which is exactly why a terminal-status call sitting 1.5 topics from a band
edge should never have been treated as settled.

---

## 6. The pooled extrapolation against direct measurement

| model | m=11 predicted | measured | gap | m=12 predicted | measured | gap |
|---|---|---|---|---|---|---|
| E2B | 0.812 | 0.833 | +0.021 | 0.904 | 1.000 | +0.096 |
| E4B | 1.000 | 1.000 | +0.000 | 1.000 | 0.958 | -0.042 |
| Qwen3-4B | 0.417 | 0.625 | +0.208 | 0.508 | 0.875 | +0.367 |
| Qwen3-4B-Inst | 0.667 | 0.667 | -0.000 | 0.796 | 0.958 | +0.162 |

The frozen protocol recorded the prior prediction — m = 11 or 12 for qwen3-4b,
m = 10 or 11 for qwen3-4b-instruct-2507 — and recorded that it should be treated as
**optimistic**, because on E2B the pooled figure had run about 0.09 above the direct
measurement.

Both predictions of *which rung* were right: qwen3-4b's first in-band rung is
m = 11, the Instruct model's is m = 10.

The prediction of *how much* was wrong in the opposite direction from the one
anticipated. A line fitted to the four registered rungs and extrapolated two rungs
**under**-predicts by +0.208 and +0.367 on qwen3-4b and by +0.162 at m = 12 on the
Instruct model. The registered-grid segment of the Qwen curves lies in a floor
region, and a line through a floor extrapolates far too flat. The extrapolation was
not a good model of a bounded proportion and should not be used again; the direct
measurement is what stands.

---

## 7. D(B←A) under the floored stem

With vacuity removed, the composed measurement is honest for the first time.
Paired on topics, at the in-band rungs:

| model | m | B solo | B in A+B | D(B←A) | paired SE | D/SE |
|---|---|---|---|---|---|---|
| E2B | 10 | 0.917 | 0.583 | +0.333 | 0.096 | +3.46 |
| E2B | 11 | 0.833 | 0.708 | +0.125 | 0.107 | +1.17 |
| E4B | 8 | 0.625 | 0.125 | +0.500 | 0.102 | +4.90 |
| E4B | 9 | 0.667 | 0.333 | +0.333 | 0.127 | +2.62 |
| E4B | 10 | 0.750 | 0.625 | +0.125 | 0.107 | +1.17 |
| Qwen3-4B | 11 | 0.625 | 0.708 | -0.083 | 0.101 | -0.83 |
| Qwen3-4B | 12 | 0.875 | 0.958 | -0.083 | 0.056 | -1.48 |
| Qwen3-4B-Inst | 10 | 0.667 | 0.708 | -0.042 | 0.125 | -0.33 |
| Qwen3-4B-Inst | 11 | 0.667 | 0.833 | -0.167 | 0.096 | -1.73 |

**The two families separate.** Both Gemmas show a positive delivery loss at their
in-band rungs, up to +0.500 at 4.9 standard errors. Both Qwens show
zero-to-slightly-negative, none beyond 1.7 standard errors of zero.

Two cautions. First, 24 topics at one draw is a small fraction of the confirmatory
design's 384 topics at M draws, so "indistinguishable from zero here" is a statement
about this screen's power, not about the estimand. Second, the sign is measured at
the screen's fixture severity A = 3, not at each model's Gate 2 n\*, which the stem
also moves.

---

## 8. A under the floored stem

The stem changes A as well as B, so n\* has to be re-anchored under whatever prompt
is finally adopted.

| model | A curve, floored (n = 1…8) | eligible n | n\* | compliance at n\* | would terminate |
|---|---|---|---|---|---|
| E2B | 0.708 0.500 0.500 0.542 0.417 0.458 0.542 0.458 | [1, 2, 3, 4, 7] | 1 | 0.708 | no |
| E4B | 0.833 0.667 0.875 0.792 0.750 0.625 0.583 0.583 | [1, 2, 4, 5, 6, 7, 8] | 2 | 0.667 | no |
| Qwen3-4B | 0.875 0.667 0.542 0.583 0.500 0.500 0.417 0.333 | [2, 3, 4, 5, 6] | 2 | 0.667 | no |
| Qwen3-4B-Inst | 0.958 1.000 0.958 1.000 0.500 0.417 0.333 0.500 | [5, 8] | 5 | 0.500 | no |

`TARGET_BAND` is (0.50, 0.85) with **inclusive** bounds — `low <= v <= high` in
`gates.select_severity` — and on that reading all four models keep an eligible n
and none would terminate.

**qwen3-4b-instruct-2507 is one topic from terminating.** Its floored A curve is
0.958, 1.000, 0.958, 1.000 at n = 1…4 — above the band ceiling — and then 0.500,
0.417, 0.333, 0.500. Its only two eligible rungs sit exactly *on* the 0.50 floor.
One topic fewer at n = 5 and n = 8 and the curve has no eligible rung at all:
`TARGET_RANGE_EXHAUSTED`. The FORM × STEM draw put n = 5 at 0.625, comfortably
inside, so this is not a stable feature — but it is a second place where this model
sits on a band edge under the stem, and it had not been measured before.

For comparison, the registered anchors under the **current** stem are n\* = 4, 1, 1,
3. Under the floored stem they are 1, 2, 2, 5. **Adopting the stem re-anchors A on
every model**, which is the mechanism by which it invalidates every reference rate
screened against the old anchor.

---

## 9. What this screen cannot decide

- **It cannot license a grid amendment.** The verdict is MARGINAL, and that branch
  requires a fresh-topic confirmation first. These 24 topics are the development
  sample and have now been spent three times.
- **It cannot settle qwen3-4b-instruct-2507 under the stem.** Two independent draws
  put it on opposite sides of the focal band floor at m = 10, and a third quantity —
  its A-side target-band eligibility — sits exactly on a band edge.
- **It says nothing about the reference pool.** No reference family was generated
  here. Every reference rate must be re-screened under whatever prompt is finally
  adopted, because reference solo compliance depends on the stem through response
  length exactly as B's does.
- **It is 24 topics at one draw.** Gate 2 measures on 96 disjoint solo-calibration
  topics at M = 4. Nothing here has been shown to predict that.
- **It registers nothing.** m = 11 and m = 12 remain unregistered.

---

## 10. Amendment C

Drafted to `user-notes/DCI1_v4_amendment_C_focal_grid.md`. **Not adopted.** The
registered grid is unchanged.

---

## 11. Artifacts

| path | contents |
|---|---|
| `dci1/reports/bgrid_screen_v4/screen_protocol.json` | the frozen protocol, hash `6a63ba78…` |
| `dci1/reports/bgrid_screen_v4/results.json` | every readout, machine-readable |
| `dci1/reports/bgrid_screen_v4/REPORT.md` | this report |
| `dci1/evidence/bgrid-screen-v4/<model>/screen-cap512/cache.jsonl` | 528 scored rows per model |
| `dci1/src/bgrid_screen_v4/` | the apparatus |
| `dci1/tests_v4/test_bgrid_screen_isolation.py` | 16 isolation and extension-identity tests |
| `user-notes/DCI1_v4_amendment_C_focal_grid.md` | the amendment draft |
