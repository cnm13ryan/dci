# The B+R pilot's Δ, and the mediator it is almost collinear with

**Classification: DERIVED / POST-HOC re-analysis of closed evidence.**
Read-only. The B+R pilot and v3 are closed and their records stand.
Produced by `dci1/tools/pilot_length_channel.py`; every number is in
`dci1/reports/pilot_reanalysis/length_channel.json`.

---

## 1. What the pilot reports, and what else is unequal

The pilot reports Δ = P(B | B+R̄) − P(B | A+B) = **+0.343** (E2B) and **+0.375**
(E4B), classified `H1_PAIR_SPECIFIC`, CI-robust. It is the largest positive
result in this repository and the reason v4 registers Δ_R as a primary estimand.

The companion is not the only thing that differs between those two cells.

| | B+R̄ cells | A+B cells |
|---|---:|---:|
| source | the pilot's own generations, 96 solo-calibration topics | the v3 confirmatory `AB` arm, 384 confirmatory topics |
| mean words | **24.8** | **127.9** (E2B) / **139.1** (E4B) |
| median words | **23** | **126** / **137** |

B at m\* = 7 is "every word has at most seven letters". Its difficulty rises
with the number of words a response contains, because each further word is
another chance to exceed the budget. The two cells being differenced differ
**five-fold** in the quantity most directly coupled to the outcome.

## 2. Vacuity, two ways, and they disagree

There are two ways to ask whether degenerate short answers carry the result, and
**the protocol's own answer is not the intuitive one**.

**§17.4, the registered partial-identification recomputation** — every vacuous
pass forced to a failure, no row dropped, nothing conditioned on:

| model | Δ, as reported | Δ, §17.4 forced |
|---|---:|---:|
| E2B | +0.3433 | **+0.0950** |
| E4B | +0.3751 | **+0.0678** |

**Both fall below the 0.10 generic-load threshold.** `P(B｜A)` does not move at
all — the A+B responses average 128–139 words and are never vacuous — while
`P(B｜R̄)` collapses from 0.688 to 0.439 and from 0.819 to 0.512, because 36% of
the pilot's B+R responses are under twenty words.

**The restriction to ≥ 20 words** — dropping the short rows instead of recoding
them — gives the opposite answer: +0.3484 and +0.3599, essentially unmoved.

The two differ because they are different operations, and §9.3 says which one
the protocol uses and why: vacuous passes "are counted as passes in the primary
estimand, because response shortening under composition is a candidate mechanism
rather than a nuisance, and **removing them would condition on a consequence of
the treatment**", and they are handled instead by the §17.4 forcing. The
restriction drops 36% of one arm and none of the other, selected on an outcome
of the treatment. **The forced recomputation is the registered bound; the
restriction is a collider-conditioned sub-population.**

### And §17.4 says what to conclude when the two disagree

§17.4's last sentence is a decision rule, not a reporting convention:

> "A claim is licensed only when the primary and the vacuity-forced
> recomputation license the same claim; otherwise **the axis is reported
> unresolved** with both bounds."

The primary estimate is +0.343 and +0.375, which under §11.6's thresholds would
support a pair-specific reading. The forced recomputation is +0.095 and +0.068,
which supports generic load. **They license different claims, so by the
registered rule the axis is unresolved and both bounds are reported.** That is
the correct disposition of the pilot's headline — stronger than "it is a vacuity
artifact" and stronger than "it survives", because it is the protocol's own
verdict rather than an adjudication between two analyses.

F6 does not gate the qualification away: the vacuity-rate difference between the
B+R cells and the B-solo baseline is far above 0.05.

An earlier draft of this report, and the earlier review in
`dci1/reports/companion_identity_review.md`, took the restriction as the answer
and concluded the result was not a vacuity artifact. That was the wrong
instrument.

## 3. It is very nearly a length contrast, and the design cannot say otherwise

Comparing P(B) between the two cells *within* word-count bins:

### gemma-3n-e2b-it

| words | B+R̄ n | P(B) | A+B n | P(B) | gap |
|---|---:|---:|---:|---:|---:|
| 20–30 | 194 | 0.732 | 9 | 0.556 | +0.176 |
| 30–45 | 126 | 0.675 | 70 | 0.786 | **−0.111** |
| 45–70 | 37 | 0.595 | 492 | 0.644 | −0.050 |
| 70–110 | 6 | 0.500 | 1624 | 0.499 | +0.001 |
| 110–170 | 4 | 0.250 | 2885 | 0.283 | −0.033 |
| 170+ | 0 | — | 1064 | 0.103 | — |

### gemma-3n-e4b-it

| words | B+R̄ n | P(B) | A+B n | P(B) | gap |
|---|---:|---:|---:|---:|---:|
| 20–30 | 186 | 0.828 | 0 | — | — |
| 30–45 | 134 | 0.821 | 34 | 0.882 | **−0.061** |
| 45–70 | 42 | 0.714 | 443 | 0.713 | **+0.001** |
| 70–110 | 5 | 0.200 | 1425 | 0.618 | −0.418 |
| 110–170 | 0 | — | 2568 | 0.426 | — |
| 170+ | 0 | — | 1674 | 0.246 | — |

Weighting the bins where both cells carry at least twenty responses:

| model | Δ raw | length-matched gap |
|---|---:|---:|
| E2B | +0.343 [+0.303, +0.382] | **−0.057** |
| E4B | +0.375 [+0.342, +0.409] | **−0.003** |

**At equal response length the identity contrast has no content, and on E2B it
points the other way.**

## 3b. Two confounds, and only one of them survives into v4

The pilot's own protocol declares the first of these. `reports/br_pilot_v4/protocol.json`, `reused_baselines.cross_set_note`:

> "P(B|A) comes from confirmatory topics while the pilot runs on
> solo-calibration topics; the seeded area-stratified random split makes the
> sets exchangeable by design, and B-solo cancels from Delta so only
> P(B|R) − P(B|A) carries the cross-set comparison."

So the structure was declared and the defence offered was topic-set
exchangeability. Nothing below overturns an undeclared assumption; it shows the
declared defence does not reach the mediator. **Exchangeable topics do not buy
comparable response lengths**, and B at m\* = 7 is length-coupled by
construction.

**(a) The source confound — the pilot only.** Δ's two terms come from two
different studies on two topic sets. **v4's own Δ_R does not inherit this**:
§8.1 puts A+B and B+R_j on every block, so both terms come from one run on one
topic set. The 25-cell matrix eliminates it by construction.

**(b) The class confound — structural, and it survives.** Every registered
reference family is an `S ≤ q` monotone count whose pass set is downward-closed
under prefix, and so is B: the empty string scores 94/94 on the reference pool,
4/4 on B and **0/8 on A**. That is a property of the pool by construction, not
of these three references. A budget companion *helps* a budget outcome by
letting length collapse; A is the only constraint in the design that fights the
collapse. The mechanism operates within a single source, on a single topic set,
at matched difficulty — so it survives everything the v4 design fixes, and
Δ_R as registered measures A's damage **plus** the control's help, with the
second term structurally non-positive in expectation.

Stated that way, H_class is the *default* reading of a positive Δ_R rather than
an alternative to it, and the class-matched companion arm of the pairwise-matrix
screen is the test.

**One residual the class arm does not remove.** A is *exactly-n*: two-sided,
failable by producing too much as well as too little. CL1, CL7 and CL8 are
*at-least-q*: one-sided. They share A's production direction, which is the axis
the shortening mechanism runs along, so the test is sound — but a two-sided
versus one-sided difference survives it. Δ_class ≈ 0 would license "the excess
belongs to the production class" and **not** "A is interchangeable with any
production companion".

## 3c. The A side separates on length by a factor of 1.2, not 5

Within v3 — one source, one set of 384 blocks — the A-side contrast is between
`AB` and the three `AR_j` arms, all of which contain A:

| model | `AB` | `AR1` | `AR2` | `AR3` | separation |
|---|---:|---:|---:|---:|---:|
| E2B | 127.9 | 159.0 | 146.6 | 184.2 | **1.15–1.44×** |
| E4B | 139.1 | 186.0 | 174.6 | 172.0 | **1.24–1.34×** |

against **5.1×** and **5.6×** for the pilot's cross-source B-side contrast. And
the consequence is visible in the numbers: length-matching **removes** the
pilot's Δ, and it **does not remove** Δ^A — which is +0.064 raw and **+0.118**
length-matched on E2B, +0.074 raw and **+0.059** length-matched on E4B, with all
six word-count bins carrying at least thirty responses in all four arms
(`dci1/reports/v3_reanalysis/`).

So the quantity v4 **demoted** to a diagnostic (Δ^A) is the better-supported one
in the existing data, and the quantity v4 **promoted** to primary (Δ_R) is the
one whose only pre-existing evidence is near-separated on the mediator. That is
not an argument for un-demoting Δ^A: v4's reasons for moving to the B side are
about the construct, not about support. It is an argument that restoring common
support on the mediator — which a uniform length instruction does — is
load-bearing for Δ_R rather than a convenience.

## 4. The qualification that matters more than the result

Only **two** of six bins carry at least twenty responses in both cells. Those
bins hold **9.1%** of the A+B rows and **28.3%** of the B+R rows on E2B, and
**7.8%** and **30.6%** on E4B.

The two cells are **nearly separated on the mediator**. That is the finding, and
it is a stronger statement than either "the effect is real" or "the effect is
length":

> In the B+R pilot, companion identity and response length are close to
> collinear. The pilot cannot separate them, and neither can any re-analysis of
> its rows.

Where the overlap is this thin, the length-adjusted contrast is weakly
identified and the raw contrast is largely a comparison of two disjoint length
regimes. The bins are also a **collider**: response length is a consequence of
the companion (§13.3), §22 registers it as a mediator the primary estimand is
never conditioned on, and a 40-word A+B response is an unusual response while a
40-word B+R response is a typical one. Nothing in §3 is a causal decomposition.

A second qualification, inherited: the pilot's P(B|A) comes from the 384
confirmatory topics and its P(B|R) from the 96 solo-calibration topics. The
pilot's protocol records this and argues exchangeability from the seeded
stratified split. The topic-set shift measured on A in
`dci1/reports/v3_reanalysis/` is −0.046 and −0.105 — far too small to produce
+0.34, but not zero, and every number here inherits it.

## 5. Why the arms separate, and what would close the gap

The mechanism is visible in the v3 arm means. Response length in v3, by arm:

| model | `TOPIC` | `A` | `AB` | `AR1` | `AR2` | `AR3` |
|---|---:|---:|---:|---:|---:|---:|
| E2B | 331.6 | 273.1 | 127.9 | 159.0 | 146.6 | 184.2 |
| E4B | 333.6 | 326.5 | 139.1 | 186.0 | 174.6 | 172.0 |

**A is the only constraint in the design that a model can fail by writing
less.** "Use the word *however* exactly n times" needs room; every other
constraint — B and all eight reference families — is a budget, satisfiable by
withholding. So a production companion holds length up while a budget companion
lets it collapse, and B's compliance moves with length. In the pilot's B+R
cells, with no production constraint present, responses fall to 23 words; in
A+B they stay at 126.

Two design changes close the gap, and both are already measured elsewhere in
this repository rather than proposed here:

1. **A uniform length instruction** (Amendment A's floored stem) puts every cell
   in the same 60–120 word band. On the calibration set the floored-stem solo
   cells run 50–88 median words across A, B and the candidate families, against
   8–31 under the current stem. The near-separation should largely disappear,
   and whether it does is a prediction the pairwise-matrix screen tests
   directly.
2. **A production-class reference.** The lower-bound families CL1, CL7 and CL8
   are the only candidates that share A's structural class. Admitting one makes
   Δ_class = D(B←A) − D(B←CL) estimable with the companion's class held fixed,
   which is the contrast Δ_R against budget-only references cannot supply.

Re-running `tools/pilot_length_channel.py` reproduces `length_channel.json`
**byte for byte**.

## 6. What this does and does not license

It does **not** show that companion identity has no effect. It shows that the
one large positive result in this repository fails on **two independent
grounds**, neither of which subsumes the other:

- on the protocol's own registered bound, §17.4's forcing takes Δ from +0.343
  and +0.375 to **+0.095 and +0.068**, below the generic-load threshold; and
- companion identity and response length are **nearly collinear** in that
  comparison — five-fold apart in words, overlapping on 8–9% of one arm, and at
  matched length the contrast is −0.057 and −0.003.

The first is a bound the protocol registers and needs no common support. The
second is a description with thin support and a collider caveat. They point the
same way.

It licenses no claim about Δ_R, which has never been estimated in a design where
the two cells share a length regime. That is what the pairwise-matrix screen is
for, and at screen scale even that will not license one.
