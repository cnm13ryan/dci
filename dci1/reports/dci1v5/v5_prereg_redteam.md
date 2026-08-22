# DCI-1 v5 preregistration — red-team audit

An adversarial reading of [`DCI1_preregistration_v5.md`](../../../user-notes/DCI1_preregistration_v5.md),
written against the design rather than for it. Each finding says what could go
wrong, what the document currently says, and whether it is **resolved**,
**registered as a limitation**, or **unresolved and blocking**.

**An unresolved item blocks the freeze.** v5 §18 stage 12
(`PREFREEZE_AUDIT`) executes §33's fifteen-item checklist and returns
`PREFREEZE_AUDIT_FAILURE` on any unresolved entry, and §34 requires every open
decision closed before stage 1 can pass. This document is the standing finding
register that checklist reports against.

**Five findings are unresolved.** They are R1, R5, R11, R14 and R16, and none
of them is a bug: each is a scientific degree of freedom that a researcher has
to close. Four of the five are registered as open decisions D18, D16, D17 and
D6; R5's residual half is not closeable by a rule. **v5 is not frozen and must
not be described as registered until they are.**

---

## A. Identification and inference

### R1 — the same-form control may make L3c near-automatic, and L3c is a memo verdict — **UNRESOLVED**

This is the sharpest objection to v5 and it is the mirror image of its central
repair.

$\Delta_R = D(B \leftarrow A) - \frac{1}{3}\sum_j D(B \leftarrow R_j)$ with
$R_j$ drawn from Tier 1: exact counts of a marker word, differing from $A$ only
in *which* marker and *how many*. If the mechanism by which $A$ damages $B$ is
a property of the **form** — a model asked for an exact count of a token stuffs
that token, shortens the answer, and abandons the word-length budget — then
every Tier-1 control reproduces it, $\frac{1}{3}\sum_j D(B \leftarrow R_j)
\approx D(B \leftarrow A)$, and $\Delta_R \approx 0$.

$\Delta_R \approx 0$ with a tight interval is **L3c**, and
`dci-construct-pass2.md` §G row 1 says an upper bound below 0.10 *"supports H2
and refutes the pairwise framing entirely, redirecting the programme to a
load-and-capacity account."* So a design choice made for methodological reasons
would be pushing the study toward one of the memo's two substantive verdicts.

**The v4r4 evidence says this is likely rather than hypothetical.**
`Δ_class` on `qwen3-4b`, whose class companion `CX1:4` is exactly a Tier-1
control, was $+0.0114$ $[-0.011, +0.033]$ and $+0.0384$ $[+0.009, +0.068]$ —
essentially zero in one configuration and a fifth of the generic-load threshold
in the other. And v4r4's follow-up found $A$ failing by **overshoot** and
`CX1` failing the same way, which is the mechanism this finding describes.

**What the document does about it.** §5, §7.5 and §29 register the narrowing
explicitly; `REFERENCE_POOL_SAME_FORM` attaches to every L3 statement with a
fixed sentence saying the excess is relative to companions sharing $A$'s form;
and §13.9's near-form arm with §17.6's `LOCAL_TIER_DISAGREE` table exists
precisely so that a $\Delta_R \approx 0$ / $\Delta_{\text{near}} > 0.10$ pattern
is **not** emitted as L3c but as a registered disagreement.

**Why it is still unresolved.** The near-form arm is nine cells and §34 D1
lists dropping it as a compute option. **If D1 drops the near-form arm, R1
becomes an unmitigated bias toward L3c**, and the document should not permit
that combination silently. §17.6 now requires an L3c emitted without the arm to
carry a fixed sentence saying the absence was tested only against companions
sharing $A$'s form, and **§34 D18** records whether the arm should instead be a
precondition of emitting L3c at all. The finding stays **unresolved** because
D18 is open and because a fixed sentence is a weaker remedy than a gate.

### R2 — the memo's 0.25 threshold is applied to a redefined quantity — registered, arguably inconsistent

§11.9 refuses to transfer the memo's 0.25 to $\delta_{\text{diff}}$ on the
ground that it *"differences an observed loss against a fitted prediction, and
nothing in that document contemplated it"*. But v5's $\Delta_R$ is also not the
quantity the memo contemplated: the memo's $R$ was a companion matched on
difficulty in a v2/v3 vocabulary, and v5's is matched on difficulty **and**
form, in a pool the memo's author never saw.

The document keeps 0.10 and 0.25 unchanged and says the thresholds *"predate
every observation in this constraint vocabulary"*, which is true and is not
quite the point. **Verdict: registered but not resolved by argument.** The
consistent alternatives are to transfer neither, or to state that $\Delta_R$'s
identity is the *shape* of the contrast rather than the reference pool.
**Registered as §34 D15**, whose standing proposal takes the second: the memo
defined the thresholds for a focal loss under $A$ against the same loss under a
matched companion, and that shape is unchanged. It is recorded as contestable
rather than argued away.

### R3 — an eight-rung marker ladder is marginal against the coverage span requirement — resolved by measurement, with the ladder widened

**The first draft of this finding claimed the spectrum was unbuildable from
Tier-1 families, and the measurement refutes it.** §13.12 requires strict
straddling — a rung strictly below $\iota_A$ and one strictly above, each
*nearest* $\iota_A \mp 0.20$ — not rungs *at* the offsets. Recomputed from the
v4r4 pre-screen difficulty tables, `CX1` over *thus* **straddles $\iota_A$ on
all four replications**:

| model | $\iota_A$ | eligible rungs | below | above | eligible span |
|---|---:|---:|---:|---:|---:|
| `gemma-3n-e2b-it` | 0.556 | 8 | 3 | 5 | **0.375** |
| `gemma-3n-e4b-it` | 0.667 | 7 | 3 | 3 | **0.375** |
| `qwen3-4b` | 0.750 | 7 | 5 | 1 | 0.417 |
| `qwen3-4b-instruct-2507` | 0.625 | 5 | 1 | 4 | **0.375** |

**What survives the correction is a real and smaller finding.** §12.6's
coverage condition C4 requires a straddling family to carry at least three
eligible rungs spanning at least **0.40** in $\iota$, and an eight-rung marker
ladder delivered **0.375 on three of the four** — short by about 0.03. §12.6's
expansion is the registered mechanism for reaching it, and a reserve of
$1 \dots 10$ would leave it two rungs to work with. **§7.10 now registers the
Tier-1 reserve at $1 \dots 12$** on exactly this measurement, and records that
higher $q$ is harder so the reserve extends the span downward, which is the
deficient side.

**A second, genuine tension the first draft found, now removed.** §7.4's slot
table read *"spectrum: tiers 1, 2, 3"* while §13.12 draws both spectrum rungs
from the **same family** as the core reference, which fixes the tier. Those two
rules could not both be right. §7.4 now reads *"the tier of its own core
family, because §13.12 draws both rungs from that same family"*, and
`reference_design_spec.json` carries the same correction.

**Residual risk, registered rather than resolved.** `CX2` — the Tier-2
semicolon family — **fails to straddle** $\iota_A$ on `gemma-3n-e4b-it` at
pre-screen: seven eligible rungs, all below. A Tier-2 family can hold a core
reference slot under §7.4, and if it does and cannot straddle, §13.12 drops it
and the next qualifying family takes the slot — the mechanism v4r4 already had.
It is the reason §13.15 requires five qualifying families rather than three.

### R4 — $\text{Ord}_\Lambda$ is linearly dependent inside a maximum-modulus family — registered

$\text{Ord}_\Lambda = \text{Ord}_B - \text{Ord}_A$ exactly. A studentised
maximum-modulus interval over a family containing a member that is a linear
combination of two others is valid but conservative in an uninteresting way:
the third member can never be the maximum unless it is more extreme than both
its components in standardised units.

§11.7 declares the dependence. **Verdict: registered, not a defect.** The
alternative — a family of two with $\text{Ord}_\Lambda$ reported marginally —
would buy a narrower interval and would hide the quantity a reader of v4r4's
sign reversal wants.

### R5 — $\kappa^{B}$ is measured under $B$, so it is not pre-treatment for the pair — **UNRESOLVED**

§13.6's defence is that $\kappa^{B}_R$ reads $X_R$ in the $B$-solo cell, never
$X_B$ in a composed cell, so it cannot select on $\Delta_R$'s outcome; and that
the residual-bias direction is conservative, because a reference $B$ makes
trivial would have shown a small $D(B \leftarrow R_j)$ and therefore a **large**
$\Delta_R$.

Both halves are right. What neither addresses: $\kappa^{B}$ is a function of
$B$'s realised response distribution at $m^*$ on the confirmatory model, so the
reference set is a function of how that model writes under $B$. Two things
follow that the document does not currently state.

1. **The reference set is not exchangeable across models**, which §29 states,
   and therefore neither is $\Delta_R$'s meaning. A cross-model comparison of
   $\Delta_R$ compares two differently-constructed counterfactuals.
2. **$\kappa^{B}$ is estimated on the calibration split and used at $m^*$ on
   the confirmatory blocks.** Nothing registers what happens if the realised
   confirmatory $\kappa^{B}$ differs materially from the calibration value.
   §23's projection audit reports it and no rule reads it.

**Closed on the second point, open on the first.** §13.8 now registers a
realised-drift qualifier: when a core reference's confirmatory
$\kappa^{B}_{R_j}$ differs from its calibration value by more than **0.15**, or
its realised $\hat p_{R_j}$ falls outside §13.6's band, every L3 statement
carries `INTERACTION_ESTIMATE_DRIFTED` naming the reference, both values and
the realised composed rate. It is an identification status and not a terminal
one, because the reference was admitted under the registered rule on the
registered data.

**Point 1 remains unresolved and is not closeable by a rule.** The reference
set is a function of how each model writes under $B$ at its own $m^*$, so
$\Delta_R$ on two models is two differently-constructed counterfactuals. §29
states it; nothing repairs it; and it is a reason no cross-model scalar carries
a claim.

### R6 — the projection assumes $\iota$ transfers, and it is only tested where it barely matters — registered

$\hat p_R = \kappa^{B}_R + \iota_R(1 - \kappa^{B}_R)$ assumes the *share of
achievable improvement* a stated constraint delivers is the same under $B$'s
response distribution as under the unconstrained one. The development data show
the projection's absolute error reaching **0.313** on a low-$\kappa^{B}$ cell,
against a median of 0.067.

§13.6 notes that as $\kappa^{B} \to 1$ the projection $\to 1$ whatever $\iota$
is, so it is least sensitive exactly where it binds. **That is correct and it
means the transfer assumption is essentially untested in the region where the
projection is used as a floor** — the lower bound of 0.10, which no v4r4
candidate came near. **Verdict: registered.** The lower bound is the weaker
half of §13.6 and §23's audit is what will say so.

---

## B. Adaptivity and selection

### R7 — no rule uses a v5 composed outcome to select a control — resolved

§13.11's calibration schema carries no composed field, is **closed** against
unknown fields, and additionally asserts that rows supplying `kappa_under_b`
are load-one cells whose single present constraint is $B$. §19 test 2 requires
all three refusals. §13.14 forbids Gate 4 from replacing a companion, widening
a threshold, or admitting a rung, and §19 test 4 requires the substitution path
**not to exist**.

### R8 — the frozen backups could become a substitution mechanism — resolved

§13.15 freezes two qualifying families beyond the three used and §13.14 states
in terms that they are never substituted after Gate 4, with the argument:
substituting a companion after observing a composed rate is outcome-based
selection with an extra step. §19 test 4 requires the code path to be absent
rather than unused. **The residual risk is human, not code**: a future revision
could reach for them, and §32's amendment discipline is the only thing stopping
it.

### R9 — the lexicographic order could be doing work it appears to do — resolved, with a clarification the document should make

A conjunction's truth value is order-independent, so §13.1's lexicographic
order decides **which rejection reason is recorded**, not which candidates
pass. A reader could mistake the order for a priority that changes outcomes.
**Closed.** §13.1 now says so: *the order decides which reason is recorded and
not which candidates pass*, with the argument that a rejection reason varying
with implementation detail is not evidence.

### R10 — no weighted composite score exists — resolved

§13.1 declines one and §34 D5 records the alternative. The stated reason —
four models cannot fix weights that generalise to an unseen candidate family —
is the right one.

### R11 — both calibration splits are development data, and Calibration-A is not naive — **UNRESOLVED**

§6.2 states it: 29 rungs per model of v4r4's library were measured on
Calibration-A's topics and the researcher has seen those measurements. §12.7
adds a second asymmetry: **Calibration-A screens and Calibration-B confirms**,
so they are not interchangeable.

The consequence the document does not draw: §13.7's stability rule is a test of
*measurement* stability, and it is being asked to protect against a
*selection* effect. It does that only if the two splits are exchangeable, and
under §12.7 they are not. The rule remains valuable — a candidate admissible on
both splits at 96 topics each is better evidenced than one admissible once at
96 — but "independent" overstates it.

**Registered as §34 D16.** The standing proposal restricts Calibration-B, and
§12.7 states the asymmetry in terms — *A screens and B confirms* — rather than
presenting the two as interchangeable. Measuring both in full costs about
35,000 further generations per replication and is purely a compute question.
The finding stays **unresolved** because D16 is open, not because the document
is silent.

---

## C. Specification completeness

### R12 — every threshold is a literal — resolved

Every value in §11.9, §12.6, §13.4, §13.6, §13.7, §13.8, §13.15 and §16.2 is a
number in the text with a derivation beside it, and
`reference_design_spec.json` carries the machine-readable copy. §13.1 states
that the preregistration governs where the two disagree.

### R13 — the 0.90 interaction ceiling sits inside a gap observed on twenty points — registered

The four failing projections were 0.9947, 0.9947, 0.9388, 0.9388 and the
highest passing one was 0.8836. Any threshold in $(0.8836,\ 0.9388)$ separates
them perfectly on that sample. §13.6 derives 0.90 from Gate 4's band and a 0.05
error allowance and records the coincidence rather than using it; §34 D7
records it as a decision. **Verdict: registered.** A reader who thinks the
derivation is post-hoc rationalisation has the sensitivity sweep in
`d4_interaction_projection.json` to argue from: 0.85 costs two false alarms,
0.95 misses two failures.

### R14 — the focal grid extension trades construct strength for band membership — **UNRESOLVED**

v5 extends $B$'s grid to $m \in \{7,\dots,14\}$ with an extension to
$\{15,16\}$, and §12.3 selects the rung whose solo compliance is nearest 0.80.
On `qwen3-4b` that curve reaches 0.742 only at $m = 12$, so v5 would very
likely select $m^* = 13$ — *every word in the answer must have at most 13
letters*.

Compliance is a behavioural quantity and 0.80 compliance at $m = 13$ is a real
constraint on that model's writing. But as a **construct**, "at most 13 letters"
is close to a null instruction in ordinary English, and the focal band is
defined on compliance rather than on construct strength. v4r4 already had this
at $m = 12$ and v5 makes it more likely by extending further.

**Registered as §34 D17.** The standing proposal registers no construct floor
and instead reports the realised $m^*$, $B$'s chance compliance at $m^*$ and
$B$'s whole curve, with §29 stating that a high $m^*$ makes $B$ a weak
instrument on that model. The finding stays **unresolved** because D17 is open.

### R15 — the realistic-witness rule is narrow, and its original justification was wrong — resolved, with a correction

An earlier draft justified the rule with `CL7:80`, *at least 80 words must
contain letter a*, claiming it unreachable under $B$. **The signed v4r4 records
contradict that**: on `gemma-3n-e4b-it` its composed compliance was 0.609 and
0.662. The rule's correct justification is `CL7`'s reserve reaching 140, where
*at least 130 words must contain the letter a* cannot be met by any answer of
at most 120 words. §7.7 now says this and says the rule is not the main
defence. The error is recorded here rather than quietly removed.

### R16 — `REFERENCE_SUPPORT_NOT_IDENTIFIED` is an identification status, not terminal — **UNRESOLVED**

§13.15 makes it non-terminal so that a replication does not discard identified
estimands — $D$, $\Lambda$, the order contrasts, $\Delta_{\text{near}}$,
$\Delta_{\text{broad}}$ — for want of $\Delta_R$. §34 D6 records the
alternative.

**The adversarial reading is that this is exactly how v4r4 ended up with two
confirmed replications and no companion-specific estimand.** Three of four
v4r4 replications ran a design that could not answer the primary question, and
each consumed a full confirmatory budget doing so. A study whose stated purpose
is the counterfactual, that spends its budget on replications which cannot
identify it, has a resource-allocation problem that a status field does not
fix.

**Registered as §34 D6, and half the obvious remedy is deliberately not
taken.** If the status stays non-terminal, an execution-order rule
de-prioritising a replication that carries it would send compute to
replications that can answer the question. The document does **not** register
one, because that ordering would depend on a per-model gate outcome and §6.1's
firewall says a scientific outcome from one replication never changes what
another does. The tension is real and is recorded rather than resolved.

---

## D. Implementation and provenance

### R17 — the presence rule was assumed and not enforced in v4r4 — resolved

v4r3 §9.1 requires every generation to be scored on every registered instance.
v4r4's Gate-2 calibration scored load-one rows on the present instance only, so
$\kappa^{B}$ did not exist in its records and had to be recomputed from raw
responses. §9.1 and §19 now make the rule mandatory at every generative stage
and assert it in qualification and the pilot. **§13.6 is free only if this
holds**, so it is now load-bearing rather than hygienic.

### R18 — v4r4's constants carry stale comments that disagree with the computed values — resolved for v5, recorded for v4r4

`dci1v4r4/verifiers/constraints.py` documents `N_SEVERITIES` as 190 and
`N_DECLARED_SEVERITIES` as 334; the computed values are **254** and **510**.
`protocol/constants.py` comments `N_CONFIRMATORY  # 408` and
`N_SEQUESTERED  # 72` against computed **384** and **96**, and v4r3 §29 says
"72 topics rather than 96" where its own §6.2 table says 96. In every case the
**computed** value is what the code uses and what the records carry, and no
scientific quantity moves. It is a documentation defect and it is recorded
because a reader checking a preregistration against a comment would be
misled. v5's §7.10 states its counts and §19's qualification asserts them
against the computed values.

### R19 — the v4r4 follow-up report quotes two caliper values the code contradicts — recorded

`dci1/reports/dci1v4r4/SCIENTIFIC_FOLLOWUP_EVIDENCE.md` §6 states
`REFERENCE_CALIPER` 0.075 and `REFERENCE_PRESCREEN_CALIPER` 0.10. The registered
values in `dci1v4r4/protocol/constants.py` are **0.10** and **0.15**, and the
machine-readable companion `02_admission_landscape.json` records 0.10 and 0.15.
**The prose is wrong and the machine-readable artifact is right.** No admission
verdict in that package is affected, because every verdict was produced by
calling the registered selection functions rather than by reapplying a quoted
threshold. Recorded here rather than corrected in place, because that report is
a completed read-only package; the correction belongs in a follow-up commit to
that file and is flagged for the researcher.

### R20 — no v4r4 outcome can be presented as a v5 observation — resolved

§14.2's admission guard refuses every v4r4 artifact structurally and in both
directions; §30's ledger classifies every carried item; §18 stage 18 requires
every final-report number to trace to a v5 stage record.

### R21 — the word "validation" — resolved

§30 forbids describing retrospective v4r4 performance as validation, §33 item
15 makes it a text check over v5 artifacts, and the development report's own
header and §9 say it three times.

---

## E. Resource and executability

### R22 — the full design has never been executed, on any revision — registered

v4r4 registered a 47-cell full design and ran none: both survivors ran 8 cells.
v5's full design is 56 cells and 172,032 confirmatory generations per model,
688,128 for four, plus roughly 75,000 pre-confirmatory per replication. **The
apparatus for the full design has been exercised only by v4r4's procedural
pilot at $M = 4$ on twelve topics.** §19 requires the v5 pilot to run the full
56-cell plan, which is the only pre-confirmatory evidence that the arm
machinery works at all.

### R23 — the Tier-1 pool has never been measured — registered

Seven of the eight registered marker families and two of the three Tier-2
families do not exist in any codebase and have no compliance measurement on any
model. Every quantitative expectation about them extrapolates from `CX1` over
*thus*. §13.15's support thresholds — eight families entering calibration, five
qualifying — are sized on an argument and not on a measured attrition rate for
the pool they govern. **If the marker families behave unlike `CX1`, v5's
support requirement is the wrong number and there is no way to know before
Gate 3A.**

### R24 — authoring 96 new questions is a hard prerequisite — registered

§13.7 does not work without Calibration-B. §34 D3 makes it a gate on stage 1.

---

## Summary

| | Finding | Verdict |
|---|---|---|
| R1 | the same-form pool may make L3c near-automatic | **unresolved** |
| R2 | the memo's 0.25 applied to a redefined $\Delta_R$ | registered |
| R3 | an eight-rung marker ladder is marginal against C4's span | resolved; reserve widened to 1…12 |
| R4 | $\text{Ord}_\Lambda$'s linear dependence | registered |
| R5 | $\kappa^{B}$ is measured under $B$; no realised-drift qualifier | **unresolved** |
| R6 | the projection's transfer assumption is untested at the floor | registered |
| R7 | no composed outcome selects a control | resolved |
| R8 | the frozen backups cannot be substituted | resolved |
| R9 | the lexicographic order decides the reason, not the verdict | resolved |
| R10 | no weighted score | resolved |
| R11 | Calibration-A screens and Calibration-B confirms | **unresolved** |
| R12 | every threshold is a literal | resolved |
| R13 | the 0.90 ceiling sits in an observed gap | registered |
| R14 | the focal extension trades construct strength for band membership | **unresolved** |
| R15 | the realistic-witness rule's original justification was wrong | resolved |
| R16 | `REFERENCE_SUPPORT_NOT_IDENTIFIED` is not terminal | **unresolved** |
| R17 | the presence rule is now enforced and load-bearing | resolved |
| R18 | v4r4's stale constant comments | resolved for v5 |
| R19 | the v4r4 follow-up report's two caliper values | recorded |
| R20 | no v4r4 outcome as a v5 observation | resolved |
| R21 | "validation" | resolved |
| R22 | the full design has never been executed | registered |
| R23 | the Tier-1 pool has never been measured | registered |
| R24 | 96 new questions are a prerequisite | registered |

**v5 is not frozen.** Five scientific degrees of freedom remain open. §34
carries nineteen decisions, D0 to D18, five of which came from this audit —
D15, D16, D17, D18 and the reopened D6 — and every one must be closed in the
signed registration manifest before stage 1 can pass. The document says so on its first page
and this register is what the pre-freeze audit reads.
