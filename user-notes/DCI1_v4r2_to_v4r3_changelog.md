# DCI-1 preregistration changelog: revision 2 → revision 3

**Current version:** 4.0 revision 3, amended 21 August 2026. **Adopted** by the
researcher on 21 August 2026 (`dci1/DECISIONS_V4R3.md` entry A0) and registered
under a signed study-wide manifest. **Not frozen; no confirmatory data.**

**Supersedes.** 4.0 revision 2 in full. Revision 2 was drafted, never
registered, never frozen and produced **no confirmatory data**: all four
registered replications stand at `REGIME_SCREEN`, no model has run Gate 1 or
Gate 2, and no confirmatory generation exists. Under v4r2 §31 a pre-freeze
change is *a revision of this document*, so the correct designation is revision
3 and not v5. The precedent is exact: v4r1 → v4r2 was the same move for the same
reason.

**Does not touch.** DCI-1 v2 and v3, their amendments, signed evidence trees and
results reports. v4r2's own signed qualification, apparatus and regime-screen
records on all four models — they remain valid evidence *under v4r2's rules*,
are not edited, and are not reinterpreted. The four v4r2 design screens
(`fs_screen_v4`, `bgrid_screen_v4`, `cal_screen_v4`, `matrix_screen_v4`), their
frozen protocols, caches and reports. **No number in any of them changes.**

**Historical comparability, once, for everything below.** v4r2 produced no
confirmatory estimate of any quantity. Every "affected results" line in this
document therefore reads the same way: *no confirmatory result is affected
because none exists*. What changes is what the design would have measured. Where
a screen quantity is re-expressed under a v4r3 rule, the screen number stands as
recorded and the v4r3 rule is not applied to it retrospectively.

---

## How to read this document

Every change carries seven fields, in the order the implementation brief asks
for them.

**Classification vocabulary**, in increasing order of consequence: *implementation*
(no scientific quantity moves) · *measurement* (what a verifier or instrument
returns) · *treatment* (what the model is shown) · *design* (which cells exist)
· *estimator* (what is computed from the cells) · *inference* (how uncertainty
or a claim is derived) · *construct* (what the study is about) · *lifecycle*
(what order things happen in).

---

## C1. The prompt carries a uniform answer-length sentence

**What changed.** §8.5's template goes from three parts to four. Between the
topic question and the numbered constraint list, every prompt now carries
`Answer in 60 to 120 words.`, byte-identical in every cell — unconstrained, solo
and composed, in both orders, for every model. It is never scored, never enters
a compliance vector, never counts toward load, and has no severity, ladder,
wording or witness obligation. Its realised satisfaction rate is recorded by
load as a diagnostic.

**Where.** v4r2 §8.5, with consequences for §6.2, §9.3, §12 and §17.4.

**Why.** v4r2 §9.3 registered the 20-word non-vacuity threshold on the stated
reasoning that *"the topic space asks for sixty to one hundred and twenty word
answers"* — but the prompts never said so. The registered vacuity threshold
rested on a premise the instrument did not put to the model.

**Evidence.** `reports/cal_screen_v4/` (protocol hash `fd49e5d4…`), which ran
§12.3 and §12.4 on the registered 96 solo-calibration topics at
$M_{\text{cal}} = 4$. Under the v4r2 template $B$'s solo vacuity rate is
**at least 0.208, and as much as 0.870, at every severity of the focal grid on
all four models** against §12.4's maximum of 0.10; Gate 2 returns `REGIME_NOT_FOUND` for every
replication before the reference question is reached. Under the floored stem the
same cells are **0.000 to 0.060**. Corroborated by `reports/fs_screen_v4/`
(protocol hash `98f8ee0d…`), which measured the vacuous share of $B$-solo passes
at 0.474 / 0.389 / 1.000 / 0.944 under the v4r2 template and 0.000 / 0.000 /
0.000 / 0.167 under the stem, and found the stem obeyed at 0.709–0.891.

**Classification.** **Treatment.** It changes what the model is shown in every
cell of every stage.

**Effect on interpretation.** Every rate measured under the v4r2 template stops
being comparable — not invalid, not comparable — and every §12 quantity is
re-measured. Generalisation claims about "the topic population of §6.2" become
claims about a population the prompts actually define. A new failure mode is
introduced and registered: the stem is one more instruction and could interact
with the constraints under study, which is why its satisfaction rate is recorded
by load.

**Historical v4r2 results affected.** None exist. The v4r2 regime-screen records
were produced under the old template and remain valid under v4r2's rules; v4r3
re-measures §12.1 and §12.2 from scratch and does not read them.

---

## C2. The candidate reference *population* is rebuilt, not merely extended

**This is the change the revision is named for, and it changes two things at
once**: how references are selected (C4, C6, C7) **and how the population they
are selected from is constructed**. v4r2 asked whether three approximately
matched controls existed. v4r3 asks whether the pool can support an empirical
difficulty-response relation at $A$'s difficulty, and that is a question about
a population rather than about three points.

**What changed.**

| | v4r2 | v4r3 |
|---|---:|---:|
| Reference families | 8 | **16** |
| — count budget `S ≤ q` | 8 | 8 |
| — rate budget `100·S/W ≤ q` | 0 | **8** |
| Class-control families | 0 | **4** |
| — count lower bound `S ≥ q` | 0 | 2 |
| — rate lower bound `100·S/W ≥ q` | 0 | **2** |
| Reference severities measured at round 0 | 94 | **158** |
| Severities measured at round 0, all roles | 94 | **190** |
| Declared candidate library | 94 | **334** |
| Feature groups | 8 | 8 |

The pool is no longer a list. §7.0 registers a **grammar** — nine counted
statistics under four predicate forms — and every family is a pair of those.
Each family carries a round-0 ladder *and a frozen reserve* that is a superset
of it, and §12.6's expansion may draw from the reserve and from nowhere else.
Eight of the nine numerators are the registered v3/v4r2 statistics unchanged;
`capital_word` — *words containing an upper-case letter* — is new, because RF6
counts upper-case *characters* and a character numerator over a word
denominator is not a proportion of anything.

**Where.** v4r2 §7.2, §7.3, §13.2; v4r3 §7.0, §7.3, §7.4, §12.6.

**Why the rate form.** Every count budget is prefix-closed: its pass set is
downward-closed under truncation. So its raw solo compliance measures answer
length as much as instruction-following, it is satisfied for free by a short
answer, and its chance compliance is high — which compresses the registered
difficulty coordinate and pushes rungs out of §13.5's band. A rate is not
prefix-closed.

**Why every numerator gets one.** An earlier v4r3 draft carried three rate
families. Three is too few: §13.6 needs three *feature groups* each supplying a
straddling triple, out of a pool whose other thirteen members share one
structural defect. §12.6's coverage criterion is what turns that from a matter
of taste into a checkable condition, and the criterion is why the pool is the
size it is.

**Evidence.** A read-only structural diagnostic: through the canonical verifier,
the empty string passes **94 of 94** registered reference severities, 4 of 4
focal severities, and **0 of 8** target severities. Only 3–6 of 94 rungs per
model meet the §13.2 vacuity condition and none of them fall inside the caliper.
`reports/fs_screen_v4/` then measured the candidates: families meeting the
condition-1 ∧ condition-6 conjunction at the same severity were **0** for the
registered pool on all four models against 3 / 4 / 5 / 2 for the candidates,
with a topic-clustered bootstrap P(≥3 families) of 0.000–0.001 against 0.41–0.88.
The candidate result is flat across non-vacuity thresholds $T \in \{10,20,30\}$,
so it was not obtained by threshold choice. The empty string passes **0 of 48**
candidate severities.

**Classification.** **Measurement** and **design**. New verifier code on a
mandatory scoring path, and a much larger population for §12.6 and §13 to
select from.

**Effect on interpretation.** The canonical verifier hash changes, so §10.2
re-opens and Gate 1's instrument population grows from 94 severities to
**348 constraint instances over the whole declared range** — reserve rungs
included, because §12.6 may admit any of them and a rung that could enter
without evidence is the failure §10.2 exists to prevent. The pool remains
jointly satisfiable pool-wide: 25,337 realisable pairs, every one discharged by
a machine-verified witness.

**Historical v4r2 results affected.** None exist.

---

## C3. Lower-bound families are excluded from the reference pool and admitted to a class arm

**What changed.** CL7 and CL8 (`S ≥ q`, production class) are registered, and an
executable check refuses them in any core-reference or spectrum slot. They are
admissible only to the new class arm of §13.7.

**Where.** New: v4r2 had no class arm and no production-class family.

**Why.** Two reasons pulling in opposite directions, resolved by separating the
roles. A lower bound breaks prefix closure, which is what the pool needs — but
it imposes a length *floor*, pushing response length up while $B$ pushes it
down, replacing one length confound with its mirror image. As a *class control*
that property is not in the way of anything the arm measures.

**Evidence.** `reports/matrix_screen_v4/`: a production-class companion cost $B$
**+0.601** (E2B) and **+0.632** (E4B) where $A$ cost +0.086 and +0.228, giving
$\Delta_{\text{class}} = -0.515$ and $-0.404$ — an order of magnitude larger than
any $\Delta_R$ the same screen produced, and with $A$ the *gentler* production
companion by five- to seven-fold. `reports/cal_screen_v4/` separately found that
under v4r2's §13.2 rule the third admitted reference on two of four models could
only be filled by a lower-bound family, so the class confound was arriving
*inside* the reference set unannounced.

**Classification.** **Design**, with a **construct** consequence: it makes
explicit that the study's excess is an excess relative to budget-class
companions.

**Effect on interpretation.** `COMPANION_CLASS_NOT_MATCHED` now attaches to
**every** L3 statement with a fixed sentence (§28.2), and $\Delta_{\text{class}}$
bounds how much class could matter. The class companion never enters $\Delta_R$,
$\bar R$, $\Xi$ or the difficulty fit — including it in the fit would let the
line absorb the quantity the arm exists to expose. One companion cannot identify
a class effect and §5 says so.

**Historical v4r2 results affected.** None exist. The matrix screen's
$\Delta_{\text{class}}$ figures stand as recorded, as screen quantities.

---

## C4. The difficulty coordinate is instructed compliance, not raw solo compliance

**What changed.** §13's matching coordinate, and the x-axis of the new
difficulty relation, become

$$\iota_c = \frac{P(X_c = 1 \mid c \text{ alone}) - \kappa_c}{1 - \kappa_c},$$

with $\kappa_c$ the chance compliance measured in a registered unconstrained
cell. Raw solo compliance is retained as a registered secondary coordinate, with
a full parallel fit and a registered disagreement status.

**Where.** v4r2 §13.2 condition 1, which read raw solo compliance; and v4r2 §25,
which measured accidental compliance and fed it into nothing.

**Why.** $A$ is an exact-count production constraint and is never satisfied by
accident. Every count budget is satisfied by accident often. Matching on raw
solo compliance therefore equates a constraint the model must work to satisfy
with one it satisfies for free, and it does so *asymmetrically*: it
systematically admits companions that demand less than $A$.

**Evidence.** `reports/section_13_2_v4/instructed_compliance.json`, computed from
§25's own registered measurement with no new generation: $A$'s chance rate is
**0.000** on all four models, while the matrix screen's references run 0.04–0.63
on instructed compliance and two are **negative** — stating the constraint made
the model satisfy it *less* often than not stating it. **Twelve of twelve
references are matched to $A$ on raw solo compliance and two of twelve on
instructed compliance.** Independently, the same screen's difficulty-spanning
rungs have chance compliance at or above their solo compliance on all four
models (E2B 0.335 solo against 0.375 chance; qwen3-4b-instruct-2507 0.173
against 0.510), so the "harder" end of a raw-coordinate spectrum consists of
rungs whose instruction is anti-productive.

**Classification.** **Construct.** It changes what "a comparable companion"
means, which is the thing the study's third question is about.

**Effect on interpretation.** An excess is now an excess relative to companions
matched on how much stating the constraint changes behaviour, rather than on how
often it ends up satisfied. This is the **harder** criterion: it moves twelve of
twelve previously matched companions out of the caliper, and it makes the
reduced design of §8.6 more likely, not less. §13.5's eligibility band
$\iota \in [0.10, 0.95]$ makes anti-productive rungs ineligible everywhere. §29
records the cost: $\iota$ is a ratio of two estimated quantities and is
therefore noisier.

**Historical v4r2 results affected.** None exist. The screens' admission tables
were computed on the raw coordinate and stand as recorded; v4r3 does not
recompute them.

---

## C5. A registered unconstrained cell

**What changed.** Every block runs one load-zero cell: the topic question, the
§8.5 stem, and `Answer:`. Every registered constraint's verifier is evaluated on
it.

**Where.** New. v4r2's block contained solo and composed cells only; load-zero
prompts appeared in §12.1's cap-selection set and nowhere else.

**Why.** $\kappa_c$ is the denominator of C4's coordinate. Measuring it anywhere
other than the confirmatory blocks, at the same $M$, under the same stem, would
leave the registered coordinate resting on an off-design quantity.

**Classification.** **Design**, enabling an **estimator**.

**Effect on interpretation.** §25's accidental compliance stops being a
diagnostic nobody reads and becomes a registered input. §22 records the exact
sense in which that is legitimate: $\kappa_c$ is pre-treatment *for the
companion* — it is measured where the companion is absent — and it is never used
as a covariate on the outcome, never used to weight or drop a block.

**Historical v4r2 results affected.** None exist.

---

## C6. The difficulty spectrum, and $\delta_{\text{diff}}$

**What changed.** Each of the three admitted core reference families supplies
two further severities, one with $\iota$ strictly below $\iota_A$ and one
strictly above, targeted at $\iota_A \mp 0.20$. Nine non-$A$ companions then
support a registered fit

$$Y_{f,s} = \alpha_f + \beta\, d_{f,s} + \varepsilon_{f,s}$$

— three family intercepts, one common slope, OLS, equal weights — and the new
primary estimand is

$$\delta_{\text{diff}} = D(B \leftarrow A) - \left[\bar\alpha + \beta\,\iota_A\right],$$

with $A$ excluded from the fit that predicts $A$.

**Where.** New. v4r2 §33 registered this as open decision **V5** —
*"Matched references only, or a difficulty-spanning set"* — with the default
*"matched only"*. This revision closes V5 in favour of both.

**Why.** v4r2's entire answer to its third question was the mean of three
companion losses. If those three happened to be gentle, or if the matching
worked less well than the caliper suggests, $\Delta_R$ says so and nothing else
does. Identifying the relation between companion difficulty and focal loss, over
companions spanning $A$ from both sides, tests the same question without
depending on three particular constraints.

**Evidence.** `reports/matrix_screen_v4/` ran a two-rung version of exactly this
arm and showed it is buildable and that $A$ can be placed inside its support on
all four models. It also showed why three points are not enough: $\Delta_R$ ran
from $-0.024$ to $+0.101$ across four models while an admitted reference
*out-damaged* $A$ on two of them — on E2B $D(B \leftarrow \text{CR6:7}) = +0.165$
[+0.121, +0.207] against $D(B \leftarrow A) = +0.086$ [+0.031, +0.143], intervals
disjoint. V5's own register recorded the objection this design answers:
*"Spanning would require more than three references and would enlarge the
pairwise matrix quadratically"* — §8.1's arm is linear, because a spectrum
companion appears beside $B$ only.

**Classification.** **Design** and **estimator**, resolving a registered
**open decision**.

**Effect on interpretation.** The study now answers its third question twice, in
two ways that can disagree, and §17.6 registers in advance what each
disagreement means. When the realised slope is flat, $\delta_{\text{diff}}$
reduces to a nine-companion $\Delta_R$; §11.7 states that in advance so it
cannot later be presented as a surprise or a failure.

**Historical v4r2 results affected.** None exist.

---

## C7. Strict straddling, and a support rule that refuses extrapolation

**What changed.** §13.6 selects the lower rung *among eligible severities with
$\iota$ strictly below $\iota_A$* and the upper rung *strictly above*, so every
family straddles $A$ by construction. §13.8 then licenses $\delta_{\text{diff}}$
only when $\iota_A$ lies inside the realised range, at least two companions lie
on each side, and at least two families contribute to each side — with the
support check re-evaluated in every bootstrap replicate and the share reported.

**Where.** New, with both parts registered because both failure modes were
observed.

**Why and evidence.** The screen's spanning rule targeted offsets without a
strictness condition, and on two of four models it put **one** point below $A$
and four above. Separately, the screen's *length* line was fitted over
companions whose length shifts all lay on one side of $A$'s — $A$ at $+15$
against others in $[-9,-1]$ on E2B, $+8$ against $[-8,-3]$ on E4B, $-16$ against
$[-10,-1]$ on the Instruct model — and a residual was nonetheless reported from
it. The correction (`CHANGES_SCIENTIFIC.md`, 2026-08-20) recorded that
extrapolated residual as **not identified** and withdrew the reading built on
it. §13.8 makes that refusal a rule rather than a discovery.

**Classification.** **Design** (straddling) and **inference** (support).

**Effect on interpretation.** `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` is a
registered outcome, distinct from a null and distinct from a terminal status. A
point estimate outside support is reported as descriptive and never as a
measurement.

**Historical v4r2 results affected.** None exist. The screen's own corrected
length residuals stand as recorded, marked not identified.

---

## C8. $A$ is excluded from the fit that predicts $A$, and the exclusion is executable

**What changed.** §11.7 registers the exclusion; §13.9 makes it a refusal in the
fitting function rather than a convention; §17.2 forbids it in every bootstrap
replicate; and a required test asserts that an input containing $A$ raises.

**Where.** New as a registered rule.

**Why and evidence.** The matrix screen's first pass fitted both the difficulty
line and the length line on a companion set that **included $A$**, then used the
line to predict $A$ — with the artifact key named
`line_fitted_on_non_A_companions`, which was false. Correcting it moved the
difficulty residuals from +0.055/+0.098 to **+0.067/+0.118** and the length
residuals from $\pm 0.010$ to $-0.117$/$+0.126$, and the conclusion that "length
explains $A$ entirely" was withdrawn. The bias is not small when the predicted
point carries leverage, and $A$ carries leverage whenever its coordinate sits
away from the others.

**Classification.** **Estimator**, enforced by **implementation**.

**Effect on interpretation.** A prediction from a fit containing the predicted
point is circular, and the circularity shrinks the residual toward zero — that
is, toward the null. Registering the exclusion protects against a false negative
here, not a false positive.

**Historical v4r2 results affected.** None exist. The screen's corrected values
are already on the record with the correction.

---

## C9. The bootstrap refits the difficulty relation in every replicate

**What changed.** §17.2 registers a seven-step replicate: resample blocks;
recompute chance, solo and hence every $d$; recompute every loss; **refit**;
predict at that replicate's $\iota_A$; form $\delta_{\text{diff}}$; re-evaluate
support. Explicitly prohibited, each with a test: fitting once and bootstrapping
the residual; including $A$; selecting the form from bootstrap outcomes;
treating spectrum points sharing topic blocks as independent; resampling
anything but blocks.

**Where.** v4r2 §17.1 bootstrapped estimands with no fitted nuisance structure;
none existed.

**Why.** $\delta_{\text{diff}}$ contains an estimated nuisance object. An
interval that treats the fitted line as known understates its own uncertainty.

**Evidence.** The screen attached **no** uncertainty of any kind to any V5
quantity: `weighted_least_squares` returns `{slope, intercept, n}` and every
slope, prediction and residual it produced is a bare point estimate while every
other estimand in the same file carries a block bootstrap. That gap is exactly
what this change closes.

**Classification.** **Inference.**

**Effect on interpretation.** $\delta_{\text{diff}}$'s interval carries the
fit's uncertainty. §16.1 derives the planning consequence — a variance inflation
of $(1+\beta^2)$ — and §16.2 sizes the design for it.

**Historical v4r2 results affected.** None exist.

---

## C10. $\Xi$ is promoted to the primary family and gates the wording of every L3 statement

**What changed.** $\Xi$ moves from secondary family F4 into primary family F1,
and §3.2 makes it decide whether an emitted L3 statement says the excess is
*specific to the outcome $B$* or carries `A_GENERAL_NOT_EXCLUDED`. No magnitude
threshold is registered for it and none is invented; it is a direction gate.

**Where.** v4r2 §11.5 and §15 (F4).

**Why and evidence.** A positive excess with a non-positive $\Xi$ means $A$
damages the references about as much as it damages $B$, which is
$H_{A\text{-general}}$ and not $H_{\text{pair}}$. In `reports/matrix_screen_v4/`
that is exactly the pattern on the two Gemmas: $\Xi = -0.036$ and $-0.009$
alongside the two largest $\Delta_R$ values in the study; and where $\Xi$ was
positive (+0.131, +0.090 on the Qwens) it was positive only because $A$ *improved*
reference compliance there while $D(B \leftarrow A)$ was itself negative.
A quantity that decides how a claim reads has to be inside the family the claim
reads.

**Classification.** **Inference**, with a **construct** consequence.

**Effect on interpretation.** F1 grows from four members to six, the Šidák
planning bound moves from 2.4909 to 2.6310, and every F1 interval widens by
about 5.6%. That is the honest cost of two more claim-bearing quantities and it
is the single largest driver of C13's block count.

**Historical v4r2 results affected.** None exist.

---

## C11. The claim ladder gains L3d and L3e, and a registered disagreement table

**What changed.** L3 gains two sub-levels for the spectrum reading — L3d
(direction of $\delta_{\text{diff}}$) and L3e (equivalence at precision) — and
§17.6 registers, in advance, the reading of every combination of $\Delta_R$ and
$\delta_{\text{diff}}$, including the two in which they disagree. A disagreement
emits **neither** claim and records `LOCAL_AND_SPECTRUM_DISAGREE`.

**Where.** v4r2 §3, §17.

**Why.** Two estimands answering one question can disagree, and the time to fix
what a disagreement means is before either is computed.

**Classification.** **Inference.**

**Effect on interpretation.** Adding a second route to L3 does not make a
positive result easier to reach: §17.6 makes agreement necessary for a claim in
the two mixed rows, so the ladder is strictly harder to climb than v4r2's, not
easier. L3d licenses direction and L3e licenses equivalence; **neither licenses
a pair-specific claim at any magnitude** — see C12.

**Historical v4r2 results affected.** None exist.

---

## C12. $\delta_{\text{diff}}$ does not inherit $\Delta_R$'s thresholds

**What changed.** §11.8 registers direction (against 0) and equivalence (against
the registered smallest effect of interest, $\pm 0.10$) for
$\delta_{\text{diff}}$, and explicitly declines to transfer the construct memo's
0.25.

**Where.** v4r2 §11.6.

**Why.** The 0.10 and 0.25 thresholds are quoted verbatim from
`dci-construct-pass2.md` §G row 1, dated 14 August 2026, and their provenance is
the protection they carry. That document defined them for one quantity: the
difference between a focal loss under $A$ and the same loss under a matched
reference. $\delta_{\text{diff}}$ differences an observed loss against a *fitted
prediction*. Transferring 0.25 would be inventing a threshold and dressing it in
someone else's provenance. What does transfer is the smallest effect of
interest, because its stated rationale is about the compliance scale itself —
*a change of 0.10 moves a system prompt from 80% to 70% compliance* — and
$\delta_{\text{diff}}$ is a difference of two compliance probabilities on that
scale.

**Classification.** **Inference.**

**Effect on interpretation.** The strongest statement $\delta_{\text{diff}}$ can
license is *"$A$ costs $B$ more than the fitted relation predicts at $A$'s
difficulty"*, never *"$A$ is pair-specific"*. §33 D5 puts a prospectively argued
threshold in the researcher's hands rather than taking one.

**Historical v4r2 results affected.** None exist.

---

## C13. The cell plan, the topic split, and the allocation are recomputed

**What changed.**

| | v4r2 | v4r3 |
|---|---:|---:|
| Cells per block | 25 | **47** |
| — unconstrained | 0 | 1 |
| — core solo | 5 | 5 |
| — core composed | 20 | 20 |
| — spectrum solo | 0 | 6 |
| — spectrum composed | 0 | 12 |
| — class solo / composed | 0 | 1 / 2 |
| Confirmatory blocks | 384 | 384 |
| Confirmatory topics per area | 32 | 32 |
| Sequestered topics | 96 | 96 |
| $M$ | 4 | **8** |
| Generations per model | 38,400 | **144,384** |
| Generations, four models | 153,600 | **577,536** |
| Primary family size | 4 | 6 |
| Šidák planning value | 2.4909 | 2.6310 |

**Where.** v4r2 §6.2, §8.1, §8.3, §16.2, §16.3.

**Why.** Three inputs to §16's calculation moved and none could be assumed away:
the block carries 47 cells; the primary family carries six members, so the
planning critical value rises; and $\delta_{\text{diff}}$ is a new estimand with
its own variance, derived in §16.1 rather than borrowed.

**Evidence.** `tools/allocation_v4r3.py`, whose formulas reproduce v4r2 §16.2's
published row exactly at 384 blocks, $M=4$, $\phi=0.27$ and a family of four —
0.0470 / 0.0422 / 0.0664 / 0.0496 — under an executable assertion, so that the
only thing changing in the new row is the estimand set. At 384 blocks the
binding member $D$ projects **0.0515** at $\phi = 0.37$ and fails its 0.05
precondition. The smallest whole-strata block count meeting every precondition
under both $\phi$ at $M = 4$ is 408 — **and 408 is not executable**. The
released bank holds the 528 non-sequestered questions; the other 96 exist to
this repository only as identities and content hashes, and
`assert_no_materialisation` refuses a released topic that reproduces one, so
the two extra confirmatory topics per area could only come from text no v4-era
process can read. With the block count fixed, $M$ is the only lever, and under
§16.1's model it is the effective one: at $\phi = 0.37$ and $\rho = 0.5$ the
draw term is 0.0000704 against a topic term of 0.0000415 at $M = 4$.
$\delta_{\text{diff}}$'s variance uses
$\sum w^2 = 0.1215$ (a centred fit over nine points, with an off-centre
allowance) and a conservative planning slope $\beta = 0.5$ — five times the
largest slope magnitude any screen produced (0.0247, 0.1001, 0.0676, 0.0603 on
five points with no interval attached).

**Classification.** **Design** and **inference**; the topic-split change is
**design**.

**Effect on interpretation.** The study costs 3.76 times what v4r2 registered —
1.88 from the cell plan and 2.0 from $M$. **The topic split does not change at
all**: v4r3 carries v4r2's cut on v4r2's seed, so the sequestered set stays at
96 and the pre-screen, solo-calibration and composed-validation sets are the
same topics v4r2 named. An earlier v4r3 draft moved the split to 34/6 to reach
408 blocks; that draft was wrong about what the bank contains, and the
correction restores v4r2's split rather than inventing a third one. §33 D1
records enlarging the bank as the alternative that would buy 408 blocks at
$M = 4$ for roughly half the generations.

**Historical v4r2 results affected.** None exist. Because the split is carried,
the v4r2 regime-screen records and the four design screens name the same
development topics v4r3 will use, which is a comparability gain rather than a
cost.

---

## C14. §12.4's graded-degeneracy clause is read as a share

**What changed.** §12.4 condition 3 now reads: *the share of responses whose
graded score exceeds 0.99, and the share whose graded score falls below 0.01,
are each at most 0.99*.

**Where.** v4r2 §12.4, which said the graded distribution must not be
*"concentrated above 0.99 or below 0.01"*, and whose code compared one float per
constraint against 0.99 without saying which.

**Why.** The clause has two readings and v4r2 fixed neither. Read as the *mean*
graded score, it fires on **every** severity §12.3 declares eligible, because
$B$'s graded score $1-(\text{words over }m)/(\text{total words})$ crosses 0.99
well inside the focal band — so §12.3 would declare a rung eligible and §12.4
would declare the same rung degenerate, on every model under every prompt. Read
as a *share*, it means what "concentrated" means in ordinary use and behaves as
designed.

**Evidence.** `reports/bgrid_screen_v4/` measured both readings on floored
$A$-solo cells: mean graded 0.646–1.000, share 0.333–1.000, firing only on two
near-ceiling qwen3-4b-instruct-2507 severities whose compliance is 1.000 — which
is the degeneracy the clause was written to catch. On $B$ the mean reading fires
on every in-band rung and the share reading on none. Recorded as a
preregistration defect in `CHANGES_SCIENTIFIC.md` (2026-08-20).

**Classification.** **Lifecycle**, resolving a defect.

**Effect on interpretation.** §12.4 states plainly that the share reading is
also the reading under which the study can run, so a reader can weigh that, and
§33 **D3** puts confirmation in the researcher's hands. The argument for it is
coherence — a clause that contradicts its own neighbour is a defect, not a
reading — and not the consequence.

**Historical v4r2 results affected.** None exist. No registered v4r2 caller ever
fixed the reading, so no v4r2 record depends on either.

---

## C15. The focal grid extends by escalation, not by widening

**What changed.** §7.2 keeps the registered grid at $m \in \{7,8,9,10\}$ and
registers a conditional extension to $\{11,12\}$, measured **only** when §12.3
finds no eligible severity in the registered grid, with selection then running
over the union.

**Where.** v4r2 §7.1.

**Why and evidence.** Under the §8.5 stem, $B$ is strictly harder — the stem
forces length and $B$ is length-monotone — and `reports/bgrid_screen_v4/`
(protocol hash `6a63ba78…`, frozen before the first generation) found that on
the registered grid qwen3-4b falls off the bottom of the focal band (0.042,
0.125, 0.167, 0.375 against a 0.60 floor) while reaching 0.625 and 0.875 at
$m = 11, 12$. But `reports/cal_screen_v4/`, measuring on the 96 registered
solo-calibration topics rather than 24 pre-screen ones, found a *flat* extension
actively harmful on qwen3-4b-instruct-2507: §12.3 selects the severity nearest
0.80, so a new rung moves $m^*$ from 10 to 11 on a model whose registered grid
already works. The escalation rule cannot do that.

The B-grid screen's own verdict was **MARGINAL**, not PASS —
qwen3-4b-instruct-2507's two in-band rungs were both 0.667, within one clustered
standard error of the band floor, and its terminal call flipped between two
independent draws on the same 24 topics. §7.2 is written so that a fresh-topic
measurement at Gate 2 decides, which is what the marginal verdict asked for.

**Classification.** **Design** and **measurement** (new boundary-suite
expectations at $m = 11, 12$; the $B$-violating token in the witness suite must
exceed the loosest admissible $m$).

**Effect on interpretation.** Where the registered grid works it is used
unchanged; where it is exhausted the replication gets an operating point instead
of a terminal status. A model needing $m > 12$ is reported, not accommodated.

**Historical v4r2 results affected.** None exist.

---

## C16. Configuration is the outcome's position, stated in the protocol

**What changed.** §11.1 states that a configuration is (model, **position of the
outcome constraint**), taking values `outcome_first` and `outcome_second`.

**Where.** v4r2 §11.1 said "(model, instruction order)" and §8.4 defined order
by the registered *slot* order. v4r2's own implementation already used the
outcome-position reading and documented why.

**Why.** v4r2 §11.4 claimed $\Delta$-type quantities "difference two composed
cells with $c$ in the same position and are position-clean in both
configurations". Under a slot-order reading that claim is false: in the
configuration where the earlier slot is stated first, the $A+B$ cell has $B$
second while the $B+R_j$ cells have $B$ first, so $\Delta_R$ would difference a
$B$-second cell against $B$-first cells.

**Evidence.** The gap between prose and implementation is visible in the
repository: `dci1v4/analysis/observations.py` uses `outcome_first` /
`outcome_second` and states the reason, while `matrix_screen_v4/estimators.py`
uses the slot reading. The screen's *pooled* figures average both order variants
within block and are unaffected; its per-configuration splits use the slot
reading and are not comparable to a v4r3 per-configuration quantity.

**Classification.** **Estimator**, as a correction of the protocol text to the
reading the implementation and §11.4's own argument require.

**Effect on interpretation.** None on any computed v4r2 quantity — the
implementation already did this. It removes a contradiction that would have
produced two defensible readings of every per-configuration number.

**Historical v4r2 results affected.** None exist. The matrix screen's
per-configuration splits are marked as slot-reading quantities.

---

## C17. Both orders for the spectrum arm

**What changed.** Every spectrum and class composed cell runs in both orders,
exactly as the core matrix does.

**Where.** New; the screen's spanning arm ran $B$-first only.

**Why and evidence.** `reports/matrix_screen_v4/`: $B$ loses **0.288** (E2B) and
**0.350** (E4B) of its compliance purely by being stated second, while $A$ shows
none — and $\Delta_R$ computed within a single order **changes sign on all four
models** (E2B +0.326 against −0.231). A difficulty relation measured in one
position would estimate a relation dominated by position.

**Classification.** **Design.**

**Effect on interpretation.** It is what makes $\delta_{\text{diff}}$ well
defined per configuration and poolable within block, and it is 6 of the 47
cells.

**Historical v4r2 results affected.** None exist.

---

## C18. Gate 1 no longer waits on Gate 3

**What changed.** §10.2's instrument population is the registered pool of §7.3
and §7.4 at every severity, not the admitted subset, so Gate 1 can complete
before Gate 2 runs. §18 states it.

**Where.** v4r2 §10.2 said Gate 1 covers "every admitted reference family
verifier", which a reader took to mean Gate 1 waits for Gate 3.

**Why.** The pool is registered by this document, so §10.2's evidence is
required under every possible admission outcome. Sequencing Gate 1 behind Gate 3
was an artefact of the wording, and it made the whole study wait on a gate that
cannot run until the regime is found.

**Evidence.** `reports/gate1_v4/section_10_2_families.json` demonstrates the
point on the v4r2 pool: three-process determinism over 1,311,582 verdicts per
process across 672 processes, boundary agreement 1.000 on 45 authored cases per
family, independent reimplementation 1.000 over 14,046 texts — produced for all
94 rungs of all eight families with no reference pool selected.

**Classification.** **Lifecycle.**

**Effect on interpretation.** None on any quantity. It removes a false
dependency.

**Historical v4r2 results affected.** None exist.

---

## C19. The independent reimplementation is itself an instrument under test

**What changed.** §10.2 adds a differential requirement: the prose-only
reimplementation and the primary must be shown to admit exactly the same
character class, over the whole Unicode range, by an executable check.

**Where.** v4r2 §10.2's "independent reimplementation" line.

**Why and evidence.** The v4r2 reimplementation segmented on the regular
expression `[^\W\d_]+`, which admits 1,151 characters in Unicode categories `No`
and `Nl` that §7.2's *alphabetic* excludes. On the genuine response
`Answer: H₂O` it read one word where the primary reads three, taking RF3's
verdict with it, and it survived because the discrepancy is invisible on $A$ and
$B$. The primary agrees with the registered prose and was not changed; the
defect was in the validation instrument. Recorded in `CHANGES_SCIENTIFIC.md`
(2026-08-20); the fixed reimplementation re-verifies at exactly 1.000.

**Classification.** **Measurement**, as a strengthening of a validation
requirement.

**Effect on interpretation.** An agreement of 1.000 between two implementations
that share a hidden disagreement is not evidence. The differential check makes
the second implementation's independence checkable rather than asserted.

**Historical v4r2 results affected.** None exist. No stored verdict, canonical
hash or estimate ever depended on the reimplementation, which is a validation
instrument only.

---

## C20. Development discipline is registered explicitly

**What changed.** §12.5 names the development data (24 pre-screen + 96 solo
calibration), enumerates the solo quantities iteration may inspect, forbids
inspecting any composed outcome for the purpose of keeping a family or severity,
fixes the sequence *propose → measure solo → improve coverage → freeze the
vocabulary and rule → observe composed outcomes*, and makes the freeze of the
vocabulary a property of this document rather than of a later stage. §13.9 gives
the executable form: selection functions accept a table with no composed field
and the loader refuses one that carries one.

**Where.** v4r2 §13.3 said what was not a matching criterion; it did not say
what development may look at, when the vocabulary freezes, or how either is
enforced.

**Why.** A design with an iterative difficulty-coverage step has a route to
outcome-adaptive selection that a single-caliper design does not, and the
protection has to be structural rather than procedural.

**Classification.** **Lifecycle**, enforced by **implementation**.

**Effect on interpretation.** The spectrum-selection rule could have been
executed before a single composed cell existed anywhere in this programme, and a
test asserts it.

**Historical v4r2 results affected.** None exist.

---

## C21. Isolation is enforced in both directions

**What changed.** §14.2 and §26 require that a v4r3 artifact cannot satisfy
v4r2's admission rule and a v4r2 artifact cannot satisfy v4r3's, with tests in
both directions.

**Where.** v4r2 §26 required v4 to refuse deprecated and foreign inputs; it
listed v2, v3 and pilot roots.

**Why.** v4r2's admission check tests a study-identifier prefix, so a
same-family identifier would pass it. The v4r3 study identifier is chosen so
that it does not.

**Classification.** **Implementation**, protecting **provenance**.

**Effect on interpretation.** None on any quantity. It is the guard that keeps
C13's larger cell plan from ever being read by a v4r2 estimator, and vice versa.

**Historical v4r2 results affected.** None. This is the change that guarantees
it.

---

## C22. The candidate library expands under a registered coverage stopping rule

**What changed.** §12.6 is new. Candidate expansion is registered as a loop with
a stopping rule, and both halves are fixed before any measurement:

- **what may be inspected** — solo compliance, chance compliance, $\iota$,
  lift, vacuity, graded distribution, response length, precision, verifier
  behaviour, satisfiability, non-entailment, wording caliper, class and form,
  on the 24 pre-screen and 96 solo-calibration topics and nowhere else;
- **what may never be inspected** — $D(B \leftarrow g)$, $\Delta_j$,
  $\Delta_R$, $\delta_{\text{diff}}$, $\Xi$, any joint state, any composed
  cell, any contrast between two composed cells;
- **the identification-coverage criterion** — seven conditions, six decisive,
  with every value either carried from an existing registered rule or set to
  the minimum the downstream rule needs;
- **the expansion rule** — bisect between the adjacent measured severities
  bracketing $\iota_A$, or extend beyond the extreme measured severity on the
  deficient side; at most four rungs per family per round, at most two rounds,
  drawn from the frozen reserve of §7.0 and from nowhere else;
- **the stop** — coverage passes, or the rounds run out, or the reserve is
  exhausted; the last two record `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` at design
  time and run the reduced spectrum arm.

**Where.** New. v4r2 had no analogue because v4r2 had nothing to expand: its
pool was a list and its criterion was a caliper.

**Why.** A design with an iterative difficulty-coverage step has a route to
outcome-adaptive selection that a single-caliper design does not, and the
honest way to close it is to make the loop's inputs a closed schema rather than
a rule. `LibraryRow` has no field a composed outcome could occupy and
`load_prescreen_table` refuses a mapping that offers one, *by schema, before a
value is read*.

**Evidence.** The four v4r2 design screens, which between them show that a
matched-only pool leaves $A$ outside its own companions' support on the length
channel on all four models, and that the spanning arm as specified put both
extra rungs on one side of $A$ on two of four.

**Classification.** **Design** and **prospective methodology**.

**Effect on interpretation.** Failure is a registered outcome with a name, not
a fallback: no band is widened, no vacuity ceiling lowered and no severity
authored in order to reach coverage. Expansion cannot author a constraint,
because everything it can return is already in a reserve this document fixes.

**Historical v4r2 results affected.** None exist.

---

## C23. Feature groups, and three references that measure three things

**What changed.** §7.0 registers eight **feature groups** over the nine counted
statistics — every statistic is its own group except `capital_char` and
`capital_word`, which are both `capital`. §13.4's structural-diversity rule
becomes *three different feature groups*, not three different families. §7.5's
witness obligation is scoped to pairs the design can realise, and two families
of one group are never such a pair. §12.6's coverage criterion counts groups
wherever it asks whether the design has enough independent companions.

**Where.** v4r2 §13.2's "three distinct families"; v4r3 §7.0, §7.5, §12.6,
§13.4.

**Why, and how it was found.** The witness suite found it. Run over every pair
of distinct families at every severity of the declared range, §7.5's
non-entailment obligation failed **1,748 times in exactly two shapes**, both
structural:

- a count budget at $q = 0$ **entails** the rate budget of the same numerator
  at every $q$, because $S \le 0$ forces the rate to zero;
- `RF6` at $q = 0$ **entails** every `CR6` severity, because zero upper-case
  characters forces zero words carrying one.

For such a pair no response satisfies the first and fails the second, so the
obligation is unsatisfiable rather than unmet. A rule that admitted RF7 and CR7
as two of the three core references would have put one measurement in two
slots, given §11.7's fit three intercepts over two properties of an answer, and
placed in one cell a pair §7.5 cannot discharge.

**Evidence.** `verifiers/witnesses.py`: 25,337 realisable pairs, every one
carrying a joint witness and two separating witnesses, zero failures. The
module refuses to construct a witness for a same-group pair rather than
returning one, so the grouping and the diversity rule are checked against each
other.

**Classification.** **Design**. It changes which reference sets §13.4 can
choose.

**Effect on interpretation.** Three references now measure three different
properties of an answer. That is what "structural diversity" was always meant
to mean, and v4r2's wording did not secure it.

**Historical v4r2 results affected.** None exist. The matrix screen's admitted
sets are screen results and were never a Gate 3 outcome.

---

## C24. The lexical rule composes in the order the prose states

**What changed.** §7.0 states the composition order explicitly: *segment the
answer, then lower-case each word for the suffix and letter tests*. v4r2's
helper lower-cased the whole response and then segmented. $B$ and every family
verifier read the corrected word list; $A$ is untouched.

**Where.** v4r2 §7.2's lexical sentence and `verifiers/words.py`.

**Why, and how it was found.** §10.2's independent reimplementation — written
from the registered prose by a process that read no primary source — disagreed
with the primary on `one_letter`. §10.2 adjudicates a disagreement against the
prose, and the prose defines the word on the answer and folds for the *test*.

**Evidence.** An exhaustive sweep of the Unicode range finds **exactly one**
character that behaves differently: `İ` (U+0130) lower-cases to `i` followed by
U+0307 COMBINING DOT ABOVE, which is not alphabetic, so folding first splits the
word. `İstanbul` becomes two words of one and seven letters; $B$ at $m = 7$
would pass an answer containing an eight-letter word. Realised frequency of
U+0130 in the **285,936** rows every v4-era process has generated: **zero**.
`statistics.assert_agrees_with_v4r2` states the equivalence executably: on any
response free of that character, all eight carried numerators return exactly
what v4r2 returns.

**Classification.** **Measurement**. It changes what a verifier computes.

**Effect on interpretation.** No measured quantity moves and no historical
comparison breaks, because the character has never appeared. The correction is
prospective; a frozen boundary case carries it and §24 reports its realised
frequency, so a future firing is visible rather than silent.

**$A$'s carry-over survives, and that is the point of the scoping.** §9.2
registers $S_0$ in its own words as *lower-case the whole response, then find
every maximal run* — fold-then-segment — and the carried counting function
implements exactly that. $A$'s construct string, segmentation function and
counting function stay byte-identical to the closed v3 instrument. The two
rules differ because the two constructs differ: $A$ counts occurrences of a
string, and $B$ and the families make claims about words as objects, whose
identity must not depend on case.

**Historical v4r2 results affected.** None, by measurement rather than by
assumption.

---

## C25. §8.6 gains a third design variant

**What changed.** v4r2 had two designs: full, and reduced when references are
not identified. v4r3 has three, and the new middle one is the one §12.6
usually produces.

| Variant | Cells | When |
|---|---:|---|
| full | 47 | three core references **and** coverage passed |
| **no-spectrum** | **29** | three core references, coverage **failed** |
| reduced | 8 | fewer than three core references |

**Where.** v4r2 §8.6.

**Why.** `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` withholds
$\delta_{\text{diff}}$, and nothing else. $\Delta_R$, $\Delta_j$,
$\Lambda$, $\Xi$, the reciprocal reference effects and
$\Delta_{\text{class}}$ are estimated from the core matrix and the class arm,
neither of which the spectrum's absence touches. Routing a coverage failure to
the 8-cell reduced design would discard six identified primary estimands
because a seventh is unavailable.

**Evidence.** The v4r3 regime screen: coverage passes on one of four models and
fails on three, and on all three §13.4's other admission conditions are met by
enough families that the core set is reachable. `reports/dci1v4r3/REPORT.md`.

**Classification.** **Design.** It changes which cells exist for a replication
in a registered state.

**Effect on interpretation.** A model in this state reports six of the seven
primary members and withholds one, with L3d and L3e withheld under §13.8 and
the fit reported as descriptive and outside support. The confirmatory cost of
the observed pre-screen picture falls from 577,536 generations to **411,648**.

**Historical v4r2 results affected.** None exist.

---

## What did not change

Recorded because "unchanged" is a claim too, and a large revision is where
things drift silently.

- $A$'s and $B$'s rules, wordings and grids (except §7.2's escalation), the
  exact-count verifier $S_0$ and its three declared alternatives, and the
  carry-over rule that binds $A$'s instrument to the v3 sources byte-identically.
- The eight registered RF families, their ladders and their graded scores. Their
  *counting predicates* are unchanged one line at a time; the word list those
  predicates read is corrected (C24), and the equivalence on U+0130-free text is
  asserted executably rather than claimed.
- **The topic split**, byte for byte, on v4r2's seed: 2 pre-screen, 8 solo, 2
  composed-validation, 32 confirmatory and 8 sequestered per area. An earlier
  v4r3 draft moved it; C13 records why that draft was wrong and why the
  correction restores v4r2's cut rather than inventing a third one.
- $D(c \leftarrow g)$, $\Lambda$, $\Delta_R$, $\Delta_j$, $\Delta^A$, the $\bar R$
  rules and $\Xi$'s formula. $\Delta_R$'s two algebraic forms and the assertion
  that they agree.
- The two $\Delta_R$ thresholds and their provenance; the smallest effect of
  interest; the equivalence region for $D$ and $\Lambda$; the caliper at 0.10
  with its Newcombe condition; the realised-gap qualifier at 0.15; the vacuity
  maximum at 0.10; the non-vacuity threshold at 20 words; the composed-headroom
  band.
- The variance model of §16.1: $p(1-p) = 0.215$, $\phi \in \{0.27, 0.37\}$,
  $\rho = 0.5$, and the requirement that every precondition be met under both.
  The precision preconditions for $D$, $\Lambda$ and $\Delta_j$.
- The block as the unit; **every** draw entering the cell mean with no draw
  selected, discarded or replaced; the wording allocation formula; both orders
  in every block; the no-exclusion rule; the missingness and duplicate
  thresholds. ($M$ itself moves from 4 to 8 — C13.)
- The bootstrap: 10,000 resamples, blocks resampled with replacement,
  studentised maximum-modulus simultaneous intervals per family, marginal
  intervals reported alongside.
- The masking scheme, its declared limitations, the single-open mask key, and
  the unmasking record.
- The stage sequence, the write-once artifact model, the terminal-status
  vocabulary and their meanings, the freeze-completeness rule, the amendment
  register, the codebook checks, the release contents.
- §10.3's human-agreement criterion including the fail-class stratification,
  §10.4's autorater pathway and its one-shot ledger, and the rule that
  author-performed labels are never described as independent validation.
- L5's permanent withholding.

---

## C26. §10.4's judging task is replaced (amendment R1, 2026-08-21)

**Post-adoption amendment.** C1–C25 were written before the first v4r3
generation. This one is written after the §12.2 regime screen and after §10.4's
development phase failed, and before Gate 1, freeze, or any composed cell. It
is a **repair of an instrument**, not a change to a scientific rule, and it is
registered here because the distinction has to be visible rather than asserted.

**What changed.** §10.4 asked the judge whether a response obeys a rule. §10.4-R
asks whether the *operationalization* — segmentation convention, numerator,
denominator, derived quantity, predicate direction, threshold, verdict —
faithfully implements the written instruction. The arithmetic is shown to the
validator rather than requested from it.

**Why.** The original task was arithmetic, and the judge exhausted its
2,048-token cap performing it. Neither registered condition survived criterion 2
on v4r3's pool: truncation 23/72 and 40/72 against 0/48 for the same
configuration on v4r2's pool of $A$ and $B$ alone, rising monotonically with how
much counting the rule demanded (0/12 on $A$, 12/12 on rate lower bounds). The
diagnosis is in `dci1/reports/dci1v4r3/section_10_4_development.json`, which is
retained.

**Why this is the right repair and not merely the cheapest.** Raising the output
cap would have been smaller, and it was considered. It does not address what
§10.4 is *for*. §10.2 already shows two independent implementations agreeing at
1.000; what agreement cannot show is that either implements the construct the
prose describes, because both could share a misreading. Asking a judge to redo
the arithmetic tests the judge; asking it to inspect the operationalization
tests the thing §10.2 cannot reach. The cap increase remains the registered
fallback if §10.4-R fails its own criteria.

**What did not change.** The deterministic verifier is still the study's
scorer — no compliance rate, cell mean, estimand or claim reads anything the
validator produces. The split, the registry disjointness, the pinned revision,
the hashed configuration, concurrency one, the repeatability check, the
single-shot freeze, the append-only ledger, the sealed final-check set, and the
requirement of explicit researcher approval are all carried unchanged.

**What is new, and load-bearing.** Half the judged cards carry exactly one
planted defect from a registered closed list of six. Without them the procedure
would measure agreeableness: a validator handed a correct derivation and asked
whether it is correct has an obvious cheap strategy. Sensitivity now has a
prospectively registered floor, **per defect kind as well as overall**, so a
validator blind to one whole class cannot pass by catching the others. Under
the old design a validator that agreed with everything would have scored well
on criterion 4; under this one it fails.

**Comparability.** No v4r3 number moves. §10.4's development evidence stands as
the record of a pathway that did not work, and is not comparable with §10.4-R's
evidence — they judge different questions and the two must never be pooled.

---

## C29. §20's mask is drawn stratified (amendment R4, 2026-08-21)

**What changed.** The number of blocks receiving a non-identity permutation is
fixed at $\lceil N \cdot \max(0.5, 1 - 1/k) \rceil$ per (outcome,
configuration) stratum, and which blocks they are is drawn uniformly without
replacement. Full statement in §20-R4.

**Why.** §8.6's reduced design gives $B$ two companions, so an independent
uniform permutation moves a label with probability exactly 0.5 — which is
`MASK_MIN_DIFFERING_FRACTION`. §20's own effectiveness check then fails about
half the time by chance. Found by the synthetic walk of the post-freeze chain
at 0.466 against 0.500.

**What it does not change.** The criterion, what is permuted, the declarations,
or the treatment of structurally unmaskable groups.

**Affected results.** None: no confirmatory generation exists on any model and
no mask has ever been built over one. The §19 pilot's mask cycle is rebuilt
under the new construction whenever Gate 0 is re-run.

---

## C28. §10.4's unit of validation becomes a microcase (amendment R2, 2026-08-21)

**What changed.** §10.4-R asked an external judge to audit an operationalization
card on a real experimental response. §10.4-R2 asks it whether a short answer
satisfies a short instruction — one wording of five to eight words, one answer
of at most fourteen, one word back. Full statement in §10.4-R2.

**Why.** §10.4-R failed four of five criteria and its planted-defect arm said
why: the judge recounted the response although told not to, and was blind to
`vacuity_ignored` (0/5) while catching `numerator_swap` and `off_by_one` (9/9
each). R1's diagnosis — "the task failed because it was arithmetic" — was wrong,
and the repaired pathway is the evidence: 0.3125 truncation against §10.4's own
0.319. The binding constraint is the reasoning chain, not the enumeration.

**What is carried unchanged.** The six defect kinds; the acceptance thresholds
for criteria 2 to 5; the deterministic verifier as the study's only scorer; the
disjoint judge registry; the held-out discipline; append-only evidence. Nothing
is relaxed because R1 failed.

**What is added.** A repeatability criterion (≥ 0.95 across two replicates of
one frozen configuration), and two arms — instruction-only, and instruction
plus §7.3's registered conventions — because two of the six kinds are not
determined by a five-word wording and scoring the validator for failing to
guess a convention would not be an audit.

**Affected results.** §10.4-R's `v4r-medium` outcome stands as recorded, and
`section_10_4R_outcome.json` remains the record of it. R2 does not reinterpret
it; R2 exists because of it.

**Comparability.** The two pathways measure different things and their rates are
not comparable. `specificity` and `sensitivity` keep their meanings — the
false-alarm side and the detection side — but the population they are computed
over is a set of microcases and not a set of operationalization cards.

---

## C27. The candidate library gains six numerators and a fifth form (amendment R3, 2026-08-21)

**What changed.** §7.0's grammar goes from nine counted statistics, eight
feature groups, four predicate forms, twenty families and 334 declared
severities to fifteen, thirteen, five, thirty and 570. The added families are
`RF9`–`RF12` and `CR9`–`CR12` (budget references over `t_initial`, `s_final`,
`vowel_initial` and `sentence`) and `CX1`–`CX2` (exact-count class controls
over `marker_thus` and `semicolon`). Full statement in §7.0-R3.

**Why.** §12.6 spent both registered expansion rounds on all four replications
and coverage still fails — `C4` on three models, `C2` on one. The diagnosis is
that the round-0 library's numerators are rare in ordinary prose, so their
budgets are impossible at tight rungs and free at loose ones, leaving little
between; 77–114 rungs per model sit below the eligibility floor. Expanding
*within* the library cannot reach the missing region because the library does
not reach it at any severity.

**What it does not change.** No criterion, caliper, band or threshold moves.
§13.7 in particular is untouched: the reference and spectrum slots still refuse
every production family, so the reference set stays one class. The two
exact-count families are class-arm families, where §7.4 already puts production
forms.

**Affected results.** The canonical verifier hash moves, so the registration
manifest is superseded and re-signed and the §10.2 instrument population goes
from 348 to 584. **The earlier 348-instrument Gate 1 evidence does not cover
the ten added families**; the whole population is re-certified at the new hash.

**Comparability.** The round-0 measurements of the original twenty families are
unaffected — no existing row is regenerated or rescored, and the added families
are measured in their own screen on the same 24 development topics at the same
cap. The `expansion_diagnosis.json` figures were computed against the pre-R3
library and remain the record of why R3 exists.

**One risk, stated.** `CX1` is $A$ with a different marker word, and it is the
strongest control this design has ever had for $A$'s constraint class. It is
also, for that reason, the family most likely to change what a $\Delta_{class}$
of any size means. It was registered before its solo compliance was measured on
any model, and the registration says so.

---

## Sequencing, and why the order is forced

1. **Amendments must precede Gate 1.** C2, C15, C23 and C24 all change the
   canonical verifier hash, and Gate 1 freezes it. There is no order in which
   any of them can be adopted after Gate 1 without discarding Gate 1's
   instrument freeze. This is not hypothetical: the §10.6 binding fired during
   this revision's own development, refusing to place 4,920 generated rows
   because a hashed module had been edited while the stage was running. No row
   was mixed, and the stage was re-run under a settled hash.
2. **The candidate vocabulary must close before Gate 1** (C22). §12.6 runs
   inside the regime screen, which the registered stage order already places
   before Gate 1, so Gate 1 certifies exactly the instruments the freeze
   contains. A family that then fails §10.2 is removed and the coverage
   criterion is re-evaluated on the table already measured — no new outcome
   information enters, because no composed cell exists at that point.
3. **Gate 1 need not follow Gate 3** (C18), so Gate 1 can begin as soon as the
   regime screen has closed the vocabulary.
4. **Gate 2 must not be run first.** A terminal record is write-once and
   disables every later command. Running Gate 2 under v4r2 would write
   `REGIME_NOT_FOUND` on all four models, and adopting a revision afterwards
   would be adopting it *because a gate failed*, which §31 prohibits. Gate 2 has
   deliberately not been run, and this document is what preserves that option.
5. **Everything else follows the registered stage sequence.**

---

## One-line summary

v4r2 asked whether $A$ costs $B$ more than three companions, drawn from a pool
of eight, matched to $A$ on how often they happen to be satisfied, using a prompt under which the focal
constraint was satisfied by eight-word answers. v4r3 asks whether $A$ costs $B$
more than three companions matched on how much stating them changes behaviour,
**and** more than a fitted relation over nine companions spanning $A$ from both
sides — drawn from a library of twenty families and 334 severities that a
registered coverage criterion expands until it can support that relation or
declares that it cannot — under a prompt that states the answer length the vacuity rule always
assumed — and it registers, in advance, what to conclude when those two answers
disagree, when $A$ falls outside the fitted relation's support, when $A$ damages
the references as much as it damages $B$, and when the excess could be a
property of $A$'s constraint class rather than of $A$.
