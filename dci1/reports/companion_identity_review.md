> **Partly superseded, 2026-08-20 (same day, later).** This review is retained
> as written. Three of its statements have since been corrected by measurement
> and one by a re-reading of the rows, and a reader should take the corrections
> first:
>
> 1. Its §7 appendix quotes `D(B←A)` = 0.468 / 0.316 against `D(R̄←A)` =
>    0.582 / 0.727. Those are **not delivery losses**: each subtracts a composed
>    rate on the 384 confirmatory topics from a solo rate on the 96 calibration
>    topics, unpaired across disjoint sets. Corrected and bounded in
>    `dci1/reports/v3_reanalysis/`, with the topic-set shift now measured on A
>    at −0.046 and −0.105.
> 2. It treats the B+R pilot's Δ = +0.34/+0.38 as possibly inflated by vacuous
>    passes. That suspicion was **right**, on the protocol's own bound: §17.4's
>    partial-identification recomputation — every vacuous pass forced to a
>    failure, no row dropped — puts Δ at **+0.095** and **+0.068**, both below
>    the 0.10 generic-load threshold. (The *restriction* to ≥20-word responses
>    gives +0.348 / +0.360 instead, but that drops 36% of one arm and none of
>    the other and conditions on a consequence of the treatment, which §9.3
>    forbids for exactly that reason.) Δ is also nearly collinear with response
>    length. `dci1/reports/pilot_reanalysis/`.
> 3. It reports the registered reference pool as structurally unusable. Under a
>    uniform length instruction the pool clears §13.2's conditions 1 and 6 on
>    three of four models at solo vacuity 0.000 — it was **length-falsified**,
>    not falsified. `dci1/reports/cal_screen_v4/`.
> 4. It does not identify the confound that matters most: A is the only
>    *production* constraint in the pool and every reference and B are
>    prefix-closed budgets, so a positive companion-swap effect is ambiguous
>    between "A" and "a production companion".
>
> The identification chain, the version history and the terminal-status
> reconstruction in the body below stand.

# The DCI Companion Question

**An evidence review of DCI-1 v2 → v4.** When a model must satisfy two
instructions at once, does *which* companion it is given change compliance with
the focal instruction — beyond the generic cost of having two instructions at all?

| | |
|---|---|
| repo | `/home/cnm13ryan/git/dci` |
| branch | `feat/dci1v4-fresh-study` |
| head | `1e40151` |
| reviewed | 2026-08-20 |

---

## Verdict

**The repository contains no confirmatory evidence that companion identity
matters beyond generic compositional difficulty, and the one large positive
result it does contain is confounded by precisely the defect that v4 was
designed to remove.** v2 produced no estimate at all — Gate 2 admitted 0 of 12
reference candidates on every calibrated model. v3 executed the only
*confirmatory* companion-swap estimand in the entire record, and all four
primary members returned *direction unresolved*; recomputed over all cached
draws it is +0.064 (E2B) and +0.074 (E4B), *below* the source memo's 0.10
generic-load threshold — and its own identity gate, reference exchangeability,
failed in both models, so no v3 result could ever have licensed an identity
claim. The large positive figure — the B+R pilot's Δ = +0.343 / +0.375,
classified `H1_PAIR_SPECIFIC` — is explicitly non-confirmatory and compares A
against references matched to *B*, not to A: the companions differ in solo
compliance by 0.10–0.16, and A is the only constraint in the registered
vocabulary that is not satisfiable by writing less.

The strongest claim the record justifies is narrower and does survive:
**companion identity moves delivery loss at approximately fixed companion
difficulty.** Across three references whose solo compliance differs by ≤ 0.021,
D(B←R_j) varies by 0.177 (E2B) and 0.188 (E4B). Compliance under composition is
therefore not a function of instruction count alone. But that is a fact about
the reference set, established on exploratory data; it does not establish that
*A* specifically damages *B*, and a read-only recomputation from the v3
confirmatory cache points the other way — A damages the matched references
*more* than it damages B (mean +0.582 vs +0.468 on E2B; +0.727 vs +0.316 on
E4B).

v4 is the design that answers the question. It is implemented, tested, and
**deliberately not frozen**: no confirmatory generation, Gate 1 unapproved, the
registered reference pool structurally falsified, nine registered decisions open.

---

## §0 Evidence tiers used throughout

These are the repository's own categories (`dci1/RESULTS_V3.md` preamble; v4r2
§3 claim ladder), with one addition of mine for quantities I computed during
this review that appear in no artifact.

| Tier | Meaning |
|---|---|
| **REGISTERED** | Preregistered confirmatory result, read from a signed stage record under the registered claim rules. |
| **DIAGNOSTIC** | Registered secondary. Reported, never a claim. |
| **EXPLORATORY** | Non-confirmatory pilots and design screens. Frozen protocols, real generations, no claim licence. |
| **DERIVED HERE** | My own arithmetic on recorded rows during this review. Reproducible; in no repository artifact. |
| **NOT RUN** | Specified and implemented, never executed — including every v4 confirmatory estimand. |

---

## §1 Identification: what each comparison could isolate

Every version operationalises the question the same way — hold the instruction
count at two, swap one slot, read the other. What changes across versions is
**which slot is the outcome** and **what the substitute is matched on**. Those
two choices decide what the contrast identifies.

### Estimands bearing on the question, v2 → v4

| Version | Estimand | Outcome | Substitute matched to | Status |
|---|---|---|---|---|
| v2 §11 | `τ = P(F_A｜A+B) − ⅓ΣP(F_A｜A+R_j)`, per order | A (failure) | **B**, on solo failure, ±0.10 (§18 Gate 2) | NOT RUN |
| v2 §11 F2 | `δ_jk` exchangeability — the gate on the Level 2 "identity-specific" claim, ±0.05 | — | — | NOT RUN |
| v3 §11 F1 | Same τ, unchanged formula | A (failure) | **B**, on solo failure, ±0.10 (§18.4) | REGISTERED, 2 of 4 models |
| v3 F2 / F3 | Exchangeability; per-reference contrasts | A | — | REGISTERED |
| B+R pilot | `Δ = D(B←A) − D(B←R̄)` | **B** (compliance) | **B** — inherited from v3, *not* re-matched to A | EXPLORATORY |
| v4r2 §11.3 | `Δ_R = D(B←A) − ⅓ΣD(B←R_j)` | B | **A**, on solo compliance, ±0.10 + Newcombe (§13.2) | NOT RUN |
| v4r2 §11.5 | `Ξ = Δ_R − [D(R̄←A) − D(R̄←R̄′)]` | B vs R̄ | A | NOT RUN |
| v4r2 §11.5 | `Δ^A` — v3's estimand on the compliance scale, demoted to diagnostic | A | B (as v3) | NOT RUN |

### What each needs to be true

A companion swap identifies a companion-*identity* effect only if the substitute
is exchangeable with A in every respect that touches the outcome except
identity. The record operationalises that in three incompatible ways.

- **v2 / v3 — matched on solo failure to B.** Correct for the estimand v3
  registered (τ on outcome A, swapping the companion between B and R_j): B and
  R_j are the two companions, and they are matched to each other. The mean
  reference-minus-B solo-compliance gap is +0.052 (E2B) and +0.028 (E4B) — v3
  succeeded on its own criterion (v4r2 §13.1). The identity upgrade additionally
  required exchangeability within ±0.05 (v2 §11 Level 2) and, from §16,
  comparable composed uptake. **Both failed.**

- **B+R pilot — matched to the wrong constraint.** The pilot moves the outcome
  to B and keeps v3's frozen references. Those are matched to B, so as
  *companions* they are 0.164 (E2B) and 0.101 (E4B) easier than A in solo
  compliance (`dci1/docs/v4_prefreeze/C6.json`). Nothing in the pilot adjusts
  for that. It also pairs across topic sets: P(B|A) is read from the 384 v3
  confirmatory blocks while P(B|R) is generated on the 96 solo-calibration
  topics, resting on the seeded area-stratified split being exchangeable
  (`protocol.json → reused_baselines.cross_set_note`).

- **v4 — matched to A, and honest about the ceiling.** §13.2 inverts the anchor,
  adds a Newcombe interval condition, a disjoint 24-topic confirmation, a
  wording-length caliper, witness and parse-independence conditions, and a
  solo-vacuity condition. §11.3 notes the algebra that makes Δ_R well-behaved —
  the solo baseline cancels, so it is immune to solo ceiling and solo noise.
  §11.4 makes position explicit: only Δ-type quantities are position-clean in
  both configurations. §5 and §29 then **permanently withhold** semantic
  identity-specificity (level L5): matching leaves every other property of A
  free.

### Two identification limits no version removes

**The slope is assumed, not estimated.** Every design matches companion
difficulty inside a caliper and then treats the residual as identity. None
estimates dD/d(companion solo compliance). v4 registers that alternative as open
decision **V5** — "matched references only, or a difficulty-spanning set" — and
defaults to matched, on the reasoning that "the pilot evidence that identity
moves delivery loss at fixed difficulty suggests the relationship is not the
dominant term". That is an assumption doing identification work.

**Load is fixed at two.** The construct memo's best-evidenced interaction is
three-place: Γ = +0.312 [+0.188, +0.438] from a complete matched factorial, in a
corpus where F(A+B) and F(A+ctrl) are both exactly 0.000 at load two
(`dci-construct-pass2.md` §D.1). v4 §5 and open decision **V2** exclude load
three by design, so the whole DCI-1 line is measuring a two-place shadow of a
quantity that may be irreducibly three-place.

---

## §2 Evidence: what actually ran, and what it returned

### v2 — terminal before any data · NOT RUN

All four registered replications reached preregistered terminal outcomes with
**zero confirmatory generations**. The Qwen pair failed Gate 2 ("Regime not
found"); the gemma-3n pair failed Gate 0 on the §17 truncation ceiling (0.139
and 0.150 against 0.10). On every calibrated model the reference pool was
inadmissible.

*Source: `evidence/dci1-v2/<model>/prefreeze-apparatus/calibration/gate2.json`*

| Model | A solo @ n*=3 | B solo @ m* | Admitted (≥3 required) | Verdict |
|---|---:|---:|---:|---|
| qwen3-4b | 0.125 ✗ band | 0.323 | **0 / 12** | terminal |
| qwen3-4b-instruct-2507 | 0.073 ✗ band | 0.333 | **0 / 12** | terminal |
| gemma-3n-e2b-it | 0.323 ✓ | 0.229 | **0 / 12** | Gate 0 terminal |
| gemma-3n-e4b-it | withheld | — | — | Gate 0 terminal |

The record states the cause as scientific, not procedural: "Across every
calibrated model, the declared reference pool … is uniformly far harder than
either A or B — a consistent scientific finding about this constraint family,
not an apparatus artifact" (`dci1/REPORT.md` §15).

### v3 — the only confirmatory companion swap ever executed · REGISTERED

Two Gemma replications ran the full pipeline to `UNMASKED_ANALYSIS`; both Qwens
terminated at Gate 2A with `REFERENCE_POOL_MISMATCH` (2 eligible family/severity
pairs where 3 were required) and carry, in the report's own words, "no evidence
about the effect".

**Family F1 — primary τ, order-stratified, 384 blocks, 10,000-resample block bootstrap**

| Model | Stratum | τ̂ | 95% simultaneous | Direction | Magnitude |
|---|---|---:|---:|---|---|
| E2B | target-first | +0.007 | [−0.080, +0.094] | unresolved | **equivalence** |
| E2B | added-first | −0.026 | [−0.117, +0.065] | unresolved | unresolved |
| E4B | target-first | +0.090 | [−0.003, +0.184] | unresolved | unresolved |
| E4B | added-first | +0.040 | [−0.047, +0.127] | unresolved | unresolved |

The single resolved registered claim of the entire study is an *equivalence*:
E2B target-first lies wholly inside ±0.10. It is fragile —
`DCI1_v3_to_v4r1_change_summary.md` C4 shows the same interval re-centred on
that estimand's own across-draw mean (+0.089) emits a resolved positive
direction instead, so "the one resolved claim of v3 turns on the draw lottery".

**Identity gates — both failed in both models**

| Gate | E2B | E4B |
|---|---|---|
| Exchangeability F2 (±0.05 required) | `false` — δ₂₃ = −0.154, sim [−0.234, −0.073] | `false` — by interval width |
| Per-reference F3, target-first | vs AR2 **+0.135** [+0.011, +0.260]; vs AR3 **−0.130** [−0.254, −0.007] — resolved in *both* directions | all six positive (+0.010…+0.120), none resolved |
| Manipulation check — companion uptake | AB 0.357 vs AR 0.539 / 0.323 / **0.021** (AR3 flagged) | AB 0.438 vs AR **0.073 / 0.042 / 0.099** (all three flagged) |

Read from `evidence/dci1-v3/<model>/analysis/unmasked/result.json`
(`exchangeability_holds`, `uptake_flagged`, families F1–F3). The E4B references
match on solo failure but are delivered at 4–10% under composition against B's
44% — the arms being contrasted did not receive comparable treatments.

**Registered diagnostics all lean positive and none is a claim (DIAGNOSTIC):**
pseudo-selection means +0.089 / +0.038 (E2B) and +0.065 / +0.081 (E4B) over
1,000 alternative primary draws; greedy pooled means +0.104 (E2B) and +0.111
(E4B). An unregistered near-miss sensitivity finds the E4B positive tendency
survives discounting off-by-one failures (added-first strengthens to +0.123)
while E2B's signs flip. E2B's registered target-first draw sits *below the 5th
percentile* of its own re-selection distribution.

### The B+R pilot — the one large positive number · EXPLORATORY

Frozen protocol `229eeae8…`, 576 rows per model, 0 truncations, verifier hash
pinned to the registered instrument, re-scored under the v4 instrument at
agreement 1.000 (check C13). It executes the construct memo's §G row 1 test in
the DCI-1 vocabulary and applies the memo's verbatim thresholds.

*Source: `dci1/reports/br_pilot_v4/result.json`, 10,000-resample percentile intervals*

| Quantity | E2B | E4B |
|---|---:|---:|
| P(B solo) @ m*=7 | 0.813 | 0.760 |
| P(B \| A+B) | 0.344 | 0.444 |
| P(B \| B+R̄) | 0.688 | 0.819 |
| D(B←A) | +0.468 | +0.316 |
| D(B←R̄) | +0.125 | −0.059 |
| **Δ** | **+0.343** [+0.281, +0.405] | **+0.375** [+0.319, +0.430] |
| Classification | `H1_PAIR_SPECIFIC`, CI-robust | `H1_PAIR_SPECIFIC`, CI-robust |

Two qualifications the headline classification does not carry. First, **the
per-reference minimum is not CI-robust above 0.25**: the smallest Δ_j is +0.265
[+0.189, +0.341] on E2B and +0.295 [+0.218, +0.371] on E4B — both exclude 0.10
decisively, both span 0.25. Under a conservative min_j rule the pilot supports
"not generic load" and does not reach "pair-specific". Second, **the references
disagree enormously with each other**: Δ_j spans 0.265–0.442 (E2B) and
0.295–0.483 (E4B), at companion solo compliance that is identical to within
0.021.

**Order does not explain it.** The v4 preregistration reports the pilot's own
order-stratified values at §16.4: E2B +0.419 (B stated first) and +0.267 (B
second); E4B +0.302 and +0.448. All four exceed 0.25 — while P(B|A) itself moves
from 0.222 to 0.466 with order on E2B, so order is a very large moderator of the
*level* and not of the contrast.

### The two design screens · EXPLORATORY

**FORM × STEM** (13,392 rows, protocol `98f8ee0d…`) and **B-grid** (2,112 rows,
protocol `6a63ba78…`) were run against the v4 reference-pool crisis. Between them
they produced the most decision-relevant facts in the current record.

| Finding | Numbers | Source |
|---|---|---|
| The registered reference pool is structurally falsified for the v4 criterion | 0 of 64 matched rungs across four models survive the solo-vacuity condition; the empty string passes 94/94 reference severities, 4/4 B, **0/8 A** (verified executably during this review) | C10; Amendment B §1 |
| Non-budget candidate families fix it | P(≥3 families) 0.41–0.88 against 0.000–0.001 for the registered pool | fs_screen §3 |
| B's apparent solo compliance is largely vacuous | vacuous share of B passes 0.15–0.60 (Gemmas), 0.64–1.00 (Qwens); median current-stem answer 4–11 words on the Qwens | bgrid §3 |
| Length control changes D(B←A) materially, and reverses it on the Qwens | raw → ≥20-word: E2B +0.375→+0.250; E4B +0.333→+0.230; Qwen3-4B +0.125→**−0.071**; Qwen-Inst +0.042→**−0.333** | fs_screen §4 |
| Under a length-floored stem the two model families separate | D(B←A) at in-band rungs: E2B +0.333 (3.5 SE), E4B +0.500 (4.9 SE); both Qwens −0.167…−0.042, none beyond 1.7 SE | bgrid §7 |
| A single 24-topic draw can flip a terminal-status call | Qwen-Inst B-solo at m=10: 0.542 (screen 1) vs 0.667 (screen 2), across the 0.60 band floor | bgrid §5 |

### v4 — implemented, not frozen · NOT RUN

All four replications completed `QUALIFIED`, `GATE_0_APPARATUS` and
`REGIME_SCREEN` (15,264 real generations). `evidence/dci1-v4/<model>/` contains
exactly three stage records each; there is no Gate 1, Gate 2, freeze or
confirmatory record anywhere. Gate 1 is not approved: §10.2 is met for A and B
over 13,953 distinct genuine responses (three-process determinism 1.000, 48 + 45
boundary cases at 1.000, prose-only reimplementation 1.000), but the family
verifiers cannot be validated until the reference pool is final, and the pool is
falsified. Pre-freeze checks C3 is `BLOCKED`, C7 / C8 / C10 / C11 / C12 / C14 are
`PARTIAL`; registered open decisions V1–V9 are all undecided; `stages/freeze.py`
refuses to execute.

---

## §3 Evolution: what each version learned by failing

| Version | What it could not identify | What the next version changed |
|---|---|---|
| **v2** | Anything. The declared 12-constraint pool is uniformly far harder than both A and B, so no difficulty-matched reference exists; and both Qwens sit at target ceiling (A solo failure 2–12.5%). | v3: target grid n∈1…8, eight tunable reference families × four severities, staged solo/composed calibration, larger response budget, four separate replications, a gate state machine. |
| **v3** | Four things at once. (i) τ is unresolved in direction everywhere. (ii) τ estimates a *swap effect against one frozen reference set* — the code's own field name is `secondary.pooled_swap_effect` — and the identity reading needs exchangeability and comparable uptake, both of which failed. (iii) 15 of 16 cached draws never entered the estimator, and the draw lottery has SD ≈ 0.036–0.039 against a block SE of 0.039–0.042. (iv) Grid coarseness, not model behaviour, terminated both Qwens. | v4: three separately named estimands with the phenomenon label attached to the identity term alone; the compliance vector replaces target failure as the primitive; references matched to **A**; order becomes a cell-level factor; all M draws enter the cell mean; a 94-rung dense ladder; a precision precondition on equivalence; the near-miss decomposition registered prospectively. |
| **v4 rev 1 → rev 2** | Revision 1 inferred the discriminating design as a difference-in-differences over a surrogate target. Recovering the source memo showed it specifies a *companion* swap on the focal outcome, and that in a design with an empty background set "B+S" simply *is* the B-alone cell. | The surrogate target is withdrawn (U1, U2); the composed-uptake caliper is withdrawn as circular (U6, §13.3); reciprocal delivery loss becomes the primary framing; the complete 25-cell pairwise matrix replaces the crossing. |
| **v4 rev 2, pre-freeze** | Its own reference criterion. §13.2 condition 1 (match A's compliance) and condition 6 (solo vacuity ≤ 0.10) are structurally opposed: matching A's low compliance needs a restrictive "at most q", and a restrictive budget is satisfied by writing a shorter answer, which makes the pass vacuous. 0 of 64 matched rungs survive, on all four models. | Nothing registered. Three amendment drafts (A prompt stem, B reference form, C focal grid) — **none adopted**. Gate 1 blocked on the pool being final. |

### The thread that runs through all four

Every version has failed at the same joint: **constructing a companion that is
comparable to A**. v2 could not find one in a fixed pool. v3 found three by
matching to the wrong constraint and then measured that they were not
exchangeable. v4 inverted the anchor and discovered that the entire registered
vocabulary makes the requirement unsatisfiable, because A is the only constraint
in it that a shorter answer cannot satisfy. The scientific question has never
been blocked by statistics or compute; it has been blocked by the construct pool.

---

## §4 Alternative explanations still on the table

Ordered by how much of the observed Δ each could account for. Every entry is
supported by a repository artifact; the verdicts are mine.

### Rival accounts of Δ = D(B←A) − D(B←R̄) ≈ +0.34 / +0.38

**1. Structural class / length channel.** A is a production constraint that
forces length up; every reference is a prefix-closed count budget that a shorter
answer satisfies; B is a max-word-length budget whose difficulty rises with
length. A's damage to B may be entirely mediated by response length.
*Support:* empty string passes 94/94 references, 4/4 B, 0/8 A (Amendment B §1;
re-verified here through the canonical verifier). Median words: unconstrained
329 (E2B) / 282 (Qwen3-4B) → one constraint 121 / 49 → two constraints 80 / 25
(`CHANGES_SCIENTIFIC.md`). B-solo median 25 words vs A+B 67 (fs_screen §4).
Restricting to ≥20-word answers cuts D(B←A) by a third on the Gemmas and
reverses it on both Qwens.
**Status: fully viable and unexcluded.** v4 §13.3 registers response length as a
*mediator* and explicitly refuses to condition on it, so the registered design
reports this channel rather than removing it.

**2. Unequal companion difficulty.** A is simply a harder instruction than any
reference, and harder companions cost more.
*Support:* reference-minus-A solo-compliance gap +0.164 (E2B), +0.101 (E4B) on
identical topics and estimator (C6). v4r2 §13.1 quotes +0.198 / +0.210 from a
cross-set pairing; the two figures disagree and `CHANGES_SCIENTIFIC.md` records
C6's as the one §13.1 asks for.
**Status: viable.** Constrained but not removed by §13.4: D(B←R_j) spans 0.177 /
0.188 at fixed difficulty, so difficulty is not the whole story — but no design
in the record estimates the difficulty→loss slope (open decision V5).

**3. Outcome-side vulnerability rather than companion specificity.** A damages
everything it is composed with; B is not special.
*Support:* derived here from the v3 confirmatory cache — see §7.
**Status: viable, and currently the better-supported reading.** The registered
discriminator (Ξ) requires reference-on-reference cells that exist in no dataset.

**4. Reference heterogeneity.** The answer depends on which reference you compare
against.
*Support:* v3 F2 `exchangeability_holds: false` in both models; E2B
per-reference contrasts resolve *positive* against AR2 and *negative* against
AR3 in the same stratum. Pilot Δ_j spans 0.18 at fixed companion difficulty.
**Status: established, not a hypothesis.** v4 §13.4 stops treating it as a
nuisance and registers a heterogeneity qualifier on every L3 statement.

**5. Measurement artifact — vacuous passing.** B's solo baseline is inflated by
degenerate short answers, so D(B←A) partly measures "A stopped the model writing
a seven-word answer".
*Support:* vacuous share of B passes 0.39–1.00 under the current stem; 0.00–0.17
under a length floor (bgrid §3). Under the floor, raw and ≥20-word D(B←A)
converge exactly (+0.208/+0.208, +0.375/+0.375).
**Status: viable for the level of D; largely neutralised by the floored stem,
which is not adopted** (Amendment A blocked on the focal grid).

**6. Manipulation-check failure.** An A+R cell where R is delivered 4% of the
time is not a two-instruction condition.
*Support:* E4B references at 0.042–0.099 uptake against B at 0.438; E2B AR3 at
0.021. All flagged by v3 §16.
**Status: viable, and it cuts both ways** — it deflates D(A←R̄) and so inflates
Δ^A, yet Δ^A is still only +0.064 / +0.074.

**7. Order effects.** Position, not identity.
*Support:* P(B|A) = 0.222 (A first) vs 0.466 (B first) on E2B. In the legacy
corpus the analogous τ reverses sign with order: +0.275 at QAC, −0.537 at ACQ
(`dci-construct-pass2.md` §D.4).
**Status: excluded as an explanation of Δ** — all four order-stratified pilot
values exceed 0.25 (v4r2 §16.4) — but a very large moderator of every level, and
the reason v4 makes order a within-block factor.

**8. Model / capability threshold.** The phenomenon is a property of a
checkpoint, not of the pair.
*Support:* both Qwens produced no v2 and no v3 estimate at all. Under the
floored stem both Gemmas show a positive loss and both Qwens are
indistinguishable from zero (bgrid §7).
**Status: viable and untested.** The two models that would carry the most
information have never reached an estimator.

**9. Higher-order structure.** The object is at least three-place, and load two
cannot see it.
*Support:* Γ = +0.312 [+0.188, +0.438]; F(A+B) = F(A+ctrl) = 0.000 at load two
(§D.1).
**Status: viable, excluded by design** (v4 §5, open decision V2).

**10. Small-sample and cross-set noise.**
*Support:* screens are 24 topics × 1 draw (SE ≈ 0.10). The pilot pairs a
96-topic set against a 384-topic set. v3 selected 1 of 16 draws and E2B's
registered τ landed below its own 5th percentile.
**Status: viable for the screens; small for the pilot's Δ**, whose intervals are
narrow.

---

## §5 Current evidential status

### Justified

- **EXPLORATORY — Companion identity moves delivery loss at approximately fixed
  companion difficulty.** Three references whose solo compliance differs by
  ≤ 0.021 produce D(B←R_j) differing by 0.177 (E2B) and 0.188 (E4B) — v4r2
  §13.4, from the pilot rows. Compliance under composition is therefore *not* a
  function of instruction count alone. The repository states the limit of this
  itself: measured at one draw per topic over 96 topics, so each solo rate
  carries SE ≈ 0.035 and "the observation constrains the difficulty explanation
  and does not settle it".
- **EXPLORATORY — Composing B with A costs B substantial delivery on both Gemma
  checkpoints, and this survives length control.** D(B←A) = +0.468 / +0.316 in
  the pilot; +0.333 (3.5 SE) and +0.500 (4.9 SE) at in-band rungs under a
  length-floored stem where B-side vacuity is zero.
- **REGISTERED — On the reciprocal side, with companions matched on solo
  difficulty, the excess is small.** v3's four F1 members are all
  direction-unresolved; one licenses equivalence inside ±0.10. Recomputed over
  all cached draws, Δ^A = +0.064 (E2B) and +0.074 (E4B) — below the source
  memo's 0.10 generic-load threshold (check C18, which also reproduces v3's
  recorded `pooled_swap_effect` exactly from the rows).
- **REGISTERED — Reference sets built by difficulty-matching alone are not
  exchangeable.** Established in both identified v3 replications, with one
  model's per-reference contrasts resolving in opposite directions within a
  single stratum.
- **REGISTERED — Non-identification is not a null.** Both Qwen replications carry
  the registered terminal status and the licensed statement is "the estimand is
  not identified for these models under this design" — never that interference
  is absent or small.

### Not justified

- **UNSUPPORTED — That A's excess damage to B exceeds generic compositional
  load.** The only quantity above the 0.10 threshold is the pilot's Δ, whose
  companion set is 0.10–0.16 easier than A, drawn from a structurally different
  constraint class, and paired across topic sets. Δ_R — the estimand designed to
  support this — has never been generated.
- **UNSUPPORTED — That the effect is a property of the (A, B) pair.** The
  `H1_PAIR_SPECIFIC` label is the pilot's own protocol vocabulary applied to a
  point estimate; the repository classifies the whole artifact as
  non-confirmatory design evidence, and the memo whose threshold it uses set that
  threshold in a different constraint vocabulary.
- **WITHHELD — Semantic identity-specificity.** v4 §3 assigns this to claim level
  L5 and withholds it *permanently*, with an executable check
  (`claims.assert_no_l5_emitter`) that refuses any code path emitting it. No
  matching rule over this pool holds every property of A constant except meaning.
- **UNSUPPORTED — Any statement about the Qwen checkpoints.** Two terminal
  outcomes, no estimate, and a terminal-status call that flipped between two
  independent 24-topic draws.
- **UNSUPPORTED — Any magnitude.** Nothing in v3 resolves a magnitude above
  SESOI; the pilot's magnitudes are exploratory and its per-reference minimum
  spans the pair-specific threshold.
- **BOUNDED — That the outcome measure captures human-judged compliance.** Every
  result is verifier-defined. v3's basis is `autorater_calibration_approved` with
  `HUMAN_VALIDATION_UNAVAILABLE`; the later 120 author-labels met the criterion
  for the verifier-pass class (0/52) and missed it for the fail class (4/52,
  Wilson upper 16.1%), every disagreement being a human off-by-one miscount. v4
  cannot improve on this: §10.3 requires an annotator independent of the design
  team and none exists.

---

## §6 The minimum remaining evidence

### First, the analysis that needs no new generation

The outcome-side control is already computable from committed rows and appears
in no artifact. Pair R_j's Gate 2A solo cells with its `added_pass` column in the
v3 confirmatory cache to get D(R_j←A); the pilot already reports D(R_j←B). §7
below does exactly this, and the result argues against B-specific vulnerability.
Formalising it — block bootstrap, the same topic set on both sides,
per-reference intervals — is a re-analysis, not an experiment, and it changes the
prior for the whole programme.

### Then, the smallest experiment that would settle it

The core defect is that the excess attributed to A is confounded with three
things at once — A's difficulty, A's structural class, and the length A forces.
A decisive design has to break all three, and add the control that distinguishes
"A damages B" from "A damages anything".

1. **References matched to A and drawn from a non-prefix-closed family.**
   Amendment B's rate and lower-bound forms (CR7, CR4, CR6) meet the §13.2
   conjunction that the registered pool fails 0-of-64, and the empty string
   passes 0 of 48 of them. Without this, no reference can be as hard as A without
   being vacuous. *Must clear the conjunction on the 96 calibration topics first
   — the pre-screen has never been shown to predict Gate 2.*
2. **Response length equalised across cells, or measured and reported as a
   mediator with the restricted estimate beside the raw one.** The floored stem
   removes B-side vacuity on all four models and makes the raw and
   length-restricted D(B←A) converge — at the cost of re-anchoring n* and m* on
   every model and terminating qwen3-4b on the registered grid, which is why the
   focal grid needs the fresh-topic confirmation the B-grid screen's MARGINAL
   verdict demands.
3. **The reference-on-reference cells.** Ξ = Δ_R − [D(R̄←A) − D(R̄←R̄′)] is
   registered at §11.5 and needs D(R_j←R_k), which exists in no dataset in the
   repository. This is the single quantity that separates "A is specifically
   damaging *to B*" from "A is a generically damaging companion", and it is the
   argument for running v4's full 25-cell matrix rather than the §8.6 reduced
   design.
4. **A difficulty-spanning reference arm (open decision V5).** Three references
   inside a 0.10 caliper cannot estimate dD/d(companion compliance); they assume
   it away. Admitting references that deliberately span companion difficulty
   turns the leading rival explanation into a measured slope with A's value read
   off it. This is the one identification gap that v4 *as registered* still does
   not close, and closing it costs references, not models.
5. **Both orders within block, all draws in the cell mean, and at least one Qwen
   carried.** Already registered (§8.2, §8.4). The Qwens matter because they are
   the only checkpoints where the length-controlled D(B←A) is not positive — they
   are the test of whether this is a pair property or a capability threshold.

Everything above is one model's worth of v4 confirmatory generation plus the
reference-pool amendment: on the registered allocation, 25 cells × 384 blocks ×
M = 4 ≈ 38,400 generations, or ≈ 48,000 if the pre-freeze variance re-estimate
(φ ≈ 0.44 pooled) forces the menu to 480 blocks. The blocker is not compute. It
is that Gate 1 cannot be approved until the reference pool is decided, and three
amendments sit drafted and unadopted.

---

## §7 Appendix — the outcome-side control, computed here

**DERIVED HERE.** This quantity appears in no repository artifact. It is
registered as a v4 secondary estimand ("Reciprocal losses: D(R_j←B) and
D(R_j←A)", §11.5) and no v4 data exist, but it is recoverable now from v3.

### Method

Solo compliance for A, B and each admitted reference is read from
`evidence/dci1-v3/<model>/gate2a/cache.jsonl` (96 calibration topics, 1 draw).
Composed compliance for the companion is the `verdicts.added_pass` column of
`evidence/dci1-v3/<model>/confirmatory/cache.jsonl`, averaged over all 6,144 rows
per arm (384 blocks × 16 draws). Arm→family mapping from `RESULTS_V3.md` §2.
This reproduces the pilot's D(B←A) to five decimals (+0.46826 / +0.31608), which
is the check that the pipeline matches.

### How much delivery each outcome loses when A is the companion

| Model | Outcome | Solo | With A | D(·←A) |
|---|---|---:|---:|---:|
| E2B | **B** @ m*=7 | 0.813 | 0.344 | **+0.468** |
| E2B | RF1 @ 5 | 0.865 | 0.520 | +0.345 |
| E2B | RF2 @ 5 | 0.865 | 0.304 | +0.560 |
| E2B | RF6 @ 4 | 0.865 | 0.022 | +0.842 |
| E2B | *mean over references* | 0.865 | 0.282 | **+0.582** |
| E4B | **B** @ m*=7 | 0.760 | 0.444 | **+0.316** |
| E4B | RF2 @ 2 | 0.781 | 0.061 | +0.720 |
| E4B | RF6 @ 4 | 0.781 | 0.042 | +0.739 |
| E4B | RF4 @ 4 | 0.802 | 0.080 | +0.723 |
| E4B | *mean over references* | 0.788 | 0.061 | **+0.727** |

### Reading

**B is not the outcome A damages most — on E4B it is damaged less than half as
much as any reference,** at a solo baseline that differs by 0.02–0.04. Set beside
the pilot's reciprocal figures, D(R̄←B) = +0.031 (E2B) and +0.056 (E4B), the
picture is that **A is a strongly damaging companion to everything and B is a
comparatively harmless one**. That is the signature of an asymmetry between two
*kinds* of constraint, not of a relationship between two particular instructions.

It also supplies the intuition for the mechanism: A demands the token *however*
exactly *n* times, which forces text; the references cap a count that grows with
text; so composition with A blows every budget. B caps a maximum over words
rather than a sum, so it saturates — which is exactly why it loses less.

### What this does not establish

- Solo baselines come from 96 calibration topics and composed cells from 384
  confirmatory topics. The comparison *among* outcomes is safe (all baselines
  share one set and one estimator); the *level* of each D is not. For scale,
  A-alone compliance is 0.708 on the calibration set and 0.662 on the
  confirmatory set (E2B), 0.688 and 0.583 (E4B).
- No intervals. These are point estimates without a block bootstrap.
- D(R̄←A) and D(R̄←B) come from different topic sets, different draw counts and
  different stages, so the difference between them is not a clean
  difference-in-differences. The clean quantity is Ξ, and it needs the
  reference-on-reference cells that do not exist.
- The E4B reference losses are near-total (composed compliance 0.04–0.08) — the
  same manipulation-check failure v3 flagged. A companion that is abandoned is
  not a companion that was delivered.
- This is exploratory re-analysis of registered rows. It licenses no confirmatory
  claim and, under v4 §14.2, these rows may never enter a v4 estimator.

---

## Primary sources

**Preregistrations:** `user-notes/DCI-1_preregistration_v2.md`,
`user-notes/DCI-1_preregistration_v3.md`,
`user-notes/DCI1_preregistration_v4r2.md`.

**Results:** `dci1/REPORT.md`, `dci1/RESULTS_V3.md`,
`dci1/reports/{br_pilot_v4,fs_screen_v4,bgrid_screen_v4,gate1_v4}/`.

**Records:** `dci1/evidence/dci1-v{2,3,4}/`, `dci1/docs/v4_prefreeze/C*.json`,
`docs/v4_traceability.md`, `CHANGES_SCIENTIFIC.md`.

**Construct background:** `user-notes/dci-construct-pass2.md`,
`exploratory/FINDINGS.md`.

*Prepared as a read-only review. No repository file was modified.*
