# DCI-1 v4 revision 2: unresolved decisions

**Date:** 19 August 2026 · **Parent:** `DCI1_preregistration_v4r2.md` §33.

Part 1 dispositions every open item of v4 revision 1. Part 2 states the
decisions that are genuinely open under revision 2. Every Part 2 item is
closed by recording the decision and its evidence in the signed
registration manifest **before study-wide freeze**, and none may be
decided after any confirmatory generation.

---

## Part 1. Disposition of the revision 1 register U1 to U12

| # | Revision 1 item | Disposition | Why |
|---|---|---|---|
| **U1** | The name and cell set of the "B+R / B+S" discriminating design, inferred as an outcome-crossing difference in differences over a surrogate target | **RESOLVED** | The source is available. `dci-construct-pass2.md` §G row 1 specifies a **companion** swap on the focal outcome: generate B+R and B+S without the target A, beside the existing B-alone and B-with-A cells, and read D(B←A) − D(B←R) against 0.25 and 0.10. The pilot has already executed the B+R half in the v3 architecture; the B+S half generated nothing, because v3 §1 registers the background set as "Empty in this study", so B+S coincides with the B-alone cell. The inferred outcome-crossing design is withdrawn |
| **U2** | The surrogate target word, registered as *hence* | **NO_LONGER_APPLICABLE** | The surrogate existed only to carry the withdrawn crossing. No recovered question requires a second outcome constraint. The related but distinct question of outcome-side specificity is carried as V9 |
| **U3** | Whether to change the target word so the focal grid can extend below $m = 7$ | **MODIFIED** | The premise inverted. Under the new estimand $B$ is an outcome whose solo compliance should be high with room to fall, so the $m \ge 7$ floor is benign. The decision is replaced by the §12.3 selection rule, which places $B$'s solo compliance nearest 0.80 inside $[0.60, 0.95]$ |
| **U4** | Confirmatory draws per cell $M$, registered at 8 | **MODIFIED** | The justification was sized against the withdrawn surrogate estimand. Re-planned in §16 to $M = 4$ with 384 blocks and order as a within-block factor, against absolute precision preconditions, on a variance model fitted to the pilot interval widths. The residual budget question is V1 |
| **U5** | Calibration draws per cell $M_{\text{cal}}$, registered at 4 | **MODIFIED** | The value is retained and its justification is not. The matching target moved from $B$ to $A$ and the caliper tightened, so the selection-noise problem is worse, not unchanged: the paired standard error of an $A$-versus-$R$ solo difference over 96 topics at $M_{\text{cal}} = 4$ is about 0.038. The registered response is to set the caliper at 0.10 rather than below the noise, and to re-measure the realised gap on the confirmatory solo cells, where the same standard error is about 0.019, and report it beside every excess-damage statement (V3) |
| **U6** | The composed-uptake admission caliper, registered at 0.15 | **NO_LONGER_APPLICABLE** | Composed compliance of the companion is now the primary **outcome**. Selecting a control on the outcome it is meant to counterfactual is circular. Withdrawn, and replaced by the solo-compliance caliper on the companion (V3) |
| **U7** | Whether a two-reference degraded path should exist | **RESOLVED, dissolved** | References no longer gate the primary estimands. Fewer than three admitted references sets `EXCESS_NOT_IDENTIFIED` and routes the model to the registered reduced design, which still estimates $D(B \leftarrow A)$, $D(A \leftarrow B)$ and $\Lambda$. There is no degraded-path question left |
| **U8** | Whether the v3 topic bank may be reused | **STILL_UNRESOLVED**, carried as **V7** | The question is unchanged in kind and now identical in scale: v4 needs 384 confirmatory blocks and a 624-topic bank at 52 per area, which is exactly the v3 structure, so the choice is purely between authoring cost and contamination exposure |
| **U9** | Whether composed response length should become an admission predicate | **RESOLVED** | Composition shortens answers and shorter answers satisfy length-style constraints more readily, so response length lies on the causal path from companion to outcome. It is registered as a **mediator** in §22, reported and never conditioned on |
| **U10** | Whether reference families whose ladder is exhausted should receive conjunctive extensions | **MODIFIED** | The concern **intensifies** rather than reverses. Revision 1 worried that families are already too easy at their most restrictive severity; matching to $A$, whose solo compliance is 0.146 and 0.182 below $B$'s in the two pilot models, requires still harder severities, so the ladder is under more pressure than before. Whether a matched severity exists is now an empirical pre-freeze check (`DCI1_v4r2_prefreeze_checks.md` C7) rather than a design decision, and failure is the registered `EXCESS_NOT_IDENTIFIED` outcome rather than a blocker |
| **U11** | Execution order and the early-stop rule | **RESOLVED** | The early-stop rule is withdrawn: no replication's outcome can invalidate a design whose primary estimands need no cross-model quantity. Order runs the two pilot models first so that the apparatus is exercised where prior operating points are known |
| **U12** | Whether a form-varying second surrogate should be added | **NO_LONGER_APPLICABLE** | Superseded together with the surrogate design. The nearest live question, a second focal-like **outcome** constraint testing outcome-side specificity, is V9 and is a different question |

---

## Part 2. Genuinely open decisions under revision 2

### V1. Confirmatory compute budget, allocation, and number of models

**Open.** §16.2 registers 384 blocks with order as a within-block factor,
$M = 4$, 25 cells: 38,400 cached generations per model and 153,600 across
four models. §16.3 registers a menu with 288, 384 and 480 blocks and
$M \in \{4, 8\}$. The choice among them, and whether all four models
proceed to confirmation, depends on compute that this document cannot
observe.

**Rule already registered.** The allocation is chosen from the menu by the
smallest cost meeting every precision precondition under the pre-freeze
variance re-estimate, and the choice is recorded in the freeze before any
confirmatory generation.

**What is genuinely open.** Whether the budget supports four models at the
selected allocation, and if not, which models are carried. The two Gemma
models have prior operating points and pilot data; the two Qwen models are
the ones the v4 architecture newly unblocks and therefore carry the most
new information about whether the phenomenon is a capability threshold.

**Default.** 384 blocks, $M = 4$, four models.

**Consequence of getting it wrong.** `INSUFFICIENT_PRECISION` on one or
more primary members, which withholds threshold and equivalence
statements while leaving resolved directions intact.

---

### V2. Whether to add a load-three arm

**Open.** The construct memo's best-evidenced interaction quantity is the
three-place $\Gamma = [F(A{+}S{+}B) - F(A{+}S)] - [F(A{+}B) - F(A)]$, at
$+0.312$ with an interval clear of zero in the legacy corpus, estimated
from a complete matched factorial. It requires a background constraint and
a load-three cell. The v3 and v4 architectures carry a topic question and
no third constraint, which is exactly why the pilot could map the memo's
B+S cell onto the existing B-alone cell.

**What adding it would cost.** A registered background constraint with its
own wordings, witnesses, verifier, graded score and non-vacuity predicate;
a count-matched inert control to separate load from background identity;
and six instruction orders rather than two at load three.

**What not adding it costs.** The design takes no position on whether the
phenomenon is two-place or higher-order, and the memo's finding that
"the object is at least three-place, not two-place" in the legacy corpus
remains untested in this constraint vocabulary.

**Default.** No load-three arm. The exclusion is stated in §5 and §29.

---

### V3. The reference solo-compliance caliper

**Open.** §13.2 registers $\left| P(R \text{ solo}) - P(A \text{ solo}) \right| \le 0.10$
on the 96 solo-calibration topics, with the 95% Newcombe interval for the
paired difference intersecting $\pm 0.05$, a 0.15 confirmation on the
disjoint pre-screen sample, and a confirmatory-measured realised-gap
qualifier at 0.15.

**Why 0.10 and not tighter.** The realised gap under the v3 rule, computed
from the pinned Gate 2A solo counts and the v3 target-alone arm and used
only as design evidence, is $+0.198$ for E2B and $+0.210$ for E4B. A tight
caliper would be desirable and the calibration sample cannot support one:
the paired standard error of the difference over 96 topics at
$M_{\text{cal}} = 4$ is about 0.038, so a caliper of 0.05 would select
mostly on noise across a dense ladder. 0.10 halves the realised gap while
staying above the selection noise, and the confirmatory design then
measures the realised gap at a standard error near 0.019 and reports it
beside every excess-damage statement.

**Not the memo's number.** The construct memo's $+0.193$ is a
reference-minus-**focal** gap in a different constraint vocabulary, where
its constraints are "exactly 4 sentences", "each sentence longer than the
last" and "sentence-initial S". The v3 reference-minus-focal gap is
$+0.052$ and $+0.028$, so the v3 rule matched on its own criterion. What
transfers from the memo is the lesson that companion difficulty is a live
confound, not the figure.

**Risk.** Even at 0.10 the caliper may admit fewer than three families,
which sets `EXCESS_NOT_IDENTIFIED` and reduces the design. Whether it is
feasible is check C7.

**Countervailing evidence, recorded without overclaiming.** Within each
pilot model the three references have almost identical solo compliance,
range 0.0000 for E2B and 0.0208 for E4B, while $D(B \leftarrow R_j)$ varies
across them by 0.177 and 0.188. Companion identity moves delivery loss at
fixed companion difficulty. The constancy is measured at one draw per
topic over 96 topics, so each solo rate carries a standard error near
0.035 and the observed range understates the true spread. That constrains,
and does not remove, the difficulty explanation for the A-versus-R gap,
and it is a reason to report per-reference heterogeneity rather than to
trust a single matched average.

**Default.** 0.10 with the Newcombe condition, and
`EXCESS_NOT_IDENTIFIED` rather than widening after the fact.

---

### V4. The non-vacuity word threshold

**Open.** §9.3 registers 20 words as the threshold below which a pass on a
non-violation constraint is vacuous.

**Why 20.** The topic space asks for sixty to one hundred and twenty word
answers, so an answer below twenty words has abandoned the task rather
than satisfied the constraint. The pilot recorded 13 of 576 and 8 of 576
responses under three words with zero truncations, so the realised rate at
a much stricter threshold is low and non-zero; the rate at 20 words is
unmeasured.

**What would settle it.** The realised distribution of response length in
the v4 calibration cells, per cell type, which check C10 requires before
freeze. The threshold must be fixed before any confirmatory generation and
must not be tuned to a rate.

**Default.** 20 words.

---

### V5. Matched references only, or a difficulty-spanning set

**Open.** §13.2 admits three references matched to $A$ within a caliper.
An alternative is to admit references deliberately spanning a range of
companion solo compliance, so that $D(B \leftarrow g)$ can be read as a
function of companion difficulty and the value at $A$'s difficulty
interpolated.

**Trade-off.** Spanning identifies the difficulty relationship rather than
assuming it away, and with three points it is fragile. Matching is simpler
and registrable, and the pilot evidence that identity moves delivery loss
at fixed difficulty suggests the relationship is not the dominant term.
Spanning would require more than three references and would enlarge the
pairwise matrix quadratically.

**Default.** Matched only, with per-reference heterogeneity reported as
family F2.

---

### V6. Which design the two Qwen replications run

**Open.** Both ended v3 at Gate 2A with `REFERENCE_POOL_MISMATCH` under
the v3 rule, which matched references to $B$. Whether a reference matched
to $A$ within the §13.2 caliper exists for them is unknown, and neither
their solo compliance for $A$ at any $n$ nor for $B$ at any $m$ appears in
the uploaded corpus.

**Registered resolution.** Gate 3 decides it per model, deterministically,
before any confirmatory generation. The full design runs where three
references are admitted; the reduced design of §8.6 runs otherwise, with
`EXCESS_NOT_IDENTIFIED`.

**Why it is listed anyway.** The compute implication is large, 38,400
against 6,144 generations per model, and it interacts with V1.

---

### V7. Whether the v3 topic bank may be reused

**Open.** §6.2 registers 624 newly authored topics, 52 per subject area,
matching the v3 bank structure, and excludes every v3 topic and every B+R
pilot topic. v3 §31 releases its 528 non-sequestered
topics with a canary string when results are reported, and release creates
contamination exposure. Whether that release has occurred is not stated in
the uploaded corpus.

**What would settle it.** Confirmation of the v3 release status. If the
release has not occurred, the v3 confirmatory and sequestered sets become
candidates, at the cost that the design team has seen v3 aggregate results
on the confirmatory set. The pilot consumed the 96 v3 solo-calibration
topics and those are excluded either way.

**Default.** Author 624 new topics. The 96 v3 sequestered topics remain
sequestered.

**Consequence of getting it wrong.** Authoring effort, which is a cost
rather than a validity threat.

---

### V8. Independent human annotator availability

**Open.** §10.3 requires at least one annotator independent of the design
and analysis team. v3 never obtained one; its Gate 1 basis was
`autorater_calibration_approved` with `HUMAN_VALIDATION_UNAVAILABLE`, and
its 120 blinded labels were performed by the study author and are
diagnostic evidence.

**New scale.** v4 needs human evidence for **every** registered outcome
verifier, which is $A$, $B$ and three reference families, not the single
instrument v3 validated. The annotation burden is five instruments rather
than one.

**Default.** Autorater pathway with `HUMAN_VALIDATION_UNAVAILABLE`, the
registered scope sentence attached to every claim, and author-performed
labels never described as independent validation.

---

### V9. A second focal-like outcome constraint

**Open.** The registered design asks whether $A$ is a specifically
damaging **companion**. The complementary question is whether $B$ is a
specifically vulnerable **outcome**, which would require a second
outcome constraint of comparable form and solo compliance, composed with
$A$ and with the references.

**Cost.** One more registered constraint takes the pairwise matrix from
10 unordered pairs to 15, and the confirmatory design from 25 cells to 36,
raising the per-model cost from 38,400 to 55,296 generations at the
registered allocation.

**Default.** Not added. Outcome-side specificity is out of scope and is
never claimed.

---

## What none of these can fix

**The design identifies excess damage relative to a matched companion set,
and nothing stronger.** Semantic identity-specificity would require
holding constant every property of the companion except its meaning, which
no matching rule over this constraint pool achieves. L5 is permanently
withheld.

**Configuration dependence is a property of the phenomenon in this
corpus, not a nuisance to be averaged away.** Eight registered
configurations are reported separately, and a result that changes sign or
magnitude across them is reported as configuration-dependent.

**Load two bounds the construct.** Whether the interaction is
higher-order, which the construct memo's strongest interaction evidence
suggests, cannot be addressed without V2.
