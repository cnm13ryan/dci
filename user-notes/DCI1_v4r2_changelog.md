# DCI-1 preregistration changelog

**Current version:** 4.0 revision 2, 19 August 2026, for registration, not
frozen, no confirmatory data.

---

## 4.0 revision 2 (19 August 2026)

**Trigger.** Recovery of the source construct memo
`dci-construct-pass2.md` (14 August 2026) and completion of the
non-confirmatory B+R pilot `reports/br_pilot_v4/`.

**Supersedes.** 4.0 revision 1 in full. Revision 1 was never registered,
never frozen and produced no data, so its replacement is prospective.

**Does not touch.** DCI-1 v3, its amendments A1 to A3.2, its signed
evidence trees, or its results report. No v3 quantity is reinterpreted and
no v3 record is edited.

### Changed

1. **The discriminating question.** Revision 1 inferred a crossed design
   over outcome constraints. The memo §G row 1 specifies a companion swap
   on the focal outcome: generate B+R and B+S without the target A, beside
   B-alone and B-with-A, and read D(B←A) − D(B←R) against 0.25 and 0.10.
   The inferred design is withdrawn.
2. **The primitive.** Target failure $F_A$ is replaced by the full
   per-constraint compliance vector $X$, with the graded vector $G$ and
   per-constraint degeneracy flags, recorded for every constraint present
   in every prompt.
3. **The primary estimands.** $\tau$, $\tau_S$ and $\iota$ are replaced by
   $D(B \leftarrow A)$, $D(A \leftarrow B)$,
   $\Lambda = D(B \leftarrow A) - D(A \leftarrow B)$ and
   $\Delta_R = D(B \leftarrow A) - \frac{1}{3}\sum_j D(B \leftarrow R_j)$,
   each defined within one (model, order) configuration.
4. **The reference's role and matching target.** The reference stops being
   a prerequisite and becomes a control arm, and it is matched to $A$ on
   solo compliance within 0.10 with a Newcombe-interval condition, rather
   than to $B$ on solo failure. The realised gap is re-measured on the
   confirmatory solo cells and reported beside every excess-damage
   statement. Failure to admit three references sets
   `EXCESS_NOT_IDENTIFIED` and routes the model to a reduced design
   instead of terminating it.
5. **Configuration handling.** Order stops being pooled and becomes a
   stratification variable. Every primary estimand is order-conditional
   and each (model, order) configuration is a separate replication with
   its own families. No pooled scalar carries a claim.
6. **The design.** Eleven surrogate-bearing arms are replaced by the
   complete pairwise composition matrix over five constraints: 5 solo
   cells and 10 unordered pairs in 2 orders, 25 cells per block, each
   composed generation scored on both of its constraints.
7. **The allocation.** 384 blocks at $M = 8$, sized so that a projected
   detectable effect of 0.064 covered the range of the v3 diagnostics, is
   replaced by 384 blocks with order as a within-block factor at $M = 4$,
   38,400 generations per model, sized against absolute precision
   preconditions using a variance model fitted to the pilot interval
   widths and checked under two correlation assumptions.
8. **Thresholds.** The memo's 0.25 and 0.10 for $\Delta_R$ are registered
   on their 14 August provenance. The smallest effect of interest 0.10 is
   retained for $D$ and $\Lambda$. Precision preconditions are 0.05 for
   $D$ and $\Delta_R$, 0.08 for $\Lambda$ and 0.06 for $\Delta_j$, met
   under both fitted variance settings. The $D$ and $\Delta_R$
   preconditions are half the smallest effect of interest; the $\Lambda$
   and $\Delta_j$ preconditions are set from what the design can achieve
   for quantities with more terms.
9. **The claim ladder.** Five levels: delivery loss exists, directional
   asymmetry, excess damage relative to matched companions with its two
   thresholds, replication across configurations, and a permanently
   withheld level covering semantic identity-specificity, universal pair
   properties, arbitration, mechanism and generalisation.
10. **Measurement scope.** The Gate 1 programme extends from the single
    exact-count instrument to every registered outcome verifier, because
    the family verifiers are now primary instruments.
11. **Vacuity.** A non-vacuity predicate is registered per constraint,
    vacuity rates are reported per cell, and vacuous passes enter a
    partial-identification recomputation instead of a filter.
12. **Response length.** Registered as a mediator, reported and never
    conditioned on, replacing its revision 1 role as a comparability
    quantity with an interpretation block.
13. **Masking.** The permuted dimension becomes the companion label within
    (outcome, order, block). The consequent inability to compute
    joint-state quantities in the masked phase is declared.
14. **Terminal statuses.** Reference-pool and uptake failures cease to be
    terminal and become per-claim identification statuses.

### Retained unchanged

Deterministic verifiers with verdicts stored at generation time; the
canonical verifier hash, its freeze, and fail-closed binding at every
downstream entry point; the autorater as a validation-only proxy under
serialised deterministic execution, never writing a behavioural score;
author-performed labels never described as independent validation; the
sealed reserved set and its one-shot rule; block-level clustering with a
bootstrap over blocks; cell means over all cached draws; declared
multiplicity families with simultaneous intervals; masked analysis with
its executable checks; the guarded emitter for absence and equivalence
statements; artifact states, closed artifact-type vocabulary and
append-only transition logs; the exclusion of deprecated and foreign
sources from registered evidence; contamination controls and sequestered
topics; and the codebook and environment checks.

---

## 4.0 revision 1 (19 August 2026, superseded)

Written from the v3 preregistration, amendments, implementation and
results before the construct memo was available. Introduced draw-averaged
cell means, a dense integer severity ladder, a precision precondition on
equivalence, a five-tier claim ladder, and the prospective registration of
the v3 autorater amendments. Introduced a surrogate outcome constraint and
the estimand $\iota$, both now withdrawn. Never registered, never frozen,
no data.

---

## 3.0 (registered 16 August 2026, amended 17 August, results reported 19 August, closed)

Executed. Four replications: two complete unmasked analyses and two
terminal `REFERENCE_POOL_MISMATCH` non-identifications. Four of four
primary estimands direction-unresolved; one licensed equivalence;
exchangeability violated in both identified replications; Gate 1 basis
`autorater_calibration_approved` with `HUMAN_VALIDATION_UNAVAILABLE`.
Closed and preserved.

---

## Disposition of historical DCI quantities

| Quantity | Disposition | Reason |
|---|---|---|
| $\tau$, target damage $A{+}B$ versus $A{+}R$ | **Demoted** to a gated diagnostic, re-expressed on the compliance scale as $\Delta^A$ | Three sign reversals in the legacy corpus; structurally degenerate where the target is at ceiling; and it is the near-zero side of an asymmetric phenomenon, reproducing the v3 record at $-0.0095$ and $+0.0651$ against a B-side companion swap of $+0.34$ and $+0.38$ |
| Target failure $F_A$ as the sole primitive | **Replaced** by the compliance vector with graded scores | A checkpoint exists where joint compliance moves about 70 points while $\tau$ is 0.000 in all four cells |
| Reciprocal delivery loss $D(c \leftarrow g)$ | **Adopted** as primary | Needs no reference, makes no commensurability assumption, survives target ceiling |
| Asymmetry $\Lambda$ | **Adopted** as primary | The one-sided sacrifice is the directional content of the phenomenon |
| Companion swap $\Delta_R$ | **Adopted** as primary | It is the memo's discriminating quantity |
| Within-arm joint-state redistribution | **Retained** as a registered secondary, used within cell | The only representation in which low joint success and one-sided abandonment are visible |
| $\Delta_{\text{joint}}$ across arms | **Abandoned** | It cannot separate "harder" from "conflicting" without a difficulty-matched pool |
| $\Gamma$, the three-place interaction | **Out of scope** at load two; retained as the memo's secondary estimand of record for a future load-three design | This architecture carries no third constraint |
| Reference exchangeability as a claim gate | **Replaced** by admission on companion solo compliance plus a reported heterogeneity qualifier | Exchangeability was a post-hoc property of a set selected on the wrong dimension |
| Composed-uptake matching | **Abandoned** | Composed compliance is now the outcome |
| The surrogate outcome constraint and $\iota$ | **Abandoned** | Introduced to reconstruct a recommendation that has since been recovered and is different |
| The matched-reference design | **Retained** as a control arm, **removed** as a prerequisite | It is needed for $\tau$, not for the primary estimand |
| Arbitration as a mechanism account | **Refuted** in the legacy corpus and not revisited | A designed priority intervention produced a clean null with three wrong-signed point estimates |
