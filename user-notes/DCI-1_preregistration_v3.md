# Preregistration: Does replacing one instruction with a comparable instruction change compliance with a different instruction?

**Protocol identifier:** DCI-1
**Version:** 3.0, for registration
**Date:** 16 August 2026
**Confirmatory data collected at the time of registration:** none
**Registration target:** Open Science Framework, protocol-document format

**Design provenance:** Version 3 was designed after inspection of the completed v2 qualification, pilot, and calibration records. Version 2 ended with four terminal model replications and zero confirmatory generations. Section 33 records the v2 outcomes and the changes made before this new registration.

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
| Model replication | One complete application of this protocol to one registered model, with its own qualification, gates, calibration, freeze, confirmatory dataset, estimates, and terminal outcome. |
| Cached draw | One of sixteen stochastic completions generated for one confirmatory prompt cell. Cached draws lie below the observation level. |
| Primary observation | The single cached draw selected for the primary dataset by the frozen hash rule. |
| Pseudo-run | A secondary dataset formed by selecting one cached draw per confirmatory cell. |
| Reference family | A structurally distinct kind of reference constraint with a registered severity grid. |
| Severity level | One registered parameter value within a target, focal, or reference family. |
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
| Reachability | The mathematical capacity of the realised comparison baseline to express an effect at least as large as the declared smallest effect of interest in a stated direction. |
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
| Qualification | The non-scientific stage that verifies code, model, environment, prompt-plan, cache, schema, and provenance requirements before the procedural pilot. |
| Gate record | A content-addressed record containing the gate decision, criterion, threshold, observed value, producing code and environment, inputs, outputs, and timestamp. |
| Generated artifact | Model output exists in temporary or durable storage but has not yet passed every integrity and stage-authorisation check. |
| Committed artifact | Immutable bytes and their content hash have been written to durable storage. |
| Accepted artifact | A committed artifact that passed integrity checks and belongs to an authorised protocol stage. |
| Superseded artifact | An artifact retained for audit and mechanically excluded from scientific evidence. |
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

The study measures the swap effect for one target constraint, one focal constraint, three references selected from distinct registered reference families, four language-model replications, one registered decoding policy per model, one prompt template, one language, one topic space, and a load of two constraints. Every model produces a separate model-conditional result. The study contains no pooled cross-model estimand and licenses no claim about models in general.

Six neighbouring phenomena fall outside the scope and are excluded by design.

**Load-driven degradation.** The decrease in compliance caused by adding constraints of any kind. Both compared prompts carry exactly two constraints, so this quantity is held fixed and is not estimated here.

**Logical impossibility.** A prompt whose constraints cannot all be satisfied forces a failure. Every composition used is certified jointly satisfiable by an explicit witness before generation, so failures observed here occur where success was available.

**Entailment and redundancy.** A prompt in which satisfying one constraint automatically satisfies another produces compliance for logical reasons. Every composition used is certified free of entailment in both directions before generation.

**Mechanism.** The internal computation that produces the behaviour. The design measures behaviour under an intervention and is silent on internal mechanism.

**The reciprocal effect.** The effect of the target constraint on compliance with the focal constraint. This requires a separate design in which the roles are exchanged, and it is not estimated here.

**Generalisation.** Behaviour under other models, target or focal constraint families, languages, loads, prompt formats, or inference policies. Each claim is conditional on one registered model and its frozen configuration. Repetition across the four models is reported as replication evidence, without pooling.

---

## 4. Models, replication order, and inference policy

The four registered model replications are:

| Execution order | Model label | Canonical repository | Registered interpretation |
|---:|---|---|---|
| 1 | Gemma 3n E2B-it | [`google/gemma-3n-E2B-it`](https://huggingface.co/google/gemma-3n-E2B-it) | Instruction-tuned Gemma replication and first test of the redesigned reference system |
| 2 | Qwen3-4B hybrid, thinking disabled | [`Qwen/Qwen3-4B`](https://huggingface.co/Qwen/Qwen3-4B) | Hybrid Qwen model evaluated with thinking disabled; this is not described as a pretrained-base model |
| 3 | Qwen3-4B instruct-only | [`Qwen/Qwen3-4B-Instruct-2507`](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) | Instruct-only Qwen replication |
| 4 | Gemma 3n E4B-it | [`google/gemma-3n-E4B-it`](https://huggingface.co/google/gemma-3n-E4B-it) | Instruction-tuned Gemma replication |

The exact repository revision for every model is entered in the signed study-wide registration manifest before qualification and is asserted at every generation. If a listed repository identifier is unavailable at registration, v3 is not opened; changing the model identity requires a new protocol version.

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
| Maximum new tokens | Model-adaptive choice from \(\{512,768,1024\}\) under the pre-screen rule of Section 18 |
| Calibration draws per cell | 1 |
| Confirmatory cached draws per cell | \(M=16\) |
| Primary observations per cell | 1, selected from the cache by the frozen hash rule |
| Seed | Derived from the fixed root seed, exact prompt hash, model identifier, and cached-draw index |
| Prompting | Zero-shot. No examples, tools, retrieval, self-consistency, best-of-N selection, revision passes, or additional turns |

For confirmatory cell \(c\), the primary cached-draw index is

$$j_c = H(\texttt{primary-root},\texttt{model-id},\texttt{prompt-hash}) \bmod 16,$$

where \(H\) is the hash function fixed in the study-wide manifest. Response contents cannot affect this choice. The estimand averages over the registered decoding policy through one selected response per prompt cell. The other fifteen cached draws enter only the pseudo-run sensitivity analysis of Section 22. No model internals are read.

E2B runs first. If it terminates with `REFERENCE_POOL_MISMATCH` or `COMPOSED_HEADROOM_FAILURE`, the remaining three v3 replications do not start. Any redesign prompted by that result requires v4. If E2B passes, the remaining models use the already frozen study-wide rules.

Study-wide rules are frozen before E2B qualification. Outcomes from one v3 replication cannot change the protocol for a later replication. Model adaptation is confined to the mechanical selection of \(n\), \(m\), reference severity and identity, and completion-token cap specified in Section 18.

| Model-adaptive through Section 18 | Study-wide fixed before E2B |
|---|---|
| \(n\), \(m\), completion-token cap, one severity per eligible reference family, and the final identities of three references | Constraint families and severity grids, selection algorithms and tie-breakers, the \(B\)-to-\(R\) caliper, number and structural diversity of references, estimands, equivalence regions, multiplicity families, bootstrap, decoding-policy form, masking rules, gate rules, artifact semantics, and claim vocabulary |

---

## 5. Constraints and reference families

The target constraint is:

> **A:** Use the word *however* exactly $n$ times.

The focal constraint is:

> **B:** Every word in the answer must have at most $m$ letters.

The registered grids are

$$n\in\{1,2,3,4,5,6,7,8\},\qquad m\in\{7,8,9,10\}.$$

The word *however* has seven letters, so every focal severity leaves the composition satisfiable.

The reference pool contains eight structurally distinct families with four severity levels each. All constraints are single-clause, apply to the whole answer, and are decided by deterministic character operations. A word is a maximal run of alphabetic characters. Suffix and letter tests use the lower-cased word. Comma and upper-case counts operate on the raw response characters.

| Family | Identifier | Constraint template | Registered severity grid, least to most restrictive |
|---|---|---|---|
| Initial-letter budget | RF1 | At most $q$ words in the answer may begin with the letter b. | $q\in\{8,5,2,0\}$ |
| Suffix budget | RF2 | At most $q$ words in the answer may end with the letters ing. | $q\in\{8,5,2,0\}$ |
| One-letter-word budget | RF3 | At most $q$ words in the answer may have one letter. | $q\in\{8,5,2,0\}$ |
| Doubled-letter budget | RF4 | At most $q$ words may contain two identical adjacent letters. | $q\in\{6,4,2,0\}$ |
| Comma budget | RF5 | The answer may contain at most $q$ comma characters. | $q\in\{12,8,4,0\}$ |
| Upper-case budget | RF6 | The answer may contain at most $q$ upper-case English letters. | $q\in\{12,8,4,0\}$ |
| Letter-a budget | RF7 | At most $q$ words in the answer may contain the letter a. | $q\in\{24,16,8,0\}$ |
| Final-y budget | RF8 | At most $q$ words in the answer may end with the letter y. | $q\in\{8,5,2,0\}$ |

The severity grids are constructed to span easy, intermediate, and restrictive forms and to offer candidates near the expected focal solo-failure region of 0.20 to 0.35. This range guides pool construction and is not an inferential threshold. Admission continues to use the model-specific focal rate and the frozen $\pm0.10$ caliper in Section 18.

At most one severity level from a family can enter the final reference set. The three final references must come from three different families. This prevents three severity settings of one underlying rule from being treated as three independent control constructions.

Four properties are established before generation and asserted by executable tests.

**Parse independence.** The target verifier receives response text, target identity, and $n$. It receives no added-constraint identity, arm label, reference-family identity, or secondary-verifier output. The target scoring rule is identical in every arm.

**Joint satisfiability.** For every $n$, $m$, family, and severity, the protocol contains a machine-verified answer satisfying both $A$ and the added constraint. Only compositions with a verified witness can enter calibration or confirmation.

**Non-entailment.** For every eligible composition, the protocol contains one verified response satisfying $A$ and failing the added constraint and one satisfying the added constraint and failing $A$.

**Wording equivalence.** Each target, focal, and reference-family template has four frozen wordings. The wordings are written before qualification, checked for identical meaning, and required to return identical verifier behaviour on a fixed set of twenty test responses at every severity.

---

## 6. Topics

The task space is short open-ended informational questions that a competent writer can answer in sixty to one hundred and twenty words without tools, arithmetic, or recall of a specific named fact.

The topic bank contains 624 questions across twelve declared subject areas, with 52 questions per area: everyday science, history, geography, food, music, sport, work and organisations, health and the body, technology, language and writing, art and design, and the natural world.

Questions are drafted by the researcher with model assistance and then verified one by one against four rules: answerable from general knowledge, no single correct short answer, no reused text from any public dataset or examination, and no wording that itself mentions any letter, word length, word shape, punctuation-count, or capitalisation requirement.

Within each subject area the 52 questions are randomly shuffled with a fixed seed and split into 12 calibration questions, 32 confirmatory questions, and 8 sequestered questions. The calibration split is divided further into 2 pre-screen questions, 8 final solo-calibration questions, and 2 composed-validation questions per area. The resulting disjoint sets are:

| Set | Topics | Permitted use |
|---|---:|---|
| Pre-screen | 24 | Cheap severity and response-length viability screening; naturally generated Gate 1 validation material |
| Final solo calibration | 96 | Mechanical selection of $n$, $m$, and one candidate severity per reference family |
| Composed-reference validation | 24 | Headroom and reachability checks for $A+R$ only |
| Confirmatory | 384 | Frozen six-arm confirmatory experiment |
| Sequestered | 96 | Future uncontaminated rerun only |

The twelve procedural-pilot topics are one fixed topic from each subject area in the pre-screen set. Pilot outputs are kept in a separate namespace, no scientific quantity is computed from them, and later pre-screen generations are new rows with new stage identifiers.

The sequestered topic texts remain inaccessible to the design and execution team throughout v3 redesign, qualification, calibration, and confirmation. Their identities and pre-existing content hashes may be held by the access-control process. Their text is opened only under a separately registered future rerun.

This is stratified random sampling: the task space is divided into twelve declared strata, an equal number of items is authored per stratum, and assignment to disjoint sets is random within stratum.

---

## 7. Prompt construction

Every prompt has the same three parts in the same order: the topic question, a numbered list of the active constraints, and the line `Answer:`.

Within a block, the prompts being compared are identical byte for byte except for the single line stating the added constraint. Confirmatory block index $i$ determines three things, fixed across all arms of that block:

- **Presentation order.** Blocks with even index place the target constraint first. Blocks with odd index place the added constraint first. This yields 192 blocks in each order.
- **Target wording.** The wording index for $A$ is $i \bmod 4$.
- **Added wording.** The wording index for the added constraint is $\lfloor i/4 \rfloor \bmod 4$.

The 12-block pilot uses the stage-specific allocation

$$w_A(i)=i\bmod4,\qquad w_{\mathrm{added}}(i)=\left(i+\lfloor i/4\rfloor\right)\bmod4,$$

with presentation order $i\bmod2$. Every generative stage has an executable allocation assertion stating the intended count for every wording and order. A stage cannot start unless its generated plan satisfies those counts. A formula is secondary to the coverage assertion: if a formula and an assertion disagree, qualification fails.

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

Each arm defines one prompt cell per block. Sixteen cached stochastic draws are generated for each cell, and exactly one becomes the primary observation through the hash rule in Section 4. Each model therefore contains $384\times6=2{,}304$ confirmatory cells, $2{,}304\times16=36{,}864$ cached draws, and 2,304 primary observations.

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

**Human agreement.** Naturally generated pre-screen and dedicated measurement-validation responses form a reservoir before human labels are opened. If either verifier class contains fewer than 150 cases, the pipeline generates the frozen set of up to 300 additional measurement-validation responses across the registered target-severity grid. Within each verifier class, a fixed seeded sample of $\min(150,N_c)$ responses is then drawn, where $N_c$ is the available natural count after the reservoir closes. Three annotators label every sampled response. The one-sided 95% Wilson upper bound on verifier-to-majority disagreement is computed once in each class. The gate requires both upper bounds to be at most 0.10. Annotators see the response text and target constraint text and see no arm, model label, added constraint, or automated verdict. Hand-authored responses cannot fill a natural-response class. A bound above 0.10 with 150 cases returns `MEASUREMENT_NOT_ESTABLISHED`; a bound above 0.10 with fewer than 150 cases because the natural class is exhausted returns `MEASUREMENT_EVIDENCE_INSUFFICIENT`.

The complete 150-item E2B packet created during v2 is annotated before E2B Gate 1. It may supply v3 evidence only when the construct definition, normalisation, target-verifier source, boundary specification, and relevant configuration hashes are byte-identical. The carry-over record names the source packet, records every hash, and reports the v2 provenance. Any mismatch requires a new packet.

**Item behaviour.** Target failure is tabulated by topic during scientific calibration and confirmation. The recorded numbers are the proportion of topics at floor, the proportion at ceiling, and, after confirmation, the proportion whose verdicts are identical in every primary arm. This is a regime and precision diagnostic evaluated in Gate 2 and the confirmatory report. It is not a Gate 1 measurement-validity criterion.

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

Two primary estimands are declared per model replication, one per presentation order:

$$\tau_{\text{target-first}} = \mathbb{E}\left[D_i \mid \text{order} = \text{target first}\right], \qquad \tau_{\text{added-first}} = \mathbb{E}\left[D_i \mid \text{order} = \text{added first}\right].$$

Three exchangeability contrasts are declared, computed over all 384 blocks:

$$\delta_{jk} = \mathbb{E}\left[F_{i,R_j} - F_{i,R_k}\right], \qquad (j,k) \in \{(1,2), (1,3), (2,3)\}.$$

The smallest effect of interest is a risk difference of 0.10. A change of that size converts a system prompt with 80% target compliance into one with 70% target compliance, which is one additional failure in every ten responses. The exchangeability margin is 0.05. Both values are fixed here and are used unchanged in the analysis.

Let

$$\bar p_R=\frac13\sum_{j=1}^{3}P(F_A=1\mid A+R_j).$$

Because $\tau$ lies in $[-\bar p_R,1-\bar p_R]$, effects of both $-0.10$ and $+0.10$ are mathematically reachable only when $\bar p_R\in[0.10,0.90]$. Gate 2 uses the buffered requirement that every composed-reference rate lies in $[0.15,0.85]$. The present two-sided estimands and claim rules therefore retain reachability in both directions.

Two claim levels are defined, and the exchangeability result decides which applies.

**Level 1, a swap effect.** Replacing the reference set with the focal constraint changed target compliance under the registered conditions. This is licensed by the design whenever the gates in Section 18 pass.

**Level 2, an identity-specific effect.** The focal constraint damages the target more than comparable constraints do. This is licensed only when all three simultaneous exchangeability intervals lie inside $\pm 0.05$.

Pre-confirmatory $B$-to-$R$ comparability and post-confirmatory $R$-to-$R$ exchangeability are separate requirements. Gate 2 establishes comparability using solo difficulty, instruction length, scope, structural family identity, satisfiability, and composed headroom. The exchangeability contrasts test whether the three frozen references behave interchangeably with respect to the target after confirmation. Neither requirement substitutes for the other.

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

The design contains no independent within-cell observation level. Sixteen cached draws exist below each confirmatory prompt cell, and one frozen hash-selected draw supplies the primary observation. The remaining draws cannot increase the primary sample size, replace a missing primary observation, or enter the primary estimator. Topic-sampling uncertainty is priced by the block bootstrap. The pseudo-run analysis measures decoding sensitivity separately.

Three executable checks enforce this structure.

**Resampling unit.** Each bootstrap replicate draws exactly 192 block identifiers with replacement inside each order stratum. The analysis asserts that the number of identifiers drawn equals the stratum size and that every drawn identifier carries six primary observations.

**Function signature.** The estimator receives a table indexed by block. The analysis asserts that no primary estimator function accepts a response-level index.

**Variance behaviour.** A synthetic dataset is generated in which within-block noise is doubled and between-block variation is held fixed. The analysis asserts that the width of the interval for the block-level mean changes by less than the Monte Carlo error of the bootstrap, which confirms that the procedure prices between-block variation.

---

## 13. Sample size, precision, and what the design can detect

The sample size is justified by a smallest-effect-of-interest power analysis, combined with a resource constraint on the number of topics.

The declared planning quantities apply independently to every model replication: smallest effect of interest 0.10, target power 0.80, two-sided significance level 0.05, block as the independent unit, 384 blocks, and 192 blocks in each presentation order.

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

The cached-draw count $M=16$ enters no sample-size calculation, estimator, standard error, interval, power statement, or claim rule. The independent-unit count remains 384 blocks per model. Pseudo-runs quantify the sensitivity of results to the one stochastic completion selected within each cell and supply no additional inferential sample size.

For the exchangeability family, computed over all 384 blocks, the simultaneous half-width falls at or below 0.05 when reference-to-reference block discordance is at or below a value between 0.168 and 0.192. The lower figure uses the Šidák bound for a family of three. The three contrasts span a two-dimensional space, because $\delta_{23}$ equals $\delta_{13}$ minus $\delta_{12}$, so the Šidák bound is conservative and the upper figure uses the two-dimensional value. The bootstrap supplies the exact critical value, and the realised half-width is reported beside the exchangeability decision.

Realised discordance is measured and reported for every contrast. The achieved detectable effect implied by that realised discordance is reported beside every estimate. The proportion of uninformative topics from Section 10 is reported alongside, because topics whose verdicts are identical in every arm contribute no information to the contrast.

The formula treats a single paired binary comparison. The reference side of $D_i$ averages three arms, which lowers its noise, so the tabulated values are conservative for this design. The realised precision reported in the results comes from the block bootstrap and supersedes them.

---

## 14. Multiplicity families

Every quantity that carries an inferential statement belongs to exactly one family declared here within one model replication. The list is closed at that model's freeze. No quantity moves between families afterwards. Any quantity computed and absent from this list is exploratory and is labelled exploratory in every report. The four model replications are reported separately; this protocol defines no cross-model multiplicity family because it licenses no pooled or model-general claim.

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

Direction and scientific magnitude are evaluated separately for every primary estimand.

| Axis | Condition | Fixed interpretation |
|---|---|---|
| Positive direction | The simultaneous lower bound exceeds zero | Target failure is higher under the focal constraint than under the reference average |
| Negative direction | The simultaneous upper bound is below zero | Target failure is lower under the focal constraint than under the reference average |
| Direction unresolved | The simultaneous interval includes zero | The direction is unresolved at the registered simultaneous confidence level |
| Meaningful positive magnitude | The simultaneous lower bound exceeds $+0.10$ | The positive effect exceeds the smallest effect of interest |
| Meaningful negative magnitude | The simultaneous upper bound is below $-0.10$ | The negative effect exceeds the smallest effect of interest in magnitude |
| Equivalence | The simultaneous interval lies wholly inside $[-0.10,+0.10]$ | Any effect present is smaller than the smallest effect of interest |
| Magnitude unresolved | None of the three magnitude conditions above holds | The study does not determine whether the effect exceeds the smallest effect of interest |

Direction and equivalence can both be resolved, for example when a narrow positive interval lies wholly between zero and $+0.10$. The report states both facts. Achieved detectable effect and realised discordance are reported as precision diagnostics and do not replace the interval-based claim rules.

One executable check enforces this. The analysis emits claim strings from a fixed vocabulary. Any string asserting absence, equivalence, or negligibility is produced by a single function whose precondition is that the simultaneous interval lies inside the declared region, and the analysis aborts when that function is reached with the precondition false.

---

## 16. Manipulation checks, compliance checks, and arm symmetry

Four checks run on the confirmatory data. Every one is computed separately from the primary estimate. None is a covariate, a filter, a stratifier, or a weight in any primary formula.

**Manipulation check: treatment delivery.** Uptake of the added constraint is computed per arm. The recorded quantities are uptake in the focal arm, uptake in each reference arm, and the focal-to-reference difference in uptake for each reference with simultaneous intervals. When any absolute difference exceeds 0.25 with its interval excluding zero, the primary estimate is reported with a fixed interpretation block stating that the compared arms delivered their treatments at materially different rates. The estimate itself stands unchanged, because it is an intention-to-treat quantity and conditioning on uptake would select on a consequence of the treatment.

**Compliance check: normal operating conditions.** Response length in words and tokens, finish reason, and whether generation reached the token limit are recorded for every cached draw. Responses of three words or fewer and responses reaching the token limit are flagged. Flag rates and finish-reason counts are reported per arm. Response-length quantiles $p_{50}$, $p_{90}$, $p_{95}$, and $p_{99}$ are standard outputs of every generative gate and the confirmatory report.

**Compliance check: instrument function.** The verifier version hash and the model revision recorded on every row are compared against the freeze record. Any mismatch aborts the run under Section 27.

**Compliance check: target feasibility.** The target-alone arm gives solo target failure on confirmatory topics. A value outside the Gate 2 admission band of Section 18 is reported beside the primary estimate, because it shows the confirmatory topics differ in difficulty from the calibration topics.

**Arm symmetry of non-behavioural failures.** The non-behavioural failure rate for an arm is the proportion of its responses that are empty, that stopped at the token limit, or that the verifier could not process. This quantity is computed for the focal arm and each reference arm, and the focal-to-reference differences form family F6 of Section 14.

Two consequences follow, and both are fixed here.

When every absolute difference in family F6 is at or below 0.05, or its simultaneous interval includes zero, the primary estimate is reported without qualification.

When any absolute difference exceeds 0.05 with its simultaneous interval excluding zero, two things happen. The primary estimate is reported with a fixed interpretation block stating that part of the contrast reflects a difference in how often a response was scorable. Partial identification bounds are computed and reported beside the estimate: each primary estimand is recalculated twice, once treating every non-behavioural response as a target pass and once treating every one as a target failure. The two recalculations give the range of values consistent with every possible outcome of the unscorable generations, and the claim rules of Section 15 are applied to the narrower of the two bounds.

---

## 17. Qualification and procedural pilot

Qualification finishes before the procedural pilot. It is non-scientific and reads no model-behaviour rate. Qualification verifies that the repository is clean, the complete implementation is tracked, the model revision resolves, the dependency manifest is non-empty, the prompt plan satisfies its schema, the registered verifier and wording tests pass, the cache and durable store are reachable, and the environment and producing commit can be hashed. A failed check returns `QUALIFICATION_FAILURE` and prevents generation.

After qualification, a procedural pilot confirms that generation, sixteen-draw caching, logging, storage, verification, masking, and analysis run end to end on real model output.

**Scale.** The pilot uses twelve fixed pre-screen topics, all six logical arms, both presentation orders, and the wording allocation of Section 7. It uses fixture values $n=3$ and $m=9$ and the fixed reference fixtures RF1 at $q=5$, RF2 at $q=5$, and RF5 at $q=8$. These fixtures exercise the arm structure and cannot become scientific calibration evidence. The pilot contains 72 logical cells and 1,152 cached draws.

**Token budget.** The pilot uses 1,024 maximum new tokens. Truncation and finish reasons are recorded and reported. They do not determine apparatus qualification because response length is evaluated scientifically in the pre-screen.

**Quantities inspected.** Exactly five classes of quantity are inspected: committed and accepted cell and draw counts; technical-generation failure after retries; codebook schema validity; content-hash and cache-restoration behaviour; and successful execution of the pilot mask, commit, unmask, and analysis cycle. No target failure rate, added-constraint uptake, arm difference, or scientific contrast is computed or viewed.

**Acceptance conditions.** All eight conditions hold.

1. Seventy-two of seventy-two logical cells and 1,152 of 1,152 cached draws are committed exactly once.
2. Every logical cell has exactly one hash-selected primary pilot row.
3. Zero generations fail for technical reasons after retries are exhausted.
4. Every codebook field is present and matches its declared type and domain.
5. The full analysis pipeline runs on pilot rows to a structurally complete result table without exposing a scientific rate or contrast.
6. Mutating one stored response byte changes its content hash and makes the analysis refuse that row.
7. Deleting the local cache and restoring from durable storage reproduces every pilot row with the same hashes.
8. The separate `pilot_mask` cycle completes, records its own key and events, and leaves the `confirmatory_mask` namespace untouched.

**Failure consequence.** A failed condition returns `APPARATUS_FAILURE`. A repair creates a new producing commit and requires qualification and the full pilot to run again.

**Data handling.** Pilot artifacts have type `pilot_record`. They enter no calibration or confirmatory quantity and are retained for audit. They are never called a freeze record and contain no confirmatory-only value such as a pseudo-run count.

---

## 18. Pre-screen, measurement gate, scientific calibration, and freeze

The only permitted stage sequence is:

1. `QUALIFIED`;
2. `GATE_0_APPARATUS_PASS`;
3. `REGIME_SCREEN_PASS`;
4. `GATE_1_MEASUREMENT_PASS`;
5. `GATE_2A_SOLO_CALIBRATION_PASS`;
6. `GATE_2B_COMPOSED_VALIDATION_PASS`;
7. `GATE_3_FREEZE`;
8. confirmatory generation;
9. masked analysis;
10. unmasked analysis.

Every command verifies the content hash and signature of the predecessor PASS record. A terminal state mechanically disables every later generation command. Every attempted transition is logged with a timestamp, model revision, producing Git commit, environment digest, input hashes, output hashes, and outcome.

### 18.1 Gate 0: apparatus

Gate 0 is the procedural pilot of Section 17. It evaluates execution integrity only. Model verbosity, scientific headroom, treatment deliverability, and reference comparability cannot produce `APPARATUS_FAILURE`.

### 18.2 Regime pre-screen

The pre-screen runs on 24 topics with one response per registered severity cell. It has four purposes: choose a completion cap, reject a clearly exhausted target or focal grid, detect an obviously mismatched reference pool, and produce natural responses eligible for Gate 1 sampling. It produces no $A+B$ composition and no focal-to-reference target contrast.

**Completion cap.** A fixed, subject-balanced set of 96 pre-screen prompts is generated at each cap in $\{512,768,1024\}$, using the same prompt identities and registered seed derivation. The smallest cap whose truncation rate is at most 0.10 is selected and then held fixed for all later stages of the model replication. If no cap qualifies, the replication terminates as `RESPONSE_LENGTH_INCOMPATIBLE`. The report contains finish-reason counts and response-length quantiles $p_{50}$, $p_{90}$, $p_{95}$, and $p_{99}$ at every cap.

**Cheap difficulty screen.** At the selected cap, the pre-screen estimates the complete target, focal, and reference-family severity curves. A target or focal grid is rejected early only when the 95% Wilson intervals for every severity lie entirely on the same inadmissible side of its Gate 2 band. A focal severity is provisionally plausible when its Wilson interval intersects $[0.15,0.55]$. A reference family is provisionally plausible when, for at least one of its severities and one provisionally plausible focal severity, the 95% Newcombe interval for $p(F_R)-p(F_B)$ intersects $[-0.10,0.10]$. Fewer than three plausible families terminates the replication as `REFERENCE_POOL_MISMATCH`. Every other configuration advances to the larger independent calibration sample. Pre-screen point estimates cannot select $n$, $m$, or a reference.

When no target or focal severity is admissible, two diagnoses are distinguished. `GRID_RESOLUTION_INSUFFICIENT` applies when two adjacent severities lie on opposite sides of the entire admission band. `TARGET_RANGE_EXHAUSTED` or `FOCAL_RANGE_EXHAUSTED` applies when the registered curve reaches the severity-grid boundary while remaining on one side of the band. Every diagnosis records the complete curve and boundary value and makes a claim only about the registered grid.

### 18.3 Gate 1: measurement

Every verifier passes the forty-case frozen boundary suite covering empty response, adjacent punctuation, capitalisation, hyphenation, target text inside a longer word, repeated words, non-Latin characters, and truncation mid-word. The target verifier additionally passes the determinism, human-agreement, face-validity, content-validity, convergent-validity, and discriminant-validity checks of Section 10.

Gate 1 passes when verifier determinism is exactly 1.000, every boundary case returns its specified verdict, and the one-sided 95% Wilson upper bound on verifier-to-majority disagreement is at most 0.10 in both naturally generated verifier classes. A measured disagreement excess returns `MEASUREMENT_NOT_ESTABLISHED`. Insufficient natural evidence within the registered annotation budget returns `MEASUREMENT_EVIDENCE_INSUFFICIENT`. A verifier repair changes a frozen scientific instrument and requires a new protocol version.

### 18.4 Gate 2A: final solo calibration

Solo calibration runs on the independent 96-topic set, using one response per severity and topic at the selected completion cap.

**Target selection.** For every $n\in\{1,2,3,4,5,6,7,8\}$, the full curve $\hat p(F_A=1\mid n)$ is recorded. Eligible values lie in $[0.15,0.50]$. Among them, $n^*$ minimises distance from 0.30, with the smaller $n$ breaking an exact tie.

**Focal selection.** For every $m\in\{7,8,9,10\}$, the full curve $\hat p(F_B=1\mid m)$ is recorded. Eligible values lie in $[0.15,0.55]$. Among them, $m^*$ minimises distance from 0.30, with the smaller $m$ breaking an exact tie.

The range-exhaustion and grid-resolution diagnoses of the pre-screen apply when either selection has no eligible value.

**Reference-family selection.** Every severity in every registered family is measured alone. Within family $f$, severity $q_f^*$ minimises

$$\left|\hat p(F_{R_f}=1\mid q_f)-\hat p(F_B=1\mid m^*)\right|$$

subject to all of the following:

1. the absolute solo-failure difference is at most 0.10;
2. every frozen wording is within 20% of the corresponding focal wording's word count;
3. the constraint applies to the whole answer;
4. target-verifier parse independence holds;
5. joint satisfiability and non-entailment witnesses pass.

The less restrictive severity breaks an exact within-family tie. At most one candidate is retained per family. All eligible families advance to composed validation. Fewer than three eligible families returns `REFERENCE_POOL_MISMATCH` with the full admission table and distances.

### 18.5 Gate 2B: composed-reference validation and reachability

Every eligible family is evaluated as $A+R_f$ on the independent 24-topic composed-validation set, using the selected $n^*$ and $q_f^*$. The focal composition $A+B$ is never generated or estimated during calibration.

A reference family passes composed validation when its target-failure rate lies in $[0.15,0.85]$. The composed rate is used as an eligibility predicate only. It cannot rank references or select a value that produces a desired focal effect. Among composed-valid families, the final three are those with the smallest solo-failure distance from $B$. Family identifier breaks an exact tie. Because each chosen composed-reference rate lies in $[0.15,0.85]$, their mean permits both $-0.10$ and $+0.10$ effects.

Fewer than three composed-valid families returns `COMPOSED_HEADROOM_FAILURE`. The report identifies which solo-matched families failed composed validation. The final three remain subject to the post-confirmatory $R$-to-$R$ exchangeability test; composed validation does not establish exchangeability.

### 18.6 Gate 3: immutable model freeze

The freeze record contains the model revision, selected completion cap, $n^*$, $m^*$, final reference families and severities, every wording, topic splits, prompt template, chat-template hash, verifier sources, scoring rules $S_0$ to $S_3$, decoding settings, seed and primary-draw rules, block plan, family declarations, equivalence regions, codebook, Git commit, clean-tree assertion, dependency and environment digests, hardware record, gate-record hashes, and the complete analysis plan.

Confirmatory generation begins only after the freeze exists and verifies successfully. Calibration topics never enter the confirmatory set. Any scientific rule change after study-wide freeze creates v4. Any model-specific frozen-field change after that model's confirmatory generation begins creates a new protocol version and leaves the original terminal result unchanged.

---

## 19. Masked analysis

Confirmatory analysis proceeds in two phases. The masked phase allows the pipeline to be checked and unexpected data problems to be diagnosed with decisions kept independent of the result. Pilot masking uses the separate `pilot_mask` namespace of Section 17. Pilot mask and unmask events cannot read, create, consume, or alter the `confirmatory_mask` key or its single permitted unmask event.

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
2. Assert that the complete matrix of 384 blocks by 6 arms by 16 cached draws exists, with every raw draw committed exactly once.
3. Apply the frozen hash rule to select exactly one accepted primary observation per cell. Assert that response content and verifier output are unavailable to the selector and that pseudo-run data cannot replace a primary row.
4. Apply the scoring rule $S_0$ to every primary observation to obtain $F_{i,q}$.
5. Compute the compliance checks and the arm symmetry quantities of Section 16.
6. Form the block contrasts $D_i$.
7. Run the block bootstrap with 10,000 resamples, stratified by presentation order, resampling blocks and carrying all six arms of each drawn block.
8. Compute simultaneous intervals within each family declared in Section 14.
9. Apply the claim rules of Section 15, together with the interpretation and bounding rules of Section 16.

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
- One thousand pseudo-runs. Each pseudo-run selects one of the sixteen cached draws independently within every prompt cell by a frozen pseudo-run seed, recomputes the two primary estimands, and reports their empirical distributions and sign stability. Pseudo-runs are decoding-sensitivity diagnostics, carry no confirmatory interval or claim, and cannot replace the primary dataset.
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

**Scoring bias check.** Within all adjudicated natural responses from Gate 1, verifier and human labels are cross-tabulated by source model and failure category. Arm is included when the source stage contains an arm identity. Any concentration of disagreement in one model, arm, or category is reported as a scoring bias affecting interpretation.

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

Confirmatory terminal outcomes retain the following vocabulary.

| Outcome | Condition | Licensed statement |
|---|---|---|
| Meaningful positive swap effect | A primary simultaneous lower bound exceeds $+0.10$, with exchangeability failing | The focal constraint raises target failure by more than the smallest effect of interest relative to this frozen reference set, at that order and under the registered conditions |
| Meaningful positive identity-specific effect | The same, with exchangeability holding | The focal constraint raises target failure by more than the smallest effect of interest relative to three controls shown to be exchangeable under the registered margin |
| Meaningful negative swap effect | A primary simultaneous upper bound is below $-0.10$ | The focal constraint lowers target failure by more than the smallest effect of interest in magnitude under the registered conditions |
| Direction resolved, magnitude unresolved | The interval excludes zero, does not lie wholly beyond either SESOI boundary, and does not lie wholly inside the equivalence region | The direction is resolved; whether the effect is scientifically meaningful remains unresolved |
| Equivalence | A primary simultaneous interval lies wholly inside $\pm0.10$ | Any effect present is smaller than the smallest effect of interest under the registered conditions |
| Direction unresolved | A primary simultaneous interval includes zero and is not wholly inside $\pm0.10$ | The replication does not resolve the direction or establish equivalence at the achieved precision |
| Reference heterogeneity | At least one exchangeability interval extends beyond $\pm0.05$ | Level 1 remains available; Level 2 is withheld and per-reference contrasts are reported |
| Scorability asymmetry | A family F6 difference exceeds 0.05 with its interval excluding zero | The contrast and partial-identification bounds are reported, and claims follow the narrower bound |

Pre-confirmatory terminal outcomes use the following diagnostic statuses.

| Status | Condition | Licensed statement |
|---|---|---|
| `QUALIFICATION_FAILURE` | Code, model, environment, schema, or provenance qualification fails | The registered implementation was not qualified; no behavioural estimand was attempted |
| `APPARATUS_FAILURE` | Execution, cache, hashing, storage restoration, mask plumbing, or integrity machinery fails | The apparatus did not complete its registered technical test |
| `RESPONSE_LENGTH_INCOMPATIBLE` | Every registered token cap has truncation above 0.10 | The registered completion-budget grid did not support sufficiently complete responses for this model |
| `TARGET_RANGE_EXHAUSTED` | The target curve remains outside its band at a registered severity boundary | The registered target grid did not yield target headroom for this model |
| `FOCAL_RANGE_EXHAUSTED` | The focal curve remains outside its band at a registered severity boundary | The registered focal grid did not yield a deliverable focal operating point for this model |
| `GRID_RESOLUTION_INSUFFICIENT` | Adjacent severities jump across the full admission band | The registered grid was too coarse to select an admissible operating point |
| `REFERENCE_POOL_MISMATCH` | Fewer than three distinct reference families satisfy the registered solo-comparability rules | The registered reference pool did not supply three solo-comparable controls |
| `COMPOSED_HEADROOM_FAILURE` | Fewer than three solo-matched families remain within composed headroom | The registered solo-matched controls did not supply three usable $A+R$ conditions |
| `MEASUREMENT_NOT_ESTABLISHED` | Verifier reliability or validity exceeds a registered failure threshold | The primary measurement did not meet the registered validity standard |
| `MEASUREMENT_EVIDENCE_INSUFFICIENT` | The natural-response annotation budget cannot establish the precision criterion | The available natural validation evidence was too limited to certify the measurement |

Every failed gate automatically emits a terminal report containing the model and revision, gate, criterion, threshold, observed value, complete severity curves where applicable, selected and boundary parameters, reference admission table and distances, composed-reference results, truncation and finish-reason summary, verifier status, artifact hashes, producing commit, environment digest, the strongest permissible statement, and the estimands made unanswerable. It reports every quantity available before termination and never implies that a confirmatory estimate exists.

---

## 27. Execution integrity

Every generation is recorded with stage, artifact state, model-replication identity, block identity, arm, cached-draw index, order, wording indices, prompt hash, model revision, backend version, scientific-interpreter identity, dependency digest, hardware class, seed, raw response text, response content hash, token counts, finish reason, and every verifier verdict with its source hash.

Artifacts move monotonically through four states: `generated`, `committed`, `accepted`, and, when an audit-preserved fragment is excluded, `superseded`. A generated row becomes committed only after durable write and content-hash verification. A committed row becomes accepted only after stage authorisation, predecessor-gate verification, schema validation, and frozen-plan membership. A superseded row can never return to accepted status.

The artifact-type field uses the closed vocabulary `qualification_record`, `prefreeze_plan`, `pilot_record`, `gate_record`, `calibration_record`, `registered_freeze`, `confirmatory_evidence`, `masked_result`, `unmasked_result`, and `superseded_non_evidence`. Artifact type records scientific role; artifact state records storage and acceptance status.

The run aborts on any of the following: a missing or invalid predecessor PASS record; a dirty Git worktree; an invoked source file absent from the producing commit; a prompt exceeding the context limit; a change in model revision inside a run; a hardware class differing from the frozen value; a dependency or interpreter digest differing from the frozen value; a prompt hash absent from the frozen plan; a duplicate accepted draw; an incorrect count of cached draws; a verifier source hash differing from the frozen value; a stored response whose content hash differs from the recorded value; a stale output path; or an artifact whose declared type disagrees with its stage.

Stage-aware stops arise only from registered integrity rules or the scientific gates of Section 18. No confirmatory stop depends on the sign or magnitude of a focal-to-reference outcome.

Every attempted state transition is written to an append-only transition log. `generated`, `committed`, and `accepted` counts are reported separately so an incomplete fragment cannot appear as registered evidence.

Every model tree contains the same required records: `qualification.json`, `gate0_apparatus.json`, `regime_screen.json`, `gate1_measurement.json`, `gate2a_solo.json`, `gate2b_composed.json`, `gate3_freeze.json`, `transition_log.jsonl`, `terminal_report.json`, and, when confirmation is reached, `confirmatory_manifest.json`, `masked_result.json`, and `unmasked_result.json`. Each path is derived from the model identifier through one frozen path function. Missing, stale, or unexpected paths fail evidence verification.

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

**Version-controlled implementation.** The entire `dci1/` implementation, including generation, prompt construction, caching, verification, masking, analysis, schema, and reporting code, is tracked in Git before the first v3 artifact is created. Qualification requires a clean working tree and fails closed when `writer_dirty=True`. Every artifact records the actual producing commit, and an executable check confirms that every invoked source path belongs to that commit.

**Computational environment.** The canonical dependency representation is `uv.lock` together with a deterministic `uv export --frozen` manifest. Qualification fails when either representation is missing or empty. The environment record contains the lockfile and export hashes, exact Python executable and version, exact scientific invocation command, vLLM version and settings, PyTorch version, ROCm and driver versions, operating-system and kernel versions, GPU name and architecture, model repository and revision, chat-template hash, and the registered execution-relevant environment variables. A container-image digest is recorded only when the producing process actually runs inside that container.

Four executable checks enforce provenance and reproducibility.

1. Changing a dependency in a test fixture changes the environment digest; an empty dependency manifest is rejected.
2. Rerunning deterministic prompt-plan, codebook, verifier, mask-construction, and analysis derivations from the producing commit reproduces their recorded hashes or outputs.
3. Rerunning the full analysis in the recorded environment on the released raw responses reproduces the released result table byte for byte.
4. Deleting the local cache and restoring from durable storage reproduces every committed row with matching content hashes and regenerates no committed draw.

**Raw data.** Raw responses are written once, never edited, and carry a content hash computed at write time. Derived tables are regenerated from accepted raw responses by the analysis script and are never edited by hand. Pilot, calibration, confirmatory, and superseded data occupy separate namespaces and have distinct artifact types.

---

## 29. Relation to existing evaluations

Benchmarks of instruction following score joint satisfaction across several verifiable instructions and report an aggregate pass rate. Those designs vary the identity of instructions together with their number, so the identity of an added instruction and the increase in load contribute to the same score. The present design fixes the number of constraints at two in both compared prompts, so identity is the only quantity that varies.

Studies of compositional constraint satisfaction sweep the number of simultaneous constraints and report how satisfaction decays as constraints accumulate. Those studies characterise the effect of load. The present design characterises the effect of identity at fixed load, which is a distinct quantity: a population whose average effect of identity is zero can contain large effects for specific pairs.

Studies of prompt sensitivity vary surface wording and report score variation. Wording variation appears here as a designed factor with four frozen wordings per constraint, assigned at block level and shared across arms, so the estimand averages over the wording pool while each comparison stays wording-matched.

The measurement built here is an experimental contrast. Its output is one risk difference per presentation order with an uncertainty interval, together with the evidence deciding what that difference is attributable to. It ranks no models and produces no leaderboard score.

---

## 30. Limitations and design trade-offs

**Narrow scope.** Four separately analysed models, one language, one target constraint, one focal constraint, one registered reference-family pool, a load of two, one prompt template, one topic space, one decoding-policy form, single turn, and no tools. Every claim remains model-conditional and carries these design conditions.

**Exact verifiability costs realism.** The constraints are character-level lexical rules chosen so that a fixed program decides compliance without ambiguity. Real deployments contain style and content rules that resist exact verification. The trade accepted here is that a measurement whose meaning is stable under the treatment is a precondition for interpreting any effect, and character-level rules deliver that stability.

**Comparability has two stages.** Before confirmation, references are matched on solo difficulty, instruction length, scope, structural-family identity, satisfiability, non-entailment, and composed headroom. After confirmation, exchangeability contrasts test whether the frozen references behave interchangeably with respect to the target. Composed validation uses no focal composition and cannot select on the DCI contrast. Reference heterogeneity can still be discovered after confirmation, and the reference set is never revised in response.

**The topic bank bounds precision.** Blocks are topics, and the bootstrap resamples topics, so precision is governed by the number of topics. A bank of 384 confirmatory topics supports a simultaneous detectable effect near 0.10 at the assumed discordance, and it cannot resolve effects below 0.070 at any discordance in the planning range. Generalisation extends to the declared task space of short open-ended informational questions.

**Order is a designed factor.** Earlier exploratory work in this programme found presentation order to be a large moderator, so the two order-conditional effects are declared as separate primary quantities and the pooled effect is secondary. This doubles the primary family and halves the blocks available to each quantity.

**One direction only.** The reciprocal effect is not estimated, so the study establishes the effect of the focal constraint on the target and says nothing about the effect of the target on the focal constraint.

**Stochastic decoding contributes noise.** One hash-selected cached draw per cell enters the block-level contrast. The remaining cached draws support pseudo-run sensitivity analysis, and the greedy replication on 96 blocks checks whether the sign survives deterministic decoding. These diagnostics do not increase the primary sample size.

**Reliability evidence is generated in-house.** No prior instrument for this construct exists, so all reliability and validity evidence comes from this study's own calibration data and its own annotators. Independent replication of the verifier's agreement with human judgement on a differently constructed corpus would strengthen it.

**Masking is single-custodian.** The mask key is held in a file the analysis code opens once at the unmask step, without a second person holding it. The protection rests on the recorded hashes and timestamps of Section 19, which make a masked-phase decision distinguishable from a post-unmasking one in the record.

---

## 31. Release

The following are released under a permissive licence when results are reported: all 528 non-sequestered topics with the canary string; a manifest stating that 96 sequestered topics remain withheld; all constraint-family definitions, severities, wordings, witnesses, and verifier source; the four target scoring implementations; study-wide and model-specific freeze records; qualification, gate, transition, and terminal reports; Git commit and clean-tree records; `uv.lock`, deterministic dependency export, environment manifest, and any genuinely used container identifier; the codebook; every prompt; every committed raw cached draw with its content hash and artifact state; the frozen primary-draw selection; every verifier verdict; human labels and carry-over records; pilot and calibration records; pseudo-run summaries; masked and unmasked outputs; the unmask timestamp; analysis code; and the machine-readable result table containing each estimate, family, standard error, marginal and simultaneous bounds, realised discordance, achieved detectable effect, and cell counts.

Every reported figure is reproducible from the machine-readable result table without regenerating any response, and every number in that table is reproducible from accepted raw responses in the recorded scientific environment.

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
| Validate automated output parsing | Sections 5, 9, 10, and 18. Parse independence is executable, the scoring rule and three alternatives are frozen, determinism is tested at 1.000, forty boundary cases are enumerated per verifier, and sequential blinded natural-response labels must place the one-sided 95% Wilson disagreement bound at or below 0.10 in both verifier classes |
| Employ sampling strategies for representativeness | Section 6. Twelve declared subject strata, 52 authored questions per stratum, and seeded random assignment to five disjoint uses |
| Verify quality and relevance of all task items | Sections 6 and 10. Every question is verified individually against four written rules, and item behaviour is tabulated for floor, ceiling, and uninformative topics |
| Include items testing known model sensitivities | Sections 7, 8, and 22. Two presentation orders, four wordings per constraint, three alternative scoring rules, and a greedy-decoding replication on 96 blocks |
| Document whether a previous dataset is adapted | Section 6. No dataset is adapted. All 624 topics are newly written and no public benchmark item is reused |
| Report strengths and limitations of adapted prior work | No prior dataset is adapted, so no comparison applies |
| Compare performance against the original dataset | No prior dataset is adapted, so no comparison applies |
| Explain modifications to reused datasets | No dataset is reused, so no modification applies |
| Implement contamination tests | Section 24. Exact-phrase search of every confirmatory topic at release, plus the topic-alone arm as an empirical bound on accidental compliance |
| Maintain a held-out set | Section 6. 96 sequestered topics are withheld from release and from this study |
| Investigate pre-exposure of source materials | Section 24. Topics are newly written. The outcome depends on instruction compliance alone, and the topic-alone arm quantifies the residual risk |
| Report sample size and justify statistical power | Section 13. Each model has 384 blocks and 192 per order, with detectable effects tabulated against discordance. Sixteen cached draws remain below the observation level and do not increase inferential sample size |
| Report uncertainty estimates for all primary scores | Sections 11, 13, 14, and 20. Block bootstrap with 10,000 resamples, six enumerated families each with its own simultaneous interval, marginal intervals reported alongside, and every quantity reported whether or not a claim is licensed |
| Describe human rater demographics and mitigate bias | Section 25. Three annotators, blinded to arm and added constraint, labelling a decidable property of the text, with agreement statistics reported |
| Use metrics capturing variability of subjective labels | Sections 9 and 10. The primary metric is an exact character test with no subjective component, its determinism is tested, and its reliability is reported as verifier-to-human agreement. The block bootstrap carries the full variability of the binary outcome |
| Conduct qualitative and quantitative failure analysis | Section 23. A nine-category priority-ordered taxonomy applied to every failure, compared across arms as family F5, plus forty hand-coded failures read during the masked phase |
| Investigate whether failures correlate with confounders | Section 23. Target failure is described as a function of response length, truncation, refusal, and subject area within each arm, and any material association is reported as a competing explanation |
| Identify scoring biases revealed by error analysis | Sections 16 and 23. Verifier and human labels are cross-tabulated by arm and category, and the arm-symmetry rule triggers partial identification bounds when scorability differs across arms |
| Propose directions to improve scores | Section 26. Target, focal, grid-resolution, reference-pool, composed-headroom, response-length, measurement, qualification, and apparatus outcomes each identify the failed registered component and the estimands left unanswered |
| Justify relevance with real-world applications | Sections 11 and 29. Product system prompts stack several rules at once, and a change of 0.10 in target failure moves a system prompt from 80% compliance to 70% |
| Provide rationale for tasks and metrics tied to the definition | Sections 2, 5, 9, and 10. The definition is a difference in target-failure probability, the metric is the target failure indicator under scoring rule $S_0$, and the constraint pool is chosen so that the metric's decision procedure is unaffected by the treatment |
| Compare with existing evaluations of similar phenomena | Section 29. Instruction-following benchmarks, constraint-count sweeps, and prompt-sensitivity studies are each distinguished from this design |
| Discuss limitations and design trade-offs | Section 30. Scope, verifiability against realism, the timing of the comparability test, the topic bank as the precision constraint, order as a designed factor, the single direction, decoding noise, in-house reliability evidence, and single-custodian masking |

---

## 33. Relationship to v2 and historical closure

Version 2 is closed as four terminal model replications with zero confirmatory generations. Its evidence directories remain unchanged. A separate audit supplement may add metadata and corrected descriptions without altering the original bytes.

The two Qwen replications produced apparatus and calibration records and terminated at v2 Gate 2. Their Gate 1 human-agreement requirement was also formally unresolved because one natural-failure packet contained only 17 cases against the rigid requirement of 75. Across the registered $n\in\{1,2,3\}$ grid, target solo failure remained below the 0.15 floor, reaching only 0.021 to 0.125 for the hybrid Qwen model and 0.052 to 0.073 for the instruct-only model. Reference candidates were substantially harder, with observed solo failure between 0.47 and 1.00. These records establish failure of the declared search grid and pool; they do not establish absence of an operating regime outside them.

Both Gemma replications exceeded v2's 0.10 truncation ceiling at the 400-token cap, with 0.139 truncation for E2B and 0.150 for E4B. Their inference pipelines otherwise produced the expected technical outputs. E2B calibration, run before its Gate 0 verdict, found target failure 0.323 at $n=3$, focal failure 0.229 at its selected severity, and reference failure between 0.81 and 1.00. These out-of-order calibration quantities are design evidence for v3 and are not confirmatory evidence. E4B began an out-of-order 64-response calibration attempt before qualification and pilot completion. That fragment was never committed, is marked `SUPERSEDED_NON_EVIDENCE`, and supplies no scientific quantity. The v2 deviation record D27 is corrected accordingly.

The v2 implementation also failed its intended provenance guarantees: `dci1/` was untracked, artifact writers recorded a dirty worktree, and the dependency digest was built from an empty package manifest. Version 3 treats these as qualification failures and replaces them with the fail-closed Git and `uv` provenance requirements of Sections 27 and 28.

The following v2 components are carried forward unchanged in substance: the directional swap estimand; six-arm confirmatory design; three-reference average; target-alone and topic-alone diagnostics; order-specific primary estimands; block as assignment, pairing, clustering, and generalisation unit; 384 confirmatory topics; deterministic target scoring and three registered alternatives; intention-to-treat analysis; block bootstrap; multiplicity families; $\pm0.10$ smallest-effect region; $\pm0.05$ exchangeability region; non-behavioural-failure bounds; fixed-size sampling; masked analysis; error taxonomy; contamination controls; and sequestered-topic protection.
