# DCI-1 v3 → v4: change summary

**Date:** 19 August 2026 · **Status:** prospective, for registration ·
**Companion documents:** `DCI1_preregistration_v4.md` (the registered
protocol), `DCI1_v4_unresolved_decisions.md` (open items).

v3 is preserved unchanged. Its preregistration, amendments A1–A3.2,
implementation, signed records, and results are historical evidence and
are never edited. Every v3 quantity cited below is read from the uploaded
first-wave artifacts: `DCI1_preregistration_v3.md`, `DECISIONS_V3.md`,
`RESULTS_V3.md`, the two unmasked `result.json` files, and the v3 source
modules `constants.py`, `claims.py`, `estimators.py`, `run.py`,
`gate2a.py`, `gate2b.py`, `target.py`, `words.py`.

Evidence class of every "v3 problem" below: **REGISTERED** (read from a
signed v3 stage record), **DIAGNOSTIC** (a v3 registered secondary),
**CAVEAT** (v3 measurement-validity evidence), or **DERIVED** (arithmetic
performed here on v3 recorded quantities, shown in the v4 preregistration
§13).

---

## C1. Construct and estimand: name what τ actually estimates

**v3 problem (REGISTERED).** v3 §2 defines the phenomenon as *directional
constraint interference* and §11 defines τ as the block contrast against
the mean of three references. The v3 report states that what τ estimates
is the average **swap effect against one frozen reference set**, using the
analysis code's own field name `secondary.pooled_swap_effect`
(`run.py:_secondary`), and that the identity-specific reading additionally
requires reference exchangeability and comparable composed uptake
(RESULTS_V3 §4). Both supports failed or were flagged in both identified
replications, so no resolved τ could ever have licensed the
identity-specific claim.

**v4 fix.** Three estimands are declared and named separately: τ (the swap
effect on the target), τ_S (the same swap measured on an independent
surrogate target, the generic-constraint-load component), and ι = τ − τ_S
(the identity-specific component). The construct sentence is written on
the estimand that carries it, and the phenomenon label *directional
constraint interference* attaches to ι alone.

**Rationale.** The gap between the phenomenon name and the estimated
quantity was the single largest interpretive liability of v3. Naming three
estimands removes it by construction rather than by qualification.

---

## C2. B+R / B+S discriminating design: separate identity from load

**v3 problem (REGISTERED + DIAGNOSTIC).** v3's only instrument for
separating identity-specific interference from generic constraint load is
the exchangeability family F2. It failed in both identified replications:
E2B δ₂₃ = −0.154, simultaneous [−0.234, −0.073]; E4B fails by interval
width (`result.json`, `exchangeability_holds: false` in both). E2B's
per-reference contrasts split sign in the same stratum, +0.135
[+0.011, +0.260] against AR2 and −0.130 [−0.254, −0.007] against AR3.
RESULTS_V3 §8 ranks the unexecuted B+R / B+S discriminating experiment as
the first remaining scientific blocker.

**v4 fix.** Each block carries eight composed cells: A+B, A+R₁, A+R₂, A+R₃
and S+B, S+R₁, S+R₂, S+R₃, where S is a second exact-count target
constraint of identical form and a shorter target word. The A-side
contrast is τ, the S-side contrast is τ_S, and ι = τ − τ_S is the
registered identity-specific estimand.

**Rationale.** Exchangeability is a property of the reference set and is
silent about whether B's excess acts through the identity of the target.
A difference-in-differences over a second outcome constraint differences
out both B's generic interferer strength and the reference set's generic
strength, and identifies the pair-specific term under one stated
assumption (v4 §11.4).

---

## C3. Draw-averaged estimator: use all cached draws

**v3 problem (REGISTERED + DIAGNOSTIC).** v3 generated M = 16 cached draws
per cell and used exactly one, selected by a frozen hash
(`constants.py: M_DRAWS = 16`; v3 §4, §12). 93.75% of generated data
entered no primary estimate. The registered E2B target-first estimate
(+0.007) lies below the 5th percentile (+0.030) of its own 1,000-draw
pseudo-selection distribution, whose mean is +0.089 (RESULTS_V3 §2). The
draw lottery has an SD of about 0.036 to 0.039, comparable to the
block-level standard error of 0.039 to 0.042 across the four F1 members of
the two identified models (`result.json`, F1 `standard_error`).

**v4 fix.** The per-cell outcome is the mean of all M registered draws.
The block stays the only resampling unit; the bootstrap is unchanged. The
two presentation-order estimands are replaced by one pooled estimand with
a registered order-interaction gate, which doubles the blocks behind the
primary quantity.

**Rationale (DERIVED, v4 §13).** Decomposing E2B target-first gives
σ²_draw ≈ 0.247 and σ²_block ≈ 0.045 per block. Averaging M = 8 draws over
384 pooled blocks projects a standard error of 0.0141 against 0.0390
realised, a simultaneous half-width of 0.034 against 0.087, and a
smallest detectable effect at 80% power of 0.045 against 0.120. The
estimand is unchanged in expectation, because the per-cell draw mean and
the single draw both estimate the same per-cell failure probability.

---

## C4. Claim fragility: precision precondition on equivalence

**v3 problem (REGISTERED + DERIVED).** The single resolved registered
claim of the whole study is the E2B target-first equivalence, licensed
because the simultaneous interval [−0.080, +0.094] lies inside ±0.10
(`claims.py: licensed_equivalence`). Its half-width is 0.087, so the rule
was satisfied only because the point estimate landed within 0.013 of zero.
Re-centring the same interval on that estimand's across-draw mean of
+0.089 gives [+0.002, +0.176], which the same code emits as a resolved
positive direction and no equivalence. The one resolved claim of v3 turns
on the draw lottery.

**v4 fix.** Equivalence additionally requires a realised simultaneous
half-width at or below SESOI/2 = 0.05. A primary member whose half-width
exceeds 0.05 records `INSUFFICIENT_PRECISION`, withholds equivalence, and
still emits a resolved direction if one exists.

**Rationale.** An equivalence claim is a statement about a narrow
interval. Under v3's rule an interval of half-width 0.099 could license
equivalence with a point estimate at 0.001, which is a statement about the
point estimate rather than about precision.

---

## C5. Reference admission: match on realised composed uptake

**v3 problem (REGISTERED + CAVEAT).** v3 matched references on **solo**
failure rate alone (v3 §18.4; `gate2a.py: admit_families`). The realised
composed uptake gap was large: E4B delivered its added constraint in 43.8%
of focal responses against 7.3%, 4.2% and 9.9% in the three references,
flagging all three §16 manipulation checks; E2B flagged AR3 at 2.1% uptake
against 35.7% (`result.json`, `per_arm[*].uptake`, `uptake_flagged`).
Composed median response length shows the same asymmetry: E2B 173 tokens
under A+B against 189, 202 and 248 under the references, E4B 191 against
224, 232 and 248.5.

**v4 fix.** Gate 2B measures composed uptake for every candidate reference
and for B, on the independent composed-validation topics, and admits a
family only when |u(R_f) − u(B)| ≤ 0.15 on the A side. Composed uptake is
an **admission predicate**, never a ranking criterion; the final three
references are still those with the smallest solo distance. Fewer than
three families passing returns the new terminal status
`COMPOSED_UPTAKE_MISMATCH`. To obtain u(B) without exposing the DCI
contrast, A+B and S+B are generated on the composed-validation topics with
the target verifier structurally never invoked on those rows.

**Rationale.** Solo difficulty measures how hard a constraint is alone.
The comparison the estimand requires is between two constraints that
actually reached the model at comparable rates. v3 preserved the
anti-selection principle by making the composed target rate a predicate
rather than a ranking criterion (v3 §18.5); the uptake predicate uses the
same device, so the selection rule gains no freedom to choose references
that produce a desired focal effect.

---

## C6. Adaptive reference calibration: dense severity ladder

**v3 problem (REGISTERED).** Both Qwen replications terminated at Gate 2A
with `REFERENCE_POOL_MISMATCH`: exactly two family/severity pairs fell
inside the ±0.10 caliper where three were required (RESULTS_V3 §3). The
cause is grid coarseness. Each family carried four severities
(`constants.py: REFERENCE_FAMILIES`), and for these models most families
sit at solo failure ≤ 0.10 at every non-zero severity while the focal rate
is 0.26 to 0.31, so admissible severities fall in the unmeasured gaps,
for example between q = 2 and q = 0 for RF1 to RF3 and RF8 and between
q = 4 and q = 0 for RF5 and RF6.

**v4 fix.** Every family carries the complete integer ladder from 0 to its
registered maximum, 94 severities across the eight families against 32 in
v3. A two-stage registered screen measures the whole ladder cheaply in the
regime pre-screen on the 24 pre-screen topics, then measures only the
shortlisted severities at higher precision at Gate 2A on the 96
solo-calibration topics with M_cal = 4 draws per cell. Selection remains the deterministic v3 rule. No sequential
search and no adaptive stopping is introduced.

**Rationale.** Model-specific non-identification in v3 was caused by
unmeasured severities, not by a missing algorithm. Exhaustive measurement
on a dense ladder removes the cause without adding researcher degrees of
freedom. Raising M_cal from 1 to 4 cuts the standard error of each solo
rate from 0.051 to 0.031, which also addresses the selection noise that a
denser ladder would otherwise amplify.

---

## C7. Measurement: split the three validation questions and assist the count

**v3 problem (CAVEAT).** v3's registered Gate 1 human criterion was never
met. Amendment A2 recorded `HUMAN_VALIDATION_UNAVAILABLE` and substituted
an autorater proxy; the final Gate 1 basis is
`autorater_calibration_approved`. The later 120-label validation by the
study author met the criterion for the verifier-pass class (0/52, Wilson
upper 4.9%) and missed it for the verifier-fail class (4/52 = 7.7%,
Wilson upper 16.1%). All four disagreements are human off-by-one
miscounts at |s0 − n| = 1, each reproduced against the verifier by four
independent recounts (RESULTS_V3 §5).

**v4 fix.** Three questions are registered separately and never
aggregated. (1) Verifier correctness is established mechanically by the
frozen 40-case boundary suite, three-process determinism at 1.000, and a
registered independent reimplementation differential test at 1.000
agreement. (2) Human agreement is measured under a **tool-assisted
counting protocol**: the annotator marks occurrences and the interface
tallies the annotator's own marks, with no automatic detection,
highlighting or counting of the target word, and the fail-class criterion
is evaluated separately on |s0 − n| = 1 items and on larger margins.
(3) Construct validity is probed by a registered detector for
construct-discordant occurrence types (metalinguistic mention, quoted
material, instruction restatement, enumeration of the word), reported per
arm with an arm-differential interval.

**Rationale.** v3's bound conflated the verifier's correctness with
unaided human arithmetic and therefore measured the annotator. The
disagreements are wholly concentrated at the off-by-one boundary, so the
protocol must remove mental tallying while keeping the human judgment of
what counts as an occurrence, which is the construct-relevant part.
Reaching the registered ≤ 0.10 bound from the v3 fail-class position needs
34 further zero-error labels (4/86 gives Wilson upper 0.0996), and ≤ 0.05
would require the fail-class sample to reach about 175 labels with those
four errors standing, above the registered per-class target of 150; the v3
report reaches the same conclusion from the observed unaided error rate.

---

## C8. Near-miss structure enters the registered plan

**v3 problem (SENSITIVITY, unregistered).** Near-miss failures
(|s0 − n*| = 1) are 67% to 85% of all failures in every arm, and the
unregistered tolerant-rule re-analysis flips both E2B signs while
strengthening E4B added-first to +0.123 (RESULTS_V3 §6). The analysis was
performed after unmasking and therefore supports no claim.

**v4 fix.** The exact decomposition τ = τ_near-miss + τ_far-miss is
registered before generation. The tolerant rule (|count − n| ≤ 1 passes)
joins the scoring-robustness family with its own simultaneous interval,
alongside S1, S2 and S3, and ι is recomputed under it.

**Rationale.** The decomposition is exact and costs no generation. v3
demonstrated that the whole registered conclusion moves under it, which is
precisely the property that requires prospective declaration.

---

## C9. Claim ladder: registered effects, diagnostics, assumptions

**v3 problem (REGISTERED).** v3's claim vocabulary covers direction,
magnitude and equivalence for the primary estimands (`claims.py`), and its
two-level ladder distinguishes a swap effect from an identity-specific
effect (v3 §11). The separation of registered results from diagnostics,
measurement caveats and unregistered sensitivity had to be constructed in
prose after the fact (RESULTS_V3 preamble).

**v4 fix.** Five machine-readable tiers are registered: Tier 0 measurement
premises, Tier 1 registered confirmatory effects, Tier 2 registered
conditional upgrades, Tier 3 registered diagnostics, Tier 4 exploratory.
Every emitted statement carries `tier`, `family`, `interval_type` and
`measurement_basis`. The v3 guarded-emitter pattern is extended to every
tier, and an executable check refuses any Tier 3 quantity name inside a
Tier 1 or Tier 2 statement.

**Rationale.** v3 proved the pattern works for one string; generalising it
makes the separation a property of the program rather than of the report.

---

## C10. Amendments A2 to A3.2 registered prospectively

**v3 problem (REGISTERED).** Seven amendments were required after
registration to reach a workable measurement gate: single annotator (A1),
autorater-assisted workflow (A2), freeze and holdout invariants (A2.1),
dev-loop correctness (A2.2), frozen autorater protocol (A3), and two
reasoning-budget corrections (A3.1, A3.2). Six of them, A2 onwards, build
the autorater pathway.

**v4 fix.** The end state is registered before execution: a
development/calibration split of the response pool, one non-study judge at
a pinned revision with a hashed configuration, one-shot calibration
enforced by an append-only ledger, realised evidence-boundary binding,
machine-distinguishable `measurement_basis` markers, and a pre-freeze
scratch-only judging-condition selection with a registered decision rule.

**Rationale.** Every amendment corrected a gap that is now known. Carrying
the corrected machinery into the registered document removes the gap
rather than the amendment.

---

## C11. Smaller corrections carried into v4

| # | v3 problem | v4 fix | Rationale |
|---|---|---|---|
| C11.1 | The unconstrained TOPIC arm truncated in 322/384 (E2B) and 333/384 (E4B) responses at the selected cap, so the accidental-compliance base rate is measured on mostly truncated text (`result.json`, `per_arm.TOPIC`) | The cap-selection pre-screen includes zero-constraint prompts; the unconstrained truncation rate is reported, and when it exceeds 0.10 the topic-alone pass rate is reported as a lower bound | The base rate bounds a contamination risk (v3 §24) and must not be silently degraded by the apparatus |
| C11.2 | The target-alone arm truncated in 47/384 = 12.2% of E4B responses, above the 0.10 truncation rate v3 registered as its completion-cap criterion, with no per-arm rule attached | Per-arm truncation is a registered Tier 3 compliance quantity with an explicit per-arm threshold and a fixed interpretation block | v3 recorded the quantity without a per-arm rule |
| C11.3 | The focal grid is floored at m = 7 because the target word *however* has seven letters (v3 §5), so both identified replications selected m* = 7, the most restrictive admissible severity | The floor is registered as a structural property of the target word, the realised m* is reported against the grid boundary, and target-word length is declared as the mechanism the discriminating design tests | The operating point sat on a grid boundary set by an unrelated design choice, which was not visible in v3 |
| C11.4 | Wording length was calipered between references and the focal constraint only | The caliper additionally binds the surrogate target's wordings to the target's wordings within 20% | The difference-in-differences requires the two outcome constraints to be length-comparable |
| C11.5 | Composed response length differs systematically by arm and had no registered treatment | Composed response length is a registered comparability quantity reported at Gate 2B and in the confirmatory report, with a fixed interpretation block on breach | It is a post-treatment quantity (v3 §21) and stays out of every primary formula |
| C11.6 | Pseudo-runs were the only draw diagnostic | The variance decomposition (σ²_block, σ²_draw) and the single-draw-equivalent standard error are registered outputs; the 1,000 pseudo-runs are retained for continuity | Under a draw-averaged estimator the decomposition is the informative quantity |

---

## Budget consequence

Counts are generations per model replication. v3 figures are derived from
its registered constants and gate code; v4 figures are the registered
values of the v4 preregistration §§17, 18.2, 18.4, 18.5, 8.

| Stage | v3 | v4 |
|---|---:|---:|
| Regime pre-screen: completion-cap selection | 288 | 288 |
| Regime pre-screen: severity screen | 1,056 (32 reference severities + 12 grid points) × 24 | 2,736 (94 ladder severities + 20 grid points) × 24 |
| Gate 2A solo calibration | 4,224 (44 cells × 96 × 1 draw) | ≤ 16,896 (≤ 44 cells × 96 × 4 draws) |
| Gate 2B composed validation | ≤ 192 | ≤ 1,728 |
| Procedural pilot | 1,152 | 1,056 |
| Confirmatory | 36,864 (6 arms × 384 × 16 draws) | 33,792 (11 arms × 384 × 8 draws) |
| Greedy replication | 384 | 768 |
| **Total** | **44,160** | **57,264** |

The confirmatory stage costs 0.92× v3 while carrying five more arms and a
projected 2.8× smaller standard error, because the draws v3 discarded now
enter the estimator. The growth is entirely in calibration: about 15,900
additional generations per model buy the dense severity ladder, the
precision that a denser ladder requires, and the composed-uptake
measurement on both sides. Total cost is about 1.30× v3.
