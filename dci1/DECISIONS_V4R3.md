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
upper bound on disagreement is 0.2152 against 0.10. At 25 items that bound
clears 0.10 only at zero disagreements — `wilson_upper(0, 25) = 0.0977` against
`0.1013` at 24, which is why the packet was 25 — so it is the two disagreements
that fail the criterion, not the sample size. They remain useful: 23/25, no
UNSURE, over eight of the ten families §7.0-R3 added.

**This decision approves nothing.** No measurement basis is written, no freeze
occurs and no confirmatory generation begins.

## A9. A §10.3-shaped audit the author can run, and what it can and cannot be (2026-08-21)

**Decision.** Build the §10.3 audit workflow and run it, on the researcher's
own labels, with its standing fixed in advance as
`author_performed_human_validation`. `src/dci1v4r3/stages/human_audit.py` holds
the rule; `tools/v4r3_human_audit.py` is the workflow.

**Standing, decided before the first item is drawn.** §10.3 requires an
annotator independent of the design and analysis team, and says in terms that
author-performed labels are never described as independent validation. This
audit therefore **cannot** write `measurement_basis = human_validated` however
well it scores, and the module offers no way to write one: `agreement_report`
carries `satisfies_section_10_3: false` unconditionally. What it can do is
answer, for the first time on natural responses across the whole R3 instrument
population, whether a person reads these instructions the way the verifier
scores them — which is the question §10.2 cannot reach and §10.4-R2 failed to.

**The registered rule, reconstructed.** Verifier classes `("pass", "fail")`;
the fail class split by whether the realised margin is exactly one; size
`min(150, N_c)` per class; stratified per instrument; the one-sided 95% Wilson
upper bound on disagreement at most 0.10 in each; natural responses; a
tool-assisted protocol in which the annotator marks and the interface tallies
*their own marks*, with no automatic detection, highlighting, counting or
normalisation, and no arm, model label, companion, verdict or other annotator's
work visible. Every constant is imported from `dci1v4r3.protocol.constants` and
the estimator is `dci1v4.analysis.intervals.wilson_upper_bound`, the certified
one §10.3 names. Nothing is restated and nothing is re-derived.

**Six choices §10.3 leaves open, fixed prospectively and recorded in the plan.**

1. *Allocation across instruments* — seeded round-robin, one item per
   instrument per pass. Every instrument contributes before any contributes
   twice, and the draw cannot be steered.
2. *The fail quota across margin strata* — split evenly, subject to
   availability, so both required bounds are reachable by construction. The
   class total stays at 150; this is stratification, not inflation.
3. *"Realised margin" beyond the exact-count rule* — the smallest change in
   the numerator that flips the verdict. Reduces to `|S − q|` on every count
   form; undefined, hence `margin_larger`, where no numerator change can flip
   it, which is a wordless answer under a rate predicate.
4. *What counts as a natural response* — a verdict on a constraint the prompt
   **stated**, on a load-0 or load-1 row. Chance verdicts are excluded because
   the model was never asked. Load 2 never enters, so no composed cell is read.
5. *UNSURE* — offered, and counted **as a disagreement**, which is the
   direction that cannot manufacture a pass. The excluding-UNSURE figure is
   reported beside it and is never the criterion.
6. *The reading of the sample size* — `per_class`, `min(150, N_c)` per verifier
   class stratified across instruments, because §10.3's criterion sentence says
   "in each verifier class" and evaluates three bounds. That is **300 items in
   12 batches of 25**. The `per_instrument` reading, which `gate1_readiness_v4.py`
   assumed, is available behind a flag and is **28,801 items** on the current
   tree. The reading is recorded in the plan artifact.

**Realised plan.** Pool 30,144 stated verdicts; population 13,658 pass / 2,594
fail-margin-one / 13,892 fail-margin-larger; quota 150 / 75 / 75. The 300 items
span **212 distinct instruments**, all four models (86 / 76 / 70 / 68) and all
six predicate forms — 130 count budgets, 99 rate budgets, 30 exact counts, 19
count lower bounds, 16 rate lower bounds, 6 focal. All three bounds are
reachable at zero disagreements. Frozen at plan hash `08a9cbbf` before any item
was shown; each batch additionally carries its own membership hash, which is a
pure function of the drawn rows and so is reproducible from the sample alone.

**What the workflow refuses.** To re-plan once any label exists; to show a batch
whose membership hash has moved; to seal an incomplete batch; to accept a row
for a sealed batch; to print agreement before every batch is sealed, unless
`--reveal-early` is passed deliberately. `cmd_review` never opens the answer
key, which a test asserts by walking the call graph rather than by comment.

## A10. The verifier gets audited by reading its derivations, not by re-labelling (2026-08-21)

**Decision.** Build the operationalization-card audit and treat it as the
primary route to trusting the deterministic verifier.
`src/dci1v4r3/stages/verifier_audit.py` and `tools/v4r3_verifier_audit.py`.

**Why, and what it replaces.** A9's §10.3 workflow asks a person to label a
hundred-word response blind, which means counting qualifying words by hand.
That is the same arithmetic task §10.4 handed a judge, and §10.4-R's own
diagnosis of why it failed applies to a human too: the counting swamps the
judgment. §10.3's blind unit is the right unit for *measuring agreement*; it is
the wrong unit for *finding defects*, because 280 correct verdicts carry no
information about whether the verifier is right and only the disagreements do.

So the audit asks a different question — **did this program count the right
things?** — over §10.4-R's registered unit, the operationalization card, with
the arithmetic shown rather than requested. R1 built that card for an LLM. A
person is the reader it was always better suited to.

**The decomposition cannot drift from the verifier.** Each card lists the
tokens the numerator matched, and a token is matched when *the registered
counting function itself*, given that token alone, returns one. Nothing
re-implements a predicate. `decompose` then checks that the per-unit probes sum
to the whole-text count and declares itself `faithful: false` when they do not,
so a card either shows a decomposition the verifier agrees with or says it
cannot. A test reaches that branch deliberately, with a pair-counting statistic
that no per-unit probe can reproduce.

**Selection.** Coverage-greedy per family over a seeded candidate cap: 128
cards over all 32 families, covering all 32 numerator-and-form pairs, the eight
phenomena the responses actually exhibit, both margin classes, and five of the
six registered misreadings. The sixth, `vacuity_ignored`, discriminates on no
natural response at all — which is the defect-sensitivity finding reappearing,
and the reason it must be audited on designed cases rather than natural ones.
Membership does not change when every recorded verdict is flipped, which a test
asserts.

**Standing, and the boundary that matters.** This is a **verifier audit and not
§10.3**. The verdict is visible before the assessment, so nothing it produces
is a human-verifier agreement rate; a test forbids the tool from emitting a
field called `agreement`, a Wilson bound, or a measurement basis, because a
reader who finds `"agreement": 0.94` in an artifact will quote it whatever the
prose beside it says. Its output is a **defect worklist** — cards where a
person read the derivation and named the component that counted wrongly.

**What a finding costs, stated up front.** Changing a verifier moves the
canonical hash that every §10.2 artifact, every stage record and all 30,144
stored verdicts are bound to. A confirmed defect is a `CHANGES_SCIENTIFIC.md`
entry, a re-run of §10.2's evidence, and a re-derivation of everything measured
under the old hash. That is the right price and it is the reason to find
defects now, before Gate 5, rather than after.

**A9 is not withdrawn, and the card audit does not spoil it.** The blinded
§10.3 plan stays frozen at `08a9cbbf` and unspent. A card shows the verdict, so
a response seen here can no longer be labelled blind; `build` therefore excludes
the 291 rows the §10.3 plan reserved before drawing. The first build overlapped
on five of them and was rebuilt; the current card set at `ad0a2a55` overlaps on
none. `--ignore-blind-sample` exists, says what it costs, and is off.

## A11. The card audit found no defect, and found what §7.3 costs (2026-08-21)

**Outcome.** 128 of 128 operationalization cards assessed **correct**; zero
wrong, zero unsure. Bound to card set `ad0a2a55` and canonical verifier hash
`41edc84c`. `reports/dci1v4r3/verifier_audit/report_Bryan.json`.

**What that does and does not establish.** Measured rather than asserted: on
the 128 cards, `numerator_swap` would have flipped 53 verdicts and visibly
changed the matched-token list on all 53; `denominator_swap` 33, with the
arithmetic line visibly different on all 33; `inequality_flip` 114 and
`off_by_one` 37, both visible in the printed threshold and direction beside the
verdict; `segmentation_drift` 2. So all five misreadings that discriminate on
natural responses were on the displayed surface and were not objected to.
`vacuity_ignored` discriminates on **no** natural response, which is the
defect-sensitivity finding reappearing and the reason it can only be audited on
designed cases.

**The structural limit, stated plainly.** 1,741 tokens were listed as matched
against 18,130 units in those responses. A defect that *includes* a wrong token
is visible in the list; one that silently *omits* a qualifying token is not,
because absence in a hundred-word answer is exactly the counting task the card
format exists to avoid. The audit is strong against counting the wrong kind of
thing and weak against counting too few of the right kind.

**What it did surface.** Fourteen cards displayed bare `t` and `s` tokens
inside matched lists — `vc-072` shows five of them in a `t_initial` count — and
all fourteen were marked correct. That is §7.3 working as registered: *a word
is a maximal run of alphabetic characters, Unicode general category L*, and an
apostrophe is not category L, so `don't` is `don` and `t`, `It's` is `It` and
`s`, and `well-known` is two words. **Not a defect.** The verifier implements
the registered prose exactly, and §10.2's independent reimplementation agrees.

**But its size was unknown, so it was measured.**
`tools/v4r3_lexical_footprint.py`, read-only over the same 30,109 responses,
against a *reader's word* in which one internal apostrophe or hyphen does not
break a word — deliberately not one of §10.4-R2's six defects, because it is a
different rule rather than a misreading of this one:

| | |
|---|---|
| rate denominator inflated by | **1.67%** (42,146 of 2,524,851 words) |
| verdicts that change | **230 of 20,928 = 1.10%**, band *detectable* |
| worst numerator | `one_letter` **7.41%** |
| worst families | `CR3` **7.94%** (shortlisted on 2 models), `RF3` **6.94%** (on 3) |
| what it splits on | `'` 22,098 · `-` 15,392 · `’` 3,920 · `—` 283 |

Detectable, below §11.8's smallest effect of interest, and concentrated in the
one-letter families — which are the ones a fragment directly creates, since
`don`+`t` manufactures a one-letter word that no reader sees. Two of those
families are on live reference shortlists, so this is a live construct
question and not an archival one.

**Standing.** §10.5's third question — *does the deterministic rule validly
operationalise the intended construct?* — which the preregistration bounds by
§9.3 and §24 and states is **not resolved by this study**. Nothing is changed
and nothing is proposed. What changes is that the registered choice now has a
measured price attached, and a choice whose footprint is unknown is a choice
nobody has actually made.

**A defect in the diagnostic, caught by its own test.** The first
implementation used a word-character class minus digits and underscore, which
admits Unicode category No, so `H₂O` was one token where §7.3 gives `H` and
`O`, and the difference would have been charged to the apostrophe rule.
`test_the_two_readings_agree_where_no_joiner_occurs` caught it on §10.2's own
boundary corpus. Rebuilt on `str.isalpha`, the same predicate the registered
rule uses. The corrected run reproduces every figure above unchanged —
subscripts are rare in real answers — so the numbers stood, but they now stand
on something correct.
