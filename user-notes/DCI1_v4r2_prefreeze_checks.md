# DCI-1 v4 revision 2: empirical checks required before freeze

**Date:** 19 August 2026 · **Parent:** `DCI1_preregistration_v4r2.md`.

Every item below is an empirical or implementation fact this document
asserts, assumes, or projects, and which the uploaded corpus cannot
settle. None may be resolved after any confirmatory generation. Each entry
gives what is unverified, why it matters, what would settle it, and what
happens if the check fails.

Checks are grouped by the gate they block. Within a group they are ordered
by how much of the design depends on them.

---

## Group A. Blocks Gate 1, measurement

### C1. Boundary suites, adversarial corpora and independent reimplementations for every registered outcome verifier

**Unverified.** v3 §18.3 required the forty-case boundary suite of every
verifier and v3 §10 required three-process determinism of every verifier,
so those two lines already extend beyond the exact-count rule. Everything
else was exact-count-only: the 120 blinded labels, the autorater
development and calibration, the independent reimplementation, and the
four validity arguments. Whether the v3 family boundary suites exist, pass
under the current instrument, and cover the wider v4 enumeration of §24 is
unverified, and no family verifier carries the remaining lines at all.

**Why it matters.** Under the new primitive these are primary
instruments. §10.2 makes Gate 1 conditional on primary-instrument evidence
for all of them.

**What settles it.** Author and freeze a forty-case suite per verifier
covering the §24 enumeration; write an independent reimplementation of
each from the registered prose; run three-process determinism over every
calibration response; run the adversarial corpus and record the realised
frequency of each boundary case in genuine generations.

**If it fails.** `MEASUREMENT_NOT_ESTABLISHED` for the affected
instrument. A family whose verifier fails cannot be admitted as a
reference; if the word-length verifier fails, the study cannot proceed.

### C2. Graded-score and non-vacuity implementations

**Unverified.** The v3 family verifier returns a boolean pass. §7.4
registers a graded score per constraint form and §9.3 registers a
non-vacuity predicate per constraint form. Neither exists in the v3
implementation.

**Why it matters.** Graded scores carry the manipulation check the
construct memo found missing from every shipped analysis, and the
non-vacuity predicate is what bounds vacuous passing on non-violation
constraints.

**What settles it.** Implement both, pin them by unit tests against
hand-derived expectations at every registered severity, and include them
in the canonical verifier hash.

**If it fails.** Gate 1 cannot freeze, because the freeze record requires
both definitions.

### C3. Human-annotator availability, and the annotation burden at five instruments

**Unverified.** v3 never obtained an independent annotator. v4 needs human
evidence for the exact-count rule, the word-length rule and three family
verifiers.

**What settles it.** A decision on annotator availability. If unavailable,
complete the autorater pathway of §10.4: confirm the medium-versus-high
comparison on the existing 56-item author-labelled calibration sample
under serialised deterministic execution at concurrency one and the frozen
cap, paired on the same items, with coverage, per-class agreement, the
confusion matrix, discordant-item table, truncation incidence and
deterministic reproducibility; then select under the §10.4 hierarchy and
record the rejected alternative.

**If it fails.** `HUMAN_VALIDATION_UNAVAILABLE`, the autorater basis, and
the registered scope sentence attached to every claim. This is a permitted
outcome, not a blocker.

### C4. Sealed final-check set status

**Unverified.** The v3 record carries a sealed 40-item reserved set with a
recorded hash and states it is untouched. Whether the seal verifies
against the current artifact, and whether the set is appropriate for the
v4 instrument population, are both unverified.

**What settles it.** Verify the canonical hash of the current sealed
artifact before opening; confirm that every autorater choice is frozen
first; open at most once and never for tuning. A v4 instrument population
that differs from the sealed set's composition requires a **new** sealed
set rather than reuse.

### C5. Verifier-hash binding covers every v4 entry point

**Unverified.** v3 enforced the binding at its dispatcher. The v4 entry
points differ: ladder screen, solo calibration, reference admission,
composed-headroom validation, freeze, confirmatory generation, scoring,
resume and restart paths, analysis, unmasking and report generation.

**What settles it.** Regression tests: unchanged verifier after Gate 1
succeeds downstream; a committed semantic verifier change fails every
protected stage closed; reverting succeeds again; an irrelevant source
change produces no false mismatch; and stored verdict provenance remains
traceable to the verifier that produced it.

---

## Group B. Blocks Gate 2 and Gate 3, regime and references

### C6. The exact solo compliance of the exact-count constraint

**Unverified.** The companion-difficulty analysis in the change summary
uses $P(A \text{ solo})$ from the v3 confirmatory target-alone arm at one
draw per cell, approximately 0.667 and 0.578, while the reference solo
rates come from the v3 Gate 2A solo cells on a different topic set at one
draw per cell. The two are not the same estimator on the same topics.

**Why it matters.** The registered reference caliper is 0.10 around
$P(A \text{ solo})$, and a 0.02 error in that anchor moves which
severities qualify.

**What settles it.** Read the `solo:A:<n*>` cells from the v3 Gate 2A
cache for both Gemma models, which places $A$ and every reference on the
same 96 topics and the same estimator. In v4 the quantity is measured
directly at Gate 2, so this check bounds feasibility rather than defining
the caliper.

### C7. Whether a reference severity matched to the exact-count constraint exists

**Unverified.** Under the v3 rule the admitted references sit about 0.20
**above** $A$ in solo compliance. Matching to $A$ requires harder
severities than v3 used. Whether each family's integer ladder reaches
within 0.10 of $P(A \text{ solo})$ with a Newcombe interval intersecting
$\pm 0.05$, and whether three families do so, is unmeasured for all four
models.

**What settles it.** The §12.2 dense ladder screen on the 24 pre-screen
topics, followed by §12.3 confirmation on the 96 solo-calibration topics.

**If it fails.** `EXCESS_NOT_IDENTIFIED` and the reduced design of §8.6.
This is a registered outcome and is not a failure of the study.

### C7b. The realised companion-difficulty gap is measurable in the confirmatory data

**Unverified as implemented.** §13.2 relies on the confirmatory design
containing the solo cell of the exact-count constraint and of every
admitted reference on all 384 blocks, so that the realised gap is
estimable there at a paired standard error near 0.019 rather than the
0.038 the calibration sample supports.

**What settles it.** An executable check that the registered cell set
contains those solo cells, that the realised-gap estimator reads them from
the same blocks, and that the gap is emitted into the result table beside
every excess-damage statement together with the 0.15 qualifier of §28.1.

### C8. Operating regime for the two Qwen replications

**Unverified.** Neither Qwen model's solo compliance for the exact-count
constraint at any $n$, nor for the word-length constraint at any $m$,
appears in the uploaded corpus. Both terminated v3 at Gate 2A before the
question arose.

**Why it matters.** These are the two models the v4 architecture newly
unblocks, and they carry the most information about whether the phenomenon
is a capability threshold rather than a pair property.

**What settles it.** Run §12 for both. `REGIME_NOT_FOUND` is a permitted
outcome and is a statement about the registered grid.

### C9. Joint satisfiability and non-entailment for all ten unordered pairs

**Unverified.** v3 certified witnesses for $A{+}B$ and $A{+}R$. The v4
matrix additionally requires $B{+}R_j$ and $R_j{+}R_k$ witnesses at the
admitted severities. The pilot generated $B{+}R$ cells but the witness
suite for reference-with-reference pairs has never been built.

**What settles it.** Extend the witness suite to all ten pairs at every
candidate severity, with the non-entailment pair in both directions, as an
executable qualification test.

### C10. Realised vacuity rates and the 20-word threshold

**Unverified.** The pilot recorded 13 of 576 and 8 of 576 responses under
three words with zero truncations. The rate at the registered 20-word
threshold is unmeasured, per cell type.

**What settles it.** Measure the response-length distribution and the
vacuity rate for every registered cell type in the §12 and §13.6
calibration stages. The threshold is fixed before confirmatory generation
and is never tuned to a rate.

**If the rate is high.** The F6 gate fires and the primary estimands are
reported with partial-identification bounds, which is the registered
handling rather than a blocker.

### C11. Accidental compliance and per-cell truncation

**Unverified.** Every constraint's verifier is evaluated in every cell,
including cells where that constraint is absent, giving the accidental
base rate. v3's analogue, the no-constraint arm, truncated in 322 of 384
and 333 of 384 responses, so its base rate was measured on mostly
truncated text.

**What settles it.** Report accidental compliance and truncation per cell
type at Gate 2 and Gate 4, and mark any figure from a cell whose
truncation rate exceeds 0.10 as a bound.

---

## Group C. Blocks the freeze, allocation and provenance

### C12. Re-estimate the variance constants from within-block data

**Unverified.** §16.1 registers $\phi = 0.27$ and $\rho = 0.5$. $\phi$ is
fitted to the pilot's reported interval widths and predicts them closely
for both models, 0.0326 against 0.0315 and 0.0284 against 0.0284. $\rho$
is assumed, and the pilot cannot estimate it because it compared a
96-topic solo set against a 384-block confirmatory set.

**Why it matters.** The whole allocation table, and therefore the choice
of 384 blocks at $M = 4$, rests on these two constants. $\phi$ is
identified by the pilot only under an assumed correlation among the three
reference cells; at an among-reference correlation of 1 the fit gives 0.27
and at 0.5 it gives about 0.37. Both are carried through §16.2 and the
allocation meets every precondition under both.

**What settles it.** Estimate two correlations separately: the
among-reference correlation, from the pilot rows, which carry three
reference cells on the same 96 topics; and the correlation between a cell
containing $A$ and a cell containing a reference with the same outcome
constraint, which the pilot cannot supply because its $A$ term comes from
a disjoint topic set, and which the v3 confirmatory cache can, because it
carries the $AB$ and $AR_j$ arms on the same 384 blocks. Then re-run the
§16.3 menu rule and record the selected allocation in the freeze.

**If the re-estimate is unfavourable.** Move up the registered menu.
Never proceed and report `INSUFFICIENT_PRECISION` when a cheaper
allocation was available and untaken.

### C13. Reproduce the pilot from its raw cache under the current verifier

**Unverified.** The pilot's reused baselines are pinned by
`test_br_pilot_characterization.py`, which checks row counts, pass counts,
model revisions, verifier source hashes, content hashes and verdict
recomputation for the reused Gate 2A and confirmatory cells. The pilot's
own B+R rows are not covered by an equivalent test.

**What settles it.** Re-score the 576 B+R rows per model from raw text
under the current verifier and confirm the reported cell rates, joint
states and per-order rates. This matters because those rows supply the
variance information behind the allocation.

### C14. Duplicate-generation rate under the v4 seed derivation

**Unverified.** The construct memo found that most legacy datasets seeded
all requests in a batch identically, giving about 98% byte-identical
replicate pairs and roughly halving the effective sample size, and that
only one legacy programme seeded from experimental identity. The v4 seed
derivation is per (root seed, stage, model, prompt hash, draw index), and
its realised duplicate rate is unmeasured.

**What settles it.** Count byte-identical replicate pairs within cells
across a calibration sample. §14.2 fails qualification above 0.05.

### C15. Provenance guard against deprecated and foreign inputs

**Unverified.** §26 requires an executable guard refusing any analysis
input that is not a registered v4 artifact, which must exclude the legacy
corpus, the v3 trees and the pilot cache.

**What settles it.** Implement the guard and test it against a legacy
artifact, a v3 artifact and a pilot artifact.

### C16. Within-block formation of every registered contrast

**Unverified.** The pilot's headline $\Delta$ compared a 96-topic solo set
against a 384-block confirmatory set and carried an explicit
exchangeability-by-design caveat. v4 removes the caveat by running every
cell on the same blocks.

**What settles it.** An executable check asserting that every registered
contrast is formed from cell means of the same block, with no cross-set
term anywhere in the analysis.

### C17. Topic authoring and the seeded split

**Unverified.** 624 topics do not yet exist. §6.2 requires 52 per subject
area, each verified individually against four authoring rules, split by a
fixed seed into five disjoint sets of 2, 8, 2, 32 and 8.

**What settles it.** Author and verify the bank, run the seeded split,
record its hash in the manifest, and confirm that no v3 topic and no pilot
topic appears in any v4 set.

---

## Group D. Recorded for the report, blocking nothing

### C18. Confirm the identity between the demoted diagnostic and the v3 record

The A-side companion swap $\Delta^A$ is algebraically equal to v3's
registered pooled swap effect on the compliance scale, and reproduces it
at $-0.0095$ against a recorded $-0.009549$ and $+0.0651$ against a
recorded $+0.065104$. Confirm the identity on the v3 rows rather than on
the summary record, so that the demotion argument rests on the rows.

### C19. Record the memo threshold provenance in the manifest

The 0.25 and 0.10 thresholds are quoted verbatim from
`dci-construct-pass2.md` §G row 1, dated 14 August 2026, and were
transcribed into the pilot protocol before the pilot generated anything.
Record the memo hash, the quoted line and both dates in the registration
manifest, so that the prospective status of the thresholds is auditable
rather than asserted.

### C20. Restate the pilot's status in every artifact that cites it

The pilot is non-confirmatory. Every v4 artifact citing it must carry that
label, must cite it only for variance information and design motivation,
and must never present its point estimates as the effect the confirmatory
design expects.
