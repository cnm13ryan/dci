# Preregistration: when two verifiable instructions are composed, which one is delivered, how much is lost, and does the loss depend on the identity of the companion beyond its difficulty?

**Protocol identifier:** DCI-1
**Version:** 5.0
**Date:** 22 August 2026
**Confirmatory data collected at the time of registration:** none under this
version.
**Registration target:** Open Science Framework, protocol-document format
**Adoption status:** **DRAFTED, NOT YET ADOPTED.** No v5 stage record exists,
no v5 topic has been authored, and no v5 instrument has been measured. §34
records what the researcher must decide before adoption; until every entry
there is closed this document is not frozen and must not be described as
registered.

**This is a standalone document.** It incorporates nothing by reference.
Where a rule is carried unchanged from an earlier revision the text says so and
then states the rule in full, so that a reader who has never opened
`DCI1_preregistration_v4r3.md` or `DCI1_preregistration_v4r4.md` can execute
and audit this study from here alone. Those documents remain the binding
protocol for the evidence produced under them and are never reinterpreted by
this one.

**Status of what this replaces.** DCI-1 v4r4 **completed**. Four replications
entered; two — `gemma-3n-e4b-it` and `qwen3-4b` — reached
`UNMASKED_ANALYSIS` on the 8-cell reduced design; two —
`gemma-3n-e2b-it` and `qwen3-4b-instruct-2507` — terminated at Gate 4 with
`COMPOSED_HEADROOM_FAILURE` before generating a confirmatory row. Its records,
its estimates and its two terminations stand unmodified and are historical
evidence. v5 does not re-analyse them, does not re-label them, and does not
describe either termination as anything other than what §28.3 of v4r3 says it
is: *a terminal pre-confirmatory status carries no evidence about the effect.*

**Why there is a v5 rather than a v4r5.** v4r4 was frozen and produced
confirmatory data. v4r3 §31 — carried here as §32 — says that after study-wide
freeze every scientific change creates a new protocol version. This document
therefore is one.

**The causal history, stated once.**

> v4r4 completed with two of four replications confirmed, both on the reduced
> design → every companion-specific estimand (`Δ_R`, `Δ_j`, `δ_difficulty`,
> `Ξ`) was `NOT_IDENTIFIED` study-wide, because the reference-construction
> procedure did not deliver a usable counterfactual on any surviving
> replication → the completed v4r4 study was analysed as **development
> evidence** to find out why → v5 rebuilds the reference-construction
> procedure and the candidate library, and registers itself as the prospective
> test of whether the rebuilt procedure works.

**Design authority.** The construct decision of
`user-notes/dci-construct-pass2.md` (14 August 2026), unchanged: it settles the
primitive observation, demotes the legacy target-damage estimand, names
reciprocal delivery loss as the primary estimand, and specifies in §G row 1 the
discriminating experiment and its two thresholds.

**Overfitting declaration, stated here and repeated in §30.** v5 was designed
**after** observing the whole of v4r4, including its terminations, its Gate-4
tables and its confirmatory estimates. Its matching rule was chosen because it
separates v4r4's known failures from v4r4's known passes. That is design
fitting. Retrospective performance on v4r4 is **not** prospective validation,
and no sentence in this document or in any v5 artifact may describe it as
validation. The development analysis is
`dci1/reports/dci1v5/reference_design_development.md` and its §9 lists what it
does not establish.

---

## 1. Definitions

| Term | Meaning |
|---|---|
| Language model | A program that receives a text input and produces a text output by sampling from a probability distribution over word pieces. |
| Prompt | The complete text sent to the model on one occasion. |
| Response | The complete text the model produces from one prompt. |
| Instruction, constraint | A sentence in the prompt stating a requirement, expressed so that a fixed program can decide whether a response meets it. |
| Verifier | The deterministic program that reads a response and returns pass or fail for one constraint. |
| Compliance, $X_c$ | $X_c = 1$ when constraint $c$'s verifier returns pass on a response, $0$ otherwise. |
| Graded score, $G_c$ | A deterministic real-valued score on $[0,1]$ recording how nearly $c$ was met, defined per constraint form in §7.9. |
| Compliance vector | The tuple $X = (X_c)$ over every registered constraint instance, with the graded vector $G = (G_c)$, the presence flags of §9.1 and the degeneracy flags of §9.3. This is the primitive observation. |
| Unconstrained cell | A prompt containing the topic question and the answer-length stem and **no** numbered constraint. Load zero. |
| Solo cell | A prompt containing exactly one numbered constraint. Load one. |
| Composed cell | A prompt containing exactly two numbered constraints. Load two. |
| Companion | For an outcome constraint $c$ in a composed cell, the other constraint $g$ present. |
| Load | The number of numbered constraints in a prompt. Zero, one or two throughout. |
| Delivery loss, $D(c \leftarrow g)$ | $P(X_c = 1 \mid c \text{ alone}) - P(X_c = 1 \mid c \text{ with } g)$. Positive means composition reduced delivery of $c$. |
| Reciprocal pair | The two delivery losses of one composed cell, $D(c \leftarrow g)$ and $D(g \leftarrow c)$. |
| Asymmetry, $\Lambda$ | $D(B \leftarrow A) - D(A \leftarrow B)$. |
| **Chance compliance**, $\kappa_c$ | $P(X_c = 1 \mid \text{unconstrained cell})$: how often a response written without $c$ stated satisfies $c$'s verifier anyway. |
| **Counterfactual chance compliance under $B$**, $\kappa_c^{B}$ | $P(X_c = 1 \mid B \text{ alone stated at } m^*,\ c \text{ absent})$. A chance verdict under a different load-one treatment. §13.6. |
| **Displacement**, $\Sigma_c$ | $\kappa_c^{B} - \kappa_c$. How far stating $B$ moves the regime in which $c$'s difficulty was measured. |
| **Instructed compliance**, $\iota_c$ | $\left(P(X_c = 1 \mid c\text{ alone}) - \kappa_c\right) / (1 - \kappa_c)$, defined when $\kappa_c < 1$. The share of the achievable improvement over chance that stating $c$ delivers. **The registered difficulty coordinate** (§13.2), and **not** the admission coordinate (§13.3). |
| **Instruction lift**, $H_c$ | $P(X_c = 1 \mid c\text{ alone}) - \kappa_c$. The unnormalised form. A registered admission quantity in v5 (§13.4). |
| **Projected composed compliance**, $\hat p_c$ | $\kappa_c^{B} + \iota_c\,(1 - \kappa_c^{B})$: $\iota_c$ evaluated at the counterfactual baseline $B$ induces rather than at the unconstrained baseline. §13.6. |
| Companion swap, $\Delta$ | $\Delta_j = D(B \leftarrow A) - D(B \leftarrow R_j)$; $\Delta_R = D(B \leftarrow A) - \frac{1}{3}\sum_j D(B \leftarrow R_j)$ over the three **core** references. |
| **Difficulty-response relation** | $\mathbb{E}[D(B \leftarrow g) \mid \iota_g = d]$ over non-$A$ companions, estimated by the registered fit of §11.8. |
| **Difficulty excess**, $\delta_{\text{diff}}$ | $D(B \leftarrow A)$ minus the value the difficulty-response relation predicts at $\iota_A$, with $A$ excluded from the fit. §11.8. |
| **Order contrast** | A registered difference of the same named estimand across the two configurations. §11.7. |
| Target constraint, $A$ | The exact-count marker constraint. Both an outcome and a companion. |
| Focal constraint, $B$ | The word-length constraint. It carries the primary outcome. |
| **Core reference**, $R_j$ | One of three constraints occupying the companion slot in place of $A$, admitted under §13 to be a valid matched counterfactual for $A$. At least two are Tier 1. |
| **Spectrum companion**, $R_{f,-}$, $R_{f,+}$ | For each core reference family $f$, two further severities of the same family, one strictly harder than $A$ and one strictly easier. They occupy the companion slot beside $B$ only. |
| **Near-form control**, $N_k$ | One of three Tier-2 companions admitted under §13.9, beside $B$ only. |
| **Broad-class control**, $CL$ | A single Tier-3 budget-class companion admitted under §13.10, beside $B$ only. |
| **Structural tier** | Tier 1 (same form as $A$), Tier 2 (near form), Tier 3 (broad). §7.4. |
| Constraint class | **Budget** ($S \le q$ or a rate $\le q$: satisfied by doing less) or **production** ($S = n$ or $S \ge q$: satisfied by doing something specific). $A$ is production; **v5's core reference pool is production, and that is a change from v4r4** (§7.5). |
| Configuration | The tuple (model checkpoint, **position of the outcome constraint**). Every primary estimand is indexed by a configuration; only the order contrasts of §11.7 are stated across configurations. §11.1. |
| Topic, block | One question the model is asked, together with the wording indices assigned to it. All cells of a block share them. |
| Cell mean | The mean of an outcome indicator over all $M$ cached draws of one prompt cell. This is the analysis input. |
| Prefix-closed | A constraint whose pass set is downward-closed under truncation of the response. Every count budget is; a rate budget, a lower bound and an exact count are not. |
| Vacuous pass | A pass by a response that fails the registered non-vacuity predicate of §9.3. |
| Joint state | For a composed cell, the pair $(X_{c_1}, X_{c_2})$, taking one of four values. |
| Family (multiplicity) | A declared set of quantities sharing one simultaneous confidence statement. §15. |
| Simultaneous interval | An interval constructed so that a stated confidence level applies to a whole declared family at once. |
| Šidák bound | The conservative critical value for a family of size $k$, at the two-sided level $1 - 0.95^{1/k}$ per member. Used for **planning only**; decisions read the bootstrap's studentised maximum-modulus value. |
| Precision precondition | The registered maximum realised simultaneous half-width for a primary member, below which no equivalence or threshold conclusion may be emitted. |
| Identification status | A per-claim marker recording whether the design as realised supports a given claim level. |
| Measurement basis | `human_validated`, `autorater_calibration_approved`, `human_validation_unavailable`, or `deterministic_measurement_validated`. §10.5. |
| Masked analysis | Analysis performed on data whose companion labels have been permuted, so that analysis decisions cannot depend on the result. |
| **Development data** | The 24 pre-screen topics and the 192 calibration topics of §6.2. The only topics any iterative or exploratory work may inspect, and only through the quantities §12.5 enumerates. **Additionally, the whole of the completed v4r4 study is development data for the design of this document** (§30). |

---

## 2. Phenomenon, construct, and scientific question

### 2.1 Phenomenon and construct

**Phenomenon.** *Compositional non-composition.* When two verifiable
instructions that address the same output are presented together, the model
produces one text that satisfies some of them and abandons others. Joint
satisfaction is not guaranteed, the abandonment is not symmetric, and the
magnitude and sign of any pairwise summary depend on the whole configuration.

**Construct.** The *compliance profile* of a prompt: for every instruction
present, the probability that it is realised, measured on its own deterministic
verifier and referenced to its own solo baseline and to its own chance
baseline, reported jointly with the other instructions of the same prompt.

### 2.2 The primary scientific question

For a registered pair of constraints $(A, B)$, a registered model, and a
registered position of the outcome constraint:

1. Does composing each constraint with the other reduce its delivery relative
   to that constraint alone?
2. Is the reduction directionally asymmetric between the two?
3. **Is the reduction of $B$ specific to the companion $A$, or is it what a
   companion of $A$'s difficulty and $A$'s form would produce whatever its
   identity?**
4. **Does any of it depend on which constraint is stated first?**

Question 3 is `dci-construct-pass2.md` §G row 1 and is what v4r4 failed to
reach. The phrase *"and $A$'s form"* is new in v5 and is the substance of §7
and §13. Question 4 is new as a *registered* question: v4r4 found large
configuration dependence and had no estimand for it (§11.7).

### 2.3 What v4r4 established, and what it did not

v4r4 is the immediate evidential background and every claim below is checkable
against a signed v4r4 record.

**(a) The compositional effects are real and large, and they are not the same
on two models.** On `qwen3-4b`, $D(A \leftarrow B) = +0.392$ and $+0.329$ in
the two configurations, with $B$ unharmed or improved; on `gemma-3n-e4b-it`,
which constraint pays flips with position and $\Lambda$ reverses sign, both
within-configuration intervals excluding zero.

**(b) No surviving replication identified a companion-specific quantity.**
$\Delta_R$, $\Delta_j$, $\delta_{\text{diff}}$, $\Xi$, $D(B \leftarrow R_j)$
and $D(R_j \leftarrow B)$ are `NOT_IDENTIFIED` on both survivors, because both
ran the reduced design. The one replication that obtained a full design,
`gemma-3n-e2b-it`, never generated a confirmatory row.

**(c) The reference-construction procedure failed in five separable ways**, and
each is measured in `dci1/reports/dci1v5/reference_design_development.md`:

| | Failure | The measurement |
|---|---|---|
| F1 | a cheap point-estimate pre-screen used as a hard selector | pre-screen → calibration $\lvert\Delta\iota\rvert$ has median 0.071 and 35.7% of candidates move further than the whole 0.10 caliper; straddling-family support fell 50–100% on all four replications |
| F2 | a single scalar $\iota$ used as the admission coordinate | six rungs sat inside the caliper with raw solo compliance above 0.90; one of them, at solo 0.9740 and chance 0.9323, terminated a replication **on its own solo cell** |
| F3 | "production class" too coarse to say what a control shares with $A$ | two companions in the same declared class produced $\Delta_{\text{class}}$ of $+0.011$ and $-0.511$ |
| F4 | solo-matched controls made trivial by the outcome constraint | composing `RF11` with $B$ cut its statistic from ≈24 to ≈17 and took its compliance from 0.635 solo to 0.969 composed |
| F5 | support calibrated to the minimum | three of four replications finished below three core references; the fourth had no spare |
| F6 | an operating-point grid that ends where the operating point is | $m^*$ was the last measured rung on **all four** replications |

**(d) A defect in the L4 emitter.** `emit_l4` compared the *set* of claim
levels reached in each configuration rather than the classification of each
*named member*, and was handed input with member identity already discarded.
For `gemma-3n-e4b-it` both configurations reach L1 while each member's
classification flips, so the emitted L4 asserted replication for the
replication that least replicates. That field is invalidated, §28.1's
*Configuration dependence* is its registered reading, and the fix is §17.7 of
this document.

### 2.4 What v5 does about it, and what it does not do

The response is **not** to weaken any criterion, and it is not to abandon
difficulty matching. It is to stop asking one scalar to certify comparability
and to build a candidate library from which a valid control can exist.

| Layer | Estimand | Answers |
|---|---|---|
| **Same-form local matching** | $\Delta_R$ | Does $A$ differ from three companions of the same predicate form, matched on instructed compliance, stable across two independent calibration splits, and not made degenerate by $B$? |
| **Near-form local matching** | $\Delta_{\text{near}}$ | Does the same hold against companions sharing $A$'s operator but not its statistic? |
| **Difficulty spectrum** | $\delta_{\text{diff}}$ | Does $A$ differ from the empirical relation between companion difficulty and focal loss, fitted over nine companions spanning $A$ from both sides, with $A$ excluded from the fit? |
| **Reciprocal specificity** | $\Xi$ | Is any excess specific to the outcome $B$, or does $A$ damage other outcomes comparably? |
| **Broad-class control** | $\Delta_{\text{broad}}$ | How much does the companion's structural class matter, now that the core pool matches $A$'s class rather than differing from it? |
| **Order** | $\text{Ord}_A$, $\text{Ord}_B$, $\text{Ord}_\Lambda$ | Does the position of the outcome constraint change the quantity, by a registered contrast rather than by comparing two intervals? |

**The governing principle: interaction-aware during development,
interaction-blind during confirmatory selection.**

The completed v4r4 study — including its composed Gate-4 tables and its
confirmatory estimates — was used to design the matching rule, the structural
taxonomy, the candidate-family grammar, the interaction-risk rule, the sample
sizes and every threshold below. Once this document is adopted:

> **No v5 composed outcome may be used to choose a reference, replace a
> reference, widen a caliper, add a family, change a structural rule, or change
> an interaction-risk rule.**

The causal sequence is fixed:

> historical and development data → design and freeze the matching rule →
> v5 pre-composition data → select references → freeze → observe $B{+}R$.

and never

> observe $B{+}R$ → decide whether $R$ is a good reference.

§13.11 is the executable form of this and §33 lists the checks that enforce it.

**Registered thresholds and their provenance.** The two $\Delta_R$ thresholds
are `dci-construct-pass2.md` §G row 1 verbatim, fixed on 14 August 2026 before
any observation in this constraint vocabulary existed:

> D(B←A) − D(B←R) > 0.25 supports H1 and licenses a pairwise construct.
> < 0.10 supports H2 and **refutes the pairwise framing entirely**, redirecting
> the programme to a load-and-capacity account.

They are carried unchanged and are **not** transferred to
$\delta_{\text{diff}}$, to $\Delta_{\text{near}}$, to $\Delta_{\text{broad}}$
or to any order contrast; §11.9 gives each its own decision rule.

---

## 3. Hypotheses and the claim ladder

### 3.1 The hypotheses that are separated

| Label | Statement |
|---|---|
| $H_{\text{pair}}$ | $A$ causes excess damage specifically to $B$, beyond every registered control. |
| $H_{\text{difficulty}}$ | $A$ behaves as a companion of its difficulty is expected to behave. |
| $H_{A\text{-general}}$ | $A$ is unusually disruptive, but about equally to every outcome, not specifically to $B$. |
| $H_{\text{form}}$ | Interference depends materially on the companion's predicate form rather than on its identity. |
| $H_{\text{class}}$ | Interference depends materially on the companion's structural class. |
| $H_{\text{family}}$ | Interference depends materially on constraint family at fixed difficulty, form and class. |
| $H_{\text{length}}$ | Response-length change mediates or explains much of any apparent effect. |
| $H_{\text{order}}$ | The effect depends materially on the position of the outcome constraint. |
| $H_{\text{model}}$ | The effect differs across model checkpoints. |

$H_{\text{model}}$ is handled by construction: every estimand is defined within
one model and no cross-model scalar carries a claim (§6.1, §15).
$H_{\text{order}}$ is **no longer** handled by construction alone — v5
registers the direct contrasts of §11.7 and the claim level L4b that reads
them. $H_{\text{length}}$ is registered as a mediator and never conditioned on
(§22); §29 records that it is **not identified** and why. $H_{\text{form}}$ is
separated by the Tier-1/Tier-2 pair $(\Delta_R, \Delta_{\text{near}})$ and
$H_{\text{class}}$ is bounded by $\Delta_{\text{broad}}$ with a permanent
identification status (§28.2). The rest are separated by the ladder below.

### 3.2 The claim ladder

Each level has a licensing rule, a fixed licensed statement, and an
identification gate. A level whose gate fails records an identification status
and is not emitted. No level licenses any statement above it. Every rule reads
the **simultaneous** interval of the member's declared family (§15).

| Level | Claim | Licensing rule | Identification gate |
|---|---|---|---|
| **L1** | Compositional delivery loss exists | The F1 simultaneous interval for the **named** $D(c \leftarrow g)$ has lower bound above 0 | $c$ has solo headroom (§12.4) and §11.4's position caveat is stated |
| **L2** | The loss is directionally asymmetric | The F1 simultaneous interval for $\Lambda$ excludes 0 | L1 conditions for **both** $D(B\leftarrow A)$ and $D(A \leftarrow B)$ |
| **L3a** | The excess over same-form matched companions exceeds the generic-load threshold | $\Delta_R$ lower bound above 0.10 | Three core references admitted under §13, at least two Tier 1; else `EXCESS_NOT_IDENTIFIED` |
| **L3b** | That excess reaches the source memo's pair-specific threshold | $\Delta_R$ lower bound above 0.25 | As L3a |
| **L3c** | Generic compositional load, locally | $\Delta_R$ upper bound below 0.10 | As L3a |
| **L3d** | $A$ is more disruptive than the difficulty-response relation predicts | $\delta_{\text{diff}}$ lower bound above 0 | §13.13 difficulty support holds; else `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` |
| **L3e** | The difficulty-response relation accounts for $A$ | The $\delta_{\text{diff}}$ interval lies wholly inside $\pm 0.10$ **and** its half-width meets the §16.2 precondition | As L3d |
| **L4a** | The result replicates across configurations | **For the named member**, the same L1/L2/L3 classification in every registered configuration | The member reached a classification in at least one configuration, and every registered configuration was analysed |
| **L4b** | The quantity is order-dependent | The F11 simultaneous interval for the named order contrast excludes 0 | Both configurations analysed; the contrast's precision precondition met |
| **L5** | Semantic identity-specificity, universal pair property, arbitration, mechanism, class attribution, or generalisation | **Never licensed by this design** | Permanently withheld; §5 and §29 state why |

**L4a is per named member, and that is the correction of v4r4's defect.**
v4r4's emitter compared the set of levels any member reached. §17.7 registers
the signature that makes the member identity reach the emitter, and §19 requires
a regression test reproducing v4r4's `gemma-3n-e4b-it` pattern — $D(A\leftarrow
B)$ reaching L1 in the first configuration only and $D(B\leftarrow A)$ in the
second only — and asserting that L4a is **not** emitted for it.

**L4a and L4b are complementary and neither implies the other.** A member can
replicate its classification across configurations while its magnitude differs
by a resolved amount, and it can fail to replicate its classification while the
order contrast is unresolved. Both are reported.

**Outcome specificity is a gate on the wording of every L3 statement, not a
level.** When the F1 simultaneous interval for $\Xi$ has lower bound above 0,
an emitted L3a, L3b or L3d statement says the excess is *specific to the
outcome $B$*. Otherwise the statement carries `A_GENERAL_NOT_EXCLUDED` and says
the excess *is not distinguishable from $A$ being generally disruptive as a
companion*.

**Every L3 statement carries `REFERENCE_POOL_SAME_FORM`** and the fixed
sentence of §28.2. This is v5's analogue of v4r4's
`COMPANION_CLASS_NOT_MATCHED` and it points the opposite way: v4r4's reference
pool was budget class where $A$ is production, so its excess was relative to
companions of a *different* class; v5's core pool is same-form and same-class
by construction, so its excess is relative to companions that are *very* like
$A$, and the reader must be told which of the two limitations applies.
`COMPANION_CLASS_NOT_MATCHED` is **removed** from v5's status vocabulary for
the core arm and is retained for statements about $\Delta_{\text{broad}}$.

Where a $\Delta_R$ interval spans 0.10 or 0.25 the result is recorded
`INDETERMINATE` at that threshold with both bounds. Failure to exclude zero is
never reported as absence: an absence statement about any quantity requires the
equivalence rule of §17.3 including its precision precondition.

---

## 4. Experimental unit, treatments, and randomisation

The **unit** is the block: one topic together with the wording indices assigned
to it, shared by every cell of that block. The position of the outcome
constraint is a cell-level factor within the block, so every block carries both
order variants of every composed cell (§8.4).

The **treatment** for an outcome constraint $c$ is which companion occupies the
other slot, taking values in {none, and each registered companion the design
pairs with $c$}. Assignment is by design: every block runs every registered
cell, so treatment is within-block and complete, and no randomisation of
assignment to units is required.

**Randomised design factors.** Topic-to-set assignment is a seeded stratified
random split (§6.2). Instruction order is balanced by construction inside every
block rather than randomised. Wording indices are assigned by the block index
under the registered allocation of §8.4, with an executable coverage assertion
that refuses a plan containing a structural zero.

---

## 5. Scope and excluded phenomena

The study measures the compliance profile of zero-, one- and two-constraint
prompts for one exact-count marker constraint, one word-length constraint,
three core reference constraints, six spectrum companions, three near-form
controls, one broad-class control, four model checkpoints, two positions of the
outcome constraint, one decoding policy per model, one prompt template, one
language, and one topic space.

Excluded by design, and never claimed:

- **Loads above two.** The construct memo's best-evidenced interaction
  quantity, the three-place $\Gamma$, requires a third *scored* constraint. The
  answer-length stem of §8.5 is template text and is not a scored constraint,
  so this is not a load-three design. §34 D2 records the extension as an open
  decision.
- **Semantic identity-specificity.** The design compares $A$ against companions
  matched on predicate form, on instructed compliance, on instruction length,
  on stability across two splits and on interaction exposure, and against a
  fitted difficulty relation. Matching leaves other properties of $A$ free, so
  an excess attributable to $A$ is an excess relative to that controlled set,
  not to the semantic content of $A$. **In v5 the controlled set is narrower and
  the excess is correspondingly sharper**: a Tier-1 control differs from $A$
  only in which marker word is counted and in the count, so $\Delta_R$ asks
  whether *however* is special among discourse markers at matched difficulty.
  It does not ask whether $A$ is special among companions in general;
  $\Delta_{\text{near}}$ and $\delta_{\text{diff}}$ carry that question, less
  tightly.
- **Constraint-class attribution.** The broad-class arm contains **one**
  budget-class companion. One companion cannot separate "budget constraints
  interfere differently" from "this particular budget constraint interferes
  differently". $\Delta_{\text{broad}}$ is registered as a bound on how much
  class could matter, never as an estimate of a class effect.
- **Response-length mediation.** Registered as a mediator, reported, never
  conditioned on, and — on the evidence of §29 — **not identified**.
- **Universal pair properties.** No scalar is quoted without its configuration,
  except the order contrasts of §11.7, which are *about* the configuration
  difference and quote both.
- **Arbitration and mechanism.** This design measures behaviour under
  composition and is silent on internal mechanism.
- **Compliance as an independent human would judge it**, while the measurement
  basis is not `human_validated` (§10.5).
- **Generalisation** beyond the registered models, constraints, order set,
  topic space, decoding policy and load.

---

## 6. Models and topic population

### 6.1 Models

Four registered replications, each analysed separately, each a moderator level
and never pooled.

| Order | Model label | Repository | v4r4 outcome |
|---:|---|---|---|
| 1 | Gemma 3n E4B-it | `google/gemma-3n-E4B-it` | confirmed, reduced design |
| 2 | Qwen3-4B, thinking disabled | `Qwen/Qwen3-4B` | confirmed, reduced design |
| 3 | Gemma 3n E2B-it | `google/gemma-3n-E2B-it` | terminated at Gate 4 |
| 4 | Qwen3-4B instruct-only | `Qwen/Qwen3-4B-Instruct-2507` | terminated at Gate 4 |

**Both v4r4 terminations are re-entered, and the reason is registered.** Each
was caused by a companion the v5 admission rule rejects before Gate 4 is
reached — `CL8:3` at `V_headroom` and `RF11:26`/`RF11:32` at `V_interaction`
(§13). Re-entering a replication that terminated under a superseded rule is not
a repair of that termination: the v4r4 records stand, `COMPOSED_HEADROOM_FAILURE`
remains their outcome under v4r4's rules, and no v5 artifact describes either
as having passed.

Execution order places the two confirmed replications first so that the
apparatus is exercised where operating points are known. **No replication is
blocked by the outcome of another.** Exact repository revisions are pinned in
the signed registration manifest before qualification and asserted at every
generation.

**Cross-replication firewall.** Every study-wide rule is fixed in the signed
registration manifest before the first qualification. Only the following adapt
mechanically by model, and only through the registered gates of §18:

| Model-adaptive through §18 | Study-wide, fixed before the first qualification |
|---|---|
| $n^*$, $m^*$, whether a focal extension was measured, the completion-token cap, the shortlist, the three admitted core reference families and their severities, the six spectrum severities, the three near-form controls, the broad-class family and severity, the two frozen backup families, the realised difficulty support, and which arms the replication runs | Constraint families and severity ladders, the structural taxonomy and tier assignment, the prompt template, graded-score definitions, non-vacuity predicates, the difficulty coordinate, every component of the validity rule $V(R)$ and every threshold in it, every selection algorithm and tie-breaker, the number and structural composition of references, estimands, the difficulty-model functional form, thresholds and regions, precision preconditions, multiplicity families, the bootstrap, the decoding-policy form, $M$, the block count, masking rules, gate rules, artifact semantics, the claim ladder, and the codebook |

A scientific outcome from one replication never modifies a study-wide rule used
by another.

### 6.2 Topics

The task space is short open-ended informational questions answerable in sixty
to one hundred and twenty words from general knowledge, without tools,
arithmetic, or recall of a specific named fact.

**The v5 bank is 720 questions, 60 in each of the twelve declared subject
areas**: everyday science, history, geography, food, music, sport, work and
organisations, health and the body, technology, language and writing, art and
design, the natural world. It is the v4 bank of 624 plus **96 newly authored
questions, 8 per area**. Each new question is verified individually against the
same four rules the v4 bank was verified against: answerable from general
knowledge, no single correct short answer, no reused text from any public
dataset or examination, and no wording that itself mentions any letter, word
length, word shape, punctuation-count, or capitalisation requirement. Fixed
template text identical in every cell — including the answer-length sentence of
§8.5 — is not question text and is not restricted by the fourth rule.

| Set | Per area | Total | Source | Permitted use |
|---|---:|---:|---|---|
| Pre-screen | 2 | 24 | v4 split, unchanged | Completion-cap selection, high-recall regime screen, Gate 1 validation material |
| **Calibration-A** | 8 | 96 | v4 solo-calibration split, unchanged | Solo, chance and counterfactual-chance quantities; one half of §13.7's stability rule |
| **Calibration-B** | 8 | 96 | **newly authored for v5** | The same quantities, on disjoint topics; the other half |
| Composed validation | 2 | 24 | v4 split, unchanged | Composed-headroom viability only (§13.14) |
| Confirmatory | 32 | 384 | v4 split, unchanged | The frozen confirmatory experiment |
| Sequestered | 8 | 96 | v4 split, unchanged | A future uncontaminated rerun only |

**Why the confirmatory set is carried rather than re-drawn.** Those 384 topics
were used by v4r4's two confirmed replications. A language model has no memory
across runs, so reuse creates no learning contamination; what reuse could
create is a dependence between v5's estimates and v4r4's on the topic
dimension. No v5 design decision reads a confirmatory topic — §12.5 confines
development to the pre-screen and calibration sets and the guard of §13.11 is
schema-level — so the dependence is confined to sampling error shared between
the two studies, which is stated here and is not otherwise adjusted for. The
alternative, authoring 384 further questions, is recorded in §34 D1 as a
researcher decision.

**Calibration-A is not naive, and Calibration-B is.** Twenty-nine rungs per
model of v4r4's library were measured on Calibration-A's topics and the
researcher has seen those measurements. They are development data under §12.5's
own definition, so this is permitted, and it is declared rather than left to be
inferred. Most of v5's core-pool candidates — seven of eight Tier-1 families
and two of three Tier-2 families — have no prior measurement on any topic.
§30's ledger records, per family, whether a prior measurement exists.

No v3 topic and no B+R pilot topic enters any v5 set. The v3 sequestered 96
remain sequestered. Sequestered v5 text is inaccessible to the design and
execution team throughout v5, existing to the implementation only as opaque
identities and content hashes.

**The reserved sets are reserved against the whole programme.** The
composed-validation 24, the confirmatory 384 and the sequestered 96 are audited
over generated rows rather than over source, and §12.5 fixes what development
work may touch.

---

## 7. Constraints

### 7.1 The two outcome constraints

> **A:** Use the word *however* exactly $n$ times.
> **B:** Every word in the answer must have at most $m$ letters.

Registered target grid $n \in \{1,\dots,8\}$.

**Registered focal grid $m \in \{7,8,9,10,11,12,13,14\}$**, with a registered
conditional extension to $m \in \{15,16\}$ (§7.2). The word *however* has seven
letters, so $m \ge 7$ is required for $A+B$ to be jointly satisfiable.

**The focal grid is v5's, not v4r4's, and the reason is measured.** v4r4
registered $\{7,8,9,10\}$ with an extension to $\{11,12\}$. On all four v4r4
replications $m^*$ was **the last measured rung**, and on `qwen3-4b` it was the
top of the extension: its B curve over $m = 7 \dots 12$ is
$0.031,\ 0.107,\ 0.245,\ 0.411,\ 0.659,\ 0.742$ against a focal band of
$(0.60, 0.95)$, so only the two extension rungs were in band and one further
short rung would have produced `FOCAL_RANGE_EXHAUSTED` with no information
about where the band begins. §12.3 additionally requires the operating point to
be **bracketed**.

$A$ and $B$ are both outcome constraints and both companions. Neither is
privileged in the recording of the compliance vector. $A$ is a **production**
constraint and $B$ is a **budget** constraint.

### 7.2 The focal extension, and when it is measured

The registered grid is $\{7,\dots,14\}$. The extension $\{15,16\}$ is measured
**only** when §12.3's selection finds no eligible severity in the registered
grid, or when the selected severity is the top of the registered grid and
§12.3's bracketing rule therefore cannot be met; selection then runs over the
union. This is a study-wide deterministic escalation rule, not a per-model
grid. Where the registered grid works, the extension is never measured, so a
new rung cannot move $m^*$ on a replication whose registered grid already
supplies a bracketed operating point.

$B$'s rule is unchanged at every severity: the longest alphabetic run is at
most $m$. The four §7.8 wordings are parameterised on $m$ and render at every
severity of the declared range from the same four strings. Boundary-suite
expectations are authored and frozen over the whole declared range before
qualification (§10.2), and the token used to violate $B$ in the witness suite
must exceed the loosest admissible $m$.

### 7.3 The candidate library, and the four populations it feeds

| Population | What it is | Fixed by |
|---|---|---|
| **Candidate library** | every (family, severity) the grammar below declares: **632 severities in 37 families** | this document |
| **Measured vocabulary** | the severities §12.2 measures for a model, plus whatever §12.6's expansion admits | §12.6, per model, before Gate 1 |
| **Qualified pool** | the severities surviving §13's pre-composition validity gates on both calibration splits | §13, per model, at Gate 2.5 and Gate 3A |
| **Final companions** | three core references, six spectrum rungs, three near-form controls, one broad-class control, two frozen backups | §13, per model, at Gate 3B |

**The library is a grammar, not a list.** A candidate family is a *counted
statistic* under a *predicate form*, and nothing else is a candidate family.

**Six registered predicate forms**, over a statistic $S$, a word count $W$ and
a severity $q$:

| Form | Predicate | Class |
|---|---|---|
| exact count | $S = q$ | production |
| count budget | $S \le q$ | budget |
| rate budget | $100 S / W \le q$, and a wordless answer fails | budget |
| count lower bound | $S \ge q$ | production |
| rate lower bound | $100 S / W \ge q$, and a wordless answer fails | production |

`rate_lower_bound` remains in the grammar and in the verifier and **no v5
family instantiates it**, for the reason v4r4 removed `CP4` and `CP7`: two of
each such family's four model-facing wordings stated the severity as a target
quantity and named no bound, which fails §10.7 A′. A family may be added to it
only by a registered amendment that supplies four wordings passing A′.

**Every family carries structural metadata**, and this is new in v5:

| Field | Values |
|---|---|
| `operator` | `==`, `<=`, `>=` |
| `statistic_type` | `marker_occurrence`, `word_property`, `punctuation_character`, `sentence_unit`, `answer_length` |
| `count_or_rate` | `count`, `rate` |
| `denominator` | `none`, `word_count` |
| `lexical_or_structural` | `lexical`, `structural` |
| `length_dependence` | `none`, `normalised`, `proportional` |
| `length_direction` | `neutral`, `lengthens`, `shortens` |
| `production_burden` | `low`, `moderate`, `high` |
| `natural_frequency_band` | `zero`, `low`, `moderate`, `high` |
| `constraint_class` | `budget`, `production` — asserted against `operator` |
| `structural_tier` | 1, 2, 3 — asserted against the tier rule of §7.4 |
| `feature_group` | the registered partition of §7.6 |

Every field is asserted at qualification against the family's own predicate,
and a family whose declared metadata contradicts its form fails qualification.

### 7.4 The structural taxonomy, and the three tiers

$A$ is an exact count of a single fixed marker word: operator `==`,
`statistic_type = marker_occurrence`, `denominator = none`, `count`, `lexical`,
`length_dependence = none`, `length_direction = neutral`,
`natural_frequency_band = low`, class `production`. The tiers are defined
relative to that description and to nothing else.

**Tier 1 — same-form controls.** `operator == `, `statistic_type =
marker_occurrence`, `denominator = none`, `count`, `length_dependence = none`.
Differs from $A$ only in which marker word is counted and in the count.

> *Use the word **thus** exactly $q$ times.*

**Tier 2 — near-form controls.** `operator ==`, `count`, `denominator = none`,
but a `statistic_type` other than `marker_occurrence`.

> *The answer must contain exactly $q$ semicolon characters.*

**Tier 3 — broad controls.** Every other registered family: count budgets,
rate budgets, count lower bounds.

**Slot eligibility.**

| Slot | Admissible tiers |
|---|---|
| core reference $R_j$ | 1, 2 — **at least two of the three must be Tier 1** |
| spectrum $R_{f,\pm}$ | the tier of its own core family, because §13.12 draws both rungs from that same family |
| near-form control $N_k$ | 2 |
| broad-class control $CL$ | 3, and `constraint_class = budget` |

An executable check refuses a plan that places a family in a slot its tier does
not admit, and a second refuses a core reference set with fewer than two Tier-1
members.

### 7.5 Why the core reference pool is production class, reversing v4r4

v4r3 §13.1 says the reference occupies $A$'s slot and therefore has to resemble
$A$. v4r3 §7.3 then forbids production families from the reference pool, on the
argument that a lower bound imposes a length *floor* while $B$ imposes a
ceiling, replacing one length confound with its mirror image.

**That argument is correct for count lower bounds and does not reach exact
counts of a short marker at small $q$.** Requiring *thus* three times imposes
essentially no length floor: three occurrences of a four-letter word. The
consequence is that v4r4's reference pool contradicted its own §13.1 rationale,
and the measured consequence is in
`dci1/reports/dci1v5/reference_design_development.md` §5.2: applied to v4r4's
own measurements, v5's validity gates leave **3, 0, 0 and 0** qualifying
families in the budget-class reference pool on the four replications, and **4,
4, 2 and 3** in the production-class pool v4r3 excluded — unchanged at every
stage of the gate stack.

Four properties make an exact-count marker family the right reference, and all
four are checkable rather than argued:

1. **Same form as $A$.** It removes v4r4's sharpest limitation,
   `COMPANION_CLASS_NOT_MATCHED`, which attached to every L3 statement.
2. **Chance-free.** The marker does not occur spontaneously, so $\kappa \approx
   0$ and $\iota$ equals raw solo compliance, carrying **none** of the
   $1/(1-\kappa)$ variance amplification. Measured: the exact-count form has a
   split-half $\lvert\Delta\iota\rvert$ median of 0.0381 against 0.0764 for
   count budgets and 0.0915 for rate budgets.
3. **Interaction-free with respect to $B$.** $\kappa^{B} = 0$ on all four v4r4
   replications for the one such family that existed, so §13.6's projection
   reduces to the solo measurement and there is nothing for $B$ to shift.
4. **Continuously tunable in difficulty through $q$**, so unlike a budget over
   a rare numerator it does not have to be lucky to land near $\iota_A$.
   Measured $\iota$ spans for `thus` at pre-screen: 0.33–0.71, 0.50–0.96,
   0.42–0.95 and 0.50–1.00 on the four models, straddling $\iota_A$ on every
   one.

**The cost, registered rather than discovered.** A Tier-1 control is *very*
like $A$. $\Delta_R$ therefore answers a narrower question than v4r4's
$\Delta_R$ would have: whether *however* is special among discourse markers at
matched difficulty, rather than whether $A$ is special among companions
generally. `REFERENCE_POOL_SAME_FORM` (§28.2) attaches to every L3 statement
and says so, and $\Delta_{\text{near}}$ and $\delta_{\text{diff}}$ carry the
broader question with their own statuses. §17.6 registers in advance what a
disagreement between $\Delta_R$ and $\Delta_{\text{near}}$ means.

### 7.6 Counted statistics and feature groups

**Registered counted statistics.** Eight marker occurrences —
`marker_thus`, `marker_hence`, `marker_indeed`, `marker_namely`,
`marker_notably`, `marker_overall`, `marker_instead`, `marker_finally` — and
the fifteen carried from v4r4: `b_initial`, `ing_final`, `one_letter`,
`doubled_letter`, `comma`, `capital_char`, `capital_word`, `letter_a`,
`y_final`, `t_initial`, `s_final`, `vowel_initial`, `sentence`, `semicolon`,
and `marker_thus` (which v4r4 already carried as `CX1`'s numerator). Twenty-two
statistics in all.

**The marker vocabulary, and how it was chosen.** Three registered rules, two
of them **measured on the predecessor study's unconstrained development
responses** rather than asserted
(`dci1/reports/dci1v5/development/d6_marker_frequency.json`):

1. **`however` is excluded.** It is $A$'s marker; a companion counting $A$'s
   word would be $A$ under another name.
2. **At most seven letters.** $B$'s admissible severities begin at $m = 7$
   *because* `however` has seven letters. A marker longer than seven is not
   jointly satisfiable with $B$ at every admissible severity, and §7.7's
   witness obligation would fail. This structural rule rejects `moreover` (8),
   `likewise` (8), `therefore` (9), `meanwhile` (9), `otherwise` (9),
   `conversely` (10) and `nonetheless` (11).
3. **Natural occurrence at or near $A$'s own.** $P(\text{at least one
   occurrence} \mid \text{unconstrained})$ must be at most **0.15** on every
   registered model. **The benchmark is $A$, not zero**: `however` itself
   appears in 1.3% to 10.4% of unconstrained development responses, so a rule
   demanding "near zero" would reject $A$'s own marker. The ceiling is about
   1.5 times $A$'s measured maximum. It rejects `finally` (0.185) and `also`
   (0.419), and it **admits** `then`, `next`, `yet`, `still`, `rather` and
   `further` — all of which an earlier draft of this document rejected on an
   assertion the measurement contradicted.

Where a registered marker's measured $\kappa$ on a v5 topic set turns out not
to match its measurement here, that is a **measurement**: §13.4's chance
ceiling decides it, and the family is not removed from the library after the
fact.

**Every marker family additionally declares a discourse role** — contrastive,
consecutive, emphatic, exemplifying, substitutive, additive, concessive — as
part of its §7.3 metadata. $A$'s role is **contrastive**. §13.8 requires the
three core references to span at least two roles and records
`REFERENCE_ROLE_NOT_MATCHED` when none of the three shares $A$'s. The role is a
declared property audited at qualification, not a measured one, and §29 records
what it does and does not control.

**Feature groups.** Each statistic is its own group except `capital_char` and
`capital_word`, which are both `capital`. **Each marker is its own group.**

The grouping criterion is entailment, not resemblance: two families of one
group are related by entailment at the edge of their ladders, so §7.7's
non-entailment obligation is *unsatisfiable* for such a pair rather than merely
unmet. No answer's `thus` count constrains its `hence` count at any severity,
so the obligation is satisfiable and the two are distinct groups — the same
argument v4r3 §7.0-R3 used to separate `t_initial` from `b_initial`. The
witness suite discharges it over every realisable pair rather than assuming it.

**A limitation this creates, registered here.** Three marker families are more
similar to one another than three arbitrary families are. Between-family
variation in $D(B \leftarrow R_j)$ will be smaller, which narrows $\Delta_R$'s
interval and *also* narrows what "a companion like $A$" means. §11.8's fit
carries family intercepts as before; §29 records the consequence.

### 7.7 Properties established before generation

Executable tests, all required to pass at qualification:

- **Parse independence.** Each verifier receives the response text and its own
  constraint identity and severity. It receives no companion identity, cell
  label, order, or other verifier's output.
- **Joint satisfiability.** For every **realisable** unordered pair of
  constraints of distinct kinds at every severity of the **declared range**, a
  machine-verified witness response satisfies both at once. A pair is
  realisable when some registered cell can contain it: $A$ with anything, $B$
  with anything, one core reference with another **of a different feature
  group**, and a near-form or broad-class companion with $B$.
- **Realistic joint satisfiability, new in v5.** For every pair the design can
  realise **with $B$ at every admissible severity**, the witness must
  additionally lie inside §8.5's stem band of 60 to 120 words. v4r4's
  obligation was formal, and a formal witness certifies only that a pair is not
  contradictory — not that it is satisfiable by a response of the length the
  task asks for. `CL7`'s frozen reserve runs to 140: *at least 130 words must
  contain the letter a* cannot be met by any answer of at most 120 words, so
  `CL7:130` and `CL7:140` are formally satisfiable and unreachable inside the
  response genre this study registers. A family with no realistic witness at a
  severity is not admissible to any slot **at that severity**, and the failure
  is reported by family and severity rather than waived.

  **This check is cheap and narrow, and it is not the main defence.** It
  catches a severity whose arithmetic exceeds the stem band. It does not catch
  a constraint that is reachable in principle and that $B$ pushes into a
  degenerate region: `CL7:80` **is** reachable and was reached at 0.609 and
  0.662 under composition on `gemma-3n-e4b-it`. §13.6's interaction gate, and
  not this one, is what measures that class of risk.
- **Non-entailment.** For every realisable pair, one verified response
  satisfies the first and fails the second, and one does the reverse.
- **Witness-constructor envelope.** Every witness constructor asserts the
  companion class it was written for and refuses outside it.
- **Wording equivalence.** $A$, $B$ and each family carry four frozen wordings,
  checked for identical meaning and required to produce identical verdicts on a
  fixed set of twenty test responses at every severity.
- **Wording length.** Every companion wording at **every severity of the
  declared range** is within 20% of the corresponding wording of **$A$** in
  alphabetic-run word count. `assert_severity_invariance` proves that no
  wording's word count moves with its severity rather than assuming it, which
  is what lets §12.6 admit a reserve rung without authoring anything.
- **Rule vocabulary.** Every compact wording is checked against its family's
  full-prose rule statement's vocabulary, so a wording cannot quietly stop
  stating its own rule.
- **Class and tier labelling.** Every family carries a declared
  `constraint_class` asserted against its predicate form and a declared
  `structural_tier` asserted against §7.4's tier rule, and every slot refuses a
  family whose tier it does not admit.

### 7.8 Wordings

Every family carries four frozen model-facing wordings, severity-invariant in
word count, and every one must expose the comparison direction of the predicate
that scores it under §10.7 A′. For the exact-count form the registered
direction phrase is *exactly*, and the four Tier-1 templates are $A$'s four
templates with the marker word substituted, which makes the same-form claim a
property of the instrument rather than of the prose describing it.

### 7.9 Graded scores

Every verifier additionally returns a deterministic graded score in $[0,1]$,
recorded on every row and never used as a primary outcome.

| Constraint form | Graded score |
|---|---|
| Exact count of a target word ($A$ and every Tier-1 family) | $\max(0,\, 1 - \lvert S - q \rvert / q)$ |
| Exact count, other statistic (Tier 2) | The same shape over the family's own numerator |
| $B$, every word at most $m$ letters | $1 - (\text{words longer than } m) / (\text{total words})$, and $0$ for an empty answer |
| Count budget, at most $q$ | $\min(1,\, q / \max(q, \text{count}))$ for $q>0$; $\mathbb{1}[\text{count}=0]$ for $q=0$ |
| Rate budget, at most $q$ percent | $\min(1,\, q / \max(q, \text{rate}))$ when the rate is positive; $1$ when it is zero; $0$ for a wordless answer |
| Count lower bound, at least $q$ | $\min(1,\, \text{count}/q)$ for $q>0$ |

Graded scores support the manipulation-check reading and enter the robustness
family of §15.

### 7.10 The registered library

**Tier 1 — eight same-form marker families**, form `exact_count`, round-0
ladder $1\dots 8$, **frozen reserve $1\dots 12$**. `MK1` is v4r4's `CX1` under
a new label, with its instrument carried byte-identically (§30).

**The reserve runs to 12 and not to 10, on a measurement.** §12.6's coverage
condition C4 requires a straddling family to carry at least three eligible
rungs spanning at least 0.40 in $\iota$. The one marker family v4r4 measured,
`CX1` over *thus*, **straddles $\iota_A$ at pre-screen on all four
replications** — which is the property the spectrum needs — and its eligible
span is **0.375 on three of the four**, just short of 0.40, reaching 0.417 only
on `qwen3-4b`. A ladder of $1\dots 8$ is therefore marginal against C4 by
about 0.03. Higher $q$ is harder, so extending the reserve extends the span
**downward** in $\iota$, which is the deficient side; $q = 0$ is a prohibition
whose chance compliance is near one and is not admissible on either side.
§12.6's expansion is the registered mechanism for reaching it, and a reserve of
$1\dots 10$ would leave it two rungs to work with.

| Family | Marker | Letters | Discourse role | max $P(\ge 1)$ over the four v4r4 models |
|---|---|---:|---|---:|
| `MK1` | thus | 4 | consecutive | 0.057 |
| `MK2` | hence | 5 | consecutive | 0.000 |
| `MK3` | though | 6 | **contrastive** | 0.013 |
| `MK4` | whereas | 7 | **contrastive** | 0.013 |
| `MK5` | indeed | 6 | emphatic | 0.000 |
| `MK6` | namely | 6 | exemplifying | 0.000 |
| `MK7` | instead | 7 | substitutive | 0.021 |
| `MK8` | overall | 7 | summative | 0.112 |
| | *`however`* | *7* | *contrastive* | *0.104 — $A$'s marker, reserved* |

**Three registered reserve markers**, admissible only by a registered amendment
and only when a registered marker fails Gate 1: `notably` (7, emphatic, 0.000),
`albeit` (6, contrastive, 0.013), `besides` (7, additive, 0.000).

**Eight further markers pass both measured rules and are not registered**, and
the reason is stated rather than left implicit. `yet`, `still`, `then`, `next`,
`rather`, `further`, `equally` and `granted` are all admissible. They are not
registered because the vocabulary is capped at eight and the eight above span
six discourse roles including **two contrastive**, which is $A$'s own role;
`then` and `next` duplicate the consecutive role, `rather` the substitutive
one, `further` and `equally` the additive one, and `yet` and `still` are
contrastive but carry common non-connective senses — *not yet*, *still water* —
which makes §7.7's semantic-neutrality audit harder to discharge. §34 D4
records the vocabulary as a researcher decision.

**Tier 2 — three near-form families.**

| Family | Statistic | Round-0 ladder | Reserve |
|---|---|---|---|
| `XC1` | `semicolon` | 1 … 8 | 1 … 10 |
| `XC2` | `comma` | 2, 4, 6, 8, 10, 12, 14, 16 | 1 … 20 |
| `XC3` | `sentence` | 3 … 10 | 1 … 14 |

`XC1` is v4r4's `CX2`, carried. `XC2` and `XC3` are new and carry v4r4's
`comma` and `sentence` counting functions unchanged, so §10.2's carry-over
evidence covers the numerators and only the predicate form is new.

**Tier 3 — twenty-six broad families**, carried from v4r4 unchanged with their
ladders and reserves: `RF1`–`RF12`, `CR1`–`CR12`, `CL7`, `CL8`. Admissible to
the spectrum and to the broad-class slot only. `CL7` and `CL8` are the two
count lower bounds and are the only families admissible to the broad-class slot
that are not budget class; §13.10 admits **budget class only**, so in practice
they are spectrum-eligible and broad-class-ineligible, and the check is executable.

**Sizes.** 37 families; **326 round-0 severities**; **632 severities in the
declared range**. With $A$'s eight and $B$'s ten, Gate 1's instrument
population is **650 constraint instances in 39 verifiers**. Every one of them
carries the full §10.2 evidence over the whole declared range before
qualification, because §12.6's expansion may admit any reserve rung.

**No rate ladder contains $q = 0$**, and no exact-count ladder contains $q = 0$.
$100 S/W \le 0$ holds exactly when $S \le 0$, so a rate rung at zero would
duplicate a count family's meaning; and an exact count at zero is a
prohibition whose chance compliance is near one, which §13.4 would reject and
which no ladder should contain. Executable checks refuse both.

---

## 8. Design

### 8.1 The cell plan

Per model replication the design registers: $A$, $B$, three core references
$R_1, R_2, R_3$, six spectrum companions $R_{f,\pm}$ for $f \in \{1,2,3\}$,
three near-form controls $N_1, N_2, N_3$, and one broad-class control $CL$.

The design is **an admitted set of arms**, not a named variant. Each arm is
admitted independently by §13 and the cell count is derived:

| Arm | Cells | Contents | Admitted when |
|---|---:|---|---|
| **Base** | **5** | unconstrained; $A$ solo; $B$ solo; $A+B$ in each order | always |
| **Core** | **21** | $R_1, R_2, R_3$ solo; $A{+}R_j$, $B{+}R_j$ and $R_j{+}R_k$, each in both orders | §13.8 admits three core references |
| **Spectrum** | **18** | six spectrum solo; $B$ + each, both orders | the core arm is admitted and every core family supplies a strictly straddling triple (§13.12) |
| **Near-form** | **9** | $N_1, N_2, N_3$ solo; $B$ + each, both orders | §13.9 admits three near-form controls |
| **Broad class** | **3** | $CL$ solo; $B{+}CL$ in each order | §13.10 admits one |
| | **56** | **cells per block when every arm is admitted** | |

Derived counts: 56 with every arm; 38 without the spectrum; 29 with base, core
and broad class; 17 with base, near-form and broad class; 8 with base and broad
class alone; 5 with the base alone. An executable function derives the count
from the admitted set and the freeze records both.

**Dropping an arm never drops another.** A replication that cannot identify the
spectrum still estimates $\Delta_R$, $\Delta_j$, $\Xi$ and the reciprocal
matrix; a replication that cannot identify the core arm still estimates
$D(B\leftarrow A)$, $D(A \leftarrow B)$, $\Lambda$, the order contrasts and
whichever of $\Delta_{\text{near}}$ and $\Delta_{\text{broad}}$ its own arms
support. Discarding an identified estimand because an unidentified one is
unavailable is not a rule this document contains.

Every generation is scored on **every constraint instance the replication
uses**, not only on those present in its prompt (§9.1): a composed generation
yields two *treated* observations and one *chance* observation per absent
instance, and the unconstrained cell and the $B$-solo cell together supply
$\kappa$ and $\kappa^{B}$ for §13.6 at no generation cost.

**Why the spectrum arm is not a full matrix.** A spectrum companion appears
beside $B$ only. Crossing the six with each other and with $A$ and the core
references would add cells for quantities no registered estimand reads. The
full reciprocal matrix that $\Xi$ needs is retained over the five core
constraints, and the spectrum and near-form arms buy their quantities at linear
rather than quadratic cost.

**Why every companion arm runs both orders.** v4r4 measured a change of
$\Lambda$ from $-0.110$ to $+0.315$ across configurations on one model. A
companion measured in one order estimates a quantity dominated by position.

### 8.2 Draws and cell means

$M = 8$ cached stochastic draws per cell. All $M$ enter the cell mean; no draw
is selected, discarded, or replaced. Blocks remain the only resampling unit.

### 8.3 Size

**384 confirmatory blocks.** Because order is within-block, every block enters
both configurations. Per model with every arm admitted:
$56 \times 384 \times 8 = 172{,}032$ cached generations; across four models,
**688,128**. §16 gives the justification and the registered menu, and §34 D1
records the compute decision.

A sensitivity run repeats the composed cells on the first 96 confirmatory
blocks at temperature 0 with one draw per cell, reported as a different
generation population.

### 8.4 Order and wording allocation

**Order is a cell-level factor.** For every composed pair the block runs both
variants. The registered slot order is

$$(A,\; B,\; R_1, R_2, R_3,\; R_{1,-}, R_{1,+}, R_{2,-}, R_{2,+}, R_{3,-}, R_{3,+},\; N_1, N_2, N_3,\; CL),$$

and one variant states the earlier constituent first, the other states it
second. Order is exactly balanced by construction inside every block, and each
configuration uses all 384 blocks.

**Wordings are a block-level factor.** For a composed cell with constituents
$(c_1, c_2)$ in registered slot order, block index $i$ fixes wording index
$i \bmod 4$ for $c_1$ and $\left(i + \lfloor i/4 \rfloor\right) \bmod 4$ for
$c_2$, applied identically to both order variants of that cell. Solo cells use
$i \bmod 4$. The unconstrained cell has no wording index. Because order does
not depend on the block index, wording and order are orthogonal by
construction.

Every generative stage carries an executable allocation assertion stating the
intended count for every wording and every order, and refuses a plan containing
a structural zero or a skew.

### 8.5 Prompt construction

Every prompt has **four** parts in the same order: the topic question, the
answer-length sentence, a numbered list of the active constraints, and the line
`Answer:`. The answer-length sentence is exactly

```
Answer in 60 to 120 words.
```

byte-identical in every cell without exception — unconstrained, solo and
composed, in both orders, for every model. The unconstrained cell carries the
question, the sentence and `Answer:` and no numbered list.

**The stem is background, not a constraint under study.** It is never scored as
an outcome, never enters a compliance vector, never counts toward load, has no
severity, ladder, wording or witness obligation, and is not subject to the §7.7
length caliper. Its realised satisfaction rate is recorded as a diagnostic on
every stage record, **by load**. That rate gates nothing and no estimand reads
it — with one exception, stated here so it is not a surprise: §7.7's *realistic*
witness obligation uses the stem's band as the definition of a reachable
answer, which is a use of the band as a design constant and not a reading of
its realised rate.

Within a block, two composed prompts sharing a constituent differ byte for byte
only in the line stating the other constituent. Both constraints occupy the
same authority level in the same numbered list in the same user message. No
constraint is placed in a system message.

---

## 9. Primitive observation

### 9.1 The compliance vector

For every generation the record carries $X_c$ and $G_c$ for **every registered
constraint instance the replication uses**, together with, for each, whether it
was *present* in that prompt, its severity, wording index and position. A
verdict on an absent constraint is a chance observation and is marked
`present = false`; no estimand reads a chance observation as a treated one, and
an executable check refuses any primary formula that mixes them. Nothing is
marginalised at record time.

**This rule is load-bearing in v5 in a way it was not in v4r4.** §13.6's
interaction gate reads the verdict of every candidate instance on the $B$-solo
calibration cells. v4r4's calibration stage scored load-one rows on the present
instance only, so that quantity did not exist in its records and had to be
recomputed for the development analysis. v5 requires the presence rule to hold
at **every** stage that generates a response, and qualification asserts it.

### 9.2 The exact-count rule and its alternatives

$A$'s verifier, written $S_0$, is fixed here and applies unchanged in every
cell: take the whole response, lower-case it, find every maximal run of
alphabetic characters, count the runs equal to `however`, and pass when the
count equals $n$. **Every Tier-1 family uses the same function with a different
target string**, which is what makes the same-form claim an identity of
implementation rather than a resemblance of prose.

Three alternatives are declared for the robustness family and never redefine
$X_A$: $S_1$ omits the lower-casing step; $S_2$ counts non-overlapping
substring occurrences in the lower-cased text; $S_3$ applies $S_0$ after
deleting a leading colon-terminated line and any line repeating an active
constraint wording.

**The lexical rule for every other statistic.** A word is a maximal run of
alphabetic characters in the answer, where *alphabetic* is Unicode general
category L; **the answer is segmented first and each word is lower-cased for
the suffix and letter tests**; comma, semicolon and upper-case-character counts
read raw characters; a word's *letters* are the characters of the word as
written. The composition order is stated because reversing it splits `İ`
(U+0130) into two words and makes every letter test read fragments; §10.2
adjudicates any disagreement against this prose.

### 9.3 Degeneracy, vacuity, and non-behavioural states

Every generation additionally carries: emptiness, word count, token count,
finish reason, truncation at the completion cap, verifier-processing failure,
whether the answer fell inside the stem's 60–120 word band, and the chance
verdict of every absent instance.

A **non-vacuity predicate** is registered per constraint form:

| Constraint form | Non-vacuity predicate |
|---|---|
| Exact count ($A$, Tier 1, Tier 2) | Response is non-empty and not truncated |
| $B$ (word-length budget) | Response is non-empty, not truncated, and contains at least 20 words |
| Count budget, rate budget | Response is non-empty, not truncated, and contains at least 20 words |
| Count lower bound | Response is non-empty and not truncated |

A pass by a response failing its predicate is a **vacuous pass**. Vacuous passes
are counted as passes in the primary estimand, because response shortening under
composition is a candidate mechanism rather than a nuisance, and removing them
would condition on a consequence of the treatment. They are handled by the
per-cell vacuity rate, by family F6 of §15, and by the partial-identification
recomputation of §17.4 in which every primary estimand is recomputed with all
vacuous passes forced to failures.

The 20-word threshold is fixed here, is stated to the model by the §8.5 stem,
and is not tuned after any data are seen.

---

## 10. Measurement: verifiers, freeze, and validation

### 10.1 Architecture invariants

1. Every behavioural score is a deterministic function of the response text and
   fixed configuration.
2. Verdicts are computed at generation time and stored with the verifier source
   hash.
3. No language model produces a behavioural score.
4. Alternative scoring rules never silently redefine a primary outcome.
5. A pass on a budget constraint is never described as engagement without the
   §9.3 predicate.
6. The difficulty coordinate is computed from stored verdicts only, by one
   named function, and never from a model judgement.

### 10.2 Verifier correctness

Every verifier that can enter the final instrument population — $A$'s
exact-count rule at every $n$, $B$'s word-length rule at every severity of the
registered grid **and of the conditional extension**, and every one of the
thirty-seven family verifiers at every severity of its **declared range**,
reserve included — must pass all of:

The population is the declared range and not the round-0 ladder, because
§12.6's expansion may admit any reserve rung. **650 constraint instances in 39
verifiers.**

- **Determinism.** Three executions on three separate processes over every
  calibration response, agreement exactly 1.000.
- **Boundary suite.** A frozen boundary suite per verifier, of at least forty
  cases, covering empty response, adjacent punctuation, capitalisation,
  hyphenation, concatenated copies, repeated words, non-Latin characters,
  Unicode punctuation and lookalikes, zero-width characters, and truncation
  mid-word. Rate verifiers additionally cover rates straddling each $q$, a
  single-word answer, and a wordless answer. Lower-bound and exact-count
  verifiers additionally cover counts at $q-1$, $q$ and $q+1$. **Every Tier-1
  marker verifier additionally covers the marker embedded in a longer word, the
  marker adjacent to punctuation, the marker capitalised at a sentence start,
  and the marker hyphenated.** Case texts and expected verdicts are frozen
  before qualification.
- **Independent reimplementation.** A second implementation written from the
  registered prose of §7 and §9 by a process that does not read the primary
  source, run over every calibration response and the whole boundary suite,
  agreement exactly 1.000. The reimplementation is an instrument under test in
  its own right: it segments text by an independent mechanism and a
  differential check over the whole Unicode range asserts that the two
  segmenters admit exactly the same character class.
- **Adversarial corpus.** A targeted corpus exercising every enumerated
  boundary case, with the realised frequency of each case in genuine
  generations reported (§24).
- **Carry-over.** A carried instrument may supply carried evidence only when
  its construct string, segmentation function source, counting function source
  and frozen case texts with their expectations are byte-identical to the
  source artifact. §30's ledger names every carried instrument and the carry-over
  record refuses on any mismatch.

**Gate 1 does not pass until every instrument in the final population carries
the full set.** The population is fixed by §7 and not by any selection outcome,
so the evidence is required under every admission result and Gate 1 does not
wait on Gate 3.

**Gate 1 runs after §12.6 closes the vocabulary.** The candidate expansion
happens inside the regime screen, on development topics, using verifiers Gate 1
has not yet certified; what it decides is a *vocabulary*, and Gate 1 then
certifies every member of it. A family or severity failing §10.2 is removed
from the frozen vocabulary, §12.6's coverage criterion is re-evaluated on the
table already measured, and no new outcome information enters because no
composed cell exists at that point.

### 10.3 Human agreement

At least one annotator independent of the design and analysis team labels a
seeded stratified sample per verifier class per instrument, under a
tool-assisted protocol: the annotator marks each qualifying feature and the
interface tallies the annotator's own marks, with no automatic detection,
highlighting, counting or normalisation, and no arm, model label, companion,
verdict or other annotator's work visible.

Criterion: the one-sided 95% Wilson upper bound on human-to-verifier
disagreement is at most 0.10 in each verifier class, on a seeded sample of
$\min(150, N_c)$ natural responses per class. Within the fail class the bound is
computed separately on items whose realised margin is exactly one and on items
with larger margins, and both must be met.

**§10.3 is not a Gate-1 prerequisite in v5**, exactly as it was not in v4r4.
The frozen sampling plan stays unspent, and a completed §10.3 supersedes §10.5's
basis rather than being blocked by it. Author-performed labels are never
described as independent validation.

### 10.4 Autorater-assisted validation

Retained in full as a **supplementary semantic diagnostic** and not as a
Gate-1 prerequisite. v4r3's §10.4, §10.4-R and §10.4-R2 and their recorded
outcomes stand: §10.4-R2 **FAILED** on its registered criterion 5 and §10.3
stands **unavailable**. Neither is described anywhere as having succeeded, and
no v5 Gate-1 pass is a retroactive pass of either. A finding from either
pathway about confusing wording or an undocumented assumption is actionable
under §10.7 A′ or under §10.2, never as a re-labelling of an outcome.

### 10.5 Measurement scope, recorded verbatim

Three questions are kept separate and never aggregated.

1. *Does each program implement its registered rule?* Answered by §10.2 and
   §10.7.
2. *Can an independent human reproduce it?* Answered by §10.3, or recorded
   unavailable.
3. *Does the deterministic rule validly operationalise the intended
   instruction-compliance construct?* Bounded by §9.3 and §24 and not resolved
   by this study.

The registered bases are `human_validated`, `autorater_calibration_approved`,
`human_validation_unavailable` and `deterministic_measurement_validated`.
**v5's Gate 1 writes the last and refuses every other**, and the refusal
happens before the gate reads any evidence, because the basis names how
validity was established and a record claiming `human_validated` under this
rule would be false.

Every analysis record carries the measurement basis and, while the basis is not
`human_validated`, the registered scope sentence: *the outcomes are
verifier-defined and support no claim about compliance as an independent human
would judge it.* **No later stage may remove it.**

### 10.6 Verifier freeze and downstream binding

The canonical verifier hash covers every source and configuration component
that can change verifier semantics for any registered instrument: the word
segmenter, the target and marker counters, the family statistics, the
constraint grids and ladders, the class and **tier** labelling, and the
compliance and graded mappings. It is frozen in the Gate 1 record. Every
downstream entry point re-verifies the current hash against the frozen hash
before any work and fails closed on mismatch: ladder screen, calibration,
**candidate qualification**, **reference calibration**, **reference
selection**, composed-headroom validation, freeze, confirmatory generation,
scoring, resume and restart paths, analysis, unmasking, and report generation.
The frozen hash is never silently updated. Historical rows remain auditable
under their own recorded hash and are never treated as newly valid.

### 10.7 Deterministic-measurement validation

**Carried from v4r4 §10.7 unchanged in substance and restated in full.** v5
changes reference matching and changes nothing about how measurement validity
is established. §33 requires the red-team to confirm that this section is
byte-equivalent in rule to v4r4's, and any difference to be enumerated.

Gate 1 answers two questions:

1. **Specification validity.** Does the written constraint correspond
   unambiguously to the intended formal predicate?
2. **Implementation validity.** Does the deterministic verifier correctly and
   reproducibly implement that predicate?

**A. Specification audit.** For every distinct family and predicate form in the
final instrument population, a specification record carries: the exact
natural-language instruction templates as the model receives them; the
full-prose rule statement; the counted statistic and what it counts; the
segmentation convention; the numerator definition; the denominator definition,
or the explicit statement that the form has none; the comparison operator; the
threshold and severity interpretation; the zero-denominator and vacuity rule;
the case-folding and Unicode behaviour; **the structural metadata of §7.3**;
and the **exact formal predicate** in a machine-evaluable form.

The audit is decided by deliberately constructed discriminating examples, never
by statistical reviewer agreement. Each family carries constructed cases at
$q-1$, $q$ and $q+1$; a zero statistic; an empty answer; a wordless answer; a
punctuation boundary; a Unicode boundary; a case-folding boundary; and, where
the form has one, a malformed delimiter. Each case records the registered
verdict and the verdict each of the six alternative readings —
`inequality_flip`, `off_by_one`, `numerator_swap`, `denominator_swap`,
`segmentation_drift`, `vacuity_ignored` — would record.

Three checks decide it, all executable: **completeness** of every field for
every family and form; **prose-to-predicate correspondence**, the recorded
formal predicate evaluated by a generic evaluator that reads only the
specification record reproducing the primary verifier's verdict on every
constructed case and on the whole frozen boundary corpus; and **resolution of
alternative readings**, every meaningful alternative named with the registered
reading and a constructed case separating them, every non-applicable one
recorded with its reason, and silence accepted for neither. An unresolved
ambiguity fails Gate 1.

**A′. The prose-to-predicate invariant, and the wording review.** Every
model-facing wording must expose the comparison direction of the predicate that
scores it, by containing a phrase from the registered direction lexicon for its
operator —

| operator | registered phrases |
|---|---|
| `≤` | at most · no more than · not more than · more than · do not exceed · exceed · longer than · limit … to · keep … to · or fewer · or less |
| `≥` | at least · no fewer than · or more · minimum |
| `==` | exactly |

— or by matching a documented construction registered as entailing one
direction and admissible for that operator. **A wording that expresses a
directional predicate only as a target quantity, with no operator, fails
specification validation.** A wording naming a direction other than its own
predicate's fails as *requires correction*.

One documented construction is registered, with deliberately narrow scope: a
**requirement verb** — *need*, *must*, *require* — is a necessity operator over
the counted feature and entails `≥`, and is admissible **only** where the
registered operator is `≥`.

Every wording of every family at every severity of the declared range is
additionally classified as **mechanically awkward but semantically
unambiguous**, **genuinely ambiguous**, or **misleading enough to require
correction**. Live prompt wording is never silently fixed: a change is
registered prospectively, every affected family and rung is identified, every
downstream measurement depending on that wording is invalidated and recorded as
invalidated, and the necessary pre-confirmatory stages are rerun. **Coverage
measured under one wording is never carried across a changed wording.**

**B. Deterministic implementation validation.** §10.2 retained unchanged and
mandatory over the final population. Any disagreement between the primary and
independent implementations is adjudicated **against the formal specification
of A**, never by majority vote.

**C. Independent reimplementation.** Mandatory, an instrument under test in its
own right, including the whole-Unicode segmenter differential. Zero unexplained
disagreement.

**D. Adversarial, boundary and mutation validation.** For each of the six
registered defect classes the evidence must show that the frozen suites and A's
constructed cases contain at least one case that *discriminates* the registered
reading from the defective one, for every family and form where that defect is
meaningful, with every non-applicability named with its reason. Sensitivity is
reported by family and form. The defect-sensitivity analysis on natural
responses establishes practical consequence only and is never read as semantic
validation.

**E. Provenance and hash binding.** The Gate-1 record binds: the canonical
verifier hash; the hash of the frozen boundary suite; the hash of every
model-facing wording in the final population; the hash of the specification
audit; the hash of the mutation report; the measurement-rule hash of this
subsection; the v5 protocol hash; the producing commit; and the environment
digest. Every downstream entry point re-verifies the verifier hash and refuses
on a wording-hash mismatch.

**The Gate-1 rule.** Gate 1 passes if and only if **all ten** hold: complete
specification records; no unresolved prose-to-predicate ambiguity; three-process
determinism at exactly 1.000; zero unexplained reimplementation disagreement;
every required boundary, adversarial and Unicode test passing with the corpus
at its registered minimum size; mutation sensitivity to every meaningful defect
class with every non-applicability explained; satisfiability and
non-entailment witnesses passing **including §7.7's realistic-witness
obligation**; wording equivalence passing, every wording exposing its direction
under A′, and no wording classified as genuinely ambiguous or requiring
correction; verifier and wording hashes bound correctly; and lifecycle and
provenance integrity passing with reserved sets unspent.

**No human or autorater agreement rate, sample size, Wilson bound, accuracy,
repeatability or judge verdict appears in this rule.** Reviewer evidence is
carried as a diagnostic and cannot cause a pass or a failure, and equally never
overrides a formally specified deterministic predicate.

**The basis this creates.** A pass writes
`measurement_basis = deterministic_measurement_validated`. That is not
`human_validated`, so §10.5's scope sentence attaches to every analysis record,
every claim at every rung and the final report, permanently. The basis may
never be upgraded except by new evidence of the kind §10.3 specifies, produced
under that section's own criteria.

**Registered limitation.** The specification audit certifies each family at the
audited severities and relies on the severity-invariance §7.7 establishes; it
does not re-audit every rung independently. The prose-to-predicate check reads
the same registered counting functions the verifier reads, so it tests the
mapping from prose to predicate and not the counting functions, which are
covered by B, C and D.

---

## 11. Estimands

### 11.1 Observation and configuration

For cell $c$ with $M$ draws the observation is the cell mean
$\bar X_c = \frac{1}{M}\sum_{j} X_{c,j}$.

**A configuration is (model, position of the outcome constraint)**, taking
values `outcome_first` and `outcome_second`. This is the reading §11.4
requires: a $\Delta$-type quantity differences two composed cells and is
position-clean only when the configuration fixes the *outcome's* position. A
solo cell states its constraint in position one and serves both configurations.
There are two configurations per model.

**A consequence stated once, because v4r4's reports were read wrongly without
it.** $D(A \leftarrow B)\vert_{\text{outcome\_first}}$ and
$D(B \leftarrow A)\vert_{\text{outcome\_first}}$ are read from **different
cells**: the first from the cell where $A$ is stated first, the second from the
cell where $B$ is. Every emitted statement names the cell as well as the
configuration, and §17.5's emitter refuses a statement that does not.

Quantities are additionally reported **pooled within block**, meaning the two
order variants of each cell averaged inside the block before the contrast is
formed. That is a single within-block estimand and carries no claim.

### 11.2 Delivery loss, chance compliance, and the counterfactual baseline

For an outcome constraint $c$ and companion $g$,

$$D(c \leftarrow g) \;=\; \mathbb{E}\!\left[\bar X_{c,\text{solo}}\right] - \mathbb{E}\!\left[\bar X_{c,\;c+g}\right],$$

both terms over the same 384 blocks, so the contrast is paired within block.

$$\kappa_c = \mathbb{E}\!\left[\bar X_{c,\;\text{unconstrained}}\right], \qquad
\iota_c = \frac{\mathbb{E}\!\left[\bar X_{c,\text{solo}}\right] - \kappa_c}{1 - \kappa_c}, \qquad
H_c = \mathbb{E}\!\left[\bar X_{c,\text{solo}}\right] - \kappa_c .$$

$$\kappa^{B}_c = \mathbb{E}\!\left[\bar X_{c,\;B\text{ solo}}\right], \qquad
\Sigma_c = \kappa^{B}_c - \kappa_c, \qquad
\hat p_c = \kappa^{B}_c + \iota_c\,(1 - \kappa^{B}_c).$$

$\kappa^{B}_c$ is $c$'s verdict on the $B$-solo cell, where $c$ is **absent**.
It is a chance observation under §9.1's presence rule, it reads no composed
cell, and §13.6 registers its only use.

$\iota_c$ is undefined when $\kappa_c = 1$; a constraint with $\kappa_c \ge
0.99$ in the confirmatory data is reported with its difficulty coordinate
withheld and `DIFFICULTY_COORDINATE_DEGENERATE`, and its spectrum point is
dropped from the fit with the drop recorded. §13.4's chance ceiling of 0.75
makes this unreachable for an admitted companion without contradicting the
admission record, and the rule exists so the contradiction is reported rather
than divided by zero.

### 11.3 Primary estimands

Per configuration, six:

$$D(B \leftarrow A), \qquad D(A \leftarrow B), \qquad \Lambda = D(B \leftarrow A) - D(A \leftarrow B),$$
$$\Delta_R = D(B \leftarrow A) - \tfrac{1}{3}\sum_{j=1}^{3} D(B \leftarrow R_j), \qquad \delta_{\text{diff}}\ (\S11.8), \qquad \Xi\ (\S11.7).$$

$\Delta_R = \frac{1}{3}\sum_j \mathbb{E}[\bar X_{B,\,B+R_j}] - \mathbb{E}[\bar X_{B,\,A+B}]$:
the solo baseline cancels, so $\Delta_R$ is unaffected by solo ceiling, solo
noise, or any property of the solo cell. $\delta_{\text{diff}}$ has the same
property (§11.8).

### 11.4 The position caveat, registered

A solo cell states its single constraint in position one. $D(c \leftarrow g)$ is
therefore position-matched to its baseline only in the configuration where $c$
is stated first; in the other it confounds added load with a change of
position. $\Delta$-type quantities difference two composed cells with $c$ in
the same position and are position-clean in both configurations. The order
contrasts of §11.7 are differences of composed cells and are position-clean by
the same argument.

Consequences: every emitted L1 statement names the position of the outcome
constraint; the L1 claim in the position-shifted configuration is stated as
"composition and position change together" and carries `POSITION_CONFOUNDED`;
and $\Delta_R$, $\Delta_{\text{near}}$, $\delta_{\text{diff}}$ and the order
contrasts are the quantities that carry the companion-identity and order
claims.

### 11.5 Secondary estimands

Per configuration, all with simultaneous intervals within their family (§15):

- **Companion heterogeneity.** $D(B \leftarrow R_j)$ and
  $\Delta_j = D(B \leftarrow A) - D(B \leftarrow R_j)$ for each core $j$.
- **Outcome-side control.** $D(A \leftarrow R_j)$ for each $j$, and
  $\Delta^A = D(A \leftarrow B) - \frac{1}{3}\sum_j D(A \leftarrow R_j)$,
  retained as a demoted diagnostic subject to outcome headroom, a matched
  companion, and the configuration quoted with the number.
- **Reciprocal losses.** $D(R_j \leftarrow B)$ and $D(R_j \leftarrow A)$.
- **Spectrum losses.** $D(B \leftarrow R_{f,s})$ and each companion's realised
  $\iota$.
- **Near-form arm.** $D(B \leftarrow N_k)$ for $k = 1,2,3$ and
  $\Delta_{\text{near}} = D(B \leftarrow A) - \frac{1}{3}\sum_k D(B \leftarrow N_k)$.
- **Broad-class arm.** $\Delta_{\text{broad}} = D(B \leftarrow A) - D(B \leftarrow CL)$,
  $D(B \leftarrow CL)$, $\iota_{CL}$ and the realised $\lvert\iota_{CL} - \iota_A\rvert$.
- **Joint-state redistribution.** For each composed cell the four-state vector
  $p = [P(0,0), P(0,1), P(1,0), P(1,1)]$, reported within cell and never
  differenced across cells with different constituents.
- **Joint success.** $P(X_{c_1} = 1, X_{c_2} = 1)$ per composed cell.
- **Chance, lift, displacement and projection.** $\kappa_c$, $H_c$, $\iota_c$,
  $\kappa^{B}_c$, $\Sigma_c$ and $\hat p_c$ for every registered instance, with
  the calibration and confirmatory values side by side. **The confirmatory
  $\hat p_c$ against the realised composed compliance is the prospective test
  of §13.6's projection**, is reported for every companion, and licenses no
  claim.

### 11.6 The reciprocal specificity estimand

Writing $D(\bar R \leftarrow g) = \frac{1}{3}\sum_j D(R_j \leftarrow g)$ for a
companion $g$ outside the core reference set, and
$D(\bar R \leftarrow \bar R') = \frac{1}{6}\sum_{j \ne k} D(R_j \leftarrow R_k)$
over the six ordered pairs of distinct core references:

$$\Xi = \Delta_R - \left[D(\bar R \leftarrow A) - D(\bar R \leftarrow \bar R')\right].$$

$\Xi$ asks whether the excess damage from $A$ is specific to the outcome $B$ or
is a property of $A$ as a companion to anything. It gates the wording of every
L3 statement (§3.2), so it is a member of the primary family F1 and carries the
multiplicity cost of being one.

### 11.7 The order contrasts, new in v5

v4r4 measured large configuration dependence — $\Lambda$ moving from $-0.110$
to $+0.315$ on one model with both within-configuration intervals excluding
zero — and registered **no** cross-configuration contrast, so the question
could not be answered and could not be answered afterwards either: the records
store no bootstrap replicates. v5 registers the contrasts directly.

$$\text{Ord}_A = D(A \leftarrow B)\big\vert_{\text{first}} - D(A \leftarrow B)\big\vert_{\text{second}},$$
$$\text{Ord}_B = D(B \leftarrow A)\big\vert_{\text{first}} - D(B \leftarrow A)\big\vert_{\text{second}},$$
$$\text{Ord}_\Lambda = \Lambda\big\vert_{\text{first}} - \Lambda\big\vert_{\text{second}} = \text{Ord}_B - \text{Ord}_A,$$
$$\text{Ord}_{\bar R} = \tfrac{1}{3}\textstyle\sum_j \left[ D(B \leftarrow R_j)\vert_{\text{first}} - D(B \leftarrow R_j)\vert_{\text{second}} \right], \qquad
\text{Ord}_{CL} = D(B \leftarrow CL)\vert_{\text{first}} - D(B \leftarrow CL)\vert_{\text{second}} .$$

**Each is a contrast between two composed cells and the solo baseline cancels.**
$\text{Ord}_A = \mathbb{E}[\bar X_{A,\,B+A}] - \mathbb{E}[\bar X_{A,\,A+B}]$,
and likewise for the others: they are position-clean, baseline-free, and paired
within block because order is a within-block factor. An executable check
computes each in both algebraic forms and refuses a disagreement above
$10^{-9}$.

**$\text{Ord}_\Lambda$ is linearly dependent** on $\text{Ord}_A$ and
$\text{Ord}_B$. It is registered anyway, because it is the asymmetry's own
order dependence and is the quantity a reader of v4r4's sign reversal wants;
the dependence is declared here and the family's simultaneous interval accounts
for its members as declared without pretending they are independent.

**Family and multiplicity.** The order contrasts form family **F11**, the one
family in this protocol declared **across** configurations. Its simultaneous
interval is computed by the same studentised maximum-modulus construction, on
the same block bootstrap, with the same index vector applied to every member in
each resample. F1's membership is unchanged, so registering the order contrasts
does not widen any primary interval.

**Interpretation, fixed in advance.** An $\text{Ord}$ interval excluding zero
licenses **L4b** for that named quantity: *the quantity depends on the position
of the outcome constraint, by the registered contrast*. It licenses no
statement about **why**, and in particular no statement about which constraint
"wins" the register — §22's length and register diagnostics are descriptive and
§29 records that the mechanism is not identified. An $\text{Ord}$ interval
containing zero is **not** evidence of order-invariance unless §17.3's
equivalence rule and its precision precondition are met.

### 11.8 The difficulty-response relation and $\delta_{\text{diff}}$

**The points.** Nine non-$A$ companions enter: the three core references and
the six spectrum companions, three families $f$ with three severities each. For
companion $R_{f,s}$ write $d_{f,s} = \iota_{R_{f,s}}$ and
$Y_{f,s} = D(B \leftarrow R_{f,s})$, both measured on the confirmatory blocks in
the configuration being estimated. $A$, the near-form controls and $CL$
contribute **no point**.

**The primary functional form**, fixed here and unchangeable after freeze:

$$Y_{f,s} = \alpha_f + \beta\, d_{f,s} + \varepsilon_{f,s},$$

three family intercepts and one common slope, fitted by ordinary least squares
on the nine points with every point weighted equally.

**The prediction at $A$.** $A$ belongs to no family, so the prediction uses the
average intercept, $\hat Y_A = \bar\alpha + \beta\, d_A$, which with three
equal-sized families is $\hat Y_A = \bar Y + \hat\beta\,(d_A - \bar d)$ over the
nine points.

$$\boxed{\;\delta_{\text{diff}} = D(B \leftarrow A) - \hat Y_A\;}$$

$A$ is excluded from the fit that predicts $A$; §13.11 makes that executable.
The prediction weights sum to one, so the $B$-solo baseline cancels exactly as
it does in $\Delta_R$ and $\delta_{\text{diff}}$ is a contrast among composed
cells alone. An executable check computes both forms and refuses a disagreement
above $10^{-9}$.

**A secondary fit with a tier indicator.** The three near-form companions
supply three further points at a different structural tier. A secondary fit
$Y = \alpha_f + \beta d + \gamma\,\mathbb{1}[\text{Tier }2]$ over twelve points
is reported with $\hat\gamma$ and its interval, as a **secondary** in family F8.
It licenses no claim and is registered so that the tier's contribution is
reported rather than absorbed silently into a residual.

**Why not a richer primary form.** With nine points and four parameters the fit
has five residual degrees of freedom. A per-family slope would leave three, and
a non-linear form would be fitted to three points per family.

**Relation to $\Delta_R$.** When $\hat\beta = 0$ and the three families are
equal-sized, $\delta_{\text{diff}}$ reduces to $D(B \leftarrow A)$ minus the
unweighted mean of nine companion losses. That is the correct behaviour when
difficulty does not predict the loss, and it means the two estimands are
correlated, which is why they sit in one simultaneous family and why §17.6
registers what their disagreement means.

### 11.9 Thresholds and regions

| Quantity | Threshold | Provenance |
|---|---|---|
| $\Delta_R$ generic-load threshold | 0.10 | `dci-construct-pass2.md` §G row 1, 14 August 2026, verbatim |
| $\Delta_R$ pair-specific threshold | 0.25 | Same |
| $\Delta_{\text{near}}$ | 0.10 only, direction and the generic-load threshold | The memo's 0.25 is defined for a matched-reference contrast and is not transferred to a different reference tier |
| $\Delta_{\text{broad}}$ | direction only | One companion bounds a class effect and does not estimate it |
| $\delta_{\text{diff}}$ direction | 0 | No magnitude threshold is transferred |
| $\delta_{\text{diff}}$ equivalence region | $\pm 0.10$ | The registered smallest effect of interest |
| Order contrasts | direction only, and $\pm 0.10$ for equivalence | The SESOI is about the compliance scale and an order contrast is a difference of two compliance differences on that scale; no magnitude threshold is invented |
| Smallest effect of interest for $D$, $\Lambda$, $\delta_{\text{diff}}$, $\text{Ord}$ | 0.10 | Carried from v3 §11: a change of 0.10 moves a system prompt from 80% to 70% compliance |
| $\Xi$ | direction only | §11.6 |
| Precision preconditions | half-width $\le 0.05$ for $D$, $\Delta_R$, $\Delta_{\text{near}}$, $\delta_{\text{diff}}$, $\text{Ord}_A$, $\text{Ord}_B$; $\le 0.08$ for $\Lambda$ and $\text{Ord}_\Lambda$; $\le 0.06$ for $\Delta_j$ | §16.2 |

**No threshold is derived from any screen, from v4r4's confirmatory estimates,
or from any development analysis.** The two $\Delta_R$ thresholds predate every
observation in this constraint vocabulary. The *admission* thresholds of §13
are a different matter and were chosen from development evidence; §13.15 says
so explicitly and §30 records it.

---

## 12. Operating regime and severity selection

The design dependency order is followed: the construct and estimands are fixed
above; the operating regime is found next; references are qualified, calibrated
and selected only afterwards.

### 12.1 Completion cap

A fixed subject-balanced set of 96 pre-screen prompts is generated at **each**
cap in $\{512, 768, 1024\}$ — every cap, because the whole table is the
registered diagnostic. The set is four prompts per pre-screen topic under the
§8.5 template: the unconstrained cell; $A$ alone at $n = 8$; $B$ alone at the
tightest registered $m$; and $A + B$ at those severities. The smallest cap whose
truncation rate over the one- and two-constraint prompts is at most 0.10 is
selected and held fixed. If none qualifies the replication terminates
`RESPONSE_LENGTH_INCOMPATIBLE`. Any quantity derived from a cell whose
truncation rate exceeds 0.10 is reported as a bound.

### 12.2 The regime screen, high-recall by construction

At the selected cap, the screen measures on the 24 pre-screen topics, one draw
per cell: the unconstrained cell, the full $n$ grid for $A$, the full $m$ grid
for $B$ **including the conditional extension**, and every round-0 ladder
severity of §7.10 — 326 rungs.

**The unconstrained rows carry a chance verdict for every severity of the
declared range**, all 632 instances, scored on the same responses by the same
verifiers without the instruction being present.

**The screen's purpose is recall, not selection, and that is v5's change.**
v4r4 used the same screen as a hard selector: §12.3 shortlisted six reference
families by point-estimate distance from $\iota_A$ and §13.4 then re-measured
only the shortlist, so a candidate discarded here could never return. The
measured cost of that is in
`dci1/reports/dci1v5/reference_design_development.md` §1: the two stages'
$\iota$ estimates disagree by a median of 0.071 and **35.7% of candidates move
further between them than the whole width of the caliper they then have to
clear**, while $\iota_A$ itself moves by up to 0.048.

**The v5 retention rule.** A candidate rung is carried into calibration when
**either** of the following holds:

1. it survives the **structural** screen of §12.4 — the checks that no amount
   of data will change: tier admissible for some slot, wording caliper,
   parse independence, formal and realistic witnesses, and a declared metadata
   record consistent with its predicate; **and** its pre-screen 95% Wilson
   interval for raw solo compliance intersects $[0.05, 0.95]$;
2. or its family is Tier 1 or Tier 2, in which case **every** rung of its
   round-0 ladder is carried regardless of its pre-screen estimate.

Rule 2 exists because the core pool is small, its rungs are cheap to measure,
and a Tier-1 family's difficulty is tunable through $q$: discarding a rung on
24 topics at one draw would discard the tuning. **No candidate is discarded on
a pre-screen point estimate of $\iota$, and no pre-screen quantity enters any
admission decision in §13.** The pre-screen distance caliper of v4r4 §13.4
condition 2 is **removed**; §13.7's two-split stability rule replaces the
winner's-curse protection it was there to provide, at a sample size that can
support it.

**Cost.** Rule 2 carries all 88 Tier-1 and Tier-2 rungs. Rule 1 carries
whichever Tier-3 rungs pass; on v4r4's measurements that is of order 30 to 60
per model. §12.7 registers the calibration cap.

### 12.3 Selecting $n^*$ and $m^*$, with bracketing

**Solo calibration.** On **each** of Calibration-A and Calibration-B at
$M_{\text{cal}} = 4$: the unconstrained cell, the full $n$ grid, the registered
$m$ grid, and every carried candidate rung.

**Selection of $n^*$.** Eligible values put solo compliance of $A$ in
$[0.50, 0.85]$ on the **pooled** 192 topics. Among them $n^*$ minimises the
distance from 0.70, with the smaller $n$ breaking an exact tie.

**Selection of $m^*$.** Eligible values put solo compliance of $B$ in
$[0.60, 0.95]$ on the pooled 192 topics. Among them $m^*$ minimises the
distance from 0.80, with the **smaller** $m$ breaking an exact tie.

**The bracketing rule, new in v5.** A selected severity is **bracketed** when
both neighbouring severities of its grid are measured at calibration precision.
If the selected $m^*$ is the top of the registered grid, the extension
$\{15,16\}$ is measured on both calibration splits and selection re-runs over
the union; if it is then still the top of the measured range the replication
records `OPERATING_POINT_AT_GRID_BOUNDARY`, which is an identification status
and not terminal. If no severity of the registered grid or its extension is
eligible the replication records `FOCAL_RANGE_EXHAUSTED`.

$A$'s construct has a genuine floor at $n = 1$: $n = 0$ is a well-formed exact
count whose chance compliance is the probability that an unconstrained answer
contains no *however*, which is near one, so it is chance-degenerate and is not
in the grid. Where $n^* = 1$ the bracketing rule cannot be met on the easy side
and the record carries `OPERATING_POINT_AT_GRID_BOUNDARY` with that reason.

$n^*$ and $m^*$ are selected on **raw solo compliance**, not on $\iota$,
because the bands exist to give an outcome constraint room to fall under
composition, which is a statement about its realised compliance. $\iota_A$ and
$\iota_B$ are recorded at the selected severities and enter §13. No eligible
value returns `TARGET_RANGE_EXHAUSTED` or `FOCAL_RANGE_EXHAUSTED`, or
`GRID_RESOLUTION_INSUFFICIENT` when two adjacent registered severities lie on
opposite sides of a whole band. Every diagnosis records the complete curve.

### 12.4 Regime adequacy

A replication proceeds only when, on the pooled calibration topics:

1. solo compliance of $A$ and of $B$ lie inside their bands;
2. the realised solo vacuity rate for $B$ is at most 0.10;
3. the graded distribution of each outcome constraint is non-degenerate,
   meaning **the share of responses whose graded score exceeds 0.99, and the
   share whose graded score falls below 0.01, are each at most 0.99**.

Otherwise the replication records `REGIME_NOT_FOUND`, which is a statement
about the registered grid and never about the model or the hypothesis.
Condition 3 is a statement about a **share**, not about a mean; read as a
statement about the mean it fires on every severity §12.3 declares eligible and
contradicts its own neighbour.

### 12.5 What development may inspect, and when the vocabulary freezes

**Development data for this study** is the 24 pre-screen topics and the 192
calibration topics, and nothing else. Iterative work — checking difficulty
coverage, vacuity, chance compliance, counterfactual chance compliance,
verifier behaviour, response lengths, structural validity — is permitted on
those topics and on those quantities.

**Prohibited during all of it, and prohibited afterwards**: inspecting
$D(B \leftarrow g)$, any other composed interference outcome, any joint state,
or any contrast between two composed cells, for the purpose of deciding which
families or severities are kept. The valid sequence is fixed:

> propose the candidate vocabulary → measure solo, chance and counterfactual-chance
> properties → improve difficulty coverage → **freeze the family and ladder
> vocabulary and the selection rule** → only then observe composed outcomes.

**Development data for the design of this document** is the whole of the
completed v4r4 study, including its composed tables. That is a different and
broader permission, it is what §30 declares, and it expires at adoption: from
the moment the v5 registration manifest is signed, no v4r4 or v5 composed
outcome may change any rule in this document.

**The family vocabulary of §7, the declared range of every ladder, the
expansion rule and coverage criterion of §12.6, and every component of §13 with
every threshold in it, are frozen by this document** and enter the signed
registration manifest before the first qualification. They are study-wide and
no replication's outcome can change them.

### 12.6 Candidate expansion, and the coverage criterion that stops it

**What may be inspected.** Solo compliance, chance compliance, counterfactual
chance compliance under $B$, instructed compliance, instruction lift, vacuity,
graded distribution, response length, measurement precision, verifier
behaviour, satisfiability, non-entailment, wording caliper, structural
metadata, tier and class — on the pre-screen and calibration topics, and
nowhere else.

**What may never be inspected**: $D(B \leftarrow g)$, $\Delta$ of any kind,
$\delta_{\text{diff}}$, $\Xi$, any joint state, any composed cell, any contrast
between two composed cells. §13.11 is the executable form.

**The identification-coverage criterion**, evaluated on the pre-screen table
with eligibility as §13's band on $\iota$ and its vacuity ceiling. Write
$\iota_A$ for the pre-screen instructed compliance of $A$ at the severity whose
solo compliance is nearest §12.3's aim.

| | Condition | Value, and where it comes from |
|---|---|---|
| C1 | an eligible reference rung strictly below $\iota_A$ and one strictly above | interpolation rather than extrapolation |
| C2 | at least **3** eligible **Tier-1 or Tier-2 feature groups** on each side of $\iota_A$ | §13.12 needs three straddling triples |
| C3 | at least **8** eligible rungs within **0.15** of $\iota_A$, from at least **4** feature groups | §13.8's caliper region; eight is two per core slot plus two backups |
| C4 | at least **6** feature groups contain a family that straddles $\iota_A$ with at least **3** eligible rungs spanning at least **0.40** in $\iota$ | three groups plus **three** spare, against v4r4's one; the measured attrition was 50–100% |
| C5 | at least **16** eligible rungs in total | §13.12 delivers nine fit points; sixteen is a floor with slack |
| C6 | at least **8** eligible Tier-1 or Tier-2 families, from at least **6** feature groups | the whole registered Tier-1 vocabulary, so the criterion is a real screen |
| C7 | at least one eligible **Tier-3 budget** rung within **0.15** of $\iota_A$ | §13.10's broad-class arm |
| C8 | at least **3** eligible **Tier-2** rungs from three feature groups | §13.9's near-form arm |

**C1 to C6 are decisive** for the core and spectrum arms. **C7 and C8 are
not**: failing C7 drops the broad-class arm with `CLASS_ARM_NOT_AVAILABLE`, and
failing C8 drops the near-form arm with `NEAR_FORM_ARM_NOT_AVAILABLE`. Neither
stops the study.

**C4's "three spare" is the direct repair of v4r4's F5.** v4r4 registered four
straddling families against a requirement of three — one spare — and lost 50%
to 100% of them between the pre-screen and calibration on every replication.

**The expansion rule.** While C1–C6 are not all met and rounds remain, one
round is run. Per family, in registered family order: if the family's measured
rungs bracket $\iota_A$, admit the reserve rungs lying strictly between the two
adjacent measured severities whose $\iota$ values bracket it; otherwise admit
the reserve rungs immediately beyond the family's extreme measured severity on
the deficient side. At most **four** rungs per family per round and at most
**two** rounds. Only the newly admitted rungs are generated, on the same 24
topics at the same cap. The loop stops the moment C1–C6 pass.

**The rule can only pick, never invent.** Everything it returns is already in
the frozen reserve of §7.10; it reads $\iota$ and severity and nothing else;
and it is deterministic given the table.

**When it stops without passing.** If two rounds complete and C1–C6 are still
not all met — or the reserve is exhausted first — the replication records
`REFERENCE_SUPPORT_NOT_IDENTIFIED` **at design time**, runs without the core
and spectrum arms, and never reports a $\Delta_R$ or a $\delta_{\text{diff}}$
obtained from an unqualified pool. This is a registered outcome and not a
fallback to be avoided: no band is widened, no vacuity ceiling lowered and no
severity authored to reach it.

**Then the vocabulary freezes.** The regime-screen record names every measured
rung. Every later stage selects from that named set, and Gate 1 certifies
exactly the instruments the freeze contains.

### 12.7 The calibration budget, and the asymmetry between the two splits

**Calibration-A measures the whole carried set.** That is all 88 Tier-1 and
Tier-2 rungs, which §12.2 rule 2 carries unconditionally, **plus at most 24
Tier-3 rungs**, ordered by ascending pre-screen
$\lvert\iota - \iota_A\rvert$ when more than 24 are carried. That ordering is
**the one place a pre-screen point estimate still decides anything, and it
decides only which Tier-3 rungs are measured when the budget binds** — never
admission, and never anything about Tier 1 or Tier 2. The cap, the priority and
the realised list are recorded on the Gate-2 record.

**Calibration-B measures only the candidates admissible on Calibration-A**,
under $V_{\text{head}}$, $V_{\text{chance}}$, $V_{\text{inter}}$ and
$V_{\text{diff}}$ evaluated on Calibration-A alone — plus $A$'s grid, $B$'s
grid and the unconstrained cell, which both splits always measure in full.

**Why this asymmetry costs nothing.** §13.7 condition 1 requires a candidate to
be independently admissible on **both** splits, so a candidate failing on
Calibration-A is excluded whatever Calibration-B would have said. Restricting
Calibration-B to A-survivors therefore changes no verdict, and it changes no
pooled quantity that any admitted candidate's admission depends on. What it
does change is that the two splits are not interchangeable in role: A screens
and B confirms. That is stated rather than presented as symmetry, and it is the
reason §13.7's stability rule is phrased as *admissible on both* rather than as
a test of which split is right.

**Cost.** Calibration-A: at most $(1 + 8 + 8 + 112) \times 96 \times 4 =
49{,}536$ generations, plus 768 if §7.2's extension is measured.
Calibration-B: $(1 + 8 + 8 + k) \times 96 \times 4$ for $k$ A-survivors; on
v4r4's measured admission rates $k$ is of order 10 to 25, giving about 10,000 to
16,000. Pre-confirmatory generation per replication is therefore about 8,300
for the dense screen, 60,000 to 66,000 for calibration, 288 for the cap
selection and $56 \times 24 \times 4 = 5{,}376$ for Gate 4 — roughly 75,000
against 172,032 confirmatory.

---

## 13. Reference validity

### 13.1 What a reference is for, and what makes one valid

Under the primary question a reference occupies the **companion** slot in place
of $A$. It estimates the counterfactual *"what would composing $B$ with a
comparable non-$A$ companion have cost?"*. It therefore has to resemble $A$,
and its resemblance to $B$ is irrelevant.

v4r4 answered "resemble $A$" with one number: a caliper on instructed
compliance. §2.3 records the five ways that failed. v5 answers it with a
**conjunction of registered components, evaluated lexicographically**:

$$V(R) = V_{\text{spec}} \wedge V_{\text{sat}} \wedge V_{\text{head}} \wedge V_{\text{chance}} \wedge V_{\text{struct}} \wedge V_{\text{inter}} \wedge V_{\text{stab}} \wedge V_{\text{diff}}$$

Evaluated in that order. **The first failing component is the recorded
rejection reason and later components are not evaluated**, so every rejection
names the earliest and most fundamental thing wrong with the candidate rather
than the most convenient.

**The order decides which reason is recorded and not which candidates pass.** A
conjunction's truth value does not depend on evaluation order, so no candidate
is admitted or rejected because of where a component sits in the sequence. The
order is a reporting rule, and it is registered because a rejection reason that
varies with implementation detail is not evidence.

**There is no weighted composite score, and none is registered.** A weighted
score needs weights, weights need to be fixed before v5 data, and the
development evidence is four models — not enough to fix weights that would
generalise to an unseen candidate family. §34 D5 records the alternative as a
decision this document does not take.

The machine-readable statement of the whole rule is
`dci1/reports/dci1v5/reference_design_spec.json`. Where that file and this
section disagree, **this section governs**, and the disagreement is a defect to
be repaired in the file.

### 13.2 The registered difficulty coordinate

$$\iota_c = \frac{P(X_c = 1 \mid c \text{ alone}) - \kappa_c}{1 - \kappa_c},$$

with $\kappa_c$ measured in the unconstrained cell of the same topic set at the
same $M$ under the same prompt. It is computed by one named function from
stored verdicts, on the calibration topics for every selection in §13, and on
the confirmatory blocks for every estimand in §11.

**Raw solo compliance is a registered secondary coordinate.** Every selection
table records both; every fit of §11.8 is computed a second time on the raw
coordinate and reported; and §17.6 registers what a disagreement between the
two coordinates means.

### 13.3 $\iota$ is the difficulty coordinate and is **not** the admission coordinate

This is v5's central structural change and it is stated as a rule rather than
as an emphasis: **$V_{\text{diff}}$ is the last component evaluated.** A
candidate reaches the caliper only after specification, satisfiability, raw
headroom, chance, structure, interaction and stability have all passed. In
v4r4, $\iota$ proximity was effectively the whole of admission, and a rung at
raw solo compliance 0.9740 with chance compliance 0.9323 was admitted **because
its $\iota$ was the closest available**, and terminated its replication on its
own solo cell.

$\iota$ is retained because it is the only coordinate comparable across
constraint classes and because the difficulty-response relation must be read
against something. It is demoted because a ratio of two estimated quantities
with a denominator approaching zero is not a certificate of comparability.

### 13.4 $V_{\text{head}}$ and $V_{\text{chance}}$: raw compliance rules

| Component | Rule |
|---|---|
| $V_{\text{head}}$ | the 95% Wilson interval for $p_{\text{solo}}(R)$ on the pooled 192 calibration topics lies inside $[0.10,\, 0.90]$ |
| | the instruction lift $H_R = p_{\text{solo}}(R) - \kappa_R \ \ge\ 0.20$ |
| | the solo vacuity rate is at most $0.10$ |
| $V_{\text{chance}}$ | $\kappa_R \le 0.75$, and the 95% Wilson upper bound on $\kappa_R$ is at most $0.85$ |

**Derivations, each an argument and not a fitted value.**

- **The band $[0.10, 0.90]$** is §13.14's composed-headroom band $(0.05, 0.95)$
  contracted by 0.05 on each side. The contraction is applied to the
  **interval** and not to the point estimate, so an imprecisely measured
  candidate cannot sit on the boundary — which is the defect §12.2 measures at
  the pre-screen, applied here to a different quantity.
- **The lift floor $0.20$.** A reference cannot lose more compliance under
  composition than stating it ever bought: $D(R \leftarrow B) \le H_R$. The
  registered smallest effect of interest is 0.10, so a reference with
  $H_R < 0.20$ cannot exhibit a reciprocal loss of two SESOI however the model
  behaves, and family F7's reciprocal estimands would be bounded by the design
  rather than by the model.
- **The chance ceiling $0.75$.** $\iota$'s sampling variance carries a
  $1/(1-\kappa)$ amplification: 4 at $\kappa = 0.75$, 10 at $\kappa = 0.90$.
  The measured split-half $\lvert\Delta\iota\rvert$ on v4r4's calibration data
  rises from 0.044 for chance-free candidates through 0.110 in
  $0.25 \le \kappa < 0.75$ to 0.195 at $\kappa \ge 0.75$. The ceiling sits where
  the empirical instability reaches roughly three times the chance-free value
  while the amplification factor is still single digit. v4r4's value was
  **0.99**, which is a degeneracy guard and not a ceiling.

`CHANCE_DEGENERACY_MAX` remains 0.99 and remains the point at which $\iota$ is
undefined and `DIFFICULTY_COORDINATE_DEGENERATE` is recorded. It is not an
admission threshold in v5 and §13.4's ceiling is.

### 13.5 $V_{\text{spec}}$, $V_{\text{sat}}$ and $V_{\text{struct}}$

$V_{\text{spec}}$: the family and severity carry a complete §10.7 A
specification record, pass A′'s direction invariant, and are inside §7.7's 20%
wording caliper against $A$, with parse independence established.

$V_{\text{sat}}$: §7.7's formal joint-satisfiability and non-entailment
witnesses pass against $A$ at $n^*$, against $B$ at every admissible $m$, and
against every other admitted companion at its admitted severity; **and §7.7's
realistic witness against $B$ at $m^*$ lies inside the stem band.**

$V_{\text{struct}}$: the family's declared `structural_tier` admits the slot
under §7.4, and the core reference set contains at least two Tier-1 members
drawn from three distinct feature groups.

### 13.6 $V_{\text{inter}}$: the interaction rule

**The problem it names.** A control can be validly matched on every solo
quantity and still be worthless, because the outcome constraint changes the
response distribution its verifier integrates over. v4r4's
`gemma-3n-e2b-it` terminated because `RF11` — *at most $q$ words may begin with
a vowel* — was composed with $B$: $B$ shortens words and shortens answers, the
vowel-initial count fell from ≈24 to ≈17, and a budget of 26 became trivially
satisfiable, taking `RF11:26` from 0.635 solo to 0.969 composed. Pairing the
same rung with other references barely moved it. **The ceiling was produced by
$B$ specifically — the outcome constraint of the whole study.**

**The quantity that sees it before composing.** Under §9.1 every generation is
scored on every registered instance, so $R$'s verifier is already run on
responses written under $B$ **alone**:

$$\kappa^{B}_R = P\!\left(X_R = 1 \;\middle|\; B \text{ alone at } m^*,\ R \text{ absent}\right).$$

$R$ is never stated in those prompts. This is a chance verdict under a
different load-one treatment. It reads no composed cell, no contrast between
composed cells, and $B$'s compliance in no cell, and it costs **zero extra
generations**.

**The projection.**

$$\hat p_R = \kappa^{B}_R + \iota_R\,\bigl(1 - \kappa^{B}_R\bigr)$$

is $\iota_R$ evaluated at the counterfactual baseline $B$ induces rather than
at the unconstrained baseline. It is the definition of instructed compliance
re-evaluated in the regime the reference will actually be used in.

**The rule.**

$$V_{\text{inter}}(R) \iff 0.10 \;\le\; \hat p_R \;\le\; 0.90 \quad\text{and}\quad \bigl\lvert \Sigma_R \bigr\rvert = \bigl\lvert \kappa^{B}_R - \kappa_R \bigr\rvert \;\le\; 0.25 .$$

**Derivations.** The band is §13.14's $(0.05, 0.95)$ contracted by one
registered **projection-error allowance** of 0.05 on each side. The allowance is
§16.2's precision precondition for $D$, and it is close to the realised median
absolute projection error of 0.067 measured in
`dci1/reports/dci1v5/reference_design_development.md` §4.3. The displacement
bound catches the **floor** direction, which the projection does not: on
`qwen3-4b`, `CL7:30` moved from $\kappa = 0.849$ to $\kappa^{B} = 0.122$, so
its measured difficulty described a response distribution $B$ destroys.

**What the development evidence showed, and what it does not establish.** On
`gemma-3n-e2b-it` — the only v4r4 replication that ever composed a reference
with $B$ — the projection was computed for 20 composed rate checks from
pre-composition quantities alone. Median absolute error 0.067; at a ceiling of
0.90 it caught 4 of 4 composed-headroom failures with 0 false alarms among 16
passing checks. **Twenty rate checks on one model is design fitting.** The 0.90
ceiling happens to sit inside the observed gap between the highest passing
projection (0.8836) and the lowest failing one (0.9388); it is derived from the
band and the error allowance and not from the gap, and the coincidence is
recorded rather than used as evidence.

One property makes the gate robust where it binds: as $\kappa^{B}_R \to 1$ the
projection $\to 1$ whatever $\iota_R$ is, so it is least sensitive to the
transfer assumption exactly where it decides.

**Why this is not outcome-based selection.** $\Delta_R$ reads $X_B$ in the
$B{+}R_j$ cells; the $B$-solo baseline cancels. $\kappa^{B}_R$ reads $X_R$ in
the $B$-solo cell. Different verdict, different rows, and $\kappa^{B}_R$
observes $B$'s compliance nowhere. The residual-bias direction is checkable: a
reference $B$ makes trivial would show a **small** $D(B \leftarrow R_j)$, which
would make $\frac{1}{3}\sum_j D(B \leftarrow R_j)$ small and $\Delta_R$
**large**, so excluding such references is conservative with respect to
$H_{\text{pair}}$ and not favourable to it.

**Generality.** The rule names a property of the pair (statistic, focal
constraint) and measures it. It excludes no family by name. It is not *"exclude
`RF11`"*; it is *"exclude a candidate whose verifier statistic the focal
constraint's own response-distribution shift moves into a degenerate region"*,
and `RF11` is excluded on a model where that is measured to happen.

**When $\kappa^{B}$ cannot be measured.** $\kappa^{B}$ requires $m^*$, so
$V_{\text{inter}}$ is evaluated at Gate 2.5, after Gate 2 and before any
selection. A candidate for which $\kappa^{B}$ is missing is **not admitted**;
absence is never read as a pass.

### 13.7 $V_{\text{stab}}$: two independent calibration splits

**The problem it names.** v4r4 measured candidates once, at 96 topics, and
selected the nearest inside a caliper of 0.10 — about 2.1 standard errors wide
on the measured split-half variance. Selection inside a two-SE window is
substantially selection on noise, and the winner's curse it produces is
observable as the pre-screen-to-calibration collapse of §12.2.

**The rule.** Calibration-A and Calibration-B are disjoint 96-topic sets
(§6.2), each measured at $M_{\text{cal}} = 4$ on the same candidate list. $R$
passes $V_{\text{stab}}$ when all three hold:

1. $R$ is **independently admissible** under $V_{\text{head}}$,
   $V_{\text{chance}}$, $V_{\text{inter}}$ and $V_{\text{diff}}$ on
   Calibration-A **and** on Calibration-B, each evaluated on that split alone;
2. the 95% percentile-bootstrap interval for
   $\iota_R^{A} - \iota_R^{B}$, resampling topics within split with 10,000
   resamples, lies wholly inside $\pm 0.20$;
3. the same interval for $p_{\text{solo}}^{A} - p_{\text{solo}}^{B}$ lies
   wholly inside $\pm 0.20$.

**Why an equivalence rule rather than a threshold on the difference.** A
threshold on the point difference **rewards** an imprecisely measured
candidate, whose difference is small by luck as often as by stability.
Requiring the interval to lie inside a bound **penalises** imprecision, which
is the correct direction for a gate whose question is *can this candidate's
coordinate be shown stable?*

**Why $\pm 0.20$.** It is twice the registered matching caliper. A coordinate
that cannot be pinned to twice the caliper across two independent 96-topic
splits cannot support matching at the caliper.

**What it implies, stated so it is not a surprise.** The rule is satisfiable
only when $\mathrm{SE}(\iota_R)$ at 96 topics is about 0.07 or better. On the
v4r4 measurements that holds for chance-free candidates (SE ≈ 0.033) and fails
for candidates near $\kappa = 0.75$ (SE ≈ 0.081). **$V_{\text{chance}}$ and
$V_{\text{stab}}$ therefore overlap**, and the overlap is registered rather than
removed: one is justified on validity and one on precision, and a rule that
holds for two reasons is not a rule to delete.

**$\iota_A$ is subject to the same rule.** $\iota_A$ is measured on both splits
and the same equivalence interval is required, because §12.2 measured $\iota_A$
itself moving by up to 0.048 between stages and both ends of every distance are
estimated.

### 13.8 $V_{\text{diff}}$ and core reference admission

Within family $f$, severity $q_f^*$ minimises
$\lvert \iota_{R_f} - \iota_A \rvert$ on the **pooled 192 calibration topics**,
subject to $V_{\text{spec}} \wedge V_{\text{sat}} \wedge V_{\text{head}} \wedge
V_{\text{chance}} \wedge V_{\text{struct}} \wedge V_{\text{inter}} \wedge
V_{\text{stab}}$ and to all of:

1. $\lvert \iota_{R_f} - \iota_A \rvert \le \mathbf{0.10}$;
2. the 95% Newcombe hybrid-score interval for the paired difference of the
   underlying solo compliance rates intersects $\pm \mathbf{0.05}$;
3. $\lvert p_{\text{solo}}(R_f) - p_{\text{solo}}(A) \rvert \le \mathbf{0.15}$
   on the secondary coordinate.

The less restrictive severity breaks an exact within-family tie. At most one
severity per family enters the core set.

**The three admitted core references** are chosen by the registered tie-break:
smallest $\lvert \iota_{R_f} - \iota_A \rvert$; then lower structural tier
(Tier 1 before Tier 2); then registered feature-group order; then the less
restrictive severity; then family identifier. **They come from three different
feature groups and at least two are Tier 1.** When the next qualifying family
belongs to a group already taken, or would take the Tier-1 count below two, it
is skipped and the following one takes the slot.

**They must additionally span at least two declared discourse roles** (§7.6).
When the three otherwise-chosen references share one role, the third slot goes
to the highest-ranked qualifying family of a different role and the
substitution is recorded. When none of the three shares $A$'s contrastive role,
`REFERENCE_ROLE_NOT_MATCHED` is recorded and attaches to every L3 statement
beside `REFERENCE_POOL_SAME_FORM`. Neither is terminal: role is a **declared**
property, §29 records that it controls discourse function by declaration only,
and a design that refused to run without a contrastive control would be
refusing on an unmeasured attribute.

**Condition 1's value does not move from v4r4's, deliberately.** The paired
standard error of $\iota$ over 192 topics at $M_{\text{cal}} = 4$ is about
0.034, so 0.10 is about 2.96 SE where v4r4's was 2.10. **What changed is the
sample, not the number.** Tightening the caliper would have selected harder on
a coordinate whose error is the size of the window, which is the defect §12.2
measures.

**Condition 3 is new.** Raw solo compliance is not comparable across the
production/budget divide, which is why it is a secondary coordinate. v5's core
pool is same-form and same-class as $A$ by construction, so within the core
pool that divide does not arise and the secondary coordinate is meaningful and
roughly 1.5 times more stable than $\iota$. It is a check on the primary, never
the selector.

**The realised gap is measured in the confirmatory data and reported.** The
confirmatory design contains the solo cell and the unconstrained cell of $A$
and of every admitted companion on all 384 blocks, so $\iota$ is re-estimated
there. When any realised $\lvert\iota_{R_j} - \iota_A\rvert$ exceeds **0.15**,
every L3 statement carries a fixed companion-difficulty block naming the
reference and its gap, and §23's sensitivity reports $D(B \leftarrow R_j)$
against the realised gap.

**The same applies to the interaction gate's own input, and this is registered
because §13.6 would otherwise have no realised check.** $\kappa^{B}_{R_j}$ is
estimated on the calibration splits and used to admit a reference that is then
composed on the confirmatory blocks, where $\kappa^{B}_{R_j}$ is measured
again on the $B$-solo cell of all 384 blocks. When any realised
$\lvert\kappa^{B}_{R_j}(\text{confirmatory}) - \kappa^{B}_{R_j}(\text{calibration})\rvert$
exceeds **0.15**, or the realised $\hat p_{R_j}$ falls outside §13.6's
admissible band, every L3 statement carries a fixed
`INTERACTION_ESTIMATE_DRIFTED` block naming the reference, both values and the
realised composed rate. It is an identification status and not a terminal one:
the reference was admitted under the registered rule on the registered data,
and a drift discovered afterwards is a finding about the rule, which is what
§26 says v5 exists to produce.

### 13.9 The near-form arm

Three Tier-2 controls $N_1, N_2, N_3$ are admitted from three distinct feature
groups, by the same $V(R)$ with the same thresholds, minimising
$\lvert\iota_{N} - \iota_A\rvert$ within family and then by the §13.8
tie-break. They occupy the companion slot **beside $B$ only** and never enter
the core reference set, the spectrum, the difficulty fit, $\Delta_R$,
$\bar R$ or $\Xi$; an executable check refuses a plan or an analysis input that
places one in any of them.

When fewer than three qualify, the arm is dropped, its nine cells are not
generated, and `NEAR_FORM_ARM_NOT_AVAILABLE` is recorded.
$\Delta_{\text{near}}$ is a registered secondary and is the second half of the
answer to $H_{\text{form}}$.

### 13.10 The broad-class arm

One Tier-3 **budget-class** companion $CL$ is admitted: the qualifying severity
across all Tier-3 budget families minimising $\lvert\iota_{CL} - \iota_A\rvert$,
ties broken by family identifier then by the less restrictive severity, subject
to the same $V(R)$. Where no severity qualifies the arm is dropped, its three
cells are not generated, and `CLASS_ARM_NOT_AVAILABLE` is recorded.

**The admitted companion is *matched* only when
$\lvert\iota_{CL} - \iota_A\rvert \le 0.15$.** When it is not, the arm still
runs, $\Delta_{\text{broad}}$ is still reported, and `CLASS_ARM_NOT_MATCHED` is
recorded on every statement about class.

$CL$ **never** enters the core set, the spectrum, the difficulty fit,
$\Delta_R$, $\bar R$ or $\Xi$. One companion cannot identify a class effect and
§5 says so; including it in the fit would let the line absorb the quantity the
arm exists to expose.

**The arm's direction is inverted from v4r4's**, and the inversion is the
point. v4r4's reference pool was budget class and its class control was
production; v5's reference pool is production and its class control is budget.
Both arrangements bound the same gap from opposite sides, and v5's is the one
in which the *references* — the quantities that carry the primary claim —
match $A$'s class rather than differ from it.

### 13.11 What is deliberately not a selection criterion, and how that is enforced

**Composed uptake is not a criterion.** Selecting a control on the outcome it
is meant to counterfactual is circular.

**Composed response length is not a criterion.** Composition shortens answers
and shorter answers satisfy budget constraints more readily, so response length
lies on the causal path from companion to outcome. It is a mediator (§22).

**No composed quantity of any kind is a criterion.** The executable form, on
the mandatory path:

- the selection functions of §13.8, §13.9, §13.10 and §13.12 accept a
  calibration table whose **schema** contains solo, chance, counterfactual-chance,
  displacement, vacuity, wording, witness, structural-metadata and tier fields
  and **no composed field**, and the loader refuses a table carrying one before
  any value is read;
- the schema is **closed**: an unknown column is refused, so a new field cannot
  smuggle in a composed quantity under an unlisted name;
- `kappa_under_b` and `displacement` are on the permitted list **by name**, and
  the loader additionally asserts that the rows supplying them are drawn from
  cells of load one whose single present constraint is $B$;
- the fit of §11.8 refuses an input containing $A$;
- the analysis refuses a spectrum set that is not a function of the frozen
  selection rule applied to the frozen calibration table;
- the freeze binds the selection rule, the calibration-table hash for **both**
  splits, and the resulting rungs, so a post-hoc change is a hash mismatch
  rather than an argument.

### 13.12 Spectrum selection

For each of the three admitted core reference families $f$, two further
severities of the **same family** are admitted:

- $R_{f,-}$: among qualifying severities of $f$ with $\iota$ **strictly below**
  $\iota_A$, the one nearest $\iota_A - 0.20$;
- $R_{f,+}$: among qualifying severities of $f$ with $\iota$ **strictly above**
  $\iota_A$, the one nearest $\iota_A + 0.20$;

ties broken toward the less restrictive severity, then by severity value. The
core rung is the third point of the triple. A spectrum rung must pass
$V_{\text{spec}}$, $V_{\text{sat}}$, $V_{\text{head}}$, $V_{\text{chance}}$,
$V_{\text{inter}}$ and $V_{\text{stab}}$; it is **not** subject to
$V_{\text{diff}}$, whose whole purpose is proximity to $\iota_A$ and which a
spectrum rung exists to violate in a controlled direction.

Strict straddling is the rule and not an accident of the targets: selecting the
two rungs nearest $\iota_A \pm 0.20$ without it permits both on the same side.
If either side is empty for an admitted family, that family cannot supply a
triple; core selection re-runs excluding it and the next qualifying family
takes the slot, until three families each supply a complete triple or the
qualified list is exhausted. Exhaustion sets
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and the spectrum arm is not generated.

**Selection reads $\iota$, $\kappa$, $\kappa^{B}$, vacuity and structural
metadata on the calibration topics and nothing else.** It could have been
executed before a single composed cell existed anywhere in this programme.

### 13.13 The difficulty-support rule

$\delta_{\text{diff}}$ is licensed only when, on the **confirmatory** data in
the configuration being estimated, all of:

1. $\iota_A$ lies inside $[\min_{f,s} d_{f,s},\; \max_{f,s} d_{f,s}]$;
2. at least **two** non-$A$ companions have $d_{f,s} < \iota_A$;
3. at least **two** have $d_{f,s} > \iota_A$;
4. at least **two** of the three families contribute a point on each side;
5. no point was dropped under §11.2's degeneracy rule.

Otherwise the configuration records `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, L3d
and L3e are withheld, and the fitted line, the support diagnostic and
$\delta_{\text{diff}}$'s point estimate are reported as **descriptive, outside
support, and not identified**. They are never reported as a null. The support
check is additionally reported as the share of bootstrap replicates in which it
holds, and a share below 0.95 attaches `DIFFICULTY_SUPPORT_MARGINAL`.

**Extrapolation is never presented as identification.**

### 13.14 Composed-headroom validation, and its non-adaptivity

Every registered cell type is generated on the 24 composed-validation topics at
$M_{\text{cal}} = 4$ and its compliance rate is evaluated independently against
the band $[0.05, 0.95]$ for each of its constraints. The gate is a viability
predicate applied cell by cell. It does not rank, select, or reorder anything,
and it computes no contrast between cells. Any cell type outside the band
returns `COMPOSED_HEADROOM_FAILURE` with the full table.

**Gate 4 runs after every companion is already fixed, and its outcomes never
revise them.** A headroom failure is a terminal status for the replication, not
an instruction to choose different rungs. Specifically, and each is an
executable refusal:

- Gate 4 may **PASS** or **TERMINATE**, and nothing else.
- Gate 4 may not replace a failed companion, including with one of §13.15's
  frozen backups.
- Gate 4 may not widen any threshold in §13.
- Gate 4 may not add a candidate family or admit a reserve rung.
- No Gate-4 table may be read by any selection function; §13.11's schema
  refusal covers it.

**Why the backups are not a substitution mechanism.** §13.15 freezes two
qualifying families beyond the three used. They exist so that the *support
requirement* is a real requirement rather than a formality — a replication that
qualifies exactly three families has no evidence that its pool was anything but
lucky — and so that a future protocol version has a documented, pre-committed
pool. **They are never substituted into a design after Gate 4**, because
substituting a companion after observing a composed rate is outcome-based
selection with an extra step. The backups are recorded in the freeze, are
generated on no confirmatory block, and carry no estimand.

**v5's Gate 4 should be, if the design works, uninformative.** §13.4 moves the
predictable solo failures earlier and §13.6 moves the predictable compositional
failures earlier. What remains for Gate 4 is genuine surprise: an
interaction the projection did not anticipate. §26's success criterion says so
in advance, and a Gate-4 failure in v5 is therefore a **finding about the
interaction rule**, to be reported as one.

### 13.15 Support requirements, and the frozen backups

| Requirement | Value | Where it comes from |
|---|---:|---|
| structurally eligible Tier-1/Tier-2 families entering calibration | ≥ **8** | the whole registered Tier-1 vocabulary, so the requirement is a screen and not a formality |
| families passing the full $V(R)$ on the pooled calibration and both splits | ≥ **5** | three core references plus two frozen backups |
| core references used | **3** | unchanged |
| of which Tier 1 | ≥ **2** | the primary local estimand is a same-form contrast |
| distinct feature groups among the core references | **3** | unchanged |
| qualifying families frozen as unused backups | **2** | v4r4 had none, and three of four replications finished below the requirement |
| status when the ≥ 5 requirement is unmet | `REFERENCE_SUPPORT_NOT_IDENTIFIED` | §28.2 |

**`REFERENCE_SUPPORT_NOT_IDENTIFIED` is an identification status, not a
stage-terminal one**, and that is a deliberate reading. Terminating a
replication that can still estimate $D(A \leftarrow B)$, $D(B \leftarrow A)$,
$\Lambda$, the order contrasts, $\Delta_{\text{near}}$ and
$\Delta_{\text{broad}}$ — because $\Delta_R$ is unavailable — would discard
identified estimands for want of an unidentified one. It cannot be silently
bypassed: it is written at design time onto the Gate-3C record, it drops the
core and spectrum arms from the cell plan, it withholds L3a–L3e, and it appears
on every emitted statement of that replication. §34 D6 records the alternative
— making it terminal — as a researcher decision this document does not take.

**Where the thresholds of §13.4, §13.6, §13.7 and §13.15 came from.** All of
them were chosen from the development analysis of the completed v4r4 study, in
`dci1/reports/dci1v5/reference_design_development.md`. That analysis is design
fitting and is not validation, and §30 records it as such. The two $\Delta_R$
decision thresholds of §11.9 are the only thresholds in this protocol that
predate every observation in this constraint vocabulary, and no admission
threshold has been allowed to touch them.

---

## 14. Unit of analysis, clustering, exclusions, and missingness

### 14.1 The block is the unit

| Role | Statement |
|---|---|
| Assignment | Both wording indices are assigned at the block and are identical across its cells; order is assigned within the block, so both order variants of every composed pair are present |
| Pairing | Every registered contrast is formed inside a block, removing between-topic variation |
| Clustering | The bootstrap resamples blocks; all of a drawn block's cell means travel with it, including the unconstrained cell and every companion cell |
| Generalisation | Uncertainty statements refer to the topic population of §6.2 |

Executable checks: each bootstrap replicate draws exactly 384 block identifiers
with replacement and asserts that each carries the cell count **derived from
the admitted arm set** of §8.1; no estimator function accepts a draw-level or
response-level index; every cell carries exactly $M$ committed accepted draws
before any cell mean is formed.

### 14.2 Exclusions, invalid generations, missingness, duplicates

- **No response is excluded from a primary estimand.** Empty responses,
  refusals, truncations and verifier-processing failures are scored by the
  registered rule and retained, because removing them would condition on events
  the treatment can cause.
- **Invalid generations**, meaning a backend failure that produced no text, are
  retried under the registered seed derivation. A cell that still lacks $M$
  committed draws after retries fails the run closed for that cell; the
  analysis refuses to form a cell mean from fewer than $M$ draws and no draw is
  imputed or substituted.
- **Missingness** is reported per cell type and per configuration, with the
  arm-differential missingness rate. A rate above 0.01 in any cell type is
  reported beside every primary estimand.
- **Duplicates.** Every draw carries a seed derived from the root seed, stage
  label, model identity, prompt hash and draw index. Byte-identical replicate
  pairs within a cell are counted and reported; a duplicate rate above 0.05 in
  any cell fails qualification.
- **Deprecated and foreign sources may never enter registered evidence.** An
  executable guard refuses any analysis input whose manifest classification is
  not a registered v5 artifact. This includes, by name and by structural test,
  every v2, v3, B+R pilot, v4r2, v4r3 and **v4r4** artifact and every artifact
  of the four v4r2 design screens. The guard is a positive admission rule — an
  input must prove it belongs to the v5 study tree — and the v5 study
  identifier is chosen so that it cannot satisfy any earlier revision's
  admission prefix, in both directions.

---

## 15. Multiplicity families

Families are declared **per configuration**, meaning per (model, position of
the outcome constraint) — with one exception, **F11**, which is declared across
the two configurations of one model because its members are cross-configuration
contrasts. There is no cross-model multiplicity family, because this protocol
licenses no pooled-across-model estimand.

| Family | Members | Size | Status |
|---|---|---:|---|
| **F1 Primary** | $D(B \leftarrow A)$, $D(A \leftarrow B)$, $\Lambda$, $\Delta_R$, $\delta_{\text{diff}}$, $\Xi$ | **6** | Supports L1, L2, L3a–L3e, and gates the L3 wording |
| **F2 Companion heterogeneity** | $D(B \leftarrow R_j)$ and $\Delta_j$, $j = 1,2,3$ | 6 | Secondary; L3 heterogeneity qualifier |
| **F3 Outcome-side control** | $D(A \leftarrow R_j)$, $j = 1,2,3$, and $\Delta^A$ | 4 | Secondary |
| **F4 Matrix completion** | $D(\bar R \leftarrow A)$, $D(\bar R \leftarrow B)$, $D(\bar R \leftarrow \bar R')$ | 3 | Secondary; the components of $\Xi$ |
| **F5 Robustness** | The six F1 members under the vacuity-forced recoding, and $D(B \leftarrow A)$, $\Delta_R$, $\delta_{\text{diff}}$ under a graded threshold at 0.99 | 9 | Secondary |
| **F6 Degeneracy symmetry** | The vacuity-rate difference between each composed cell containing $B$ and the $B$ solo cell | up to 14 | Gate on the §17.4 interpretation |
| **F7 Reciprocal detail** | $D(R_j \leftarrow B)$ and $D(R_j \leftarrow A)$, $j = 1,2,3$ | 6 | Secondary |
| **F8 Spectrum detail** | $D(B \leftarrow R_{f,s})$ for the six spectrum companions, $\hat\beta$, the three family intercepts, and $\hat\gamma$ from the tier-indicator fit | 11 | Secondary |
| **F9 Near-form arm** | $D(B \leftarrow N_k)$, $k = 1,2,3$, and $\Delta_{\text{near}}$ | 4 | Secondary; the $H_{\text{form}}$ bound |
| **F10 Broad-class arm** | $D(B \leftarrow CL)$ and $\Delta_{\text{broad}}$ | 2 | Secondary; the class bound |
| **F11 Order** | $\text{Ord}_A$, $\text{Ord}_B$, $\text{Ord}_\Lambda$, $\text{Ord}_{\bar R}$, $\text{Ord}_{CL}$ | 5 | **Primary tier**; supports L4b. Declared across configurations |

**F1's membership is unchanged from v4r4.** $\Delta_{\text{near}}$,
$\Delta_{\text{broad}}$ and the order contrasts are elsewhere, so registering
three new arms does not widen any interval that carries an L1, L2 or L3 claim.
**F11 is primary-tier despite not being in F1**: it licenses a claim level, so
it carries a simultaneous interval and a precision precondition, and its
members' dependence — $\text{Ord}_\Lambda = \text{Ord}_B - \text{Ord}_A$ — is
declared in §11.7 rather than hidden.

Each family receives its own simultaneous 95% interval, computed by
standardising each member by its bootstrap standard error and taking the
largest absolute standardised deviation across the family in each resample.
Marginal percentile intervals are reported alongside; decision rules read the
simultaneous intervals.

Reported with marginal intervals only and supporting no claim: joint-state
vectors and their redistribution, joint success, graded-score distributions,
response-length quantiles, finish-reason counts, chance, lift, displacement and
projection tables, the stem satisfaction rate, compliance by subject area and
by wording index, the raw-coordinate replication of the fit, the greedy
replication, and every cross-model comparison.

---

## 16. Sample size and power

### 16.1 Variance model

Let $\phi$ be the share of a cell's compliance variance carried by
between-topic heterogeneity and $\rho$ the within-block correlation of the
topic component between two cells sharing an outcome constraint. With $p(1-p)$
the cell compliance variance, $\sigma^2_{\text{topic}} = \phi\, p(1-p)$ and
$\sigma^2_{\text{draw}} = (1-\phi)\, p(1-p)$. For $T$ blocks and $M$ draws:

$$\mathrm{Var}[D] = \frac{2(1-\rho)\sigma^2_{\text{topic}} + 2\sigma^2_{\text{draw}}/M}{T}, \qquad
\mathrm{Var}[\Lambda] = \frac{4(1-\rho)\sigma^2_{\text{topic}} + 4\sigma^2_{\text{draw}}/M}{T}.$$

A **weighted composed contrast** — one composed cell against a weighted average
of others, weights summing to one, the shape of $\Delta_R$,
$\Delta_{\text{near}}$ and $\delta_{\text{diff}}$ once the solo baseline
cancels — has

$$\mathrm{Var} = \frac{2(1-\rho)\sigma^2_{\text{topic}} + \sigma^2_{\text{draw}}\left(1 + \textstyle\sum w^2\right)/M}{T},$$

with $\sum w^2 = 1/3$ for three equal weights.

**The order contrasts.** $\text{Ord}_A$ is a paired within-block difference of
two composed cells with weights $\pm 1$, so it takes the same form as
$\mathrm{Var}[D]$ and the same precision precondition. $\text{Ord}_\Lambda$ is
a difference of two such and takes $\Lambda$'s form and $\Lambda$'s
precondition.

**$\delta_{\text{diff}}$'s weights and its extra term.** Writing the fit as
$\hat Y_A = \bar Y + \hat\beta(d_A - \bar d)$ over the nine points, the weight
on $Y_{f,s}$ is $1/9 + c_{f,s}(d_A - \bar d)$. §13.12's strict-straddling rule
puts $\bar d$ at $d_A$ up to the realised offset error, so $\sum w^2$ is $1/9$
plus a leverage allowance; registered planning values are an off-centre
allowance of 0.05 and $S_{dd}$ from three families straddling by 0.20, giving
$\sum w^2 = 0.1215$. The difficulty coordinate is itself estimated, so
$\mathrm{Var}[\delta_{\text{diff}}] \approx (1 + \beta^2)\,\mathrm{Var}[\delta_{\text{diff}} \mid d \text{ known}]$.

**Registered planning constants:** $p(1-p) = 0.215$, $\phi = 0.27$ with
$\phi = 0.37$ as the alternate, $\rho = 0.5$, and $\beta = 0.5$ as the planning
slope. Carried unchanged from v4r3 §16.1. **No effect estimate from v4r4 enters
this section**, and in particular v4r4's realised $D$ and $\Lambda$ are not
used to re-fit $\phi$ or $\rho$: §16.4 records why.

### 16.2 Registered allocation

**384 blocks at $M = 8$**, over a 56-cell block when every arm is admitted:
**172,032 generations per model**, 688,128 across the four registered
replications.

| Member | precondition | $\phi = 0.27$ | $\phi = 0.37$ |
|---|---:|---:|---:|
| $D$ | 0.05 | 0.0421 | 0.0452 |
| $\Delta_R$ (F1), and $\Delta_{\text{near}}$ quoted at F1's constant | 0.05 | 0.0402 | 0.0429 |
| $\delta_{\text{diff}}$ | 0.05 | 0.0440 | 0.0471 |
| $\Lambda$ | 0.08 | 0.0595 | 0.0639 |
| $\Delta_j$ | 0.06 | 0.0421 | 0.0452 |
| $\text{Ord}_A$, $\text{Ord}_B$ | 0.05 | 0.0421 | 0.0452 |
| $\text{Ord}_\Lambda$ | 0.08 | 0.0595 | 0.0639 |

Every primary member meets its precondition under both fitted variance
settings.

**Two rows are quoted conservatively and the conservatism is stated rather than
buried.** $\Delta_{\text{near}}$ sits in F9, a family of four, whose Šidák
planning constant is 2.4909 against F1's 2.6310, so its projected half-width is
smaller than the row shows. The F11 rows are quoted at F1's constant too;
F11 is a family of five, whose constant is 2.5697. In both cases the registered
*decision* reads the realised bootstrap studentised maximum-modulus value for
that family, not a planning constant, and the planning table is deliberately the
wider of the two readings.

**Why $M = 8$ and not more blocks.** The released bank holds 384 accessible
confirmatory topics; the remaining 96 are sequestered as opaque hashes, so a
larger block count would have to be drawn from text no process in this
programme may read. With the block count fixed, $M$ is the only lever, and
under §16.1's model it is the effective one: at $\phi = 0.37$ and $\rho = 0.5$
the draw term exceeds the topic term at $M = 4$, so the part $M$ reduces is the
larger part. Doubling $M$ costs generations and nothing scientific.

**What v5's cell plan costs against v4r4's.** 56 cells against 47, a factor of
1.19 per block. The added cells are the near-form arm's nine. §34 D1 records
the compute decision, including the option of registering fewer than four
models and the option of dropping the near-form arm, and states plainly which
estimand each option gives up.

### 16.3 What the allocation would and would not resolve

At a projected $\Delta_R$ half-width of 0.0429 the design resolves the 0.10
generic-load threshold whenever the quantity is at least about 0.143 or at most
about 0.057, and resolves the direction of $\delta_{\text{diff}}$ whenever it is
at least about 0.047 in magnitude. At a projected $\text{Ord}$ half-width of
0.0452 it resolves an order contrast whose magnitude exceeds about 0.045 —
v4r4's observed cross-configuration differences in $D(A \leftarrow B)$ were
0.063 and 0.148, and in $\Lambda$ were 0.174 and 0.425, so a contrast of that
size is resolvable if it recurs. A configuration whose interval spans a
threshold is reported `INDETERMINATE` at that threshold.

**Two things the allocation cannot buy, at any block count.** The length
channel (§29) and a class *claim* (§5).

### 16.4 Excluded planning sources

No effect estimate enters the sample-size calculation. The preconditions are
absolute and derived from the smallest effect of interest. The B+R pilot
contributes the variance constants and the matrix screen the planning slope's
order of magnitude. **v4r4's confirmatory effects contribute nothing to §16**,
and that is deliberate: v4r4's estimates were produced under the reduced design
on two models, using them to size v5 would make the allocation depend on an
observed effect, and §16's preconditions are absolute by design.

---

## 17. Uncertainty, decision rules, and claim licensing

### 17.1 Uncertainty estimation

Nonparametric block bootstrap, 10,000 resamples, seeded from the registration
manifest, resampling the 384 blocks with replacement and carrying **every** cell
mean of each drawn block — the unconstrained cell, both solo cells of every
contrast, and every composed cell — so that quantities computed from different
cells of the same block stay coupled. **Both configurations of a block travel
together**, which is what makes F11's cross-configuration contrasts estimable
on the same resample.

Simultaneous intervals per family by the studentised maximum-modulus
construction of §15, with the same index vector applied to every member of a
family in each resample. Marginal percentile intervals are reported alongside.

### 17.2 The bootstrap for the difficulty relation

**Every replicate refits.** In each resample, in order: resample the 384 block
identifiers; recompute $\kappa_c$ from the resampled unconstrained cells and
the solo compliance of every companion from the resampled solo cells, and from
them $d_{f,s}$ and $d_A$; recompute $Y_{f,s}$ and $D(B \leftarrow A)$ from the
resampled composed cells; **refit** the §11.8 model on the nine non-$A$ points
of that replicate; predict at that replicate's $d_A$ using that replicate's
fit; form $\delta_{\text{diff}}$; and evaluate the §13.13 support conditions on
that replicate and record whether they held.

Explicitly prohibited, each enforced by a test: fitting the curve once and
bootstrapping only the residual; including $A$ in the fit that predicts $A$;
selecting the model form from bootstrap outcomes; treating points that share
topic blocks as independent; resampling anything other than blocks.

A replicate in which $\hat\beta$ is not finite contributes to a recorded
degenerate-replicate count and, above 0.01 of replicates, the estimand records
`INSUFFICIENT_PRECISION`.

### 17.3 Equivalence and the precision precondition

An equivalence statement about $D$, $\Lambda$, $\delta_{\text{diff}}$ or an
order contrast requires the simultaneous interval to lie wholly inside
$\pm 0.10$ **and** its half-width to be at or below the precondition of §16.2.
A member whose realised half-width exceeds its precondition records
`INSUFFICIENT_PRECISION`, withholds every equivalence and threshold statement,
and still reports a resolved direction if one exists.

Any string asserting absence, equivalence or negligibility is produced by a
single guarded function whose precondition is exactly this rule, and the
analysis aborts if that function is reached with the precondition false. **An
order contrast whose interval contains zero is not order-invariance** unless
this rule is met, and the emitter refuses the word.

### 17.4 Vacuity and partial identification

Family F6 gates the interpretation. When every vacuity-rate difference is at or
below 0.05 or its interval includes zero, the primary estimands are reported
without qualification. Otherwise they carry a fixed block stating that
composition changed how often the outcome constraint could bind, and the F5
vacuity-forced recomputation is reported beside them as partial-identification
bounds. A claim is licensed only when the primary and the vacuity-forced
recomputation license the same claim; otherwise the axis is reported unresolved
with both bounds.

**The vacuity-forced recomputation is the registered operation and a length
restriction is not.** Recomputing an estimand on the subset of responses above
a word threshold drops a different share of each arm and conditions on a
post-treatment variable.

### 17.5 Emission machinery

Every emitted statement carries the machine fields `claim_level`,
`configuration`, `cell`, `family`, `interval_type`, `identification_status`,
`measurement_basis`, `difficulty_coordinate`, `structural_tier_of_reference_pool`,
and the position of the outcome constraint. One guarded emitter exists per
claim level; each refuses a member name not registered to it. An executable
check refuses any statement missing a field, a second refuses any statement
that quotes a scalar without its configuration, and a third refuses any L1, L2
or L3 statement that does not name the **cell** the composed term was read
from — the field v4r4's reports needed and did not carry.

### 17.6 When the estimands disagree

Registered in advance, within one configuration. Every row assumes the
identification gates of §3.2 hold.

**$\Delta_R$ against $\delta_{\text{diff}}$:**

| $\Delta_R$ | $\delta_{\text{diff}}$ | Registered reading | Emitted |
|---|---|---|---|
| upper < 0.10 | inside $\pm 0.10$ at precision | Generic difficulty and the local matched set agree: no $A$-specific excess is identified | L3c **and** L3e |
| lower > 0.10 | lower > 0 | $A$ exceeds both the local matches and the broader relation | L3a (and L3b if > 0.25) **and** L3d, subject to the $\Xi$ gate |
| lower > 0.10 | inside $\pm 0.10$ at precision | The three core references were unrepresentative of the difficulty relation | **Neither.** `LOCAL_AND_SPECTRUM_DISAGREE`; both intervals and the $\Delta_j$ table reported |
| upper < 0.10 | lower > 0 | The core references resemble $A$ unusually closely relative to the relation | **Neither.** `LOCAL_AND_SPECTRUM_DISAGREE` |
| either | support fails | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`; the local reading stands alone with that status | L3a/L3b/L3c only |
| either | half-width above precondition | `INSUFFICIENT_PRECISION` on that member | as available |

**$\Delta_R$ against $\Delta_{\text{near}}$, new in v5:**

| $\Delta_R$ (Tier 1) | $\Delta_{\text{near}}$ (Tier 2) | Registered reading | Emitted |
|---|---|---|---|
| lower > 0.10 | lower > 0.10 | The excess is not a property of the predicate form: $A$ exceeds both same-form and near-form companions | L3a, with the near-form agreement reported |
| upper < 0.10 | upper < 0.10 | No local excess against either tier | L3c, with the same |
| lower > 0.10 | upper < 0.10 | $A$ exceeds same-form markers but not other exact counts. The excess is specific relative to *markers* and not relative to the operator | **Neither.** `LOCAL_TIER_DISAGREE`; both reported |
| upper < 0.10 | lower > 0.10 | The marker controls resemble $A$ unusually closely, which is what a same-form control is supposed to do; the near-form comparison is the informative one | **Neither.** `LOCAL_TIER_DISAGREE`; both reported |
| any | arm not admitted | `NEAR_FORM_ARM_NOT_AVAILABLE`; the $\Delta_R$ reading stands alone with that status | L3a/L3b/L3c only |

**An emitted L3c without the near-form arm carries a fixed sentence**, because
L3c is the memo's refutation verdict and v5's core pool is chosen to resemble
$A$: *the local excess is below the generic-load threshold against companions
that share $A$'s predicate form, and no companion of a different form was
available to test whether the absence is a property of the form rather than of
$A$.* §34 D18 records whether the near-form arm should instead be a
precondition of emitting L3c at all.

**A disagreement is a result.** It is reported as one, with both quantities and
the diagnostics that distinguish them, and it never resolves toward whichever
estimand crossed a threshold.

**Coordinate agreement.** The §11.8 fit is computed on the registered
instructed-compliance coordinate and, separately, on raw solo compliance. When
the two give different L3d/L3e classifications the statement carries
`DIFFICULTY_COORDINATE_DEPENDENT` and both readings are reported; the
registered coordinate decides which classification is emitted and the secondary
decides whether it carries the status.

### 17.7 The L4 emitters, and the correction of v4r4's defect

**What went wrong in v4r4, restated so the fix is checkable.** `emit_l4`
received `per_configuration: Mapping[configuration, Sequence[level]]` and
compared the **sets** of levels reached. Its caller built that input as
`[s["claim_level"] for s in statements if emitted]`, discarding the member
identity before the emitter could see it. For `gemma-3n-e4b-it` both
configurations reached L1 — but $D(A\leftarrow B)$ reached it in
`outcome_first` only and $D(B\leftarrow A)$ in `outcome_second` only — so the
sets matched and the emitted L4 asserted replication for the replication that
least replicates. §28.1 pairs *Replication* with *Configuration dependence* and
both rows are about **a named quantity**; the gate is per member.

**The v5 signature.**

```
emit_l4a(*, per_member: Mapping[str, Mapping[str, str | None]],
         measurement_basis: str,
         identification_statuses: Sequence[str] = ()) -> dict
```

`per_member` maps each **registered member name** to a mapping from
configuration to that member's classification in that configuration, or `None`
where the member reached no level. L4a is licensed iff:

1. every registered configuration appears for every member;
2. at least one member reached a classification in at least one configuration;
3. **for every member, the classification is identical across every registered
   configuration.**

A member reaching a level in one configuration and not the other makes
condition 3 false and L4a is not emitted; the registered reading is §28.1's
*Configuration dependence*, and the reported table is the per-member
classification map itself.

**`emit_l4b`** reads F11's simultaneous intervals and emits, per named order
contrast, *the quantity depends on the position of the outcome constraint*
when the interval excludes zero. It never emits an order-invariance statement
except through §17.3's guarded function.

**The regression test is registered, not left to implementation taste.** §19
requires a test that constructs v4r4's `gemma-3n-e4b-it` pattern — member
$D(A\leftarrow B)$ at L1 in `outcome_first` and `None` in `outcome_second`,
member $D(B\leftarrow A)$ at `None` in `outcome_first` and L1 in
`outcome_second` — and asserts `emitted is False` with the reason naming the
differing members. A second test constructs v4r4's `qwen3-4b` pattern —
$D(A\leftarrow B)$ at L1 in both — and asserts `emitted is True`. A third
asserts that no code path can call an L4 emitter with a bare sequence of
levels: the parameter is keyword-only and its value is validated as a mapping
of mappings.

**Disposition of v4r4's field.** v4r4's emitted `claims.L4` for
`gemma-3n-e4b-it` remains invalidated and is **not** recomputed inside v4r4:
its `run_unmasked_analysis` refuses an unmasked analysis under a moved
`analysis_code_hash` and §20 forbids re-masking after unmasking. v5's fix is
prospective and repairs nothing retrospectively.

---

## 18. Stage sequence and gates

| # | Stage | Passes when | Failure |
|---:|---|---|---|
| 1 | `PROTOCOL_REGISTERED` | Every §34 open decision closed; the registration manifest signed, binding this document's hash, the spec file's hash, the model revisions, the topic-bank hash and the split seed | `REGISTRATION_INCOMPLETE` |
| 2 | `QUALIFIED` | Clean tree, tracked implementation, resolved revisions, non-empty dependency manifest, schema-valid prompt plan, wording and witness suites pass for every registered pair **including §7.7's realistic witness**, class **and tier** labelling asserted, structural metadata asserted against every predicate, §9.1's presence rule asserted at every generative stage, cache and durable store reachable, environment and commit hashable | `QUALIFICATION_FAILURE` |
| 3 | `GATE_0_APPARATUS` | The procedural pilot of §19 | `APPARATUS_FAILURE` |
| 4 | `REGIME_SCREEN` | Completion cap selected; dense ladder screen complete; §12.6's expansion run to its stopping rule and the **candidate vocabulary frozen**; the §12.2 high-recall retention rule applied and its carried set recorded | `RESPONSE_LENGTH_INCOMPATIBLE` |
| 5 | `GATE_1_MEASUREMENT` | §10.2 for every verifier in the final instrument population, plus §10.7 A–E; verifier hash **and wording hash** frozen | `MEASUREMENT_NOT_ESTABLISHED`, `MEASUREMENT_EVIDENCE_INSUFFICIENT`, `SPECIFICATION_AMBIGUOUS` |
| 6 | `GATE_2_FOCAL_CALIBRATION` | $n^*$ and $m^*$ selected inside their bands on the pooled calibration; §12.4 adequacy holds; §12.3's bracketing evaluated and its status recorded | `TARGET_RANGE_EXHAUSTED`, `FOCAL_RANGE_EXHAUSTED`, `GRID_RESOLUTION_INSUFFICIENT`, `REGIME_NOT_FOUND` |
| 7 | `GATE_2_5_CANDIDATE_QUALIFICATION` | $\kappa^{B}$ measured for every carried candidate at $m^*$; $V_{\text{spec}}$, $V_{\text{sat}}$, $V_{\text{head}}$, $V_{\text{chance}}$, $V_{\text{struct}}$ and $V_{\text{inter}}$ evaluated on the pooled calibration and recorded per candidate with its earliest failing component | Not terminal: writes the qualified pool, which may be empty |
| 8 | `GATE_3A_REFERENCE_CALIBRATION` | Every §13.7 quantity computed on Calibration-A and Calibration-B separately and on the pooled set; the two split tables and their hashes written | Not terminal |
| 9 | `GATE_3B_REFERENCE_SELECTION` | §13.8, §13.9, §13.10 and §13.12 applied to the qualified pool; core references, spectrum triples, near-form controls, broad-class control and the two frozen backups written | Not terminal |
| 10 | `GATE_3C_IDENTIFICATION` | §13.15's support requirements evaluated; the admitted arm set and the derived cell count written; every identification status written at design time | Not terminal: sets `REFERENCE_SUPPORT_NOT_IDENTIFIED`, `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, `NEAR_FORM_ARM_NOT_AVAILABLE` and/or `CLASS_ARM_NOT_AVAILABLE` and drops the corresponding arms |
| 11 | `GATE_4_COMPOSED_HEADROOM` | Every registered cell type inside $[0.05, 0.95]$ on every constraint | `COMPOSED_HEADROOM_FAILURE` |
| 12 | `PREFREEZE_AUDIT` | Every §18.1 field present and derivable; every arm's admission traceable to a signed record; the §33 red-team checklist executed and its result recorded | `PREFREEZE_AUDIT_FAILURE` |
| 13 | `GATE_5_FREEZE` | The freeze record of §18.1 written and verified | none |
| 14 | `CONFIRMATORY_GENERATION` | Complete draw matrix committed | none |
| 15 | `MASKED_ANALYSIS` | §20 | none |
| 16 | `UNMASKING` | §20 | none |
| 17 | `UNMASKED_ANALYSIS` | §20, §21 | none |
| 18 | `FINAL_REPORT` | The machine-readable result table of §31 written from signed records only, with every number traceable to a stage record and a hash | none |

Every command verifies the content hash and signature of its predecessor record
and re-verifies the frozen verifier hash before any mutation. A terminal state
mechanically disables every later command. Every attempted transition is logged
with timestamp, revisions, producing commit, environment digest, input and
output hashes, and outcome. Every stage record carries `study_id`, and
`read_stage_record` refuses a record whose `study_id` is not this study's.

**`PREFREEZE_AUDIT` and `FINAL_REPORT` are stages in v5 and were tools in
v4r4.** A check that runs beside the lifecycle can be skipped; a stage cannot.

**Gate 1 does not depend on Gate 3.** The instrument population is the declared
range of §7, which this document registers, so §10.2's evidence is required
whatever Gate 3 selects. It does follow the regime screen, because the regime
screen is where the vocabulary closes.

### 18.1 The freeze record

Protocol version and hash; the reference-design spec hash; model repository and
revision; the prompt template including the §8.5 stem byte-for-byte; completion
cap; $n^*$; $m^*$; whether a focal extension was measured and the bracketing
status; the complete candidate family vocabulary of §7 with every ladder,
reserve, structural-metadata record and tier; every wording; the difficulty-coordinate
definition; the chance-compliance and **counterfactual-chance-compliance**
definitions; every component of $V(R)$ with every threshold; the
**Calibration-A and Calibration-B table hashes**; the qualified pool with each
candidate's earliest failing component; the three core references with their
severities, tiers and feature groups; the six spectrum severities; the three
near-form controls; the broad-class control or `CLASS_ARM_NOT_AVAILABLE`; **the
two frozen backup families, with the statement that they are never
substituted**; the support rule and its realised counts; the admitted arm set
and the derived cell count; the order and wording allocation; topic splits and
the split seed; seed rules; $M$ and the block count with the §16.1 variance
re-estimate; every verifier source and the canonical verifier hash; the
graded-score definitions; the non-vacuity predicates; decoding settings; family
declarations F1–F11; the difficulty-model functional form and the
tier-indicator secondary; the bootstrap algorithm including the refit loop; all
thresholds, regions and precision preconditions; the claim ladder including
both L4 emitters; every decision rule of §17.6; the codebook; producing commit;
clean-tree assertion; dependency and environment digests; hardware record;
gate-record hashes; the Gate-1 measurement basis; the §30 reuse ledger hash;
and the complete analysis plan.

**A field a variant legitimately leaves empty is declared empty, with the
identification status that explains it**, and the freeze refuses an empty field
that no status explains. **No scientific rule changes after the freeze.**

---

## 19. Qualification and procedural pilot

Qualification is non-scientific and reads no behavioural rate. After it, a
procedural pilot on twelve fixed pre-screen topics runs the full 56-cell plan,
both orders, and the registered wording allocation, at fixture values that
cannot become calibration evidence, with $M = 4$.

Acceptance requires all of: every logical cell and draw committed exactly once;
every cell yielding one cell mean over exactly $M$ accepted draws; zero
technical generation failures after retries; every codebook field present and
in domain; **§9.1's presence rule holding on every pilot row, at every load**;
the full analysis pipeline running to a structurally complete result table with
every numeric value redacted, including a fitted difficulty relation, a support
diagnostic, a $\delta_{\text{diff}}$ row, an F11 order row and both L4 rows;
mutating one stored byte changing its content hash and causing the analysis to
refuse the row; cache deletion and durable restore reproducing every row with
matching hashes; and the separate pilot mask cycle completing without touching
the confirmatory mask namespace.

**Registered unit tests that must exist and pass before qualification.**

1. §17.7's three L4a regression tests, including the two reconstructed from
   v4r4's `gemma-3n-e4b-it` and `qwen3-4b` claim tables.
2. A test asserting that `load_calibration_table` refuses a table carrying a
   composed field **and** a table carrying an unknown field, and that
   `kappa_under_b` is accepted only when its supplying rows are load-one cells
   whose single present constraint is $B$.
3. A test asserting that $V(R)$ is evaluated lexicographically and that the
   recorded rejection reason is the **earliest** failing component.
4. A test asserting that no Gate-4 table can reach any selection function, and
   that a frozen backup cannot be substituted into an admitted slot after Gate
   4 — the substitution path must not exist, not merely be unused.
5. A test asserting that every family's declared structural metadata agrees
   with its predicate form, and that every slot refuses a family whose tier it
   does not admit.
6. A test asserting that `assert_no_l5_emitter` holds over the claims module.

Failure returns `APPARATUS_FAILURE`; repair creates a new producing commit and
requires qualification and the pilot to run again.

---

## 20. Masking and unmasking

**What is masked.** After confirmatory generation and before any analysis, the
pipeline permutes the **companion label** within each (outcome constraint,
configuration, block) group of composed observations, using a seed from the
system random source. Solo and unconstrained cells carry no companion and are
not permuted.

**The mask is stratified, not independent.** Within each (outcome,
configuration) stratum the *number* of blocks receiving a non-identity
permutation is fixed at $\lceil N \cdot \max(0.5,\ 1 - 1/k) \rceil$ rather than
left to the binomial, and *which* blocks they are is drawn uniformly without
replacement; a chosen block receives a permutation drawn uniformly from those
with no fixed point. An analyst learns how many blocks moved, which is a
registered constant computable from $N$ and $k$; they learn nothing about
which.

**Consequences, declared.** Permuting companion labels permutes which
$D(B \leftarrow \cdot)$ belongs to which companion, so the masked-phase fit is
a fit of the same losses against a permuted assignment of difficulties. The
companion **difficulties** come from solo and unconstrained cells and are not
permuted; that is deliberate, because they are pre-treatment quantities fixed
at Gate 3B. $A$'s point is inside the permuted group, so $\delta_{\text{diff}}$
and $\Delta_R$ are not computable in the masked phase and are computed after
unmasking under the fully registered plan, labelled as such. A composed
generation contributes two observations whose companion labels are permuted
independently, so joint-state and joint-success quantities are computed after
unmasking and are labelled as computed post-unmasking.

**The order contrasts are computable in the masked phase for $A$ and $CL$ and
not for the reference mean.** $\text{Ord}_A$ differences the two $A{+}B$ cells,
whose companion is $B$ in both, and $B$ is not inside any permuted group with
another companion in the reduced arm set; $\text{Ord}_{\bar R}$ averages over
permuted labels and is not. Which order contrasts are masked-phase computable
depends on the admitted arm set, is derived by one named function, and is
recorded on the masked record rather than assumed.

**Masked phase.** All planned analysis code executes on the permuted table. All
reading of response text, all hand coding, all inspection of degeneracy and
compliance quantities, and all anomaly diagnosis happen here. Permitted:
repairing an analysis defect, adding a diagnostic, declaring an anomaly and
fixing the rule that will handle it. Forbidden here and afterwards: changing an
estimand, family, threshold, region, precondition, reference set, spectrum set,
near-form set, class companion, difficulty coordinate, functional form, support
rule, verifier, scoring rule, claim rule, claim level, non-vacuity predicate,
or topic split.

**Unmasking.** A single named function invoked once, writing a timestamped
entry with the content hash of the analysis code at that moment. Executable
checks: the permuted labels differ from the true labels in at least half of the
blocks in every maskable group; the mask key file is opened exactly once in a
full run; the recorded analysis-code hash at unmasking reproduces every
masked-phase output byte for byte.

**A group with one companion is structurally unmaskable** and is recorded as
`structurally_unmaskable`; a group with two is masked only in the aggregate
sense. Both are stated on the record rather than inferred from $k$.

**After unmasking.** Any analysis-code change is labelled post-unmasking, is
exploratory, and supports no registered claim. Masked and unmasked outputs are
both released.

**The commitment device and its known cost.** `run_unmasked_analysis` refuses
an unmasked analysis under an `analysis_code_hash` differing from the masked
seal, and this section forbids regenerating a mask once semantic identities are
known. Together these make a post-unmask repair of an analysis defect
impossible — which is what happened to v4r4's L4 emitter. That is the device
working as designed and it is the reason §19 requires the L4 regression tests
**before qualification**: the only place a claim-emitter defect can be caught
is before the seal.

---

## 21. Analysis order

1. Load confirmatory rows; reject any row outside the frozen plan by prompt
   hash, revision, verifier hash, or block identity.
2. Re-verify the frozen verifier hash; fail closed on mismatch.
3. Assert the complete matrix of 384 blocks by the cell count **derived from
   the frozen arm set** by $M$ draws, each committed exactly once; count
   duplicates and missingness.
4. Form cell means over all $M$ accepted draws; refuse any partial cell.
5. Score the compliance vector, the graded vector and the degeneracy flags for
   every instance, marking each verdict present or chance.
6. Compute per-cell compliance, chance compliance, counterfactual chance
   compliance, displacement, projected composed compliance, instructed
   compliance, vacuity, truncation, length and graded-score summaries.
7. Form the delivery losses, the asymmetry, the companion swaps,
   $\Delta_{\text{near}}$ and $\Delta_{\text{broad}}$ within each configuration.
8. Form the F11 order contrasts across the two configurations, in both
   algebraic forms, and assert their agreement.
9. Fit the §11.8 difficulty relation on the nine non-$A$ points, assert $A$'s
   exclusion, evaluate the §13.13 support conditions, and form
   $\delta_{\text{diff}}$ in both algebraic forms and assert their agreement.
   Fit the tier-indicator secondary on twelve points.
10. Form $\Xi$ and the F4 components.
11. Run the block bootstrap with 10,000 resamples, carrying both configurations
    of every drawn block and refitting the difficulty relation in every
    replicate.
12. Compute simultaneous intervals within each declared family, F1–F11.
13. Compute the F5 vacuity-forced recomputation and the F6 gate.
14. Repeat steps 9 and 12 on the raw-coordinate secondary fit.
15. Apply §17.6's joint readings, then the claim ladder of §3 with the rules of
    §17, emitting through the guarded emitters, `emit_l4a` last of the
    per-member levels and `emit_l4b` from F11.
16. Compute the post-unmasking joint-state and redistribution quantities and
    label them.
17. Report the realised $\hat p_c$ against the realised composed compliance for
    every companion, as the prospective record of §13.6's projection.

The analysis fails closed. A missing cell, an incomplete draw set, a duplicate
accepted row, a non-finite standard error, a non-finite bound or a degenerate
fit returns a named inconclusive status for the affected quantity and computes
no claim. No cell, block, constraint or draw is dropped, and no missing value
is imputed. The design is fixed size: no interim analysis, no optional
stopping, no adaptive sample size.

---

## 22. Prohibited and mediating quantities

Recorded for every generation and never entering a primary estimand as a
covariate, filter, stratifier or weight: response length in words and tokens,
truncation status, finish reason, graded score, vacuity flag, joint state,
stem-band membership, and any other quantity produced during or after
generation. The analysis asserts this by checking the declared causal role of
every field named in a primary formula.

**Chance compliance is pre-treatment for the companion and is not on this
list.** $\kappa_c$ is measured where $c$ is absent, so it is not produced by
any treatment applied to $c$; it enters the difficulty coordinate by
registration. It is *post-treatment for the topic*, so it is never a covariate
on the outcome, never a block weight, and never used to select or drop a block.

**Counterfactual chance compliance $\kappa^{B}_c$ has the same standing, with
one difference stated plainly.** $c$ is absent in the cell it is measured on,
so it is pre-treatment for $c$ exactly as $\kappa_c$ is. It is measured on rows
produced under $B$, so it is *not* pre-treatment with respect to the pair
$(c, B)$. §13.6 registers its only use — as a component of a pre-composition
admission gate — and §13.11 makes that executable. It is never a covariate, a
weight, a filter, or a term in any estimand.

**Response length is registered as a mediator.** Composition shortens answers
and shorter answers satisfy budget constraints more readily, so response length
lies on the path from companion to outcome. It is reported per cell, its
composed-to-solo change is reported per constraint, and a registered
descriptive decomposition reports the delivery loss within strata of realised
response length. **No mediation effect is claimed and no primary estimand is
adjusted for it.** §29 records that the length account of $A$ is not identified
by this design.

**Lexical register is registered as a second mediator and is new in v5.**
v4r4's follow-up evidence found that at matched response length the
first-stated constraint appeared to determine the vocabulary the answer was
written in, and that this — not length — separated the good and bad orderings
on one model. v5 reports, per cell, the distribution of $B$'s own verifier
statistic (the longest word length) and of each companion's statistic, and the
composed-to-solo change in each. **These are descriptive, are post-treatment,
and carry no claim.** They exist so that a mechanistic reading of an order
effect has a measured basis rather than an anecdote.

---

## 23. Secondary analyses and error analysis

All Tier-secondary, none able to change a primary conclusion.

- Every F2–F11 member with its simultaneous interval.
- The fitted difficulty relation: slope, family intercepts, per-companion
  residuals, the support diagnostic and its bootstrap share, the tier-indicator
  secondary, and the same on the raw coordinate.
- The near-form arm: $D(B \leftarrow N_k)$, $\Delta_{\text{near}}$, and each
  $N_k$'s residual from the difficulty line it did not enter.
- The broad-class arm: $D(B \leftarrow CL)$, $\Delta_{\text{broad}}$, and
  $CL$'s residual from the same line.
- **The projection audit**: realised $\hat p_c$ against realised composed
  compliance for every companion in every composed cell, with the absolute
  error distribution, reported as the prospective record of §13.6.
- Chance, lift, displacement, projection and instructed compliance for every
  registered instance, with the pre-screen, Calibration-A, Calibration-B,
  pooled and confirmatory values side by side.
- The stem's satisfaction rate by load and by cell type.
- Joint-state vectors per composed cell and their redistribution across order;
  joint success per composed cell.
- The graded vector distribution per cell, and the graded manipulation check.
- The demoted estimand $\Delta^A$, with its three gates satisfied and its
  configuration quoted.
- Failure taxonomy for every exact-count constraint: empty, cut off, refusal,
  restatement, target inside a longer word, zero occurrences, too few, too
  many, other, in that priority order, split by whether the realised margin is
  exactly one. **Reported for $A$ and for every Tier-1 reference**, because
  v4r4's follow-up found $A$ failing by *overshoot* and its marker class
  companion failing the same way, and the same-form design makes the comparison
  exact.
- The primary estimands recomputed under $S_1$, $S_2$ and $S_3$ for the
  $A$-side outcome.
- Companion-difficulty sensitivity: $D(B \leftarrow R_j)$ against the
  confirmatory-measured $\lvert\iota_{R_j} - \iota_A\rvert$.
- Confounder description: compliance as a function of response length,
  truncation, refusal and subject area within each cell.
- Lexical-register diagnostics (§22).
- The greedy replication on 96 blocks, as a different generation population.
- The realised variance decomposition beside every primary estimate, with the
  realised simultaneous half-width and the achieved detectable effect.
- Compliance by subject area and by wording index.
- Cross-configuration and cross-model tables, descriptive only.

---

## 24. Segmentation and construct-validity checks

Before freeze, for every registered verifier: enumerate the boundary cases of
its scoring convention; encode each as a deterministic unit test with a frozen
expected verdict; run a targeted adversarial corpus over the enumerated cases;
quantify how often each case occurs in genuine generations from the calibration
stages, per cell type; compare the primary convention against prespecified
reasonable alternatives registered before the comparison is run; and report the
alternatives as robustness analyses. Switching a scoring convention after
results are seen is prohibited.

For every exact-count marker constraint the enumerated cases include the marker
inside a longer word, concatenated copies, hyphenation, Unicode punctuation and
lookalikes, zero-width characters, capitalisation, and sentence-boundary
punctuation. For the word-length and budget constraints they include empty
output, single-token output, hyphenated and apostrophised forms, non-Latin
script, digits and symbols adjacent to words, and markdown emphasis. For the
rate constraints they additionally include a wordless answer, a single-word
answer, and rates straddling each severity. For the lower-bound and exact-count
constraints they additionally include counts at $q-1$, $q$ and $q+1$.

**The enumeration is checked in both directions.** Every enumerated case must
appear in the adversarial corpus and in the boundary suite, and a case named
differently by the two must be reconciled explicitly rather than reported as a
coverage gap.

---

## 25. Contamination and chance compliance

Every v5 topic is newly written or carried from the v4 bank, whose questions
were newly written; no v3 topic and no pilot topic enters any v5 set. At
release the exact text of each confirmatory topic is queried against a public
web search index and the number of exact-phrase matches is reported. A canary
string is embedded in the released dataset file. The 96 v5 sequestered topics
are withheld; the 96 v3 sequestered topics remain sequestered.

**Chance compliance is measured on the confirmatory blocks and is a registered
input, not only a diagnostic.** The unconstrained cell gives $\kappa_c$ for
every registered instance on the same 384 blocks at the same $M$, and every
cell where a constraint is absent additionally records that constraint's
verdict, giving the base rate under other constraint loads — **which is where
the confirmatory $\kappa^{B}_c$ comes from, and therefore where §23's
projection audit is computed.**

Any cell whose truncation rate exceeds 0.10 has its chance figure reported as a
bound. The outcomes are instruction compliance, which does not depend on
knowing a correct answer, so memorised answer content cannot by itself produce a
pass.

---

## 26. The primary methodological success criterion

Separate from every scientific claim, v5 registers one methodological
objective, judged **before any confirmatory composed outcome is seen**:

> Before Gate 5, v5 identifies a sufficiently redundant set of stable,
> structurally appropriate, non-degenerate reference controls — at least five
> families passing the full $V(R)$ on both calibration splits, three used and
> two frozen — and those controls survive Gate 4's composed-headroom validation
> **without replacement**.

This is **not** the scientific effect claim. It establishes that the
counterfactual $\Delta_R$ requires is identified. It is recorded per
replication on the Gate-3C and Gate-4 records as `MET` or `NOT_MET` with the
realised counts, before any confirmatory generation, and it is reported in the
final report whether or not any L3 statement is emitted.

**A Gate-4 failure in v5 is a finding about §13.6's interaction rule**, because
§13.4 and §13.6 exist to move the predictable failures earlier. It is reported
as one, with the failing cell's pre-composition $\kappa^{B}$, $\hat p$ and
$\Sigma$ beside its observed rate, and it terminates the replication exactly as
§13.14 says.

---

## 27. Codebook and computational environment

A codebook accompanies every released table with one row per variable giving
name, type, permitted values, units, causal role and a one-sentence definition.
Causal role takes one of identity, treatment, design, outcome, post-treatment,
provenance, difficulty-coordinate. Executable checks: every released column
appears in the codebook and every codebook row appears as a column; every value
is in domain and of declared type; no post-treatment field appears in a primary
formula; every field declared to constrain execution is consumed by a named
check in §28.

The environment record contains lockfile and frozen-export hashes, interpreter
and version, exact invocation command, backend version and settings,
tensor-library and driver versions, operating system and kernel, GPU name and
architecture, model repository and revision, chat-template hash, and registered
execution-relevant environment variables. Executable checks: a dependency
change moves the environment digest and an empty manifest is rejected;
deterministic derivations reproduce their recorded hashes from the producing
commit; rerunning the analysis in the recorded environment on released raw
responses reproduces the released table byte for byte; cache deletion and
durable restore reproduce every committed row and regenerate no committed draw.

---

## 28. Execution integrity, provenance, and the outcome vocabulary

### 28.0 Execution integrity

Every generation records stage, artifact state, model replication, block, cell
type, arm, constituent constraint identities, severities, classes **and
tiers**, order, position of each constraint, wording indices, draw index,
prompt hash, model revision, backend version, interpreter identity, dependency
digest, hardware class, seed, raw response, response content hash, token
counts, finish reason, stem-band membership, and every verifier verdict, graded
score, presence flag and degeneracy flag with the verifier source hash.

Artifacts move monotonically through `generated`, `committed`, `accepted` and,
when audit-preserved and excluded, `superseded`. A committed artifact becomes
accepted only after durable write, content-hash verification, stage
authorisation, predecessor-gate verification, schema validation and frozen-plan
membership. A superseded artifact never returns to accepted.

The run aborts on a missing or invalid predecessor record, a dirty tree, an
invoked source absent from the producing commit, a prompt exceeding the context
limit, a revision or hardware or dependency change inside a run, a prompt hash
absent from the frozen plan, a duplicate accepted draw, a cell whose accepted
draw count differs from $M$, a verifier hash differing from the frozen value, a
content-hash mismatch, a stale output path, or an artifact whose declared type
disagrees with its stage.

**The v5 implementation lives in its own namespace**, writes nothing inside any
earlier evidence tree, and refuses any analysis input classified deprecated or
foreign, in both directions.

### 28.1 Confirmatory outcomes

Recorded per member per configuration, and for F11 per member across
configurations.

| Outcome | Condition | Licensed statement |
|---|---|---|
| Delivery loss resolved | $D(c \leftarrow g)$ simultaneous lower bound above 0 | Composing $c$ with $g$ reduced delivery of $c$ in this configuration, with $c$ in the named position and the named cell |
| Delivery gain resolved | Upper bound below 0 | Composing $c$ with $g$ raised delivery of $c$ |
| Meaningful magnitude | The interval lies wholly beyond $\pm 0.10$ | The change exceeds the smallest effect of interest |
| Equivalence | Wholly inside $\pm 0.10$ and the half-width meets its precondition | Any change is smaller than the smallest effect of interest, at adequate precision |
| Asymmetry resolved | The $\Lambda$ interval excludes 0 | The loss is directionally asymmetric in this configuration |
| Local excess above generic-load threshold | $\Delta_R$ lower bound exceeds 0.10 | $A$ costs $B$ more than same-form companions matched on instructed compliance do, by more than the generic-load threshold |
| Pair-specific threshold reached | $\Delta_R$ lower bound exceeds 0.25 | The local excess reaches the source memo's pair-specific threshold |
| Generic compositional load, locally | $\Delta_R$ upper bound below 0.10 | The local excess is below the generic-load threshold |
| Near-form agreement | $\Delta_{\text{near}}$ classifies as $\Delta_R$ does | The excess, or its absence, is not a property of the predicate form |
| Spectrum excess resolved | $\delta_{\text{diff}}$ lower bound above 0, support holding | $A$ costs $B$ more than the fitted relation predicts at $A$'s difficulty |
| Difficulty accounts for $A$ | $\delta_{\text{diff}}$ wholly inside $\pm 0.10$ at precision | $A$ behaves as a companion of its difficulty is expected to behave |
| Outcome-specific | $\Xi$ lower bound above 0 | The excess is specific to the outcome $B$ |
| $A$-general not excluded | $\Xi$ does not exclude 0 from below | The excess is not distinguishable from $A$ being generally disruptive |
| **Order dependence resolved** | An F11 interval excludes 0 | The named quantity depends on the position of the outcome constraint, by the registered contrast |
| **Order equivalence** | An F11 interval wholly inside $\pm 0.10$ at precision | The named quantity's dependence on position is smaller than the smallest effect of interest |
| Estimands disagree | §17.6 rows 3 or 4 of either table | The readings disagree; both are reported and neither is emitted |
| Indeterminate at a threshold | The interval spans that threshold | The design did not separate the two readings at that threshold |
| Insufficient precision | The realised half-width exceeds its precondition | The design did not achieve the registered precision |
| Reference heterogeneity | The three $\Delta_j$ intervals do not agree on one side of the threshold used | The L3 statement is emitted with the disagreeing reference named |
| Companion-difficulty qualifier | A realised gap exceeds 0.15 | The L3 statement names the reference and its realised gap |
| Vacuity asymmetry | An F6 difference exceeds 0.05 with its interval excluding zero | Composition changed how often the constraint could bind; claims follow both bounds |
| **Replication** | **For the named member**, the same classification in every registered configuration | That member's classification is stable across the registered configurations |
| **Configuration dependence** | **For the named member**, classifications differ across configurations | That member is configuration-dependent; the table is reported and no pooled scalar is quoted |

### 28.2 Identification statuses, which are not terminal

| Status | Meaning |
|---|---|
| `REFERENCE_SUPPORT_NOT_IDENTIFIED` | **New in v5.** Fewer than five families passed the full $V(R)$, or fewer than three core references could be selected under §13.15. The core and spectrum arms are dropped, L3a–L3e are withheld, and every emitted statement of the replication carries this status. It cannot be bypassed and no threshold moves in response |
| `EXCESS_NOT_IDENTIFIED` | $\Delta_R$ is not computable under the admitted arm set. Recorded beside `REFERENCE_SUPPORT_NOT_IDENTIFIED` when that is its cause |
| `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | §12.6's coverage criterion fails at design time, no core family supplies a straddling triple, or §13.13's support conditions fail on the confirmatory data. L3d and L3e are withheld; any fit is descriptive and outside support |
| `CANDIDATE_RESERVE_EXHAUSTED` | §12.6's expansion ran out of reserve rungs before coverage passed; the library rather than the model was the binding constraint |
| `DIFFICULTY_SUPPORT_MARGINAL` | Support holds on the point estimate but in fewer than 0.95 of bootstrap replicates |
| `A_GENERAL_NOT_EXCLUDED` | $\Xi$'s interval does not exclude 0 from below |
| `LOCAL_AND_SPECTRUM_DISAGREE` | §17.6 table 1 rows 3 or 4 |
| `LOCAL_TIER_DISAGREE` | **New in v5.** §17.6 table 2 rows 3 or 4: $\Delta_R$ and $\Delta_{\text{near}}$ classify differently |
| `DIFFICULTY_COORDINATE_DEPENDENT` | The registered and secondary coordinates give different L3d/L3e classifications |
| `DIFFICULTY_COORDINATE_DEGENERATE` | A companion's chance compliance reached 0.99 and its point was dropped from the fit |
| `INTERACTION_ESTIMATE_DRIFTED` | **New in v5.** A core reference's realised confirmatory $\kappa^{B}$ or $\hat p$ departed from the calibration value that admitted it, by more than §13.8's registered amount |
| `REFERENCE_ROLE_NOT_MATCHED` | **New in v5.** None of the three core references shares $A$'s declared contrastive discourse role; the excess is relative to markers of other discourse functions |
| `REFERENCE_POOL_SAME_FORM` | **New in v5, attached to every L3 statement.** The registered sentence: *the core reference pool is same-form with $A$ — an exact count of a marker word, differing only in which word and how many — so this excess is an excess relative to companions that share $A$'s predicate form and is not an excess relative to companions in general* |
| `COMPANION_CLASS_NOT_MATCHED` | Retained, and attached only to statements about $\Delta_{\text{broad}}$: the broad-class control is budget class where $A$ is production |
| `NEAR_FORM_ARM_NOT_AVAILABLE` | **New in v5.** Fewer than three Tier-2 controls qualified; $\Delta_{\text{near}}$ is not computed |
| `CLASS_ARM_NOT_AVAILABLE` | No Tier-3 budget severity qualified; $\Delta_{\text{broad}}$ is not computed |
| `CLASS_ARM_NOT_MATCHED` | A broad-class companion was admitted but $\lvert\iota_{CL} - \iota_A\rvert > 0.15$ |
| `OPERATING_POINT_AT_GRID_BOUNDARY` | **New in v5.** §12.3's bracketing rule could not be met for $n^*$ or $m^*$; the record names which side and why |
| `POSITION_CONFOUNDED` | Attached to every L1 statement in the configuration where the outcome constraint is not stated first |
| `HUMAN_VALIDATION_UNAVAILABLE` | No independent annotator; §10.5's scope sentence attaches |

### 28.3 Terminal statuses

| Status | Condition |
|---|---|
| `REGISTRATION_INCOMPLETE` | A §34 open decision is unclosed at stage 1 |
| `QUALIFICATION_FAILURE` | Code, model, environment, schema, witness, metadata, tier-labelling or provenance qualification fails |
| `APPARATUS_FAILURE` | Execution, cache, hashing, storage restoration, mask plumbing, integrity machinery or a registered §19 unit test fails |
| `RESPONSE_LENGTH_INCOMPATIBLE` | Every registered cap has truncation above 0.10 on constrained prompts |
| `TARGET_RANGE_EXHAUSTED` / `FOCAL_RANGE_EXHAUSTED` | An outcome constraint's curve stays outside its band at a registered grid boundary, the focal case after the §7.2 extension has been measured |
| `GRID_RESOLUTION_INSUFFICIENT` | Adjacent registered severities jump across a whole band |
| `REGIME_NOT_FOUND` | §12.4 adequacy fails |
| `COMPOSED_HEADROOM_FAILURE` | A registered cell type falls outside $[0.05, 0.95]$ on any of its constraints |
| `PREFREEZE_AUDIT_FAILURE` | A §18.1 field is absent and unexplained, an arm's admission is not traceable to a signed record, or the §33 checklist records an unresolved item |
| `MEASUREMENT_NOT_ESTABLISHED` / `MEASUREMENT_EVIDENCE_INSUFFICIENT` / `SPECIFICATION_AMBIGUOUS` | §10.7's Gate-1 rule fails |

Every terminal record carries the model and revision, gate, criterion,
threshold, observed value, complete curves, difficulty table, **qualification
table with each candidate's earliest failing component**, admission table,
spectrum table, composed table, degeneracy and truncation summary, verifier
status and measurement basis, artifact hashes, producing commit, environment
digest, the strongest permissible statement, and the estimands left
unanswerable. It also carries verbatim: **a terminal pre-confirmatory status
carries no evidence about the effect.**

`REGIME_NOT_FOUND` is a statement about the registered grid and is never
reported as a failure of the model or of the hypothesis.

---

## 29. Limitations and design trade-offs

**No independent human reproduced the verifier.** §10.7 establishes that the
instrument implements the predicate the prose specifies. It does not establish
that an independent human would reproduce the verdicts and does not claim to.
§10.5's scope sentence attaches to every claim under this basis, permanently.
The frozen §10.3 sampling plan stays unspent and a completed §10.3 supersedes
the basis rather than being blocked by it.

**v5 was designed after seeing all of v4r4, and its matching rule is fitted to
v4r4's failures.** This is the sharpest limitation of the *procedure* and it is
not reducible by any amount of care in v5's execution. §30 states it in full.
The mitigation is that v5's prospective performance is measurable — §23's
projection audit and §26's success criterion are both recorded before any
confirmatory outcome is seen — and that a rule fitted to four models on one
outcome constraint may simply not transfer.

**The core reference pool is same-form with $A$, which is a limitation as well
as a repair.** v4r4's references shared none of $A$'s form and its L3 statements
carried `COMPANION_CLASS_NOT_MATCHED`. v5's share all of it and its L3
statements carry `REFERENCE_POOL_SAME_FORM`. The excess $\Delta_R$ measures is
an excess relative to *other exact counts of a marker word at matched
difficulty*, which is a sharper counterfactual and a narrower one: it asks
whether *however* is special among discourse markers, not whether $A$ is
special among companions. $\Delta_{\text{near}}$ and $\delta_{\text{diff}}$
carry the broader question, less tightly, and §17.6 registers what their
disagreement means.

**Discourse role is declared, not measured, and the pool does not match $A$ on
it by construction.** §7.6 assigns every marker a role and §13.8 requires two
distinct roles among the three core references, with
`REFERENCE_ROLE_NOT_MATCHED` when none is contrastive as $A$ is. That is a
label a human assigned; nothing in this design measures whether the model
treats *though* and *however* as the same kind of connective, and a marker's
role in an informational answer under two simultaneous constraints may not be
its role in ordinary prose. Two of the eight registered markers are
contrastive, so the matched case is reachable; it is not guaranteed, and the
status says which happened.

**Three marker families are more alike than three arbitrary families.**
Between-family variation in $D(B \leftarrow R_j)$ will be smaller than v4r4's
design anticipated, which narrows $\Delta_R$'s interval and narrows what "a
companion like $A$" means. §11.8's fit carries family intercepts, and a flat
realised $\hat\beta$ over three near-identical families is less informative
about the difficulty relation than a flat $\hat\beta$ over three structurally
distinct ones would be.

**Load two only**, and the memo's three-place $\Gamma$ is not estimable here.

**Matched and fitted, not semantic.** Matching leaves other properties of $A$
free, so semantic identity-specificity is not identified and is never claimed.

**The length account is not identified, at any block count.** Response-length
shift and companion identity remain partly collinear across the companion sets
this pool can produce. v5 improves the situation and does not resolve it:
Tier-1 controls are length-neutral by construction and $A$ is length-neutral by
the same construction, so the *core* comparison is no longer confounded by a
lengthening or shortening companion. But the design still cannot test whether
$A$'s effect on $B$ operates *through* length, because that needs a companion
that changes length about as much as $A$ does without being $A$, and the
Tier-1 pool is chosen to change it as little as possible. The design reports
length diagnostics and states that they identify nothing about $A$.

**Lexical register is a mediator with no identification.** §22 registers the
register diagnostics because v4r4's follow-up found them more explanatory than
length. They are descriptive; nothing in this design identifies a register
mechanism.

**The difficulty relation is fitted on nine points.** Three families, three
rungs each, four parameters, five residual degrees of freedom. Enough for a
family-aware line; not enough for a per-family slope or a non-linear form.

**The difficulty coordinate is a choice with a cost.** $\iota$ nets out chance
and is comparable across constraint classes; it is also noisier, because it is
a ratio of two estimated quantities. v5 mitigates this by a chance ceiling, a
larger calibration sample, a two-split stability rule, and a core pool for
which $\kappa \approx 0$ so that the ratio is not one — but the coordinate's
properties on a Tier-3 spectrum rung are unchanged.

**Configuration dependence is a scope condition, not noise.** v5 additionally
*measures* it. An F11 interval excluding zero licenses L4b and nothing more: it
says the quantity depends on position and it does not say why.

**The position confound.** In the configuration where the outcome constraint is
stated second, $D(c \leftarrow g)$ mixes added load with a change of position.
$\Delta$-type quantities and the order contrasts are position-clean.

**Vacuous passing is bounded, not eliminated.**

**The stem is one more instruction.** It competes for compliance and could
interact with the constraints under study. Its satisfaction rate by load is the
diagnostic. **§7.7's realistic-witness rule additionally makes the stem's band
a design constant**, so a change to the stem would change which candidates are
admissible, and the stem is therefore frozen at the same level as a verifier.

**The confirmatory topics were used by v4r4.** §6.2 states the reuse, its
argument and its residual: sampling error shared between two studies, not
adjusted for.

**Calibration-A is not naive.** §6.2 states which of v5's candidate families
have a prior measurement on those topics and which do not.

**The compute is large and the full design has never been executed.** v4r4
registered a 47-cell full design and never ran one: both survivors ran 8 cells.
v5's full design is 56 cells and 172,032 generations per model. Whether four
replications can be executed is a resource question and is §34 D1, not a
scientific one, and a replication not executed is recorded `NOT_EXECUTED`
rather than analysed.

**Interaction risk is measured against $B$ at $m^*$ only.** $\kappa^{B}$ is a
property of the pair $(R,\ B\text{ at }m^*)$ on one model. No cross-model
transfer of an interaction verdict is licensed, and a reference valid on one
model may be invalid on another — which is correct, and is why §13 runs per
replication.

---

## 30. Provenance: how v5 was designed, and the v4r4 → v5 ledger

### 30.1 The declaration

- v5 was designed **after** observing the completed v4r4 study in full,
  including its Gate-4 tables, its confirmatory estimates, its two terminations
  and its L4 defect.
- v4r4's matching failures were used as **development evidence** to choose
  v5's structural taxonomy, candidate library, validity components, every
  threshold in §13, the calibration sample size, the focal grid and the support
  requirements.
- This creates a real risk of **overfitting the matching rule to v4r4**. §13.6's
  projection ceiling was chosen on a sample of twenty rate checks on one model;
  §13.4's chance ceiling on a split-half analysis of four models; §13.7's
  equivalence bound on an extrapolation from a 48-topic split to a 96-topic
  one.
- **Retrospective performance on v4r4 is not prospective validation.** No v5
  artifact may describe it as validation, and §33's red-team checks for the
  word.
- **v5 is the prospective test** of whether the revised control-construction
  procedure generalises. §26 registers the criterion, §23 registers the audit,
  and both are recorded before any confirmatory outcome is seen.

### 30.2 The ledger

Every artifact entering v5 from an earlier revision carries exactly one
classification in `dci1/reports/dci1v5/evidence_reuse_ledger.json`, together
with its source path, source hash, the reason reuse is scientifically valid,
and the v5 criterion it satisfies.

| Class | Meaning | Examples |
|---|---|---|
| `HISTORICAL_OUTCOME` | A v4r4 scientific result. Preserved, cited for provenance, **never** presented as a v5 observation and never re-analysed | v4r4's $D$, $\Lambda$, $\Delta_{\text{class}}$; both terminal reports |
| `DEVELOPMENT_EVIDENCE` | A v4r4 measurement used to choose a v5 rule | the Gate-2 calibration tables; `gemma-3n-e2b-it`'s Gate-4 rate table; the pre-screen difficulty tables |
| `REUSED_IMPLEMENTATION` | Source carried byte-identically, with a carry-over record | $A$'s counting and segmentation functions; `CX1`'s and `CX2`'s verifiers, carried as `MK1` and `XC1`; the `comma` and `sentence` statistics |
| `RECOMPUTED_DIAGNOSTIC` | A quantity computed for v5's design from v4r4 raw rows with a registered v4r4 verifier | every $\kappa^{B}$ in `d2_kappa_under_b.json`; every split-half figure in `d3` |
| `NEW_V5_EVIDENCE` | Produced under this protocol | everything the v5 lifecycle writes |

An entry in `REUSED_IMPLEMENTATION` must record a finding for all seven
registered invariants — verifier semantics, the model-facing prompt, instrument
identity, severity, the sampling regime, the model and its revision, and the
decoding configuration — and two of the seven are **measured** rather than
asserted: both revisions' compliance predicates are run over every carried
instrument against every case of the frozen boundary corpus, and every
constraint sentence stored on every carried row is compared with the wording v5
renders now.

**No v4r4 generation is carried into a v5 estimand.** v4r4's rows exist for v5
only as `DEVELOPMENT_EVIDENCE` and `RECOMPUTED_DIAGNOSTIC`; §14.2's admission
guard refuses them structurally, in both directions.

**Never present a reused v4r4 outcome as a v5 observation.** §33 checks for it
and the final report's every number is traceable to a v5 stage record.

---

## 31. Release

Released under a permissive licence when results are reported: all 624
non-sequestered v5 topics with the canary string and a manifest recording that
96 of the 720 are withheld; every constraint definition, ladder, wording,
witness, structural-metadata record, tier, class label and verifier source; the
graded-score and non-vacuity definitions; the difficulty-coordinate, chance and
counterfactual-chance definitions with their tables; the boundary suites and
adversarial corpora; study-wide and per-model freeze records; qualification,
gate, transition and terminal reports; **the candidate-qualification table with
every candidate's earliest failing component, and both calibration-split
tables**; commit and clean-tree records; lockfile, frozen dependency export and
environment manifest; the codebook; every prompt; every committed raw draw with
its content hash, artifact state, compliance vector, graded vector, presence
flags and degeneracy flags; carry-over records and the §30 ledger; the fitted
difficulty relations and their support diagnostics; **the projection audit of
§23**; masked and unmasked outputs; the unmask timestamp; analysis code; and
the machine-readable result table carrying each estimate with its
configuration, cell, claim level, family, identification status, measurement
basis, difficulty coordinate, reference-pool tier, standard error, marginal and
simultaneous bounds, realised half-width, realised variance decomposition,
achieved detectable effect and cell counts.

Every reported figure is reproducible from the result table without
regenerating a response, and every number in that table is reproducible from
accepted raw responses in the recorded environment.

---

## 32. Amendment procedure and allowed deviations

Before study-wide freeze, any change is a revision of this document, recorded
with its date, its evidence and its author, and is prospective by definition
because no confirmatory data exist under this version.

After study-wide freeze: operational settings that cannot change a scientific
quantity, such as device placement or batch size, may change with a recorded
environment note. Every other change creates v6. A model-specific frozen-field
change after that model's confirmatory generation begins creates a new protocol
version and leaves the original result unchanged.

**An amendment is never used to weaken a criterion in order to make a gate
pass.** Three consequences are made explicit.

1. **A gate failure is a result.** `REGIME_NOT_FOUND`, `FOCAL_RANGE_EXHAUSTED`,
   `REFERENCE_SUPPORT_NOT_IDENTIFIED`, `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and
   `COMPOSED_HEADROOM_FAILURE` are registered outcomes with registered
   readings. None is an occasion to widen a caliper, lower a ceiling, extend a
   ladder, add a family, or change a coordinate.
2. **A change adopted after a gate has run is adopted because that gate ran.**
   The changes this document makes are adopted after v4r4 *completed*, on
   evidence that document produced, and §30 declares it rather than presenting
   the changes as independent.
3. **No component of §13 changes after Gate 2.5 begins on the first
   replication.** From the moment the first v5 candidate-qualification record
   exists, $V(R)$ and every threshold in it are final for this version.

Amendments are recorded in a single append-only register carrying the amendment
text, its timing relative to every affected artifact, what it supersedes, and
what it leaves untouched.

---

## 33. The pre-freeze red-team checklist

Executed at stage 12 (`PREFREEZE_AUDIT`), recorded with a verdict per item, and
an unresolved item is `PREFREEZE_AUDIT_FAILURE`. The standing findings are in
`dci1/reports/dci1v5/v5_prereg_redteam.md`; this list is what the audit runs.

| # | Check | Where it is discharged |
|---:|---|---|
| 1 | No rule uses a v5 composed outcome to select a control | §13.11's schema refusal; §19 test 2 |
| 2 | No adaptive escape hatch exists after failed reference calibration | §13.14; §19 test 4; the backup-substitution path must not exist |
| 3 | No threshold in this document is unspecified | every value in §11.9, §12.6, §13.4–§13.15, §16.2 is a literal |
| 4 | No weighted score with unfrozen weights exists | §13.1: no composite score is registered |
| 5 | No candidate family may be added after outcome-bearing data | §12.6's reserve is frozen by §7.10; expansion picks, never authors |
| 6 | Core controls and spectrum controls are not conflated | §7.4's slot table; §13.12's exemption from $V_{\text{diff}}$ is explicit |
| 7 | Every quantity's identification assumptions are explicit | §13.13, §13.15, §28.2 |
| 8 | Gate 4 introduces no outcome-based selection | §13.14's five refusals |
| 9 | No unregistered order comparison is emitted | §11.7's F11; §17.5's emitter refuses an unregistered member |
| 10 | No stale v4r4 L4 logic survives | §17.7's signature and its three regression tests |
| 11 | Which historical data were used to design v5 is unambiguous | §30's declaration and ledger |
| 12 | No failure status can be silently bypassed | §28.2's statuses are written at design time onto a signed record and appear on every emitted statement |
| 13 | §10.7 is rule-equivalent to v4r4's, with every difference enumerated | the audit diffs the two texts and records the diff |
| 14 | No v4r4 outcome is presented as a v5 observation | §30; every final-report number traces to a v5 stage record |
| 15 | The word "validation" is not applied to any retrospective analysis | a text check over v5 artifacts |

---

## 34. Registered open decisions

Recorded here so they cannot migrate into the analysis. **All nineteen must be closed, with the
decision and its evidence recorded in the signed registration manifest, before
stage 1 can pass.** None may be decided after any v5 generation. **D15 to D18
came from the pre-freeze red-team** (`dci1/reports/dci1v5/v5_prereg_redteam.md`)
and D6 was reopened by it.

| # | Open decision | This document's standing proposal |
|---|---|---|
| **D0** | **Whether to adopt v5 at all**, given that its matching rule is fitted to v4r4 and that §30 says so plainly | Adopt, with §30's declaration attached permanently |
| **D1** | **The confirmatory compute budget.** Four models at 56 cells is 688,128 confirmatory generations, against v4r4's registered 577,536 for a design that never ran. Options: four models at 56 cells; four models at 47 cells, dropping the near-form arm and $\Delta_{\text{near}}$ with it; two models at 56 cells, halving the replication; 384 blocks at $M = 4$, which fails three precision preconditions under $\phi = 0.37$ | Four models at 56 cells, with the registered execution order of §6.1 and `NOT_EXECUTED` for any replication not reached |
| **D2** | Whether a load-three arm is added so that the memo's $\Gamma$ becomes estimable | No load-three arm; §5's exclusion stands |
| **D3** | **Whether the 96 new Calibration-B questions are authored before adoption.** They must exist and be verified against §6.2's four rules before stage 1, and authoring them is the largest non-compute prerequisite | Author before adoption; the bank hash enters the registration manifest |
| **D4** | **The Tier-1 marker vocabulary.** Eight are registered on three prospective rules (§7.6). A reader may hold that `namely`, `notably` or `overall` is not semantically neutral in an informational answer, or that eight is too many or too few | The eight of §7.10, with every rejection reason recorded |
| **D5** | Whether a weighted composite validity score replaces the lexicographic conjunction | Lexicographic; no composite score, because the development data cannot fix weights that generalise |
| **D6** | **Whether `REFERENCE_SUPPORT_NOT_IDENTIFIED` is terminal or an identification status.** §13.15 makes it an identification status so that a replication does not discard identified estimands for want of an unidentified one. A reader may prefer that a study which cannot identify its primary counterfactual should stop | Identification status, with §13.15's argument recorded |
| **D7** | **The interaction-gate ceiling of 0.90.** Derived from Gate 4's band and a 0.05 error allowance, and coinciding with a gap observed on twenty rate checks on one model | 0.90, with the coincidence recorded and not used as evidence |
| **D8** | **The chance ceiling of 0.75.** A stricter 0.50 costs a further family on two v4r4 models for no measured stability gain; a looser 0.90 is where the instability cliff is | 0.75 on the point, 0.85 on the Wilson upper bound |
| **D9** | Whether an independent annotator will be available, which decides whether §10.3 can ever supersede §10.5's basis | Unavailable; `deterministic_measurement_validated` with the scope sentence attached permanently |
| **D10** | Whether the broad-class arm carries more than one companion, which is what a class *claim* would require | One companion; no class claim is made |
| **D11** | **Whether the confirmatory topics are re-authored rather than carried from v4.** Carrying them shares sampling error between two studies | Carry, with §6.2's statement of the residual |
| **D12** | Whether $\delta_{\text{diff}}$ or an order contrast receives a magnitude threshold of its own | Direction and the SESOI only; the memo's 0.25 is not transferred |
| **D13** | **Whether F11 is primary-tier.** Making the order contrasts primary-tier gives them a simultaneous interval and a claim level and costs nothing in F1's width; leaving them secondary would make L4b unavailable | Primary tier, F11, licensing L4b |
| **D14** | Whether instructed compliance remains the difficulty coordinate now that the core pool is chance-free and $\iota$ equals raw compliance within it | $\iota$ remains primary, raw solo secondary, `DIFFICULTY_COORDINATE_DEPENDENT` on disagreement — because the spectrum and broad-class arms are not chance-free |

| **D15** | **Whether the memo's 0.10 and 0.25 apply to a same-form $\Delta_R$.** §11.9 refuses to transfer 0.25 to $\delta_{\text{diff}}$ because it is a different quantity. v5's $\Delta_R$ is also not quite the quantity the memo contemplated: its reference pool is matched on form as well as difficulty. A consistent reader could hold that neither threshold transfers | Both transfer, on the ground that the memo defined them for the *shape* of the contrast — a focal loss under $A$ against the same loss under a matched companion — and that shape is unchanged. Recorded as contestable |
| **D16** | **Whether Calibration-B measures the full carried set or only Calibration-A's survivors.** §12.7 restricts it, which changes no admission verdict and costs about 35,000 fewer generations per replication, at the price that the two splits are not exchangeable and §13.7's rule is "screen then confirm" rather than two independent measurements | Restrict, with §12.7's statement of the asymmetry. Measuring both in full is the alternative and it is purely a compute question |
| **D17** | **Whether a construct floor is registered for $m^*$.** §12.3 selects the focal severity whose *compliance* is nearest 0.80, over a grid now reaching $m = 16$. On `qwen3-4b`'s v4r4 curve that points at $m^* = 13$ — *every word at most 13 letters* — which is a real behavioural constraint and a weak construct. The focal band is defined on compliance and nothing bounds how weak the instruction may become | No construct floor; the realised $m^*$, $B$'s chance compliance at $m^*$, and $B$'s whole curve are reported, and §29 states that a high $m^*$ makes $B$ a weak instrument on that model |
| **D18** | **Whether the near-form arm is a precondition of emitting L3c.** L3c is the memo's refutation verdict, and v5's core pool is chosen to resemble $A$ closely enough that $\Delta_R \approx 0$ is a plausible consequence of the *design* rather than of $A$. The near-form arm is what distinguishes the two, and §34 D1 lists dropping it as a compute option | Not a precondition; L3c without the arm is emitted with `NEAR_FORM_ARM_NOT_AVAILABLE` and §17.6's fixed sentence. A researcher who accepts the red-team's R1 should make it a precondition, or close D1 so the arm is retained |

**What none of these can fix.** The length account is not identified by any
companion set this pool can produce (§29); a class claim needs a design this
document does not attempt (§5); and v5's matching rule was fitted to v4r4 and
can only be tested prospectively (§30).
