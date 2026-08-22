# DCI-1 v4r4 — scientific follow-up evidence package

**Read-only.** Nothing in this task modified code, re-ran generation,
re-ran or overwrote a registered analysis, changed a stage record,
regenerated a mask, unmasked anything, repaired the L4 artifact, or altered
superseded evidence. Every registered number below is copied from a signed
record; every derived number is recomputed from the rows those records were
built on, and says so.

Machine-readable companions: `reports/dci1v4r4/followup_diagnostics/`
(files `00`–`10`, plus the `_*.py` scripts that produced them). That
directory is **not** registered evidence and nothing in it was
preregistered.

**Verified after the fact**: `tools/v4r4_evidence_manifest.py --verify`
reports `OK` — 0 files missing, 0 changed, 0 added across all 355 evidence
files and 155,712 scored rows. The only new paths in the working tree are
this report and `followup_diagnostics/`.

**Self-check**: every headline number below was re-read from the artifact it
came from — 39 checks, 39 pass (`11_crosscheck.json`). All twenty registered
point estimates across the two survivors reproduce from the signed rows to
better than 1e-9 with no estimator, no `ObservationTable` and no bootstrap.

Three labels are used throughout and never mixed:

| Label | Meaning |
|---|---|
| **REGISTERED** | produced by a preregistered v4r4 stage, signed and mirrored |
| **PRE-REGISTERED DIAGNOSTIC** | a derived artifact of the registered pipeline's own reporting tools |
| **POST-HOC DIAGNOSTIC** | produced by this task; descriptive only; carries no claim level, no multiplicity adjustment and no identification status |

---

## 1. Final study state

Verified from signed records, not from prose. `01_final_state.json`.

| Model | Stages | Terminal | Design | n\* | m\* | Focal ext. | Reached confirmation? |
|---|---|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | 6 of 12 | `COMPOSED_HEADROOM_FAILURE` | **full** (47 cells) | 1 | 10 | no | **no** |
| `qwen3-4b-instruct-2507` | 6 of 12 | `COMPOSED_HEADROOM_FAILURE` | reduced (8) | 5 | 10 | no | **no** |
| `gemma-3n-e4b-it` | **12 of 12** | — | reduced (8) | 4 | 10 | no | **yes** |
| `qwen3-4b` | **12 of 12** | — | reduced (8) | 2 | 12 | **yes** | **yes** |

Both terminations are at **Gate 4**, before any confirmatory generation.
Both terminal records carry §28.3's sentence — *"a terminal pre-confirmatory
status carries no evidence about the effect"* — and neither is treated below
as a scientific result. Neither was revisited: §13.10 forbids it, and no
rung, caliper, reference or threshold was changed in response.

**Registered lifecycle facts for the two survivors** (all REGISTERED):

| | `qwen3-4b` | `gemma-3n-e4b-it` |
|---|---|---|
| Gate 5 freeze | PASS at `450a049`, 66 §18.1 fields | same |
| Confirmatory rows | 24,576 / 384 blocks / M=8 | 24,576 / 384 / 8 |
| Completeness | 0 missing, 0 duplicated, 0 unexpected | same |
| Masked artifact | `3368b857…` | `6ca030d9…` |
| Mask effectiveness | 6 groups, 2 maskable, differing share 0.5 | identical |
| Unmask binds artifact | yes | yes |
| `analysis_code_hash` | `dffb5a86…` | **same** — the two are comparable |
| Resamples | 10,000 | 10,000 |
| Measurement basis | `deterministic_measurement_validated` | same |

**Identification.** Both survivors carry
`EXCESS_NOT_IDENTIFIED`, `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and
`COMPANION_CLASS_NOT_MATCHED`. Six registered quantities are
**NOT_IDENTIFIED for every surviving replication**: `Δ_R`, `Δ_j`,
`δ_difficulty`, `Ξ`, `D(B←R_j)`, `D(R_j←B)`. Identified and estimated:
`D(A←B)`, `D(B←A)`, `Λ`, `D(B←CL)`, `Δ_class`, the F5 robustness recodings
and the F6 vacuity differences.

**The full-design replication is the one that died.** `gemma-3n-e2b-it` was
the sole replication that identified the difficulty spectrum, and Gate 4
ended it. No surviving replication identifies a spectrum-dependent quantity.

### 1.1 One value in an existing summary does not reproduce

`reports/dci1v4r4/EXECUTION_REPORT.md` line 343 reads *"Three of four models
admitted none [no core reference]"*. The signed Gate-3 records say
otherwise: **`qwen3-4b` admitted two** core references (`RF11:21`, `CR5:8`),
both of which supply a straddling triple. Two of four admitted none
(`gemma-3n-e4b-it`, `qwen3-4b-instruct-2507`). Three of four ran the reduced
design, which is the true statement the sentence garbles: `qwen3-4b` fell to
reduced because §13.4 requires **three**, not because it had none.
Flagged, not silently copied and not corrected here — this task is
read-only. `02_admission_landscape.json`.

---

## 2. Class-control results (Q1)

### 2.1 What CL was, and why Gate 3 chose it

§13.7 admits **one** production-class companion: the eligible
production-class rung minimising `|ι − ι_A|`. There is no caliper on raw
solo compliance and no headroom band at admission. That single fact governs
§5 below.

| Model | CL | Constraint (verbatim) | Cal. solo | Cal. chance | ι | ι_A | \|ι−ι_A\| |
|---|---|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | `CX2:1` | *Your answer must use exactly 1 semicolons.* | 0.6276 | 0.1276 | 0.5731 | 0.5739 | 0.0008 |
| `gemma-3n-e4b-it` | `CL7:80` | *At least 80 words must contain letter a.* | 0.7083 | 0.0000 | 0.7083 | 0.6948 | 0.0136 |
| `qwen3-4b` | `CX1:4` | *Use the word thus exactly 4 times.* | 0.6953 | 0.0000 | 0.6953 | 0.7017 | 0.0063 |
| `qwen3-4b-instruct-2507` | `CL8:3` | *At least 3 words must end with y.* | **0.9740** | **0.9323** | 0.6154 | 0.5963 | 0.0191 |

For reference, A is *"Use the word **however** exactly n\* times"* and B is
*"Every word in the answer must have at most m\* letters"* on every model.

**The class arm is not comparable across the two survivors, and the reason is
structural.** `qwen3-4b`'s CL (`CX1:4`, "use the word *thus* exactly 4
times") is the **same constraint form as A** — an exact-count token
production constraint, differing only in the token and the count.
`gemma-3n-e4b-it`'s CL (`CL7:80`, "at least 80 words must contain letter a")
is a different form that also **forces a long answer**. §13.7 matched on ι
alone, and ι is blind to form.

### 2.2 Registered class-control estimands

All REGISTERED, copied from the signed `UNMASKED_ANALYSIS` records
(`08_claim_ladder_audit.json`). Intervals are **simultaneous** (F9 has two
members; Šidák). Every precision precondition is met.

**`qwen3-4b`**

| Estimand | Config | Estimate | SE | Simultaneous | Half-width | Precond. |
|---|---|---|---|---|---|---|
| `D(B←CL)` | outcome_first | −0.1341 | 0.0137 | [−0.1647, −0.1035] | 0.0306 | met (0.05) |
| `D(B←CL)` | outcome_second | −0.0505 | 0.0140 | [−0.0814, −0.0195] | 0.0309 | met |
| `Δ_class` | outcome_first | +0.0114 | 0.0099 | [−0.0106, +0.0334] | 0.0220 | met (0.06) |
| `Δ_class` | outcome_second | +0.0384 | 0.0134 | [+0.0088, +0.0680] | 0.0296 | met |

**`gemma-3n-e4b-it`**

| Estimand | Config | Estimate | SE | Simultaneous | Half-width | Precond. |
|---|---|---|---|---|---|---|
| `D(B←CL)` | outcome_first | +0.3164 | 0.0173 | [+0.2793, +0.3535] | 0.0371 | met |
| `D(B←CL)` | outcome_second | **+0.7946** | 0.0146 | [+0.7624, +0.8268] | 0.0322 | met |
| `Δ_class` | outcome_first | −0.3102 | 0.0185 | [−0.3498, −0.2706] | 0.0396 | met |
| `Δ_class` | outcome_second | −0.5114 | 0.0173 | [−0.5495, −0.4733] | 0.0381 | met |

F6 vacuity, also registered: on `qwen3-4b`, `vac(B|B+CL) − vac(B solo)` =
**+0.1292** [+0.0980, +0.1604] in outcome_first — the largest vacuity move in
the study, and the reason §17.4's gate binds there. On
`gemma-3n-e4b-it` the same quantity is +0.0003 and the gate does not bind in
either configuration.

### 2.3 Underlying raw rates

POST-HOC recomputation from the signed rows (`06_effects_and_order.json`);
each registered point estimate above reproduces from these to <1e-9.

| | `qwen3-4b` | `gemma-3n-e4b-it` |
|---|---|---|
| solo A | 0.7197 | 0.7718 |
| solo B | 0.7793 | 0.8512 |
| solo CL | 0.6292 | 0.7152 |
| B in `B+CL`, B first | 0.9134 | 0.5348 |
| B in `CL+B`, B second | 0.8298 | **0.0566** |
| CL in `CL+B`, CL first | 0.3529 | 0.6090 |
| CL in `B+CL`, CL second | 0.3988 | 0.6621 |

### 2.4 Does the class-control effect resemble A's effect on B?

**`qwen3-4b`: yes, almost exactly.** `Δ_class` = +0.0114 (interval spans 0)
in outcome_first and +0.0384 [+0.0088, +0.0680] in outcome_second. A and CL
do nearly the same thing to B — which is what one expects when CL is A's
structural twin. Note what this does **not** license: with
`EXCESS_NOT_IDENTIFIED` standing, a small `Δ_class` is not evidence that A's
effect is generic. It says A and *this one* production-class companion are
indistinguishable in their effect on B.

**`gemma-3n-e4b-it`: no, strongly not.** `Δ_class` is −0.3102 and −0.5114:
CL damages B **far more** than A does. The mechanism is legible in §4 —
`CL7:80` forces a long, letter-a-rich answer, and B is the maximum-word-length
constraint.

### 2.5 Quantities that do not exist

| Quantity | Status | Why |
|---|---|---|
| `D(CL←B)` | **NOT_REGISTERED** | The cells exist, so it is computable, but no `FAMILY_MEMBERS` entry contains it. Reported POST-HOC only: `qwen3-4b` +0.2764 / +0.2305; `gemma-3n-e4b-it` +0.1061 / +0.0531 (outcome_first / outcome_second). No interval, no claim. |
| `D(A←CL)` | **NOT_REGISTERED and NOT_IDENTIFIED** | No `A+CL` cell exists in any §8.6 design, so the data do not exist either. |
| `Δ_class` for terminated models | **NOT_IDENTIFIED** | They produced no confirmatory data. Their Gate-4 tables are calibration material at M=4 on 24 topics, not effect estimates. |

---

## 3. Directionality and order (Q2)

### 3.1 The registered mapping, stated once

§11.1 defines **configuration = the position of the OUTCOME constraint**.
So `D(A←B)|outcome_first` and `D(B←A)|outcome_first` are read from
**different cells**. Writing the two composed cells out removes the ambiguity:

| Cell | `qwen3-4b` A | `qwen3-4b` B | `e4b` A | `e4b` B |
|---|---|---|---|---|
| solo | 0.7197 | 0.7793 | 0.7718 | 0.8512 |
| **A first, B second** | 0.3278 | 0.7913 | 0.6559 | 0.5680 |
| **B first, A second** | 0.3906 | 0.9020 | 0.8040 | 0.8451 |

Every registered directional estimand is `solo − composed` on this table, and
all ten registered point estimates per model reproduce from it to <1e-9
(`06_effects_and_order.json`, `recomputation_agrees_with_record`).

### 3.2 Registered directional results

**`qwen3-4b`** (simultaneous intervals, F1 has 6 registered members)

| | outcome_first | outcome_second |
|---|---|---|
| `D(A←B)` | **+0.3919** [+0.3503, +0.4335] | **+0.3291** [+0.2835, +0.3747] |
| `D(B←A)` | −0.1227 [−0.1536, −0.0918] | −0.0120 [−0.0450, +0.0209] |
| `Λ` | −0.5146 [−0.5671, −0.4622] | −0.3411 [−0.3989, −0.2834] |

**`gemma-3n-e4b-it`**

| | outcome_first | outcome_second |
|---|---|---|
| `D(A←B)` | **+0.1159** [+0.0771, +0.1546] | −0.0322 [−0.0734, +0.0089] |
| `D(B←A)` | +0.0062 [−0.0182, +0.0306] | **+0.2832** [+0.2485, +0.3179] |
| `Λ` | −0.1097 [−0.1546, −0.0648] | +0.3154 [+0.2594, +0.3714] |

### 3.3 Which constraint is sacrificed

**`qwen3-4b` — a genuine, order-robust trade-off.** In *both* composed cells
A collapses (0.720 → 0.328 / 0.391) and B is unharmed or helped (0.779 →
0.791 / 0.902). A is sacrificed for B regardless of order. The magnitude
changes with order (D(A←B) 0.392 vs 0.329) but the direction does not.

**`gemma-3n-e4b-it` — not a trade-off at all.** Read the cells rather than
the estimands: in **A-first**, *both* constraints lose (A 0.772→0.656, B
0.851→0.568). In **B-first**, *neither* does (A 0.772→0.804, B 0.851→0.845).
There is no constraint that is consistently sacrificed. The apparent
"flip in which constraint is harmed" is what the registered indexing does to
this pattern: `D(A←B)|outcome_first` and `D(B←A)|outcome_second` are the same
bad cell read twice, and `D(A←B)|outcome_second` and `D(B←A)|outcome_first`
are the same good cell read twice. **This is a first-mentioned-constraint
effect on the pair, not a directional interference asymmetry.**

**Sign reversals.** On `gemma-3n-e4b-it`, `Λ` reverses sign between
configurations (−0.1097 → +0.3154) with both simultaneous intervals
excluding zero. The two *within-configuration* signs are each statistically
supported at the registered level. Whether the *difference* between them is
supported is §7 — and the honest answer is that v4r4 registers no test of it.

**Are the two models qualitatively different? Yes**, and it is the clearest
cross-model result in the study: one order-robust trade-off, one order-driven
joint failure. With n = 2 survivors this is described, not estimated; no
pooled scalar and no model-dependence estimand exists.

---

## 4. Response-length and strategy — POST-HOC DESCRIPTIVE / MECHANISTIC DIAGNOSTIC (Q3)

**Response length is post-treatment.** Composition changes it. Nothing below
conditions on length and reads the residual causally, and no quantity here
carries a claim level. `04_confirmatory_raw.json`, `05_length_strategy.json`,
`10_response_samples.json`.

### 4.1 The verifier statistics make the mechanism readable

The scored rows carry each verifier's own statistic. For **B** it is the
**length of the longest word**; for **A** it is the **number of occurrences
of "however"**; for **RF11** it is the **count of vowel-initial words**.
B and RF11 are budget constraints whose statistic falls as answers get
shorter; A and the `CX`/`CL` families are production constraints whose
statistic must hit a target.

### 4.2 Length by cell

| Cell | `qwen3-4b` median words | B max-word median | `e4b` median words | B max-word median |
|---|---|---|---|---|
| A solo | 77 | — | 123 | — |
| B solo | 55 | 11 | 83 | 9 |
| A first, B second | 55 | 11 | 96 | 10 |
| B first, A second | **47** | 10 | 89 | 9 |
| B first, CL second | **34** | 10 | 110 | 10 |
| CL first, B second | 43 | 11 | **111** | **12** |
| CL solo | 66 | — | 126 | — |

**Adding a companion shortens `qwen3-4b`'s answers substantially** (77 → 34
words at the extreme) and B's compliance rises as they shorten. On
`gemma-3n-e4b-it` the class companion does the opposite: `CL7:80` demands at
least 80 letter-a words, answers grow to ~110 words, and B's longest word
goes from 9 to 12 against a severity of 10.

### 4.3 Compliance by length **within** cell — the length hypothesis fails

Holding the cell fixed (so the companion is fixed) and binning by word count:

**`qwen3-4b`, B compliance:**

| Cell | 30–45 w | 45–60 w | 60–80 w |
|---|---|---|---|
| B solo | 0.765 | 0.797 | 0.748 |
| A first, B second | 0.852 | 0.798 | 0.750 |
| **B first**, A second | **0.915** | **0.891** | **0.892** |
| **B first**, CL second | **0.899** | **0.886** | 0.838 |
| CL first, B second | 0.838 | 0.799 | 0.872 |

At **matched length**, B-first cells sit ~0.09–0.14 above B-solo and
B-second cells. Length moves with the effect but **does not account for it**;
position does. (A within-cell length comparison is still a comparison across
a post-treatment variable and is descriptive only.)

**`gemma-3n-e4b-it`, B compliance in the 80–110-word bin:** B solo 0.881,
A-first/B-second 0.566, B-first/A-second 0.853, B-first/CL-second 0.533,
**CL-first/B-second 0.069**. At identical length the CL-first cell destroys
B. Length is not the mechanism there either — **lexical register** is.

### 4.4 Truncation, empties, finish reasons

Registered generation integrity, both survivors: 0 empty answers, 0
processing failures, all outcomes `OK`. Truncation (`finish_reason = length`)
is 6 rows on `qwen3-4b` (0.0244%) and 1 on `gemma-3n-e4b-it` (0.0041%).
**Truncation is far too rare to explain anything.**

Vacuity is registered and is not rare: `qwen3-4b`'s B vacuous-pass rate
reaches **0.132** in the B-first/CL-second cell against ~0.002 solo. This is
what F6 measures and what §17.4's gate responds to.

### 4.5 Representative responses (illustrative; selected by topic order and draw 0, never by compliance)

**`qwen3-4b`, B solo** (62 w, longest word 12, passes) — telegraphic
short-word register:
> "Noise cancelling headphones use microphones to detect sound. They analyze
> sound waves. Then, they create opposite waves. These waves cancel out
> noise. The system adjusts in real time…"

**`qwen3-4b`, A first + B second** (82 w, A statistic 3 vs target 2, **A
fails**):
> "…**However**, this works best in quiet environments. **However**, loud
> noises may still be heard…"

**`qwen3-4b`, B first + A second** (42 w, A statistic 2, passes) — the token
is stuffed rather than used:
> "The system works **however**. It uses feedback loops. These loops adjust
> the sound. The tech works **however**."

**`qwen3-4b`, B first + CL second** (41 w, CX1 statistic 5 vs target 4,
**CL fails**) — same stuffing failure with a different token:
> "This process is **thus** effective. The system **thus** reduces background
> sound. **Thus**, it improves listening experience. **Thus**, it helps in
> focusing. Each step **thus** works together."

**`gemma-3n-e4b-it`, B solo** (94 w, longest word 9, passes) — deliberate
short-word paraphrase, "heads" for "headphones":
> "Noise-canceling **heads** use clever tech to block out sound. They have
> tiny mics that listen to noise…"

**`gemma-3n-e4b-it`, CL first + B second** (122 w, longest word 12, **B
fails**) — Latinate, letter-a-rich register:
> "…**dramatically** alter how we manage unwanted **ambient** sounds… a
> dedicated processor **analyzes**… **practically** a mirror image"

### 4.6 What the diagnostic supports

Two distinct mechanisms, both descriptive:

1. **Overshoot on exact-count production constraints.** `qwen3-4b`'s A
   fails by *overshooting* (occurrence distribution shifts from a mode at 2
   to heavy mass at 3–6), and its class companion `CX1` fails the same way.
   That is why `Δ_class ≈ 0` on that model.
2. **Register capture on budget constraints.** Whichever constraint sets the
   lexical register determines whether the maximum-word-length constraint can
   be met. On `gemma-3n-e4b-it` the first-stated constraint appears to win
   the register, which is why one ordering is bad for both constraints.

Neither is a registered estimand and neither is causal. Both are testable in
a future revision with an order-and-form factorial.

---

## 5. Gate-4 failure anatomy (Q4)

`03_gate4_anatomy.json`. §13.10 evaluates **every registered cell's raw
compliance rate for each constraint** against
`COMPOSED_HEADROOM_BAND = (0.05, 0.95)`, on the 24 reserved composed topics
at `M_CAL = 4`.

| Model | Cells | Rate checks | Failing | Outcome |
|---|---|---|---|---|
| `gemma-3n-e2b-it` | 46 rated (+`unconstrained`) | 80 | **5** | TERMINAL |
| `qwen3-4b-instruct-2507` | 7 | 11 | **1** | TERMINAL |
| `gemma-3n-e4b-it` | 7 | 11 | 0 | PASS |
| `qwen3-4b` | 7 | 11 | 0 | PASS (narrowly: `B` in `B+CL` at 0.9479) |

(The `unconstrained` cell carries no instructed constraint and so contributes
no rate check; `e2b`'s 47-cell full design therefore yields 46 rated cells.)

### 5.1 `qwen3-4b-instruct-2507` — the failure was **not** compositional

The single failing cell is **`solo:CL`** at 0.9896. A solo cell.

| Stage | `CL8:3` — *"At least 3 words must end with y."* |
|---|---|
| Pre-screen (24 topics × 1) | solo 0.500, ι 0.500 |
| Gate-2 calibration (96 × 4) | **solo 0.9740, chance 0.9323**, ι 0.6154, vacuity 0.0026 |
| Gate-3 admission | ADMITTED: \|ι − ι_A\| = 0.0191, the smallest of any eligible production rung |
| Gate-4 composition (24 × 4) | solo **0.9896** → above the 0.95 ceiling → TERMINAL |

**Anatomy in one sentence: §13.7 admits on ι, §13.10 checks the raw rate, and
nothing between them checks the raw rate.** "At least 3 words must end with
y" is satisfied by ordinary English prose 93% of the time unasked;
`CHANCE_DEGENERACY_MAX = 0.99` let that through and
`SPECTRUM_ELIGIBILITY_BAND = (0.1, 0.95)` bounds ι, not compliance. The
constraint's raw solo compliance was already 0.974 at Gate 2 — **the Gate-4
failure was fully determined one gate earlier and merely observed at Gate 4.**
Composition, order, length and iota are all irrelevant to it.

### 5.2 `gemma-3n-e2b-it` — a genuine compositional ceiling, and its cause

All five failures involve `RF11` — *"Words beginning with vowels: at most N"*
— paired with **B**, *"Every word in the answer must have at most 10
letters."*

| Cell | Slot | Rate | Band |
|---|---|---|---|
| `pair:B+R3` | B (`B:10`) | 0.9583 | **FAIL** |
| `pair:B+R3` | R3 (`RF11:26`) | 0.9688 | **FAIL** |
| `pair:R3+B` | R3 (`RF11:26`) | 0.9583 | **FAIL** |
| `pair:B+R3+` | R3+ (`RF11:32`) | 1.0000 | **FAIL** |
| `pair:R3++B` | R3+ (`RF11:32`) | 1.0000 | **FAIL** |

The verifier statistics say why (POST-HOC, from the Gate-4 scored rows):

| Cell | median words | `RF11` statistic (vowel-initial count) | `RF11:26` pass |
|---|---|---|---|
| `RF11:26` solo | 80 | 24 | 0.635 |
| `RF11:26` + `RF9:10` | 72 | 23 | 0.740 |
| `RF11:26` + `CR5:2` | 84 / 75 | 26 / 23 | 0.542 / 0.719 |
| **`RF11:26` + `B:10`** | **76 / 70** | **17 / 18** | **0.969 / 0.958** |

Composing with **B** cuts the vowel-initial count from ~24 to ~17 because
B forces shorter words and shorter answers, and `RF11`'s budget of 26 then
becomes trivially satisfiable. Pairing the same `RF11` rung with other
references barely moves it. **The ceiling is produced by B specifically, and
B is the outcome constraint of the whole study.**

Note also that `RF11:32`'s *solo* Gate-4 rate was already 0.9375 — inside the
band by 0.0125. It was admitted as the spectrum's upper rung on ι
(0.854, inside `[0.1, 0.95]`) while its raw compliance sat one step from the
ceiling.

### 5.3 What Gate-4 failure was and was not associated with

| Factor | Evidence |
|---|---|
| **High chance compliance** | **Decisive for qwen-instruct** (0.9323). ι hid it; the raw rate exposed it. |
| **High solo compliance at admission** | **Decisive for both.** `CL8:3` solo 0.974; `RF11:32` solo 0.919 at calibration and 0.938 at Gate-4 solo. |
| **ι** | Not associated. Every failing constraint was admitted *because* its ι matched A closely. |
| **Family / form** | **Strongly associated.** All e2b failures are one family (`RF11`, vowel-initial budget); qwen-instruct's is a near-vacuous y-final production rung. |
| **Severity** | Associated within family — the two loosest `RF11` rungs (26, 32) failed, the tightest (21) did not. |
| **Response length** | Associated as the *channel* for e2b (composition shortens answers → budget statistic falls). Irrelevant for qwen-instruct. |
| **Order** | Not associated. Both e2b `RF11` rungs failed in **both** orders. |
| **Composition itself** | **True for e2b** (solo 0.635 → composed 0.969). **False for qwen-instruct**, whose failing cell is solo. |

### 5.4 Companion trajectories, pre-screen → Gate 4

Full table in `03_gate4_anatomy.json` (`companion_trajectories`). The
`gemma-3n-e2b-it` slots involved in the failure:

| Slot | Constraint | Pre-screen ι | Cal. ι | Cal. solo | Gate-4 solo | Gate-4 composed with B |
|---|---|---|---|---|---|---|
| `B` | `B:10` | — | — | 0.7995 | 0.8333 | 0.9583 (with `R3`) |
| `R3` | `RF11:26` | 0.476 | 0.633 | 0.688 | 0.635 | **0.969 / 0.958** |
| `R3+` | `RF11:32` | 0.941 | 0.854 | 0.919 | 0.938 | **1.000 / 1.000** |
| `R3−` | `RF11:21` | 0.273 | 0.336 | 0.341 | 0.354 | 0.823 / 0.760 |
| `R1` | `RF9:10` | 0.632 | 0.534 | 0.646 | 0.771 | passes |
| `R2` | `CR5:2` | 0.667 | 0.632 | 0.633 | 0.635 | passes |
| `CL` | `CX2:1` | 0.600 | 0.573 | 0.628 | 0.656 | passes |

**The methodological reading**: solo-matched references became uninformative
under composition because §13.4's matching coordinate (ι, measured solo) is
invariant to the thing that changed (the response distribution the companion
induces). A budget constraint matched on solo ι is not matched on composed
compliance, because composition moves the response length that its statistic
integrates over.

---

## 6. Reference-spectrum identification (Q5)

`02_admission_landscape.json`, `09_coverage_vs_calibration.json`. All
verdicts were produced by calling the **registered** selection functions
(`admit_family`, `eligible`, `select_spectrum_triple`) on the signed Gate-2
calibration table — nothing was reimplemented.

Registered thresholds: `REFERENCE_CALIPER` 0.075 on ι,
`REFERENCE_PRESCREEN_CALIPER` 0.10, `REFERENCE_NEWCOMBE_REGION` 0.05,
`REFERENCE_VACUITY_MAX` 0.10, `CHANCE_DEGENERACY_MAX` 0.99,
`SPECTRUM_ELIGIBILITY_BAND` (0.10, 0.95), `SPECTRUM_OFFSET` 0.20,
`N_CORE_REFERENCES` **3**.

### 6.1 Per model: exactly why each landed where it did

| Model | Families admitted | Straddling | Core refs | Design | Reason |
|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | 4 — `CR5:2`, `RF9:10`, `RF11:26`, `RF6:1` | 3 | **3** | **full** | `RF6` admitted but **cannot straddle** (dropped for no triple); the other three each supply a triple. |
| `qwen3-4b` | 2 — `RF11:21`, `CR5:8` | **2** | **2** | reduced | **Both admitted families straddle and both supply a valid triple.** It failed only because §13.4 requires **three** families from three feature groups. A usable two-family spectrum existed and was discarded. |
| `gemma-3n-e4b-it` | 1 — `RF9:13` | 0 | **0** | reduced | The single admitted family cannot straddle: no eligible rung strictly above ι_A. |
| `qwen3-4b-instruct-2507` | 1 — `RF7:24` | 0 | **0** | reduced | Same shape: `RF7`'s other eligible rungs are all below A. |

### 6.2 Rejection landscape

Admissible rungs, of those measured at calibration:

| Model | Admissible / measured |
|---|---|
| `gemma-3n-e2b-it` | 4 / 21 |
| `gemma-3n-e4b-it` | 1 / 20 |
| `qwen3-4b` | 3 / 23 |
| `qwen3-4b-instruct-2507` | 1 / 20 |

Rejection reasons, pooled over all four models (a rung may carry several):

| Reason | Count |
|---|---|
| ι distance above the 0.075 caliper | **66** |
| pre-screen distance above the 0.10 caliper | 47 |
| Newcombe interval misses the region | 42 |
| ι outside the eligibility band | 7 |
| solo vacuity above 0.10 | 2 |

Wording caliper, witnesses and parse independence rejected **nothing**. The
binding constraint is entirely **distance from ι_A after re-measurement**.

### 6.3 The failure mode, quantified

Every model passed **all seven** §12.6 coverage conditions C1–C7 at
pre-screen. Then:

| Model | C4 straddling families (full ladder, pre-screen; needs ≥4) | Straddling after 96-topic calibration (needs ≥3) | Attrition | Design |
|---|---|---|---|---|
| `gemma-3n-e2b-it` | 7 | 3 | −57% | full |
| `gemma-3n-e4b-it` | 5 | **0** | −100% | reduced |
| `qwen3-4b` | 4 | 2 | −50% | reduced |
| `qwen3-4b-instruct-2507` | 4 | **0** | −100% | reduced |

The pre-screen measures the complete 94-rung ladder at **24 topics × 1
draw**; Gate 2 re-measures a ≤29-rung shortlist at **96 topics × 4 draws** on
a disjoint split. The two ι estimates disagree by a median of **0.057 to
0.116** depending on the model — *the same magnitude as the 0.075 caliper the
shortlist then has to clear.* C4 was written with "one spare"
(`COVERAGE_MIN_STRADDLING_FAMILIES = 4` against a requirement of 3); the
observed attrition is 50–100%.

ι_A itself moves between the two stages by −0.048 to +0.028, so the target
shifts while the candidates are re-estimated — both ends of the distance are
noisy at pre-screen.

**The methodological reading**: §12.6's coverage gate certifies the ladder
against a noisy estimate of the same quantity §13.4 later matches on, at a
sample size an order of magnitude smaller and with no allowance for
selection. Passing C1–C7 predicts nothing about surviving §13.4, and on
three of four models it predicted the wrong answer. No reference is proposed
here and no threshold is relaxed.

---

## 7. Operating-point comparison (Q6)

`07_operating_points.json`. All REGISTERED. Completion cap is 512 on every
model; the difficulty coordinate is `instructed_compliance` throughout.

| | `e2b` | `e4b` | `qwen3-4b` | `qwen-instruct` |
|---|---|---|---|---|
| n\* / A wording | 1 / "however × 1" | 4 / "however × 4" | 2 / "however × 2" | 5 / "however × 5" |
| A solo / chance / ι_A | 0.617 / 0.102 / **0.574** | 0.727 / 0.104 / **0.695** | 0.719 / 0.057 / **0.702** | 0.602 / 0.013 / **0.596** |
| m\* / B wording | 10 / "≤10 letters" | 10 | **12** | 10 |
| B solo / chance / ι_B | 0.799 / 0 / 0.799 | 0.849 / 0 / **0.849** | 0.742 / 0 / **0.742** | 0.680 / 0 / 0.680 |
| B solo vacuity | 0.000 | 0.000 | 0.005 | 0.057 |
| Focal extension used | no | no | **yes** | no |
| m\* is the last rung measured | **yes** | **yes** | **yes** | **yes** |

**`qwen3-4b`'s complete B curve, m = 7…12** (REGISTERED, Gate 2 `focal`):

| m | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|
| B solo compliance | 0.031 | 0.107 | 0.245 | 0.411 | 0.659 | **0.742** |

`FOCAL_BAND = (0.60, 0.95)`, so only m = 11 and 12 are in band; had B:12 also
fallen short the replication would have recorded `FOCAL_RANGE_EXHAUSTED`.

**Neighbouring rungs on the other three** (measured, in band nowhere else):

| m | 7 | 8 | 9 | 10 |
|---|---|---|---|---|
| `e2b` | 0.430 | 0.552 | 0.620 | **0.799** |
| `e4b` | 0.456 | 0.628 | 0.729 | **0.849** |
| `qwen-instruct` | 0.128 | 0.305 | 0.479 | **0.680** |

### 7.1 Assessment

**Two of the differences are real and one commonly-cited one is not.**

1. **`m*` is the top of the measured grid on all four models**, not just
   `qwen3-4b`. Every replication's B sits at the edge of its measured range.
   `qwen3-4b` is distinctive only in having needed the *extension* (11, 12)
   to reach the band at all.
2. **`qwen3-4b` operates on a much steeper and lower B curve.** At the
   common rung m = 10 its B compliance is 0.411 against `e4b`'s 0.849 —
   `qwen3-4b` writes with far more long words, and needed a two-step looser
   constraint to reach comparable compliance. So `B:12` on `qwen3-4b` and
   `B:10` on `e4b` are matched on *compliance* (0.742 vs 0.849) and not on
   *constraint content*.
3. **The two survivors are well matched on ι_A** (0.702 vs 0.695, a
   difference of 0.007) and on A solo compliance (0.719 vs 0.727). The focal
   arm is genuinely comparable; the outcome arm is not.
4. **The class arms are not comparable at all** (§2.1): `CX1:4` is A's
   structural twin, `CL7:80` is a length-forcing constraint of a different
   family. §13.7 matched them on ι, which is blind to this.

**Could the qualitative cross-model difference be partly an operating-point
artefact? Yes, plausibly, and the study cannot separate it.** `qwen3-4b`
carries a looser B (12 letters) and n\* = 2, `gemma-3n-e4b-it` a tighter B
(10) and n\* = 4. Those two facts alone could produce "A is sacrificed" on
one model and "the first-stated constraint wins" on the other. No composed
cell was generated at any other (n, m), so nothing in the existing data
separates model identity from operating point. **This is the single largest
confound in the cross-model comparison** and is answerable only by a new
experiment.

---

## 8. Claim-ladder audit (Q8)

`08_claim_ladder_audit.json` holds the complete table (44 rows: 2 models × 2
configurations × 11 estimands) with estimate, SE, marginal and simultaneous
intervals, half-width, Šidák critical value and family size, precision
verdict, identification status, claim level and emission reason.

### 8.1 Registered levels, as emitted

| Model | Config | Level | Member | Emitted | Reason if withheld |
|---|---|---|---|---|---|
| `qwen3-4b` | first | **L1** | `D(A←B)` | **yes** | — |
| `qwen3-4b` | first | L1 | `D(B←A)` | no | simultaneous lower bound not above 0 |
| `qwen3-4b` | first | L2 | `Λ` | no | gate is L1 in **both** directions; `D(B←A)` did not reach L1 |
| `qwen3-4b` | first | L3 | — | no | reduced design does not estimate `Δ_R` |
| `qwen3-4b` | second | **L1** | `D(A←B)` | **yes** | — (carries `POSITION_CONFOUNDED`) |
| `qwen3-4b` | second | L1 / L2 / L3 | `D(B←A)` / `Λ` / — | no | as above |
| `e4b` | first | **L1** | `D(A←B)` | **yes** | — |
| `e4b` | first | L1 | `D(B←A)` | no | interval not above 0 |
| `e4b` | first | L2 / L3 | `Λ` / — | no | as above |
| `e4b` | second | **L1** | `D(B←A)` | **yes** | — (carries `POSITION_CONFOUNDED`) |
| `e4b` | second | L1 | `D(A←B)` | no | interval not above 0 |
| `e4b` | second | L2 / L3 | `Λ` / — | no | as above |

**L3a–L3e are unreachable on both replications**, not withheld for lack of
signal: the reduced design does not estimate `Δ_R` or `δ_difficulty`.
**L5 is permanently withheld** by design, and `assert_no_l5_emitter` verifies
no code path can emit it.

**Every precision precondition is met** on both replications. No estimand
carries `INSUFFICIENT_PRECISION`. Identification statuses on every statement:
`COMPANION_CLASS_NOT_MATCHED`, `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`,
`EXCESS_NOT_IDENTIFIED`, plus `POSITION_CONFOUNDED` in `outcome_second`.

### 8.2 The L4 defect: what it does, and its exact scope

**What the bug is.** `analysis.claims.emit_l4` compares the **set of claim
levels** reached in each configuration. `run/analysis_run.py` builds that
input as `[s["claim_level"] for s in statements if emitted]`, discarding the
member identity before the emitter can see it.

**What the registered rule is.** §3.2 licenses L1 on *"the named
D(c ← g)"*, and §28.1 pairs *Replication* — "the same classification in every
registered configuration" — with *Configuration dependence* — "**the
quantity** is configuration-dependent; the table is reported and no pooled
scalar is quoted." Both rows are about a **named quantity**. The gate is per
member.

**Which statements are invalidated.**

| Model | Per-member classification | Emitted L4 | Registered per-member gate | Verdict |
|---|---|---|---|---|
| `qwen3-4b` | `D(A←B)`: L1 in **both**; `D(B←A)`: L1 in neither; `Λ`: neither | `true` | **licensed** | **valid** — emitted and registered readings agree |
| `gemma-3n-e4b-it` | `D(A←B)`: L1 in first only; `D(B←A)`: L1 in second only — **both flip** | `true` | **not licensed** | **INVALIDATED** |

So exactly **one** emitted statement in the study is invalidated:
`gemma-3n-e4b-it`'s `claims.L4`. Its registered replacement reading is
*Configuration dependence (§28.1)*: the table is reported and no pooled
scalar is quoted.

**What is unaffected.** `emit_l4` reads already-emitted statements and writes
one dictionary. It does not enter any estimate, standard error, bootstrap
draw, marginal or simultaneous interval, Šidák constant, precision check, F6
vacuity gate, masking decision, or any L1/L2/L3 licensing decision.
**Every row of the 44-row table in §8.1 stands**, on both replications, and
so does `qwen3-4b`'s L4.

**Why it is not repaired.** `run_unmasked_analysis` refuses an unmasked
analysis under an `analysis_code_hash` differing from the masked seal, and
§20 forbids regenerating a mask once semantic identities are known. Editing
`emit_l4` would either strand both replications — their unmasked analyses
could never be recomputed — or require a forbidden re-mask. The commitment
device bound the author of the defect. Correction belongs to v4r5.

### 8.3 What can still be concluded manually

From the unaffected registered quantities alone:

1. **`D(A←B)` on `qwen3-4b` replicates across configurations.** L1 emitted
   for the same named member in both, with simultaneous intervals
   [+0.350, +0.434] and [+0.284, +0.375]. This is a *per-member* replication
   statement and does not depend on `emit_l4`.
2. **`gemma-3n-e4b-it` is configuration-dependent.** No named member reaches
   the same level in both configurations. Under §28.1 the table is reported
   and no pooled scalar is quoted — which is exactly what §3 above does.
3. **No L2 anywhere, despite `Λ` excluding zero in all four
   model × configuration cells.** L2's gate is L1 for *both* `D(B←A)` and
   `D(A←B)`, and no configuration on either model has both. Directional
   asymmetry is **not** licensed by this study — which is the ladder working
   as designed: an asymmetry between two losses means little when only one of
   them is established as a loss.
4. **Non-significance is never absence.** `D(B←A)` = −0.0120
   [−0.0450, +0.0209] on `qwen3-4b` in `outcome_second`, and +0.0062
   [−0.0182, +0.0306] on `e4b` in `outcome_first`, are unresolved
   directions, not evidence of no effect.

---

## 9. Remaining unresolved questions

### 9.1 Answerable from existing data (no new generation)

| Question | Where the data are |
|---|---|
| Distribution of the A-overshoot failure by topic area and by draw | confirmatory `scored.jsonl`, `statistic` field |
| Whether B's vacuous passes on `qwen3-4b` concentrate in particular topics | `scored.jsonl` `vacuous_pass`, already summarised in `04` |
| Per-block variance decomposition of the directional effects | `resolved.jsonl`, all 384 blocks |
| Whether e2b's `RF11` ceiling generalises to its other budget families at Gate 4 | e2b Gate-4 `scored.jsonl`, 4,512 rows, 46 cells — **only calibration material, never an effect** |
| The graded (F5) recodings' sensitivity to the 0.99 threshold | `graded` field on every score |
| Sharper rejection-reason attribution per family per model | `02_admission_landscape.json`, complete |

### 9.2 Requiring a new experiment (v4r5)

| Question | Why existing data cannot answer it |
|---|---|
| Any spectrum-dependent quantity (`Δ_R`, `Δ_j`, `δ_difficulty`, `Ξ`) | NOT_IDENTIFIED on both survivors; the one full-design replication never generated confirmatory data |
| Is the cross-model difference model identity or operating point? | No composed cell exists at any other (n, m) — §7.1 |
| Does the first-stated constraint capture the lexical register? | Needs an order × form factorial; §4 is descriptive |
| Is `Δ_class` small on `qwen3-4b` because A is generic, or because `CX1` is A's twin? | Needs ≥2 class companions of different form, matched on ι |
| Would a raw-compliance caliper at admission have saved the terminated replications? | Needs re-selection and re-generation |
| Does a two-family spectrum identify anything useful? | `qwen3-4b` had two valid triples; §13.4 requires three. Answering means changing the registered rule, which is a v4r5 decision |
| L4's per-member gate | Cannot be recomputed inside v4r4 (§8.2) |
| Model dependence as an estimand | n = 2 survivors; no pooling estimand is registered |

---

## 10. Source manifest

Complete machine-readable manifest with SHA-256, record hash, signature,
producing stage and registration status for **173 items**:
`reports/dci1v4r4/followup_diagnostics/00_source_manifest.json`.

### 10.1 Diagnostic artifacts produced by this task (all POST-HOC)

| File | Covers | Produced by |
|---|---|---|
| `00_source_manifest.json` | §10 | `_manifest.py` |
| `01_final_state.json` | §1 | `_state.py` |
| `02_admission_landscape.json` | §6 | `_admission.py` |
| `03_gate4_anatomy.json` | §5 | `_gate4.py` |
| `04_confirmatory_raw.json` | §2.3, §3.1, §4.2 | `_confirmatory.py` |
| `05_length_strategy.json` | §4 | `_length.py` |
| `06_effects_and_order.json` | §2, §3, §7 | `_effects.py` |
| `07_operating_points.json` | §7 | `_operating.py` |
| `08_claim_ladder_audit.json` | §8 | `_ladder.py` |
| `09_coverage_vs_calibration.json` | §6.3 | `_coverage.py` |
| `10_response_samples.json` | §4.5 | `_samples.py` |

`02`, `06` and `08` call the **registered** functions
(`stages.selection`, `analysis.estimators`, `run.analysis_run.observation_table`)
on signed inputs, so their verdicts are the study's own rather than a
reimplementation.

### 10.2 Registered sources read

- **Signed stage records**, all four models:
  `evidence/dci1v4r4/<model>/<STAGE>/records/*.json` — `QUALIFIED`,
  `GATE_0_APPARATUS`, `REGIME_SCREEN`, `GATE_1_MEASUREMENT`, `GATE_2_REGIME`,
  `GATE_3_REFERENCES`, and for survivors `GATE_4_COMPOSED_HEADROOM`,
  `GATE_5_FREEZE`, `CONFIRMATORY_GENERATION`, `MASKED_ANALYSIS`, `UNMASKING`,
  `UNMASKED_ANALYSIS`. Each carries `record_hash` and `signature`.
- **Signed terminal reports**: `evidence/dci1v4r4/<model>/terminal_report.json`
  for `gemma-3n-e2b-it`, `qwen3-4b-instruct-2507`.
- **Superseded records** (read, unaltered):
  `evidence/dci1v4r4/<model>/superseded/7eb19472dfc4/GATE_3_REFERENCES/`.
- **Generation rows**: `rows.jsonl`, `scored.jsonl`, `resolved.jsonl` under
  each stage's `backend_runs/` — 155,712 scored rows total; 24,576 confirmatory
  rows per survivor.
- **Durable mirrors**: `durable_root/dci1v4r4/…`, byte-identical to the above.

### 10.3 Pre-registered diagnostics read

`reports/dci1v4r4/`: `final_results.json`, `prefreeze_audit.json`,
`post_freeze_delta.json`, `evidence_manifest.json`, `durability.json`,
`backend_provenance.json`, `EXECUTION_REPORT.md`.

### 10.4 Source and preregistration inspected

`src/dci1v4r4/`: `stages/selection.py`, `stages/gates.py`, `stages/freeze.py`,
`stages/confirmatory.py`, `analysis/estimators.py`, `analysis/observations.py`,
`analysis/claims.py`, `analysis/masking.py`, `analysis/bootstrap.py`,
`analysis/spectrum.py`, `analysis/run.py`, `run/analysis_run.py`,
`run/confirmatory_run.py`, `run/freeze_run.py`, `run/gates_run.py`,
`protocol/constants.py`, `protocol/wordings.py`, `design/cells.py`;
plus `tools/v4r4_final_report.py`.

`user-notes/`: `DCI1_preregistration_v4r1.md` (§15 tiers),
`DCI1_preregistration_v4r2.md` (§3.2 ladder table),
`DCI1_preregistration_v4r3.md` (§3.2, §28.1, §28.2, §18.1),
`DCI1_preregistration_v4r4.md`; plus `CHANGES_SCIENTIFIC.md` and
`RESEARCH_STATE.md`.

### 10.5 Provenance of every number in this report

| Section | Status |
|---|---|
| §1 lifecycle, hashes, completeness | REGISTERED |
| §2.1 CL identity, ι, solo, chance | REGISTERED (Gate 2 / Gate 3) |
| §2.2 class-control estimands | REGISTERED (UNMASKED_ANALYSIS) |
| §2.3 raw rates | POST-HOC recomputation; reproduces §2.2 to <1e-9 |
| §2.5 `D(CL←B)` | POST-HOC, NOT_REGISTERED |
| §3.1 cell table | POST-HOC recomputation from signed rows |
| §3.2 directional estimands | REGISTERED |
| §3.3 interpretation | derived from the above; no new quantity |
| §4 all | POST-HOC DESCRIPTIVE / MECHANISTIC |
| §5 rates, band, failures | REGISTERED (Gate-4 records and terminal reports) |
| §5.2 verifier statistics and word counts | POST-HOC, from Gate-4 scored rows |
| §6 admission verdicts | computed by REGISTERED selection functions on signed input |
| §6.3 attrition, ι drift | POST-HOC comparison of two REGISTERED stages |
| §7 operating points, B curves | REGISTERED |
| §8.1 ladder table | REGISTERED |
| §8.2 per-member L4 re-reading | POST-HOC, read-only; frozen artifact untouched |
