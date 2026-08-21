# DCI-1 v4 revision 3 — adoption and pre-freeze decisions register

Every entry is a dated, explicit pre-freeze decision. Each resolves a value the
preregistration (`user-notes/DCI1_preregistration_v4r3.md`) leaves open, or
records a protocol-level interpretation. Nothing here may change after the
study-wide freeze; the freeze record carries these values and any post-freeze
mismatch fails closed.

## A0 — researcher adoption of DCI-1 v4r3 (2026-08-21)

The researcher authorised, in the session brief of 2026-08-21 and before any
v4r3 generation, that the study proceed as **DCI-1 v4 revision 3**: adopting the
difficulty-spectrum design, expanding the reference-candidate library
prospectively, amending the v4r3 preregistration to specify that expansion,
implementing the infrastructure, executing permitted development and calibration
work, running the registered gates, freezing the study if all preconditions
pass, and running confirmatory generation after a valid freeze.

The same authorisation **explicitly withholds** four things, and none of them is
taken here:

1. any retrospective change to v4r2 or to earlier evidence;
2. any weakening of a gate after observing a failure;
3. any selection of a control from a composed outcome;
4. **any separate researcher approval that the protocol reserves** — in
   particular §10.4's `measurement_basis = autorater_calibration_approved`,
   which Gate 1 cannot pass without and which no agent may write on the
   researcher's behalf.

**Why v4r3 and not v5.** v4r2 §31: *"Before study-wide freeze, any change is a
revision of this document."* v4r2 was never frozen and produced no confirmatory
data — all four replications stand at `REGIME_SCREEN`, and no
`gate1_measurement.json` exists anywhere in the tree, so the §10.6 binding has
never compared. A pre-freeze change is therefore a revision. The v4r1 → v4r2
transition is the precedent, for the same reason. This closes **D0**.

## D — the registered open decisions and their standing

| # | Decision | Standing as of 2026-08-21 |
|---|---|---|
| D0 | Adopt v4r3 | **CLOSED** by A0 |
| D1 | Confirmatory compute budget and allocation | **CLOSED** by A1 below: 384 blocks at M = 8 |
| D2 | Models carried to confirmation | open; four registered, per-model outcomes independent |
| D3 | §12.4's graded clause read as a share | open; the share reading is registered and its coherence argument is in §12.4 |
| D4 | Whether the focal extension is a study-wide escalation | **CLOSED**: registered as an escalation in §7.2 |
| D5 | Whether `delta_difficulty` gets a magnitude threshold of its own | open; direction and the registered SESOI only |
| D6 | Instructed compliance as the primary difficulty coordinate | **CLOSED**: registered in §13.3, raw solo retained as secondary |
| D7 | The class arm's scope | **CLOSED** in part by A2 below |
| D8–D11 | as registered in §33 | open |

## A1 — the allocation is 384 blocks at M = 8, not 408 at M = 4 (2026-08-21)

An earlier v4r3 draft registered 34 confirmatory and 6 sequestered topics per
area so that 408 blocks would meet every §16.2 precision precondition at M = 4.

**That allocation is not executable.** `dci1v4.topics.bank` releases the 528
non-sequestered questions; the other 96 exist to this repository only as
identities and content hashes in `dci1v4.topics.sequestered`, and
`assert_no_materialisation` refuses a released topic that reproduces one. The
two extra confirmatory topics per area could only be drawn from text no v4-era
process can read. The finding came from reading the topic module rather than
the table, and the table had been wrong since it was written.

With the block count fixed at 384, M is the only remaining lever, and under
§16.1's variance model it is the effective one: at φ = 0.37 and ρ = 0.5 the
draw term is 0.0000704 against a topic term of 0.0000415 at M = 4, so the part
M reduces is the larger part. **384 blocks at M = 8** meets every precondition
under both φ settings, restores v4r2's 96-topic sequestered set, and leaves the
topic split byte-identical to v4r2's.

Cost: 144,384 generations per model, 577,536 across four — against the 306,816
the unexecutable row promised. The alternative, authoring at least 24 further
topics under §6.2's four rules and re-cutting the split, is recorded as D1's
open half.

## A2 — the class pool gains two rate lower bounds (2026-08-21)

The pairwise-matrix screen measured one production-class companion and found it
cost B **+0.601** and **+0.632** where A cost +0.086 and +0.228. A
Δ_class computed between companions that far apart in difficulty bounds a class
effect only in the weakest sense.

A count lower bound is hard to make gentle: it demands an absolute number of
qualifying words and so scales with response length. A **rate** lower bound
(`100·S/W ≥ q`) is scale-free and can be tuned to any difficulty, so §13.7 has a
real chance of admitting a class companion matched to A on ι. CP4 and CP7 are
registered for that purpose, and §13.7 now distinguishes an *admitted* class
companion from a *matched* one: `CLASS_ARM_NOT_MATCHED` fires when
|ι_CL − ι_A| > 0.15 and every class statement carries it.

A rate lower bound is classed `production` because its registered satisfaction
route is to produce more of the counted feature. It also admits a budget-like
route — deleting non-conforming words raises the rate — and §7.4 records that
rather than hiding it.

## A3 — the lexical rule's composition order is corrected (2026-08-21)

§10.2's independent reimplementation, written from the registered prose by a
process that read no primary source, disagreed with the primary on the
`one_letter` statistic. v4r2's helper lower-cases the whole response and then
segments; §7.3's prose segments the answer and lower-cases each word for the
suffix and letter tests. §10.2 adjudicates against the prose, so v4r3 composes
in the registered order.

Scope, enumerated executably over the whole Unicode range: **exactly one
character** behaves differently. `İ` (U+0130) lower-cases to `i` followed by
U+0307 COMBINING DOT ABOVE, which is not alphabetic, so folding first splits the
word — `İstanbul` becomes two words of one and seven letters, and B at m = 7
would pass an answer containing an eight-letter word.

Realised frequency of U+0130 in the 285,936 rows every v4-era process has
generated: **zero**. No measured quantity moves and no historical comparison is
broken. The correction is prospective; the boundary suites carry a frozen case
for it; §24 reports its realised frequency so a future firing is visible.

**A is deliberately untouched.** §9.2 registers S0 in its own words as
lower-case-then-segment, and A's carried counting function implements exactly
that, so A's construct string, segmentation function and counting function stay
byte-identical to the closed v3 instrument and its §10.2 carry-over survives.
The two rules differ because the two constructs differ: A counts occurrences of
a string; B and the families make claims about words as objects, whose identity
must not depend on case.

## A4 — the candidate library is a grammar with a frozen reserve (2026-08-21)

The expansion the researcher authorised is registered as a *restriction of a
frozen enumeration*, never as authoring after data has been seen. §7.0 declares
nine counted statistics and four predicate forms; every family is a pair of
those; every family carries a round-0 ladder and a frozen reserve that is a
superset of it; §12.6's expansion may admit reserve rungs and nothing else, at
most four per family per round and at most two rounds, by a deterministic rule
that reads ι and severity only.

Because wordings are severity-invariant and §10.2 freezes boundary cases over
the whole declared range before qualification, a reserve rung inherits its
family's wordings and its evidence exactly, so an expansion never admits an
instrument that carries no evidence.

The stopping rule is the §12.6 identification-coverage criterion, whose seven
conditions and their values are registered before any measurement. Failure is
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` at design time, which is a registered
outcome and not a fallback to be avoided.

## A5 — §10.4's judging task is replaced, its thresholds set before judging (2026-08-21)

The researcher authorised, in the session brief of 2026-08-21, a prospective
repair of §10.4 before freeze, preferring a validator that checks whether the
deterministic operationalization faithfully implements the written constraint
over one that forces an LLM to reproduce long exact counts, and naming a larger
output cap as the acceptable smaller alternative. §10.4-R is that repair; C26
records it; the retained §10.4 evidence records why it was needed.

**The deterministic verifier is unchanged and remains the study's scorer.** This
decision touches an instrument used to validate the operationalization, not the
operationalization itself and not any scoring path.

**The thresholds, registered here before any card was judged.** The ordering is
not asserted; the commit introducing §10.4-R and this entry precedes the first
run of the repaired pathway, and the two are separately hashed.

| # | Criterion | Threshold |
|---|---|---|
| 1 | valid deterministic execution | two runs agree on every parsed label |
| 2 | truncation, pooled | ≤ 0.10 |
| 2 | truncation, per instrument group | ≤ 0.20 |
| 3 | parse validity | ≥ 0.95 |
| 4 | specificity on faithful cards | ≥ 0.90 |
| 5 | sensitivity on mutated cards, overall | ≥ 0.80 |
| 5 | sensitivity, per defect kind with ≥ 4 items | ≥ 0.50 |
| 6 | practically indistinguishable, for the cost tie-break | ≤ 0.05 on both |

**Why criterion 5 exists and why it is per-kind.** A validator handed a correct
derivation and asked whether it is correct can score perfectly by always
agreeing. The planted-defect arm is what makes the procedure informative, and
the per-kind floor is what stops a validator that is blind to one whole class of
defect from passing on the strength of the others. Under §10.4's design such a
validator would have scored well on criterion 4.

**What this decision does not do.** It does not approve the measurement basis.
`measurement_basis = autorater_calibration_approved` may be written only after
criteria 1–5 pass on the development half **and** once on the untouched
calibration half, and it is written under the researcher's explicit
authorisation recorded in the approval artifact, never because the study needs
to continue.

This closes no registered §33 decision. It is an amendment to an instrument,
registered as C26 and as §10.4-R, and the open decisions D2, D3, D5 and D8–D14
stand exactly as they did.

---

## A6. The candidate library is extended (amendment R3, 2026-08-21)

**Decision.** Adopt §7.0-R3: six added counted statistics, six added feature
groups, a fifth predicate form (exact count, $S = q$), and ten added families —
`RF9`–`RF12` and `CR9`–`CR12` as budget references, `CX1`–`CX2` as exact-count
class controls. Registered as C27.

**Authority.** The researcher's session brief of 2026-08-21, which directs the
prospective expansion of the reference-candidate population so that the
registered difficulty coordinate has adequate support around $A$, and which
states the target region and the prohibition in the same breath: *do not widen
calipers or change the difficulty coordinate because support fails*.

**What the decision rests on.** The natural distribution of every candidate
numerator on the §12.2 screen's unconstrained rows — 24 per model, the
registered chance quantity — and nothing else. No solo compliance of any added
family existed when this was registered, on any model.

**The rule this decision refused to change.** §13.7 keeps every production
family out of every reference slot. The brief asks for constructive obligations
to be prioritised, and the strongest of them — an exact count of a marker word,
which is $A$'s own predicate — is a production form. Admitting it as a
*reference* would have made $\Delta_R$ a contrast across two constraint classes
and $\Delta_{class}$ a contrast against a set that already contained its own
class. So the constructive obligations are admitted to the **class arm**, where
§7.4 already puts production forms, and the four added *reference* families are
budgets over common numerators. The brief's aim is met in the arm the protocol
registers for it; the admission rule is not weakened because coverage failed.

**What would falsify the reasoning.** If the four added budget families turn
out to sit below the eligibility floor like the round-0 pool, the diagnosis
that "the numerators were too rare" was wrong, and the honest reading is that
these models do not respond to *any* budget with graded compliance.
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` then stands and §8.6's no-spectrum design
runs. That outcome is registered and is not a fallback to be avoided.


---

## A7. The semantic validator becomes a microcase audit (amendment R2, 2026-08-21)

**Decision.** Adopt §10.4-R2. Registered as C28, before the tool was run and
before any microcase was judged.

**Authority.** The researcher's session brief of 2026-08-21, which directs a
prospective amendment R2 registered before any R2 validation outcome is
collected, names the microcase design, and states the stopping rule: *if the
validator still cannot satisfy the registered semantic-validation criteria on
tiny discriminating cases, stop the LLM-validator pathway rather than
iteratively prompt-tuning it.*

**Thresholds.** §10.4-R's, carried unchanged. Criterion 6, repeatability at
0.95, is added rather than substituted, so R2 is strictly harder to pass than
the pathway it replaces on every axis the two share.

**What this decision does not do.** It does not approve the measurement basis.
`measurement_basis = autorater_calibration_approved` may be written only after
the criteria pass on the development half **and** once on the untouched
calibration half, and only under the researcher's explicit authorisation
recorded in the approval artifact — never because the study needs to continue.

**What would falsify the reasoning.** If R2 fails on truncation again at a cap
of 8,192 with an answer of fourteen words and a one-word reply, then the length
of the reasoning chain was not the binding constraint either, and the honest
reading is that this judge at this scale cannot be made into a semantic
validator by changing the task. §10.3's human audit is then the only registered
route left, and `HUMAN_VALIDATION_UNAVAILABLE` is a standing condition rather
than a temporary one.

## A8. §10.4-R2 failed, and Gate 1 is blocked on §10.3 alone (2026-08-21)

**Outcome.** The R2 microcase audit ran its development half at the registered
`mc-medium` configuration and returned **FAIL** on one registered criterion.
Recorded in `dci1/reports/dci1v4r3/section_10_4R2_outcome.json`, bound to the
case-set hash `14152535`, the split hash `e3b8fa1e`, the config hash
`eb9da523` and the canonical verifier hash `41edc84c`.

| # | Criterion | Threshold | Observed | |
|---|---|---|---|---|
| 2 | truncation, pooled / worst group | ≤ 0.10 / ≤ 0.20 | 0.0119 / 0.0294 | pass |
| 3 | parse validity | ≥ 0.95 | 0.9881 | pass |
| 4 | specificity | ≥ 0.90 | 0.9125 | pass |
| 5 | sensitivity, overall | ≥ 0.80 | 0.8140 | pass |
| 5 | sensitivity, per defect kind | ≥ 0.50 | `denominator_swap` 0.231 | **fail** |
| 6 | repeatability | ≥ 0.95 | not measured | — |

R1's diagnosis is vindicated on its own terms and the pathway still stops.
Removing the reasoning chain fixed what it was meant to fix — truncation fell
from 0.3125 to 0.0119 and parse validity rose from 0.6875 to 0.9881 — and the
validator then failed on a different axis.

**Why criterion 6 was not measured and the calibration half was not run.**
Criterion 6 is conjunctive with 2–5, so a second replicate cannot turn this
half's FAIL into a PASS; §10.4-R2 says the calibration half is not run until the
development half passes. Neither omission is a discretionary shortcut and
neither changes the outcome.

**Why `mc-high` and `mc-low` were not run.** They are registered contingencies
on §10.4's reasoning-effort axis, and they are not matched to this failure.
Seven of the ten items deciding `denominator_swap` have answers with no words
at all — `'   '`, `';;;'`, `',,,'` — so their verdict turns on §7.3's
wordless-rate rule, which the instruction-only arm deliberately withholds;
§10.4-R2 registers that withholding in terms, saying that judging a convention
on the wording alone "would score the validator for failing to guess a
convention". More reasoning cannot supply a convention the prompt does not
state. The same cases in the conventions arm, which does state it, agree 9 of
11. Running a contingency after seeing the failure, aimed at a failure mode it
does not address, is seeking a better draw. The contingencies remain the
researcher's to invoke.

**An implementation note that does not change the verdict.** §10.4-R2 defines
sensitivity as agreement on cases the verifier records as *not satisfied*. The
overall figure is computed that way; the per-kind figure in
`tools/gate1_microcase_v4r3.py` is computed over every parsed discriminating
case in the deciding arm, satisfied ones included. Both readings are recorded
in the outcome artifact. `denominator_swap` fails the floor under both — 0.231
implemented, 0.200 as worded — and no other kind fails either. The run is left
exactly as recorded; the computation should be corrected before any future
R2-style run.

**Consequence, registered in advance.** §10.4-R2: the LLM-validator pathway
stops. §10.3's human semantic audit is the only remaining registered route to a
measurement basis. Gate 1 refuses with `MEASUREMENT_EVIDENCE_INSUFFICIENT` and
`measurement_basis = human_validation_unavailable`, and the refusal is logged
against all four replications at commit `9a3c058`.

**The 25 human annotations are not that route.** They are recorded as
**human semantic evidence** and explicitly not as registered independent human
validation. They fail §10.3 on four separate grounds — the annotator is the
researcher, the unit is a microcase rather than a natural response, one packet
of 25 is not min(150, N_c) per verifier class, and the one-sided 95% Wilson
upper bound on disagreement is 0.2152 against 0.10, a bound 25 items cannot
reach even at zero disagreements. They remain useful: 23/25, no UNSURE, over
eight of the ten families §7.0-R3 added.

**This decision approves nothing.** No measurement basis is written, no freeze
occurs and no confirmatory generation begins.
