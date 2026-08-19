# Preregistration: is the interference between two instructions specific to the pair, or is it generic constraint load?

**Protocol identifier:** DCI-1
**Version:** 4.0, for registration
**Date:** 19 August 2026
**Confirmatory data collected at the time of registration:** none
**Registration target:** Open Science Framework, protocol-document format

**Design provenance.** Version 4 was designed after the completed version 3
study closed with two unmasked confirmatory replications and two terminal
non-identifications. Version 3 is preserved unchanged: its preregistration,
amendments A1 to A3.2, signed evidence trees, and results report are
historical evidence and are never edited. Section 34 records what v3
established and what changed. Every v3 quantity cited in this document is
read from the v3 artifacts named there; v3 recorded quantities are design
evidence for v4 and are never confirmatory evidence for v4.

**Companion documents.** `DCI1_v3_to_v4_change_summary.md` gives one entry
per substantive change in the form v3 problem, v4 fix, rationale.
`DCI1_v4_unresolved_decisions.md` lists the design choices this document
deliberately leaves open, each with the evidence needed to close it before
freeze. Section 35 reproduces the open items in registered form.

---

## 1. Definitions

Every term below is used throughout with the meaning given here. Terms
carried unchanged from v3 §1 are marked (v3).

| Term | Meaning |
|---|---|
| Language model | A program that receives a text input and produces a text output by sampling from a probability distribution over word pieces. (v3) |
| Prompt | The complete text sent to the language model on one occasion. (v3) |
| Response | The complete text the model produces from one prompt. (v3) |
| Instruction | A sentence in the prompt stating a requirement the response is meant to meet. (v3) |
| Constraint | An instruction expressed so that a fixed computer program can decide whether a response meets it. (v3) |
| Verifier | The computer program that reads a response and returns pass or fail for one constraint. (v3) |
| Scoring rule | The exact procedure turning a response into a verifier verdict, including text normalisation, the unit counted, and the comparison applied. (v3) |
| Compliance | The state in which the verifier returns pass. (v3) |
| Failure | The state in which the verifier returns anything other than pass. (v3) |
| Outcome constraint | A constraint whose compliance is a measured outcome in some arm. v4 registers two of them. |
| Target constraint, written $A$ | The primary outcome constraint. (v3) |
| Surrogate target constraint, written $S$ | The second outcome constraint, of identical structural form to $A$ and a different target word. It carries the generic-load comparison. New in v4. |
| Focal constraint, written $B$ | The constraint whose presence is the treatment under study. (v3) |
| Reference constraint, written $R$ | A constraint used in place of $B$ to form the comparison condition. (v3) |
| Added slot | The position in a two-constraint prompt occupied by $B$ or by a reference. |
| Load | The number of constraints present in a prompt at once. (v3) |
| Arm | One of the conditions a topic is run under, defined by which outcome constraint is present and which constraint occupies the added slot. |
| Topic | One question the model is asked to answer. (v3) |
| Item | One topic considered as a draw from a larger population of possible topics. (v3) |
| Block | One topic together with the fixed presentation order and the fixed wording choices assigned to it. All arms of a block share these. (v3) |
| Model replication | One complete application of this protocol to one registered model, with its own qualification, gates, calibration, freeze, confirmatory dataset, estimates, and terminal outcome. (v3) |
| Cached draw | One of $M$ stochastic completions generated for one confirmatory prompt cell. |
| Cell mean | The mean of the outcome indicator over all $M$ cached draws of one prompt cell. This is the v4 observation. |
| Draw-averaged estimator | An estimator whose per-cell input is the cell mean. Draws are averaged inside the cell; the block remains the only resampling unit. |
| Reference family | A structurally distinct kind of reference constraint with a registered severity ladder. (v3) |
| Severity ladder | The complete ordered set of registered integer severity values of one family, from most to least restrictive. New in v4; replaces the four-point grid. |
| Estimand | The numerical quantity the study aims to estimate, defined before data exist. (v3) |
| Risk difference | The difference between two probabilities, expressed on the probability scale. (v3) |
| Swap effect | The change in an outcome constraint's failure probability when $B$ replaces a reference in the added slot, at fixed load. |
| Generic constraint load | The component of a swap effect that is common to outcome constraints of the registered form, independent of which outcome constraint is measured. |
| Identity-specific interference | The component of a swap effect attributable to the pairing of $B$ with the specific outcome constraint measured. |
| Intention to treat | The rule that an estimate is computed from the condition assigned, with no conditioning on what the model did in response. (v3) |
| Post-treatment quantity | Any quantity produced by or after generation, such as response length or truncation status. (v3) |
| Uptake | Compliance with the constraint occupying the added slot. (v3) |
| Composed uptake | Uptake measured on a two-constraint composition, distinguished from solo compliance with the same constraint alone. |
| Manipulation check | A measurement showing that the assigned treatment reached the model, computed separately from the outcome. (v3) |
| Compliance check | A measurement showing that a generation was produced under normal operating conditions. (v3) |
| Non-behavioural failure | An outcome failure whose immediate cause is the apparatus, specifically an empty response, a response cut off at the token limit, or a response the verifier cannot process. (v3) |
| Jointly satisfiable | The property that at least one response satisfies every constraint in a prompt at the same time. (v3) |
| Witness | A concrete response demonstrating joint satisfiability. (v3) |
| Entailment | The property that satisfying one constraint automatically satisfies another. (v3) |
| Ceiling, floor, headroom | A condition in which the outcome constraint almost always passes, almost always fails, or neither. (v3) |
| Reachability | The capacity of the realised comparison baseline to express an effect at least as large as the declared smallest effect of interest in a stated direction. (v3) |
| Exchangeability | The property that any member of the reference set serves equally well as the comparison condition. (v3) |
| Near-miss failure | An outcome failure whose recorded count differs from the required count by exactly one. |
| Far-miss failure | An outcome failure whose recorded count differs from the required count by two or more, or which is non-behavioural. |
| Tolerant rule | A registered alternative scoring rule under which a near-miss counts as a pass. |
| Construct-discordant occurrence | An occurrence of the target word that the frozen rule counts and whose status as an instance of the intended construct is disputable, enumerated in §10. |
| Reliability | The extent to which a measurement procedure returns the same value when the same thing is measured again. (v3) |
| Precision | The narrowness of the uncertainty interval around an estimate. (v3) |
| Face, content, convergent, discriminant, ecological validity | As in v3 §1, with the evidence for each recorded in §10. |
| Construct validity | The degree to which a measurement provides evidence about the phenomenon it is meant to represent, established by assembling the forms of evidence above. (v3) |
| Cluster | The unit resampled by the bootstrap. (v3) |
| Bootstrap | A procedure that repeatedly resamples clusters with replacement to estimate uncertainty. (v3) |
| Family | A declared set of quantities that share one simultaneous confidence statement. (v3) |
| Simultaneous interval | An uncertainty interval constructed so that a stated confidence level applies to a whole declared family at once. (v3) |
| Šidák bound | A conservative critical value for a family of size $k$, obtained by using the two-sided level $1-0.95^{1/k}$ for each member. (v3) |
| Smallest effect of interest | The smallest risk difference the study treats as scientifically meaningful. (v3) |
| Equivalence region | The interval around zero inside which an effect counts as negligible. (v3) |
| Precision precondition | The registered requirement that a simultaneous half-width be at or below half the smallest effect of interest before an equivalence claim may be emitted. New in v4. |
| Partial identification bounds | The range of estimates consistent with every possible value of an unmeasured quantity. (v3) |
| Claim tier | One of the five registered levels of §15 that fix what a statement may assert and what must hold before it is emitted. New in v4. |
| Measurement basis | A machine-readable marker recording how the outcome measure was validated, taking the values `human_validated`, `autorater_calibration_approved`, or `human_validation_unavailable`. Carried from v3 amendment A2.1. |
| Masked analysis | Analysis performed on data whose condition labels have been permuted, so that decisions taken during analysis cannot depend on the result. (v3) |
| Mask key | The stored mapping from permuted labels back to true labels. (v3) |
| Procedural pilot | A small run whose purpose is confirming that the apparatus works end to end, with the quantities inspected fixed in advance. (v3) |
| Qualification | The non-scientific stage that verifies code, model, environment, prompt-plan, cache, schema, and provenance requirements before the procedural pilot. (v3) |
| Gate record | A content-addressed record containing the gate decision, criterion, threshold, observed value, producing code and environment, inputs, outputs, and timestamp. (v3) |
| Generated, committed, accepted, superseded artifact | The four artifact states of §27. (v3) |
| Codebook | A table with one row per recorded variable, giving name, type, permitted values, units, causal role, and definition. (v3) |
| Causal role | The label stating what a variable may be used for, drawn from identity, treatment, design, outcome, post-treatment, and provenance. (v3) |
| Contamination | The presence of study materials, or close relatives of them, in the data used to train the model. (v3) |
| Canary string | A rare fixed text placed in a released file so that its later presence in training data is detectable. (v3) |
| Decoding, greedy decoding | The procedure converting the model's output distribution into text, and its deterministic form. (v3) |
| Autorater | A language model used as a proxy instrument for verifier development and held-out evaluation. It is never human validation, never ground truth, and never scores a study outcome. Carried from v3 amendment A2. |

---

## 2. Phenomenon and its three separable components

The phenomenon is **directional constraint interference**: the change in
the probability that a language model complies with one designated
constraint when a different constraint in the same prompt is replaced by a
comparable alternative, with the number of constraints held fixed.

v3 declared two components of this phenomenon, the swap effect and the
exchangeability of the reference set (v3 §2). Its results report then
distinguished two readings of the swap effect, one against a frozen
reference set and one attributing the effect to the focal constraint's
identity, and ranked an unexecuted experiment separating target-specific
interference from generic constraint load first among remaining blockers
(v3 results report §4, §8). The three-quantity decomposition below is a v4
construction that makes that separation an estimand rather than a
reading.

Write $F_Y = 1$ when the verifier for outcome constraint $Y$ returns
failure. For a fixed outcome constraint $Y$, a fixed load of two, and a
frozen reference set $\mathcal{R} = \{R_1, R_2, R_3\}$:

$$\tau_Y \;=\; P\!\left(F_Y = 1 \mid Y + B\right) \;-\; \tfrac{1}{3}\sum_{j=1}^{3} P\!\left(F_Y = 1 \mid Y + R_j\right).$$

The three components are:

**Component 1, the swap effect on the target.** $\tau \equiv \tau_A$.
Replacing the reference set with the focal constraint changes target
compliance. This is the quantity v3 estimated.

**Component 2, generic constraint load.** $\tau_S$, the same swap measured
on an independent surrogate outcome constraint $S$ of identical structural
form. If $B$ is simply a heavier constraint than the references, it raises
failure of any outcome constraint of this form by about the same amount,
and $\tau_S \approx \tau$.

**Component 3, identity-specific interference.**

$$\iota \;=\; \tau \;-\; \tau_S .$$

The phenomenon name attaches to $\iota$ alone. Positive $\iota$ means the
focal constraint damages the target more than it damages a comparable
outcome constraint, which is interference attributable to the pairing
rather than to the added constraint's weight.

A fourth quantity is measured as a property of the design rather than of
the phenomenon: the **exchangeability** of the reference set, the spread
of failure rates among references intended to be interchangeable. v3
found it violated in both identified replications, so v4 treats it as a
gate on interpretation and as a reported design quantity.

---

## 3. Scope and excluded phenomena

The study measures the three components above for one target constraint,
one surrogate target constraint, one focal constraint, three references
drawn from distinct registered reference families, four language-model
replications, one registered decoding policy per model, one prompt
template, one language, one topic space, and a load of two constraints.
Every model produces a separate model-conditional result. The study
contains no pooled cross-model estimand and licenses no claim about models
in general.

Seven neighbouring phenomena fall outside the scope.

**Load-driven degradation.** The decrease in compliance caused by adding
constraints of any kind. Both compared prompts carry exactly two
constraints, so this quantity is held fixed and is not estimated. The
solo arms give descriptive increments over one constraint and carry a load
confound that is stated wherever they are reported.

**Logical impossibility.** Every composition used is certified jointly
satisfiable by an explicit witness before generation.

**Entailment and redundancy.** Every composition used is certified free of
entailment in both directions before generation.

**Mechanism.** The internal computation producing the behaviour. The
design measures behaviour under an intervention and is silent on internal
mechanism. $\iota$ localises interference to the pairing and does not
explain it.

**The reciprocal effect.** The effect of an outcome constraint on
compliance with the focal constraint. Composed uptake is recorded as a
manipulation check and is never analysed as a reciprocal estimand.

**Identity-specificity with respect to constraint form.** $S$ varies the
target word and holds the constraint form fixed, so $\iota$ identifies
specificity with respect to the outcome constraint's word and not with
respect to its form. §35 records this as an open extension.

**Generalisation.** Behaviour under other models, constraint families,
languages, loads, prompt formats, or inference policies. Each claim is
conditional on one registered model and its frozen configuration.
Repetition across the four models is reported as replication evidence,
without pooling.

---

## 4. Models, replication order, and inference policy

The four registered model replications, in execution order, are the four
v3 models. Two of them produced v3 confirmatory estimates and two
terminated at v3 Gate 2A; both outcomes are informative for v4 and neither
is carried forward as evidence about the effect.

| Execution order | Model label | Canonical repository | Registered interpretation |
|---:|---|---|---|
| 1 | Gemma 3n E2B-it | `google/gemma-3n-E2B-it` | Instruction-tuned Gemma replication and first test of the v4 reference system |
| 2 | Qwen3-4B hybrid, thinking disabled | `Qwen/Qwen3-4B` | Hybrid Qwen model evaluated with thinking disabled; not described as a pretrained-base model |
| 3 | Qwen3-4B instruct-only | `Qwen/Qwen3-4B-Instruct-2507` | Instruct-only Qwen replication |
| 4 | Gemma 3n E4B-it | `google/gemma-3n-E4B-it` | Instruction-tuned Gemma replication |

The exact repository revision for every model is entered in the signed
study-wide registration manifest before qualification and is asserted at
every generation. Revisions are re-pinned for v4 and are not inherited
from the v3 manifest. If a listed repository identifier is unavailable at
registration, v4 is not opened; changing a model identity requires a new
protocol version.

The inference policy is:

| Element | Value |
|---|---|
| Backend | vLLM, invoked through the scientific interpreter and exact command recorded in the registration manifest |
| Numeric precision | bfloat16 |
| Hardware | Model-specific GPU class and architecture recorded at qualification and held fixed within a replication |
| Temperature | 0.7 |
| Top-p | 0.9 |
| Top-k | 50, set explicitly |
| Thinking policy | Disabled for the Qwen3-4B hybrid model; unavailable or inactive for the other registered models |
| Maximum new tokens | Model-adaptive choice from $\{512, 768, 1024\}$ under the pre-screen rule of §18.2 |
| Ladder-screen draws per cell | $M_{\text{screen}} = 1$ |
| Calibration draws per cell | $M_{\text{cal}} = 4$ |
| Confirmatory cached draws per cell | $M = 8$ |
| Observations per cell | 1 cell mean over all $M$ cached draws |
| Seed | Derived from the fixed root seed, exact prompt hash, model identifier, and cached-draw index |
| Prompting | Zero-shot. No examples, tools, retrieval, self-consistency, best-of-N selection, revision passes, or additional turns |

Every cached draw of a confirmatory cell enters the cell mean. No hash
rule selects a privileged draw and no draw is discarded. The v3
primary-draw selection rule is retired; §13 gives the quantitative reason.

E2B runs first. If it terminates with `REFERENCE_POOL_MISMATCH`,
`COMPOSED_HEADROOM_FAILURE`, or `COMPOSED_UPTAKE_MISMATCH`, the remaining
three v4 replications do not start and any redesign requires v5.

Study-wide rules are frozen before E2B qualification. Outcomes from one
v4 replication cannot change the protocol for a later replication. Model
adaptation is confined to the mechanical selections of §18.

| Model-adaptive through §18 | Study-wide fixed before E2B |
|---|---|
| $n$, $k$, $m$, completion-token cap, one severity per eligible reference family, and the final identities of three references | Constraint families and severity ladders, the surrogate target and its grid, selection algorithms and tie-breakers, both calipers, number and structural diversity of references, estimands, equivalence regions, the precision precondition, multiplicity families, bootstrap, decoding-policy form, $M$, masking rules, gate rules, artifact semantics, and the claim ladder |

---

## 5. Constraints, surrogate target, and reference families

The target constraint is:

> **A:** Use the word *however* exactly $n$ times.

The surrogate target constraint is:

> **S:** Use the word *hence* exactly $k$ times.

The focal constraint is:

> **B:** Every word in the answer must have at most $m$ letters.

The registered grids are

$$n \in \{1,\dots,8\}, \qquad k \in \{1,\dots,8\}, \qquad m \in \{7,8,9,10\}.$$

**The focal floor is structural.** *however* has seven letters, so $m \ge 7$
is required for $A+B$ to be jointly satisfiable, and the focal grid cannot
extend below 7 while the target word is *however*. Both v3 replications
that reached selection chose $m^* = 7$, the most restrictive admissible
severity, at focal solo failure 0.188 and 0.240. The realised operating
point therefore sat on a grid boundary fixed by the target word's length.
This is recorded here because it is the mechanism the discriminating
design tests: at $m^* = 7$ the target word is the longest word the focal
constraint permits, while *hence* has five letters and sits two letters
inside the ceiling at every registered $m$. §35 records the alternative of
changing the target word as an open decision.

$A$ and $S$ never appear in the same prompt. Every prompt contains exactly
one outcome constraint.

The reference pool contains eight structurally distinct families. All
constraints are single-clause, apply to the whole answer, and are decided
by deterministic character operations. A word is a maximal run of
alphabetic characters. Suffix and letter tests use the lower-cased word.
Comma and upper-case counts operate on the raw response characters.

| Family | Identifier | Constraint template | Registered severity ladder |
|---|---|---|---|
| Initial-letter budget | RF1 | At most $q$ words in the answer may begin with the letter b. | $q \in \{0,1,\dots,8\}$ |
| Suffix budget | RF2 | At most $q$ words in the answer may end with the letters ing. | $q \in \{0,1,\dots,8\}$ |
| One-letter-word budget | RF3 | At most $q$ words in the answer may have one letter. | $q \in \{0,1,\dots,8\}$ |
| Doubled-letter budget | RF4 | At most $q$ words may contain two identical adjacent letters. | $q \in \{0,1,\dots,6\}$ |
| Comma budget | RF5 | The answer may contain at most $q$ comma characters. | $q \in \{0,1,\dots,12\}$ |
| Upper-case budget | RF6 | The answer may contain at most $q$ upper-case English letters. | $q \in \{0,1,\dots,12\}$ |
| Letter-a budget | RF7 | At most $q$ words in the answer may contain the letter a. | $q \in \{0,1,\dots,24\}$ |
| Final-y budget | RF8 | At most $q$ words in the answer may end with the letter y. | $q \in \{0,1,\dots,8\}$ |

The ladders contain 94 severities in total, against the 32 registered in
v3. The family maxima are the v3 grid maxima and are unchanged; v4 fills
the interior. The reason is recorded in §18.4: both v3 Qwen replications
terminated with exactly two admissible family severities where three were
required, and their family curves place the admissible region inside the
unmeasured interior of the v3 grids.

At most one severity level from a family can enter the final reference
set. The three final references must come from three different families.

Five properties are established before generation and asserted by
executable tests.

**Parse independence.** Each outcome verifier receives response text, its
own outcome-constraint identity, and its required count. It receives no
added-constraint identity, arm label, reference-family identity, or other
verifier's output. Each outcome scoring rule is identical in every arm in
which it runs.

**Joint satisfiability.** For every $n$, $k$, $m$, family, and ladder
severity, the protocol contains a machine-verified answer satisfying the
outcome constraint and the added constraint at the same time. Witnesses
are required for $A+B$, $A+R$, $S+B$, and $S+R$. Only compositions with a
verified witness can enter calibration or confirmation.

**Non-entailment.** For every eligible composition, the protocol contains
one verified response satisfying the outcome constraint and failing the
added constraint, and one satisfying the added constraint and failing the
outcome constraint.

**Wording equivalence.** Each of $A$, $S$, $B$, and each reference family
has four frozen wordings, written before qualification, checked for
identical meaning, and required to return identical verifier behaviour on
a fixed set of twenty test responses at every severity.

**Wording length.** Every wording of $S$ is within 20% of the
corresponding wording of $A$ in alphabetic-run word count, and every
wording of every reference family at every admitted severity is within 20%
of the corresponding focal wording. Severity parameters render as
numerals and contribute no words, so the caliper is severity-invariant.

---

## 6. Topics

The task space is short open-ended informational questions that a
competent writer can answer in sixty to one hundred and twenty words
without tools, arithmetic, or recall of a specific named fact.

The v4 topic bank contains 624 newly authored questions across the same
twelve declared subject areas as v3, with 52 questions per area: everyday
science, history, geography, food, music, sport, work and organisations,
health and the body, technology, language and writing, art and design, and
the natural world.

Questions are drafted by the researcher with model assistance and verified
one by one against four rules: answerable from general knowledge, no
single correct short answer, no reused text from any public dataset or
examination, and no wording that itself mentions any letter, word length,
word shape, punctuation-count, or capitalisation requirement.

**No v3 topic enters the v4 confirmatory set.** The 528 released v3 topics
are excluded because release with a canary string exposes them to
contamination (v3 §24, §31). The 96 v3 sequestered topics remain
sequestered and are not opened by v4; they stay available for a future
uncontaminated rerun of either protocol version. §35 records the
alternative of reusing the v3 bank as an open decision, with the condition
that it can be taken only if the v3 release has not occurred.

Within each subject area the 52 questions are randomly shuffled with a
fixed seed and split into 12 calibration questions, 32 confirmatory
questions, and 8 sequestered questions. The calibration split is divided
further into 2 pre-screen questions, 8 final solo-calibration questions,
and 2 composed-validation questions per area.

| Set | Topics | Permitted use |
|---|---:|---|
| Pre-screen | 24 | Completion-cap selection, dense severity-ladder screen, naturally generated Gate 1 validation material |
| Final solo calibration | 96 | Mechanical selection of $n$, $k$, $m$, and one candidate severity per reference family |
| Composed-reference validation | 24 | Headroom, reachability, and composed-uptake matching |
| Confirmatory | 384 | Frozen eleven-arm confirmatory experiment |
| Sequestered | 96 | Future uncontaminated rerun only |

The twelve procedural-pilot topics are one fixed topic from each subject
area in the pre-screen set. Pilot outputs are kept in a separate
namespace, no scientific quantity is computed from them, and later
pre-screen generations are new rows with new stage identifiers.

The sequestered topic texts remain inaccessible to the design and
execution team throughout v4. Their identities and pre-existing content
hashes may be held by the access-control process. Their text is opened
only under a separately registered future protocol version.

This is stratified random sampling: the task space is divided into twelve
declared strata, an equal number of items is authored per stratum, and
assignment to disjoint sets is random within stratum.

---

## 7. Prompt construction

Every prompt has the same three parts in the same order: the topic
question, a numbered list of the active constraints, and the line
`Answer:`.

Within a block and within one outcome constraint, the prompts being
compared are identical byte for byte except for the single line stating
the added constraint. The $A$-side and $S$-side prompts of a block differ
only in the line stating the outcome constraint, which occupies the same
list position in both.

Confirmatory block index $i$ determines three things, fixed across all
arms of that block:

- **Presentation order.** Blocks with even index place the outcome
  constraint first. Blocks with odd index place the added constraint
  first. This yields 192 blocks in each order.
- **Outcome wording.** The wording index for the outcome constraint is
  $i \bmod 4$, applied to $A$ in the $A$-side arms and to $S$ in the
  $S$-side arms.
- **Added wording.** The wording index for the added constraint is
  $\lfloor i/4 \rfloor \bmod 4$.

The 12-block pilot uses the stage-specific allocation
$w_{\text{outcome}}(i) = i \bmod 4$,
$w_{\text{added}}(i) = (i + \lfloor i/4 \rfloor) \bmod 4$, with
presentation order $i \bmod 2$.

Every generative stage has an executable allocation assertion stating the
intended count for every wording and order. A stage cannot start unless
its generated plan satisfies those counts. A formula is secondary to the
coverage assertion: if a formula and an assertion disagree, qualification
fails.

Both constraints occupy the same authority level, appearing in the same
numbered list in the same user message. No constraint is placed in a
system message.

---

## 8. Design

Each of the 384 confirmatory blocks is run under eleven arms.

| # | Arm | Prompt contents | Outcome scored | Purpose |
|---:|---|---|---|---|
| 1 | `AB` | Target and focal | $A$ | Treatment condition, target side |
| 2 | `AR1` | Target and reference 1 | $A$ | Comparison condition |
| 3 | `AR2` | Target and reference 2 | $A$ | Comparison condition |
| 4 | `AR3` | Target and reference 3 | $A$ | Comparison condition |
| 5 | `SB` | Surrogate and focal | $S$ | Treatment condition, surrogate side |
| 6 | `SR1` | Surrogate and reference 1 | $S$ | Comparison condition |
| 7 | `SR2` | Surrogate and reference 2 | $S$ | Comparison condition |
| 8 | `SR3` | Surrogate and reference 3 | $S$ | Comparison condition |
| 9 | `A` | Target only | $A$ | Headroom diagnostic |
| 10 | `S` | Surrogate only | $S$ | Headroom diagnostic |
| 11 | `TOPIC` | No constraints | $A$ and $S$ | Base rate of accidental compliance for both outcome constraints |

Arms 1 to 8 are the primary arms and all carry a load of two. Arms 9 to 11
carry a load of one or zero, sit at a different load, are excluded from
every contrast, and are reported as descriptive quantities.

Each arm defines one prompt cell per block. $M = 8$ cached stochastic
draws are generated for each cell and all eight enter the cell mean. Each
model therefore contains $384 \times 11 = 4{,}224$ confirmatory cells and
$4{,}224 \times 8 = 33{,}792$ cached draws. For comparison, v3 generated
36,864 cached draws per model across six arms and used 2,304 of them.

A sensitivity run repeats the eight primary arms on the first 96
confirmatory blocks under greedy decoding, giving a further 768
generations.

---

## 9. Outcomes and scoring rules

The primary outcome on the $A$ side is $F_A \in \{0,1\}$, target failure.
The primary outcome on the $S$ side is $F_S \in \{0,1\}$, surrogate
failure. Both use the same rule form.

The primary scoring rule, written $S_0$, is fixed here and applies
unchanged to every response in every arm in which its outcome constraint
is active:

1. Take the whole response text, including any preamble or trailing remark.
2. Convert it to lower case.
3. Find every maximal run of alphabetic characters.
4. Count the runs whose content equals the outcome constraint's target word.
5. Return pass when the count equals the required count, and failure otherwise.

Non-alphabetic characters act as run boundaries, so markdown emphasis,
quotation marks, and punctuation adjacent to the word leave the count
unchanged. The word-segmentation function and the $A$-side counting
function are byte-identical in source to the v3 instruments, which are
byte-identical in source to the v2 instruments that produced the carried
Gate 1 packet. The carry-over rule of §10 asserts this identity on every
load.

Failure includes every state that is not a pass: an incorrect count, an
empty response, a refusal, a response cut off by the token limit, and a
response the verifier cannot process. Removing these states would
condition the analysis on events the treatment can itself cause, so they
are retained as failures. Their frequencies are reported by arm and are
subject to the symmetry rule of §16.

Four alternative scoring rules are declared here and enter the robustness
family of §14. No further scoring rule enters the analysis.

| Rule | Definition | Difference from $S_0$ |
|---|---|---|
| $S_1$ | The same procedure without the lower-casing step | Treats capitalised and lower-case forms as different |
| $S_2$ | Count non-overlapping occurrences of the target word as a substring anywhere in the lower-cased text | Counts occurrences inside longer runs of letters |
| $S_3$ | Apply $S_0$ after deleting any leading line ending in a colon and any line repeating the constraint text | Excludes preamble and instruction restatement from the count |
| $T_1$ | Pass when the $S_0$ count differs from the required count by at most one | Treats a near miss as compliance |

The graded quantity $|\text{count} - \text{required}|$ and the signed
quantity $\text{count} - \text{required}$ are recorded for every response.

**Near-miss decomposition.** The failure indicator decomposes exactly:
failure under $S_0$ equals failure under $T_1$ plus near-miss failure.
Therefore

$$\tau \;=\; \tau^{\text{near-miss}} \;+\; \tau^{T_1},$$

and the same identity holds for $\tau_S$ and $\iota$. Both components are
registered members of the robustness family. The decomposition is
registered because the v3 unregistered re-analysis showed that near-miss
failures are 67% to 85% of all failures in every arm and that both E2B
signs flip when they are discounted, while the E4B positive tendency
survives and strengthens.

---

## 10. Verifiers, reliability, and validity

Each outcome verifier receives the response text and its own outcome
constraint identity. It receives no arm label, no information about which
constraint occupied the added slot, and no output from any other verifier.
The same code path runs in every arm.

Secondary verifiers score the added constraint in each primary arm,
producing composed uptake. Every verifier is deterministic, reads the
response text alone, and requires no model access. No language model
judges any scored outcome. No human rating produces a primary score.

The measurement record answers five questions and each answer is fixed
before generation.

| Question | Answer |
|---|---|
| What is the construct | Compliance with an outcome constraint, defined as the response containing its target word exactly the required number of times |
| What measure operationalises it | The scoring rule $S_0$ of §9, implemented as a deterministic program |
| Selected from prior work or created here | Created in this programme. The $A$-side instrument is carried forward byte-identically from v3 and v2 under the carry-over rule below; the $S$-side instrument is the same function applied to a different word |
| Any modification, and when | The scoring rules are fixed at freeze. Any change after freeze creates a new protocol version and the original result is reported unchanged |
| How the measure is quantified, and when that was decided | Binary pass or failure under $S_0$, with four alternatives declared as a robustness family, all decided before any confirmatory generation |

### 10.1 Three validation questions, kept separate

v3 established that one criterion cannot answer all three, because its
single human-agreement bound was driven entirely by human arithmetic at
the off-by-one boundary. v4 registers three separate answers with three
separate criteria, and no result of one is reported as evidence for
another.

**Question 1: does the program implement the registered rule?** Answered
mechanically.

- *Determinism.* Every verifier is executed three times on every
  calibration response, once on each of three separate processes. The
  recorded agreement is the proportion of responses receiving identical
  verdicts across all three executions. The required value is 1.000.
- *Boundary suite.* Every verifier passes a frozen forty-case suite
  covering empty response, adjacent punctuation, capitalisation,
  hyphenation, target text inside a longer word, repeated words,
  non-Latin characters, and truncation mid-word. The $A$-side case texts
  and their $S_0$ to $S_2$ expectations are carried byte-identically from
  v3. The $S$-side suite is the same forty constructions on the surrogate
  word with hand-derived expectations frozen before qualification.
- *Independent reimplementation.* A second implementation of each outcome
  rule is written from the registered prose of §9 by a process that does
  not read the primary implementation's source. It is run on every
  calibration response and on the whole boundary suite. Required agreement
  with the primary implementation is 1.000, and any disagreement blocks
  Gate 1. This test is registered because the v3 forensic review used
  exactly this device after the fact and found 235 of 235 field
  disagreements to be judge-side rather than verifier-side.
- *Carry-over.* The $A$-side instrument may supply carried evidence only
  when the construct string, the word-segmentation function source, the
  counting function source, and the forty boundary case texts with their
  expectations are byte-identical to the v3 artifacts. The carry-over
  record names the source packet, records every hash, and refuses on any
  mismatch.

**Question 2: can an independent human reproduce the rule?** Answered by
blinded human labels under a tool-assisted counting protocol.

- *Annotator.* At least one annotator independent of the design and
  analysis team, adult and fluent in English. The labelling question is
  whether a given letter sequence appears a given number of times in a
  given text, which is a decidable property of the text.
- *Interface.* The annotator reads the response and the outcome constraint
  text and marks each occurrence of the target word. The interface tallies
  the annotator's own marks and displays the running tally. The interface
  performs no automatic detection, highlighting, counting, or
  normalisation of the target word, and shows no arm, model label, added
  constraint, verifier verdict, item identity, or other annotator's work.
  The label is derived as pass when the marked count equals the required
  count. Rationale: all four v3 human-verifier disagreements were human
  off-by-one miscounts at a margin of one, reproduced against the verifier
  by four independent recounts, so the v3 bound measured unaided human
  arithmetic rather than the instrument.
- *Sampling.* Naturally generated pre-screen and dedicated
  measurement-validation responses form a reservoir before human labels
  are opened. If either verifier class contains fewer than 150 cases, the
  pipeline generates a frozen set of up to 300 additional
  measurement-validation responses across the registered grids. Within
  each verifier class a fixed seeded sample of $\min(150, N_c)$ responses
  is drawn. Hand-authored responses cannot fill a natural-response class.
- *Criterion.* The one-sided 95% Wilson upper bound on
  human-to-verifier disagreement is at most 0.10 in each verifier class.
  Within the verifier-fail class the bound is additionally computed
  separately on items whose $S_0$ count differs from the required count by
  exactly one and on items whose margin is larger, and both must be at
  most 0.10. This sub-criterion is registered because the v3 fail-class
  disagreements were wholly concentrated at margin one, four of
  forty-four, with none at larger margins.
- *Statuses.* A measured excess returns `MEASUREMENT_NOT_ESTABLISHED`. An
  exhausted natural class that cannot reach the criterion returns
  `MEASUREMENT_EVIDENCE_INSUFFICIENT`. Unavailability of an independent
  annotator returns `HUMAN_VALIDATION_UNAVAILABLE` and routes measurement
  to §10.2 without waiving the criterion.

**Question 3: does exact-count compliance operationalise the intended
construct?** Answered by a registered construct-discordance probe rather
than left open.

A deterministic detector classifies every counted occurrence in every
confirmatory response into one of five types, in priority order:

| Order | Type | Detection rule |
|---:|---|---|
| 1 | Instruction restatement | The occurrence lies on a line whose character overlap with an active constraint wording exceeds 0.60 under the frozen similarity function |
| 2 | Quoted material | The occurrence lies inside a paired quotation span under the frozen span rule |
| 3 | Metalinguistic mention | The occurrence is immediately preceded or followed within two words by one of a frozen list of mention markers, for example *the word*, *the term*, *spelled* |
| 4 | Enumeration | The occurrence lies on a line that is a list item containing no other alphabetic run of more than three letters |
| 5 | Ordinary use | No rule above applies |

The share of responses containing at least one occurrence of types 1 to 4
is reported per arm, and the focal-to-reference difference in that share
is a registered diagnostic with a simultaneous interval. When any such
difference exceeds 0.05 with its interval excluding zero, every Tier 1
statement carries a fixed construct-scope interpretation block. Rationale:
v3 stored a single quoted-mention discordant case as an open construct
question with no measurement attached, and an arm-differential discordance
rate is a threat to the contrast rather than only to the level.

### 10.2 Autorater-assisted verifier development

When Question 2 returns `HUMAN_VALIDATION_UNAVAILABLE`, verifier
development and held-out evaluation proceed against a configured
autorater. This pathway is registered here in the form v3 reached through
amendments A2, A2.1, A2.2, A3, A3.1, and A3.2. It is a proxy instrument.
It is never human validation, never ground truth, and never scores a study
outcome.

1. *Response pool and split.* The pool is the pre-screen outcome-solo
   responses plus the frozen validation responses. A deterministic
   seeded split, stratified by verifier class, produces disjoint
   development and calibration halves.
2. *Development.* The boundary suite, three-process determinism, the
   independent reimplementation, the frozen human packet, and one
   configured autorater judge the development half. A complete
   disagreement listing is produced for researcher inspection. Verifier
   refinement is permitted here and must be encoded in regression tests.
   A repeat run of the identical development items under the identical
   configuration reports label flips, operational-status changes, and
   affected item identities; instability under greedy decoding blocks the
   freeze.
3. *Judge configuration.* One judge model resolved through a registry
   deliberately disjoint from the registered study models, at a pinned
   revision, with a hashed configuration recording judge key, identifier,
   revision, backend identity, prompt version and hash, parser version,
   the binary label mapping, decoding settings, reasoning budget, and
   token cap. Configuration drift fails closed. Stored judge rows carry
   their producing configuration hash and refuse reuse under a different
   configuration. The judging condition is selected before the freeze on
   scratch material only, never on pool or calibration data, under a
   registered decision rule over accuracy, coverage, stability, failure
   modes, and cost. A superseded round is parked under an audited
   supersession that deletes nothing.
4. *Freeze.* A study-level single-shot signed manifest binds verifier
   source hashes, the regression-test file hash and its passing run, the
   producing commit, the split derivation, the autorater configuration,
   and the realised evidence boundary per model, namely the response-pool
   hash, split hash, and development-record hash. The freeze refuses until
   every registered non-terminal model replication has completed
   development, and calibration and approval re-verify all bindings.
5. *Calibration.* The same autorater judges the untouched calibration
   half. The report gives totals, valid and invalid outputs with distinct
   operational statuses never recoded into labels, coverage, both
   marginals, total and directional disagreement, the complete
   contingency table, the full-set agreement identification interval, and
   the complete disagreement case listing. No automatic acceptance
   threshold exists and the human Wilson rule is not reused. Calibration
   is one-shot, enforced through an append-only ledger written before any
   mutation; a contaminated calibration requires genuinely new untouched
   response data.
6. *Approval and marking.* Explicit researcher approval writes the Gate 1
   record with `measurement_basis = autorater_calibration_approved`,
   distinct from `human_validated`. Readiness reporting, the confirmatory
   freeze, and every analysis record read the effective human-validation
   status through one helper and never through a bare stage status.

The registered strongest supported claim under this pathway, attached
verbatim to gate, freeze, and analysis outputs, is: *The frozen
deterministic verifier was developed and evaluated on held-out responses
against the specified autorater under the registered configuration.
Independent human validation is unavailable.*

### 10.3 Item behaviour

Outcome failure is tabulated by topic during calibration and confirmation.
The recorded numbers are the proportion of topics at floor, the proportion
at ceiling, and, after confirmation, the proportion whose cell means are
identical in every primary arm of a side. This is a regime and precision
diagnostic, not a Gate 1 criterion.

### 10.4 Validity arguments

**Face validity.** Annotators independently judge whether the plain-language
statement of $S_0$ matches the constraint text as written. The recorded
number is the count of agreements.

**Content validity.** The boundary suite enumerates one case for each way
the requirement could be ambiguous. The recorded number is the count of
enumerated cases the verifier handles as specified.

**Convergent validity.** The human agreement test of Question 2 supplies an
independent measurement of the same requirement.

**Discriminant validity.** Two checks. First, an assertion that each
outcome verifier's inputs exclude the arm label, the added-constraint
identity, and every other verifier's output. Second, the parse-independence
property of §5.

**Ecological validity.** The prompt format resembles a request accompanied
by written rules. The character-level rules are chosen for exact
decidability, and §31 records the resulting limit on realism.

---

## 11. Estimands

### 11.1 The observation

For confirmatory cell $c$ with $M$ cached draws, the **cell mean** is

$$\bar F_c \;=\; \frac{1}{M}\sum_{j=1}^{M} F_{c,j},$$

where $F_{c,j}$ is the outcome failure indicator of draw $j$ under $S_0$.
$\bar F_c$ estimates $P(F = 1 \mid \text{cell } c)$ under the registered
decoding policy. Every registered estimand is defined on cell means.

Draws are averaged inside the cell. The block remains the only resampling
unit and the only independent unit. Averaging within a cell does not
create additional independent observations and does not enter any
sample-size statement as such; it reduces the measurement error of each
cell, which §13 quantifies.

### 11.2 Block contrasts

Write $\bar F_{i,q}$ for the cell mean in block $i$ under arm $q$.

$$D^A_i \;=\; \bar F_{i,\mathrm{AB}} \;-\; \tfrac{1}{3}\left(\bar F_{i,\mathrm{AR1}} + \bar F_{i,\mathrm{AR2}} + \bar F_{i,\mathrm{AR3}}\right),$$

$$D^S_i \;=\; \bar F_{i,\mathrm{SB}} \;-\; \tfrac{1}{3}\left(\bar F_{i,\mathrm{SR1}} + \bar F_{i,\mathrm{SR2}} + \bar F_{i,\mathrm{SR3}}\right),$$

$$\Delta_i \;=\; D^A_i \;-\; D^S_i .$$

### 11.3 Primary estimands

Three primary estimands are declared per model replication, each computed
over all 384 confirmatory blocks:

$$\tau = \mathbb{E}\!\left[D^A_i\right], \qquad \tau_S = \mathbb{E}\!\left[D^S_i\right], \qquad \iota = \mathbb{E}\!\left[\Delta_i\right] = \tau - \tau_S .$$

$\tau$ is the swap effect on the target. $\tau_S$ is the generic
constraint-load component. $\iota$ is the identity-specific component and
is the quantity the phenomenon name attaches to.

Presentation order is a designed factor, balanced 192 blocks per order,
and enters as a registered order-interaction family rather than by
splitting the primary estimands. v3 declared two order-conditional primary
estimands and halved the blocks behind each. Its realised order
interactions were +0.0330 for E2B and +0.0503 for E4B, one below and one
marginally above the registered exchangeability margin of 0.05. v3
registered no threshold and no simultaneous interval for this quantity,
listing it among those reported with marginal intervals and supporting no
claim, and its result records carry the interaction as a bare scalar. v4
registers it as a family member with an interval and a gate, so the
quantity that decided v3's estimand structure now carries a registered
decision rule. §13 gives the precision consequence and §14 the gate.

### 11.4 Identification assumption for $\iota$

Write the interference of added constraint $X$ on outcome constraint $Y$
as $\iota(X \to Y)$ and decompose it into an additive interferer term, an
additive vulnerability term, and a pair term:

$$\iota(X \to Y) \;=\; \alpha_X + \beta_Y + \gamma_{XY}.$$

Then $\tau = \alpha_B - \bar\alpha_R + \gamma_{BA} - \bar\gamma_{RA}$ and
$\tau_S = \alpha_B - \bar\alpha_R + \gamma_{BS} - \bar\gamma_{RS}$, so

$$\iota \;=\; \left(\gamma_{BA} - \gamma_{BS}\right) - \left(\bar\gamma_{RA} - \bar\gamma_{RS}\right).$$

Both the interferer strength of $B$, the average interferer strength of
the reference set, and the vulnerability of each outcome constraint cancel.
$\iota$ equals the pair-specific term $\gamma_{BA}$ under one registered
assumption:

> **A1 (reference neutrality).** The reference set carries no
> pair-specific term with either outcome constraint, and the focal
> constraint carries no pair-specific term with the surrogate:
> $\bar\gamma_{RA} = \bar\gamma_{RS} = \gamma_{BS} = 0$.

A1 is not testable inside this design and is stated as an assumption
wherever $\iota$ is interpreted as $\gamma_{BA}$. Two registered
quantities bear on it. The exchangeability family bears on
$\bar\gamma_{RA}$: heterogeneity among references intended to be
interchangeable is evidence that reference-side pair terms are non-zero.
The composed-uptake family bears on whether the compared constraints
reached the model at comparable rates. Under A1's failure, $\iota$ remains
a well-defined registered contrast and is interpreted as the difference
between the swap effect on the target and the swap effect on the
surrogate, with no attribution to a pair term.

### 11.5 Design quantities

Three exchangeability contrasts are declared on each side, computed over
all 384 blocks:

$$\delta^Y_{jk} = \mathbb{E}\!\left[\bar F_{i, YR_j} - \bar F_{i, YR_k}\right], \qquad (j,k) \in \{(1,2),(1,3),(2,3)\}, \quad Y \in \{A, S\}.$$

### 11.6 Thresholds

The smallest effect of interest is a risk difference of 0.10 for every
primary estimand. A change of that size converts a system prompt with 80%
outcome compliance into one with 70%, which is one additional failure in
every ten responses. This value is carried unchanged from v3 and is a
substantive judgment about meaningfulness; it is not adjusted in the light
of v3's realised effect sizes.

The exchangeability margin is 0.05. The precision precondition is
$\text{SESOI}/2 = 0.05$: an equivalence claim additionally requires the
realised simultaneous half-width to be at or below 0.05. §15 gives the
rule and §13 the projection showing it is attainable.

Let $\bar p_R$ be the mean composed-reference failure probability on a
side. Because a swap effect lies in $[-\bar p_R, 1 - \bar p_R]$, effects of
both $-0.10$ and $+0.10$ are reachable only when
$\bar p_R \in [0.10, 0.90]$. Gate 2B uses the buffered requirement that
every composed rate lies in $[0.15, 0.85]$ on both sides.

---

## 12. Unit of analysis and clustering structure

The block is the unit at four levels.

| Role | Statement |
|---|---|
| Assignment | Presentation order and both wording indices are assigned at the block and are identical across the eleven arms of that block |
| Pairing | Focal and reference arms are compared inside a block on the same side, and the two sides are compared inside a block, so between-topic variation is removed from every contrast |
| Clustering | The bootstrap resamples blocks. When a block is drawn, all eleven of its cell means travel with it, preserving the correlation induced by the shared topic |
| Generalisation | Uncertainty statements refer to the population of topics defined in §6 |

Responses are nested inside cells and cells inside blocks. Eleven cell
means exist per block and are correlated because they share a topic, an
order, and a wording. Resampling cells or responses individually would
treat them as independent and would understate uncertainty, so neither is
ever the resampling unit.

Four executable checks enforce this structure.

**Resampling unit.** Each bootstrap replicate draws exactly 384 block
identifiers with replacement, stratified 192 and 192 by presentation
order. The analysis asserts that the number of identifiers drawn equals
the stratum size and that every drawn identifier carries eleven cell means.

**Function signature.** Every estimator receives a table indexed by block.
The analysis asserts that no estimator function accepts a response-level
or draw-level index.

**Draw completeness.** The analysis asserts that every confirmatory cell
carries exactly $M$ committed accepted draws before any cell mean is
formed, and fails closed on any cell with fewer. No cell mean is formed
from a partial draw set and no missing draw is imputed.

**Variance behaviour.** A synthetic dataset is generated in which
within-cell draw noise is doubled and between-block variation is held
fixed. The analysis asserts that the interval width for the block-level
mean grows by the amount predicted by the registered decomposition of §13
and that the block component of the reported variance is unchanged.

---

## 13. Sample size, precision, and what the design can detect

### 13.1 Planning quantities

Smallest effect of interest 0.10, target power 0.80, two-sided
significance level 0.05, block as the independent unit, 384 confirmatory
blocks per model, 192 blocks in each presentation order, three primary
estimands in one family.

### 13.2 The v3 variance decomposition

v3 recorded the two quantities needed to decompose the block-level
variance of a swap contrast. The block bootstrap standard error of E2B
$\tau_{\text{target-first}}$ was 0.03901 on 192 blocks, giving a per-block
contrast variance of $0.03901^2 \times 192 = 0.2922$. The registered
pseudo-selection diagnostic re-ran the same estimator 1,000 times under
alternative draw selections from the same frozen cache. The v3 report gives
a standard deviation of about 0.036 to 0.039 as a property of the
primary-draw lottery across the study, and reports the E2B target-first
pseudo distribution through its mean of +0.089 and its fifth percentile of
+0.030, which imply 0.0359 under a normal approximation. That approximation
is an assumption of this projection and is not required by anything
registered here. The implied standard deviation is the draw-selection
component of the same per-block variance, giving $\sigma^2_{\text{draw}} = 0.0359^2 \times 192 \approx 0.247$ and
therefore $\sigma^2_{\text{block}} \approx 0.045$.

Approximately 85% of the per-block variance of the v3 contrast was
stochastic decoding noise from a single retained draw. This is the
quantitative reason the v3 design could not resolve effects of the size
its own diagnostics suggested.

The decomposition is a projection with three stated sources of
uncertainty. It uses one model and one order stratum; the pseudo-run
standard deviation is reported as a range and its upper end implies a
block component near zero, which is implausible and bounds the projection
optimistically; and the finite cache of sixteen draws makes the
re-selection variance a slight underestimate of the true draw variance.
§18.6 requires the decomposition to be recomputed on the v4 cache before
any claim of achieved precision is made, and §35 records recomputation on
the v3 cache before freeze as an open pre-registration input.

### 13.3 Projected precision under the v4 estimator

With cell means over $M$ draws and $n_b$ blocks, the per-block contrast
variance is $\sigma^2_{\text{block}} + \sigma^2_{\text{draw}}/M$ and the
standard error is the square root of that quantity divided by $n_b$. Using
the decomposition above:

| Design | $M$ | Blocks | Family size | SE | Simultaneous half-width | Detectable effect at 80% power |
|---|---:|---:|---:|---:|---:|---:|
| v3 as executed | 1 | 192 | 2 | 0.0390 | 0.0868 | 0.1196 |
| v4 primary $\tau$ | 8 | 384 | 3 | 0.0141 | 0.0336 | 0.0454 |
| v4 primary $\tau$ | 16 | 384 | 3 | 0.0126 | 0.0300 | 0.0405 |
| v4 primary $\iota$ | 8 | 384 | 3 | 0.0199 | 0.0475 | 0.0642 |
| v4 primary $\iota$ | 16 | 384 | 3 | 0.0177 | 0.0424 | 0.0573 |

Critical values for the v4 rows use the Šidák bound for a family of
three, 2.388; the bootstrap supplies the exact value, which is smaller
because the three members are linearly dependent. The v3 row uses that
replication's realised bootstrap critical value of 2.2253 and reproduces
its realised simultaneous half-width of 0.0868. The $\iota$ projection
assumes zero correlation between the two sides' contrasts within a block,
which is conservative: any positive correlation reduces its variance, and a
correlation of 0.2 lowers the $\iota$ half-width at $M = 8$ to 0.042.

Three consequences are registered.

1. At $M = 8$ the projected half-width for $\tau$ and $\tau_S$ is 0.034,
   inside the 0.05 precision precondition, so both a meaningful-magnitude
   conclusion and an equivalence conclusion are reachable.
2. At $M = 8$ the projected half-width for $\iota$ is 0.048, just inside
   the precondition, and its detectable effect at 80% power is 0.064.
   Identity-specific components below roughly 0.06 will be unresolved.
   Reaching a detectable effect of 0.05 for $\iota$ requires about 633
   blocks and of 0.04 about 989 blocks, which the registered topic bank
   does not supply. This is a declared limitation, not a contingency.
3. Increasing $M$ beyond 8 improves $\tau$ by about 11% and $\iota$ by
   about 11% at 2× the generation cost, because the block component then
   dominates. $M = 8$ is registered on that basis and because it makes
   the eleven-arm confirmatory stage cost 33,792 generations per model
   against v3's 36,864.

### 13.4 Why the order estimands are pooled

v3 declared two order-conditional primary estimands, which halved the
blocks behind each and raised the family size to two. Pooling to one
estimand over 384 blocks with order retained as a balanced designed factor
improves the standard error by a factor of $\sqrt{2}$. v3's realised order
interactions were +0.0330 for E2B and +0.0503 for E4B, one below and one
marginally above the registered exchangeability margin, and v3 registered
neither a threshold nor a simultaneous interval for the quantity. §14
registers the interaction as a family member with an interval and an
interpretation gate, so an order effect remains detectable and reportable
without costing the primary quantity half its blocks.

### 13.5 Excluded planning sources

No effect estimate from v3 or any earlier work in this programme sets the
sample size. The v3 recorded quantities set only the variance
decomposition used for the precision projection, which is a
noise-structure quantity and not an effect. No effect estimate from
calibration sets the sample size, and no focal-to-reference outcome
contrast is computed on calibration data at any point. The procedural
pilot computes no contrast.

### 13.6 Realised precision reporting

Realised block-level discordance, the realised variance decomposition, the
achieved detectable effect implied by it, and the realised simultaneous
half-width are reported beside every primary estimate. The single-draw
equivalent standard error, namely the standard error the v3-style
estimator would have had on the same data, is reported as a registered
diagnostic so that the precision gain is auditable.

---

## 14. Multiplicity families

Every quantity carrying an inferential statement belongs to exactly one
family declared here within one model replication. The list is closed at
that model's freeze. No quantity moves between families afterwards. Any
quantity computed and absent from this list is exploratory and is labelled
exploratory in every report. The four model replications are reported
separately; this protocol defines no cross-model multiplicity family.

| Family | Members | Size | Status |
|---|---|---:|---|
| F1 Primary | $\tau$, $\tau_S$, $\iota$ | 3 | Primary. Supports a Tier 1 claim under §15 |
| F2 Order | The order interaction of $D^A$, of $D^S$, and of $\Delta$ | 3 | Gate on the pooling interpretation |
| F3 Exchangeability | $\delta^A_{12}, \delta^A_{13}, \delta^A_{23}$ | 3 | Gate on the Tier 2 identity-specific claim |
| F4 Per reference | $\mathbb{E}[\bar F_{i,YB} - \bar F_{i,YR_j}]$ for each reference on each side | 6 | Secondary. Diagnostic for reference disagreement |
| F5 Scoring robustness | $\tau$ and $\iota$ under $S_1$, $S_2$, $S_3$, and $T_1$, plus the near-miss components $\tau^{\text{near-miss}}$ and $\iota^{\text{near-miss}}$ | 10 | Secondary. Sensitivity to the scoring rule and to the near-miss boundary |
| F6 Failure categories | The focal-to-reference difference in the rate of each of the nine categories of §23, on the target side | 9 | Secondary. Locates which failure type drives any contrast |
| F7 Apparatus symmetry | The focal-to-reference difference in non-behavioural failure rate for each reference on each side | 6 | Gate on the interpretation rule of §16 |
| F8 Manipulation check | The focal-to-reference difference in composed uptake for each reference on each side | 6 | Gate on the dose-mismatch interpretation block |
| F9 Construct discordance | The focal-to-reference difference in the construct-discordant occurrence share on each side | 6 | Gate on the construct-scope interpretation block |
| F10 Exchangeability, surrogate side | $\delta^S_{12}, \delta^S_{13}, \delta^S_{23}$ | 3 | Secondary. Reports reference behaviour on the surrogate side |

Each family receives its own simultaneous 95% interval, computed by
standardising each member by its bootstrap standard error and taking the
largest absolute standardised deviation across the family in each
resample. Marginal intervals are reported alongside, and the decision
rules use the simultaneous intervals.

**Order gate.** When the absolute order interaction of $D^A$ exceeds 0.05
with its F2 simultaneous interval excluding zero, $\tau$ is reported with a
fixed interpretation block stating that the pooled estimand averages two
materially different order-conditional quantities, and the two
order-conditional means are reported as registered secondaries with
marginal intervals. The pooled estimand itself stands unchanged, because
it is defined over the registered balanced order distribution. The same
rule applies to $\tau_S$ and $\iota$ through their own F2 members.

Quantities reported with marginal intervals and no simultaneous statement,
supporting no claim of any kind: the order-conditional means, joint
compliance, outcome failure by subject area, outcome failure by wording
index, the outcome-alone rates, the topic-alone rates, composed and solo
response-length quantiles by arm, the greedy replication, the pseudo-run
distribution, the variance decomposition, and the human-written baseline.

---

## 15. The claim ladder

Five tiers are registered. Every emitted statement carries the machine
fields `tier`, `family`, `interval_type`, and `measurement_basis`, and is
produced by the guarded emitter of its tier.

### Tier 0, measurement premises

Statuses only, never an effect statement. Tier 0 records verifier
determinism, boundary-suite result, independent-reimplementation
agreement, the human-agreement bound per verifier class with the fail-class
margin split, the measurement basis marker, the construct-discordance
result, and the registered scope sentence. No Tier 1 or Tier 2 statement
may be emitted while Tier 0 is unresolved, and every Tier 1 and Tier 2
statement carries the Tier 0 basis string verbatim.

### Tier 1, registered confirmatory effects

The three F1 members under the fixed vocabulary below. Direction and
magnitude are separate interval-based axes evaluated for each member.

| Axis | Condition | Fixed interpretation |
|---|---|---|
| Positive direction | The simultaneous lower bound exceeds zero | Failure is higher under the focal constraint than under the reference average |
| Negative direction | The simultaneous upper bound is below zero | Failure is lower under the focal constraint than under the reference average |
| Direction unresolved | The simultaneous interval includes zero | The direction is unresolved at the registered simultaneous confidence level |
| Meaningful positive magnitude | The simultaneous lower bound exceeds $+0.10$ | The positive effect exceeds the smallest effect of interest |
| Meaningful negative magnitude | The simultaneous upper bound is below $-0.10$ | The negative effect exceeds the smallest effect of interest in magnitude |
| Equivalence | The simultaneous interval lies wholly inside $[-0.10, +0.10]$ **and** its half-width is at most 0.05 | Any effect present is smaller than the smallest effect of interest, at adequate precision |
| Insufficient precision | The simultaneous half-width exceeds 0.05 | The design did not achieve the registered precision for this member; equivalence is withheld and a resolved direction is still reported |
| Magnitude unresolved | None of the conditions above holds | The study does not determine whether the effect exceeds the smallest effect of interest |

The precision precondition on equivalence is registered because v3's only
resolved claim was an equivalence licensed by a simultaneous interval of
half-width 0.087 whose point estimate happened to fall within 0.013 of
zero, and re-centring that interval on the same estimand's across-draw
mean of +0.089 yields [+0.002, +0.176], which the same rule emits as a
resolved positive direction with no equivalence.

Failure to exclude zero is never reported as absence.

### Tier 2, registered conditional upgrades

| Claim | Licensing conditions | Licensed statement |
|---|---|---|
| Identity-specific interference | $\iota$ direction resolved, all three F3 exchangeability intervals inside $\pm0.05$, no F8 member flagged, and Gate 2B's composed-uptake predicate satisfied | The focal constraint changes target failure by more than it changes failure of a comparable outcome constraint, under assumption A1 of §11.4 and the registered conditions |
| Generic constraint load | $\tau$ and $\tau_S$ both direction resolved with the same sign, and $\iota$ meeting the equivalence conditions of Tier 1 | The focal constraint changes outcome failure by an amount that does not depend on which of the two registered outcome constraints is measured, to within the smallest effect of interest |
| Swap effect only | $\tau$ direction resolved with any Tier 2 condition above unmet | Replacing the reference set with the focal constraint changed target failure under the registered conditions, against this frozen reference set |

### Tier 3, registered diagnostics

Families F4 to F10, composed uptake, solo increments, greedy replication,
pseudo-run distribution, variance decomposition, per-arm lengths, finish
reasons, failure categories, item behaviour, and every quantity listed in
§22. Tier 3 statements describe. They never assert an effect and never
qualify as evidence for a Tier 1 or Tier 2 claim.

### Tier 4, exploratory

Any quantity computed outside this document, including unregistered
re-analysis of registered rows. Always labelled exploratory, always
reported after the registered result, and never able to change a
registered outcome.

### Executable enforcement

1. Every claim string is drawn from the fixed vocabulary above.
2. Any string asserting absence, equivalence, or negligibility is produced
   by a single function whose precondition is that the simultaneous
   interval lies inside the declared region and that its half-width is at
   most 0.05. The analysis aborts when that function is reached with the
   precondition false. This generalises the v3 guarded emitter.
3. One emitter exists per tier. Each refuses a member name that is not
   registered to its tier, so a Tier 3 quantity name cannot appear inside
   a Tier 1 or Tier 2 statement.
4. Every emitted statement carries the four machine fields, and an
   executable check refuses a statement missing any of them.

---

## 16. Manipulation checks, compliance checks, and arm symmetry

Six checks run on the confirmatory data. Every one is computed separately
from the primary estimates. None is a covariate, a filter, a stratifier,
or a weight in any primary formula.

**Manipulation check: treatment delivery.** Composed uptake of the added
constraint is computed per arm. The recorded quantities are uptake in each
primary arm and the focal-to-reference difference on each side, family F8,
with simultaneous intervals. When any absolute difference exceeds 0.25
with its interval excluding zero, the affected primary estimates are
reported with a fixed interpretation block stating that the compared arms
delivered their treatments at materially different rates. The estimates
themselves stand unchanged, because they are intention-to-treat quantities
and conditioning on uptake would select on a consequence of the treatment.
Gate 2B additionally refuses references whose composed uptake is far from
the focal constraint's before confirmation begins, so this check is a
residual monitor rather than the primary defence. Rationale: in v3 all
three E4B references were flagged, at focal uptake 43.8% against 7.3%,
4.2% and 9.9%, and E2B's third reference was flagged at 2.1% against
35.7%.

**Compliance check: normal operating conditions.** Response length in
words and tokens, finish reason, and whether generation reached the token
limit are recorded for every cached draw. Responses of three words or
fewer and responses reaching the token limit are flagged. Flag rates and
finish-reason counts are reported per arm. Response-length quantiles
$p_{50}$, $p_{90}$, $p_{95}$, $p_{99}$ are standard outputs of every
generative stage.

**Compliance check: per-arm truncation.** Truncation is evaluated per arm
against the registered ceiling of 0.10. Any primary arm exceeding it is
reported with a fixed interpretation block. Any diagnostic arm exceeding it
is reported, and the quantities derived from that arm are reported as
bounds. Rationale: in v3 the unconstrained arm truncated in 322 of 384 E2B
responses and 333 of 384 E4B responses, and the E4B target-alone arm
truncated in 47 of 384, above the ceiling, with no per-arm rule attached.

**Compliance check: instrument function.** The verifier version hash and
the model revision recorded on every row are compared against the freeze
record. Any mismatch aborts the run under §27.

**Compliance check: outcome feasibility.** The outcome-alone arms give solo
failure on confirmatory topics for $A$ and for $S$. A value outside the
Gate 2A admission band is reported beside the primary estimates, because
it shows the confirmatory topics differ in difficulty from the calibration
topics.

**Arm symmetry of non-behavioural failures.** The non-behavioural failure
rate for an arm is the proportion of its cached draws that are empty, that
stopped at the token limit, or that the verifier could not process.
Focal-to-reference differences form family F7.

Two consequences follow.

When every absolute difference in F7 is at or below 0.05, or its
simultaneous interval includes zero, the primary estimates are reported
without qualification.

When any absolute difference exceeds 0.05 with its simultaneous interval
excluding zero, the primary estimates are reported with a fixed
interpretation block stating that part of the contrast reflects a
difference in how often a response was scorable, and partial
identification bounds are computed: each primary estimand is recalculated
twice, once treating every non-behavioural draw as an outcome pass and once
treating every one as an outcome failure. Both recalculations use full
simultaneous intervals, and a claim is licensed only when both
recalculations license the same claim; otherwise the axis is reported
unresolved with both bounds. This is the conservative reading v3 adopted
in its registered implementation decision V12 and it is registered here
directly.

**Composed comparability report.** Composed response-length quantiles per
arm are reported at Gate 2B and in the confirmatory report, with the
focal-to-reference difference in median composed length. When any absolute
difference exceeds 20% of the focal median, the primary estimates carry a
fixed interpretation block stating that the compared conditions produced
materially different response lengths. Response length is a post-treatment
quantity and never enters a primary formula. Rationale: in v3 the focal
arm's median composed length was 173 tokens against 189, 202 and 248 in
the E2B references and 191 against 224, 232 and 248.5 in the E4B
references, an asymmetry solo matching does not constrain.

---

## 17. Qualification and procedural pilot

Qualification finishes before the procedural pilot. It is non-scientific
and reads no model-behaviour rate. It verifies that the repository is
clean, the complete implementation is tracked, the model revision
resolves, the dependency manifest is non-empty, the prompt plan satisfies
its schema, the registered verifier and wording tests pass, the witness
and non-entailment suites pass for every registered composition of $A+B$,
$A+R$, $S+B$, and $S+R$, the cache and durable store are reachable, and
the environment and producing commit can be hashed. A failed check returns
`QUALIFICATION_FAILURE` and prevents generation.

After qualification, a procedural pilot confirms that generation, caching,
logging, storage, verification, masking, and analysis run end to end on
real model output.

**Scale.** Twelve fixed pre-screen topics, all eleven arms, both
presentation orders, and the pilot wording allocation of §7. Fixture
values $n = 3$, $k = 3$, $m = 9$, and fixed reference fixtures RF1 at
$q = 5$, RF2 at $q = 5$, RF5 at $q = 8$. These fixtures exercise the arm
structure and cannot become scientific calibration evidence. The pilot
contains $12 \times 11 = 132$ logical cells and $132 \times 8 = 1{,}056$
cached draws.

**Token budget.** 1,024 maximum new tokens. Truncation and finish reasons
are recorded and reported. They do not determine apparatus qualification,
because response length is evaluated scientifically in the pre-screen.

**Quantities inspected.** Exactly five classes: committed and accepted cell
and draw counts; technical-generation failure after retries; codebook
schema validity; content-hash and cache-restoration behaviour; and
successful execution of the pilot mask, commit, unmask, and analysis
cycle. No outcome failure rate, uptake, arm difference, or scientific
contrast is computed or viewed.

**Acceptance conditions.** All eight hold.

1. 132 of 132 logical cells and 1,056 of 1,056 cached draws are committed
   exactly once.
2. Every logical cell yields exactly one cell mean over exactly eight
   accepted draws.
3. Zero generations fail for technical reasons after retries are exhausted.
4. Every codebook field is present and matches its declared type and domain.
5. The full analysis pipeline runs on pilot rows to a structurally complete
   result table without exposing a scientific rate or contrast.
6. Mutating one stored response byte changes its content hash and makes
   the analysis refuse that row.
7. Deleting the local cache and restoring from durable storage reproduces
   every pilot row with the same hashes.
8. The separate `pilot_mask` cycle completes, records its own key and
   events, and leaves the `confirmatory_mask` namespace untouched.

The pilot's structurally complete analysis is persisted fully redacted,
with every numeric value replaced, so no scientific rate or contrast is
exposed.

**Failure consequence.** A failed condition returns `APPARATUS_FAILURE`. A
repair creates a new producing commit and requires qualification and the
full pilot to run again.

**Data handling.** Pilot artifacts have type `pilot_record`. They enter no
calibration or confirmatory quantity and are retained for audit.

---

## 18. Pre-screen, measurement gate, scientific calibration, and freeze

The only permitted stage sequence is:

1. `QUALIFIED`
2. `GATE_0_APPARATUS_PASS`
3. `REGIME_SCREEN_PASS`
4. `GATE_1_MEASUREMENT_PASS`
5. `GATE_2A_SOLO_CALIBRATION_PASS`
6. `GATE_2B_COMPOSED_VALIDATION_PASS`
7. `GATE_3_FREEZE`
8. confirmatory generation
9. masked analysis
10. unmasked analysis

Every command verifies the content hash and signature of the predecessor
PASS record. A terminal state mechanically disables every later generation
command. Every attempted transition is logged with a timestamp, model
revision, producing commit, environment digest, input hashes, output
hashes, and outcome.

### 18.1 Gate 0: apparatus

Gate 0 is the procedural pilot of §17. It evaluates execution integrity
only. Model verbosity, scientific headroom, treatment deliverability, and
reference comparability cannot produce `APPARATUS_FAILURE`.

### 18.2 Regime pre-screen and the dense ladder screen

The pre-screen runs on the 24 pre-screen topics with one response per
registered cell. It has five purposes: choose a completion cap, reject a
clearly exhausted outcome or focal grid, screen the complete severity
ladders, produce natural responses eligible for Gate 1 sampling, and
supply the disjoint confirmation set used against selection noise in
§18.4. It produces no $A+B$ or $S+B$ target-outcome measurement and no
focal-to-reference outcome contrast.

**Completion cap.** A fixed, subject-balanced set of 96 pre-screen prompts
is generated at each cap in $\{512, 768, 1024\}$, using the same prompt
identities and registered seed derivation. The set includes prompts at
every registered load, namely two-constraint, one-constraint, and
zero-constraint prompts, so the cap is chosen against the response lengths
the confirmatory design actually produces. The smallest cap whose
truncation rate over the two-constraint and one-constraint prompts is at
most 0.10 is selected and held fixed for all later stages. If no cap
qualifies, the replication terminates as `RESPONSE_LENGTH_INCOMPATIBLE`.
The truncation rate of the zero-constraint prompts at the selected cap is
recorded; when it exceeds 0.10, every quantity derived from the
`TOPIC` arm is reported as a bound and labelled as such. Rationale: v3
selected its cap from constrained prompts only and then measured its
accidental-compliance base rate on an arm that truncated in more than 83%
of responses.

**Dense ladder screen.** At the selected cap, the pre-screen measures the
complete registered severity ladder of every reference family, all 94
severities, plus the full target grid, the full surrogate grid, and the
full focal grid, one response per topic and cell. This is
$(94 + 8 + 8 + 4) \times 24 = 2{,}736$ generations.

**Cheap difficulty screen.** An outcome or focal grid is rejected early
only when the 95% Wilson intervals for every severity lie entirely on the
same inadmissible side of its Gate 2A band. A focal severity is
provisionally plausible when its Wilson interval intersects $[0.15, 0.55]$.
A reference severity is provisionally plausible when, for at least one
provisionally plausible focal severity, the 95% Newcombe interval for the
solo-failure difference intersects $[-0.10, +0.10]$. Fewer than three
families with at least one provisionally plausible severity terminates the
replication as `REFERENCE_POOL_MISMATCH`. Pre-screen point estimates
cannot select $n$, $k$, $m$, or a reference; they only shortlist.

**Shortlist.** For each family, the shortlist is the at most three ladder
severities whose pre-screen solo-failure estimate is closest to the
pre-screen focal estimate at the provisionally plausible focal severity
nearest 0.30, restricted to provisionally plausible severities. The
shortlist rule is deterministic and its output is recorded in the
pre-screen record before Gate 2A generates anything.

**Diagnoses.** When no outcome or focal severity is admissible,
`GRID_RESOLUTION_INSUFFICIENT` applies when two adjacent registered
severities lie on opposite sides of the entire admission band, and
`TARGET_RANGE_EXHAUSTED`, `SURROGATE_RANGE_EXHAUSTED`, or
`FOCAL_RANGE_EXHAUSTED` applies when the curve reaches a grid boundary
while remaining on one side of the band. Every diagnosis records the
complete curve and boundary value and makes a claim only about the
registered grid.

### 18.3 Gate 1: measurement

Gate 1 applies §10 in full. It passes when: verifier determinism is
exactly 1.000 for every outcome verifier; every boundary case returns its
specified verdict on both sides; the independent reimplementation agrees
at 1.000; and either the human-agreement criterion of §10.1 Question 2 is
met in both verifier classes including the fail-class margin split, giving
`measurement_basis = human_validated`, or the autorater pathway of §10.2
completes through explicit researcher approval, giving
`measurement_basis = autorater_calibration_approved` together with
`HUMAN_VALIDATION_UNAVAILABLE`.

A measured human disagreement excess returns `MEASUREMENT_NOT_ESTABLISHED`.
Insufficient natural evidence within the registered annotation budget
returns `MEASUREMENT_EVIDENCE_INSUFFICIENT`. A verifier repair after the
verifier freeze changes a frozen scientific instrument and requires a new
protocol version.

The construct-discordance detector of §10.1 Question 3 is frozen at Gate 1
and is never revised afterwards.

### 18.4 Gate 2A: solo calibration on the dense ladder

Solo calibration runs on the independent 96-topic set at the selected cap
with $M_{\text{cal}} = 4$ draws per cell, and measures the full target
grid, the full surrogate grid, the full focal grid, and every shortlisted
reference severity. This is at most
$(8 + 8 + 4 + 24) \times 96 \times 4 = 16{,}896$ generations and typically
fewer, because families contribute at most three shortlisted severities
each. Every rate is a mean of cell means.

**Target selection.** For every $n$ the full curve is recorded. Eligible
values lie in $[0.15, 0.50]$. Among them $n^*$ minimises distance from
0.30, with the smaller $n$ breaking an exact tie.

**Surrogate selection.** The identical rule on the surrogate curve gives
$k^*$.

**Focal selection.** For every $m$ the full curve is recorded. Eligible
values lie in $[0.15, 0.55]$. Among them $m^*$ minimises distance from
0.30, with the smaller $m$ breaking an exact tie. The selected $m^*$ is
reported against the grid boundary, because the floor at $m = 7$ is
structural.

The range-exhaustion and grid-resolution diagnoses of §18.2 apply when a
selection has no eligible value.

**Reference-family selection.** Within family $f$, severity $q_f^*$
minimises the absolute difference between its solo failure rate and the
focal solo failure rate at $m^*$, subject to all of the following:

1. the absolute solo-failure difference is at most 0.075;
2. the same absolute difference computed on the disjoint pre-screen
   sample is at most 0.15;
3. every frozen wording is within 20% of the corresponding focal wording's
   word count;
4. the constraint applies to the whole answer;
5. parse independence holds for both outcome verifiers;
6. joint satisfiability and non-entailment witnesses pass against $A$ and
   against $S$.

The less restrictive severity breaks an exact within-family tie. At most
one candidate is retained per family. All eligible families advance to
composed validation. Fewer than three eligible families returns
`REFERENCE_POOL_MISMATCH` with the full admission table, the complete
ladder curves, and the distances.

Two changes from v3 are registered here with their reasons. The caliper
tightens from 0.10 to 0.075 because a dense ladder supplies candidates
that a four-point grid could not, and because v3's admitted references,
matched within 0.10, produced exchangeability failures as large as 0.154.
Condition 2 is a disjoint-sample confirmation registered against the
winner's-curse selection that a dense ladder would otherwise amplify: the
Gate 2A sample both estimates and selects, so the selected severity's true
distance is farther from the focal rate than its estimate suggests, and
the pre-screen sample was measured before the shortlist existed. The
pre-screen caliper of 0.15 is set at roughly one standard error of a
24-topic difference and rules out gross mismatch only.

$M_{\text{cal}} = 4$ is registered because it cuts the selection noise of
v3's single-draw calibration by about 40%: the standard error of a solo
rate over 96 topics falls from about 0.051 to about 0.031, and the standard
error of a difference from about 0.072 to about 0.044, against a caliper
of 0.075.

### 18.5 Gate 2B: composed validation, reachability, and uptake matching

Every eligible family is evaluated on the independent 24-topic
composed-validation set at $M_{\text{cal}} = 4$, in four cell types:
$A + R_f$, $S + R_f$, $A + B$, and $S + B$, using $n^*$, $k^*$, $m^*$, and
$q_f^*$. With at most eight eligible families this is at most
$(8 \times 2 + 2) \times 24 \times 4 = 1{,}728$ generations.

**The focal compositions are generated with their outcome verdicts
structurally withheld.** On rows whose stage is Gate 2B and whose arm is
$A+B$ or $S+B$, only the added-constraint verifier is executed. The outcome
verifiers are never invoked on those rows at any point in the study, which
an executable check asserts. The focal composition therefore contributes
composed uptake and nothing else, and no selection rule can see a
focal-to-reference outcome contrast. This preserves v3's guarantee that
calibration cannot select a reference producing a desired focal effect,
while supplying the dose quantity that v3 lacked.

A family passes composed validation when all of the following hold:

1. its composed target-failure rate under $A + R_f$ lies in $[0.15, 0.85]$;
2. its composed surrogate-failure rate under $S + R_f$ lies in
   $[0.15, 0.85]$;
3. the absolute difference between its composed uptake under $A + R_f$ and
   the focal constraint's composed uptake under $A + B$ is at most 0.15.

Conditions 1 and 2 are the headroom and reachability predicates. Condition
3 is the composed-uptake predicate, new in v4. The absolute difference
between composed uptake under $S + R_f$ and under $S + B$ is recorded and
reported; when it exceeds 0.15 for any admitted reference, $\iota$ carries
a fixed interpretation block. Composed response-length quantiles are
recorded for every cell type and reported.

All three predicates are eligibility conditions only. They cannot rank
references. Among passing families, the final three are those with the
smallest solo-failure distance from $B$, with family identifier breaking
an exact tie, exactly as in v3.

Fewer than three families passing returns a terminal status distinguished
by which predicate failed: `COMPOSED_HEADROOM_FAILURE` when condition 1 or
2 eliminates the shortfall, and `COMPOSED_UPTAKE_MISMATCH` when condition
3 does. The report identifies which solo-matched families failed which
predicate and records every measured value.

The uptake caliper of 0.15 is registered against the v3 realised
mismatches: E4B's three admitted references differed from the focal
constraint's composed uptake by 0.339, 0.365, and 0.396, and E2B's third
reference by 0.336, while E2B's second reference differed by 0.034. A
caliper of 0.15 admits the last of these and refuses the others. The
consequence is registered explicitly: under this rule the v3 E4B design
would have terminated at Gate 2B rather than producing three flagged
manipulation checks, and that termination is the intended behaviour.

### 18.6 Gate 3: immutable model freeze

The freeze record contains the model revision, selected completion cap,
$n^*$, $k^*$, $m^*$, final reference families and severities, every
wording, topic splits, prompt template, chat-template hash, verifier
sources, scoring rules $S_0$ to $S_3$ and $T_1$, the construct-discordance
detector, decoding settings, $M$, seed rules, block plan, family
declarations, equivalence regions, the precision precondition, the claim
ladder, codebook, producing commit, clean-tree assertion, dependency and
environment digests, hardware record, gate-record hashes, the Gate 1
measurement basis, and the complete analysis plan.

Confirmatory generation begins only after the freeze exists and verifies.
Calibration topics never enter the confirmatory set. Any scientific rule
change after study-wide freeze creates v5. Any model-specific frozen-field
change after that model's confirmatory generation begins creates a new
protocol version and leaves the original terminal result unchanged.

---

## 19. Masked analysis

Confirmatory analysis proceeds in two phases. The masked phase allows the
pipeline to be checked and unexpected data problems diagnosed with
decisions kept independent of the result. Pilot masking uses the separate
`pilot_mask` namespace. Pilot mask and unmask events cannot read, create,
consume, or alter the `confirmatory_mask` key or its single permitted
unmask event.

**Constructing the mask.** After confirmatory generation completes and
before any analysis runs, the pipeline permutes the added-constraint labels
of the four $A$-side primary arms independently within each block, and
permutes the four $S$-side primary arms independently within each block
under a separate permutation. The two sides are permuted independently, so
the masked table cannot be de-anonymised by matching one side against the
other. The permuted table is written to the working directory, the true
labels are written to a separate mask key file, and the content hash of the
mask key file is recorded in the run record at the moment it is written.

**Masked view.** Arm labels are permuted; the fields `row_id`, `cell_id`,
`kind`, `prompt_hash`, `seed`, `constraint_id`, `severity`, `draw_index`,
`dependency_digest`, `interpreter`, and `record_hash` are excluded, because
each would identify the true arm or the draw; `verifier_source_hash` is
dropped from the verdict block. Response text is retained, because the
masked phase requires response reading. The failure category and the
non-behavioural flag are computed mechanically by the registered
deterministic program; the forty-failure hand coding of §23 remains a
masked-phase activity.

**Masked phase.** All planned analysis code executes on the permuted table.
All reading of response text, all hand coding of failure categories, all
inspection of compliance and symmetry quantities, and all diagnosis of
anomalies happen in this phase.

Decisions permitted in the masked phase: repairing a defect in analysis
code; adding a diagnostic output; declaring an anomaly and fixing the rule
that will handle it.

Decisions forbidden in the masked phase and afterwards: changing an
estimand, a family, an equivalence region, the precision precondition, the
reference set, a scoring rule, a verifier, a claim rule, a claim tier, or
the topic splits.

**Unmasking.** The mask key is applied by a single named function, invoked
once. Its invocation writes a timestamped entry to the run record together
with the content hash of the analysis code at that moment. The planned
analysis then runs on the true labels and the outputs are recorded. The
unmask operation opens the key exactly once, writes the true-labelled row
set durably, and a separate final-analysis operation consumes that row set;
the key is never read again. Durable replication is incremental, so no
storage path re-opens the key.

**After unmasking.** Any change to analysis code after the unmask timestamp
is labelled post-unmasking in the release, is Tier 4, and supports no
registered claim. The masked-phase and unmasked-phase outputs are both
released.

Three executable checks enforce this.

1. The permuted labels differ from the true labels in at least half of the
   blocks on each side, asserted at mask construction.
2. The mask key file is unreadable by the analysis code outside the unmask
   function, asserted by a test that the file is opened exactly once during
   a full run.
3. The recorded analysis code hash at unmasking matches the hash of the
   code that produced every masked-phase output, asserted by rerunning the
   masked phase from the recorded hash and comparing outputs byte for byte.

---

## 20. Analysis

The analysis runs in a fixed order.

1. Load confirmatory rows. Reject any row whose prompt hash, model
   revision, verifier hash, or block identity falls outside the frozen
   plan.
2. Assert that the complete matrix of 384 blocks by 11 arms by $M$ cached
   draws exists, with every raw draw committed exactly once.
3. Form the cell mean for every cell over all $M$ accepted draws. Assert
   that no cell has fewer than $M$ accepted draws and that no cell mean is
   formed from an imputed or substituted draw.
4. Apply the scoring rule $S_0$ to every draw before averaging, and record
   the four alternative rules for the robustness family.
5. Compute the compliance checks, manipulation checks, construct-discordance
   shares, and arm-symmetry quantities of §10 and §16.
6. Form the block contrasts $D^A_i$, $D^S_i$, and $\Delta_i$.
7. Run the block bootstrap with 10,000 resamples, stratified by
   presentation order, resampling blocks and carrying all eleven cell means
   of each drawn block.
8. Compute simultaneous intervals within each family declared in §14.
9. Compute the realised variance decomposition and the single-draw
   equivalent standard error of §13.6.
10. Apply the claim ladder of §15, together with the interpretation and
    bounding rules of §16.

The analysis fails closed. A missing cell, an incomplete draw set, a
duplicate accepted response, a non-finite standard error, or a non-finite
simultaneous bound returns a named inconclusive status for the affected
quantity and computes no claim. A degenerate contrast whose block values
are all identical stays in the calculation and is reported. No reference,
block, arm, or draw is dropped, and no missing cell is averaged around.

The design is fixed size. There is no interim analysis, no optional
stopping, and no adaptive sample size.

---

## 21. Prohibited quantities in primary estimates

The following are recorded for every generation and never enter a primary
estimate as a covariate, a filter, a stratifier, or a weight: response
length, realised token count, truncation status, finish reason, composed
uptake, refusal status, malformed-output status, failure category,
construct-discordance type, and any other quantity produced during or
after generation. The analysis code asserts this rule by checking the
declared causal role of every field named in a primary formula and refusing
any field whose role is post-treatment.

Composed uptake is used as an eligibility predicate at Gate 2B, before the
confirmatory design exists, and never as a covariate, filter, stratifier,
or weight in any estimate. §30 records this as a design trade-off.

---

## 22. Secondary analyses

Every quantity below is reported with its interval and is labelled Tier 3.
None can change a primary conclusion. Members of families F2 to F10 carry
simultaneous intervals within their family. The remainder carry marginal
intervals and support no claim.

- Order-conditional means of $D^A$, $D^S$, and $\Delta$, and their
  interactions, family F2.
- Per-reference contrasts on each side, family F4.
- The primary estimands recomputed under $S_1$, $S_2$, $S_3$, and $T_1$,
  and the near-miss components, family F5.
- Failure-category differences, family F6.
- Non-behavioural failure differences, family F7.
- Composed-uptake differences, family F8.
- Construct-discordance differences, family F9.
- Surrogate-side exchangeability, family F10.
- Composed uptake by arm, order, and wording.
- Joint compliance, the probability that both active constraints pass.
- Solo interference increments, defined as the composed failure rate minus
  the outcome-alone failure rate for each added constraint, reported with
  the explicit statement that they carry a load confound and license
  nothing.
- Outcome failure by topic subject area and by wording index.
- The graded and signed miss quantities by arm.
- The greedy-decoding replication on 96 blocks, reported as a
  sign-stability check on a different generation population.
- One thousand pseudo-runs, each selecting one cached draw per cell, with
  their empirical distribution and sign stability, retained for continuity
  with v3 and superseded as an inferential device by the draw-averaged
  estimator.
- The realised variance decomposition and the single-draw equivalent
  standard error.
- The outcome-alone arms and the topic-alone arm, the latter reported as a
  bound whenever its truncation rate exceeds 0.10.

---

## 23. Error analysis

Every outcome failure in the eight primary arms is assigned to exactly one
of nine categories by a deterministic program applied in the priority order
below. The first matching category is assigned.

| Order | Category | Detection rule |
|---:|---|---|
| 1 | Empty | The response contains no non-whitespace character |
| 2 | Cut off | The generation stopped because it reached the token limit |
| 3 | Refusal | The response matches one of twenty frozen refusal patterns and contains no answer text |
| 4 | Restatement | The character overlap between the response and the instruction text exceeds 0.60 under a frozen similarity function |
| 5 | Target word only inside longer words | The $S_0$ count is zero and the $S_2$ count is positive |
| 6 | Zero occurrences | The $S_0$ count is zero |
| 7 | Too few | The $S_0$ count is positive and below the required count |
| 8 | Too many | The $S_0$ count exceeds the required count |
| 9 | Other | No rule above applies |

Categories 7 and 8 are additionally reported split by margin, exactly one
against two or more, because v3 established that the margin-one class
carries 67% to 85% of all failures and behaves differently under the
tolerant rule.

Five analyses follow.

**Distribution comparison.** The focal-to-reference difference in the rate
of each category forms family F6 on the target side and is reported
descriptively on the surrogate side.

**Direction-of-miss comparison.** The signed miss distribution is compared
across arms and sides. v3 recorded a model-level rather than arm-level
pattern, with too-few dominant for E2B at $n^* = 5$ and too-many dominant
for E4B at $n^* = 7$, so this quantity is reported per model without
pooling.

**Confounder check.** Within each arm, outcome failure is described as a
function of response length in words, truncation status, refusal status,
and topic subject area. A material association is reported as a competing
explanation, and the contrast is recomputed within strata of that quantity
as a descriptive check.

**Scoring bias check.** Within all adjudicated natural responses from Gate
1, verifier and human labels are cross-tabulated by source model, failure
category, and miss margin. Any concentration of disagreement is reported as
a scoring bias affecting interpretation.

**Automatic coding accuracy.** Forty failures, five drawn at random from
each of the eight primary arms, are read and categorised by hand during the
masked phase. The recorded number is the proportion on which the hand
assignment matches the automatic assignment, with a qualitative summary.

---

## 24. Contamination

**Topic contamination.** Every v4 topic is newly written for this study and
no v3-released topic enters the v4 confirmatory set. At release, the exact
text of each confirmatory topic is queried against a public web search
index and the number of topics returning an exact-phrase match is reported.

**Accidental compliance.** The topic-alone arm measures how often an
unconstrained answer satisfies each outcome constraint by chance. The rate
is reported beside every primary estimate, as a bound whenever the
unconstrained truncation rate exceeds 0.10. v3 recorded a topic-alone pass
rate of 0.000 for both identified models, measured on an arm that truncated
in more than 83% of responses, which is the reason for the bound rule.

**Future contamination.** A canary string is embedded in the released
dataset file. The 96 v4 sequestered topics are held back from release and
support a later rerun on uncontaminated items. The 96 v3 sequestered topics
remain sequestered and untouched.

The outcome is instruction compliance, which does not depend on knowing a
correct answer, so memorised answer content cannot by itself produce a
pass. The topic-alone arm bounds the residual risk empirically.

---

## 25. Human labels and human baseline

Human labels enter the study at exactly one place, the Gate 1 measurement
criterion of §10.1 Question 2, and never score a confirmatory outcome.

At least one annotator, independent of the design and analysis team, adult
and fluent in English, produces the Gate 1 labels under the tool-assisted
counting protocol. Annotators receive written instructions and twelve
worked examples demonstrating the plain reading on clear cases only, and
see no arm, model label, added constraint, item identity, verifier verdict,
or other annotator's work. Display order is a per-annotator seeded shuffle,
so a class-ordered packet layout cannot leak. Finalisation requires a label
on every item plus the face-validity judgment and is immutable thereafter.
Session files record item identity, annotator identity, label, marked
count, sequence, timestamp, and interface and rubric versions for audit,
outside the evidence tree until submitted through the registered Gate 1
pathway. Annotator count, instructions, interface version, and per-class
disagreement counts are reported.

When more than one annotator is available, each labels the same sample and
per-annotator disagreement bounds are reported separately; no majority rule
and no adjudication is applied, and the registered criterion is evaluated
on each annotator's own labels. Two independent grounds support this.
v3 §25 argues that the labelling question is a decidable property of the
text, so annotator background is not a source of systematic variation in
the label, and v3's amendment A1 removed majority adjudication on
researcher instruction before any annotation began. Separately, the v3
validation performed after execution found every realised disagreement to
be annotator arithmetic rather than a label dispute, which majority voting
would have concealed rather than corrected.

For twelve randomly chosen confirmatory topics, one annotator writes an
answer under the focal composition and an answer under one reference
composition on each side, without model assistance. The outcome compliance
of these 48 answers is reported. This establishes that a competent writer
satisfies the compositions and that observed failures are properties of the
model.

A sealed reserve of 40 further validation items is created at Gate 1,
hash-pinned, and never opened under this protocol version. The v3 sealed
40-item reserved set remains sealed and untouched.

---

## 26. Terminal outcomes

Confirmatory terminal outcomes use the vocabulary of §15. Each is recorded
per F1 member.

| Outcome | Condition | Licensed statement |
|---|---|---|
| Meaningful positive swap effect | The $\tau$ simultaneous lower bound exceeds $+0.10$ | The focal constraint raises target failure by more than the smallest effect of interest relative to this frozen reference set, under the registered conditions |
| Meaningful negative swap effect | The $\tau$ simultaneous upper bound is below $-0.10$ | The focal constraint lowers target failure by more than the smallest effect of interest in magnitude under the registered conditions |
| Identity-specific interference resolved | Tier 2 conditions of §15 met with $\iota$ resolved positive | The focal constraint changes target failure by more than it changes failure of a comparable outcome constraint, under assumption A1 |
| Generic constraint load | Tier 2 conditions of §15 met with $\iota$ equivalent | The swap effect does not depend on which of the two registered outcome constraints is measured, to within the smallest effect of interest |
| Direction resolved, magnitude unresolved | An interval excludes zero, lies wholly beyond neither SESOI boundary, and does not meet the equivalence conditions | The direction is resolved; whether the effect is scientifically meaningful remains unresolved |
| Equivalence | An interval lies wholly inside $\pm0.10$ with half-width at most 0.05 | Any effect present is smaller than the smallest effect of interest, at adequate precision |
| Insufficient precision | The realised simultaneous half-width exceeds 0.05 | The design did not achieve the registered precision for this member; equivalence is withheld |
| Direction unresolved | An interval includes zero | The replication does not resolve the direction at the achieved precision |
| Reference heterogeneity | At least one F3 interval extends beyond $\pm0.05$ | Tier 1 remains available; the Tier 2 identity-specific claim is withheld and per-reference contrasts are reported |
| Dose mismatch | An F8 difference exceeds 0.25 with its interval excluding zero | The compared arms delivered their treatments at materially different rates; the estimate stands as an intention-to-treat quantity and the Tier 2 identity-specific claim is withheld |
| Scorability asymmetry | An F7 difference exceeds 0.05 with its interval excluding zero | The contrast and partial-identification bounds are reported, and claims follow both bounds |
| Construct-scope caveat | An F9 difference exceeds 0.05 with its interval excluding zero | The compared arms differ in the rate of construct-discordant occurrences; Tier 1 statements carry the construct-scope block |

Pre-confirmatory terminal statuses:

| Status | Condition | Licensed statement |
|---|---|---|
| `QUALIFICATION_FAILURE` | Code, model, environment, schema, witness, or provenance qualification fails | The registered implementation was not qualified; no behavioural estimand was attempted |
| `APPARATUS_FAILURE` | Execution, cache, hashing, storage restoration, mask plumbing, or integrity machinery fails | The apparatus did not complete its registered technical test |
| `RESPONSE_LENGTH_INCOMPATIBLE` | Every registered token cap has truncation above 0.10 on constrained prompts | The registered completion-budget grid did not support sufficiently complete responses for this model |
| `TARGET_RANGE_EXHAUSTED` | The target curve remains outside its band at a registered grid boundary | The registered target grid did not yield target headroom for this model |
| `SURROGATE_RANGE_EXHAUSTED` | The surrogate curve remains outside its band at a registered grid boundary | The registered surrogate grid did not yield a usable second outcome constraint for this model |
| `FOCAL_RANGE_EXHAUSTED` | The focal curve remains outside its band at a registered grid boundary | The registered focal grid did not yield a deliverable focal operating point for this model |
| `GRID_RESOLUTION_INSUFFICIENT` | Adjacent registered severities jump across the full admission band | The registered grid was too coarse to select an admissible operating point |
| `REFERENCE_POOL_MISMATCH` | Fewer than three distinct families satisfy the registered solo-comparability rules over the complete ladder | The registered reference pool did not supply three solo-comparable controls, at the registered ladder resolution |
| `COMPOSED_HEADROOM_FAILURE` | Fewer than three solo-matched families remain within composed headroom on both sides | The registered solo-matched controls did not supply three usable composed conditions |
| `COMPOSED_UPTAKE_MISMATCH` | Fewer than three solo-matched, headroom-valid families deliver composed uptake within the registered caliper of the focal constraint's | The registered pool did not supply three controls the model took up at a rate comparable to the focal constraint |
| `MEASUREMENT_NOT_ESTABLISHED` | Verifier reliability or validity exceeds a registered failure threshold | The primary measurement did not meet the registered validity standard |
| `MEASUREMENT_EVIDENCE_INSUFFICIENT` | The natural-response annotation budget cannot establish the precision criterion | The available natural validation evidence was too limited to certify the measurement |

Every failed gate automatically emits a terminal report containing the
model and revision, gate, criterion, threshold, observed value, complete
ladder curves where applicable, selected and boundary parameters, reference
admission table and distances, composed results including uptake and
length, truncation and finish-reason summary, verifier status and
measurement basis, artifact hashes, producing commit, environment digest,
the strongest permissible statement, and the estimands made unanswerable.
It reports every quantity available before termination and never implies
that a confirmatory estimate exists.

**A terminal pre-confirmatory status carries no evidence about the
effect.** v4 registers this sentence as a fixed emission in every terminal
report. v3 registered no such fixed emission; its results report stated the
same thing in prose for the two Qwen replications, as "These outcomes carry
no evidence about the effect".

---

## 27. Execution integrity

Every generation is recorded with stage, artifact state, model-replication
identity, block identity, arm, outcome-constraint identity, cached-draw
index, order, wording indices, prompt hash, model revision, backend
version, scientific-interpreter identity, dependency digest, hardware
class, seed, raw response text, response content hash, token counts,
finish reason, and every verifier verdict with its source hash.

Artifacts move monotonically through four states: `generated`, `committed`,
`accepted`, and, when an audit-preserved fragment is excluded,
`superseded`. A generated row becomes committed only after durable write
and content-hash verification. A committed row becomes accepted only after
stage authorisation, predecessor-gate verification, schema validation, and
frozen-plan membership. A superseded row can never return to accepted
status.

The artifact-type field uses the closed vocabulary `qualification_record`,
`prefreeze_plan`, `pilot_record`, `gate_record`, `calibration_record`,
`registered_freeze`, `confirmatory_evidence`, `masked_result`,
`unmasked_result`, and `superseded_non_evidence`.

The run aborts on any of the following: a missing or invalid predecessor
PASS record; a dirty worktree; an invoked source file absent from the
producing commit; a prompt exceeding the context limit; a change in model
revision inside a run; a hardware class differing from the frozen value; a
dependency or interpreter digest differing from the frozen value; a prompt
hash absent from the frozen plan; a duplicate accepted draw; a cell whose
accepted draw count differs from $M$; a verifier source hash differing from
the frozen value; an outcome verifier invoked on a Gate 2B focal-composition
row; a stored response whose content hash differs from the recorded value;
a stale output path; or an artifact whose declared type disagrees with its
stage.

Stage-aware stops arise only from registered integrity rules or the
scientific gates of §18. No confirmatory stop depends on the sign or
magnitude of any outcome contrast.

Every attempted state transition is written to an append-only transition
log. Counts of `generated`, `committed`, and `accepted` rows are reported
separately so an incomplete fragment cannot appear as registered evidence.

Every model tree contains the same required records: `qualification.json`,
`gate0_apparatus.json`, `regime_screen.json`, `gate1_measurement.json`,
`gate2a_solo.json`, `gate2b_composed.json`, `gate3_freeze.json`,
`transition_log.jsonl`, `terminal_report.json`, and, when confirmation is
reached, `confirmatory_manifest.json`, `masked_result.json`, and
`unmasked_result.json`. Each path is derived from the model identifier
through one frozen path function. Missing, stale, or unexpected paths fail
evidence verification.

The v4 implementation lives in its own namespace and imports nothing from
any earlier DCI implementation, which an executable test asserts. Its study
identifier and evidence roots are distinct from v3's, and no v4 operation
writes inside a v3 tree.

---

## 28. Codebook and computational environment

**Codebook.** Every recorded table is accompanied by a codebook containing
one row per variable, with six fields: name, type, permitted values or
range, units, causal role, and a one-sentence definition. Causal role takes
one of six values.

| Causal role | Meaning | Permitted use |
|---|---|---|
| Identity | Names a row or a group of rows | Joining, grouping, resampling |
| Treatment | Records the condition assigned | Defining contrasts |
| Design | Records a choice fixed before generation | Blocking, stratifying, describing |
| Outcome | Records a verifier verdict on an outcome constraint | Primary estimates |
| Post-treatment | Records something produced during or after generation | Diagnostics and secondary description only |
| Provenance | Records how the row was produced | Integrity checks |

Four executable checks enforce the codebook.

1. Every column in every released table appears in the codebook, and every
   codebook row appears as a column.
2. Every recorded value falls inside its declared domain and matches its
   declared type.
3. No field whose role is post-treatment appears in any primary formula,
   checked by the assertion of §21.
4. Every field declared as constraining execution is consumed by a named
   check in §27, so a declared field cannot be inert.

**Version-controlled implementation.** The entire implementation, including
generation, prompt construction, caching, verification, masking, analysis,
schema, and reporting code, is tracked before the first v4 artifact is
created. Qualification requires a clean working tree and fails closed
otherwise. Every artifact records the actual producing commit, and an
executable check confirms that every invoked source path belongs to it.

**Computational environment.** The canonical dependency representation is a
lockfile together with a deterministic frozen export. Qualification fails
when either representation is missing or empty. The environment record
contains the lockfile and export hashes, exact interpreter and version,
exact scientific invocation command, backend version and settings, tensor
library version, driver versions, operating-system and kernel versions, GPU
name and architecture, model repository and revision, chat-template hash,
and the registered execution-relevant environment variables. A
container-image digest is recorded only when the producing process actually
runs inside that container.

Four executable checks enforce provenance and reproducibility.

1. Changing a dependency in a test fixture changes the environment digest;
   an empty dependency manifest is rejected.
2. Rerunning deterministic prompt-plan, codebook, verifier,
   mask-construction, and analysis derivations from the producing commit
   reproduces their recorded hashes or outputs.
3. Rerunning the full analysis in the recorded environment on the released
   raw responses reproduces the released result table byte for byte.
4. Deleting the local cache and restoring from durable storage reproduces
   every committed row with matching content hashes and regenerates no
   committed draw.

**Raw data.** Raw responses are written once, never edited, and carry a
content hash computed at write time. Derived tables are regenerated from
accepted raw responses by the analysis script and are never edited by hand.
Pilot, calibration, confirmatory, and superseded data occupy separate
namespaces and have distinct artifact types.

---

## 29. Relation to existing evaluations

Benchmarks of instruction following score joint satisfaction across several
verifiable instructions and report an aggregate pass rate. Those designs
vary the identity of instructions together with their number, so identity
and load contribute to the same score. The present design fixes the number
of constraints at two in both compared prompts, so identity is the only
quantity that varies.

Studies of compositional constraint satisfaction sweep the number of
simultaneous constraints and report how satisfaction decays as constraints
accumulate. They characterise load. The present design characterises the
effect of identity at fixed load, and v4 additionally separates the part of
that effect which depends on the outcome constraint measured from the part
that does not.

Studies of prompt sensitivity vary surface wording and report score
variation. Wording variation appears here as a designed factor with four
frozen wordings per constraint, assigned at block level and shared across
arms, so the estimands average over the wording pool while each comparison
stays wording-matched.

The measurement built here is an experimental contrast. Its output is a
small set of risk differences with uncertainty intervals, together with the
evidence deciding what those differences are attributable to. It ranks no
models and produces no leaderboard score.

---

## 30. Limitations and design trade-offs

**Narrow scope.** Four separately analysed models, one language, one target
constraint, one surrogate target constraint, one focal constraint, one
registered reference pool, a load of two, one prompt template, one topic
space, one decoding-policy form, single turn, and no tools.

**Exact verifiability costs realism.** The constraints are character-level
lexical rules chosen so that a fixed program decides compliance without
ambiguity. Real deployments contain style and content rules that resist
exact verification. The trade accepted is that a measurement whose meaning
is stable under the treatment is a precondition for interpreting any
effect.

**Identity-specificity is tested with respect to the target word only.**
The surrogate holds the constraint form fixed and varies the word, so
$\iota$ isolates specificity with respect to the outcome constraint's word,
chiefly its length relative to the focal ceiling. Specificity with respect
to constraint form is not estimated. §35 records the extension.

**$\iota$ is the precision-limiting quantity.** Its projected detectable
effect at 80% power is 0.064, above the range the v3 diagnostics suggest
for the total swap effect. Identity-specific components below roughly 0.06
will be unresolved, and the registered topic bank cannot supply the 633
blocks a detectable effect of 0.05 would require.

**Composed-uptake matching selects on a post-treatment quantity.** Gate 2B
admits references partly on how the model behaved in composition. The
quantity is measured on an independent topic set, before freeze, is a
manipulation check rather than an outcome, is a predicate rather than a
ranking criterion, and never enters an estimate. The alternative accepted
in v3, matching on solo difficulty alone, produced composed-uptake gaps of
0.34 to 0.40 in one replication and a flagged reference in the other. The
residual risk is that composed uptake correlates with composed outcome
failure, so equalising dose is not fully independent of the contrast. The
focal composition's outcome verdicts are structurally withheld at Gate 2B
to bound that risk, and the selection path is reported in full.

**The precision gain relies on a v3-derived variance decomposition.** The
projections of §13 rest on one model, one order stratum, and a reported
range for the draw-selection standard deviation. They are projections, not
guarantees. §13.6 requires the realised decomposition to be reported, and
an unfavourable realisation appears as `INSUFFICIENT_PRECISION` rather than
as a silent widening.

**The topic bank bounds precision.** Blocks are topics and the bootstrap
resamples topics, so precision is governed by the number of topics. 384
confirmatory topics support a projected simultaneous half-width near 0.034
for the swap effects and 0.048 for the identity-specific effect.

**Order is pooled.** The primary estimands average over a balanced order
distribution. An order interaction above 0.05 with a resolved interval
triggers a fixed interpretation block and the reporting of order-conditional
means, and it does not invalidate the pooled estimand.

**One direction only.** The reciprocal effect is not estimated.

**Stochastic decoding still contributes noise.** Cell means over eight
draws remove most of it; the residual is reported in the variance
decomposition, and the greedy replication checks whether the sign survives
deterministic decoding on a different generation population.

**Reliability evidence is generated in-house.** No prior instrument for
this construct exists outside this programme. Independent replication of
verifier-to-human agreement on a differently constructed corpus would
strengthen it.

**Human validation may again be unavailable.** The registered fallback is a
proxy instrument with a machine-distinguishable basis marker and a fixed
strongest-claim sentence. A study completed on that basis states that its
outcome is verifier-defined and supports no claim about compliance as an
independent human would judge it.

**Masking is single-custodian.** The mask key is held in a file the analysis
code opens once at the unmask step. The protection rests on recorded hashes
and timestamps, which make a masked-phase decision distinguishable from a
post-unmasking one in the record.

---

## 31. Release

The following are released under a permissive licence when results are
reported: all 528 non-sequestered v4 topics with the canary string; a
manifest stating that 96 v4 sequestered topics remain withheld; all
constraint definitions, ladders, wordings, witnesses, and verifier source;
the outcome scoring implementations and the construct-discordance detector;
study-wide and model-specific freeze records; qualification, gate,
transition, and terminal reports; commit and clean-tree records; the
lockfile, deterministic dependency export, environment manifest, and any
genuinely used container identifier; the codebook; every prompt; every
committed raw cached draw with its content hash and artifact state; every
verifier verdict; human labels, marked counts, and carry-over records;
autorater configuration, judgments, and calibration records where that
pathway was used; pilot and calibration records including the complete
ladder curves and the full admission and composed tables; masked and
unmasked outputs; the unmask timestamp; analysis code; and the
machine-readable result table containing each estimate, family, tier,
standard error, marginal and simultaneous bounds, realised half-width,
realised variance decomposition, single-draw equivalent standard error,
achieved detectable effect, measurement basis, and cell counts.

Every reported figure is reproducible from the machine-readable result
table without regenerating any response, and every number in that table is
reproducible from accepted raw responses in the recorded environment.

---

## 32. Construct validity checklist responses

Responses follow the checklist of
[Bean et al. (2025)](https://arxiv.org/abs/2511.04703).

| Checklist item | Response |
|---|---|
| Provide a precise and operational definition for the phenomenon | §2. Three separable risk differences on the outcome-failure scale at fixed load, with the phenomenon name attached to $\iota$ |
| Specify the scope and acknowledge excluded aspects | §3. Seven neighbouring phenomena named and excluded, four of them by an executable gate |
| Identify sub-components and measure them separately | §2 and §11. The swap effect, the generic-load component, the identity-specific component, and reference exchangeability are separate estimands with separate families and intervals |
| Control for unrelated tasks that may affect results | §8, §16, §22. Two outcome-alone arms and a topic-alone arm; both prompts in every contrast carry the same load, authority level, template, and topic |
| Assess the impact of format constraints on performance | §9, §16, §23. Truncation, refusal, malformed output, and restatement are counted per arm, enter the failure taxonomy, and are subject to the arm-symmetry rule with partial identification bounds |
| Validate automated output parsing | §5, §9, §10, §18.3. Parse independence is executable, five scoring rules are frozen, determinism is required at 1.000, an independent reimplementation must agree at 1.000, forty boundary cases are enumerated per outcome verifier, and blinded human labels under a tool-assisted protocol must place the one-sided 95% Wilson disagreement bound at or below 0.10 in each verifier class and in each fail-class margin stratum |
| Employ sampling strategies for representativeness | §6. Twelve declared subject strata, 52 authored questions per stratum, seeded random assignment to five disjoint uses |
| Verify quality and relevance of all task items | §6, §10.3. Every question verified individually against four written rules; item behaviour tabulated for floor, ceiling, and uninformative topics |
| Include items testing known model sensitivities | §7, §8, §9, §22. Two presentation orders, four wordings per constraint, four alternative scoring rules including a tolerant rule, and a greedy-decoding replication |
| Document whether a previous dataset is adapted | §6. No dataset is adapted. All 624 v4 topics are newly written and no v3 topic enters the confirmatory set |
| Report strengths and limitations of adapted prior work | No prior dataset is adapted |
| Compare performance against the original dataset | No prior dataset is adapted |
| Explain modifications to reused datasets | No dataset is reused |
| Implement contamination tests | §24. Exact-phrase search of every confirmatory topic at release, plus the topic-alone arm as an empirical bound, reported as a bound when its truncation rate exceeds 0.10 |
| Maintain a held-out set | §6. 96 v4 sequestered topics withheld; the 96 v3 sequestered topics remain sequestered |
| Investigate pre-exposure of source materials | §24. Topics newly written; the outcome depends on instruction compliance alone |
| Report sample size and justify statistical power | §13. 384 blocks per model with a variance decomposition, projected standard errors, simultaneous half-widths, and detectable effects for all three primary estimands, including the block counts $\iota$ would require and does not have |
| Report uncertainty estimates for all primary scores | §11, §13, §14, §20. Block bootstrap with 10,000 resamples, ten enumerated families each with its own simultaneous interval, marginal intervals alongside, and every quantity reported whether or not a claim is licensed |
| Describe human rater demographics and mitigate bias | §25. At least one annotator independent of the design and analysis team, blinded to arm and added constraint, labelling a decidable property of the text under a tool-assisted counting interface, with per-class disagreement counts reported |
| Use metrics capturing variability of subjective labels | §9, §10. The primary metric is an exact character test with no subjective component; determinism is tested, reliability reported as verifier-to-human agreement split by miss margin, and the block bootstrap carries the full variability of the outcome |
| Conduct qualitative and quantitative failure analysis | §23. A nine-category priority-ordered taxonomy applied to every failure, split by miss margin, compared across arms as family F6, plus forty hand-coded failures read during the masked phase |
| Investigate whether failures correlate with confounders | §23. Outcome failure described as a function of response length, truncation, refusal, and subject area within each arm |
| Identify scoring biases revealed by error analysis | §16, §23. Verifier and human labels cross-tabulated by arm, category, and margin; arm-symmetry triggers partial identification bounds; construct-discordance rates compared across arms |
| Propose directions to improve scores | §26. Every terminal status identifies the failed registered component and the estimands left unanswered |
| Justify relevance with real-world applications | §11, §29. Product system prompts stack several rules at once, and a change of 0.10 in outcome failure moves a system prompt from 80% compliance to 70% |
| Provide rationale for tasks and metrics tied to the definition | §2, §5, §9, §10. The definition is a difference in outcome-failure probability, the metric is the failure indicator under $S_0$, and the constraint pool is chosen so that the metric's decision procedure is unaffected by the treatment |
| Compare with existing evaluations of similar phenomena | §29 |
| Discuss limitations and design trade-offs | §30. Scope, verifiability against realism, the word-only test of identity-specificity, $\iota$ as the precision-limiting quantity, selection on a post-treatment quantity, reliance on a v3-derived variance decomposition, the topic bank, order pooling, the single direction, decoding noise, in-house reliability evidence, possible unavailability of human validation, and single-custodian masking |

---

## 33. Registered implementation decisions delegated to the manifest

The following are fixed in the signed registration manifest before any v4
artifact exists, and none alters a scientific rule stated above: root seeds
for generation, bootstrap, topic split, ladder screen, Gate 1 sampling,
autorater split, and the engine; the hash function and its
domain-separation strings; registered model revisions; the dependency
representation and scientific interpreter identity; operational engine
settings that are not scientific rules; and the evidence and durable-mirror
roots. Each is recorded with the section of this document that delegates
it.

---

## 34. Relationship to v3 and historical closure

Version 3 is closed as four terminal model replications: two complete
unmasked analyses and two pre-confirmatory non-identifications. Its
evidence directories remain unchanged and this protocol writes nothing
inside them.

**What v3 established.** Both Gemma replications completed the full stage
sequence with verified evidence trees and bit-for-bit reproduction of the
masked analysis at unmasking. Four of four primary estimands were direction
unresolved. One claim resolved: equivalence for E2B in the target-first
stratum, on a simultaneous interval of half-width 0.087. Reference
exchangeability failed in both replications, decisively in E2B, where the
per-reference contrasts split sign inside one stratum. Both Qwen
replications terminated at Gate 2A with `REFERENCE_POOL_MISMATCH`, which is
non-identification of the design and carries no evidence about the effect.
Registered diagnostics were consistently directionally positive with means
of roughly +0.04 to +0.11 and are not confirmatory evidence.

**What v3 measured about itself.** Three quantities drive the v4 redesign
and none of them is an effect estimate. First, the draw-selection lottery
carries about 85% of the per-block variance of the swap contrast, and the
registered E2B target-first draw landed below the fifth percentile of its
own draw distribution. Second, solo-difficulty matching left composed
uptake mismatched by 0.34 to 0.40 in E4B and by 0.34 for one E2B reference.
Third, the fixed four-point severity grids left the admissible reference
region unmeasured for both Qwen models.

**What v3 could not establish.** The registered human-agreement criterion
was never met by an independent annotator. The final Gate 1 basis is
`autorater_calibration_approved` with `HUMAN_VALIDATION_UNAVAILABLE`. A
later author-annotator validation certified the verifier-pass class and
missed the verifier-fail class, with every disagreement traced to human
off-by-one arithmetic. The third validation question, whether exact-count
compliance validly operationalises instruction compliance, was left
explicitly open.

**Carried forward unchanged in substance.** The swap estimand form; the
block as assignment, pairing, clustering, and generalisation unit; 384
confirmatory topics; deterministic outcome scoring with declared
alternatives; intention-to-treat analysis; the block bootstrap with
simultaneous family intervals; the $\pm0.10$ smallest-effect region; the
$\pm0.05$ exchangeability margin; non-behavioural-failure partial
identification under the conservative both-bounds reading; fixed-size
sampling; masked analysis; the error taxonomy; contamination controls; the
guarded equivalence emitter; artifact-state semantics; fail-closed
provenance; and sequestered-topic protection.

**Changed, with the v3 evidence that forced each change.** Recorded in full
in `DCI1_v3_to_v4_change_summary.md` and summarised in §35's table of
origins. In brief: three named estimands replace one; a surrogate outcome
constraint and eight composed arms replace six arms; cell means over all
cached draws replace one hash-selected draw; pooled order replaces split
order under an interaction gate; a dense integer severity ladder with a
two-stage screen replaces a four-point grid; a composed-uptake predicate
joins composed headroom at Gate 2B; a precision precondition joins the
equivalence rule; a five-tier claim ladder replaces the two-level ladder;
the tool-assisted human protocol, the independent reimplementation test,
and the construct-discordance probe replace a single conflated agreement
bound; and the autorater pathway that v3 reached through six amendments is
registered before execution.

---

## 35. Registered open decisions

A preregistration that hides its open decisions moves them into the
analysis. The following are open, are recorded here, and are closed by
recording the decision and its evidence in the signed manifest before
study-wide freeze. Nothing below may be decided after any v4 confirmatory
generation. The companion document
`DCI1_v4_unresolved_decisions.md` gives the full statement of each.

| # | Open decision | Evidence needed to close it | Default if no evidence is obtained |
|---|---|---|---|
| U1 | The name and exact cell set of the discriminating design. The v3 results report ranks a "B+R / B+S discriminating experiment" first among remaining blockers and states it was registered as the natural next step, but no specification of it appears in the uploaded v3 corpus | The source note defining that design, checked against §8 and §11.4 | The crossed design of §8 and §11.4 as written |
| U2 | The surrogate target word. §5 registers *hence*, five letters | Pre-screen solo-failure curves for candidate words, and their topic-alone accidental-compliance rates | *hence* as registered |
| U3 | Whether to change the target word so the focal grid can extend below $m=7$ | Pre-screen focal curves for a shorter target word against the natural base-rate cost | Keep *however* and the structural floor |
| U4 | Confirmatory draws per cell $M$. §4 registers 8 | The variance decomposition recomputed on the v3 confirmatory caches, and the generation budget | $M = 8$ |
| U5 | Calibration draws per cell $M_{\text{cal}}$. §4 registers 4 | The calibration budget and the realised selection-noise target | $M_{\text{cal}} = 4$ |
| U6 | The composed-uptake caliper. §18.5 registers 0.15 | Gate 2B uptake distributions from the first replication's shortlist, inspected before freeze | 0.15 |
| U7 | Whether a two-reference degraded path should exist when exactly two families are eligible | A decision on whether partial evidence under a restricted claim ladder is preferable to none | No degraded path; three references remain required |
| U8 | Whether the v3 topic bank may be reused | Confirmation of whether the v3 release has occurred | v4 authors a new bank; no v3 topic enters |
| U9 | Whether composed response length should become an admission predicate rather than a reported comparability quantity | Gate 2B composed-length distributions from the first replication | Reported only |
| U10 | Whether reference families whose ladder is exhausted at $q=0$ should receive registered conjunctive extensions | Ladder-screen curves showing whether any family is still too easy at $q=0$ for a registered model | No extensions; `LADDER_EXHAUSTED` is recorded in the admission table |
| U11 | Execution order and the early-stop rule. §4 keeps E2B first with a stop on three terminal statuses | A decision on whether the hardest identification case should run first | E2B first, stop rule as written |
| U12 | Whether a form-varying second surrogate should be added to test identity-specificity with respect to constraint form as well as word | A generation budget and a witness suite for the additional compositions | Word-varying surrogate only |
