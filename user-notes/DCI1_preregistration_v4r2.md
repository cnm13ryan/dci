# Preregistration: when two verifiable instructions are composed, which one is delivered, how much is lost, and does the loss depend on the identity of the companion?

**Protocol identifier:** DCI-1
**Version:** 4.0, revision 2, for registration
**Date:** 19 August 2026
**Confirmatory data collected at the time of registration:** none
**Registration target:** Open Science Framework, protocol-document format

**Status of the documents this replaces.** v4 revision 1 was drafted, never
registered, never frozen, and produced no data. It is superseded in full
and retained only as a design record. DCI-1 v3 is closed. Its
preregistration, amendments A1 to A3.2, signed evidence trees and results
report are historical evidence, are not modified or reinterpreted here,
and are never confirmatory evidence for v4.

**Design authority.** The construct decision of
`user-notes/dci-construct-pass2.md` (14 August 2026, "pass 2"), which
settles the primitive observation, demotes the legacy target-damage
estimand, names reciprocal delivery loss as the primary estimand, and
specifies in §G row 1 the discriminating experiment this design follows.
The takeover specification `user-notes/prompt-to-red-team.md` supplies the
integrity invariants (§X), the design dependency order (§N), the
operating-regime and reference requirements (§O, §P), and the required
contents of this document (§U).

**Status of the B+R pilot.** `reports/br_pilot_v4/` executed the B+R half
of the memo's §G row 1 in the v3 architecture on two models. The B+S half
generated nothing: v3 §1 registers the background set $S$ as "Empty in
this study", so in that architecture $B+S$ coincides with the $B$-alone
cell and $D(B \leftarrow S)$ is zero by construction. The memo lists $B+S$
and $B$-alone as distinct cells, which implies a non-empty background and
therefore a load-three design; §33 V2 carries that as an open decision. It
is **non-confirmatory**. It
is not a registered v3 stage and it is not a v4 confirmatory run. In this
document it supplies exactly three things: the motivation for the
redesign, exploratory variance and effect-size information for the power
plan of §16, and a set of empirical checks that must be repeated
prospectively (checks C12, C13 and C16 of
`DCI1_v4r2_prefreeze_checks.md`). It licenses no
scientific claim, and its point estimates are never treated as the
confirmatory effect this design expects to observe.

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
| Graded score, $G_c$ | A deterministic real-valued score on $[0,1]$ recording how nearly $c$ was met, defined per constraint family in §7.4. |
| Compliance vector | The tuple $X = (X_c)$ over every constraint present in the prompt, with the graded vector $G = (G_c)$ and the degeneracy flags of §9.3. This is the primitive observation. |
| Solo cell | A prompt containing exactly one constraint. |
| Composed cell | A prompt containing exactly two constraints. |
| Companion | For an outcome constraint $c$ in a composed cell, the other constraint $g$ present. |
| Load | The number of constraints in a prompt. Fixed at one or two throughout. |
| Delivery loss, $D(c \leftarrow g)$ | $P(X_c = 1 \mid c \text{ alone}) - P(X_c = 1 \mid c \text{ with } g)$. Positive means composition reduced delivery of $c$. |
| Reciprocal pair | The two delivery losses of one composed cell, $D(c \leftarrow g)$ and $D(g \leftarrow c)$. |
| Asymmetry, $\Lambda$ | $D(B \leftarrow A) - D(A \leftarrow B)$. |
| Companion swap, $\Delta$ | The change in a constraint's delivery loss when its companion is replaced: $\Delta_j = D(B \leftarrow A) - D(B \leftarrow R_j)$, $\Delta_R = D(B \leftarrow A) - \frac{1}{3}\sum_j D(B \leftarrow R_j)$. |
| Target constraint, $A$ | The exact-count constraint. In v3 it was the outcome; here it is one of five registered constraints and is both an outcome and a companion. |
| Focal constraint, $B$ | The word-length constraint. It carries the primary outcome under the recovered question. |
| Reference constraint, $R_j$ | A constraint occupying the companion slot in place of $A$, selected under §13 to be comparable to $A$. |
| Configuration | The tuple (model checkpoint, instruction order). Every primary estimand is indexed by a configuration and no estimand is pooled across configurations. |
| Instruction order | Which of the two constraints in a composed prompt is stated first. |
| Topic, block | One question the model is asked, together with the wording indices and order assigned to it. All cells of a block share them. |
| Cell mean | The mean of an outcome indicator over all $M$ cached draws of one prompt cell. This is the analysis input. |
| Non-violation constraint | A constraint of the form "at most $q$ …" or "every word at most $m$ letters", which an empty or degenerate response satisfies mechanically. |
| Vacuous pass | A pass on a non-violation constraint by a response that fails the registered non-vacuity predicate of §9.3. |
| Joint state | For a composed cell, the pair $(X_{c_1}, X_{c_2})$, taking one of four values. |
| Redistribution | A change in the four-state joint distribution under an intervention that does not change which constraints are present. |
| Family | A declared set of quantities sharing one simultaneous confidence statement within one configuration. |
| Simultaneous interval | An interval constructed so that a stated confidence level applies to a whole declared family at once. |
| Šidák bound | The conservative critical value for a family of size $k$, using the two-sided level $1 - 0.95^{1/k}$ per member. |
| Precision precondition | The registered maximum realised simultaneous half-width for a primary member, below which no equivalence or threshold conclusion may be emitted. |
| Identification status | A per-claim marker recording whether the design as realised supports a given claim level. |
| Measurement basis | A machine-readable marker of how the outcome instruments were validated: `human_validated`, `autorater_calibration_approved`, or `human_validation_unavailable`. |
| Autorater | A language model used only as a proxy instrument for verifier development and held-out evaluation. It never produces a behavioural score, never overwrites a deterministic verdict, and its judgments live in separate artifacts. |
| Masked analysis | Analysis performed on data whose companion labels have been permuted, so that analysis decisions cannot depend on the result. |

---

## 2. Phenomenon, construct, and scientific question

**Phenomenon.** *Compositional non-composition.* When two verifiable
instructions that address the same output are presented together, the
model produces one text that satisfies some of them and abandons others.
Joint satisfaction is not guaranteed, the abandonment is not symmetric,
and the magnitude and sign of any pairwise summary depend on the whole
configuration.

**Construct.** The *compliance profile* of a prompt: for every instruction
present, the probability that it is realised, measured on its own
deterministic verifier and referenced to its own solo baseline, reported
jointly with the other instructions of the same prompt.

**Primary scientific question.** For a registered pair of constraints
$(A, B)$ and a registered model, in a registered instruction order:

1. Does composing each constraint with the other reduce its delivery
   relative to that constraint alone?
2. Is the reduction directionally asymmetric between the two?
3. Is the reduction of $B$ specific to the companion $A$, or does a
   companion matched to $A$ on solo compliance produce a comparable
   reduction?

Question 3 is the discriminating question of `dci-construct-pass2.md` §G
row 1. That row has two cells. The design cell reads:

> Generate B+R and B+S without the sentence-count instruction, beside the
> existing B-alone and B-with-A cells.

The discriminating-result cell reads:

> D(B←A) − D(B←R) > 0.25 supports H1 and licenses a pairwise construct.
> < 0.10 supports H2 and **refutes the pairwise framing entirely**,
> redirecting the programme to a load-and-capacity account.

Both thresholds were fixed in a document dated 14 August 2026, before any
data addressing them existed in this constraint vocabulary, and were
transcribed verbatim into the pilot protocol before the pilot generated
anything. They are registered here as prospective decision thresholds on
that provenance, and §33 requires the memo hash, the quoted lines and both
dates to be recorded in the manifest.

---

## 3. Hypotheses and the claim ladder

Five claim levels are registered. Each has a licensing rule, a fixed
licensed statement, and an identification gate. A level whose gate fails
records an identification status and is not emitted. No level licenses any
statement above it.

| Level | Claim | Licensing rule (within one configuration) | Identification gate |
|---|---|---|---|
| **L1** | Compositional delivery loss exists | The F1 simultaneous interval for the named $D(c \leftarrow g)$ has lower bound above 0 | $c$ has solo headroom (§12) and the position caveat of §11.4 is stated |
| **L2** | The loss is directionally asymmetric | The F1 simultaneous interval for $\Lambda$ excludes 0 | L1 conditions for both $D(B\leftarrow A)$ and $D(A \leftarrow B)$ |
| **L3a** | The excess damage from $A$ exceeds the generic-load threshold | The F1 simultaneous interval for $\Delta_R$ has lower bound above 0.10 | Three references admitted under §13; otherwise `EXCESS_NOT_IDENTIFIED` |
| **L3b** | The excess reaches the source memo's pair-specific threshold | The same interval has lower bound above 0.25 | As L3a |
| **L3c** | Generic compositional load | The same interval has upper bound below 0.10 | As L3a |
| **L4** | The result replicates across configurations | The same L1/L2/L3 classification holds in every registered configuration | All configurations reached the corresponding level |
| **L5** | Semantic identity-specificity, universal pair property, arbitration, mechanism, or generalisation | **Never licensed by this design** | Permanently withheld; §5 and §29 state why |

Where the $\Delta_R$ interval spans 0.10 or 0.25 the result is recorded
`INDETERMINATE` at that threshold with both bounds.

Failure to exclude zero is never reported as absence. An absence statement
about $D$ or $\Lambda$ requires the equivalence rule of §17.3, including
its precision precondition.

---

## 4. Experimental unit, treatments, and randomisation

The **unit** is the block: one topic together with the wording indices
assigned to it, shared by every cell of that block. Instruction order is a
cell-level factor within the block, so every block carries both order
variants of every composed cell (§8.4).

The **treatment** for an outcome constraint $c$ is which companion
occupies the other slot, taking values in {none, and each other registered
constraint}. Assignment is by design: every block runs every registered
cell, so treatment is within-block and complete, and no randomisation of
assignment to units is required.

**Randomised design factors.** Topic-to-set assignment is a seeded
stratified random split (§6). Instruction order is balanced by
construction inside every block rather than randomised. Wording indices
are assigned by the block index under the registered allocation of §8.4,
with an executable coverage assertion that refuses a plan containing a
structural zero.

---

## 5. Scope and excluded phenomena

The study measures the compliance profile of two-constraint prompts for
one exact-count constraint, one word-length constraint, three reference
constraints, four model checkpoints, two instruction orders, one decoding
policy per model, one prompt template, one language, and one topic space.

Excluded by design, and never claimed:

- **Loads above two.** The construct memo's best-evidenced interaction
  quantity, the three-place $\Gamma$, requires a background constraint and
  a load-three cell. The v3 and v4 architectures carry a topic question
  and no third constraint, so this design cannot estimate $\Gamma$ and
  says nothing about whether the phenomenon is two-place or higher-order.
  §33 records the extension as an open decision.
- **Semantic identity-specificity.** The design compares $A$ against
  companions matched on solo compliance and instruction length. Matching
  leaves other properties of $A$ free, so an excess attributable to $A$ is
  an excess relative to that matched set, not to the semantic content of
  $A$.
- **Universal pair properties.** The pilot shows the quantities changing
  by a factor of four across two model checkpoints and two orders. No
  scalar is quoted without its configuration and no configuration-pooled
  scalar carries a claim.
- **Arbitration and mechanism.** The construct memo tested an explicit
  priority intervention and recorded a clean null. This design measures
  behaviour under composition and is silent on internal mechanism.
- **Response-length mediation as a causal claim.** Response length is
  registered as a mediator and reported; no mediation effect is claimed.
- **Compliance as an independent human would judge it**, while the
  measurement basis is not `human_validated` (§10.5).
- **Generalisation** beyond the registered models, constraints, order set,
  topic space, decoding policy and load.

---

## 6. Models and topic population

### 6.1 Models

Four registered replications, each analysed separately, each a moderator
level and never pooled.

| Order | Model label | Repository | Note |
|---:|---|---|---|
| 1 | Gemma 3n E2B-it | `google/gemma-3n-E2B-it` | Completed v3 confirmatory; pilot model |
| 2 | Gemma 3n E4B-it | `google/gemma-3n-E4B-it` | Completed v3 confirmatory; pilot model |
| 3 | Qwen3-4B, thinking disabled | `Qwen/Qwen3-4B` | Terminal at v3 Gate 2A; estimable here (§13.5) |
| 4 | Qwen3-4B instruct-only | `Qwen/Qwen3-4B-Instruct-2507` | Terminal at v3 Gate 2A; estimable here |

Execution order places the two pilot models first so that the registered
apparatus is exercised where prior operating points are known. **No
replication is blocked by the outcome of another.** The v3 early-stop rule
is withdrawn, because no per-model outcome can invalidate a design whose
primary estimands need no cross-model quantity. Exact repository revisions
are pinned in the signed registration manifest before qualification and
asserted at every generation.

**Cross-replication firewall.** Every study-wide rule is fixed in the
signed registration manifest before the first qualification. Only the
following adapt mechanically by model, and only through the registered
gates of §18:

| Model-adaptive through §18 | Study-wide, fixed before the first qualification |
|---|---|
| $n^*$, $m^*$, the completion-token cap, one selected severity per admitted reference family, the identities of the three admitted references, and whether the full or the reduced design runs | Constraint families and severity ladders, graded-score definitions, non-vacuity predicates, selection algorithms and tie-breakers, both calipers, the number and structural diversity of references, estimands, thresholds and regions, precision preconditions, multiplicity families, the bootstrap, the decoding-policy form, $M$, the block count, masking rules, gate rules, artifact semantics, the claim ladder, and the codebook |

A scientific outcome from one replication never modifies a study-wide rule
used by another.

### 6.2 Topics

The task space is short open-ended informational questions answerable in
sixty to one hundred and twenty words from general knowledge, without
tools, arithmetic, or recall of a specific named fact.

The v4 bank contains **624 newly authored questions**, 52 in each of the
twelve declared subject areas: everyday science, history, geography, food,
music, sport, work and organisations, health and the body, technology,
language and writing, art and design, the natural world. Each question is
verified individually against four rules: answerable from general
knowledge, no single correct short answer, no reused text from any public
dataset or examination, and no wording that itself mentions any letter,
word length, word shape, punctuation-count, or capitalisation requirement.

Within each area the 52 questions are shuffled with a fixed seed and split:

| Set | Per area | Total | Permitted use |
|---|---:|---:|---|
| Pre-screen | 2 | 24 | Completion-cap selection, dense ladder screen, Gate 1 validation material |
| Solo calibration | 8 | 96 | Solo-compliance curves; selection of $n^*$, $m^*$, and reference severities |
| Composed validation | 2 | 24 | Composed-headroom viability only |
| Confirmatory | 32 | **384** | The frozen confirmatory experiment |
| Sequestered | 8 | 96 | A future uncontaminated rerun only |

No v3 topic and no B+R pilot topic enters any v4 set. The v3 sequestered
96 remain sequestered and are not opened. Sequestered v4 text is
inaccessible to the design and execution team throughout v4.

---

## 7. Constraints

### 7.1 The two outcome constraints

> **A:** Use the word *however* exactly $n$ times.
> **B:** Every word in the answer must have at most $m$ letters.

Registered grids $n \in \{1,\dots,8\}$ and $m \in \{7,8,9,10\}$. The word
*however* has seven letters, so $m \ge 7$ is required for $A+B$ to be
jointly satisfiable. Under this design the floor is benign: $B$ is an
outcome whose solo compliance should be high with room to fall, and the
most restrictive admissible severity is the one that keeps solo compliance
away from ceiling. §12 gives the selection rule.

$A$ and $B$ are both outcome constraints and both companions. Neither is
privileged in the recording of the compliance vector.

### 7.2 The reference pool and its severity ladders

Eight structurally distinct families, each carrying the complete integer
severity ladder from 0 to its registered maximum. All constraints are
single-clause, apply to the whole answer, and are decided by deterministic
character operations. A word is a maximal run of alphabetic characters;
suffix and letter tests use the lower-cased word; comma and upper-case
counts read raw characters.

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

94 severities in total. The family maxima are the v3 grid maxima; v4 fills
the interiors, because the v3 four-point grids left the admissible region
unmeasured for two of four models.

At most one severity from a family enters the final reference set, and the
three references come from three different families.

### 7.3 Properties established before generation

Executable tests, all required to pass at qualification:

- **Parse independence.** Each verifier receives the response text and its
  own constraint identity and severity. It receives no companion identity,
  cell label, order, or other verifier's output.
- **Joint satisfiability.** For every registered unordered pair of
  constraints at every registered severity, a machine-verified witness
  response satisfies both at once.
- **Non-entailment.** For every registered pair, one verified response
  satisfies the first and fails the second, and one does the reverse.
- **Wording equivalence.** $A$, $B$ and each family carry four frozen
  wordings, checked for identical meaning and required to produce
  identical verdicts on a fixed set of twenty test responses at every
  severity.
- **Wording length.** Every reference wording at an admitted severity is
  within 20% of the corresponding wording of **$A$** in alphabetic-run
  word count. Severity parameters render as numerals and contribute no
  words.

### 7.4 Graded scores

Every verifier additionally returns a deterministic graded score in
$[0,1]$, recorded on every row and never used as a primary outcome.

| Constraint form | Graded score |
|---|---|
| $A$, exact count of a target word | $\max(0,\, 1 - \lvert s_0 - n \rvert / n)$, where $s_0$ is the registered exact count |
| $B$, every word at most $m$ letters | $1 - (\text{words longer than } m) / (\text{total words})$, and $0$ for an empty answer |
| RF1–RF8, at most $q$ occurrences | $\min(1,\, q / \max(q, \text{realised count}))$ for $q>0$; $\mathbb{1}[\text{count}=0]$ for $q=0$ |

Graded scores support the manipulation-check reading the construct memo
found missing from every shipped analysis (memo §G row 3), and they enter
the robustness family of §15.

---

## 8. Design

### 8.1 The complete pairwise composition matrix

Five constraints are registered per model replication: $A$, $B$, and three
references $R_1, R_2, R_3$ selected under §13. Every block runs:

- **5 solo cells**, one per constraint;
- **20 composed cells**: each of the $\binom{5}{2} = 10$ unordered pairs
  in each of the two instruction orders.

**25 cells per block.** Instruction order is a **within-block** factor:
every block runs both order variants of every pair, so every block
contributes to both configurations and the order contrast is paired within
topic. Each composed generation is scored on both of its constraints, so a
block yields 5 solo observations and 40 composed (outcome, companion)
observations per draw.

This design is the smallest one that supplies, without any unregistered
extrapolation: every $D(c \leftarrow g)$ for the registered constraints,
both reciprocal directions of every pair, the companion swap on the $B$
side and on the $A$ side, and the complete outcome-by-companion table
needed for §11.5.

### 8.2 Draws and cell means

$M = 4$ cached stochastic draws per cell. All $M$ enter the cell mean; no
draw is selected, discarded, or replaced. Blocks remain the only
resampling unit (§14).

### 8.3 Size

**384 confirmatory blocks.** Because order is within-block, every block
enters both configurations, so each configuration is estimated on all 384
blocks. Per model: $25 \times 384 \times 4 = 38{,}400$ cached generations.
Across four models, 153,600. §16 gives the justification and the
registered alternatives.

A sensitivity run repeats the 20 composed cells on the first 96
confirmatory blocks at temperature 0 with one draw per cell, giving 1,920
further generations per model, reported as a different generation
population.

### 8.4 Order and wording allocation

**Order is a cell-level factor.** For every unordered pair the block runs
both variants: one with the constraint earlier in the registered order
$(A, B, R_1, R_2, R_3)$ stated first, one with it stated second. Order is
therefore exactly balanced by construction inside every block, and each
configuration uses all 384 blocks.

**Wordings are a block-level factor.** For a composed cell with
constituents $(c_1, c_2)$ in registered order, block index $i$ fixes
wording index $i \bmod 4$ for $c_1$ and
$\left(i + \lfloor i/4 \rfloor\right) \bmod 4$ for $c_2$, applied
identically to both order variants of that cell. Solo cells use
$i \bmod 4$. The offset formula de-correlates the two wording indices; it
is the allocation v3 used for its pilot and the B+R pilot used for its
reference wording.

Because order no longer depends on the block index, wording and order are
orthogonal by construction, and each of the four wordings appears in 96 of
the 384 blocks in each order of each cell type.

Every generative stage carries an executable allocation assertion stating
the intended count for every wording and every order, and the assertion
refuses a plan containing a structural zero. Where a formula and an
assertion disagree, qualification fails.

### 8.5 Prompt construction

Every prompt has three parts in the same order: the topic question, a
numbered list of the active constraints, and the line `Answer:`. Within a
block, two composed prompts sharing a constituent differ byte for byte
only in the line stating the other constituent. Both constraints occupy
the same authority level in the same numbered list in the same user
message. No constraint is placed in a system message.

### 8.6 The reduced design when references are not identified

If §13 admits fewer than three references for a model, that replication
runs the **reduced design**: 2 solo cells ($A$, $B$) and 2 composed cells
($A+B$ in each order), 4 cells per block, $4 \times 384 \times 4 = 6{,}144$
generations. It estimates $D(B \leftarrow A)$, $D(A \leftarrow B)$ and
$\Lambda$, records `EXCESS_NOT_IDENTIFIED` for L3, and is analysed under
the same rules. This branch is decided by the deterministic Gate 3 rule
before any confirmatory generation and is recorded in the freeze.

---

## 9. Primitive observation

### 9.1 The compliance vector

For every generation the record carries $X_c$ and $G_c$ for **every**
constraint present in that prompt, together with the constraint identity,
severity, wording index and position. Nothing is marginalised at record
time. Target failure under the exact-count rule is one component of the
vector and has no privileged status.

### 9.2 The exact-count rule and its alternatives

$A$'s verifier, written $S_0$, is fixed here and applies unchanged in
every cell: take the whole response, lower-case it, find every maximal run
of alphabetic characters, count the runs equal to `however`, and pass when
the count equals $n$. Its word-segmentation and counting function sources
are byte-identical to the v3 instruments under the carry-over rule of
§10.2.

Three alternatives are declared for the robustness family and never
redefine $X_A$: $S_1$ omits the lower-casing step; $S_2$ counts
non-overlapping substring occurrences in the lower-cased text; $S_3$
applies $S_0$ after deleting a leading colon-terminated line and any line
repeating an active constraint wording.

### 9.3 Degeneracy, vacuity, and non-behavioural states

Every generation additionally carries: emptiness, word count, token count,
finish reason, truncation at the completion cap, verifier-processing
failure, and the accidental-occurrence count of the exact-count target
word in cells where $A$ is absent.

A **non-vacuity predicate** is registered per constraint form:

| Constraint form | Non-vacuity predicate |
|---|---|
| $A$ (exact count) | Response is non-empty and not truncated |
| $B$ (every word at most $m$ letters) | Response is non-empty, not truncated, and contains at least 20 words |
| RF families (at most $q$) | Response is non-empty, not truncated, and contains at least 20 words |

A pass on a non-violation constraint by a response failing its predicate
is a **vacuous pass**. Vacuous passes are counted as passes in the primary
estimand, because response shortening under composition is a candidate
mechanism rather than a nuisance, and removing them would condition on a
consequence of the treatment. They are handled instead by:

1. the vacuity rate reported per cell and per constraint;
2. family F6 of §15, the vacuity-rate differences between each composed
   cell and the corresponding solo cell;
3. the registered partial-identification recomputation of §17.4, in which
   every primary estimand is recomputed with all vacuous passes forced to
   failures.

The 20-word threshold is registered on the reasoning that the topic space
asks for sixty to one hundred and twenty word answers, so an answer below
twenty words has abandoned the task rather than satisfied the constraint.
It is fixed here and is not tuned after any data are seen.

---

## 10. Measurement: verifiers, freeze, and validation

### 10.1 Architecture invariants

1. Every behavioural score is a deterministic function of the response
   text and fixed configuration.
2. Verdicts are computed at generation time and stored with the verifier
   source hash.
3. No language model produces a behavioural score. The autorater of §10.4
   is a validation-only proxy, its judgments live in separate artifacts,
   and no execution path lets an autorater judgment reach a stored
   verdict.
4. Alternative scoring rules never silently redefine a primary outcome.
5. A pass on a non-violation constraint is never described as engagement
   without the §9.3 predicate.

### 10.2 Verifier correctness

Every registered outcome verifier, meaning $A$'s exact-count rule **and**
$B$'s word-length rule **and** every admitted reference family verifier,
must pass all of:

- **Determinism.** Three executions on three separate processes over every
  calibration response, agreement exactly 1.000.
- **Boundary suite.** A frozen boundary suite per verifier, of at least
  forty cases, covering
  empty response, adjacent punctuation, capitalisation, hyphenation,
  concatenated copies, repeated words, non-Latin characters, Unicode
  punctuation and lookalikes, zero-width characters, and truncation
  mid-word. Case texts and expected verdicts are frozen before
  qualification. The $A$-side suite consists of the v3 forty case texts
  and their expectations carried byte-identically under the carry-over
  rule, **plus** the additional cases the §24 enumeration requires and the
  v3 forty do not cover; the carried subset stays byte-identical and the
  additions are authored and frozen for v4. The $B$-side and family suites
  are authored for v4 in full.
- **Independent reimplementation.** A second implementation written from
  the registered prose of §7 and §9 by a process that does not read the
  primary source, run over every calibration response and the whole
  boundary suite, agreement exactly 1.000.
- **Adversarial corpus.** A targeted corpus exercising every enumerated
  boundary case, with the realised frequency of each case in genuine
  generations reported (§24).
- **Carry-over.** $A$'s instrument may supply carried evidence only when
  the construct string, the segmentation function source, the counting
  function source, and the forty case texts with their expectations are
  byte-identical to the v3 artifacts. The carry-over record names the
  source, records every hash, and refuses on any mismatch.

**What v3 already covered, precisely.** v3 §18.3 required the forty-case
boundary suite of every verifier, and v3 §10 required three-process
determinism of every verifier, so those two lines of evidence already
extend beyond the exact-count rule. Everything else was $S_0$-only: the
120 blinded human labels, the autorater development and calibration, the
independent reimplementation, and the four validity arguments. Under this
design the word-length and family verifiers are primary instruments, so
Gate 1 does not pass until each of them carries the full set above. The
boundary suites follow the split rule of the bullet above: the $A$-side
forty cases are carried byte-identically and extended to cover the wider
§24 enumeration, and the $B$-side and family suites are authored for v4 in
full.

### 10.3 Human agreement

At least one annotator independent of the design and analysis team labels
a seeded stratified sample per verifier class per instrument, under a
tool-assisted protocol: the annotator marks each qualifying feature and
the interface tallies the annotator's own marks, with no automatic
detection, highlighting, counting or normalisation, and no arm, model
label, companion, verdict or other annotator's work visible.

Criterion, carried from v3 as amended with one addition: the one-sided 95% Wilson
upper bound on human-to-verifier disagreement is at most 0.10 in each
verifier class, on a seeded sample of $\min(150, N_c)$ natural responses
per class. The addition is the fail-class stratification: within the fail class the
bound is computed separately on items whose realised margin is exactly one
and on items with larger margins, and both must be met. It is registered
because v3's realised fail-class disagreements were concentrated at margin
one, four of forty-four, with none at larger margins. It is strictly
stricter than the v3 criterion and never weakens it.

Statuses: a measured excess returns `MEASUREMENT_NOT_ESTABLISHED`; an
exhausted natural class returns `MEASUREMENT_EVIDENCE_INSUFFICIENT`; no
independent annotator returns `HUMAN_VALIDATION_UNAVAILABLE` and routes to
§10.4 without waiving the criterion.

**Author-performed labels are never described as independent validation.**
The v3 record contains 120 author-performed blinded labels; they are
diagnostic evidence there and are not carried as independent validation
here.

### 10.4 Autorater-assisted validation

When human validation is unavailable, verifier development and held-out
evaluation proceed against one configured autorater under a registered
workflow: a deterministic class-stratified disjoint development and
calibration split of the response pool; one judge model resolved through a
registry disjoint from the registered study models, at a pinned revision,
with a hashed configuration recording judge identity, revision, backend,
prompt version and hash, parser version, label mapping, decoding, and
output cap; **serialised deterministic execution** at concurrency one, or
an equivalently demonstrated fixed-composition offline path, because
concurrent serving was shown to produce repeated-run label instability; a
development-phase repeatability check; a single-shot signed freeze binding
verifier hashes, the regression-test file and its passing run, the split
derivation, the realised evidence boundary, and the judge configuration; a
one-shot calibration on the untouched held-out half enforced by an
append-only ledger; and explicit researcher approval writing
`measurement_basis = autorater_calibration_approved`.

Selection of the judging condition uses the hierarchy: valid deterministic
execution, then adequate output cap and absence of problematic truncation,
then valid parsing and coverage, then agreement with human labels, then
the lower-cost setting when performance is practically indistinguishable.
Configurations are compared as **paired** on the same items.

A reserved final-check set is sealed at Gate 1, its hash recorded, and
opened at most once after every autorater choice is frozen. It is never
used for tuning and is never rerun to obtain a better result.

### 10.5 Measurement scope, recorded verbatim

Three questions are kept separate and never aggregated.

1. *Does each program implement its registered rule?* Answered by §10.2.
2. *Can an independent human reproduce it?* Answered by §10.3, or recorded
   unavailable.
3. *Does the deterministic rule validly operationalise the intended
   instruction-compliance construct?* Bounded by §9.3 and §24 and not
   resolved by this study.

Every analysis record carries the measurement basis and, while the basis
is not `human_validated`, the registered scope sentence: *the outcomes are
verifier-defined and support no claim about compliance as an independent
human would judge it.*

### 10.6 Verifier freeze and downstream binding

The canonical verifier hash covers every source and configuration
component that can change verifier semantics for any registered
instrument. It is frozen in the Gate 1 record. Every downstream entry
point re-verifies the current hash against the frozen hash before any work
and fails closed on mismatch: reference calibration, composed-headroom
validation, freeze, confirmatory generation, scoring, resume and restart
paths, analysis, unmasking, and report generation. The frozen hash is
never silently updated; a semantic change requires explicit invalidation
and recalibration. Historical rows remain auditable under their own
recorded hash and are never treated as newly valid.

---

## 11. Estimands

### 11.1 Observation and configuration

For cell $c$ with $M$ draws the observation is the cell mean
$\bar X_c = \frac{1}{M}\sum_{j} X_{c,j}$, which estimates the compliance
probability of that cell under the registered decoding policy. Every
estimand below is defined **within one configuration**, a (model,
instruction order) pair, and is estimated on all 384 blocks, because order
is a within-block factor and every block carries both order variants of
every cell. There are two configurations per model and eight in total
across the four models.

### 11.2 Delivery loss

For an outcome constraint $c$ and companion $g$,

$$D(c \leftarrow g) \;=\; \mathbb{E}\!\left[\bar X_{c,\text{solo}}\right] - \mathbb{E}\!\left[\bar X_{c,\;c+g}\right],$$

with both terms taken over the same 384 blocks, so the contrast is paired
within block.

### 11.3 Primary estimands

Per configuration, four:

$$D(B \leftarrow A), \qquad D(A \leftarrow B), \qquad \Lambda = D(B \leftarrow A) - D(A \leftarrow B), \qquad \Delta_R = D(B \leftarrow A) - \tfrac{1}{3}\sum_{j=1}^{3} D(B \leftarrow R_j).$$

Note the algebra that makes $\Delta_R$ well behaved:
$\Delta_R = \frac{1}{3}\sum_j \mathbb{E}[\bar X_{B,\,B+R_j}] - \mathbb{E}[\bar X_{B,\,A+B}]$.
The solo baseline cancels, so $\Delta_R$ is unaffected by solo ceiling,
solo noise, or any property of the solo cell.

### 11.4 The position caveat, registered

A solo cell states its single constraint in position one. $D(c \leftarrow g)$
is therefore position-matched to its baseline only in the configuration
where $c$ is stated first; in the other configuration it confounds added
load with a change of position. $\Delta$-type quantities difference two
composed cells with $c$ in the same position and are position-clean in
both configurations.

Consequences, fixed here: every emitted L1 statement names the position of
the outcome constraint; the L1 claim in the position-shifted configuration
is stated as "composition and position change together"; and $\Delta_R$,
which is position-clean, is the quantity that carries the companion
identity claim.

### 11.5 Secondary estimands

Per configuration, all with simultaneous intervals within their family
(§15):

- **Companion heterogeneity.** $D(B \leftarrow R_j)$ and
  $\Delta_j = D(B \leftarrow A) - D(B \leftarrow R_j)$ for each $j$.
- **Outcome-side control.** $D(A \leftarrow R_j)$ for each $j$, and the
  $A$-side companion swap
  $\Delta^A = D(A \leftarrow B) - \frac{1}{3}\sum_j D(A \leftarrow R_j)$.
  $\Delta^A$ is the v3 registered swap effect re-expressed on the
  compliance scale and is retained as a **demoted diagnostic**, subject to
  the memo's three gates: outcome headroom, a companion matched on
  measured solo compliance, and the configuration quoted with the number.
- **Interference matrix completion.** Writing
  $D(\bar R \leftarrow g) = \frac{1}{3}\sum_j D(R_j \leftarrow g)$ for a
  companion $g$ outside the reference set, and
  $D(\bar R \leftarrow \bar R') = \frac{1}{6}\sum_{j \ne k} D(R_j \leftarrow R_k)$
  over the six ordered pairs of distinct admitted references:
  $D(\bar R \leftarrow A)$, $D(\bar R \leftarrow B)$,
  $D(\bar R \leftarrow \bar R')$, and the
  outcome-by-companion difference in differences
  $\Xi = \Delta_R - \left[D(\bar R \leftarrow A) - D(\bar R \leftarrow \bar R')\right]$,
  which asks whether the excess damage from $A$ is specific to the outcome
  $B$ or is a property of $A$ as a companion to anything.
- **Reciprocal losses.** $D(R_j \leftarrow B)$ and $D(R_j \leftarrow A)$.
- **Joint-state redistribution.** For each composed cell the four-state
  vector $p = [P(0,0), P(0,1), P(1,0), P(1,1)]$, and its change across
  configurations that do not alter which constraints are present, namely
  order and checkpoint. Reported within cell, never differenced across
  cells with different constituents.
- **Joint success.** $P(X_{c_1} = 1, X_{c_2} = 1)$ per composed cell.

### 11.6 Thresholds and regions

| Quantity | Threshold | Provenance |
|---|---|---|
| $\Delta_R$ generic-load threshold | 0.10 | `dci-construct-pass2.md` §G row 1, 14 August 2026, verbatim |
| $\Delta_R$ pair-specific threshold | 0.25 | Same |
| Smallest effect of interest for $D$ and $\Lambda$ | 0.10 | Carried from v3 §11; a change of 0.10 moves a system prompt from 80% to 70% compliance |
| Equivalence region for $D$ and $\Lambda$ | $\pm 0.10$ | Same |
| Precision preconditions (§17.3) | half-width $\le 0.05$ for $D$ and $\Delta_R$, $\le 0.08$ for $\Lambda$, $\le 0.06$ for $\Delta_j$ | §16.2; met with margin under both fitted variance settings |
| Reference solo-compliance caliper (§13) | 0.10 on the point difference, with the 95% Newcombe interval intersecting $\pm 0.05$ | §13.2 |
| Realised companion-difficulty qualifier | 0.15 on the confirmatory-measured gap | §13.2 |

No threshold is derived from the pilot. The two $\Delta_R$ thresholds
predate every observation in this constraint vocabulary.

---

## 12. Operating regime and severity selection

The design dependency order is followed: the construct and estimands are
fixed above; the operating regime is found next; references are selected
only afterwards.

### 12.1 Completion cap

A fixed subject-balanced set of 96 pre-screen prompts, containing
zero-constraint, one-constraint and two-constraint prompts, is generated
at each cap in $\{512, 768, 1024\}$. The smallest cap whose truncation
rate over the one- and two-constraint prompts is at most 0.10 is selected
and held fixed for the replication. If none qualifies the replication
terminates `RESPONSE_LENGTH_INCOMPATIBLE`. The zero-constraint truncation
rate is recorded, and any quantity derived from a cell whose truncation
rate exceeds 0.10 is reported as a bound.

### 12.2 Dense ladder screen

At the selected cap, the pre-screen measures on the 24 pre-screen topics,
one draw per cell: the full $n$ grid for $A$, the full $m$ grid for $B$,
and all 94 reference ladder severities. This is
$(8 + 4 + 94) \times 24 = 2{,}544$ generations and produces the shortlist
of at most three ladder severities per family whose solo compliance is
nearest the pre-screen solo compliance of $A$.

### 12.3 Solo-compliance calibration and outcome selection

On the 96 solo-calibration topics at $M_{\text{cal}} = 4$ draws per cell,
the full $n$ grid, the full $m$ grid, and every shortlisted reference
severity are measured. This is at most
$(8 + 4 + 24) \times 96 \times 4 = 13{,}824$ generations.

**Selection of $n^*$.** Eligible values put solo compliance of $A$ in
$[0.50, 0.85]$. Among them $n^*$ minimises the distance from 0.70, with
the smaller $n$ breaking an exact tie.

**Selection of $m^*$.** Eligible values put solo compliance of $B$ in
$[0.60, 0.95]$. Among them $m^*$ minimises the distance from 0.80, with
the **smaller** $m$, meaning the more restrictive severity, breaking an
exact tie.

The bands are set so that both outcome constraints have room to fall under
composition without sitting at ceiling, which is what a delivery-loss
estimand requires and what the construct memo's §D.6 shows is absent from
most of the legacy corpus. No eligible value returns
`TARGET_RANGE_EXHAUSTED` or `FOCAL_RANGE_EXHAUSTED`, or
`GRID_RESOLUTION_INSUFFICIENT` when two adjacent registered severities lie
on opposite sides of a whole band. Every diagnosis records the complete
curve and makes a claim only about the registered grid.

### 12.4 Regime adequacy

A replication proceeds only when, on the calibration topics: solo
compliance of $A$ and of $B$ lie inside their bands; the realised solo
vacuity rate for $B$ is at most 0.10; and the graded distribution of each
outcome constraint is non-degenerate, meaning it is not concentrated above
0.99 or below 0.01. Otherwise the replication records `REGIME_NOT_FOUND`,
which is a statement about the registered grid and never about the model
or the hypothesis.

---

## 13. Reference calibration

### 13.1 What a reference is for

Under the recovered question the reference occupies the **companion** slot
in place of $A$. It estimates the counterfactual "what would composing $B$
with a comparable non-$A$ companion have cost?". It therefore has to
resemble $A$, and its resemblance to $B$ is irrelevant.

This inverts the v3 rule, which matched the reference to $B$ because $B$
occupied the swapped slot there. **v3 succeeded on its own criterion and
the criterion is the wrong one here.** Computed from the pinned Gate 2A
solo counts and used only as design evidence, the mean reference-minus-$B$
solo-compliance gap is $+0.052$ (E2B) and $+0.028$ (E4B), so the v3 rule
matched references to $B$ closely. The reference-minus-$A$ gap, which is
the quantity the recovered question needs, is $+0.198$ and $+0.210$.

The construct memo reports a related but distinct quantity in a **different
constraint vocabulary**: its $A$ is "write exactly 4 sentences", its $B$ is
"each sentence strictly longer than the last", and its $R$ is "begin every
sentence with a word starting with S", with pooled solo compliance 0.964,
0.541 and 0.716. Its §B.3 gap of $+0.193$ is reference minus **focal**, and
it is that gap the memo classifies `[Not identified]` for every estimand
comparing $P(X_B)$ against $P(X_R)$. In the memo's vocabulary the
reference-minus-target gap is $-0.248$, of the opposite sign to the v3
figure. The two memo figures are different kinds of estimate: $+0.193$ is
the memo's paired mean over the 19 runs containing all three constraints,
while $-0.248$ is derived here from its pooled marginals, whose pooled
reference-minus-focal counterpart is $+0.175$. The two corpora are not being equated here: the memo establishes
that companion difficulty is a live confound that no shipped analysis had
measured, and the v3 numbers establish independently that the confound
binds for the contrast this design registers.

### 13.2 Admission rule

Within family $f$, severity $q_f^*$ minimises
$\left| \hat P(X_{R_f}=1 \mid R_f \text{ alone}) - \hat P(X_A = 1 \mid A \text{ alone at } n^*) \right|$
subject to all of:

1. that absolute difference is at most **0.10** on the 96 solo-calibration
   topics, and the 95% Newcombe interval for the paired difference
   intersects $\pm 0.05$;
2. the same absolute difference is at most 0.15 on the disjoint 24
   pre-screen topics;
3. every frozen wording of the family at that severity is within 20% of
   the corresponding wording of $A$ in word count;
4. the constraint applies to the whole answer and parse independence holds
   for every registered verifier;
5. joint-satisfiability and non-entailment witnesses pass against $A$,
   against $B$, and against every other admitted reference;
6. the family's solo vacuity rate at that severity is at most 0.10.

The less restrictive severity breaks an exact within-family tie. At most
one severity per family. The final three are the admitted families with
the smallest solo distance from $A$, with family identifier breaking an
exact tie.

Condition 1 is a caliper on the companion's own difficulty. Its value is
set by what the calibration sample can support rather than by ambition:
the paired standard error of an $A$-versus-$R$ solo difference over 96
topics at $M_{\text{cal}} = 4$ is about 0.038 under the §16.1 variance
constants, so a caliper below about 0.10 would select mostly on noise and
a dense ladder would amplify that. Condition 2 is a disjoint-sample
confirmation against the same winner's-curse selection.

**The realised gap is measured precisely in the confirmatory data and
reported.** The confirmatory design contains the solo cell of $A$ and of
every admitted reference on all 384 blocks, giving a paired difference
standard error of about 0.019, twice as tight as the calibration
estimate. The realised companion-difficulty gap of every
admitted reference is reported beside every L3 statement. When any
realised gap exceeds **0.15**, the L3 statement carries a fixed
companion-difficulty block naming the reference and its gap, and the
registered sensitivity of §23 reports $D(B \leftarrow R_j)$ against the
realised gap across the three references.

### 13.3 What is deliberately not a matching criterion

**Composed uptake of the companion is not a matching criterion.** Under
this design composed compliance is the outcome; selecting a control on the
outcome it is meant to counterfactual is circular. The v4 revision 1
composed-uptake caliper is withdrawn.

**Composed response length is not a matching criterion.** Composition
shortens answers and shorter answers satisfy length-style constraints more
readily, so response length lies on the causal path from companion to
outcome. It is registered as a mediator in §22 and never conditioned on.

### 13.4 Reference heterogeneity is expected and is reported, never averaged away

The pilot found that at essentially constant companion solo compliance,
range 0.0000 for E2B and 0.0208 for E4B across its three references,
$D(B \leftarrow R_j)$ still varied by 0.177 and 0.188. Companion identity
moves delivery loss at fixed companion difficulty. The constancy is
measured at one draw per topic over 96 topics, so each solo rate carries a
standard error near 0.035 and the observed range understates the true
spread; the observation constrains the difficulty explanation and does not
settle it. v4 therefore reports
every per-reference quantity as family F2 with simultaneous intervals, and
registers a heterogeneity qualifier: when the three $\Delta_j$ intervals
do not all fall on the same side of the threshold used for an L3
statement, the L3 statement is emitted with a fixed block naming the
disagreeing reference and its value.

### 13.5 When references cannot be admitted

Fewer than three admitted families sets `EXCESS_NOT_IDENTIFIED` for that
model and routes it to the reduced design of §8.6. **This is not a
terminal status.** L1 and L2 remain available, because
$D(B \leftarrow A)$, $D(A \leftarrow B)$ and $\Lambda$ need only solo cells
and the $A+B$ cell.

This rule is what allows the two Qwen replications, which ended at v3 Gate
2A with `REFERENCE_POOL_MISMATCH` and produced no evidence, to be
estimable here. Whether any reference matched to $A$ exists for them is an
empirical question the v4 ladder screen answers, and neither outcome
blocks their primary estimands.

### 13.6 Composed-headroom validation

Every registered cell type is generated on the 24 composed-validation
topics at $M_{\text{cal}} = 4$ and its compliance rate is evaluated
independently against the band $[0.05, 0.95]$ for each of its two
constraints. This is at most $20 \times 24 \times 4 = 1{,}920$
generations. The gate is a viability predicate applied cell by cell. It
does not rank, select, or reorder anything, and it computes no contrast
between cells. Any cell type outside the band returns
`COMPOSED_HEADROOM_FAILURE` with the full table.

---

## 14. Unit of analysis, clustering, exclusions, and missingness

### 14.1 The block is the unit

| Role | Statement |
|---|---|
| Assignment | Both wording indices are assigned at the block and are identical across its cells; order is assigned within the block, so both order variants of every pair are present |
| Pairing | Every registered contrast is formed inside a block, removing between-topic variation |
| Clustering | The bootstrap resamples blocks; all of a drawn block's cell means travel with it |
| Generalisation | Uncertainty statements refer to the topic population of §6.2 |

Executable checks: each bootstrap replicate draws exactly 384 block
identifiers with replacement and asserts that each carries the registered
cell count for the design in force, 25 under §8.1 and 4 under §8.6; no
estimator function accepts a draw-level or response-level index; every
cell carries exactly $M$ committed accepted draws before any cell mean is
formed.

### 14.2 Exclusions, invalid generations, missingness, duplicates

- **No response is excluded from a primary estimand.** Empty responses,
  refusals, truncations and verifier-processing failures are scored by the
  registered rule and retained, because removing them would condition on
  events the treatment can cause.
- **Invalid generations**, meaning a backend failure that produced no
  text, are retried under the registered seed derivation. A cell that
  still lacks $M$ committed draws after retries fails the run closed for
  that cell; the analysis refuses to form a cell mean from fewer than $M$
  draws and no draw is imputed or substituted.
- **Missingness** is reported per cell type and per configuration, with
  the arm-differential missingness rate. A missingness rate above 0.01 in
  any cell type is reported beside every primary estimand.
- **Duplicates.** Every draw carries a seed derived from the root seed,
  stage label, model identity, prompt hash and draw index. Byte-identical
  replicate pairs within a cell are counted and reported; a duplicate rate
  above 0.05 in any cell fails qualification, because duplicate rows
  cannot count as independent replicates.
- **Deprecated and foreign sources** may never enter registered evidence.
  An executable guard refuses any analysis input whose manifest
  classification is not a registered v4 artifact. The construct memo's
  legacy-corpus quantities and the B+R pilot rows are design evidence and
  are structurally excluded from every v4 analysis input.

---

## 15. Multiplicity families

Families are declared **per configuration**, meaning per (model,
instruction order). Each configuration is a separate replication with its
own simultaneous statements. There is no cross-configuration and no
cross-model multiplicity family, because this protocol licenses no pooled
estimand.

| Family | Members | Size | Status |
|---|---|---:|---|
| **F1 Primary** | $D(B \leftarrow A)$, $D(A \leftarrow B)$, $\Lambda$, $\Delta_R$ | 4 | Supports L1, L2, L3 |
| **F2 Companion heterogeneity** | $D(B \leftarrow R_j)$ and $\Delta_j$, $j = 1,2,3$ | 6 | Secondary; L3 heterogeneity qualifier |
| **F3 Outcome-side control** | $D(A \leftarrow R_j)$, $j = 1,2,3$, and $\Delta^A$ | 4 | Secondary; the demoted v3 estimand |
| **F4 Matrix completion** | $D(\bar R \leftarrow A)$, $D(\bar R \leftarrow B)$, $D(\bar R \leftarrow \bar R')$, $\Xi$ | 4 | Secondary; outcome-by-companion table |
| **F5 Robustness** | The four F1 members under the vacuity-forced recoding, and $D(B \leftarrow A)$ and $\Delta_R$ under a graded-score threshold at 0.99 | 6 | Secondary; sensitivity of the primary |
| **F6 Degeneracy symmetry** | The vacuity-rate difference between each composed cell containing $B$ and the $B$ solo cell, namely $B{+}A$ and $B{+}R_j$ for $j = 1,2,3$ | 4 | Gate on the §17.4 interpretation |
| **F7 Reciprocal detail** | $D(R_j \leftarrow B)$ and $D(R_j \leftarrow A)$, $j = 1,2,3$ | 6 | Secondary |

Each family receives its own simultaneous 95% interval, computed by
standardising each member by its bootstrap standard error and taking the
largest absolute standardised deviation across the family in each
resample. Marginal intervals are reported alongside; decision rules read
the simultaneous intervals.

Reported with marginal intervals only and supporting no claim: joint-state
vectors and their redistribution, joint success, graded-score
distributions, response-length quantiles, finish-reason counts, accidental
occurrence counts, compliance by subject area and by wording index, the
greedy replication, cross-configuration summaries, and every
cross-model comparison.

---

## 16. Sample size and power

### 16.1 Variance model

Let $\phi$ be the share of a cell's compliance variance carried by
between-topic heterogeneity and $\rho$ the within-block correlation of the
topic component between two cells sharing an outcome constraint. With
$p(1-p)$ the cell compliance variance,
$\sigma^2_{\text{topic}} = \phi\, p(1-p)$ and
$\sigma^2_{\text{draw}} = (1-\phi)\, p(1-p)$. For $T$ blocks and $M$ draws:

$$\mathrm{Var}\!\left[\Delta_R\right] = \frac{2(1-\rho)\sigma^2_{\text{topic}} + \sigma^2_{\text{draw}}\left(\tfrac{1}{M} + \tfrac{1}{3M}\right)}{T}, \quad
\mathrm{Var}\!\left[D\right] = \frac{2(1-\rho)\sigma^2_{\text{topic}} + \tfrac{2\sigma^2_{\text{draw}}}{M}}{T}, \quad
\mathrm{Var}\!\left[\Lambda\right] = \frac{4(1-\rho)\sigma^2_{\text{topic}} + \tfrac{4\sigma^2_{\text{draw}}}{M}}{T}.$$

**Registered planning constants:** $p(1-p) = 0.215$, $\phi = 0.27$,
$\rho = 0.5$, giving $\sigma^2_{\text{topic}} = 0.0581$ and
$\sigma^2_{\text{draw}} = 0.1570$. The $\Lambda$ expression treats its four
cell means as carrying independent draw noise, which is conservative
because two of them are scored on the same generation.

**How $\phi$ was obtained, and what it does not pin down.** $\phi$ is
fitted to the **pilot's reported interval widths**, which are exploratory
variance information and carry no effect information. The fit uses the
pilot's own structure: its $P(B \mid \bar R)$ term averages three
reference cells measured on the same 96 topics, and its $P(B \mid A)$ term
comes from a disjoint 384-block set, so the fit constrains the correlation
*among reference cells* and says nothing about the correlation *between*
an $A{+}B$ cell and a $B{+}R$ cell, which is the $\rho$ the design
formulas use. Under the pilot's implied among-reference correlation of 1,
$\phi = 0.27$ reproduces the observed standard errors closely: predicted
0.0326 against 0.0315 observed for E2B, and 0.0284 against 0.0284 for
E4B. Refitting with an among-reference correlation of 0.5 instead gives
$\phi \approx 0.37$.

Both settings are therefore carried through §16.2, and the registered
allocation is chosen to satisfy every precision precondition under the
less favourable one. §29 and check C12 record that $\rho$ itself is
assumed rather than estimated, and C12 requires it to be estimated before
freeze from data that carry two composed cells on the same block, which
the pilot rows and the v3 confirmatory cache both do.

### 16.2 Registered allocation

**384 confirmatory blocks, order within block, $M = 4$ draws per cell, 25
cells per block: 38,400 cached generations per model and 153,600 across
four models.** Because order is a within-block factor, every configuration
is estimated on all 384 blocks.

Projected simultaneous half-widths, at the Šidák critical value 2.4909 for
the primary family of four and 2.6310 for the family of six:

| Quantity | Precondition | Projected at $\phi = 0.27$ | Projected at $\phi = 0.37$ | 80% power detectable effect, $\phi = 0.27$ | the same at $\phi = 0.37$ |
|---|---:|---:|---:|---:|---:|
| $D(c \leftarrow g)$ | 0.05 | 0.0470 | 0.0488 | 0.0628 | 0.0653 |
| $\Delta_R$ | 0.05 | 0.0422 | 0.0449 | 0.0565 | 0.0601 |
| $\Lambda$ | 0.08 | 0.0664 | 0.0690 | 0.0889 | 0.0923 |
| $\Delta_j$ (family of six) | 0.06 | 0.0496 | 0.0515 | not applicable | not applicable |

Every precondition is met under both fitted settings, with the tightest
margin at $\Delta_j$ under $\phi = 0.37$.

### 16.3 Why this allocation, and the alternatives considered

The withdrawn revision 1 allocation was sized so that its projected
detectable effect, 0.064 at $M = 8$ on 384 blocks, covered the 0.04 to
0.11 range of the v3 diagnostics of the target-side swap effect. That
justification lapsed with the estimand.

The requirement registered here is absolute rather than
effect-dependent: every primary member must reach its precision
precondition, which is set at half the smallest effect of interest for
$D$ and $\Delta_R$. No expected effect enters the calculation, and the
pilot's magnitudes are used only in §16.4 to state, in advance, which
threshold comparisons the design would and would not resolve.

Blocks buy more precision than draws once the draw term is small relative
to the topic term, because the draw term scales as $1/M$ and the topic
term does not. At $M = 4$ the two terms are already comparable, so
doubling $M$ cuts the standard error of $\Delta_R$ by 12.7% at twice the
cost, while doubling blocks cuts it by 29.3% at twice the cost.

| Blocks | $M$ | generations/model | hw $D$ | hw $\Delta_R$ | hw $\Lambda$ | hw $\Delta_j$ |
|---:|---:|---:|---:|---:|---:|---:|
| 288 | 4 | 28,800 | 0.0542 | 0.0488 | 0.0767 | 0.0573 |
| **384** | **4** | **38,400** | **0.0470** | **0.0422** | **0.0664** | **0.0496** |
| 480 | 4 | 48,000 | 0.0420 | 0.0378 | 0.0594 | 0.0444 |
| 384 | 8 | 76,800 | 0.0396 | 0.0369 | 0.0561 | 0.0419 |
| 480 | 8 | 96,000 | 0.0355 | 0.0330 | 0.0502 | 0.0375 |

Values shown at $\phi = 0.27$. 288 blocks at $M = 4$ fails the $D$
precondition at $\phi = 0.27$ and both the $D$ and $\Delta_R$
preconditions at $\phi = 0.37$, and it is the only cheaper entry. 384
blocks at $M = 4$ is therefore the cheapest allocation meeting all four
preconditions under both settings. The allocation is confirmed or increased at freeze by the
registered rule: take the smallest entry in this menu meeting every
precondition under the pre-freeze variance re-estimate of §16.1, and
record the choice in the freeze before any confirmatory generation.

### 16.4 What the allocation would and would not resolve

Applying the projected $\Delta_R$ half-width of 0.0422 to the pilot's four
order-stratified values, purely as an illustration of resolving power and
never as an expectation of the confirmatory result:

| Configuration | pilot $\Delta$ | projected interval | vs 0.10 | vs 0.25 |
|---|---:|---|---|---|
| E2B, $B$ first | +0.419 | [+0.377, +0.461] | resolved above | resolved above |
| E2B, $B$ second | +0.267 | [+0.225, +0.309] | resolved above | spans |
| E4B, $B$ first | +0.302 | [+0.260, +0.344] | resolved above | resolved above |
| E4B, $B$ second | +0.448 | [+0.406, +0.491] | resolved above | resolved above |

The design is sized to resolve the generic-load threshold wherever the
quantity is of the pilot's magnitude, and to resolve the pair-specific
threshold in most such cases. A configuration whose interval spans a
threshold is reported `INDETERMINATE` at that threshold, which is declared
here rather than discovered later.

### 16.5 Excluded planning sources

No effect estimate enters the sample-size calculation. The preconditions
are absolute and are derived from the smallest effect of interest. The
pilot contributes the variance constants and the §16.4 illustration and
nothing else. Calibration computes no companion-swap contrast at any
point. The procedural pilot computes no contrast. The v3 registered
effects contribute nothing.

## 17. Uncertainty, decision rules, and claim licensing

### 17.1 Uncertainty estimation

Nonparametric block bootstrap, 10,000 resamples, seeded from the
registration manifest, resampling the 384 blocks with replacement and
carrying every cell mean of each drawn block. A configuration's estimands
read the cells of that order.
Simultaneous intervals per family by the studentised maximum-modulus
construction of §15. Marginal percentile intervals reported alongside.

### 17.2 Direction and threshold rules

For each F1 member, direction is resolved when the simultaneous interval
excludes zero. For $\Delta_R$ the threshold rules of §3 apply. For $D$ and
$\Lambda$ the magnitude rules use the smallest effect of interest 0.10:
meaningful when the interval lies wholly beyond $\pm 0.10$.

### 17.3 Equivalence and the precision precondition

An equivalence statement about $D$ or $\Lambda$ requires the simultaneous
interval to lie wholly inside $\pm 0.10$ **and** its half-width to be at
or below the precondition of §16.2. A member whose realised half-width
exceeds its precondition records `INSUFFICIENT_PRECISION`, withholds every
equivalence and threshold statement, and still reports a resolved
direction if one exists. Any string asserting absence, equivalence or
negligibility is produced by a single guarded function whose precondition
is exactly this rule, and the analysis aborts if that function is reached
with the precondition false.

### 17.4 Vacuity and partial identification

Family F6 gates the interpretation. When every vacuity-rate difference is
at or below 0.05 or its interval includes zero, the primary estimands are
reported without qualification. Otherwise they are reported with a fixed
block stating that composition changed how often the outcome constraint
could bind, and the F5 vacuity-forced recomputation is reported beside
them as partial-identification bounds. A claim is licensed only when the
primary and the vacuity-forced recomputation license the same claim;
otherwise the axis is reported unresolved with both bounds.

### 17.5 Emission machinery

Every emitted statement carries the machine fields `claim_level`,
`configuration`, `family`, `interval_type`, `identification_status`,
`measurement_basis`, and the position of the outcome constraint. One
guarded emitter exists per claim level; each refuses a member name not
registered to it, so a secondary quantity cannot appear inside an L1, L2
or L3 statement. An executable check refuses any statement missing a
field, and a second refuses any statement that quotes a scalar without its
configuration.

---

## 18. Stage sequence and gates

| # | Stage | Passes when | Failure |
|---:|---|---|---|
| 1 | `QUALIFIED` | Clean tree, tracked implementation, resolved revisions, non-empty dependency manifest, schema-valid prompt plan, wording and witness suites pass for every registered pair, cache and durable store reachable, environment and commit hashable | `QUALIFICATION_FAILURE` |
| 2 | `GATE_0_APPARATUS` | The procedural pilot of §19 | `APPARATUS_FAILURE` |
| 3 | `REGIME_SCREEN` | Completion cap selected; dense ladder screen complete; shortlist written before any Gate 2 generation | `RESPONSE_LENGTH_INCOMPATIBLE` |
| 4 | `GATE_1_MEASUREMENT` | §10.2 for every registered outcome verifier, plus §10.3 or §10.4; verifier hash frozen | `MEASUREMENT_NOT_ESTABLISHED`, `MEASUREMENT_EVIDENCE_INSUFFICIENT` |
| 5 | `GATE_2_REGIME` | $n^*$ and $m^*$ selected inside their bands; §12.4 adequacy holds | `TARGET_RANGE_EXHAUSTED`, `FOCAL_RANGE_EXHAUSTED`, `GRID_RESOLUTION_INSUFFICIENT`, `REGIME_NOT_FOUND` |
| 6 | `GATE_3_REFERENCES` | Three families admitted under §13.2 | Not terminal: sets `EXCESS_NOT_IDENTIFIED` and the reduced design of §8.6 |
| 7 | `GATE_4_COMPOSED_HEADROOM` | Every registered cell type inside $[0.05, 0.95]$ on both constraints | `COMPOSED_HEADROOM_FAILURE` |
| 8 | `GATE_5_FREEZE` | The freeze record of §18.1 written and verified | none |
| 9 | `CONFIRMATORY_GENERATION` | Complete draw matrix committed | none |
| 10 | `MASKED_ANALYSIS` | §20 | none |
| 11 | `UNMASKING` and `UNMASKED_ANALYSIS` | §20 | none |

Every command verifies the content hash and signature of its predecessor
record and re-verifies the frozen verifier hash (§10.6) before any
mutation. A terminal state mechanically disables every later generation
command. Every attempted transition is logged with timestamp, revisions,
producing commit, environment digest, input and output hashes, and
outcome.

### 18.1 The freeze record

Model revision, completion cap, $n^*$, $m^*$, admitted reference families
and severities or the `EXCESS_NOT_IDENTIFIED` marker, every wording, topic
splits, prompt template, chat-template hash, every verifier source and the
canonical verifier hash, the graded-score definitions, the non-vacuity
predicates, decoding settings, $M$ and the block count with the §16.1
re-estimate that justified them, seed rules, the 25-cell plan, family
declarations, thresholds and regions, precision preconditions, the claim
ladder, the codebook, producing commit, clean-tree assertion, dependency
and environment digests, hardware record, gate-record hashes, the Gate 1
measurement basis, and the complete analysis plan.

No scientific rule changes after the study-wide freeze. Any change creates
v5. Any model-specific frozen-field change after that model's confirmatory
generation begins creates a new protocol version and leaves the original
result unchanged.

---

## 19. Qualification and procedural pilot

Qualification is non-scientific and reads no behavioural rate. After it, a
procedural pilot on twelve fixed pre-screen topics runs all 25 cells, both
orders, and the registered wording allocation, at fixture values that
cannot become calibration evidence, with $M = 4$: 1,200 cached draws.

Acceptance requires all of: every logical cell and draw committed exactly
once; every cell yielding one cell mean over exactly $M$ accepted draws;
zero technical generation failures after retries; every codebook field
present and in domain; the full analysis pipeline running to a
structurally complete result table with every numeric value redacted;
mutating one stored byte changing its content hash and causing the
analysis to refuse the row; cache deletion and durable restore
reproducing every row with matching hashes; and the separate pilot mask
cycle completing without touching the confirmatory mask namespace.

Failure returns `APPARATUS_FAILURE`; repair creates a new producing commit
and requires qualification and the pilot to run again.

---

## 20. Masking and unmasking

**What is masked.** After confirmatory generation and before any analysis,
the pipeline permutes the **companion label** within each (outcome
constraint, order, block) group of composed observations, using a seed
from the system random source. Solo cells carry no companion and are not
permuted. The primary contrasts are companion swaps, so this is the
dimension that must be hidden.

**What is not masked, declared.** A composed generation contributes two
observations whose companion labels are permuted independently, so
joint-state and joint-success quantities cannot be computed in the masked
phase. They are computed after unmasking under the fully registered plan
of §11.5 and are labelled as computed post-unmasking. This is a stated
limitation of the masking scheme, and those quantities support no L1, L2
or L3 claim.

**Masked phase.** All planned analysis code executes on the permuted
table. All reading of response text, all hand coding, all inspection of
degeneracy and compliance quantities, and all anomaly diagnosis happen
here. Permitted: repairing an analysis defect, adding a diagnostic,
declaring an anomaly and fixing the rule that will handle it. Forbidden
here and afterwards: changing an estimand, family, threshold, region,
precondition, reference set, verifier, scoring rule, claim rule, claim
level, non-vacuity predicate, or topic split.

**Unmasking.** A single named function invoked once, writing a timestamped
entry with the content hash of the analysis code at that moment. Executable
checks: the permuted labels differ from the true labels in at least half
of the blocks in every group; the mask key file is opened exactly once in
a full run; the recorded analysis-code hash at unmasking reproduces every
masked-phase output byte for byte.

**After unmasking.** Any analysis-code change is labelled post-unmasking,
is exploratory, and supports no registered claim. Masked and unmasked
outputs are both released.

---

## 21. Analysis order

1. Load confirmatory rows; reject any row outside the frozen plan by
   prompt hash, revision, verifier hash, or block identity.
2. Re-verify the frozen verifier hash; fail closed on mismatch.
3. Assert the complete matrix of 384 blocks by the registered cell count
   of the design in force by $M$ draws, each committed exactly once; count
   duplicates and missingness.
4. Form cell means over all $M$ accepted draws; refuse any partial cell.
5. Score the compliance vector, the graded vector and the degeneracy flags
   for every constraint present.
6. Compute per-cell compliance, vacuity, truncation, length and
   graded-score summaries.
7. Form the delivery losses, the asymmetry and the companion swaps within
   each configuration.
8. Run the block bootstrap with 10,000 resamples inside each
   configuration.
9. Compute simultaneous intervals within each declared family.
10. Compute the F5 vacuity-forced recomputation and the F6 gate.
11. Apply the claim ladder of §3 with the rules of §17, emitting through
    the guarded emitters.
12. Compute the post-unmasking joint-state and redistribution quantities
    and label them.

The analysis fails closed. A missing cell, an incomplete draw set, a
duplicate accepted row, a non-finite standard error or a non-finite bound
returns a named inconclusive status for the affected quantity and computes
no claim. No cell, block, constraint or draw is dropped, and no missing
value is imputed. The design is fixed size: no interim analysis, no
optional stopping, no adaptive sample size.

---

## 22. Prohibited and mediating quantities

Recorded for every generation and never entering a primary estimand as a
covariate, filter, stratifier or weight: response length in words and
tokens, truncation status, finish reason, graded score, vacuity flag,
accidental occurrence count, joint state, and any other quantity produced
during or after generation. The analysis asserts this by checking the
declared causal role of every field named in a primary formula.

**Response length is registered as a mediator.** Composition shortens
answers, and shorter answers satisfy length-style constraints more
readily, so response length lies on the path from companion to outcome.
It is reported per cell, its composed-to-solo change is reported per
constraint, and a registered descriptive decomposition reports the
delivery loss within strata of realised response length. No mediation
effect is claimed, and no primary estimand is adjusted for it. Changing
the estimand to a length-conditional one would require a new protocol
version.

---

## 23. Secondary analyses and error analysis

All Tier-secondary, none able to change a primary conclusion.

- Every F2 to F7 member with its simultaneous interval.
- Joint-state vectors per composed cell and their redistribution across
  order and checkpoint.
- Joint success per composed cell.
- The graded vector distribution per cell, and the graded manipulation
  check: the graded score on a constraint with the instruction present
  minus the same score on the cell where it is absent.
- The demoted v3 estimand $\Delta^A$, reported only with its three gates
  satisfied and its configuration quoted.
- Failure taxonomy for the exact-count constraint: empty, cut off,
  refusal, restatement, target inside a longer word, zero occurrences, too
  few, too many, other, applied in that priority order, split by whether
  the realised margin is exactly one.
- The primary estimands recomputed under $S_1$, $S_2$ and $S_3$ for the
  $A$-side outcome.
- Companion-difficulty sensitivity: $D(B \leftarrow R_j)$ reported against
  the confirmatory-measured solo-compliance gap between $R_j$ and $A$,
  across the three admitted references, descriptive only.
- Confounder description: compliance as a function of response length,
  truncation, refusal and subject area within each cell, with any material
  association reported as a competing explanation.
- The greedy replication on 96 blocks, reported as a different generation
  population.
- The realised variance decomposition, namely $\sigma^2_{\text{topic}}$,
  $\sigma^2_{\text{draw}}$ and the within-block correlations of §16.1
  estimated from the confirmatory cell means, reported beside every
  primary estimate together with the realised simultaneous half-width and
  the achieved detectable effect it implies. No draw is selected and no
  re-selection diagnostic exists, because the estimator averages all $M$
  draws.
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
5. Compare the primary convention against prespecified reasonable
   alternatives, registered before the comparison is run.
6. Report the alternatives as robustness analyses. Switching a scoring
   convention after results are seen is prohibited.

For the exact-count constraint the enumerated cases include ordinary
punctuation adjacent to the target word, concatenated copies, hyphenation,
Unicode punctuation, Unicode lookalikes, zero-width characters,
capitalisation, and sentence-boundary punctuation. For the word-length and
budget constraints they include empty output, single-token output,
hyphenated and apostrophised forms, non-Latin script, digits and symbols
adjacent to words, and markdown emphasis.

The goal is to know exactly what construct each deterministic rule
operationalises and how often its edge cases matter empirically, not to
make any rule imitate human intuition.

---

## 25. Contamination

Every v4 topic is newly written; no v3 topic and no pilot topic enters any
v4 set. At release the exact text of each confirmatory topic is queried
against a public web search index and the number of exact-phrase matches
is reported. A canary string is embedded in the released dataset file. The
96 v4 sequestered topics are withheld; the 96 v3 sequestered topics remain
sequestered and untouched.

Accidental compliance is measured directly: in every cell where a
constraint is absent, that constraint's verifier is still evaluated and
recorded, giving the base rate at which an unconstrained or
differently-constrained answer satisfies it by chance. Any cell whose
truncation rate exceeds 0.10 has its accidental-compliance figure reported
as a bound.

The outcomes are instruction compliance, which does not depend on knowing
a correct answer, so memorised answer content cannot by itself produce a
pass.

---

## 26. Execution integrity and provenance

Every generation records stage, artifact state, model replication, block,
cell type, constituent constraint identities and severities, order,
position of each constraint, wording indices, draw index, prompt hash,
model revision, backend version, interpreter identity, dependency digest,
hardware class, seed, raw response, response content hash, token counts,
finish reason, and every verifier verdict, graded score and degeneracy
flag with the verifier source hash.

Artifacts move monotonically through `generated`, `committed`, `accepted`
and, when audit-preserved and excluded, `superseded`. A committed artifact
becomes accepted only after durable write, content-hash verification,
stage authorisation, predecessor-gate verification, schema validation and
frozen-plan membership. A superseded artifact never returns to accepted.

The artifact-type vocabulary is closed:

```
qualification_record   prefreeze_plan        pilot_record
gate_record            calibration_record    registered_freeze
confirmatory_evidence  masked_result         unmasked_result
superseded_non_evidence
```

Every model tree contains the same required records, with every path
derived through one frozen path function:

```
qualification.json      gate0_apparatus.json    regime_screen.json
gate1_measurement.json  gate2_regime.json       gate3_references.json
gate4_composed.json     gate5_freeze.json
transition_log.jsonl    terminal_report.json
```

and, when confirmation is reached, `confirmatory_manifest.json`,
`masked_result.json` and `unmasked_result.json`. Missing, stale or
unexpected paths fail evidence verification.

The run aborts on a missing or invalid predecessor
record, a dirty tree, an invoked source absent from the producing commit,
a prompt exceeding the context limit, a revision or hardware or dependency
change inside a run, a prompt hash absent from the frozen plan, a
duplicate accepted draw, a cell whose accepted draw count differs from
$M$, a verifier hash differing from the frozen value, a content-hash
mismatch, a stale output path, or an artifact whose declared type
disagrees with its stage. Every transition is written to an append-only
log, and `generated`, `committed` and `accepted` counts are reported
separately.

The v4 implementation lives in its own namespace, imports nothing from any
earlier DCI implementation, writes nothing inside any v3 or pilot evidence
tree, and refuses any analysis input classified deprecated or foreign.

---

## 27. Codebook and computational environment

A codebook accompanies every released table with one row per variable
giving name, type, permitted values, units, causal role and a
one-sentence definition. Causal role takes one of identity, treatment,
design, outcome, post-treatment, provenance. Executable checks: every
released column appears in the codebook and every codebook row appears as
a column; every value is in domain and of declared type; no
post-treatment field appears in a primary formula; every field declared to
constrain execution is consumed by a named check in §26.

The environment record contains lockfile and frozen-export hashes,
interpreter and version, exact invocation command, backend version and
settings, tensor-library and driver versions, operating system and kernel,
GPU name and architecture, model repository and revision, chat-template
hash, and registered execution-relevant environment variables. Executable
checks: a dependency change moves the environment digest and an empty
manifest is rejected; deterministic derivations reproduce their recorded
hashes from the producing commit; rerunning the analysis in the recorded
environment on released raw responses reproduces the released table byte
for byte; cache deletion and durable restore reproduce every committed row
and regenerate no committed draw.

---

## 28. Outcome vocabulary, terminal statuses, and identification statuses

### 28.1 Confirmatory outcomes

Recorded per F1 member per configuration.

| Outcome | Condition | Licensed statement |
|---|---|---|
| Delivery loss resolved | The simultaneous interval for $D(c \leftarrow g)$ has lower bound above 0 | Composing $c$ with $g$ reduced delivery of $c$ in this configuration, with $c$ stated in the named position |
| Delivery gain resolved | Upper bound below 0 | Composing $c$ with $g$ raised delivery of $c$ in this configuration |
| Meaningful magnitude | The interval lies wholly beyond $\pm 0.10$ | The change exceeds the smallest effect of interest |
| Equivalence | The interval lies wholly inside $\pm 0.10$ and the half-width meets its precondition | Any change is smaller than the smallest effect of interest, at adequate precision |
| Asymmetry resolved | The $\Lambda$ interval excludes 0 | The loss is directionally asymmetric between $A$ and $B$ in this configuration |
| Excess above generic-load threshold | The $\Delta_R$ lower bound exceeds 0.10 | $A$ costs $B$ more than companions matched to $A$ on solo compliance do, by more than the registered generic-load threshold |
| Pair-specific threshold reached | The $\Delta_R$ lower bound exceeds 0.25 | The excess reaches the source memo's pair-specific threshold |
| Generic compositional load | The $\Delta_R$ upper bound is below 0.10 | The excess is below the registered generic-load threshold; the delivery loss is attributable to composition rather than to this companion |
| Indeterminate at a threshold | The interval spans that threshold | The design did not separate the two readings at that threshold in this configuration |
| Insufficient precision | The realised half-width exceeds its precondition | The design did not achieve the registered precision; equivalence and threshold statements are withheld |
| Reference heterogeneity | The three $\Delta_j$ intervals do not agree on one side of the threshold used | The L3 statement is emitted with the disagreeing reference named |
| Companion-difficulty qualifier | A realised confirmatory-measured solo-compliance gap between $A$ and an admitted reference exceeds 0.15 | The L3 statement is emitted with the reference and its realised gap named, and the §23 sensitivity reported beside it |
| Vacuity asymmetry | An F6 difference exceeds 0.05 with its interval excluding zero | Composition changed how often the constraint could bind; claims follow both partial-identification bounds |
| Replication | The same classification in every registered configuration | The classification is stable across the registered configurations |
| Configuration dependence | Classifications differ across configurations | The quantity is configuration-dependent; the table is reported and no pooled scalar is quoted |

### 28.2 Identification statuses, which are not terminal

| Status | Meaning |
|---|---|
| `EXCESS_NOT_IDENTIFIED` | Fewer than three references admitted under §13.2. L1 and L2 proceed under the reduced design; L3 is withheld |
| `POSITION_CONFOUNDED` | Attached to every L1 statement in the configuration where the outcome constraint is not stated first |
| `HUMAN_VALIDATION_UNAVAILABLE` | No independent annotator; the measurement basis is the autorater pathway and the scope sentence of §10.5 is attached |

### 28.3 Terminal statuses

| Status | Condition |
|---|---|
| `QUALIFICATION_FAILURE` | Code, model, environment, schema, witness or provenance qualification fails |
| `APPARATUS_FAILURE` | Execution, cache, hashing, storage restoration, mask plumbing or integrity machinery fails |
| `RESPONSE_LENGTH_INCOMPATIBLE` | Every registered cap has truncation above 0.10 on constrained prompts |
| `TARGET_RANGE_EXHAUSTED` / `FOCAL_RANGE_EXHAUSTED` | An outcome constraint's curve stays outside its band at a registered grid boundary |
| `GRID_RESOLUTION_INSUFFICIENT` | Adjacent registered severities jump across a whole band |
| `REGIME_NOT_FOUND` | §12.4 adequacy fails |
| `COMPOSED_HEADROOM_FAILURE` | A registered cell type falls outside $[0.05, 0.95]$ on either constraint |
| `MEASUREMENT_NOT_ESTABLISHED` / `MEASUREMENT_EVIDENCE_INSUFFICIENT` | §10.3 criteria fail or cannot be reached |

Every terminal record carries the model and revision, gate, criterion,
threshold, observed value, complete curves, admission table, composed
table, degeneracy and truncation summary, verifier status and measurement
basis, artifact hashes, producing commit, environment digest, the
strongest permissible statement, and the estimands left unanswerable. It
also carries verbatim: **a terminal pre-confirmatory status carries no
evidence about the effect.**

`REGIME_NOT_FOUND` is a statement about the registered grid. It is never
reported as a failure of the model or of the hypothesis.

---

## 29. Limitations and design trade-offs

**Load two only.** The construct memo's best-evidenced interaction
quantity is three-place and requires a background constraint. This design
cannot estimate it and takes no position on whether the phenomenon is
two-place or higher-order.

**Matched, not semantic.** An excess attributable to $A$ is an excess
relative to companions matched on solo compliance and instruction length.
Other properties of $A$ remain free, so semantic identity-specificity is
not identified and is never claimed.

**Configuration dependence is a scope condition, not noise.** Eight
registered configurations are reported separately. A quantity that
reverses or changes magnitude across them is reported as
configuration-dependent, and no pooled scalar is offered as a summary.

**The position confound.** In the configuration where the outcome
constraint is stated second, $D(c \leftarrow g)$ mixes added load with a
change of position. Only $\Delta$-type quantities are position-clean in
both configurations.

**Vacuous passing is bounded, not eliminated.** Non-violation constraints
can be satisfied by degenerate output. The registered predicate, the
per-cell vacuity rates, the F6 gate and the partial-identification
recomputation bound the effect; they do not remove it, and the 20-word
predicate threshold is a judgement fixed in advance.

**The variance model is a projection.** It is fitted to two models' pilot
interval widths, and the fit constrains only the correlation among the
three reference cells, giving $\phi = 0.27$ if that correlation is 1 and
about 0.37 if it is 0.5. The correlation the design formulas use, between
a cell containing $A$ and a cell containing a reference with the same
outcome constraint, is assumed at 0.5 and cannot be estimated from the
pilot, whose $A$ term came from a disjoint topic set. Both $\phi$ settings
are carried through §16.2 and the allocation meets every precondition
under both. §16.1 and check C12 require both correlations to be estimated
before freeze, and an unfavourable realisation appears as
`INSUFFICIENT_PRECISION` rather than as a silent widening.

**The pilot is exploratory throughout.** Its point estimates never
function as the expected confirmatory effect, its topics are excluded from
v4, and its rows cannot enter a v4 analysis.

**Measurement may remain verifier-defined.** If no independent annotator
is available, the basis is the autorater pathway and every claim carries
the scope sentence of §10.5.

**In-house reliability evidence.** No prior instrument for these
constructs exists outside this programme.

**Single-custodian masking.** The mask key is opened once by the analysis
code, with the protection resting on recorded hashes and timestamps.

**Joint-state quantities are unprotected by masking**, as declared in §20.

---

## 30. Release

Released under a permissive licence when results are reported: all 528
non-sequestered v4 topics with the canary string and a manifest recording
that 96 of the 624 are withheld; every constraint definition, ladder, wording,
witness and verifier source; the graded-score and non-vacuity definitions;
the boundary suites and adversarial corpora; study-wide and per-model
freeze records; qualification, gate, transition and terminal reports;
commit and clean-tree records; lockfile, frozen dependency export and
environment manifest; the codebook; every prompt; every committed raw
draw with its content hash, artifact state, compliance vector, graded
vector and degeneracy flags; human labels and carry-over records;
autorater configuration, judgments and calibration records where that
pathway was used; calibration records including the complete ladder curves
and admission tables; masked and unmasked outputs; the unmask timestamp;
analysis code; and the machine-readable result table carrying each
estimate with its configuration, claim level, family, identification
status, measurement basis, standard error, marginal and simultaneous
bounds, realised half-width, realised variance decomposition, achieved
detectable effect and cell counts.

Every reported figure is reproducible from the result table without
regenerating a response, and every number in that table is reproducible
from accepted raw responses in the recorded environment.

---

## 31. Amendment procedure and allowed deviations

Before study-wide freeze, any change is a revision of this document,
recorded with its date, its evidence and its author, and is prospective by
definition because no confirmatory data exist.

After study-wide freeze: operational settings that cannot change a
scientific quantity, such as device placement or batch size, may change
with a recorded environment note. Every other change creates v5. A
model-specific frozen-field change after that model's confirmatory
generation begins creates a new protocol version and leaves the original
result unchanged. An amendment is never used to weaken a criterion in
order to make a gate pass.

Amendments are recorded in a single append-only register carrying the
amendment text, its timing relative to every affected artifact, what it
supersedes, and what it leaves untouched.

---

## 32. Changelog and the disposition of historical DCI quantities

The full changelog is `DCI1_v4r2_changelog.md`. The dispositions it
records are binding here.

| Quantity | Disposition | Reason |
|---|---|---|
| $\tau$, target damage under $A+B$ versus $A+R$ | **Demoted** to a gated diagnostic, re-expressed as $\Delta^A$ on the compliance scale | Three sign reversals in the legacy corpus; structurally degenerate where the target is at ceiling; and it is the near-zero side of an asymmetric phenomenon |
| Target failure $F_A$ as the sole primitive | **Replaced** by the compliance vector $X$ with the graded vector $G$ | Memo §H; a checkpoint exists where joint compliance moves 70 points while $\tau$ is 0.000 in all four cells |
| Reciprocal delivery loss $D(c \leftarrow G)$ | **Adopted** as primary | Needs no reference, no commensurability assumption, and survives target ceiling |
| Asymmetry $\Lambda$ | **Adopted** as primary | The one-sided sacrifice is the directional content of the phenomenon |
| Companion swap $\Delta_R$ | **Adopted** as primary | It is the memo's §G row 1 discriminating quantity |
| Joint-state redistribution | **Retained** as a registered secondary, used within cell | The only representation in which low joint success and one-sided abandonment are visible |
| $\Delta_{\text{joint}}$ across arms | **Abandoned** | It cannot separate "the constraint is harder" from "the constraint conflicts" without a difficulty-matched pool |
| $\Gamma$, the three-place interaction | **Out of scope** at load two, retained as the memo's secondary estimand of record for a future load-three design | This architecture carries no third constraint |
| The surrogate outcome constraint and $\iota$ | **Abandoned** | Introduced in v4 revision 1 to reconstruct a recommendation that has since been recovered and is different |
| Exchangeability of the reference set as a claim gate | **Replaced** by reference admission on solo compliance plus the F2 heterogeneity qualifier | Exchangeability was a post-hoc property of a set selected on the wrong dimension |
| Composed-uptake matching | **Abandoned** | Composed compliance is now the outcome |
| Matched-reference design | **Retained** as a control arm and removed as a prerequisite | Memo §H: it is needed for $\tau$, not for the primary estimand |

---

## 33. Registered open decisions

Recorded here so they cannot migrate into the analysis. Each is closed by
recording the decision and its evidence in the signed manifest **before
study-wide freeze**, and none may be decided after any confirmatory
generation. `DCI1_v4r2_unresolved_decisions.md` gives the full statement
of each.

| # | Open decision | Default if unresolved |
|---|---|---|
| V1 | The confirmatory compute budget, and with it the allocation from the §16.3 menu and the number of models carried to confirmation | 384 blocks, $M = 4$, four models, 153,600 generations |
| V2 | Whether a load-three arm with a registered background constraint is added so that the memo's $\Gamma$ becomes estimable | No load-three arm; §5 exclusion stands |
| V3 | The reference solo-compliance caliper, registered at 0.10 with a Newcombe-interval condition and a confirmatory-measured realised-gap qualifier at 0.15 | 0.10, with `EXCESS_NOT_IDENTIFIED` rather than widening |
| V4 | The non-vacuity word threshold, registered at 20 | 20 words |
| V5 | Whether references should span a range of companion difficulty in addition to being matched, so that delivery loss can be read against companion difficulty | Matched only |
| V6 | Whether the two Qwen replications run the full or the reduced design, which the v4 ladder screen decides empirically | Decided by Gate 3 per model |
| V7 | Authoring 624 new topics, against reusing any v3 set | Author 624 new topics |
| V8 | Whether an independent annotator will be available, which decides the measurement basis | Autorater pathway with `HUMAN_VALIDATION_UNAVAILABLE` |
| V9 | Whether a second focal-like outcome constraint is added as an exploratory test of outcome-side specificity | Not added |
