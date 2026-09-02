# DCI-1 v8 — the confirmatory design (frozen per model; Approach A)

**Status (2026-09-02).** Design note of record for the confirmatory layer
`dci1/src/dci1v8dev/confirm/`. It continues the v8 pilot
(`V8_PILOT.md`, `V8_FRAME_CONDITIONING.md`) past the point the pilot could
not go: a signed freeze per model and, after it, the protected composed
cells `B+A`, `A+B`, `B+R`, `R+B` and the frame-specific estimates. This
document is bound by hash into the confirmatory manifest and is not edited
after registration; results live in `dci1/reports/dci1v8dev/confirmatory/`.

## 1. What is estimated, and where the boundary is

The scientific question is the study's: within a fixed reasonable wording
frame f, does A cost B more than companions of comparable difficulty do?
The primary estimand is **Δ_R(f)** — §11.3's matched-reference contrast,
`mean_j P(B | B+R_j) − P(B | B+A)` inside each block, cancelled form — per
entering LOCAL frame and per registered configuration, at the frozen
n\*(f), m\*(f) and core triple; and **δ_difficulty(f)** with the §11.8
slope per entering SPECTRUM frame. Every threshold, estimator, interval
construction and reading is v7's registered code, called per frame
(`dci1v7.analysis.{observations,estimators,bootstrap,spectrum,boundary,claims}`,
hashed into the manifest and the freeze).

**The development / protected boundary.** Stages 1–4 (`CONFIRM_REGISTERED`,
`LOCAL_TOPUP`, `MEMBERSHIP`, `FROZEN`) read solo, chance and
counterfactual-chance rows only; the pilot's closed §13.11 schema is
unchanged and the pre-freeze half of the package imports no composed
observation module (`tests_v8dev/test_schema_leakage.py`). A composed cell
is rendered only under `CONFIRMATORY_GENERATION`, whose runner verifies
the signed freeze before rendering one; `FROZEN` is write-once and every
earlier stage is refused after it exists; `CONFIRMATORY_ANALYSIS` and
`FINAL_REPORT` assert their inputs against the freeze hash. Nothing after
the freeze can move a threshold, an operating point, a reference or a
frame.

## 2. The frame-preserving block

v7's block, with two changes (`confirm/design.py`): every stated line of a
block is rendered under the block's frame (v7's §8.4 gave the two
constituents of a composed cell different wording indices; under Approach
A that would put one row in two conditions), and two linear arms are new.

| arm | cells | what |
|---|---:|---|
| base | 5 | unconstrained; A solo; B solo; A+B; B+A |
| core | 21 | R1..R3 solo; every remaining unordered pair over {A,B,R1,R2,R3}, both orders (Δ_R, Ξ, Δ_j, Δ^A, R̄ quantities, Ord_R̄) |
| backup | 6 | R4, R5 solo; B+R4, R4+B, B+R5, R5+B — the two frozen §13.15 backups, for the reference-sensitivity contrast only |
| spectrum | 3k | S_j solo; B+S_j, S_j+B for the frame's k ≤ 12 selected spectrum points (`design.MAX_SPECTRUM_POINTS`) (a point that is a core/backup rung is aliased, not generated twice) |

A LOCAL frame runs base+core+backup (32 cells); a SPECTRUM frame runs
base+spectrum; a frame in both runs all four (≤ 56). A block is one
confirmatory topic under one frame, `block_index = 4·position + frame`,
so the pilot's invariant `frame = block_index mod 4` holds on every row.
Order and wording stay orthogonal: the frame is fixed within a block and
both orders of every pair run in every block. Δ_R reads four composed
cells per configuration; R4/R5 and S_j never enter Δ_R, R̄, Ξ or the fit
(`estimators.reference_slots` filters on exact `CORE_SLOTS` membership).

## 3. Pre-freeze identification work, and what each rule reads

**3a. The frame-aware LOCAL top-up (`LOCAL_TOPUP`).** The audit of
2026-09-01 measured that the pilot's screen and second pass forward rungs
by a difficulty pooled over the four frames while every later step is
frame-specific, and that a rung's iota spreads across frames by 1.7–2.7×
the 0.10 caliper — so a rung inside frame f's caliper can be left
unmeasured because its pooled coordinate sits elsewhere, and several
frames end exactly one family short of §13.15's five. The rule, stated
before any run and applied symmetrically to every model and frame: with
`need(f) = max(0, 5 − |LOCAL-valid families on f|)`, the candidates are the
Tier-1/2 rungs the first-pass screen measured under f whose frame-f screen
iota lies inside iota_A(f) ± 0.10, from families not LOCAL-valid on f and
not forwarded to calibration; the top-up measures every candidate on f's
own calibration topics at M_cal iff `need(f) ≥ 1` and the candidate
families ≥ `need(f)`. The frame's stored load-0 and B-solo answers are
re-scored for the new instances (scoring is a pure function of stored
text; the verifier hash is asserted unchanged), the §13.11 producer forms
the rows, and Gate 3 is re-verdicted for **every** supported frame by the
pilot's own kernel under its recorded seed — a frame without a top-up must
reproduce the pilot's verdict exactly, and that equality is asserted on the
record. Dry-run on the four pilot roots the rule fires on `qwen3-4b` f2
(XC3), `gemma-3n-e2b-it` f0 (MK1), `gemma-3n-e4b-it` f0 (XC1, XC3) and f1
(MK3): six rungs (2,688 generations on the signed records; an earlier note said seven). It adds no family; §13's full V(R)
admits a measured rung or does not.

**3b. Operating-point stability (`MEMBERSHIP`).** §12.3's n\*(f) is chosen
among near-tied rungs by a point estimate whose standard error is of the
order of the gaps between them. The rule is unchanged; what is recorded,
per entering frame, is the distribution of the selected severity and of
iota_A(f) under a topic-level bootstrap that re-runs §12.3 on each
resample (`confirm/stability.py`). Δ_R(f) is stated as **conditional on
the frozen n\*(f), m\*(f)** with `p_selected_reproduced` beside it. No
threshold is attached.

**3c. Reference-class uncertainty.** The core triple is one of 9–35
admissible triples that are statistically indistinguishable at the
caliper. The backup arm generates R4/R5 beside B, and the pre-registered
**reference-sensitivity family** re-forms Δ_R(f) over every admissible
triple of the five frozen families (§13.8's own structural rules: three
feature groups, ≥ 2 Tier-1, ≥ 2 declared roles), reported with its own
simultaneous interval. It licenses no claim; it bounds how much the frozen
triple mattered.

**3d. Membership.** A frame enters LOCAL iff it is `LOCAL_SUPPORTED` on its
own (top-up-augmented) table and its model has ≥ 2 such frames
(`rules.LOCAL_ELIGIBILITY_MIN_FRAMES`); every supported frame of an
eligible model enters. A frame enters SPECTRUM iff Gate 2 supported it and
the v8 coverage gate identified its selected set, whatever the model's
LOCAL standing. The study-level lock
(`tools/v8_membership_lock.py` → `reports/dci1v8dev/confirmatory_membership.json`)
is written from every model's signed `MEMBERSHIP` record before any
composed row and bound by hash into every freeze.

## 4. Allocation and multiplicity (prospective; `confirm/precision.py`)

**The family.** Per (model, frame, configuration): F1 as registered, six
members. Per (model, configuration): the **joint family** of every F1
member of every entering frame, whose simultaneous critical value is the
studentised maximum-modulus over a *topic*-level bootstrap — one draw of
the confirmatory topics shared by every frame's members, because the same
topic underlies each frame's block. The decision interval of every primary
claim is the joint one; the per-frame F1 interval is reported beside it. A
model-level LOCAL verdict is the **conjunction** over entering frames
(intersection–union; no further adjustment); `FRAME_HETEROGENEOUS` is a
verdict, never a support claim, and no "at least one frame" claim exists.

**The precision rule.** Blocks per frame, from {288, 384}: the smallest
whose projected simultaneous half-width for Δ_R at the joint Šidák
constant (k = 6 × LOCAL frames entering) is ≤ 0.05 under §16.1's variance
form at **both** `REGISTERED_ALTERNATE` (φ 0.37, ρ 0.5, p(1−p) 0.215) and
`COMPOSED_AT_HALF` (φ 0.27, ρ 0.5, p(1−p) 0.25 — the composed cell at 0.5,
which the hypothesis predicts and the pre-freeze anchor at B's solo rate
understates). The two bounds (`WORST_CASE`, ρ 0; `ALTERNATE_AT_HALF`) are
reported and gate nothing. At two entering frames (k = 12): 288 gives
0.0538 / 0.0527 and fails; **384 gives 0.0466 / 0.0456 and is selected**.
384 is every confirmatory topic under every entering frame — the ceiling —
and it makes the joint family fully paired across frames. At three frames
(k = 18) 384 still meets the rule (0.0487 / 0.0476); at four it sits on the
line and §17.3's non-terminal `INSUFFICIENT_PRECISION` decides on the
realised interval. Draws M = 8; the cap is the pilot's selected cap.

## 5. What the freeze binds

Per model (`FROZEN`): the manifest hash; the pilot record hashes; the
top-up and membership record hashes; the membership lock by hash and the
assertion that its entry equals this model's record; blocks per frame,
draws, cap; per entering frame the arms, slot map, spectrum slots and
aliases, n\*(f), m\*(f), iota_A(f), core, backups, stability block and
reference-sensitivity plan; the estimands; the family declarations and the
multiplicity rule; the bootstrap algorithm and 10,000 resamples; the
precision preconditions and claim thresholds (unchanged); the analysis
code by hash; the deviations (§6). A model with no entering frame is
terminal `NOT_ELIGIBLE` at the freeze.

## 6. Deviations from v7's registered post-freeze sequence

* No `MASKED_ANALYSIS` / `UNMASKING`: v7 §20 protects analyst decisions
  taken between generation and report; this layer has no such decision
  point — the analysis is frozen code, run once, unattended.
* The near-form and class arms are not run (the pilot selected neither);
  `Delta_near`, `Delta_broad` and L3c's near-form requirement are recorded
  as unavailable, and L3c is reported as `NEAR_FORM_UNAVAILABLE` rather
  than emitted.
* The backup arm is generated (§3c); spectrum points are the v8 selection
  rather than six core-family companions (`V8_CANDIDATE.md` §5).

## 7. Stopping rule

The design is not modified after a composed outcome exists. Inconvenient,
underpowered, heterogeneous or v7-contrary results are reported as what the
frozen readings say; `INSUFFICIENT_PRECISION`, `FRAME_HETEROGENEOUS`,
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and the boundary statuses are outcomes,
not reasons to re-run.
