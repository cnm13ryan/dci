# Preregistration: when two verifiable instructions are composed, which one is delivered, how much is lost, and does the loss depend on the identity of the companion beyond its difficulty?

**Protocol identifier:** DCI-1
**Version:** 4.0, revision 3
**Date:** 21 August 2026 (drafted 20 August, amended and adopted 21 August)
**Confirmatory data collected at the time of registration:** none
**Registration target:** Open Science Framework, protocol-document format
**Adoption status:** **ADOPTED and REGISTERED. Not frozen. No confirmatory
data.** The researcher adopted this revision on 21 August 2026; the record is
`dci1/DECISIONS_V4R3.md` entry A0, and every study-wide rule below is bound
into a signed registration manifest under
`dci1/evidence/dci1v4r3/registration/`. No registered v4r2 constant, verifier,
grid, ladder, wording, threshold or evidence record has been changed on account
of this document. §33 records what remains open.

**What the adoption did not authorise**, and what is therefore not taken here:
any retrospective change to v4r2 or earlier evidence; any weakening of a gate
after observing a failure; any selection of a control from a composed outcome;
and **any separate researcher approval this protocol reserves** — in particular
§10.4's `measurement_basis = autorater_calibration_approved`, without which
Gate 1 cannot pass and which no agent may write on the researcher's behalf.

**Status of the documents this replaces.** v4 revision 2 was drafted, never
registered, never frozen and produced **no confirmatory data**: all four
registered replications stand at `REGIME_SCREEN` and no model has run Gate 1,
Gate 2 or anything after them. Under v4r2 §31 — *"Before study-wide freeze, any
change is a revision of this document"* — a pre-freeze change is a revision, so
this document is revision 3 and not v5. v4r2 is superseded in full and retained
as a design record. Its signed qualification, apparatus and regime-screen
records remain valid evidence **under v4r2's rules** and are never reinterpreted
here. DCI-1 v3 and v2 are closed; their preregistrations, amendments, signed
evidence trees and results reports are historical evidence, are not modified,
and are never confirmatory evidence for v4.

**Status of the four v4r2 design screens.** `fs_screen_v4` (FORM × STEM),
`bgrid_screen_v4` (the focal grid), `cal_screen_v4` (the Gate-2 calibration
screen) and `matrix_screen_v4` (the pairwise matrix) are **non-confirmatory
design evidence**. They supply exactly four things to this document: the
demonstration that the v4r2 prompt cannot start, the demonstration that raw
solo compliance is not a comparability coordinate, variance and slope
information for the power plan of §16, and a set of empirical checks to be
repeated prospectively. They license no scientific claim, their point estimates
are never the confirmatory effect this design expects, their topics are the
pre-screen and solo-calibration sets, and their rows are structurally excluded
from every v4r3 analysis input (§14.2). **No family, severity, threshold,
estimand or claim rule in this document was chosen because it made a screen
result larger, smaller or more significant.** §13.9 records the specific rule
that enforces this and §33 D6 records the one place where a screen quantity
does enter, and why that entry is variance information rather than effect
information.

**Design authority.** The construct decision of
`user-notes/dci-construct-pass2.md` (14 August 2026), unchanged from v4r2: it
settles the primitive observation, demotes the legacy target-damage estimand,
names reciprocal delivery loss as the primary estimand, and specifies in §G
row 1 the discriminating experiment. v4r2 §33 registered open decision **V5** —
*"Matched references only, or a difficulty-spanning set"*, default *"matched
only"* — and this revision closes V5 in the other direction, for reasons §2.4
gives.

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
| Graded score, $G_c$ | A deterministic real-valued score on $[0,1]$ recording how nearly $c$ was met, defined per constraint form in §7.6. |
| Compliance vector | The tuple $X = (X_c)$ over every constraint present in the prompt, with the graded vector $G = (G_c)$ and the degeneracy flags of §9.3. This is the primitive observation. |
| Unconstrained cell | A prompt containing the topic question and the answer-length stem and **no** numbered constraint. Load zero. |
| Solo cell | A prompt containing exactly one numbered constraint. Load one. |
| Composed cell | A prompt containing exactly two numbered constraints. Load two. |
| Companion | For an outcome constraint $c$ in a composed cell, the other constraint $g$ present. |
| Load | The number of numbered constraints in a prompt. Zero, one or two throughout. |
| Delivery loss, $D(c \leftarrow g)$ | $P(X_c = 1 \mid c \text{ alone}) - P(X_c = 1 \mid c \text{ with } g)$. Positive means composition reduced delivery of $c$. |
| Reciprocal pair | The two delivery losses of one composed cell, $D(c \leftarrow g)$ and $D(g \leftarrow c)$. |
| Asymmetry, $\Lambda$ | $D(B \leftarrow A) - D(A \leftarrow B)$. |
| **Chance compliance**, $\kappa_c$ | $P(X_c = 1 \mid \text{unconstrained cell})$: how often a response written without $c$ stated satisfies $c$'s verifier anyway. Measured on the same blocks as every other quantity (§8.1, §25). |
| **Instructed compliance**, $\iota_c$ | $\left(P(X_c = 1 \mid c\text{ alone}) - \kappa_c\right) / (1 - \kappa_c)$, defined when $\kappa_c < 1$. The share of the achievable improvement over chance that stating $c$ actually delivers. **This is the registered difficulty coordinate** (§13.3). |
| **Instruction lift** | $P(X_c=1 \mid c\text{ alone}) - \kappa_c$, the unnormalised form, reported as a diagnostic. |
| Companion swap, $\Delta$ | $\Delta_j = D(B \leftarrow A) - D(B \leftarrow R_j)$; $\Delta_R = D(B \leftarrow A) - \frac{1}{3}\sum_j D(B \leftarrow R_j)$ over the three **core** references. |
| **Difficulty-response relation** | $\mathbb{E}[D(B \leftarrow g) \mid \iota_g = d]$ over non-$A$ companions, estimated by the registered fit of §11.7. |
| **Difficulty excess**, $\delta_{\text{diff}}$ | $D(B \leftarrow A)$ minus the value the difficulty-response relation predicts at $\iota_A$, with $A$ excluded from the fit. §11.7. |
| Target constraint, $A$ | The exact-count constraint. Both an outcome and a companion. |
| Focal constraint, $B$ | The word-length constraint. It carries the primary outcome. |
| Core reference, $R_j$ | One of three constraints occupying the companion slot in place of $A$, admitted under §13.4 to be comparable to $A$ on instructed compliance. |
| **Spectrum companion**, $R_{f,-}$, $R_{f,+}$ | For each core reference family $f$, two further severities of the same family, one strictly harder than $A$ and one strictly easier, admitted under §13.6. They occupy the companion slot beside $B$ only. |
| **Class-control companion**, $CL$ | A single production-class companion, admitted under §13.7, beside $B$ only, to quantify how much of any excess belongs to constraint class rather than companion identity. |
| Constraint class | **Budget** ($S \le q$ or a rate $\le q$: satisfied by doing less) or **production** ($S = n$ or $S \ge q$: satisfied by doing something specific). $A$ is production, $B$ is budget. |
| Configuration | The tuple (model checkpoint, **position of the outcome constraint**). Every primary estimand is indexed by a configuration and no estimand is pooled across configurations. §11.1. |
| Topic, block | One question the model is asked, together with the wording indices assigned to it. All cells of a block share them. |
| Cell mean | The mean of an outcome indicator over all $M$ cached draws of one prompt cell. This is the analysis input. |
| Budget constraint | A constraint of the form "at most $q$ …", which a shorter response satisfies at least as readily as a longer one. |
| Prefix-closed | A constraint whose pass set is downward-closed under truncation of the response. Every count budget is; a rate budget and every production constraint are not. |
| Vacuous pass | A pass by a response that fails the registered non-vacuity predicate of §9.3. |
| Joint state | For a composed cell, the pair $(X_{c_1}, X_{c_2})$, taking one of four values. |
| Family | A declared set of quantities sharing one simultaneous confidence statement within one configuration. |
| Simultaneous interval | An interval constructed so that a stated confidence level applies to a whole declared family at once. |
| Šidák bound | The conservative critical value for a family of size $k$, using the two-sided level $1 - 0.95^{1/k}$ per member. Used for **planning only**; decisions read the bootstrap's studentised maximum-modulus value. |
| Precision precondition | The registered maximum realised simultaneous half-width for a primary member, below which no equivalence or threshold conclusion may be emitted. |
| Identification status | A per-claim marker recording whether the design as realised supports a given claim level. |
| Measurement basis | `human_validated`, `autorater_calibration_approved`, or `human_validation_unavailable`. |
| Autorater | A language model used only as a proxy instrument for verifier development and held-out evaluation. It never produces a behavioural score, never overwrites a deterministic verdict, and its judgments live in separate artifacts. |
| Masked analysis | Analysis performed on data whose companion labels have been permuted, so that analysis decisions cannot depend on the result. |
| Development data | The 24 pre-screen and 96 solo-calibration topics. The only topics any iterative or exploratory work may inspect, and only through the solo quantities §12.5 enumerates. |

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
verifier and referenced to its own solo baseline **and to its own chance
baseline**, reported jointly with the other instructions of the same prompt.

### 2.2 The primary scientific question

For a registered pair of constraints $(A, B)$, a registered model, and a
registered position of the outcome constraint:

1. Does composing each constraint with the other reduce its delivery relative to
   that constraint alone?
2. Is the reduction directionally asymmetric between the two?
3. **Is the reduction of $B$ specific to the companion $A$, or is it what a
   companion of $A$'s difficulty would produce whatever its identity?**

Question 3 is the discriminating question of `dci-construct-pass2.md` §G row 1.
v4r2 operationalised it with a single comparison: $A$ against three companions
matched to $A$ on solo compliance. This revision keeps that comparison and adds
a second, independent one, because a single matched set answers the question
only if the matching worked and only if the matched set is representative.
§2.3 and §2.4 give the evidence that neither could be assumed.

### 2.3 What the v4r2 screens established about the v4r2 answer

Three findings from non-confirmatory screens motivate this revision. Each is
design evidence: it changes what the *design* must contain, and none of it is
treated as an answer to question 3.

**(a) The v4r2 prompt could not start.** On the registered 96 solo-calibration
topics at $M_{\text{cal}} = 4$, $B$'s realised solo vacuity rate is at least
0.208, and as much as 0.870, at every severity of the registered focal grid on
all four models, against a §12.4 maximum of 0.10. Gate 2 returns `REGIME_NOT_FOUND` for every
replication before the reference question is reached. Under a prompt carrying a
uniform answer-length sentence the same cells are 0.000 to 0.060.
(`reports/cal_screen_v4/`.) §8.5 adopts that sentence.

**(b) Raw solo compliance is not a comparability coordinate across the
production/budget divide.** $A$ is an exact-count production constraint; an
unconstrained answer satisfies it by chance at rate **0.000** on all four
models. Every count-budget reference family is prefix-closed, and an
unconstrained answer satisfies the matched rungs by chance at 0.52 to 0.89.
Matching on raw solo compliance therefore equates a constraint the model must
work to satisfy with one it satisfies for free: **twelve of twelve references
in the matrix screen are matched to $A$ on raw solo compliance and two of
twelve on instructed compliance**, and two have *negative* instructed
compliance — stating them made the model satisfy them less often than not
stating them. (`reports/section_13_2_v4/instructed_compliance.json`.) This is
structural rather than incidental, it is measurable before any composed cell
exists, and it makes raw solo compliance unusable as the coordinate a
difficulty-response relation is read against. §13.3 replaces it.

**(c) The single matched set is fragile in exactly the way a single point
always is.** In the matrix screen, at a screen scale that licenses nothing,
$\Delta_R$ ran from $-0.024$ to $+0.101$ across four models while an admitted
reference *out-damaged* $A$ on two of them, and the same companions read
against a difficulty line placed $A$ above it on two models and below it on
two. A design whose entire answer to question 3 rests on the mean of three
companions cannot distinguish "the excess is real" from "these three companions
happened to be gentle".

### 2.4 What this revision does about it, and what it does not do

The response is **not** to abandon difficulty matching. Without controlling
generic companion difficulty, a difference in $D(B \leftarrow g)$ cannot be
attributed to companion identity at all. The response is to identify the
difficulty relationship instead of assuming it, on a coordinate that is
comparable across constraint classes, and to keep the local matched comparison
beside it as an independent reading:

| Layer | Estimand | Answers |
|---|---|---|
| **Local matching** | $\Delta_R$ | Does $A$ differ from three companions of closely matched instructed compliance? |
| **Difficulty spectrum** | $\delta_{\text{diff}}$ | Does $A$ differ from the empirical relation between companion difficulty and focal loss, fitted over nine companions spanning $A$ from both sides, with $A$ excluded from the fit? |
| **Reciprocal specificity** | $\Xi$ | Is any excess specific to the outcome $B$, or does $A$ damage other outcomes comparably? |
| **Class control** | $\Delta_{\text{class}}$ | How much of any excess is attributable to $A$'s structural class rather than its identity? |

The two excess estimands are complementary and are **not** two tests of one
hypothesis: $\Delta_R$ asks a local question and $\delta_{\text{diff}}$ asks a
global one, and §17.6 registers what to conclude when they disagree, in advance,
rather than choosing the agreeable one afterwards.

**Registered thresholds and their provenance.** The two $\Delta_R$ thresholds
are `dci-construct-pass2.md` §G row 1 verbatim, fixed on 14 August 2026 before
any observation in this constraint vocabulary existed:

> D(B←A) − D(B←R) > 0.25 supports H1 and licenses a pairwise construct.
> < 0.10 supports H2 and **refutes the pairwise framing entirely**, redirecting
> the programme to a load-and-capacity account.

§33 requires the memo hash, the quoted lines and both dates in the manifest.
**Those two numbers are not transferred to $\delta_{\text{diff}}$.** §11.8 gives
$\delta_{\text{diff}}$'s own decision rule and the argument for it.

---

## 3. Hypotheses and the claim ladder

### 3.1 The hypotheses that are separated

| Label | Statement |
|---|---|
| $H_{\text{pair}}$ | $A$ causes excess damage specifically to $B$, beyond every registered control. |
| $H_{\text{difficulty}}$ | $A$ behaves as a companion of its difficulty is expected to behave. |
| $H_{A\text{-general}}$ | $A$ is unusually disruptive, but about equally to every outcome, not specifically to $B$. |
| $H_{\text{class}}$ | Interference depends materially on the companion's structural class rather than on its identity. |
| $H_{\text{family}}$ | Interference depends materially on constraint family at fixed difficulty and class. |
| $H_{\text{length}}$ | Response-length change mediates or explains much of any apparent effect. |
| $H_{\text{order}}$ | The effect depends materially on the position of the outcome constraint. |
| $H_{\text{model}}$ | The effect differs across model checkpoints. |

$H_{\text{order}}$ and $H_{\text{model}}$ are handled by construction: every
estimand is defined within one configuration and no configuration-pooled scalar
carries a claim (§11.1, §15). $H_{\text{length}}$ is registered as a mediator
and never conditioned on (§22); §29 records that it is **not identified** by
this design and why. $H_{\text{class}}$ is bounded by the class arm (§13.7) and
by a permanent identification status (§28.2). The remaining four are separated
by the ladder below.

### 3.2 The claim ladder

Each level has a licensing rule, a fixed licensed statement, and an
identification gate. A level whose gate fails records an identification status
and is not emitted. No level licenses any statement above it. Every rule below
reads the **simultaneous** interval of the member's declared family (§15).

| Level | Claim | Licensing rule (within one configuration) | Identification gate |
|---|---|---|---|
| **L1** | Compositional delivery loss exists | The F1 simultaneous interval for the named $D(c \leftarrow g)$ has lower bound above 0 | $c$ has solo headroom (§12) and the position caveat of §11.4 is stated |
| **L2** | The loss is directionally asymmetric | The F1 simultaneous interval for $\Lambda$ excludes 0 | L1 conditions for both $D(B\leftarrow A)$ and $D(A \leftarrow B)$ |
| **L3a** | The excess over locally matched companions exceeds the generic-load threshold | $\Delta_R$ lower bound above 0.10 | Three core references admitted under §13.4; else `EXCESS_NOT_IDENTIFIED` |
| **L3b** | That excess reaches the source memo's pair-specific threshold | $\Delta_R$ lower bound above 0.25 | As L3a |
| **L3c** | Generic compositional load, locally | $\Delta_R$ upper bound below 0.10 | As L3a |
| **L3d** | $A$ is more disruptive than the difficulty-response relation predicts | $\delta_{\text{diff}}$ lower bound above 0 | §13.8 difficulty support holds; else `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` |
| **L3e** | The difficulty-response relation accounts for $A$ | The $\delta_{\text{diff}}$ interval lies wholly inside $\pm 0.10$ **and** its half-width meets the §16.2 precondition | As L3d |
| **L4** | The result replicates across configurations | The same L1/L2/L3 classification holds in every registered configuration | All configurations reached the corresponding level |
| **L5** | Semantic identity-specificity, universal pair property, arbitration, mechanism, class attribution, or generalisation | **Never licensed by this design** | Permanently withheld; §5 and §29 state why |

**Outcome specificity is a gate on the wording of every L3 statement, not a
level.** When the F1 simultaneous interval for $\Xi$ has lower bound above 0,
an emitted L3a, L3b or L3d statement says the excess is *specific to the
outcome $B$*. Otherwise the statement is emitted with the identification status
`A_GENERAL_NOT_EXCLUDED` and says the excess *is not distinguishable from $A$
being generally disruptive as a companion*. This is registered because a
positive excess with a non-positive $\Xi$ is exactly the pattern the matrix
screen produced on two models, and the reading has to be fixed before the
number is seen.

**Every L3 statement, at every sub-level, carries
`COMPANION_CLASS_NOT_MATCHED`** and the fixed sentence of §28.2, because the
reference pool is budget-class by construction (§7.3) and $A$ is production
class. §13.7's class arm reports how large that gap is; it never removes the
status.

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
prompts for one exact-count constraint, one word-length constraint, three core
reference constraints, six spectrum companions, one class-control companion,
four model checkpoints, two positions of the outcome constraint, one decoding
policy per model, one prompt template, one language, and one topic space.

Excluded by design, and never claimed:

- **Loads above two.** The construct memo's best-evidenced interaction
  quantity, the three-place $\Gamma$, requires a third *scored* constraint.
  The answer-length stem of §8.5 is template text and is not a scored
  constraint, so it does not make this a load-three design. §33 D2 records the
  extension as an open decision.
- **Semantic identity-specificity.** The design compares $A$ against companions
  matched on instructed compliance and instruction length and against a fitted
  difficulty relation. Matching and fitting leave other properties of $A$ free,
  so an excess attributable to $A$ is an excess relative to that controlled set,
  not to the semantic content of $A$.
- **Constraint-class attribution.** The class arm contains **one** production-
  class companion. One companion cannot separate "production constraints
  interfere more" from "this particular production constraint interferes more".
  $\Delta_{\text{class}}$ is registered as a bound on how much class could
  matter, never as an estimate of a class effect. §29 states the design a class
  claim would need.
- **Response-length mediation.** Registered as a mediator, reported, never
  conditioned on, and — on the evidence of §29 — **not identified** by any
  companion set this pool can produce.
- **Universal pair properties.** No scalar is quoted without its configuration
  and no configuration-pooled scalar carries a claim.
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

| Order | Model label | Repository | Note |
|---:|---|---|---|
| 1 | Gemma 3n E2B-it | `google/gemma-3n-E2B-it` | Completed v3 confirmatory |
| 2 | Gemma 3n E4B-it | `google/gemma-3n-E4B-it` | Completed v3 confirmatory |
| 3 | Qwen3-4B, thinking disabled | `Qwen/Qwen3-4B` | Terminal at v3 Gate 2A; estimable here (§13.5) |
| 4 | Qwen3-4B instruct-only | `Qwen/Qwen3-4B-Instruct-2507` | Terminal at v3 Gate 2A; estimable here |

Execution order places the two Gemma replications first so that the apparatus is
exercised where prior operating points are known. **No replication is blocked by
the outcome of another.** Exact repository revisions are pinned in the signed
registration manifest before qualification and asserted at every generation.

**Cross-replication firewall.** Every study-wide rule is fixed in the signed
registration manifest before the first qualification. Only the following adapt
mechanically by model, and only through the registered gates of §18:

| Model-adaptive through §18 | Study-wide, fixed before the first qualification |
|---|---|
| $n^*$, $m^*$, whether the focal extension of §12.3 was needed, the completion-token cap, the shortlist, the three admitted core reference families and their severities, the six spectrum severities, the class-control family and severity, the realised difficulty support, and whether the full or the reduced design runs | Constraint families and severity ladders, the prompt template, graded-score definitions, non-vacuity predicates, the difficulty coordinate, every selection algorithm and tie-breaker, every caliper and offset, the number and structural composition of references, estimands, the difficulty-model functional form, thresholds and regions, precision preconditions, multiplicity families, the bootstrap, the decoding-policy form, $M$, the block count, masking rules, gate rules, artifact semantics, the claim ladder, and the codebook |

A scientific outcome from one replication never modifies a study-wide rule used
by another.

### 6.2 Topics

The task space is short open-ended informational questions answerable in sixty
to one hundred and twenty words from general knowledge, without tools,
arithmetic, or recall of a specific named fact.

The v4 bank contains **624 newly authored questions**, 52 in each of the twelve
declared subject areas: everyday science, history, geography, food, music,
sport, work and organisations, health and the body, technology, language and
writing, art and design, the natural world. Each question is verified
individually against four rules: answerable from general knowledge, no single
correct short answer, no reused text from any public dataset or examination, and
no wording that itself mentions any letter, word length, word shape,
punctuation-count, or capitalisation requirement. **This fourth rule governs
authored question text. Fixed template text that is identical in every cell —
including the answer-length sentence of §8.5 — is not question text and is not
restricted by this rule**; §8.5 gives the argument.

Within each area the 52 questions are shuffled with a fixed seed and split.
**The split is v4r2's, carried unchanged, on v4r2's seed.**

| Set | Per area | Total | Permitted use |
|---|---:|---:|---|
| Pre-screen | 2 | 24 | Completion-cap selection, dense ladder screen, candidate expansion, Gate 1 validation material |
| Solo calibration | 8 | 96 | Solo-compliance and chance-compliance curves; selection of $n^*$, $m^*$, core references, spectrum severities and the class companion |
| Composed validation | 2 | 24 | Composed-headroom viability only (§13.10) |
| Confirmatory | 32 | 384 | The frozen confirmatory experiment |
| Sequestered | 8 | 96 | A future uncontaminated rerun only |

**An earlier draft of this document registered 34 and 6, and that split is not
executable.** It was chosen so that 408 blocks would meet every §16.2 precision
precondition at $M = 4$. But the released bank holds the 528 non-sequestered
questions and the other 96 exist to this repository only as opaque identities
and content hashes: the two extra confirmatory topics per area could only be
drawn from text that no v4-era process is able to read, and materialising them
is precisely what §6.2 forbids. The finding was made by reading the topic
module rather than the table. §16.2 reaches the same preconditions by raising
$M$ from 4 to 8 on v4r2's 384 blocks, which costs generations instead of the
sequestered set; §33 D1 records it.

No v3 topic and no B+R pilot topic enters any v4 set. The v3 sequestered 96
remain sequestered and are not opened. Sequestered v4 text is inaccessible to
the design and execution team throughout v4, existing to the implementation only
as opaque identities and content hashes.

**The reserved sets are reserved against the whole programme, not only against
the confirmatory run.** The composed-validation 24, the confirmatory 384 and the
sequestered 72 are unspent as of this document, audited over the 285,936 rows
every v4-era process has generated rather than over source, and §12.5 fixes what
development work may touch.

---

## 7. Constraints

### 7.1 The two outcome constraints

> **A:** Use the word *however* exactly $n$ times.
> **B:** Every word in the answer must have at most $m$ letters.

Registered target grid $n \in \{1,\dots,8\}$.

Registered focal grid $m \in \{7, 8, 9, 10\}$, with a **registered conditional
extension** to $m \in \{11, 12\}$ (§7.2). The word *however* has seven letters,
so $m \ge 7$ is required for $A+B$ to be jointly satisfiable.

$A$ and $B$ are both outcome constraints and both companions. Neither is
privileged in the recording of the compliance vector. $A$ is a **production**
constraint and $B$ is a **budget** constraint; §7.3 and §28.2 carry the
consequence.

### 7.2 The focal extension, and when it is measured

The focal grid is $\{7,8,9,10\}$. The extension $\{11,12\}$ is measured **only
when §12.3's selection finds no eligible severity in the registered grid**, and
selection then runs over the union of the two. This is a study-wide
deterministic escalation rule, not a per-model grid.

It is registered in this form, rather than as a flat six-rung grid, on evidence
and on the rule's own logic. Under the §8.5 stem the registered grid supplies an
in-band $m^*$ on three of four models; on the fourth it is exhausted, and
$m = 11$ and $m = 12$ restore it. A *flat* extension would change $m^*$ on a
model whose registered grid already works, because §12.3 selects the severity
nearest 0.80 and a new rung can be nearer — moving a replication off an
operating point the registered grid supplies. The escalation rule cannot do
that: where the registered grid works, the extension is never measured.

$B$'s rule is unchanged at every severity: the longest alphabetic run is at most
$m$. The four §7.5 wordings are parameterised on $m$ and render at 11 and 12
from the same four strings. Boundary-suite expectations at $m = 11$ and $m = 12$
are authored and frozen before qualification (§10.2), and the token used to
violate $B$ in the witness suite must exceed the loosest admissible $m$.

### 7.0 The candidate library, and the three populations it feeds

v4r2 asked a small question of the reference pool — *are there three
approximately matched controls?* — and answered it with a caliper. v4r3 asks a
larger one — *does the pool support an empirical difficulty-response relation
at $A$'s difficulty?* — and a caliper cannot answer that. Three populations are
therefore named and kept distinct, and no rule in this document is allowed to
confuse them.

| Population | What it is | Fixed by |
|---|---|---|
| **Candidate library** | every (family, severity) the grammar below declares: **334 severities in 20 families** | this document |
| **Measured vocabulary** | the severities §12.2 actually measures for a model: the 190 round-0 rungs plus whatever §12.6's expansion admits | §12.6, per model, before Gate 1 |
| **Final references and spectrum** | the three core references and the nine fit points | §13.4 and §13.6, per model, at Gate 3 |

**The library is a grammar, not a list.** A candidate family is a *counted
statistic* under a *predicate form*, and nothing else is a candidate family.

Nine registered counted statistics: `b_initial`, `ing_final`, `one_letter`,
`doubled_letter`, `comma`, `capital_char`, `capital_word`, `letter_a`,
`y_final`.

**Eight registered feature groups**, which say which statistics measure the
same property of an answer: each statistic is its own group except
`capital_char` and `capital_word`, which are both `capital`. Two families of
one group never co-occur in a cell (§7.5) and never both enter the core
reference set (§13.4).

The grouping is a scientific rule and not bookkeeping, and it was **forced by
the witness suite rather than written in advance**. Run over every pair of
distinct families, §7.5's non-entailment obligation failed 1,748 times in
exactly two shapes, both structural: a count budget at $q = 0$ entails the rate
budget of the same numerator at every $q$, because $S \le 0$ forces the rate to
zero; and `RF6` at $q = 0$ entails every `CR6` severity, because zero
upper-case characters forces zero words carrying one. For such a pair *no*
response satisfies the first and fails the second, so the obligation is
unsatisfiable rather than unmet. A design that could put both families in the
core reference set would be putting one measurement in two slots, and the
§11.7 fit would carry three intercepts over two properties of an answer.

Four registered predicate forms, over a statistic $S$, a word count $W$ and a
severity $q$:

| Form | Predicate | Class |
|---|---|---|
| count budget | $S \le q$ | budget |
| rate budget | $100 S / W \le q$, and a wordless answer fails | budget |
| count lower bound | $S \ge q$ | production |
| rate lower bound | $100 S / W \ge q$, and a wordless answer fails | production |

**Each family carries two ladders**: the *registered ladder* that §12.2
measures at round 0, and a *frozen reserve* that is a superset of it and is the
only source from which §12.6's expansion may draw. Both are fixed by this
document. Because severity parameters render as numerals and no wording's word
count depends on its severity (§7.5), a reserve rung inherits its family's four
frozen wordings exactly, and §10.2 freezes its boundary cases over the whole
declared range before qualification. Admitting a reserve rung therefore adds no
instrument that carries no evidence.

**The lexical rule, corrected.** A word is a maximal run of alphabetic
characters in the answer, where *alphabetic* is Unicode general category L;
**the answer is segmented first and each word is lower-cased for the suffix and
letter tests**; comma and upper-case-character counts read raw characters; a
word's *letters* are the characters of the word as written.

The composition order is stated because v4r2's helper reversed it —
lower-casing the whole response and then segmenting — and §10.2's independent
reimplementation, written from this prose, disagreed with the primary because
of it. Exactly one character in the Unicode range behaves differently under the
two orders: `İ` (U+0130) lower-cases to `i` followed by U+0307 COMBINING DOT
ABOVE, which is not alphabetic, so folding first splits the word. Under the
reversed order `İstanbul` is two words of one and seven letters, $B$ at $m = 7$
passes an answer containing an eight-letter word, and every letter test reads
fragments. §10.2 adjudicates a disagreement against this prose, so v4r3
composes in the order written here. The character occurs **zero** times in the
285,936 rows every v4-era process has generated, so no measured quantity moves;
the correction is prospective, the boundary suites carry a frozen case for it,
and §24 reports its realised frequency.

$A$ is **not** affected and is deliberately left alone: §9.2 registers $S_0$ in
its own words — *take the whole response, lower-case it, find every maximal run
of alphabetic characters, count the runs equal to* however — which is
fold-then-segment, and that is what $A$'s carried counting function does. The
two rules differ because the two constructs differ: $A$ counts occurrences of a
string, and $B$ and the families make claims about words as objects, whose
identity must not depend on case. $A$'s construct string, segmentation function
and counting function stay byte-identical to the closed v3 instrument and its
§10.2 carry-over survives.

### 7.3 The reference pool

**Sixteen families, all budget class** — the eight registered count budgets and
one rate budget per registered numerator. All constraints are single-clause,
apply to the whole answer, and are decided by deterministic character
operations under the lexical rule of §7.0.

**Count-budget families** — the v4r2 pool, unchanged, ladders complete and
already dense, so their reserve is their ladder:

| Family | Template | Ladder |
|---|---|---|
| RF1 | At most $q$ words in the answer may begin with the letter b. | $0 \dots 8$ |
| RF2 | At most $q$ words in the answer may end with the letters ing. | $0 \dots 8$ |
| RF3 | At most $q$ words in the answer may have one letter. | $0 \dots 8$ |
| RF4 | At most $q$ words may contain two identical adjacent letters. | $0 \dots 6$ |
| RF5 | The answer may contain at most $q$ comma characters. | $0 \dots 12$ |
| RF6 | The answer may contain at most $q$ upper-case English letters. | $0 \dots 12$ |
| RF7 | At most $q$ words in the answer may contain the letter a. | $0 \dots 24$ |
| RF8 | At most $q$ words in the answer may end with the letter y. | $0 \dots 8$ |

**Rate-budget families** — one per registered numerator, added in this
revision. The reserve is the frozen expansion range of §12.6; the ladder is the
subset §12.2 measures at round 0.

| Family | Numerator | Round-0 ladder ($q$, percentage points) | Reserve |
|---|---|---|---|
| CR1 | RF1's, unchanged | 1, 2, 3, 4, 5, 6, 8, 10 | $1 \dots 14$ |
| CR2 | RF2's, unchanged | 1, 2, 3, 4, 5, 6, 8, 10 | $1 \dots 14$ |
| CR3 | RF3's, unchanged | 1, 2, 3, 4, 5, 6, 8, 10 | $1 \dots 14$ |
| CR4 | RF4's, unchanged | 3, 5, 7, 9, 11, 13, 15, 18 | $2 \dots 20$ |
| CR5 | RF5's, unchanged | 1, 2, 3, 4, 5, 6, 8, 10 | $1 \dots 14$ |
| CR6 | **new**: words containing an upper-case letter | 3, 4, 5, 6, 7, 8, 10, 12 | $1 \dots 16$ |
| CR7 | RF7's, unchanged | 24, 28, 32, 36, 40, 44, 48, 52 | $20, 22, \dots, 56$ |
| CR8 | RF8's, unchanged | 1, 2, 3, 4, 5, 6, 8, 10 | $1 \dots 14$ |

**158 reference severities at round 0**, in 16 families; **218** in the
declared range.

**No rate ladder contains $q = 0$.** $100 S / W \le 0$ holds exactly when
$S \le 0$ for any answer with a word, so a rate rung at zero would enter the
pool as a second family carrying a first family's meaning, and §12.6's coverage
criterion counts cross-family overlap. An executable check refuses it.

**Why every numerator gets a rate form.** Every count budget is prefix-closed:
its pass set is downward-closed under truncation, so the empty string scores 94
of 94 on the count pool. That is the structural source of finding 2.3(b) — a
prefix-closed constraint is satisfied for free by a short answer, so its raw
solo compliance measures answer length as much as instruction-following, and
its chance compliance $\kappa$ is high, which compresses $\iota$ and pushes
rungs out of §13.5's band. A rate is not prefix-closed and the empty string
passes none of the rate severities. v4r2's draft carried three rate families;
three is too few to supply §13.6 with the three straddling triples it needs
from a pool whose other thirteen members share a structural defect, and §12.6's
coverage criterion is what makes that concrete rather than a matter of taste.

**Why no lower-bound family is a reference.** Lower bounds ($S \ge q$) also
break prefix closure, and they were considered and **excluded from the
reference pool**: a count lower bound imposes a length *floor*, pushing
response length up while $B$ pushes it down, which replaces one length confound
with its mirror image. They appear only in the class arm of §7.4, where that
property is not in the way of anything the arm measures.

**The eight (numerator, budget form) pairs are the whole reference grammar.**
There is no expansion reserve of unregistered *families* for the reference
pool, because the grammar is already exhausted at the budget forms: §12.6's
expansion is therefore a densification of ladders, never an authoring of
constraints.

**The pool is budget class throughout, and this is a registered limitation, not
an oversight.** $A$ is a production constraint. A reference pool of budget
constraints therefore matches $A$ on difficulty and never on class, so every
excess this design measures is an excess *relative to budget-class companions*.
§28.2's `COMPANION_CLASS_NOT_MATCHED` attaches to every L3 statement and §29
states the design that would remove it.

### 7.4 The class-control pool

**Four families, production class**, admissible **only** to the class arm of
§13.7 and never to the core reference set or the spectrum. An executable check
refuses a plan that places a class family in any reference or spectrum slot.

| Family | Form | Numerator | Round-0 ladder | Reserve |
|---|---|---|---|---|
| CL7 | count lower bound | RF7's | 10, 20, 30, 45, 60, 80, 100, 130 | $5, 10, \dots, 140$ |
| CL8 | count lower bound | RF8's | 2, 3, 5, 7, 10, 14, 19, 25 | $1 \dots 28$ |
| CP4 | rate lower bound | RF4's | 5, 8, 10, 12, 15, 18, 22, 28 | $2 \dots 32$ |
| CP7 | rate lower bound | RF7's | 30, 34, 38, 42, 46, 50, 56, 64 | $20, 22, \dots, 76$ |

Thirty-two class severities at round 0; 116 in the declared range. The count
ladders are geometric rather than uniform because the underlying counts vary
roughly threefold across the registered models while the corresponding rates do
not; a uniform count ladder cannot serve four replications.

**The two rate lower bounds are new in this revision and they exist for a
measured reason.** The pairwise-matrix screen found that the one production
companion it ran cost $B$ **+0.601** and **+0.632** where $A$ cost +0.086 and
+0.228 — so $\Delta_{\text{class}}$ was measured between companions of wildly
different difficulty and bounds almost nothing. A count lower bound is hard to
make gentle: it demands an absolute number of qualifying words and so scales
with length. A *rate* lower bound is scale-free and can be tuned to any
difficulty, so §13.7 has a real chance of admitting a class companion matched
to $A$ on $\iota$, and a difficulty-matched class contrast is the only kind
that bounds a class effect rather than restating a difficulty gap.

**A rate lower bound is classed `production`, and its one impurity is
recorded.** Its registered satisfaction route is to produce more of the counted
feature. It also admits a budget-like route — deleting non-conforming words
raises the rate — and this document states that rather than hiding it, because
the class arm exists to bound a class effect and an honest bound needs an
honest label. §29 carries the consequence.

**190 severities across 20 families** enter the §12.2 dense screen at round 0;
the declared candidate library is **334 severities across 20 families**.

### 7.5 Properties established before generation

Executable tests, all required to pass at qualification:

- **Parse independence.** Each verifier receives the response text and its own
  constraint identity and severity. It receives no companion identity, cell
  label, order, or other verifier's output.
- **Joint satisfiability.** For every **realisable** unordered pair of
  constraints of distinct kinds at every severity of the **declared range**, a
  machine-verified witness response satisfies both at once. A pair is
  realisable when some registered cell can contain it: $A$ with anything, $B$
  with anything, one core reference with another **of a different feature
  group**, and the class companion with $A$ or $B$. 25,337 pairs; the suite
  discharges all of them and refuses to construct a witness for a pair the
  design cannot realise, so §7.0's grouping and §13.4's diversity rule are
  checked against each other rather than assumed compatible. The pool of §7.3
  is jointly satisfiable pool-wide: every reference family is an upper bound on
  a numerator, and an answer short of every bound satisfies all of them at once.
  Each class family's witness obligation is discharged against $A$ at every $n$
  and against $B$ at every admissible $m$, which is the complete set of pairs
  the design can realise for a class companion (§13.7 places a class family
  only beside $B$, and §7.5's obligation is nevertheless proved against both).
- **Non-entailment.** For every such pair, one verified response satisfies the
  first and fails the second, and one does the reverse.
- **Witness-constructor envelope.** Every witness constructor asserts the
  companion class it was written for and refuses outside it. This is registered
  because a constructor used outside its envelope was found to report a
  construction failure as an entailment claim.
- **Wording equivalence.** $A$, $B$ and each family carry four frozen wordings,
  checked for identical meaning and required to produce identical verdicts on a
  fixed set of twenty test responses at every severity.
- **Wording length.** Every reference, spectrum and class wording at **every
  severity of the declared range** is within 20% of the corresponding wording of
  **$A$** in alphabetic-run word count. Severity parameters render as numerals
  and contribute no words, and `assert_severity_invariance` proves that no
  wording's word count moves with its severity rather than assuming it — which
  is what lets §12.6 admit a reserve rung without authoring anything. v4r2
  asserted only that *some* severity of each family was feasible; v4r3 asserts
  *all*, because a rung that could never be admitted for a typographic reason
  would silently shrink the coverage §12.6 exists to deliver.
- **Rule vocabulary.** The full-prose rule statements of §7.3 and §7.4 are
  eleven and twelve words and could never meet the caliper, so they are the
  *definition* of each family and never a wording. Every compact wording is
  checked against its rule statement's vocabulary, so a wording cannot quietly
  stop stating its own rule.
- **Class labelling.** Every family carries a declared class in
  {`budget`, `production`}, asserted against its predicate form, and the
  reference/spectrum slots refuse a `production` family.

### 7.6 Graded scores

Every verifier additionally returns a deterministic graded score in $[0,1]$,
recorded on every row and never used as a primary outcome.

| Constraint form | Graded score |
|---|---|
| $A$, exact count of a target word | $\max(0,\, 1 - \lvert s_0 - n \rvert / n)$ |
| $B$, every word at most $m$ letters | $1 - (\text{words longer than } m) / (\text{total words})$, and $0$ for an empty answer |
| Count budget, at most $q$ | $\min(1,\, q / \max(q, \text{count}))$ for $q>0$; $\mathbb{1}[\text{count}=0]$ for $q=0$ |
| Rate budget, at most $q$ percent | $\min(1,\, q / \max(q, \text{rate}))$ when the rate is positive; $1$ when it is zero; $0$ for a wordless answer |
| Count lower bound, at least $q$ | $\min(1,\, \text{count}/q)$ for $q>0$ |
| Rate lower bound, at least $q$ percent | $\min(1,\, \text{rate}/q)$ for $q>0$; $0$ for a wordless answer |

Graded scores support the manipulation-check reading and enter the robustness
family of §15.

---

## 8. Design

### 8.1 The cell plan

Per model replication the design registers: $A$, $B$, three core references
$R_1, R_2, R_3$ (§13.4), six spectrum companions $R_{f,-}, R_{f,+}$ for
$f \in \{1,2,3\}$ (§13.6), and one class-control companion $CL$ (§13.7). Every
block runs:

| Arm | Cells | Contents |
|---|---:|---|
| Unconstrained | **1** | The topic question and the §8.5 stem, no numbered constraint |
| Core solo | **5** | One per core constraint: $A$, $B$, $R_1$, $R_2$, $R_3$ |
| Core composed | **20** | Each of the $\binom{5}{2} = 10$ unordered pairs in each of the two orders |
| Spectrum solo | **6** | One per spectrum companion |
| Spectrum composed | **12** | $B$ + each spectrum companion, in each of the two orders |
| Class solo | **1** | The class-control companion alone |
| Class composed | **2** | $B + CL$ in each of the two orders |
| | **47** | **cells per block** |

The position of the outcome constraint is a **within-block** factor: every block
runs both order variants of every composed cell, so every block contributes to
both configurations and the order contrast is paired within topic.

Every generation is scored on **every constraint the verifier set contains**,
not only on those present in its prompt (§9.1, §25): a composed generation
yields two *treated* observations and the unconstrained cell yields one *chance*
observation per registered constraint. So a block yields 5 + 6 + 1 = 12 solo
observations, 2 × (20 + 12 + 2) = 68 composed observations, and one full
chance vector, per draw.

**Why the spectrum arm is not a full matrix.** A spectrum companion appears
beside $B$ only. Crossing the six spectrum companions with each other and with
$A$ and the core references would add 90 composed cells per block for quantities
no registered estimand reads. The full reciprocal matrix that $\Xi$ needs is
retained over the five core constraints, exactly as v4r2 registered it, and the
spectrum buys the difficulty relation at linear rather than quadratic cost.

**Why the spectrum arm runs both orders.** In the matrix screen $B$ lost 0.288
and 0.350 of its compliance purely by being stated second, and $\Delta_R$
computed within a single order changed sign on all four models. A spectrum
measured in one order would estimate the difficulty relation in a position where
the focal loss is dominated by position. Both orders is what makes
$\delta_{\text{diff}}$ well defined, not a robustness nicety.

**Why the unconstrained cell is registered.** Chance compliance $\kappa_c$ is
the denominator of the registered difficulty coordinate (§13.3) and the subject
of §25. It has to be measured on the confirmatory blocks, at the same $M$, under
the same stem, for every constraint at once, or the coordinate the design reads
is not the coordinate the design registered.

### 8.2 Draws and cell means

$M = 8$ cached stochastic draws per cell. All $M$ enter the cell mean; no draw
is selected, discarded, or replaced. Blocks remain the only resampling unit
(§14).

### 8.3 Size

**384 confirmatory blocks.** Because order is within-block, every block enters
both configurations, so each configuration is estimated on all 384 blocks. Per
model: $47 \times 384 \times 8 = 144{,}384$ cached generations. Across four
models, **577,536**. §16 gives the justification and the registered menu.

A sensitivity run repeats the 34 composed cells on the first 96 confirmatory
blocks at temperature 0 with one draw per cell, giving 3,264 further generations
per model, reported as a different generation population.

### 8.4 Order and wording allocation

**Order is a cell-level factor.** For every composed pair the block runs both
variants. The registered slot order is

$$(A,\; B,\; R_1,\; R_2,\; R_3,\; R_{1,-},\; R_{1,+},\; R_{2,-},\; R_{2,+},\; R_{3,-},\; R_{3,+},\; CL),$$

and one variant states the earlier constituent first, the other states it
second. Order is exactly balanced by construction inside every block, and each
configuration uses all 384 blocks.

**Wordings are a block-level factor.** For a composed cell with constituents
$(c_1, c_2)$ in registered slot order, block index $i$ fixes wording index
$i \bmod 4$ for $c_1$ and $\left(i + \lfloor i/4 \rfloor\right) \bmod 4$ for
$c_2$, applied identically to both order variants of that cell. Solo cells use
$i \bmod 4$. The unconstrained cell has no wording index.

Because order does not depend on the block index, wording and order are
orthogonal by construction, and each of the four wordings appears in 96 of the
384 blocks in each order of each cell type.

Every generative stage carries an executable allocation assertion stating the
intended count for every wording and every order, and the assertion refuses a
plan containing a structural zero or a skew. Where a formula and an assertion
disagree, qualification fails.

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
severity, ladder, wording or witness obligation, and is not subject to the §7.5
length caliper. Its realised satisfaction rate — the share of answers landing in
$[60,120]$ words — is recorded as a diagnostic on every stage record, **by
load**, so that a strong load-dependence in it is visible. That rate gates
nothing and no estimand reads it.

**Why it is registered.** §9.3's non-vacuity threshold is registered on the
reasoning that the topic space asks for sixty to one hundred and twenty word
answers, so a much shorter answer has abandoned the task rather than satisfied
the constraint. Under the v4r2 template the prompts never said so, and both
Qwen replications answered a $B$-solo prompt in a median of eight words: the
registered vacuity threshold rested on a premise the instrument did not put to
the model. This change does not alter what counts as vacuous; it makes the
prompt state the expectation against which vacuity was already being judged.
Every registered rate is re-measured under it (§12), and nothing measured under
the v4r2 template is carried forward as comparable.

**What it does not fix.** The stem removes the shortening escape; it does not
remove the length *gradient*. Within the 60–120 band a 62-word answer still
satisfies a count budget more readily than a 118-word one. The rate families of
§7.3 address the gradient; the two changes are complements and neither is
sufficient alone.

Within a block, two composed prompts sharing a constituent differ byte for byte
only in the line stating the other constituent. Both constraints occupy the same
authority level in the same numbered list in the same user message. No
constraint is placed in a system message.

### 8.6 The reduced designs, and which one a replication runs

Three variants, decided by deterministic rule before any confirmatory
generation and recorded in the freeze.

**Full, 47 cells.** §13.4 admits three core references from three feature
groups, each supplying a straddling triple, and §12.6's coverage criterion
passed.

**No-spectrum, 29 cells.** §13.4 admits three core references but §12.6's
coverage criterion failed, so `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` is recorded
at design time. The six spectrum solo cells and their twelve composed cells are
not generated; the core matrix, the class arm and the unconstrained cell are
unchanged. $\Delta_R$, $\Delta_j$, $\Lambda$, $\Xi$, the reciprocal
reference effects and $\Delta_{\text{class}}$ are all still identified and are
all still primary; only $\delta_{\text{diff}}$ is withheld, with L3d and L3e
withheld under §13.8. **Dropping the core matrix as well would discard
identified estimands because an unidentified one is unavailable**, and this
document declines to do that.

**Reduced, 8 cells.** §13.4 admits fewer than three core reference families at
all. That replication runs: 1 unconstrained cell, 2 solo cells
($A$, $B$), 2 composed cells ($A+B$ in each order) and, when §13.7 admits one, 1
class solo and 2 class composed cells. It estimates $D(B \leftarrow A)$,
$D(A \leftarrow B)$, $\Lambda$ and $\Delta_{\text{class}}$, records
`EXCESS_NOT_IDENTIFIED` for L3a–L3c and `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` for
L3d–L3e, and is analysed under the same rules. This branch is decided by the
deterministic Gate 3 rule before any confirmatory generation and is recorded in
the freeze.

**None of the three is a fallback to be avoided.** No caliper is widened, no
vacuity threshold lowered, no eligibility band loosened and no ladder extended
in order to reach a larger design. §13.9 makes that executable, and §12.6's
expansion is the only permitted way to add rungs — from a reserve this document
fixes in advance.

---

## 9. Primitive observation

### 9.1 The compliance vector

For every generation the record carries $X_c$ and $G_c$ for **every registered
constraint instance the design uses in that replication**, together with, for
each, whether it was *present* in that prompt, its severity, wording index and
position. A verdict on an absent constraint is a chance observation (§25) and is
marked `present = false`; no estimand reads a chance observation as a treated
one, and an executable check refuses any primary formula that mixes them.
Nothing is marginalised at record time.

### 9.2 The exact-count rule and its alternatives

$A$'s verifier, written $S_0$, is fixed here and applies unchanged in every
cell: take the whole response, lower-case it, find every maximal run of
alphabetic characters, count the runs equal to `however`, and pass when the
count equals $n$. Its word-segmentation and counting function sources are
byte-identical to the v3 instruments under the carry-over rule of §10.2.

Three alternatives are declared for the robustness family and never redefine
$X_A$: $S_1$ omits the lower-casing step; $S_2$ counts non-overlapping substring
occurrences in the lower-cased text; $S_3$ applies $S_0$ after deleting a
leading colon-terminated line and any line repeating an active constraint
wording.

### 9.3 Degeneracy, vacuity, and non-behavioural states

Every generation additionally carries: emptiness, word count, token count,
finish reason, truncation at the completion cap, verifier-processing failure,
whether the answer fell inside the stem's 60–120 word band, and the chance
verdict of every absent constraint.

A **non-vacuity predicate** is registered per constraint form:

| Constraint form | Non-vacuity predicate |
|---|---|
| $A$ (exact count) | Response is non-empty and not truncated |
| $B$ (word-length budget) | Response is non-empty, not truncated, and contains at least 20 words |
| Count budget, rate budget | Response is non-empty, not truncated, and contains at least 20 words |
| Lower bound | Response is non-empty and not truncated |

A pass by a response failing its predicate is a **vacuous pass**. Vacuous passes
are counted as passes in the primary estimand, because response shortening under
composition is a candidate mechanism rather than a nuisance, and removing them
would condition on a consequence of the treatment. They are handled instead by:

1. the vacuity rate reported per cell and per constraint;
2. family F6 of §15, the vacuity-rate differences between each composed cell
   containing $B$ and the $B$ solo cell;
3. the registered partial-identification recomputation of §17.4, in which every
   primary estimand is recomputed with all vacuous passes forced to failures.

The 20-word threshold is registered on the reasoning of §8.5, is now stated to
the model by the stem, and is fixed here and not tuned after any data are seen.
A lower-bound constraint carries no word-count clause in its predicate because
its own rule already forces length upward, so a 20-word clause would be
redundant rather than protective.

---

## 10. Measurement: verifiers, freeze, and validation

### 10.1 Architecture invariants

1. Every behavioural score is a deterministic function of the response text and
   fixed configuration.
2. Verdicts are computed at generation time and stored with the verifier source
   hash.
3. No language model produces a behavioural score. The autorater of §10.4 is a
   validation-only proxy, its judgments live in separate artifacts, and no
   execution path lets an autorater judgment reach a stored verdict.
4. Alternative scoring rules never silently redefine a primary outcome.
5. A pass on a budget constraint is never described as engagement without the
   §9.3 predicate.
6. The difficulty coordinate is computed from stored verdicts only, by one named
   function, and never from a model judgment.

### 10.2 Verifier correctness

Every verifier that can enter the final instrument population — $A$'s
exact-count rule at every $n$, $B$'s word-length rule at every severity of the
registered grid **and of the conditional extension**, and every one of the
twenty family verifiers at every severity of its **declared range**, reserve
included — must pass all of:

The population is the declared range and not the round-0 ladder, because
§12.6's expansion may admit any reserve rung and a rung that could enter
without evidence is exactly the failure this section exists to prevent. 348
constraint instances in 22 verifiers.

- **Determinism.** Three executions on three separate processes over every
  calibration response, agreement exactly 1.000.
- **Boundary suite.** A frozen boundary suite per verifier, of at least forty
  cases, covering empty response, adjacent punctuation, capitalisation,
  hyphenation, concatenated copies, repeated words, non-Latin characters,
  Unicode punctuation and lookalikes, zero-width characters, and truncation
  mid-word. Rate verifiers additionally cover rates straddling each $q$, a
  single-word answer, and a wordless answer. Lower-bound verifiers additionally
  cover counts at $q-1$, $q$ and $q+1$. Case texts and expected verdicts are
  frozen before qualification. The $A$-side suite consists of the v3 forty case
  texts and their expectations carried byte-identically under the carry-over
  rule, **plus** the additional cases the §24 enumeration requires. The $B$-side
  and family suites are authored for v4 in full.
- **Independent reimplementation.** A second implementation written from the
  registered prose of §7 and §9 by a process that does not read the primary
  source, run over every calibration response and the whole boundary suite,
  agreement exactly 1.000. **The reimplementation is an instrument under test
  in its own right**: it segments text by an independent mechanism and a
  differential check over the whole Unicode range asserts that the two
  segmenters admit exactly the same character class. This is registered because
  a prose-only reimplementation that segmented on a regular-expression word
  class was found to admit 1,151 non-decimal numeric characters that §7.3's
  *alphabetic* excludes, and disagreed with the primary on a genuine response.
- **Adversarial corpus.** A targeted corpus exercising every enumerated boundary
  case, with the realised frequency of each case in genuine generations reported
  (§24).
- **Carry-over.** $A$'s instrument may supply carried evidence only when the
  construct string, the segmentation function source, the counting function
  source, and the forty case texts with their expectations are byte-identical to
  the v3 artifacts. The carry-over record names the source, records every hash,
  and refuses on any mismatch.

- **Composition equivalence.** The nine counted statistics under the corrected
  lexical rule of §7.0 return, on every response free of U+0130, exactly what
  the v4r2 functions return. This is executable
  (`statistics.assert_agrees_with_v4r2`) and is what makes the scope claim in
  §7.0 a measurement rather than an assurance.

**Gate 1 does not pass until every instrument in the final population carries
the full set.** The population is fixed by §7.0, §7.3 and §7.4 and not by Gate
3's outcome: the library is registered, so the evidence is required under every
admission result, and Gate 1 therefore does not wait on Gate 3.

**Gate 1 runs after §12.6 closes the vocabulary, and that ordering is
deliberate.** The candidate expansion happens inside the regime screen, on
development topics, using verifiers that Gate 1 has not yet certified — which
is v4r2's ordering too, since the dense ladder screen has always preceded Gate
1. What the expansion decides is a *vocabulary*, and Gate 1 then certifies
every member of it. A family or severity that fails §10.2 is removed from the
frozen vocabulary and §12.6's coverage criterion is re-evaluated on the table
already measured; no new outcome information enters, because no composed cell
exists at that point in the sequence.

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

Statuses: a measured excess returns `MEASUREMENT_NOT_ESTABLISHED`; an exhausted
natural class returns `MEASUREMENT_EVIDENCE_INSUFFICIENT`; no independent
annotator returns `HUMAN_VALIDATION_UNAVAILABLE` and routes to §10.4 without
waiving the criterion.

**Author-performed labels are never described as independent validation.** The
v3 record contains 120 author-performed blinded labels; they are diagnostic
evidence there and are not carried as independent validation here.

### 10.4 Autorater-assisted validation

When human validation is unavailable, verifier development and held-out
evaluation proceed against one configured autorater under a registered workflow:
a deterministic class-stratified disjoint development and calibration split of
the response pool; one judge model resolved through a registry disjoint from the
registered study models, at a pinned revision, with a hashed configuration
recording judge identity, revision, backend, prompt version and hash, parser
version, label mapping, decoding, and output cap — **including every
generation-time keyword that changes the judging condition**, because a judging
keyword outside the configuration hash was found to be silently droppable;
**serialised deterministic execution** at concurrency one, or an equivalently
demonstrated fixed-composition offline path; a development-phase repeatability
check; a single-shot signed freeze binding verifier hashes, the regression-test
file and its passing run, the split derivation, the realised evidence boundary,
and the judge configuration; a one-shot calibration on the untouched held-out
half enforced by an append-only ledger; and explicit researcher approval writing
`measurement_basis = autorater_calibration_approved`.

Selection of the judging condition uses the hierarchy: valid deterministic
execution, then adequate output cap and absence of problematic truncation, then
valid parsing and coverage, then agreement with human labels, then the
lower-cost setting when performance is practically indistinguishable.
Configurations are compared as **paired** on the same items.

A reserved final-check set is sealed at Gate 1, its hash recorded, and opened at
most once after every autorater choice is frozen. It is never used for tuning
and is never rerun to obtain a better result.

### 10.5 Measurement scope, recorded verbatim

Three questions are kept separate and never aggregated.

1. *Does each program implement its registered rule?* Answered by §10.2.
2. *Can an independent human reproduce it?* Answered by §10.3, or recorded
   unavailable.
3. *Does the deterministic rule validly operationalise the intended
   instruction-compliance construct?* Bounded by §9.3 and §24 and not resolved
   by this study.

Every analysis record carries the measurement basis and, while the basis is not
`human_validated`, the registered scope sentence: *the outcomes are
verifier-defined and support no claim about compliance as an independent human
would judge it.*

### 10.6 Verifier freeze and downstream binding

The canonical verifier hash covers every source and configuration component that
can change verifier semantics for any registered instrument: the word
segmenter, the target counter, the family statistics, the constraint grids and
ladders, the class labelling, and the compliance and graded mappings. It is
frozen in the Gate 1 record. Every downstream entry point re-verifies the
current hash against the frozen hash before any work and fails closed on
mismatch: ladder screen, solo calibration, reference admission, **spectrum
selection**, **class admission**, composed-headroom validation, freeze,
confirmatory generation, scoring, resume and restart paths, analysis, unmasking,
and report generation. The frozen hash is never silently updated; a semantic
change requires explicit invalidation and recalibration. Historical rows remain
auditable under their own recorded hash and are never treated as newly valid.

---

## 11. Estimands

### 11.1 Observation and configuration

For cell $c$ with $M$ draws the observation is the cell mean
$\bar X_c = \frac{1}{M}\sum_{j} X_{c,j}$.

**A configuration is (model, position of the outcome constraint)**, taking
values `outcome_first` and `outcome_second`. This is the reading §11.4 requires:
a $\Delta$-type quantity differences two composed cells and is position-clean
only when the configuration fixes the *outcome's* position. Under a slot-order
reading, $\Delta_R$ would difference $D(B \leftarrow A)$ with $B$ second against
$D(B \leftarrow R_j)$ with $B$ first and would not be position-clean. Every
estimand below is defined within one configuration and is estimated on all 384
blocks, because order is a within-block factor. A solo cell states its
constraint in position one and serves both configurations. There are two
configurations per model and eight in total.

Quantities are additionally reported **pooled within block**, meaning the two
order variants of each cell averaged inside the block before the contrast is
formed. Pooling within block is not pooling across configurations: it is a
single within-block estimand and it carries no claim except through L4.

### 11.2 Delivery loss and chance compliance

For an outcome constraint $c$ and companion $g$,

$$D(c \leftarrow g) \;=\; \mathbb{E}\!\left[\bar X_{c,\text{solo}}\right] - \mathbb{E}\!\left[\bar X_{c,\;c+g}\right],$$

with both terms taken over the same 384 blocks, so the contrast is paired within
block.

$$\kappa_c = \mathbb{E}\!\left[\bar X_{c,\;\text{unconstrained}}\right], \qquad
\iota_c = \frac{\mathbb{E}\!\left[\bar X_{c,\text{solo}}\right] - \kappa_c}{1 - \kappa_c}.$$

$\iota_c$ is undefined when $\kappa_c = 1$; a constraint with $\kappa_c \ge 0.99$
in the confirmatory data is reported with its difficulty coordinate withheld and
`DIFFICULTY_COORDINATE_DEGENERATE`, and its spectrum point is dropped from the
fit with the drop recorded. This cannot happen for an admitted companion without
contradicting §13.5's eligibility band, and the rule exists so that the
contradiction is reported rather than divided by zero.

### 11.3 Primary estimands

Per configuration, six:

$$D(B \leftarrow A), \qquad D(A \leftarrow B), \qquad \Lambda = D(B \leftarrow A) - D(A \leftarrow B),$$
$$\Delta_R = D(B \leftarrow A) - \tfrac{1}{3}\sum_{j=1}^{3} D(B \leftarrow R_j), \qquad \delta_{\text{diff}} \;(\S11.7), \qquad \Xi \;(\S11.6).$$

Note the algebra that makes $\Delta_R$ well behaved:
$\Delta_R = \frac{1}{3}\sum_j \mathbb{E}[\bar X_{B,\,B+R_j}] - \mathbb{E}[\bar X_{B,\,A+B}]$.
The solo baseline cancels, so $\Delta_R$ is unaffected by solo ceiling, solo
noise, or any property of the solo cell. §11.7 shows $\delta_{\text{diff}}$ has
the same property.

### 11.4 The position caveat, registered

A solo cell states its single constraint in position one. $D(c \leftarrow g)$ is
therefore position-matched to its baseline only in the configuration where $c$
is stated first; in the other configuration it confounds added load with a
change of position. $\Delta$-type quantities difference two composed cells with
$c$ in the same position and are position-clean in both configurations.

Consequences, fixed here: every emitted L1 statement names the position of the
outcome constraint; the L1 claim in the position-shifted configuration is stated
as "composition and position change together"; and $\Delta_R$ and
$\delta_{\text{diff}}$, which are position-clean, are the quantities that carry
the companion-identity claim.

### 11.5 Secondary estimands

Per configuration, all with simultaneous intervals within their family (§15):

- **Companion heterogeneity.** $D(B \leftarrow R_j)$ and
  $\Delta_j = D(B \leftarrow A) - D(B \leftarrow R_j)$ for each core $j$.
- **Outcome-side control.** $D(A \leftarrow R_j)$ for each $j$, and the $A$-side
  companion swap
  $\Delta^A = D(A \leftarrow B) - \frac{1}{3}\sum_j D(A \leftarrow R_j)$,
  retained as a **demoted diagnostic** subject to three gates: outcome headroom,
  a companion matched on measured instructed compliance, and the configuration
  quoted with the number.
- **Reciprocal losses.** $D(R_j \leftarrow B)$ and $D(R_j \leftarrow A)$.
- **Spectrum losses.** $D(B \leftarrow R_{f,s})$ for each of the six spectrum
  companions, and each companion's realised $\iota$.
- **Class arm.** $\Delta_{\text{class}} = D(B \leftarrow A) - D(B \leftarrow CL)$,
  $D(B \leftarrow CL)$, $\iota_{CL}$ and the realised $|\iota_{CL} - \iota_A|$.
- **Joint-state redistribution.** For each composed cell the four-state vector
  $p = [P(0,0), P(0,1), P(1,0), P(1,1)]$, and its change across configurations
  that do not alter which constraints are present. Reported within cell, never
  differenced across cells with different constituents.
- **Joint success.** $P(X_{c_1} = 1, X_{c_2} = 1)$ per composed cell.
- **Chance and lift.** $\kappa_c$, the instruction lift, and $\iota_c$ for every
  registered constraint instance.

### 11.6 The reciprocal specificity estimand

Writing $D(\bar R \leftarrow g) = \frac{1}{3}\sum_j D(R_j \leftarrow g)$ for a
companion $g$ outside the core reference set, and
$D(\bar R \leftarrow \bar R') = \frac{1}{6}\sum_{j \ne k} D(R_j \leftarrow R_k)$
over the six ordered pairs of distinct core references:

$$\Xi = \Delta_R - \left[D(\bar R \leftarrow A) - D(\bar R \leftarrow \bar R')\right].$$

$\Xi$ asks whether the excess damage from $A$ is specific to the outcome $B$ or
is a property of $A$ as a companion to anything. In v4r2 it was a secondary. In
v4r3 it **gates the wording of every L3 statement** (§3.2), so it is a member of
the primary family F1 and carries the multiplicity cost of being one.

### 11.7 The difficulty-response relation and $\delta_{\text{diff}}$

**The points.** Nine non-$A$ companions enter: the three core references and the
six spectrum companions, three families $f$ with three severities each. For
companion $R_{f,s}$ write

$$d_{f,s} = \iota_{R_{f,s}}, \qquad Y_{f,s} = D(B \leftarrow R_{f,s}),$$

both measured on the confirmatory blocks in the configuration being estimated.
$A$ and the class companion $CL$ contribute **no point**.

**The primary functional form**, fixed here and unchangeable after freeze:

$$Y_{f,s} = \alpha_f + \beta\, d_{f,s} + \varepsilon_{f,s},$$

three family intercepts and one common slope, fitted by ordinary least squares
on the nine points with every point weighted equally. Family-aware intercepts
are registered rather than a single intercept because family is the one
companion property the design deliberately varies at fixed difficulty, and
v4r2's own §13.4 records that $D(B \leftarrow R_j)$ varied by 0.177 and 0.188 at
essentially constant companion compliance. A single intercept would push that
variation into the residual and into $\delta_{\text{diff}}$.

**The prediction at $A$.** $A$ belongs to no family, so the prediction uses the
average intercept:

$$\hat Y_A = \bar\alpha + \beta\, d_A, \qquad \bar\alpha = \tfrac{1}{3}\sum_f \alpha_f,$$

which with three equal-sized families is $\hat Y_A = \bar Y + \hat\beta\,(d_A - \bar d)$
over the nine points.

$$\boxed{\;\delta_{\text{diff}} = D(B \leftarrow A) - \hat Y_A\;}$$

**Two properties that are registered consequences, not conveniences.** First,
$A$ is excluded from the fit that predicts $A$; §13.9 makes that executable and
§29 records why it matters. Second, the prediction weights sum to one, so

$$\delta_{\text{diff}} = \sum_{f,s} w_{f,s}\, \mathbb{E}\!\left[\bar X_{B,\,B+R_{f,s}}\right] - \mathbb{E}\!\left[\bar X_{B,\,A+B}\right],$$

the $B$-solo baseline cancels exactly as it does in $\Delta_R$, and
$\delta_{\text{diff}}$ is a contrast among composed cells alone. An executable
check computes both forms and refuses a disagreement above $10^{-9}$.

**Why not a richer model.** With nine points and four parameters the fit has
five residual degrees of freedom. A per-family slope would leave three, and a
non-linear form would be fitted to three points per family. The registered form
is the richest one the design's own support can carry, and §33 D4 records the
alternative that a larger spectrum would license.

**Relation to $\Delta_R$.** When $\hat\beta = 0$ and the three families are
equal-sized, $\delta_{\text{diff}}$ reduces to $D(B \leftarrow A)$ minus the
unweighted mean of nine companion losses — a nine-companion $\Delta_R$. That is
not a defect: it is the correct behaviour when difficulty does not predict the
loss, and it is why $\delta_{\text{diff}}$ is worth having even if the relation
turns out flat. It also means the two estimands are correlated, which is
precisely why §17.6 registers what their disagreement means and why they sit in
one simultaneous family.

### 11.8 Thresholds and regions

| Quantity | Threshold | Provenance |
|---|---|---|
| $\Delta_R$ generic-load threshold | 0.10 | `dci-construct-pass2.md` §G row 1, 14 August 2026, verbatim |
| $\Delta_R$ pair-specific threshold | 0.25 | Same |
| $\delta_{\text{diff}}$ direction | 0 | No magnitude threshold is transferred; see below |
| $\delta_{\text{diff}}$ equivalence region | $\pm 0.10$ | The registered smallest effect of interest, on its own stated rationale |
| Smallest effect of interest for $D$, $\Lambda$, $\delta_{\text{diff}}$ | 0.10 | Carried from v3 §11: a change of 0.10 moves a system prompt from 80% to 70% compliance |
| Equivalence region for $D$ and $\Lambda$ | $\pm 0.10$ | Same |
| $\Xi$ | direction only | §11.6; no magnitude threshold is registered and none is invented |
| Precision preconditions (§17.3) | half-width $\le 0.05$ for $D$, $\Delta_R$ and $\delta_{\text{diff}}$; $\le 0.08$ for $\Lambda$; $\le 0.06$ for $\Delta_j$ | §16.2 |
| Reference instructed-compliance caliper (§13.4) | 0.10 on the point difference, with the 95% Newcombe interval intersecting $\pm 0.05$ | §13.4 |
| Realised companion-difficulty qualifier | 0.15 on the confirmatory-measured instructed-compliance gap | §13.4 |
| Spectrum eligibility band for $\iota$ | $[0.10, 0.95]$ | §13.5 |
| Registered spectrum offset | $\pm 0.20$ on $\iota$ | §13.6 |

**Why $\delta_{\text{diff}}$ gets a direction rule and the SESOI, and not
0.25.** The two $\Delta_R$ thresholds are quoted from a document that defined
them for one specific quantity — the difference between a focal loss under $A$
and the same loss under a matched reference — and their provenance is the
protection they carry. $\delta_{\text{diff}}$ is a different quantity: it
differences an observed loss against a *fitted prediction*, and nothing in that
document contemplated it. Transferring 0.25 would be inventing a threshold and
dressing it in someone else's provenance. What does transfer is the smallest
effect of interest, 0.10, because its stated rationale is about the compliance
scale itself — *a change of 0.10 moves a system prompt from 80% to 70%
compliance* — and $\delta_{\text{diff}}$ is a difference of two compliance
probabilities on that scale. So $\delta_{\text{diff}}$ licenses a direction
claim (L3d) and an equivalence claim (L3e) and licenses no pair-specific claim
at any magnitude. §33 D5 records the alternative, that a $\delta_{\text{diff}}$
threshold be registered on its own prospective argument, as a researcher
decision this document does not take.

No threshold is derived from any screen. The two $\Delta_R$ thresholds predate
every observation in this constraint vocabulary.

---

## 12. Operating regime and severity selection

The design dependency order is followed: the construct and estimands are fixed
above; the operating regime is found next; references, the spectrum and the
class companion are selected only afterwards.

### 12.1 Completion cap

A fixed subject-balanced set of 96 pre-screen prompts is generated at **each**
cap in $\{512, 768, 1024\}$ — every cap, not only those up to the first that
qualifies, because the whole table is the registered diagnostic. The set is
four prompts per pre-screen topic under the §8.5 template: the unconstrained
cell; $A$ alone at $n = 8$; $B$ alone at $m = 7$; and $A + B$ at those
severities. The one- and two-constraint prompts use the **most restrictive**
registered severity of each grid, because a cap has to be adequate where the
answer is hardest to write, not where it is easiest.

The smallest cap whose truncation rate over the one- and two-constraint prompts
is at most 0.10 is selected and held fixed for the replication. If none
qualifies the replication terminates `RESPONSE_LENGTH_INCOMPATIBLE`. The
zero-constraint truncation rate is recorded, and any quantity derived from a
cell whose truncation rate exceeds 0.10 is reported as a bound. 288
generations.

### 12.2 Dense ladder screen

At the selected cap, the pre-screen measures on the 24 pre-screen topics, one
draw per cell: the unconstrained cell, the full $n$ grid for $A$, the full $m$
grid for $B$ **including the conditional extension**, and all 190 round-0
ladder severities of §7.3 and §7.4. This is
$(1 + 8 + 6 + 190) \times 24 = 4{,}920$ generations, plus whatever §12.6's
expansion adds — at most $2 \times 20 \times 4 \times 24 = 3{,}840$ more.

**The unconstrained rows carry a chance verdict for every severity of the
declared range**, all 348 instances, scored on the same responses by the same
verifiers without the instruction being present. That is where $\kappa$ comes
from (§25), and measuring it over the declared range rather than the round-0
ladder is what lets §12.6 admit a reserve rung whose $\kappa$ was estimated on
the same draws as every other rung's.

It produces three things, all written before any Gate 2 generation:

1. **the pre-screen difficulty table** — $\kappa$, solo compliance and $\iota$
   for every measured instance;
2. **the frozen candidate vocabulary**, by the rule of §12.6;
3. **the shortlist**, by the rule of §12.3.

The extension rungs $m = 11, 12$ are *measured* here on all models, because the
screen is one draw on 24 topics and costs 48 generations, and because §12.3's
escalation rule needs to know whether they exist before it can decide not to use
them. Measuring them here never makes them selectable: §12.3 decides that.

### 12.3 The shortlist, and what §12.3 measures

**Family ranking.** Reference families are ordered by: (i) whether the family
possesses a *complete straddling triple* at pre-screen — an eligible rung with
$\iota$ below $\iota_A$, an eligible rung with $\iota$ above it, and an eligible
rung nearest it — with families possessing one first; then (ii) ascending
$|\iota_{\text{near}} - \iota_A|$ at pre-screen; then (iii) family identifier.
Eligibility at pre-screen is the §13.5 band on $\iota$ alone.

**The shortlist** is the top **six** reference families and **all four** class
families. Per reference family it holds at most four severities: the rung
nearest $\iota_A$; the eligible rung with $\iota < \iota_A$ nearest
$\iota_A - 0.20$; the eligible rung with $\iota > \iota_A$ nearest
$\iota_A + 0.20$; and the second-nearest rung to $\iota_A$. Duplicates
collapse. For a class family the shortlist holds only the two rungs nearest
$\iota_A$. Ranking and shortlisting read the **measured vocabulary**, so a rung
§12.6 admitted in an expansion round is a candidate here; reading the round-0
ladder instead would generate an expansion rung and then ignore it.

Six reference families is registered as twice the three the design needs, so
that a family failing at calibration what it passed at pre-screen does not by
itself force the reduced design. An executable invariant refuses a shortlist
naming a rung with no pre-screen measurement, because §13.4 condition 2 reads
that measurement and would otherwise be unevaluable.

**Solo-compliance calibration.** On the 96 solo-calibration topics at
$M_{\text{cal}} = 4$: the unconstrained cell, the full $n$ grid, the registered
$m$ grid, and every shortlisted severity — at most four rungs for each of six
reference families and two for each of four class families. This is at most
$(1 + 8 + 4 + 6\times4 + 4\times2) \times 96 \times 4 = 45 \times 384 = 17{,}280$
generations, plus $2 \times 384 = 768$ more if the focal extension is
triggered.

**Selection of $n^*$.** Eligible values put solo compliance of $A$ in
$[0.50, 0.85]$. Among them $n^*$ minimises the distance from 0.70, with the
smaller $n$ breaking an exact tie.

**Selection of $m^*$.** Eligible values put solo compliance of $B$ in
$[0.60, 0.95]$. Among them $m^*$ minimises the distance from 0.80, with the
**smaller** $m$ — the more restrictive severity — breaking an exact tie. If no
severity of the registered grid is eligible, the extension of §7.2 is measured
on the same 96 topics and selection runs over the union $\{7,\dots,12\}$ by the
same rule; if none of the six is eligible the replication records
`FOCAL_RANGE_EXHAUSTED`.

$n^*$ and $m^*$ are selected on raw solo compliance, not on $\iota$, because the
bands exist to give an outcome constraint room to fall under composition, which
is a statement about its realised compliance and not about its lift. $\iota_A$
and $\iota_B$ are recorded at the selected severities and enter §13.

No eligible value returns `TARGET_RANGE_EXHAUSTED` or `FOCAL_RANGE_EXHAUSTED`,
or `GRID_RESOLUTION_INSUFFICIENT` when two adjacent registered severities lie on
opposite sides of a whole band. Every diagnosis records the complete curve and
makes a claim only about the registered grid.

### 12.4 Regime adequacy

A replication proceeds only when, on the calibration topics:

1. solo compliance of $A$ and of $B$ lie inside their bands;
2. the realised solo vacuity rate for $B$ is at most 0.10;
3. the graded distribution of each outcome constraint is non-degenerate,
   meaning **the share of responses whose graded score exceeds 0.99, and the
   share whose graded score falls below 0.01, are each at most 0.99**.

Otherwise the replication records `REGIME_NOT_FOUND`, which is a statement about
the registered grid and never about the model or the hypothesis.

**Condition 3 is stated as a share, and the reading is fixed here because v4r2
left it open and the two readings disagree.** v4r2 §12.4 said the graded
distribution must not be *"concentrated above 0.99 or below 0.01"* and its code
compared one float per constraint against 0.99 without saying which. Read as a
statement about the *mean* graded score, the clause fires on every severity
§12.3 declares eligible, because $B$'s graded score
$1 - (\text{words over } m)/(\text{total words})$ crosses 0.99 well inside the
focal band — so §12.3 would declare a rung eligible and §12.4 would declare the
same rung degenerate, on every model under every prompt. A clause that
contradicts its own neighbour is not a reading, it is a defect. Read as a
*share*, the clause says what "concentrated" means in ordinary use and behaves
as intended: on $A$ it fires exactly on the near-ceiling severities it was
written to catch. **The share reading is adopted because it is coherent and the
mean reading is not**, and this document records plainly that it is also the
reading under which the study can run, so that a reader can weigh that. §33 D3
puts the confirmation in the researcher's hands.

### 12.5 What development may inspect, and when the vocabulary freezes

**Development data** is the 24 pre-screen and 96 solo-calibration topics, and
nothing else. Iterative work — checking difficulty coverage, vacuity, chance
compliance, verifier behaviour, response lengths, structural validity — is
permitted on those topics and on those quantities.

**Prohibited during all of it**, and prohibited afterwards: inspecting
$D(B \leftarrow g)$, any other composed interference outcome, any joint state,
or any contrast between two composed cells, for the purpose of deciding which
families or severities are kept. The valid sequence is fixed:

> propose the candidate vocabulary → measure solo and chance properties →
> improve difficulty coverage → **freeze the family and ladder vocabulary and
> the selection rule** → only then observe composed outcomes.

**The family vocabulary of §7.3 and §7.4, the declared range of every ladder,
the expansion rule and coverage criterion of §12.6, and every selection rule of
§13, are frozen by this document** and enter the signed registration manifest
before the first qualification. They are study-wide under §6.1 and no
replication's outcome can change them. What §12.6 chooses per model is *which
reserve rungs are measured*; what Gate 3 chooses is *which measured rungs are
used*. Both rules read only solo and chance quantities.

The composed-validation 24, the confirmatory 384 and the sequestered 96 are
untouchable by development, and an executable audit over generated rows — not
over source — reports the topic set of every row any v4r3 process has produced.

### 12.6 Candidate expansion, and the coverage criterion that stops it

Three references can be found by luck. A difficulty-response relation cannot,
and a design that discovers at Gate 3 that its pool does not span $A$ has spent
its confirmatory budget to learn something a development screen could have told
it. §12.6 is the development screen, and it has a registered stopping rule.

**What may be inspected.** Solo compliance, chance compliance $\kappa$,
instructed compliance $\iota$, instruction lift, vacuity, graded distribution,
response length, measurement precision, verifier behaviour, satisfiability,
non-entailment, wording caliper, and constraint class and form — on the 24
pre-screen topics and the 96 solo-calibration topics, and nowhere else.

**What may never be inspected, during this loop or after it**:
$D(B \leftarrow g)$, $\Delta_j$, $\Delta_R$, $\delta_{\text{diff}}$, $\Xi$,
any joint state, any composed cell, or any contrast between two composed cells.
The executable form is §13.9's, extended to this loop: the candidate table's
schema carries no field a composed outcome could occupy, and its loader refuses
a mapping that offers one, before any value is read.

**The identification-coverage criterion**, evaluated on the §12.2 pre-screen
table with eligibility as §13.5's band on $\iota$ and §13.4 condition 6's
vacuity ceiling. Write $\iota_A$ for the pre-screen instructed compliance of
$A$ at the severity whose solo compliance is nearest §12.3's target aim.

| | Condition | Value, and where it comes from |
|---|---|---|
| C1 | an eligible reference rung strictly below $\iota_A$ and one strictly above | the minimum for interpolation rather than extrapolation |
| C2 | at least **3** eligible reference **feature groups** on each side of $\iota_A$ | §13.6 needs three groups each supplying a straddling triple |
| C3 | at least **6** eligible rungs within **0.15** of $\iota_A$, from at least **3** feature groups | 0.15 is §13.4 condition 2's pre-screen caliper; six is two per core slot |
| C4 | at least **4** feature groups contain a family that straddles $\iota_A$ with at least **3** eligible rungs spanning at least **0.40** in $\iota$ | three groups plus one spare, as §12.3's shortlist carries; 0.40 is two registered spectrum offsets |
| C5 | at least **12** eligible reference rungs in total | §13.6 delivers nine fit points; twelve is a floor with slack |
| C6 | at least **6** eligible reference families, from at least **4** feature groups | so §12.3's shortlist is not short before it starts |

**Wherever the criterion counts companions it counts feature groups, not
families.** Sixteen families over eight groups would otherwise let eight
families across four groups look like eight independent controls, and §13.4 can
use at most one family per group.
| C7 | at least one eligible **class** rung within **0.15** of $\iota_A$ | §13.7, and see below |

C1 to C6 are decisive. **C7 is not**: an unmatched class companion attaches
`COMPANION_CLASS_NOT_MATCHED` to every L3 statement and the study proceeds, as
§7.3 already requires it to.

**The expansion rule.** While C1–C6 are not all met and rounds remain, one
round is run. Per family, in registered family order:

- if the family's measured rungs bracket $\iota_A$, admit the reserve rungs
  lying strictly between the two adjacent measured severities whose $\iota$
  values bracket it — bisecting where the family's curve crosses $A$;
- otherwise admit the reserve rungs immediately beyond the family's extreme
  measured severity on the deficient side — extending toward $A$;

at most **four** rungs per family per round, taken nearest the target first and
then by severity, and **at most two rounds**. Only the newly admitted rungs are
generated, on the same 24 topics at the same cap. The loop stops the moment
C1–C6 pass, so the number of rounds is a result and not a parameter, and the
maximum cost is $2 \times 20 \times 4 \times 24 = 3{,}840$ generations.

**The rule can only pick, never invent.** Everything it returns is already in
the frozen reserve of §7.0, which this document fixes; it reads $\iota$ and
severity and nothing else; and it is deterministic given the table. There is no
branch in which a family or a predicate is authored after data has been seen.

**When it stops without passing.** If two rounds complete and C1–C6 are still
not all met — or the reserve is exhausted first — the replication records
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` **at design time**, runs the reduced design
of §8.6 for the spectrum arm, and never reports a $\delta_{\text{diff}}$
obtained by extrapolation. This is a registered outcome and not a fallback to
be avoided: no band is widened, no vacuity ceiling lowered and no severity
authored in order to reach it.

**Then the vocabulary freezes.** The regime-screen record names every measured
rung. Every later stage selects from that named set, so a selection over a rung
the freeze does not name is a set difference rather than an argument, and Gate 1
certifies exactly the instruments the freeze contains.

---

## 13. Reference calibration, the difficulty spectrum, and the class arm

### 13.1 What a reference is for

Under the recovered question the reference occupies the **companion** slot in
place of $A$. It estimates the counterfactual "what would composing $B$ with a
comparable non-$A$ companion have cost?". It therefore has to resemble $A$, and
its resemblance to $B$ is irrelevant. This inverts the v3 rule, which matched
the reference to $B$ because $B$ occupied the swapped slot there.

### 13.2 Comparable in what

v4r2 answered: comparable in raw solo compliance. §2.3(b) is the evidence that
this answer does not survive its own measurement. Raw solo compliance mixes two
things that a production constraint and a prefix-closed budget constraint do not
share — how often the model would satisfy the constraint anyway, and how much
stating it changes what the model does. $A$'s chance rate is 0.000 by
construction: an exact count of a specific word is never satisfied by accident.
A count budget's chance rate is whatever the model's natural answer length makes
it, and it was measured at 0.52 to 0.89 on the matched rungs.

Matching on raw solo compliance therefore certifies nothing about comparability
where it matters most, and it does so *asymmetrically*: it systematically admits
companions that demand less than $A$, which inflates $\Delta_R$. §29 records the
direction.

### 13.3 The registered difficulty coordinate

**The difficulty coordinate is instructed compliance,**

$$\iota_c = \frac{P(X_c = 1 \mid c \text{ alone}) - \kappa_c}{1 - \kappa_c},$$

with $\kappa_c$ measured in the unconstrained cell of the same topic set at the
same $M$ under the same prompt. It is computed by one named function from stored
verdicts, on the calibration topics for every selection in §13, and on the
confirmatory blocks for every estimand in §11.

**Raw solo compliance is retained as a registered secondary coordinate.** Every
selection table records both; every fit of §11.7 is computed a second time on
the raw coordinate and reported; and §17.6 registers what a disagreement between
the two coordinates means. Raw solo compliance is not abandoned — it is demoted
from the quantity that decides comparability to a quantity reported beside the
one that does.

**This is the more demanding choice, and that is part of why it is registered.**
Netting out chance moves twelve of twelve matched companions in the matrix
screen out of the caliper. A coordinate that makes matching *harder* is not a
coordinate chosen to make a result appear.

**What is measured and reported for every candidate**, at pre-screen and at
calibration: solo compliance; chance compliance $\kappa$; instruction lift;
instructed compliance $\iota$; vacuity rate; median and quartile response
length; graded-score distribution; family and class; and verifier readiness.

### 13.4 Core reference admission

Within family $f$, severity $q_f^*$ minimises
$\left| \iota_{R_f} - \iota_A \right|$ at $n^*$ subject to all of:

1. that absolute difference is at most **0.10** on the 96 solo-calibration
   topics, and the 95% Newcombe interval for the paired difference of the
   underlying compliance rates intersects $\pm 0.05$;
2. the same absolute difference on $\iota$ is at most 0.15 on the disjoint 24
   pre-screen topics;
3. every frozen wording of the family at that severity is within 20% of the
   corresponding wording of $A$ in word count;
4. the constraint applies to the whole answer and parse independence holds for
   every registered verifier;
5. joint-satisfiability and non-entailment witnesses pass against $A$ at $n^*$,
   against $B$ at every admissible $m$, and against every other admitted
   reference at its admitted severity;
6. the family's solo vacuity rate at that severity is at most 0.10;
7. **the family is declared `budget` class** (§7.5).

The less restrictive severity breaks an exact within-family tie. At most one
severity per family enters the core set. The final three are the admitted
families with the smallest $|\iota_{R_f} - \iota_A|$, with family identifier
breaking an exact tie, and **the three come from three different feature
groups** (§7.0) — not merely from three different families.

Three different families is not enough. `RF7` and `CR7` are two families and
one measurement; admitting both would give §11.7's fit three intercepts over
two properties of an answer, and it would put in one cell a pair whose
non-entailment obligation §7.5 cannot discharge at all. When the next admitted
family belongs to a group already taken, it is skipped and the following one
takes the slot, exactly as a family that cannot straddle is skipped.

Condition 1's value is set by what the calibration sample supports rather than
by ambition: the paired standard error of an $A$-versus-$R$ solo difference over
96 topics at $M_{\text{cal}} = 4$ is about 0.038, so a caliper below about 0.10
would select mostly on noise. Condition 2 is a disjoint-sample confirmation
against winner's-curse selection; §12.3's shortlist invariant guarantees its
input exists.

**The realised gap is measured precisely in the confirmatory data and
reported.** The confirmatory design contains the solo cell and the unconstrained
cell of $A$ and of every admitted companion on all 384 blocks, so $\iota$ is
re-estimated there. When any realised $|\iota_{R_j} - \iota_A|$ exceeds **0.15**,
every L3 statement carries a fixed companion-difficulty block naming the
reference and its gap, and the §23 sensitivity reports $D(B \leftarrow R_j)$
against the realised gap.

### 13.5 Eligibility, common to references, spectrum and class

A severity is **eligible** when conditions 3 to 6 of §13.4 hold and its
instructed compliance lies inside the registered band

$$\iota \in [0.10,\; 0.95].$$

The floor is the registered smallest effect of interest: a constraint whose
stating changes compliance by less than 0.10 of the achievable range is not
distinguishable from an absent instruction, and it cannot serve as a companion
in a study about what companions cost. The ceiling is the upper end of the
§12.3 focal band: above it a constraint is at ceiling and carries no
information. Neither number is new to this document.

The band is what excludes the pathology §2.3(b) found: rungs whose chance
compliance equals or exceeds their solo compliance have $\iota \le 0$ and are
ineligible everywhere, so an anti-productive instruction can never enter the
core set, the spectrum, or the class arm.

### 13.6 Spectrum selection

For each of the three admitted core reference families $f$, two further
severities of the **same family** are admitted:

- $R_{f,-}$: among eligible severities of $f$ with $\iota$ **strictly below**
  $\iota_A$, the one nearest $\iota_A - 0.20$;
- $R_{f,+}$: among eligible severities of $f$ with $\iota$ **strictly above**
  $\iota_A$, the one nearest $\iota_A + 0.20$;

ties broken toward the less restrictive severity, then by severity value. The
core rung $R_{f,0} = R_j$ is the third point of the triple.

If either side is empty for an admitted family, that family **cannot supply a
triple**. Gate 3 then re-runs core selection excluding it, taking the next
admitted family in §13.4's order, and repeats until three families each supply a
complete triple or the admitted list is exhausted. Exhaustion sets
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED`; §13.8 says what follows.

**Strict straddling is the point of the rule.** Selecting "the two rungs nearest
$\iota_A \pm 0.20$" without the strictness condition permits both rungs on the
same side of $A$, which is what a difficulty-spanning arm run at screen scale
actually produced on two of four models — one point below $A$ and four above.
Requiring one strictly below and one strictly above in every family guarantees
three below and three above, which is what §13.8's support rule needs and what
keeps the fit centred on $A$, and a centred fit is also the one whose prediction
at $A$ carries least leverage (§16.1).

**Selection reads $\iota$ and vacuity on the calibration topics and nothing
else.** It does not read $D(B \leftarrow \cdot)$, any composed cell, any joint
state, or any quantity from any screen. It could have been executed before a
single composed cell existed anywhere in this programme, and §13.9 makes that
executable.

### 13.7 The class arm

One production-class companion is admitted, from CL7, CL8, CP4 and CP7
together: the eligible severity across all four families minimising
$|\iota_{CL} - \iota_A|$, ties broken by family identifier then by the less
restrictive severity, subject to conditions 3 to 6 of §13.4 and to witnesses
against $A$ and against $B$. When no severity of any of the four is eligible,
the arm is dropped, its three cells are not generated, and
`CLASS_ARM_NOT_AVAILABLE` is recorded.

**The admitted companion is *matched* only when $|\iota_{CL} - \iota_A| \le
0.15$**, §13.4 condition 2's caliper. When it is not, the arm still runs and
$\Delta_{\text{class}}$ is still reported, but `CLASS_ARM_NOT_MATCHED` is
recorded and every statement about class carries it. The distinction is
registered because the pairwise-matrix screen's production companion cost $B$
five to seven times what $A$ cost, so its $\Delta_{\text{class}}$ was a
difficulty gap wearing a class label. The rate lower bounds of §7.4 exist to
make the matched case reachable.

The class companion **never** enters the core reference set, the spectrum, the
difficulty fit, $\Delta_R$, $\bar R$, or $\Xi$. An executable check refuses a
plan or an analysis input that places it in any of them. It exists to make
$\Delta_{\text{class}} = D(B \leftarrow A) - D(B \leftarrow CL)$ computable, and
$\Delta_{\text{class}}$ is a registered secondary that bounds how much of any
excess could be a class effect rather than an identity effect.

**One companion cannot identify a class effect**, and §5 says so. Including it
in the difficulty fit would let the line absorb the very quantity the arm exists
to expose, which is why the exclusion is a rule and not a preference.

### 13.8 The difficulty-support rule

$\delta_{\text{diff}}$ is licensed only when, on the **confirmatory** data in
the configuration being estimated, all of:

1. $\iota_A$ lies inside $[\min_{f,s} d_{f,s},\; \max_{f,s} d_{f,s}]$;
2. at least **two** non-$A$ companions have $d_{f,s} < \iota_A$;
3. at least **two** have $d_{f,s} > \iota_A$;
4. at least **two** of the three families contribute a point on each side;
5. no point was dropped under §11.2's degeneracy rule.

Otherwise the configuration records `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, L3d and
L3e are withheld, and the fitted line, the support diagnostic and
$\delta_{\text{diff}}$'s point estimate are reported as **descriptive, outside
support, and not identified**. They are never reported as a null.

Conditions 2 to 4 are floors below §13.6's construction, which delivers three
per side spread over three families; they tolerate one family's rung moving
across $A$ between calibration and confirmation without voiding the estimand.
The support check is additionally reported as the share of bootstrap replicates
in which it holds, and a share below 0.95 attaches
`DIFFICULTY_SUPPORT_MARGINAL` to the statement.

**Extrapolation is never presented as identification.** A line fitted on
companions that all sit on one side of $A$ does not predict $A$; it extrapolates
to $A$, and the residual it produces is an artefact of the slope's
extrapolation. This rule exists because exactly that failure was found in a
screen's length channel, where $A$'s length shift lay outside every other
companion's range on all four models and the residual was nonetheless reported.

### 13.9 What is deliberately not a selection criterion, and how that is enforced

**Composed uptake is not a criterion.** Selecting a control on the outcome it is
meant to counterfactual is circular.

**Composed response length is not a criterion.** Composition shortens answers
and shorter answers satisfy budget constraints more readily, so response length
lies on the causal path from companion to outcome. It is a mediator (§22) and is
never conditioned on.

**No composed quantity of any kind is a criterion.** The executable form of this
rule, on the mandatory path:

- the selection functions of §13.4, §13.6 and §13.7 accept a calibration table
  whose schema contains solo, chance, vacuity, wording, witness and class
  fields **and no composed field**, and the loader refuses a table carrying one;
- the fit of §11.7 refuses an input containing $A$;
- the analysis refuses a spectrum set that is not a function of the frozen
  selection rule applied to the frozen calibration table;
- the freeze binds the selection rule, the calibration table hash and the
  resulting rungs, so a post-hoc change is a hash mismatch rather than an
  argument.

### 13.10 Composed-headroom validation

Every registered cell type is generated on the 24 composed-validation topics at
$M_{\text{cal}} = 4$ and its compliance rate is evaluated independently against
the band $[0.05, 0.95]$ for each of its constraints. This is at most
$47 \times 24 \times 4 = 4{,}512$ generations. The gate is a viability predicate
applied cell by cell. It does not rank, select, or reorder anything, and it
computes no contrast between cells. Any cell type outside the band returns
`COMPOSED_HEADROOM_FAILURE` with the full table.

**Gate 4 runs after the spectrum and the class companion are already fixed, and
its outcomes never revise them.** A headroom failure is a terminal status for
the replication, not an instruction to choose different rungs.

---

## 14. Unit of analysis, clustering, exclusions, and missingness

### 14.1 The block is the unit

| Role | Statement |
|---|---|
| Assignment | Both wording indices are assigned at the block and are identical across its cells; order is assigned within the block, so both order variants of every composed pair are present |
| Pairing | Every registered contrast is formed inside a block, removing between-topic variation |
| Clustering | The bootstrap resamples blocks; all of a drawn block's cell means travel with it, including the unconstrained cell and every spectrum cell |
| Generalisation | Uncertainty statements refer to the topic population of §6.2 |

Executable checks: each bootstrap replicate draws exactly 384 block identifiers
with replacement and asserts that each carries the registered cell count for the
design in force, 47 under §8.1, 44 when the class arm is dropped, and 3 to 6
under §8.6; no estimator function accepts a draw-level or response-level index;
every cell carries exactly $M$ committed accepted draws before any cell mean is
formed.

### 14.2 Exclusions, invalid generations, missingness, duplicates

- **No response is excluded from a primary estimand.** Empty responses,
  refusals, truncations and verifier-processing failures are scored by the
  registered rule and retained, because removing them would condition on events
  the treatment can cause.
- **Invalid generations**, meaning a backend failure that produced no text, are
  retried under the registered seed derivation. A cell that still lacks $M$
  committed draws after retries fails the run closed for that cell; the analysis
  refuses to form a cell mean from fewer than $M$ draws and no draw is imputed
  or substituted.
- **Missingness** is reported per cell type and per configuration, with the
  arm-differential missingness rate. A missingness rate above 0.01 in any cell
  type is reported beside every primary estimand.
- **Duplicates.** Every draw carries a seed derived from the root seed, stage
  label, model identity, prompt hash and draw index. Byte-identical replicate
  pairs within a cell are counted and reported; a duplicate rate above 0.05 in
  any cell fails qualification.
- **Deprecated and foreign sources may never enter registered evidence.** An
  executable guard refuses any analysis input whose manifest classification is
  not a registered v4r3 artifact. This includes, by name and by structural test:
  every v2, v3 and B+R pilot artifact; **every v4r2 artifact**; and every
  artifact of the four v4r2 design screens. The guard is a positive admission
  rule — an input must prove it belongs to the v4r3 study tree — and the v4r3
  study identifier is chosen so that it cannot satisfy v4r2's own admission
  prefix, so the exclusion holds in both directions.

---

## 15. Multiplicity families

Families are declared **per configuration**, meaning per (model, position of the
outcome constraint). Each configuration is a separate replication with its own
simultaneous statements. There is no cross-configuration and no cross-model
multiplicity family, because this protocol licenses no pooled estimand.

| Family | Members | Size | Status |
|---|---|---:|---|
| **F1 Primary** | $D(B \leftarrow A)$, $D(A \leftarrow B)$, $\Lambda$, $\Delta_R$, $\delta_{\text{diff}}$, $\Xi$ | **6** | Supports L1, L2, L3a–L3e, and gates the L3 wording |
| **F2 Companion heterogeneity** | $D(B \leftarrow R_j)$ and $\Delta_j$, $j = 1,2,3$ | 6 | Secondary; L3 heterogeneity qualifier |
| **F3 Outcome-side control** | $D(A \leftarrow R_j)$, $j = 1,2,3$, and $\Delta^A$ | 4 | Secondary; the demoted v3 estimand |
| **F4 Matrix completion** | $D(\bar R \leftarrow A)$, $D(\bar R \leftarrow B)$, $D(\bar R \leftarrow \bar R')$ | 3 | Secondary; the components of $\Xi$, which is itself in F1 |
| **F5 Robustness** | The six F1 members under the vacuity-forced recoding, and $D(B \leftarrow A)$, $\Delta_R$ and $\delta_{\text{diff}}$ under a graded-score threshold at 0.99 | 9 | Secondary; sensitivity of the primary |
| **F6 Degeneracy symmetry** | The vacuity-rate difference between each composed cell containing $B$ and the $B$ solo cell: $B{+}A$, $B{+}R_j$ for $j=1,2,3$, $B{+}R_{f,s}$ for the six spectrum companions, and $B{+}CL$ | 11 | Gate on the §17.4 interpretation |
| **F7 Reciprocal detail** | $D(R_j \leftarrow B)$ and $D(R_j \leftarrow A)$, $j = 1,2,3$ | 6 | Secondary |
| **F8 Spectrum detail** | $D(B \leftarrow R_{f,s})$ for the six spectrum companions, the fitted slope $\hat\beta$, and the three family intercepts | 10 | Secondary; the fit's own components |
| **F9 Class arm** | $D(B \leftarrow CL)$ and $\Delta_{\text{class}}$ | 2 | Secondary; the class bound |

**$\delta_{\text{diff}}$ and $\Xi$ are in the primary family because the claim
ladder reads them.** A quantity that licenses or gates a claim carries the
multiplicity cost of doing so. Putting either in a family of its own, or leaving
$\Xi$ in F4 while §3.2 gates on it, would buy a narrower interval by
misdeclaring what the analysis actually does. §16.2's allocation is sized for a
primary family of six and this is the largest single driver of the block count.

Each family receives its own simultaneous 95% interval, computed by
standardising each member by its bootstrap standard error and taking the largest
absolute standardised deviation across the family in each resample. Marginal
percentile intervals are reported alongside; decision rules read the
simultaneous intervals.

Reported with marginal intervals only and supporting no claim: joint-state
vectors and their redistribution, joint success, graded-score distributions,
response-length quantiles, finish-reason counts, chance-compliance and lift
tables, the stem satisfaction rate, compliance by subject area and by wording
index, the raw-coordinate replication of the fit, the greedy replication,
cross-configuration summaries, and every cross-model comparison.

---

## 16. Sample size and power

### 16.1 Variance model

Let $\phi$ be the share of a cell's compliance variance carried by
between-topic heterogeneity and $\rho$ the within-block correlation of the topic
component between two cells sharing an outcome constraint. With $p(1-p)$ the
cell compliance variance, $\sigma^2_{\text{topic}} = \phi\, p(1-p)$ and
$\sigma^2_{\text{draw}} = (1-\phi)\, p(1-p)$. For $T$ blocks and $M$ draws:

$$\mathrm{Var}[D] = \frac{2(1-\rho)\sigma^2_{\text{topic}} + \tfrac{2\sigma^2_{\text{draw}}}{M}}{T}, \qquad
\mathrm{Var}[\Lambda] = \frac{4(1-\rho)\sigma^2_{\text{topic}} + \tfrac{4\sigma^2_{\text{draw}}}{M}}{T}.$$

A **weighted composed contrast** — one composed cell against a weighted average
of others, with weights summing to one, which is the shape of both $\Delta_R$
and $\delta_{\text{diff}}$ once the solo baseline cancels — has

$$\mathrm{Var} = \frac{2(1-\rho)\sigma^2_{\text{topic}} + \sigma^2_{\text{draw}}\left(1 + \textstyle\sum w^2\right)/M}{T},$$

with $\sum w^2 = 1/3$ for $\Delta_R$'s three equal weights.

**$\delta_{\text{diff}}$'s weights and its extra term.** Writing the fit as
$\hat Y_A = \bar Y + \hat\beta(d_A - \bar d)$ over the nine points, the weight on
$Y_{f,s}$ is $1/9 + c_{f,s}(d_A - \bar d)$ where $c_{f,s}$ are the slope's own
coefficients. §13.6's strict-straddling rule puts $\bar d$ at $d_A$ up to the
realised offset error, so $\sum w^2$ is $1/9$ plus a leverage allowance
$(d_A - \bar d)^2 / S_{dd}$. Registered planning values: an off-centre allowance
of 0.05 and $S_{dd}$ from three families straddling by 0.20, giving
$\sum w^2 = 0.1215$.

The difficulty coordinate is itself estimated, and to first order
$\partial \delta_{\text{diff}} / \partial d_A = -\beta$ and
$\partial \delta_{\text{diff}} / \partial \bar d = +\beta$, so

$$\mathrm{Var}[\delta_{\text{diff}}] \;\approx\; (1 + \beta^2)\; \mathrm{Var}[\delta_{\text{diff}} \mid d \text{ known}].$$

The cross-covariance between the difficulty error and the loss error is order
$1/T$, can take either sign, and no planning claim rests on it.

**Registered planning constants:** $p(1-p) = 0.215$, $\phi = 0.27$,
$\phi = 0.37$ as the alternate, $\rho = 0.5$, and $\beta = 0.5$ as the planning
slope. Carried unchanged from v4r2 §16.1 except for $\beta$, which is new. The
formulas above reproduce v4r2's published §16.2 row exactly at 384 blocks,
$M = 4$, $\phi = 0.27$ and the Šidák value for a family of four, and an
executable check asserts that reproduction: if the variance model has drifted,
the v4r3 numbers are not comparable to the registered ones and the discrepancy
is the finding.

**Where $\phi$ and $\beta$ come from, and what they do not pin down.** $\phi$ is
fitted to the B+R pilot's reported interval widths — exploratory variance
information carrying no effect information — under two assumptions about the
among-reference correlation, giving 0.27 and 0.37. $\rho$ itself is assumed
rather than estimated and check C12 requires it to be estimated before freeze.
$\beta = 0.5$ is a conservative planning value: the largest slope magnitude any
non-confirmatory screen produced, on five points at screen scale with no
interval attached, is 0.100, and 0.5 is five times it. **$\beta$ enters the
projection and nothing else.** §16.5 records that no effect estimate enters the
sample-size calculation and that the preconditions are absolute; the planning
slope is a variance input in exactly the sense $\phi$ is, and an unfavourable
realisation appears as `INSUFFICIENT_PRECISION` rather than as a silent
widening.

### 16.2 Registered allocation

**384 blocks at $M = 8$**, over a 47-cell block: **144,384 generations per
model**, 577,536 across the four registered replications.

| Member | precondition | $\phi = 0.27$ | $\phi = 0.37$ |
|---|---:|---:|---:|
| $D$ | 0.05 | 0.0421 | 0.0452 |
| $\Delta_R$ | 0.05 | 0.0402 | 0.0429 |
| $\delta_{\text{diff}}$ | 0.05 | 0.0440 | 0.0471 |
| $\Lambda$ | 0.08 | 0.0595 | 0.0639 |
| $\Delta_j$ | 0.06 | 0.0421 | 0.0452 |

Every primary member meets its precondition under **both** fitted variance
settings, which is the standard v4r2 §16.2 set and which v4r3 keeps.

**Why $M$ and not blocks.** v4r2 registered 384 blocks at $M = 4$ over a
25-cell block. v4r3 changes three inputs: the block carries 47 cells; the
primary family F1 grows from four members to six, moving the Šidák planning
bound from $k = 2.4909$ to $k = 2.6310$; and $\delta_{\text{diff}}$ is a new
estimand with its own variance. At 384 blocks and $M = 4$ that combination puts
$D$, $\delta_{\text{diff}}$ and $\Delta_j$ at 0.0515 against a 0.05
precondition under $\phi = 0.37$ — a failure, not a margin.

The obvious repair is more blocks, and 408 would do it. **It is not available.**
§6.2's bank holds 384 accessible confirmatory topics and the remaining 96 are
sequestered as opaque hashes, so 408 blocks would have to be drawn from text no
v4-era process can read. With the block count fixed, $M$ is the only lever, and
under §16.1's model it is the effective one: at $\phi = 0.37$ and $\rho = 0.5$
the draw term is 0.0000704 against a topic term of 0.0000415 at $M = 4$, so the
part $M$ reduces is the larger part. Doubling $M$ costs generations and nothing
scientific: §8.2 averages all draws into the cell mean, no draw is selected, and
the topic split, the sequestered set and every registered rule are untouched.

**What it costs.** 577,536 generations against v4r2's 153,600 — a factor of
3.76, of which 1.88 is the cell plan and 2.0 is $M$. The sensitivity run of
§8.3 is unchanged at 96 blocks and one greedy draw, 4,512 generations per model.

### 16.3 Why this allocation, and the alternatives considered

The requirement is absolute rather than effect-dependent: every primary member
with a registered precondition must reach it, and the preconditions for $D$,
$\Delta_R$ and $\delta_{\text{diff}}$ are half the smallest effect of interest.
No expected effect enters the calculation.

Candidate block counts are whole numbers of confirmatory topics per subject
area, because §6.2 cuts the bank stratum by stratum and the bank is fixed at
624. **Only the 384-block rows are executable**: every larger count requires
confirmatory topics drawn from the sequestered 96, whose text this repository
holds only as content hashes. The larger rows are kept in the menu because a
future enlargement of the bank would make them reachable, and §33 D1 is that
decision.

| Blocks | per area | sequestered | $M$ | gen/model | gen total | meets both $\phi$ | registrable |
|---:|---:|---:|---:|---:|---:|---|---|
| 384 | 32 | 96 | 4 | 72,192 | 288,768 | no ($D$ = 0.0515) | no |
| **384** | **32** | **96** | **8** | **144,384** | **577,536** | **yes** | **selected** |
| 408 | 34 | 72 | 4 | 76,704 | 306,816 | yes | not executable: bank |
| 432 | 36 | 48 | 4 | 81,216 | 324,864 | yes | not executable: bank |
| 456 | 38 | 24 | 4 | 85,728 | 342,912 | yes | not executable; sequestered below floor |

Among the executable rows, 384 blocks at $M = 8$ is the only one meeting every
precondition under both variance settings, and it keeps the sequestered set at
v4r2's 96. An earlier draft of this document selected the 408 row and reasoned
that blocks buy more precision than draws; that reasoning is sound and
irrelevant, because the blocks are not there to be bought.

The allocation is confirmed or increased at freeze by the registered rule: take
the smallest entry in this menu meeting every precondition under the pre-freeze
variance re-estimate of §16.1, and record the choice in the freeze before any
confirmatory generation.

### 16.4 What the allocation would and would not resolve

At a projected $\Delta_R$ half-width of 0.0429 and a $\delta_{\text{diff}}$
half-width of 0.0471, the design resolves the 0.10 generic-load threshold for
$\Delta_R$ whenever the quantity is at least about 0.143 or at most about 0.057,
and resolves the direction of $\delta_{\text{diff}}$ whenever it is at least
about 0.047 in magnitude. A configuration whose interval spans a threshold is
reported `INDETERMINATE` at that threshold, which is declared here rather than
discovered later.

**Two things the allocation cannot buy, at any block count.** The first is the
length channel: §29 records that companion identity and length shift are
collinear across every companion set this pool can produce, so no number of
blocks separates them. The second is class: one production-class companion
bounds the class effect and does not estimate it.

### 16.5 Excluded planning sources

No effect estimate enters the sample-size calculation. The preconditions are
absolute and are derived from the smallest effect of interest. The B+R pilot
contributes the variance constants; the matrix screen contributes the planning
slope's order of magnitude and nothing else. Calibration computes no companion
contrast at any point. The procedural pilot computes no contrast. The v3
registered effects contribute nothing.

---

## 17. Uncertainty, decision rules, and claim licensing

### 17.1 Uncertainty estimation

Nonparametric block bootstrap, 10,000 resamples, seeded from the registration
manifest, resampling the 384 blocks with replacement and carrying **every** cell
mean of each drawn block — the unconstrained cell, both solo cells of every
contrast, and every composed cell — so that quantities computed from different
cells of the same block stay coupled.

Simultaneous intervals per family by the studentised maximum-modulus
construction of §15, with the same index vector applied to every member of a
family in each resample. Marginal percentile intervals are reported alongside.

### 17.2 The bootstrap for the difficulty relation

**Every replicate refits.** In each resample, in order:

1. resample the 384 block identifiers with replacement;
2. recompute $\kappa_c$ from the resampled unconstrained cells and the solo
   compliance of every companion from the resampled solo cells, and from them
   recompute $d_{f,s}$ and $d_A$;
3. recompute $Y_{f,s}$ and $D(B \leftarrow A)$ from the resampled composed
   cells;
4. **refit** the §11.7 model on the nine non-$A$ points of that replicate;
5. predict at that replicate's $d_A$ using that replicate's fit;
6. form $\delta_{\text{diff}}$ for that replicate;
7. evaluate the §13.8 support conditions on that replicate and record whether
   they held.

Explicitly prohibited, each enforced by a test: fitting the curve once and
bootstrapping only the residual; including $A$ in the fit that predicts $A$;
selecting the model form from bootstrap outcomes; treating spectrum points that
share topic blocks as independent; resampling anything other than blocks.

The share of replicates in which the support conditions held is reported and
feeds §13.8's `DIFFICULTY_SUPPORT_MARGINAL` marker. A replicate in which
$\hat\beta$ is not finite — possible only if a resample collapses the difficulty
spread — contributes to a recorded degenerate-replicate count and, above 0.01 of
replicates, the estimand records `INSUFFICIENT_PRECISION`.

### 17.3 Equivalence and the precision precondition

An equivalence statement about $D$, $\Lambda$ or $\delta_{\text{diff}}$ requires
the simultaneous interval to lie wholly inside $\pm 0.10$ **and** its half-width
to be at or below the precondition of §16.2. A member whose realised half-width
exceeds its precondition records `INSUFFICIENT_PRECISION`, withholds every
equivalence and threshold statement, and still reports a resolved direction if
one exists. Any string asserting absence, equivalence or negligibility is
produced by a single guarded function whose precondition is exactly this rule,
and the analysis aborts if that function is reached with the precondition false.

### 17.4 Vacuity and partial identification

Family F6 gates the interpretation. When every vacuity-rate difference is at or
below 0.05 or its interval includes zero, the primary estimands are reported
without qualification. Otherwise they are reported with a fixed block stating
that composition changed how often the outcome constraint could bind, and the F5
vacuity-forced recomputation is reported beside them as partial-identification
bounds. A claim is licensed only when the primary and the vacuity-forced
recomputation license the same claim; otherwise the axis is reported unresolved
with both bounds.

**The vacuity-forced recomputation is the registered operation and a
length restriction is not.** Recomputing an estimand on the subset of responses
above a word threshold drops a different share of each arm and conditions on a
post-treatment variable; it is not §17.4 and is never reported in its place.

### 17.5 Emission machinery

Every emitted statement carries the machine fields `claim_level`,
`configuration`, `family`, `interval_type`, `identification_status`,
`measurement_basis`, `difficulty_coordinate`, and the position of the outcome
constraint. One guarded emitter exists per claim level; each refuses a member
name not registered to it, so a secondary quantity cannot appear inside an L1,
L2 or L3 statement. An executable check refuses any statement missing a field,
and a second refuses any statement that quotes a scalar without its
configuration.

### 17.6 When the estimands disagree

Registered in advance, for the joint reading of $\Delta_R$,
$\delta_{\text{diff}}$ and $\Xi$ within one configuration. Every row assumes the
identification gates of §3.2 hold; where one fails, its row is not reached.

| $\Delta_R$ | $\delta_{\text{diff}}$ | Registered reading | Emitted |
|---|---|---|---|
| upper bound < 0.10 | inside $\pm 0.10$ at precision | Generic companion difficulty and the local matched set agree: no $A$-specific excess is identified | L3c **and** L3e |
| lower bound > 0.10 | lower bound > 0 | $A$ exceeds both the local matches and the broader difficulty relation | L3a (and L3b if > 0.25) **and** L3d, subject to the $\Xi$ gate |
| lower bound > 0.10 | inside $\pm 0.10$ at precision | The three local references were unrepresentative of the difficulty relation; the broader relation explains $A$ | **Neither.** `LOCAL_AND_SPECTRUM_DISAGREE`; both intervals reported; the per-reference $\Delta_j$ table and the fitted line reported beside them |
| upper bound < 0.10 | lower bound > 0 | The local matches resemble $A$ unusually closely relative to the relation | **Neither.** `LOCAL_AND_SPECTRUM_DISAGREE`; same reporting |
| either | support fails | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`; the local reading stands alone and is emitted with that status attached | L3a/L3b/L3c only |
| either | half-width above precondition | `INSUFFICIENT_PRECISION` on that member; direction reported if resolved | as available |
| any | any, with the three $\Delta_j$ intervals not on one side of the threshold used | §13.4 heterogeneity qualifier fires | the statement, with the disagreeing reference named |

**A disagreement is a result.** It is reported as one, with both quantities and
the diagnostics that distinguish them, and it never resolves toward whichever
estimand crossed a threshold.

**Coordinate agreement.** The fit of §11.7 is computed on the registered
instructed-compliance coordinate and, separately, on raw solo compliance. When
the two coordinates give different L3d/L3e classifications, the statement
carries `DIFFICULTY_COORDINATE_DEPENDENT` and both readings are reported. The
registered coordinate decides which classification is *emitted*; the secondary
decides whether that emission carries the status.

---

## 18. Stage sequence and gates

| # | Stage | Passes when | Failure |
|---:|---|---|---|
| 1 | `QUALIFIED` | Clean tree, tracked implementation, resolved revisions, non-empty dependency manifest, schema-valid prompt plan, wording and witness suites pass for every registered pair, class labelling asserted, cache and durable store reachable, environment and commit hashable | `QUALIFICATION_FAILURE` |
| 2 | `GATE_0_APPARATUS` | The procedural pilot of §19 | `APPARATUS_FAILURE` |
| 3 | `REGIME_SCREEN` | Completion cap selected; dense ladder screen complete; §12.6's expansion run to its stopping rule and the **candidate vocabulary frozen**; pre-screen difficulty table and shortlist written before any Gate 2 generation | `RESPONSE_LENGTH_INCOMPATIBLE` |
| 4 | `GATE_1_MEASUREMENT` | §10.2 for every verifier in the final instrument population, plus §10.3 or §10.4; verifier hash frozen | `MEASUREMENT_NOT_ESTABLISHED`, `MEASUREMENT_EVIDENCE_INSUFFICIENT` |
| 5 | `GATE_2_REGIME` | $n^*$ and $m^*$ selected inside their bands; §12.4 adequacy holds | `TARGET_RANGE_EXHAUSTED`, `FOCAL_RANGE_EXHAUSTED`, `GRID_RESOLUTION_INSUFFICIENT`, `REGIME_NOT_FOUND` |
| 6 | `GATE_3_REFERENCES` | Three core families admitted under §13.4, each supplying a complete straddling triple under §13.6; class companion admitted or `CLASS_ARM_NOT_AVAILABLE` | Not terminal: sets `EXCESS_NOT_IDENTIFIED` and/or `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and the reduced design of §8.6 |
| 7 | `GATE_4_COMPOSED_HEADROOM` | Every registered cell type inside $[0.05, 0.95]$ on every constraint | `COMPOSED_HEADROOM_FAILURE` |
| 8 | `GATE_5_FREEZE` | The freeze record of §18.1 written and verified | none |
| 9 | `CONFIRMATORY_GENERATION` | Complete draw matrix committed | none |
| 10 | `MASKED_ANALYSIS` | §20 | none |
| 11 | `UNMASKING` and `UNMASKED_ANALYSIS` | §20 | none |

Every command verifies the content hash and signature of its predecessor record
and re-verifies the frozen verifier hash (§10.6) before any mutation. A terminal
state mechanically disables every later command, generation or not. Every
attempted transition is logged with timestamp, revisions, producing commit,
environment digest, input and output hashes, and outcome.

**Gate 1 does not depend on Gate 3.** The instrument population is the declared
range of §7.0, §7.3 and §7.4, which this document registers, so §10.2's evidence
is required whatever §12.6 measures and whatever Gate 3 selects, and can be
produced before Gate 2 runs. It *does* follow the regime screen, because the
regime screen is where the vocabulary closes; §10.2 says what happens to a
family that fails there.

### 18.1 The freeze record

Protocol version; model repository and revision; the prompt template including
the §8.5 stem byte-for-byte; completion cap; $n^*$; $m^*$ and whether the
conditional extension was measured; the complete candidate family vocabulary of
§7.3 and §7.4 with every ladder; every wording; the class label of every family;
the difficulty-coordinate definition; the chance-compliance definition; the
eligibility band; the core-reference selection rule and the three admitted
families with their severities; the spectrum-selection rule, the registered
offset, and the six admitted spectrum severities; the class-admission rule and
the admitted class severity or `CLASS_ARM_NOT_AVAILABLE`; the support rule; the
hash of the calibration table the selections read; the 47-cell plan; the order
and wording allocation; topic splits; seed rules; $M$ and the block count with
the §16.1 re-estimate that justified them; every verifier source and the
canonical verifier hash; the graded-score definitions; the non-vacuity
predicates; decoding settings; family declarations F1–F9; the
difficulty-model functional form; the bootstrap algorithm including the refit
loop of §17.2; thresholds, regions and precision preconditions; the claim ladder
and every decision rule of §17.6; the codebook; producing commit; clean-tree
assertion; dependency and environment digests; hardware record; gate-record
hashes; the Gate 1 measurement basis; and the complete analysis plan.

No scientific rule changes after the study-wide freeze. Any change creates a new
protocol version. A model-specific frozen-field change after that model's
confirmatory generation begins creates a new protocol version and leaves the
original result unchanged.

---

## 19. Qualification and procedural pilot

Qualification is non-scientific and reads no behavioural rate. After it, a
procedural pilot on twelve fixed pre-screen topics runs all 47 cells, both
orders, and the registered wording allocation, at fixture values that cannot
become calibration evidence, with $M = 4$: 2,256 cached draws.

Acceptance requires all of: every logical cell and draw committed exactly once;
every cell yielding one cell mean over exactly $M$ accepted draws; zero
technical generation failures after retries; every codebook field present and in
domain; the full analysis pipeline running to a structurally complete result
table with every numeric value redacted, **including a fitted difficulty
relation, a support diagnostic and a $\delta_{\text{diff}}$ row**; mutating one
stored byte changing its content hash and causing the analysis to refuse the
row; cache deletion and durable restore reproducing every row with matching
hashes; and the separate pilot mask cycle completing without touching the
confirmatory mask namespace.

Failure returns `APPARATUS_FAILURE`; repair creates a new producing commit and
requires qualification and the pilot to run again.

---

## 20. Masking and unmasking

**What is masked.** After confirmatory generation and before any analysis, the
pipeline permutes the **companion label** within each (outcome constraint,
configuration, block) group of composed observations, using a seed from the
system random source. Solo and unconstrained cells carry no companion and are
not permuted.

**Consequences for the difficulty relation, declared.** Permuting companion
labels within an outcome-and-configuration group permutes which
$D(B \leftarrow \cdot)$ belongs to which companion, so the masked-phase fit is a
fit of the same nine losses against a permuted assignment of difficulties. That
is the intended protection: analysis decisions about the fit — its diagnostics,
its degenerate-replicate handling, its support reporting — are made without
knowing which point is which. The companion **difficulties** themselves come
from solo and unconstrained cells and are not permuted, so the difficulty
coordinate is visible in the masked phase; that is deliberate, because it is a
pre-treatment quantity fixed by Gate 3 and nothing about it can be tuned.
$A$'s point is inside the permuted group, so $\delta_{\text{diff}}$ is not
computable in the masked phase and is computed after unmasking under the fully
registered plan, labelled as such.

**What else is not masked, declared.** A composed generation contributes two
observations whose companion labels are permuted independently, so joint-state
and joint-success quantities cannot be computed in the masked phase. They are
computed after unmasking under §11.5 and are labelled as computed
post-unmasking. Those quantities support no claim.

**Masked phase.** All planned analysis code executes on the permuted table. All
reading of response text, all hand coding, all inspection of degeneracy and
compliance quantities, and all anomaly diagnosis happen here. Permitted:
repairing an analysis defect, adding a diagnostic, declaring an anomaly and
fixing the rule that will handle it. Forbidden here and afterwards: changing an
estimand, family, threshold, region, precondition, reference set, spectrum set,
class companion, difficulty coordinate, functional form, support rule, verifier,
scoring rule, claim rule, claim level, non-vacuity predicate, or topic split.

**Unmasking.** A single named function invoked once, writing a timestamped entry
with the content hash of the analysis code at that moment. Executable checks:
the permuted labels differ from the true labels in at least half of the blocks
in every group; the mask key file is opened exactly once in a full run; the
recorded analysis-code hash at unmasking reproduces every masked-phase output
byte for byte.

**After unmasking.** Any analysis-code change is labelled post-unmasking, is
exploratory, and supports no registered claim. Masked and unmasked outputs are
both released.

---

## 21. Analysis order

1. Load confirmatory rows; reject any row outside the frozen plan by prompt
   hash, revision, verifier hash, or block identity.
2. Re-verify the frozen verifier hash; fail closed on mismatch.
3. Assert the complete matrix of 384 blocks by the registered cell count of the
   design in force by $M$ draws, each committed exactly once; count duplicates
   and missingness.
4. Form cell means over all $M$ accepted draws; refuse any partial cell.
5. Score the compliance vector, the graded vector and the degeneracy flags for
   every constraint, marking each verdict present or chance.
6. Compute per-cell compliance, chance compliance, instructed compliance,
   vacuity, truncation, length and graded-score summaries.
7. Form the delivery losses, the asymmetry, the companion swaps and
   $\Delta_{\text{class}}$ within each configuration.
8. Fit the §11.7 difficulty relation on the nine non-$A$ points, assert $A$'s
   exclusion, evaluate the §13.8 support conditions, and form
   $\delta_{\text{diff}}$ in both algebraic forms and assert their agreement.
9. Form $\Xi$ and the F4 components.
10. Run the block bootstrap with 10,000 resamples inside each configuration,
    refitting the difficulty relation in every replicate per §17.2.
11. Compute simultaneous intervals within each declared family.
12. Compute the F5 vacuity-forced recomputation and the F6 gate.
13. Repeat steps 8 to 11 on the raw-coordinate secondary fit.
14. Apply §17.6's joint reading, then the claim ladder of §3 with the rules of
    §17, emitting through the guarded emitters.
15. Compute the post-unmasking joint-state and redistribution quantities and
    label them.

The analysis fails closed. A missing cell, an incomplete draw set, a duplicate
accepted row, a non-finite standard error, a non-finite bound or a degenerate
fit returns a named inconclusive status for the affected quantity and computes
no claim. No cell, block, constraint or draw is dropped, and no missing value is
imputed. The design is fixed size: no interim analysis, no optional stopping, no
adaptive sample size.

---

## 22. Prohibited and mediating quantities

Recorded for every generation and never entering a primary estimand as a
covariate, filter, stratifier or weight: response length in words and tokens,
truncation status, finish reason, graded score, vacuity flag, joint state,
stem-band membership, and any other quantity produced during or after
generation. The analysis asserts this by checking the declared causal role of
every field named in a primary formula.

**Chance compliance is pre-treatment for the companion and is not on this
list.** $\kappa_c$ is measured in a cell where $c$ is absent, so it is not
produced by any treatment applied to $c$; it enters the difficulty coordinate by
registration. It is nevertheless *post-treatment for the topic*, in that a
topic's natural answer determines it, and it is therefore never used as a
covariate on the outcome, never used to weight a block, and never used to select
or drop a block. Its only registered use is as the denominator of §13.3's
coordinate, computed as a cell-level quantity on the same blocks as everything
else.

**Response length is registered as a mediator.** Composition shortens answers,
and shorter answers satisfy budget constraints more readily, so response length
lies on the path from companion to outcome. It is reported per cell, its
composed-to-solo change is reported per constraint, and a registered descriptive
decomposition reports the delivery loss within strata of realised response
length. No mediation effect is claimed, and no primary estimand is adjusted for
it. §29 records that the length account of $A$ is **not identified** by this
design. Changing the estimand to a length-conditional one would require a new
protocol version.

---

## 23. Secondary analyses and error analysis

All Tier-secondary, none able to change a primary conclusion.

- Every F2 to F9 member with its simultaneous interval.
- The fitted difficulty relation: slope, family intercepts, per-companion
  residuals, the support diagnostic and its bootstrap share, and the same on the
  raw coordinate.
- The class arm: $D(B \leftarrow CL)$, $\Delta_{\text{class}}$, and $CL$'s
  residual from the difficulty line, reported as a residual from a line the
  class companion did not enter.
- Chance compliance, instruction lift and instructed compliance for every
  registered constraint instance, with the pre-screen, calibration and
  confirmatory values side by side.
- The stem's satisfaction rate by load and by cell type.
- Joint-state vectors per composed cell and their redistribution across order
  and checkpoint; joint success per composed cell.
- The graded vector distribution per cell, and the graded manipulation check.
- The demoted v3 estimand $\Delta^A$, reported only with its three gates
  satisfied and its configuration quoted.
- Failure taxonomy for the exact-count constraint: empty, cut off, refusal,
  restatement, target inside a longer word, zero occurrences, too few, too many,
  other, applied in that priority order, split by whether the realised margin is
  exactly one.
- The primary estimands recomputed under $S_1$, $S_2$ and $S_3$ for the $A$-side
  outcome.
- Companion-difficulty sensitivity: $D(B \leftarrow R_j)$ reported against the
  confirmatory-measured instructed-compliance gap between $R_j$ and $A$.
- Confounder description: compliance as a function of response length,
  truncation, refusal and subject area within each cell, with any material
  association reported as a competing explanation.
- The greedy replication on 96 blocks, reported as a different generation
  population.
- The realised variance decomposition — $\sigma^2_{\text{topic}}$,
  $\sigma^2_{\text{draw}}$, both within-block correlations, the realised
  $\sum w^2$ and the realised $\hat\beta$ — reported beside every primary
  estimate together with the realised simultaneous half-width and the achieved
  detectable effect it implies.
- Compliance by subject area and by wording index.
- Cross-configuration and cross-model tables, descriptive only.

---

## 24. Segmentation and construct-validity checks

Before freeze, for every registered verifier:

1. Enumerate the boundary cases of its scoring convention.
2. Encode each as a deterministic unit test with a frozen expected verdict.
3. Run a targeted adversarial corpus over the enumerated cases.
4. Quantify how often each case occurs in genuine generations from the
   calibration stages, per cell type.
5. Compare the primary convention against prespecified reasonable alternatives,
   registered before the comparison is run.
6. Report the alternatives as robustness analyses. Switching a scoring
   convention after results are seen is prohibited.

For the exact-count constraint the enumerated cases include ordinary punctuation
adjacent to the target word, concatenated copies, hyphenation, Unicode
punctuation, Unicode lookalikes, zero-width characters, capitalisation, and
sentence-boundary punctuation. For the word-length and budget constraints they
include empty output, single-token output, hyphenated and apostrophised forms,
non-Latin script, digits and symbols adjacent to words, and markdown emphasis.
For the rate constraints they additionally include a wordless answer, a
single-word answer, and rates straddling each severity. For the lower-bound
constraints they additionally include counts at $q-1$, $q$ and $q+1$.

**The enumeration is checked in both directions.** Every enumerated case must
appear in the adversarial corpus and in the boundary suite, and a case named
differently by the two must be reconciled explicitly rather than reported as a
coverage gap: two independently authored enumerations of the same seven cases
were found to disagree on three labels and to report a gap that did not exist.

The goal is to know exactly what construct each deterministic rule
operationalises and how often its edge cases matter empirically, not to make any
rule imitate human intuition.

---

## 25. Contamination and chance compliance

Every v4 topic is newly written; no v3 topic and no pilot topic enters any v4
set. At release the exact text of each confirmatory topic is queried against a
public web search index and the number of exact-phrase matches is reported. A
canary string is embedded in the released dataset file. The 72 v4 sequestered
topics are withheld; the 96 v3 sequestered topics remain sequestered and
untouched.

**Chance compliance is measured on the confirmatory blocks and is a registered
input, not only a diagnostic.** The unconstrained cell of §8.1 gives $\kappa_c$
for every registered constraint on the same 384 blocks at the same $M$, and
every cell where a constraint is absent additionally records that constraint's
verdict, giving the base rate under other constraint loads. Any cell whose
truncation rate exceeds 0.10 has its chance figure reported as a bound.

This is the one place v4r3 changes what §25 is *for*. In v4r2, accidental
compliance was measured and never fed into anything. §13.3 makes it the
denominator of the difficulty coordinate, on the evidence of §2.3(b), and §22
records the exact sense in which that is legitimate.

The outcomes are instruction compliance, which does not depend on knowing a
correct answer, so memorised answer content cannot by itself produce a pass.

---

## 26. Execution integrity and provenance

Every generation records stage, artifact state, model replication, block, cell
type, arm, constituent constraint identities, severities and classes, order,
position of each constraint, wording indices, draw index, prompt hash, model
revision, backend version, interpreter identity, dependency digest, hardware
class, seed, raw response, response content hash, token counts, finish reason,
stem-band membership, and every verifier verdict, graded score, presence flag and
degeneracy flag with the verifier source hash.

Artifacts move monotonically through `generated`, `committed`, `accepted` and,
when audit-preserved and excluded, `superseded`. A committed artifact becomes
accepted only after durable write, content-hash verification, stage
authorisation, predecessor-gate verification, schema validation and frozen-plan
membership. A superseded artifact never returns to accepted.

The artifact-type vocabulary is closed:

```
qualification_record   prefreeze_plan        pilot_record
gate_record            calibration_record    registered_freeze
confirmatory_evidence  masked_result         unmasked_result
superseded_non_evidence
```

Every model tree contains the same required records, with every path derived
through one frozen path function:

```
qualification.json      gate0_apparatus.json    regime_screen.json
gate1_measurement.json  gate2_regime.json       gate3_references.json
gate4_composed.json     gate5_freeze.json
transition_log.jsonl    terminal_report.json
```

and, when confirmation is reached, `confirmatory_manifest.json`,
`masked_result.json` and `unmasked_result.json`.

The run aborts on a missing or invalid predecessor record, a dirty tree, an
invoked source absent from the producing commit, a prompt exceeding the context
limit, a revision or hardware or dependency change inside a run, a prompt hash
absent from the frozen plan, a duplicate accepted draw, a cell whose accepted
draw count differs from $M$, a verifier hash differing from the frozen value, a
content-hash mismatch, a stale output path, or an artifact whose declared type
disagrees with its stage.

**The v4r3 implementation lives in its own namespace**, writes nothing inside any
v2, v3, pilot, v4r2 or screen evidence tree, and refuses any analysis input
classified deprecated or foreign. Its study identifier is chosen so that a v4r3
artifact cannot satisfy v4r2's admission prefix and a v4r2 artifact cannot
satisfy v4r3's, so the isolation holds in both directions and is tested in both
directions.

---

## 27. Codebook and computational environment

A codebook accompanies every released table with one row per variable giving
name, type, permitted values, units, causal role and a one-sentence definition.
Causal role takes one of identity, treatment, design, outcome, post-treatment,
provenance. Executable checks: every released column appears in the codebook and
every codebook row appears as a column; every value is in domain and of declared
type; no post-treatment field appears in a primary formula; every field declared
to constrain execution is consumed by a named check in §26.

The environment record contains lockfile and frozen-export hashes, interpreter
and version, exact invocation command, backend version and settings,
tensor-library and driver versions, operating system and kernel, GPU name and
architecture, model repository and revision, chat-template hash, and registered
execution-relevant environment variables. Executable checks: a dependency change
moves the environment digest and an empty manifest is rejected; deterministic
derivations reproduce their recorded hashes from the producing commit; rerunning
the analysis in the recorded environment on released raw responses reproduces
the released table byte for byte; cache deletion and durable restore reproduce
every committed row and regenerate no committed draw.

---

## 28. Outcome vocabulary, terminal statuses, and identification statuses

### 28.1 Confirmatory outcomes

Recorded per F1 member per configuration.

| Outcome | Condition | Licensed statement |
|---|---|---|
| Delivery loss resolved | $D(c \leftarrow g)$ simultaneous lower bound above 0 | Composing $c$ with $g$ reduced delivery of $c$ in this configuration, with $c$ stated in the named position |
| Delivery gain resolved | Upper bound below 0 | Composing $c$ with $g$ raised delivery of $c$ in this configuration |
| Meaningful magnitude | The interval lies wholly beyond $\pm 0.10$ | The change exceeds the smallest effect of interest |
| Equivalence | The interval lies wholly inside $\pm 0.10$ and the half-width meets its precondition | Any change is smaller than the smallest effect of interest, at adequate precision |
| Asymmetry resolved | The $\Lambda$ interval excludes 0 | The loss is directionally asymmetric between $A$ and $B$ in this configuration |
| Local excess above generic-load threshold | $\Delta_R$ lower bound exceeds 0.10 | $A$ costs $B$ more than companions matched to $A$ on instructed compliance do, by more than the registered generic-load threshold |
| Pair-specific threshold reached | $\Delta_R$ lower bound exceeds 0.25 | The local excess reaches the source memo's pair-specific threshold |
| Generic compositional load, locally | $\Delta_R$ upper bound below 0.10 | The local excess is below the generic-load threshold |
| Spectrum excess resolved | $\delta_{\text{diff}}$ lower bound above 0, support holding | $A$ costs $B$ more than the fitted relation between companion difficulty and focal loss predicts at $A$'s difficulty |
| Difficulty accounts for $A$ | $\delta_{\text{diff}}$ interval wholly inside $\pm 0.10$ at precision | $A$ behaves as a companion of its difficulty is expected to behave, within the smallest effect of interest |
| Outcome-specific | $\Xi$ lower bound above 0 | The excess is specific to the outcome $B$ |
| $A$-general not excluded | $\Xi$ interval does not exclude 0 from below | The excess is not distinguishable from $A$ being generally disruptive as a companion |
| Estimands disagree | §17.6 rows 3 or 4 | The local and spectrum readings disagree; both are reported and neither is emitted as a claim |
| Indeterminate at a threshold | The interval spans that threshold | The design did not separate the two readings at that threshold in this configuration |
| Insufficient precision | The realised half-width exceeds its precondition | The design did not achieve the registered precision; equivalence and threshold statements are withheld |
| Reference heterogeneity | The three $\Delta_j$ intervals do not agree on one side of the threshold used | The L3 statement is emitted with the disagreeing reference named |
| Companion-difficulty qualifier | A realised instructed-compliance gap exceeds 0.15 | The L3 statement is emitted with the reference and its realised gap named |
| Vacuity asymmetry | An F6 difference exceeds 0.05 with its interval excluding zero | Composition changed how often the constraint could bind; claims follow both partial-identification bounds |
| Replication | The same classification in every registered configuration | The classification is stable across the registered configurations |
| Configuration dependence | Classifications differ across configurations | The quantity is configuration-dependent; the table is reported and no pooled scalar is quoted |

### 28.2 Identification statuses, which are not terminal

| Status | Meaning |
|---|---|
| `EXCESS_NOT_IDENTIFIED` | Fewer than three core references admitted under §13.4. L1 and L2 proceed under the reduced design; L3a–L3c are withheld |
| `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | §12.6's coverage criterion fails at design time, or §13.8's support conditions fail on the confirmatory data. L3d and L3e are withheld; any fit is reported as descriptive and outside support |
| `CANDIDATE_RESERVE_EXHAUSTED` | §12.6's expansion ran out of reserve rungs before coverage passed. Recorded beside `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, and it says the library rather than the model was the binding constraint |
| `DIFFICULTY_SUPPORT_MARGINAL` | Support holds on the point estimate but in fewer than 0.95 of bootstrap replicates |
| `A_GENERAL_NOT_EXCLUDED` | $\Xi$'s interval does not exclude 0 from below; no L3 statement says the excess is $B$-specific |
| `LOCAL_AND_SPECTRUM_DISAGREE` | §17.6 rows 3 or 4; no L3 claim is emitted and both readings are reported |
| `DIFFICULTY_COORDINATE_DEPENDENT` | The registered and secondary coordinates give different L3d/L3e classifications |
| `DIFFICULTY_COORDINATE_DEGENERATE` | A companion's chance compliance reached 0.99 and its point was dropped from the fit |
| `COMPANION_CLASS_NOT_MATCHED` | Attached to **every** L3 statement. The registered sentence: *the reference pool is budget class and $A$ is production class, so this excess is relative to budget-class companions matched on instructed compliance and is not an excess relative to companions of $A$'s own structural class* |
| `CLASS_ARM_NOT_AVAILABLE` | No class severity was eligible; $\Delta_{\text{class}}$ is not computed and the class bound is unavailable |
| `CLASS_ARM_NOT_MATCHED` | A class companion was admitted but $\lvert \iota_{CL} - \iota_A \rvert > 0.15$; $\Delta_{\text{class}}$ is reported as a contrast between companions of different difficulty and bounds a class effect only weakly |
| `POSITION_CONFOUNDED` | Attached to every L1 statement in the configuration where the outcome constraint is not stated first |
| `HUMAN_VALIDATION_UNAVAILABLE` | No independent annotator; the measurement basis is the autorater pathway and the scope sentence of §10.5 is attached |

### 28.3 Terminal statuses

| Status | Condition |
|---|---|
| `QUALIFICATION_FAILURE` | Code, model, environment, schema, witness, class-labelling or provenance qualification fails |
| `APPARATUS_FAILURE` | Execution, cache, hashing, storage restoration, mask plumbing or integrity machinery fails |
| `RESPONSE_LENGTH_INCOMPATIBLE` | Every registered cap has truncation above 0.10 on constrained prompts |
| `TARGET_RANGE_EXHAUSTED` / `FOCAL_RANGE_EXHAUSTED` | An outcome constraint's curve stays outside its band at a registered grid boundary, the focal case after the §7.2 extension has been measured |
| `GRID_RESOLUTION_INSUFFICIENT` | Adjacent registered severities jump across a whole band |
| `REGIME_NOT_FOUND` | §12.4 adequacy fails |
| `COMPOSED_HEADROOM_FAILURE` | A registered cell type falls outside $[0.05, 0.95]$ on any of its constraints |
| `MEASUREMENT_NOT_ESTABLISHED` / `MEASUREMENT_EVIDENCE_INSUFFICIENT` | §10.3 criteria fail or cannot be reached |

Every terminal record carries the model and revision, gate, criterion,
threshold, observed value, complete curves, difficulty table, admission table,
spectrum table, composed table, degeneracy and truncation summary, verifier
status and measurement basis, artifact hashes, producing commit, environment
digest, the strongest permissible statement, and the estimands left
unanswerable. It also carries verbatim: **a terminal pre-confirmatory status
carries no evidence about the effect.**

`REGIME_NOT_FOUND` is a statement about the registered grid. It is never
reported as a failure of the model or of the hypothesis.

---

## 29. Limitations and design trade-offs

**Load two only.** The construct memo's best-evidenced interaction quantity is
three-place and requires a third scored constraint. This design cannot estimate
it and takes no position on whether the phenomenon is two-place or higher-order.

**Matched and fitted, not semantic.** An excess attributable to $A$ is an excess
relative to companions matched on instructed compliance and instruction length,
and relative to a fitted relation over nine such companions. Other properties of
$A$ remain free, so semantic identity-specificity is not identified and is never
claimed.

**The reference pool is budget class and $A$ is production class.** This is the
sharpest limitation of the design and it is structural rather than
circumstantial. A production-class reference matched to $A$ on difficulty would
have to be a lower-bound constraint, which imposes a length floor while $B$
imposes a length ceiling; the pool contains no production-class family that is
free of that. `COMPANION_CLASS_NOT_MATCHED` attaches to every L3 statement,
$\Delta_{\text{class}}$ bounds how much it could matter, and a class *claim*
would need several production-class families replicated at matched difficulty —
a design this document does not attempt.

**The length account is not identified, at any block count.** Response-length
shift and companion identity are collinear across every companion set this pool
can produce: $A$ lengthens responses far more than any budget companion
shortens or lengthens them, so a line fitted over the companions extrapolates to
$A$. Testing the length account needs a companion that changes length about as
much as $A$ does without being $A$, and the pool contains none. The design
reports length diagnostics and states that they identify nothing about $A$; it
does not report a length residual as if it were a measurement.

**The difficulty relation is fitted on nine points.** Three families, three
rungs each, four parameters, five residual degrees of freedom. That is enough
for a family-aware line and not enough for a per-family slope or a non-linear
form. A flat realised slope would make $\delta_{\text{diff}}$ close to a
nine-companion $\Delta_R$; that is the correct behaviour and not a failure, and
§11.7 says so in advance.

**The difficulty coordinate is a choice with a cost.** Instructed compliance
nets out chance and is therefore comparable across the production/budget divide,
which raw solo compliance is not. It is also noisier, because it is a ratio of
two estimated quantities, and it is undefined at $\kappa = 1$. Both coordinates
are computed and §17.6 registers what their disagreement means. A researcher who
prefers raw solo compliance as primary would be choosing the coordinate on which
matching is easier and comparability is weaker; §33 D6 records the decision.

**Configuration dependence is a scope condition, not noise.** Eight registered
configurations are reported separately. A quantity that reverses or changes
magnitude across them is reported as configuration-dependent.

**The position confound.** In the configuration where the outcome constraint is
stated second, $D(c \leftarrow g)$ mixes added load with a change of position.
Only $\Delta$-type quantities are position-clean in both configurations.

**Vacuous passing is bounded, not eliminated.** The stem narrows the range over
which the length gradient operates and the rate families remove prefix closure,
but a 62-word answer still satisfies a budget more readily than a 118-word one.
The registered predicate, the per-cell vacuity rates, the F6 gate and the
partial-identification recomputation bound the effect; they do not remove it.

**The stem is one more instruction.** It competes for compliance and could
interact with the constraints under study rather than sitting inertly beneath
them. Its satisfaction rate by load is the diagnostic, it is reported on every
stage record, and a strong load-dependence in it is a limitation to be reported
rather than a result.

**The sequestered set is smaller than v4r2's.** 72 topics rather than 96,
because 47 cells, six primary members and a 624-question bank cannot all be
had at $M = 4$.

**The variance model is a projection**, fitted to two models' pilot interval
widths under two correlation assumptions, with $\rho$ assumed and the planning
slope conservative. Both settings are carried through §16.2 and the allocation
meets every precondition under both. An unfavourable realisation appears as
`INSUFFICIENT_PRECISION` rather than as a silent widening.

**All four screens are exploratory throughout.** Their point estimates never
function as the expected confirmatory effect, their topics are the development
sets, and their rows cannot enter a v4r3 analysis.

**Measurement may remain verifier-defined.** If no independent annotator is
available, the basis is the autorater pathway and every claim carries the scope
sentence of §10.5.

**Single-custodian masking.** The mask key is opened once by the analysis code,
with the protection resting on recorded hashes and timestamps.

---

## 30. Release

Released under a permissive licence when results are reported: all 552
non-sequestered v4 topics with the canary string and a manifest recording that
72 of the 624 are withheld; every constraint definition, ladder, wording,
witness, class label and verifier source; the graded-score and non-vacuity
definitions; the difficulty-coordinate definition and the chance-compliance
tables; the boundary suites and adversarial corpora; study-wide and per-model
freeze records; qualification, gate, transition and terminal reports; commit and
clean-tree records; lockfile, frozen dependency export and environment manifest;
the codebook; every prompt; every committed raw draw with its content hash,
artifact state, compliance vector, graded vector, presence flags and degeneracy
flags; human labels and carry-over records; autorater configuration, judgments
and calibration records where that pathway was used; calibration records
including the complete ladder curves, difficulty tables, admission tables and
spectrum tables; the fitted difficulty relations and their support diagnostics;
masked and unmasked outputs; the unmask timestamp; analysis code; and the
machine-readable result table carrying each estimate with its configuration,
claim level, family, identification status, measurement basis,
difficulty coordinate, standard error, marginal and simultaneous bounds,
realised half-width, realised variance decomposition, achieved detectable effect
and cell counts.

Every reported figure is reproducible from the result table without regenerating
a response, and every number in that table is reproducible from accepted raw
responses in the recorded environment.

---

## 31. Amendment procedure and allowed deviations

Before study-wide freeze, any change is a revision of this document, recorded
with its date, its evidence and its author, and is prospective by definition
because no confirmatory data exist. **This document is itself such a revision**:
v4r2 was never frozen and produced no confirmatory data, so revision was the
available mechanism and v5 was not required.

After study-wide freeze: operational settings that cannot change a scientific
quantity, such as device placement or batch size, may change with a recorded
environment note. Every other change creates v5. A model-specific frozen-field
change after that model's confirmatory generation begins creates a new protocol
version and leaves the original result unchanged.

**An amendment is never used to weaken a criterion in order to make a gate
pass.** Two consequences are made explicit because this revision is large enough
that they could be blurred:

1. **A gate failure is a result.** `REGIME_NOT_FOUND`, `FOCAL_RANGE_EXHAUSTED`,
   `EXCESS_NOT_IDENTIFIED` and `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` are
   registered outcomes with registered readings. None of them is an occasion to
   widen a caliper, lower a vacuity threshold, extend a ladder, add a family, or
   change a coordinate.
2. **A change adopted after a gate has run is adopted because that gate ran.**
   The changes this revision makes are adopted *before* Gate 1 and Gate 2 have
   been executed under any protocol version, on evidence from screens that were
   deliberately run outside the registered lifecycle for exactly this reason. If
   a gate is executed under v4r3 and fails, the answer is the registered
   reading, not v4r4.

Amendments are recorded in a single append-only register carrying the amendment
text, its timing relative to every affected artifact, what it supersedes, and
what it leaves untouched.

---

## 32. Changelog and the disposition of historical DCI quantities

The full v4r2 → v4r3 changelog is `DCI1_v4r2_to_v4r3_changelog.md`. The
dispositions it records are binding here. v4r2's own dispositions of the v2 and
v3 quantities are carried forward unchanged and are not restated. The
dispositions this revision adds:

| Quantity | Disposition | Reason |
|---|---|---|
| Raw solo compliance as the reference-matching coordinate | **Demoted** to a registered secondary coordinate | It equates a constraint the model must work to satisfy with one it satisfies for free; §2.3(b) |
| Instructed compliance $\iota$ | **Adopted** as the registered difficulty coordinate | It is the same quantity net of chance, measurable before any composed cell, and comparable across constraint classes |
| Chance compliance $\kappa$ | **Promoted** from an unused §25 diagnostic to a registered design input with its own confirmatory cell | It is the denominator of the coordinate; measuring it off-design would leave the coordinate unregistered |
| $\delta_{\text{diff}}$ | **Adopted** as primary | It answers the difficulty question by identifying the relation rather than assuming it, and it does not depend on three particular companions |
| $\Xi$ | **Promoted** from secondary to primary | The v4r3 claim ladder gates the wording of every L3 statement on it, and a gating quantity carries its multiplicity cost |
| $\Delta_R$ | **Retained** as primary, on a new coordinate | The local matched comparison remains the memo's discriminating quantity; only what "matched" means has changed |
| $\Delta_{\text{class}}$ | **Adopted** as a registered secondary bound | Constraint class moved focal compliance more than companion identity did in every screen that measured both |
| Open decision V5, "matched only or difficulty-spanning" | **Closed** in favour of both, with the spectrum arm at linear rather than quadratic cost | §2.4 |
| The v4r2 prompt template | **Superseded** by the four-part template of §8.5 | It could not reach a non-vacuous operating point on any model |
| The v4r2 focal grid as a flat grid | **Superseded** by the conditional escalation of §7.2 | A flat extension moves $m^*$ on models whose registered grid already works |
| §12.4's graded clause read as a mean | **Rejected** in favour of the share reading | The mean reading declares degenerate exactly the severities §12.3 declares eligible |
| Lower-bound families in the reference pool | **Excluded**; admitted to the class arm only | A lower bound imposes a length floor while $B$ imposes a ceiling |
| The pool-wide §7.5 witness obligation | **Scoped to realisable pairs** | Two families of one feature group are related by entailment at the edge of their ladders, so the obligation is *unsatisfiable* for such a pair rather than unmet; §7.0 groups them and §13.4 never admits both. 25,337 pairs remain and all are discharged |
| The reference pool as a fixed list of eight families | **Superseded** by the §7.0 grammar and the §12.6 expansion | Three approximately matched controls can be found by luck; a difficulty-response relation cannot, and a pool sized for the first cannot serve the second |
| "Three different families" as structural diversity | **Superseded** by three different **feature groups** | RF7 and CR7 are two families and one measurement; the §11.7 fit would carry three intercepts over two properties of an answer |
| The v4r2 composition order for the lexical rule | **Corrected** to segment-then-fold for $B$ and the families; unchanged for $A$ | §10.2's independent reimplementation disagreed with the primary, and §10.2 adjudicates against the prose. Realised frequency of the one affected character in 285,936 generations: zero |
| 408 confirmatory blocks at $M = 4$ | **Rejected as not executable** in favour of 384 at $M = 8$ | The released bank holds 384 accessible confirmatory topics; the rest are sequestered content hashes |

---

## 33. Registered open decisions

Recorded here so they cannot migrate into the analysis. Each is closed by
recording the decision and its evidence in the signed manifest **before
study-wide freeze**, and none may be decided after any confirmatory generation.

| # | Open decision | Standing |
|---|---|---|
| **D0** | **Whether to adopt this revision at all.** | **CLOSED 21 August 2026.** Adopted; `dci1/DECISIONS_V4R3.md` A0 |
| D1 | The confirmatory compute budget. 384 blocks at $M = 8$ is the only **executable** menu entry meeting every precision precondition, and it costs 577,536 generations. Enlarging the topic bank beyond 624 would make the 408-block row reachable at $M = 4$ for 306,816 generations, at the cost of authoring and verifying at least 24 further questions under §6.2's four rules and re-cutting the split. | **CLOSED 21 August 2026**: 384 blocks, $M = 8$, four models, 577,536 generations, 96 sequestered topics (`DECISIONS_V4R3.md` A1) |
| D2 | Whether a load-three arm with a registered background constraint is added so that the memo's $\Gamma$ becomes estimable | No load-three arm; §5 exclusion stands |
| **D3** | **§12.4's graded-degeneracy reading.** §12.4 adopts the share reading and gives the coherence argument. The researcher is asked to confirm it, because the mean reading halts every replication under every prompt and a reader is entitled to see that the reading under which the study runs was chosen on an argument and not on that consequence. | The share reading of §12.4 |
| D4 | Whether the spectrum carries more than two extra rungs per family, which would license a per-family slope or a non-linear form in §11.7 at quadratic cost in the fit's complexity and linear cost in cells | Two extra rungs per family; the registered form of §11.7 |
| **D12** | **Whether the class arm's rate lower bounds are the right way to reach a difficulty-matched class companion.** §7.4 registers CP4 and CP7 for that purpose and states plainly that a rate lower bound admits a budget-like satisfaction route — deleting non-conforming words raises the rate — so its `production` label is not pure. | **CLOSED 21 August 2026**: registered, with the impurity stated (`DECISIONS_V4R3.md` A2) |
| **D13** | **The §12.6 coverage criterion's seven values.** Every one is either carried from an existing registered rule or set to the minimum the downstream rule needs; none was chosen after seeing a coverage table. | **CLOSED 21 August 2026**: registered before any measurement (`DECISIONS_V4R3.md` A4) |
| **D5** | **Whether $\delta_{\text{diff}}$ receives a magnitude threshold of its own.** §11.8 registers direction plus the smallest effect of interest and declines to transfer the memo's 0.25. A prospectively argued threshold could be registered instead. | Direction and the SESOI only; no pair-specific threshold for $\delta_{\text{diff}}$ |
| **D6** | **Whether instructed compliance or raw solo compliance is the primary difficulty coordinate.** §13.3 registers instructed compliance on the evidence of §2.3(b), notes it is the harder criterion, and computes both. | Instructed compliance primary, raw solo secondary, `DIFFICULTY_COORDINATE_DEPENDENT` on disagreement |
| D7 | The reference caliper, registered at 0.10 on $\iota$ with a Newcombe condition and a realised-gap qualifier at 0.15 | 0.10, with `EXCESS_NOT_IDENTIFIED` rather than widening |
| D8 | The non-vacuity word threshold, registered at 20 and now stated to the model by the §8.5 stem | 20 words |
| D9 | Whether an independent annotator will be available, which decides the measurement basis | Autorater pathway with `HUMAN_VALIDATION_UNAVAILABLE` |
| D10 | Whether the class arm carries more than one production-class companion, which is what a class *claim* would require | One companion; `COMPANION_CLASS_NOT_MATCHED` stands and no class claim is made |
| D14 | Whether the eight feature groups of §7.0 are the right partition. `capital_char` and `capital_word` are grouped because one entails the other at $q = 0$; no other pair of numerators was found to be nested. | Eight groups as registered; the witness suite is the check |
| D11 | Whether a second focal-like outcome constraint is added as an exploratory test of outcome-side specificity | Not added |

**What none of these can fix.** The length account is not identified by any
companion set this pool can produce (§29); a class claim needs a design this
document does not attempt (§5); and no allocation resolves either.
