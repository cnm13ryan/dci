# Scientific claim audit

Each major current claim receives one status:

`SUPPORTED` · `SUPPORTED_WITH_NARROWER_WORDING` · `UNDERPOWERED` ·
`NOT_IDENTIFIED` · `INVALIDATED_BY_PIPELINE_BUG` · `REQUIRES_RERUN`

Statuses are assigned against the repaired pipeline and against identification,
which is computed separately from estimation. A number that survived the
pipeline repairs unchanged can still be `NOT_IDENTIFIED`: the two questions are
independent, and conflating them is the failure mode this audit exists to catch.

**Headline finding of the audit.** No published estimate was wrong. Almost every
pipeline defect was latent. What the audit changes is what the estimates are
*evidence for* — and there the changes are large, because identification was
never checked and joint compliance was never reported beside target damage.

---

## 1. Natural-reasoning claims (PR #15)

### 1.1 "The bracket conflict disappears under natural reasoning" — `NOT_IDENTIFIED`

τ = +0.000, CI [+0.000, +0.000]. The estimate is arithmetically correct and
survives every pipeline repair. It is not evidence that the conflict resolved.

Three independent reasons, each sufficient:

**Target ceiling.** Target failure is 0.000 in *both* arms. τ = 0 is produced by
construction, not by an absence of interference. The zero-width interval is a
zero-event cluster bootstrap, not certainty.

**Focal non-uptake.** The focal instruction was satisfied in **7.5%** of focal
rows. The reference was satisfied in **90.0%**. A treatment delivered one time
in thirteen is not a treatment whose null is informative.

**Joint compliance contradicts the wording.** This is the decisive one:

| natural reasoning, bracket | P(both) | P(target only) | P(focal only) | P(neither) |
|---|---|---|---|---|
| focal arm (B, relational) | **0.075** | 0.925 | 0.000 | 0.000 |
| reference arm (C_L3, local) | **0.900** | 0.100 | 0.000 | 0.000 |
| **ρ = p_B − p_R** | **−0.825** | **+0.825** | 0.000 | 0.000 |

Swapping the reference for the focal instruction moves 82.5 points of
probability mass out of *both satisfied* and into *target only*. The target was
**protected**, not composed with. Nothing "disappeared": the conflict was
resolved by abandoning the focal instruction almost entirely.

**Narrower wording that would be supported:** *under natural reasoning the
bracket configuration shows no additional target failure, and joint compliance
in the focal arm is 7.5% against 90% in the reference arm.* That sentence is
true and says something quite different from the current headline.

### 1.2 "The semicolon conflict does not disappear" — `SUPPORTED_WITH_NARROWER_WORDING`

τ = +0.400, CI [+0.225, +0.551]. Target failure 0.500 focal vs 0.100 reference,
so there is genuine headroom and the estimate is not degenerate. Replicates are
independent (0/80 identical), no cap binds (0% cap-hit), and the verifier repair
changes 0 of 5,440 rows.

Two qualifications:

* **Focal uptake is 10%.** Under the identification layer this cell is
  `FOCAL_NONUPTAKE`. τ here is the effect of *presenting* the focal instruction,
  not of the model satisfying it — a defensible estimand, but not the one the
  prose implies, and one in which the "matched" reference is not matched in
  realised difficulty.
* **The contrast with the bracket claim is weaker than it reads.** In
  joint-compliance terms both backgrounds collapse joint success by roughly the
  same amount (ρ_both = −0.825 bracket, −0.775 semicolon). What differs is
  *where the mass goes*: bracket → target-only, semicolon → split between
  target-only (0.450) and neither (0.450).

**Supported wording:** *the semicolon configuration produces additional target
failure that natural reasoning does not remove; the bracket configuration does
not. Both configurations reduce joint compliance by a similar margin.*

### 1.3 "The bracket/semicolon difference is a reasoning × background interaction" — `UNDERPOWERED`

The published evidence is two separate intervals, one excluding zero and one
not. The framework is explicit that an interaction may not be inferred that way.
Γ = Δ_R − Δ_0 is estimable from the existing paired data but is not currently
computed, and no paired-resampling interval for it is published.

**Requires:** Γ estimated directly with paired task resampling before any
interaction is claimed. The data to do it already exists — this is an analysis
gap, not a data gap.

### 1.4 "Any thinking at all fixes the bracket conflict" — `INVALIDATED_BY_PIPELINE_BUG`

Withdrawn. Two defects: no positive budget below 256 was ever run, and 256 is
itself cap-bound at 86% (bracket) and 94% (semicolon), so it is a truncation
condition rather than a small reasoning budget. The semicolon peak at 512
(+0.625, the highest point on the chart) is cap-bound at 60%.

Replaced by *"Gone by the smallest budget tested"*, with cap-bound points drawn
hollow. `dci-natural-reasoning-headline@8cac2f0`

### 1.5 Long-trace robustness table — `SUPPORTED_WITH_NARROWER_WORDING`

Recomputed after the share/pairing repair. Before → after:

| exclusion | rows_kept | n_tasks | semicolon τ | bracket τ |
|---|---|---|---|---|
| all rows | 80 → 80 | 20 → 20 | +0.400 → +0.400 | +0.000 → +0.000 |
| drop longest 1 | 79 → 78 (per arm) | 20 → 20 | +0.400 → +0.425 | +0.000 → +0.000 |
| drop longest 5% | 78 → **76** | 20 → 20 | +0.400 → +0.400 | +0.000 → +0.000 |
| drop longest 10% | 76 → **72** | 20 → **19 / 18** | +0.450 → +0.472 | +0.000 → +0.000 |

**Reason for change:** the labelled share is now the share removed (5% of 80 is
4, not 2), and it is removed per arm rather than from the pooled cell.

**Scientific consequence:** the conclusion is unchanged — the semicolon effect
does not rest on a few long traces — and it is now tested at the advertised
depth. The corrected table also exposes task loss at the deepest exclusion
(n_tasks 20 → 19 and 18) that the pooled drop concealed, so the deepest row is
no longer comparing the same task set as the others.

### 1.6 "Natural reasoning is uncapped and closed naturally" — `SUPPORTED`

0 ceiling hits in 160 rows, all traces closed naturally, median 511 reasoning
tokens against a derived ceiling of 39,550, max 5,888. Guarded and re-verified.

---

## 2. Cross-model transport claims (PR #16)

### 2.1 "Five-checkpoint cross-model DCI transport" — `NOT_IDENTIFIED` (all 8 cells)

Applying the identification layer to the five main runs:

| model | mode | background | τ | F_focal | F_ref | uptake focal | uptake ref | verdict |
|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | NO_THINKING | bracket | 0.000 | 0.000 | 0.000 | 0.175 | 1.000 | `FOCAL_NONUPTAKE` |
| Qwen3.5-4B | NO_THINKING | semicolon | 0.000 | 0.000 | 0.000 | 0.200 | 0.975 | `FOCAL_NONUPTAKE` |
| Qwen3.5-9B | NO_THINKING | bracket | 0.000 | 0.000 | 0.000 | 0.275 | 1.000 | `FOCAL_NONUPTAKE` |
| Qwen3.5-9B | NO_THINKING | semicolon | −0.150 | 0.100 | 0.250 | 0.275 | 1.000 | `FOCAL_NONUPTAKE` |
| gemma-4-12B-it | NO_THINKING | bracket | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | `TARGET_CEILING` |
| gemma-4-12B-it | NO_THINKING | semicolon | 0.000 | 0.000 | 0.000 | 0.900 | 1.000 | `TARGET_CEILING` |
| gemma-4-E4B-it | NATURAL | bracket | 0.000 | 0.000 | 0.000 | 0.550 | 1.000 | `TARGET_CEILING` |
| gemma-4-E4B-it | NATURAL | semicolon | 0.000 | 0.000 | 0.000 | 0.525 | 1.000 | `TARGET_CEILING` |

**0 of 8 poolable.** The failures split cleanly by family, and the two causes
are scientifically different:

* **Qwen3.5** — the treatment was not delivered. Focal uptake 17.5–27.5%.
* **gemma-4** — the target never fails. The instrument has no headroom.

**Consequence for the PR's framing.** The study currently reports these as
transport results with a caution about backends. They are not weak transport
results; they are non-results, for two different and separately fixable reasons.
Reporting them as "τ ≈ 0 across four checkpoints" invites exactly the reading
the framework forbids: that the instrument transported and found nothing.

### 2.2 "The vLLM TP=2 retry qualified 0/5" — `SUPPORTED`

Unaffected by every repair here. The gate is correct and correctly refused to
run the slice at less than 5/5. Recorded diagnoses stand.

### 2.3 "Qwen3.5-9B semicolon shows τ = −0.150" — `NOT_IDENTIFIED`

The only nominally non-zero cross-model estimate. Focal uptake 27.5%; the CI
spans zero; the sign is negative, meaning the *reference* damaged the target
more than the focal did. Not interpretable as transport of the semicolon effect.

### 2.4 Manifest canonical status — `SUPPORTED` (after repair)

All five runs remain `CANONICAL` under identity checking: 160/160 expected
design cells, no missing, unexpected or duplicated cells, no malformed replicate
groups. `dci-cross-model@0368a13`

### 2.5 "Backend differences are not attributed to models" — `SUPPORTED`

The documents state this consistently and the manifest carries per-row execution
identity. Reinforced by X5's repair: the execution table now reports an
unrecorded ceiling as unrecorded rather than crashing or printing 0.

---

## 3. Cheapest-ROCm claims (PR #17)

### 3.1 Estimands computed over technical failures — `SUPPORTED` (latent defect)

The `fillna("")` path would have converted apparatus failures into target
failures. Audit: **0 technical failures across 47,452 rows** carrying the field;
`raw_final_answer` present and non-empty in all 19,850 rows. No published
estimate was affected. Repaired before it could be. `@ece245a`

### 3.2 Sentence-count outcomes — `SUPPORTED` (latent defect)

The verifier merged sentences when an abbreviation or ellipsis was followed by
an opening quote, bracket or Markdown mark. Recounting every stored generation
under both rules changes **0 of 19,850** rows here and **0 of 5,440** in the
natural-reasoning corpus, with 0 changes in each arm separately. No
arm-differential verifier error is introduced or removed. `@8643526`

### 3.3 "The anti-splice intervention did not pass its manipulation gate" — `SUPPORTED`

Consistent with the framework's own reading. No causal mechanism estimand should
be computed from it, and none is.

---

## 4. Claims requiring rerun

| claim | status | why |
|---|---|---|
| Any gemma-4 DCI estimate | `REQUIRES_RERUN` | `TARGET_CEILING`. Needs a harder target or higher load, chosen on held-out calibration data, as a *calibrated operating-point* study — not as fixed-contract transport. |
| Any Qwen3.5 DCI estimate | `REQUIRES_RERUN` | `FOCAL_NONUPTAKE`. Needs a focal instruction the checkpoint actually follows, or an uptake-conditioned estimand declared in advance. |
| Reasoning × background interaction | `UNDERPOWERED` | Γ computable from existing data; not yet computed with paired resampling. |
| Kimi anything | `REQUIRES_RERUN` | Never generated. `CAPACITY_BLOCKED` / `BACKEND_BLOCKED`. |

---

## 5. What did not change

Stated explicitly, because "we audited it and it held" is a result:

* Semicolon τ = **+0.400** under natural reasoning — unchanged by every repair.
* Bracket τ = **+0.000** — unchanged as an estimate; reclassified as
  `NOT_IDENTIFIED`.
* Every capped-ladder point — unchanged.
* All five cross-model runs remain `CANONICAL`.
* 0 of 25,290 stored answers change sentence count under the repaired verifier.

The pipeline was, numerically, in better shape than the defect list suggests.
The identification and joint-compliance gaps are where the real damage was.
