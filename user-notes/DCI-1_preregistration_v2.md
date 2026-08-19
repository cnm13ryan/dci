# Preregistration: Does replacing one instruction with a comparable instruction change compliance with a different instruction?

**Protocol identifier:** DCI-1
**Version:** 2.0, for registration
**Date:** 16 August 2026
**Confirmatory data collected at the time of registration:** none
**Registration target:** Open Science Framework, protocol-document format

---

## 1. Definitions

Every term below is used throughout with the meaning given here.

| Term | Meaning |
|---|---|
| Language model | A program that receives a text input and produces a text output by sampling from a probability distribution over word pieces. |
| Prompt | The complete text sent to the language model on one occasion. |
| Response | The complete text the model produces from one prompt. |
| Instruction | A sentence in the prompt stating a requirement the response is meant to meet. |
| Constraint | An instruction expressed so that a fixed computer program can decide whether a response meets it. Used interchangeably with instruction in this protocol. |
| Verifier | The computer program that reads a response and returns pass or fail for one constraint. |
| Scoring rule | The exact procedure that turns a response into a verifier verdict, including text normalisation, the unit counted, and the comparison applied. |
| Compliance | The state in which the verifier returns pass. |
| Failure | The state in which the verifier returns anything other than pass. |
| Target constraint, written A | The constraint whose compliance is the measured outcome. |
| Focal constraint, written B | The constraint whose presence is the treatment under study. |
| Reference constraint, written R | A constraint used in place of B to form the comparison condition. |
| Background set, written S | Any further constraints held identical across comparison conditions. Empty in this study. |
| Load | The number of constraints present in a prompt at once. |
| Arm | One of the conditions a topic is run under, defined by which constraint occupies the added slot. |
| Topic | One question the model is asked to answer. |
| Item | One topic considered as a draw from a larger population of possible topics. |
| Block | One topic together with the fixed presentation order and the fixed wording choices assigned to it. All arms of a block share these. |
| Replicate | One generated response for one arm of one block. |
| Estimand | The numerical quantity the study aims to estimate, defined before data exist. |
| Risk difference | The difference between two probabilities, expressed in percentage points. |
| Intention to treat | The rule that an estimate is computed from the condition assigned, with no conditioning on what the model did in response. |
| Post-treatment quantity | Any quantity produced by or after generation, such as response length or truncation status. |
| Non-behavioural failure | A target failure whose immediate cause is the apparatus, specifically an empty response, a response cut off at the token limit, or a response the verifier cannot process. |
| Jointly satisfiable | The property that at least one response satisfies every constraint in a prompt at the same time. |
| Witness | A concrete response demonstrating joint satisfiability. |
| Entailment | The property that satisfying one constraint automatically satisfies another. |
| Ceiling | A condition in which the target constraint almost always passes, leaving no room to detect a decrease. |
| Floor | A condition in which the target constraint almost always fails, leaving no room to detect an increase. |
| Headroom | The absence of ceiling and floor. |
| Uptake | Compliance with the constraint occupying the added slot. |
| Manipulation check | A measurement showing that the assigned treatment reached the model, computed separately from the outcome. |
| Compliance check | A measurement showing that a generation was produced under normal operating conditions. |
| Exchangeability | The property that any member of the reference set serves equally well as the comparison condition. |
| Negative control | A comparison whose expected result is zero, used to test an assumption. |
| Reliability | The extent to which a measurement procedure returns the same value when the same thing is measured again. |
| Precision | The narrowness of the uncertainty interval around an estimate. |
| Face validity | Evidence that the measure appears on inspection to capture the requirement it names. |
| Content validity | Evidence that the measure covers every part of the requirement it names. |
| Convergent validity | Evidence that the measure agrees with an independent measure of the same requirement. |
| Discriminant validity | Evidence that the measure is unaffected by quantities outside the requirement it names. |
| Ecological validity | Evidence that the measurement setting resembles the setting the claim is about. |
| Construct validity | The degree to which a measurement provides evidence about the phenomenon it is meant to represent, established by assembling the forms of evidence above. |
| Aggregation unit | The level at which observations are averaged before an estimate is formed. |
| Cluster | The unit resampled by the bootstrap. |
| Bootstrap | A procedure that repeatedly resamples clusters with replacement to estimate uncertainty. |
| Discordance | The probability that two paired observations disagree, used to size a paired binary comparison. |
| Studentised | Divided by an estimate of its own standard error. |
| Family | A declared set of quantities that share one simultaneous confidence statement. |
| Simultaneous interval | An uncertainty interval constructed so that a stated confidence level applies to a whole declared family at once. |
| Šidák bound | A conservative critical value for a family of size $k$, obtained by using the two-sided level $1 - 0.95^{1/k}$ for each member. |
| Smallest effect of interest | The smallest risk difference the study treats as scientifically meaningful. |
| Equivalence region | The interval around zero inside which an effect counts as negligible. |
| Equivalence test | A test whose conclusion is that an effect lies inside the equivalence region. |
| Partial identification bounds | The range of estimates consistent with every possible value of an unmeasured quantity. |
| Masked analysis | Analysis performed on data whose condition labels have been permuted, so that decisions taken during analysis cannot depend on the result. |
| Mask key | The stored mapping from permuted labels back to true labels. |
| Procedural pilot | A small run whose purpose is confirming that the apparatus works end to end, with the quantities inspected fixed in advance. |
| Codebook | A table with one row per recorded variable, giving its name, type, permitted values, units, causal role, and definition. |
| Causal role | The label stating what a variable may be used for, drawn from identity, treatment, design, outcome, post-treatment, and provenance. |
| Container image | A packaged operating system and software stack, identified by a digest, that reproduces one computing environment exactly. |
| Lockfile | A file pinning the exact version of every software package used. |
| Content hash | A fixed-length value computed from a file's bytes, used to detect any change to it. |
| Contamination | The presence of study materials, or close relatives of them, in the data used to train the model. |
| Canary string | A rare fixed text placed in a released file so that its later presence in training data is detectable. |
| Decoding | The procedure converting the model's output distribution into text. |
| Greedy decoding | Decoding that always takes the highest-probability word piece, producing one deterministic response per prompt. |

---

## 2. Phenomenon

The phenomenon is **directional constraint interference**: the change in the probability that a language model complies with one designated constraint when a different constraint in the same prompt is replaced by a comparable alternative, with the number of constraints held fixed.

The operational definition is a risk difference. Write $F_A = 1$ when the target verifier returns failure and $F_A = 0$ when it returns pass. For a fixed target $A$, a fixed background set $S$, and one reference $R$:

$$\tau = P(F_A = 1 \mid A + B + S) - P(F_A = 1 \mid A + R + S).$$

Positive $\tau$ means the focal constraint produces more target failure than the reference does. Negative $\tau$ means it produces less. Zero means the two produce the same amount.

The word *directional* describes the construction of the estimand: one constraint is designated the outcome and the other is designated the treatment, so the quantity has a direction by definition.

The phenomenon has two components, and each is measured separately. The first is the swap effect $\tau$ itself. The second is the exchangeability of the reference set, measured as the spread of effects among references that are meant to be interchangeable. The second component determines what the first licenses.

---

## 3. Scope and excluded phenomena

The study measures the swap effect for one target constraint, one focal constraint, three references, one language model, one decoding policy, one prompt template, one language, one topic space, and a load of two constraints.

Six neighbouring phenomena fall outside the scope and are excluded by design.

**Load-driven degradation.** The decrease in compliance caused by adding constraints of any kind. Both compared prompts carry exactly two constraints, so this quantity is held fixed and is not estimated here.

**Logical impossibility.** A prompt whose constraints cannot all be satisfied forces a failure. Every composition used is certified jointly satisfiable by an explicit witness before generation, so failures observed here occur where success was available.

**Entailment and redundancy.** A prompt in which satisfying one constraint automatically satisfies another produces compliance for logical reasons. Every composition used is certified free of entailment in both directions before generation.

**Mechanism.** The internal computation that produces the behaviour. The design measures behaviour under an intervention and is silent on internal mechanism.

**The reciprocal effect.** The effect of the target constraint on compliance with the focal constraint. This requires a separate design in which the roles are exchanged, and it is not estimated here.

**Generalisation.** Behaviour under other models, constraint families, languages, loads, prompt formats, or inference policies. Each of these is held at one fixed level, and every claim carries that level as a condition.

---

## 4. Model and inference policy

| Element | Value |
|---|---|
| Model | Qwen2.5-3B-Instruct |
| Revision | The commit hash recorded in the frozen protocol record, pinned at freeze and asserted at every generation |
| Backend | Hugging Face Transformers, version pinned at freeze |
| Numeric precision | bfloat16 |
| Hardware | One GPU, class recorded and asserted at every generation |
| Temperature | 0.7 |
| Top-p | 0.9 |
| Top-k | 50, set explicitly |
| Maximum new tokens | 400 |
| Samples per cell | 1 |
| Seed | Derived deterministically from a fixed root seed and a hash of the exact prompt text |
| Prompting | Zero-shot. No examples, no tools, no retrieval, no self-consistency, no best-of-N, no revision passes, one turn |

The estimand averages over this decoding policy. Compliance is scored on the response text alone, and no model internals are read.

---

## 5. Constraints

The target constraint is:

> **A:** Use the word *however* exactly $n$ times.

The focal constraint is:

> **B:** Every word in the answer must have at most $m$ letters.

The value of $n$ is drawn from $\{1, 2, 3\}$ and the value of $m$ is drawn from $\{7, 8, 9, 10\}$ by the calibration rules in Section 18. The word *however* has seven letters, so every value of $m$ in this grid leaves the composition satisfiable.

The reference candidate pool contains twelve constraints. All are single-clause, apply to the whole answer, and are decided by exact character operations.

| Identifier | Constraint text |
|---|---|
| C1 | Every word in the answer must have at least two letters. |
| C2 | Every word in the answer must have at least three letters. |
| C3 | No word in the answer may begin with the letter b. |
| C4 | No word in the answer may begin with the letter c. |
| C5 | No word in the answer may begin with the letter f. |
| C6 | No word in the answer may begin with the letter m. |
| C7 | No word in the answer may begin with the letter p. |
| C8 | No word in the answer may begin with the letter s. |
| C9 | No word in the answer may begin with the letter t. |
| C10 | No word in the answer may end with the letters ly. |
| C11 | No word in the answer may end with the letters ing. |
| C12 | No word in the answer may contain the same letter twice in a row. |

Three properties of this pool are established by inspection before any generation and are recorded in the protocol.

**Parse independence.** The target verifier's decision depends only on runs of letters and on whether the sequence `however` occupies a whole run. No constraint in the pool, and no value of $B$, mentions the sequence `however` or any of the letters h, o, w, e, v, r. Every other constraint therefore leaves the target verifier's decision procedure unchanged, and the treatment cannot alter the meaning of the outcome measurement.

**Joint satisfiability.** The word *however* has seven letters, contains no doubled letter, begins with h, and ends with the letters er. It therefore satisfies every constraint in the pool and every admissible value of $B$. A written witness answer satisfying both constraints is produced and verified for each composition used.

**Non-entailment.** For each composition, two written responses are produced and verified: one satisfying $A$ and failing the added constraint, and one satisfying the added constraint and failing $A$. Both directions are checked.

Each constraint has four frozen wordings that state the same rule in different words. The four wordings of each constraint are written before calibration, checked by the researcher for identical meaning, and verified to produce identical verifier behaviour on a fixed set of twenty test responses.

---

## 6. Topics

The task space is short open-ended informational questions that a competent writer can answer in sixty to one hundred and twenty words without tools, without arithmetic, and without recalling a specific named fact.

The topic bank contains 576 questions across twelve declared subject areas, with 48 questions per area: everyday science, history, geography, food, music, sport, work and organisations, health and the body, technology, language and writing, art and design, and the natural world.

Questions are drafted by the researcher with model assistance and then verified one by one by the researcher against four rules: answerable from general knowledge, no single correct short answer, no reused text from any public dataset or examination, and no wording that itself mentions any letter, word length, or word-shape requirement.

Within each subject area the 48 questions are randomly shuffled with a fixed seed and split into 8 calibration questions, 32 confirmatory questions, and 8 sequestered questions. The three splits are disjoint. This gives 96 calibration topics, 384 confirmatory topics, and 96 sequestered topics. The sequestered topics are never used in this study and exist so that a later uncontaminated re-run is possible.

This is stratified random sampling: the task space is divided into twelve declared strata, an equal number of items is authored per stratum, and assignment to splits is random within stratum.

---

## 7. Prompt construction

Every prompt has the same three parts in the same order: the topic question, a numbered list of the active constraints, and the line `Answer:`.

Within a block, the two prompts being compared are identical byte for byte except for the single line stating the added constraint. Block index $i$ determines three things, fixed across all arms of that block:

- **Presentation order.** Blocks with even index place the target constraint first. Blocks with odd index place the added constraint first. This yields 192 blocks in each order.
- **Target wording.** The wording index for $A$ is $i \bmod 4$.
- **Added wording.** The wording index for the added constraint is $\lfloor i/4 \rfloor \bmod 4$.

Both constraints occupy the same authority level, appearing in the same numbered list in the same user message. No constraint is placed in a system message.

---

## 8. Design

Each of the 384 confirmatory blocks is run under six arms.

| Arm | Prompt contents | Purpose |
|---|---|---|
| Focal | Target constraint and focal constraint | Treatment condition |
| Reference 1 | Target constraint and the first admitted reference | Comparison condition |
| Reference 2 | Target constraint and the second admitted reference | Comparison condition |
| Reference 3 | Target constraint and the third admitted reference | Comparison condition |
| Target alone | Target constraint only | Headroom diagnostic |
| Topic alone | No constraints | Base rate of accidental compliance |

Each arm produces one response per block. Confirmatory generations total $384 \times 6 = 2{,}304$.

A sensitivity run repeats the four primary arms on the first 96 confirmatory blocks under greedy decoding, giving a further 384 generations.

The two diagnostic arms carry one constraint or none, so they sit at a different load and are excluded from every contrast. They are reported as descriptive quantities.

---

## 9. Outcome and scoring rule

The primary outcome is $F_A \in \{0, 1\}$, target failure.

The primary scoring rule, written $S_0$, is fixed here and applies unchanged to every response in every arm:

1. Take the whole response text, including any preamble or trailing remark.
2. Convert it to lower case.
3. Find every maximal run of alphabetic characters.
4. Count the runs whose content equals `however`.
5. Return pass when the count equals $n$, and failure otherwise.

Non-alphabetic characters act as run boundaries, so markdown emphasis, quotation marks, and punctuation adjacent to the word leave the count unchanged.

Failure includes every state that is not a pass: an incorrect count, an empty response, a refusal, a response cut off by the token limit, and a response the verifier cannot process. Removing these states would condition the analysis on events the treatment can itself cause, so they are retained as failures. Their frequencies are reported by arm and are subject to the symmetry rule in Section 16.

Three alternative scoring rules are defensible, are named here, and are used in the declared robustness family of Section 14. No further scoring rule enters the analysis.

| Rule | Definition | Difference from $S_0$ |
|---|---|---|
| $S_1$ | The same procedure without the lower-casing step | Treats `However` and `however` as different |
| $S_2$ | Count non-overlapping occurrences of the substring `however` anywhere in the lower-cased text | Counts occurrences inside longer runs of letters |
| $S_3$ | Apply $S_0$ after deleting any leading line that ends in a colon and any line that repeats the constraint text | Excludes preamble and instruction restatement from the count |

The choice of $S_0$ as primary is fixed before any generation and is recorded in the freeze record of Section 18. The graded quantity $|{\text{count}} - n|$ is recorded for every response and is reported descriptively.

---

## 10. Verifiers, reliability, and validity

The verifier receives the response text and the target constraint identity. It receives no arm label, no information about which constraint occupied the added slot, and no output from any other verifier. The same code path runs in every arm.

Secondary verifiers score the added constraint in each arm, producing uptake. Every verifier is deterministic, reads the response text alone, and requires no model access. No language model is used as a judge anywhere in the scoring. No human rating produces a primary score.

The measurement record answers five questions, and each answer is fixed before generation.

| Question | Answer |
|---|---|
| What is the construct | Compliance with the target constraint, defined as the response containing the word *however* exactly $n$ times |
| What measure operationalises it | The scoring rule $S_0$ of Section 9, implemented as a deterministic program |
| Selected from prior work or created here | Created for this study. No prior instrument for this construct is reused, so its reliability and validity evidence is generated here |
| Any modification, and when | The scoring rule is fixed at freeze. Any change after freeze creates a new protocol version, and the original result is reported unchanged |
| How the measure is quantified, and when that was decided | Binary pass or failure under $S_0$, with the three alternatives of Section 9 declared as a robustness family. All of this is decided before any confirmatory generation |

Reliability is established by three tests, each producing a recorded number.

**Determinism.** Every verifier is executed three times on every calibration response, once on each of three separate processes. The recorded agreement is the proportion of responses receiving identical verdicts across all three executions. The required value is 1.000.

**Human agreement.** 150 responses drawn from the calibration run are labelled by three annotators, 75 drawn from responses $S_0$ passed and 75 from responses $S_0$ failed. Annotators see the response text and the target constraint text, and see nothing about the arm or the added constraint. The majority label is taken. The recorded numbers are the disagreement rate in each class, the 95% Wilson upper bound on each, and the pairwise agreement among annotators.

**Item behaviour.** Target failure is tabulated by topic across the calibration run. The recorded numbers are the proportion of topics at floor, the proportion at ceiling, and the proportion whose verdicts are identical in every arm. Topics in the last group carry no information about the contrast, and their proportion enters the precision report of Section 13.

Validity is established by four arguments, each with a recorded check.

**Face validity.** Three annotators independently judge whether the plain-language statement of $S_0$ matches the constraint text as written. The recorded number is the count of agreements out of three.

**Content validity.** The boundary-case suite of Section 18 enumerates one case for each way the requirement could be ambiguous: empty response, punctuation adjacent to the target word, capitalisation, hyphenation, the target word inside a longer word, repeated target words, non-Latin characters, and a response cut off mid-word. The recorded number is the count of enumerated cases the verifier handles as specified.

**Convergent validity.** The human agreement test above supplies an independent measurement of the same requirement.

**Discriminant validity.** The verifier's decision is unaffected by the treatment. Two checks record this. The first is an assertion that the verifier function's inputs exclude the arm label, the added constraint identity, and every other verifier's output. The second is the parse-independence property of Section 5, established by inspection of the constraint pool.

**Ecological validity.** The prompt format resembles a request accompanied by written rules, which is how instructions reach a model in deployment. The specific character-level rules are chosen for exact decidability, and Section 30 records the resulting limit on realism.

---

## 11. Estimands

Write $F_{i,q}$ for the target failure indicator in block $i$ under arm $q$. Write $B$ for the focal arm and $R_1, R_2, R_3$ for the reference arms.

The block contrast is

$$D_i = F_{i,B} - \tfrac{1}{3}\left(F_{i,R_1} + F_{i,R_2} + F_{i,R_3}\right).$$

Two primary estimands are declared, one per presentation order:

$$\tau_{\text{target-first}} = \mathbb{E}\left[D_i \mid \text{order} = \text{target first}\right], \qquad \tau_{\text{added-first}} = \mathbb{E}\left[D_i \mid \text{order} = \text{added first}\right].$$

Three exchangeability contrasts are declared, computed over all 384 blocks:

$$\delta_{jk} = \mathbb{E}\left[F_{i,R_j} - F_{i,R_k}\right], \qquad (j,k) \in \{(1,2), (1,3), (2,3)\}.$$

The smallest effect of interest is a risk difference of 0.10. A change of that size converts a system prompt with 80% target compliance into one with 70% target compliance, which is one additional failure in every ten responses. The exchangeability margin is 0.05. Both values are fixed here and are used unchanged in the analysis.

Two claim levels are defined, and the exchangeability result decides which applies.

**Level 1, a swap effect.** Replacing the reference set with the focal constraint changed target compliance under the registered conditions. This is licensed by the design whenever the gates in Section 18 pass.

**Level 2, an identity-specific effect.** The focal constraint damages the target more than comparable constraints do. This is licensed only when all three simultaneous exchangeability intervals lie inside $\pm 0.05$.

---

## 12. Unit of analysis and clustering structure

The block is the unit at four levels, and each role is stated separately.

| Role | Statement |
|---|---|
| Assignment | Presentation order and both wording indices are assigned at the block and are identical across the six arms of that block |
| Pairing | The focal and reference arms are compared inside a block, so between-topic variation is removed from the contrast |
| Clustering | The bootstrap resamples blocks. When a block is drawn, all six of its responses travel with it, preserving the correlation induced by the shared topic |
| Generalisation | Uncertainty statements refer to the population of topics defined in Section 6. Claims extend to that topic space |

Responses are nested inside blocks. Six responses exist per block, and they are correlated because they share a topic, an order, and a wording. Resampling responses individually would treat those six as independent and would understate uncertainty, so responses are never the resampling unit.

The design contains no replicate level. One response is generated per block and arm, so within-cell decoding variability is absorbed into the block-level contrast and is priced by the block bootstrap.

Three executable checks enforce this structure.

**Resampling unit.** Each bootstrap replicate draws exactly 192 block identifiers with replacement inside each order stratum. The analysis asserts that the number of identifiers drawn equals the stratum size and that every drawn identifier carries six responses.

**Function signature.** The estimator receives a table indexed by block. The analysis asserts that no primary estimator function accepts a response-level index.

**Variance behaviour.** A synthetic dataset is generated in which within-block noise is doubled and between-block variation is held fixed. The analysis asserts that the width of the interval for the block-level mean changes by less than the Monte Carlo error of the bootstrap, which confirms that the procedure prices between-block variation.

---

## 13. Sample size, precision, and what the design can detect

The sample size is justified by a smallest-effect-of-interest power analysis, combined with a resource constraint on the number of topics.

The declared planning quantities are fixed here: smallest effect of interest 0.10, target power 0.80, two-sided significance level 0.05, block as the independent unit, 384 blocks, 192 blocks in each presentation order.

For a paired binary contrast with block-level discordance $p_d$, 80% power, and a two-sided 5% level, the number of blocks required to detect a risk difference $\delta$ is

$$H \approx \frac{7.84\, p_d}{\delta^2}.$$

Inverting this at $H = 192$ gives the marginal detectable effect for one primary estimand considered alone:

| Block discordance $p_d$ | Marginal detectable effect | Simultaneous detectable effect |
|---:|---:|---:|
| 0.10 | 0.064 | 0.070 |
| 0.20 | 0.090 | 0.099 |
| 0.202 | 0.091 | 0.100 |
| 0.245 | 0.100 | 0.110 |
| 0.30 | 0.111 | 0.122 |

The simultaneous column applies the decision rule the analysis actually uses. The two primary estimands are computed on disjoint sets of blocks, so their sampling errors are independent, and the Šidák bound for a family of two gives a two-sided critical value of 2.24. Substituting $(2.24 + 0.84)^2 = 9.49$ for $7.84$ produces the second column. Under the rule applied, the design has at least 80% power for the smallest effect of interest whenever block discordance is at or below 0.202.

Three planning sources are excluded. No effect estimate from any earlier work in this programme sets the sample size. No effect estimate from the calibration run sets the sample size, and no focal-to-reference contrast is computed on calibration data at any point. No effect estimate from the procedural pilot of Section 17 sets the sample size, and the pilot computes no contrast.

The resource constraint is the topic bank. Blocks are topics, so precision is governed by the number of confirmatory topics. Reaching a simultaneous detectable effect of 0.10 requires roughly 320 to 470 topics across the plausible discordance range, and 384 sits inside that range.

For the exchangeability family, computed over all 384 blocks, the simultaneous half-width falls at or below 0.05 when reference-to-reference block discordance is at or below a value between 0.168 and 0.192. The lower figure uses the Šidák bound for a family of three. The three contrasts span a two-dimensional space, because $\delta_{23}$ equals $\delta_{13}$ minus $\delta_{12}$, so the Šidák bound is conservative and the upper figure uses the two-dimensional value. The bootstrap supplies the exact critical value, and the realised half-width is reported beside the exchangeability decision.

Realised discordance is measured and reported for every contrast. The achieved detectable effect implied by that realised discordance is reported beside every estimate. The proportion of uninformative topics from Section 10 is reported alongside, because topics whose verdicts are identical in every arm contribute no information to the contrast.

The formula treats a single paired binary comparison. The reference side of $D_i$ averages three arms, which lowers its noise, so the tabulated values are conservative for this design. The realised precision reported in the results comes from the block bootstrap and supersedes them.

---

## 14. Multiplicity families

Every quantity that carries an inferential statement belongs to exactly one family declared here. The list is closed at freeze. No quantity moves between families afterwards. Any quantity computed and absent from this list is exploratory and is labelled exploratory in every report.

| Family | Members | Size | Status |
|---|---|---:|---|
| F1 Primary | $\tau_{\text{target-first}}$, $\tau_{\text{added-first}}$ | 2 | Primary. Supports a claim under Section 15 |
| F2 Exchangeability | $\delta_{12}$, $\delta_{13}$, $\delta_{23}$ | 3 | Gate on the Level 2 claim |
| F3 Per reference | $\mathbb{E}[F_{i,B} - F_{i,R_j}]$ for each reference at each order | 6 | Secondary. Diagnostic for reference disagreement |
| F4 Scoring robustness | $\tau$ at each order under $S_1$, $S_2$, $S_3$ | 6 | Secondary. Reports sensitivity to the scoring rule |
| F5 Failure categories | The focal-to-reference difference in the rate of each of the nine categories of Section 23 | 9 | Secondary. Locates which failure type drives any contrast |
| F6 Apparatus symmetry | The focal-to-reference difference in non-behavioural failure rate for each reference | 3 | Gate on the interpretation rule of Section 16 |

Each family receives its own simultaneous 95% interval, computed by standardising each member by its bootstrap standard error and taking the largest absolute standardised deviation across the family in each resample. Marginal intervals are reported alongside for readers who want them, and the decision rules use the simultaneous intervals.

Quantities reported with marginal intervals and no simultaneous statement, which support no claim of any kind: the pooled swap effect across both orders, the order interaction, uptake by arm, joint compliance, target failure by subject area, target failure by wording index, the target-alone rate, the topic-alone rate, the greedy replication, and the human-written baseline.

---

## 15. What a null result means

A result showing no meaningful interference requires an equivalence test. Failure to exclude zero is never reported as absence.

For each primary estimand, the equivalence region is $[-0.10, +0.10]$. Equivalence is declared when the 95% simultaneous interval for that estimand lies wholly inside the region. That rule is conservative relative to two one-sided tests at the 5% level, because it applies a family-adjusted 95% interval where the two one-sided procedure would apply a marginal 90% interval.

For each exchangeability contrast, the equivalence region is $[-0.05, +0.05]$, and the same rule applies. All three contrasts satisfying it establishes the reference set as exchangeable and licenses the Level 2 claim of Section 11.

Three outcomes are distinguished for every primary estimand, and each has a fixed wording.

| Condition | What is reported |
|---|---|
| The simultaneous interval excludes zero and the estimate exceeds the achieved detectable effect | The focal constraint changed target failure by the estimated amount under the registered conditions |
| The simultaneous interval lies wholly inside $\pm 0.10$ | Any effect present is smaller than the smallest effect of interest under the registered conditions |
| The simultaneous interval includes zero and extends beyond $\pm 0.10$ | The study does not resolve this quantity, together with the achieved detectable effect and the realised discordance |

One executable check enforces this. The analysis emits claim strings from a fixed vocabulary. Any string asserting absence, equivalence, or negligibility is produced by a single function whose precondition is that the simultaneous interval lies inside the declared region, and the analysis aborts when that function is reached with the precondition false.

---

## 16. Manipulation checks, compliance checks, and arm symmetry

Four checks run on the confirmatory data. Every one is computed separately from the primary estimate. None is a covariate, a filter, a stratifier, or a weight in any primary formula.

**Manipulation check: treatment delivery.** Uptake of the added constraint is computed per arm. The recorded quantities are uptake in the focal arm, uptake in each reference arm, and the focal-to-reference difference in uptake for each reference with simultaneous intervals. When any absolute difference exceeds 0.25 with its interval excluding zero, the primary estimate is reported with a fixed interpretation block stating that the compared arms delivered their treatments at materially different rates. The estimate itself stands unchanged, because it is an intention-to-treat quantity and conditioning on uptake would select on a consequence of the treatment.

**Compliance check: normal operating conditions.** Two passive measures are recorded for every generation: response length in words, and whether the generation stopped because it reached the token limit. Responses of three words or fewer are flagged. Responses stopping at the token limit are flagged. Flag rates are reported per arm.

**Compliance check: instrument function.** The verifier version hash and the model revision recorded on every row are compared against the freeze record. Any mismatch aborts the run under Section 27.

**Compliance check: target feasibility.** The target-alone arm gives solo target failure on confirmatory topics. A value outside the Gate 2 admission band of Section 18 is reported beside the primary estimate, because it shows the confirmatory topics differ in difficulty from the calibration topics.

**Arm symmetry of non-behavioural failures.** The non-behavioural failure rate for an arm is the proportion of its responses that are empty, that stopped at the token limit, or that the verifier could not process. This quantity is computed for the focal arm and each reference arm, and the focal-to-reference differences form family F6 of Section 14.

Two consequences follow, and both are fixed here.

When every absolute difference in family F6 is at or below 0.05, or its simultaneous interval includes zero, the primary estimate is reported without qualification.

When any absolute difference exceeds 0.05 with its simultaneous interval excluding zero, two things happen. The primary estimate is reported with a fixed interpretation block stating that part of the contrast reflects a difference in how often a response was scorable. Partial identification bounds are computed and reported beside the estimate: each primary estimand is recalculated twice, once treating every non-behavioural response as a target pass and once treating every one as a target failure. The two recalculations give the range of values consistent with every possible outcome of the unscorable generations, and the claim rules of Section 15 are applied to the narrower of the two bounds.

---

## 17. Procedural pilot

A procedural pilot runs before any calibration or confirmatory generation. Its purpose is confirming that generation, logging, storage, verification, and analysis run end to end on real model output.

**Scale.** Twelve topics drawn from the calibration split, all six arms, both presentation orders, all four wordings of each constraint represented. Seventy-two generations.

**Quantities inspected.** Exactly four, fixed here: the count of committed rows, the proportion of generations that failed for technical reasons after retries were exhausted, the proportion of responses that stopped at the token limit, and whether every field named in the codebook of Section 28 is present and of the declared type. No target failure rate is computed. No arm difference is computed. No contrast of any kind is computed or viewed.

**Acceptance conditions.** All seven of the following hold.

1. Seventy-two of seventy-two rows are committed, each exactly once.
2. Zero generations fail for technical reasons after retries are exhausted.
3. The proportion of responses stopping at the token limit is at or below 0.10.
4. Every codebook field is present on every row and matches its declared type and domain.
5. The full analysis script runs on the pilot rows to a complete result table with no error.
6. Mutating one stored response byte changes its recorded content hash and causes the analysis to refuse that row.
7. Deleting the local cache and restoring from durable storage reproduces the same seventy-two rows with the same hashes.

**Failure consequence.** Any condition failing means the apparatus is repaired and the pilot is rerun in full.

**Data handling.** Pilot rows are discarded. They enter no calibration quantity, no confirmatory quantity, and no reported estimate. They are retained in the release as a record of the pilot.

---

## 18. Gates and freeze

Four gates run in order. Each can stop the study. All four complete before any confirmatory generation.

**Gate 0, apparatus.** The procedural pilot of Section 17.

**Gate 1, measurement.** Every verifier passes a fixed suite of forty hand-written boundary cases covering an empty answer, punctuation adjacent to a target word, capitalisation, hyphenated words, the target word inside a longer word, repeated words, non-Latin characters, and an answer cut off mid-word. The determinism test, the human agreement test, the item behaviour tabulation, and the four validity checks of Section 10 are all executed and recorded. The gate passes when determinism is exactly 1.000, when the verifier disagrees with the majority human label on at most two of the 75 cases in each class, and when every enumerated boundary case is handled as specified. Two disagreements out of 75 places the 95% Wilson upper bound on the conditional disagreement rate at 0.092, below the declared ceiling of 0.10. A higher disagreement rate stops the study and requires a verifier repair and a new protocol version.

**Gate 2, regime.** All quantities below are measured on the 96 calibration topics, one response per constraint per topic, each constraint presented alone.

- The target parameter $n$ is set to the value in $\{1,2,3\}$ whose solo failure rate is closest to 0.30. The gate requires that rate to lie in $[0.15, 0.50]$, which establishes headroom in both directions.
- The focal parameter $m$ is set to the value in $\{7,8,9,10\}$ whose solo failure rate is closest to 0.30. The gate requires that rate to lie in $[0.15, 0.55]$, which establishes that the focal constraint can be followed.
- A candidate from the pool is admitted when its solo failure rate is within 0.10 of the focal constraint's, its instruction text is within 20% of the focal constraint's length in words, and it applies to the whole answer. Admitted candidates are ranked by absolute difference in solo failure rate from the focal constraint, and the three closest are taken. The gate requires at least three admitted candidates.
- Every composition to be used is certified jointly satisfiable by a verified witness and certified free of entailment in both directions.

Failure of any condition in Gate 2 stops the study before confirmatory generation. Insufficient admitted candidates is a scientific result and is reported as such.

The calibration run produces solo failure rates for single constraints. It produces no composed condition, no focal-to-reference contrast, and no estimate of any quantity in the families of Section 14.

**Gate 3, freeze.** The constraint identities, parameter values, reference set, wordings, topic splits, prompt template, verifier source, scoring rule $S_0$ and the three alternatives, model revision, decoding settings, seed rule, block plan, family declarations, equivalence regions, codebook, container image digest, and the whole of this analysis plan are recorded and hashed. Confirmatory generation begins after the freeze record exists.

No confirmatory outcome may influence any frozen field. Calibration topics never appear in the confirmatory set. Any change to a frozen field after confirmatory generation begins creates a new protocol version, and the original result is reported unchanged.

---

## 19. Masked analysis

Confirmatory analysis proceeds in two phases. The masked phase allows the pipeline to be checked and unexpected data problems to be diagnosed with decisions kept independent of the result.

**Constructing the mask.** After confirmatory generation completes and before any analysis runs, the pipeline permutes the arm labels of the four primary arms independently within each block, using a seed drawn from the system random source. The permuted table is written to the working directory. The true labels are written to a separate mask key file. The content hash of the mask key file is recorded in the run record at the moment it is written.

**Masked phase.** All planned analysis code executes on the permuted table. All reading of response text, all coding of failure categories, all inspection of compliance and symmetry quantities, and all diagnosis of anomalies happen in this phase.

Decisions permitted in the masked phase: repairing a defect in analysis code; adding a diagnostic output; declaring an anomaly and fixing the rule that will handle it.

Decisions forbidden in the masked phase and afterwards: changing an estimand, a family, an equivalence region, the reference set, a scoring rule, a verifier, a claim rule, or the topic splits.

**Unmasking.** The mask key is applied by a single named function, invoked once. Its invocation writes a timestamped entry to the run record together with the content hash of the analysis code at that moment. The planned analysis then runs on the true labels and the outputs are recorded.

**After unmasking.** Any change to analysis code after the unmask timestamp is labelled post-unmasking in the release and supports no primary claim. The masked-phase and unmasked-phase outputs are both released.

Three executable checks enforce this.

1. The permuted labels differ from the true labels in at least half of the blocks, asserted at mask construction.
2. The mask key file is unreadable by the analysis code outside the unmask function, asserted by a test that the file is opened exactly once during a full run.
3. The recorded analysis code hash at unmasking matches the hash of the code that produced every masked-phase output, asserted by rerunning the masked phase from the recorded hash and comparing outputs byte for byte.

---

## 20. Analysis

The analysis runs in a fixed order.

1. Load confirmatory rows. Reject any row whose prompt hash, model revision, verifier hash, or block identity falls outside the frozen plan.
2. Assert that the complete matrix of 384 blocks by 6 arms exists, with exactly one accepted response per cell.
3. Apply the scoring rule $S_0$ to every response to obtain $F_{i,q}$.
4. Compute the compliance checks and the arm symmetry quantities of Section 16.
5. Form the block contrasts $D_i$.
6. Run the block bootstrap with 10,000 resamples, stratified by presentation order, resampling blocks and carrying all six arms of each drawn block.
7. Compute simultaneous intervals within each family declared in Section 14.
8. Apply the claim rules of Section 15, together with the interpretation and bounding rules of Section 16.

The analysis fails closed. A missing cell, a duplicate accepted response, a non-finite standard error, or a non-finite simultaneous bound returns a named inconclusive status for the affected quantity and computes no claim. A degenerate contrast whose block values are all identical stays in the calculation and is reported. No reference, block, or arm is dropped, and no missing cell is averaged around.

The design is fixed size. There is no interim analysis, no optional stopping, and no adaptive sample size.

---

## 21. Prohibited quantities in primary estimates

The following are recorded for every generation and never enter a primary estimate as a covariate, a filter, a stratifier, or a weight: response length, realised token count, truncation status, finish reason, compliance with the added constraint, refusal status, malformed-output status, failure category, and any other quantity produced during or after generation. The analysis code asserts this rule by checking the declared causal role of every field named in a primary formula and refusing any field whose role is post-treatment.

---

## 22. Secondary analyses

Every quantity below is reported with its interval and is labelled secondary. None can change a primary conclusion. Members of families F3, F4, F5, and F6 carry simultaneous intervals within their family. The remainder carry marginal intervals and support no claim.

- The pooled swap effect over both orders.
- The order interaction, defined as the difference between the two order-conditional effects.
- Per-reference contrasts, family F3.
- The primary estimands recomputed under scoring rules $S_1$, $S_2$, and $S_3$, family F4.
- Failure-category differences, family F5.
- Non-behavioural failure differences, family F6.
- Uptake of the added constraint by arm, order, and wording.
- Joint compliance, the probability that both active constraints pass.
- Target failure by topic subject area.
- Target failure by wording index, for both the target and the added constraint.
- The graded quantity $|{\text{count}} - n|$ by arm.
- The greedy-decoding replication on 96 blocks, reported as a sign-stability check.
- The target-alone arm, giving solo target failure under confirmatory topics.
- The topic-alone arm, giving the rate at which an unconstrained answer satisfies the target constraint by chance.

---

## 23. Error analysis

Every target failure in the four primary arms is assigned to exactly one of nine categories by a deterministic program applied in the priority order below. The first matching category is assigned.

| Order | Category | Detection rule |
|---:|---|---|
| 1 | Empty | The response contains no non-whitespace character |
| 2 | Cut off | The generation stopped because it reached the token limit |
| 3 | Refusal | The response matches one of twenty frozen refusal patterns and contains no answer text |
| 4 | Restatement | The character overlap between the response and the instruction text exceeds 0.60 under a frozen similarity function |
| 5 | Target word only inside longer words | The $S_0$ count is zero and the $S_2$ count is positive |
| 6 | Zero occurrences | The $S_0$ count is zero |
| 7 | Too few | The $S_0$ count is positive and below $n$ |
| 8 | Too many | The $S_0$ count exceeds $n$ |
| 9 | Other | No rule above applies |

Four analyses follow.

**Distribution comparison.** The focal-to-reference difference in the rate of each category forms family F5 of Section 14, computed with the block bootstrap.

**Confounder check.** Within each arm, target failure is described as a function of response length in words, truncation status, refusal status, and topic subject area. A material association with any of these is reported as a competing explanation for the observed contrast, and the contrast is recomputed within strata of that quantity as a descriptive check.

**Scoring bias check.** Within the 150 adjudicated responses of Gate 1, verifier and human labels are cross-tabulated by arm and by failure category. Any concentration of disagreement in one arm or one category is reported as a scoring bias affecting the primary comparison.

**Automatic coding accuracy.** Forty failures, ten drawn at random from each primary arm, are read and categorised by hand during the masked phase of Section 19. The recorded number is the proportion of the forty on which the hand assignment matches the automatic assignment. A qualitative summary of those forty accompanies the counts.

---

## 24. Contamination

Three sources of contamination are addressed.

**Topic contamination.** Every topic is newly written for this study. No topic reuses text from a public dataset, benchmark, or examination. At release, the exact text of each confirmatory topic is queried against a public web search index, and the number of topics returning an exact-phrase match is reported.

**Accidental compliance.** The topic-alone arm measures how often an unconstrained answer satisfies the target constraint by chance. A high rate would show the target constraint is satisfied by default text, which weakens its value as an outcome. The rate is reported beside every primary estimate.

**Future contamination.** A canary string is embedded in the released dataset file so that later presence of these materials in training data is detectable. The 96 sequestered topics are held back from release and support a later re-run on uncontaminated items.

The outcome is instruction compliance, which does not depend on knowing a correct answer, so memorised answer content cannot by itself produce a pass. The topic-alone arm bounds the residual risk empirically.

---

## 25. Human labels and human baseline

Three annotators produce the Gate 1 adjudication labels. All three are adults fluent in English and are recruited from the research group. The labelling question is whether a given letter sequence appears a given number of times in a given text, which is a decidable property of the text, so annotator background is not a source of systematic variation in the label. Annotators receive written instructions, twelve worked examples, and no information about arm or added constraint. Annotator count, instructions, per-annotator agreement with the majority, and pairwise percentage agreement are reported.

For twelve randomly chosen confirmatory topics, one annotator writes an answer under the focal composition and an answer under one reference composition, without model assistance. The target compliance of these 24 answers is reported. This establishes that a competent writer satisfies both compositions and that observed failures are properties of the model.

---

## 26. Terminal outcomes

| Outcome | Condition | What is claimed |
|---|---|---|
| Positive swap effect | A primary simultaneous interval excludes zero and lies above 0.10, with exchangeability failing | The focal constraint raises target failure relative to this reference set, at that order, for this model, topic space, wording pool, load, and decoding policy |
| Positive identity-specific effect | The same, with exchangeability holding | The above, and the effect is attributable to the identity of the focal constraint, with the choice of comparison shown to be immaterial |
| Negative swap effect | A primary simultaneous interval excludes zero and lies below $-0.10$ | The focal constraint lowers target failure relative to this reference set, under the same conditions |
| Equivalence | A primary simultaneous interval lies wholly inside $\pm 0.10$ | Any effect present is smaller than the smallest effect of interest, under the same conditions |
| Inconclusive | A primary simultaneous interval includes zero and extends beyond $\pm 0.10$ | The study does not resolve this quantity at the achieved precision, which is reported |
| Reference heterogeneity | The exchangeability intervals disagree in sign or extend beyond $\pm 0.05$ | The reference set is heterogeneous. Level 1 stands and Level 2 is withheld. Per-reference contrasts are reported in full |
| Scorability asymmetry | A family F6 difference exceeds 0.05 with its interval excluding zero | The contrast is reported together with its partial identification bounds, and claims follow the narrower bound |
| Regime not found | Gate 2 fails | No operating point with headroom, deliverable treatment, and three comparable references exists in the declared pool for this model |
| Measurement not established | Gate 1 fails | The verifier does not meet the declared reliability and validity standards, and no behavioural claim is made |
| Apparatus not established | Gate 0 fails after repair and rerun | The pipeline does not run end to end, and no data are collected |

Every outcome is reported with the full set of estimates and intervals, whether or not a claim is licensed.

---

## 27. Execution integrity

Every generation is recorded with the block identity, arm, order, wording indices, prompt hash, model revision, backend version, container image digest, hardware class, seed, raw response text, response content hash, token counts, finish reason, and every verifier verdict with its source hash.

The run aborts on any of the following: a prompt exceeding the context limit; a change in model revision inside a run; a hardware class differing from the frozen value; a container image digest differing from the frozen value; a prompt hash absent from the frozen plan; two accepted responses for one cell; a verifier source hash differing from the frozen value; a stored response whose content hash differs from the recorded value.

These are the only permitted stops. None depends on an observed outcome.

---

## 28. Codebook and computational environment

**Codebook.** Every recorded table is accompanied by a codebook containing one row per variable, with six fields: name, type, permitted values or range, units, causal role, and a one-sentence definition in plain language. Causal role takes one of six values.

| Causal role | Meaning | Permitted use |
|---|---|---|
| Identity | Names a row or a group of rows | Joining, grouping, resampling |
| Treatment | Records the condition assigned | Defining contrasts |
| Design | Records a choice fixed before generation | Blocking, stratifying, describing |
| Outcome | Records a verifier verdict on the target constraint | Primary estimates |
| Post-treatment | Records something produced during or after generation | Diagnostics and secondary description only |
| Provenance | Records how the row was produced | Integrity checks |

Four executable checks enforce the codebook.

1. Every column in every released table appears in the codebook, and every codebook row appears as a column.
2. Every recorded value falls inside its declared domain and matches its declared type.
3. No field whose role is post-treatment appears in any primary formula, checked by the assertion of Section 21.
4. Every field declared as constraining execution is consumed by a named check in Section 27, so that a declared field cannot be inert.

**Computational environment.** All generation, verification, and analysis run inside one container image. The image contains a lockfile pinning the operating system version, the Python version, and the exact version of every package. The image digest is recorded in the freeze record of Section 18 and asserted on every generation.

Two executable checks enforce the environment.

1. Rerunning the full analysis inside the recorded image, on the released raw responses, reproduces the released result table byte for byte.
2. Deleting the local cache and restoring from durable storage reproduces every row with matching content hashes, and regenerates nothing already committed.

**Raw data.** Raw responses are written once, never edited, and carry a content hash computed at write time. Derived tables are regenerated from raw responses by the analysis script and are never edited by hand.

---

## 29. Relation to existing evaluations

Benchmarks of instruction following score joint satisfaction across several verifiable instructions and report an aggregate pass rate. Those designs vary the identity of instructions together with their number, so the identity of an added instruction and the increase in load contribute to the same score. The present design fixes the number of constraints at two in both compared prompts, so identity is the only quantity that varies.

Studies of compositional constraint satisfaction sweep the number of simultaneous constraints and report how satisfaction decays as constraints accumulate. Those studies characterise the effect of load. The present design characterises the effect of identity at fixed load, which is a distinct quantity: a population whose average effect of identity is zero can contain large effects for specific pairs.

Studies of prompt sensitivity vary surface wording and report score variation. Wording variation appears here as a designed factor with four frozen wordings per constraint, assigned at block level and shared across arms, so the estimand averages over the wording pool while each comparison stays wording-matched.

The measurement built here is an experimental contrast. Its output is one risk difference per presentation order with an uncertainty interval, together with the evidence deciding what that difference is attributable to. It ranks no models and produces no leaderboard score.

---

## 30. Limitations and design trade-offs

**Narrow scope.** One model, one language, one target constraint, one focal constraint, one constraint family for the references, a load of two, one prompt template, one topic space, one decoding policy, single turn, no tools. Every claim carries these as conditions.

**Exact verifiability costs realism.** The constraints are character-level lexical rules chosen so that a fixed program decides compliance without ambiguity. Real deployments contain style and content rules that resist exact verification. The trade accepted here is that a measurement whose meaning is stable under the treatment is a precondition for interpreting any effect, and character-level rules deliver that stability.

**Comparability is tested after the fact.** References are matched before generation on solo difficulty, instruction length, and scope, which are measurable without touching the target constraint. Comparability with respect to the target is measured afterwards by the exchangeability contrasts. This ordering avoids predicting comparability from behaviour on unrelated constraints, and it accepts that a heterogeneous reference set can only be discovered after the confirmatory run. The reference set is never revised in response to the confirmatory outcome.

**The topic bank bounds precision.** Blocks are topics, and the bootstrap resamples topics, so precision is governed by the number of topics. A bank of 384 confirmatory topics supports a simultaneous detectable effect near 0.10 at the assumed discordance, and it cannot resolve effects below 0.070 at any discordance in the planning range. Generalisation extends to the declared task space of short open-ended informational questions.

**Order is a designed factor.** Earlier exploratory work in this programme found presentation order to be a large moderator, so the two order-conditional effects are declared as separate primary quantities and the pooled effect is secondary. This doubles the primary family and halves the blocks available to each quantity.

**One direction only.** The reciprocal effect is not estimated, so the study establishes the effect of the focal constraint on the target and says nothing about the effect of the target on the focal constraint.

**Stochastic decoding contributes noise.** One sample per cell means decoding variability enters the block-level contrast. The greedy replication on 96 blocks checks whether the sign of the effect survives deterministic decoding.

**Reliability evidence is generated in-house.** No prior instrument for this construct exists, so all reliability and validity evidence comes from this study's own calibration data and its own annotators. Independent replication of the verifier's agreement with human judgement on a differently constructed corpus would strengthen it.

**Masking is single-custodian.** The mask key is held in a file the analysis code opens once at the unmask step, without a second person holding it. The protection rests on the recorded hashes and timestamps of Section 19, which make a masked-phase decision distinguishable from a post-unmasking one in the record.

---

## 31. Release

The following are released under a permissive licence at the time the results are reported: all 480 released topics with the canary string, the 96 sequestered topics withheld, all constraint wordings, all verifier source code, the four scoring rule implementations, the frozen protocol record with its hashes, the container image and its lockfile, the codebook, every prompt, every raw response with its content hash, every verifier verdict, the human labels, the pilot rows and pilot report, the masked-phase outputs, the unmasked-phase outputs, the run record with the unmask timestamp, the analysis code, and the machine-readable result table containing each estimate, its family, its standard error, its marginal and simultaneous bounds, its realised discordance, its achieved detectable effect, and its cell counts.

Every reported figure is reproducible from the machine-readable result table without regenerating any response, and every number in that table is reproducible from the raw responses inside the recorded container image.

---

## 32. Construct validity checklist responses

Responses follow the checklist of [Bean et al. (2025)](https://arxiv.org/abs/2511.04703).

| Checklist item | Response |
|---|---|
| Provide a precise and operational definition for the phenomenon | Section 2. The definition is a risk difference on the target-failure scale with the number of constraints held fixed |
| Specify the scope and acknowledge excluded aspects | Section 3. Six neighbouring phenomena are named and excluded, four of them by an executable gate |
| Identify sub-components and measure them separately | Section 2. The swap effect and reference exchangeability are separate estimands with separate families and separate intervals |
| Control for unrelated tasks that may affect results | Sections 8, 16, and 22. The target-alone arm measures solo target difficulty and the topic-alone arm measures accidental compliance. Both prompts in every contrast carry the same number of constraints, the same authority level, the same template, and the same topic |
| Assess the impact of format constraints on performance | Sections 9, 16, and 23. Truncation, refusal, malformed output, and restatement are counted by arm, enter the failure taxonomy, and are subject to the arm-symmetry rule with partial identification bounds |
| Validate automated output parsing | Sections 5, 9, 10, and 18. Parse independence is established by inspection, the scoring rule and three alternatives are fixed before generation, determinism is tested at 1.000, forty boundary cases are enumerated per verifier, and 150 blinded human labels bound the conditional disagreement rate below 0.10 in each truth class |
| Employ sampling strategies for representativeness | Section 6. Twelve declared subject strata, 48 authored questions per stratum, seeded random assignment to disjoint splits |
| Verify quality and relevance of all task items | Sections 6 and 10. Every question is verified individually against four written rules, and item behaviour is tabulated for floor, ceiling, and uninformative topics |
| Include items testing known model sensitivities | Sections 7, 8, and 22. Two presentation orders, four wordings per constraint, three alternative scoring rules, and a greedy-decoding replication on 96 blocks |
| Document whether a previous dataset is adapted | Section 6. No dataset is adapted. All 576 topics are newly written and no public benchmark item is reused |
| Report strengths and limitations of adapted prior work | No prior dataset is adapted, so no comparison applies |
| Compare performance against the original dataset | No prior dataset is adapted, so no comparison applies |
| Explain modifications to reused datasets | No dataset is reused, so no modification applies |
| Implement contamination tests | Section 24. Exact-phrase search of every confirmatory topic at release, plus the topic-alone arm as an empirical bound on accidental compliance |
| Maintain a held-out set | Section 6. 96 sequestered topics are withheld from release and from this study |
| Investigate pre-exposure of source materials | Section 24. Topics are newly written. The outcome depends on instruction compliance alone, and the topic-alone arm quantifies the residual risk |
| Report sample size and justify statistical power | Section 13. 384 blocks, 192 per order, with marginal and family-adjusted detectable effects tabulated against block discordance, the smallest effect of interest justified in Section 11, three excluded planning sources named, and the topic bank identified as the binding resource |
| Report uncertainty estimates for all primary scores | Sections 11, 13, 14, and 20. Block bootstrap with 10,000 resamples, six enumerated families each with its own simultaneous interval, marginal intervals reported alongside, and every quantity reported whether or not a claim is licensed |
| Describe human rater demographics and mitigate bias | Section 25. Three annotators, blinded to arm and added constraint, labelling a decidable property of the text, with agreement statistics reported |
| Use metrics capturing variability of subjective labels | Sections 9 and 10. The primary metric is an exact character test with no subjective component, its determinism is tested, and its reliability is reported as verifier-to-human agreement. The block bootstrap carries the full variability of the binary outcome |
| Conduct qualitative and quantitative failure analysis | Section 23. A nine-category priority-ordered taxonomy applied to every failure, compared across arms as family F5, plus forty hand-coded failures read during the masked phase |
| Investigate whether failures correlate with confounders | Section 23. Target failure is described as a function of response length, truncation, refusal, and subject area within each arm, and any material association is reported as a competing explanation |
| Identify scoring biases revealed by error analysis | Sections 16 and 23. Verifier and human labels are cross-tabulated by arm and category, and the arm-symmetry rule triggers partial identification bounds when scorability differs across arms |
| Propose directions to improve scores | Section 26. Each terminal outcome states what it licenses and what follows. Reference heterogeneity directs work to the reference set, a regime failure directs work to the constraint pool, a measurement failure directs work to the verifier, and an apparatus failure directs work to the pipeline |
| Justify relevance with real-world applications | Sections 11 and 29. Product system prompts stack several rules at once, and a change of 0.10 in target failure moves a system prompt from 80% compliance to 70% |
| Provide rationale for tasks and metrics tied to the definition | Sections 2, 5, 9, and 10. The definition is a difference in target-failure probability, the metric is the target failure indicator under scoring rule $S_0$, and the constraint pool is chosen so that the metric's decision procedure is unaffected by the treatment |
| Compare with existing evaluations of similar phenomena | Section 29. Instruction-following benchmarks, constraint-count sweeps, and prompt-sensitivity studies are each distinguished from this design |
| Discuss limitations and design trade-offs | Section 30. Scope, verifiability against realism, the timing of the comparability test, the topic bank as the precision constraint, order as a designed factor, the single direction, decoding noise, in-house reliability evidence, and single-custodian masking |
