# DCI-1 v4: unresolved decisions requiring further evidence before execution

**Date:** 19 August 2026 · **Status:** open items of a prospective
registration · **Parent document:** `DCI1_preregistration_v4.md` §35.

Each item states what is undecided, why the uploaded v3 corpus cannot
settle it, what evidence would settle it, the registered default that
applies if no evidence is obtained, and the consequence of the default
being wrong. Every item is closed by recording the decision and its
evidence in the signed registration manifest **before study-wide freeze**.
None may be decided after any v4 confirmatory generation.

Items are ordered by how much of the design turns on them.

---

## U1. The discriminating design's specification is not in the uploaded corpus

**Undecided.** The v3 results report ranks first among remaining blockers
"Run the B+R / B+S discriminating experiment (registered as the natural
next step; not executed)" and describes its purpose as separating
target-specific interference from generic constraint load. No
specification of that design appears in any uploaded file. A search of the
v3 preregistration finds the letter $S$ only as the background set, in the
§1 definition table and in the §2 estimand formula, defined as "any further
constraints held identical across comparison conditions" and recorded as
empty in v3, and as the names $S_0$ to $S_3$ of the scoring rules. v3
registers no surrogate outcome constraint.

**Interpretation taken.** v4 §8 and §11.4 register the design that achieves
the stated purpose: a crossing of the outcome constraint, $A$ or the
surrogate $S$, with the added constraint, $B$ or a reference, giving the
four composed cell types $A+B$, $A+R$, $S+B$, $S+R$, and identifying the
identity-specific component as the difference in differences. In the v3
report's shorthand the two new cell types are the focal constraint and a
reference each composed with a non-target partner.

**Evidence needed.** The source note that defines "B+R / B+S", checked
against §8 and §11.4. If that note specifies different cells, §8, §11, §13
and §14 change together.

**Default.** The crossed design as written.

**Consequence if wrong.** The registered $\iota$ would answer a different
question from the one the programme intended. This is the largest single
risk in the document and the cheapest to remove.

---

## U2. The surrogate target word

**Undecided.** §5 registers $S$ as "use the word *hence* exactly $k$
times". *hence* was chosen because it has five letters, so it sits two
letters inside the focal ceiling at the most restrictive registered focal
severity $m=7$; it contains no b, no doubled letter, no letter a, no
terminal y, no -ing suffix, and needs no capital, so it composes with every
reference family at maximum severity; and it is a discourse connective of
the same grammatical class as *however*.

**Why v3 cannot settle it.** v3 registered no surrogate. Its only relevant
evidence is that *however* produced a topic-alone accidental-compliance
rate of 0.000 in both identified models, measured on a heavily truncated
arm, and solo failure of 0.333 and 0.422 at the selected counts. Nothing in
the corpus bears on any other word.

**Evidence needed.** Pre-screen solo-failure curves across $k$ for two or
three candidate words, plus their topic-alone accidental-compliance rates.
A candidate is usable when its solo curve reaches the $[0.15, 0.50]$
admission band inside the registered grid and its accidental-compliance
rate is near zero.

**Default.** *hence*.

**Consequence if wrong.** `SURROGATE_RANGE_EXHAUSTED` at Gate 2A, which
stops the replication before any confirmatory generation and wastes the
calibration budget.

---

## U3. Whether to change the target word so the focal grid can extend below $m = 7$

**Undecided.** *however* has seven letters, so joint satisfiability of
$A+B$ requires $m \ge 7$ and the focal grid cannot go lower. Both v3
replications that reached selection chose $m^* = 7$, the most restrictive
admissible severity, at focal solo failure 0.188 and 0.240, both below the
0.30 selection centre. The focal constraint therefore operated at a grid
boundary fixed by an unrelated choice, and no harder focal severity exists
for this target word.

**Trade-off.** A shorter target word, four or five letters, would open
$m \in \{5,6\}$ and widen the focal difficulty range, improving the
prospects for matching references on both difficulty and dose. It would
also change the target word's natural base rate, which is the property that
makes an exact-count constraint informative, and it would break the
carry-over of the v3 and v2 target instrument, its forty-case boundary
suite, and the 120 human labels attached to it.

**Evidence needed.** Pre-screen focal curves at $m \in \{5,6\}$ against a
candidate shorter target word, and that word's topic-alone rate.

**Default.** Keep *however*, register the structural floor explicitly, and
report the realised $m^*$ against the grid boundary.

**Consequence if wrong.** The focal constraint stays weaker than the design
intends for models that find it easy, and the reference pool must absorb
the mismatch.

---

## U4. Confirmatory draws per cell, $M$

**Undecided.** §4 registers $M = 8$. The projection in §13 uses a variance
decomposition derived from a single v3 model and order stratum: a block
bootstrap standard error of 0.03901 on 192 blocks and a pseudo-selection
standard deviation reported as a range of 0.036 to 0.039, of which the
distribution mean and fifth percentile imply 0.0359.

**Why the corpus cannot fully settle it.** The upper end of the reported
pseudo-run range implies a block-level variance component of essentially
zero, which is implausible and would make the projection optimistic. The
decomposition is available exactly from the v3 confirmatory caches, which
contain all 36,864 draws per model, and has not been computed here because
those caches are not among the uploaded files.

**Evidence needed.** Recompute $\sigma^2_{\text{block}}$ and
$\sigma^2_{\text{draw}}$ directly from the v3 caches for both identified
models and both order strata, then choose $M$ so the projected simultaneous
half-width for every F1 member is at or below the 0.05 precision
precondition with margin.

**Default.** $M = 8$, which projects a half-width of 0.034 for the swap
effects and 0.048 for the identity-specific effect and costs 33,792
generations per model, below v3's 36,864.

**Consequence if wrong.** `INSUFFICIENT_PRECISION` on one or more F1
members, which withholds equivalence claims while leaving resolved
directions intact.

---

## U5. Calibration draws per cell, $M_{\text{cal}}$

**Undecided.** §4 registers $M_{\text{cal}} = 4$. v3 used one draw per
calibration cell, giving a standard error of about 0.051 for each solo rate
over 96 topics and about 0.072 for a difference, against a caliper of 0.10.
Selection was therefore made at a noise level comparable to the caliper
itself, and a dense ladder amplifies the resulting winner's curse.

**Evidence needed.** The calibration generation budget, and a target for
selection noise expressed as a fraction of the caliper. At
$M_{\text{cal}} = 4$ the difference standard error is about 0.044 against a
caliper of 0.075; at $M_{\text{cal}} = 8$ it is about 0.037 at twice the
cost.

**Default.** $M_{\text{cal}} = 4$, with the disjoint pre-screen
confirmation of §18.4 condition 2 as the additional guard.

**Consequence if wrong.** Admitted references sit farther from the focal
difficulty than their estimates suggest, which shows up after the fact as
exchangeability failure, exactly as in v3.

---

## U6. The composed-uptake caliper

**Undecided.** §18.5 registers 0.15. The realised v3 gaps between focal and
reference composed uptake were 0.339, 0.365 and 0.396 for the three E4B
references and 0.182, 0.034 and 0.336 for the three E2B references. A
caliper of 0.15 admits one of those six and refuses five.

**Registered consequence.** Under this rule the v3 E4B replication would
have terminated at Gate 2B with `COMPOSED_UPTAKE_MISMATCH` rather than
producing three flagged manipulation checks and a positive but unresolved
estimate. That termination is the intended behaviour and is stated in §18.5
so that it cannot be reinterpreted later as an unexpected failure.

**Risk.** A caliper this tight, combined with the three-family requirement,
may terminate every replication. The dense ladder is the mitigation: it
supplies many more candidate severities than v3 had, and dose is expected
to vary along a family's ladder.

**Evidence needed.** Gate 2B composed-uptake distributions for the first
replication's full shortlist, inspected before study-wide freeze. If no
family reaches 0.15 for any model, the caliper is either widened with the
reason recorded, or the design accepts termination and reports
non-identification.

**Default.** 0.15, with no widening after freeze.

**Consequence if wrong.** Either universal termination, which produces no
estimates, or a caliper loose enough to reproduce the v3 dose mismatch.

---

## U7. Whether a two-reference degraded path should exist

**Undecided.** v3 required three references from three families and both
Qwen replications terminated with exactly two eligible pairs, producing no
evidence at all. A registered degraded path would let a replication with
exactly two eligible families proceed with a two-reference average, one
exchangeability contrast instead of three, and the Tier 2 identity-specific
claim structurally unavailable.

**Argument for.** Two of four v3 replications produced nothing. Partial
evidence under a restricted claim ladder is more informative than none.

**Argument against.** It lowers the bar for reaching a result, weakens the
exchangeability evidence from three contrasts to one, and adds a
researcher-visible branch at the gate where none exists today.

**Evidence needed.** A decision by the researcher. No measurement settles
it.

**Default.** No degraded path. Three references remain required and
`REFERENCE_POOL_MISMATCH` remains terminal.

---

## U8. Whether the v3 topic bank may be reused

**Undecided.** §6 registers a newly authored bank of 624 topics and
excludes every v3 topic from the v4 confirmatory set, because v3 §31
releases its 528 non-sequestered topics with a canary string when results
are reported, and release creates contamination exposure. Whether that
release has occurred is not stated in the uploaded corpus.

**Evidence needed.** Confirmation of whether the v3 release has happened.
If it has not, reuse becomes possible and the authoring cost of 624 new
questions is avoided, at the cost that the design team has seen v3
aggregate results on those topics. Per-topic results are not in the
uploaded corpus, so topic-level selection is not a live risk either way.

**Default.** Author a new bank. No v3 topic enters the v4 confirmatory set,
and the 96 v3 sequestered topics remain sequestered.

**Consequence if wrong.** Unnecessary authoring effort, which is a cost
rather than a validity threat.

---

## U9. Whether composed response length should become an admission predicate

**Undecided.** §16 registers composed response length as a reported
comparability quantity with an interpretation block on breach, not as a
Gate 2B predicate. v3 recorded a systematic asymmetry: median composed
length under the focal composition was 173 tokens against 189 to 248 in the
E2B references and 191 against 224, 232 and 248.5 in the E4B references, so the
focal constraint compressed responses more than any solo-matched reference
did.

**Why it matters.** Compression plausibly mediates the effect on an
exact-count target, because a shorter answer offers fewer places to put the
required word. Making length a predicate would match the compared
conditions on that mediator. Matching on a mediator changes the estimand:
it would remove from the contrast the part of $B$'s effect that operates
through compression, which may be the effect of interest.

**Evidence needed.** Gate 2B composed-length distributions for the first
replication's shortlist, and a decision on whether compression is a
nuisance to be matched away or the mechanism to be measured.

**Default.** Reported only. Length never enters an estimate and remains a
post-treatment quantity under §21.

---

## U10. Registered conjunctive extensions for exhausted ladders

**Undecided.** The dense ladder fills the interior of the v3 grids and does
not extend beyond their maxima or below $q = 0$. A family that a model
satisfies easily even at $q = 0$ contributes no admissible severity, and
the ladder is exhausted.

**What v3 shows.** For both Qwen models most families sat at solo failure
at or below 0.10 at every non-zero severity while the focal rate was 0.26
to 0.31, and the two admissible pairs each came from a low severity, RF4 at
$q=2$ and RF6 at $q=0$ for one model, RF3 at $q=2$ and RF4 at $q=4$ for the
other. The evidence is consistent with the dense ladder supplying a third
eligible family and does not establish it, because the intervening
severities were never measured.

**Evidence needed.** Ladder-screen curves from the v4 pre-screen for each
registered model. If a family remains below the caliper window at $q = 0$,
the only way to extend it is a new constraint construction, for example the
conjunction of two families at their most restrictive severities, which
requires new wordings, witnesses, verifiers, and a wording-length check.

**Default.** No extensions. A family whose ladder cannot reach the window
is recorded `LADDER_EXHAUSTED` in the admission table and the replication
terminates if fewer than three families remain.

---

## U11. Execution order and the early-stop rule

**Undecided.** §4 keeps v3's order, E2B first, with the remaining three
replications blocked if E2B terminates with a reference-pool, composed
headroom, or composed uptake failure. The alternative is to run the hardest
identification case first, one of the Qwen models, since the dense ladder
and the uptake predicate are aimed at exactly the failure those models
produced.

**Trade-off.** Running E2B first preserves continuity with v3 and treats a
pool failure on a model known to be identifiable as evidence of a design
fault. Running a Qwen model first tests the redesign against the case it
was built for, at the cost that a Qwen termination under the stop rule
would block the models most likely to produce estimates.

**Evidence needed.** A researcher decision. If a Qwen model runs first, the
stop rule must be rewritten so that its termination does not block the
Gemma replications.

**Default.** E2B first with the stop rule as written.

---

## U12. A form-varying second surrogate

**Undecided.** The registered surrogate varies the target word and holds
the constraint form fixed, so $\iota$ identifies identity-specificity with
respect to the word. A second surrogate of a different form, for example a
budget constraint rather than an exact-count constraint, would additionally
test specificity with respect to form.

**Cost.** Four further composed cells and one further solo arm per block,
raising the confirmatory stage from 11 arms to 16 and from 33,792 to 49,152
generations per model at $M = 8$, plus a further witness and wording suite.

**Evidence needed.** A generation budget decision and confirmation that
form-specificity is in scope. §3 currently excludes it.

**Default.** Word-varying surrogate only, with the exclusion stated in §3
and §30.

---

## Cross-cutting note on what none of these can fix

Two limitations of the v4 design are settled rather than open, and are
recorded here so they are not mistaken for open items.

**$\iota$ is under-powered relative to the effects the v3 diagnostics
suggest.** Its projected detectable effect at 80% power is 0.064 at
$M = 8$ and 0.057 at $M = 16$, while every v3 diagnostic mean fell between
+0.04 and +0.11. Reaching 0.05 needs about 633 blocks and 0.04 about 989,
which the 384-block bank cannot supply, and raising $M$ does not close the
gap because the block component then dominates. Only more topics do.

**Human validation may again be unavailable.** The registered fallback is a
proxy instrument with a machine-distinguishable basis marker and a fixed
strongest-claim sentence. A v4 completed on that basis reports a
verifier-defined outcome and supports no claim about compliance as an
independent human would judge it, exactly as v3 did. Reaching the
registered fail-class bound from the v3 position requires 34 further
zero-error labels. A bound of 0.05 would require the fail-class sample to
reach about 175 labels with those four errors standing, above the
registered per-class sample target of 150; the v3 report reaches the same
conclusion from the observed unaided error rate.
