# The pairwise-matrix screen: every §8.1 cell, at screen scale

**Classification: NON-CONFIRMATORY DESIGN SCREEN.** It runs the registered
§8.1 cell set on screen topics with a reference set the calibration screen
selected, so it cannot meet the §17.3 precision preconditions and **licenses no
L1, L2 or L3 statement**. Per-model protocols, each hashed before that model
generated anything, at `reports/matrix_screen_v4/screen_protocol_<model>.json`.

---

## 1. What had never been measured

Four quantities that bear directly on the scientific question have never been
estimated in this constraint vocabulary by any stage of this study:

| quantity | why it was missing |
|---|---|
| `Δ_R = D(B←A) − mean_j D(B←R_j)` | the registered primary; needs B+R_j cells, which only the B+R pilot has, and there unpaired against a cross-set `D(B←A)` |
| `Ξ = Δ_R − [D(R̄←A) − D(R̄←R̄′)]` | needs reference-on-reference cells, which exist nowhere |
| `D(R_j←A)`, `D(R_j←B)` | the pilot has `D(R_j←B)`, paired within topic. `D(R_j←A)` needs a reference **solo** cell on the same topics as the A+R_j cell; v3 scores R_j in A+R_j but has no reference solo cell on its confirmatory topics, so the loss is not formable |
| the companion-difficulty → `D(B←companion)` relation | decision V5. Not merely unmeasured: **unidentifiable by construction** on a matched design — E2B's three v3 references have identical solo compliance to four decimal places, so the regressor has zero variance |

Check C12 records the A-versus-reference correlation ρ as `BLOCKED` and the
FORM × STEM report says the same from the other side: "This screen carries no
composed reference cells and does not supply it." Neither does any other
artifact. §13.6's Gate 4 will supply ρ one stage before the freeze needs it,
which is why ρ is **not** the reason this screen exists.

## 2. The two confounds this screen adds cells for

**Outcome specificity.** Ξ asks whether A's excess damage is specific to the
outcome B or is a property of A as a companion to anything. It needs the six
ordered reference-on-reference cells, and the full §8.1 matrix carries them.

**Companion class.** A is the only *production* constraint in the pool — it is
failed by writing less. B, all eight registered families and all three
candidate rate families are *budgets*. §13.2's caliper matches difficulty and
leaves class unmatched, so a positive Δ_R is equally consistent with "A damages
B" and with "a production companion damages a budget outcome". The class arm
adds the best-admitted lower-bound family, composed with both outcome
constraints in both orders, giving

    Δ_class = D(B←A) − D(B←CL)

with class held fixed and difficulty inside the same caliper.

## 3. The safeguard, stated before the numbers

The reference set, n\*, m\*, the spanning rungs and the class-matched companion
are **inputs** to this screen and **outputs** of the calibration screen. The
frozen per-model protocol carries the declaration verbatim: no reference
family, no reference severity, no n\*, no m\*, and no amendment may be revised,
reordered or reconsidered on any evidence this screen produces. §13.3 exists
because selecting a control on the outcome it is meant to counterfactual is
circular, and a pre-freeze screen is where that would happen unnoticed.

## 4. Precision, stated before the numbers

From the registered §16.1 variance model with its own planning constants
(`p(1−p) = 0.215`, ρ = 0.5, φ ∈ {0.27, 0.37}), pointwise 95% half-widths at
M = 4:

| blocks | `D(c←g)` | Δ_R | Ξ (conservative) |
|---:|---:|---:|---:|
| 384 (registered) | 0.037–0.038 | 0.033–0.035 | 0.062–0.065 |
| **120 (this screen)** | **0.066–0.069** | **0.059–0.063** | **0.111–0.116** |
| 24 (pre-screen only) | 0.148–0.154 | 0.133–0.141 | 0.248–0.259 |

So at 120 blocks Δ_R lands close to the registered §17.3 precondition of 0.05
and **Ξ does not**: its half-width is roughly 0.11, against thresholds of 0.10
and 0.25. **Ξ at this scale can show its sign and rough size and cannot settle
outcome specificity.** That sentence belongs in the verdict, not a footnote —
calling a hypothesis from an interval that wide is the failure mode the FORM ×
STEM screen's own terminal-status call demonstrated.

The registered precision needs the 384 confirmatory blocks, and those cannot be
opened before Gate 5.

## 5. Topics, and the decision behind them

120 blocks: the 24 pre-screen topics and the 96 solo-calibration topics.
**The 24 composed-validation topics are excluded** — §13.6 evaluates every
registered composed cell type on exactly those topics at exactly this M_cal, so
generating composed cells there first would make Gate 4 a check of cells it had
already seen and `COMPOSED_HEADROOM_FAILURE` unfalsifiable. The 384 confirmatory
topics are reserved and the 96 sequestered topics are inaccessible by
construction.

Using the solo-calibration topics for **composed** cells is outside §6.2's
literal wording even for a non-registered screen, and the frozen protocol
records the basis in full: the registered gate code was read and no gate reads a
composed cell from that set (`gates.gate2_payload` takes only solo quantities;
`gates.admit_family`'s own docstring says its calibration argument is "per-topic
solo-compliance cell means"; Gate 4, the one stage that reads composed cells,
runs on the composed-validation set); a second session working the Gate 1 track
traced the same code independently and agreed; and that session reports its user
ratified it conditional on the no-revision bar being in the frozen protocol,
which it is. **That ratification reached this screen relayed by a peer session
rather than directly, and is recorded as such.**

The screen is built so the ratification is not load-bearing: every quantity is
reported on the 24 pre-screen blocks alone as well as on all 120, the pre-screen
half needs no ratification, the pre-screen blocks are **disjoint from the 96 the
reference severities were selected on**, and `evidence/matrix-screen-v4` can be
deleted without touching anything else.

## 6. The cell set, per block

| arm | cells | why |
|---|---:|---|
| §25 unconstrained | 1 | accidental compliance: the rate at which an answer carrying no constraint satisfies each one by chance. Without it a compliance of 0.7 cannot be read as delivery |
| §8.1 solo | 5 | A, B, R₁, R₂, R₃ |
| §8.1 composed | 20 | ten unordered pairs, both orders, order within block |
| V5 spanning | 4 | two rungs of one rate family at −0.25 and +0.20 of A's compliance, each solo and composed with B, **B stated first** so the loss is position-matched to B's solo cell (§11.4) |
| class control | 5 | the best-admitted lower-bound family: solo, and composed with **both** outcome constraints in both orders |

Wording allocation is §8.4 verbatim — `i mod 4` for the first constituent in the
registered order and `(i + ⌊i/4⌋) mod 4` for the second, applied identically to
both order variants — and `assert_allocation` refuses a plan with a structural
zero or an unbalanced order.

The three **R slots are drawn from the budget families** in §13.2's own order
and the lower-bound families are reserved for the class arm: a lower-bound
reference would make Δ_R itself a mixed-class contrast and would blur the exact
distinction the class arm draws.

**The spanning arm is drawn from a rate family, not from the admitted
references.** A spanning companion is by definition *not* difficulty-matched, so
§13.2's caliper does not apply to it; it needs a measured calibration curve, low
solo vacuity, valid wordings and certified witnesses, which the three rate
families have over their full ladders on every model. Drawing it from the
admitted set instead would leave gemma-3n-E4B with no difficulty axis at all,
because all three of its admitted references are registered families carrying
only the three-rung §12.2 shortlist, whose compliances differ by a few points.
One family is used rather than three, chosen for the widest measured span that
brackets A's compliance, which keeps the arm at four cells per block and keeps
the difficulty regression from being dominated by whichever family has the
longest ladder.

**With one fallback, applied per model and recorded on its protocol.** Where
reserving a lower-bound family would leave fewer than three budget references,
§13.2's plain ordering is used instead and the lower-bound family takes an R
slot. Nothing is lost from the class question when that happens: that
reference's own **Δ_j = D(B←A) − D(B←CL) *is* the class contrast**. What is lost
is `D(A←CL)` and the two reciprocal directions the dedicated arm adds, and Δ_R
for that model then averages over one production and two budget companions
rather than three budgets — which is stated wherever that model's Δ_R appears.

Joint satisfiability and both non-entailment directions are certified for every
pair that actually co-occurs in a cell — by the study's own constructor where it
reaches, and from the model's own calibration-screen generations where it does
not. A real response that satisfies one constraint and fails the other is a
machine-verified non-entailment witness and a stronger one than an authored
string. `verify_candidate_pair` is bounded to A and B, because outside that
envelope its "candidate satisfied, other failed" branch appends a long word —
which fails B and says nothing about a reference family — and reports the
construction failure as an apparent entailment.

## 7b. How the numbers will be read, fixed before they exist

Written before any matrix cell was scored, so the reading is not chosen to fit
the result. The registered thresholds are §11.6's: **0.10** generic load,
**0.25** pair-specific, both from `dci-construct-pass2.md` §G row 1 and both
predating every observation in this constraint vocabulary.

| pattern | reading |
|---|---|
| Δ_R's interval lies entirely **above 0.25**, Ξ positive, Δ_class positive | the strongest pattern the design can produce; at this scale it is **still not an L3 claim**, and it would justify the confirmatory run rather than substitute for it |
| Δ_R positive but **Ξ ≈ 0 or negative** | A damages the references about as much as it damages B: an **A-general / constraint-class disruption** reading, not an A–B pair-specific one |
| Δ_R positive but **Δ_class ≈ 0** | the excess belongs to the **production class**, not to A. Note the residual: it would not license "A is interchangeable with any production companion", because A is two-sided and the class control is one-sided |
| A's **residual from the difficulty line ≈ 0** | companion difficulty is the better-supported account and the matched design was hiding it |
| A's **residual from the length line ≈ 0**, or Δ_R collapses under §17.4 | the structural/length channel, not semantic pair specificity |
| Δ_R's interval lies entirely **within ±0.10** | equivalence under the registered conditions, at this precision |
| Δ_R's interval **spans a threshold** | **unresolved at the achieved precision** — which, given §4's projected half-widths, is the outcome the design should be expected to produce for Ξ regardless of the truth |

**And §17.4's own decision rule governs all of them.** Its last sentence:
"a claim is licensed only when the primary and the vacuity-forced recomputation
license the same claim; otherwise **the axis is reported unresolved** with both
bounds." So every row above is conditional on the compliance-scale and
vacuity-forced readings agreeing; where they do not, the axis is unresolved by
rule and both bounds are reported. Under the floored stem the calibration cells
run 0.000–0.060 vacuity, so the two are expected to coincide — but that is a
prediction, and §17.4 decides it, not this table.

Two quantities are read **only** as sign-and-rough-size and never against a
threshold: **Ξ**, whose half-width here is ~0.11, and **ρ**, which is a planning
input for §16.1 and not an estimand.

Per-reference disagreement is reported and never averaged away: §13.4 registers
the heterogeneity qualifier, and v3's own Δ^A components on E2B were +0.056,
+0.142 and −0.006 — a case where the pooled number described none of the three.

## 8. What this screen cannot decide, stated before its numbers

- **No L1, L2 or L3 statement.** §17.3's precision preconditions need 384
  blocks. `claim_licensed` is `False` on the artifact by construction.
- **Outcome specificity.** Ξ's half-width here is ~0.11 against thresholds of
  0.10 and 0.25. It can show sign and rough size. It cannot separate
  "A is unusually damaging to B" from "A is a broadly damaging companion".
- **Anything about a different reference set.** If the real Gate 3 admits
  different families or severities, every per-reference number here is about
  constraints that are not in the study. The *structural* conclusion — whether
  the design identifies what it claims — survives that; the per-reference
  numbers do not.
- **Δ_R's own reference-set uncertainty.** Δ_R is a companion swap, so it moves
  with which references are swapped between. At this scale the honest claim is
  about the sign and rough size of the swap **for these references**.
- **A residual in Δ_class.** A is *exactly-n* and two-sided; the class control is
  *at-least-q* and one-sided. Δ_class ≈ 0 licenses "the excess belongs to the
  production class", not "A is interchangeable with any production companion".
- **Length as a causal channel.** The length diagnostics here are
  across-companion descriptions. §22 forbids conditioning the primary estimand
  on response length and nothing below does.
- **Anything registered.** Gate 1 is not approved, no verifier hash is frozen,
  no freeze record exists, and none of these rows may enter a v4 estimator.

## 7. The design each model actually ran

| model | A | B | R₁ | R₂ | R₃ | class C₁ | spanning | cells/block | generations |
|---|---|---|---|---|---|---|---|---:|---:|
| E2B | A:7 | B:10 | CR6:7 | RF3:4 | RF2:6 | CL7:80 | CR4:9, CR4:13 | 35 | 16,800 |
| E4B | A:6 | B:9 | RF8:8 | RF3:4 | RF2:8 | CL8:25 | CR4:11, CR4:15 | 35 | 16,800 |
| Qwen3-4B | A:2 | B:12 | CR7:44 | CL8:5 | RF7:24 | **none** | CR4:11, CR4:15 | 30 | 14,400 |
| Qwen3-4B-Inst | A:5 | B:10 | CR7:44 | RF1:5 | RF7:24 | CL8:10 | CR6:6, CR6:8 | 35 | 16,800 |

Protocol hashes, frozen before each model generated anything: E2B `54d5d61c60b2…`, E4B `ba2b12d82497…`, Qwen3-4B `78733f69c99a…`, Qwen3-4B-Inst `931cae4a5935…`.

**qwen3-4b is the one model with no dedicated class arm.** Only two budget
families cleared §13.2 for it, so reserving the lower-bound family would have
cost it a third reference; §13.2's plain ordering puts CL8:5 in the R₂ slot
instead. Its **Δ_R₂ is the class contrast**, and its Δ_R averages over one
production and two budget companions — stated wherever that number appears.

Every pair that co-occurs in a cell is certified: 14 pairs on three models, 12
on qwen3-4b, all proved.


---

# Results

64,800 generations, four models, every §8.1 cell in both orders, M = 4 draws,
120 blocks (24 pre-screen + 96 solo), floored stem, 10,000 block-bootstrap
resamples. `claim_licensed` is `False` on every artifact by construction (§8).

## 9. What the matrix found

### 9.1 The primary axis is *resolved*, and it reads as equivalence

| model | D(B←A) | D(A←B) | Λ | Δ_R | Δ_R reading |
|---|---|---|---|---|---|
| E2B | +0.086 [+0.031, +0.143] | +0.178 [+0.114, +0.242] | -0.092 [-0.177, -0.005] | +0.048 [+0.009, +0.087] | entirely below the generic-load threshold |
| E4B | +0.228 [+0.174, +0.282] | +0.223 [+0.167, +0.279] | +0.005 [-0.071, +0.080] | +0.101 [+0.056, +0.146] | spans at least one threshold |
| Qwen3-4B | -0.039 [-0.085, +0.009] | +0.357 [+0.296, +0.419] | -0.396 [-0.470, -0.322] | +0.011 [-0.020, +0.044] | entirely below the generic-load threshold |
| Qwen3-4B-Inst | -0.095 [-0.151, -0.040] | -0.055 [-0.129, +0.019] | -0.040 [-0.126, +0.047] | -0.024 [-0.067, +0.019] | entirely below the generic-load threshold |

Read against §7b's table, fixed before these numbers existed:

| model | Δ_R | §7b reading |
|---|---|---|
| E2B | +0.048 [+0.009, +0.087] | interval lies entirely **within ±0.10** → **equivalence** under the registered conditions, at this precision |
| E4B | +0.101 [+0.056, +0.146] | interval **spans 0.10** → **unresolved at the achieved precision** |
| Qwen3-4B | +0.011 [−0.020, +0.044] | entirely within ±0.10 → **equivalence** |
| Qwen3-4B-Inst | −0.024 [−0.067, +0.019] | entirely within ±0.10 → **equivalence** |

**On no model does Δ_R approach the 0.25 pair-specific threshold**, and on no
model does its interval include it. The largest point estimate in the study,
E4B's +0.101, sits at the generic-load threshold with an interval that contains
it.

**And §17.4's decision rule is satisfied rather than violated.** The rule is
that "a claim is licensed only when the primary and the vacuity-forced
recomputation license the same claim". Here they do, on all four models: Δ_R
under forcing is +0.048, +0.101, +0.007, −0.053 against +0.048, +0.101, +0.011,
−0.024 on the compliance scale, and every pair lands in the same §7b row. This
is the **first time in the study that the primary axis has been resolved by that
rule** — the FORM × STEM screen under the *registered* stem failed it, taking
E2B's `D(B←A)` from +0.375 to +0.000 and reversing sign on both Qwens. The
difference is the floored stem: calibration vacuity runs 0.000–0.060 here, and
§7b predicted in advance that the two scales would therefore coincide.

So the reading is not "we could not tell". It is that under these conditions,
at this precision, swapping A for a genuinely comparable companion moves focal
compliance by **less than the study's own generic-load threshold**, on three of
four models, on both scales.

### 9.2 A is *less* disruptive than a class-matched production companion

The class arm is the cell the study had never run: a companion that is a
**production** constraint like A rather than a prefix-closed budget like B and
the references.

| model | companion | D(B←A) | D(B←CL) | **Δ_class** | D(A←CL) | D(CL←A) | D(CL←B) |
|---|---|---|---|---|---|---|---|
| E2B | ['CL7', 80] | +0.086 [+0.031, +0.143] | +0.601 [+0.544, +0.657] | **-0.515 [-0.564, -0.464]** | +0.310 [+0.245, +0.377] | -0.285 [-0.344, -0.230] | -0.002 [-0.055, +0.050] |
| E4B | ['CL8', 25] | +0.228 [+0.174, +0.282] | +0.632 [+0.578, +0.686] | **-0.404 [-0.453, -0.355]** | +0.245 [+0.176, +0.310] | +0.138 [+0.073, +0.201] | -0.226 [-0.289, -0.166] |
| Qwen3-4B | — | | | | | | |
| Qwen3-4B-Inst | ['CL8', 10] | -0.095 [-0.151, -0.040] | -0.182 [-0.244, -0.124] | **+0.087 [+0.046, +0.130]** | +0.029 [-0.046, +0.104] | +0.181 [+0.113, +0.252] | -0.024 [-0.098, +0.050] |

`Δ_class = D(B←A) − D(B←CL)` is **strongly negative on both Gemmas**: a
one-sided lower-bound production companion costs B **+0.601** and **+0.632** of
its compliance, where A costs **+0.086** and **+0.228**. A is not the disruptive
member of its class; it is five- to seven-fold *gentler* than the other
production constraint tested. On Qwen3-4B-Inst Δ_class is **+0.087
[+0.046, +0.130]** — positive, but inside the equivalence band, and sitting on
top of a `D(B←A)` that is itself negative.

§7b anticipated the "Δ_class ≈ 0" case and warned that even then the residual
would not license "A is interchangeable with any production companion", because
A is two-sided and the control is one-sided. That caution applies with more
force here: what the arm shows is that **constraint class moves focal compliance
by 0.4–0.6 while companion identity within a class moves it by ~0.05–0.10**.
The confound §2 was built to expose is real, and it is an order of magnitude
larger than the effect the study was designed to detect.

### 9.3 A's excess over the difficulty line is real; the length line cannot test A at all

§7b: "A's **residual from the length line ≈ 0** … the structural/length channel,
not semantic pair specificity." That row **cannot be evaluated on this companion
set**, and the reason is itself the finding.

Both lines are fitted on the budget companions and then used to predict A. A is
excluded from each fit — a line fitted *through* the point it is used to predict
answers a different question, and shrinks A's residual toward zero by
construction whenever A carries leverage.

| model | difficulty residual | A inside fitted range? | length residual | A inside fitted range? |
|---|---:|:--:|---:|:--:|
| E2B | **+0.067** | yes, [+0.335, +0.735] ∋ +0.562 | −0.117 | **NO** — others [−9, −1], A **+15** |
| E4B | **+0.118** | yes, [+0.531, +0.838] ∋ +0.719 | +0.126 | **NO** — others [−8, −3], A **+8** |
| Qwen3-4B | **−0.050** | yes, [+0.494, +0.829] ∋ +0.710 | −0.012 | **NO** — others [−5, +4], A **−8** |
| Qwen3-4B-Inst | **−0.048** | yes, [+0.173, +0.790] ∋ +0.592 | +0.024 | **NO** — others [−10, −1], A **−16** |

**The difficulty residual is identified.** A's solo compliance sits inside the
range the other companions span on all four models, so the line interpolates to
A rather than extrapolating. A sits **above** the difficulty line by +0.067 on
E2B and **+0.118** on E4B — the latter above the 0.10 generic-load threshold —
and **below** it on both Qwens. Companion difficulty alone does not account for
A on the Gemmas, and over-accounts for it on the Qwens.

**The length residual is not identified, on any model.** A's length shift lies
outside the range every other companion spans, every time. A is the only
companion in the pool that substantially changes response length — it lengthens
by 15 and 8 words on the Gemmas and shortens by 8 and 16 on the Qwens, where no
other companion moves by more than 10 in either direction and all of them sit on
one side of A. A line fitted on that range does not predict A; it extrapolates to
A, and the residual it produces is an artefact of the slope's extrapolation, not
a measurement.

**So companion identity and length shift are collinear across this companion
set** — the same collinearity the B+R pilot showed between its two arms, now
shown to hold *within* the matrix design across companions. The length account of
A can be neither confirmed nor refuted here. Testing it needs a companion that
lengthens responses about as much as A does without being A, and the pool
contains none: the class control C₁ is the only other lengthener and it belongs
to the class arm, where it is doing different work.

**This corrects an earlier reading of this same screen.** The first pass fitted
both lines *including* A and reported A's length residual as ±0.010 on all four
models, concluding that the length channel accounted for A entirely. With A in
the fit and A the only point in its region, the line was effectively pinned to A
and the residual was near zero by construction. The corrected residuals are
−0.117 to +0.126 and, more to the point, unidentified. The difficulty residuals
moved less — +0.055/+0.098 to +0.067/+0.118 — because A is genuinely inside that
fit's support.

### 9.4 Ξ is negative on the Gemmas, and positive on the Qwens for the wrong reason

§7b reads Ξ as sign-and-rough-size only, never against a threshold.


On **E2B (−0.036) and E4B (−0.009)** Ξ is zero or negative, which is §7b's
"A damages the references about as much as it damages B" row: an **A-general /
constraint-class disruption** reading, not an A–B pair-specific one. E2B is the
clearest case — A costs the reference set **+0.179** and costs B **+0.086**.
A is a worse companion for the references than it is for B.

On **Qwen3-4B (+0.131) and Qwen3-4B-Inst (+0.090)** Ξ is positive, and it would
be a mistake to read that as support. Ξ = Δ_R − [D(R̄←A) − D(R̄←R̄′)], and on
these two models the bracket is negative because **A improves reference
compliance** (D(R̄←A) = −0.095 and −0.180). Ξ is positive there not because A
specifically damages B, but because A specifically *helps the references* — and
`D(B←A)` on those same models is **−0.039** and **−0.095**, i.e. A does not
damage B at all. Outcome specificity computed where the focal loss is itself
null or negative is not evidence for the claim; it is a statement about the
reference side.

The §25 unconstrained cell explains part of why. Accidental compliance is
**0.000 for A on all four models**, 0.000–0.013 for B on three, and **0.52–0.89
for the references**. The reference outcomes are near-ceiling — largely
satisfied without ever being asked — so reference-side "delivery loss" is
measured against a saturated outcome and A's apparent "help" is partly headroom.
That is a property of the admitted reference pool, and it is the same
prefix-closure asymmetry §2 identified.

### 9.5 The focal constraint's *position* matters more than the companion's identity

This is the largest effect in the screen and it was not what the screen was
built to find.

Δ_R computed **within a single order configuration** is not the same quantity in
the two configurations, because §8.4's registered order puts B *second* in the
A-cell and *first* in the R-cells under `registered_first`, and swaps both under
`registered_second`. So a single-order Δ_R contrasts cells in which the focal
constraint occupies different positions:

| model | Δ_R registered-first | Δ_R registered-second | contrast | Δ_R pooled |
|---|---|---|---|---|
| E2B | +0.326 [+0.265, +0.389] | −0.231 [−0.287, −0.174] | +0.558 | **+0.048** |
| E4B | +0.450 [+0.383, +0.516] | −0.249 [−0.313, −0.185] | +0.699 | **+0.101** |
| Qwen3-4B | +0.083 [+0.043, +0.126] | −0.060 [−0.100, −0.022] | +0.142 | **+0.011** |
| Qwen3-4B-Inst | +0.035 [−0.023, +0.095] | −0.083 [−0.133, −0.033] | +0.118 | **−0.024** |

**Δ_R changes sign with presentation order on all four models**, and on the
Gemmas the single-order estimate exceeds the 0.25 pair-specific threshold in one
direction and the equivalence band in the other. A single-order study of this
pair would have reported a decisive pair-specific effect — of whichever sign its
order happened to produce.

The mechanism is a position effect on the focal constraint itself, measured
directly across all composed cells pooled over companions:

| model | B first | B second | position effect | A first | A second | position effect |
|---|---:|---:|---:|---:|---:|---:|
| E2B | 0.856 | 0.568 | **+0.288** | 0.385 | 0.425 | −0.040 |
| E4B | 0.785 | 0.435 | **+0.350** | 0.581 | 0.533 | +0.048 |
| Qwen3-4B | 0.877 | 0.830 | +0.047 | 0.440 | 0.503 | −0.063 |
| Qwen3-4B-Inst | 0.801 | 0.744 | +0.056 | 0.573 | 0.586 | −0.012 |

B loses **0.29–0.35 of its compliance on the Gemmas purely by being stated
second**, against a companion-identity effect of 0.05–0.10. A shows essentially
no position effect on any model (|effect| ≤ 0.063). The asymmetry is itself
class-structured: the constraint whose satisfaction depends on the whole
response is the one that suffers from being read last.

§8.1's requirement that both orders be generated is therefore not a robustness
nicety in this construct — **it is what makes Δ_R a well-defined quantity at
all**. Pooled Δ_R balances the focal constraint's position; a single-order Δ_R
does not.

### 9.6 Per-reference heterogeneity, and the selection-clean subgroup

§13.4 registers the heterogeneity qualifier and §7b commits to reporting
per-reference disagreement rather than averaging it away. It is substantial:

| model | Δ_R1 | Δ_R2 | Δ_R3 |
|---|---|---|---|
| E2B | −0.078 [−0.134, −0.023] | +0.131 [+0.076, +0.187] | +0.090 [+0.032, +0.147] |
| E4B | +0.102 [+0.045, +0.159] | +0.178 [+0.117, +0.239] | +0.022 [−0.044, +0.088] |
| Qwen3-4B | −0.005 [−0.055, +0.045] | +0.044 [+0.008, +0.080] | −0.004 [−0.051, +0.043] |
| Qwen3-4B-Inst | −0.015 [−0.069, +0.040] | −0.005 [−0.060, +0.050] | −0.053 [−0.118, +0.012] |

On E2B the three components are **−0.078, +0.131, +0.090** — they do not share a
sign, and the pooled +0.048 describes none of them. This repeats v3's pattern
(+0.056, +0.142, −0.006) on a different reference set. Δ_R is a swap against
*these three* references and moves with which three they are; §8's limitation on
reference-set uncertainty is the operative one.

**And the swaps hide which side moved.** Δ_j is a difference of two losses, so
the same Δ_j can mean "A damages B" or "R_j helps B". The levels separate them:

| model | reference set | D(B←A) | D(B←R₁) | D(B←R₂) | D(B←R₃) |
|---|---|---|---|---|---|
| E2B | CR6:7, RF3:4, RF2:6 | +0.086 [+0.031, +0.143] | **+0.165 [+0.121, +0.207]** | −0.045 [−0.099, +0.008] | −0.003 [−0.055, +0.047] |
| E4B | RF8:8, RF3:4, RF2:8 | +0.228 [+0.174, +0.282] | +0.126 [+0.079, +0.172] | +0.050 [+0.003, +0.097] | +0.206 [+0.151, +0.261] |
| Qwen3-4B | CR7:44, CL8:5, RF7:24 | −0.039 [−0.085, +0.009] | −0.033 [−0.075, +0.007] | −0.082 [−0.128, −0.037] | −0.034 [−0.077, +0.009] |
| Qwen3-4B-Inst | CR7:44, RF1:5, RF7:24 | −0.095 [−0.151, −0.040] | −0.080 [−0.128, −0.032] | −0.090 [−0.141, −0.041] | −0.042 [−0.094, +0.009] |

**On E2B a registered-pool reference damages B more than A does.** CR6:7 costs B
**+0.165** where A costs +0.086, and the intervals do not overlap. E2B's Δ_R is
positive only because the other two references *help* B slightly. On E4B, RF2:8
costs +0.206 against A's +0.228 — statistically hard to separate. So on both
Gemmas there exists an admitted companion at least as damaging to B as A is, and
on E2B one strictly more damaging.

That is the single most direct evidence against a pair-specific reading: if A
were interfering with B by virtue of *what A is*, an equally-matched companion
drawn from the registered pool should not out-damage it.

The **selection-clean subgroup** — the 24 pre-screen blocks, which played no
part in choosing n\*, m\* or the reference set — agrees in sign and size with
the full 120 everywhere, at roughly half the precision: Δ_R = +0.059, +0.122,
+0.012, −0.075. Nothing in the main result depends on topics that informed
selection.

### 9.7 Achieved precision against §4's projection

§4 projected, from §16.1's variance model at 120 blocks, half-widths of
0.059–0.063 for Δ_R and **0.111–0.116 for Ξ**. Achieved: **0.032–0.045** for
Δ_R and **0.037–0.055** for Ξ — roughly half the projected width in both cases.
The measured intra-block correlation is ρ = 0.53–0.69 against the 0.5 the model
assumed, and the projection is conservative in φ.

This does **not** promote any reading. §7b restricts Ξ to sign and rough size on
grounds of what the quantity can distinguish, not only on grounds of width, and
§8's limitations — 120 blocks, calibration topics, provisional reference set —
are unaffected by the interval being narrower than expected. It is recorded
because §4 stated the projection before the numbers and the numbers should be
held against it.

## 10. What the screen supports, and what it does not

**It is a screen.** Calibration topics, 120 blocks, floored stem, Gate 1 not
approved, no verifier hash frozen, no freeze record. Nothing here is L1, L2 or
L3; nothing here may enter a v4 estimator; `claim_licensed` is `False` on every
artifact. It cannot confirm the DCI claim and it cannot falsify a confirmatory
result, because no confirmatory result exists to falsify.

What it can do is tell the study whether its primary estimand identifies what it
claims to identify, on data generated under the design's own rules. On that
question it is informative, and the answer is unfavourable in a specific way:

1. **Δ_R is small everywhere and resolved on three of four models.** Entirely
   within ±0.10 on E2B, Qwen3-4B and Qwen3-4B-Inst; spanning 0.10 on E4B; never
   near 0.25; and the compliance and §17.4-forced scales agree on all four, so
   §17.4 licenses the reading rather than voiding it.
2. **The excess that does exist is not explained by companion difficulty, and
   the length account cannot be tested here.** A sits above the difficulty line
   by +0.067 (E2B) and +0.118 (E4B) — identified, because A is inside that
   fit's support — and below it on both Qwens. A's length shift lies *outside*
   the range every other companion spans, on all four models, so the length line
   extrapolates to A and its residual is not identified. Companion identity and
   length shift are collinear across this companion set.
3. **Constraint class dominates companion identity by an order of magnitude.**
   0.40–0.60 for the class contrast against 0.05–0.10 for identity — and with
   the sign showing A to be the *gentler* production companion.
4. **Focal position dominates it too, on the models where anything moves.**
   0.29–0.35 for B's position against 0.05–0.10 for identity, and Δ_R changes
   sign with order on all four models.
5. **An admitted reference out-damages A on E2B.** `D(B←CR6:7)` is **+0.165**
   against A's +0.086, intervals disjoint; on E4B `D(B←RF2:8)` is +0.206 against
   +0.228. A is not the most damaging companion its own reference pool contains.

Points 3–5 are rival explanations §2 and §7b named in advance — constraint
class, order, reference heterogeneity — and each is larger than the effect the
study is powered to detect. Point 2 is worse than a rival explanation: it is a
**non-identification**. That is the screen's central finding. Not merely that
Δ_R is small, but that **two nuisance channels each move focal compliance more
than companion identity does, a third is collinear with identity and cannot be
separated from it on this companion set, and a pool reference out-damages A**.
A confirmatory design that does not fix all of this would measure it instead.

**What would change the reading.** Δ_R here is a swap against three specific
references; §9.6 shows the per-reference components do not share a sign on E2B.
A Gate 3 admitting a different reference set could produce a different Δ_R, and
this screen does not bound that. The structural findings — class and position —
do not depend on the reference set in the same way, because they are measured
against controls the reference set does not enter. The length non-identification
is a property of the companion set and would be repaired only by adding a
companion that lengthens like A without being A.

**What it means for the confirmatory design.** Every one of the four points
above is a design requirement rather than a result: both orders are mandatory
(§8.1 already requires them, and §9.5 shows why), a class-matched companion
belongs in the reference pool or the class confound stays unresolved, and the
reference pool needs at least one companion matched to A on **length shift** or
the length channel stays unidentified no matter how many blocks are run —
§22's mediator treatment reports length, it does not identify it. None of that is a decision this agent can take; all of it is Gate 1
material.

---

## Appendix A. Full estimand tables

Generated by `tools/matrix_screen_report_v4.py --resamples 10000` from
`reports/matrix_screen_v4/results.json`. Intervals are percentile block
bootstrap; per-reference intervals are studentised simultaneous within family.

### Constraint sets and design

| model | design | A | B | R1 | R2 | R3 | blocks |
|---|---|---|---|---|---|---|---:|
| E2B | §8.1 full matrix | A:7 | B:10 | CR6:7 | RF3:4 | RF2:6 | 120 |
| E4B | §8.1 full matrix | A:6 | B:9 | RF8:8 | RF3:4 | RF2:8 | 120 |
| Qwen3-4B | §8.1 full matrix | A:2 | B:12 | CR7:44 | CL8:5 | RF7:24 | 120 |
| Qwen3-4B-Inst | §8.1 full matrix | A:5 | B:10 | CR7:44 | RF1:5 | RF7:24 | 120 |

### Primary estimands, pooled over orders (compliance scale)

| model | D(B←A) | D(A←B) | Λ | Δ_R | Δ_R reading |
|---|---|---|---|---|---|
| E2B | +0.086 [+0.031, +0.143] | +0.178 [+0.114, +0.242] | -0.092 [-0.177, -0.005] | +0.048 [+0.009, +0.087] | entirely below the generic-load threshold |
| E4B | +0.228 [+0.174, +0.282] | +0.223 [+0.167, +0.279] | +0.005 [-0.071, +0.080] | +0.101 [+0.056, +0.146] | spans at least one threshold |
| Qwen3-4B | -0.039 [-0.085, +0.009] | +0.357 [+0.296, +0.419] | -0.396 [-0.470, -0.322] | +0.011 [-0.020, +0.044] | entirely below the generic-load threshold |
| Qwen3-4B-Inst | -0.095 [-0.151, -0.040] | -0.055 [-0.129, +0.019] | -0.040 [-0.126, +0.047] | -0.024 [-0.067, +0.019] | entirely below the generic-load threshold |

### Per-reference swap Δ_j (simultaneous within family)

| model | Δ_R1 | Δ_R2 | Δ_R3 |
|---|---|---|---|
| E2B | -0.078 [-0.134, -0.023] | +0.131 [+0.076, +0.187] | +0.090 [+0.032, +0.147] |
| E4B | +0.102 [+0.045, +0.159] | +0.178 [+0.117, +0.239] | +0.022 [-0.044, +0.088] |
| Qwen3-4B | -0.005 [-0.055, +0.045] | +0.044 [+0.008, +0.080] | -0.004 [-0.051, +0.043] |
| Qwen3-4B-Inst | -0.015 [-0.069, +0.040] | -0.005 [-0.060, +0.050] | -0.053 [-0.118, +0.012] |

### Focal losses against each companion, D(B<-x)

| model | D(B<-A) | D(B<-R1) | D(B<-R2) | D(B<-R3) |
|---|---|---|---|---|
| E2B | +0.086 [+0.031, +0.143] | +0.165 [+0.121, +0.207] | -0.045 [-0.099, +0.008] | -0.003 [-0.055, +0.047] |
| E4B | +0.228 [+0.174, +0.282] | +0.126 [+0.079, +0.172] | +0.050 [+0.003, +0.097] | +0.206 [+0.151, +0.261] |
| Qwen3-4B | -0.039 [-0.085, +0.009] | -0.033 [-0.075, +0.007] | -0.082 [-0.128, -0.037] | -0.034 [-0.077, +0.009] |
| Qwen3-4B-Inst | -0.095 [-0.151, -0.040] | -0.080 [-0.128, -0.032] | -0.090 [-0.141, -0.041] | -0.042 [-0.094, +0.009] |

### Reciprocal / outcome-specificity

| model | D(R̄←A) | D(R̄←B) | D(R̄←R̄′) | Ξ | Ξ half-width |
|---|---|---|---|---|---:|
| E2B | +0.179 [+0.135, +0.223] | +0.040 [-0.005, +0.084] | +0.095 [+0.065, +0.125] | -0.036 [-0.082, +0.010] | 0.046 |
| E4B | +0.073 [+0.018, +0.128] | -0.101 [-0.152, -0.050] | -0.036 [-0.071, -0.001] | -0.009 [-0.063, +0.047] | 0.055 |
| Qwen3-4B | -0.095 [-0.125, -0.065] | -0.013 [-0.048, +0.024] | +0.024 [-0.005, +0.053] | +0.131 [+0.094, +0.167] | 0.037 |
| Qwen3-4B-Inst | -0.180 [-0.221, -0.137] | -0.176 [-0.227, -0.123] | -0.065 [-0.102, -0.029] | +0.090 [+0.038, +0.142] | 0.052 |

### Reference-side losses

| model | D(R1←A) | D(R2←A) | D(R3←A) | D(R1←B) | D(R2←B) | D(R3←B) |
|---|---|---|---|---|---|---|
| E2B | +0.379 [+0.309, +0.448] | +0.220 [+0.164, +0.278] | -0.061 [-0.121, -0.003] | +0.451 [+0.377, +0.523] | +0.004 [-0.054, +0.062] | -0.336 [-0.401, -0.272] |
| E4B | +0.098 [+0.015, +0.181] | +0.222 [+0.171, +0.274] | -0.101 [-0.177, -0.025] | -0.169 [-0.243, -0.096] | +0.090 [+0.041, +0.138] | -0.223 [-0.304, -0.142] |
| Qwen3-4B | -0.144 [-0.189, -0.099] | +0.056 [+0.001, +0.110] | -0.199 [-0.259, -0.140] | -0.075 [-0.130, -0.021] | +0.126 [+0.060, +0.194] | -0.090 [-0.157, -0.022] |
| Qwen3-4B-Inst | -0.180 [-0.239, -0.123] | -0.053 [-0.145, +0.039] | -0.305 [-0.373, -0.239] | -0.232 [-0.301, -0.164] | -0.022 [-0.121, +0.079] | -0.273 [-0.342, -0.205] |

### Order

| model | Δ_R registered-first | Δ_R registered-second | contrast |
|---|---|---|---|
| E2B | +0.326 [+0.265, +0.389] | -0.231 [-0.287, -0.174] | +0.558 [+0.469, +0.648] |
| E4B | +0.450 [+0.383, +0.516] | -0.249 [-0.313, -0.185] | +0.699 [+0.604, +0.790] |
| Qwen3-4B | +0.083 [+0.043, +0.126] | -0.060 [-0.100, -0.022] | +0.142 [+0.096, +0.193] |
| Qwen3-4B-Inst | +0.035 [-0.023, +0.095] | -0.083 [-0.133, -0.033] | +0.118 [+0.053, +0.183] |

### §17.4 vacuity-forced recomputation

| model | Δ_R (compliance) | Δ_R (vacuity forced) | D(B←A) compliance | D(B←A) forced |
|---|---|---|---|---|
| E2B | +0.048 [+0.009, +0.087] | +0.048 [+0.009, +0.087] | +0.086 [+0.031, +0.143] | +0.086 [+0.031, +0.143] |
| E4B | +0.101 [+0.056, +0.146] | +0.101 [+0.056, +0.146] | +0.228 [+0.174, +0.282] | +0.228 [+0.174, +0.282] |
| Qwen3-4B | +0.011 [-0.020, +0.044] | +0.007 [-0.025, +0.040] | -0.039 [-0.085, +0.009] | -0.043 [-0.090, +0.005] |
| Qwen3-4B-Inst | -0.024 [-0.067, +0.019] | -0.053 [-0.101, -0.006] | -0.095 [-0.151, -0.040] | -0.126 [-0.188, -0.067] |

### V5 companion difficulty, and the length channel

Lines are fitted on the budget companions **excluding A**, then used to predict A.
A residual is only meaningful where A's predictor value lies inside the fitted range.

| model | slope (difficulty) | A observed | A predicted | **A residual** | A in support | slope (length) | **A residual (length)** | A in support | rho mean |
|---|---:|---:|---:|---:|:--:|---:|---:|:--:|---:|
| E2B | +0.025 | -0.044 | -0.110 | **+0.067** | yes | +0.0089 | **-0.117** | **NO** | 0.529 |
| E4B | -0.100 | +0.054 | -0.064 | **+0.118** | yes | -0.0007 | **+0.126** | **NO** | 0.528 |
| Qwen3-4B | -0.068 | -0.098 | -0.047 | **-0.050** | yes | +0.0065 | **-0.012** | **NO** | 0.691 |
| Qwen3-4B-Inst | -0.060 | -0.127 | -0.079 | **-0.048** | yes | +0.0065 | **+0.024** | **NO** | 0.562 |

Fitted ranges, and where A sits:

| model | difficulty: others range | A | length: others range | A |
|---|---|---:|---|---:|
| E2B | [+0.335, +0.735] | +0.562 | [-9, -1] | +15 |
| E4B | [+0.531, +0.838] | +0.719 | [-8, -3] | +8 |
| Qwen3-4B | [+0.494, +0.829] | +0.710 | [-5, +4] | -8 |
| Qwen3-4B-Inst | [+0.173, +0.790] | +0.592 | [-10, -1] | -16 |

### V5 points

#### E2B

| companion | arm | companion solo | D(B←companion) | length shift |
|---|---|---:|---:|---:|
| A | matched | 0.562 | -0.044 | 15 |
| R1 | matched | 0.644 | -0.062 | -1 |
| R2 | matched | 0.644 | -0.152 | -9 |
| R3 | matched | 0.598 | -0.115 | -8 |
| C1 | class_matched_production | 0.683 | +0.454 | 34 |
| S1 | spanning | 0.335 | -0.115 | -4 |
| S2 | spanning | 0.735 | -0.104 | -5 |

#### E4B

| companion | arm | companion solo | D(B←companion) | length shift |
|---|---|---:|---:|---:|
| A | matched | 0.719 | +0.054 | 8 |
| R1 | matched | 0.744 | -0.067 | -8 |
| R2 | matched | 0.742 | -0.094 | -8 |
| R3 | matched | 0.642 | +0.017 | -6 |
| C1 | class_matched_production | 0.673 | +0.529 | 9 |
| S1 | spanning | 0.531 | -0.083 | -5 |
| S2 | spanning | 0.838 | -0.083 | -3 |

#### Qwen3-4B

| companion | arm | companion solo | D(B←companion) | length shift |
|---|---|---:|---:|---:|
| A | matched | 0.710 | -0.098 | -8 |
| R1 | matched | 0.698 | -0.025 | -3 |
| R2 | matched | 0.740 | -0.131 | -5 |
| R3 | matched | 0.640 | -0.029 | 4 |
| S1 | spanning | 0.494 | -0.027 | -4 |
| S2 | spanning | 0.829 | -0.015 | -1 |

#### Qwen3-4B-Inst

| companion | arm | companion solo | D(B←companion) | length shift |
|---|---|---:|---:|---:|
| A | matched | 0.592 | -0.127 | -16 |
| R1 | matched | 0.623 | -0.098 | -2 |
| R2 | matched | 0.633 | -0.165 | -10 |
| R3 | matched | 0.610 | -0.029 | -8 |
| C1 | class_matched_production | 0.648 | -0.237 | -5 |
| S1 | spanning | 0.173 | -0.044 | -1 |
| S2 | spanning | 0.790 | -0.054 | -3 |


### Class-matched companion (production vs budget)

| model | companion | D(B←A) | D(B←CL) | **Δ_class** | D(A←CL) | D(CL←A) | D(CL←B) |
|---|---|---|---|---|---|---|---|
| E2B | ['CL7', 80] | +0.086 [+0.031, +0.143] | +0.601 [+0.544, +0.657] | **-0.515 [-0.564, -0.464]** | +0.310 [+0.245, +0.377] | -0.285 [-0.344, -0.230] | -0.002 [-0.055, +0.050] |
| E4B | ['CL8', 25] | +0.228 [+0.174, +0.282] | +0.632 [+0.578, +0.686] | **-0.404 [-0.453, -0.355]** | +0.245 [+0.176, +0.310] | +0.138 [+0.073, +0.201] | -0.226 [-0.289, -0.166] |
| Qwen3-4B | — | | | | | | |
| Qwen3-4B-Inst | ['CL8', 10] | -0.095 [-0.151, -0.040] | -0.182 [-0.244, -0.124] | **+0.087 [+0.046, +0.130]** | +0.029 [-0.046, +0.104] | +0.181 [+0.113, +0.252] | -0.024 [-0.098, +0.050] |

### §25 accidental compliance (unconstrained cell)

| model | A | B | R1 | R2 | R3 | C1 |
|---|---:|---:|---:|---:|---:|---:|
| E2B | 0.000 | 0.008 | 0.617 | 0.515 | 0.581 | 0.000 |
| E4B | 0.000 | 0.000 | 0.623 | 0.554 | 0.769 | 0.000 |
| Qwen3-4B | 0.000 | 0.406 | 0.598 | 0.694 | 0.037 | — |
| Qwen3-4B-Inst | 0.000 | 0.013 | 0.523 | 0.890 | 0.025 | 0.079 |

### Selection-clean subgroup (24 pre-screen blocks)

| model | blocks | D(B←A) | Δ_R | Ξ |
|---|---:|---|---|---|
| E2B | 24 | +0.073 [-0.057, +0.203] | +0.059 [-0.049, +0.168] | -0.043 [-0.174, +0.086] |
| E4B | 24 | +0.245 [+0.109, +0.375] | +0.122 [+0.040, +0.210] | +0.036 [-0.088, +0.169] |
| Qwen3-4B | 24 | +0.010 [-0.104, +0.141] | +0.012 [-0.057, +0.080] | +0.164 [+0.069, +0.254] |
| Qwen3-4B-Inst | 24 | -0.130 [-0.250, -0.016] | -0.075 [-0.170, +0.023] | +0.010 [-0.111, +0.126] |

### Median response words by cell (mediator, reported never conditioned on)

**E2B** — A|B|A_first 100, A|B|B_first 99, A|C1|A_first 167, A|C1|C1_first 177, A|R1|A_first 131, A|R1|R1_first 138, A|R2|A_first 111, A|R2|R2_first 94, A|R3|A_first 113, A|R3|R3_first 103
**E4B** — A|B|A_first 98, A|B|B_first 92, A|C1|A_first 142, A|C1|C1_first 140, A|R1|A_first 113, A|R1|R1_first 99, A|R2|A_first 107, A|R2|R2_first 91, A|R3|A_first 113, A|R3|R3_first 101
**Qwen3-4B** — A|B|A_first 55, A|B|B_first 47, A|R1|A_first 70, A|R1|R1_first 64, A|R2|A_first 75, A|R2|R2_first 69, A|R3|A_first 52, A|R3|R3_first 46, A|solo 75, B|R1|B_first 52
**Qwen3-4B-Inst** — A|B|A_first 48, A|B|B_first 35, A|C1|A_first 86, A|C1|C1_first 74, A|R1|A_first 65, A|R1|R1_first 58, A|R2|A_first 65, A|R2|R2_first 52, A|R3|A_first 46, A|R3|R3_first 42
